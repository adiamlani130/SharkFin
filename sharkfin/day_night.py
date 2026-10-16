"""TQQQ Day + Night: two buy-only trades on TQQQ (3x the Nasdaq-100) that never hold at the same time.

Day leg, a noise-range breakout (flat by the close):
  * TQQQ's "normal" move by each half hour is the average of |price / that day's open - 1| at the same time of
    day over the last 14 sessions. The upper band is max(today's open, yesterday's close) x (1 + that move).
  * Every 30 minutes from 10:00 to 15:30 New York time, the line is the higher of the upper band and the
    session VWAP (the paper's trailing stop). If flat and TQQQ is above the line, buy at the next price; if
    long and TQQQ is back under it, sell. Anything still held sells at the 16:00 close. Entry and exit use
    the same line, so a check can never sell and buy back at the same price.
Night leg, buy the weak close:
  * At 15:30, if TQQQ sits in the bottom 20% of the day's high-low range so far, buy at the close
    (market-on-close orders are due by 15:50, so the decision can only use what's known by 15:30) and sell at
    the next morning's open. No trade across a half-day session.

Each leg uses the whole sleeve. Costs: 0.02% per side. SharkFin's Oct 2026 research (1-minute Alpaca data,
settings picked on 2016-21, graded Oct 2021 - Oct 2026): day leg 20.1% a year (46% of trades won, +0.18% a
trade), night leg 12.1% a year (57% won, +0.28% a trade), together 34.6% a year with a 30% worst drop and
+19% in 2022, against 22.5% a year and an 82% crash for holding TQQQ. The two legs barely move together
(correlation 0.06 over 2016-26). Researched on TQQQ, not QQQ: on QQQ the same pair made 12% a year.
The research's night leg decided on the 16:00 close itself, which can't be traded (orders are due by 15:50),
so its night numbers are somewhat optimistic; this module decides at 15:30. The research's day leg also bought
above the band alone, even under VWAP, so a check could sell and buy straight back (a 0.04% round trip for
nothing); here a buy also needs TQQQ above VWAP, which skips those trades.

This module replays the rules on 30-minute bars, which give the same check times, prices and VWAP as the
research's 1-minute version (each check uses the bar's close and fills at the next bar's open).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import walkforward

SYMBOL = "TQQQ"
K = 1.0
LOOKBACK = 14
WEAK = 0.20
COST_BPS = 2.0
BARS = 13                         # 09:30, 10:00, ..., 15:30
CHECKS = list(range(0, 12))       # bar closes at 10:00 ... 15:30
DECIDE = 11                       # the night leg decides on the bar closing at 15:30
CHECK_TIMES = [f"{(600 + 30 * j) // 60}:{(600 + 30 * j) % 60:02d}" for j in CHECKS]  # each bar's closing time

DAY_RULE = ("Every 30 minutes from 10:00 to 15:30: buy if TQQQ is above both its upper noise band and VWAP; if long, "
            "sell once it drops back under the higher of the two. Always flat by the close.")
NIGHT_RULE = ("At 15:30: if TQQQ sits in the bottom 20% of the day's range so far, buy at the close (market-on-close, "
              "due by 15:50) and sell at the next morning's open.")


def session_matrix(bars: pd.DataFrame) -> dict:
    """Day x half-hour matrices (13 regular-session bars) from 30-minute bars indexed by New York time.
    Days without all 13 bars (half days, outages) are dropped, as in the research."""
    if bars is None or bars.empty:
        return {}
    df = bars.copy()
    mins = df.index.hour * 60 + df.index.minute - 570
    df = df[(mins >= 0) & (mins < 390)]
    slot = ((df.index.hour * 60 + df.index.minute - 570) // 30).astype(int)
    day = pd.DatetimeIndex(df.index.tz_localize(None) if df.index.tz is not None else df.index).normalize()
    df = df.assign(_s=slot, _d=day)
    full = df.groupby("_d")["_s"].nunique()
    every_close = df.sort_index().groupby("_d")["c"].last()     # every session, half days included
    df = df[df["_d"].isin(full[full == BARS].index)]
    if df.empty:
        return {}
    out = {k: df.pivot_table(index="_d", columns="_s", values=k, aggfunc="last").reindex(columns=range(BARS))
           for k in ("o", "h", "l", "c", "v", "vw")}
    out["open"] = out["o"][0]
    out["close"] = out["c"][BARS - 1]
    out["high"] = out["h"].max(axis=1)
    out["low"] = out["l"].min(axis=1)
    # the real previous session's close, even when that session was a half day dropped above
    out["prev_close"] = every_close.shift(1).reindex(out["close"].index)
    # the next session's date (half days included), to stop night trades that would span a dropped session
    out["next_session"] = pd.Series(every_close.index, index=every_close.index).shift(-1).reindex(out["close"].index)
    pv = (out["vw"] * out["v"]).cumsum(axis=1)
    vv = out["v"].cumsum(axis=1)
    out["vwap"] = (pv / vv.replace(0, np.nan)).ffill(axis=1).fillna(out["c"])
    return out


def bands(M: dict, k: float = K, lookback: int = LOOKBACK) -> pd.DataFrame:
    """Upper noise band at each check (day x check), from the previous ``lookback`` days only."""
    move = (M["c"][CHECKS].div(M["open"], axis=0) - 1).abs()
    sigma = move.rolling(lookback, min_periods=lookback).mean().shift(1) * k
    base = np.maximum(M["open"], M["prev_close"])
    return sigma.mul(base, axis=0).add(base, axis=0)


def hold_after_check(long: bool, price: float, band: float, vwap: float) -> bool:
    """Whether the day leg is long after a check: it buys above the higher of the band and VWAP and sells under it.
    A missing VWAP falls back to the band."""
    line = max(band, vwap) if np.isfinite(vwap) else band
    return price >= line if long else price > line


def day_leg(M: dict, k: float = K, lookback: int = LOOKBACK, cost_bps: float = COST_BPS) -> tuple[pd.Series, pd.DataFrame]:
    """Daily return of the day leg and its trade list."""
    ub = bands(M, k, lookback).to_numpy()
    c, o, vw = M["c"].to_numpy(), M["o"].to_numpy(), M["vwap"].to_numpy()
    days = M["c"].index
    daily = np.zeros(len(days))
    trades = []
    cost = 2 * cost_bps * 1e-4
    for i in range(len(days)):
        if not np.isfinite(ub[i, 0]):
            continue
        pos, e, t_in = False, 0.0, 0
        for j in CHECKS:
            hold = hold_after_check(pos, c[i, j], ub[i, j], vw[i, j])
            if pos and not hold:
                r = o[i, j + 1] / e - 1 - cost
                daily[i] += r
                trades.append((days[i], CHECK_TIMES[t_in], CHECK_TIMES[j], e, o[i, j + 1], r))
                pos = False
            elif hold and not pos:
                pos, e, t_in = True, o[i, j + 1], j
        if pos:
            r = c[i, BARS - 1] / e - 1 - cost
            daily[i] += r
            trades.append((days[i], CHECK_TIMES[t_in], "16:00", e, c[i, BARS - 1], r))
    tr = pd.DataFrame(trades, columns=["Date", "Signal at", "Sold at", "Buy price", "Sell price", "Return"])
    return pd.Series(daily, index=days), tr


def close_location(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Where the close sits in the day's range: 0 = at the low, 1 = at the high."""
    return (close - low) / (high - low).replace(0, np.nan)


