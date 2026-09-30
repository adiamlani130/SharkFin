"""Strategy Lab: backtest trading rules against buy-and-hold, with costs."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import backtest, data, risk, ui

st.title("Strategy Lab")
st.caption("Test classic rules on any ticker. Signals use the close and trade on the next bar (no look-ahead), "
           "costs are charged on every position change, and idle cash earns the risk-free rate.")

c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    sym = ui.symbol_picker("lab")
period = c2.segmented_control("History", ["3y", "5y", "10y", "max"], default="10y")
cost = c3.number_input("Trading cost (bps per trade)", 0.0, 100.0, 5.0, 1.0)
chosen = st.multiselect("Strategies", list(backtest.STRATEGIES), default=list(backtest.STRATEGIES))
if not sym or not chosen:
    st.stop()

with st.expander("Strategy parameters"):
    params = {}
    p = st.columns(4)
    params["SMA Crossover"] = {"fast": p[0].number_input("SMA fast", 5, 150, 50), "slow": p[0].number_input("SMA slow", 20, 400, 200)}
    params["RSI Mean Reversion"] = {"entry": p[1].number_input("RSI entry <", 5, 50, 30), "exit": p[1].number_input("RSI exit >", 40, 90, 55),
                                    "trend_filter": p[1].toggle("200-day trend filter", True)}
    params["Donchian Breakout"] = {"entry": p[2].number_input("Breakout days", 10, 200, 55), "exit": p[2].number_input("Exit days", 5, 100, 20)}
    params["Vol-Targeted Trend"] = {"target_vol": p[3].slider("Target vol", 0.05, 0.40, 0.15, 0.01), "sma": 200}
    params["Time-Series Momentum"] = {"lookback": p[3].number_input("Momentum lookback (days)", 21, 504, 252)}

hist = data.history(sym, period or "10y")
if len(hist) < 260:
    st.error("Need at least a year of history.")
    st.stop()

rf = data.risk_free_rate()
results = {n: backtest.run(hist, n, params.get(n), cost, rf) for n in chosen}

fig = go.Figure([go.Scatter(x=r["equity"].index, y=r["equity"], name=n) for n, r in results.items()])
fig.update_layout(title=f"{sym}: growth of $1", yaxis_type="log", hovermode="x unified")
ui.plotly(fig, 460)

stats = pd.DataFrame({n: r["stats"] for n, r in results.items()}).T
pct_cols = ["CAGR", "Volatility", "Max Drawdown", "VaR 95% (1d)", "CVaR 95% (1d)", "CF VaR 95% (1d)", "Hit Rate",
            "Alpha (ann.)", "Tracking Error", "Exposure"]
cfg = {c: st.column_config.NumberColumn(format="percent") for c in pct_cols if c in stats}
cfg.update({c: st.column_config.NumberColumn(format="%.2f") for c in stats.columns if c not in cfg and c != "Trades"})
st.dataframe(stats.sort_values("Sharpe", ascending=False), width="stretch", column_config=cfg)

l, r = st.columns(2)
with l:
    fig = go.Figure([go.Scatter(x=v["returns"].index, y=risk.drawdown_series(v["returns"]) * 100, name=n) for n, v in results.items()])
    fig.update_layout(title="Drawdowns (%)")
    ui.plotly(fig, 340)
with r:
    pick = st.selectbox("Rolling 1-year Sharpe for", list(results))
    rr = results[pick]["returns"]
    roll = rr.rolling(252).mean() / rr.rolling(252).std() * (252 ** 0.5)
    fig = go.Figure(go.Scatter(x=roll.index, y=roll, line=dict(color=ui.BLUE)))
    fig.add_hline(y=0, line=dict(color=ui.MUTED, dash="dot"))
    fig.update_layout(title=f"{pick}: rolling 1-year Sharpe")
    ui.plotly(fig, 340)

with st.expander("How each strategy works"):
    for n in chosen:
        st.markdown(f"**{n}**: {backtest.STRATEGIES[n].description}")
st.caption("A single-stock backtest is one path of history; beware overfitting parameters to it.")
ui.disclaimer()
