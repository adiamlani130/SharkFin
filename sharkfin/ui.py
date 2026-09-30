"""Shared Streamlit UI helpers: styling, chart template, formatting, state."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from . import data

GREEN, RED, BLUE, ORANGE, MUTED = "#00d68f", "#ff4d6d", "#38bdf8", "#f59e0b", "#8b95a7"
BG, PANEL, GRID = "#0b0f14", "#121821", "#1f2937"
DATA_DIR = Path(".sharkfin")

pio.templates["sharkfin"] = go.layout.Template(
    layout=dict(
        paper_bgcolor=PANEL, plot_bgcolor=PANEL, font=dict(color="#e5e7eb", family="Inter, sans-serif", size=12),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID), yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        colorway=[BLUE, GREEN, ORANGE, "#a78bfa", RED, "#f472b6", "#34d399", "#fbbf24"],
        margin=dict(l=40, r=20, t=80, b=40), hoverlabel=dict(bgcolor="#1f2937"),
        title=dict(y=0.97, yanchor="top", font=dict(size=15)),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.02, x=0, yanchor="bottom"),
    )
)
pio.templates.default = "plotly_dark+sharkfin"

CSS = """
<style>
.block-container {padding-top: 1.6rem; max-width: 1400px;}
[data-testid="stMetric"] {background: #121821; border: 1px solid #1f2937; border-radius: 12px; padding: 12px 16px;}
[data-testid="stMetricLabel"] p {color: #8b95a7 !important; font-size: 0.8rem;}
[data-testid="stMetricValue"] {font-size: 1.55rem;}
.sf-card {background: #121821; border: 1px solid #1f2937; border-radius: 14px; padding: 16px 18px; margin-bottom: 12px;}
.sf-card.buy {border-left: 4px solid #00d68f;} .sf-card.sell {border-left: 4px solid #ff4d6d;}
.sf-pill {display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; margin-right: 6px;}
.sf-pos {background: rgba(0,214,143,.15); color: #00d68f;} .sf-neg {background: rgba(255,77,109,.15); color: #ff4d6d;}
.sf-neu {background: rgba(139,149,167,.15); color: #cbd5e1;}
.sf-muted {color: #8b95a7; font-size: 0.85rem;}
.sf-tape {white-space: nowrap; overflow: hidden; border-bottom: 1px solid #1f2937; padding: 6px 0 10px 0; margin-bottom: 8px;}
.sf-tape span {margin-right: 22px; font-weight: 600; font-size: 0.9rem;}
</style>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def fmt_money(x, digits: int = 2) -> str:
    if x is None or not np.isfinite(x):
        return "—"
    a, neg = abs(x), "-" if x < 0 else ""
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if a >= div:
            return f"{neg}${a / div:,.{digits}f}{suf}"
    return f"{neg}${a:,.{digits}f}"


def fmt_pct(x, digits: int = 1, sign: bool = False) -> str:
    if x is None or not np.isfinite(x):
        return "—"
    return f"{x:+.{digits}%}" if sign else f"{x:.{digits}%}"


def fmt_num(x, digits: int = 2) -> str:
    if x is None or not isinstance(x, (int, float, np.floating, np.integer)) or not np.isfinite(x):
        return "—"
    return f"{x:,.{digits}f}"


def pill(text: str, tone: str = "neu") -> str:
    return f"<span class='sf-pill sf-{tone}'>{text}</span>"


def tone(x: float, pos: float = 0.0) -> str:
    if x is None or not np.isfinite(x):
        return "neu"
    return "pos" if x > pos else "neg" if x < -pos else "neu"


def num(x, default=np.nan) -> float:
    try:
        v = float(x)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default


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


def symbol_picker(key: str, label: str = "Search a stock, ETF or crypto", default: str | None = None) -> str | None:
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
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False})


def price_chart(df: pd.DataFrame, symbol: str, overlays=("SMA 50", "SMA 200"), lower=("Volume", "RSI")) -> go.Figure:
    """Candlestick with overlays and indicator sub-panels."""
    from plotly.subplots import make_subplots

    from . import indicators as ind

    rows = 1 + len(lower)
    heights = [0.6] + [0.4 / max(1, len(lower))] * len(lower)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=heights)
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                 name=symbol, increasing_line_color=GREEN, decreasing_line_color=RED), 1, 1)
    c = df["Close"]
    for o in overlays:
        if o.startswith("SMA"):
            p = int(o.split()[1])
            fig.add_trace(go.Scatter(x=df.index, y=ind.sma(c, p), name=o, line=dict(width=1.3)), 1, 1)
        elif o.startswith("EMA"):
            p = int(o.split()[1])
            fig.add_trace(go.Scatter(x=df.index, y=ind.ema(c, p), name=o, line=dict(width=1.3)), 1, 1)
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
            colors = np.where(c.diff() >= 0, GREEN, RED)
            fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volume", showlegend=False), i, 1)
        elif name == "RSI":
            fig.add_trace(go.Scatter(x=df.index, y=ind.rsi(c), name="RSI 14", line=dict(color=ORANGE)), i, 1)
            for lvl in (30, 70):
                fig.add_hline(y=lvl, line=dict(color=MUTED, dash="dot", width=1), row=i, col=1)
        elif name == "MACD":
            m = ind.macd(c)
            fig.add_trace(go.Bar(x=df.index, y=m["hist"], name="MACD hist",
                                 marker_color=np.where(m["hist"] >= 0, GREEN, RED), showlegend=False), i, 1)
            fig.add_trace(go.Scatter(x=df.index, y=m["macd"], name="MACD", line=dict(width=1.2)), i, 1)
            fig.add_trace(go.Scatter(x=df.index, y=m["signal"], name="Signal", line=dict(width=1.2)), i, 1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=620, hovermode="x unified", margin=dict(t=30))
    if isinstance(df.index, pd.DatetimeIndex) and not (df.index.dayofweek >= 5).any():
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])  # hide weekend gaps (not for crypto)
    return fig


def disclaimer():
    st.caption("SharkFin is an educational research tool, not investment advice. Models are probabilistic and can be wrong; "
               "past performance does not guarantee future results.")


def esc(text: str) -> str:
    """Escape characters Streamlit markdown would misinterpret ($ starts LaTeX)."""
    return str(text or "").replace("$", "\\$").replace("[", "(").replace("]", ")")
