"""A 12-month price target and an ideal range to buy in, for a long-term or growth investor.

Price target. Two views of what a stock is worth: SharkFin's blended fair value (cash-flow model, peer multiples
and analyst targets) and the analysts' own average 12-month target. The target is their geometric mean; the bear
and bull cases are the middle of the low and high ends of every method's range. Analysts' targets run too high on
average, which is why they are only half the target and a fifth of the fair value.

Entry range. SharkFin's Nov 2026 study (``growth_lab.entry_zones``) checked where in its price path a stock
was bought, for every S&P 500 member at each month end since 2006, against what it did over the next 6-12 months.
Price-path timing barely mattered: the zones were within a few points of each other and flipped between 2006-15
and 2016-26. The one small, steady edge was buying a market leader on a pullback, RSI(14) under 40 while above its
200-day average: 2.5 points more over the next 12 months than buying the same leaders on any day in 2006-15,
and 0.2 points more in 2016-26. So the range is set by value
first: the top is the price that leaves a margin of safety below the target, and the bottom is where the trend
breaks (the 200-day average or the nearest support under the top), with the RSI-40 pullback price as the
technical hint inside it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MARGIN = 0.15        # buy only with at least 15% upside to the target
RANGE_DEPTH = 0.15   # the range spans at most 15% under its top


def _ok(x) -> bool:
    try:
        return x is not None and np.isfinite(float(x)) and float(x) > 0
    except (TypeError, ValueError):
        return False


def price_target(price: float, fair_value: float, analyst_mean: float, lows: list, highs: list) -> dict:
    """{"target", "upside", "bear", "bull", "basis"}: the geometric mean of the blended fair value and the analyst
    mean target (whichever exist), with bear / bull cases from the median of the methods' low and high ends."""
    parts = [(n, float(v)) for n, v in (("fair value", fair_value), ("analyst target", analyst_mean)) if _ok(v)]
    if not parts or not _ok(price):
        return {"target": np.nan, "upside": np.nan, "bear": np.nan, "bull": np.nan, "basis": []}
    t = float(np.exp(np.mean([np.log(v) for _, v in parts])))
    lo = [float(x) for x in lows if _ok(x)]
    hi = [float(x) for x in highs if _ok(x)]
    bear = float(np.median(lo)) if lo else t * 0.75
    bull = float(np.median(hi)) if hi else t * 1.25
    bear, bull = min(bear, t), max(bull, t)
    return {"target": t, "upside": t / price - 1, "bear": bear, "bull": bull, "basis": [n for n, _ in parts]}


def rsi_pullback_price(close: pd.Series, level: float = 40.0, n: int = 14) -> float:
    """The price at which a one-day drop would take Wilder's RSI(n) down to ``level``: where a pullback starts in
    the study's terms. NaN when RSI is already at or under ``level``."""
    c = close.dropna().astype(float)
    if len(c) < n * 3:
        return np.nan
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean().iloc[-1]
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean().iloc[-1]
    ratio = level / (100 - level)  # RS at the level
    # Tomorrow: up' = up (n-1)/n, dn' = (dn (n-1) + x) / n; solve up' / dn' = ratio for the drop x.
    x = (n - 1) * up / ratio - (n - 1) * dn
    return float(c.iloc[-1] - x) if x > 0 else np.nan


def entry_range(price: float, target: float, close: pd.Series, support: float | None = None) -> dict:
    """The ideal range to buy in: {"low", "high", "status", "tone", "note", "pullback", "sma200"}."""
    c = close.dropna().astype(float)
    sma200 = float(c.rolling(200).mean().iloc[-1]) if len(c) >= 200 else np.nan
    pull = rsi_pullback_price(c)
    if not (_ok(target) and _ok(price)):
        return {"low": np.nan, "high": np.nan, "status": "No target", "tone": "neu", "pullback": pull,
                "sma200": sma200, "note": "Not enough valuation data for a target, so no entry range."}
    high = target / (1 + MARGIN)
    floor = high * (1 - RANGE_DEPTH)
    cands = [x for x in (sma200, support) if _ok(x) and floor <= x < high]
    low = max(cands) if cands else floor
    if price <= high and price >= low:
        status, tone = "In the range now", "pos"
        note = (f"At today's price there is {target / price - 1:.0%} upside to the target, more than the {MARGIN:.0%} "
                "margin of safety.")
    elif price > high:
        status, tone = f"Wait for {high / price - 1:.0%}", "neu"
        note = (f"Today's price leaves only {target / price - 1:+.0%} to the target. The range starts "
                f"{1 - high / price:.0%} lower.")
    else:
        status, tone = "Below the range", "neg"
        note = ("The price has fallen under the range's floor (its 200-day average or support). Cheap can get "
                "cheaper: check what broke before buying.")
    if _ok(sma200) and price < sma200:
        note += " It is also under its 200-day average, a downtrend."
    return {"low": float(low), "high": float(high), "status": status, "tone": tone, "note": note, "pullback": pull,
            "sma200": sma200}
