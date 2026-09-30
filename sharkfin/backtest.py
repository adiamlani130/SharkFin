"""Rule-based strategy backtester (long/flat), no look-ahead, with costs.

Signals are computed on the close of day t and the position is applied to the
return of day t+1. Trading costs (commission + slippage, in basis points) are
charged on every change in position.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import indicators as ind
from . import risk, swing


@dataclass
class Strategy:
    name: str
    description: str
    params: dict


STRATEGIES = {
    "Buy & Hold": Strategy("Buy & Hold", "Always fully invested.", {}),
    "SMA Crossover": Strategy("SMA Crossover", "Long when the fast moving average is above the slow one.",
                              {"fast": 50, "slow": 200}),
    "RSI Mean Reversion": Strategy("RSI Mean Reversion", "Buy when RSI falls below the entry level, sell when it recovers above the exit level, only while above the 200-day trend filter.",
                                   {"entry": 30, "exit": 55, "trend_filter": True}),
    "Donchian Breakout": Strategy("Donchian Breakout", "Turtle-style: buy a new N-day high, exit on an M-day low.",
                                  {"entry": 55, "exit": 20}),
    "MACD Trend": Strategy("MACD Trend", "Long while the MACD line is above its signal line.", {}),
    "Time-Series Momentum": Strategy("Time-Series Momentum", "Long when the trailing 12-month return is positive (Moskowitz, Ooi & Pedersen 2012).",
                                     {"lookback": 252}),
    "Vol-Targeted Trend": Strategy("Vol-Targeted Trend", "200-day trend filter with position size scaled to hit a target volatility.",
                                   {"target_vol": 0.15, "sma": 200}),
    "Confluence Pullback": Strategy("Confluence Pullback",
                                    "Long-only swing system: in a market and stock uptrend, buy a pullback to the 20 EMA / "
                                    "50 SMA when price closes above the prior day's high and enough confluences line up "
                                    "(volume, RSI, MACD, OBV, room to resistance). Stop under the pullback, part off at "
                                    "T1, trail the rest under the 20 EMA.", {}),
}
TRADE_BASED = {"Confluence Pullback"}


def positions(ohlcv: pd.DataFrame, name: str, params: dict | None = None) -> pd.Series:
    p = {**STRATEGIES[name].params, **(params or {})}
    c = ohlcv["Close"]
    if name == "Buy & Hold":
        pos = pd.Series(1.0, index=c.index)
    elif name == "SMA Crossover":
        pos = (ind.sma(c, p["fast"]) > ind.sma(c, p["slow"])).astype(float)
    elif name == "RSI Mean Reversion":
        r = ind.rsi(c, 14)
        trend_ok = (c > ind.sma(c, 200)) if p.get("trend_filter") else pd.Series(True, index=c.index)
        state, out = 0.0, []
        for rv, ok in zip(r.values, trend_ok.values):
            if state == 0 and rv < p["entry"] and ok:
                state = 1.0
            elif state == 1 and (rv > p["exit"]):
                state = 0.0
            out.append(state)
        pos = pd.Series(out, index=c.index)
    elif name == "Donchian Breakout":
        hi = ohlcv["High"].rolling(p["entry"]).max().shift(1)
        lo = ohlcv["Low"].rolling(p["exit"]).min().shift(1)
        state, out = 0.0, []
        for px, h, l in zip(c.values, hi.values, lo.values):
            if state == 0 and np.isfinite(h) and px > h:
                state = 1.0
            elif state == 1 and np.isfinite(l) and px < l:
                state = 0.0
            out.append(state)
        pos = pd.Series(out, index=c.index)
    elif name == "MACD Trend":
        m = ind.macd(c)
        pos = (m["macd"] > m["signal"]).astype(float)
    elif name == "Time-Series Momentum":
        pos = (c / c.shift(p["lookback"]) - 1 > 0).astype(float)
    elif name == "Vol-Targeted Trend":
        vol = np.log(c).diff().rolling(21).std() * np.sqrt(252)
        size = (p["target_vol"] / vol).clip(upper=1.5)
        pos = (c > ind.sma(c, p["sma"])).astype(float) * size
    else:
        raise KeyError(name)
    return pos.fillna(0.0)


def run(ohlcv: pd.DataFrame, name: str, params: dict | None = None, cost_bps: float = 5.0,
        rf: float = 0.0) -> dict:
    if name in TRADE_BASED:
        params = dict(params or {})
        market = params.pop("market", None)
        return swing.backtest(ohlcv, params, cost_bps, rf, market)
    c = ohlcv["Close"]
    asset_ret = c.pct_change(fill_method=None).fillna(0.0)
    pos = positions(ohlcv, name, params)
    held = pos.shift(1).fillna(0.0)  # trade on next bar: no look-ahead
    trades = held.diff().abs().fillna(held.abs())
    # Idle cash earns the risk-free rate.
    strat_ret = held * asset_ret + (1 - held.clip(upper=1)) * rf / 252 - trades * cost_bps / 1e4
    equity = (1 + strat_ret).cumprod()
    stats = risk.summary(strat_ret, asset_ret, rf)
    stats["Exposure"] = float((held > 0).mean())
    stats["Trades"] = int((trades > 0).sum())
    return {"returns": strat_ret, "equity": equity, "position": held, "stats": stats}


def compare(ohlcv: pd.DataFrame, names=None, cost_bps: float = 5.0, rf: float = 0.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    names = names or list(STRATEGIES)
    eq, st = {}, {}
    for n in names:
        res = run(ohlcv, n, cost_bps=cost_bps, rf=rf)
        eq[n] = res["equity"]
        st[n] = res["stats"]
    return pd.DataFrame(eq), pd.DataFrame(st)
