"""Market dashboard: indices, regime, sector rotation, movers, sentiment."""

from datetime import datetime, time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
from pandas.tseries.holiday import (AbstractHolidayCalendar, GoodFriday, Holiday, USLaborDay, USMartinLutherKingJr,
                                    USMemorialDay, USPresidentsDay, USThanksgivingDay, nearest_workday)

from sharkfin import data, sentiment, ui
from sharkfin import indicators as ind

st.title("Market Dashboard")


class NYSECalendar(AbstractHolidayCalendar):
    rules = [
        Holiday("New Year", month=1, day=1, observance=nearest_workday), USMartinLutherKingJr, USPresidentsDay,
        GoodFriday, USMemorialDay, Holiday("Juneteenth", month=6, day=19, start_date="2022-01-01", observance=nearest_workday),
        Holiday("Independence Day", month=7, day=4, observance=nearest_workday), USLaborDay, USThanksgivingDay,
        Holiday("Christmas", month=12, day=25, observance=nearest_workday),
    ]


def market_status():
    ny = datetime.now(pytz.timezone("America/New_York"))
    holidays = NYSECalendar().holidays(f"{ny.year}-01-01", f"{ny.year}-12-31")
    is_open = ny.weekday() < 5 and ny.date() not in set(holidays.date) and time(9, 30) <= ny.time() < time(16, 0)
    pre = ny.weekday() < 5 and time(4, 0) <= ny.time() < time(9, 30)
    post = ny.weekday() < 5 and time(16, 0) <= ny.time() < time(20, 0)
    label = "Open" if is_open else "Pre-market" if pre else "After-hours" if post else "Closed"
    return label, ny


@st.cache_data(ttl=600, show_spinner=False)
def load_overview():
    syms = tuple(data.MARKET_TICKERS.values()) + tuple(data.SECTOR_ETFS.values())
    return data.download_prices(syms, period="1y")


status, ny = market_status()
tone = "pos" if status == "Open" else "neu"
st.markdown(ui.pill(f"NYSE {status}", tone) + f"<span class='sf-muted'>{ny:%A %b %d, %I:%M %p} ET</span>",
            unsafe_allow_html=True)

with st.spinner("Loading markets…"):
    px = load_overview()

if px.empty:
    st.error("Market data is unavailable right now (Yahoo Finance did not respond). Try again shortly.")
    st.stop()

# ---- Index tiles -------------------------------------------------------------
cols = st.columns(5)
for i, (name, sym) in enumerate(data.MARKET_TICKERS.items()):
    if sym not in px:
        continue
    s = px[sym].dropna()
    if len(s) < 2:
        continue
    chg = s.iloc[-1] / s.iloc[-2] - 1
    ytd_base = s[s.index.year == s.index[-1].year]
    ytd = s.iloc[-1] / ytd_base.iloc[0] - 1 if len(ytd_base) else np.nan
    val = f"{s.iloc[-1]:.2f}%" if sym == "^TNX" else f"{s.iloc[-1]:,.2f}"
    with cols[i % 5]:
        st.metric(name, val, f"{chg:+.2%} today", delta_color="inverse" if sym in ("^VIX",) else "normal",
                  help=f"YTD {ui.fmt_pct(ytd, sign=True)}", chart_data=s.iloc[-60:].values, chart_type="line")

# ---- Market regime -----------------------------------------------------------
st.subheader("Market regime")
spx = px.get("^GSPC", pd.Series(dtype=float)).dropna()
vix = px.get("^VIX", pd.Series(dtype=float)).dropna()
c1, c2, c3, c4 = st.columns(4)
if len(spx) > 200:
    trend = spx.iloc[-1] / spx.rolling(200).mean().iloc[-1] - 1
    dd = spx.iloc[-1] / spx.max() - 1
    rv = ind.realized_vol(spx).iloc[-1]
    c1.metric("S&P 500 vs 200-day", ui.fmt_pct(trend, sign=True), "Uptrend" if trend > 0 else "Downtrend",
              delta_color="normal" if trend > 0 else "inverse")
    c2.metric("Drawdown from 1y high", ui.fmt_pct(dd))
    c3.metric("S&P realised vol (21d)", ui.fmt_pct(rv))
if len(vix):
    v = vix.iloc[-1]
    regime = "Calm" if v < 15 else "Normal" if v < 20 else "Elevated" if v < 30 else "Stress"
    vrp = (v / 100 - rv) if len(spx) > 200 else np.nan
    c4.metric("VIX regime", f"{v:.1f} · {regime}", f"Vol risk premium {ui.fmt_pct(vrp, sign=True)}",
              help="Implied (VIX) minus realised volatility. Positive = options price in more risk than is being realised.")

# ---- Sector rotation ---------------------------------------------------------
st.subheader("Sector performance")
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
        fig = go.Figure(go.Heatmap(z=z, x=sec.columns, y=sec.index, colorscale=[[0, ui.RED], [0.5, "#1f2937"], [1, ui.GREEN]],
                                   zmid=0, text=[[f"{v:+.1f}%" for v in r] for r in z], texttemplate="%{text}",
                                   showscale=False))
        fig.update_layout(title="Returns by sector (SPDR ETFs)", yaxis=dict(autorange="reversed"))
        ui.plotly(fig, 420)
    with right:
        # Relative rotation: 3M momentum vs 1M change in momentum
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sec["3M"] * 100, y=(sec["1M"] - sec["3M"] / 3) * 100, mode="markers+text",
                                 text=sec.index, textposition="top center",
                                 marker=dict(size=12, color=sec["1M"], colorscale="RdYlGn", cmid=0)))
        fig.add_hline(y=0, line=dict(color=ui.MUTED, dash="dot"))
        fig.add_vline(x=0, line=dict(color=ui.MUTED, dash="dot"))
        fig.update_layout(title="Sector rotation (trend vs acceleration)", xaxis_title="3M return %",
                          yaxis_title="Momentum acceleration %", showlegend=False)
        ui.plotly(fig, 420)

# ---- Watchlist + portfolio snapshot ------------------------------------------
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
                "Trend": st.column_config.LineChartColumn(width="small"),
            })
    else:
        st.info("Your watchlist is empty. Add stocks from the Research page.")
with right:
    st.subheader("Market headlines")
    arts = sentiment.rank_articles(data.news("stock market economy Fed earnings")[:60], "stock market")
    agg = sentiment.aggregate_sentiment(arts[:40])
    st.markdown(ui.pill(f"News sentiment: {agg['label']} ({agg['score']:+.2f})", ui.tone(agg["score"], 0.1)) +
                f"<span class='sf-muted'>{agg['positive']} positive · {agg['negative']} negative · {agg['neutral']} neutral</span>",
                unsafe_allow_html=True)
    for a in arts[:8]:
        t = ui.tone(a["sentiment"], 0.25)
        link = a.get("link") or "#"
        st.markdown(f"{ui.pill(a['sentiment_label'], t)} [{ui.esc(a['title'])}]({link}) "
                    f"<span class='sf-muted'>· {a.get('publisher', '')}</span>", unsafe_allow_html=True)

ui.disclaimer()
