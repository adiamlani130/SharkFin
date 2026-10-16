"""Strategy Lab: build a trading strategy from indicators, backtest it, compare ideas."""

import itertools
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from sharkfin import builder, data, leader_dip, live, swing, ui
from sharkfin.explain import tip

ui.header("Strategy Lab",
          "Pick a ready-made strategy or build your own from indicators, then see how it would have traded. "
          "Signals use the day's close and fill at the next open, and every trade pays costs.")

c1, c2, c3 = st.columns([3, 2, 2], vertical_alignment="bottom")
with c1:
    sym = ui.symbol_picker("lab")
period = c2.segmented_control("History", ["5y", "10y", "max"], default="10y", help=tip("history")) or "10y"
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


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def lab_walk_forward(ticker: str, period_: str, rules_json: str, cost_bps: float, rf_: float) -> dict:
    """Walk-forward test of one rule set on one ticker (cached by its rules)."""
    h_ = data.history(ticker, period_)
    if len(h_) < 260:
        raise ValueError(f"Not enough price history for {ticker}.")
    m_ = data.market_history(period_)
    return builder.walk_forward(h_, json.loads(rules_json), cost_bps, rf_, m_["Close"] if not m_.empty else None)


def rules_key(s_: dict) -> str:
    return json.dumps(s_, sort_keys=True, default=float)


def split_open_trade(wf: dict, last_day) -> tuple[pd.DataFrame, dict | None]:
    """The walk-forward's trades, with a position still held on the last day split out as the open trade."""
    tr = wf["trades"]
    if len(tr) and tr.iloc[-1]["Exit reason"] == "End of test window" and tr.iloc[-1]["Exit date"] == last_day:
        last = tr.iloc[-1]
        return tr.iloc[:-1], {"Entry date": last["Entry date"], "Entry": last["Entry"], "Return": last["Exit"] / last["Entry"] - 1}
    return tr, None
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
tabs = st.tabs(["Build and test", "Compare strategies", "Leader Dip Plus 7 (S&P 500)"])

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
        with st.spinner("Picking the rule's numbers year by year, then trading each next year…"):
            res = lab_walk_forward(sym, period, rules_key(s), float(cost), float(rf))
    except ValueError as e:
        st.warning(f"{e} Pick a longer history or shorter indicator lengths.")
        return
    stt = res["stats"]
    tr, open_trade = split_open_trade(res, hist.index[-1])
    stt["Trades"] = int(len(tr))
    buy_txt, sell_txt = builder.describe_strategy(s)
    u1, u2 = st.columns([2, 5], vertical_alignment="center")
    if u1.button("Use as my swing strategy", icon=":material/bookmark_add:",
                 help="Top Performers → Swing setups and Research → Trade setup will use these rules instead of "
                      "Leader Dip. Switch back any time from the Swing strategy box on either page."):
        if ui.save_my_swing_rules(swing.clean(s)):
            ui.set_swing_choice(swing.MINE)
            st.toast("Saved. Top Performers and Research now use these rules for swing trades.")
        else:
            st.toast("Couldn't save the rules on the server.")
    current = ui.swing_choice()
    u2.caption(f"Swing strategy used across the app: **{current}**.")

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
        f"<div class='sf-card {cls}'><div class='t'>${end_val:,.0f} from ${START:,} over {stt['Years']:.1f} "
        f"out-of-sample years</div>"
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
    tuned_txt = (f"Tuned each year from 80-120% of your numbers: {', '.join(res['knobs'])}." if res["knobs"]
                 else "No numbers to tune, so your rules ran as set in every test year.")
    ui.walk_forward_table(res, "lab_wf", tuned_txt)
    if open_trade:
        ot = open_trade
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
    if not tr.empty:
        fig.add_scatter(x=tr["Entry date"], y=tr["Entry"], mode="markers", name="Buy",
                        marker=dict(symbol="triangle-up", size=10, color=ui.GREEN, line=dict(width=0)), row=1, col=1)
        fig.add_scatter(x=tr["Exit date"], y=tr["Exit"], mode="markers", name="Sell", text=tr["Exit reason"],
                        hovertemplate="%{text}: $%{y:.2f}<extra></extra>",
                        marker=dict(symbol="triangle-down", size=10, color=ui.RED, line=dict(width=0)), row=1, col=1)
    if open_trade:
        fig.add_scatter(x=[open_trade["Entry date"]], y=[open_trade["Entry"]], mode="markers", name="Open trade",
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
                                        bgcolor=ui.PANEL, activecolor=ui.BORDER, font=dict(size=11), y=1.02, x=1,
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
            with st.spinner("Walking the rules forward on each ticker…"):
                for t in [t.strip().upper() for t in others.split(",") if t.strip()][:15]:
                    try:
                        r_ = lab_walk_forward(t, period, rules_key(s), float(cost), float(rf))["stats"]
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
        runs = {}
        with st.spinner("Walking each strategy forward…"):
            for n in chosen:
                try:
                    runs[n] = lab_walk_forward(sym, period, rules_key(builder.template(n)), float(cost), float(rf))
                except ValueError:
                    pass
        if not runs:
            st.warning("Not enough history for a walk-forward test of these strategies. Pick a longer history.")
            st.stop()
        common = max(r_["equity"].index[0] for r_ in runs.values())
        for r_ in runs.values():  # same test days for every line, so the curves compare fairly
            for k in ("equity", "bh_equity"):
                e = r_[k].loc[common:]
                r_[k] = e / e.iloc[0]
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
                   "Build and test to tweak the rules. " + ui.WALK_FORWARD_NOTE)

