"""Probabilistic, walk-forward validated price forecasting.

Design principles (what was wrong before and how this fixes it):

* **Model returns, not price levels.** Tree models cannot extrapolate price
  levels and linear fits on prices produce spurious trends. Every model here
  forecasts cumulative *log returns*.
* **No random noise in point forecasts.** Uncertainty is modelled explicitly:
  a GARCH(1,1) filtered-historical-simulation (FHS) engine produces the
  volatility cone (vol clustering + fat tails from bootstrapped standardised
  residuals). The ensemble of mean models only sets the *location*.
* **Honest validation.** Every model is re-fit at a series of past origins and
  scored out-of-sample against a random-walk baseline (walk-forward with a
  purge gap). Ensemble weights come from that out-of-sample error, so models
  that don't beat a random walk get little or no weight.
* **Calibration is measured.** The backtest reports how often realised prices
  fell inside the 80% band.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import optimize, signal

from . import indicators as ind

QUANTILES = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)


# ---------------------------------------------------------------------------
# GARCH(1,1) volatility model
# ---------------------------------------------------------------------------


@dataclass
class GarchFit:
    omega: float
    alpha: float
    beta: float
    mu: float
    last_sigma2: float
    last_resid: float
    std_resid: np.ndarray = field(repr=False)

    @property
    def persistence(self) -> float:
        return self.alpha + self.beta

    @property
    def long_run_vol(self) -> float:
        """Annualised unconditional volatility."""
        denom = max(1e-6, 1 - self.persistence)
        return float(np.sqrt(self.omega / denom * 252))

    @property
    def current_vol(self) -> float:
        """Annualised next-day conditional volatility."""
        nxt = self.omega + self.alpha * self.last_resid**2 + self.beta * self.last_sigma2
        return float(np.sqrt(nxt * 252))

    @property
    def half_life(self) -> float:
        p = self.persistence
        return float(np.log(0.5) / np.log(p)) if 0 < p < 1 else float("inf")


def _garch_recursion(omega, alpha, beta, eps2, init_var):
    n = len(eps2)
    # Closed form via lfilter: s_t - beta*s_{t-1} = omega + alpha*eps2_{t-1}
    drive = np.empty(n)
    drive[0] = init_var * (1 - beta)  # so that s_0 = init_var when s_{-1} = init_var
    drive[1:] = omega + alpha * eps2[:-1]
    zi = np.array([beta * init_var])
    s, _ = signal.lfilter([1.0], [1.0, -beta], drive, zi=zi)
    s[0] = init_var
    return np.maximum(s, 1e-12)


def fit_garch(log_returns: np.ndarray) -> GarchFit:
    """Gaussian quasi-MLE GARCH(1,1). Robust to failures (falls back to EWMA)."""
    r = np.asarray(log_returns, dtype=float)
    r = r[np.isfinite(r)]
    mu = float(r.mean())
    eps = r - mu
    eps2 = eps**2
    var0 = float(eps2.mean())

    def nll(p):
        omega, alpha, beta = p
        if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 0.999:
            return 1e10
        s2 = _garch_recursion(omega, alpha, beta, eps2, var0)
        return 0.5 * np.sum(np.log(s2) + eps2 / s2)

    x0 = np.array([var0 * 0.05, 0.08, 0.90])
    bounds = [(1e-12, var0 * 10), (0.0, 0.5), (0.0, 0.999)]
    try:
        res = optimize.minimize(nll, x0, method="L-BFGS-B", bounds=bounds)
        omega, alpha, beta = res.x
        if not res.success or alpha + beta >= 0.999:
            raise RuntimeError
    except Exception:
        # RiskMetrics EWMA fallback (lambda = 0.94)
        omega, alpha, beta = var0 * 1e-6, 0.06, 0.94 - 1e-6
    s2 = _garch_recursion(omega, alpha, beta, eps2, var0)
    z = eps / np.sqrt(s2)
    return GarchFit(float(omega), float(alpha), float(beta), mu, float(s2[-1]), float(eps[-1]), z)


def simulate_garch_paths(fit: GarchFit, horizon: int, n_paths: int = 4000, seed: int = 7) -> np.ndarray:
    """Filtered historical simulation. Returns (n_paths, horizon) cumulative
    *zero-drift* log returns."""
    rng = np.random.default_rng(seed)
    z = fit.std_resid
    z = (z - z.mean()) / z.std()
    s2 = np.full(n_paths, fit.omega + fit.alpha * fit.last_resid**2 + fit.beta * fit.last_sigma2)
    cum = np.zeros((n_paths, horizon))
    total = np.zeros(n_paths)
    for t in range(horizon):
        shock = rng.choice(z, size=n_paths, replace=True)
        e = np.sqrt(s2) * shock
        total = total + e
        cum[:, t] = total
        s2 = fit.omega + fit.alpha * e**2 + fit.beta * s2
    return cum - cum.mean(axis=0, keepdims=True)


# ---------------------------------------------------------------------------
# Mean (location) models. Each returns cumulative expected log return for
# horizons 1..H given a history of log prices.
# ---------------------------------------------------------------------------


class MeanModel:
    name = "base"
    description = ""

    def forecast(self, log_price: pd.Series, horizon: int, ohlcv: pd.DataFrame | None = None) -> np.ndarray:
        raise NotImplementedError


class RandomWalk(MeanModel):
    name = "Random Walk"
    description = "Efficient-market baseline: best guess for tomorrow is today's price."

    def forecast(self, log_price, horizon, ohlcv=None):
        return np.zeros(horizon)


class BayesianDrift(MeanModel):
    name = "Bayesian Drift"
    description = ("Historical drift shrunk toward a long-run equity premium prior "
                   "(normal-normal conjugate update), avoiding naive trend extrapolation.")

    def __init__(self, lookback: int = 504, prior_annual: float = 0.07, prior_sd_annual: float = 0.10):
        self.lookback = lookback
        self.prior = prior_annual / 252
        self.tau2 = (prior_sd_annual / 252) ** 2  # prior variance of the daily mean

    def forecast(self, log_price, horizon, ohlcv=None):
        r = log_price.diff().dropna().iloc[-self.lookback:]
        n, xbar, s2 = len(r), float(r.mean()), float(r.var())
        if n < 20 or s2 <= 0:
            return self.prior * np.arange(1, horizon + 1)
        post = (self.prior / self.tau2 + n * xbar / s2) / (1 / self.tau2 + n / s2)
        return post * np.arange(1, horizon + 1)


class ArimaModel(MeanModel):
    name = "ARIMA"
    description = "ARMA(p,q) on daily log returns, order chosen by AIC over a small grid."

    ORDERS = ((0, 0, 1), (1, 0, 0), (1, 0, 1), (2, 0, 1), (0, 0, 2))

    def forecast(self, log_price, horizon, ohlcv=None):
        from statsmodels.tsa.arima.model import ARIMA

        r = log_price.diff().dropna().iloc[-750:].values * 100  # percent for numerics
        best, best_aic = None, np.inf
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for order in self.ORDERS:
                try:
                    res = ARIMA(r, order=order, trend="c").fit()
                    if res.aic < best_aic:
                        best, best_aic = res, res.aic
                except Exception:
                    continue
        if best is None:
            return np.zeros(horizon)
        daily = np.asarray(best.forecast(horizon)) / 100
        return np.cumsum(daily)


class DampedTrendETS(MeanModel):
    name = "Damped ETS"
    description = "Holt's exponential smoothing with a damped trend on log prices."

    def forecast(self, log_price, horizon, ohlcv=None):
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        y = log_price.iloc[-500:].values
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = ExponentialSmoothing(y, trend="add", damped_trend=True).fit(optimized=True)
                fc = np.asarray(res.forecast(horizon))
            except Exception:
                return np.zeros(horizon)
        return fc - y[-1]


def build_features(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Stationary, scale-free features for return prediction (no look-ahead)."""
    c = ohlcv["Close"]
    lr = np.log(c).diff()
    f = pd.DataFrame(index=ohlcv.index)
    for w in (1, 5, 10, 21, 63, 126, 252):
        f[f"ret_{w}"] = np.log(c / c.shift(w))
    f["mom_12_1"] = np.log(c.shift(21) / c.shift(252))
    f["vol_21"] = lr.rolling(21).std()
    f["vol_63"] = lr.rolling(63).std()
    f["vol_ratio"] = f["vol_21"] / f["vol_63"]
    f["rsi_14"] = ind.rsi(c, 14) / 100
    m = ind.macd(c)
    f["macd_hist_n"] = m["hist"] / c
    f["bb_pct_b"] = ind.bollinger(c)["pct_b"]
    f["dist_sma50"] = c / ind.sma(c, 50) - 1
    f["dist_sma200"] = c / ind.sma(c, 200) - 1
    f["dist_52w_high"] = c / c.rolling(252, min_periods=60).max() - 1
    if {"High", "Low"}.issubset(ohlcv.columns):
        f["natr"] = ind.atr(ohlcv["High"], ohlcv["Low"], c) / c
        f["adx"] = ind.adx(ohlcv["High"], ohlcv["Low"], c)["adx"] / 100
        f["range_pos"] = (c - ohlcv["Low"].rolling(20).min()) / (
            ohlcv["High"].rolling(20).max() - ohlcv["Low"].rolling(20).min()
        )
    if "Volume" in ohlcv.columns:
        v = ohlcv["Volume"].replace(0, np.nan)
        f["vol_z"] = (np.log(v) - np.log(v).rolling(63).mean()) / np.log(v).rolling(63).std()
    f["dow"] = ohlcv.index.dayofweek if isinstance(ohlcv.index, pd.DatetimeIndex) else 0
    return f.replace([np.inf, -np.inf], np.nan)