def decision_location(M: dict) -> pd.Series:
    """Where TQQQ sat in the day's range at 15:30, using only the bars up to then (0 = at the low)."""
    upto = list(range(DECIDE + 1))
    return close_location(M["h"][upto].max(axis=1), M["l"][upto].min(axis=1), M["c"][DECIDE])


def night_leg(M: dict, weak: float = WEAK, cost_bps: float = COST_BPS) -> tuple[pd.Series, pd.DataFrame]:
    """Night leg from the session matrix: decided at 15:30, bought at the 16:00 close, sold at the next session's
    open. The return of a night held after day t is booked on day t+1. A night is skipped when the next session
    isn't in the matrix (a half day or a missing day), rather than holding across it."""
    loc = decision_location(M)
    close, days = M["close"], M["close"].index
    nxt_open = M["open"].shift(-1)
    adjacent = pd.Series(days, index=days).shift(-1).eq(M["next_session"])  # the next row is the next session
    cond = (loc < weak).fillna(False) & adjacent & nxt_open.notna()
    on = nxt_open / close - 1 - 2 * cost_bps * 1e-4
    r = on.where(cond, 0.0).shift(1).fillna(0.0)
    held = cond.shift(1, fill_value=False).astype(bool)
    tr = pd.DataFrame({"Bought (close)": days[cond.to_numpy()], "Sold (open)": days[held.to_numpy()],
                       "15:30 location": loc[cond].to_numpy(), "Return": r[held].to_numpy()})
    return r, tr


