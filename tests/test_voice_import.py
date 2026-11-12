"""Voice/typed commands and screenshot import."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sharkfin import screenshot_import as shot
from sharkfin.voice import parse
from tests import fakes

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("text, action, fields", [
    ("Hey SharkFin, forecast NVDA for a month", "forecast", {"query": "nvda", "horizon": "1 month"}),
    ("forecast nvidia over the next year", "forecast", {"query": "nvidia", "horizon": "1 year"}),
    ("add 10 shares of Apple at 180", "add", {"query": "apple", "shares": 10, "price": 180}),
    ("add ten shares of apple", "add", {"query": "apple", "shares": 10, "price": None}),
    ("buy 2.5 shares of TSLA at $250.50", "add", {"query": "tsla", "shares": 2.5, "price": 250.5}),
    ("add tesla to my watchlist", "watch", {"query": "tesla"}),
    ("open the playbook", "page", {"page": "app_pages/playbook.py"}),
    ("show me my portfolio", "page", {"page": "app_pages/portfolio.py"}),
    ("top performers", "page", {"page": "app_pages/scanner.py"}),
    ("read me today's market brief", "brief", {}),
    ("what's the fair value of microsoft", "research", {"query": "microsoft"}),
    ("should I sell before earnings?", "ask", {}),
    ("", "empty", {}),
])
def test_parse(text, action, fields):
    c = parse(text)
    assert c.action == action
    for k, v in fields.items():
        assert getattr(c, k) == v, (k, getattr(c, k))


def test_parse_positions_one_line_and_two_line_layouts():
    rows = shot.parse_positions("Positions\nAAPL Apple Inc. 10 shares $1,890.20 +1.2%\n"
                                "NVDA 25.5 shares Avg cost $112.40 $3,600.00\nMSFT  Qty: 4  Avg $310.00\n"
                                "Total $7,190.20\nCash $210.55")
    assert rows == [{"symbol": "AAPL", "shares": 10, "buy_price": None},
                    {"symbol": "NVDA", "shares": 25.5, "buy_price": 112.4},
                    {"symbol": "MSFT", "shares": 4, "buy_price": 310}]
    assert shot.parse_positions("AAPL $228.10\n12 shares +1.10%\nVOO $560.02\n4.5 shares") == [
        {"symbol": "AAPL", "shares": 12, "buy_price": None}, {"symbol": "VOO", "shares": 4.5, "buy_price": None}]


def test_claude_reply_is_cleaned():
    rows = shot.clean_rows(shot._json_array('Here you go: [{"symbol": "aapl", "shares": "10", "buy_price": "182.5"},'
                                            ' {"symbol": "CASH", "shares": 0}, {"symbol": "VOO", "shares": 3, "buy_price": null}]'))
    assert rows == [{"symbol": "AAPL", "shares": 10, "buy_price": 182.5}, {"symbol": "VOO", "shares": 3, "buy_price": None}]


@pytest.fixture
def offline(monkeypatch, tmp_path):
    from sharkfin import data
    fakes.install(monkeypatch)
    data._cache.clear()
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(ROOT))


def test_typed_command_adds_a_position(offline):
    at = AppTest.from_file(str(ROOT / "main.py"), default_timeout=240)
    at.run()
    at.chat_input(key="sf_cmd_text").set_value("add 3 shares of MSFT at 100").run()
    assert not at.exception, [e.value for e in at.exception]
    assert any(p["symbol"] == "MSFT" and p["shares"] == 3 and p["buy_price"] == 100 for p in at.session_state.portfolio)


def test_typed_brief(offline):
    at = AppTest.from_file(str(ROOT / "main.py"), default_timeout=240)
    at.run()
    at.chat_input(key="sf_cmd_text").set_value("read me today's market brief").run()
    assert not at.exception, [e.value for e in at.exception]
    assert "S and P 500" in at.session_state["_sf_brief_text"]