class GradientBoostingML(MeanModel):
    name = "Gradient Boosting"
    description = ("Histogram gradient-boosted trees on 20+ stationary features, trained "
                   "directly per horizon with a purge gap (no recursive error compounding).")

    def __init__(self, anchors=(5, 10, 21, 42, 63)):
        self.anchors = anchors

    def forecast(self, log_price, horizon, ohlcv=None):
        from sklearn.ensemble import HistGradientBoostingRegressor

        if ohlcv is None:
            ohlcv = pd.DataFrame({"Close": np.exp(log_price)})
        feats = build_features(ohlcv)
        lp = np.log(ohlcv["Close"])
        anchors = sorted({a for a in self.anchors if a < horizon} | {horizon})
        preds = {0: 0.0}
        x_now = feats.iloc[[-1]]
        for h in anchors:
            y = lp.shift(-h) - lp
            data = feats.join(y.rename("y"))
            # Purge: only rows whose target window ended before today
            train = data.iloc[: len(data) - h].dropna(subset=["y"])
            train = train.dropna(thresh=int(train.shape[1] * 0.7))
            if len(train) < 150:
                preds[h] = 0.0
                continue
            model = HistGradientBoostingRegressor(
                max_iter=150, learning_rate=0.04, max_leaf_nodes=15,
                min_samples_leaf=40, l2_regularization=1.0, random_state=0,
            )
            model.fit(train.drop(columns="y"), train["y"])
            # Shrink toward zero in proportion to in-sample noise (predictions of
            # returns are notoriously over-confident).
            preds[h] = float(model.predict(x_now)[0]) * 0.5
        hs = np.array(sorted(preds))
        vals = np.array([preds[h] for h in hs])
        return np.interp(np.arange(1, horizon + 1), hs, vals)


