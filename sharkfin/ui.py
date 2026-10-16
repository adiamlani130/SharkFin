"""Shared Streamlit UI helpers: styling, chart template, formatting, state."""

from __future__ import annotations

import functools
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

GREEN, RED, BLUE, ORANGE, MUTED = "#2dd4a3", "#ff5c7a", "#4ea8ff", "#f5a524", "#8599ab"
PURPLE = "#a78bfa"
BG, PANEL, GRID, BORDER = "#06101a", "#0b1824", "#132536", "#172a3b"
DIVERGING = [[0, "#9b2c45"], [0.5, "#122333"], [1, "#167a5f"]]
MA_COLORS = {"SMA 20": PURPLE, "EMA 20": PURPLE, "EMA 21": "#f472b6", "SMA 50": BLUE, "SMA 200": ORANGE}
DATA_DIR = Path(".sharkfin")

pio.templates["sharkfin"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b4c4d1", family="IBM Plex Sans, system-ui, sans-serif", size=12),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=BORDER, showline=False),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=BORDER, showline=False),
        colorway=[BLUE, GREEN, ORANGE, PURPLE, RED, "#f472b6", "#5eead4", "#facc15"],
        margin=dict(l=10, r=10, t=56, b=10), hoverlabel=dict(bgcolor="#0d1b28", bordercolor="#21394f", font=dict(color="#e4edf3", family="IBM Plex Sans, sans-serif")),
        title=dict(x=0, xanchor="left", y=0.98, yanchor="top", font=dict(size=14, color="#e4edf3")),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.1, x=0, yanchor="top", font=dict(size=11)),
    )
)
pio.templates.default = "plotly_dark+sharkfin"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
/* SharkFin night-sea palette: abyss #06101a, trench #0b1824, swell #172a3b, foam #e4edf3, mist #8599ab,
   fin blue #3fa9e0 (interface), green / red (money only) */

