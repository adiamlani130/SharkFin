"""Shared Streamlit UI helpers: styling, chart template, formatting, state."""

from __future__ import annotations

import functools
import hashlib
import html as _html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from . import data, store

# Chart colors. Pages build figures with these night-mode values; ui.plotly() swaps them for their day-mode
# equivalents (DAY_COLORS) when the viewer is in day mode, so pages never need to know the mode.
GREEN, RED, BLUE, ORANGE, MUTED = "#2dd4a3", "#ff5c7a", "#4ea8ff", "#f5a524", "#8599ab"
PURPLE = "#a78bfa"
BG, PANEL, GRID, BORDER = "#05060d", "#0c0e1c", "#181c31", "#1e2340"
DIVERGING = [[0, "#9b2c45"], [0.5, "#151a2e"], [1, "#167a5f"]]
MA_COLORS = {"SMA 20": PURPLE, "EMA 20": PURPLE, "EMA 21": "#f472b6", "SMA 50": BLUE, "SMA 200": ORANGE}
DATA_DIR = store.DATA_DIR

# Night color -> day color. Keys are lowercase; rgba keys are prefixes so any opacity carries over.
DAY_COLORS = {
    GREEN: "#059669", RED: "#e11d48", BLUE: "#9333ea", ORANGE: "#ea580c", PURPLE: "#4f46e5", MUTED: "#9a8088",
    "#ff7a93": "#e11d48", "#3fa9e0": "#db2777", "#f472b6": "#0891b2", "#5eead4": "#0d9488", "#facc15": "#ca8a04",
    "#c9d1dc": "#3b2630", "#e4edf3": "#3b2630", "#e6e9ef": "#3b2630", "#5b6574": "#b8a3aa", "#7ee0bf": "#6ee7b7",
    "#ff9fb0": "#fda4af", "#2a3442": "#ecd9de", "#8b95a7": "#9a8088", "#5f6b7d": "#c4b0b6",
    "#9b2c45": "#f27d95", "#151a2e": "#fdf4f2", "#167a5f": "#5cc79c", BG: "#ffffff", PANEL: "#fff7f6",
    GRID: "#f3e4e7", BORDER: "#efd9de",
    "rgba(45,212,163,": "rgba(5,150,105,", "rgba(255,92,122,": "rgba(225,29,72,", "rgba(78,168,255,": "rgba(219,39,119,",
    "rgba(139,149,167,": "rgba(154,128,136,",
}
_DAY_SWAP = re.compile("|".join(re.escape(k) for k in sorted(DAY_COLORS, key=len, reverse=True)), re.I)

_COLORWAY = [BLUE, GREEN, ORANGE, PURPLE, RED, "#f472b6", "#5eead4", "#facc15"]


def _template(day: bool) -> go.layout.Template:
    ink, title, grid, line = ("#5a4650", "#24151d", "#f3e4e7", "#efd9de") if day else ("#b7bbd4", "#eceefa", GRID, BORDER)
    return go.layout.Template(layout=dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=ink, family="IBM Plex Sans, system-ui, sans-serif", size=12),
        xaxis=dict(gridcolor=grid, zerolinecolor=grid, linecolor=line, showline=False),
        yaxis=dict(gridcolor=grid, zerolinecolor=grid, linecolor=line, showline=False),
        colorway=[day_color(c) for c in _COLORWAY] if day else _COLORWAY,
        margin=dict(l=10, r=10, t=56, b=10),
        hoverlabel=dict(bgcolor="#ffffff" if day else "#11142a", bordercolor="#eab8c4" if day else "#2b3160",
                        font=dict(color=title, family="IBM Plex Sans, sans-serif")),
        title=dict(x=0, xanchor="left", y=0.98, yanchor="top", font=dict(size=14, color=title)),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.1, x=0, yanchor="top", font=dict(size=11)),
    ))


def day_color(c: str) -> str:
    """The day-mode version of a night-mode chart color (unchanged if it has none)."""
    return _DAY_SWAP.sub(lambda m: DAY_COLORS[m.group(0).lower()], c) if isinstance(c, str) else c


pio.templates["sharkfin"] = _template(day=False)
pio.templates["sharkfin_day"] = _template(day=True)
pio.templates.default = "plotly_dark+sharkfin"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
/* Colors come from the --sf-* variables that theme_css() sets for day or night mode.
   Accent = interface, green / red = money only. */

