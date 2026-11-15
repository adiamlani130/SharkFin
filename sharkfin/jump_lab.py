"""Merton jump-diffusion: symbolic moments, maximum-likelihood fits, option prices, implied-vol surfaces,
and leak-free "jump risk" features for strategy research. Research only, nothing in the app imports it.

Merton (1976) adds a Poisson stream of jumps to Black-Scholes: log price moves by a normal diffusion
(volatility ``sigma``) plus, at rate ``lam`` per year, jumps whose log size is Normal(``mu_j``, ``delta``).
That one change produces fat tails and a volatility smile, which constant-volatility Black-Scholes cannot.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import optimize, stats

# ----------------------------------------------------------------------------- symbolic moments (SymPy)


@lru_cache(maxsize=1)
def cumulant_functions():
    """Derive the first four cumulants of the Merton log return over a horizon ``t`` with SymPy, from the
    cumulant generating function K(u) = log E[exp(u X_t)], and compile them to fast numpy functions.

    Returns ``(exprs, fns)``: the SymPy expressions (for the write-up) and lambdified callables
    ``f(mu, sigma, lam, mu_j, delta, t)``.
    """
    import sympy as sp
    u, mu, sigma, lam, mu_j, delta, t = sp.symbols("u mu sigma lambda mu_J delta t", real=True)
    k = sp.exp(mu_j + delta ** 2 / 2) - 1                    # mean relative jump size
    drift = mu - sigma ** 2 / 2 - lam * k                    # compensated so E[S_t] = S_0 e^{mu t}
    K = u * drift * t + sp.Rational(1, 2) * sigma ** 2 * u ** 2 * t + lam * t * (sp.exp(u * mu_j + u ** 2 * delta ** 2 / 2) - 1)
    exprs = [sp.simplify(sp.diff(K, u, n).subs(u, 0)) for n in range(1, 5)]
    fns = [sp.lambdify((mu, sigma, lam, mu_j, delta, t), e, "numpy") for e in exprs]
    return exprs, fns


def merton_moments(sigma, lam, mu_j, delta, t, mu=0.0):
    """Mean, variance, skewness and excess kurtosis of the log return over ``t`` years."""
    _, (k1, k2, k3, k4) = cumulant_functions()
    c1, c2, c3, c4 = (f(mu, sigma, lam, mu_j, delta, t) for f in (k1, k2, k3, k4))
    return c1, c2, c3 / c2 ** 1.5, c4 / c2 ** 2


# ----------------------------------------------------------------------------- maximum likelihood fit


def merton_logpdf(x, mu, sigma, lam, mu_j, delta, dt, n_max=8):
    """Log density of a Merton log return over ``dt`` (a Poisson mixture of normals, truncated at n_max)."""
    x = np.asarray(x, float)[:, None]
    n = np.arange(n_max + 1)[None, :]
    k = math.exp(mu_j + 0.5 * delta ** 2) - 1
    m = (mu - 0.5 * sigma ** 2 - lam * k) * dt + n * mu_j
    v = sigma ** 2 * dt + n * delta ** 2
    logw = stats.poisson.logpmf(n, lam * dt)
    comp = logw - 0.5 * np.log(2 * np.pi * v) - (x - m) ** 2 / (2 * v)
    mx = comp.max(axis=1, keepdims=True)
    return (mx + np.log(np.exp(comp - mx).sum(axis=1, keepdims=True)))[:, 0]


def fit_merton(returns, dt=1 / 252, start=None):
    """Maximum-likelihood fit of (mu, sigma, lam, mu_j, delta) to daily log returns.

    Bounds keep it a *jump* model rather than a two-normal blend: jump size spread ``delta`` >= 2% (about
    twice a normal S&P day) and at most 20 jumps a year.
    Returns a dict, or None if it fails.
    """
    r = np.asarray(returns, float)
    r = r[np.isfinite(r)]
    if len(r) < 120:
        return None
    sd = r.std() / math.sqrt(dt)
    x0 = start if start is not None else [r.mean() / dt, 0.8 * sd, 3.0, -0.02, 0.03]
    bounds = [(-1.0, 1.0), (0.02, 1.5), (0.0, 20.0), (-0.25, 0.15), (0.02, 0.30)]

    def nll(p):
        return -merton_logpdf(r, *p, dt).sum()
    try:
        res = optimize.minimize(nll, x0, method="L-BFGS-B", bounds=bounds)
    except (ValueError, FloatingPointError):
        return None
    mu, sigma, lam, mu_j, delta = res.x
    # likelihood-ratio check against plain normal (Black-Scholes world)
    ll_bs = stats.norm.logpdf(r, r.mean(), r.std()).sum()
    return dict(mu=mu, sigma=sigma, lam=lam, mu_j=mu_j, delta=delta, ll=-res.fun, ll_bs=ll_bs, n=len(r))


# ----------------------------------------------------------------------------- option pricing


def bs_price(S, K, T, r, vol, call=True, q=0.0):
    S, K, T, vol = (np.asarray(a, float) for a in (S, K, T, vol))
    sq = vol * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * vol ** 2) * T) / sq
    d2 = d1 - sq
    if call:
        return S * np.exp(-q * T) * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
    return K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * np.exp(-q * T) * stats.norm.cdf(-d1)


def merton_price(S, K, T, r, sigma, lam, mu_j, delta, call=True, q=0.0, n_max=30):
    """Merton's series: a Poisson-weighted sum of Black-Scholes prices (risk-neutral parameters)."""
    k = math.exp(mu_j + 0.5 * delta ** 2) - 1
    lam_p = lam * (1 + k)
    out = 0.0
    for n in range(n_max + 1):
        w = stats.poisson.pmf(n, lam_p * T)
        if w < 1e-12 and n > lam_p * T:
            break
        vol_n = np.sqrt(sigma ** 2 + n * delta ** 2 / T)
        r_n = r - lam * k + n * (mu_j + 0.5 * delta ** 2) / T
        out = out + w * bs_price(S, K, T, r_n, vol_n, call, q)
    return out


