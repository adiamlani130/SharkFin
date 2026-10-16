"""The Strategy Playbook: SharkFin's three researched strategies and how they combine.

The research (Oct 2026) replayed each strategy on point-in-time data: Leader Dip Plus 7 and Tech Breakout Rider
on the stocks that were actually in the S&P 500 on each date, the TQQQ pair on 1-minute bars. Their daily
returns since 2016 ship with the app (``research_data/strategy_returns.csv``), so the combined plan can be
re-weighted and re-tested here without downloading anything. Settings and weights were picked on 2016 - Oct
2021 data and graded on the five years after (Oct 2021 - Oct 2026).

Mixes rebalance to their target weights at the start of each month. As in the research's combined grade, the TQQQ
sleeve earns nothing outside its trades (no interest is credited on its idle cash), so its numbers are slightly
conservative. Sharpe ratios are measured after T-bills.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import walkforward

DATA = Path(__file__).with_name("research_data") / "strategy_returns.csv"
PICK = ("2016-01-04", "2021-10-12")
GRADE = ("2021-10-13", "2026-10-12")

LD, BR, DN = "Leader Dip Plus 7", "Tech Breakout Rider", "TQQQ Day + Night"
COLUMNS = {LD: "leader_dip_plus7", BR: "tech_breakout_rider", DN: "tqqq_day_night",
           "Classic Leader Dip": "leader_dip_classic", "TQQQ day leg": "tqqq_day", "TQQQ night leg": "tqqq_night",
           "S&P 500 (SPY)": "spy", "Nasdaq-100 (QQQ)": "qqq"}
INTRADAY: set = set()  # sleeves credited T-bill interest on idle cash (none, matching the research grade)
WEIGHTS = {LD: 0.5, BR: 0.2, DN: 0.3}
COLORS = {LD: "#2dd4a3", BR: "#4ea8ff", DN: "#a78bfa", "The plan": "#f5a524", "S&P 500 (SPY)": "#8b95a7",
          "Nasdaq-100 (QQQ)": "#5f6b7d"}

# Graded on Oct 2021 - Oct 2026 in the research (trade stats from the research's own trade lists). Settings were
# picked on earlier data, so this window is out of sample: one walk-forward step. Sharpe ratios are after T-bills
# (the legs' 1.06 / 0.66 quoted earlier were before T-bills). The night leg decided on the 16:00 close, which
# can't be traded, so its numbers are somewhat optimistic; the app's own night leg decides at 15:30.
FACTS = {
    LD: {"return": 0.331, "sharpe": 1.40, "worst": -0.18, "win": 0.64, "edge": 0.017, "avg_win": 0.054,
         "avg_loss": -0.050, "payoff": 1.07, "pf": 1.92, "trades_yr": 96, "hold": "5 days", "y2022": -0.057,
         "older": "16.5% a year in 2000-12 (worst drop 20%)", "stress": "28.7% a year, Sharpe 1.20, with fills 0.25% worse"},
    BR: {"return": 0.338, "sharpe": 1.09, "worst": -0.29, "win": 0.49, "edge": 0.119, "avg_win": 0.36,
         "avg_loss": -0.115, "payoff": 3.1, "pf": 3.05, "trades_yr": 29, "hold": "about 2 months", "y2022": -0.248,
         "older": "7.3% a year in 2000-12", "stress": "about 15% a year without its 5 best stocks; nearby settings 27%"},
    DN: {"return": 0.346, "sharpe": 1.06, "worst": -0.30, "win": None, "edge": None, "trades_yr": 158, "hold": "hours / overnight",
         "y2022": 0.194, "older": "32% a year in 2016-21, when the settings were picked",
         "stress": "the edge is 0.2-0.3% a trade, so every 0.1% of extra slippage costs a third of it",
         "legs": {"Day": {"return": 0.201, "sharpe": 0.86, "worst": -0.13, "win": 0.46, "edge": 0.0018, "avg_win": 0.0139,
                          "avg_loss": -0.0085, "trades_yr": 109},
                  "Night": {"return": 0.121, "sharpe": 0.47, "worst": -0.34, "win": 0.57, "edge": 0.0028, "avg_win": 0.0207,
                            "avg_loss": -0.0210, "trades_yr": 49}}},
    "S&P 500 (SPY)": {"return": 0.139, "sharpe": 0.63, "worst": -0.25, "y2022": -0.182},
    "Nasdaq-100 (QQQ)": {"return": 0.165, "sharpe": 0.61, "worst": -0.35, "y2022": -0.326},
    "The plan": {"return": 0.354, "sharpe": 1.60, "worst": -0.18, "y2022": -0.020},
}


def load() -> pd.DataFrame:
    """Daily returns since 2016 (columns as in ``COLUMNS``, plus the daily T-bill rate ``tbill``)."""
    d = pd.read_csv(DATA, index_col=0, parse_dates=True)
    return d


def sleeve(d: pd.DataFrame, name: str) -> pd.Series:
    """One strategy's daily returns (columns in ``INTRADAY`` also earn T-bill interest on idle cash)."""
    col = COLUMNS.get(name, name)
    r = d[col]
    return r + d["tbill"].where(r.notna()) if col in INTRADAY else r


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
    """How ``amount`` divides across the sleeves, and the size of one position in each."""
    from . import breakout_rider, leader_dip

    tot = sum(weights.values()) or 1.0
    out = {}
    for k, w in weights.items():
        sl = amount * w / tot
        per = {LD: sl / leader_dip.SLOTS, BR: sl / breakout_rider.SLOTS, DN: sl}.get(k, sl)
        out[k] = {"weight": w / tot, "sleeve": sl, "position": per}
    return out


def best_weights(d: pd.DataFrame, names=(LD, BR, DN), step: float = 0.1, start=PICK[0], end=PICK[1]) -> dict:
    """The weights (in ``step`` increments) with the highest Sharpe on the picking window, as the research did
    (a plain daily-weighted blend for the search, monthly rebalancing for the grade)."""
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


def correlations(d: pd.DataFrame, names=(LD, BR, DN, "S&P 500 (SPY)"), start=GRADE[0], end=GRADE[1],
                 down_days: bool = False) -> pd.DataFrame:
    X = pd.DataFrame({k: sleeve(d, k) for k in names}).loc[start:end]
    if down_days:
        X = X[d["spy"].reindex(X.index) < -0.01]
    return X.corr()


def walk_forward_mix(d: pd.DataFrame, names=(LD, BR, DN), step: float = 0.1) -> dict:
    """The mix with its weights re-picked every year on the three years before it (the best Sharpe, as
    ``best_weights`` does), then held for that year. Only the strategies' weights are re-picked here: each
    strategy's own settings come from the research and were chosen on 2016-21."""
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
