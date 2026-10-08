"""Price levels and trend context for charts: support and resistance zones,
the weekly trend, and RSI bearish divergence.

These describe where a stock sits; they are not a trading system. SharkFin's
swing system is Leader Dip (``leader_dip.py``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import indicators as ind


def pivots(high: pd.Series, low: pd.Series, k: int = 5) -> tuple[pd.Series, pd.Series]:
    """Swing highs/lows: the extreme of a 2k+1 bar window. A pivot at bar j is
    only known at bar j+k, so callers must respect that confirmation lag."""
    win = 2 * k + 1
    ph = high.where(high == high.rolling(win, center=True).max())
    pl = low.where(low == low.rolling(win, center=True).min())
    return ph, pl


def sr_zones(ohlcv: pd.DataFrame, lookback: int = 250, k: int = 5, merge_atr: float = 0.75) -> list[dict]:
    """Support/resistance zones from clustered swing highs and lows over the
    last ``lookback`` bars, as of the last bar."""
    df = ohlcv.iloc[-lookback - k:]
    if len(df) < 2 * k + 2:
        return []
    ph, pl = pivots(df["High"], df["Low"], k)
    a = float(ind.atr(ohlcv["High"], ohlcv["Low"], ohlcv["Close"]).iloc[-1])
    if not np.isfinite(a) or a <= 0:
        a = float((df["High"] - df["Low"]).mean())
    levels = sorted([(float(v), "high") for v in ph.dropna()] + [(float(v), "low") for v in pl.dropna()])
    zones: list[dict] = []
    for lvl, _ in levels:
        if zones and lvl - zones[-1]["high"] <= merge_atr * a:
            z = zones[-1]
            z["high"], z["touches"] = lvl, z["touches"] + 1
            z["levels"].append(lvl)
        else:
            zones.append({"low": lvl, "high": lvl, "touches": 1, "levels": [lvl]})
    price = float(ohlcv["Close"].iloc[-1])
    out = []
    for z in zones:
        mid = float(np.mean(z["levels"]))
        out.append({"low": z["low"], "high": z["high"], "mid": mid, "touches": z["touches"],
                    "kind": "resistance" if mid > price else "support"})
    return out


def nearest_levels(ohlcv: pd.DataFrame, zones: list[dict] | None = None) -> tuple[float, float]:
    """(nearest resistance above, nearest support below) the last close."""
    zones = sr_zones(ohlcv) if zones is None else zones
    price = float(ohlcv["Close"].iloc[-1])
    res = [z["low"] for z in zones if z["low"] > price] + [z["mid"] for z in zones if z["low"] <= price < z["mid"]]
    sup = [z["high"] for z in zones if z["high"] < price] + [z["mid"] for z in zones if z["mid"] < price <= z["high"]]
    return (min(res) if res else np.nan, max(sup) if sup else np.nan)


def rsi_bearish_divergence(high: pd.Series, rsi: pd.Series, window: int = 14, min_gap: int = 3) -> pd.Series:
    """True on bars that make a higher high than the highest bar of the prior
    ``window`` bars while RSI is lower than it was at that earlier high."""
    h, r = high.values, rsi.values
    out = np.zeros(len(h), dtype=bool)
    for t in range(window, len(h)):
        seg = h[t - window:t - min_gap + 1]
        j = t - window + int(np.nanargmax(seg))
        if h[t] > h[j] and np.isfinite(r[j]) and np.isfinite(r[t]) and r[j] >= 60 and r[t] < r[j] - 2:
            out[t] = True
    return pd.Series(out, index=high.index)


def weekly_trend(close: pd.Series) -> dict:
    wk = close.resample("W-FRI").last().dropna()
    if len(wk) < 45:
        return {"label": "Not enough history", "above_40w": None, "ma10_above_ma40": None}
    ma10, ma40 = wk.rolling(10).mean(), wk.rolling(40).mean()
    above = bool(wk.iloc[-1] > ma40.iloc[-1])
    aligned = bool(ma10.iloc[-1] > ma40.iloc[-1])
    rising = bool(ma40.iloc[-1] > ma40.iloc[-5])
    if above and aligned and rising:
        label = "Uptrend"
    elif not above and not aligned:
        label = "Downtrend"
    else:
        label = "Mixed"
    return {"label": label, "above_40w": above, "ma10_above_ma40": aligned, "ma40_rising": rising,
            "ma40": float(ma40.iloc[-1])}
