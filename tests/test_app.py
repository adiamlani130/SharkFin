"""Smoke-test every page end to end with Streamlit's AppTest and offline data."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sharkfin import data
from tests import fakes

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["home", "research", "predictions", "scanner", "portfolio", "strategy_lab", "news", "playbook", "speculation"]

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
    data._cache.clear()
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


def _scanned(view=None):
    at = _page("scanner")
    at.button[0].click().run()
    if view:
        at.session_state["tp_view"] = view
        at.run()
    return at


def test_scanner_every_tab_renders():
    at = _scanned()
    for view in ("Rankings", "Swing setups", "Core longs", "Could run", "Shark Score list", "Does the ranking work?"):
        at.session_state["tp_view"] = view
        at.run()
        _ok(at)


def test_scanner_weights_rescore_without_downloading_again(monkeypatch):
    calls = []
    real = data.download_prices
    monkeypatch.setattr(data, "download_prices", lambda *a, **k: calls.append(a) or real(*a, **k))
    at = _scanned()
    first = at.dataframe[0].value.index.tolist()
    n = len(calls)
    at.slider(key="tw_Momentum").set_value(0.5).run()
    _ok(at)
    assert len(calls) == n
    assert at.dataframe[0].value.index.tolist() != first


def test_scanner_keeps_last_results_when_settings_change():
    at = _scanned()
    at.selectbox[0].set_value("Dow 30").run()
    _ok(at)
    assert any("Showing the last scan (S&P 500 with fundamentals)" in i.value for i in at.info)
    assert len(at.dataframe)


def test_scanner_stops_a_scan_whose_settings_changed_midway():
    at = _page("scanner")
    at.session_state["scan_req"] = ("Nasdaq-100", ("AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"), True)
    at.run()
    _ok(at)
    assert any("so that scan stopped" in i.value for i in at.info)
    assert not len(at.dataframe)


def test_scanner_leader_dip_and_core_tabs():
    at = _scanned("Core longs")
    _ok(at)
    assert any("Core score" in str(df.value.columns.tolist()) for df in at.dataframe)
    at.session_state["tp_view"] = "Swing setups"
    at.run()
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
    at.selectbox(key="lab_tpl").set_value("Golden cross").run()
    _ok(at)
    assert any("SMA(50) is above SMA(200)" in md.value for md in at.markdown)
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


def test_research_target_and_entry_tab():
    at = _page("research")
    _ok(at)
    labels = {m.label for m in at.metric}
    assert {"Fair value", "12-month target", "Entry range"}.issubset(labels)
    assert any("Ideal entry range" in md.value for md in at.markdown)
    assert any("vs its sector" in lab for lab in labels) and {"Shark Score", "Value", "Risk"}.issubset(labels)
    assert not any(t.label == "Trade setup" for t in at.tabs)


def test_scanner_shows_signals_and_logs_them(monkeypatch, tmp_path):
    from sharkfin import leader_dip
    real = leader_dip.latest

    def forced(close, ref=None, **kw):
        out = real(close, ref, **kw)
        out.loc[out.index[:2], "Signal"] = True  # make sure the table and the log have rows
        return out
    monkeypatch.setattr(leader_dip, "latest", forced)
    at = _scanned("Swing setups")
    _ok(at)
    assert any("Limit" in str(df.value.columns.tolist()) for df in at.dataframe)
    log = tmp_path / ".sharkfin" / "leader_dip_log.json"
    assert log.exists() or not leader_dip.market_on(fakes.history("SPY")["Close"]).iloc[-1]


def test_news_flags_big_beats():
    at = _page("news")
    at.segmented_control[0].set_value("Stock catalysts").run()
    _ok(at)
    assert any("Big-beat flag" in md.value or "Big earnings beat" in md.value for md in at.markdown)


def test_scanner_could_run_and_ranking_check():
    at = _scanned()
    assert any("Earnings" in str(df.value.columns.tolist()) for df in at.dataframe)
    at.session_state["tp_view"] = "Could run"
    at.run()
    _ok(at)
    assert any("Top-5% winner" in str(df.value.columns.tolist()) for df in at.dataframe)
    at.session_state["tp_view"] = "Does the ranking work?"
    at.run()
    _ok(at)
    assert any("Right direction" in str(df.value.columns.tolist()) for df in at.dataframe)
    assert any(m.label == "Months ahead" for m in at.metric)


def test_swing_choice_is_remembered(tmp_path):
    at = _scanned("Swing setups")
    at.session_state["tp_view"] = "Swing setups"  # AppTest doesn't send the open tab back with other widgets
    at.selectbox(key="swing_pick_tp").set_value("Tech Breakout Rider").run()
    _ok(at)
    assert (tmp_path / ".sharkfin" / "swing_choice.json").exists()
    at.selectbox(key="swing_pick_tp").set_value("Dive Zone").run()
    _ok(at)


def test_strategy_lab_saves_my_swing_strategy(tmp_path):
    at = _page("strategy_lab")
    next(b for b in at.button if b.label == "Use as my swing strategy").click().run()
    _ok(at)
    assert (tmp_path / ".sharkfin" / "my_swing_strategy.json").exists()
    tp = _scanned("Swing setups")
    tp.session_state["tp_view"] = "Swing setups"
    tp.run()
    _ok(tp)
    assert tp.selectbox(key="swing_pick_tp").value == "My Strategy Lab strategy"


def test_playbook_every_view_and_scan():
    at = _page("playbook")
    _ok(at)
    labels = set()
    for view in ("Dive Zone", "Tech Breakout Rider", "Using both", "What we tested"):
        at.session_state["pb_view"] = view
        at.run()
        _ok(at)
        labels |= {m.label for m in at.metric}
        for b in [b for b in at.button if b.key in ("pb_ld_scan", "pb_br_scan", "pb_ld_run", "pb_br_run")]:
            b.click().run()
            _ok(at)
        if view == "What we tested":
            assert any("VIX and GEX filters" in md.value for md in at.markdown)
    assert {"Return per year", "Sharpe ratio", "Worst drop"}.issubset(labels)
    assert not any("TQQQ" in str(getattr(b, "label", "")) for b in at.button)


def test_forecast_drivers_change_with_the_timeframe():
    at = _page("predictions")
    _ok(at)
    seen = {}
    for h in ("1 week", "1 year"):
        at.session_state["pred_h"] = h
        at.run()
        _ok(at)
        assert any(f"What moves it over {h}" in s.value for s in at.subheader)
        html = " ".join(m.value for m in at.markdown if "sf-driver" in m.value)
        seen[h] = html
    assert "Earnings report" in seen["1 week"] or "News tone" in seen["1 week"]
    assert "Valuation" in seen["1 year"] or "Business quality" in seen["1 year"] or "Growth" in seen["1 year"]
    assert seen["1 week"] != seen["1 year"]
