"""Market dashboard: the indices, which way the market is going today and why, sectors, watchlist, headlines."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import data, market_today as mt, sentiment, ui

OVERVIEW = tuple(data.MARKET_TICKERS.values()) + tuple(data.SECTOR_ETFS.values())
HEADLINES = "stock market economy Fed earnings"
# The biggest US companies: Wall Street's view of them is most of Wall Street's view of the index.
MEGA_CAPS = ("NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "AVGO", "TSLA", "BRK-B", "JPM", "LLY", "WMT", "V",
             "ORCL", "MA", "XOM", "NFLX", "COST", "JNJ", "PLTR", "HD", "ABBV", "BAC", "PG", "AMD", "UNH", "KO", "GE",
             "CSCO", "MU")

status, ny = data.market_status()
ui.header("Market Dashboard", ui.pill(f"NYSE {status}", "pos" if status == "Open" else "neu") +
          f"{ny:%A, %b %d · %I:%M %p} ET")

with st.spinner("Loading markets…"):
    # Everything this page reads, fetched side by side (the data layer caches each call, so the sections below
    # get them instantly). The page stays responsive to clicks while it waits.
    ui.fetch_all([(data.download_prices, (OVERVIEW,), {"period": "1y"}),
                  (data.download_prices, (tuple(data.universe("S&P 500")),), {"period": "2y"}),
                  (data.infos, (MEGA_CAPS,)), (data.news, (HEADLINES,))] +
                 ([(data.download_prices, (tuple(st.session_state.watchlist),), {"period": "3mo"})]
                  if st.session_state.watchlist else []))
    px = data.download_prices(OVERVIEW, period="1y")

if px.empty:
    st.error("Market data is unavailable right now (Yahoo Finance did not respond). Try again shortly.")
    st.stop()


def tile(name, sym):
    s = px[sym].dropna() if sym in px else pd.Series(dtype=float)
    if len(s) < 2:
        return None
    chg = s.iloc[-1] / s.iloc[-2] - 1
    ytd_base = s[s.index.year == s.index[-1].year]
    ytd = s.iloc[-1] / ytd_base.iloc[0] - 1 if len(ytd_base) else np.nan
    val = f"{s.iloc[-1]:.2f}%" if sym == "^TNX" else f"{s.iloc[-1]:,.0f}" if s.iloc[-1] > 10_000 else f"{s.iloc[-1]:,.2f}"
    return {"label": name, "value": val, "delta": f"{chg:+.2%}", "delta_color": "inverse" if sym == "^VIX" else "normal",
            "help": f"Year to date: {ui.fmt_pct(ytd, 1, True)}. The line shows the last 3 months.",
            "chart_data": s.iloc[-63:].values, "chart_type": "area"}


ui.metrics([t for n, sym in data.MARKET_TICKERS.items() if (t := tile(n, sym))], key="tiles")

# ---- Today ---------------------------------------------------------------------------------------------
spx = px.get("^GSPC", pd.Series(dtype=float)).dropna()
sp_px = data.download_prices(tuple(data.universe("S&P 500")), period="2y")
br = mt.breadth(sp_px.iloc[-80:] if not sp_px.empty else sp_px)
today = mt.direction(spx, px.get("^IXIC"), px.get("^VIX"), br)
street = mt.street_view(data.infos(MEGA_CAPS))
arts = sentiment.rank_articles(data.news(HEADLINES)[:60], "stock market")
sect = mt.sector_leaders(px, data.SECTOR_ETFS)
drivers = mt.macro_drivers(px)
themes = mt.headline_drivers(arts[:40])

st.subheader("Today", help="Which way the market is moving, how broad the move is, what analysts expect, and anything "
                           "unusual driving it. A move counts as big when it is at least twice that asset's normal "
                           "daily move over the past year.")
color = {"pos": ui.GREEN, "neg": ui.RED}.get(today["tone"], ui.BLUE)


def stat(k, v, s=""):
    return f"<div><div class='k'>{ui.h(k)}</div><div class='v'>{v}</div><div class='s'>{ui.h(s)}</div></div>"


trend = spx.iloc[-1] / spx.rolling(200).mean().iloc[-1] - 1 if len(spx) > 200 else np.nan
off_high = spx.iloc[-1] / spx.iloc[-252:].max() - 1 if len(spx) else np.nan
stats_html = "".join([
    stat("S&P 500 today", ui.fmt_pct(today["move"], 2, True),
         f"{abs(today['z']):.1f}x a normal day" if np.isfinite(today.get("z", np.nan)) else ""),
    stat("Stocks rising", ui.fmt_pct(br["up_today"], 0) if np.isfinite(br["up_today"]) else "—",
         f"{ui.fmt_pct(br['above50'], 0)} above their 50-day" if np.isfinite(br["above50"]) else "of the S&P 500"),
    stat("Trend", f"{ui.fmt_pct(trend, 1, True)} vs 200-day" if np.isfinite(trend) else "—",
         f"{ui.fmt_pct(off_high, 1)} from its 1-year high" if np.isfinite(off_high) else ""),
    stat("Analysts' upside", ui.fmt_pct(street["upside"], 1, True) if street else "—",
         (f"to targets on the {street['n']} biggest stocks · {street['buy_share']:.0%} rated buy"
          if street and np.isfinite(street.get("buy_share", np.nan)) else "average 12-month target vs price")),
])

rows = []
for d in drivers:
    rows.append(f"<div class='sf-driver'>{ui.pill(d['driver'] + ' ' + d['move'], 'info')}<span>{ui.h(d['text'])}</span></div>")
if sect and abs(sect["spread"]) > 0.025:
    (bn, bv), (wn, wv) = sect["best"], sect["worst"]
    rows.append(f"<div class='sf-driver'>{ui.pill('Sectors', 'neu')}<span>{ui.h(bn)} leads ({bv:+.1%}) and {ui.h(wn)} "
                f"lags ({wv:+.1%}): money is rotating, not just rising or falling together.</span></div>")
for t in themes:
    rows.append(f"<div class='sf-driver'>{ui.pill(t['driver'], 'neu')}<span>In {t['hits']} of the latest headlines, "
                f"e.g. <q>{ui.h(t['example'])}</q></span></div>")
if not rows:
    rows.append("<div class='sf-driver'><span class='sf-muted'>No single big driver today: oil, rates, the dollar and "
                "the headlines are all moving within their normal range.</span></div>")

st.markdown(f"<div class='sf-today' style='--c:{color}'><div class='hd'><span class='lb'>{ui.h(today['label'])}</span>"
            f"{ui.pill(status, 'pos' if status == 'Open' else 'neu')}</div><div class='tx'>{ui.h(today['text'])}</div>"
            f"<div class='st'>{stats_html}</div>"
            f"<div class='sf-drivers'><div class='sf-muted'>What's driving it</div>{''.join(rows)}</div></div>",
            unsafe_allow_html=True)
if street:
    with st.expander("Analyst targets on the biggest stocks"):
        up = pd.Series({**street["top"], **street["bottom"]}).sort_values(ascending=False)
        st.caption(f"Cap-weighted upside to the average 12-month analyst target across {street['n']} of the largest "
                   f"US companies: {street['upside']:+.1%} (median stock {street['median_upside']:+.1%}). Analysts "
                   "are usually too optimistic by a few points, so read it as a direction, not a forecast. Most and "
                   "least upside:")
        ui.kv([(k, f"{v:+.1%}") for k, v in up.items()])

# ---- Sectors -------------------------------------------------------------------------------------------
st.subheader("Sectors", help="SPDR sector ETFs, sorted by return over the period you pick.")
span = st.segmented_control("Period", ["1D", "1W", "1M", "3M", "YTD"], default="1M", key="home_span",
                            label_visibility="collapsed") or "1M"
look = {"1D": 1, "1W": 5, "1M": 21, "3M": 63}
rows_ = []
for name, sym in data.SECTOR_ETFS.items():
    s = px.get(sym, pd.Series(dtype=float)).dropna()
    if len(s) < 70:
        continue
    if span == "YTD":
        base = s[s.index.year == s.index[-1].year]
        r = s.iloc[-1] / base.iloc[0] - 1 if len(base) else np.nan
    else:
        r = s.iloc[-1] / s.iloc[-1 - look[span]] - 1
    rows_.append((name, r))
if rows_:
    sec = pd.Series(dict(rows_)).dropna().sort_values()
    mkt = spx.iloc[-1] / spx.iloc[-1 - look.get(span, 1)] - 1 if span != "YTD" and len(spx) > 64 else np.nan
    fig = go.Figure(go.Bar(x=sec.values * 100, y=sec.index, orientation="h",
                           marker_color=np.where(sec.values >= 0, ui.GREEN, ui.RED), marker_line_width=0,
                           text=[f"{v:+.1%}" for v in sec.values], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{text}<extra></extra>"))
    if np.isfinite(mkt):
        fig.add_vline(x=mkt * 100, line=dict(color=ui.MUTED, dash="dot", width=1), annotation_text="S&P 500",
                      annotation_position="top", annotation_font=dict(size=10, color=ui.MUTED))
    fig.update_layout(xaxis=dict(ticksuffix="%", zeroline=True, zerolinecolor="#2a3442"), yaxis=dict(showgrid=False),
                      margin=dict(l=10, r=40, t=10, b=30), bargap=0.35)
    ui.plotly(fig, 360, key="home_sectors")

# ---- Watchlist + headlines -----------------------------------------------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("Watchlist")
    wl = st.session_state.watchlist
    if wl:
        wpx = data.download_prices(tuple(wl), period="3mo")
        rows = []
        for s in wl:
            if s in wpx and wpx[s].notna().sum() > 22:
                ser = wpx[s].dropna()
                rows.append({"Symbol": s, "Price": ser.iloc[-1], "1D": ser.iloc[-1] / ser.iloc[-2] - 1,
                             "1M": ser.iloc[-1] / ser.iloc[-22] - 1, "Trend": ser.iloc[-40:].tolist()})
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "1D": st.column_config.NumberColumn(format="percent"),
                "1M": st.column_config.NumberColumn(format="percent"),
                "Trend": st.column_config.LineChartColumn("2 months", width="small"),
            })
    else:
        st.info("Your watchlist is empty. Add stocks from Research & Valuation or the Portfolio page.")
with right:
    st.subheader("Headlines")
    agg = sentiment.aggregate_sentiment(arts[:40])
    st.markdown(ui.pill(f"Tone: {agg['label']}", ui.tone(agg["score"], 0.1)) +
                f"<span class='sf-muted'>{agg['positive']} positive · {agg['negative']} negative · {agg['neutral']} neutral "
                f"in the latest {agg['n']} stories</span>", unsafe_allow_html=True)
    for a in arts[:8]:
        ui.news_item(a, show_summary=False)

ui.disclaimer()
