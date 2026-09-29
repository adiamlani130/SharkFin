"""Smoke-test every page end to end with Streamlit's AppTest and offline data."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests import fakes

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["home", "research", "predictions", "scanner", "portfolio", "strategy_lab", "news"]

RUNNER = """
import runpy, streamlit as st
from sharkfin import ui
ui.setup()
st.session_state.portfolio = [
    {"symbol": "AAPL", "shares": 10, "buy_price": 90},
    {"symbol": "MSFT", "shares": 5, "buy_price": 120},
    {"symbol": "NVDA", "shares": 8, "buy_price": 80},
]
st.session_state.watchlist = ["GOOGL", "AMZN"]
runpy.run_path(r"{path}", run_name="__main__")
"""


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    fakes.install(monkeypatch)
    monkeypatch.chdir(tmp_path)  # keep saved JSON out of the repo
    monkeypatch.syspath_prepend(str(ROOT))


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = AppTest.from_string(RUNNER.replace("{path}", str(ROOT / "app_pages" / f"{page}.py")), default_timeout=240)
    at.run()
    if page == "scanner":
        at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    errors = [e.value for e in at.error]
    assert not errors, errors


def test_main_navigation_renders():
    at = AppTest.from_file(str(ROOT / "main.py"), default_timeout=240)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
