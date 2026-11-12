"""Daily alerts: what each user's notification says, and that nothing is sent when there's nothing to say."""

import pandas as pd
import pytest

from sharkfin import alerts, store, threat

SIG = {"dive": ["AAPL"], "breakout": ["NVDA", "AMD"],
       "dive_table": pd.DataFrame({"Signal": [True, False], "Sell signal": [False, True]}, index=["AAPL", "TSLA"]),
       "breakout_table": pd.DataFrame({"Signal": [True, True, False], "Trend intact": [True, True, False]},
                                      index=["NVDA", "AMD", "MSFT"])}


def _th(level, score):
    return threat.Threat(score, level, [{"name": "One stock too big", "points": score, "max": 15, "detail": "TSLA is 60%"}])


def test_topics():
    t = alerts.new_topic()
    assert alerts.valid_topic(t) and t != alerts.new_topic()
    assert not alerts.valid_topic("short") and not alerts.valid_topic("has spaces in it here!!")


def test_compose_signals_exits_and_threat(monkeypatch):
    monkeypatch.setattr(alerts, "portfolio_threat", lambda rows: _th("HIGH", 60))
    title, body, prio, level = alerts.compose({"topic": "x"}, [{"symbol": "tsla", "shares": 1}, {"symbol": "MSFT", "shares": 1}],
                                              SIG, "MEDIUM")
    assert "3 signals" in title and prio == "high" and level == "HIGH"
    assert "Dive Zone buys: AAPL" in body and "Breakout Rider buys: NVDA, AMD" in body
    assert "MSFT (Breakout trend broke)" in body and "TSLA (Dive Zone exit)" in body
    assert "MEDIUM -> HIGH" in body


def test_threat_only_when_it_rises_or_is_high():
    assert alerts.threat_line(_th("MEDIUM", 30), "MEDIUM") == (None, False)
    assert alerts.threat_line(_th("LOW", 5), None) == (None, False)
    line, urgent = alerts.threat_line(_th("MEDIUM", 30), "LOW")
    assert "LOW -> MEDIUM" in line and not urgent


def test_quiet_day_sends_nothing(monkeypatch):
    monkeypatch.setattr(alerts, "portfolio_threat", lambda rows: _th("LOW", 0))
    _, body, _, level = alerts.compose({"signals": False}, [{"symbol": "AAPL", "shares": 1}],
                                       {"dive": [], "breakout": []}, "LOW")
    assert body == "" and level == "LOW"


def test_run_sends_per_user_and_saves_state(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "sharkfin-owner-topic-123")
    monkeypatch.setattr(alerts, "todays_signals", lambda: SIG)
    monkeypatch.setattr(alerts, "portfolio_threat", lambda rows: _th("HIGH", 70))
    monkeypatch.setattr(store, "supabase_config", lambda: ("https://x.supabase.co", "k"))
    lists = {"alerts": {"u1": [{"topic": "sharkfin-user-one-topic"}], "u2": [{"topic": "bad"}]},
             "alert_state": {"u1": [{"level": "LOW"}]}}
    monkeypatch.setattr(store, "cloud_all", lambda name: lists[name])
    monkeypatch.setattr(store, "load", lambda name, who: [{"symbol": "TSLA", "shares": 2}])
    saved, sent = [], []
    monkeypatch.setattr(store, "save", lambda name, rows, who: saved.append((name, rows, who.user_id)))
    monkeypatch.setattr(alerts, "send", lambda topic, title, body, prio="default", tags="": sent.append((topic, body, prio)) or True)
    alerts.run()
    topics = [t for t, _, _ in sent]
    assert topics == ["sharkfin-owner-topic-123", "sharkfin-user-one-topic"]
    assert sent[1][2] == "high" and "LOW -> HIGH" in sent[1][1]
    assert saved == [("alert_state", [{"level": "HIGH"}], "u1")]


def test_send_refuses_bad_topic(monkeypatch):
    monkeypatch.setattr(alerts.requests, "post", lambda *a, **k: pytest.fail("should not post"))
    assert alerts.send("bad", "t", "b") is False