DEFAULT_MODELS = (RandomWalk, BayesianDrift, ArimaModel, DampedTrendETS, GradientBoostingML)


# ---------------------------------------------------------------------------
# Walk-forward evaluation and ensemble
# ---------------------------------------------------------------------------


@dataclass
class ModelScore:
    name: str
    description: str
    rmse: float
    mae: float
    directional_accuracy: float
    skill_vs_rw: float
    weight: float = 0.0
    forecast_return: float = 0.0


@dataclass
class ForecastResult:
    symbol: str
    last_price: float
    horizon: int
    dates: pd.DatetimeIndex
    quantiles: pd.DataFrame  # index = dates, columns = quantile levels (prices)
    expected_price: np.ndarray
    prob_up: np.ndarray
    model_paths: dict  # name -> price path (expected)
    scores: list
    garch: GarchFit
    coverage_80: float
    n_backtest: int
    sample_paths: np.ndarray = field(repr=False, default=None)

    def at(self, h: int) -> dict:
        i = min(h, self.horizon) - 1
        return {
            "date": self.dates[i],
            "expected": float(self.expected_price[i]),
            "median": float(self.quantiles.iloc[i][0.5]),
            "low80": float(self.quantiles.iloc[i][0.10]),
            "high80": float(self.quantiles.iloc[i][0.90]),
            "low90": float(self.quantiles.iloc[i][0.05]),
            "high90": float(self.quantiles.iloc[i][0.95]),
            "prob_up": float(self.prob_up[i]),
            "exp_return": float(self.expected_price[i] / self.last_price - 1),
        }


