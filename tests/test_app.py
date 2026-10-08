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


def test_scanner_leader_dip_and_core_tabs():
    at = _page("scanner")
    at.button[0].click().run()
    _ok(at)
    assert any("Core score" in str(df.value.columns.tolist()) for df in at.dataframe)
    assert any("Signal log" in e.label for e in at.expander)


def test_news_catalysts_view_and_10k_compare():
    at = _page("news")
    at.segmented_control[0].set_value("Stock catalysts").run()
    _ok(at)
    assert any(m.label == "Insider buyers (6m)" for m in at.metric)
    next(b for b in at.button if "annual reports" in b.label).click().run()
    _ok(at)
    assert any(m.label == "Wording kept" for m in at.metric)


def test_strategy_lab_builder_and_leader_dip():
    at = _page("strategy_lab")
    _ok(at)
    labels = {m.label for m in at.metric}
    assert {"Return per year", "Worst drop", "Winning trades"}.issubset(labels)
    at.selectbox(key="lab_tpl").set_value("RSI dip in an uptrend").run()
    _ok(at)
    assert any("RSI(14) is below 35" in md.value for md in at.markdown)
    next(b for b in at.button if b.label == "Add a buy rule").click().run()
    _ok(at)
    removes = [b for b in at.button if b.key and b.key.endswith("_x")]
    removes[0].click().run()
    _ok(at)
    next(b for b in at.button if b.key == "ld_run").click().run()
    _ok(at)
    assert {"Trades per year", "Sharpe ratio", "Avg trade"}.issubset({m.label for m in at.metric})
    at.selectbox(key="ld_cash").set_value("SPY always").run()
    _ok(at)


def test_research_trade_setup_tab():
    at = _page("research")
    _ok(at)
    labels = {m.label for m in at.metric}
    assert "Fair value" in labels
    assert {"2-day RSI", "vs 200-day average", "6-month strength", "Market switch", "Swing (Leader Dip)"}.issubset(labels)
    assert any("vs its sector" in lab for lab in labels) and "VST" in labels


def test_scanner_shows_signals_and_logs_them(monkeypatch, tmp_path):
    from sharkfin import leader_dip
    real = leader_dip.latest

    def forced(close, ref=None):
        out = real(close, ref)
        out.loc[out.index[:2], "Signal"] = True  # make sure the table and the log have rows
        return out
    monkeypatch.setattr(leader_dip, "latest", forced)
    at = _page("scanner")
    at.button[0].click().run()
    _ok(at)
    assert any("Limit" in str(df.value.columns.tolist()) for df in at.dataframe)
    log = tmp_path / ".sharkfin" / "leader_dip_log.json"
    assert log.exists() or not leader_dip.market_on(fakes.history("SPY")["Close"]).iloc[-1]


def test_news_flags_big_beats():
    at = _page("news")
    at.segmented_control[0].set_value("Stock catalysts").run()
    _ok(at)
    assert any("Big-beat flag" in md.value or "Big earnings beat" in md.value for md in at.markdown)
