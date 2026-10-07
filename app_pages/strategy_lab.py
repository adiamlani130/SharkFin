"""Strategy Lab: build a trading strategy from indicators, backtest it, compare ideas."""

import itertools

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from sharkfin import builder, data, swing, ui
from sharkfin.explain import tip

ui.header("Strategy Lab",
          "Pick a ready-made strategy or build your own from indicators, then see how it would have traded. "
          "Signals use the day's close and fill at the next open, and every trade pays costs.")

c1, c2, c3 = st.columns([3, 2, 2], vertical_alignment="bottom")
with c1:
    sym = ui.symbol_picker("lab")
period = c2.segmented_control("History", ["3y", "5y", "10y", "max"], default="10y", help=tip("history")) or "10y"
cost = c3.number_input("Trading cost per trade (bps)", 0.0, 100.0, 5.0, 1.0, help=tip("cost"))
if not sym:
    st.stop()

hist = data.history(sym, period)
if len(hist) < 260:
    st.error("Need at least a year of price history for this ticker.")
    st.stop()
mkt_df = data.market_history(period)
market = mkt_df["Close"] if not mkt_df.empty else None
rf = data.risk_free_rate()
START = 10_000

IND_KEYS = list(builder.INDICATORS)
RHS_KEYS = [builder.VALUE] + IND_KEYS
_ids = itertools.count(int(pd.Timestamp.now().timestamp() * 1000))


def _load(name: str):
    s = builder.template(name)
    for c in s["entry"] + s["exit"]:
        c["id"] = next(_ids)
    st.session_state.lab_strategy = s
    st.session_state.lab_ver = st.session_state.get("lab_ver", 0) + 1


if "lab_strategy" not in st.session_state:
    _load("MACD momentum")


def _add(kind: str):
    base = builder.C("RSI", "is below", value=30) if kind == "entry" else builder.C("RSI", "is above", value=70)
    st.session_state.lab_strategy[kind].append({**base, "id": next(_ids)})


def _remove(kind: str, cid: int):
    st.session_state.lab_strategy[kind] = [c for c in st.session_state.lab_strategy[kind] if c["id"] != cid]


def _value_step(key: str) -> float:
    return {"osc": 1.0, "pct": 1.0, "ratio": 0.1, "macd": 0.1, "price": 1.0}.get(builder.INDICATORS[key].kind, 1.0)


def condition_rows(kind: str):
    s = st.session_state.lab_strategy
    ver = st.session_state.lab_ver
    for c in s[kind]:
        k = f"{kind}{ver}_{c['id']}"
        row = st.container(key=f"sfrule-{k}").columns([2.4, 1.0, 1.7, 2.4, 1.1, 0.45], vertical_alignment="bottom",
                                                     gap="small")
        c["ind"] = row[0].selectbox("Indicator", IND_KEYS, index=IND_KEYS.index(c["ind"]), key=f"{k}_i",
                                    label_visibility="collapsed", help=builder.INDICATORS[c["ind"]].help)
        dn = builder.INDICATORS[c["ind"]].default_n
        if dn:
            c["n"] = row[1].number_input("Days", 2, 400, int(c.get("n") or dn), key=f"{k}_n_{c['ind']}",
                                         label_visibility="collapsed", help="Length in days")
        else:
            c["n"] = None
        c["op"] = row[2].selectbox("Condition", builder.OPS, index=builder.OPS.index(c["op"]), key=f"{k}_o",
                                   label_visibility="collapsed")
        if c["op"] in builder.UNARY:
            c["lookback"] = row[3].number_input("vs days ago", 1, 100, int(c.get("lookback") or 5), key=f"{k}_lb",
                                                label_visibility="collapsed", help="Compared with its value this many days ago.")
        else:
            rhs = c.get("rhs", builder.VALUE)
            c["rhs"] = row[3].selectbox("Compared with", RHS_KEYS, index=RHS_KEYS.index(rhs), key=f"{k}_r",
                                        label_visibility="collapsed",
                                        format_func=lambda x: "a number" if x == builder.VALUE else x)
            if c["rhs"] == builder.VALUE:
                c["value"] = row[4].number_input("Value", value=float(c.get("value", 0.0)), step=_value_step(c["ind"]),
                                                 key=f"{k}_v_{c['ind']}", label_visibility="collapsed", format="%g")
            elif builder.INDICATORS[c["rhs"]].default_n:
                rn = c.get("rn") or builder.INDICATORS[c["rhs"]].default_n
                c["rn"] = row[4].number_input("Days", 2, 400, int(rn), key=f"{k}_rn_{c['rhs']}",
                                              label_visibility="collapsed", help="Length in days")
            else:
                c["rn"] = None
        row[5].button("", icon=":material/close:", key=f"{k}_x", on_click=_remove, args=(kind, c["id"]),
                      help="Remove this rule", type="tertiary")


