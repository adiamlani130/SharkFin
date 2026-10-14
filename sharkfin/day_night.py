"""TQQQ Day + Night: two buy-only trades on TQQQ (3x the Nasdaq-100) that never hold at the same time.

Day leg, a noise-range breakout (flat by the close):
  * TQQQ's "normal" move by each half hour is the average of |price / that day's open - 1| at the same time of
    day over the last 14 sessions. The upper band is max(today's open, yesterday's close) x (1 + that move).
  * Every 30 minutes from 10:00 to 15:30 New York time: if TQQQ is above the upper band, buy at the next
    price. If long and TQQQ is back under the higher of the band and the session VWAP, sell. Anything still
    held sells at the 16:00 close.
Night leg, buy the weak close:
  * If TQQQ closes in the bottom 20% of the day's high-low range, buy at the close and sell at the next
    morning's open.

Each leg uses the whole sleeve. Costs: 0.02% per side. SharkFin's Oct 2026 research (1-minute Alpaca data,
settings picked on 2016-21, graded Oct 2021 - Oct 2026): day leg 20.1% a year (46% of trades won, +0.18% a
trade), night leg 12.1% a year (57% won, +0.28% a trade), together 34.6% a year with a 30% worst drop and
+19% in 2022, against 22.5% a year and an 82% crash for holding TQQQ. The two legs barely move together
(correlation 0.06). Researched on TQQQ, not QQQ: on QQQ the same pair made 12% a year.

This module replays the rules on 30-minute bars, which give the same check times, prices and VWAP as the
research's 1-minute version (each check uses the bar's close and fills at the next bar's open).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SYMBOL = "TQQQ"
K = 1.0
LOOKBACK = 14
WEAK = 0.20
COST_BPS = 2.0
BARS = 13                         # 09:30, 10:00, ..., 15:30
CHECKS = list(range(0, 12))       # bar closes at 10:00 ... 15:30
CHECK_TIMES = [f"{(600 + 30 * j) // 60}:{(600 + 30 * j) % 60:02d}" for j in CHECKS]  # each bar's closing time

DAY_RULE = ("Every 30 minutes from 10:00 to 15:30: buy if TQQQ is above its upper noise band; if long, sell once "
            "it drops back under the higher of the band and VWAP. Always flat by the close.")
NIGHT_RULE = ("At the close: if TQQQ closed in the bottom 20% of the day's range, buy at the close and sell at the "
              "next morning's open.")


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
    df = df[df["_d"].isin(full[full == BARS].index)]
    if df.empty:
        return {}
    out = {k: df.pivot_table(index="_d", columns="_s", values=k, aggfunc="last").reindex(columns=range(BARS))
           for k in ("o", "h", "l", "c", "v", "vw")}
    out["open"] = out["o"][0]
    out["close"] = out["c"][BARS - 1]
    out["high"] = out["h"].max(axis=1)
    out["low"] = out["l"].min(axis=1)
    out["prev_close"] = out["close"].shift(1)
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
            px = c[i, j]
            if pos and px < max(ub[i, j], vw[i, j]):
                r = o[i, j + 1] / e - 1 - cost
                daily[i] += r
                trades.append((days[i], CHECK_TIMES[t_in], CHECK_TIMES[j], e, o[i, j + 1], r))
                pos = False
            if not pos and px > ub[i, j]:
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


def night_leg(daily: pd.DataFrame, weak: float = WEAK, cost_bps: float = COST_BPS) -> tuple[pd.Series, pd.DataFrame]:
    """Night leg from daily bars (Open, High, Low, Close of the regular session). The return of a night held
    after day t is booked on day t+1."""
    d = daily.astype(float)
    loc = close_location(d["High"], d["Low"], d["Close"])
    on = d["Open"].shift(-1) / d["Close"] - 1 - 2 * cost_bps * 1e-4
    cond = (loc < weak).fillna(False)
    r = on.where(cond, 0.0).shift(1).fillna(0.0)
    m = cond.shift(1, fill_value=False)
    tr = pd.DataFrame({"Bought (close)": d.index[cond.to_numpy()][: int(m.sum())], "Sold (open)": r.index[m.to_numpy()],
                       "Close location": loc[cond].iloc[: int(m.sum())].to_numpy(), "Return": r[m].to_numpy()})
    return r, tr


def backtest(bars: pd.DataFrame, daily: pd.DataFrame | None = None, tbill_yields: pd.Series | None = None,
             cost_bps: float = COST_BPS) -> dict:
    """Both legs. ``bars`` are 30-minute bars (day leg and, when ``daily`` is missing, the night leg's ranges).
    ``daily`` (Open/High/Low/Close) lets the night leg run on a longer history than the intraday bars."""
    M = session_matrix(bars)
    if not M:
        raise ValueError("No complete intraday sessions to test on.")
    d_r, d_tr = day_leg(M, cost_bps=cost_bps)
    sess = pd.DataFrame({"Open": M["open"], "High": M["high"], "Low": M["low"], "Close": M["close"]})
    n_r, n_tr = night_leg(sess, cost_bps=cost_bps)
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
    if daily is not None and len(daily) > len(sess) + 60:
        ln, ltr = night_leg(daily, cost_bps=cost_bps)
        out["night_long"], out["night_long_trades"] = ln, ltr
        out["stats"]["Night (daily history)"] = leg_stats(ln, ltr, None)
    return out


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
    complete_session = len(tb) == BARS and (now is None or now.hour >= 16)
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
        px, ub, vw = float(tb["c"].loc[j]), float(band.iloc[j]), float(vwap.loc[j])
        if pos and px < max(ub, vw):
            pos = False
            events.append((CHECK_TIMES[j], "Sell", px))
        if not pos and px > ub:
            pos = True
            events.append((CHECK_TIMES[j], "Buy", px))
    nxt = next((j for j in CHECKS if j not in done_checks), None)
    hi, lo = max(float(tb["h"].max()), price), min(float(tb["l"].min()), price)
    loc = (price - lo) / (hi - lo) if hi > lo else np.nan
    cur_vwap = float(vwap.iloc[-1]) if len(vwap) else np.nan
    next_band = float(band.iloc[nxt]) if nxt is not None else np.nan
    return {"date": last_day, "prev_close": prev_close, "open": o0, "price": price, "vwap": cur_vwap,
            "band": band.rename(lambda j: CHECK_TIMES[j]), "next_check": CHECK_TIMES[nxt] if nxt is not None else None,
            "next_band": next_band, "in_trade": pos, "events": events, "high": hi, "low": lo, "close_location": loc,
            "weak_close": bool(np.isfinite(loc) and loc < WEAK), "night_trigger": lo + WEAK * (hi - lo),
            "complete": complete_session, "bars": tb}