def implied_vol(price, S, K, T, r, call=True, q=0.0):
    intrinsic = max(0.0, (S * math.exp(-q * T) - K * math.exp(-r * T)) if call else (K * math.exp(-r * T) - S * math.exp(-q * T)))
    if not np.isfinite(price) or price <= intrinsic + 1e-8:
        return np.nan
    f = lambda v: float(bs_price(S, K, T, r, v, call, q)) - price  # noqa: E731
    try:
        return optimize.brentq(f, 1e-4, 5.0, xtol=1e-6)
    except ValueError:
        return np.nan


def merton_iv(S, K, T, r, sigma, lam, mu_j, delta, call=None):
    """Black-Scholes implied vol of a Merton price (OTM side, so it is the 'smile' a desk would quote)."""
    c = (K >= S) if call is None else call
    return implied_vol(float(merton_price(S, K, T, r, sigma, lam, mu_j, delta, c)), S, K, T, r, c)


def calibrate_surface(quotes: pd.DataFrame, S: float, r: float):
    """Fit risk-neutral Merton (sigma, lam, mu_j, delta) to market implied vols.

    ``quotes`` needs columns K, T, iv (OTM options). Least squares in vol points.
    """
    q = quotes.dropna(subset=["iv"])

    def resid(p):
        sigma, lam, mu_j, delta = p
        return np.array([merton_iv(S, k, t, r, sigma, lam, mu_j, delta) - v
                         for k, t, v in zip(q.K, q["T"], q.iv)])

    def safe(p):
        e = resid(p)
        return np.where(np.isfinite(e), e, 0.5)
    res = optimize.least_squares(safe, [0.12, 1.0, -0.10, 0.10],
                                 bounds=([0.02, 0.01, -0.5, 0.01], [0.8, 20, 0.2, 0.6]), max_nfev=200)
    sigma, lam, mu_j, delta = res.x
    return dict(sigma=sigma, lam=lam, mu_j=mu_j, delta=delta, rmse=float(np.sqrt(np.mean(res.fun ** 2))))


# ----------------------------------------------------------------------------- leak-free rolling features


def rolling_fits(close: pd.Series, window=504, every=5) -> pd.DataFrame:
    """Refit Merton every ``every`` days on the trailing ``window`` daily log returns (data up to and
    including that close only), forward-filled between refits."""
    lr = np.log(close).diff()
    rows, prev = {}, None
    idx = close.index
    for i in range(window, len(idx), every):
        f = fit_merton(lr.iloc[i - window + 1: i + 1].to_numpy(), start=prev)
        if f is None:
            continue
        prev = [f["mu"], f["sigma"], f["lam"], f["mu_j"], f["delta"]]
        rows[idx[i]] = f
    return pd.DataFrame(rows).T.reindex(idx).ffill()


def jump_features(fits: pd.DataFrame, vix: pd.Series, skew: pd.Series | None = None) -> pd.DataFrame:
    """Turn rolling Merton fits into signals (all known at the close).

    * ``jump_share``: share of total variance that comes from jumps.
    * ``fair_vol``: Merton's 30-day volatility from history (diffusion + jumps).
    * ``vrp``: VIX minus fair_vol, in vol points: how much the option market charges over what the
      jump-diffusion fitted to the last two years says is fair.
    * ``skew_gap``: Cboe SKEW index minus the SKEW that the fitted jumps imply (SKEW = 100 - 10 x skewness
      of the 30-day return). Positive = options price more crash risk than history justifies.
    """
    t = 30 / 365
    jv = fits["lam"] * (fits["mu_j"] ** 2 + fits["delta"] ** 2)
    tot = fits["sigma"] ** 2 + jv
    out = pd.DataFrame(index=fits.index)
    out["jump_share"] = jv / tot
    out["fair_vol"] = np.sqrt(tot)
    out["lam"] = fits["lam"]
    out["vrp"] = vix.reindex(fits.index) / 100 - out["fair_vol"]
    m = merton_moments(fits["sigma"].to_numpy(), fits["lam"].to_numpy(), fits["mu_j"].to_numpy(),
                       fits["delta"].to_numpy(), t)
    out["skew30"] = m[2]
    if skew is not None:
        out["skew_gap"] = skew.reindex(fits.index) - (100 - 10 * out["skew30"])
    return out