def backtest(bars: pd.DataFrame, tbill_yields: pd.Series | None = None, cost_bps: float = COST_BPS,
             k: float = K, weak: float = WEAK) -> dict:
    """Both legs on 30-minute bars, with band width ``k`` and weak-close level ``weak``."""
    M = session_matrix(bars)
    if not M:
        raise ValueError("No complete intraday sessions to test on.")
    d_r, d_tr = day_leg(M, k=k, cost_bps=cost_bps)
    n_r, n_tr = night_leg(M, weak=weak, cost_bps=cost_bps)
    both = d_r + n_r
    out = {"day": d_r, "night": n_r, "both": both, "day_trades": d_tr, "night_trades": n_tr, "sessions": len(both)}
    bh = (M["close"] / M["prev_close"] - 1).fillna(0.0)
    out["hold"] = bh
    rf = None
    if tbill_yields is not None and len(tbill_yields.dropna()):
        from .swing_engine import daily_cash

        rf = pd.Series(daily_cash(pd.DatetimeIndex(both.index), tbill_yields), index=both.index)
    out["stats"] = {k: leg_stats(v, t, rf) for k, v, t in (("Day", d_r, d_tr), ("Night", n_r, n_tr), ("Day + night", both, None),
                                                          ("Hold TQQQ", bh, None))}
    return out


K_GRID = (0.8, 1.0, 1.2)
WEAK_GRID = (0.15, 0.20, 0.25)


def walk_forward(bars: pd.DataFrame, tbill_yields: pd.Series | None = None, cost_bps: float = COST_BPS,
                 progress=None) -> dict:
    """Day + Night graded out of sample: each year's band width and weak-close level are picked on the three
    years before it (see ``walkforward``), then traded on that year only. Needs about four years of
    30-minute bars."""
    M = session_matrix(bars)
    if not M:
        raise ValueError("No complete intraday sessions to test on.")
    days = M["close"].index
    points = walkforward.grid(**{"Band width": K_GRID, "Weak close below": WEAK_GRID})

    def evaluate(d, p, start):
        res = backtest(d, None, cost_bps, k=p["Band width"], weak=p["Weak close below"])
        return {"returns": res["both"].loc[start:]}

    rf = None
    if tbill_yields is not None and len(tbill_yields.dropna()):
        from .swing_engine import daily_cash

        rf = pd.Series(daily_cash(pd.DatetimeIndex(days), tbill_yields), index=days)
    wf = walkforward.run(evaluate, bars, points, walkforward.folds(days, purge=1, first=LOOKBACK + 1), rf, progress)
    r = wf["returns"]
    hold = (M["close"] / M["prev_close"] - 1).reindex(r.index).fillna(0.0)
    hold.iloc[0] = 0.0
    wf["hold_equity"] = (1 + hold).cumprod()
    wf["stats"] = {"Day + night": leg_stats(r, None, rf), "Hold TQQQ": leg_stats(hold, None, rf)}
    return wf


