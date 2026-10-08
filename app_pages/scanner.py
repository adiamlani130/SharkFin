"""Top Performers: multi-factor rankings, swing setups for the chosen swing strategy, core longs, a could-run screen,
the sector VST list and an honest check of whether the ranking works."""

import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import builder, catalysts, data, factors, leader_dip, ratings, risk, swing, ui
from sharkfin.explain import tip

ui.header("Top Performers",
          "Scores every stock in an index on momentum, trend, short-term reversal, earnings surprises, value, quality "
          "and growth, each compared within its own sector, and ranks them. Weights come from a 2000-2026 test.")

c1, c2, c3 = st.columns([2, 2, 2], vertical_alignment="bottom")
uni_name = c1.selectbox("Universe", ["S&P 500", "Nasdaq-100", "Dow 30", "S&P 500 + Nasdaq-100", "My watchlist + portfolio"])
use_fund = c2.toggle("Include fundamentals and earnings", value=True,
                     help="Adds the Earnings, Value, Quality, Growth and Analysts themes, and is needed for Core longs. "
                          "Company data is kept for 12 hours and earnings history until each company reports again, so "
                          "only the first scan is slow.")
top_n = c3.slider("Show top / bottom", 5, 25, 10)

with st.expander("What counts, and how much"):
    st.caption("Each theme is scored in standard deviations versus the stock's own sector, then combined with these weights. "
               "The defaults come from the 2000-2026 test on the last tab; Low Risk and Analysts start at zero because "
               "they pointed the wrong way there. Hover a slider for what the test found.")
    tw = {}
    cols = st.columns(4)
    for i, (theme, w) in enumerate(factors.DEFAULT_THEME_WEIGHTS.items()):
        if not use_fund and (theme in factors.FUNDAMENTAL_FACTORS or theme in factors.EARNINGS_FACTORS):
            continue
        tw[theme] = cols[i % 4].slider(theme, 0.0, 0.5, w, 0.05, key=f"tw_{theme}", help=factors.THEME_HELP[theme])


def get_universe(name):
    if name == "My watchlist + portfolio":
        return sorted(set(st.session_state.watchlist) | {p["symbol"] for p in st.session_state.portfolio})
    return data.universe(name)


@data.ttl_cache(1800)
def scan_data(symbols: tuple, with_fund: bool) -> dict | None:
    """Everything a scan needs except the weights, so moving a weight slider only re-scores."""
    px = data.download_prices(symbols, period="2y")
    px = px.dropna(axis=1, thresh=int(len(px) * 0.8)) if len(px) else px
    if px.empty or px.shape[1] < 5:
        return None
    out = {"px": px, "pf": factors.price_factor_frame(px), "ff": None, "ef": None, "sectors": None,
           "names": pd.Series(dtype=object), "info": pd.DataFrame()}
    tab = data.sp500_table().set_index("Symbol")
    if with_fund:
        info_df = data.infos(symbols).reindex(px.columns)
        out.update(info=info_df, ff=factors.fundamental_factor_frame(info_df),
                   ef=factors.earnings_factor_frame({s: e for s, e in data.earnings_histories(symbols).items()
                                                     if s in px.columns}),
                   sectors=info_df["sector"] if "sector" in info_df else None,
                   names=info_df["shortName"] if "shortName" in info_df else out["names"])
    if out["sectors"] is None or out["sectors"].isna().all():
        out["sectors"] = tab["Sector"].reindex(px.columns) if "Sector" in tab else None
    if not len(out["names"]):
        out["names"] = tab["Name"].reindex(px.columns) if "Name" in tab else out["names"]
    return out


def load_scan(symbols: tuple, with_fund: bool, slot) -> dict | None:
    """Download what the scan needs with a progress bar, then build it. Each download is cached as soon as it
    finishes, so a scan interrupted by a settings change resumes where it stopped."""
    if scan_data.cached(symbols, with_fund):
        return scan_data(symbols, with_fund)
    jobs = [(data.download_prices, (symbols,), {"period": "2y"})]
    if with_fund:
        need_info = not getattr(data.infos, "cached", lambda *a: False)(symbols)
        need_earn = not getattr(data.earnings_histories, "cached", lambda *a: False)(symbols)
        for s in symbols:  # interleaved, so the slow earnings pages don't wait behind the company data
            jobs += [(data.earnings_history, (s,))] * need_earn + [(data.info, (s,))] * need_info
    with slot.container(), st.status(f"Scanning {len(symbols)} stocks…", expanded=True) as box:
        what = "prices, company data and earnings history" if with_fund else "prices"
        bar = st.progress(0.0, text=f"Downloading {what}…")
        st.caption("Earnings history is the slow part the first time (Yahoo serves it one stock at a time). It is "
                   "saved until each company reports again, so later scans are much quicker.")

        def tick(done, total):
            bar.progress(done / total, text=f"Downloading {what}: {done:,} of {total:,} done")

        data.prefetch(jobs, progress=tick)
        box.update(label="Scoring…")
        out = scan_data(symbols, with_fund)
        box.update(label=f"Scanned {out['px'].shape[1]} stocks" if out else "Scan failed",
                   state="complete" if out else "error", expanded=False)
    return out