/* ---------- layout ---------- */
.block-container {padding-top: 2.6rem; padding-bottom: 3.5rem; max-width: 1320px;}
@media (max-width: 900px) {.block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem;}}
h2, h3, h4 {letter-spacing: -0.008em;}
[data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {padding-top: 1.1rem;}
hr {margin: 1.4rem 0 !important; border-color: var(--sf-line) !important;}
::selection {background: rgba(var(--sf-accent-rgb),.35);}
* {scrollbar-width: thin; scrollbar-color: var(--sf-line-hover) transparent;}

/* ---------- page header ---------- */
.sf-head {margin: 0 0 1.5rem 0; padding-bottom: 1.1rem; border-bottom: 1px solid var(--sf-line-soft);}
.sf-head h1 {font-family: 'Newsreader', Georgia, serif !important; font-weight: 400 !important; font-size: 2.45rem !important;
  letter-spacing: -0.018em; margin: 0; padding: 0 !important; line-height: 1.1; color: var(--sf-strong);}
.sf-head p {color: var(--sf-muted); margin: .5rem 0 0 0; font-size: .93rem; max-width: 760px; line-height: 1.55;}
@media (max-width: 640px) {.sf-head h1 {font-size: 1.9rem !important;}}

/* ---------- sidebar ---------- */
[data-testid="stSidebarNavLink"] {border-radius: 6px; transition: background .15s ease;}
[data-testid="stSidebarNavLink"] p {font-size: .9rem; color: var(--sf-soft);}
[data-testid="stSidebarNavLink"]:hover p {color: var(--sf-text);}
[data-testid="stSidebarNavLink"][aria-current="page"] {background: rgba(var(--sf-accent-rgb),.12);
  box-shadow: inset 2px 0 0 var(--sf-accent);}
[data-testid="stSidebarNavLink"][aria-current="page"] p {color: var(--sf-text); font-weight: 500;}
[data-testid="stNavSectionHeader"] p {font-size: .76rem; color: var(--sf-faint); font-weight: 500;}
[data-testid="stSidebarNavSeparator"] {border-color: var(--sf-line-soft);}

/* ---------- metrics ---------- */
[data-testid="stMetric"] {background: var(--sf-panel); border: 1px solid var(--sf-line); border-radius: 10px; padding: 13px 15px 12px;
  height: 100%; transition: border-color .2s ease;}
[data-testid="stMetric"]:hover {border-color: var(--sf-line-hover);}
[data-testid="stMetricLabel"] p {color: var(--sf-muted) !important; font-size: .8rem !important; font-weight: 500;}
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
.stTabs [data-baseweb="tab-list"] {gap: 1.6rem; border-bottom: 1px solid var(--sf-line); overflow-x: auto; scrollbar-width: none;}
.stTabs [data-baseweb="tab"] {padding: .6rem 0; font-weight: 500;}
.stTabs [data-baseweb="tab"] p {font-size: .92rem; color: var(--sf-muted); transition: color .15s ease;}
.stTabs [data-baseweb="tab"]:hover p {color: var(--sf-soft);}
.stTabs [aria-selected="true"] p {color: var(--sf-text); font-weight: 600;}
[data-testid="stBaseButton-primary"] {color: var(--sf-on-accent) !important; font-weight: 600; border: none;}
[data-testid="stBaseButton-primary"] p {color: var(--sf-on-accent) !important;}
[data-testid="stBaseButton-primary"]:hover {background: var(--sf-accent-2) !important;}
[data-testid="stBaseButton-secondary"] {background: var(--sf-panel); border-color: var(--sf-line-hover);}
[data-testid="stBaseButton-secondary"]:hover {border-color: var(--sf-accent); color: var(--sf-text);}
button:focus-visible, a:focus-visible {outline: 2px solid var(--sf-link) !important; outline-offset: 2px;}

/* ---------- cards and text ---------- */
.sf-card {background: var(--sf-panel); border: 1px solid var(--sf-line); border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;}
.sf-card.buy {border-left: 3px solid var(--sf-up);} .sf-card.sell {border-left: 3px solid var(--sf-down);}
.sf-card .t {font-weight: 600; font-size: 1.02rem; color: var(--sf-text);}
.sf-card .row {margin-top: 6px; font-size: .87rem; color: var(--sf-body); line-height: 1.55;}
.sf-hero {background: var(--sf-panel); border: 1px solid var(--sf-line); border-left: 3px solid var(--sf-accent); border-radius: 10px;
  padding: 18px 20px; margin-bottom: 14px;}
.sf-hero .k {color: var(--sf-muted); font-size: .82rem; font-weight: 500;}
.sf-hero .v {font-size: 1.95rem; font-weight: 500; letter-spacing: -0.02em; color: var(--sf-strong); line-height: 1.25;
  font-variant-numeric: tabular-nums;}
.sf-hero .s {color: var(--sf-muted); font-size: .88rem; margin-top: 4px; line-height: 1.55;}
.sf-pill {display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: .74rem; font-weight: 600;
  margin-right: 6px; white-space: nowrap; vertical-align: middle;}
.sf-pos {background: rgba(var(--sf-up-rgb),.12); color: var(--sf-up);} .sf-neg {background: rgba(var(--sf-down-rgb),.12); color: var(--sf-down);}
.sf-neu {background: rgba(var(--sf-neu-rgb),.14); color: var(--sf-neu-ink);} .sf-info {background: rgba(var(--sf-info-rgb),.14); color: var(--sf-info);}
.sf-muted {color: var(--sf-muted); font-size: .85rem;}
.sf-up {color: var(--sf-up);} .sf-down {color: var(--sf-down);}
.sf-note {color: var(--sf-soft); font-size: .9rem; line-height: 1.6;}
.sf-kv {display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 0 1.6rem; margin: .2rem 0 .6rem 0;
  font-variant-numeric: tabular-nums;}
.sf-kv div {display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px solid var(--sf-line-soft); font-size: .88rem;}
.sf-kv span:first-child {color: var(--sf-muted);} .sf-kv span:last-child {color: var(--sf-text); font-weight: 500; text-align: right;}

/* ---------- checklists ---------- */
.sf-cklist {display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 0 1.6rem;}
.sf-ckrow {display: flex; gap: 10px; padding: 9px 0; border-bottom: 1px solid var(--sf-line-soft); font-size: .9rem; color: var(--sf-text);}
.sf-ckrow .w {color: var(--sf-muted); font-size: .8rem; margin-top: 2px; line-height: 1.45;}
.sf-ck {flex: 0 0 20px; height: 20px; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center;
  font-size: .72rem; font-weight: 700; margin-top: 1px;}
.sf-ck.ok {background: rgba(var(--sf-up-rgb),.15); color: var(--sf-up);} .sf-ck.no {background: rgba(var(--sf-down-rgb),.13); color: var(--sf-down);}
.sf-ck.na {background: rgba(var(--sf-neu-rgb),.14); color: var(--sf-muted);}

/* ---------- news ---------- */
.sf-news {padding: 12px 0; border-bottom: 1px solid var(--sf-line-soft);}
.sf-news a {color: var(--sf-text) !important; text-decoration: none !important; font-weight: 500; line-height: 1.45;}
.sf-news a:hover {color: var(--sf-link) !important;}
.sf-news .m {color: var(--sf-muted); font-size: .78rem; margin-top: 3px;}
.sf-news .d {color: var(--sf-soft); font-size: .86rem; margin-top: 4px; line-height: 1.55;}

/* ---------- misc ---------- */
[data-testid="stExpander"] details {border-color: var(--sf-line); border-radius: 10px; background: var(--sf-panel-a);}
[data-testid="stExpander"] summary p {font-weight: 500;}
[data-testid="stCaptionContainer"] {color: var(--sf-muted);}
[data-testid="stAlert"] {border-radius: 10px;}
.sf-tape {white-space: nowrap; overflow: hidden; border-bottom: 1px solid var(--sf-line); padding: 6px 0 10px 0; margin-bottom: 8px;}
/* ---------- strategy playbook ---------- */
.sf-strats {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; margin-bottom: .6rem;}
@container (max-width: 1000px) {.sf-strats {grid-template-columns: repeat(2, minmax(0, 1fr));}}
@container (max-width: 560px) {.sf-strats {grid-template-columns: minmax(0, 1fr);}}
.sf-strat {background: var(--sf-panel); border: 1px solid var(--sf-line); border-top: 2px solid var(--c); border-radius: 10px; padding: 14px 16px;}
.sf-strat .nm {font-weight: 600; color: var(--sf-text); font-size: .98rem;}
.sf-strat .tg {color: var(--c); font-size: .78rem; font-weight: 500; margin-top: 2px;}
.sf-strat .big {font-size: 1.65rem; font-weight: 500; color: var(--sf-strong); letter-spacing: -0.02em; margin-top: 8px;
  font-variant-numeric: tabular-nums;}
.sf-strat .big span {font-size: .8rem; color: var(--sf-muted); font-weight: 400;}
.sf-strat .sub {color: var(--sf-soft); font-size: .8rem;}
.sf-strat .bl {color: var(--sf-muted); font-size: .8rem; margin-top: 8px; line-height: 1.5;}
.sf-steps {margin: 8px 0 0 0; padding-left: 1.2rem; font-size: .88rem; color: var(--sf-body); line-height: 1.6;}
.sf-steps li {margin-bottom: 6px;} .sf-steps b {color: var(--sf-text);}

/* ---------- market dashboard: today ---------- */
.sf-today {background: var(--sf-panel); border: 1px solid var(--sf-line); border-left: 3px solid var(--c, var(--sf-accent)); border-radius: 12px;
  padding: 16px 18px; margin: .2rem 0 .8rem;}
.sf-today .hd {display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap;}
.sf-today .lb {font-size: 1.35rem; font-weight: 600; color: var(--sf-strong); letter-spacing: -0.01em;}
.sf-today .tx {color: var(--sf-body); font-size: .92rem; line-height: 1.6; margin-top: 6px;}
.sf-today .st {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .6rem 1.4rem; margin-top: 12px;
  font-variant-numeric: tabular-nums;}
@container (max-width: 700px) {.sf-today .st {grid-template-columns: repeat(2, minmax(0, 1fr));}}
.sf-today .st div {border-top: 1px solid var(--sf-line); padding-top: 8px;}
.sf-today .st .k {color: var(--sf-muted); font-size: .76rem;} .sf-today .st .v {color: var(--sf-strong); font-size: 1.05rem; font-weight: 500;}
.sf-today .st .s {color: var(--sf-muted); font-size: .74rem;}
.sf-drivers {display: grid; gap: 8px; margin-top: 12px;}
.sf-driver {display: flex; gap: 10px; align-items: baseline; font-size: .88rem; color: var(--sf-body); line-height: 1.5;}
.sf-driver .sf-pill {flex: 0 0 auto; min-width: 92px; text-align: center;}
.sf-driver q {color: var(--sf-muted); font-size: .8rem;}

/* ---------- speculation radar ---------- */
.sf-themes {display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .8rem; margin: .3rem 0 1rem;}
@container (max-width: 1000px) {.sf-themes {grid-template-columns: repeat(2, minmax(0, 1fr));}}
@container (max-width: 600px) {.sf-themes {grid-template-columns: minmax(0, 1fr);}}
.sf-theme {position: relative; background: linear-gradient(180deg, var(--sf-panel-hi), var(--sf-panel) 60%); border: 1px solid var(--sf-line);
  border-radius: 12px; padding: 14px 16px 13px; overflow: hidden;
  transition: transform .35s var(--sf-ease), border-color .35s ease, box-shadow .35s ease;
  animation: sf-rise .6s var(--sf-ease) both;}
.sf-theme::before {content: ""; position: absolute; inset: 0 0 auto 0; height: 2px; background: var(--c); opacity: .85;}
.sf-theme:hover {transform: translateY(-3px); border-color: var(--sf-line-hover); box-shadow: 0 14px 30px -18px rgba(var(--sf-shadow-rgb),.8);}
.sf-theme .top {display: flex; align-items: center; gap: 4px; flex-wrap: wrap;}
.sf-theme .hz {margin-left: auto; color: var(--sf-faint); font-size: .74rem;}
.sf-theme .nm {font-weight: 600; color: var(--sf-strong); font-size: 1.04rem; margin-top: 10px;}
.sf-theme .tg {color: var(--sf-soft); font-size: .85rem; line-height: 1.5; margin-top: 4px;}
.sf-theme .nums {display: flex; gap: 14px; flex-wrap: wrap; margin-top: 10px; font-size: .78rem; color: var(--sf-muted);
  font-variant-numeric: tabular-nums;}
.sf-theme .nums b {font-weight: 600; color: var(--sf-text);} .sf-theme .nums b.sf-up {color: var(--sf-up);} .sf-theme .nums b.sf-down {color: var(--sf-down);}
.sf-theme .tk {margin-top: 10px; display: flex; flex-wrap: wrap; gap: 4px;}
.sf-theme .tk code {background: rgba(var(--sf-accent-rgb),.1); color: var(--sf-link); border-radius: 5px; padding: 1px 6px; font-size: .74rem;}
.sf-themes .sf-theme:nth-child(2) {animation-delay: .04s} .sf-themes .sf-theme:nth-child(3) {animation-delay: .08s}
.sf-themes .sf-theme:nth-child(4) {animation-delay: .12s} .sf-themes .sf-theme:nth-child(5) {animation-delay: .16s}
.sf-themes .sf-theme:nth-child(6) {animation-delay: .2s} .sf-themes .sf-theme:nth-child(n+7) {animation-delay: .24s}
.sf-stages {display: grid; gap: 8px;} .sf-stage {display: flex; gap: 10px; align-items: baseline; font-size: .88rem; color: var(--sf-body);}
.sf-stage .sf-pill {flex: 0 0 auto; min-width: 84px; text-align: center;}
.sf-cols {display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.2rem; margin-top: .4rem;}
@container (max-width: 700px) {.sf-cols, .sf-cols.two {grid-template-columns: minmax(0, 1fr);}}
.sf-cols.two {grid-template-columns: repeat(2, minmax(0, 1fr));}
.sf-cols h5, .sf-h5 {font-size: .82rem !important; color: var(--sf-muted) !important; font-weight: 600 !important; margin: .3rem 0 0 !important;
  padding: 0 !important; text-transform: uppercase; letter-spacing: .05em;}
.sf-steps.ok li::marker {color: var(--sf-up);} .sf-steps.bad li::marker {color: var(--sf-down);}
.sf-timeline li {padding-left: 2px;}

/* ---------- motion: soft entrances and smooth state changes ---------- */
:root {--sf-ease: cubic-bezier(.22,.8,.24,1);}
html {scroll-behavior: smooth;}
@keyframes sf-rise {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: none;}}
@keyframes sf-fade {from {opacity: 0;} to {opacity: 1;}}
/* new page content glides in once; elements that stay on screen across reruns don't replay it */
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"],
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
  animation: sf-rise .5s var(--sf-ease) both;}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > :nth-child(2) {animation-delay: .03s;}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > :nth-child(3) {animation-delay: .06s;}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > :nth-child(4) {animation-delay: .09s;}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > :nth-child(5) {animation-delay: .12s;}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > :nth-child(n+6) {animation-delay: .15s;}
