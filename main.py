"""
SharkFin - Financial Intelligence Platform
Main application entry point
"""

import streamlit as st
import json
from datetime import datetime
import pytz

# Configure page
st.set_page_config(
    page_title="SharkFin - Financial Intelligence",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
)
with st.sidebar:
    st.markdown("## 📂 Menu")

# Import pages
from home_page import HomePage
from portfolio_page import PortfolioPage
from research_page import ResearchPage
from prediction_page import PredictionPage
from top_performers_page import TopPerformersPage

# Custom CSS
st.markdown("""
<style>

/* =========================
   GLOBAL APP BACKGROUND
   ========================= */
.stApp {
    background-color: #0a0a0a;
}

/* Remove excess top padding */
.main .block-container {
    padding-top: 1rem !important;
}

/* =========================
   SIDEBAR (MENU)
   ========================= */
/* Sidebar outer + inner container */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {
    background-color: #0f0f0f;
    padding-top: 1rem;
}

/* Sidebar toggle (hamburger menu) */
button[kind="header"] {
    background-color: #1a1a1a !important;
    border: 2px solid #00aa55 !important;
    border-radius: 8px !important;
}

/* Hamburger icon bars */
button[kind="header"] svg {
    color: #00aa55 !important;
    fill: #00aa55 !important;
}

/* Hover state */
button[kind="header"]:hover {
    background-color: #00aa55 !important;
}

/* =========================
   TEXT (SAFE SCOPED)
   ========================= */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6,
.stApp p,
.stApp label,
.stApp li {
    color: #ffffff !important;
}

/* =========================
   METRICS (KPI CARDS)
   ========================= */
.stMetric {
    background-color: #1a1a1a;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #2a2a2a;
}

.stMetric label {
    color: #888888 !important;
    font-size: 13px !important;
}

.stMetric [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 26px !important;
    font-weight: bold !important;
}

/* =========================
   BUTTONS
   ========================= */
.stButton > button {
    background-color: #00aa55 !important;
    color: #000000 !important;
    font-weight: bold !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 28px !important;
    font-size: 15px !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background-color: #008844 !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 170, 85, 0.3);
}

/* =========================
   INPUTS
   ========================= */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
    background-color: #1a1a1a !important;
    color: white !important;
    border: 2px solid #00aa55 !important;
    border-radius: 6px !important;
    padding: 10px !important;
}

/* =========================
   TABS
   ========================= */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background-color: #2a2a2a;
    color: white !important;
    border-radius: 8px;
    padding: 12px 24px;
    border: 2px solid transparent;
}

.stTabs [aria-selected="true"] {
    background-color: #00aa55 !important;
    color: black !important;
    font-weight: bold !important;
    border: 3px solid white !important;
}

/* =========================
   EXPANDERS, ALERTS, PROGRESS
   ========================= */
.streamlit-expanderHeader {
    background-color: #1a1a1a !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-weight: bold !important;
}

.stAlert {
    background-color: #1a1a1a !important;
    color: white !important;
    border-radius: 8px !important;
}

.stProgress > div > div {
    background-color: #00aa55 !important;
}

/* =========================
   DIVIDERS
   ========================= */
hr {
    border-color: #2a2a2a !important;
    margin: 20px 0 !important;
}


</style>
""", unsafe_allow_html=True)

# Session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'news_cache' not in st.session_state:
    st.session_state.news_cache = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Data functions
def load_data():
    try:
        with open('portfolio.json', 'r') as f:
            data = json.load(f)
            st.session_state.portfolio = data if isinstance(data, list) else []
    except:
        st.session_state.portfolio = []
    
    try:
        with open('watchlist.json', 'r') as f:
            data = json.load(f)
            st.session_state.watchlist = data if isinstance(data, list) else []
    except:
        st.session_state.watchlist = []

def save_data():
    try:
        with open('portfolio.json', 'w') as f:
            json.dump(st.session_state.portfolio, f, indent=2)
        with open('watchlist.json', 'w') as f:
            json.dump(st.session_state.watchlist, f, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {e}")

load_data()
st.session_state.save_data = save_data
# SIDEBAR with visible current page
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    try:
        from pathlib import Path
        logo_path = Path("sharkfin_logo.png")
        if logo_path.exists():
            import base64
            with open(logo_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_data}" width="160" style="pointer-events: none;"></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown("<h2 style='text-align: center;'>🦈 SharkFin</h2>", unsafe_allow_html=True)
    except:
        st.markdown("<h2 style='text-align: center;'>🦈 SharkFin</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Show current page
    st.markdown(f"**Current Page:** {st.session_state.current_page}")
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation buttons with active state
    pages = [
        ("🏠  Home", "Home"),
        ("💼  Portfolio", "Portfolio"),
        ("🔍  Research", "Research"),
        ("🔮  Predictions", "Predictions"),
        ("🏆  Top Performers", "Top Performers")
    ]
    
    for label, page_name in pages:
        # Highlight active page
        button_type = "primary" if st.session_state.current_page == page_name else "secondary"
        
        if st.button(label, key=f"nav_{page_name}", width='stretch', type=button_type):
            st.session_state.current_page = page_name
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)

# Route to page
if st.session_state.current_page == "Home":
    home = HomePage()
    home.create_content()
elif st.session_state.current_page == "Portfolio":
    portfolio = PortfolioPage()
    portfolio.create_content()
elif st.session_state.current_page == "Research":
    research = ResearchPage()
    research.create_content()
elif st.session_state.current_page == "Predictions":
    prediction = PredictionPage()
    prediction.create_content()
elif st.session_state.current_page == "Top Performers":
    top_performers = TopPerformersPage()
    top_performers.create_content()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888888; font-size: 11px;'>"
    "© 2025 SharkFin • ML-Powered Financial Intelligence"
    "</p>",
    unsafe_allow_html=True
)
