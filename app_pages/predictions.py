"""Probabilistic forecasts with walk-forward validation, volatility model and technical regime."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import data, forecasting, ui
from sharkfin import indicators as ind
from sharkfin.explain import tip

ui.header("Forecasts",
          "Five statistical and machine-learning models, each tested on this stock's past and weighted by how well it "
          "actually forecast it. The cone shows the range of likely prices, from a volatility model with realistic fat tails.")

c1, c2, c3 = st.columns([3, 5, 2], vertical_alignment="bottom")
with c1:
    sym = ui.symbol_picker("pred")
horizon_lbl = c2.segmented_control("Horizon", ["1 week", "2 weeks", "1 month", "3 months"], default="1 month",
                                 help=tip("horizon"))
H = {"1 week": 5, "2 weeks": 10, "1 month": 21, "3 months": 63}[horizon_lbl or "1 month"]
depth = c3.select_slider("Backtest depth", options=[6, 8, 12, 16], value=8,
                         help=tip("backtest_depth"))

if not sym:
    st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def run_forecast(symbol: str, horizon: int, n_origins: int):
    hist = data.history(symbol, "10y")
    if hist.empty:
        return None, None
    hist = hist.iloc[-2520:]
    return forecasting.ensemble_forecast(hist, symbol, horizon=horizon, n_origins=n_origins), hist


with st.status(f"Fitting & backtesting 5 models on {sym}…", expanded=False) as status:
    try:
        res, hist = run_forecast(sym, H, depth)
    except ValueError as e:
        status.update(label=str(e), state="error")
        st.stop()
    status.update(label="Forecast ready", state="complete")

if res is None:
    st.error(f"No price history for {sym}.")
    st.stop()

last = res.last_price
end = res.at(H)

ui.metrics([
    {"label": f"Expected in {horizon_lbl or '1 month'}", "value": f"${end['expected']:,.2f}",
     "delta": f"{ui.fmt_pct(end['exp_return'], 1, True)} from ${last:,.2f}", "help": tip("expected")},
    {"label": "Chance it ends higher", "value": ui.fmt_pct(end["prob_up"], 0), "help": tip("prob_up")},
    {"label": "Likely range (80%)", "value": f"${end['low80']:,.0f} – ${end['high80']:,.0f}", "help": tip("range80")},
    {"label": "Volatility", "value": f"{res.garch.current_vol:.0%}", "delta": f"normal {res.garch.long_run_vol:.0%}",
     "delta_color": "off", "delta_arrow": "off",
     "help": tip("garch") + f" Shocks fade with a half-life of about {res.garch.half_life:.0f} trading days."},
], key="fc")

# ---- Fan chart ------------------------------------------------------------------

look = hist["Close"].iloc[-max(120, H * 4):]
q = res.quantiles
fig = go.Figure()
fig.add_trace(go.Scatter(x=look.index, y=look.values, name="Price", line=dict(color="#c9d1dc", width=1.8)))
x0 = [look.index[-1]]
band = lambda lo, hi, color, name: [
    go.Scatter(x=x0 + list(q.index), y=[last] + list(q[hi]), line=dict(width=0), showlegend=False, hoverinfo="skip"),
    go.Scatter(x=x0 + list(q.index), y=[last] + list(q[lo]), line=dict(width=0), fill="tonexty", fillcolor=color, name=name),
]
for tr in band(0.05, 0.95, "rgba(78,168,255,0.10)", "90% of outcomes") + band(0.10, 0.90, "rgba(78,168,255,0.16)", "80%") \
        + band(0.25, 0.75, "rgba(78,168,255,0.26)", "50%"):
    fig.add_trace(tr)
if st.toggle("Show individual model forecasts", value=False,
             help="Draws each model's own forecast path. The orange blend weights them by past accuracy."):
    for name, path in res.model_paths.items():
        fig.add_trace(go.Scatter(x=x0 + list(q.index), y=[last] + list(path), name=name, line=dict(width=1, dash="dot")))
fig.add_trace(go.Scatter(x=x0 + list(q.index), y=[last] + list(res.expected_price), name="Expected path",
                         line=dict(color=ui.ORANGE, width=2.5)))
fig.update_layout(title=dict(text=f"{sym}: where the price could be in {horizon_lbl or '1 month'}"),
                  hovermode="x unified", yaxis_tickprefix="$")
ui.plotly(fig, 500)
st.caption("The shaded bands hold 50%, 80% and 90% of simulated outcomes. Wider bands mean more uncertainty.",
           help=tip("fan_chart"))

# ---- Horizon table ------------------------------------------------------------------
st.subheader("Along the way", help=tip("horizon_table"))
checkpoints = sorted({h for h in (5, 10, 21, 42, 63) if h <= H} | {H})
tbl = pd.DataFrame([{**res.at(h), "horizon": f"{h} days"} for h in checkpoints]).set_index("horizon").rename_axis("In")
tbl["exp_return"] *= 100
tbl["prob_up"] *= 100
st.dataframe(tbl[["date", "expected", "exp_return", "prob_up", "low80", "median", "high80"]], width="stretch",
             column_config={"date": st.column_config.DateColumn("Date", format="MMM D"),
                            "expected": st.column_config.NumberColumn("Expected", format="$%.2f", help=tip("expected")),
                            "exp_return": st.column_config.NumberColumn("Expected change", format="%+.1f%%", help="Expected % change from today's price."),
                            "prob_up": st.column_config.ProgressColumn("Chance higher", min_value=0, max_value=100, format="%.0f%%", help=tip("prob_up")),
                            "low80": st.column_config.NumberColumn("Low end (10%)", format="$%.2f", help=tip("p10")),
                            "median": st.column_config.NumberColumn("Median", format="$%.2f", help=tip("median")),
                            "high80": st.column_config.NumberColumn("High end (90%)", format="$%.2f", help=tip("p90"))})

# ---- Model leaderboard ------------------------------------------------------------------
st.subheader("Which models to trust", help=tip("leaderboard"))
lb = pd.DataFrame([{
    "Model": s.name, "Weight": s.weight * 100, f"Forecast ({H}d)": s.forecast_return * 100,
    "Skill vs random walk": s.skill_vs_rw * 100, "Direction hit rate": s.directional_accuracy * 100,
    "How it works": s.description,
} for s in res.scores]).sort_values("Weight", ascending=False)
st.dataframe(lb, hide_index=True, width="stretch", column_config={
    "Weight": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%", help=tip("weight")),
    f"Forecast ({H}d)": st.column_config.NumberColumn(format="%+.1f%%", help="This model's own forecast return over the horizon."),
    "Skill vs random walk": st.column_config.NumberColumn(format="%+.1f%%", help=tip("skill")),
    "Direction hit rate": st.column_config.NumberColumn("Right direction", format="%.0f%%", help=tip("hit_rate")),
    "How it works": st.column_config.TextColumn(help="A one-line description of the model."),
})
cov_txt = ui.fmt_pct(res.coverage_80, 0)
st.caption(f"Scored on {res.n_backtest} walk-forward origins. The 80% band contained the realised price "
           f"{cov_txt} of the time in backtest (well-calibrated ≈ 80%). Stock returns are close to unpredictable over short "
           "horizons, so a model that doesn't beat the random walk is automatically down-weighted rather than trusted.",
           help=tip("coverage"))

# ---- Technical regime ------------------------------------------------------------------
st.subheader("Technical picture", help="A snapshot of trend and momentum indicators on the daily chart.")
panel = ind.compute_all(hist)
sig = ind.technical_signal(panel)
hurst = ind.hurst_exponent(hist["Close"].iloc[-500:])
ui.metrics([
    {"label": "Signal", "value": sig["label"], "delta": f"score {sig['score']:+.2f}", "delta_color": "off",
     "delta_arrow": "off", "help": tip("tech_signal")},
    {"label": "Market regime", "value": sig["regime"], "delta": f"ADX {panel['adx'].iloc[-1]:.0f}", "delta_color": "off",
     "delta_arrow": "off", "help": tip("adx_regime")},
    {"label": "Hurst exponent", "value": ui.fmt_num(hurst),
     "delta": "trending" if hurst > 0.55 else "mean-reverting" if hurst < 0.45 else "random-walk-like",
     "delta_color": "off", "delta_arrow": "off", "help": tip("hurst")},
    {"label": "Daily range (ATR)", "value": ui.fmt_pct(panel["natr_14"].iloc[-1] / 100, 2), "help": tip("natr")},
], key="tech")
ev = pd.DataFrame(sig["evidence"], columns=["Evidence", "Contribution"])
fig = go.Figure(go.Bar(x=ev["Contribution"], y=ev["Evidence"], orientation="h",
                       marker_color=np.where(ev["Contribution"] >= 0, ui.GREEN, ui.RED)))
fig.update_layout(title=f"What's driving the signal (trend weight {'75%' if sig['regime'] == 'Trending' else '35%'} in a {sig['regime'].lower()} regime)",
                  yaxis=dict(autorange="reversed"))
ui.plotly(fig, 320)

latest = panel.iloc[-1]
tech = {
    "RSI (14)": latest["rsi_14"], "Stoch %K": latest["stoch_k"], "MFI (14)": latest["mfi_14"], "ADX": latest["adx"],
    "+DI / -DI": f"{latest['plus_di']:.0f} / {latest['minus_di']:.0f}", "MACD hist": latest["hist"],
    "Bollinger %B": latest["bb_pct_b"], "BB width": latest["bb_width"], "ATR (14)": latest["atr_14"],
    "Realised vol (21d)": latest["rv_21"], "Parkinson vol (21d)": latest["pk_vol_21"],
    "vs SMA 50": latest["close"] / latest["sma_50"] - 1, "vs SMA 200": latest["close"] / latest["sma_200"] - 1,
    "vs VWAP 20": latest["close"] / latest["vwap_20"] - 1,
}
def _fmt(k, v):
    if isinstance(v, str):
        return v
    if k.startswith("vs") or "vol" in k:
        return ui.fmt_pct(v, 1, k.startswith("vs"))
    return ui.fmt_num(v)


with st.expander("All indicator readings"):
    ui.kv([(k, _fmt(k, v)) for k, v in tech.items()])

ui.disclaimer()
