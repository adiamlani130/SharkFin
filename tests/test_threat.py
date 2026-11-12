"""Threat level: each warning sign moves the score the way it says, and calm portfolios read LOW."""

import numpy as np
import pandas as pd

from sharkfin import threat

IDX = pd.bdate_range("2025-01-01", periods=300)


def _prices(**cols):
    return pd.DataFrame({k: np.asarray(v, float) for k, v in cols.items()}, index=IDX)


def _up(start=100, step=0.001):
    return start * (1 + step) ** np.arange(len(IDX))


def test_calm_portfolio_is_low():
    px = _prices(AAPL=_up(), MSFT=_up(50), NVDA=_up(30), JPM=_up(80), SPY=_up(400))
    w = pd.Series(0.25, index=["AAPL", "MSFT", "NVDA", "JPM"])
    sec = {"AAPL": "Tech", "MSFT": "Software", "NVDA": "Semis", "JPM": "Financials"}
    t = threat.assess(px, w, sec, {}, vix=14)
    assert t.level == "LOW" and t.score == 0 and not t.triggered


def test_crash_concentration_and_market_stress_is_high():
    crash = np.r_[_up()[:250], _up()[249] * np.linspace(1, 0.6, 50)]
    spy = np.r_[_up(400)[:250], _up(400)[249] * np.linspace(1, 0.85, 50)]
    px = _prices(TSLA=crash, SPY=spy)
    t = threat.assess(px, pd.Series({"TSLA": 1.0}), {"TSLA": "Autos"},
                      {"TSLA": IDX[-1] + pd.Timedelta(days=1)}, vix=32, today=IDX[-1])
    names = {s["name"] for s in t.triggered}
    assert t.level == "HIGH" and t.score >= 80
    assert {"Drop from peak", "One stock too big", "One sector too big", "Earnings within 3 days",
            "SPY below 200-day", "VIX above 25", "Holdings below their 200-day"} <= names


def test_var_breach_flags_a_bad_day():
    rng = np.random.default_rng(1)
    r = rng.normal(0.0005, 0.01, len(IDX))
    r[-1] = -0.06
    px = _prices(AAPL=100 * np.cumprod(1 + r), SPY=_up(400))
    t = threat.assess(px, pd.Series({"AAPL": 1.0}), vix=15)
    var = next(s for s in t.signs if s["name"] == "Loss beyond normal range")
    assert var["points"] == 15


def test_levels_and_score_bounds():
    assert threat.level_of(0) == "LOW" and threat.level_of(24.9) == "LOW"
    assert threat.level_of(25) == "MEDIUM" and threat.level_of(50) == "HIGH"
    assert sum(s["max"] for s in threat.assess(_prices(A=_up(), SPY=_up()), pd.Series({"A": 1.0})).signs) == 100


def test_next_earnings_picks_future_date():
    now = pd.Timestamp.now()
    rows = pd.DataFrame({"earningsTimestamp": [(now - pd.Timedelta(days=60)).timestamp(), (now + pd.Timedelta(days=2)).timestamp()],
                         "earningsTimestampStart": [np.nan, (now + pd.Timedelta(days=2)).timestamp()]},
                        index=["OLD", "SOON"])
    out = threat.next_earnings(rows)
    assert "OLD" not in out and (out["SOON"] - now).days in (1, 2)
