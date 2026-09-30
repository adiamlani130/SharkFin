"""
SharkFin - Quant research platform
Run with:  streamlit run main.py
"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="SharkFin", page_icon="🦈", layout="wide", initial_sidebar_state="expanded")

from sharkfin import ui  # noqa: E402  (after set_page_config)

ui.setup()

logo = Path(__file__).with_name("sharkfin_logo.png")
if logo.exists():
    st.logo(str(logo), size="large")

pages = {
    "Markets": [
        st.Page("app_pages/home.py", title="Market Dashboard", icon="🏠", default=True),
        st.Page("app_pages/scanner.py", title="Top Performers", icon="🏆"),
        st.Page("app_pages/news.py", title="News Desk", icon="📰"),
    ],
    "Stock Analysis": [
        st.Page("app_pages/research.py", title="Research & Valuation", icon="🔍"),
        st.Page("app_pages/predictions.py", title="Forecasts", icon="🔮"),
        st.Page("app_pages/strategy_lab.py", title="Strategy Lab", icon="🧪"),
    ],
    "You": [
        st.Page("app_pages/portfolio.py", title="Portfolio", icon="💼"),
    ],
}
nav = st.navigation(pages)

with st.sidebar:
    st.caption(f"{len(st.session_state.portfolio)} positions · {len(st.session_state.watchlist)} on watchlist")
    from sharkfin import ai

    st.caption("AI analyst: " + ("enabled" if ai.available() else "set ANTHROPIC_API_KEY to enable"))

nav.run()
