"""Strategy Playbook: SharkFin's three researched strategies (Leader Dip Plus 7, Tech Breakout Rider, TQQQ Day + Night),
how each works and why, today's signals, and the plan that combines them."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from sharkfin import breakout_rider, data, day_night, leader_dip, live, playbook as pb, ui
from sharkfin.explain import tip

ui.header("Strategy Playbook",
          "SharkFin's three researched strategies, how each one works, why it has an edge, what can go wrong, and "
          "today's signals. The last view combines them into one plan.")

START = 10_000
LD, BR, DN, PLAN = pb.LD, pb.BR, pb.DN, "The combined plan"
VIEWS = [LD, BR, DN, PLAN]
SPY, QQQ = "S&P 500 (SPY)", "Nasdaq-100 (QQQ)"
TAGS = {LD: "Swing · days", BR: "Trend · weeks to months", DN: "Day + overnight · hours"}
BLURB = {
    LD: "Buys a sharp two-day selloff in one of the S&P 500's strongest stocks and sells into the bounce. Idle cash "
        "rides SPY.",
    BR: "Buys tech leaders breaking out to a new one-month high and rides the trend until it bends.",
    DN: "Two buy-only TQQQ trades that never overlap: a breakout during the day and a bounce bet overnight.",
    PLAN: "50% Leader Dip Plus 7, 20% Tech Breakout Rider, 30% TQQQ Day + Night, rebalanced monthly.",
}


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def research() -> pd.DataFrame:
    return pb.load()


d = research()
series = {k: pb.sleeve(d, k) for k in (LD, BR, DN, SPY, QQQ)}
series[PLAN] = pb.mix(d, pb.WEIGHTS)


def pct(x, digits=1, sign=False):
    return ui.fmt_pct(x, digits, sign) if x is not None and np.isfinite(x) else "—"


# ---- Overview cards ---------------------------------------------------------
def overview():
    cards = []
    for k in VIEWS:
        f = pb.FACTS["The plan" if k == PLAN else k]
        col = pb.COLORS["The plan" if k == PLAN else k]
        cards.append(
            f"<div class='sf-strat' style='--c:{col}'><div class='nm'>{ui.h(k)}</div>"
            f"<div class='tg'>{ui.h(TAGS.get(k, 'All three together'))}</div>"
            f"<div class='big'>{f['return']:.1%}<span> a year</span></div>"
            f"<div class='sub'>Sharpe {f['sharpe']:.2f} · worst drop {abs(f['worst']):.0%} · 2022 {f['y2022']:+.0%}</div>"
            f"<div class='bl'>{ui.h(BLURB[k])}</div></div>")
    st.markdown(f"<div class='sf-strats'>{''.join(cards)}</div>", unsafe_allow_html=True)
    st.caption("Last 5 years (Oct 2021 to Oct 2026) in SharkFin's research, after trading costs. The S&P 500 made "
               "13.9% a year with a 25% worst drop and lost 18% in 2022; the Nasdaq-100 made 16.5% with a 35% drop. "
               "Settings were picked on older data before this window was graded.")


def switch_strip():
    sw = live.switches()
    if not sw:
        return
    ld_, br_ = sw.get("leader_dip"), sw.get("breakout")
    bits = []
    if ld_:
        why = (f"SPY {ld_['gap']:+.1%} vs its 200-day" if ld_.get("gap") is not None and np.isfinite(ld_["gap"]) else "")
        if ld_.get("panic"):
            why += f", VIX {ld_['vix']:.0f} (panic: buying allowed)"
        bits.append(ui.pill(f"Leader Dip switch {'on' if ld_['on'] else 'off'}", "pos" if ld_["on"] else "neg") +
                    f"<span class='sf-muted'>{ui.h(why)} · idle cash in {ld_.get('idle') or 'T-bills'}</span>")
    if br_:
        bits.append(ui.pill(f"Tech switch {'on' if br_['on'] else 'off'}", "pos" if br_["on"] else "neg") +
                    f"<span class='sf-muted'>QQQ 21-day EMA {br_['gap']:+.1%} vs its 50-day</span>")
    st.markdown(f"<div class='sf-card'>{'<br>'.join(bits)}</div>", unsafe_allow_html=True)


overview()
view = st.segmented_control("Strategy", VIEWS, default=LD, key="pb_view", label_visibility="collapsed") or LD
switch_strip()


# ---- Shared pieces ----------------------------------------------------------
def kpis(name: str, key: str):
    f = pb.FACTS[name]
    spy = pb.FACTS[SPY]
    items = [
        {"label": "Return per year", "value": pct(f["return"]), "delta": f"{(f['return'] - spy['return']) * 100:+.1f} pts vs SPY",
         "help": "Compound yearly return over the last 5 years, after trading costs."},
        {"label": "Sharpe ratio", "value": f"{f['sharpe']:.2f}", "delta": f"SPY {spy['sharpe']:.2f}", "delta_color": "off",
         "delta_arrow": "off", "help": tip("Sharpe") + " Measured after T-bill interest."},
        {"label": "Worst drop", "value": pct(f["worst"], 0), "delta": f"SPY {spy['worst']:.0%}", "delta_color": "off",
         "delta_arrow": "off", "help": "The biggest fall from a high to a later low: the pain you'd have had to sit through."},
    ]
    if f.get("win") is not None:
        items += [
            {"label": "Win rate", "value": pct(f["win"], 0), "delta": f"{f['trades_yr']:.0f} trades a year", "delta_color": "off",
             "delta_arrow": "off", "help": tip("Win rate")},
            {"label": "Edge per trade", "value": pct(f["edge"], 1, True),
             "delta": f"wins {f['avg_win']:+.1%} · losses {f['avg_loss']:+.1%}", "delta_color": "off", "delta_arrow": "off",
             "help": "What the average trade made after costs."},
            {"label": "Risk : reward", "value": f"1 : {f['payoff']:.1f}", "delta": f"profit factor {f['pf']:.1f}",
             "delta_color": "off", "delta_arrow": "off",
             "help": "Average win divided by average loss. Profit factor = total won / total lost (1.5+ is solid)."},
        ]
    else:
        items.append({"label": "2022", "value": pct(f["y2022"], 1, True), "delta": f"SPY {spy['y2022']:+.1%}",
                      "delta_color": "off", "delta_arrow": "off", "help": "The 2022 tech bear market."})
    ui.metrics(items, key=key, cols=6 if len(items) == 6 else None)


def steps_card(title: str, steps: list[str]):
    lis = "".join(f"<li>{s}</li>" for s in steps)
    st.markdown(f"<div class='sf-card'><div class='t'>{title}</div><ol class='sf-steps'>{lis}</ol></div>",
                unsafe_allow_html=True)


def text_card(title: str, body: str, cls: str = ""):
    st.markdown(f"<div class='sf-card {cls}'><div class='t'>{title}</div><div class='row'>{body}</div></div>",
                unsafe_allow_html=True)


def research_charts(names: list[str], key: str, since: str = pb.GRADE[0]):
    g = pb.growth({k: series[k] for k in names}, since)
    fig = go.Figure()
    for k in names:
        bench = k in (SPY, QQQ)
        fig.add_scatter(x=g.index, y=g[k], name=k, line=dict(color=pb.COLORS.get(k, ui.MUTED), width=1.4 if bench else 2.2,
                                                                dash="dot" if bench else None))
    fig.update_layout(title=f"What ${START:,} became (research backtest, from {pd.Timestamp(since):%b %Y})",
                      yaxis_tickprefix="$", hovermode="x unified")
    yr = pb.yearly({k: series[k] for k in names}).loc[2016:]
    fig2 = go.Figure([go.Bar(x=yr.index.astype(str), y=yr[k] * 100, name=k, marker_color=pb.COLORS.get(k, ui.MUTED))
                      for k in names])
    fig2.update_layout(title="Year by year (2026 to Oct 12)", yaxis_ticksuffix="%", barmode="group", hovermode="x unified")
    a, b = st.columns([3, 2])
    with a:
        ui.plotly(fig, 380, key=f"{key}_g")
    with b:
        ui.plotly(fig2, 380, key=f"{key}_y")


def trades_table(tr: pd.DataFrame, key: str):
    st.dataframe(tr.iloc[::-1], hide_index=True, width="stretch", height=320, key=key, column_config={
        "Signal date": st.column_config.DateColumn(format="MMM D, YYYY"),
        "Bought": st.column_config.DateColumn(format="MMM D, YYYY"),
        "Sold": st.column_config.DateColumn(format="MMM D, YYYY"),
        "Buy price": st.column_config.NumberColumn(format="$%.2f"),
        "Sell price": st.column_config.NumberColumn(format="$%.2f"),
        "Return": st.column_config.NumberColumn(format="percent")})


def backtest_summary(stt: dict, bench: dict, bench_name: str, key: str):
    ui.metrics([
        {"label": "Return per year", "value": pct(stt["Return per year"]),
         "delta": f"{(stt['Return per year'] - bench['Return per year']) * 100:+.1f} pts vs {bench_name}"},
        {"label": "Sharpe ratio", "value": ui.fmt_num(stt["Sharpe"]), "delta": f"{bench_name} {ui.fmt_num(bench['Sharpe'])}",
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Worst drop", "value": pct(stt["Worst drop"], 0), "delta": f"{bench_name} {pct(bench['Worst drop'], 0)}",
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Win rate", "value": pct(stt.get("Win rate"), 0),
         "delta": f"{stt.get('Trades per year', 0):.0f} trades a year", "delta_color": "off", "delta_arrow": "off"},
        {"label": "Avg trade", "value": pct(stt.get("Avg trade"), 2, True),
         "delta": f"held {stt.get('Avg days held', np.nan):.0f} days" if np.isfinite(stt.get("Avg days held", np.nan)) else None,
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Risk : reward", "value": f"1 : {stt['Payoff']:.1f}" if np.isfinite(stt.get("Payoff", np.nan)) else None},
    ], key=key)


SURVIVOR_NOTE = ("Stocks are only ranked and traded on days they were in the S&P 500 (point-in-time membership). "
                 "Yahoo no longer has prices for some that left, usually takeovers and failures, so a little "
                 "survivorship bias remains and the results may still run slightly high.")
YEARS = {"10y": 10, "20y": 20}
TECH_SURVIVOR_NOTE = ("Stocks are only traded on days they were in the S&P 500, but the tech list comes from today's "
                      "sector table, so tech names that have since left the index are missing (survivorship bias): "
                      "expect these results to run high.")


# ---- Leader Dip Plus 7 ------------------------------------------------------
@st.cache_data(ttl=12 * 3600, show_spinner=False)
def ld_backtest(years: str, rules: str, cash: str, slots: int, cost_bps: float) -> dict:
    n = YEARS[years]
    period = data.yahoo_period(n)
    start = pd.Timestamp.now().normalize() - pd.DateOffset(years=n)
    ohlcv = data.last_years(data.download_ohlcv(tuple(data.sp500_ever(start)), period=period), n)
    if "Close" not in ohlcv or ohlcv["Close"].shape[1] < 10:
        raise ValueError("Couldn't download prices for the S&P 500 right now.")
    m = live.market_inputs(period)
    if not len(m["spy"]):
        raise ValueError("Couldn't download SPY, which the market switch needs.")
    members = data.sp500_members(ohlcv["Close"].index, ohlcv["Close"].columns)
    sr = leader_dip.sector_returns(ohlcv["Close"].index, ohlcv["Close"].columns, live.sector_map(), m["etf"])
    return leader_dip.walk_forward(ohlcv, m["spy"], cash=cash, tbill_yields=data.tbill_yields(period), slots=slots,
                                   cost_bps=cost_bps, rules=rules, vix=m["vix"] if len(m["vix"]) else None,
                                   sector_ret3=sr, members=members)


def leader_dip_view():
    kpis(LD, "pb_ld")
    a, b = st.columns([1, 1])
    with a:
        steps_card("How it works", [
            "<b>Find leaders.</b> Stocks above their 200-day average whose 6-month gain beats 70% of the S&amp;P 500.",
            "<b>Wait for a flush.</b> The 2-day RSI closes under 10: two sharp down days in a row.",
            "<b>Check it's a real dip.</b> At least one quality point: a deep drop (2.5+ ATRs under the 10-day high), "
            "more than 10% under the 52-week high, the stock's sector ETF down 2%+ in 3 days, or VIX above 20.",
            "<b>Buy cheap.</b> A limit order 3% under the signal close, good for the next day only. Many signals never "
            "fill; the ones that do are bought at a discount.",
            "<b>Sell into the bounce.</b> At a profit target of the signal close + 1.5 ATR, or at the next open once "
            "the 2-day RSI tops 70, the stock closes under its 200-day, or 10 trading days pass. No stop loss.",
            "<b>Size it.</b> 7 equal slots (about 14% each), strongest 6-month gainers first. Money not in trades sits in "
            "SPY while SPY is above its 200-day, and in T-bills otherwise.",
            "<b>Market switch.</b> New trades only while SPY is above its 200-day, or during a panic (VIX above 25).",
        ])
    with b:
        text_card("Why it has an edge",
                  "Even great companies get dumped for two days at a time: funds rebalance, stops trigger, headlines "
                  "spook holders. Leaders in long uptrends get bought back fast, so the average trade lasts about 5 days "
                  "and makes +1.7%. The limit order demands a discount, the quality points skip ordinary wobbles, and "
                  "the market switch keeps it out of bear markets. Parking idle cash in SPY fixes the old version's "
                  "biggest weakness: it was only about a quarter invested.", "buy")
        text_card("What's new vs the old Leader Dip",
                  "Same entry. Added: the quality-point filter, the 1.5 ATR profit target, the exit on a close under the "
                  "200-day, the panic exception to the market switch, 7 bigger slots instead of 10, and idle cash in SPY. "
                  "Over the last 5 years that took it from 24.9% to 33.1% a year (classic rules: about 12-13% a year "
                  "with cash in T-bills).")
        text_card("The risks",
                  "No stop loss, so one trade can lose 20%. Idle cash in SPY means it falls with the market: worst drop "
                  "18% (vs 14% with T-bills) and −5.7% in 2022. With fills 0.25% worse it made 28.7% a year, and in "
                  "2000-12 it made 16.5%. <b>Plan on roughly 20-28% a year</b>, not 33%.", "sell")
    research_charts([LD, SPY, QQQ], "ld")

    st.subheader("Today's signals", help="Every S&P 500 stock checked against the Plus rules at the last close.")
    if st.button("Scan the S&P 500 now", type="primary", key="pb_ld_scan") or st.session_state.get("pb_ld_scanned"):
        st.session_state.pb_ld_scanned = True
        with st.spinner("Downloading the S&P 500 and checking every stock…"):
            now = live.leader_dip_today()
        if now.empty:
            st.warning("Couldn't download the S&P 500 right now. Try again shortly.")
        else:
            ld_signals(now)
    else:
        st.caption("Downloads two years of prices for every S&P 500 stock, so the first scan takes a minute. "
                   "Top Performers → Swing setups shows the same list and logs every signal.")

    with st.expander("Walk-forward test on the S&P 500 of each date"):
        q = st.columns(4)
        years = q[0].segmented_control("History", list(YEARS), default="10y", key="pb_ld_years") or "10y"
        rules_lbl = q[1].selectbox("Rules", list(leader_dip.RULESETS), key="pb_ld_rules")
        cash_lbl = q[2].selectbox("Idle cash", list(leader_dip.CASH_CHOICES), key="pb_ld_cash", help=leader_dip.CASH_HELP)
        slots = q[3].slider("Slots", 3, 15, leader_dip.SLOTS, key="pb_ld_slots", help=tip("ld_slots"))
        if st.button("Run the walk-forward test", key="pb_ld_run"):
            try:
                with st.spinner("Downloading every stock that was in the S&P 500, then picking settings year by year…"):
                    res = ld_backtest(years, leader_dip.RULESETS[rules_lbl], leader_dip.CASH_CHOICES[cash_lbl],
                                      int(slots), leader_dip.COST_BPS)
            except ValueError as e:
                st.warning(str(e))
                return
            backtest_summary(res["stats"], res["spy_stats"], "SPY", "pb_ldbt")
            eq = res["equity"] * START
            fig = go.Figure([go.Scatter(x=eq.index, y=eq, name=rules_lbl, line=dict(color=ui.GREEN, width=2)),
                             go.Scatter(x=eq.index, y=res["spy_equity"] * START, name="SPY", line=dict(color=ui.MUTED, width=1.4))])
            fig.update_layout(title=f"What ${START:,} became", yaxis_type="log", yaxis_tickprefix="$", hovermode="x unified")
            ui.plotly(fig, 340, key="pb_ld_eq")
            if len(res["trades"]):
                why = res["trades"]["Why it sold"].value_counts(normalize=True)
                st.caption("How trades ended: " + ", ".join(f"{v:.0%} {k}" for k, v in why.items()) + ".")
            trades_table(res["trades"], "pb_ld_tr")
            ui.walk_forward_table(res, "pb_ld_wf", SURVIVOR_NOTE)


def ld_signals(now: pd.DataFrame):
    sig = now[now["Signal"]].sort_values("6-month gain", ascending=False)
    sw = live.switches().get("leader_dip", {})
    if sw.get("on") is False:
        st.warning("The market switch is **off** (SPY below its 200-day and VIX calm), so no new trades. Signals are for "
                   "reference only.")
    if sig.empty:
        st.info("No S&P 500 stock passed every rule at the last close. Plus fires on a few stocks a week, less often in "
                "calm, rising markets.")
    else:
        names = data.sp500_table().set_index("Symbol")
        show = sig.join(names[["Name"]] if "Name" in names else pd.DataFrame(index=sig.index), how="left")
        st.dataframe(show[[c for c in ("Name", "Price", "Limit", "Target", "RSI2", "Quality points", "6-month gain",
                                       "Strength") if c in show]],
                     width="stretch", key="pb_ld_sig", column_config={
                         "Price": st.column_config.NumberColumn("Close", format="$%.2f"),
                         "Limit": st.column_config.NumberColumn("Limit buy (next session)", format="$%.2f", help=tip("ld_limit")),
                         "Target": st.column_config.NumberColumn("Profit target", format="$%.2f",
                                                                 help="Signal close + 1.5 ATR: a sell limit once you own it."),
                         "RSI2": st.column_config.NumberColumn("2-day RSI", format="%.1f", help=tip("ld_rsi2")),
                         "6-month gain": st.column_config.NumberColumn(format="percent"),
                         "Strength": st.column_config.ProgressColumn("Strength rank", min_value=0, max_value=1, format="percent")})
        st.caption(f"{len(sig)} signal{'s' if len(sig) != 1 else ''} at the last close, strongest first. With more "
                   f"signals than free slots (7), take them from the top.")
    skipped = now[now.get("Base signal", now["Signal"]) & ~now["Signal"]] if "Base signal" in now else now.iloc[0:0]
    if len(skipped):
        st.caption(f"Skipped for having no quality point: {', '.join(skipped.index[:12])}"
                   f"{'…' if len(skipped) > 12 else ''}. The classic rules would have bought these.")


# ---- Tech Breakout Rider ----------------------------------------------------
@st.cache_data(ttl=12 * 3600, show_spinner=False)
def br_backtest(years: str, slots: int, cost_bps: float) -> dict:
    n = YEARS[years]
    period = data.yahoo_period(n)
    ohlcv = data.last_years(data.download_ohlcv(tuple(breakout_rider.tech_universe(data.sp500_table())), period=period), n)
    if "Close" not in ohlcv or ohlcv["Close"].shape[1] < 10:
        raise ValueError("Couldn't download prices for the tech stocks right now.")
    m = live.market_inputs(period)
    if not len(m["qqq"]):
        raise ValueError("Couldn't download QQQ, which the tech switch needs.")
    members = data.sp500_members(ohlcv["Close"].index, ohlcv["Close"].columns)
    members[[c for c in breakout_rider.TECH_EXTRA if c in members]] = True  # AMZN and TSLA are always in its universe
    return breakout_rider.walk_forward(ohlcv, m["qqq"], data.tbill_yields(period), slots, cost_bps,
                                       market_close=m["spy"] if len(m["spy"]) else None, members=members)


def breakout_view():
    kpis(BR, "pb_br")
    a, b = st.columns([1, 1])
    with a:
        steps_card("How it works", [
            "<b>Tech only.</b> S&amp;P 500 technology and communication stocks, plus AMZN and TSLA (about 100 names).",
            "<b>Leaders only.</b> The 6-month gain ranks in the top 30% of those tech stocks.",
            "<b>The breakout.</b> The stock closes above its highest high of the previous 20 days, on an up day, with "
            "ADX(14) above 20 (a real trend, not a sideways drift).",
            "<b>Tech switch.</b> New trades only while QQQ's 21-day EMA is above its 50-day EMA.",
            "<b>Buy on a small pullback.</b> A limit order half an ATR under the signal close, next day only.",
            "<b>Ride it.</b> Hold until the stock's 21-day EMA closes under its 50-day EMA, then sell at the next open "
            "(or after 90 trading days). No stop, no profit target.",
            "<b>Size it.</b> Up to 10 positions, biggest 1-month gainers first. Cash not in trades earns T-bill interest.",
        ])
    with b:
        text_card("Why it has an edge",
                  "Trend following. Tech leaders that break out to a new high tend to keep running for months, because "
                  "the news, earnings revisions and fund flows behind them don't change overnight. It is wrong half the "
                  "time, but the EMA exit cuts losers at about −11.5% while winners average +36%: a 3-to-1 payoff. "
                  "It was the best of 4,200 tech systems tested across six families, picked on 2016-21 data.", "buy")
        text_card("The risks",
                  "It leans on a few monster winners: without its best 5 stocks (SNDK, STX, NVDA, PLTR, MU) it made "
                  "about 15% a year. It lost 25% in 2022, its worst drop was 29%, and in 2000-12 it made only 7% a "
                  "year. Nearby settings made 27% a year at the median, so the result isn't one lucky setting, but "
                  "<b>keep it a small part of the money</b>.", "sell")
        text_card("What it is not",
                  "EMA crossovers on their own, Stochastic RSI with ATR stops, and tight 1.5R targets all lost to plain "
                  "momentum in the same test (the popular EMA + StochRSI + ATR system made 0% a year).")
    research_charts([BR, QQQ, SPY], "br")

    st.subheader("Today's signals", help="Every tech stock checked against the rules at the last close.")
    if st.button("Scan tech stocks now", type="primary", key="pb_br_scan") or st.session_state.get("pb_br_scanned"):
        st.session_state.pb_br_scanned = True
        with st.spinner("Downloading tech stocks and checking for breakouts…"):
            now = live.breakout_today()
        if now.empty:
            st.warning("Couldn't download the tech stocks right now. Try again shortly.")
        else:
            br_signals(now)
    else:
        st.caption("Downloads two years of prices for about 100 tech stocks.")

    with st.expander("Walk-forward test on tech stocks"):
        q = st.columns(3)
        years = q[0].segmented_control("History", list(YEARS), default="10y", key="pb_br_years") or "10y"
        slots = q[1].slider("Slots", 3, 20, breakout_rider.SLOTS, key="pb_br_slots")
        cost = q[2].number_input("Cost per side (bps)", 0.0, 50.0, breakout_rider.COST_BPS, 1.0, key="pb_br_cost")
        if st.button("Run the walk-forward test", key="pb_br_run"):
            try:
                with st.spinner("Picking settings year by year and trading each next year…"):
                    res = br_backtest(years, int(slots), float(cost))
            except ValueError as e:
                st.warning(str(e))
                return
            backtest_summary(res["stats"], res["qqq_stats"], "QQQ", "pb_brbt")
            eq = res["equity"] * START
            fig = go.Figure([go.Scatter(x=eq.index, y=eq, name="Tech Breakout Rider", line=dict(color=ui.BLUE, width=2)),
                             go.Scatter(x=eq.index, y=res["qqq_equity"] * START, name="QQQ", line=dict(color=ui.MUTED, width=1.4))])
            fig.update_layout(title=f"What ${START:,} became", yaxis_type="log", yaxis_tickprefix="$", hovermode="x unified")
            ui.plotly(fig, 340, key="pb_br_eq")
            tr = res["trades"]
            done = tr[tr["Why it sold"] != "Open"] if len(tr) else tr
            if len(done):
                top = done.groupby("Symbol")["Return"].sum().sort_values(ascending=False)
                st.caption(f"Biggest contributors: {', '.join(f'{s} ({v:+.0%})' for s, v in top.head(5).items())}. "
                           "A trend system's results always hinge on a handful of names.")
            trades_table(tr, "pb_br_tr")
            ui.walk_forward_table(res, "pb_br_wf", TECH_SURVIVOR_NOTE)


def br_signals(now: pd.DataFrame):
    gate = now.attrs.get("gate_on")
    if gate is False:
        st.warning("The tech switch is **off** (QQQ's 21-day EMA is under its 50-day), so no new trades.")
    sig = now[now["Signal"]].sort_values("1-month gain", ascending=False)
    names = data.sp500_table().set_index("Symbol")
    nm = names[["Name"]] if "Name" in names else pd.DataFrame(index=now.index)
    cfg = {"Price": st.column_config.NumberColumn("Close", format="$%.2f"),
           "Limit": st.column_config.NumberColumn("Limit buy (next session)", format="$%.2f",
                                                  help="Signal close minus half an ATR, good for the next session only."),
           "20-day high": st.column_config.NumberColumn("Prior 20-day high", format="$%.2f"),
           "ADX": st.column_config.NumberColumn(format="%.0f"),
           "1-month gain": st.column_config.NumberColumn(format="percent"),
           "6-month gain": st.column_config.NumberColumn(format="percent"),
           "vs 20-day high": st.column_config.NumberColumn(format="percent"),
           "Strength": st.column_config.ProgressColumn("Strength vs tech", min_value=0, max_value=1, format="percent")}
    if sig.empty:
        st.info("No tech stock broke out under every rule at the last close. Expect about one new signal a week on average, "
                "in bursts when tech is running.")
    else:
        st.dataframe(sig.join(nm, how="left")[[c for c in ("Name", "Price", "Limit", "20-day high", "ADX", "1-month gain",
                                                          "6-month gain", "Strength") if c in sig.join(nm, how="left")]],
                     width="stretch", key="pb_br_sig", column_config=cfg)
        st.caption(f"{len(sig)} signal{'s' if len(sig) != 1 else ''}, biggest 1-month gainers first (the order the system "
                   "fills its 10 slots).")
    near = now[~now["Signal"] & (now["Strength"] >= breakout_rider.STRENGTH_MIN) & (now["vs 20-day high"] > -0.03)
               & now["Trend intact"]].sort_values("vs 20-day high", ascending=False)
    if len(near):
        with st.expander(f"Near a breakout ({len(near)}): tech leaders within 3% of their 20-day high"):
            st.dataframe(near.join(nm, how="left")[[c for c in ("Name", "Price", "20-day high", "vs 20-day high", "ADX",
                                                                "Strength") if c in near.join(nm, how="left")]],
                         width="stretch", key="pb_br_near", column_config=cfg)
    broken = now[~now["Trend intact"] & (now["Strength"] >= breakout_rider.STRENGTH_MIN)]
    if len(broken):
        st.caption(f"Trend exits (21-day EMA under the 50-day) among tech leaders: {', '.join(broken.index[:15])}. "
                   "If you hold one of these from a Breakout Rider signal, it sells at the next open.")


# ---- TQQQ Day + Night ---------------------------------------------------------
@st.cache_data(ttl=6 * 3600, show_spinner=False)
def dn_backtest(days: int) -> dict:
    bars = data.intraday_bars(day_night.SYMBOL, days)
    if bars.empty:
        raise ValueError("Couldn't load TQQQ's intraday bars right now.")
    res = day_night.walk_forward(bars, data.tbill_yields("10y"))
    res["source"] = bars.attrs.get("source", "")
    return res


def day_night_view():
    kpis(DN, "pb_dn")
    legs = pb.FACTS[DN]["legs"]
    ui.kv([("Day leg", f"{legs['Day']['return']:.1%} a year · wins {legs['Day']['win']:.0%} · {legs['Day']['edge']:+.2%} a trade"),
           ("Night leg", f"{legs['Night']['return']:.1%} a year · wins {legs['Night']['win']:.0%} · "
                         f"{legs['Night']['edge']:+.2%} a trade"),
           ("Together", "34.6% a year · worst drop 30% · +19% in 2022"),
           ("Holding TQQQ", "22.5% a year · worst drop 82%")])
    a, b = st.columns([1, 1])
    with a:
        steps_card("How it works", [
            "<b>Know the normal move.</b> For each half hour of the day, average how far TQQQ had moved from that day's "
            "open by then, over the last 14 sessions. The upper band is today's open (or yesterday's close, if higher) "
            "plus that normal move.",
            "<b>Day leg: buy the breakout.</b> Every 30 minutes from 10:00 to 15:30 New York time, buy if TQQQ is above "
            "the band.",
            "<b>Get out when it fades.</b> If long, sell at a check once TQQQ is back under the higher of the band and "
            "the day's VWAP. Anything still held sells at the 16:00 close.",
            "<b>Night leg: buy the weak close.</b> At 15:30, if TQQQ sits in the bottom 20% of the day's high-low range "
            "so far, buy at the close (market-on-close orders are due by 15:50) and sell at the next morning's open.",
            "<b>Size it.</b> Each leg uses the whole sleeve, but they never hold at the same time (one is 09:30-16:00, "
            "the other 16:00-09:30). Every trade is a buy: no shorting.",
        ])
    with b:
        text_card("Why it has an edge",
                  "Day: when the Nasdaq moves further than usual by a given time of day, the move tends to carry into the "
                  "close. Leveraged ETFs and option dealers have to buy more as prices rise, late in the day. Night: a "
                  "close near the day's low is often an overreaction that partly reverses by the next open. The two legs "
                  "barely move together (correlation 0.06 over 2016-26, 0.01 over the last 5 years), so together they beat either one, and the pair made money "
                  "in 2022 (+19%) when tech fell a third.", "buy")
        text_card("The risks",
                  "TQQQ is 3x the Nasdaq-100: the pair's worst drop was 30%. The edge is only 0.2-0.3% a trade, so fills "
                  "decide everything; a <b>paper-money run on Alpaca is testing real fills from Oct 14 to Dec 11, "
                  "2026</b>, and the plan keeps this sleeve in Leader Dip Plus 7 until it passes. It needs a check every "
                  "30 minutes and an order before 15:50. Day trading in a margin account under $25,000 runs into the "
                  "pattern-day-trader rule. Researched on TQQQ: on QQQ the same pair made about 12% a year.", "sell")
    research_charts([DN, QQQ, SPY], "dn")

    st.subheader("Today", help="Where TQQQ stands for both legs right now.")
    with st.spinner("Loading TQQQ's intraday bars…"):
        t = live.day_night_today()
    if not t:
        st.info("Intraday data for TQQQ isn't available right now. With Alpaca keys set (ALPACA_API_KEY and "
                "ALPACA_SECRET_KEY in the app's secrets) SharkFin reads 30-minute bars and live trades from Alpaca.")
    else:
        dn_today(t)

    with st.expander("Walk-forward test on intraday bars"):
        if data.alpaca_keys() is None:
            st.info("A walk-forward test needs about four years of 30-minute bars: three to pick the settings and one "
                    "to test them. Yahoo only has the last 60 days, so set Alpaca keys (ALPACA_API_KEY and "
                    "ALPACA_SECRET_KEY in the app's secrets) to run it.")
            return
        span = st.segmented_control("History", ["5 years", "10 years"], default="5 years", key="pb_dn_span") or "5 years"
        if st.button("Run the walk-forward test", key="pb_dn_run"):
            days = {"5 years": 1827, "10 years": 3653}[span]
            try:
                with st.spinner("Loading 30-minute bars, then picking settings year by year…"):
                    res = dn_backtest(days)
            except ValueError as e:
                st.warning(str(e))
                return
            rows = [{"": k, "Per year": v["Return per year"], "Sharpe": v["Sharpe"], "Worst drop": v["Worst drop"],
                     "Days invested": v.get("Days invested"), "Years": v["Years"]} for k, v in res["stats"].items() if v]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", key="pb_dn_tab", column_config={
                "Per year": st.column_config.NumberColumn(format="percent"), "Worst drop": st.column_config.NumberColumn(format="percent"),
                "Sharpe": st.column_config.NumberColumn(format="%.2f"),
                "Days invested": st.column_config.NumberColumn(format="percent"),
                "Years": st.column_config.NumberColumn(format="%.1f")})
            g = pd.DataFrame({"Day + night": res["equity"], "Hold TQQQ": res["hold_equity"]}) * START
            fig = go.Figure()
            for k, col in (("Day + night", ui.PURPLE), ("Hold TQQQ", ui.MUTED)):
                fig.add_scatter(x=g.index, y=g[k], name=k, line=dict(color=col, width=2 if k == "Day + night" else 1.3,
                                                                    dash="dot" if k == "Hold TQQQ" else None))
            fig.update_layout(title=f"What ${START:,} became in the test years ({res['source']})", yaxis_tickprefix="$",
                              hovermode="x unified")
            ui.plotly(fig, 340, key="pb_dn_eq")
            ui.walk_forward_table(res, "pb_dn_wf",
                                  "Costs: 0.02% per side. Day checks use each half-hour bar's close and fill at the next "
                                  "bar's open; the night leg decides at 15:30 and buys at the close.")


def dn_today(t: dict):
    when = t.get("live_time")
    src = t.get("source", "")
    st.caption(f"{t['date']:%A %b %d} · {src}" + (f" · last trade {when:%H:%M:%S} ET (IEX)" if when is not None else ""))
    ui.metrics([
        {"label": "TQQQ now", "value": ui.fmt_money(t["price"]), "delta": f"{t['price'] / t['prev_close'] - 1:+.2%} today"},
        {"label": f"Band at {t['next_check']}" if t.get("next_check") else "Day leg", "value":
            ui.fmt_money(t["next_band"]) if t.get("next_check") else "Done",
         "delta": (f"{t['price'] / t['next_band'] - 1:+.2%} away" if t.get("next_check") and np.isfinite(t["next_band"]) else None),
         "delta_color": "off", "delta_arrow": "off", "help": "Buy at the next check if TQQQ is above this band."},
        {"label": "Session VWAP", "value": ui.fmt_money(t["vwap"]),
         "help": "Volume-weighted average price since the open. A long day trade sells under the higher of the band and VWAP."},
        {"label": "Day leg", "value": "Long" if t["in_trade"] else "Flat",
         "delta": t["events"][-1][1] + " at " + t["events"][-1][0] if t["events"] else "no trade yet today",
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Close location", "value": pct(t["close_location"], 0),
         "delta": f"night buy below {ui.fmt_money(t['night_trigger'])}", "delta_color": "off", "delta_arrow": "off",
         "help": "Where the price sits in today's high-low range. Under 20% at the close triggers the night leg."},
    ], key="pb_dn_now")
    if t.get("night_decided"):
        st.markdown(ui.pill("Night buy" if t["weak_close"] else "No night trade", "info" if t["weak_close"] else "neu") +
                    "<span class='sf-note'>Decided at 15:30: TQQQ was "
                    f"{'in' if t['weak_close'] else 'above'} the bottom 20% of the day's range by then. "
                    + ("Buy at the close (market-on-close, due by 15:50) and sell at tomorrow's open." if t["weak_close"]
                       else "The night leg sits out tonight.") + "</span>", unsafe_allow_html=True)
    elif t["weak_close"]:
        st.markdown(ui.pill("Weak close so far", "info") + "<span class='sf-note'>If TQQQ is still in the bottom 20% of "
                    "today's range at 15:30, the night leg buys at the close (market-on-close orders are due by "
                    "15:50) and sells at tomorrow's open.</span>", unsafe_allow_html=True)
    tb = t["bars"]
    x = [pd.Timestamp(t["date"]) + pd.Timedelta(minutes=570 + 30 * int(i)) for i in tb.index]
    fig = go.Figure(go.Candlestick(x=x, open=tb["o"], high=tb["h"], low=tb["l"], close=tb["c"], name="TQQQ",
                                   increasing_line_color=ui.GREEN, decreasing_line_color=ui.RED,
                                   increasing_fillcolor=ui.GREEN, decreasing_fillcolor=ui.RED))
    bx = [pd.Timestamp(t["date"]) + pd.Timedelta(minutes=600 + 30 * j) for j in range(len(t["band"]))]
    fig.add_scatter(x=bx, y=t["band"].to_numpy(), name="Upper band", mode="lines+markers",
                    line=dict(color=ui.PURPLE, width=1.5, dash="dash", shape="hv"), marker=dict(size=4))
    vw = (tb["vw"] * tb["v"]).cumsum() / tb["v"].cumsum().replace(0, np.nan)
    fig.add_scatter(x=[xx + pd.Timedelta(minutes=30) for xx in x], y=vw, name="VWAP", line=dict(color=ui.ORANGE, width=1.3))
    fig.add_hline(y=t["night_trigger"], line=dict(color=ui.BLUE, dash="dot", width=1),
                  annotation_text="weak-close line", annotation_position="bottom right")
    fig.update_layout(title="Today in half-hour bars, with the breakout band and VWAP", xaxis_rangeslider_visible=False,
                      hovermode="x unified")
    ui.plotly(fig, 380, key="pb_dn_chart")
    st.caption("SharkFin only reads market data: it never places orders. " + day_night.DAY_RULE + " " + day_night.NIGHT_RULE)


# ---- The combined plan ------------------------------------------------------
def plan_view():
    f = pb.FACTS["The plan"]
    ui.hero("The combined plan", f"{f['return']:.1%} a year",
            f"Sharpe {f['sharpe']:.2f} · worst drop {abs(f['worst']):.0%} · 2022 {f['y2022']:+.1%} — last 5 years in "
            f"the research. The S&amp;P 500 made 14.0% a year, Sharpe 0.63, worst drop 25%, −18% in 2022.",
            ui.pill("50 / 20 / 30", "info"))
    a, b = st.columns([2, 3])
    with a:
        fig = go.Figure(go.Pie(labels=list(pb.WEIGHTS), values=list(pb.WEIGHTS.values()), hole=0.62, sort=False,
                               marker=dict(colors=[pb.COLORS[k] for k in pb.WEIGHTS]), textinfo="percent",
                               hovertemplate="%{label}: %{percent}<extra></extra>"))
        fig.update_layout(title="Where the money goes", showlegend=True, legend=dict(y=-0.05),
                          annotations=[dict(text="Monthly<br>rebalance", showarrow=False, font=dict(size=12, color="#c9d1dc"))])
        ui.plotly(fig, 330, key="pb_pie")
    with b:
        steps_card("How the plan works", [
            "<b>50% Leader Dip Plus 7: the core.</b> Steady short swing trades in S&amp;P 500 leaders, with idle cash in "
            "SPY. The best Sharpe of the three.",
            "<b>20% Tech Breakout Rider: the upside.</b> Catches the big tech trends the core sells too early. Kept small "
            "because a few stocks drive its results.",
            "<b>30% TQQQ Day + Night: the shock absorber.</b> In and out within hours, so it barely moves with the other "
            "two, and it made money in 2022 when they lost.",
            "<b>Rebalance monthly.</b> On the first trading day of each month, move money between the three so they are "
            "back to 50 / 20 / 30.",
            "<b>Until the TQQQ paper run passes</b> (Dec 11, 2026), keep that 30% in Leader Dip Plus 7 (80 / 20 / 0).",
        ])
    st.markdown("<div class='sf-card buy'><div class='t'>Why the mix beats each part</div><div class='row'>The three "
                "strategies lose money at different times. In 2022 Tech Breakout Rider lost 25% and Leader Dip Plus 7 "
                "lost 6%, while the TQQQ pair made 19%, so the plan lost only 2%. On days the S&amp;P 500 fell more than "
                "1%, the TQQQ pair's returns had almost no link to the other two. The result is about the same return "
                "as each strategy alone with a much smoother ride: Sharpe 1.60 against 1.06-1.40. The weights were "
                "chosen on 2016-21 data only (the best Sharpe then), and graded on the five years after.</div></div>",
                unsafe_allow_html=True)

    names = [PLAN, LD, BR, DN, SPY, QQQ]
    since = st.segmented_control("Chart from", ["Last 5 years", "2016 (incl. the picking years)"], default="Last 5 years",
                                 key="pb_since") or "Last 5 years"
    s0 = pb.GRADE[0] if since == "Last 5 years" else "2016-01-05"
    g = pb.growth({k: series[k] for k in names}, s0)
    dd = pb.drawdowns({k: series[k] for k in names}, s0)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    for k in names:
        bench = k in (SPY, QQQ)
        style = dict(color=pb.COLORS.get(k, ui.MUTED), width=3 if k == PLAN else 1.3 if bench else 1.5,
                     dash="dot" if bench else None)
        fig.add_scatter(x=g.index, y=g[k], name=k, line=style, row=1, col=1, legendgroup=k)
        if k in (PLAN, SPY):
            fig.add_scatter(x=dd.index, y=dd[k] * 100, name=k, line=style, row=2, col=1, legendgroup=k, showlegend=False,
                            fill="tozeroy" if k == PLAN else None)
    fig.update_yaxes(tickprefix="$", type="log", row=1, col=1)
    fig.update_yaxes(ticksuffix="%", title_text="Below peak", row=2, col=1)
    fig.update_layout(title=f"What ${START:,} became, and how far each fell from its high (plan vs SPY)",
                      hovermode="x unified")
    ui.plotly(fig, 520, key="pb_plan_g")

    st.subheader("Mixes compared (last 5 years)")
    mixes = {"The plan: 50 / 20 / 30": pb.WEIGHTS, "Before the paper run: 80 / 20 / 0": {LD: 0.8, BR: 0.2},
             "Equal thirds": {LD: 1 / 3, BR: 1 / 3, DN: 1 / 3}, "50% Plus 7 + 50% TQQQ pair": {LD: 0.5, DN: 0.5},
             "50% Plus 7 + 50% Breakout Rider": {LD: 0.5, BR: 0.5}}
    ser = {k: pb.mix(d, w) for k, w in mixes.items()}
    ser.update({LD + " alone": series[LD], BR + " alone": series[BR], DN + " alone": series[DN], SPY: series[SPY],
                QQQ: series[QQQ]})
    tab = pb.table(d, ser)
    st.dataframe(tab[["Return per year", "Sharpe", "Worst drop", "2022", "Volatility"]], width="stretch", key="pb_mixes",
                 column_config={"Return per year": st.column_config.NumberColumn(format="percent"),
                                "Sharpe": st.column_config.NumberColumn(format="%.2f", help=tip("Sharpe")),
                                "Worst drop": st.column_config.NumberColumn(format="percent"),
                                "2022": st.column_config.NumberColumn(format="percent"),
                                "Volatility": st.column_config.NumberColumn(format="percent")})

    st.subheader("Weights re-picked every year", help="A walk-forward check of the plan's weights.")
    wfm = pb.walk_forward_mix(d)
    fixed = pb.stats(series[PLAN].reindex(wfm["returns"].index), d["tbill"])
    ui.metrics([
        {"label": "Return per year", "value": pct(wfm["stats"]["Return per year"]),
         "delta": f"{(wfm['stats']['Return per year'] - fixed['Return per year']) * 100:+.1f} pts vs fixed 50 / 20 / 30"},
        {"label": "Sharpe ratio", "value": f"{wfm['stats']['Sharpe']:.2f}", "delta": f"fixed {fixed['Sharpe']:.2f}",
         "delta_color": "off", "delta_arrow": "off"},
        {"label": "Worst drop", "value": pct(wfm["stats"]["Worst drop"], 0), "delta": f"fixed {pct(fixed['Worst drop'], 0)}",
         "delta_color": "off", "delta_arrow": "off"},
    ], key="pb_wfmix")
    st.dataframe(wfm["folds"], hide_index=True, width="stretch", key="pb_wfmix_tab", column_config={
        **{k: st.column_config.NumberColumn(k, format="percent") for k in (LD, BR, DN)},
        "Return": st.column_config.NumberColumn("Return that year", format="percent"),
        "Sharpe": st.column_config.NumberColumn("Sharpe that year", format="%.2f")})
    st.caption("Each year's weights were picked on the three years before it only, then held for that year. Only the "
               "weights are re-picked here: each strategy's own settings come from the research, which picked them on "
               "2016-21, so the years up to Oct 2021 are still in-sample for the strategies themselves.")

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Try your own weights", help="Re-runs the research's daily returns with your weights, rebalanced monthly.")
        w = st.columns(3)
        wl = w[0].slider(LD, 0, 100, 50, 5, key="pb_w_ld", format="%d%%")
        wb = w[1].slider(BR, 0, 100, 20, 5, key="pb_w_br", format="%d%%")
        wd = w[2].slider(DN, 0, 100, 30, 5, key="pb_w_dn", format="%d%%")
        tot = wl + wb + wd
        if tot == 0:
            st.info("Give at least one strategy some weight.")
        else:
            mine = pb.mix(d, {LD: wl / tot, BR: wb / tot, DN: wd / tot})
            sm = pb.stats(mine.loc[pb.GRADE[0]:pb.GRADE[1]], d["tbill"])
            sp = pb.stats(series[PLAN].loc[pb.GRADE[0]:pb.GRADE[1]], d["tbill"])
            pick = pb.stats(mine.loc[pb.PICK[0]:pb.PICK[1]], d["tbill"])
            if tot != 100:
                st.caption(f"Weights add to {tot}%, so they're scaled to 100%: "
                           f"{wl / tot:.0%} / {wb / tot:.0%} / {wd / tot:.0%}.")
            ui.metrics([
                {"label": "Return per year", "value": pct(sm["Return per year"]),
                 "delta": f"{(sm['Return per year'] - sp['Return per year']) * 100:+.1f} pts vs the plan"},
                {"label": "Sharpe ratio", "value": f"{sm['Sharpe']:.2f}", "delta": f"{sm['Sharpe'] - sp['Sharpe']:+.2f} vs the plan"},
                {"label": "Worst drop", "value": pct(sm["Worst drop"], 0),
                 "delta": f"{(sm['Worst drop'] - sp['Worst drop']) * 100:+.1f} pts vs the plan"},
                {"label": "2022", "value": pct(sm["2022"], 1, True), "delta_color": "off"},
                {"label": "Sharpe in 2016-21", "value": f"{pick['Sharpe']:.2f}", "delta": "when weights were picked",
                 "delta_color": "off", "delta_arrow": "off"},
            ], key="pb_mine")
            st.caption("Tuning weights until the last 5 years look best is how backtests fool people. The plan's weights "
                       "were picked on 2016-21 alone; judge yours the same way with the last tile.")
    with c2:
        st.subheader("Your money")
        amount = st.number_input("Account size ($)", 1_000, 100_000_000, 50_000, 5_000, key="pb_amount")
        pre = st.toggle("Before the paper run passes (80 / 20 / 0)", key="pb_pre",
                        help="The research's advice: keep the TQQQ sleeve in Leader Dip Plus 7 until real fills are proven.")
        wts = {LD: 0.8, BR: 0.2, DN: 0.0} if pre else pb.WEIGHTS
        sp_ = pb.split(float(amount), wts)
        rows = [{"Strategy": k, "Share": v["weight"], "Money": v["sleeve"],
                 "Each position": v["position"] if v["sleeve"] > 0 else np.nan,
                 "Positions": {LD: f"up to {leader_dip.SLOTS}", BR: f"up to {breakout_rider.SLOTS}", DN: "1 at a time"}[k]}
                for k, v in sp_.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", key="pb_split", column_config={
            "Share": st.column_config.NumberColumn(format="percent"),
            "Money": st.column_config.NumberColumn(format="$%,.0f"),
            "Each position": st.column_config.NumberColumn(format="$%,.0f")})
        if not pre and amount < 25_000:
            st.caption("Under $25,000 in a margin account, US rules limit day trades to 3 per 5 days, which the TQQQ day "
                       "leg would exceed. A cash account avoids the rule but has to wait for trades to settle.")

    st.subheader("Do they move together?", help="Correlation of daily returns over the last 5 years: 1 = in lockstep, 0 = unrelated.")
    c1, c2 = st.columns(2)
    for col, down, title in ((c1, False, "Every day"), (c2, True, "Days the S&P 500 fell more than 1%")):
        cm = pb.correlations(d, down_days=down)
        fig = go.Figure(go.Heatmap(z=cm.values, x=cm.columns, y=cm.index, zmin=-1, zmax=1, colorscale=ui.DIVERGING,
                                   text=[[f"{v:.2f}" for v in r] for r in cm.values], texttemplate="%{text}",
                                   showscale=False, xgap=2, ygap=2, hovertemplate="%{y} vs %{x}: %{text}<extra></extra>"))
        fig.update_layout(title=title, yaxis=dict(autorange="reversed", showgrid=False), xaxis=dict(showgrid=False))
        with col:
            ui.plotly(fig, 330, key=f"pb_corr_{int(down)}")

    yr = pb.yearly({k: series[k] for k in [PLAN, LD, BR, DN, SPY]}).loc[2016:]
    with st.expander("Year by year"):
        st.dataframe(yr, width="stretch", key="pb_years",
                     column_config={k: st.column_config.NumberColumn(format="percent") for k in yr.columns})
        st.caption("2016 to Oct 2021 is the window the settings and weights were picked on; Oct 2021 onward is the "
                   "honest grade. 2026 runs to Oct 12.")

    st.subheader("Running it")
    a, b = st.columns(2)
    with a:
        steps_card("Each trading day", [
            "<b>After the close:</b> open this page (or Top Performers → Swing setups) and scan Leader Dip Plus 7 and "
            "Tech Breakout Rider. Note each signal's limit price, and Plus 7's profit target.",
            "<b>Before the next open:</b> place the limit buys (day orders) for as many signals as you have free slots, "
            "strongest first. For Plus 7 trades that fill, add the profit-target sell limit.",
            "<b>Exits:</b> sell at the open any position whose exit fired at the last close (RSI above 70 or a close under "
            "the 200-day for Plus 7; the 21 / 50 EMA cross for Breakout Rider).",
            "<b>TQQQ, during the day:</b> check at 10:00, 10:30 … 15:30 against the band; sell when it fades under the "
            "band and VWAP; flat by 16:00. By 15:50, send a market-on-close buy if the close is in the bottom 20% of "
            "the range, and a market-on-open sell for the next morning.",
        ])
    with b:
        text_card("What to expect",
                  "The last 5 years were kind to buying tech: one bear market (2022) and four strong years. Expect less "
                  "live: slippage, missed orders and a tougher market all cut returns. A reasonable plan is 20-30% a "
                  "year with drops of 20% or more along the way. Results this good would be impressive for a retail "
                  "trader, but a backtest Sharpe of 1.6 is not a proven track record.", "")
        text_card("Check it's still working",
                  "Top Performers → Swing setups logs every Leader Dip signal and checks it against what happened next. "
                  "If live trades fall well short of the research (64% winners, +1.7% a trade for Plus 7), cut size "
                  "before cutting corners.")


if view == LD:
    leader_dip_view()
elif view == BR:
    breakout_view()
elif view == DN:
    day_night_view()
else:
    plan_view()

st.caption("All research numbers are backtests after trading costs: Leader Dip Plus 7 and Tech Breakout Rider on the "
           "stocks that were in the S&P 500 on each date, the TQQQ pair on 1-minute bars. Their settings were picked on "
           "earlier data and graded on Oct 2021 - Oct 2026, one walk-forward step; the tests on this page re-pick them "
           "every year. The research's night leg decided on the 16:00 close itself, which can't be traded, so its night "
           "numbers run somewhat high. Past results don't guarantee future ones, and none of this is investment advice. "
           "SharkFin never places orders.")
ui.disclaimer()
