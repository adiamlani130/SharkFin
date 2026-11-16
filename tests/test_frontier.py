"""Tests for the Frontier Lab engine (sharkfin/frontier.py) and its frozen research data."""
import numpy as np
import pandas as pd

from sharkfin import frontier as fl
from sharkfin import jump_lab as jl
from sharkfin import neat_core as nc


def test_vectorised_merton_matches_the_research_pricer():
    K = np.array([80.0, 95, 100, 112])
    T = np.array([0.1, 0.5, 1.0, 0.25])
    fast = fl.merton_iv(100, K, T, 0.04, 0.11, 0.46, -0.185, 0.14)
    slow = [jl.merton_iv(100, k, t, 0.04, 0.11, 0.46, -0.185, 0.14) for k, t in zip(K, T)]
    assert np.allclose(fast, slow, atol=1e-5)


def test_no_jumps_gives_a_flat_black_scholes_surface():
    _, _, iv = fl.surface_grid(100, 0.03, dict(sigma=0.2, lam=0.0, mu_j=-0.1, delta=0.1))
    assert np.nanmax(np.abs(iv - 0.2)) < 1e-3


def test_closed_form_skew_matches_sympy_cumulants():
    _, _, sk, _ = jl.merton_moments(0.12, 0.5, -0.18, 0.14, 30 / 365)
    assert abs(fl.merton_skew(0.12, 0.5, -0.18, 0.14, 30 / 365) - sk) < 1e-9


def test_crash_odds_rise_with_jump_risk():
    calm = dict(sigma=0.15, lam=0.0, mu_j=-0.2, delta=0.1)
    jumpy = dict(sigma=0.15, lam=1.0, mu_j=-0.2, delta=0.1)
    assert fl.crash_odds(jumpy, 1, -0.2) > fl.crash_odds(calm, 1, -0.2) + 0.05


def test_frozen_champions_round_trip_through_json():
    ev = fl.load("evolution.json")
    assert ev["tracked"]["members"] == ["orig_s2"] and len(ev["names"]) == ev["champions"]["orig_s2"]["n_inputs"]
    X = np.random.default_rng(0).normal(size=(50, len(ev["names"]))).astype(np.float32)
    for tag in ev["champions"]:
        g = fl.genome_from_json(ev["champions"][tag])
        y = nc.activate(g, X)
        assert y.shape == (50,) and np.isfinite(y).all()
        pos, conns = fl.network_layout(ev["champions"][tag])
        assert all(c["src"] in pos and c["dst"] in pos for c in conns)


def test_forward_record_starts_at_the_freeze_and_uses_next_open():
    idx = pd.bdate_range("2026-10-01", "2026-12-31")
    o = pd.DataFrame({"SPY": np.linspace(100, 120, len(idx)), "QQQ": 100.0}, index=idx)
    px = {"Open": o, "Close": o * 1.001}
    pos = pd.DataFrame(1.0, index=idx, columns=["SPY", "QQQ"])
    gate = pd.Series(1.0, index=idx)
    rec = fl.forward_record(px, pos, gate)
    assert rec["network"].index.min() >= fl.FROZEN
    d = rec["network"].index[3]
    i = idx.get_loc(d)
    want = (o.SPY.iloc[i + 2] / o.SPY.iloc[i + 1] - 1 + 0) / 2
    assert abs(rec["network"].loc[d] - want) < 1e-12
