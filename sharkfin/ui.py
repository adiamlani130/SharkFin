"""Shared Streamlit UI helpers: styling, chart template, formatting, state."""

from __future__ import annotations

import hashlib
import html as _html
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from . import data

GREEN, RED, BLUE, ORANGE, MUTED = "#2dd4a3", "#ff5c7a", "#4ea8ff", "#f5a524", "#8b95a7"
PURPLE = "#a78bfa"
BG, PANEL, GRID, BORDER = "#0a0e14", "#121822", "#1c2431", "#1f2836"
DIVERGING = [[0, "#9b2c45"], [0.5, "#1a212c"], [1, "#167a5f"]]
MA_COLORS = {"SMA 20": PURPLE, "EMA 20": PURPLE, "EMA 21": "#f472b6", "SMA 50": BLUE, "SMA 200": ORANGE}
DATA_DIR = Path(".sharkfin")

pio.templates["sharkfin"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1dc", family="Inter, system-ui, sans-serif", size=12),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=BORDER, showline=False),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=BORDER, showline=False),
        colorway=[BLUE, GREEN, ORANGE, PURPLE, RED, "#f472b6", "#5eead4", "#facc15"],
        margin=dict(l=10, r=10, t=56, b=10), hoverlabel=dict(bgcolor="#1a212c", bordercolor=BORDER, font=dict(color="#e6e9ef")),
        title=dict(x=0, xanchor="left", y=0.98, yanchor="top", font=dict(size=14, color="#e6e9ef")),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.1, x=0, yanchor="top", font=dict(size=11)),
    )
)
pio.templates.default = "plotly_dark+sharkfin"

