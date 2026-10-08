"""Strategy Lab: build a trading strategy from indicators, backtest it, compare ideas."""

import itertools

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from sharkfin import builder, data, leader_dip, ui
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
tabs = st.tabs(["Build and test", "Compare strategies", "Leader Dip (S&P 500)"])

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
@st.cache_data(ttl=12 * 3600, show_spinner=False)
def leader_dip_run(universe: str, years: str, cash: str, slots: int, cost_bps: float) -> dict:
    syms_ = tuple(data.universe(universe))
    ohlcv = data.download_ohlcv(syms_, period=years)
    if "Close" not in ohlcv or ohlcv["Close"].shape[1] < 10:
        raise ValueError("Couldn't download prices for the index right now.")
    mkt = data.market_history(years)
    if mkt.empty:
        raise ValueError("Couldn't download SPY, which the market switch needs.")
    return leader_dip.backtest(ohlcv, mkt["Close"], cash=cash, tbill_yields=data.tbill_yields(years), slots=slots,
                               cost_bps=cost_bps)


def leader_dip_tab():
    st.markdown(
        "<div class='sf-note'><b>Leader Dip</b>, SharkFin's swing system, the one behind Top Performers and Trade setup. "
        "It buys a sharp two-day drop (2-day RSI under 10) in a stock that is above its 200-day average and among the "
        "30% strongest in the S&amp;P 500 over 6 months, with a limit order 3% under the signal close. It sells at the "
        "next open once the 2-day RSI closes above 70, or after 10 days, with no stop loss, and only opens trades while "
        "SPY is above its 200-day. Because it picks from the whole index and fires only a few times a year on any one "
        "stock, it is tested as a portfolio of the index, not on the ticker above.</div>", unsafe_allow_html=True)
    q = st.columns(4)
    universe = q[0].selectbox("Stocks", ["S&P 500", "Nasdaq-100"], key="ld_uni")
    years = q[1].segmented_control("History", ["5y", "10y"], default="10y", key="ld_years") or "10y"
    cash_label = q[2].selectbox("Idle cash", list(leader_dip.CASH_CHOICES), index=1, key="ld_cash",
                                help=leader_dip.CASH_HELP)
    slots = q[3].slider("Slots", 5, 20, leader_dip.SLOTS, key="ld_slots", help=tip("ld_slots"))
    st.caption(f"Costs: {cost:g} bps on each buy and each sell (set at the top of the page; the research used 10).")
    if not (st.button(f"Backtest Leader Dip on the {universe}", type="primary", key="ld_run")
            or st.session_state.get("ld_ran")):
        st.caption("Downloads daily prices for every stock in the index, so the first run takes a minute.")
        return
    st.session_state.ld_ran = True
    try:
        with st.spinner(f"Downloading the {universe} and replaying every day…"):
            res = leader_dip_run(universe, years, leader_dip.CASH_CHOICES[cash_label], int(slots), float(cost))
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

    tr = res["trades"]
    mine = tr[tr["Symbol"] == sym]
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
    st.caption("This uses today's index members, so stocks that were dropped (often the big losers) are missing, which "
               "flatters a strength-based system like this one. SharkFin's research ran it on the members of each date: "
               "12.7% a year in 2013-26 with a 1.02 Sharpe, and the median of 576 nearby variants was 9.9% a year. "
               "Expect results closer to that than to a perfect-hindsight run.")


with tabs[2]:
    leader_dip_tab()

st.caption("A backtest on one stock is one path of history. Rules tuned until they look perfect on the past usually "
           "disappoint in the future, so check them on other stocks too.")
ui.disclaimer()