# ---------------------------------------------------------------------------
tabs = st.tabs(["Build and test", "Compare strategies", "Swing system"])

def build_tab():
    names = list(builder.TEMPLATES)
    t1, t2 = st.columns([2, 5], vertical_alignment="bottom")
    pick = t1.selectbox("Start from", names, index=None, placeholder="Load a ready-made strategy…", key="lab_tpl",
                        on_change=lambda: _load(st.session_state.lab_tpl) if st.session_state.lab_tpl else None)
    if pick:
        t2.caption(builder.TEMPLATES[pick]["about"])
    s = st.session_state.lab_strategy

    b, x = st.container(border=True), st.container(border=True)
    with b:
        st.markdown("**Buy when**")
        s["logic"] = "ALL" if st.radio("Combine buy rules", ["all of these are true", "any of these is true"],
                                       index=0 if s.get("logic", "ALL") == "ALL" else 1, horizontal=True,
                                       key=f"logic{st.session_state.lab_ver}", label_visibility="collapsed"
                                       ).startswith("all") else "ANY"
        condition_rows("entry")
        st.button("Add a buy rule", icon=":material/add:", on_click=_add, args=("entry",), type="tertiary")
        s["market_filter"] = st.toggle("Only buy while the S&P 500 is above its 200-day average",
                                       s.get("market_filter", False), key=f"mf{st.session_state.lab_ver}",
                                       help="A market-trend filter. It keeps you out of most bear markets, at the cost of some late entries.")
    with x:
        st.markdown("**Sell when any of these happens**")
        condition_rows("exit")
        st.button("Add a sell rule", icon=":material/add:", on_click=_add, args=("exit",), type="tertiary")
        v = st.session_state.lab_ver
        r = st.container(key=f"sfrule-risk{v}").columns(4)
        s["stop"] = r[0].number_input("Stop loss %", 0.0, 50.0, float(s.get("stop") or 0), 1.0, key=f"stop{v}",
                                      help="Sell if price falls this far below the entry. 0 = off.")
        s["trail"] = r[1].number_input("Trailing stop %", 0.0, 50.0, float(s.get("trail") or 0), 1.0, key=f"trail{v}",
                                       help="Sell if price falls this far from its highest close since entry. 0 = off.")
        s["target"] = r[2].number_input("Take profit %", 0.0, 500.0, float(s.get("target") or 0), 5.0, key=f"tgt{v}",
                                        help="Sell when price rises this far above the entry. 0 = off.")
        s["max_days"] = r[3].number_input("Max days held", 0, 1000, int(s.get("max_days") or 0), 5, key=f"md{v}",
                                          help="Sell after this many trading days. 0 = no limit.")

    if not s["entry"]:
        st.info("Add at least one buy rule.")
        return
    try:
        res = builder.run(hist, s, cost, rf, market)
    except ValueError as e:
        st.warning(f"{e} Try a longer history or shorter indicator lengths.")
        return
    stt = res["stats"]
    buy_txt, sell_txt = builder.describe_strategy(s)

    end_val, bh_val = START * (1 + stt["Total return"]), START * (1 + stt["Buy & hold return"])
    beat = stt["Return per year"] > stt["Buy & hold per year"]
    smoother = stt["Sharpe"] > stt["Buy & hold Sharpe"]
    if stt["Trades"] == 0:
        verdict, cls = "These rules never triggered a buy over this period. Loosen a rule or pick a longer history.", ""
    else:
        verdict = ("It beat buying and holding." if beat else
                   "It earned less than buying and holding, but with a smoother ride (more return per unit of risk)."
                   if smoother else "Simply buying and holding did better on both return and risk.")
        cls = "buy" if beat or smoother else "sell"
        if stt["Trades"] < 10:
            verdict += (f" Only {stt['Trades']} trade{'s' if stt['Trades'] > 1 else ''}, though: "
                        "too few to tell skill from luck.")
    st.markdown(
        f"<div class='sf-card {cls}'><div class='t'>${end_val:,.0f} from ${START:,} over {stt['Years']:.1f} years</div>"
        f"<div class='row'><b>Buys when</b> {ui.h(buy_txt)}.</div><div class='row'><b>Sells when</b> {ui.h(sell_txt)}.</div>"
        f"<div class='row'>That is {ui.fmt_pct(stt['Return per year'], 1)} a year; buying and holding {sym} turned "
        f"${START:,} into ${bh_val:,.0f} ({ui.fmt_pct(stt['Buy & hold per year'], 1)} a year). "
        f"{ui.h(verdict)}</div></div>".replace("$", "&#36;"), unsafe_allow_html=True)

    ui.metrics([
        {"label": "Return per year", "value": ui.fmt_pct(stt["Return per year"], 1),
         "delta": f"{(stt['Return per year'] - stt['Buy & hold per year']) * 100:+.1f} pts vs buy & hold",
         "help": "Compound annual return, after costs, with idle cash earning the risk-free rate."},
        {"label": "Worst drop", "value": ui.fmt_pct(stt["Worst drop"], 0),
         "delta": f"buy & hold {ui.fmt_pct(stt['Buy & hold worst drop'], 0)}", "delta_color": "off", "delta_arrow": "off",
         "help": "Largest fall from a peak in the strategy's account value."},
        {"label": "Trades", "value": f"{stt['Trades']}",
         "delta": f"avg {stt['Avg days held']:.0f} days" if np.isfinite(stt["Avg days held"]) else None,
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Winning trades", "value": ui.fmt_pct(stt["Win rate"], 0),
         "delta": (f"avg win {ui.fmt_pct(stt['Avg win'], 1)}, loss {ui.fmt_pct(stt['Avg loss'], 1)}"
                   if np.isfinite(stt["Avg win"]) and np.isfinite(stt["Avg loss"]) else None),
         "delta_color": "off", "delta_arrow": "off", "help": tip("Win rate")},
        {"label": "Time in market", "value": ui.fmt_pct(stt["Time in market"], 0),
         "help": "Share of days holding the stock. The rest of the time the money sits in cash earning interest."},
        {"label": "Sharpe ratio", "value": ui.fmt_num(stt["Sharpe"]),
         "delta": f"buy & hold {ui.fmt_num(stt['Buy & hold Sharpe'])}", "delta_color": "off", "delta_arrow": "off",
         "help": tip("Sharpe")},
    ], key="labm", cols=6)
    if res["open_trade"]:
        ot = res["open_trade"]
        st.caption(f"Currently in a trade: bought {ot['Entry date']:%b %d, %Y} at ${ot['Entry']:,.2f}, "
                   f"{ui.fmt_pct(ot['Return'], 1, True)} so far.".replace("$", "\\$"))

    # Price chart with the indicators the rules use and the trades.
    used = []
    for c in s["entry"] + s["exit"]:
        for k_, n_ in ((c["ind"], c.get("n")), (c.get("rhs"), c.get("rn"))):
            if k_ and k_ != builder.VALUE and (k_, n_) not in used:
                used.append((k_, n_))
    price_ind = [(k_, n_) for k_, n_ in used if builder.INDICATORS[k_].kind == "price" and k_ != "Price"]
    lower = [(k_, n_) for k_, n_ in used if builder.INDICATORS[k_].kind != "price"]
    lower_kind = builder.INDICATORS[lower[0][0]].kind if lower else None
    lower = [(k_, n_) for k_, n_ in lower if builder.INDICATORS[k_].kind == lower_kind]
    view = hist.loc[res["equity"].index[0]:]
    fig = make_subplots(rows=2 if lower else 1, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28] if lower else [1],
                        vertical_spacing=0.04)
    fig.add_scatter(x=view.index, y=view["Close"], name=sym, line=dict(color="#c9d1dc", width=1.3), row=1, col=1)
    palette = [ui.BLUE, ui.ORANGE, ui.PURPLE, "#f472b6", "#facc15"]
    for (k_, n_), col in zip(price_ind, palette):
        fig.add_scatter(x=view.index, y=builder.series(hist, k_, n_, market).loc[view.index], name=builder.label(k_, n_),
                        line=dict(width=1.1, color=col), row=1, col=1)
    tr = res["trades"]
    if not tr.empty:
        fig.add_scatter(x=tr["Entry date"], y=tr["Entry"], mode="markers", name="Buy",
                        marker=dict(symbol="triangle-up", size=10, color=ui.GREEN, line=dict(width=0)), row=1, col=1)
        fig.add_scatter(x=tr["Exit date"], y=tr["Exit"], mode="markers", name="Sell", text=tr["Exit reason"],
                        hovertemplate="%{text}: $%{y:.2f}<extra></extra>",
                        marker=dict(symbol="triangle-down", size=10, color=ui.RED, line=dict(width=0)), row=1, col=1)
    if res["open_trade"]:
        fig.add_scatter(x=[res["open_trade"]["Entry date"]], y=[res["open_trade"]["Entry"]], mode="markers", name="Open trade",
                        marker=dict(symbol="triangle-up", size=12, color=ui.GREEN, line=dict(width=2, color="#fff")))
    for (k_, n_), col in zip(lower, palette[::-1]):
        fig.add_scatter(x=view.index, y=builder.series(hist, k_, n_, market).loc[view.index], name=builder.label(k_, n_),
                        line=dict(width=1.1, color=col), row=2, col=1)
    if lower:
        for c in s["entry"] + s["exit"]:
            if c.get("rhs") == builder.VALUE and builder.INDICATORS[c["ind"]].kind == lower_kind and c["op"] not in builder.UNARY:
                fig.add_hline(y=c["value"], line=dict(color=ui.MUTED, dash="dot", width=1), row=2, col=1)
    span_start = max(view.index[0], view.index[-1] - pd.DateOffset(years=2))
    fig.update_xaxes(range=[span_start, view.index[-1]])
    vis = view["Close"].loc[span_start:]
    fig.update_yaxes(range=[vis.min() * 0.93, vis.max() * 1.05], row=1, col=1)
    fig.update_xaxes(rangeselector=dict(buttons=[dict(count=1, label="1y", step="year", stepmode="backward"),
                                                 dict(count=2, label="2y", step="year", stepmode="backward"),
                                                 dict(count=5, label="5y", step="year", stepmode="backward"),
                                                 dict(step="all", label="All")],
                                        bgcolor="#121822", activecolor="#1f2836", font=dict(size=11), y=1.02, x=1,
                                        xanchor="right"), row=1, col=1)
    fig.update_layout(title=f"{sym}: every buy and sell", hovermode="x unified")
    ui.plotly(fig, 520 if lower else 440)

    eq = pd.DataFrame({"Strategy": res["equity"] * START, f"Buy & hold {sym}": res["bh_equity"] * START})
    fig = go.Figure([go.Scatter(x=eq.index, y=eq["Strategy"], name="Your strategy", line=dict(color=ui.GREEN, width=2)),
                     go.Scatter(x=eq.index, y=eq.iloc[:, 1], name=f"Buy & hold {sym}", line=dict(color=ui.MUTED, width=1.4))])
    fig.update_layout(title=f"What ${START:,} became", yaxis_type="log", yaxis_tickprefix="$", hovermode="x unified")
    ui.plotly(fig, 360)

    with st.expander(f"Every trade ({len(tr)})"):
        if tr.empty:
            st.caption("No completed trades.")
        else:
            st.dataframe(tr.iloc[::-1], hide_index=True, width="stretch", column_config={
                "Entry date": st.column_config.DateColumn("Bought", format="MMM D, YYYY"),
                "Exit date": st.column_config.DateColumn("Sold", format="MMM D, YYYY"),
                "Entry": st.column_config.NumberColumn("Buy price", format="$%.2f"),
                "Exit": st.column_config.NumberColumn("Sell price", format="$%.2f"),
                "Return": st.column_config.NumberColumn(format="percent"), "Days": st.column_config.NumberColumn("Days held"),
                "Exit reason": "Why it sold"})
    with st.expander("Full statistics"):
        rows = [("Total return", stt["Total return"], stt["Buy & hold return"], "pct"),
                ("Return per year", stt["Return per year"], stt["Buy & hold per year"], "pct"),
                ("Worst drop", stt["Worst drop"], stt["Buy & hold worst drop"], "pct"),
                ("Sharpe ratio", stt["Sharpe"], stt["Buy & hold Sharpe"], "num"),
                ("Sortino ratio", stt["Sortino"], np.nan, "num"), ("Volatility", stt["Volatility"], np.nan, "pct"),
                ("Profit factor", stt["Profit factor"], np.nan, "num"), ("Time in market", stt["Time in market"], 1.0, "pct")]
        f = lambda v, k: "—" if not np.isfinite(v) else (ui.fmt_pct(v, 1) if k == "pct" else ui.fmt_num(v))
        st.dataframe(pd.DataFrame([{"": n, "Strategy": f(a, k), "Buy & hold": f(b_, k)} for n, a, b_, k in rows]),
                     hide_index=True, width="stretch")
        st.caption("Profit factor = total gains on winning trades divided by total losses on losing ones. Above 1.5 is good.")

    with st.expander("Does it work on other stocks?"):
        st.caption("A rule that only works on one stock is probably luck. Run the same rules on a few others.")
        others = st.text_input("Tickers (comma separated)", "SPY, QQQ, MSFT, NVDA, JPM, XOM, KO", key="lab_multi")
        if st.button("Run on these tickers"):
            out = []
            with st.spinner("Backtesting…"):
                for t in [t.strip().upper() for t in others.split(",") if t.strip()][:15]:
                    h_ = data.history(t, period)
                    try:
                        r_ = builder.run(h_, s, cost, rf, market)["stats"]
                    except (ValueError, KeyError):
                        continue
                    out.append({"Ticker": t, "Strategy / yr": r_["Return per year"], "Buy & hold / yr": r_["Buy & hold per year"],
                                "Worst drop": r_["Worst drop"], "B&H worst drop": r_["Buy & hold worst drop"],
                                "Trades": r_["Trades"], "Winning trades": r_["Win rate"],
                                "Beat B&H": "Yes" if r_["Return per year"] > r_["Buy & hold per year"] else "No"})
            if out:
                odf = pd.DataFrame(out)
                st.dataframe(odf, hide_index=True, width="stretch", column_config={
                    c: st.column_config.NumberColumn(format="percent") for c in
                    ("Strategy / yr", "Buy & hold / yr", "Worst drop", "B&H worst drop", "Winning trades")})
                st.caption(f"Beat buy-and-hold on {(odf['Beat B&H'] == 'Yes').sum()} of {len(odf)} tickers.")
            else:
                st.info("Couldn't load any of those tickers.")


