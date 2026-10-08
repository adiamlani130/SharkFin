"""Top Performers: multi-factor rankings, Leader Dip swing setups, core longs, the sector VST list and a check
that the ranking works."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import catalysts, data, factors, leader_dip, ratings, risk, ui
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
def sp500_gains() -> pd.Series:
    """Every S&P 500 stock's 6-month gain: the yardstick for Leader Dip's strength rank."""
    sp = data.download_prices(tuple(data.universe("S&P 500")), period="2y")
    return leader_dip.six_month_gain(sp.ffill()).iloc[-1].dropna() if not sp.empty else pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def market_close() -> pd.Series:
    m = data.market_history("2y")
    return m["Close"] if not m.empty else pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def sector_ratings(symbols: tuple, with_fund: bool, weights: tuple) -> pd.DataFrame:
    scores_, px_, info_ = scan(symbols, with_fund, weights)
    if scores_ is None:
        return pd.DataFrame()
    return ratings.ratings(px_, scores_["Sector"], info_ if with_fund else None, data.risk_free_rate())


@st.cache_data(ttl=1800, show_spinner=False)
def log_prices(symbols: tuple) -> dict:
    return data.download_ohlcv(symbols, period="6mo")


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

tabs = st.tabs(["Rankings", "Leader Dip setups", "Core longs", "Sector VST list", "Does the ranking work?"])


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


LOG = "leader_dip_log"


def log_signals(today: pd.DataFrame, asof, market_ok: bool | None):
    """Add today's signals to the saved log (one row per date and ticker)."""
    log = ui.load_list(LOG)
    seen = {(r.get("Date"), r.get("Symbol")) for r in log}
    day = f"{pd.Timestamp(asof):%Y-%m-%d}"
    new = [{"Date": day, "Symbol": sym_, "Close": round(float(r_["Price"]), 4), "Limit": round(float(r_["Limit"]), 4),
            "RSI2": round(float(r_["RSI2"]), 1), "Strength": round(float(r_["Strength"]), 3), "Market on": market_ok}
           for sym_, r_ in today.iterrows() if (day, sym_) not in seen]
    if new:
        ui.save_list(LOG, log + new)


def leader_dip_tab():
    st.markdown(
        "<div class='sf-note'><b>Leader Dip</b> buys a sharp two-day drop in one of the market's strongest stocks while "
        "the market is in an uptrend, and sells into the bounce. A stock signals when its <b>2-day RSI is below 10</b>, "
        "it is <b>above its 200-day average</b>, and its <b>6-month gain beats 70% of the S&amp;P 500</b>. "
        f"{ui.h(leader_dip.ENTRY_RULE)} {ui.h(leader_dip.EXIT_RULE)}</div>", unsafe_allow_html=True)
    mc = market_close()
    m_on = leader_dip.market_on(mc)
    switch = bool(m_on.iloc[-1]) if len(m_on) else None
    ref = sp500_gains()
    now = leader_dip.latest(px, ref if len(ref) else None)
    asof = px.index[-1]
    sig = now[now["Signal"]].sort_values("6-month gain", ascending=False)
    if switch is False:
        st.warning("Market switch is **off**: SPY closed below its 200-day average, so the system places no new trades. "
                   "Signals below are for reference only.")
    st.caption(f"Signals at the {asof:%b %d, %Y} close, strongest first. Leader Dip holds up to {leader_dip.SLOTS} "
               "trades at once, so with more signals than free slots, take them from the top.")
    if sig.empty:
        st.info("No stock in this list signalled at the last close. Leader Dip fires on only a few stocks a week, and "
                "less often in calm, rising markets.")
    else:
        if switch is not False:
            log_signals(sig, asof, switch)
        show = sig.join(scores[["Name", "Sector"]], how="left")
        st.dataframe(show[["Name", "Price", "Limit", "RSI2", "vs 200-day", "6-month gain", "Strength", "Sector"]],
                     width="stretch", column_config={
                         "Price": st.column_config.NumberColumn("Close", format="$%.2f"),
                         "Limit": st.column_config.NumberColumn("Limit buy (next session)", format="$%.2f",
                                                                help=tip("ld_limit")),
                         "RSI2": st.column_config.NumberColumn("2-day RSI", format="%.1f", help=tip("ld_rsi2")),
                         "vs 200-day": st.column_config.NumberColumn(format="percent"),
                         "6-month gain": st.column_config.NumberColumn(format="percent"),
                         "Strength": st.column_config.ProgressColumn("Strength rank", min_value=0, max_value=1,
                                                                     format="percent", help=tip("ld_strength"))})
    near = now[now["Uptrend"] & now["Leader"] & ~now["Signal"] & (now["RSI2"] < 30)].sort_values("RSI2")
    if len(near):
        with st.expander(f"Dips forming ({len(near)}): leaders in an uptrend with a 2-day RSI under 30"):
            st.dataframe(near.join(scores[["Name"]], how="left")[["Name", "Price", "RSI2", "6-month gain", "Strength"]],
                         width="stretch", column_config={
                             "Price": st.column_config.NumberColumn("Close", format="$%.2f"),
                             "RSI2": st.column_config.NumberColumn("2-day RSI", format="%.1f"),
                             "6-month gain": st.column_config.NumberColumn(format="percent"),
                             "Strength": st.column_config.ProgressColumn("Strength rank", min_value=0, max_value=1,
                                                                         format="percent")})
    log = pd.DataFrame(ui.load_list(LOG))
    with st.expander(f"Signal log ({len(log)} signals saved)", expanded=False):
        st.caption("Every signal this page shows while the market switch is on is saved here, then checked against what "
                   "happened next: did the limit fill, and how did the trade end under the exit rules? Over time this "
                   "shows whether live results match the backtest (about 67% winners, +1.4% a trade, ~6-day holds).")
        if log.empty:
            st.caption("Nothing logged yet.")
            return
        with st.spinner("Checking logged signals against prices since…"):
            fu = leader_dip.follow_up(log, log_prices(tuple(sorted(log["Symbol"].unique()))))
        filled = fu[fu["Filled"] == True]  # noqa: E712 (column holds True/False/None)
        closed = filled[filled["Status"] == "Closed"]
        decided = fu["Filled"].notna().sum()
        ui.metrics([
            {"label": "Signals logged", "value": f"{len(fu)}"},
            {"label": "Limit filled", "value": ui.fmt_pct(len(filled) / decided, 0) if decided else None,
             "help": "Share of signals where the next day's low reached the limit price."},
            {"label": "Closed trades", "value": f"{len(closed)}"},
            {"label": "Winning trades", "value": ui.fmt_pct((closed["Return"] > 0).mean(), 0) if len(closed) else None,
             "help": "Backtest: about 67%."},
            {"label": "Avg trade", "value": ui.fmt_pct(closed["Return"].mean(), 1, True) if len(closed) else None,
             "help": "Before costs. Backtest: about +1.4% after costs."},
        ], key="ldlog")
        st.dataframe(fu.iloc[::-1], hide_index=True, width="stretch", column_config={
            "Date": st.column_config.TextColumn("Signal date"),
            "Close": st.column_config.NumberColumn(format="$%.2f"),
            "Limit": st.column_config.NumberColumn(format="$%.2f"),
            "Strength": st.column_config.NumberColumn(format="percent"),
            "Fill price": st.column_config.NumberColumn(format="$%.2f"),
            "Exit date": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Exit price": st.column_config.NumberColumn(format="$%.2f"),
            "Return": st.column_config.NumberColumn(format="percent")})
        st.download_button("Download the log (CSV)", fu.to_csv(index=False).encode(), "leader_dip_log.csv", "text/csv")
        st.caption("The log is saved on the server next to your watchlist. A redeploy of the app can clear it, so "
                   "download a copy now and then.")