CSS = """
<style>
/* ---------- layout ---------- */
.block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1360px;}
@media (max-width: 900px) {.block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem;}}
h1 {letter-spacing: -0.025em;}
h2, h3, h4 {letter-spacing: -0.01em;}
hr {margin: 1.2rem 0 !important; border-color: #1f2836 !important;}

/* ---------- page header ---------- */
.sf-head {margin: 0 0 1.1rem 0;}
.sf-head h1 {font-size: 1.9rem; margin: 0; padding: 0; line-height: 1.2;}
.sf-head p {color: #8b95a7; margin: .35rem 0 0 0; font-size: .92rem; max-width: 820px; line-height: 1.5;}
@media (max-width: 640px) {.sf-head h1 {font-size: 1.55rem;}}

/* ---------- metrics ---------- */
[data-testid="stMetric"] {background: #111722; border: 1px solid #1f2836; border-radius: 10px; padding: 12px 14px;
  height: 100%;}
[data-testid="stMetricLabel"] p {color: #8b95a7 !important; font-size: .72rem !important; text-transform: uppercase;
  letter-spacing: .06em; font-weight: 600;}
[data-testid="stMetricValue"] {white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
[data-testid="stMetricDelta"] {font-size: .8rem;}
/* metric rows built with ui.metrics(): responsive grid that wraps instead of squashing */
.block-container {container-type: inline-size;}
div[class*="st-key-sfc"] {display: grid !important; gap: .6rem;}
div[class*="st-key-sfc"] > div {width: auto !important; min-width: 0;}
div[class*="st-key-sfc"] [data-testid="stElementContainer"] > div, div[class*="st-key-sfc"] [data-testid="stMetric"] {height: 100%;}
div[class*="st-key-sfc1-"] {grid-template-columns: minmax(0, 1fr);}
div[class*="st-key-sfc2-"] {grid-template-columns: repeat(2, minmax(0, 1fr));}
div[class*="st-key-sfc3-"] {grid-template-columns: repeat(3, minmax(0, 1fr));}
div[class*="st-key-sfc4-"] {grid-template-columns: repeat(4, minmax(0, 1fr));}
div[class*="st-key-sfc5-"] {grid-template-columns: repeat(5, minmax(0, 1fr));}
div[class*="st-key-sfc6-"] {grid-template-columns: repeat(6, minmax(0, 1fr));}
@container (max-width: 1000px) {div[class*="st-key-sfc6-"] {grid-template-columns: repeat(3, minmax(0, 1fr));}}
@container (max-width: 760px) {
  div[class*="st-key-sfc4-"], div[class*="st-key-sfc5-"] {grid-template-columns: repeat(2, minmax(0, 1fr));}}
/* ---------- Strategy Lab rule rows: wrap two-per-line on phones instead of stacking ---------- */
div[class*="st-key-sfrule"] [data-testid="stHorizontalBlock"] {flex-wrap: wrap; row-gap: .5rem;}
@media (max-width: 640px) {
  div[class*="st-key-sfrule"] [data-testid="stColumn"] {flex: 1 1 calc(50% - 1rem) !important; min-width: calc(50% - 1rem) !important; width: auto !important;}
}
@container (max-width: 520px) {
  div[class*="st-key-sfc3-"], div[class*="st-key-sfc6-"] {grid-template-columns: repeat(2, minmax(0, 1fr));}}

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] {gap: 1.4rem; border-bottom: 1px solid #1f2836; overflow-x: auto; scrollbar-width: none;}
.stTabs [data-baseweb="tab"] {padding: .55rem 0; font-weight: 500;}
.stTabs [data-baseweb="tab"] p {font-size: .92rem;}
.stTabs [aria-selected="true"] p {color: #e6e9ef; font-weight: 600;}

/* ---------- cards and text ---------- */
.sf-card {background: #111722; border: 1px solid #1f2836; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;}
.sf-card.buy {border-left: 3px solid #2dd4a3;} .sf-card.sell {border-left: 3px solid #ff5c7a;}
.sf-card .t {font-weight: 600; font-size: 1.02rem; color: #e6e9ef;}
.sf-card .row {margin-top: 6px; font-size: .86rem; color: #c9d1dc;}
.sf-hero {background: linear-gradient(135deg, #121a26 0%, #0f141c 100%); border: 1px solid #1f2836; border-radius: 14px;
  padding: 18px 20px; margin-bottom: 14px;}
.sf-hero .k {color: #8b95a7; font-size: .72rem; text-transform: uppercase; letter-spacing: .07em; font-weight: 600;}
.sf-hero .v {font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; color: #e6e9ef; line-height: 1.25;}
.sf-hero .s {color: #8b95a7; font-size: .88rem; margin-top: 4px; line-height: 1.5;}
.sf-pill {display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: .72rem; font-weight: 600;
  margin-right: 6px; letter-spacing: .02em; white-space: nowrap; vertical-align: middle;}
.sf-pos {background: rgba(45,212,163,.13); color: #2dd4a3;} .sf-neg {background: rgba(255,92,122,.13); color: #ff7a93;}
.sf-neu {background: rgba(139,149,167,.14); color: #c3cad6;} .sf-info {background: rgba(78,168,255,.13); color: #7cc4ff;}
.sf-muted {color: #8b95a7; font-size: .85rem;}
.sf-up {color: #2dd4a3;} .sf-down {color: #ff7a93;}
.sf-note {color: #aab3c2; font-size: .9rem; line-height: 1.55;}
.sf-kv {display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 0 1.6rem; margin: .2rem 0 .6rem 0;}
.sf-kv div {display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px solid #18202b; font-size: .88rem;}
.sf-kv span:first-child {color: #8b95a7;} .sf-kv span:last-child {color: #e6e9ef; font-weight: 500; text-align: right;}

/* ---------- checklists ---------- */
.sf-cklist {display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 0 1.6rem;}
.sf-ckrow {display: flex; gap: 10px; padding: 9px 0; border-bottom: 1px solid #18202b; font-size: .9rem; color: #e6e9ef;}
.sf-ckrow .w {color: #8b95a7; font-size: .8rem; margin-top: 2px; line-height: 1.45;}
.sf-ck {flex: 0 0 20px; height: 20px; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center;
  font-size: .72rem; font-weight: 700; margin-top: 1px;}
.sf-ck.ok {background: rgba(45,212,163,.15); color: #2dd4a3;} .sf-ck.no {background: rgba(255,92,122,.13); color: #ff7a93;}
.sf-ck.na {background: rgba(139,149,167,.14); color: #8b95a7;}

/* ---------- news ---------- */
.sf-news {padding: 11px 0; border-bottom: 1px solid #18202b;}
.sf-news a {color: #e6e9ef !important; text-decoration: none !important; font-weight: 500; line-height: 1.45;}
.sf-news a:hover {color: #7cc4ff !important;}
.sf-news .m {color: #8b95a7; font-size: .78rem; margin-top: 3px;}
.sf-news .d {color: #9aa4b2; font-size: .85rem; margin-top: 4px; line-height: 1.5;}

/* ---------- misc ---------- */
[data-testid="stExpander"] details {border-color: #1f2836; border-radius: 10px;}
[data-testid="stExpander"] summary p {font-weight: 500;}
[data-testid="stSidebarNav"] a span {font-size: .92rem;}
[data-testid="stCaptionContainer"] {color: #8b95a7;}
.sf-tape {white-space: nowrap; overflow: hidden; border-bottom: 1px solid #1f2836; padding: 6px 0 10px 0; margin-bottom: 8px;}
</style>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _finite(x) -> bool:
    try:
        return x is not None and np.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def fmt_money(x, digits: int = 2) -> str:
    if not _finite(x):
        return "—"
    x = float(x)
    a, neg = abs(x), "-" if x < 0 else ""
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if a >= div:
            return f"{neg}${a / div:,.{digits}f}{suf}"
    if a >= 1e5:
        return f"{neg}${a / 1e3:,.0f}K"
    return f"{neg}${a:,.{digits}f}"


def fmt_big(x, digits: int = 1) -> str:
    """Compact plain number: 1.2T, 340.5B, 12.0M, 45.3K."""
    if not _finite(x):
        return "—"
    x = float(x)
    a, neg = abs(x), "-" if x < 0 else ""
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"{neg}{a / div:,.{digits}f}{suf}"
    return f"{neg}{a:,.2f}" if a < 100 else f"{neg}{a:,.0f}"


def fmt_pct(x, digits: int = 1, sign: bool = False) -> str:
    if not _finite(x):
        return "—"
    return f"{float(x):+.{digits}%}" if sign else f"{float(x):.{digits}%}"


def fmt_num(x, digits: int = 2) -> str:
    if isinstance(x, bool) or not _finite(x):
        return "—"
    return f"{float(x):,.{digits}f}"


def fmt_x(x, digits: int = 1) -> str:
    """A valuation multiple, e.g. 24.3x."""
    return f"{float(x):,.{digits}f}x" if _finite(x) and float(x) > 0 else "—"


def compact_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Statement-style table (big numbers) rendered as compact strings."""
    out = df.copy()
    for c in out.columns:
        out[c] = [fmt_big(v) if _finite(v) else "" for v in pd.to_numeric(out[c], errors="coerce")]
    return out


