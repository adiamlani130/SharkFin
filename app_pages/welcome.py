"""Landing page: SharkFin over a live night sea, and the way into the app."""

import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from sharkfin import data, ui

LOGO = Path(__file__).resolve().parents[1] / "sharkfin_logo.svg"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
html, body {background: #040b13;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {background: transparent !important;}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"],
[data-testid="stHeaderLogo"], [data-testid="stHeaderActionElements"] {display: none !important;}
.block-container {padding-top: 8vh !important; padding-bottom: 6rem; max-width: 1180px;}

.st-key-sf-ocean iframe {position: fixed !important; inset: 0; width: 100vw !important; height: 100vh !important;
  z-index: -1; border: 0; pointer-events: none;}
.st-key-sf-ocean {height: 0; overflow: visible;}

.sf-mark {display: block; width: 150px; height: auto; margin-bottom: 4.5vh; filter: drop-shadow(0 6px 24px rgba(0,0,0,.45));
  animation: sf-in 1.1s .15s cubic-bezier(.22,.8,.24,1) both;}
@keyframes sf-in {from {opacity: 0; transform: translateY(14px); filter: blur(6px);} to {opacity: 1; transform: none; filter: blur(0);}}
.sf-land h1 {animation: sf-in 1.1s .3s cubic-bezier(.22,.8,.24,1) both;}
.sf-land p {animation: sf-in 1.1s .45s cubic-bezier(.22,.8,.24,1) both;}
.st-key-sf-cta {animation: sf-in 1.1s .6s cubic-bezier(.22,.8,.24,1) both;}
.sf-status {animation: sf-in 1.1s .75s cubic-bezier(.22,.8,.24,1) both;}
.st-key-sf-ocean::after {content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background: radial-gradient(120% 90% at 0% 0%, rgba(3,9,16,.55), rgba(3,9,16,0) 60%);}
.st-key-sf-ocean iframe {animation: sf-fadein 2.2s ease both;}
@keyframes sf-fadein {from {opacity: 0;} to {opacity: 1;}}
@media (prefers-reduced-motion: reduce) {.sf-mark, .sf-land h1, .sf-land p, .st-key-sf-cta, .sf-status,
  .st-key-sf-ocean iframe {animation: none !important;}}
.sf-land h1 {font-family: 'Newsreader', Georgia, serif !important; font-weight: 400 !important;
  font-size: clamp(2.7rem, 6.2vw, 5.4rem) !important; line-height: 1.02 !important; letter-spacing: -0.022em;
  color: #eef4f7 !important; margin: 0 !important; padding: 0 !important; max-width: 11.5em; text-wrap: balance;}
.sf-land p {font-size: 1.07rem; line-height: 1.62; color: #a9bdcb; max-width: 31em; margin: 1.5rem 0 0 0;}

.st-key-sf-cta {gap: .7rem !important; margin-top: 2.1rem;}
.st-key-sf-cta [data-testid="stPageLink"] a {padding: .7rem 1.15rem; border-radius: 10px; text-decoration: none;
  border: 1px solid rgba(214,236,246,.24); background: rgba(5,16,27,.55); backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: background .25s ease, border-color .25s ease, transform .25s cubic-bezier(.22,.8,.24,1), box-shadow .25s ease;}
.st-key-sf-cta [data-testid="stPageLink"] a:hover {transform: translateY(-2px); box-shadow: 0 10px 26px -12px rgba(0,0,0,.7);}
.st-key-sf-cta [data-testid="stPageLink"] a:hover {border-color: rgba(214,236,246,.5); background: rgba(10,30,48,.7);}
.st-key-sf-cta [data-testid="stPageLink"] a:active {transform: translateY(1px);}
.st-key-sf-cta [data-testid="stPageLink"] p {color: #e6eef2 !important; font-weight: 500; font-size: .96rem;}
.st-key-sf-go [data-testid="stPageLink"] a {background: #3fa9e0; border-color: #3fa9e0;}
.st-key-sf-go [data-testid="stPageLink"] a:hover {background: #62bbea; border-color: #62bbea;}
.st-key-sf-go [data-testid="stPageLink"] p {color: #03121d !important; font-weight: 600;}
.st-key-sf-cta a:focus-visible {outline: 2px solid #9ad3f2; outline-offset: 3px;}

.sf-status {margin-top: 1.7rem; font-size: .87rem; color: #8ea5b7; display: flex; align-items: center; gap: .55rem;}
.sf-status i {width: 7px; height: 7px; border-radius: 50%; background: #5f7486; display: inline-block;}
.sf-status i.on {background: #2dd4a3; box-shadow: 0 0 0 4px rgba(45,212,163,.15);}
.sf-foot {position: fixed; left: 0; right: 0; bottom: 14px; text-align: center; font-size: .74rem;
  color: rgba(190,210,222,.5); pointer-events: none;}

@media (max-width: 700px) {
  .block-container {padding-top: 6vh !important;}
  .sf-mark {margin-bottom: 4vh; width: 112px;}
  .sf-land p {font-size: 1rem;}
  .sf-foot {display: none;}
}
</style>
"""

STATUS = {"Open": "The NYSE is open", "Pre-market": "The NYSE opens at 9:30 AM",
          "After-hours": "The NYSE closed at 4:00 PM", "Closed": "The NYSE is closed"}

st.markdown(CSS, unsafe_allow_html=True)

with st.container(key="sf-ocean"):
    components.html(ui.asset("ocean.html"), height=10)

if LOGO.exists():
    svg = base64.b64encode(LOGO.read_bytes()).decode()
    st.markdown(f"<img class='sf-mark' alt='SharkFin' src='data:image/svg+xml;base64,{svg}'>", unsafe_allow_html=True)

st.markdown(
    "<div class='sf-land'><h1>Swim with the market, not against it.</h1>"
    "<p>SharkFin checks the S&amp;P 500 every trading day: how the market is trending, which stocks are leading, "
    "and when its three tested swing strategies say buy or sell.</p></div>",
    unsafe_allow_html=True)

with st.container(key="sf-cta", horizontal=True):
    with st.container(key="sf-go", width="content"):
        st.page_link("app_pages/home.py", label="Open the dashboard")
    with st.container(key="sf-pb", width="content"):
        st.page_link("app_pages/playbook.py", label="See the strategy playbook")
    with st.container(key="sf-sp", width="content"):
        st.page_link("app_pages/speculation.py", label="Speculation radar")

status, ny = data.market_status()
when = f"{ny:%A, %B} {ny.day}, {ny:%I:%M %p}".replace(", 0", ", ")
st.markdown(
    f"<div class='sf-status'><i class='{'on' if status == 'Open' else ''}'></i>{STATUS[status]}. {when} in New York.</div>"
    "<div class='sf-foot'>SharkFin is a research tool, not investment advice.</div>",
    unsafe_allow_html=True)
