"""Forecasts: where a stock could be over a week to a year, and what is most likely to move it over that time.

The range comes from five models tested on the stock's own past (walk-forward) and a volatility model with fat
tails. The drivers change with the timeframe (``sharkfin.drivers``): news and the next report over days and weeks,
estimates and earnings surprises over months, valuation and business quality over a year.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import data, drivers, forecasting, sentiment, ui
from sharkfin import indicators as ind
from sharkfin import valuation
from sharkfin.explain import tip

ui.header("Forecasts",
          "Where a stock could be in a week, a month or a year, and what is most likely to move it over that time. "
          "Short-term it's mostly news and earnings; long-term it's growth and what you pay for it.")

c1, c2 = st.columns([3, 6], vertical_alignment="bottom")
with c1:
    sym = ui.symbol_picker("pred")
horizon_lbl = c2.segmented_control("Timeframe", list(drivers.HORIZONS), default="3 months", help=tip("horizon"),
                                   key="pred_h") or "3 months"
H = drivers.HORIZONS[horizon_lbl]

if not sym:
    st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def run_forecast(symbol: str, horizon: int, n_origins: int):
    hist = data.history(symbol, "10y")
    if hist.empty:
        return None, None
    hist = hist.iloc[-2520:]
    return forecasting.ensemble_forecast(hist, symbol, horizon=horizon, n_origins=n_origins), hist


with st.spinner(f"Loading {sym}…"):
    ui.fetch_all([(data.info, (sym,)), (data.history, (sym, "10y")), (data.analyst_data, (sym,)),
                  (data.earnings_history, (sym,)), (data.market_history, ("2y",)), (data.history, ("^VIX", "1y")),
                  (data.news, (sym, sym))])
    inf = data.info(sym) or {}

with st.status(f"Testing 5 forecast models on {sym}'s past…", expanded=False) as status:
    try:
        res, hist = run_forecast(sym, H, 8)
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
    {"label": f"Middle estimate in {horizon_lbl}", "value": f"${end['expected']:,.2f}",
     "delta": f"{ui.fmt_pct(end['exp_return'], 1, True)} from ${last:,.2f}", "help": tip("expected")},
    {"label": "Chance it ends higher", "value": ui.fmt_pct(end["prob_up"], 0), "help": tip("prob_up")},
    {"label": "Likely range (8 in 10)", "value": f"${end['low80']:,.0f} – ${end['high80']:,.0f}", "help": tip("range80")},
    {"label": "How bumpy", "value": f"{res.garch.current_vol:.0%} a year",
     "delta": f"normal for it {res.garch.long_run_vol:.0%}", "delta_color": "off", "delta_arrow": "off",
     "help": "Expected volatility: how much the price typically swings in a year. " + tip("garch")},
], key="fc")

# ---- Fan chart ------------------------------------------------------------------

look = hist["Close"].iloc[-max(120, min(H * 3, 500)):]
q = res.quantiles
fig = go.Figure()
fig.add_trace(go.Scatter(x=look.index, y=look.values, name="Price", line=dict(color="#c9d1dc", width=1.8)))
x0 = [look.index[-1]]
band = lambda lo, hi, color, name: [
    go.Scatter(x=x0 + list(q.index), y=[last] + list(q[hi]), line=dict(width=0), showlegend=False, hoverinfo="skip"),
    go.Scatter(x=x0 + list(q.index), y=[last] + list(q[lo]), line=dict(width=0), fill="tonexty", fillcolor=color, name=name),
]
for tr in band(0.05, 0.95, "rgba(78,168,255,0.10)", "9 in 10 outcomes") + band(0.10, 0.90, "rgba(78,168,255,0.16)", "8 in 10") \
        + band(0.25, 0.75, "rgba(78,168,255,0.26)", "Half"):
    fig.add_trace(tr)
fig.add_trace(go.Scatter(x=x0 + list(q.index), y=[last] + list(res.expected_price), name="Middle estimate",
                         line=dict(color=ui.ORANGE, width=2.5)))
fig.update_layout(title=dict(text=f"{sym}: where the price could be in {horizon_lbl}"),
                  hovermode="x unified", yaxis_tickprefix="$")
ui.plotly(fig, 460)
st.caption("The shaded bands hold half, 8 in 10 and 9 in 10 of the simulated outcomes. Price models can't see news "
           "or earnings coming, so read the drivers below with them.", help=tip("fan_chart"))

# ---- What moves it over this timeframe ------------------------------------------------------------------

ad = data.analyst_data(sym) or {}
ed = data.earnings_history(sym)
if not isinstance(ed, pd.DataFrame) or ed.empty:
    ed = ad.get("earnings_dates")
spy = data.market_history("2y")
spy_c = spy["Close"] if isinstance(spy, pd.DataFrame) and "Close" in spy else pd.Series(dtype=float)
vix_h = data.history("^VIX", "1y")
vix = float(vix_h["Close"].dropna().iloc[-1]) if isinstance(vix_h, pd.DataFrame) and len(vix_h.get("Close", [])) else np.nan
spy_week = float(spy_c.iloc[-1] / spy_c.iloc[-6] - 1) if len(spy_c) > 6 else np.nan
er = drivers.earnings_record(ed, hist["Close"], spy_c if len(spy_c) else None)
est = drivers.estimate_trend(ad.get("eps_trend"), ad.get("eps_revisions"))
name = inf.get("shortName") or sym
arts = sentiment.rank_articles(data.news(sym, sym) or [], f"{sym} {name}")
news_agg = sentiment.aggregate_sentiment(arts[:30])
g = valuation.forward_growth(ad.get("growth_estimates"))
dv = drivers.drivers(H, info=inf, earnings=er, estimates=est, news=news_agg, close=hist["Close"], vix=vix,
                     spy_week=spy_week, growth=g)

st.subheader(f"What moves it over {horizon_lbl}",
             help="Ranked by how much each has mattered at this timeframe in SharkFin's research and the best-known "
                  "studies. Price patterns barely predict anything at any horizon, so the list leads with earnings, "
                  "estimates, news and value.")
rows = []
for it in dv["items"]:
    rows.append(f"<div class='sf-driver'>{ui.pill(it['name'], it['tone'])}<span><b>{ui.h(it['reading'])}.</b> "
                f"{ui.h(it['why'])}</span></div>")
if not rows:
    rows.append("<div class='sf-driver'><span class='sf-muted'>No earnings, estimate or news data for this stock.</span></div>")
st.markdown(f"<div class='sf-today' style='--c:var(--sf-accent)'><div class='tx'>{ui.h(dv['summary'])}</div>"
            f"<div class='sf-drivers'>{''.join(rows)}</div></div>", unsafe_allow_html=True)

# ---- Earnings and catalysts ------------------------------------------------------------------

st.subheader("Earnings and catalysts")
tgt = ui.num(inf.get("targetMeanPrice"))
ui.metrics([
    {"label": "Next report", "value": f"{er['next']:%b %d}" if er["next"] is not None else None,
     "delta": f"in {er['days_to_next']} days" if er["days_to_next"] is not None else None, "delta_color": "off",
     "delta_arrow": "off"},
    {"label": "Typical report-day move", "value": ui.fmt_pct(er["typical_move"], 1) if np.isfinite(er["typical_move"]) else None,
     "help": "The median size of the stock's move vs the market on the day after its last 8 reports, either way."},
    {"label": "Beat estimates", "value": f"{er['beats']} of the last 4" if er["beats"] is not None else None},
    {"label": "Analyst target", "value": f"${tgt:,.0f}" if np.isfinite(tgt) else None,
     "delta": f"{tgt / last - 1:+.0%} from here" if np.isfinite(tgt) else None, "delta_arrow": "off",
     "help": "The average 12-month target. Targets tend to run a few points too high."},
    {"label": "Estimates, 30 days", "value": ui.fmt_pct(est["chg30"], 1, True) if np.isfinite(est["chg30"]) else None,
     "help": "How the consensus EPS estimate for next year changed over the last 30 days."},
], key="fc_cat")
if not er["history"].empty:
    h = er["history"].head(4)
    with st.expander("The last reports"):
        st.dataframe(h, hide_index=True, width="stretch", column_config={
            "Reported": st.column_config.DateColumn(format="MMM D, YYYY"),
            "EPS estimate": st.column_config.NumberColumn(format="$%.2f"),
            "Reported EPS": st.column_config.NumberColumn(format="$%.2f"),
            "Surprise": st.column_config.NumberColumn(format="percent"),
            "Next-day move": st.column_config.NumberColumn("Move vs market", format="percent")})
if arts:
    with st.expander(f"Latest headlines ({news_agg['label'].lower()} overall)"):
        for a in arts[:6]:
            ui.news_item(a, show_summary=False)

# ---- For the technically minded ------------------------------------------------------------------

with st.expander("How the forecast was made"):
    checkpoints = sorted({h for h in (5, 21, 63, 126, 252) if h <= H} | {H})
    tbl = pd.DataFrame([{**res.at(h), "horizon": f"{h} days"} for h in checkpoints]).set_index("horizon").rename_axis("In")
    tbl["exp_return"] *= 100
    tbl["prob_up"] *= 100
    st.dataframe(tbl[["date", "expected", "exp_return", "prob_up", "low80", "high80"]], width="stretch",
                 column_config={"date": st.column_config.DateColumn("Date", format="MMM D"),
                                "expected": st.column_config.NumberColumn("Middle", format="$%.2f"),
                                "exp_return": st.column_config.NumberColumn("Change", format="%+.1f%%"),
                                "prob_up": st.column_config.ProgressColumn("Chance higher", min_value=0, max_value=100,
                                                                           format="%.0f%%"),
                                "low80": st.column_config.NumberColumn("Low end", format="$%.2f", help=tip("p10")),
                                "high80": st.column_config.NumberColumn("High end", format="$%.2f", help=tip("p90"))})
    lb = pd.DataFrame([{
        "Model": s.name, "Weight": s.weight * 100, f"Forecast ({H}d)": s.forecast_return * 100,
        "Skill vs random walk": s.skill_vs_rw * 100, "Direction hit rate": s.directional_accuracy * 100,
        "How it works": s.description,
    } for s in res.scores]).sort_values("Weight", ascending=False)
    st.dataframe(lb, hide_index=True, width="stretch", column_config={
        "Weight": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%", help=tip("weight")),
        f"Forecast ({H}d)": st.column_config.NumberColumn(format="%+.1f%%"),
        "Skill vs random walk": st.column_config.NumberColumn(format="%+.1f%%", help=tip("skill")),
        "Direction hit rate": st.column_config.NumberColumn("Backtested accuracy", format="%.0f%%", help=tip("hit_rate")),
    })
    st.caption(f"Scored on {res.n_backtest} past dates as if live. The 8-in-10 band held the real price "
               f"{ui.fmt_pct(res.coverage_80, 0)} of the time (80% is right). Models that don't beat 'the price "
               "stays where it is' get little weight, which is why most forecasts sit close to today's price plus "
               "the stock's normal drift.", help=tip("coverage"))
    panel = ind.compute_all(hist)
    sig = ind.technical_signal(panel)
    latest = panel.iloc[-1]
    ui.kv([("Chart signal", f"{sig['label']} ({sig['regime'].lower()})"), ("RSI (14)", ui.fmt_num(latest["rsi_14"])),
           ("vs 50-day average", ui.fmt_pct(latest["close"] / latest["sma_50"] - 1, 1, True)),
           ("vs 200-day average", ui.fmt_pct(latest["close"] / latest["sma_200"] - 1, 1, True)),
           ("Daily range (ATR)", ui.fmt_pct(latest["natr_14"] / 100, 2))])
    st.caption("Chart readings are context, not drivers: in SharkFin's 2006-26 test of S&P 500 stocks, no price "
               "pattern (momentum, the 200-day, the 52-week high, last month's move) sorted the next week to year "
               "by more than a rank correlation of 0.05.")

ui.disclaimer()
