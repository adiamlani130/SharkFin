"""Top Performers: multi-factor rankings, swing setups, core longs and a check that the ranking works."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import catalysts, data, factors, risk, swing, ui
from sharkfin.explain import tip

ui.header("Top Performers",
          "Scores every stock in an index on the traits that have historically predicted returns (momentum, trend, "
          "low risk, value, quality, growth and analyst views), compared within its own sector, and ranks them.")

c1, c2, c3 = st.columns([2, 2, 2], vertical_alignment="bottom")
uni_name = c1.selectbox("Universe", ["S&P 500", "Nasdaq-100", "Dow 30", "S&P 500 + Nasdaq-100", "My watchlist + portfolio"])
use_fund = c2.toggle("Include fundamentals and analyst data", value=True,
                     help="Adds the Value, Quality, Growth and Analysts themes, and is needed for Core longs. Company "
                          "data for every stock is cached for 12 hours, so the first scan is slower.")
top_n = c3.slider("Show top / bottom", 5, 25, 10)

with st.expander("What counts, and how much"):
    st.caption("Each theme is scored in standard deviations versus the stock's own sector, then combined with these weights.")
    tw = {}
    cols = st.columns(4)
    for i, (theme, w) in enumerate(factors.DEFAULT_THEME_WEIGHTS.items()):
        if not use_fund and theme in factors.FUNDAMENTAL_FACTORS:
            continue
        tw[theme] = cols[i % 4].slider(theme, 0.0, 0.5, w, 0.05, key=f"tw_{theme}", help=factors.THEME_HELP[theme])


def get_universe(name):
    if name == "My watchlist + portfolio":
        return sorted(set(st.session_state.watchlist) | {p["symbol"] for p in st.session_state.portfolio})
    return data.universe(name)


@st.cache_data(ttl=3600, show_spinner=False)
def scan(symbols: tuple, with_fund: bool, weights: tuple):
    px = data.download_prices(symbols, period="2y")
    px = px.dropna(axis=1, thresh=int(len(px) * 0.8)) if len(px) else px
    if px.empty or px.shape[1] < 5:
        return None, None, None
    pf = factors.price_factor_frame(px)
    sectors, ff, names, info_df = None, None, pd.Series(dtype=object), pd.DataFrame()
    tab = data.sp500_table().set_index("Symbol")
    if with_fund:
        info_df = data.infos(tuple(px.columns))
        ff = factors.fundamental_factor_frame(info_df)
        sectors = info_df["sector"] if "sector" in info_df else None
        names = info_df["shortName"] if "shortName" in info_df else names
    if sectors is None or sectors.isna().all():
        sectors = tab["Sector"].reindex(px.columns) if "Sector" in tab else None
    scores = factors.composite_scores(pf, ff, sectors, dict(weights))
    scores["Sector"] = sectors.reindex(scores.index) if sectors is not None else None
    scores["Name"] = names.reindex(scores.index) if len(names) else tab["Name"].reindex(scores.index)
    scores["Price"] = px.iloc[-1].reindex(scores.index)
    return scores.dropna(subset=["Composite"]).sort_values("Composite", ascending=False), px, info_df


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def factor_backtest(symbols: tuple, weights: tuple):
    long = data.download_prices(symbols, period="5y")
    return factors.backtest_price_composite(long, theme_weights=dict(weights))


@st.cache_data(ttl=3600, show_spinner=False)
def swing_scan(symbols: tuple) -> pd.DataFrame:
    ohlcv = data.download_ohlcv(symbols, period="2y")
    if "Close" not in ohlcv:
        return pd.DataFrame()
    mkt = data.market_history("2y")
    mc = mkt["Close"] if not mkt.empty else None
    rows = []
    for s_ in ohlcv["Close"].columns:
        try:
            df = pd.DataFrame({f: ohlcv[f][s_] for f in ("Open", "High", "Low", "Close", "Volume") if f in ohlcv}).dropna()
            if len(df) < 260 or "Volume" not in df:
                continue
            plan = swing.trade_plan(df.iloc[-320:], mc)
        except Exception:
            continue
        if plan["tone"] == "neg":
            continue
        rows.append({"Symbol": s_, "Status": "Triggered" if plan["triggered"] else "Forming", "Score": plan["score"],
                     "Price": plan["price"], "Entry": plan["entry"], "Stop": plan["stop"], "Risk %": plan["risk_pct"],
                     "T1": plan["t1"], "T2": plan["t2"], "Resistance": plan["resistance"], "Weekly": plan["weekly"]["label"]})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).set_index("Symbol").sort_values(["Status", "Score"], ascending=[False, False])


syms = get_universe(uni_name)
if len(syms) < 5:
    st.info("Add at least 5 stocks to your watchlist or portfolio to scan them, or pick an index.")
    st.stop()

if not (st.button(f"Scan {len(syms)} stocks", type="primary", width="stretch") or st.session_state.get("scan_ran")):
    st.stop()
st.session_state.scan_ran = True
with st.status("Scanning…", expanded=False) as s:
    scores, px, info_df = scan(tuple(syms), use_fund, tuple(sorted(tw.items())))
    s.update(label=f"Scanned {len(scores)} stocks" if scores is not None else "Scan failed",
             state="complete" if scores is not None else "error")
if scores is None:
    st.error("Couldn't download prices for this universe right now. Try again in a minute.")
    st.stop()

themes = [t for t in factors.DEFAULT_THEME_WEIGHTS if t in scores.columns]
top_n = min(top_n, len(scores) // 2)
n_fund = int(info_df["sector"].notna().sum()) if use_fund and "sector" in info_df else 0
if use_fund and n_fund < 0.8 * len(scores):
    st.warning(f"Yahoo only returned company data for {n_fund} of {len(scores)} stocks (it rate-limits bursts of requests), "
               "so fundamental themes are missing for the rest. Re-run the scan in a few minutes to fill them in.")

tabs = st.tabs(["Rankings", "Swing setups", "Core longs", "Does the ranking work?"])


def card(row, sym, kind):
    pos, neg = factors.explain(row)
    drivers = "".join(ui.pill(p, "pos") for p in pos) + "".join(ui.pill(n, "neg") for n in neg)
    sub = " · ".join(ui.h(x) for x in (row.get("Name"), row.get("Sector")) if isinstance(x, str) and x)
    st.markdown(
        f"<div class='sf-card {kind}'><span class='t'>{sym}</span> <span class='sf-muted'>{sub}</span>"
        f"<div class='row'>Score <b>{row['Composite']:+.2f}</b> · beats {row['Percentile']:.0f}% of the list · "
        f"{ui.h(ui.fmt_money(row['Price']))} · 1M {ui.fmt_pct(row.get('ret_1m'), 1, True)} · "
        f"12M {ui.fmt_pct(row.get('mom_12_1'), 0, True)}</div><div class='row'>{drivers}</div></div>",
        unsafe_allow_html=True)


with tabs[0]:
    l, r = st.columns(2)
    with l:
        st.subheader(f"Top {top_n}", help="The strongest overall profile right now.")
        for sym_, row in scores.head(top_n).iterrows():
            card(row, sym_, "buy")
    with r:
        st.subheader(f"Bottom {top_n}", help="The weakest overall profile: the stocks the factors say to avoid.")
        for sym_, row in scores.tail(top_n).iloc[::-1].iterrows():
            card(row, sym_, "sell")
    st.subheader("Full ranking", help="Theme columns are standard deviations above (+) or below (−) the stock's sector "
                                      "average. Hover a column name for what it measures.")
    show = ["Name", "Sector", "Price", "Composite", "Percentile", *themes, "ret_1m", "mom_12_1", "volatility"]
    show = [c for c in show if c in scores.columns]
    st.dataframe(scores[show], width="stretch", height=460, column_config={
        "Price": st.column_config.NumberColumn(format="$%.2f"),
        "Composite": st.column_config.NumberColumn("Score", format="%+.2f", help="Weighted blend of the theme scores."),
        "Percentile": st.column_config.ProgressColumn("Rank", min_value=0, max_value=100, format="%.0f",
                                                      help="Share of the list this stock beats."),
        "ret_1m": st.column_config.NumberColumn("1M", format="percent"),
        "mom_12_1": st.column_config.NumberColumn("12M (ex last month)", format="percent"),
        "volatility": st.column_config.NumberColumn("Volatility", format="percent"),
        **{t: st.column_config.NumberColumn(format="%+.2f", help=factors.THEME_HELP[t]) for t in themes},
    })
    st.download_button("Download ranking (CSV)", scores[show].to_csv().encode(), "sharkfin_scan.csv", "text/csv")

with tabs[1]:
    st.markdown("<div class='sf-note'>Stocks where the <b>Confluence Pullback</b> swing setup has triggered today or is "
                "forming: the market and the stock are in uptrends, price has pulled back to the 20-day EMA or 50-day "
                "average, and enough confirming signals line up. Strategy Lab → Swing system shows how it has performed.</div>",
                unsafe_allow_html=True)
    if st.button(f"Check {px.shape[1]} charts for setups", key="swing_scan"):
        st.session_state.swing_ran = True
    if st.session_state.get("swing_ran"):
        with st.spinner("Checking every chart…"):
            setups = swing_scan(tuple(px.columns))
        if setups.empty:
            st.info("No stock passes the must-pass rules today. That's normal in a weak or choppy market.")
        else:
            setups = setups.join(scores[["Name", "Sector"]], how="left")
            n_trig = int((setups["Status"] == "Triggered").sum())
            st.caption(f"{n_trig} triggered today (buy at the next open) and {len(setups) - n_trig} forming "
                       "(buy only above today's high).")
            st.dataframe(setups[["Name", "Status", "Score", "Price", "Entry", "Stop", "Risk %", "T1", "T2", "Resistance",
                                 "Weekly", "Sector"]], width="stretch", column_config={
                "Status": st.column_config.TextColumn(help=tip("trade_status")),
                "Score": st.column_config.ProgressColumn(min_value=0, max_value=6, format="%d", help=tip("min_score")),
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Entry": st.column_config.NumberColumn(format="$%.2f", help=tip("entry")),
                "Stop": st.column_config.NumberColumn(format="$%.2f", help=tip("stop")),
                "Risk %": st.column_config.NumberColumn(format="percent", help=tip("risk_r")),
                "T1": st.column_config.NumberColumn("Target 1", format="$%.2f", help=tip("t1")),
                "T2": st.column_config.NumberColumn("Target 2", format="$%.2f", help=tip("t2")),
                "Resistance": st.column_config.NumberColumn(format="$%.2f", help=tip("resistance")),
                "Weekly": st.column_config.TextColumn("Weekly trend", help=tip("weekly_trend")),
            })
            st.caption("Open a ticker on Research & Valuation → Trade setup for the full checklist and chart.")

with tabs[2]:
    st.markdown(f"<div class='sf-note'>{catalysts.CORE_LONG_INTRO}</div>", unsafe_allow_html=True)
    if not use_fund:
        st.info("Turn on **Include fundamentals and analyst data** above to build the core-long list.")
    else:
        core, funnel = catalysts.core_long_screen(scores, info_df)
        with st.expander("The rules, and how many stocks pass each one", expanded=core.empty):
            fdf = pd.DataFrame(funnel)
            st.dataframe(fdf, hide_index=True, width="stretch", column_config={
                "Rule": st.column_config.TextColumn(width="medium"),
                "Still in": st.column_config.ProgressColumn(min_value=0, max_value=int(fdf["Still in"].max() or 1), format="%d"),
                "Why": st.column_config.TextColumn(width="large")})
        if core.empty:
            st.info("No stock passes every rule in this universe right now. The table above shows which rule removed "
                    "the most; in a falling market the trend rules can screen out almost everything, which is the point.")
        else:
            cols = [c for c in ("Name", "Sector", "Price", "Core score", "mom_12_1", "fip", "Value", "volatility",
                                "roe", "fcf_yield", "earnings_yield") if c in core]
            st.dataframe(core[cols], width="stretch", column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Core score": st.column_config.NumberColumn(format="%+.2f", help=catalysts.CORE_SCORE_HELP),
                "Value": st.column_config.NumberColumn("Value vs sector", format="%+.2f", help=factors.THEME_HELP["Value"]),
                "fip": st.column_config.ProgressColumn("Steady climb", min_value=-0.2, max_value=0.2, format="%+.2f",
                                                       help="Share of up days minus share of down days over the past year (skipping the last month)."),
                "roe": st.column_config.NumberColumn("ROE", format="percent"),
                "fcf_yield": st.column_config.NumberColumn("FCF yield", format="percent"),
                "earnings_yield": st.column_config.NumberColumn("Earnings yield", format="percent"),
                "mom_12_1": st.column_config.NumberColumn("12M return", format="percent"),
                "volatility": st.column_config.NumberColumn("Volatility", format="percent"),
            })
            st.caption("For a passive core, hold 15-30 of these across different sectors and re-check quarterly rather "
                       "than concentrating. Check each one on Research & Valuation → Trade setup (long-term checklist).")

with tabs[3]:
    st.markdown("<div class='sf-note'>A ranking is only useful if the stocks at the top actually go on to do better. "
                "This replays the last ~4 years: every month, buy the top 20% of this list by the <b>price-based</b> themes "
                "(momentum, trend, low risk, reversal) using only the data available at the time, hold for a month, "
                "pay trading costs, repeat. Fundamentals are left out because free data doesn't have their history.</div>",
                unsafe_allow_html=True)
    with st.spinner("Replaying the ranking month by month…"):
        try:
            bt = factor_backtest(tuple(px.columns), tuple(sorted(tw.items())))
        except ValueError as e:
            st.warning(str(e))
            bt = None
    if bt:
        s_stats = risk.summary(bt["strategy"], bt["benchmark"])
        b_stats = risk.summary(bt["benchmark"])
        edge = s_stats["CAGR"] - b_stats["CAGR"]
        verdict = ("The top of the ranking beat the average stock" if edge > 0.01 else
                   "The top of the ranking did about the same as the average stock" if edge > -0.01 else
                   "The top of the ranking lagged the average stock")
        st.markdown(f"<div class='sf-card'>{ui.pill('Worked' if edge > 0.01 else 'Mixed' if edge > -0.01 else 'Did not work', 'pos' if edge > 0.01 else 'neu' if edge > -0.01 else 'neg')}"
                    f"<span class='sf-note'>{verdict}: <b>{s_stats['CAGR']:.1%}</b> a year vs <b>{b_stats['CAGR']:.1%}</b> "
                    f"for an equal-weight basket of the same stocks, and the ranking pointed the right way in "
                    f"<b>{bt['hit_rate']:.0%}</b> of months.</span></div>", unsafe_allow_html=True)
        eq = pd.DataFrame({"Top 20% each month": (1 + bt["strategy"]).cumprod() * 10_000,
                           "Average stock in the list": (1 + bt["benchmark"]).cumprod() * 10_000})
        fig = go.Figure([go.Scatter(x=eq.index, y=eq[c], name=c, line=dict(width=2 if i == 0 else 1.5,
                                                                          color=ui.GREEN if i == 0 else ui.MUTED))
                         for i, c in enumerate(eq)])
        fig.update_layout(title="What $10,000 became", yaxis=dict(tickprefix="$", tickformat=",.0f"), hovermode="x unified")
        ui.plotly(fig, 400)
        ui.metrics([
            {"label": "Return per year", "value": ui.fmt_pct(s_stats["CAGR"]), "delta": f"{edge:+.1%} vs average",
             "delta_color": "normal"},
            {"label": "Worst drop", "value": ui.fmt_pct(s_stats["Max Drawdown"]),
             "delta": f"average {ui.fmt_pct(b_stats['Max Drawdown'])}", "delta_color": "off", "delta_arrow": "off"},
            {"label": "Sharpe ratio", "value": ui.fmt_num(s_stats["Sharpe"]),
             "delta": f"average {ui.fmt_num(b_stats['Sharpe'])}", "delta_color": "off", "delta_arrow": "off",
             "help": tip("Sharpe")},
            {"label": "Right direction", "value": ui.fmt_pct(bt["hit_rate"], 0),
             "help": "Share of months where higher-ranked stocks did better than lower-ranked ones (positive rank "
                     f"correlation). The average correlation was {bt['ic_mean']:.3f}; anything above ~0.03 is useful."},
            {"label": "Portfolio turnover", "value": ui.fmt_pct(bt["avg_turnover"], 0),
             "help": "Share of the portfolio replaced each month. Higher turnover means more trading costs (10 bps charged)."},
        ], key="btm")
        st.caption("Caveat: this uses today's index members, so companies that were dropped (often the big losers) are "
                   "missing, which flatters both lines. Past results don't guarantee future ones.")

ui.disclaimer()
