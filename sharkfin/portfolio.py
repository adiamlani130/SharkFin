"""Portfolio construction: shrinkage covariance, HRP, risk parity, min-variance,
max-Sharpe and the efficient frontier."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

TRADING_DAYS = 252


def shrunk_covariance(returns: pd.DataFrame) -> pd.DataFrame:
    """Ledoit-Wolf shrinkage covariance (annualised). Far more stable out of
    sample than the sample covariance when assets > a handful."""
    from sklearn.covariance import LedoitWolf

    r = returns.dropna()
    lw = LedoitWolf().fit(r.values)
    return pd.DataFrame(lw.covariance_ * TRADING_DAYS, index=r.columns, columns=r.columns)


def expected_returns(returns: pd.DataFrame, rf: float = 0.04, erp: float = 0.05,
                     shrink: float = 0.5) -> pd.Series:
    """Blend of historical mean and CAPM-implied return (equal-weight market).

    Raw historical means are the noisiest input in mean-variance optimisation;
    shrinking toward CAPM equilibrium keeps the optimiser from chasing
    last year's winners.
    """
    r = returns.dropna()
    hist = r.mean() * TRADING_DAYS
    mkt = r.mean(axis=1)
    betas = r.apply(lambda c: np.cov(c, mkt)[0, 1] / mkt.var())
    capm = rf + betas * erp
    return shrink * capm + (1 - shrink) * hist


def _portfolio_stats(w, mu, cov, rf):
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ cov @ w))
    return ret, vol, (ret - rf) / vol if vol > 0 else np.nan


def _solve(obj, n, max_weight, extra_cons=()):
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}, *extra_cons]
    bounds = [(0.0, max_weight)] * n
    x0 = np.full(n, 1 / n)
    res = optimize.minimize(obj, x0, method="SLSQP", bounds=bounds, constraints=cons,
                            options={"maxiter": 500, "ftol": 1e-10})
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def min_variance(cov: pd.DataFrame, max_weight: float = 1.0) -> pd.Series:
    c = cov.values
    w = _solve(lambda w: w @ c @ w, len(c), max_weight)
    return pd.Series(w, index=cov.index)


def max_sharpe(mu: pd.Series, cov: pd.DataFrame, rf: float = 0.04, max_weight: float = 1.0) -> pd.Series:
    c, m = cov.values, mu.reindex(cov.index).values

    def neg_sharpe(w):
        v = np.sqrt(w @ c @ w)
        return -(w @ m - rf) / v if v > 0 else 0.0

    w = _solve(neg_sharpe, len(c), max_weight)
    return pd.Series(w, index=cov.index)


def risk_parity(cov: pd.DataFrame) -> pd.Series:
    """Equal risk contribution portfolio."""
    c = cov.values
    n = len(c)

    def obj(w):
        pv = w @ c @ w
        rc = w * (c @ w) / pv
        return ((rc - 1 / n) ** 2).sum()

    w = _solve(obj, n, 1.0)
    return pd.Series(w, index=cov.index)


def hrp(returns: pd.DataFrame) -> pd.Series:
    """Hierarchical Risk Parity (Lopez de Prado, 2016).

    Clusters assets by correlation distance, orders them quasi-diagonally and
    allocates by recursive bisection with inverse-variance weights. Does not
    require inverting the covariance matrix, so it is robust with many,
    highly correlated holdings.
    """
    r = returns.dropna()
    cov = shrunk_covariance(r)
    corr = r.corr().values
    if len(cov) == 1:
        return pd.Series([1.0], index=cov.index)
    dist = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    np.fill_diagonal(dist, 0)
    link = linkage(squareform(dist, checks=False), method="single")
    order = leaves_list(link)
    items = list(cov.index[order])
    w = pd.Series(1.0, index=items)
    clusters = [items]
    while clusters:
        clusters = [c[i:j] for c in clusters for i, j in ((0, len(c) // 2), (len(c) // 2, len(c))) if len(c) > 1]
        for k in range(0, len(clusters), 2):
            left, right = clusters[k], clusters[k + 1]
            vl, vr = _cluster_var(cov, left), _cluster_var(cov, right)
            alpha = 1 - vl / (vl + vr)
            w[left] *= alpha
            w[right] *= 1 - alpha
    return w.reindex(cov.index)


def _cluster_var(cov: pd.DataFrame, items) -> float:
    c = cov.loc[items, items].values
    ivp = 1 / np.diag(c)
    ivp /= ivp.sum()
    return float(ivp @ c @ ivp)


def efficient_frontier(mu: pd.Series, cov: pd.DataFrame, points: int = 30, max_weight: float = 1.0) -> pd.DataFrame:
    c, m = cov.values, mu.reindex(cov.index).values
    n = len(c)
    wmin = min_variance(cov, max_weight).values
    lo = float(wmin @ m)
    hi = float(np.sort(m)[::-1][: max(1, int(np.ceil(1 / max_weight)))].mean())
    rows = []
    for target in np.linspace(lo, hi, points):
        cons = ({"type": "eq", "fun": lambda w, t=target: w @ m - t},)
        try:
            w = _solve(lambda w: w @ c @ w, n, max_weight, cons)
        except Exception:
            continue
        rows.append({"return": float(w @ m), "volatility": float(np.sqrt(w @ c @ w))})
    return pd.DataFrame(rows).drop_duplicates().sort_values("volatility")


def compare_allocations(returns: pd.DataFrame, current: pd.Series | None = None, rf: float = 0.04,
                        max_weight: float = 0.35) -> pd.DataFrame:
    """Weights and ex-ante stats for each allocation method side by side."""
    r = returns.dropna()
    cov = shrunk_covariance(r)
    mu = expected_returns(r, rf=rf)
    n = len(cov)
    cap = max(max_weight, 1.0 / n + 1e-9)
    alloc = {
        "Equal Weight": pd.Series(1 / n, index=cov.index),
        "HRP": hrp(r),
        "Risk Parity": risk_parity(cov),
        "Min Variance": min_variance(cov, cap),
        "Max Sharpe": max_sharpe(mu, cov, rf, cap),
    }
    if current is not None and current.sum() > 0:
        alloc = {"Current": (current / current.sum()).reindex(cov.index).fillna(0), **alloc}
    w = pd.DataFrame(alloc)
    stats = {}
    for name, col in w.items():
        ret, vol, sh = _portfolio_stats(col.values, mu.values, cov.values, rf)
        stats[name] = {"Exp. return": ret, "Volatility": vol, "Sharpe": sh,
                       "Effective N": float(1 / (col**2).sum())}
    return w, pd.DataFrame(stats), mu, cov