/* ---------- layout ---------- */
.block-container {padding-top: 2.6rem; padding-bottom: 3.5rem; max-width: 1320px;}
@media (max-width: 900px) {.block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem;}}
[data-testid="stMainBlockContainer"] {animation: sf-in .45s ease-out both;}
@keyframes sf-in {from {opacity: 0;} to {opacity: 1;}}
@media (prefers-reduced-motion: reduce) {[data-testid="stMainBlockContainer"] {animation: none;}}
h2, h3, h4 {letter-spacing: -0.008em;}
[data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {padding-top: 1.1rem;}
hr {margin: 1.4rem 0 !important; border-color: #172a3b !important;}
::selection {background: rgba(63,169,224,.35);}
* {scrollbar-width: thin; scrollbar-color: #1d3347 transparent;}

/* ---------- page header ---------- */
.sf-head {margin: 0 0 1.5rem 0; padding-bottom: 1.1rem; border-bottom: 1px solid #12212f;}
.sf-head h1 {font-family: 'Newsreader', Georgia, serif !important; font-weight: 400 !important; font-size: 2.45rem !important;
  letter-spacing: -0.018em; margin: 0; padding: 0 !important; line-height: 1.1; color: #eef4f7;}
.sf-head p {color: #8599ab; margin: .5rem 0 0 0; font-size: .93rem; max-width: 760px; line-height: 1.55;}
@media (max-width: 640px) {.sf-head h1 {font-size: 1.9rem !important;}}

/* ---------- sidebar ---------- */
[data-testid="stSidebarNavLink"] {border-radius: 6px; transition: background .15s ease;}
[data-testid="stSidebarNavLink"] p {font-size: .9rem; color: #a9bccb;}
[data-testid="stSidebarNavLink"]:hover p {color: #e4edf3;}
[data-testid="stSidebarNavLink"][aria-current="page"] {background: rgba(63,169,224,.12);
  box-shadow: inset 2px 0 0 #3fa9e0;}
[data-testid="stSidebarNavLink"][aria-current="page"] p {color: #e4edf3; font-weight: 500;}
[data-testid="stNavSectionHeader"] p {font-size: .76rem; color: #5f7a90; font-weight: 500;}
[data-testid="stSidebarNavSeparator"] {border-color: #12212f;}

/* ---------- metrics ---------- */
[data-testid="stMetric"] {background: #0b1824; border: 1px solid #152738; border-radius: 10px; padding: 13px 15px 12px;
  height: 100%; transition: border-color .2s ease;}
[data-testid="stMetric"]:hover {border-color: #21394f;}
[data-testid="stMetricLabel"] p {color: #8599ab !important; font-size: .8rem !important; font-weight: 500;}
[data-testid="stMetricValue"] {white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-variant-numeric: tabular-nums; letter-spacing: -0.01em;}
[data-testid="stMetricDelta"] {font-size: .8rem; font-variant-numeric: tabular-nums;}
[data-testid="stMetricChart"] svg {background-color: transparent !important;}
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

/* ---------- tabs, buttons, inputs ---------- */
.stTabs [data-baseweb="tab-list"] {gap: 1.6rem; border-bottom: 1px solid #152738; overflow-x: auto; scrollbar-width: none;}
.stTabs [data-baseweb="tab"] {padding: .6rem 0; font-weight: 500;}
.stTabs [data-baseweb="tab"] p {font-size: .92rem; color: #8599ab; transition: color .15s ease;}
.stTabs [data-baseweb="tab"]:hover p {color: #c9d8e3;}
.stTabs [aria-selected="true"] p {color: #e4edf3; font-weight: 600;}
[data-testid="stBaseButton-primary"] {color: #03121d !important; font-weight: 600; border: none;}
[data-testid="stBaseButton-primary"] p {color: #03121d !important;}
[data-testid="stBaseButton-primary"]:hover {background: #62bbea !important;}
[data-testid="stBaseButton-secondary"] {background: #0b1824; border-color: #1d3347;}
[data-testid="stBaseButton-secondary"]:hover {border-color: #3fa9e0; color: #e4edf3;}
button:focus-visible, a:focus-visible {outline: 2px solid #8fcdf2 !important; outline-offset: 2px;}

/* ---------- cards and text ---------- */
.sf-card {background: #0b1824; border: 1px solid #152738; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;}
.sf-card.buy {border-left: 3px solid #2dd4a3;} .sf-card.sell {border-left: 3px solid #ff5c7a;}
.sf-card .t {font-weight: 600; font-size: 1.02rem; color: #e4edf3;}
.sf-card .row {margin-top: 6px; font-size: .87rem; color: #b4c4d1; line-height: 1.55;}
.sf-hero {background: #0b1824; border: 1px solid #152738; border-left: 3px solid #3fa9e0; border-radius: 10px;
  padding: 18px 20px; margin-bottom: 14px;}
.sf-hero .k {color: #8599ab; font-size: .82rem; font-weight: 500;}
.sf-hero .v {font-size: 1.95rem; font-weight: 500; letter-spacing: -0.02em; color: #eef4f7; line-height: 1.25;
  font-variant-numeric: tabular-nums;}
.sf-hero .s {color: #8599ab; font-size: .88rem; margin-top: 4px; line-height: 1.55;}
.sf-pill {display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: .74rem; font-weight: 600;
  margin-right: 6px; white-space: nowrap; vertical-align: middle;}
.sf-pos {background: rgba(45,212,163,.12); color: #2dd4a3;} .sf-neg {background: rgba(255,92,122,.12); color: #ff7a93;}
.sf-neu {background: rgba(133,153,171,.14); color: #bccad6;} .sf-info {background: rgba(63,169,224,.14); color: #8fcdf2;}
.sf-muted {color: #8599ab; font-size: .85rem;}
.sf-up {color: #2dd4a3;} .sf-down {color: #ff7a93;}
.sf-note {color: #a9bccb; font-size: .9rem; line-height: 1.6;}
.sf-kv {display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 0 1.6rem; margin: .2rem 0 .6rem 0;
  font-variant-numeric: tabular-nums;}
.sf-kv div {display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px solid #12212f; font-size: .88rem;}
.sf-kv span:first-child {color: #8599ab;} .sf-kv span:last-child {color: #e4edf3; font-weight: 500; text-align: right;}

/* ---------- checklists ---------- */
.sf-cklist {display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 0 1.6rem;}
.sf-ckrow {display: flex; gap: 10px; padding: 9px 0; border-bottom: 1px solid #12212f; font-size: .9rem; color: #e4edf3;}
.sf-ckrow .w {color: #8599ab; font-size: .8rem; margin-top: 2px; line-height: 1.45;}
.sf-ck {flex: 0 0 20px; height: 20px; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center;
  font-size: .72rem; font-weight: 700; margin-top: 1px;}
.sf-ck.ok {background: rgba(45,212,163,.15); color: #2dd4a3;} .sf-ck.no {background: rgba(255,92,122,.13); color: #ff7a93;}
.sf-ck.na {background: rgba(133,153,171,.14); color: #8599ab;}

/* ---------- news ---------- */
.sf-news {padding: 12px 0; border-bottom: 1px solid #12212f;}
.sf-news a {color: #e4edf3 !important; text-decoration: none !important; font-weight: 500; line-height: 1.45;}
.sf-news a:hover {color: #8fcdf2 !important;}
.sf-news .m {color: #8599ab; font-size: .78rem; margin-top: 3px;}
.sf-news .d {color: #98abbb; font-size: .86rem; margin-top: 4px; line-height: 1.55;}

/* ---------- misc ---------- */
[data-testid="stExpander"] details {border-color: #152738; border-radius: 10px; background: rgba(11,24,36,.5);}
[data-testid="stExpander"] summary p {font-weight: 500;}
[data-testid="stCaptionContainer"] {color: #8599ab;}
[data-testid="stAlert"] {border-radius: 10px;}
.sf-tape {white-space: nowrap; overflow: hidden; border-bottom: 1px solid #152738; padding: 6px 0 10px 0; margin-bottom: 8px;}
/* ---------- strategy playbook ---------- */
.sf-strats {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; margin-bottom: .6rem;}
@container (max-width: 1000px) {.sf-strats {grid-template-columns: repeat(2, minmax(0, 1fr));}}
@container (max-width: 560px) {.sf-strats {grid-template-columns: minmax(0, 1fr);}}
.sf-strat {background: #0b1824; border: 1px solid #152738; border-top: 2px solid var(--c); border-radius: 10px; padding: 14px 16px;}
.sf-strat .nm {font-weight: 600; color: #e4edf3; font-size: .98rem;}
.sf-strat .tg {color: var(--c); font-size: .78rem; font-weight: 500; margin-top: 2px;}
.sf-strat .big {font-size: 1.65rem; font-weight: 500; color: #eef4f7; letter-spacing: -0.02em; margin-top: 8px;
  font-variant-numeric: tabular-nums;}
.sf-strat .big span {font-size: .8rem; color: #8599ab; font-weight: 400;}
.sf-strat .sub {color: #a9bccb; font-size: .8rem;}
.sf-strat .bl {color: #8599ab; font-size: .8rem; margin-top: 8px; line-height: 1.5;}
.sf-steps {margin: 8px 0 0 0; padding-left: 1.2rem; font-size: .88rem; color: #b4c4d1; line-height: 1.6;}
.sf-steps li {margin-bottom: 6px;} .sf-steps b {color: #e4edf3;}
</style>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()


def asset(name: str) -> str:
    """A text file from ``sharkfin/assets`` (e.g. the landing page's ocean), re-read when it changes."""
    p = Path(__file__).with_name("assets") / name
    return _read_asset(p, p.stat().st_mtime)


@functools.lru_cache(maxsize=16)
def _read_asset(path: Path, mtime: float) -> str:
    return path.read_text()


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


def load_list(name: str) -> list:
    """A list saved next to the portfolio and watchlist (e.g. the Leader Dip signal log)."""
    return _load(name)


def save_list(name: str, rows: list) -> bool:
    try:
        p = DATA_DIR / f"{name}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(rows, indent=1, default=str))
        return True
    except Exception:
        return False


def save_state():
    try:
        for name in ("portfolio", "watchlist"):
            p = _path(name)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(st.session_state[name], indent=2, default=str))
    except Exception as e:
        st.toast(f"Could not save: {e}")


def my_swing_rules() -> dict | None:
    """The rule set the user saved from Strategy Lab as their swing strategy, if any."""
    rows = _load("my_swing_strategy")
    return rows[0] if rows and isinstance(rows[0], dict) else None


def save_my_swing_rules(rules: dict) -> bool:
    return save_list("my_swing_strategy", [rules])


def swing_choice() -> str:
    """The swing strategy picked anywhere in the app (shared by Top Performers and Research)."""
    from . import swing

    ss = st.session_state
    if "swing_choice" not in ss:
        saved = _load("swing_choice")
        ss.swing_choice = saved[0] if saved and isinstance(saved[0], str) else swing.LEADER_DIP
    if ss.swing_choice not in swing.choices(my_swing_rules()):
        ss.swing_choice = swing.LEADER_DIP
    return ss.swing_choice


def set_swing_choice(name: str):
    st.session_state.swing_choice = name
    save_list("swing_choice", [name])


def swing_picker(key: str) -> str:
    """Select box for the swing strategy; the choice is remembered across pages and visits."""
    from . import swing

    current = swing_choice()
    opts = swing.choices(my_swing_rules())
    wkey = f"swing_pick_{key}"
    if st.session_state.get(wkey) not in opts:
        st.session_state[wkey] = current
    return st.selectbox("Swing strategy", opts, key=wkey, on_change=lambda: set_swing_choice(st.session_state[wkey]),
                        help="Leader Dip is SharkFin's tested default. Pick a Strategy Lab template, or save your own "
                             "rules in Strategy Lab → Build and test → Use as my swing strategy. The choice applies on "
                             "Top Performers and Research.")


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


WALK_FORWARD_NOTE = ("Walk-forward test: each year's settings were picked using only the three years before it, then "
                     "traded on that year untouched. Only those unseen years are shown, so every number here is out "
                     "of sample.")


def walk_forward_table(wf: dict, key: str, note: str = ""):
    """The folds of a walk-forward test: when settings were picked, what was chosen, and how the next year went."""
    f = wf["folds"].drop(columns=["settings", "Fold"], errors="ignore")
    st.dataframe(f, hide_index=True, width="stretch", key=key, column_config={
        "Train Sharpe": st.column_config.NumberColumn("Sharpe when picked", format="%.2f"),
        "Test return": st.column_config.NumberColumn("Next year's return", format="percent"),
        "Test Sharpe": st.column_config.NumberColumn("Next year's Sharpe", format="%.2f"),
        "Test worst drop": st.column_config.NumberColumn("Next year's worst drop", format="percent")})
    stable = wf.get("stable")
    kept = (f" The settings carried over from one year to the next {stable:.0%} of the time."
            if stable is not None and np.isfinite(stable) else "")
    st.caption(WALK_FORWARD_NOTE + kept + (" " + note if note else ""))


def disclaimer():
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.caption("SharkFin is an educational research tool, not investment advice. Models are probabilistic and can be wrong; "
               "past performance does not guarantee future results.")


def esc(text: str) -> str:
    """Escape characters Streamlit markdown would misinterpret ($ starts LaTeX)."""
    return str(text or "").replace("$", "\\$").replace("[", "(").replace("]", ")")
