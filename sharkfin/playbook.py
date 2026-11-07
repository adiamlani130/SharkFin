"""The Strategy Playbook: SharkFin's two researched strategies, Dive Zone (swing, days) and Tech Breakout Rider
(trend, weeks to months), and how they combine.

The Nov 2026 growth lab (``growth_lab.py``) replayed both on point-in-time data: the stocks that were actually in
the S&P 500 on each date, 0.1% cost per side, through Nov 6 2026 (so the Oct-Nov 2026 tech selloff is in). Their
daily returns since 2006 ship with the app (``research_data/growth_returns.csv``), so the page needs no download.
The picking window is 2006 - Oct 2021; Oct 2021 - Nov 2026 is the out-of-sample grade. Sharpe ratios are after
T-bills.

The TQQQ Day + Night pair left the playbook in Nov 2026: SharkFin is aimed at mid-to-long-term growth investing,
and a day-trading edge of 0.2-0.3% a trade that needs a check every 30 minutes doesn't fit it. Its code stays in
``day_night.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import walkforward

DATA = Path(__file__).with_name("research_data") / "growth_returns.csv"
PICK = ("2006-01-03", "2021-10-12")
GRADE = ("2021-10-13", "2026-11-06")

LD, BR = "Dive Zone", "Tech Breakout Rider"
COLUMNS = {LD: "dive_zone", BR: "tech_breakout_rider", "S&P 500 (SPY)": "spy", "Nasdaq-100 (QQQ)": "qqq"}
WEIGHTS = {LD: 0.7, BR: 0.3}
COLORS = {LD: "#2dd4a3", BR: "#4ea8ff", "Both (70 / 30)": "#f5a524", "S&P 500 (SPY)": "#8b95a7",
          "Nasdaq-100 (QQQ)": "#5f6b7d"}

# Graded on Oct 13 2021 - Nov 6 2026 (out of sample; trade stats from the lab's own trade lists).
FACTS = {
    LD: {"return": 0.276, "sharpe": 1.13, "worst": -0.225, "win": 0.64, "edge": 0.015, "avg_win": 0.054,
         "avg_loss": -0.055, "payoff": 0.99, "pf": 1.74, "trades_yr": 98, "hold": "5 days", "y2022": -0.065,
         "nov2026": -0.204, "older": "16.2% a year in 2006-12, worst drop 18%, while SPY lost half in 2008",
         "stress": "18.8% a year, Sharpe 0.77, with fills 0.25% worse on every buy and sell",
         "before_crash": "34.1% a year, Sharpe 1.43, worst drop 18% (to Oct 12 2026)"},
    BR: {"return": 0.289, "sharpe": 0.95, "worst": -0.306, "win": 0.48, "edge": 0.111, "avg_win": 0.36,
         "avg_loss": -0.118, "payoff": 3.0, "pf": 2.80, "trades_yr": 29, "hold": "about 3 months", "y2022": -0.262,
         "nov2026": -0.133, "older": "4.7% a year in 2006-12",
         "stress": "8.6% a year without its 5 best stocks (SNDK, STX, NVDA, PLTR, MU)",
         "before_crash": "33.2% a year, Sharpe 1.07 (to Oct 12 2026)"},
    "S&P 500 (SPY)": {"return": 0.125, "sharpe": 0.56, "worst": -0.245, "y2022": -0.182, "nov2026": -0.055},
    "Nasdaq-100 (QQQ)": {"return": 0.135, "sharpe": 0.50, "worst": -0.351, "y2022": -0.326, "nov2026": -0.121},
    "Both (70 / 30)": {"return": 0.290, "sharpe": 1.20, "worst": -0.197, "y2022": -0.125},
}


def load() -> pd.DataFrame:
    """Daily returns since 2006 (columns as in ``COLUMNS``, plus the daily T-bill rate ``tbill``)."""
    return pd.read_csv(DATA, index_col=0, parse_dates=True)


def sleeve(d: pd.DataFrame, name: str) -> pd.Series:
    return d[COLUMNS.get(name, name)]


def mix(d: pd.DataFrame, weights: dict, start=None, end=None) -> pd.Series:
    """Daily returns of a mix rebalanced to ``weights`` at the start of each month."""
    names = [k for k, w in weights.items() if w > 0]
    X = pd.DataFrame({k: sleeve(d, k) for k in names}).loc[start:end].dropna()
    w = np.array([weights[k] for k in names], float)
    out = []
    for _, g in X.groupby(X.index.to_period("M")):
        v = w.copy()
        for row in g.to_numpy():
            out.append(v @ (1 + row) / v.sum() - 1)
            v = v * (1 + row)
    return pd.Series(out, index=X.index, dtype=float)


def stats(r: pd.Series, rf: pd.Series) -> dict:
    """Return per year, Sharpe after T-bills, worst drop, volatility and the 2022 return."""
    r = r.dropna()
    if len(r) < 20:
        return {}
    e = (1 + r).cumprod()
    yrs = len(r) / 252
    in22 = r.index.year == 2022
    return {"Return per year": float(e.iloc[-1] ** (1 / yrs) - 1),
            "Sharpe": float((r - rf.reindex(r.index).fillna(0)).mean() / r.std() * np.sqrt(252)),
            "Worst drop": float((e / e.cummax() - 1).min()), "Volatility": float(r.std() * np.sqrt(252)),
            "2022": float((1 + r[in22]).prod() - 1) if in22.any() else np.nan,
            "Total return": float(e.iloc[-1] - 1)}


def table(d: pd.DataFrame, series: dict, start=GRADE[0], end=GRADE[1]) -> pd.DataFrame:
    rows = {k: stats(v.loc[start:end], d["tbill"]) for k, v in series.items()}
    return pd.DataFrame(rows).T


def yearly(series: dict) -> pd.DataFrame:
    """Calendar-year returns of each series."""
    return pd.DataFrame({k: (1 + v.dropna()).groupby(v.dropna().index.year).prod() - 1 for k, v in series.items()})


def growth(series: dict, start=GRADE[0], end=None, amount: float = 10_000) -> pd.DataFrame:
    """What ``amount`` became in each series, from ``start``."""
    return pd.DataFrame({k: amount * (1 + v.loc[start:end].fillna(0)).cumprod() for k, v in series.items()})


def drawdowns(series: dict, start=GRADE[0], end=None) -> pd.DataFrame:
    g = growth(series, start, end, 1.0)
    return g / g.cummax() - 1


def split(amount: float, weights: dict = WEIGHTS) -> dict:
    """How ``amount`` divides across the strategies, and the size of one position in each."""
    from . import breakout_rider, leader_dip

    tot = sum(weights.values()) or 1.0
    out = {}
    for k, w in weights.items():
        sl = amount * w / tot
        per = {LD: sl / leader_dip.SLOTS, BR: sl / breakout_rider.SLOTS}.get(k, sl)
        out[k] = {"weight": w / tot, "sleeve": sl, "position": per}
    return out


def best_weights(d: pd.DataFrame, names=(LD, BR), step: float = 0.1, start=PICK[0], end=PICK[1]) -> dict:
    """The weights (in ``step`` increments) with the highest Sharpe on the picking window."""
    X = pd.DataFrame({k: sleeve(d, k) for k in names}).loc[start:end].dropna()
    rf = d["tbill"].reindex(X.index)
    k = int(round(1 / step))
    best, best_w = -np.inf, None
    for combo in _grid(len(names), k):
        w = np.array(combo) / k
        r = X.to_numpy() @ w
        s = (r - rf.to_numpy()).mean() / r.std() * np.sqrt(252) if r.std() > 0 else -np.inf
        if s > best:
            best, best_w = s, w
    return dict(zip(names, best_w))


def _grid(n: int, k: int):
    if n == 1:
        yield (k,)
        return
    for i in range(k + 1):
        for rest in _grid(n - 1, k - i):
            yield (i, *rest)


def correlations(d: pd.DataFrame, names=(LD, BR, "S&P 500 (SPY)"), start=GRADE[0], end=GRADE[1]) -> pd.DataFrame:
    return pd.DataFrame({k: sleeve(d, k) for k in names}).loc[start:end].corr()


def walk_forward_mix(d: pd.DataFrame, names=(LD, BR), step: float = 0.1) -> dict:
    """The mix with its weights re-picked every year on the three years before it (the best Sharpe), then held
    for that year."""
    X = pd.DataFrame({k: sleeve(d, k) for k in names}).dropna()
    pieces, rows = [], []
    for f in walkforward.folds(X.index):
        w = best_weights(walkforward.cut(d, f.train_end), names, step, f.train_start, f.train_end)
        r = mix(walkforward.cut(d, f.test_end), w, f.test_start, f.test_end)
        pieces.append(r)
        e = (1 + r).cumprod()
        rows.append({"Picked on": f"{f.train_start:%b %Y} - {f.train_end:%b %Y}",
                     "Used in": f"{f.test_start:%b %Y} - {f.test_end:%b %Y}",
                     **{k: float(w[k]) for k in names}, "Return": float(e.iloc[-1] - 1),
                     "Sharpe": walkforward.sharpe(r, d["tbill"])})
    r = pd.concat(pieces).sort_index()
    return {"returns": r, "folds": pd.DataFrame(rows), "stats": stats(r, d["tbill"])}
