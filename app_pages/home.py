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

# ---- Sector rotation ---------------------------------------------------------
st.subheader("Sectors", help="SPDR sector ETFs. The heatmap shows returns; the map shows which sectors are leading and "
                             "which are gaining or losing momentum.")
rows = []
for name, sym in data.SECTOR_ETFS.items():
    s = px.get(sym, pd.Series(dtype=float)).dropna()
    if len(s) < 130:
        continue
    rows.append({"Sector": name, "1D": s.iloc[-1] / s.iloc[-2] - 1, "1W": s.iloc[-1] / s.iloc[-6] - 1,
                 "1M": s.iloc[-1] / s.iloc[-22] - 1, "3M": s.iloc[-1] / s.iloc[-64] - 1,
                 "6M": s.iloc[-1] / s.iloc[-127] - 1})
if rows:
    sec = pd.DataFrame(rows).set_index("Sector").sort_values("1M", ascending=False)
    left, right = st.columns([3, 2])
    with left:
        z = sec.values * 100
        fig = go.Figure(go.Heatmap(z=np.clip(z, -15, 15), x=sec.columns, y=sec.index, colorscale=ui.DIVERGING,
                                   zmid=0, text=[[f"{v:+.1f}%" for v in r] for r in z], texttemplate="%{text}",
                                   showscale=False, xgap=2, ygap=2, hovertemplate="%{y} · %{x}: %{text}<extra></extra>"))
        fig.update_layout(title="Returns by sector", yaxis=dict(autorange="reversed", showgrid=False),
                          xaxis=dict(side="top", showgrid=False))
        ui.plotly(fig, 430, key="home_heat")
    with right:
        # Relative rotation: 3M momentum vs 1M change in momentum
        # Relative to the average sector, so the quadrants read as leading / lagging.
        x = (sec["3M"] - sec["3M"].mean()) * 100
        y = ((sec["1M"] - sec["3M"] / 3) - (sec["1M"] - sec["3M"] / 3).mean()) * 100
        colors = np.where((x >= 0) & (y >= 0), ui.GREEN, np.where(x >= 0, ui.ORANGE, np.where(y >= 0, ui.BLUE, ui.RED)))
        fig = go.Figure(go.Scatter(x=x, y=y, mode="markers+text", text=sec.index, textposition="top center",
                                   textfont=dict(size=10), marker=dict(size=11, color=colors),
                                   hovertemplate="%{text}<br>3M vs avg %{x:+.1f}%<br>Acceleration %{y:+.1f}%<extra></extra>"))
        fig.add_hline(y=0, line=dict(color="#2a3442"))
        fig.add_vline(x=0, line=dict(color="#2a3442"))
        mx, my = max(abs(x).max(), 1) * 1.25, max(abs(y).max(), 1) * 1.3
        for qx, qy, lbl, colr in ((1, 1, "Leading", ui.GREEN), (1, -1, "Weakening", ui.ORANGE),
                                  (-1, -1, "Lagging", ui.RED), (-1, 1, "Improving", ui.BLUE)):
            fig.add_annotation(x=qx * mx * 0.97, y=qy * my * 0.95, text=lbl, showarrow=False, font=dict(color=colr, size=11),
                               xanchor="right" if qx > 0 else "left", yanchor="top" if qy > 0 else "bottom", opacity=0.8)
        fig.update_layout(title="Rotation map", xaxis=dict(title="3-month return vs average sector (%)", range=[-mx, mx]),
                          yaxis=dict(title="Momentum change (%)", range=[-my, my]), showlegend=False)
        ui.plotly(fig, 430, key="home_rotation")

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
