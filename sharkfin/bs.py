"""Black-Scholes pricing, implied volatility and a simple implied-vol surface (research only).

The surface is fit per day and per expiry to real option prices:

    iv(x) = a + b*x + c*x**2,    x = ln(K / F) / sqrt(T)

(a "sticky-moneyness" quadratic smile in standardised log-moneyness), and the at-the-money level ``a`` is
interpolated across expiries in total variance (a * a * T), linearly in T. That is enough to read the level, skew
and curvature of the market's prices and to price strikes that did not trade."""
from __future__ import annotations

import math

import numpy as np
from scipy.special import ndtr

YEAR_MIN = 252 * 390  # trading minutes in a year: same-day options are timed in trading minutes


def bs_price(S, K, T, sigma, cp, r=0.0, q=0.0):
    """European price; cp is +1 for calls, -1 for puts. Vectorised. At T <= 0 returns intrinsic value."""
    S, K, T, sigma, cp = map(np.asarray, (S, K, T, sigma, cp))
    T = np.maximum(T, 0.0)
    intrinsic = np.maximum(cp * (S - K), 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        st = sigma * np.sqrt(T)
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / st
        d2 = d1 - st
        px = cp * (S * np.exp(-q * T) * ndtr(cp * d1) - K * np.exp(-r * T) * ndtr(cp * d2))
    return np.where((T <= 0) | (st <= 0), intrinsic, px)


def bs_delta(S, K, T, sigma, cp, r=0.0, q=0.0):
    S, K, T, sigma, cp = map(np.asarray, (S, K, T, sigma, cp))
    with np.errstate(divide="ignore", invalid="ignore"):
        st = sigma * np.sqrt(np.maximum(T, 1e-12))
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / st
    return np.where(cp > 0, ndtr(d1), ndtr(d1) - 1.0) * np.exp(-q * T)


def implied_vol(price, S, K, T, cp, r=0.0, lo=1e-3, hi=5.0, iters=60):
    """Vectorised bisection. NaN where the price is below intrinsic or above the no-arbitrage bound."""
    price, S, K, T, cp = map(lambda a: np.asarray(a, dtype=float), (price, S, K, T, cp))
    a = np.full(np.broadcast(price, S, K, T, cp).shape, lo)
    b = np.full_like(a, hi)
    intrinsic = np.maximum(cp * (S - K * math.exp(0)), 0.0)
    bad = (price <= intrinsic + 1e-6) | (T <= 0) | ~np.isfinite(price)
    for _ in range(iters):
        m = 0.5 * (a + b)
        f = bs_price(S, K, T, m, cp, r) - price
        a = np.where(f < 0, m, a)
        b = np.where(f >= 0, m, b)
    out = 0.5 * (a + b)
    out = np.where(bad | (out >= hi * 0.999) | (out <= lo * 1.001), np.nan, out)
    return out


def fit_smile(x, iv, w=None):
    """Weighted least-squares quadratic smile iv = a + b x + c x^2. Returns (a, b, c) or None."""
    x, iv = np.asarray(x, float), np.asarray(iv, float)
    ok = np.isfinite(x) & np.isfinite(iv)
    if ok.sum() < 4:
        return None
    w = np.ones_like(x) if w is None else np.asarray(w, float)
    X = np.vstack([np.ones(ok.sum()), x[ok], x[ok] ** 2]).T
    W = np.sqrt(w[ok])
    coef, *_ = np.linalg.lstsq(X * W[:, None], iv[ok] * W, rcond=None)
    return tuple(float(c) for c in coef)


def smile_iv(coef, x):
    a, b, c = coef
    return np.maximum(a + b * np.asarray(x) + c * np.asarray(x) ** 2, 0.01)


class Surface:
    """Smiles at several expiries; iv(K, T) interpolates the ATM level in total variance and the skew
    and curvature linearly in T (flat outside the fitted range)."""

    def __init__(self, F: float, smiles: dict[float, tuple]):
        self.F = F
        self.T = np.array(sorted(smiles))
        self.coef = np.array([smiles[t] for t in self.T])

    def iv(self, K, T):
        K, T = np.asarray(K, float), np.asarray(T, float)
        Tc = np.clip(T, self.T[0], self.T[-1])
        tv = np.interp(Tc, self.T, self.coef[:, 0] ** 2 * self.T)
        a = np.sqrt(np.maximum(tv, 1e-10) / Tc)
        b = np.interp(Tc, self.T, self.coef[:, 1])
        c = np.interp(Tc, self.T, self.coef[:, 2])
        x = np.log(K / self.F) / np.sqrt(np.maximum(T, 1e-8))
        return np.maximum(a + b * x + c * x * x, 0.01)

    def price(self, K, T, cp):
        return bs_price(self.F, K, T, self.iv(K, T), cp)