def time_ago(ts) -> str:
    if ts is None:
        return ""
    try:
        now = datetime.now(timezone.utc)
        t = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        mins = (now - t).total_seconds() / 60
    except Exception:
        return ""
    if mins < 60:
        return f"{max(1, int(mins))}m ago"
    if mins < 60 * 24:
        return f"{int(mins // 60)}h ago"
    if mins < 60 * 24 * 7:
        return f"{int(mins // 1440)}d ago"
    return f"{ts:%b %d}"


def pill(text: str, tone: str = "neu") -> str:
    return f"<span class='sf-pill sf-{tone}'>{text}</span>"


def tone(x: float, pos: float = 0.0) -> str:
    if not _finite(x):
        return "neu"
    return "pos" if x > pos else "neg" if x < -pos else "neu"


def num(x, default=np.nan) -> float:
    try:
        v = float(x)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def missing(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() in ("", "—", "— / —", "nan"))


# ---------------------------------------------------------------------------
# Layout components
# ---------------------------------------------------------------------------


def header(title: str, subtitle: str = ""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"<div class='sf-head'><h1>{_html.escape(title)}</h1>{sub}</div>", unsafe_allow_html=True)


def metrics(items, key: str | None = None, hide_missing: bool = True, cols: int | None = None):
    """A responsive grid of st.metric tiles: one row on wide screens, an even
    2- or 3-column grid when the window (or the sidebar) makes it narrow.

    ``items`` is a list of dicts with st.metric kwargs (label, value, delta,
    delta_color, help, chart_data...) or (label, value) tuples. Tiles whose
    value is missing are dropped so pages never show a wall of dashes.
    """
    rows = []
    for it in items:
        d = dict(label=it[0], value=it[1]) if isinstance(it, tuple) else dict(it)
        if hide_missing and missing(d.get("value")):
            continue
        for k in ("value", "delta"):  # two "$" in one string would render as LaTeX
            if isinstance(d.get(k), str):
                d[k] = d[k].replace("\\$", "$").replace("$", "\\$")
        if d.get("delta") is None:
            d.pop("delta", None)
        rows.append(d)
    if not rows:
        return
    key = key or hashlib.md5("|".join(r["label"] for r in rows).encode()).hexdigest()[:10]
    n = len(rows)
    cols = cols or (n if n <= 6 else 4 if n in (7, 8) else 5)
    with st.container(key=f"sfc{cols}-{key}"):
        for d in rows:
            st.metric(**d)