@st.cache_data(ttl=1800, show_spinner=False)
def scan(symbols: tuple, with_fund: bool, weights: tuple):
    d = scan_data(symbols, with_fund)
    if d is None:
        return None, None, None
    scores = factors.composite_scores(d["pf"], d["ff"], d["sectors"], dict(weights), earn_f=d["ef"])
    scores["Sector"] = d["sectors"].reindex(scores.index) if d["sectors"] is not None else None
    scores["Name"] = d["names"].reindex(scores.index)
    scores["Price"] = d["px"].iloc[-1].reindex(scores.index)
    return scores.dropna(subset=["Composite"]).sort_values("Composite", ascending=False), d["px"], d["info"]


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def factor_backtest(symbols: tuple, weights: tuple, with_earnings: bool):
    long = data.download_prices(symbols, period="5y")
    earn = data.earnings_histories(symbols) if with_earnings else None
    return factors.backtest_price_composite(long, theme_weights=dict(weights), earnings=earn or None)


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

# The scan runs for the settings that were current when Scan was pressed. Weight changes only re-score, so they
# apply at once; a new universe or the fundamentals toggle needs another press, because it means new downloads.
want = (uni_name, tuple(syms), bool(use_fund))
if st.button(f"Scan {len(syms)} stocks", type="primary", width="stretch"):
    st.session_state.scan_req = want
req = st.session_state.get("scan_req")
if req is None:
    st.stop()
note = st.empty()  # one fixed spot for the progress or a settings notice, so the tabs below never shift
req_name, req_syms, req_fund = req
if req != want:
    what = f"{req_name} {'with' if req_fund else 'without'} fundamentals"
    if not scan_data.cached(req_syms, req_fund):
        note.info(f"You changed the settings while {what} was scanning, so that scan stopped. Press **Scan** to scan "
                "with the new settings. Downloads that already finished are kept.")
        st.stop()
    note.info(f"Showing the last scan ({what}). Press **Scan** to update it to the new settings.")
if load_scan(req_syms, req_fund, note) is None:
    st.error("Couldn't download prices for this universe right now. Try again in a minute.")
    st.stop()
use_fund = req_fund
for theme, w in factors.DEFAULT_THEME_WEIGHTS.items():
    if theme in factors.FUNDAMENTAL_FACTORS or theme in factors.EARNINGS_FACTORS:
        if use_fund:
            tw.setdefault(theme, st.session_state.get(f"tw_{theme}", w))
        else:
            tw.pop(theme, None)
scores, px, info_df = scan(req_syms, use_fund, tuple(sorted(tw.items())))
syms = list(req_syms)

