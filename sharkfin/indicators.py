"""Vectorised technical indicators.

Every function takes pandas Series/DataFrames and returns a Series/DataFrame
aligned on the same index, so indicators can be used both for display and as
model features without look-ahead (each value only uses data up to that bar).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _wilder(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothing (an EMA with alpha = 1/period)."""
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def sma(close: pd.Series, period: int) -> pd.Series:
    return close.rolling(period, min_periods=period).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index with Wilder smoothing (the standard definition)."""
    delta = close.diff()
    gain = _wilder(delta.clip(lower=0), period)
    loss = _wilder(-delta.clip(upper=0), period)
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    # No losses in the window -> RSI 100; no gains -> 0.
    out = out.where(loss != 0, 100.0)
    return out.where(gain.notna())


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    sig = line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def bollinger(close: pd.Series, period: int = 20, n_std: float = 2.0) -> pd.DataFrame:
    mid = sma(close, period)
    sd = close.rolling(period, min_periods=period).std(ddof=0)
    upper, lower = mid + n_std * sd, mid - n_std * sd
    width = (upper - lower) / mid
    pct_b = (close - lower) / (upper - lower)
    return pd.DataFrame({"upper": upper, "mid": mid, "lower": lower, "width": width, "pct_b": pct_b})


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev = close.shift(1)
    return pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    return _wilder(true_range(high, low, close), period)


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.DataFrame:
    """Average Directional Index (trend strength) with +DI / -DI."""
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=high.index)
    tr = _wilder(true_range(high, low, close), period)
    plus_di = 100 * _wilder(plus_dm, period) / tr
    minus_di = 100 * _wilder(minus_dm, period) / tr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return pd.DataFrame({"adx": _wilder(dx, period), "plus_di": plus_di, "minus_di": minus_di})


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k: int = 14, d: int = 3) -> pd.DataFrame:
    ll = low.rolling(k, min_periods=k).min()
    hh = high.rolling(k, min_periods=k).max()
    pct_k = 100 * (close - ll) / (hh - ll).replace(0, np.nan)
    return pd.DataFrame({"k": pct_k, "d": pct_k.rolling(d).mean()})


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """Money Flow Index: volume-weighted RSI."""
    tp = (high + low + close) / 3
    raw = tp * volume
    pos = raw.where(tp > tp.shift(1), 0.0).rolling(period).sum()
    neg = raw.where(tp < tp.shift(1), 0.0).rolling(period).sum()
    return 100 - 100 / (1 + pos / neg.replace(0, np.nan))


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
    """Rolling volume-weighted average price."""
    tp = (high + low + close) / 3
    return (tp * volume).rolling(period).sum() / volume.rolling(period).sum()


def realized_vol(close: pd.Series, period: int = 21, annualize: int = 252) -> pd.Series:
    r = np.log(close).diff()
    return r.rolling(period).std() * np.sqrt(annualize)


def parkinson_vol(high: pd.Series, low: pd.Series, period: int = 21, annualize: int = 252) -> pd.Series:
    """Range-based volatility estimator (~5x more efficient than close-to-close)."""
    hl = np.log(high / low) ** 2
    return np.sqrt(hl.rolling(period).mean() / (4 * np.log(2)) * annualize)


def donchian(high: pd.Series, low: pd.Series, period: int = 20) -> pd.DataFrame:
    return pd.DataFrame({"upper": high.rolling(period).max(), "lower": low.rolling(period).min()})


def hurst_exponent(close: pd.Series, max_lag: int = 50) -> float:
    """Hurst exponent via the variance-of-lagged-differences method.

    ~0.5 random walk, >0.5 trending/persistent, <0.5 mean-reverting.
    """
    x = np.log(close.dropna().values)
    if len(x) < max_lag * 2:
        return float("nan")
    lags = np.arange(2, max_lag)
    tau = np.array([np.std(x[lag:] - x[:-lag]) for lag in lags])
    ok = tau > 0
    if ok.sum() < 5:
        return float("nan")
    slope = np.polyfit(np.log(lags[ok]), np.log(tau[ok]), 1)[0]
    return float(slope)


def compute_all(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Full indicator panel for an OHLCV frame (columns Open/High/Low/Close/Volume)."""
    c, h, l, v = ohlcv["Close"], ohlcv["High"], ohlcv["Low"], ohlcv["Volume"]
    out = pd.DataFrame(index=ohlcv.index)
    out["close"] = c
    for p in (10, 20, 50, 100, 200):
        out[f"sma_{p}"] = sma(c, p)
    out["ema_12"], out["ema_26"] = ema(c, 12), ema(c, 26)
    out["rsi_14"] = rsi(c, 14)
    out = out.join(macd(c).add_prefix(""))
    out = out.join(bollinger(c).add_prefix("bb_"))
    out["atr_14"] = atr(h, l, c)
    out["natr_14"] = out["atr_14"] / c * 100
    out = out.join(adx(h, l, c))
    out = out.join(stochastic(h, l, c).add_prefix("stoch_"))
    out["obv"] = obv(c, v)
    out["mfi_14"] = mfi(h, l, c, v)
    out["vwap_20"] = vwap(h, l, c, v)
    out["rv_21"] = realized_vol(c)
    out["pk_vol_21"] = parkinson_vol(h, l)
    return out