# ---------------------------------------------------------------------------
@st.cache_data(ttl=12 * 3600, show_spinner=False)
def leader_dip_run(universe: str, years: str, cash: str, slots: int, cost_bps: float, rules: str = "plus") -> dict:
    point_in_time = universe == "S&P 500"
    start = pd.Timestamp.now().normalize() - pd.DateOffset(years=int(years.rstrip("y")))
    syms_ = tuple(data.sp500_ever(start) if point_in_time else data.universe(universe))
    ohlcv = data.download_ohlcv(syms_, period=years)
    if "Close" not in ohlcv or ohlcv["Close"].shape[1] < 10:
        raise ValueError("Couldn't download prices for the index right now.")
    mkt = data.market_history(years)
    if mkt.empty:
        raise ValueError("Couldn't download SPY, which the market switch needs.")
    m = live.market_inputs(years)
    members = data.sp500_members(ohlcv["Close"].index, ohlcv["Close"].columns) if point_in_time else None
    sr = leader_dip.sector_returns(ohlcv["Close"].index, ohlcv["Close"].columns, live.sector_map(), m["etf"])
    return leader_dip.walk_forward(ohlcv, mkt["Close"], cash=cash, tbill_yields=data.tbill_yields(years), slots=slots,
                                   cost_bps=cost_bps, rules=rules, vix=m["vix"] if len(m["vix"]) else None,
                                   sector_ret3=sr, members=members)


