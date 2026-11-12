"""Portfolio threat level: one weighted 0-100 score from seven warning signs, shown as LOW / MEDIUM / HIGH.

It's a rule-of-thumb checklist (like a security system's threat score), not a tested forecast. Each sign adds up to
its weight in points; the total sets the level. The same function feeds the Portfolio banner and the daily alerts.

| Sign                                                    | Max points |
| ------------------------------------------------------- | ---------- |
| Drop from the portfolio's 1-year peak (5% -> 0, 20% -> full) | 20     |
| Today's loss worse than the normal daily range (95% VaR) | 15        |
| One stock too big (25% -> 0, 50% -> full)                | 15        |
| One sector too big (40% -> 0, 70% -> full)               | 10        |
| A holding reports earnings within 3 days (by weight)     | 10        |
| SPY below its 200-day average                            | 10        |
| VIX above 25                                             | 10        |
| Holdings closed below their own 200-day average (by weight) | 10     |
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import risk

LEVELS = ((50, "HIGH"), (25, "MEDIUM"), (0, "LOW"))
VIX_HIGH = 25.0
EARNINGS_DAYS = 3
TREND_DAYS = 200


@dataclass
class Threat:
    score: float
    level: str
    signs: list[dict] = field(default_factory=list)  # {name, points, max, detail}

    @property
    def triggered(self) -> list[dict]:
        return [s for s in self.signs if s["points"] > 0.5]


def _ramp(x: float, lo: float, hi: float) -> float:
    """0 at ``lo`` or below, 1 at ``hi`` or above, linear between."""
    if not np.isfinite(x):
        return 0.0
    return float(np.clip((x - lo) / (hi - lo), 0, 1))


def level_of(score: float) -> str:
    return next(name for cut, name in LEVELS if score >= cut)


def portfolio_returns(prices: pd.DataFrame, weights: pd.Series, days: int = 252) -> pd.Series:
    """Daily returns of today's mix held over the last ``days`` sessions."""
    cols = [s for s in weights.index if s in prices]
    if not cols:
        return pd.Series(dtype=float)
    w = weights.reindex(cols).fillna(0)
    w = w / w.sum() if w.sum() > 0 else w
    r = prices[cols].ffill().pct_change(fill_method=None).iloc[-days - 1:].iloc[1:].fillna(0)
    return r @ w


def assess(prices: pd.DataFrame, weights: pd.Series, sectors: pd.Series | None = None,
           earnings: dict | None = None, vix: float = np.nan, market: str = "SPY",
           today: pd.Timestamp | None = None) -> Threat:
    """``prices``: daily closes (columns = holdings, plus ``market``). ``weights``: current value weights.
    ``sectors``: {symbol: sector}. ``earnings``: {symbol: next earnings Timestamp}. ``vix``: latest VIX close."""
    weights = weights[weights > 0].astype(float)
    weights = weights / weights.sum() if weights.sum() > 0 else weights
    today = pd.Timestamp(today or pd.Timestamp.now()).tz_localize(None).normalize()
    signs = []

    def add(name, frac, weight, detail):
        signs.append({"name": name, "points": round(weight * frac, 1), "max": weight, "detail": detail})

    port = portfolio_returns(prices, weights)
    if len(port) > 20:
        dd = float(risk.drawdown_series(port).iloc[-1])
        add("Drop from peak", _ramp(-dd, 0.05, 0.20), 20, f"{max(0.0, -dd):.1%} below its 1-year high")
        var95 = risk.historical_var(port.iloc[:-1], 0.95)
        last = float(port.iloc[-1])
        add("Loss beyond normal range", 1.0 if np.isfinite(var95) and -last > var95 else 0.0, 15,
            f"last day {last:+.2%} vs a normal worst day of -{var95:.2%} (95% VaR)")
    else:
        add("Drop from peak", 0, 20, "not enough price history")
        add("Loss beyond normal range", 0, 15, "not enough price history")

    if len(weights):
        top, top_w = weights.idxmax(), float(weights.max())
        add("One stock too big", _ramp(top_w, 0.25, 0.50), 15, f"{top} is {top_w:.0%} of the portfolio")
    else:
        add("One stock too big", 0, 15, "no holdings")

    if sectors is not None and len(weights):
        by_sec = weights.groupby(pd.Series(sectors).reindex(weights.index).fillna("Other / ETF")).sum()
        big = by_sec.drop("Other / ETF", errors="ignore")
        if len(big):
            add("One sector too big", _ramp(float(big.max()), 0.40, 0.70), 10, f"{big.idxmax()} is {big.max():.0%}")
        else:
            add("One sector too big", 0, 10, "no sector data")
    else:
        add("One sector too big", 0, 10, "no sector data")

    soon = {}
    for s, d in (earnings or {}).items():
        if s in weights.index and d is not None and not pd.isna(d):
            days = (pd.Timestamp(d).tz_localize(None).normalize() - today).days
            if 0 <= days <= EARNINGS_DAYS:
                soon[s] = days
    w_soon = float(weights.reindex(list(soon)).sum()) if soon else 0.0
    add("Earnings within 3 days", _ramp(w_soon, 0.0, 0.20), 10,
        ", ".join(f"{s} in {d} day{'s' if d != 1 else ''}" if d else f"{s} today" for s, d in soon.items())
        or "none of your holdings")

    m = prices[market].dropna() if market in prices else pd.Series(dtype=float)
    if len(m) > TREND_DAYS:
        sma = float(m.iloc[-TREND_DAYS:].mean())
        gap = float(m.iloc[-1]) / sma - 1
        add("SPY below 200-day", 1.0 if gap < 0 else 0.0, 10, f"SPY is {gap:+.1%} vs its 200-day average")
    else:
        add("SPY below 200-day", 0, 10, "SPY history unavailable")

    add("VIX above 25", 1.0 if np.isfinite(vix) and vix > VIX_HIGH else 0.0, 10,
        f"VIX {vix:.1f}" if np.isfinite(vix) else "VIX unavailable")

    below = []
    for s in weights.index:
        c = prices[s].dropna() if s in prices else pd.Series(dtype=float)
        if len(c) > TREND_DAYS and c.iloc[-1] < c.iloc[-TREND_DAYS:].mean():
            below.append(s)
    w_below = float(weights.reindex(below).sum()) if below else 0.0
    add("Holdings below their 200-day", _ramp(w_below, 0.0, 0.50), 10,
        (", ".join(below) + f" ({w_below:.0%} of the portfolio)") if below else "none")

    score = round(sum(s["points"] for s in signs), 1)
    return Threat(score, level_of(score), signs)


def next_earnings(info_rows: pd.DataFrame) -> dict:
    """{symbol: next earnings date} from Yahoo ``info`` rows (``earningsTimestamp``/``earningsTimestampStart``)."""
    out: dict = {}
    now = pd.Timestamp.now() - pd.Timedelta(days=1)
    for s in info_rows.index:
        cands = []
        for col in ("earningsTimestampStart", "earningsTimestamp", "earningsTimestampEnd"):
            v = info_rows[col].get(s) if col in info_rows else None
            try:
                if v is not None and not pd.isna(v):
                    cands.append(pd.Timestamp(float(v), unit="s"))
            except (TypeError, ValueError):
                pass
        future = [d for d in cands if d >= now]
        if future:
            out[s] = min(future)
    return out