.sf-rise {animation: sf-rise .6s var(--sf-ease) both;}
.sf-head h1 {animation: sf-rise .55s var(--sf-ease) both;}
.sf-head p {animation: sf-rise .55s .06s var(--sf-ease) both;}
.sf-head {position: relative;}
.sf-head::after {content: ""; position: absolute; left: 0; bottom: -1px; height: 1px; width: 120px;
  background: var(--sf-grad); animation: sf-fade 1s .2s ease both;}
.sf-card, .sf-hero, .sf-strat, [data-testid="stMetric"] {
  transition: transform .3s var(--sf-ease), border-color .3s ease, box-shadow .3s ease, background-color .3s ease;}
.sf-card:hover, .sf-strat:hover {transform: translateY(-2px); border-color: var(--sf-line-hover); box-shadow: 0 12px 26px -18px rgba(var(--sf-shadow-rgb),.85);}
[data-testid="stMetric"]:hover {transform: translateY(-1px); box-shadow: 0 10px 22px -18px rgba(var(--sf-shadow-rgb),.9);}
.sf-hero {background: linear-gradient(135deg, rgba(var(--sf-accent-rgb),.08), transparent 55%), var(--sf-panel);}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-pills"],
[data-testid="stBaseButton-segmented_control"], [data-testid="stBaseButton-pillsActive"],
[data-testid="stBaseButton-segmented_controlActive"] {
  transition: background-color .2s ease, border-color .2s ease, color .2s ease, transform .15s ease, box-shadow .2s ease !important;}
