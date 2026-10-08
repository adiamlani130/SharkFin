"""Market dashboard: indices, regime, sector rotation, movers, sentiment."""

from datetime import datetime, time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
from pandas.tseries.holiday import (AbstractHolidayCalendar, GoodFriday, Holiday, USLaborDay, USMartinLutherKingJr,
                                    USMemorialDay, USPresidentsDay, USThanksgivingDay, nearest_workday)

from sharkfin import data, leader_dip, sentiment, ui
from sharkfin import indicators as ind



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
ui.header("Market Dashboard", ui.pill(f"NYSE {status}", "pos" if status == "Open" else "neu") +
          f"{ny:%A, %b %d · %I:%M %p} ET")

with st.spinner("Loading markets…"):
    px = load_overview()

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

# ---- Market pulse ------------------------------------------------------------
st.subheader("Market pulse", help="The backdrop for every trade: is the broad market trending, how far is it from its high, "
                                  "and how nervous are options traders?")
spx = px.get("^GSPC", pd.Series(dtype=float)).dropna()
vix = px.get("^VIX", pd.Series(dtype=float)).dropna()
if len(spx) > 200:
    trend = spx.iloc[-1] / spx.rolling(200).mean().iloc[-1] - 1
    dd = spx.iloc[-1] / spx.max() - 1
    rv = ind.realized_vol(spx).iloc[-1]
    v = vix.iloc[-1] if len(vix) else np.nan
    regime = ("calm" if v < 15 else "normal" if v < 20 else "elevated" if v < 30 else "stressed") if np.isfinite(v) else "unknown"
    vrp = v / 100 - rv if np.isfinite(v) else np.nan
    verdict = ("Risk-on" if trend > 0 and v < 20 else "Cautious" if trend > 0 else "Risk-off")
    tone_ = "pos" if verdict == "Risk-on" else "neu" if verdict == "Cautious" else "neg"
    st.markdown(
        f"<div class='sf-card'>{ui.pill(verdict, tone_)}<span class='sf-note'>The S&amp;P 500 is "
        f"<b>{abs(trend):.1%} {'above' if trend > 0 else 'below'}</b> its 200-day average "
        f"({'uptrend' if trend > 0 else 'downtrend'}) and <b>{abs(dd):.1%}</b> below its 1-year high. "
        f"Volatility is {regime} (VIX {v:.1f}).</span></div>", unsafe_allow_html=True)
    ui.metrics([
        {"label": "S&P 500 vs 200-day", "value": ui.fmt_pct(trend, 1, True), "delta": "Uptrend" if trend > 0 else "Downtrend",
         "delta_color": "normal" if trend > 0 else "inverse", "delta_arrow": "off",
         "help": "Above the 200-day average is the classic definition of a bull-market backdrop."},
        {"label": "Off 1-year high", "value": ui.fmt_pct(dd), "help": "How far the index is below its highest close of the last year."},
        {"label": "Realised volatility", "value": ui.fmt_pct(rv),
         "help": "How much the S&P 500 actually moved over the last month, annualised. The long-run average is about 15-16%."},
        {"label": "Fear gauge (VIX)", "value": f"{v:.1f}", "delta": regime.title(), "delta_color": "off", "delta_arrow": "off",
         "help": "Options-implied volatility. Below 15 calm, 15-20 normal, 20-30 elevated, above 30 stressed."},
        {"label": "Volatility premium", "value": ui.fmt_pct(vrp, 1, True),
         "help": "VIX minus realised volatility. Positive (the usual state) means options price in more risk than is "
                 "showing up; negative is a stress signal."},
    ], key="pulse")

# ---- Market regime light -----------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def spy_regime() -> dict:
    m = data.market_history("2y")
    return leader_dip.regime(m["Close"]) if not m.empty else {}


reg = spy_regime()
if reg:
    on = reg["leader_dip_on"]
    band = reg["band_on"]
    ten = reg["ten_month_on"]
    st.subheader("Market regime", help="Slow trend switches on SPY. In SharkFin's research these halved drawdowns, "
                                       "while faster timing signals whipsawed and lagged plain holding.")
    lines = [
        f"<div class='row'><b>200-day line</b> · SPY is <b>{abs(reg['gap200']):.1%} {'above' if on else 'below'}</b> its "
        f"200-day average, so Leader Dip's switch is <b>{'on: new trades allowed' if on else 'off: no new trades'}</b>.</div>",
        f"<div class='row'><b>200-day with a 2% band</b> · "
        f"{'Uptrend' if band else 'Downtrend' if band is False else 'Not set yet'}. It only flips on a close more than 2% "
        f"through the average, so it changed {reg['band_flips_1y']} time{'s' if reg['band_flips_1y'] != 1 else ''} in the "
        "past year.</div>",
    ]
    if ten is not None:
        lines.append(
            f"<div class='row'><b>10-month average</b> · SPY closed {reg['month_end']:%B} "
            f"<b>{'above' if ten else 'below'}</b> it ({ui.fmt_money(reg['month_close']).replace('$', '&#36;')} vs "
            f"{ui.fmt_money(reg['ten_month_avg']).replace('$', '&#36;')}). Checked once a month: "
            f"{'stay invested' if ten else 'long-term trend money waits in cash'} until the next month end.</div>")
    lines.append(
        f"<div class='row'><b>Idle cash</b> · {'SPY' if on else 'T-bills'}. Leader Dip's best mix kept money it "
        "wasn't using in SPY while SPY was above its 200-day, and in T-bills otherwise.</div>")
    pill_txt = "Leader Dip on" if on else "Leader Dip off"
    st.markdown(f"<div class='sf-card'>{ui.pill(pill_txt, 'pos' if on else 'neg')}"
                f"{ui.pill('10-month: ' + ('up' if ten else 'down'), 'pos' if ten else 'neg') if ten is not None else ''}"
                f"{''.join(lines)}</div>", unsafe_allow_html=True)

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
        ui.plotly(fig, 430)
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
        ui.plotly(fig, 430)

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
                "Trend": st.column_config.LineChartColumn("2 months", width="small"),
            })
    else:
        st.info("Your watchlist is empty. Add stocks from Research & Valuation or the Portfolio page.")
with right:
    st.subheader("Headlines")
    arts = sentiment.rank_articles(data.news("stock market economy Fed earnings")[:60], "stock market")
    agg = sentiment.aggregate_sentiment(arts[:40])
    st.markdown(ui.pill(f"Tone: {agg['label']}", ui.tone(agg["score"], 0.1)) +
                f"<span class='sf-muted'>{agg['positive']} positive · {agg['negative']} negative · {agg['neutral']} neutral "
                f"in the latest {agg['n']} stories</span>", unsafe_allow_html=True)
    for a in arts[:8]:
        ui.news_item(a, show_summary=False)

ui.disclaimer()
