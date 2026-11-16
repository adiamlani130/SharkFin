"""Tests for the research-only NEAT engine and Merton jump-diffusion tools."""
import numpy as np

from sharkfin import jump_lab as jl
from sharkfin import neat_core as nc


def test_neat_learns_a_product_rule_and_stays_acyclic():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(3000, 6)).astype(np.float32)
    y = np.sign(X[:, 1] * X[:, 4])
    neat = nc.Neat(6, nc.Config(pop=120, gens=30), seed=0)
    best = neat.run(lambda g: float(np.mean(np.sign(nc.activate(g, X)) == y)))
    assert best.fitness > 0.8              # a linear rule cannot beat ~0.5 on this
    for g in neat.pop:
        nc.topo_order(g)                   # raises on a cycle
    assert neat.evaluated > 120 * 20       # elites keep their score, everyone else is new


def test_merton_reduces_to_black_scholes_without_jumps():
    m = jl.merton_price(100, 105, 0.5, 0.03, 0.2, 0.0, -0.1, 0.1)
    b = jl.bs_price(100, 105, 0.5, 0.03, 0.2)
    assert abs(float(m) - float(b)) < 1e-8


def test_merton_puts_a_skew_on_the_smile():
    lo = jl.merton_iv(100, 85, 0.25, 0.03, 0.15, 1.0, -0.1, 0.1)
    hi = jl.merton_iv(100, 110, 0.25, 0.03, 0.15, 1.0, -0.1, 0.1)
    assert lo > hi + 0.02


def test_symbolic_cumulants_match_simulation_and_fit_recovers_parameters():
    rng = np.random.default_rng(0)
    n, dt, sig, lam, mj, d = 4000, 1 / 252, 0.15, 6.0, -0.03, 0.04
    N = rng.poisson(lam * dt, n)
    x = (0.05 - 0.5 * sig ** 2) * dt + sig * np.sqrt(dt) * rng.normal(size=n) + N * mj + np.sqrt(N) * d * rng.normal(size=n)
    _, var, _, _ = jl.merton_moments(sig, lam, mj, d, dt)
    assert abs(x.var() / var - 1) < 0.15
    f = jl.fit_merton(x)
    assert abs(f["sigma"] - sig) < 0.03 and f["ll"] > f["ll_bs"]