def leg_stats(r: pd.Series, trades: pd.DataFrame | None = None, rf: pd.Series | None = None) -> dict:
    """Return per year, Sharpe, worst drop and trade stats for a daily return series (flat days are 0)."""
    r = r.fillna(0.0)
    if len(r) < 2:
        return {}
    eq = (1 + r).cumprod()
    years = len(r) / 252
    ex = r - (rf.reindex(r.index).fillna(0.0) if rf is not None else 0.0)
    out = {"Return per year": float(eq.iloc[-1] ** (1 / years) - 1) if eq.iloc[-1] > 0 else -1.0,
           "Total return": float(eq.iloc[-1] - 1), "Worst drop": float((eq / eq.cummax() - 1).min()),
           "Sharpe": float(ex.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan,
           "Days invested": float((r != 0).mean()), "Years": years}
    if trades is not None and len(trades):
        t = trades["Return"].to_numpy()
        w, lo = t[t > 0], t[t <= 0]
        out.update({"Trades": int(len(t)), "Trades per year": len(t) / years, "Win rate": float(len(w) / len(t)),
                    "Avg trade": float(t.mean()), "Avg win": float(w.mean()) if len(w) else np.nan,
                    "Avg loss": float(lo.mean()) if len(lo) else np.nan,
                    "Profit factor": float(w.sum() / -lo.sum()) if len(lo) and lo.sum() < 0 else np.nan})
    return out


def today(bars: pd.DataFrame, last_price: float | None = None, now: pd.Timestamp | None = None) -> dict:
    """Where today's session stands for both legs: the band, VWAP, the last check and the close location.
    ``bars`` must hold the previous 14+ full sessions and today's bars so far."""
    if bars is None or bars.empty:
        return {}
    b = bars.copy()
    day = pd.DatetimeIndex(b.index.tz_localize(None) if b.index.tz is not None else b.index).normalize()
    last_day = day.max()
    hist = session_matrix(b[day < last_day])
    if not hist or len(hist["c"]) < LOOKBACK:
        return {}
    tb = b[day == last_day]
    slot = ((tb.index.hour * 60 + tb.index.minute - 570) // 30).astype(int)
    tb = tb.assign(_s=slot).groupby("_s").last()
    after_close = now is None or now.tz_localize(None).normalize() > last_day or now.hour >= 16
    complete_session = len(tb) == BARS and after_close
    in_session = now is not None and not after_close and now.tz_localize(None).normalize() == last_day \
        and (now.hour, now.minute) >= (9, 30)
    if not in_session:
        last_price = None  # outside 09:30-16:00 the latest trade is an extended-hours print, not this session
    prev_close = float(hist["close"].iloc[-1])
    o0 = float(tb["o"].iloc[0])
    move = (hist["c"][CHECKS].div(hist["open"], axis=0) - 1).abs().iloc[-LOOKBACK:].mean() * K
    base = max(o0, prev_close)
    band = base * (1 + move)
    pv = (tb["vw"] * tb["v"]).cumsum()
    vwap = pv / tb["v"].cumsum().replace(0, np.nan)
    price = float(last_price) if last_price and np.isfinite(last_price) else float(tb["c"].iloc[-1])
    done_checks = [j for j in CHECKS if j in tb.index and (j + 1 in tb.index or complete_session)]
    # replay today's checks so far
    pos, events = False, []
    for j in done_checks:
        px = float(tb["c"].loc[j])
        hold = hold_after_check(pos, px, float(band.iloc[j]), float(vwap.loc[j]))
        if hold != pos:
            events.append((CHECK_TIMES[j], "Buy" if hold else "Sell", px))
            pos = hold
    nxt = next((j for j in CHECKS if j not in done_checks), None)
    decided = DECIDE in done_checks
    if decided:  # the night leg's call was made on the 15:30 bar: range and price up to then only
        upto = tb.loc[tb.index <= DECIDE]
        hi, lo, at = float(upto["h"].max()), float(upto["l"].min()), float(tb["c"].loc[DECIDE])
    else:
        hi, lo, at = max(float(tb["h"].max()), price), min(float(tb["l"].min()), price), price
    loc = (at - lo) / (hi - lo) if hi > lo else np.nan
    cur_vwap = float(vwap.iloc[-1]) if len(vwap) else np.nan
    next_band = float(band.iloc[nxt]) if nxt is not None else np.nan
    return {"date": last_day, "prev_close": prev_close, "open": o0, "price": price, "vwap": cur_vwap,
            "band": band.rename(lambda j: CHECK_TIMES[j]), "next_check": CHECK_TIMES[nxt] if nxt is not None else None,
            "next_band": next_band, "in_trade": pos, "events": events, "high": hi, "low": lo, "close_location": loc,
            "weak_close": bool(np.isfinite(loc) and loc < WEAK), "night_trigger": lo + WEAK * (hi - lo),
            "night_decided": decided, "complete": complete_session, "bars": tb}
