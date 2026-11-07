"""Strategy Playbook: SharkFin's two researched strategies (Dive Zone and Tech Breakout Rider), how each works,
today's signals, how to use them together, and what the Nov 2026 research tested and threw out."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import breakout_rider, data, leader_dip, live, playbook as pb, ui
from sharkfin.explain import tip

ui.header("Strategy Playbook",
          "Two researched strategies for growth investors: Dive Zone buys sharp dips in market leaders, Tech Breakout "
          "Rider rides tech trends for months. Graded on the five years to Nov 6 2026, including the Oct-Nov selloff.")

START = 10_000
LD, BR = pb.LD, pb.BR
BOTH, NOTES = "Using both", "What we tested"
VIEWS = [LD, BR, BOTH, NOTES]
SPY, QQQ = "S&P 500 (SPY)", "Nasdaq-100 (QQQ)"
LAB = Path(pb.__file__).with_name("research_data") / "growth_lab"
TAGS = {LD: "Swing · about 5 days", BR: "Trend · about 3 months"}
BLURB = {
    LD: "Buys a sharp two-day selloff in one of the S&P 500's strongest stocks and sells into the bounce. Idle cash "
        "rides SPY.",
    BR: "Buys tech leaders breaking out to a new one-month high and rides the trend until it bends.",
}


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def research(version: tuple) -> pd.DataFrame:
    # Keyed on the data file's size and time, so a new research file never meets an old cached copy (a cache
    # from before the Nov 2026 rename had other columns and crashed the page).
    return pb.load()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def lab_table(name: str) -> pd.DataFrame:
    return pd.read_csv(LAB / f"{name}.csv")


d = research((pb.DATA.stat().st_mtime_ns, pb.DATA.stat().st_size, tuple(pb.COLUMNS.values())))
series = {k: pb.sleeve(d, k) for k in (LD, BR, SPY, QQQ)}


def pct(x, digits=1, sign=False):
    return ui.fmt_pct(x, digits, sign) if x is not None and np.isfinite(x) else "—"


# ---- Overview ---------------------------------------------------------------
def overview():
    cards = []
    for k in (LD, BR):
        f = pb.FACTS[k]
        cards.append(
            f"<div class='sf-strat' style='--c:{pb.COLORS[k]}'><div class='nm'>{ui.h(k)}</div>"
            f"<div class='tg'>{ui.h(TAGS[k])}</div><div class='big'>{f['return']:.1%}<span> a year</span></div>"
            f"<div class='sub'>Sharpe {f['sharpe']:.2f} · worst drop {abs(f['worst']):.0%} · 2022 {f['y2022']:+.0%}</div>"
            f"<div class='bl'>{ui.h(BLURB[k])}</div></div>")
    s, q = pb.FACTS[SPY], pb.FACTS[QQQ]
    cards.append(
        f"<div class='sf-strat' style='--c:{pb.COLORS[SPY]}'><div class='nm'>The yardstick</div>"
        f"<div class='tg'>Buy and hold</div><div class='big'>{s['return']:.1%}<span> a year (SPY)</span></div>"
        f"<div class='sub'>Sharpe {s['sharpe']:.2f} · worst drop {abs(s['worst']):.0%} · 2022 {s['y2022']:+.0%}</div>"
        f"<div class='bl'>QQQ made {q['return']:.1%} a year, Sharpe {q['sharpe']:.2f}, worst drop {abs(q['worst']):.0%}."
        "</div></div>")
    cards.append(
        "<div class='sf-strat' style='--c:#ff7a93'><div class='nm'>Dropped in Nov 2026</div>"
        "<div class='tg'>Didn't make the cut</div><div class='big'>4<span> ideas cut</span></div>"
        "<div class='sub'>TQQQ Day + Night, Classic Dive Zone, momentum rotation, fear buying</div>"
        "<div class='bl'>And none of 18 VIX, GEX and crash filters improved the two that stayed. See What we tested."
        "</div></div>")
    st.markdown(f"<div class='sf-strats'>{''.join(cards)}</div>", unsafe_allow_html=True)
    st.caption("Oct 13 2021 to Nov 6 2026, after 0.1% costs on every buy and sell, on the stocks that were in the S&P 500 "
               "on each date. Settings were picked on older data, so this window is out of sample.")


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
        bits.append(ui.pill(f"Dive Zone switch {'on' if ld_['on'] else 'off'}", "pos" if ld_["on"] else "neg") +
                    f"<span class='sf-muted'>{ui.h(why)} · idle cash in {ld_.get('idle') or 'T-bills'}</span>")
    if br_:
        bits.append(ui.pill(f"Tech switch {'on' if br_['on'] else 'off'}", "pos" if br_["on"] else "neg") +
                    f"<span class='sf-muted'>QQQ 21-day EMA {br_['gap']:+.1%} vs its 50-day</span>")
    st.markdown(f"<div class='sf-card'>{'<br>'.join(bits)}</div>", unsafe_allow_html=True)


overview()
view = st.segmented_control("Strategy", VIEWS, default=LD, key="pb_view", label_visibility="collapsed") or LD
if view in (LD, BR):
    switch_strip()


# ---- Shared pieces ----------------------------------------------------------
def kpis(name: str, key: str):
    f = pb.FACTS[name]
    spy = pb.FACTS[SPY]
    ui.metrics([
        {"label": "Return per year", "value": pct(f["return"]), "delta": f"{(f['return'] - spy['return']) * 100:+.1f} pts vs SPY",
         "help": "Compound yearly return over the last 5 years, after trading costs."},
        {"label": "Sharpe ratio", "value": f"{f['sharpe']:.2f}", "delta": f"SPY {spy['sharpe']:.2f}", "delta_color": "off",
         "delta_arrow": "off", "help": tip("Sharpe") + " Measured after T-bill interest."},
        {"label": "Worst drop", "value": pct(f["worst"], 0), "delta": f"SPY {spy['worst']:.0%}", "delta_color": "off",
         "delta_arrow": "off", "help": "The biggest fall from a high to a later low: the pain you'd have had to sit through."},
        {"label": "Win rate", "value": pct(f["win"], 0), "delta": f"{f['trades_yr']:.0f} trades a year", "delta_color": "off",
         "delta_arrow": "off", "help": tip("Win rate")},
        {"label": "Edge per trade", "value": pct(f["edge"], 1, True),
         "delta": f"wins {f['avg_win']:+.1%} · losses {f['avg_loss']:+.1%}", "delta_color": "off", "delta_arrow": "off",
         "help": "What the average trade made after costs."},
        {"label": "Nov 2026 selloff", "value": pct(f["nov2026"], 1, True), "delta": f"SPY {spy['nov2026']:+.1%}",
         "delta_color": "off", "delta_arrow": "off", "help": "Oct 12 to Nov 6 2026, when chip and software stocks fell hard."},
    ], key=key, cols=6)


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
    fig2.update_layout(title="Year by year (2026 to Nov 6)", yaxis_ticksuffix="%", barmode="group", hovermode="x unified")
    a, b = st.columns([3, 2])
    with a:
        ui.plotly(fig, 360, key=f"{key}_g")
    with b:
        ui.plotly(fig2, 360, key=f"{key}_y")


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


# ---- Dive Zone ----------------------------------------------------------------
@st.cache_data(ttl=12 * 3600, show_spinner=False)
def ld_backtest(years: str, cash: str, slots: int, cost_bps: float) -> dict:
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
                                   cost_bps=cost_bps, rules="plus", vix=m["vix"] if len(m["vix"]) else None,
                                   sector_ret3=sr, members=members)


def dive_zone_view():
    f = pb.FACTS[LD]
    kpis(LD, "pb_ld")
    a, b = st.columns([1, 1])
    with a:
        steps_card("How it works", [
            "<b>Leaders only.</b> Stocks above their 200-day average whose 6-month gain beats 70% of the S&amp;P 500.",
            "<b>The dive.</b> The 2-day RSI closes under 10 (two sharp down days), with at least one sign it's a real "
            "flush: 2.5+ ATRs under the 10-day high, 10%+ under the 52-week high, the sector ETF down 2%+ in 3 days, "
            "or VIX above 20.",
            "<b>Buy cheaper.</b> A limit order 3% under the signal close, next day only.",
            "<b>Sell into the bounce.</b> At the signal close + 1.5 ATR, or at the next open once the 2-day RSI tops "
            "70, the stock closes under its 200-day, or 10 days pass. No stop loss.",
            "<b>Size and switch.</b> 7 equal slots, strongest first. New trades only while SPY is above its 200-day "
            "(or VIX is above 25). Idle cash sits in SPY while SPY is above its 200-day, T-bills otherwise.",
        ])
    with b:
        text_card("Why it works",
                  "Funds rebalancing, stop-loss cascades and scary headlines knock good stocks down for a day or two. "
                  f"Leaders get bought back fast: the average trade lasts {f['hold']} and makes {f['edge']:+.1%}, and "
                  f"{f['win']:.0%} win. It made {f['return']:.1%} a year against SPY's {pb.FACTS[SPY]['return']:.1%}, "
                  f"with a Sharpe of {f['sharpe']:.2f}. Older data agrees: {f['older']}.", "buy")
        text_card("The risks",
                  f"Buying dips fails when a whole sector breaks. From Oct 12 to Nov 6 2026 it lost "
                  f"{abs(f['nov2026']):.0%} (SPY {pb.FACTS[SPY]['nov2026']:+.1%}) as it kept buying chip and software "
                  f"leaders that kept falling; before that the five years stood at {f['before_crash']}. No stop "
                  f"loss, so one trade can lose 20%. With fills 0.25% worse: {f['stress']}. "
                  "<b>Plan on 15-25% a year</b>, with drops of 20%+.", "sell")
    research_charts([LD, SPY, QQQ], "ld")

    st.subheader("Today's signals", help="Every S&P 500 stock checked against the rules at the last close.")
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
        q = st.columns(3)
        years = q[0].segmented_control("History", list(YEARS), default="10y", key="pb_ld_years") or "10y"
        cash_lbl = q[1].selectbox("Idle cash", list(leader_dip.CASH_CHOICES), key="pb_ld_cash", help=leader_dip.CASH_HELP)
        slots = q[2].slider("Slots", 3, 15, leader_dip.SLOTS, key="pb_ld_slots", help=tip("ld_slots"))
        if st.button("Run the walk-forward test", key="pb_ld_run"):
            try:
                with st.spinner("Downloading every stock that was in the S&P 500, then picking settings year by year…"):
                    res = ld_backtest(years, leader_dip.CASH_CHOICES[cash_lbl], int(slots), leader_dip.COST_BPS)
            except ValueError as e:
                st.warning(str(e))
                return
            backtest_summary(res["stats"], res["spy_stats"], "SPY", "pb_ldbt")
            eq = res["equity"] * START
            fig = go.Figure([go.Scatter(x=eq.index, y=eq, name=LD, line=dict(color=ui.GREEN, width=2)),
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
        st.info("No S&P 500 stock passed every rule at the last close. Dive Zone fires on a few stocks a week, less often "
                "in calm, rising markets.")
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
                   f"signals than free slots ({leader_dip.SLOTS}), take them from the top.")


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
    f = pb.FACTS[BR]
    kpis(BR, "pb_br")
    a, b = st.columns([1, 1])
    with a:
        steps_card("How it works", [
            "<b>Tech leaders.</b> S&amp;P 500 tech and communication stocks plus AMZN and TSLA, in the top 30% of that "
            "group by 6-month gain.",
            "<b>The breakout.</b> A close above the highest high of the previous 20 days, on an up day, with ADX(14) "
            "above 20 (a real trend).",
            "<b>Tech switch.</b> New trades only while QQQ's 21-day EMA is above its 50-day EMA.",
            "<b>Buy on a small pullback.</b> A limit order half an ATR under the signal close, next day only.",
            "<b>Ride it.</b> Hold until the stock's 21-day EMA closes under its 50-day, then sell at the next open (or "
            "after 90 trading days). Up to 10 positions; cash earns T-bill interest.",
        ])
    with b:
        text_card("Why it works",
                  "Trend following. Tech leaders breaking out tend to keep running for months, because the earnings "
                  "revisions and fund flows behind them don't stop overnight. It is wrong half the time, but losers "
                  f"are cut at about {f['avg_loss']:.0%} while winners average {f['avg_win']:+.0%}: a 3-to-1 payoff. "
                  "It caught every big wave of the last five years: +84% in the 2023-24 AI run (QQQ +92%) and +88% in "
                  "the 2026 memory run (QQQ +23%).", "buy")
        text_card("The risks",
                  f"It leans on a few monster winners: {f['stress']}. It lost {abs(f['y2022']):.0%} in 2022, its worst "
                  f"drop was {abs(f['worst']):.0%}, and on older data it was ordinary: 14.7% a year in 2006-21 (QQQ 15.8%), "
                  f"{f['older']}. "
                  "<b>Keep it the smaller part of the money</b>, and let winners run: cutting them early removes the "
                  "edge.", "sell")
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
            fig = go.Figure([go.Scatter(x=eq.index, y=eq, name=BR, line=dict(color=ui.BLUE, width=2)),
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
        show = sig.join(nm, how="left")
        st.dataframe(show[[c for c in ("Name", "Price", "Limit", "20-day high", "ADX", "1-month gain", "6-month gain",
                                       "Strength") if c in show]], width="stretch", key="pb_br_sig", column_config=cfg)
        st.caption(f"{len(sig)} signal{'s' if len(sig) != 1 else ''}, biggest 1-month gainers first (the order the system "
                   "fills its 10 slots).")
    near = now[~now["Signal"] & (now["Strength"] >= breakout_rider.STRENGTH_MIN) & (now["vs 20-day high"] > -0.03)
               & now["Trend intact"]].sort_values("vs 20-day high", ascending=False)
    if len(near):
        with st.expander(f"Near a breakout ({len(near)}): tech leaders within 3% of their 20-day high"):
            show = near.join(nm, how="left")
            st.dataframe(show[[c for c in ("Name", "Price", "20-day high", "vs 20-day high", "ADX", "Strength") if c in show]],
                         width="stretch", key="pb_br_near", column_config=cfg)
    broken = now[~now["Trend intact"] & (now["Strength"] >= breakout_rider.STRENGTH_MIN)]
    if len(broken):
        st.caption(f"Trend exits (21-day EMA under the 50-day) among tech leaders: {', '.join(broken.index[:15])}. "
                   "If you hold one of these from a Breakout Rider signal, it sells at the next open.")


# ---- Using both -------------------------------------------------------------
def both_view():
    f = pb.FACTS["Both (70 / 30)"]
    a, b = st.columns([3, 2])
    with a:
        text_card("70% Dive Zone, 30% Tech Breakout Rider",
                  f"Over the last five years this mix made <b>{f['return']:.1%} a year</b> with a Sharpe of "
                  f"{f['sharpe']:.2f} and a worst drop of {abs(f['worst']):.0%} ({f['y2022']:+.1%} in 2022): smoother "
                  f"than either alone, because the two only move together about half the time (correlation 0.56). "
                  "Be clear about what that is: picked on 2006-21 data, the best mix was all Dive Zone, and re-picked "
                  "every year it averaged about 85 / 15. The 30% in Breakout Rider is a growth tilt for catching the "
                  "next AI-style wave, not something the older data asked for.", "")
    with b:
        steps_card("Running it", [
            "<b>After the close:</b> scan both strategies here or on Top Performers → Swing setups, and note each "
            "signal's limit price.",
            "<b>Before the open:</b> place the limit buys (day orders) for your free slots, strongest first; add Dive "
            "Zone's profit-target sell once a buy fills.",
            "<b>Exits:</b> sell at the open anything whose exit fired at the close.",
            "<b>Monthly:</b> move money between the two to get back to 70 / 30.",
        ])
    names = ["Both (70 / 30)", LD, BR, SPY, QQQ]
    ser = {"Both (70 / 30)": pb.mix(d, pb.WEIGHTS), LD: series[LD], BR: series[BR], SPY: series[SPY], QQQ: series[QQQ]}
    g = pb.growth(ser, pb.GRADE[0])
    fig = go.Figure()
    for k in names:
        bench = k in (SPY, QQQ)
        fig.add_scatter(x=g.index, y=g[k], name=k, line=dict(color=pb.COLORS.get(k, ui.MUTED),
                                                             width=3 if k == names[0] else 1.3 if bench else 1.6,
                                                             dash="dot" if bench else None))
    fig.update_layout(title=f"What ${START:,} became since Oct 2021", yaxis_tickprefix="$", yaxis_type="log",
                      hovermode="x unified")
    ui.plotly(fig, 380, key="pb_both_g")

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Try your own split", help="Re-runs the research's daily returns, rebalanced monthly.")
        w = st.slider("Share in Dive Zone", 0, 100, 70, 5, key="pb_w_ld", format="%d%%")
        mine = pb.mix(d, {LD: w / 100, BR: 1 - w / 100})
        sm = pb.stats(mine.loc[pb.GRADE[0]:pb.GRADE[1]], d["tbill"])
        pick = pb.stats(mine.loc[pb.PICK[0]:pb.PICK[1]], d["tbill"])
        ui.metrics([
            {"label": "Return per year", "value": pct(sm["Return per year"]), "delta": "last 5 years", "delta_color": "off",
             "delta_arrow": "off"},
            {"label": "Sharpe ratio", "value": f"{sm['Sharpe']:.2f}"},
            {"label": "Worst drop", "value": pct(sm["Worst drop"], 0)},
            {"label": "2022", "value": pct(sm["2022"], 1, True)},
            {"label": "Sharpe in 2006-21", "value": f"{pick['Sharpe']:.2f}", "delta": "before the test window",
             "delta_color": "off", "delta_arrow": "off"},
        ], key="pb_mine")
        st.caption("Tuning the split until the last five years look best is how backtests fool people; the last tile "
                   "shows the same split on the older data.")
    with c2:
        st.subheader("Your money")
        amount = st.number_input("Account size ($)", 1_000, 100_000_000, 50_000, 5_000, key="pb_amount")
        sp_ = pb.split(float(amount), {LD: w / 100, BR: 1 - w / 100})
        rows = [{"Strategy": k, "Share": v["weight"], "Money": v["sleeve"],
                 "Each position": v["position"] if v["sleeve"] > 0 else np.nan,
                 "Positions": {LD: f"up to {leader_dip.SLOTS}", BR: f"up to {breakout_rider.SLOTS}"}[k]}
                for k, v in sp_.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", key="pb_split", column_config={
            "Share": st.column_config.NumberColumn(format="percent"),
            "Money": st.column_config.NumberColumn(format="$%,.0f"),
            "Each position": st.column_config.NumberColumn(format="$%,.0f")})

    yr = pb.yearly(ser).loc[2016:]
    with st.expander("Year by year"):
        st.dataframe(yr, width="stretch", key="pb_years",
                     column_config={k: st.column_config.NumberColumn(format="percent") for k in yr.columns})
        st.caption("2026 runs to Nov 6. Years before Oct 2021 are the window the settings were picked on.")


# ---- What we tested -----------------------------------------------------------
def notes_view():
    st.markdown("<div class='sf-note'>Everything below was graded the same way: decided at the close with data known "
                "by then, filled on later prices, costs on every trade, settings and filters chosen on 2006 - Oct 2021 "
                "and judged on Oct 2021 - Nov 6 2026. A missing price is never filled from a later date.</div>",
                unsafe_allow_html=True)
    st.subheader("Waves and crashes", help="How each strategy did in the moves people remember.")
    w = lab_table("windows").set_index(lab_table("windows").columns[0])
    w = w[[c for c in (LD, BR, SPY, QQQ) if c in w]]
    st.dataframe(w, width="stretch", key="pb_windows",
                 column_config={c: st.column_config.NumberColumn(format="percent") for c in w.columns})
    st.caption("Dive Zone shines in normal pullbacks and bear markets (2008: −10% vs SPY −46%; 2022: −7% vs −18%). "
               "Its weak spot is a fast sector-wide breakdown in the very leaders it buys, like Oct-Nov 2026. Breakout "
               "Rider is the reverse: it lags in chop and wins big in waves.")

    a, b = st.columns(2)
    with a:
        text_card("VIX and GEX filters: no help",
                  "We tried 11 entry filters on both strategies: VIX bands, VIX term structure (VIX above VIX3M), "
                  "SqueezeMetrics GEX above or below its 1-year median, GEX in its bottom 20%, positive GEX, and a "
                  "low-GEX-or-high-VIX combination. <b>None raised the Sharpe ratio on 2006-21</b>, and every one cut "
                  "returns, so none were added. Dive Zone already uses VIX where it helps: VIX above 20 counts as a "
                  "quality point and VIX above 25 lets it buy panics.", "sell")
        text_card("Crash guards: no help either",
                  "To dodge selloffs like Nov 2026 we tested 7 guards: market breadth, QQQ above its 50-day, SPY's "
                  "20-day drop, VIX spikes, the stock's sector above its 50-day, and the stock above its 50-day. A "
                  "breadth guard would have cut the Nov loss from 20% to 14%, but it lowered the Sharpe ratio on "
                  "2006-21, so adding it now would be fitting to the last month. Dive Zone stays as it is.", "")
    with b:
        text_card("Momentum rotation: dropped",
                  "Holding the 5-20 S&amp;P 500 or tech stocks with the best 6- or 12-month gain, re-picked monthly. "
                  "The best version on 2006-21 (top 5 tech, 6-month) made 22% a year but with a 38% worst drop and a "
                  "Sharpe of 0.61 in the last five years, and lost 30% in the Nov 2026 selloff. The 12-month S&amp;P "
                  "500 versions made 0-2% a year. Not good enough to keep.", "sell")
        text_card("Buying fear: a signal, not a strategy",
                  "Since 1999, QQQ bought the day after VIX closed above 30 was up 78% of the time 6 months later "
                  "(average +13%, vs +7% on a random day); above 40, 95% of the time (+24%). Buying a 4-6% down day "
                  "had no edge at all. As a stand-alone strategy (own QQQ for months after a VIX spike, cash "
                  "otherwise) it trailed simply holding QQQ, so it isn't one. The lesson: <b>a VIX close above 30 is "
                  "a good time to add to long-term holdings</b>, not to sell. VIX peaked at 28 on Nov 5 2026.", "buy")
    ev = lab_table("crash_events")
    show = ev[["Event", "Events", "3 months avg", "6 months avg", "6 months up", "12 months avg", "12 months up", "Latest"]]
    with st.expander("QQQ after fear events, since 1999"):
        st.dataframe(show, hide_index=True, width="stretch", key="pb_events", column_config={
            **{c: st.column_config.NumberColumn(format="percent") for c in
               ("3 months avg", "6 months avg", "6 months up", "12 months avg", "12 months up")},
            "Events": st.column_config.NumberColumn(help="Counted at most once every 20 trading days.")})
        st.caption("Bought at the next open after the event. 'Up' is the share of events where QQQ was higher by then.")
    with st.expander("Every filter result"):
        ft = lab_table("confluence_filters")
        st.dataframe(ft[["Strategy", "Filter", "pick Sharpe", "grade Sharpe", "pick Return per year", "grade Return per year",
                         "grade Worst drop", "Trades"]], hide_index=True, width="stretch", key="pb_filters",
                     column_config={c: st.column_config.NumberColumn(format="percent") for c in
                                    ("pick Return per year", "grade Return per year", "grade Worst drop")})
        gd = lab_table("dive_zone_guards")
        st.dataframe(gd[["Guard", "pick Sharpe", "grade Sharpe", "grade Return per year", "Nov 2026 selloff", "Trades"]],
                     hide_index=True, width="stretch", key="pb_guards",
                     column_config={c: st.column_config.NumberColumn(format="percent") for c in
                                    ("grade Return per year", "Nov 2026 selloff")})
        st.caption("'pick' is 2006 - Oct 2021, where a filter has to prove itself; 'grade' is the five years after.")
    text_card("Also retired: TQQQ Day + Night",
              "The intraday TQQQ pair made money in research, but its edge was 0.2-0.3% a trade, it needed a check "
              "every 30 minutes and an order before 15:50, and SharkFin is now aimed at mid-to-long-term growth "
              "investing. Classic Dive Zone (the original Leader Dip rules) is gone too: the current rules beat it "
              "every way.", "")


if view == LD:
    dive_zone_view()
elif view == BR:
    breakout_view()
elif view == BOTH:
    both_view()
else:
    notes_view()

st.caption("All research numbers are backtests after trading costs on the stocks that were in the S&P 500 on each date. "
           "Settings were picked on earlier data and graded on Oct 2021 - Nov 2026; the walk-forward tests on this page "
           "re-pick them every year. Past results don't guarantee future ones, and none of this is investment advice. "
           "SharkFin never places orders.")
ui.disclaimer()
