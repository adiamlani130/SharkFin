"""Checks for the Sharpe-hunt / options research code (research only)."""
import numpy as np
import pandas as pd

from sharkfin.bs import Surface, bs_price, fit_smile, implied_vol, smile_iv
from sharkfin import sharpe_lab


def test_put_call_parity_and_iv_round_trip():
    S, K, T, v = 100.0, np.array([90.0, 100.0, 110.0]), 30 / 365, 0.25
    c, p = bs_price(S, K, T, v, 1), bs_price(S, K, T, v, -1)
    assert np.allclose(c - p, S - K, atol=1e-9)
    assert np.allclose(implied_vol(c, S, K, T, 1), v, atol=1e-6)
    assert np.allclose(implied_vol(p, S, K, T, -1), v, atol=1e-6)


def test_smile_fit_recovers_shape():
    x = np.linspace(-1.5, 1.0, 15)
    iv = 0.2 - 0.05 * x + 0.03 * x * x
    a, b, c = fit_smile(x, iv)
    assert abs(a - 0.2) < 1e-9 and abs(b + 0.05) < 1e-9 and abs(c - 0.03) < 1e-9
    s = Surface(100.0, {7 / 365: (0.2, -0.05, 0.03), 30 / 365: (0.25, -0.08, 0.02)})
    assert np.isclose(s.iv(100.0, 7 / 365), 0.2)


def test_next_open_engine_ignores_future():
    """A position decided at close t must not earn day t's return, and cutting later data changes nothing."""
    days = pd.bdate_range("2020-01-01", periods=60)
    rng = np.random.default_rng(0)
    c = pd.DataFrame({"SPY": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 60)))}, index=days)
    o = c.shift(1).fillna(100) * (1 + rng.normal(0, 0.002, (60, 1)))
    d = {"O": o, "C": c}
    sig = pd.DataFrame({"SPY": (np.arange(60) % 7 == 0).astype(float)}, index=days)
    full = sharpe_lab.run_next_open(d, sig)
    cut = sharpe_lab.run_next_open({"O": o.iloc[:40], "C": c.iloc[:40]}, sig.iloc[:40])
    assert np.allclose(full.iloc[:40], cut)
    assert full.iloc[0] == 0.0  # the first day's signal only trades from the next open