[data-testid="stBaseButton-primary"]:hover {box-shadow: 0 6px 18px -8px rgba(var(--sf-accent-rgb),.7);}
[data-testid="stBaseButton-primary"]:active, [data-testid="stBaseButton-secondary"]:active {transform: translateY(1px) scale(.99);}
.stTabs [data-baseweb="tab-highlight"] {transition: left .35s var(--sf-ease), width .35s var(--sf-ease) !important;
  background: var(--sf-accent) !important; height: 2px !important; border-radius: 2px;}
.stTabs [data-baseweb="tab-panel"] {animation: sf-fade .35s ease both;}
[data-testid="stExpander"] details {transition: border-color .25s ease, background-color .25s ease;}
[data-testid="stExpander"] details:hover {border-color: var(--sf-line-hover);}
[data-testid="stExpander"] details[open] > div {animation: sf-fade .3s ease both;}
[data-testid="stExpander"] summary svg {transition: transform .25s var(--sf-ease);}
[data-testid="stSidebarNavLink"] {transition: background-color .2s ease, box-shadow .25s var(--sf-ease) !important;}
[data-testid="stSidebarNavLink"]:hover {background: rgba(var(--sf-accent-rgb),.07);}
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {animation: sf-fade .45s ease both;}
[data-testid="stDataFrame"] {border-radius: 10px; overflow: hidden;}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-testid="stNumberInputContainer"] {
  transition: border-color .2s ease, box-shadow .2s ease;}