def kv(pairs, hide_missing: bool = True):
    """Compact two-column key/value list (for secondary stats)."""
    cells = "".join(f"<div><span>{_html.escape(str(k))}</span><span>{_html.escape(str(v))}</span></div>"
                    for k, v in pairs if not (hide_missing and missing(v)))
    if cells:
        st.markdown(f"<div class='sf-kv'>{cells}</div>", unsafe_allow_html=True)


def h(text) -> str:
    """HTML-escape text for unsafe_allow_html blocks ($ becomes an entity so it never starts LaTeX)."""
    return _html.escape(str(text if text is not None else "")).replace("$", "&#36;")


def checklist(rows: list[dict], name: str = "Rule"):
    """Pass/fail list with the detail and a plain-English reason under each line."""
    items = []
    for r in rows:
        ok = r.get("Pass")
        mark = ("<span class='sf-ck ok'>&#10003;</span>" if ok else "<span class='sf-ck no'>&#10005;</span>" if ok is False
                else "<span class='sf-ck na'>&ndash;</span>")
        tag = f"<span class='sf-pill sf-neu'>{h(r['Type'])}</span>" if r.get("Type") else ""
        detail = f"<span class='sf-muted'> · {h(r['Detail'])}</span>" if r.get("Detail") not in (None, "", "n/a") else ""
        why = f"<div class='w'>{h(r.get('Why it matters', ''))}</div>" if r.get("Why it matters") else ""
        items.append(f"<div class='sf-ckrow'>{mark}<div><div>{h(r.get(name) or r.get('Test') or r.get('Rule'))} {tag}{detail}</div>{why}</div></div>")
    st.markdown(f"<div class='sf-cklist'>{''.join(items)}</div>", unsafe_allow_html=True)


def hero(label: str, value: str, sub: str = "", badge: str = ""):
    st.markdown(f"<div class='sf-hero'><div class='k'>{label}</div><div class='v'>{value} {badge}</div>"
                f"<div class='s'>{sub}</div></div>", unsafe_allow_html=True)


def news_item(a: dict, show_summary: bool = True, sentiment_pill: bool = True):
    from .sentiment import clean_text

    link = a.get("link") or "#"
    raw_pub = str(a.get("publisher") or "")
    raw_title = a.get("title", "")
    if raw_pub and raw_title.endswith(f" - {raw_pub}"):  # Google News appends " - Publisher"
        raw_title = raw_title[: -len(raw_pub) - 3]
    title = _html.escape(raw_title)
    pub = _html.escape(raw_pub)
    when = time_ago(a.get("published"))
    p = pill(a["sentiment_label"], tone(a["sentiment"], 0.25)) if sentiment_pill and "sentiment" in a else ""
    summary = clean_text(a.get("summary", "")) if show_summary else ""
    if summary and (summary.lower()[:60] in raw_title.lower() or raw_title.lower()[:50] in summary.lower()):
        summary = ""
    desc = f"<div class='d'>{_html.escape(summary[:240])}{'…' if len(summary) > 240 else ''}</div>" if summary else ""
    meta = " · ".join(x for x in (pub, when) if x)
    st.markdown(f"<div class='sf-news'><a href='{_html.escape(link)}' target='_blank'>{title}</a>"
                f"<div class='m'>{p}{meta}</div>{desc}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Persistent state (portfolio + watchlist)
# ---------------------------------------------------------------------------


def _path(name: str) -> Path:
    # Keep backward compatibility with the old root-level JSON files.
    legacy = Path(f"{name}.json")
    return legacy if legacy.exists() else DATA_DIR / f"{name}.json"


def _load(name: str) -> list:
    try:
        d = json.loads(_path(name).read_text())
        return d if isinstance(d, list) else []
    except Exception:
        return []


def init_state():
    ss = st.session_state
    if "portfolio" not in ss:
        ss.portfolio = _load("portfolio")
    if "watchlist" not in ss:
        ss.watchlist = _load("watchlist")
    ss.setdefault("symbol", "AAPL")


def save_state():
    try:
        for name in ("portfolio", "watchlist"):
            p = _path(name)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(st.session_state[name], indent=2, default=str))
    except Exception as e:
        st.toast(f"Could not save: {e}")


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------