def vst_tab():
    st.markdown(
        "<div class='sf-note'>SharkFin's versions of VectorVest's ratings, each ranked <b>within the stock's own sector</b> "
        "on a 0-2 scale (1 = the sector's middle stock): <b>RV</b> value, <b>RT</b> price trend vs the market, "
        "<b>RS</b> safety, <b>CI</b> comfort (avoiding deep declines) and <b>VST</b>, which combines RV, RT and RS. "
        "<b>On their own the ratings barely predict next month's return.</b> What held up in the research was a steady "
        "weekly list: the 20 highest VSTs among stocks with a steady past-year climb, re-checked each Friday, holding "
        "a stock until it falls out of the top 60, and sitting in cash while the S&amp;P 500 is below its 10-month "
        "average. That made 10-11% a year in every test period with a worst drop of 16%: steadier than "
        "Leader Dip, not stronger.</div>", unsafe_allow_html=True)
    if not use_fund:
        st.info("Turn on **Include fundamentals and analyst data** above: RV needs each company's earnings.")
        return
    rat = sector_ratings(tuple(syms), use_fund, tuple(sorted(tw.items())))
    if rat.empty or rat["VST"].notna().sum() < 25:
        st.info("Not enough company data came back to rate this list. Pick a bigger universe or re-run in a few minutes.")
        return
    reg = leader_dip.regime(market_close()) if len(market_close()) else {}
    if reg.get("ten_month_on") is False:
        st.warning("The S&P 500 closed last month below its 10-month average, so this list's rule is to hold cash "
                   "until a month ends back above it.")
    elif reg.get("ten_month_on"):
        st.caption(f"The S&P 500 closed {reg['month_end']:%B} above its 10-month average, so the list is on.")
    top = ratings.vst_list(rat, scores["fip"] if "fip" in scores else None)
    show = top.join(scores[["Name", "Sector", "Price"]], how="left")
    cfg = {k: st.column_config.NumberColumn(ratings.NAMES[k], format="%.2f", help=ratings.HELP[k]) for k in ratings.NAMES}
    st.dataframe(show[["Name", "Sector", "Price", "VST", "RV", "RT", "RS", "CI", "VST rank"]], width="stretch",
                 column_config={**cfg, "Price": st.column_config.NumberColumn(format="$%.2f"),
                                "VST rank": st.column_config.NumberColumn("Rank in list", format="%d",
                                                                          help="Sell a holding once it drops below 60th.")})
    with st.expander("Every stock's ratings"):
        allr = rat.join(scores[["Name", "Sector"]], how="left").sort_values("VST", ascending=False)
        st.dataframe(allr[["Name", "Sector", "VST", "RV", "RT", "RS", "CI"]], width="stretch", height=420, column_config=cfg)
    st.caption("Ratings use today's prices and Yahoo's latest company data. Research & Valuation shows the same ratings "
               "for any single stock.")


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
    leader_dip_tab()

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
    vst_tab()

with tabs[4]:
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