[data-baseweb="select"] > div:hover, [data-baseweb="input"]:hover {border-color: var(--sf-line-hover) !important;}
[data-baseweb="popover"] {animation: sf-fade .15s ease both;}
.sf-news {transition: background-color .2s ease, padding-left .25s var(--sf-ease);}
.sf-news:hover {background: rgba(var(--sf-accent-rgb),.035); padding-left: 6px;}
[data-testid="stSidebar"] {transition: transform .35s var(--sf-ease), width .35s var(--sf-ease) !important;}
/* a calmer "running" shimmer instead of the stock flicker while a page recomputes */
[data-stale="true"] {opacity: .55 !important; transition: opacity .4s ease .15s !important;}
/* ---------- day / night switch (bottom-left corner) ---------- */
#sf-mode {position: fixed; left: .9rem; bottom: .9rem; z-index: 1000002; display: flex; gap: 2px; padding: 3px;
  border-radius: 999px; background: var(--sf-panel-a); border: 1px solid var(--sf-line); backdrop-filter: blur(12px);
  box-shadow: 0 6px 20px -12px rgba(var(--sf-shadow-rgb),.6); font-family: 'IBM Plex Sans', sans-serif;}
#sf-mode button {display: inline-flex; align-items: center; gap: 5px; border: 0; background: transparent; cursor: pointer;
  color: var(--sf-muted); font: 500 .78rem/1 'IBM Plex Sans', sans-serif; padding: 6px 10px 6px 8px; border-radius: 999px;
  transition: background .25s ease, color .2s ease;}