themes = [t for t in factors.DEFAULT_THEME_WEIGHTS if t in scores.columns]
top_n = min(top_n, len(scores) // 2)
n_fund = int(info_df["sector"].notna().sum()) if use_fund and "sector" in info_df else 0
if use_fund and n_fund < 0.8 * len(scores):
    st.warning(f"Yahoo only returned company data for {n_fund} of {len(scores)} stocks (it rate-limits bursts of requests), "
               "so fundamental themes are missing for the rest. Re-run the scan in a few minutes to fill them in.")

# Only the open tab runs, so the slower ones (the replay, the swing scan) cost nothing until opened.
tabs = st.tabs(["Rankings", "Swing setups", "Core longs", "Could run", "Sector VST list", "Does the ranking work?"],
               key="tp_view", on_change="rerun")


def card(row, sym, kind):
    pos, neg = factors.explain(row, weights=tw)
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


@st.cache_data(ttl=3600, show_spinner=False)
def universe_ohlcv(symbols: tuple) -> dict:
    return data.download_ohlcv(symbols, period="2y")


@st.cache_data(ttl=3600, show_spinner=False)
def rule_signals(symbols: tuple, rules_json: str) -> pd.DataFrame:
    return swing.scan(universe_ohlcv(symbols), json.loads(rules_json), market_close())


def swing_tab():
    c1, c2 = st.columns([2, 5], vertical_alignment="bottom")
    with c1:
        name = ui.swing_picker("tp")
    c2.caption(swing.about(name))
    if name == swing.LEADER_DIP:
        leader_dip_tab()
        return
    rules_ = swing.rules(name, ui.my_swing_rules())
    if not rules_ or not rules_.get("entry"):
        st.info("This strategy has no buy rules yet. Build one in Strategy Lab → Build and test.")
        return
    buy_txt, sell_txt = builder.describe_strategy(rules_)
    st.markdown(f"<div class='sf-note'><b>Buys</b> at the next open when {ui.h(buy_txt)}. <b>Sells</b> when "
                f"{ui.h(sell_txt)}. {ui.h(swing.NOTE_UNTESTED.split(' The backtest')[0])} Strategy Lab can backtest it "
                "on any stock.</div>", unsafe_allow_html=True)
    with st.spinner("Checking every stock against the rules…"):
        sig = rule_signals(tuple(px.columns), json.dumps(rules_, sort_keys=True, default=str))
    st.caption(f"Stocks whose buy rules all held at the {px.index[-1]:%b %d, %Y} close.")
    if sig.empty:
        st.info("No stock in this list meets the buy rules at the last close.")
        return
    show = sig.join(scores[["Name", "Sector"]], how="left")
    st.dataframe(show[["Name", "Sector", "Price", "1-day change", "1-month change", "Signals in the last 20 days"]],
                 width="stretch", column_config={
                     "Price": st.column_config.NumberColumn("Close", format="$%.2f"),
                     "1-day change": st.column_config.NumberColumn(format="percent"),
                     "1-month change": st.column_config.NumberColumn(format="percent"),
                     "Signals in the last 20 days": st.column_config.NumberColumn(
                         help="Days in the last 20 when the buy rules held. Rules like 'is above' stay true for a "
                              "while; 1 means the signal is new.")})


def could_run_tab():
    st.markdown(f"<div class='sf-note'>{catalysts.COULD_RUN_INTRO}</div>", unsafe_allow_html=True)
    if not use_fund:
        st.info("Turn on **Include fundamentals and earnings** above: the last rule needs each company's earnings.")
        return
    picks, funnel = catalysts.could_run(scores, px)
    with st.expander("The rules, and how many stocks pass each one", expanded=picks.empty):
        fdf = pd.DataFrame(funnel)
        st.dataframe(fdf, hide_index=True, width="stretch", column_config={
            "Still in": st.column_config.ProgressColumn(min_value=0, max_value=int(fdf["Still in"].max() or 1), format="%d"),
            "Why": st.column_config.TextColumn(width="large")})
    if picks.empty:
        st.info("No stock passes all four rules right now.")
    else:
        cols = [c for c in ("Name", "Sector", "Price", "6-month gain", "volatility", "trend_200", "eps_surprise",
                            "eps_yoy", "Percentile") if c in picks]
        st.dataframe(picks[cols], width="stretch", column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "6-month gain": st.column_config.NumberColumn(format="percent"),
            "volatility": st.column_config.NumberColumn("Volatility", format="percent"),
            "trend_200": st.column_config.NumberColumn("vs 200-day", format="percent"),
            "eps_surprise": st.column_config.NumberColumn("Last EPS surprise", format="%+.1f%%"),
            "eps_yoy": st.column_config.NumberColumn("EPS vs a year ago", format="percent",
                                                     help="Over +25% raised the odds of a big winner after 2013, but "
                                                          "lowered them in 2002-12."),
            "Percentile": st.column_config.ProgressColumn("Overall rank", min_value=0, max_value=100, format="%.0f")})
    st.markdown("**How past lists did over the next 12 months**")
    odds = catalysts.COULD_RUN_ODDS
    st.dataframe(odds, hide_index=True, width="stretch", column_config={
        "Top-5% winner": st.column_config.NumberColumn(format="percent", help="Ended up among the year's top 5% of members."),
        "Top-5% loser": st.column_config.NumberColumn(format="percent", help="Ended up among the year's worst 5%."),
        "Doubled": st.column_config.NumberColumn(format="percent", help="Gained 100% or more."),
        "vs average stock": st.column_config.NumberColumn("Avg return vs average stock", format="percent")})
    st.caption("Same point-in-time S&P 500 test as the last tab. Stocks that later left the index are partly missing "
               "before 2013, which flatters every row a little.")


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
    if tabs[0].open is not False:
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
    if tabs[1].open is not False:
        swing_tab()

with tabs[2]:
    if tabs[2].open is not False:
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
    if tabs[3].open is not False:
        could_run_tab()

with tabs[4]:
    if tabs[4].open is not False:
        vst_tab()