def walk_forward(ohlcv: pd.DataFrame, horizon: int, models, n_origins: int = 10, step: int | None = None):
    """Re-fit each model at past origins and record out-of-sample errors of the
    cumulative log return at the full horizon."""
    lp = np.log(ohlcv["Close"])
    step = step or max(5, horizon // 2)
    n = len(lp)
    last_origin = n - 1 - horizon
    origins = [last_origin - i * step for i in range(n_origins)]
    origins = [o for o in origins if o > 300]
    errors = {m.name: [] for m in models}
    preds = {m.name: [] for m in models}
    realized, garch_bands = [], []
    for o in sorted(origins):
        hist = ohlcv.iloc[: o + 1]
        lph = lp.iloc[: o + 1]
        actual = float(lp.iloc[o + horizon] - lp.iloc[o])
        realized.append(actual)
        for m in models:
            try:
                f = float(m.forecast(lph, horizon, hist)[-1])
            except Exception:
                f = 0.0
            preds[m.name].append(f)
            errors[m.name].append(f - actual)
        g = fit_garch(lph.diff().dropna().values[-1000:])
        sims = simulate_garch_paths(g, horizon, n_paths=800, seed=o)[:, -1]
        garch_bands.append((np.quantile(sims, 0.10), np.quantile(sims, 0.90)))
    return origins, errors, preds, realized, garch_bands


def ensemble_forecast(ohlcv: pd.DataFrame, symbol: str = "", horizon: int = 21,
                      n_origins: int = 10, models=None, n_paths: int = 4000) -> ForecastResult:
    if len(ohlcv) < 320:
        raise ValueError("Need at least ~15 months of daily history for a validated forecast.")
    models = [m() for m in (models or DEFAULT_MODELS)]
    ohlcv = ohlcv.dropna(subset=["Close"])
    lp = np.log(ohlcv["Close"])
    last = float(ohlcv["Close"].iloc[-1])

    origins, errors, preds, realized, bands = walk_forward(ohlcv, horizon, models, n_origins)
    realized_arr = np.array(realized)
    rw_mse = float(np.mean(realized_arr**2)) if len(realized_arr) else np.nan

    scores = []
    for m in models:
        e = np.array(errors[m.name])
        p = np.array(preds[m.name])
        mse = float(np.mean(e**2)) if len(e) else np.nan
        if m.name == "Random Walk" or not len(p):
            da = 0.5
        else:
            nz = p != 0
            da = float(np.mean(np.sign(p[nz]) == np.sign(realized_arr[nz]))) if nz.any() else 0.5
        skill = 1 - mse / rw_mse if rw_mse and np.isfinite(mse) else 0.0
        scores.append(ModelScore(m.name, m.description, float(np.sqrt(mse)), float(np.mean(np.abs(e))) if len(e) else np.nan, da, skill))

    # Weights: inverse MSE, but models that fail to beat the random walk are
    # penalised hard; everything is then blended with the random walk.
    raw = []
    for s in scores:
        inv = 1.0 / max(s.rmse**2, 1e-8)
        if s.name != "Random Walk" and s.skill_vs_rw < 0:
            inv *= max(0.0, 1 + 4 * s.skill_vs_rw)  # skill -25% -> weight 0
        raw.append(inv)
    raw = np.array(raw)
    w = raw / raw.sum() if raw.sum() > 0 else np.ones(len(raw)) / len(raw)
    for s, wi in zip(scores, w):
        s.weight = float(wi)

    # Final fits on full history
    paths = {}
    mu = np.zeros(horizon)
    for m, s in zip(models, scores):
        try:
            f = np.asarray(m.forecast(lp, horizon, ohlcv), dtype=float)
        except Exception:
            f = np.zeros(horizon)
        f = np.nan_to_num(f)
        s.forecast_return = float(np.exp(f[-1]) - 1)
        paths[m.name] = last * np.exp(f)
        mu += s.weight * f

    g = fit_garch(lp.diff().dropna().values[-1500:])
    sims = simulate_garch_paths(g, horizon, n_paths=n_paths)
    # Model disagreement adds epistemic uncertainty on top of GARCH risk.
    disagreement = np.sqrt(sum(s.weight * (np.log(paths[s.name] / last) - mu) ** 2 for s in scores))
    rng = np.random.default_rng(11)
    sims = sims + rng.standard_normal((n_paths, 1)) * disagreement[None, :]
    cum = mu[None, :] + sims
    price_paths = last * np.exp(cum)

    dates = pd.bdate_range(ohlcv.index[-1] + pd.Timedelta(days=1), periods=horizon) \
        if isinstance(ohlcv.index, pd.DatetimeIndex) else pd.RangeIndex(1, horizon + 1)
    q = np.quantile(price_paths, QUANTILES, axis=0).T
    qdf = pd.DataFrame(q, index=dates, columns=list(QUANTILES))
    coverage = float(np.mean([(lo <= r <= hi) for (lo, hi), r in zip(bands, realized)])) if bands else np.nan

    return ForecastResult(
        symbol=symbol, last_price=last, horizon=horizon, dates=dates, quantiles=qdf,
        expected_price=price_paths.mean(axis=0), prob_up=(price_paths > last).mean(axis=0),
        model_paths=paths, scores=scores, garch=g, coverage_80=coverage,
        n_backtest=len(realized), sample_paths=price_paths[:60],
    )