with tabs[0]:
    build_tab()

# ---------------------------------------------------------------------------
with tabs[1]:
    st.caption("Every ready-made strategy on the same stock and the same dates, side by side.")
    chosen = st.multiselect("Strategies", list(builder.TEMPLATES)[:-1],
                            default=["Above the 200-day", "Golden cross", "MACD momentum", "55-day breakout",
                                     "RSI dip in an uptrend"])
    if chosen:
        runs = builder.compare_templates(hist, chosen, cost, rf, market)
        first = next(iter(runs.values()))
        fig = go.Figure(go.Scatter(x=first["bh_equity"].index, y=first["bh_equity"] * START, name=f"Buy & hold {sym}",
                                   line=dict(color=ui.MUTED, width=2, dash="dot")))
        for n, r_ in runs.items():
            fig.add_scatter(x=r_["equity"].index, y=r_["equity"] * START, name=n, line=dict(width=1.5))
        fig.update_layout(title=f"What ${START:,} became in {sym}", yaxis_type="log", yaxis_tickprefix="$", hovermode="x unified")
        ui.plotly(fig, 440)
        rows = [{"Strategy": f"Buy & hold {sym}", "Per year": first["stats"]["Buy & hold per year"],
                 "Worst drop": first["stats"]["Buy & hold worst drop"], "Sharpe": first["stats"]["Buy & hold Sharpe"],
                 "Trades": np.nan, "Winning trades": np.nan, "Time in market": 1.0}]
        rows += [{"Strategy": n, "Per year": r_["stats"]["Return per year"], "Worst drop": r_["stats"]["Worst drop"],
                  "Sharpe": r_["stats"]["Sharpe"], "Trades": r_["stats"]["Trades"], "Winning trades": r_["stats"]["Win rate"],
                  "Time in market": r_["stats"]["Time in market"]} for n, r_ in runs.items()]
        cdf = pd.DataFrame(rows).sort_values("Sharpe", ascending=False)
        st.dataframe(cdf, hide_index=True, width="stretch", column_config={
            "Per year": st.column_config.NumberColumn(format="percent", help="Compound annual return after costs."),
            "Worst drop": st.column_config.NumberColumn(format="percent"),
            "Sharpe": st.column_config.NumberColumn(format="%.2f", help=tip("Sharpe")),
            "Trades": st.column_config.NumberColumn(format="%d"),
            "Winning trades": st.column_config.NumberColumn(format="percent"),
            "Time in market": st.column_config.NumberColumn(format="percent")})
        best = cdf.iloc[0]["Strategy"]
        st.caption(f"Sorted by Sharpe ratio (return per unit of risk). Best here: {best}. Load any of them in "
                   "Build and test to tweak the rules.")