#sf-mode button:hover {color: var(--sf-text);}
#sf-mode svg {width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round;}
#sf-mode button[data-mode="night"] svg {fill: currentColor; stroke: none;}
#sf-mode button[aria-pressed="true"] {background: var(--sf-grad); color: #fff; cursor: default;
  box-shadow: 0 4px 14px -6px rgba(var(--sf-accent-rgb),.7);}
#sf-mode button:focus-visible {outline: 2px solid var(--sf-link); outline-offset: 1px;}
@media (max-width: 640px) {#sf-mode {left: .6rem; bottom: .6rem;} #sf-mode span {display: none;} #sf-mode button {padding: 6px 8px;}}
[data-testid="stSidebarContent"] {padding-bottom: 3.6rem;}
html.sf-switching body {opacity: 0; transition: opacity .2s ease;}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {animation-duration: .01ms !important; animation-delay: 0s !important;
    transition-duration: .01ms !important; scroll-behavior: auto !important;}
}
</style>
"""


# ---------------------------------------------------------------------------
# Day / night mode
# ---------------------------------------------------------------------------
# Streamlit's own light and dark themes ([theme.light] / [theme.dark] in .streamlit/config.toml) style the built-in
# widgets and tables; these variables style SharkFin's own cards, and the backgrounds below decorate the empty space.
# Night: black with aurora green / blue / violet. Day: white with watercolor pink / orange / magenta.

PALETTES = {
    "night": {
        "bg": "#05060d", "panel": "#0c0e1c", "panel-a": "rgba(12,14,28,.55)", "panel-hi": "rgba(24,28,58,.9)",
        "line": "#1a1e36", "line-soft": "#141729", "line-hover": "#2e3566",
        "text": "#e6e8f4", "strong": "#f3f4fb", "body": "#b7bbd4", "soft": "#a6abc8", "muted": "#8a8fae", "faint": "#5f6488",
        "neu-ink": "#c3c6dc", "accent": "#6d8cff", "accent-2": "#8ea6ff", "on-accent": "#060818", "link": "#a3b6ff",
        "up": "#34d399", "down": "#fb7185", "accent-rgb": "109,140,255", "up-rgb": "52,211,153", "down-rgb": "251,113,133",
        "neu-rgb": "138,143,174", "shadow-rgb": "0,0,0", "info": "#a3b6ff", "info-rgb": "109,140,255",
        "grad": "linear-gradient(90deg, #34d399, #3b82f6 45%, #a855f7)",
    },
    "day": {
        "bg": "#ffffff", "panel": "#fffafa", "panel-a": "rgba(255,247,246,.7)", "panel-hi": "rgba(255,240,243,.95)",
        "line": "#f3dfe3", "line-soft": "#f6e8eb", "line-hover": "#eebccb",
        "text": "#2b1b24", "strong": "#1f1219", "body": "#54414b", "soft": "#614c56", "muted": "#8b7179", "faint": "#ad959c",
        "neu-ink": "#6b545c", "accent": "#db2777", "accent-2": "#be185d", "on-accent": "#ffffff", "link": "#c2185b",
        "up": "#059669", "down": "#e11d48", "accent-rgb": "219,39,119", "up-rgb": "5,150,105", "down-rgb": "225,29,72",
        "neu-rgb": "139,113,121", "shadow-rgb": "150,52,90", "info": "#7e22ce", "info-rgb": "147,51,234",
        "grad": "linear-gradient(90deg, #c026d3, #db2777 40%, #fb923c)",
    },
}


def _waves(colors: list[str], opacity: float) -> str:
    """Three soft wave lines along the bottom of the window, as a CSS background image."""
    paths = [
        "M0 90 C160 40 320 140 480 90 S800 40 960 90 S1280 140 1440 90",
        "M0 120 C180 75 340 165 520 120 S860 70 1040 120 S1300 160 1440 115",
        "M0 150 C200 110 380 190 560 150 S900 105 1080 150 S1320 185 1440 145",
    ]
    lines = "".join(f"<path d='{d}' fill='none' stroke='{c}' stroke-width='1.4' stroke-opacity='{opacity}'/>"
                    for d, c in zip(paths, colors))
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 220' preserveAspectRatio='none'>{lines}</svg>"
    return "url(\"data:image/svg+xml," + svg.replace("#", "%23").replace("<", "%3C").replace(">", "%3E") + "\")"


def theme_css(m: str) -> str:
    pal = PALETTES[m]
    vars_ = "".join(f"--sf-{k}: {v};" for k, v in pal.items())
    if m == "night":
        glow = ("radial-gradient(55% 40% at 0% 0%, rgba(52,211,153,.13), transparent 70%), "
                "radial-gradient(45% 38% at 100% 0%, rgba(168,85,247,.15), transparent 70%), "
                "radial-gradient(60% 45% at 75% 100%, rgba(59,130,246,.11), transparent 70%)")
        waves = _waves(["#34d399", "#3b82f6", "#a855f7"], .16)
        side = "linear-gradient(180deg, rgba(52,211,153,.05), transparent 30%, rgba(168,85,247,.06)), #04050b"
    else:
        glow = ("radial-gradient(42% 34% at 100% 0%, rgba(244,114,182,.2), transparent 70%), "
                "radial-gradient(38% 30% at 82% 6%, rgba(251,146,60,.12), transparent 70%), "
                "radial-gradient(40% 36% at 0% 100%, rgba(251,146,60,.11), transparent 70%), "
                "radial-gradient(34% 30% at 14% 96%, rgba(219,39,119,.09), transparent 70%)")
        waves = _waves(["#f472b6", "#fb923c", "#c026d3"], .22)
        side = "linear-gradient(180deg, rgba(244,114,182,.08), transparent 35%, rgba(251,146,60,.08)), #fff8f7"
    return f"""<style>