RESEARCH_TAKEAWAYS = [
    "<b>No ranking built from public data reliably picks S&amp;P 500 winners.</b> Over 2000-2026 we tested 50 signals "
    "one by one, in blends and with a machine-learning model trained only on past data. The best blend pointed the "
    "right way in 60% of months, and its top 20% beat the average stock by under 1% a year. Professional quant funds "
    "work with edges about this size; anyone promising 70% accuracy on big stocks is overfitting.",
    "<b>Analyst price targets and ratings did not help.</b> Across 2012-2026 (about 200,000 rating and target changes) a "
    "big gap to the target came slightly more often before big losers than big winners, and upgrades, downgrades, "
    "initiations and target raises left the next 3-12 months about where the average stock went.",
    "<b>Insider buying did not help in big companies.</b> Of 11,700 open-market purchases by officers and directors of "
    "S&amp;P 500 members (2004-2026), even CEO buys and clusters of three or more insiders did no better than average "
    "over the next 6-12 months. The famous insider effect lives in small companies.",
    "<b>What came before big winners:</b> volatility, more than anything. The Could run tab shows that profile and "
    "its honest odds.",
    "<b>What the defaults changed:</b> Low Risk and Analysts start at zero (they pointed the wrong way), an Earnings "
    "theme was added (steady in both halves), Momentum now rewards a steady climb instead of closeness to the 52-week "
    "high, and Reversal looks at the last month as well as the last week.",
]

with tabs[5]:
    if tabs[5].open is not False:
        st.markdown("<div class='sf-note'>A ranking is only useful if the stocks at the top go on to do better. This tab "
                    "has two checks: a <b>24-year test</b> on the stocks that were actually in the S&amp;P 500 at each "
                    "date, and a <b>replay of the last ~4 years</b> on this list with your weights.</div>",
                    unsafe_allow_html=True)
        st.subheader("What 24 years of testing found",
                     help="Point-in-time S&P 500 members, 2000-2026: every month, buy the top 20% by score, hold a month, "
                          "compare with the equal-weight average of the members. Earnings history starts in 2002 and analyst "
                          "history in 2012; fundamental themes were tested with earnings yield, dividend yield and earnings "
                          "stability, the parts with history.")
        st.markdown("<div class='sf-card'>" + "".join(f"<div class='row'>{t}</div>" for t in RESEARCH_TAKEAWAYS) + "</div>",
                    unsafe_allow_html=True)
        st.dataframe(factors.RESEARCH, hide_index=True, width="stretch", column_config={
            "Ranking": st.column_config.TextColumn(width="large"),
            "Top 20% vs average": st.column_config.NumberColumn(format="percent",
                                                                help="Yearly return of the top 20% minus the average member."),
            "Right direction": st.column_config.NumberColumn(format="percent",
                                                             help="Share of months where higher scores went on to do better.")})

        st.subheader("Replay: the last ~4 years with your weights")
        with_earn = bool(use_fund and tw.get("Earnings", 0) > 0)
        replayed = [t for t in factors.REPLAYABLE if tw.get(t, 0) > 0 and (with_earn or t in factors.PRICE_FACTORS)]
        st.caption("Every month, buy the top 20% of this list using only what was known then, hold a month, pay trading "
                   f"costs, repeat. It can rebuild {', '.join(replayed) if replayed else 'no theme'} from history; Value, "
                   "Quality, Growth and Analysts are left out because free data doesn't keep their past values.")
        with st.spinner("Replaying the ranking month by month…"):
            try:
                bt = factor_backtest(tuple(px.columns), tuple(sorted(tw.items())), with_earn)
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
            st.markdown(f"<div class='sf-card'>{ui.pill('Ahead' if edge > 0.01 else 'Even' if edge > -0.01 else 'Behind', 'pos' if edge > 0.01 else 'neu' if edge > -0.01 else 'neg')}"
                        f"<span class='sf-note'>{verdict}: <b>{s_stats['CAGR']:.1%}</b> a year vs <b>{b_stats['CAGR']:.1%}</b> "
                        f"for an equal-weight basket of the same stocks. The top 20% beat the basket in "
                        f"<b>{bt['beat_rate']:.0%}</b> of months. Four years is short: the 24-year test above is the better "
                        "guide to what to expect.</span></div>", unsafe_allow_html=True)
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
                {"label": "Months ahead", "value": ui.fmt_pct(bt["beat_rate"], 0),
                 "help": "Share of months the top 20% returned more than the equal-weight basket."},
                {"label": "Right direction", "value": ui.fmt_pct(bt["hit_rate"], 0),
                 "help": "Share of months where higher-ranked stocks did better than lower-ranked ones across the whole list "
                         f"(positive rank correlation; the average was {bt['ic_mean']:.3f}). Real signals in big stocks "
                         "land around 52-60%."},
                {"label": "Portfolio turnover", "value": ui.fmt_pct(bt["avg_turnover"], 0),
                 "help": "Share of the portfolio replaced each month. Higher turnover means more trading costs (10 bps charged)."},
            ], key="btm")
            st.caption("Caveat: the replay uses today's index members, so companies that were dropped (often the big losers) "
                       "are missing, which flatters both lines. Past results don't guarantee future ones.")

ui.disclaimer()
