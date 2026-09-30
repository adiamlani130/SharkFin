"""Performance and risk statistics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

TRADING_DAYS = 252


def to_returns(prices: pd.Series | pd.DataFrame, log: bool = False):
    if log:
        return np.log(prices).diff().dropna(how="all")
    return prices.pct_change(fill_method=None).dropna(how="all")


def annualized_return(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    r = returns.dropna()
    if r.empty:
        return float("nan")
    growth = float((1 + r).prod())
    if growth <= 0:
        return -1.0
    return growth ** (periods / len(r)) - 1


def annualized_vol(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    return float(returns.dropna().std() * np.sqrt(periods))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    r = returns.dropna() - rf / periods
    sd = r.std()
    return float(r.mean() / sd * np.sqrt(periods)) if sd > 0 else float("nan")


def sortino_ratio(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    r = returns.dropna() - rf / periods
    downside = np.sqrt((np.minimum(r, 0) ** 2).mean())
    return float(r.mean() / downside * np.sqrt(periods)) if downside > 0 else float("nan")


def drawdown_series(returns: pd.Series) -> pd.Series:
    wealth = (1 + returns.fillna(0)).cumprod()
    return wealth / wealth.cummax() - 1


def max_drawdown(returns: pd.Series) -> float:
    dd = drawdown_series(returns)
    return float(dd.min()) if not dd.empty else float("nan")


def calmar_ratio(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    mdd = max_drawdown(returns)
    return annualized_return(returns, periods) / abs(mdd) if mdd < 0 else float("nan")


def historical_var(returns: pd.Series, level: float = 0.95) -> float:
    """1-period historical Value-at-Risk, reported as a positive loss."""
    r = returns.dropna()
    return float(-np.quantile(r, 1 - level)) if len(r) else float("nan")


def historical_cvar(returns: pd.Series, level: float = 0.95) -> float:
    """Expected shortfall: average loss beyond VaR."""
    r = returns.dropna()
    if r.empty:
        return float("nan")
    cutoff = np.quantile(r, 1 - level)
    tail = r[r <= cutoff]
    return float(-tail.mean()) if len(tail) else float("nan")


def cornish_fisher_var(returns: pd.Series, level: float = 0.95) -> float:
    """Parametric VaR adjusted for skew and fat tails (Cornish-Fisher expansion)."""
    r = returns.dropna()
    if len(r) < 30:
        return float("nan")
    z = stats.norm.ppf(1 - level)
    s, k = stats.skew(r), stats.kurtosis(r)  # excess kurtosis
    z_cf = z + (z**2 - 1) * s / 6 + (z**3 - 3 * z) * k / 24 - (2 * z**3 - 5 * z) * s**2 / 36
    return float(-(r.mean() + z_cf * r.std()))


def beta_alpha(returns: pd.Series, bench: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS):
    """OLS beta and annualised Jensen's alpha versus a benchmark."""
    df = pd.concat([returns, bench], axis=1).dropna()
    if len(df) < 20:
        return float("nan"), float("nan")
    y = df.iloc[:, 0] - rf / periods
    x = df.iloc[:, 1] - rf / periods
    beta = float(np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1))
    alpha = float((y.mean() - beta * x.mean()) * periods)
    return beta, alpha


def blume_adjusted_beta(raw_beta: float) -> float:
    """Blume (1971) adjustment: betas mean-revert toward 1 (0.67*raw + 0.33)."""
    return 0.67 * raw_beta + 0.33 if np.isfinite(raw_beta) else float("nan")


def summary(returns: pd.Series, bench: pd.Series | None = None, rf: float = 0.0) -> dict:
    out = {
        "CAGR": annualized_return(returns),
        "Volatility": annualized_vol(returns),
        "Sharpe": sharpe_ratio(returns, rf),
        "Sortino": sortino_ratio(returns, rf),
        "Max Drawdown": max_drawdown(returns),
        "Calmar": calmar_ratio(returns),
        "VaR 95% (1d)": historical_var(returns),
        "CVaR 95% (1d)": historical_cvar(returns),
        "CF VaR 95% (1d)": cornish_fisher_var(returns),
        "Skew": float(stats.skew(returns.dropna())) if len(returns.dropna()) > 2 else float("nan"),
        "Excess Kurtosis": float(stats.kurtosis(returns.dropna())) if len(returns.dropna()) > 3 else float("nan"),
        "Hit Rate": float((returns.dropna() > 0).mean()) if len(returns.dropna()) else float("nan"),
    }
    if bench is not None:
        b, a = beta_alpha(returns, bench, rf)
        out["Beta"] = b
        out["Alpha (ann.)"] = a
        active = (returns - bench).dropna()
        te = active.std() * np.sqrt(TRADING_DAYS)
        out["Tracking Error"] = float(te)
        out["Information Ratio"] = float(active.mean() * TRADING_DAYS / te) if te > 0 else float("nan")
    return out


def risk_contributions(weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Fraction of total portfolio variance contributed by each asset."""
    w = np.asarray(weights, dtype=float)
    port_var = float(w @ cov @ w)
    if port_var <= 0:
        return np.full_like(w, np.nan)
    return w * (cov @ w) / port_var