:root {{{vars_}}}
.stApp {{background: {glow}, {waves} center bottom / 100% 190px no-repeat, var(--sf-bg) !important;
  background-attachment: fixed !important;}}
[data-testid="stHeader"] {{background: transparent !important;}}
[data-testid="stSidebar"] {{background: {side} !important;}}
</style>"""


def mode() -> str:
    """"day" or "night": the theme this viewer's browser is showing (Streamlit reports it with each run)."""
    try:
        return "day" if st.context.theme.type == "light" else "night"
    except Exception:
        return "night"


def color(c: str) -> str:
    """A night-mode color adjusted for the current mode (for colors written into HTML)."""
    return day_color(c) if mode() == "day" else c


_TOGGLE_JS = """(() => {
  const mode = "%s";
  let el = document.getElementById("sf-mode");
  if (!el) {
    el = document.createElement("div");
    el.id = "sf-mode";
    el.setAttribute("role", "group");
    el.setAttribute("aria-label", "Color theme");
    el.innerHTML =
      '<button type="button" data-mode="day" title="Day mode"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/>' +
      '<path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg><span>Day</span></button>' +
      '<button type="button" data-mode="night" title="Night mode"><svg viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6z"/></svg><span>Night</span></button>';
    document.body.appendChild(el);
    el.addEventListener("click", (ev) => {
      const b = ev.target.closest("button");
      if (!b || b.getAttribute("aria-pressed") === "true") return;
      // Streamlit keeps the chosen theme in localStorage, one key per page path; set them all, then reload.
      const v = JSON.stringify(b.dataset.mode === "day" ? "Light" : "Dark");
      const paths = new Set(["/", location.pathname]);
      document.querySelectorAll("a[href]").forEach((a) => {
        try { const u = new URL(a.href); if (u.origin === location.origin) paths.add(u.pathname); } catch (e) {}
      });
      try {
        Object.keys(localStorage).filter((k) => k.startsWith("stActiveTheme-")).forEach((k) => localStorage.setItem(k, v));
        paths.forEach((p) => localStorage.setItem("stActiveTheme-" + p + "-v2", v));
      } catch (e) {}
      document.documentElement.classList.add("sf-switching");
      setTimeout(() => location.reload(), 220);
    });
  }
  el.dataset.mode = mode;
  el.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
})();"""
# Streamlit's HTML sanitizer drops a script whose text contains "<tag", so the markup inside the JS strings is escaped.
TOGGLE_JS = "<script>" + _TOGGLE_JS.replace("<", "\\x3c") + "</script>"