def leader_dip_tab():
    st.markdown(
        "<div class='sf-note'><b>Leader Dip Plus 7</b>, SharkFin's swing system, the one behind Top Performers and Trade "
        "setup. It buys a sharp two-day drop (2-day RSI under 10) in a stock that is above its 200-day average and among "
        "the 30% strongest in the S&amp;P 500 over 6 months, if it has at least one quality point (a deep dip, a stock "
        "well off its high, a sector selloff or VIX above 20), with a limit order 3% under the signal close. It sells at "
        "a profit target of the signal close + 1.5 ATR, or at the next open once the 2-day RSI closes above 70, the "
        "stock closes under its 200-day, or 10 days pass. It opens trades while SPY is above its 200-day or VIX is above "
        "25, holds 7 at a time, and parks idle cash in SPY. <b>Classic</b> is the original rules (10 slots, RSI exit "
        "only). Strategy Playbook explains why it works.</div>", unsafe_allow_html=True)
    q = st.columns(5)
    universe = q[0].selectbox("Stocks", ["S&P 500", "Nasdaq-100"], key="ld_uni")
    rules_label = q[1].selectbox("Rules", list(leader_dip.RULESETS), key="ld_rules")
    years = q[2].segmented_control("History", ["10y", "20y"], default="10y", key="ld_years") or "10y"
    cash_label = q[3].selectbox("Idle cash", list(leader_dip.CASH_CHOICES), index=0, key="ld_cash",
                                help=leader_dip.CASH_HELP)
    rules_key = leader_dip.RULESETS[rules_label]
    slots = q[4].slider("Slots", 3, 20, leader_dip.SLOTS if rules_key == "plus" else leader_dip.CLASSIC_SLOTS,
                        key=f"ld_slots_{rules_key}", help=tip("ld_slots"))
    st.caption(f"Costs: {cost:g} bps on each buy and each sell (set at the top of the page; the research used 10).")
    if not (st.button(f"Backtest Leader Dip on the {universe}", type="primary", key="ld_run")
            or st.session_state.get("ld_ran")):
        st.caption("Downloads daily prices for every stock in the index, so the first run takes a minute.")
        return
    st.session_state.ld_ran = True
    try:
        with st.spinner(f"Downloading the {universe}, then picking settings year by year…"):
            res = leader_dip_run(universe, years, leader_dip.CASH_CHOICES[cash_label], int(slots), float(cost), rules_key)
    except ValueError as e:
        st.warning(str(e))
        return
    stt, spy, bsk = res["stats"], res["spy_stats"], res["basket_stats"]
    end_val = START * (1 + stt["Total return"])
    st.markdown(
        f"<div class='sf-card {'buy' if stt['Sharpe'] > spy['Sharpe'] else ''}'><div class='t'>${end_val:,.0f} from "
        f"${START:,} over {stt['Years']:.1f} years</div><div class='row'>That is {ui.fmt_pct(stt['Return per year'], 1)} "
        f"a year with a worst drop of {ui.fmt_pct(stt['Worst drop'], 0)}. SPY did {ui.fmt_pct(spy['Return per year'], 1)} "
        f"a year (worst drop {ui.fmt_pct(spy['Worst drop'], 0)}) and an equal-weight basket of the same "
        f"{res['symbols']} stocks did {ui.fmt_pct(bsk['Return per year'], 1)}.</div></div>".replace("$", "&#36;"),
        unsafe_allow_html=True)
    ui.metrics([
        {"label": "Return per year", "value": ui.fmt_pct(stt["Return per year"], 1),
         "delta": f"{(stt['Return per year'] - spy['Return per year']) * 100:+.1f} pts vs SPY"},
        {"label": "Worst drop", "value": ui.fmt_pct(stt["Worst drop"], 0), "delta": f"SPY {ui.fmt_pct(spy['Worst drop'], 0)}",
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Sharpe ratio", "value": ui.fmt_num(stt["Sharpe"]), "delta": f"SPY {ui.fmt_num(spy['Sharpe'])}",
         "delta_color": "off", "delta_arrow": "off", "help": tip("Sharpe")},
        {"label": "Trades per year", "value": ui.fmt_num(stt["Trades per year"], 0),
         "delta": f"avg {stt['Avg days held']:.1f} days" if np.isfinite(stt["Avg days held"]) else None,
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Winning trades", "value": ui.fmt_pct(stt["Win rate"], 0), "help": tip("Win rate")},
        {"label": "Avg trade", "value": ui.fmt_pct(stt["Avg trade"], 2, True), "help": "Average return per trade after costs."},
    ], key="ldm", cols=6)

    eq = res["equity"] * START
    fig = go.Figure([go.Scatter(x=eq.index, y=eq, name=f"Leader Dip, idle cash in {cash_label.split(' while')[0]}",
                                line=dict(color=ui.GREEN, width=2)),
                     go.Scatter(x=eq.index, y=res["spy_equity"] * START, name="SPY", line=dict(color=ui.MUTED, width=1.4)),
                     go.Scatter(x=eq.index, y=res["basket_equity"] * START, name=f"Equal-weight {universe}",
                                line=dict(color=ui.BLUE, width=1.2, dash="dot"))])
    fig.update_layout(title=f"What ${START:,} became", yaxis_type="log", yaxis_tickprefix="$", hovermode="x unified")
    ui.plotly(fig, 380)
    expo = res["exposure"].rolling(21).mean()
    fig = go.Figure(go.Scatter(x=expo.index, y=expo * 100, fill="tozeroy", line=dict(color=ui.BLUE, width=1),
                               name="Invested in trades"))
    fig.update_layout(title="Share of the account in Leader Dip trades (1-month average)", yaxis=dict(ticksuffix="%", range=[0, 100]))
    ui.plotly(fig, 220)

    ui.walk_forward_table(res, "ld_wf")
    tr = res["trades"]
    mine = tr[tr["Symbol"] == sym] if len(tr) else tr
    if len(mine):
        st.caption(f"{sym} was traded {len(mine)} times in this backtest; those trades are marked below.")
        view = hist.loc[max(hist.index[0], res["equity"].index[0]):]
        fig = go.Figure(go.Scatter(x=view.index, y=view["Close"], name=sym, line=dict(color="#c9d1dc", width=1.3)))
        fig.add_scatter(x=mine["Bought"], y=mine["Buy price"], mode="markers", name="Buy",
                        marker=dict(symbol="triangle-up", size=10, color=ui.GREEN))
        done = mine.dropna(subset=["Sold"])
        fig.add_scatter(x=done["Sold"], y=done["Sell price"], mode="markers", name="Sell", text=done["Why it sold"],
                        hovertemplate="%{text}: $%{y:.2f}<extra></extra>",
                        marker=dict(symbol="triangle-down", size=10, color=ui.RED))
        fig.update_layout(title=f"{sym}: Leader Dip buys and sells", hovermode="x unified")
        ui.plotly(fig, 360)
    with st.expander(f"Every trade ({len(tr)})"):
        st.dataframe(tr.iloc[::-1], hide_index=True, width="stretch", height=360, column_config={
            "Signal date": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Bought": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Sold": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Buy price": st.column_config.NumberColumn(format="$%.2f"),
            "Sell price": st.column_config.NumberColumn(format="$%.2f"),
            "Return": st.column_config.NumberColumn(format="percent")})
        by_year = tr.dropna(subset=["Sold"]).assign(Year=lambda d: pd.to_datetime(d["Bought"]).dt.year)
        yr = res["equity"].resample("YE").last().pct_change()
        yr.iloc[0] = res["equity"].resample("YE").last().iloc[0] / res["equity"].iloc[0] - 1
        spy_yr = res["spy_equity"].resample("YE").last().pct_change()
        spy_yr.iloc[0] = res["spy_equity"].resample("YE").last().iloc[0] / res["spy_equity"].iloc[0] - 1
        ytab = pd.DataFrame({"Leader Dip": yr.values, "SPY": spy_yr.values}, index=yr.index.year)
        ytab["Trades"] = by_year.groupby("Year").size().reindex(ytab.index).fillna(0).astype(int)
        st.markdown("**Year by year**")
        st.dataframe(ytab, width="stretch", column_config={
            "Leader Dip": st.column_config.NumberColumn(format="percent"), "SPY": st.column_config.NumberColumn(format="percent")})
    st.caption("S&P 500: stocks are only ranked and traded on days they were in the index. Yahoo no longer has prices "
               "for some that left (usually takeovers and failures), so a little survivorship bias remains. Nasdaq-100: "
               "SharkFin has no membership history for it, so it uses today's members and the results run high.")


with tabs[2]:
    leader_dip_tab()

st.caption("A backtest on one stock is one path of history. Rules tuned until they look perfect on the past usually "
           "disappoint in the future, so check them on other stocks too.")
ui.disclaimer()
