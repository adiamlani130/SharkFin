"""Build-your-own strategy engine for the Strategy Lab.

A strategy is a list of entry conditions (combined with ALL or ANY), a list of
exit conditions (any one triggers), and optional risk exits (stop loss, take
profit, trailing stop, maximum days held). Each condition compares an
indicator with a number or another indicator, e.g. "RSI(14) is below 30" or
"SMA(50) crosses above SMA(200)".

Execution is long/flat with no look-ahead: signals use the close of day t and
fill at the open of day t+1. Stops and targets fill intraday at their level, or
at the open when the price gaps through them. Trading costs are charged on
every fill and idle cash earns the risk-free rate.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from . import indicators as ind
from . import risk


@dataclass(frozen=True)
class Indicator:
    label: str          # short name used in sentences, "{n}" is replaced with the length
    default_n: int | None
    kind: str           # "price" (drawn on the price chart), "osc" (0-100), "pct", "ratio", "macd", "volume"
    fn: Callable
    help: str
    needs_market: bool = False


def _close(d):
    return d["Close"]


INDICATORS: dict[str, Indicator] = {
    "Price": Indicator("price", None, "price", lambda d, n, m: _close(d), "The daily closing price."),
    "SMA": Indicator("SMA({n})", 50, "price", lambda d, n, m: ind.sma(_close(d), n),
                     "Simple moving average: the average close of the last N days. Smooths out noise to show the trend."),
    "EMA": Indicator("EMA({n})", 20, "price", lambda d, n, m: ind.ema(_close(d), n),
                     "Exponential moving average: like the SMA but weights recent days more, so it turns faster."),
    "Bollinger upper": Indicator("upper Bollinger band({n})", 20, "price",
                                 lambda d, n, m: ind.bollinger(_close(d), n)["upper"],
                                 "N-day average plus two standard deviations. Price above it is stretched to the upside."),
    "Bollinger middle": Indicator("middle Bollinger band({n})", 20, "price",
                                  lambda d, n, m: ind.bollinger(_close(d), n)["mid"], "The N-day simple average."),
    "Bollinger lower": Indicator("lower Bollinger band({n})", 20, "price",
                                 lambda d, n, m: ind.bollinger(_close(d), n)["lower"],
                                 "N-day average minus two standard deviations. Price below it is stretched to the downside."),
    "N-day high": Indicator("{n}-day high", 55, "price", lambda d, n, m: d["High"].rolling(n).max().shift(1),
                            "The highest price of the previous N days. Closing above it is a breakout."),
    "N-day low": Indicator("{n}-day low", 20, "price", lambda d, n, m: d["Low"].rolling(n).min().shift(1),
                           "The lowest price of the previous N days. Closing below it is a breakdown."),
    "RSI": Indicator("RSI({n})", 14, "osc", lambda d, n, m: ind.rsi(_close(d), n),
                     "Relative Strength Index, 0-100. Below 30 is usually called oversold, above 70 overbought."),
    "Stochastic %K": Indicator("Stochastic({n})", 14, "osc",
                               lambda d, n, m: ind.stochastic(d["High"], d["Low"], _close(d), n)["k"],
                               "Where the close sits in the last N days' range, 0-100. Below 20 = near the bottom of the range."),
    "ADX": Indicator("ADX({n})", 14, "osc", lambda d, n, m: ind.adx(d["High"], d["Low"], _close(d), n)["adx"],
                     "Trend strength, 0-100, regardless of direction. Above 25 is usually a trending market."),
    "MACD line": Indicator("MACD line", None, "macd", lambda d, n, m: ind.macd(_close(d))["macd"],
                           "12-day EMA minus 26-day EMA. Above zero means the short-term trend is up."),
    "MACD signal": Indicator("MACD signal line", None, "macd", lambda d, n, m: ind.macd(_close(d))["signal"],
                             "9-day EMA of the MACD line. The MACD crossing above it is a classic buy signal."),
    "MACD histogram": Indicator("MACD histogram", None, "macd", lambda d, n, m: ind.macd(_close(d))["hist"],
                                "MACD line minus its signal line. Positive and growing = momentum building."),
    "Return over N days %": Indicator("{n}-day return (%)", 63, "pct",
                                      lambda d, n, m: (_close(d) / _close(d).shift(n) - 1) * 100,
                                      "Percent change over the last N days. 252 days is about a year."),
    "Distance from SMA %": Indicator("distance from SMA({n}) (%)", 200, "pct",
                                     lambda d, n, m: (_close(d) / ind.sma(_close(d), n) - 1) * 100,
                                     "How far price is above (+) or below (−) its N-day average, in percent."),
    "ATR %": Indicator("ATR({n}) (% of price)", 14, "pct",
                       lambda d, n, m: ind.atr(d["High"], d["Low"], _close(d), n) / _close(d) * 100,
                       "Average daily range as a percent of price. Higher = more volatile."),
    "Relative volume": Indicator("volume vs {n}-day average (x)", 20, "ratio",
                                 lambda d, n, m: d["Volume"] / d["Volume"].rolling(n).mean(),
                                 "Today's volume divided by the N-day average. 2 means twice the usual volume."),
    "OBV trend": Indicator("OBV vs its {n}-day average (%)", 20, "pct",
                           lambda d, n, m: _obv_gap(d, n),
                           "On-balance volume compared with its own N-day average. Positive = more volume on up days."),
    "Market vs SMA %": Indicator("S&P 500 distance from SMA({n}) (%)", 200, "pct",
                                 lambda d, n, m: _market_gap(d, n, m),
                                 "How far the S&P 500 (SPY) is above its N-day average. Above zero = market uptrend.",
                                 needs_market=True),
}
VALUE = "Value"
OPS = ["is above", "is below", "crosses above", "crosses below", "is rising", "is falling"]
UNARY = {"is rising", "is falling"}


def _obv_gap(d, n):
    o = ind.obv(_close(d), d["Volume"])
    avg = o.rolling(n).mean()
    scale = d["Volume"].rolling(n).mean() * n
    return (o - avg) / scale.replace(0, np.nan) * 100


def _market_gap(d, n, m):
    if m is None or len(m) == 0:
        return pd.Series(np.nan, index=d.index)
    m = m.reindex(d.index).ffill()
    return (m / ind.sma(m, n) - 1) * 100


def label(key: str, n: int | None) -> str:
    i = INDICATORS[key]
    return i.label.replace("{n}", str(int(n))) if "{n}" in i.label else i.label


def series(ohlcv: pd.DataFrame, key: str, n: int | None, market: pd.Series | None = None) -> pd.Series:
    i = INDICATORS[key]
    return i.fn(ohlcv, int(n) if n else i.default_n, market).astype(float)


def _fmt_value(v: float) -> str:
    return f"{v:g}"


def describe(c: dict) -> str:
    """Plain-English sentence for one condition."""
    lhs = label(c["ind"], c.get("n"))
    if c["op"] in UNARY:
        return f"{lhs} {c['op']} (vs {int(c.get('lookback') or 5)} days ago)"
    rhs = _fmt_value(c.get("value", 0)) if c.get("rhs", VALUE) == VALUE else label(c["rhs"], c.get("rn"))
    return f"{lhs} {c['op']} {rhs}"


def describe_strategy(s: dict) -> tuple[str, str]:
    joiner = " and " if s.get("logic", "ALL") == "ALL" else " or "
    buy = joiner.join(describe(c) for c in s.get("entry", [])) or "never"
    exits = [describe(c) for c in s.get("exit", [])]
    if s.get("stop"):
        exits.append(f"price falls {s['stop']:g}% below the entry")
    if s.get("trail"):
        exits.append(f"price falls {s['trail']:g}% from its highest close since entry")
    if s.get("target"):
        exits.append(f"price rises {s['target']:g}% above the entry")
    if s.get("max_days"):
        exits.append(f"{int(s['max_days'])} trading days have passed")
    sell = " or ".join(exits) if exits else "never (holds until the end)"
    if s.get("market_filter"):
        buy += ", and only while the S&P 500 is above its 200-day average"
    return buy, sell


def condition_mask(ohlcv: pd.DataFrame, c: dict, market: pd.Series | None = None) -> pd.Series:
    lhs = series(ohlcv, c["ind"], c.get("n"), market)
    if c["op"] in UNARY:
        k = int(c.get("lookback") or 5)
        out = lhs > lhs.shift(k) if c["op"] == "is rising" else lhs < lhs.shift(k)
        return out.fillna(False)
    if c.get("rhs", VALUE) == VALUE:
        rhs = pd.Series(float(c.get("value", 0)), index=ohlcv.index)
    else:
        rhs = series(ohlcv, c["rhs"], c.get("rn"), market)
    above, below = lhs > rhs, lhs < rhs
    op = c["op"]
    if op == "is above":
        out = above
    elif op == "is below":
        out = below
    elif op == "crosses above":
        out = above & (lhs.shift(1) <= rhs.shift(1))
    elif op == "crosses below":
        out = below & (lhs.shift(1) >= rhs.shift(1))
    else:
        raise ValueError(op)
    return out.fillna(False)


def signals(ohlcv: pd.DataFrame, s: dict, market: pd.Series | None = None) -> tuple[pd.Series, pd.Series]:
    idx = ohlcv.index
    ent = [condition_mask(ohlcv, c, market) for c in s.get("entry", [])]
    if ent:
        entry = pd.concat(ent, axis=1).all(axis=1) if s.get("logic", "ALL") == "ALL" else pd.concat(ent, axis=1).any(axis=1)
    else:
        entry = pd.Series(False, index=idx)
    if s.get("market_filter") and market is not None and len(market):
        m = market.reindex(idx).ffill()
        entry &= (m > ind.sma(m, 200)).fillna(False)
    ex = [condition_mask(ohlcv, c, market) for c in s.get("exit", [])]
    exit_ = pd.concat(ex, axis=1).any(axis=1) if ex else pd.Series(False, index=idx)
    return entry.astype(bool), exit_.astype(bool)


def warmup(s: dict) -> int:
    """Bars needed before every indicator in the strategy has a value."""
    ns = [200 if s.get("market_filter") else 0]
    for c in s.get("entry", []) + s.get("exit", []):
        for k, n in ((c["ind"], c.get("n")), (c.get("rhs"), c.get("rn"))):
            if k and k != VALUE:
                ns.append(int(n or INDICATORS[k].default_n or 35))
    return max(ns) + 1


def run(ohlcv: pd.DataFrame, s: dict, cost_bps: float = 5.0, rf: float = 0.0,
        market: pd.Series | None = None, start: pd.Timestamp | None = None) -> dict:
    """Simulate the strategy. Returns daily returns, equity, trades, stats and the
    buy-and-hold comparison over exactly the same dates."""
    d = ohlcv.dropna(subset=["Open", "High", "Low", "Close"])
    entry, exit_ = signals(d, s, market)
    first = max(warmup(s), 1)
    if start is not None:
        first = max(first, int(d.index.searchsorted(start)))
    if len(d) - first < 30:
        raise ValueError("Not enough history after the indicators warm up.")
    o, h, l, c = (d[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
    ent, exs = entry.to_numpy(), exit_.to_numpy()
    cost = cost_bps / 1e4
    daily_rf = rf / 252
    stop_pct, tgt_pct, trail_pct = (float(s.get(k) or 0) / 100 for k in ("stop", "target", "trail"))
    max_days = int(s.get("max_days") or 0)

    cash, shares = 1.0, 0.0
    pend_in = pend_out = False
    entry_px = peak = 0.0
    entry_i = 0
    pend_reason = ""
    eq = np.empty(len(d) - first)
    trades = []

    def close_trade(i, px, reason):
        nonlocal cash, shares
        cash = shares * px * (1 - cost)
        trades.append({"Entry date": d.index[entry_i], "Entry": entry_px, "Exit date": d.index[i], "Exit": px,
                       "Return": px * (1 - cost) / (entry_px * (1 + cost)) - 1, "Days": i - entry_i, "Exit reason": reason})
        shares = 0.0

    for j, i in enumerate(range(first, len(d))):
        cash *= 1 + daily_rf
        if shares == 0 and pend_in:
            entry_px, entry_i, peak = o[i], i, o[i]
            shares, cash = cash * (1 - cost) / o[i], 0.0
            pend_in = False
        if shares > 0:
            fixed = entry_px * (1 - stop_pct) if stop_pct else -np.inf
            trailing = peak * (1 - trail_pct) if trail_pct else -np.inf
            stop = max(fixed, trailing)
            stop_reason = "Trailing stop" if trailing > fixed else "Stop loss"
            tgt = entry_px * (1 + tgt_pct) if tgt_pct else np.inf
            if pend_out and i > entry_i:
                close_trade(i, o[i], pend_reason)
            elif o[i] <= stop and i > entry_i:
                close_trade(i, o[i], stop_reason)
            elif l[i] <= stop:
                close_trade(i, stop, stop_reason)
            elif o[i] >= tgt and i > entry_i:
                close_trade(i, o[i], "Take profit")
            elif h[i] >= tgt:
                close_trade(i, tgt, "Take profit")
            pend_out = False
        if shares > 0:
            peak = max(peak, c[i])
            if exs[i]:
                pend_out, pend_reason = True, "Sell rule"
            elif max_days and i - entry_i >= max_days:
                pend_out, pend_reason = True, "Time limit"
        elif ent[i] and i < len(d) - 1:
            pend_in = True
        eq[j] = cash + shares * c[i]

    idx = d.index[first:]
    equity = pd.Series(eq, index=idx)
    rets = equity.pct_change().fillna(equity.iloc[0] - 1)
    bh = d["Close"].iloc[first:] / d["Close"].iloc[first]
    bh_rets = bh.pct_change().fillna(0.0)
    open_trade = None
    if shares > 0:
        open_trade = {"Entry date": d.index[entry_i], "Entry": entry_px, "Return": c[-1] / entry_px - 1,
                      "Days": len(d) - 1 - entry_i}
    tdf = pd.DataFrame(trades, columns=["Entry date", "Entry", "Exit date", "Exit", "Return", "Days", "Exit reason"])
    held = pd.Series(0.0, index=idx)
    for t in trades + ([{**open_trade, "Exit date": idx[-1]}] if open_trade else []):
        held.loc[t["Entry date"]:t["Exit date"]] = 1.0
    stats = summarize(rets, bh_rets, tdf, rf, float(held.mean()))
    return {"returns": rets, "equity": equity, "bh_equity": bh, "bh_returns": bh_rets, "trades": tdf,
            "open_trade": open_trade, "stats": stats, "entry": entry, "exit": exit_, "in_market": held}


def summarize(rets: pd.Series, bh_rets: pd.Series, trades: pd.DataFrame, rf: float, exposure: float) -> dict:
    years = max(len(rets) / 252, 1e-9)
    total = float((1 + rets).prod() - 1)
    bh_total = float((1 + bh_rets).prod() - 1)
    wins = trades["Return"][trades["Return"] > 0] if not trades.empty else pd.Series(dtype=float)
    losses = trades["Return"][trades["Return"] <= 0] if not trades.empty else pd.Series(dtype=float)
    gross_loss = -losses.sum()
    return {
        "Total return": total, "Buy & hold return": bh_total,
        "Return per year": (1 + total) ** (1 / years) - 1, "Buy & hold per year": (1 + bh_total) ** (1 / years) - 1,
        "Worst drop": risk.max_drawdown(rets), "Buy & hold worst drop": risk.max_drawdown(bh_rets),
        "Sharpe": risk.sharpe_ratio(rets, rf), "Buy & hold Sharpe": risk.sharpe_ratio(bh_rets, rf),
        "Sortino": risk.sortino_ratio(rets, rf), "Volatility": risk.annualized_vol(rets),
        "Trades": int(len(trades)), "Win rate": float(len(wins) / len(trades)) if len(trades) else np.nan,
        "Avg win": float(wins.mean()) if len(wins) else np.nan, "Avg loss": float(losses.mean()) if len(losses) else np.nan,
        "Profit factor": float(wins.sum() / gross_loss) if gross_loss > 0 else (np.inf if len(wins) else np.nan),
        "Avg days held": float(trades["Days"].mean()) if len(trades) else np.nan,
        "Time in market": exposure, "Years": years,
    }


# ---------------------------------------------------------------------------
# Ready-made strategies (all editable in the builder)
# ---------------------------------------------------------------------------

def C(ind_: str, op: str, rhs: str = VALUE, value: float = 0.0, n: int | None = None, rn: int | None = None,
      lookback: int = 5) -> dict:
    return {"ind": ind_, "n": n if n is not None else INDICATORS[ind_].default_n, "op": op, "rhs": rhs,
            "rn": rn if rn is not None else (INDICATORS[rhs].default_n if rhs != VALUE else None),
            "value": float(value), "lookback": lookback}


TEMPLATES: dict[str, dict] = {
    "Golden cross": {
        "about": "The classic long-term trend signal: own the stock while the 50-day average is above the 200-day.",
        "logic": "ALL", "entry": [C("SMA", "crosses above", "SMA", n=50, rn=200)],
        "exit": [C("SMA", "crosses below", "SMA", n=50, rn=200)]},
    "Above the 200-day": {
        "about": "The simplest trend filter there is. Historically it gave up some return but avoided most of the big crashes.",
        "logic": "ALL", "entry": [C("Price", "is above", "SMA", rn=200)], "exit": [C("Price", "is below", "SMA", rn=200)]},
    "RSI dip in an uptrend": {
        "about": "Buy short, sharp pullbacks in stocks that are still in a long-term uptrend, sell into the bounce.",
        "logic": "ALL", "entry": [C("RSI", "is below", value=35), C("Price", "is above", "SMA", rn=200)],
        "exit": [C("RSI", "is above", value=55)], "stop": 10.0, "max_days": 30},
    "MACD momentum": {
        "about": "Ride momentum when the MACD turns up, but only while the long-term trend is up.",
        "logic": "ALL", "entry": [C("MACD line", "crosses above", "MACD signal"), C("Price", "is above", "SMA", rn=200)],
        "exit": [C("MACD line", "crosses below", "MACD signal")], "stop": 8.0},
    "55-day breakout": {
        "about": "The Turtle traders' rule: buy when price makes a new 55-day high, sell on a new 20-day low.",
        "logic": "ALL", "entry": [C("Price", "is above", "N-day high", rn=55)],
        "exit": [C("Price", "is below", "N-day low", rn=20)]},
    "Bollinger bounce": {
        "about": "Buy when price snaps back inside the lower Bollinger band in an uptrend; sell at the middle band.",
        "logic": "ALL", "entry": [C("Price", "crosses above", "Bollinger lower", rn=20), C("Price", "is above", "SMA", rn=200)],
        "exit": [C("Price", "is above", "Bollinger middle", rn=20)], "stop": 8.0, "max_days": 30},
    "Pullback in an uptrend": {
        "about": "Wait for the 50-day to be above the 200-day, then buy when the stochastic turns up from oversold.",
        "logic": "ALL", "entry": [C("SMA", "is above", "SMA", n=50, rn=200), C("Stochastic %K", "crosses above", value=20)],
        "exit": [C("Stochastic %K", "is above", value=80)], "stop": 7.0, "max_days": 30},
    "Volume breakout": {
        "about": "A new 20-day high on at least 1.5x normal volume, exiting when price loses the 20-day EMA.",
        "logic": "ALL", "entry": [C("Price", "is above", "N-day high", rn=20), C("Relative volume", "is above", value=1.5)],
        "exit": [C("Price", "is below", "EMA", rn=20)], "stop": 8.0},
    "12-month momentum": {
        "about": "Hold the stock while it is up over the past year (time-series momentum, Moskowitz, Ooi & Pedersen 2012).",
        "logic": "ALL", "entry": [C("Return over N days %", "is above", value=0, n=252)],
        "exit": [C("Return over N days %", "is below", value=0, n=252)]},
    "Start from scratch": {
        "about": "One simple rule to get you going. Change it, add more, and watch the results update.",
        "logic": "ALL", "entry": [C("Price", "is above", "EMA", rn=50)], "exit": [C("Price", "is below", "EMA", rn=50)]},
}


def template(name: str) -> dict:
    t = copy.deepcopy(TEMPLATES[name])
    t.setdefault("stop", 0.0)
    t.setdefault("target", 0.0)
    t.setdefault("trail", 0.0)
    t.setdefault("max_days", 0)
    t.setdefault("market_filter", False)
    return t


def compare_templates(ohlcv: pd.DataFrame, names: list[str], cost_bps: float, rf: float,
                      market: pd.Series | None = None) -> dict:
    """Run several templates over the same dates (after the longest warm-up)."""
    tpls = {n: template(n) for n in names}
    start = ohlcv.index[min(max(warmup(t) for t in tpls.values()), len(ohlcv) - 31)]
    return {n: run(ohlcv, t, cost_bps, rf, market, start=start) for n, t in tpls.items()}