def setup():
    m = mode()
    st.markdown(CSS + theme_css(m), unsafe_allow_html=True)
    st.html(TOGGLE_JS % m, unsafe_allow_javascript=True)
    init_state()


def fetch_all(jobs: list, workers: int = 8) -> None:
    """Warm the data cache for many calls at once (see ``data.prefetch``), keeping the page interruptible.

    Streamlit can only stop a running page when the page touches Streamlit, so a page that sat inside a long
    download ignored clicks on other pages until the download finished. This touches an empty placeholder about
    once a second while it waits: a page switch stops the wait right away, and the downloads still running finish
    in the background and stay cached for the next visit."""
    beat = st.empty()
    data.prefetch(jobs, workers=workers, progress=lambda done, total: beat.empty())


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


def _load(name: str) -> list:
    """A saved list for whoever is using the app (see ``sharkfin.store``). A cloud read that fails returns []
    and blocks saving that list for the rest of the visit, so an outage can't overwrite good data."""
    try:
        return store.load(name)
    except store.StoreError as e:
        st.session_state.setdefault("_sf_unsaved", set()).add(name)
        st.toast(f"Heads up: {e}. Changes won't be saved until it's back.")
        return []


def _save(name: str, rows: list) -> bool:
    if name in st.session_state.get("_sf_unsaved", set()):
        return False
    try:
        return store.save(name, rows)
    except store.StoreError as e:
        st.toast(f"Could not save: {e}")
        return False


def init_state():
    ss = st.session_state
    who = store.identity()
    if ss.get("_sf_owner") != who.key:  # first run, or the visitor signed in / out: show their own data
        ss.pop("_sf_unsaved", None)
        ss.portfolio = _load("portfolio")
        ss.watchlist = _load("watchlist")
        ss.pop("swing_choice", None)
        ss._sf_owner = who.key
    ss.setdefault("portfolio", [])
    ss.setdefault("watchlist", [])
    ss.setdefault("symbol", "AAPL")


def load_list(name: str) -> list:
    """A list saved next to the portfolio and watchlist (e.g. the Dive Zone signal log)."""
    return _load(name)


def save_list(name: str, rows: list) -> bool:
    return _save(name, rows)


def save_state():
    for name in ("portfolio", "watchlist"):
        _save(name, st.session_state[name])


def account_box():
    """Sign-in / sign-out in the sidebar. Shows nothing when sign-in isn't set up (e.g. running locally)."""
    who = store.identity()
    if who.mode == "local":
        return
    if who.signed_in:
        st.caption(f"Signed in as {who.email or who.name or 'you'}"
                   + ("" if who.mode == "cloud" else " · saved on this server only"))
        if st.button("Sign out", key="sf_logout", width="stretch"):
            st.logout()
    else:
        if st.button("Sign in with Google", key="sf_login", type="primary", width="stretch",
                     help="Keeps your portfolio, watchlist and swing strategy private and saved. "
                          "Google lets you use a passkey (Face ID, Touch ID, Windows Hello)."):
            st.login()
        st.caption("Guest mode: your portfolio is kept for this visit only.")


def guest_notice():
    """One line on pages that edit personal data, telling guests their changes won't be kept."""
    if store.identity().mode == "guest":
        st.info("You're browsing as a guest, so this portfolio and watchlist last only for this visit. "
                "Sign in (sidebar) to keep them private and saved.", icon=":material/lock:")


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
                        help="Dive Zone is SharkFin's tested default. Pick a Strategy Lab template, or save your own "
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
    if mode() == "day":  # same chart, day-mode colors
        fig = pio.from_json(day_color(fig.to_json()), skip_invalid=True)
        fig.update_layout(template="plotly_white+sharkfin_day")
    # Streamlit's chart theme paints the page color behind charts; keep them see-through so the backdrop shows.
    if fig.layout.paper_bgcolor is None:
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    if fig.layout.plot_bgcolor is None:
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
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