def technical_signal(panel: pd.DataFrame) -> dict:
    """Regime-aware technical read of the latest bar.

    Instead of blindly adding "RSI oversold = buy" to "momentum = buy" (which
    contradict each other), the signal first classifies the regime with ADX:
    in trending regimes trend-following evidence dominates, in ranging regimes
    mean-reversion oscillators dominate. Returns a score in [-1, 1] and the
    evidence behind it.
    """
    last = panel.iloc[-1]
    evidence: list[tuple[str, float]] = []
    price = last["close"]

    trending = bool(last.get("adx", np.nan) >= 25)
    regime = "Trending" if trending else "Range-bound"

    # Trend evidence
    trend_pts = 0.0
    if pd.notna(last.get("sma_200")):
        s = 1.0 if price > last["sma_200"] else -1.0
        trend_pts += s
        evidence.append(("Price vs 200-day MA", s))
    if pd.notna(last.get("sma_50")) and pd.notna(last.get("sma_200")):
        s = 1.0 if last["sma_50"] > last["sma_200"] else -1.0
        trend_pts += s
        evidence.append(("50/200 MA cross (golden/death)", s))
    if pd.notna(last.get("hist")):
        s = 0.5 if last["hist"] > 0 else -0.5
        trend_pts += s
        evidence.append(("MACD histogram", s))
    if pd.notna(last.get("plus_di")) and pd.notna(last.get("minus_di")):
        s = 0.5 if last["plus_di"] > last["minus_di"] else -0.5
        trend_pts += s
        evidence.append(("Directional movement (+DI vs -DI)", s))
    trend_score = trend_pts / 3.0

    # Mean-reversion evidence
    mr_pts = 0.0
    r = last.get("rsi_14", np.nan)
    if pd.notna(r):
        s = float(np.clip((50 - r) / 20, -1, 1))
        mr_pts += s
        evidence.append((f"RSI(14) = {r:.0f}", s))
    pb = last.get("bb_pct_b", np.nan)
    if pd.notna(pb):
        s = float(np.clip((0.5 - pb) * 2, -1, 1))
        mr_pts += s
        evidence.append(("Bollinger %B", s))
    k = last.get("stoch_k", np.nan)
    if pd.notna(k):
        s = float(np.clip((50 - k) / 40, -1, 1)) * 0.5
        mr_pts += s
        evidence.append(("Stochastic %K", s))
    mr_score = mr_pts / 2.5

    w_trend = 0.75 if trending else 0.35
    score = float(np.clip(w_trend * trend_score + (1 - w_trend) * mr_score, -1, 1))

    if score >= 0.5:
        label = "Strong Buy"
    elif score >= 0.15:
        label = "Buy"
    elif score <= -0.5:
        label = "Strong Sell"
    elif score <= -0.15:
        label = "Sell"
    else:
        label = "Neutral"
    return {
        "score": score,
        "label": label,
        "regime": regime,
        "trend_score": trend_score,
        "mean_reversion_score": mr_score,
        "evidence": evidence,
    }