def symbol_picker(key: str, label: str = "Ticker or company", default: str | None = None) -> str | None:
    """Type a ticker or company name; resolves via Yahoo search."""
    default = default or st.session_state.get("symbol", "AAPL")
    q = st.text_input(label, value=default, key=f"{key}_q", placeholder="e.g. NVDA or Nvidia").strip()
    if not q:
        return None
    matches = data.search(q)
    exact = [m for m in matches if m[0].upper() == q.upper()]
    if exact or not matches:
        sym = (exact[0][0] if exact else q.upper())
    else:
        opts = [f"{s} — {n}" for s, n in matches]
        choice = st.selectbox("Matches", opts, key=f"{key}_sel", label_visibility="collapsed")
        sym = choice.split(" — ")[0]
    st.session_state.symbol = sym
    return sym


def plotly(fig, height: int | None = None, key: str | None = None):
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False, "displayModeBar": False})


def price_chart(df: pd.DataFrame, symbol: str, overlays=("SMA 50", "SMA 200"), lower=("Volume", "RSI")) -> go.Figure:
    """Candlestick with overlays and indicator sub-panels."""
    from plotly.subplots import make_subplots

    from . import indicators as ind

    rows = 1 + len(lower)
    heights = [0.62] + [0.38 / max(1, len(lower))] * len(lower)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.025, row_heights=heights)
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                 name=symbol, increasing_line_color=GREEN, decreasing_line_color=RED,
                                 increasing_fillcolor=GREEN, decreasing_fillcolor=RED), 1, 1)
    c = df["Close"]
    for o in overlays:
        if o.startswith("SMA") or o.startswith("EMA"):
            p = int(o.split()[1])
            line = ind.sma(c, p) if o.startswith("SMA") else ind.ema(c, p)
            fig.add_trace(go.Scatter(x=df.index, y=line, name=o, line=dict(width=1.4, color=MA_COLORS.get(o, PURPLE))), 1, 1)
        elif o == "Bollinger":
            bb = ind.bollinger(c)
            fig.add_trace(go.Scatter(x=df.index, y=bb["upper"], name="BB upper", line=dict(width=1, color=MUTED, dash="dot")), 1, 1)
            fig.add_trace(go.Scatter(x=df.index, y=bb["lower"], name="BB lower", line=dict(width=1, color=MUTED, dash="dot"),
                                     fill="tonexty", fillcolor="rgba(139,149,167,0.08)"), 1, 1)
        elif o == "VWAP":
            fig.add_trace(go.Scatter(x=df.index, y=ind.vwap(df["High"], df["Low"], c, df["Volume"]), name="VWAP 20",
                                     line=dict(width=1.2, dash="dash")), 1, 1)
    for i, name in enumerate(lower, start=2):
        if name == "Volume":
            colors = np.where(c.diff() >= 0, "rgba(45,212,163,.55)", "rgba(255,92,122,.55)")
            fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volume", showlegend=False), i, 1)
        elif name == "RSI":
            fig.add_trace(go.Scatter(x=df.index, y=ind.rsi(c), name="RSI 14", line=dict(color="#facc15", width=1.3)), i, 1)
            for lvl in (30, 70):
                fig.add_hline(y=lvl, line=dict(color=MUTED, dash="dot", width=1), row=i, col=1)
        elif name == "MACD":
            m = ind.macd(c)
            fig.add_trace(go.Bar(x=df.index, y=m["hist"], name="MACD hist",
                                 marker_color=np.where(m["hist"] >= 0, GREEN, RED), showlegend=False), i, 1)
            fig.add_trace(go.Scatter(x=df.index, y=m["macd"], name="MACD", line=dict(width=1.2)), i, 1)
            fig.add_trace(go.Scatter(x=df.index, y=m["signal"], name="Signal", line=dict(width=1.2)), i, 1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=600, hovermode="x unified", margin=dict(t=30))
    if isinstance(df.index, pd.DatetimeIndex) and not (df.index.dayofweek >= 5).any():
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])  # hide weekend gaps (not for crypto)
    return fig


def disclaimer():
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.caption("SharkFin is an educational research tool, not investment advice. Models are probabilistic and can be wrong; "
               "past performance does not guarantee future results.")


def esc(text: str) -> str:
    """Escape characters Streamlit markdown would misinterpret ($ starts LaTeX)."""
    return str(text or "").replace("$", "\\$").replace("[", "(").replace("]", ")")
