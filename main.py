"""
SharkFin - Quant research platform
Run with:  streamlit run main.py
"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="SharkFin", page_icon=str(Path(__file__).with_name("sharkfin_logo.png")), layout="wide", initial_sidebar_state="auto")

from sharkfin import ui  # noqa: E402  (after set_page_config)

ui.setup()

logo = Path(__file__).with_name("sharkfin_logo.png")
if logo.exists():
    st.logo(str(logo), size="large")

pages = {
    "Markets": [
        st.Page("app_pages/home.py", title="Market Dashboard", default=True),
        st.Page("app_pages/scanner.py", title="Top Performers"),
        st.Page("app_pages/news.py", title="News Desk"),
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