# ---------------------------------------------------------------------------
with tabs[2]:
    st.markdown("<div class='sf-note'>SharkFin's own swing-trading system, the same one behind <b>Trade setup</b> on "
                "Research &amp; Valuation: in an uptrend, buy a pullback to the 20-day or 50-day average once price "
                "turns back up and enough signals agree. It sells part at the first target and trails the rest.</div>",
                unsafe_allow_html=True)
    with st.expander("Settings"):
        st.caption("Must-pass rules all have to be true. Point rules each add 1 to the score; a trade needs the minimum score.")
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
            "t1_r": q[2].number_input("First target (R)", 0.5, 5.0, 1.5, 0.25, help=tip("t1_r")),
            "t2_r": q[3].number_input("Second target (R, 0 = none)", 0.0, 10.0, 3.0, 0.5, help=tip("t2_r")),
            "t1_fraction": q[0].slider("Sell at first target", 0.25, 1.0, 0.5, 0.25, format="%.2f", help=tip("t1_fraction")),
            "max_hold": q[1].number_input("Max days in trade", 5, 250, 40, help=tip("max_hold")),
            "flow": q[2].radio("Volume-flow line", ["OBV", "VPT"], horizontal=True, help=tip("flow")),
        }
        e = st.columns(4)
        conf["trail"] = e[0].toggle("Trail under 20 EMA after T1", True, help=tip("trail"))
        conf["exit_below_50"] = e[1].toggle("Exit on close below 50-day", True, help=tip("exit_below_50"))
        conf["divergence_tighten"] = e[2].toggle("RSI divergence tightens stop", True, help=tip("divergence"))
        conf["rsi_fade_partial"] = e[3].toggle("RSI over 70 takes partial", True, help=tip("rsi_fade"))

    res = swing.backtest(hist, conf, cost, rf, market)
    ts, trades = res["trade_stats"], res["trades"]
    eq_s = res["equity"]
    bh = hist["Close"].loc[eq_s.index[0]:] / hist["Close"].loc[eq_s.index[0]]
    ui.metrics([
        {"label": "Trades", "value": f"{ts['Trades']}", "help": tip("Trades")},
        {"label": "Winning trades", "value": ui.fmt_pct(ts["Win rate"], 0), "help": tip("Win rate")},
        {"label": "Avg result per trade", "value": f"{ts['Expectancy (R)']:+.2f}R" if np.isfinite(ts["Expectancy (R)"]) else None,
         "help": tip("Expectancy (R)")},
        {"label": "Profit factor", "value": ui.fmt_num(ts["Profit factor"]), "help": tip("Profit factor")},
        {"label": "Return per year", "value": ui.fmt_pct(res["stats"].get("CAGR"), 1),
         "help": "Compound annual return of the account, after costs."},
        {"label": "Avg days held", "value": ui.fmt_num(ts["Avg bars held"], 1), "help": tip("Avg bars held")},
    ], key="swm", cols=6)
    st.caption("R = the amount risked on a trade (entry minus stop). +0.30R per trade means you made 30% of your risk "
               "on average, across winners and losers.")
    if trades.empty:
        st.info("No trades triggered with these settings. Try lowering the minimum score or switching a must-pass rule off.")
    else:
        view = hist.iloc[-504:]
        rules = res["rules"].reindex(view.index)
        fig = go.Figure(go.Candlestick(x=view.index, open=view["Open"], high=view["High"], low=view["Low"], close=view["Close"],
                                       name=sym, increasing_line_color=ui.GREEN, decreasing_line_color=ui.RED))
        for col, nm in (("ema20", "EMA 20"), ("sma50", "SMA 50"), ("sma200", "SMA 200")):
            fig.add_scatter(x=view.index, y=rules[col], name=nm, line=dict(width=1.1, color=ui.MA_COLORS.get(nm)))
        tv = trades[trades["Entry date"] >= view.index[0]]
        fig.add_scatter(x=tv["Entry date"], y=tv["Entry"], mode="markers", name="Buy",
                        marker=dict(symbol="triangle-up", size=11, color=ui.GREEN))
        tc = tv.dropna(subset=["Exit date"])
        fig.add_scatter(x=tc["Exit date"], y=tc["Avg exit"], mode="markers", name="Sell",
                        marker=dict(symbol="triangle-down", size=11, color=np.where(tc["Return"] > 0, ui.BLUE, ui.RED)),
                        text=tc["Exit reason"], hovertemplate="%{text}: $%{y:.2f}<extra></extra>")
        fig.update_layout(title="Last 2 years: buys and sells", xaxis_rangeslider_visible=False, hovermode="x unified")
        ui.plotly(fig, 460)

        fig = go.Figure([go.Scatter(x=eq_s.index, y=eq_s * START, name="Swing system", line=dict(color=ui.GREEN, width=2)),
                         go.Scatter(x=bh.index, y=bh * START, name=f"Buy & hold {sym}", line=dict(color=ui.MUTED, width=1.4))])
        fig.update_layout(title=f"What ${START:,} became", yaxis_type="log", yaxis_tickprefix="$", hovermode="x unified")
        ui.plotly(fig, 320)

        with st.expander(f"Every trade ({len(trades)})"):
            show = trades.drop(columns=[k for k in swing.RULES if k in trades]).iloc[::-1]
            st.dataframe(show, hide_index=True, width="stretch", height=320, column_config={
                "Entry date": st.column_config.DateColumn("Bought", format="MMM D, YYYY"),
                "Exit date": st.column_config.DateColumn("Sold", format="MMM D, YYYY"),
                "Entry": st.column_config.NumberColumn(format="$%.2f"), "Stop": st.column_config.NumberColumn(format="$%.2f"),
                "Risk ($)": st.column_config.NumberColumn(format="$%.2f", help=tip("risk_r")),
                "Avg exit": st.column_config.NumberColumn(format="$%.2f"),
                "Return": st.column_config.NumberColumn(format="percent"),
                "R multiple": st.column_config.NumberColumn(format="%.2f", help=tip("R multiple")),
                "Score": st.column_config.NumberColumn(help="How many point rules passed on the signal day."),
            })
        with st.expander("Which rules actually help"):
            rep = swing.rule_report(trades)
            if not rep.empty:
                st.caption("Trades where each point rule was on, versus off.")
                st.dataframe(rep, width="stretch", column_config={
                    c: st.column_config.NumberColumn(format="percent" if "Win" in c else "%.2f") for c in rep.columns
                    if "Trades" not in c})
            if st.toggle("Test what each filter adds (re-runs the backtest several times)", help=tip("ablation")):
                with st.spinner("Re-running variants…"):
                    abl = swing.ablation(hist, conf, cost, rf, market)
                st.dataframe(abl, width="stretch", column_config={
                    "Win rate": st.column_config.NumberColumn(format="percent", help=tip("Win rate")),
                    "Expectancy (R)": st.column_config.NumberColumn(format="%.2f", help=tip("Expectancy (R)")),
                    "Profit factor": st.column_config.NumberColumn(format="%.2f", help=tip("Profit factor")),
                    "Avg win": st.column_config.NumberColumn(format="percent"),
                    "Avg loss": st.column_config.NumberColumn(format="percent"),
                    "Avg bars held": st.column_config.NumberColumn(format="%.1f"),
                    "CAGR": st.column_config.NumberColumn(format="percent"),
                })
                st.caption("Look for filters that raise the average result without cutting trades to a handful. "
                           "Fewer than about 30 trades is too few to trust.")

st.caption("A backtest on one stock is one path of history. Rules tuned until they look perfect on the past usually "
           "disappoint in the future, so check them on other stocks too.")
ui.disclaimer()
