"""Sliding-window walk-forward testing: how every SharkFin backtest is graded.

History is split into folds. In each fold a strategy's settings are picked on a trailing training window
(``TRAIN_YEARS``), then run once, untouched, on the ``TEST_YEARS`` that follow a purge gap as long as the
strategy's longest hold. The windows then slide forward by the test length. Only the test windows are
reported, stitched end to end, so every day in the result was unseen when its settings were chosen.

Two rules keep later data out:
  * every run receives its data already cut at the last day it may know (``cut``): later rows don't exist
    for it, so nothing has to be trusted not to look ahead
  * a missing value may only be filled from an earlier record (``carry_forward``), and for at most
    ``STALE_DAYS`` rows; never from a later one

Settings are picked by the best after-T-bill Sharpe on the training window, averaged with the neighbouring
grid points so a stable region beats a lone spike (one lucky setting is how backtests overfit).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

TRAIN_YEARS = 3
TEST_YEARS = 1
DAYS_A_YEAR = 252
STALE_DAYS = 5
MIN_TEST_DAYS = 30


def carry_forward(x):
    """Fill gaps from the last earlier record only, for at most ``STALE_DAYS`` rows."""
    return x.ffill(limit=STALE_DAYS)


def cut(obj, end):
    """``obj`` (a DataFrame, Series, or a dict / tuple of them) keeping only rows dated on or before ``end``.
    Anything without a date index passes through unchanged."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: cut(v, end) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return tuple(cut(v, end) for v in obj)
    if isinstance(obj, (pd.DataFrame, pd.Series)) and isinstance(obj.index, pd.DatetimeIndex):
        return obj.loc[_day(obj.index) <= _day(pd.DatetimeIndex([end]))[0]]
    return obj


