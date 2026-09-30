"""Top Performers: cross-sectional multi-factor scanner with a factor backtest."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import catalysts, data, factors, risk, swing, ui
from sharkfin.explain import tip

st.title("Top Performers")
st.caption("Every stock in the universe is scored on documented return factors (momentum, trend, low risk, value, "
           "quality, growth, analyst revisions), winsorised and z-scored within its sector, then combined into one "
           "composite rank. Prices are downloaded in batches, so a full S&P 500 scan takes seconds, not minutes.")

c1, c2, c3 = st.columns([2, 2, 2])
uni_name = c1.selectbox("Universe", ["S&P 500", "Nasdaq-100", "Dow 30", "S&P 500 + Nasdaq-100", "My watchlist + portfolio"])
use_fund = c2.toggle("Include fundamentals & analyst data", value=True,
                     help="Adds Value, Quality, Growth and Analyst themes. Fetches company data for every stock "
                          "(cached for 12 hours), so the first run is slower.")
top_n = c3.slider("Show top / bottom", 5, 25, 10)

with st.expander("Factor weights", expanded=False):
    tw = {}
    cols = st.columns(4)
    for i, (theme, w) in enumerate(factors.DEFAULT_THEME_WEIGHTS.items()):
        if not use_fund and theme in factors.FUNDAMENTAL_FACTORS:
            continue
        tw[theme] = cols[i % 4].slider(theme, 0.0, 0.5, w, 0.05, key=f"tw_{theme}")


def get_universe(name):
    if name == "My watchlist + portfolio":
        return sorted(set(st.session_state.watchlist) | {p["symbol"] for p in st.session_state.portfolio})
    return data.universe(name)


@st.cache_data(ttl=3600, show_spinner=False)
def scan(symbols: tuple, with_fund: bool, weights: tuple):
    px = data.download_prices(symbols, period="2y")
    px = px.dropna(axis=1, thresh=int(len(px) * 0.8)) if len(px) else px
    if px.empty or px.shape[1] < 5:
        return None, None
    pf = factors.price_factor_frame(px)
    sectors, ff, names = None, None, pd.Series(dtype=object)
    tab = data.sp500_table().set_index("Symbol")
    if with_fund:
        info_df = data.infos(tuple(px.columns))
        ff = factors.fundamental_factor_frame(info_df)
        sectors = info_df.get("sector")
        names = info_df.get("shortName", names)
    if sectors is None or sectors.isna().all():
        sectors = tab["Sector"].reindex(px.columns) if "Sector" in tab else None
    scores = factors.composite_scores(pf, ff, sectors, dict(weights))
    scores["Sector"] = sectors.reindex(scores.index) if sectors is not None else None
    scores["Name"] = names.reindex(scores.index) if len(names) else tab["Name"].reindex(scores.index)
    scores["Price"] = px.iloc[-1].reindex(scores.index)
    return scores.dropna(subset=["Composite"]).sort_values("Composite", ascending=False), px


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
    st.info("Add at least 5 stocks to your watchlist/portfolio to scan them, or pick an index universe.")
    st.stop()

if st.button(f"Run scan on {len(syms)} stocks", type="primary", width="stretch") or st.session_state.get("scan_ran"):
    st.session_state.scan_ran = True
    with st.status("Scanning…", expanded=False) as s:
        scores, px = scan(tuple(syms), use_fund, tuple(sorted(tw.items())))
        s.update(label="Scan complete" if scores is not None else "Scan failed", state="complete" if scores is not None else "error")
    if scores is None:
        st.error("Couldn't download prices for this universe right now.")
        st.stop()

    themes = [t for t in factors.DEFAULT_THEME_WEIGHTS if t in scores.columns]
    top_n = min(top_n, len(scores) // 2)
    tabs = st.tabs(["🏆 Rankings", "🎯 Swing setups", "🏛️ Core longs", "🗺️ Factor map", "📊 Backtest"])

    def card(row, sym, kind):
        pos, neg = factors.explain(row)
        drivers = " ".join(ui.pill(p, "pos") for p in pos) + " ".join(ui.pill(n, "neg") for n in neg)
        st.markdown(
            f"<div class='sf-card {kind}'><b style='font-size:1.1rem'>{sym}</b> "
            f"<span class='sf-muted'>{row.get('Name') or ''} · {row.get('Sector') or ''}</span><br>"
            f"Composite <b>{row['Composite']:+.2f}σ</b> · {row['Percentile']:.0f}th percentile · "
            f"${row['Price']:,.2f} · 1M {ui.fmt_pct(row.get('ret_1m'), 1, True)} · "
            f"12-1M {ui.fmt_pct(row.get('mom_12_1'), 0, True)}<br>{drivers}</div>", unsafe_allow_html=True)

    with tabs[0]:
        l, r = st.columns(2)
        with l:
            st.subheader(f"Top {top_n}: strongest factor profile")
            for sym_, row in scores.head(top_n).iterrows():
                card(row, sym_, "buy")
        with r:
            st.subheader(f"Bottom {top_n}: weakest factor profile")
            for sym_, row in scores.tail(top_n).iloc[::-1].iterrows():
                card(row, sym_, "sell")
        st.subheader("Full ranking")
        show = ["Name", "Sector", "Price", "Composite", "Percentile", *themes, "ret_1m", "mom_12_1", "volatility"]
        show = [c for c in show if c in scores.columns]
        st.dataframe(scores[show], width="stretch", height=480, column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Composite": st.column_config.NumberColumn(format="%.2f"),
            "Percentile": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
            "ret_1m": st.column_config.NumberColumn("1M", format="percent"),
            "mom_12_1": st.column_config.NumberColumn("12-1M mom.", format="percent"),
            "volatility": st.column_config.NumberColumn("Vol", format="percent"),
            **{t: st.column_config.NumberColumn(format="%.2f") for t in themes},
        })
        st.download_button("Download ranking (CSV)", scores[show].to_csv().encode(), "sharkfin_scan.csv", "text/csv")

    with tabs[1]:
        st.markdown("Stocks where the **Confluence Pullback** swing setup (see Strategy Lab) has triggered today or is forming: "
                    "market and stock in an uptrend, a pullback to the 20 EMA / 50 SMA, and enough confirming signals.",
                    help=tip("trade_status"))
        if st.button(f"Find swing setups in {px.shape[1]} stocks", key="swing_scan"):
            st.session_state.swing_ran = True
        if st.session_state.get("swing_ran"):
            with st.spinner("Checking every chart…"):
                setups = swing_scan(tuple(px.columns))
            if setups.empty:
                st.info("No stock passes the must-pass rules today. That's normal in a weak or choppy market.")
            else:
                setups = setups.join(scores[["Name", "Sector", "Composite"]], how="left")
                st.dataframe(setups, width="stretch", column_config={
                    "Status": st.column_config.TextColumn(help=tip("trade_status")),
                    "Score": st.column_config.ProgressColumn(min_value=0, max_value=6, format="%d",
                                                             help=tip("min_score")),
                    "Price": st.column_config.NumberColumn(format="$%.2f"),
                    "Entry": st.column_config.NumberColumn(format="$%.2f", help=tip("entry")),
                    "Stop": st.column_config.NumberColumn(format="$%.2f", help=tip("stop")),
                    "Risk %": st.column_config.NumberColumn(format="percent", help=tip("risk_r")),
                    "T1": st.column_config.NumberColumn(format="$%.2f", help=tip("t1")),
                    "T2": st.column_config.NumberColumn(format="$%.2f", help=tip("t2")),
                    "Resistance": st.column_config.NumberColumn(format="$%.2f", help=tip("resistance")),
                    "Composite": st.column_config.NumberColumn("Factor score", format="%.2f"),
                })
                st.caption("Open a ticker on Research → Trade Setup for the full checklist and chart.")

    with tabs[2]:
        st.markdown("Candidates for a passive, long-term core: **above-average quality** within their sector, **not expensive**, "
                    "and a **positive 12-month trend** so you avoid value traps. Ranked by 40% quality, 30% value, "
                    "20% momentum, 10% analyst views.", help=tip("core_long"))
        core = catalysts.core_long_screen(scores) if use_fund else pd.DataFrame()
        if not use_fund:
            st.info("Turn on **Include fundamentals & analyst data** above to build the core-long list.")
        elif core.empty:
            st.info("No stock passes all the core-long filters in this universe right now.")
        else:
            cols = [c for c in ("Name", "Sector", "Price", "Core score", "Quality", "Value", "Momentum", "Analysts",
                                "roe", "fcf_yield", "earnings_yield", "mom_12_1") if c in core]
            st.dataframe(core[cols], width="stretch", column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Core score": st.column_config.NumberColumn(format="%.2f", help="Weighted blend of the theme scores (σ vs sector peers)."),
                **{t: st.column_config.NumberColumn(format="%.2f", help="Standard deviations above (+) or below (−) sector peers.")
                   for t in ("Quality", "Value", "Momentum", "Analysts")},
                "roe": st.column_config.NumberColumn("ROE", format="percent"),
                "fcf_yield": st.column_config.NumberColumn("FCF yield", format="percent"),
                "earnings_yield": st.column_config.NumberColumn("Earnings yield", format="percent"),
                "mom_12_1": st.column_config.NumberColumn("12-1M momentum", format="percent"),
            })
            st.caption("For a passive fallback, hold 15-30 of these across sectors and rebalance quarterly, rather than "
                       "concentrating. Check each one on Research → Trade Setup (long-term checklist) and News Desk → Catalysts.")

    with tabs[3]:
        sel = pd.concat([scores.head(top_n), scores.tail(top_n)])
        fig = go.Figure(go.Heatmap(z=sel[themes].values, x=themes, y=sel.index, zmid=0,
                                   colorscale=[[0, ui.RED], [0.5, "#1f2937"], [1, ui.GREEN]],
                                   text=np.round(sel[themes].values, 1), texttemplate="%{text}"))
        fig.update_layout(title="Theme exposures (σ, sector-neutral)", yaxis=dict(autorange="reversed"))
        ui.plotly(fig, 40 + 22 * len(sel))
        if "Sector" in scores and scores["Sector"].notna().any():
            sec = scores.groupby("Sector")["Composite"].agg(["mean", "count"]).sort_values("mean")
            fig = go.Figure(go.Bar(x=sec["mean"], y=sec.index, orientation="h",
                                   marker_color=np.where(sec["mean"] >= 0, ui.GREEN, ui.RED),
                                   text=sec["count"], texttemplate="n=%{text}"))
            fig.update_layout(title="Average composite by sector")
            ui.plotly(fig, 420)

    with tabs[4]:
        st.markdown("Backtest of the **price-based** themes (momentum, trend, low risk, reversal) over ~5 years: each month, "
                    "buy the top 20% of the universe equal-weighted, net of 10 bps trading costs. Fundamental themes are "
                    "excluded because point-in-time fundamentals aren't available for free.")
        with st.spinner("Running factor backtest…"):
            try:
                bt = factor_backtest(tuple(px.columns), tuple(sorted(tw.items())))
            except ValueError as e:
                st.warning(str(e))
                bt = None
        if bt:
            eq = pd.DataFrame({"Top-quintile strategy": (1 + bt["strategy"]).cumprod(),
                               "Equal-weight universe": (1 + bt["benchmark"]).cumprod()})
            fig = go.Figure([go.Scatter(x=eq.index, y=eq[c], name=c) for c in eq])
            fig.update_layout(title="Growth of $1", yaxis_type="log")
            ui.plotly(fig, 420)
            s_stats = risk.summary(bt["strategy"], bt["benchmark"])
            b_stats = risk.summary(bt["benchmark"])
            c = st.columns(6)
            c[0].metric("CAGR", ui.fmt_pct(s_stats["CAGR"]), f"bench {ui.fmt_pct(b_stats['CAGR'])}", delta_color="off")
            c[1].metric("Sharpe", ui.fmt_num(s_stats["Sharpe"]), f"bench {ui.fmt_num(b_stats['Sharpe'])}", delta_color="off")
            c[2].metric("Max drawdown", ui.fmt_pct(s_stats["Max Drawdown"]), f"bench {ui.fmt_pct(b_stats['Max Drawdown'])}", delta_color="off")
            c[3].metric("Mean rank IC", f"{bt['ic_mean']:.3f}", f"t-stat {bt['ic_t']:.2f}", delta_color="off",
                        help="Spearman correlation between the composite and next-month returns. >0.03 is useful in practice.")
            c[4].metric("IC hit rate", ui.fmt_pct(bt["hit_rate"], 0))
            c[5].metric("Monthly turnover", ui.fmt_pct(bt["avg_turnover"], 0))
            fig = go.Figure(go.Bar(x=bt["ic"].index, y=bt["ic"].values, marker_color=np.where(bt["ic"] >= 0, ui.GREEN, ui.RED)))
            fig.update_layout(title="Monthly information coefficient")
            ui.plotly(fig, 280)
            st.caption("Caveat: uses today's index members, so delisted losers are missing (survivorship bias flatters results).")

ui.disclaimer()
