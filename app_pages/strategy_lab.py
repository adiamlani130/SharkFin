"""Strategy Lab: backtest trading rules against buy-and-hold, with costs."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import backtest, data, risk, swing, ui
from sharkfin.explain import tip

st.title("Strategy Lab")
st.caption("Test trading rules on any ticker. Signals use the close and trade on the next bar (no look-ahead), "
           "costs are charged on every trade, and idle cash earns the risk-free rate. Hover the ⓘ icons for plain-English explanations.")

CONF = "Confluence Pullback"

c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    sym = ui.symbol_picker("lab")
period = c2.segmented_control("History", ["3y", "5y", "10y", "max"], default="10y", help=tip("history"))
cost = c3.number_input("Trading cost (bps per trade)", 0.0, 100.0, 5.0, 1.0, help=tip("cost"))
chosen = st.multiselect("Strategies", list(backtest.STRATEGIES), default=list(backtest.STRATEGIES), help=tip("strategies"))
if not sym or not chosen:
    st.stop()

params = {}
with st.expander("Classic strategy parameters"):
    st.caption(tip("params"))
    p = st.columns(4)
    params["SMA Crossover"] = {"fast": p[0].number_input("SMA fast", 5, 150, 50, help="Days in the fast moving average."),
                               "slow": p[0].number_input("SMA slow", 20, 400, 200, help="Days in the slow moving average.")}
    params["RSI Mean Reversion"] = {"entry": p[1].number_input("RSI entry <", 5, 50, 30, help="Buy when RSI drops below this."),
                                    "exit": p[1].number_input("RSI exit >", 40, 90, 55, help="Sell when RSI recovers above this."),
                                    "trend_filter": p[1].toggle("200-day trend filter", True, help="Only buy dips while the stock is above its 200-day average.")}
    params["Donchian Breakout"] = {"entry": p[2].number_input("Breakout days", 10, 200, 55, help="Buy when price beats its highest high of this many days."),
                                   "exit": p[2].number_input("Exit days", 5, 100, 20, help="Sell when price breaks its lowest low of this many days.")}
    params["Vol-Targeted Trend"] = {"target_vol": p[3].slider("Target vol", 0.05, 0.40, 0.15, 0.01,
                                                              help="Position size is scaled so the strategy's volatility lands near this level."),
                                    "sma": 200}
    params["Time-Series Momentum"] = {"lookback": p[3].number_input("Momentum lookback (days)", 21, 504, 252,
                                                                     help="Hold the stock while its return over this many days is positive.")}

if CONF in chosen:
    with st.expander("Confluence Pullback settings", expanded=True):
        st.caption("Must-pass rules all have to be true. Point rules each add 1 to the score, and a trade needs at least the minimum score.")
        enabled = {}
        req = [k for k, r in swing.RULES.items() if r.kind == "required"]
        pts = [k for k, r in swing.RULES.items() if r.kind == "point"]
        l, r = st.columns(2)
        l.markdown("**Must pass**")
        for k in req:
            enabled[k] = l.toggle(swing.RULES[k].label, swing.RULES[k].default, key=f"cp_{k}", help=swing.RULES[k].explain)
        r.markdown("**Points**")
        for k in pts:
            enabled[k] = r.toggle(swing.RULES[k].label, swing.RULES[k].default, key=f"cp_{k}", help=swing.RULES[k].explain)
        n_pts = sum(enabled[k] for k in pts)
        q = st.columns(4)
        conf = {
            "enabled": enabled,
            "min_score": q[0].slider("Minimum score", 0, max(n_pts, 1), min(4, n_pts), help=tip("min_score")),
            "stop_mode": q[1].selectbox("Stop placement", swing.STOP_MODES, help=tip("stop_mode")),
            "t1_r": q[2].number_input("T1 (R multiple)", 0.5, 5.0, 1.5, 0.25, help=tip("t1_r")),
            "t2_r": q[3].number_input("T2 (R multiple, 0 = none)", 0.0, 10.0, 3.0, 0.5, help=tip("t2_r")),
            "t1_fraction": q[0].slider("Sell at T1", 0.25, 1.0, 0.5, 0.25, format="%.2f", help=tip("t1_fraction")),
            "max_hold": q[1].number_input("Max days in trade", 5, 250, 40, help=tip("max_hold")),
            "flow": q[2].radio("Volume-flow line", ["OBV", "VPT"], horizontal=True, help=tip("flow")),
        }
        e = st.columns(4)
        conf["trail"] = e[0].toggle("Trail under 20 EMA after T1", True, help=tip("trail"))
        conf["exit_below_50"] = e[1].toggle("Exit on close below 50-day", True, help=tip("exit_below_50"))
        conf["divergence_tighten"] = e[2].toggle("RSI divergence tightens stop", True, help=tip("divergence"))
        conf["rsi_fade_partial"] = e[3].toggle("RSI > 70 fade takes partial", True, help=tip("rsi_fade"))
    params[CONF] = conf

hist = data.history(sym, period or "10y")
if len(hist) < 260:
    st.error("Need at least a year of history.")
    st.stop()

rf = data.risk_free_rate()
if CONF in chosen:
    mkt = data.market_history(period or "10y")
    params[CONF] = {**params[CONF], "market": mkt["Close"] if not mkt.empty else None}
results = {n: backtest.run(hist, n, params.get(n), cost, rf) for n in chosen}

st.subheader("Growth of $1", help=tip("growth_of_1"))
fig = go.Figure([go.Scatter(x=r["equity"].index, y=r["equity"], name=n) for n, r in results.items()])
fig.update_layout(title=f"{sym}: growth of $1", yaxis_type="log", hovermode="x unified")
ui.plotly(fig, 460)

stats = pd.DataFrame({n: r["stats"] for n, r in results.items()}).T
pct_cols = ["CAGR", "Volatility", "Max Drawdown", "VaR 95% (1d)", "CVaR 95% (1d)", "CF VaR 95% (1d)", "Hit Rate",
            "Alpha (ann.)", "Tracking Error", "Exposure"]
cfg = {c: st.column_config.NumberColumn(format="percent", help=tip(c)) for c in pct_cols if c in stats}
cfg.update({c: st.column_config.NumberColumn(format="%.2f", help=tip(c)) for c in stats.columns if c not in cfg and c != "Trades"})
cfg["Trades"] = st.column_config.NumberColumn(help=tip("Trades"))
st.subheader("Performance statistics", help="Hover any column header for what it means.")
st.dataframe(stats.sort_values("Sharpe", ascending=False), width="stretch", column_config=cfg)

l, r = st.columns(2)
with l:
    st.markdown("**Drawdowns**", help=tip("drawdowns"))
    fig = go.Figure([go.Scatter(x=v["returns"].index, y=risk.drawdown_series(v["returns"]) * 100, name=n) for n, v in results.items()])
    fig.update_layout(title="Drawdowns (%)")
    ui.plotly(fig, 340)
with r:
    pick = st.selectbox("Rolling 1-year Sharpe for", list(results), help=tip("rolling_sharpe"))
    rr = results[pick]["returns"]
    roll = rr.rolling(252).mean() / rr.rolling(252).std() * (252 ** 0.5)
    fig = go.Figure(go.Scatter(x=roll.index, y=roll, line=dict(color=ui.BLUE)))
    fig.add_hline(y=0, line=dict(color=ui.MUTED, dash="dot"))
    fig.update_layout(title=f"{pick}: rolling 1-year Sharpe")
    ui.plotly(fig, 340)

# ---------------------------------------------------------------------------
# Confluence Pullback: trade-by-trade view
# ---------------------------------------------------------------------------
if CONF in results:
    res = results[CONF]
    ts, trades = res["trade_stats"], res["trades"]
    st.subheader("Confluence Pullback: trade by trade",
                 help="Win rate alone is misleading: a 70% win rate with small wins and big losses still loses money. "
                      "Expectancy (average R per trade) is what tells you whether the system makes money.")
    m = st.columns(6)
    m[0].metric("Completed trades", ts["Trades"], help=tip("Trades"))
    m[1].metric("Win rate", ui.fmt_pct(ts["Win rate"], 0), help=tip("Win rate"))
    m[2].metric("Expectancy", f"{ts['Expectancy (R)']:+.2f}R" if np.isfinite(ts["Expectancy (R)"]) else "—", help=tip("Expectancy (R)"))
    m[3].metric("Profit factor", ui.fmt_num(ts["Profit factor"]), help=tip("Profit factor"))
    m[4].metric("Avg win / loss", f"{ui.fmt_pct(ts['Avg win'], 1)} / {ui.fmt_pct(ts['Avg loss'], 1)}",
                help="Average return of winning trades and of losing trades.")
    m[5].metric("Avg days held", ui.fmt_num(ts["Avg bars held"], 1), help=tip("Avg bars held"))
    if trades.empty:
        st.info("No trades triggered with these settings. Try lowering the minimum score or switching a must-pass rule off.")
    else:
        view = hist.iloc[-504:]
        rules = res["rules"].reindex(view.index)
        fig = go.Figure(go.Candlestick(x=view.index, open=view["Open"], high=view["High"], low=view["Low"], close=view["Close"],
                                       name=sym, increasing_line_color=ui.GREEN, decreasing_line_color=ui.RED))
        fig.add_scatter(x=view.index, y=rules["ema20"], name="EMA 20", line=dict(width=1.2))
        fig.add_scatter(x=view.index, y=rules["sma50"], name="SMA 50", line=dict(width=1.2))
        fig.add_scatter(x=view.index, y=rules["sma200"], name="SMA 200", line=dict(width=1.2))
        tv = trades[trades["Entry date"] >= view.index[0]]
        fig.add_scatter(x=tv["Entry date"], y=tv["Entry"], mode="markers", name="Entry",
                        marker=dict(symbol="triangle-up", size=12, color=ui.GREEN))
        tc = tv.dropna(subset=["Exit date"])
        fig.add_scatter(x=tc["Exit date"], y=tc["Avg exit"], mode="markers", name="Exit",
                        marker=dict(symbol="triangle-down", size=12, color=np.where(tc["Return"] > 0, ui.BLUE, ui.RED)),
                        text=tc["Exit reason"], hovertemplate="%{text}: $%{y:.2f}<extra></extra>")
        fig.update_layout(title="Last 2 years: entries and exits", xaxis_rangeslider_visible=False, hovermode="x unified")
        ui.plotly(fig, 480)

        l, r = st.columns([3, 2])
        with l:
            show = trades.drop(columns=[k for k in swing.RULES if k in trades]).iloc[::-1]
            st.markdown("**Every trade**", help=tip("R multiple"))
            st.dataframe(show, hide_index=True, width="stretch", height=320, column_config={
                "Entry date": st.column_config.DateColumn(), "Exit date": st.column_config.DateColumn(),
                "Entry": st.column_config.NumberColumn(format="$%.2f"), "Stop": st.column_config.NumberColumn(format="$%.2f"),
                "Risk ($)": st.column_config.NumberColumn(format="$%.2f", help=tip("risk_r")),
                "Avg exit": st.column_config.NumberColumn(format="$%.2f"),
                "Return": st.column_config.NumberColumn(format="percent"),
                "R multiple": st.column_config.NumberColumn(format="%.2f", help=tip("R multiple")),
                "Score": st.column_config.NumberColumn(help="How many point rules passed on the signal day."),
            })
        with r:
            fig = go.Figure(go.Histogram(x=trades["R multiple"], nbinsx=30, marker_color=ui.BLUE))
            fig.add_vline(x=0, line=dict(color=ui.MUTED, dash="dot"))
            fig.update_layout(title="Distribution of trade results (R)", xaxis_title="R multiple")
            ui.plotly(fig, 340)

        rep = swing.rule_report(trades)
        if not rep.empty:
            st.markdown("**Which point rules helped**", help=tip("rule_report"))
            st.dataframe(rep, width="stretch", column_config={
                c: st.column_config.NumberColumn(format="percent" if "Win" in c else "%.2f") for c in rep.columns if "Trades" not in c})

    if st.toggle("Test what each filter adds (re-runs the backtest several times)", help=tip("ablation")):
        with st.spinner("Re-running variants…"):
            conf_p = dict(params[CONF])
            mkt_c = conf_p.pop("market", None)
            abl = swing.ablation(hist, conf_p, cost, rf, mkt_c)
        st.dataframe(abl, width="stretch", column_config={
            "Win rate": st.column_config.NumberColumn(format="percent", help=tip("Win rate")),
            "Expectancy (R)": st.column_config.NumberColumn(format="%.2f", help=tip("Expectancy (R)")),
            "Profit factor": st.column_config.NumberColumn(format="%.2f", help=tip("Profit factor")),
            "Avg win": st.column_config.NumberColumn(format="percent"), "Avg loss": st.column_config.NumberColumn(format="percent"),
            "Avg bars held": st.column_config.NumberColumn(format="%.1f"), "CAGR": st.column_config.NumberColumn(format="percent"),
        })
        st.caption("Look for filters that raise expectancy without cutting trades to a handful. Fewer than ~30 trades is too few to trust.")

with st.expander("How each strategy works"):
    for n in chosen:
        st.markdown(f"**{n}**: {backtest.STRATEGIES[n].description}")
st.caption("A single-stock backtest is one path of history; beware overfitting parameters to it.")
ui.disclaimer()