def _day(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Calendar day of each stamp in its own (exchange) time zone, so intraday bars cut at a whole day."""
    return (idx.tz_localize(None) if idx.tz is not None else idx).normalize()


@dataclass(frozen=True)
class Fold:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def folds(dates: pd.DatetimeIndex, train: int = TRAIN_YEARS * DAYS_A_YEAR, test: int = TEST_YEARS * DAYS_A_YEAR,
          purge: int = 0, first: int = 0) -> list[Fold]:
    """Sliding folds over ``dates``: ``train`` days to pick settings, ``purge`` days skipped, then ``test`` days
    to grade them. ``first`` is the first usable row (after indicator warm-up). A last test window shorter
    than a month is dropped."""
    dates = pd.DatetimeIndex(dates)
    out, i = [], first + train + purge
    while len(dates) - i >= MIN_TEST_DAYS:
        j = min(i + test, len(dates)) - 1
        out.append(Fold(dates[i - purge - train], dates[i - purge - 1], dates[i], dates[j]))
        i += test
    return out


def grid(**axes) -> list[dict]:
    """Every combination of the given settings, e.g. ``grid(rsi=[5, 10, 15], target=[1.0, 1.5])``."""
    keys = list(axes)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(axes[k] for k in keys))]


def sharpe(returns: pd.Series, rf: pd.Series | None = None) -> float:
    """Annualized Sharpe ratio after T-bills (``rf`` daily rates); NaN with under a month of returns."""
    r = returns.dropna()
    if len(r) < MIN_TEST_DAYS or r.std() == 0:
        return np.nan
    ex = r - (rf.reindex(r.index).fillna(0.0) if rf is not None else 0.0)
    return float(ex.mean() / r.std() * np.sqrt(DAYS_A_YEAR))


def _neighbours(points: list[dict]) -> list[list[int]]:
    """For each grid point, the points one step away along exactly one numeric setting (named choices, like a
    weight preset, have no neighbours: they must match exactly)."""
    if not points:
        return []
    numeric = {k for k in points[0] if all(isinstance(p[k], (int, float)) for p in points)}
    axes = {k: sorted({p[k] for p in points}) for k in numeric}
    out = []
    for a in points:
        out.append([j for j, b in enumerate(points)
                    if all(a[k] == b[k] for k in a if k not in numeric)
                    and sum(abs(axes[k].index(a[k]) - axes[k].index(b[k])) for k in numeric) == 1])
    return out


def pick(points: list[dict], scores: list[float]) -> int:
    """Index of the setting whose own score averaged with its neighbours' is best (stable regions win)."""
    s = np.asarray(scores, float)
    if not np.isfinite(s).any():
        return 0
    smooth = []
    for i, nb in enumerate(_neighbours(points)):
        vals = s[[i, *nb]]
        smooth.append(np.nanmean(vals) if np.isfinite(s[i]) and np.isfinite(vals).any() else -np.inf)
    return int(np.argmax(smooth))


def run(evaluate: Callable, data, points: list[dict], fold_list: list[Fold], rf: pd.Series | None = None,
        progress: Callable | None = None) -> dict:
    """Walk ``evaluate`` forward.

    ``evaluate(data_cut, settings, start)`` must return ``{"returns": daily returns from start on, "trades":
    optional trade list}``; any other Series it returns (e.g. exposure) is stitched the same way. It is always handed ``data`` cut at the last day of the window it is run on, so it
    can't see later rows. Returns the stitched test-window returns and equity, the trades taken in test
    windows, and one row per fold with the settings it chose."""
    if not fold_list:
        raise ValueError("Not enough history for a walk-forward test: it needs at least "
                         f"{TRAIN_YEARS} years to pick settings plus a month to test them.")
    pieces, trades, rows, extras = [], [], [], {}
    for n, f in enumerate(fold_list):
        train_data = cut(data, f.train_end)
        scores = []
        for p in points:
            try:
                r = evaluate(train_data, p, f.train_start)["returns"]
                scores.append(sharpe(r.loc[f.train_start:f.train_end], rf))
            except ValueError:
                scores.append(np.nan)
        best = pick(points, scores)
        res = evaluate(cut(data, f.test_end), points[best], f.test_start)
        r = res["returns"].loc[f.test_start:f.test_end]
        pieces.append(r)
        for k, v in res.items():
            if k != "returns" and isinstance(v, pd.Series):
                extras.setdefault(k, []).append(v.loc[f.test_start:f.test_end])
        if res.get("trades") is not None and len(res["trades"]):
            trades.append(res["trades"].assign(Fold=n + 1))
        eq = (1 + r).cumprod()
        rows.append({"Fold": n + 1, "Picked on": f"{f.train_start:%b %Y} - {f.train_end:%b %Y}",
                     "Tested on": f"{f.test_start:%b %Y} - {f.test_end:%b %Y}",
                     "Settings": ", ".join(f"{k} {v:g}" if isinstance(v, (int, float)) else f"{k} {v}"
                                           for k, v in points[best].items()),
                     "Train Sharpe": scores[best], "Test return": float(eq.iloc[-1] - 1) if len(eq) else np.nan,
                     "Test Sharpe": sharpe(r, rf), "Test worst drop": float((eq / eq.cummax() - 1).min()) if len(eq) else np.nan,
                     "settings": points[best]})
        if progress:
            progress((n + 1) / len(fold_list))
    returns = pd.concat(pieces).sort_index()
    returns = returns[~returns.index.duplicated(keep="first")]
    out = {k: pd.concat(v).sort_index() for k, v in extras.items()}
    out.update({"returns": returns, "equity": (1 + returns).cumprod(), "folds": pd.DataFrame(rows),
                "trades": pd.concat(trades, ignore_index=True) if trades else pd.DataFrame(),
                "stable": _stability(rows)})
    return out


def _stability(rows: list[dict]) -> float:
    """Share of folds that kept the previous fold's settings: high means the choice wasn't noise."""
    if len(rows) < 2:
        return np.nan
    same = [rows[i]["settings"] == rows[i - 1]["settings"] for i in range(1, len(rows))]
    return float(np.mean(same))
