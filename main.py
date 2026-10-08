"""
SharkFin - Quant research platform
Run with:  streamlit run main.py
"""

import importlib
import os
import sys
import time
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="SharkFin", page_icon=str(Path(__file__).with_name("sharkfin_logo.png")), layout="wide", initial_sidebar_state="auto")


def reload_changed_sharkfin():
    """After a deploy, Streamlit Cloud pulls the new code into the running server and reruns the page
    scripts, but the already-imported ``sharkfin`` package stays in memory as the old version (so a page
    can call a function its old module doesn't have). Reload the package when any of its files changed."""
    import sharkfin

    mods = [m for n, m in list(sys.modules.items())
            if (n == "sharkfin" or n.startswith("sharkfin.")) and getattr(m, "__file__", None)]
    loaded = getattr(sharkfin, "LOADED_AT", 0.0)
    if all(os.path.getmtime(m.__file__) <= loaded for m in mods if os.path.exists(m.__file__)):
        return
    for m in reversed(mods):  # dependencies were imported last, so they reload first
        if os.path.exists(m.__file__):
            importlib.reload(m)
    sharkfin.LOADED_AT = time.time()


reload_changed_sharkfin()

from sharkfin import ui  # noqa: E402  (after set_page_config)

ui.setup()

logo = Path(__file__).with_name("sharkfin_logo.png")
if logo.exists():
    st.logo(str(logo), size="large")

pages = {
    "Markets": [
        st.Page("app_pages/home.py", title="Market Dashboard", default=True),
        st.Page("app_pages/scanner.py", title="Top Performers"),
        st.Page("app_pages/news.py", title="News"),
    ],
    "Stock Analysis": [
        st.Page("app_pages/research.py", title="Research & Valuation"),
        st.Page("app_pages/predictions.py", title="Forecasts"),
        st.Page("app_pages/strategy_lab.py", title="Strategy Lab"),
    ],
    "You": [
        st.Page("app_pages/portfolio.py", title="Portfolio"),
    ],
}
nav = st.navigation(pages)

with st.sidebar:
    st.caption(f"{len(st.session_state.portfolio)} positions · {len(st.session_state.watchlist)} on watchlist")

nav.run()
