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


def _page(page):
    at = AppTest.from_string(RUNNER.replace("{path}", str(ROOT / "app_pages" / f"{page}.py")), default_timeout=240)
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def test_scanner_swing_and_core_tabs():
    at = _page("scanner")
    at.button[0].click().run()
    _ok(at)
    next(b for b in at.button if b.key == "swing_scan").click().run()
    _ok(at)
    assert any("Core score" in str(df.value.columns.tolist()) for df in at.dataframe)


def test_news_catalysts_view_and_10k_compare():
    at = _page("news")
    at.segmented_control[0].set_value("Catalysts").run()
    _ok(at)
    assert any(m.label == "Insider buyers (6m)" for m in at.metric)
    next(b for b in at.button if "10-K" in b.label).click().run()
    _ok(at)
    assert any(m.label == "Wording similarity" for m in at.metric)


def test_strategy_lab_confluence_ablation():
    at = _page("strategy_lab")
    _ok(at)
    assert any(m.label == "Expectancy" for m in at.metric)
    next(t for t in at.toggle if "filter adds" in t.label).set_value(True).run()
    _ok(at)


def test_research_trade_setup_tab():
    at = _page("research")
    _ok(at)
    labels = {m.label for m in at.metric}
    assert {"Entry", "Stop", "Nearest resistance"}.issubset(labels)
