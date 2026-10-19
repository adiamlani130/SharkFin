"""NQ strategy lab: short-term day and swing strategies on the Nasdaq-100, graded walk-forward.

Every strategy here is a function ``evaluate(data, settings, start)`` that ``walkforward.run`` can grade, so it
gets the same treatment as the rest of SharkFin's backtests: settings are picked on a trailing 3-year window,
then run once on the following year, and the data handed to each run is already cut at the last day it may know.

What each strategy may know, and when:
  * daily prices: a decision made at a session's close is filled at the next session's open
  * VIX, VIX9D, VIX3M: a swing decision may use that day's close (it is filled at the next open); a day
    trade only knows the prior session's close
  * GEX (SqueezeMetrics' daily S&P 500 dealer gamma estimate): always the prior session's value, and only
    as a percentile against the 252 sessions before it, never against the whole history
  * 5-minute bars: a decision made at a bar's close is filled at the next bar's open; day trades are flat by
    the 15:55 bar (one strategy exits on the closing print)
  * a stop and a target hit inside the same bar count as the stop (the worse outcome)

Prices: QQQ stands in for NQ. Both track the Nasdaq-100, QQQ has clean split/dividend-adjusted history and real
5-minute bars back to 2016, and NQ futures earn the index's excess return over T-bills. So a strategy's daily
return is its position times QQQ's return over T-bills, plus the T-bill rate the margin cash earns.
Costs: ``COST`` per unit traded each side (about 1-2 NQ ticks plus commission).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from sharkfin import walkforward as wf

COST = 0.0001          # 1 basis point per side
BARS = 78              # 5-minute bars in a full regular session, 09:30 ... 15:55
LAST_ENTRY = 75        # no new day-trade entries decided after the 15:45 bar
FLAT_BAR = 76          # day trades decide to be flat at the 15:50 bar's close and fill at 15:55
GEX_LOOKBACK = 252


# --------------------------------------------------------------------------------------------- data loading


def load(folder: str | Path) -> dict:
    """Daily and intraday inputs from CSV files in ``folder`` (see ``fetch`` for how they are made)."""
    f = Path(folder)

    def daily(name):
        d = pd.read_csv(f / f"{name}.csv", index_col=0, parse_dates=True)
        d.index = pd.DatetimeIndex(d.index).normalize()
        return d[~d.index.duplicated(keep="last")].sort_index()

    q = daily("QQQ")
    adj = q["Adj Close"] / q["Close"]
    px = pd.DataFrame({"o": q["Open"] * adj, "h": q["High"] * adj, "l": q["Low"] * adj, "c": q["Adj Close"],
                       "raw": 1 / adj})  # raw = multiply an adjusted price by this to get the traded price
    days = px.index
    out = {"px": px}
    for k, name in (("vix", "VIX"), ("vix9d", "VIX9D"), ("vix3m", "VIX3M"), ("vvix", "VVIX")):
        try:
            out[k] = wf.carry_forward(daily(name)["Close"].reindex(days))
        except FileNotFoundError:
            pass
    rf = daily("IRX")["Close"].reindex(days)
    out["rf"] = (wf.carry_forward(rf) / 100 / wf.DAYS_A_YEAR).fillna(0.0)
    try:
        g = pd.read_csv(f / "DIX.csv", index_col=0, parse_dates=True)["gex"]
        out["gex"] = wf.carry_forward(g.reindex(days))
        out["gex_pct"] = trailing_pct(out["gex"])  # trailing only, so cutting it later changes nothing before
    except FileNotFoundError:
        pass
    p = f / "qqq5.csv"
    if p.exists():
        out.update(intraday_frames(pd.read_csv(p, index_col=0, parse_dates=True)))
    return out


def fetch(folder: str | Path) -> None:
    """Download everything ``load`` reads into ``folder``: Yahoo daily QQQ, VIX family and T-bills, Alpaca
    QQQ 5-minute bars since 2016 (needs Alpaca keys; slow on the free tier's rate limit). SqueezeMetrics'
    GEX history (https://squeezemetrics.com/monitor/static/DIX.csv) has to be saved there by hand as DIX.csv."""
    import time

    import requests
    import yfinance as yf

    from sharkfin import data as sd

    f = Path(folder)
    f.mkdir(parents=True, exist_ok=True)
    for sym in ("QQQ", "^VIX", "^VIX9D", "^VIX3M", "^VVIX", "^IRX"):
        h = yf.Ticker(sym).history(period="max", interval="1d", auto_adjust=False)
        h.index = pd.DatetimeIndex(h.index).tz_localize(None).normalize()
        h.to_csv(f / f"{sym.lstrip('^')}.csv")
    keys = sd.alpaca_keys()
    if not keys:
        return
    hdr = {"APCA-API-KEY-ID": keys[0], "APCA-API-SECRET-KEY": keys[1]}
    rows, tok = [], None
    while True:
        prm = {"timeframe": "5Min", "start": "2016-01-01T00:00:00Z", "limit": 10000, "feed": "sip",
               "adjustment": "all", **({"page_token": tok} if tok else {})}
        for k in range(12):
            r = requests.get(f"{sd.ALPACA_DATA}/stocks/QQQ/bars", params=prm, headers=hdr, timeout=60)
            if r.status_code == 200:
                break
            time.sleep(5 * (k + 1))
        r.raise_for_status()
        j = r.json()
        rows += j.get("bars") or []
        tok = j.get("next_page_token")
        if not tok:
            break
    b = pd.DataFrame(rows)
    b["t"] = pd.to_datetime(b["t"], utc=True).dt.tz_convert("America/New_York")
    b = b.set_index("t").sort_index()[["o", "h", "l", "c", "v", "vw"]].between_time("09:30", "15:55")
    b.index = b.index.tz_localize(None)
    b.to_csv(f / "qqq5.csv")


def intraday_frames(bars: pd.DataFrame) -> dict:
    """5-minute bars (o, h, l, c, v, vw indexed by New York bar-start time) as day x bar-number frames.
    Days with fewer than a full session of bars (half days, outages) are left out."""
    b = bars.copy()
    idx = pd.DatetimeIndex(b.index)
    b["day"] = idx.normalize()
    b["n"] = ((idx.hour - 9) * 60 + idx.minute - 30) // 5
    b = b[(b["n"] >= 0) & (b["n"] < BARS)]
    full = b.groupby("day")["n"].nunique()
    b = b[b["day"].isin(full.index[full >= BARS - 2])]
    out = {}
    for k in ("o", "h", "l", "c", "v", "vw"):
        m = b.pivot_table(index="day", columns="n", values=k, aggfunc="last").reindex(columns=range(BARS))
        out["i" + k] = m.ffill(axis=1) if k != "v" else m.fillna(0.0)
    for k in ("io", "ih", "il"):
        out[k] = out[k].fillna(out["ic"])
    return out


# --------------------------------------------------------------------------------------------- indicators


def ema(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(span=n, adjust=False, min_periods=n).mean()


def rsi(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr(px: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = px["c"].shift(1)
    tr = pd.concat([px["h"] - px["l"], (px["h"] - pc).abs(), (px["l"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def trailing_pct(x: pd.Series, n: int = GEX_LOOKBACK) -> pd.Series:
    """Where each value sits among the ``n`` values before it (0 = lowest, 1 = highest)."""
    a = x.to_numpy(float)
    out = np.full(len(a), np.nan)
    for i in range(n, len(a)):
        w = a[i - n:i]
        w = w[np.isfinite(w)]
        if np.isfinite(a[i]) and len(w) > n // 2:
            out[i] = (w < a[i]).mean()
    return pd.Series(out, index=x.index)


def known(d: dict, key: str, idx: pd.DatetimeIndex) -> pd.Series:
    """A daily input as it was known before each session in ``idx`` opened (the prior session's value)."""
    s = d.get(key)
    if s is None:
        return pd.Series(np.nan, index=idx)
    return s.shift(1).reindex(idx)


def gex_pct(d: dict, idx: pd.DatetimeIndex) -> pd.Series:
    """Prior session's GEX as a trailing-year percentile: what is known at the open, and at the close, of
    each session in ``idx`` (a session's GEX is published after it ends)."""
    s = d.get("gex_pct")
    if s is None:
        return pd.Series(np.nan, index=idx)
    return s.shift(1).reindex(idx)


# --------------------------------------------------------------------------------------------- swing engine


def swing_returns(d: dict, pos: pd.Series, start) -> pd.Series:
    """Daily returns of holding ``pos`` (decided at each close, filled at the next open)."""
    px, rf = d["px"], d["rf"]
    pos = pos.reindex(px.index).fillna(0.0).astype(float)
    overnight = px["o"] / px["c"].shift(1) - 1
    day = px["c"] / px["o"] - 1
    held_night, held_day = pos.shift(2).fillna(0.0), pos.shift(1).fillna(0.0)
    r = held_night * overnight.fillna(0.0) + held_day * day.fillna(0.0)
    r = r - held_day * rf + rf - (held_day - held_night).abs() * COST
    return r.loc[start:]


def hold_until(entry: pd.Series, exit_: pd.Series, max_hold: int = 0) -> pd.Series:
    """1 from an entry day until an exit day (or ``max_hold`` days), else 0. Both are known at that close."""
    e, x = entry.fillna(False).to_numpy(bool), exit_.fillna(False).to_numpy(bool)
    out, on, held = np.zeros(len(e)), False, 0
    for i in range(len(e)):
        if on:
            held += 1
            if x[i] or (max_hold and held >= max_hold):
                on = False
        if not on and e[i]:
            on, held = True, 0
        out[i] = 1.0 if on else 0.0
    return pd.Series(out, index=entry.index)


def _sw(fn):
    def evaluate(d, p, start):
        return {"returns": swing_returns(d, fn(d, p), start)}
    evaluate.__name__ = fn.__name__
    evaluate.signal = fn
    return evaluate


@_sw
def ema_cross(d, p):
    c = d["px"]["c"]
    up = ema(c, p["fast"]) > ema(c, p["slow"])
    return up.astype(float) - ((~up).astype(float) if p["short"] else 0.0)


@_sw
def ema_pullback(d, p):
    c = d["px"]["c"]
    trend = c > ema(c, p["trend"])
    f = ema(c, p["fast"])
    return hold_until(trend & (c < f * (1 - p["dip"])), c > f, p["hold"])


@_sw
def rsi2_dip(d, p):
    c = d["px"]["c"]
    r = rsi(c, 2)
    ok = (c > ema(c, 200)) if p["trend"] else pd.Series(True, index=c.index)
    return hold_until(ok & (r < p["entry"]), r > p["exit"], 10)


@_sw
def ibs_reversion(d, p):
    px = d["px"]
    ibs = (px["c"] - px["l"]) / (px["h"] - px["l"]).replace(0, np.nan)
    ok = (px["c"] > ema(px["c"], 200)) if p["trend"] else pd.Series(True, index=px.index)
    return hold_until(ok & (ibs < p["entry"]), (ibs > p["exit"]) | (px["c"] > px["h"].shift(1)), 5)


@_sw
def vix_term(d, p):
    idx = d["px"].index
    ratio = (d["vix"] / d["vix3m"]).reindex(idx)  # today's close: the decision is filled tomorrow
    calm = ratio < p["th"]
    return calm.astype(float) - ((ratio > p["short_above"]).astype(float) if p["short_above"] < 9 else 0.0)


@_sw
def vix_trend(d, p):
    v = d["vix"].reindex(d["px"].index)
    pos = (v < ema(v, p["n"])).astype(float)
    if p["cap"] < 99:
        pos = pos.where(v < p["cap"], 0.0)
    return pos


@_sw
def vix_spike_buy(d, p):
    v = d["vix"].reindex(d["px"].index)
    spike = v / ema(v, 10) - 1 > p["k"]
    return hold_until(spike, pd.Series(False, index=v.index), p["hold"])


@_sw
def vix9d_inversion(d, p):
    idx = d["px"].index
    r = (d["vix9d"] / d["vix"]).reindex(idx)
    return hold_until(r > p["th"], r < 1.0, p["hold"])


@_sw
def gex_regime(d, p):
    c = d["px"]["c"]
    g = gex_pct(d, c.index)
    pos = (g > p["q"]).astype(float)
    if p["trend"]:
        pos = pos * (c > ema(c, p["trend"])).astype(float)
    return pos.where(g.notna(), 0.0)


@_sw
def gex_switch(d, p):
    """High gamma: ride the trend. Low gamma: only buy sharp dips (dealer hedging overshoots both ways)."""
    c = d["px"]["c"]
    g = gex_pct(d, c.index)
    trend = (c > ema(c, p["trend"])).astype(float)
    dip = hold_until(rsi(c, 2) < p["entry"], rsi(c, 2) > 70, 10)
    return (trend.where(g > p["q"], dip)).where(g.notna(), 0.0)


@_sw
def donchian(d, p):
    px = d["px"]
    hi, lo = px["h"].rolling(p["n"]).max().shift(1), px["l"].rolling(p["m"]).min().shift(1)
    pos = hold_until(px["c"] > hi, px["c"] < lo)
    if p["vix_cap"] < 99:
        pos = pos.where(d["vix"].reindex(px.index) < p["vix_cap"], 0.0)
    return pos


@_sw
def vol_target_trend(d, p):
    c = d["px"]["c"]
    vol = c.pct_change().rolling(20).std() * math.sqrt(wf.DAYS_A_YEAR)
    size = (p["target"] / vol).clip(upper=2.0)
    return (size * (c > ema(c, p["trend"])).astype(float)).fillna(0.0)


@_sw
def macd_trend(d, p):
    c = d["px"]["c"]
    m = ema(c, p["fast"]) - ema(c, p["slow"])
    hist = m - ema(m, 9)
    pos = (hist > 0).astype(float)
    return pos * (c > ema(c, 200)).astype(float) if p["filter"] else pos


@_sw
def regime_vote(d, p):
    """One vote each: price over its EMA, VIX under VIX3M, VIX under its 20-day EMA, GEX above its 30th
    percentile. Long when at least ``k`` agree (or sized by the share agreeing)."""
    c = d["px"]["c"]
    v, v3 = d["vix"].reindex(c.index), d["vix3m"].reindex(c.index)
    g = gex_pct(d, c.index)
    votes = pd.concat([(c > ema(c, p["trend"])), (v / v3 < 1.0), (v < ema(v, 20)), (g > 0.3)], axis=1).astype(float)
    n = votes.sum(axis=1)
    pos = (n / 4) if p["k"] == 0 else (n >= p["k"]).astype(float)
    return pos.where(g.notna(), 0.0)


@_sw
def dip_in_calm(d, p):
    """RSI(2) dip buying only when the volatility curve is in contango and gamma is not deeply negative."""
    c = d["px"]["c"]
    v, v3 = d["vix"].reindex(c.index), d["vix3m"].reindex(c.index)
    g = gex_pct(d, c.index)
    ok = (v / v3 < p["term"]) & (g > p["q"])
    r = rsi(c, 2)
    return hold_until(ok & (r < p["entry"]), r > 65, 7).where(g.notna(), 0.0)


def _regime(d, idx, name):
    """Swing regime filters, known at each close."""
    v = d["vix"].reindex(idx)
    if name == "none":
        return pd.Series(True, index=idx)
    if name == "contango":
        return v / d["vix3m"].reindex(idx) < 0.95
    if name == "vix_high":
        return v > 20
    if name == "vix_low":
        return v < 20
    g = gex_pct(d, idx)
    return {"gex_low": g < 0.35, "gex_high": g > 0.5}[name]


@_sw
def ibs_filtered(d, p):
    px = d["px"]
    ibs = (px["c"] - px["l"]) / (px["h"] - px["l"]).replace(0, np.nan)
    ok = _regime(d, px.index, p["filter"]) & (px["c"] > ema(px["c"], p["trend"]) if p["trend"] else True)
    return hold_until(ok & (ibs < p["entry"]), (ibs > 0.7) | (px["c"] > px["h"].shift(1)), 5)


@_sw
def ema_vix_sized(d, p):
    """EMA trend, full size when VIX is under ``calm`` and ``rest`` size when it is above."""
    c = d["px"]["c"]
    v = d["vix"].reindex(c.index)
    size = pd.Series(np.where(v < p["calm"], 1.0, p["rest"]), index=c.index)
    return size * (ema(c, p["fast"]) > ema(c, p["slow"])).astype(float)


def night_returns(d: dict, sig: pd.Series, start) -> pd.Series:
    """Hold only overnight: ``sig`` decided at a close is bought on the next close and sold the open after."""
    px, rf = d["px"], d["rf"]
    sig = sig.reindex(px.index).fillna(0.0).astype(float)
    held = sig.shift(2).fillna(0.0)
    on = (px["o"] / px["c"].shift(1) - 1).fillna(0.0)
    return (held * (on - rf) + rf - held * 2 * COST).loc[start:]


def overnight_hold(d, p, start):
    return {"returns": night_returns(d, overnight_hold.signal(d, p), start)}


def _night_signal(d, p):
    c = d["px"]["c"]
    ok = _regime(d, c.index, p["filter"])
    if p["trend"]:
        ok = ok & (c > ema(c, p["trend"]))
    return ok.astype(float)


overnight_hold.signal = _night_signal


@_sw
def buy_hold(d, p):
    return pd.Series(1.0, index=d["px"].index)


# --------------------------------------------------------------------------------------------- day-trade engine


@dataclass
class Day:
    """The intraday arrays a day-trade strategy sees, all trimmed to the same sessions."""
    days: pd.DatetimeIndex
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    vwap: np.ndarray
    prev_c: np.ndarray   # prior session's close (adjusted), from the daily table
    prev_h: np.ndarray
    prev_l: np.ndarray
    atr: np.ndarray      # daily ATR(14) as of the prior close
    raw: np.ndarray      # adjusted -> traded price factor
    vix: np.ndarray      # prior close
    vix_ratio: np.ndarray
    gex: np.ndarray      # prior session's GEX percentile


def day_view(d: dict) -> Day:
    days = d["ic"].index.intersection(d["px"].index)
    hit = d.get("_day")
    if hit is not None and hit.days.equals(days):  # a cache made from this very (already cut) data
        return hit
    px = d["px"]
    g = lambda k: d[k].loc[days].to_numpy(float)
    v, vw = d["iv"].loc[days].to_numpy(float), d["ivw"].loc[days].to_numpy(float)
    cv = np.cumsum(v, axis=1)
    vwap = np.where(cv > 0, np.cumsum(np.nan_to_num(vw) * v, axis=1) / np.where(cv > 0, cv, 1), g("ic"))
    a = atr(px).shift(1)
    vix = known(d, "vix", px.index)
    ratio = (d["vix"] / d["vix3m"]).shift(1).reindex(px.index) if "vix3m" in d else vix * np.nan
    # the prior regular session's close, high and low, from the same 5-minute bars the trades use
    sess = pd.DataFrame({"c": d["ic"].iloc[:, -1], "h": d["ih"].max(axis=1), "l": d["il"].min(axis=1)})
    prev = sess.shift(1).loc[days]
    out = Day(days, g("io"), g("ih"), g("il"), g("ic"), vwap,
              prev["c"].to_numpy(float), prev["h"].to_numpy(float), prev["l"].to_numpy(float),
              a.loc[days].to_numpy(float),
              px["raw"].loc[days].to_numpy(float), vix.loc[days].to_numpy(float),
              ratio.loc[days].to_numpy(float), gex_pct(d, px.index).loc[days].to_numpy(float))
    d["_day"] = out
    return out


TRACE: list | None = None  # tests set this to a list to record every day-trade decision


def run_positions(dv: Day, pos: np.ndarray) -> np.ndarray:
    """Daily return of bar-level positions ``pos`` (days x bars, decided at each bar's close and filled at
    the next bar's open). Positions must be 0 from ``FLAT_BAR`` on so every day ends flat."""
    pos = np.nan_to_num(pos)
    pos[:, FLAT_BAR:] = 0.0
    if TRACE is not None:
        TRACE.append(("positions", pos.copy()))
    held_gap = np.zeros_like(pos)
    held_body = np.zeros_like(pos)
    held_body[:, 1:] = pos[:, :-1]
    held_gap[:, 2:] = pos[:, :-2]
    gap = np.zeros_like(pos)
    gap[:, 1:] = dv.o[:, 1:] / dv.c[:, :-1] - 1
    body = dv.c / dv.o - 1
    trades = np.abs(np.diff(np.concatenate([np.zeros((len(pos), 1)), pos], axis=1), axis=1)).sum(axis=1)
    return (held_gap * gap + held_body * body).sum(axis=1) - trades * COST


def bracket(dv: Day, side: np.ndarray, entry_bar: np.ndarray, stop: np.ndarray, target: np.ndarray,
            exit_bar: int = FLAT_BAR + 1, close_exit: bool = False) -> np.ndarray:
    """One bracket trade a day: enter ``side`` (+1/-1, 0 = no trade) at the open of ``entry_bar``, exit at the
    first bar whose range touches ``stop`` or ``target`` (stop first when both), else at ``exit_bar``'s open
    (or that bar's close with ``close_exit``). Returns each day's return net of costs."""
    n = len(side)
    out = np.zeros(n)
    side = np.asarray(side, float)
    entry_bar = np.asarray(entry_bar)
    if TRACE is not None:
        TRACE.append(("bracket", np.where(side != 0, entry_bar, BARS), side.copy(),
                      np.asarray(stop, float).copy(), np.asarray(target, float).copy()))
    stop, target = np.broadcast_to(np.asarray(stop, float), (n,)), np.broadcast_to(np.asarray(target, float), (n,))
    live = (side != 0) & (entry_bar < exit_bar)
    rows = np.arange(n)
    e = np.clip(entry_bar, 0, BARS - 1).astype(int)
    px_in = np.where(live, dv.o[rows, e], np.nan)
    px_out = np.full(n, np.nan)
    last = exit_bar + 1 if close_exit else exit_bar
    open_ = live.copy()
    for j in range(int(e[live].min()) if live.any() else BARS, last):
        on = open_ & (j >= entry_bar)
        if not on.any():
            continue
        hi, lo, op = dv.h[:, j], dv.l[:, j], dv.o[:, j]
        hit_stop = on & np.where(side > 0, lo <= stop, hi >= stop)
        hit_tgt = on & ~hit_stop & np.where(side > 0, hi >= target, lo <= target)
        px_out = np.where(hit_stop, np.where(side > 0, np.minimum(stop, op), np.maximum(stop, op)), px_out)  # gaps fill worse
        px_out = np.where(hit_tgt, np.where(side > 0, np.maximum(target, op), np.minimum(target, op)), px_out)
        open_ &= ~(hit_stop | hit_tgt)
    final = dv.c[:, exit_bar] if close_exit else dv.o[:, min(exit_bar, BARS - 1)]
    px_out = np.where(open_, final, px_out)
    out = np.where(live, side * (px_out / px_in - 1) - 2 * COST, 0.0)
    return np.nan_to_num(out)


def first_true(mask: np.ndarray) -> np.ndarray:
    """Index of each row's first True (``BARS`` when none)."""
    any_ = mask.any(axis=1)
    return np.where(any_, mask.argmax(axis=1), BARS)


def _filter(dv: Day, name: str) -> np.ndarray:
    """Day filters, all known before the open: GEX regime, VIX level, volatility curve shape."""
    g, v, r = dv.gex, dv.vix, dv.vix_ratio
    return {"none": np.ones(len(g), bool),
            "gex_low": g < 0.35, "gex_high": g > 0.5,
            "vix_high": v > 20, "vix_low": v < 20,
            "backwardation": r > 1.0, "contango": r < 0.9}[name]


def _day(fn):
    def evaluate(d, p, start):
        dv = day_view(d)
        r = pd.Series(fn(dv, p), index=dv.days)
        rf = d["rf"].reindex(dv.days).fillna(0.0)
        return {"returns": (r + rf).loc[start:]}
    evaluate.__name__ = fn.__name__
    evaluate.day_fn = fn
    return evaluate


@_day
def opening_range_breakout(dv: Day, p):
    k = p["minutes"] // 5
    hi, lo = dv.h[:, :k].max(axis=1), dv.l[:, :k].min(axis=1)
    c = dv.c.copy()
    c[:, :k] = np.nan
    up, dn = first_true(c > hi[:, None]), first_true(c < lo[:, None])
    side = np.where(up < dn, 1, np.where(dn < up, -1, 0)) * _filter(dv, p["filter"])
    sig = np.minimum(up, dn)
    side = np.where(sig <= LAST_ENTRY, side, 0)
    rng = hi - lo
    stop = np.where(side > 0, hi - rng * p["stop"], lo + rng * p["stop"])
    tgt = np.where(side > 0, hi + rng * p["target"], lo - rng * p["target"]) if p["target"] else \
        np.where(side > 0, np.inf, -np.inf)
    return bracket(dv, side, sig + 1, stop, tgt)


@_day
def gap_fade(dv: Day, p):
    gap = dv.o[:, 0] / dv.prev_c - 1
    side = np.where(gap > p["gap"], -1, np.where(gap < -p["gap"], 1, 0)) * _filter(dv, p["filter"])
    stop = dv.o[:, 0] * (1 + gap * p["stop"])  # the gap extending by ``stop`` of itself
    return bracket(dv, side, np.ones(len(side), int), stop, dv.prev_c)


@_day
def gap_go(dv: Day, p):
    gap = dv.o[:, 0] / dv.prev_c - 1
    # wait for the first bar to confirm the gap's direction
    conf = np.sign(dv.c[:, 0] - dv.o[:, 0]) == np.sign(gap)
    side = np.where(gap > p["gap"], 1, np.where(gap < -p["gap"], -1, 0)) * conf * _filter(dv, p["filter"])
    stop = np.where(side > 0, dv.l[:, 0], dv.h[:, 0])
    tgt = np.where(side > 0, np.inf, -np.inf)
    return bracket(dv, side, np.ones(len(side), int), stop, tgt)


def _ema_rows(x: np.ndarray, n: int) -> np.ndarray:
    a = 2 / (n + 1)
    out = np.empty_like(x)
    out[:, 0] = x[:, 0]
    for j in range(1, x.shape[1]):
        out[:, j] = a * x[:, j] + (1 - a) * out[:, j - 1]
    return out


@_day
def vwap_ema_trend(dv: Day, p):
    """Long above VWAP with the fast 5-minute EMA over the slow one, short below with it under (any number of
    flips a day), from ``start`` minutes after the open."""
    f, s = _ema_rows(dv.c, p["fast"]), _ema_rows(dv.c, p["slow"])
    long_ = (dv.c > dv.vwap) & (f > s)
    short = (dv.c < dv.vwap) & (f < s)
    pos = long_.astype(float) - (short.astype(float) if p["short"] else 0.0)
    pos[:, :p["start"] // 5] = 0.0
    pos[:, LAST_ENTRY + 1:] = 0.0
    pos *= _filter(dv, p["filter"])[:, None]
    return run_positions(dv, pos)


@_day
def intraday_momentum(dv: Day, p):
    """The first half hour's move (from the prior close) points the last half hour (Gao, Han, Li & Zhou 2018;
    Baltussen et al. tie it to dealers hedging short gamma). Enter at 15:30, exit on the closing print."""
    first = dv.c[:, 5] / dv.prev_c - 1
    side = np.where(first > p["th"], 1, np.where(first < -p["th"], -1, 0)) * _filter(dv, p["filter"])
    entry = np.full(len(side), BARS - 6)
    none = np.where(side > 0, -np.inf, np.inf)
    return bracket(dv, side, entry, none, -none, exit_bar=BARS - 1, close_exit=True)


@_day
def prior_day_levels(dv: Day, p):
    """Prior-day high and low as the levels. ``fade``: sell the first tag of the high, buy the first tag of the
    low, aim for VWAP-ish (the prior close). ``break``: trade a 5-minute close through it. ``gamma``: fade
    when GEX is high, break when it is low."""
    k = 2
    c = dv.c.copy()
    c[:, :k] = np.nan
    up, dn = first_true(c > dv.prev_h[:, None]), first_true(c < dv.prev_l[:, None])
    first_up = up < dn
    sig = np.minimum(up, dn)
    brk = np.where(first_up, 1, -1)
    mode = p["mode"]
    if mode == "gamma":
        brk = np.where(dv.gex > 0.5, -brk, brk)
    elif mode == "fade":
        brk = -brk
    ok = np.isfinite(dv.atr) & (np.isfinite(dv.gex) if mode == "gamma" else True)
    side = np.where((sig <= LAST_ENTRY) & ok, brk, 0)
    lvl = np.where(first_up, dv.prev_h, dv.prev_l)
    # stops sit ``stop`` ATRs on the losing side of the level
    stop = np.where(side > 0, lvl - dv.atr * p["stop"], lvl + dv.atr * p["stop"])
    fade = side != np.where(first_up, 1, -1)
    tgt = np.where(fade, dv.prev_c, np.where(side > 0, np.inf, -np.inf))
    return bracket(dv, side, sig + 1, stop, tgt)


@_day
def strike_magnet(dv: Day, p):
    """GEX-level stand-in: QQQ's whole-$5 strikes carry the most open interest. On high-gamma days, from
    ``hour`` on, lean toward the nearest $5 strike when price sits at least ``dist`` of the way to the next one,
    and close on the print. (Strikes are found on the traded, unadjusted price.)"""
    j = (p["hour"] - 9) * 12 - 6
    raw = dv.c[:, j] * dv.raw
    strike = np.round(raw / 5) * 5
    off = (raw - strike) / 2.5  # -1 .. 1: how far toward the neighbouring strike
    side = np.where(off > p["dist"], -1, np.where(off < -p["dist"], 1, 0)) * _filter(dv, p["filter"])
    tgt = strike / dv.raw
    stop = np.where(side > 0, -np.inf, np.inf)
    return bracket(dv, side, np.full(len(side), j + 1), stop, tgt, exit_bar=BARS - 1, close_exit=True)


@_day
def bollinger_fade(dv: Day, p):
    """Fade 5-minute stretches of ``z`` standard deviations from a 20-bar mean, back to the mean."""
    c = pd.DataFrame(dv.c)
    m = c.T.rolling(20).mean().T.to_numpy()
    sd = c.T.rolling(20).std().T.to_numpy()
    z = (dv.c - m) / sd
    pos = np.zeros_like(z)
    state = np.zeros(len(z))
    for j in range(20, LAST_ENTRY + 1):
        zj = z[:, j]
        state = np.where(state == 0, np.where(zj > p["z"], -1, np.where(zj < -p["z"], 1, 0)), state)
        state = np.where((state > 0) & (zj > 0) | (state < 0) & (zj < 0), 0, state)
        state = np.where((state > 0) & (zj < -p["z"] - 1.5) | (state < 0) & (zj > p["z"] + 1.5), 0, state)
        pos[:, j] = state
    pos *= _filter(dv, p["filter"])[:, None]
    return run_positions(dv, pos)


@_day
def ema_cross_5m(dv: Day, p):
    f, s = _ema_rows(dv.c, p["fast"]), _ema_rows(dv.c, p["slow"])
    pos = np.where(f > s, 1.0, -1.0 if p["short"] else 0.0)
    pos[:, :p["start"] // 5] = 0.0
    pos[:, LAST_ENTRY + 1:] = 0.0
    pos *= _filter(dv, p["filter"])[:, None]
    return run_positions(dv, pos)


@_day
def day_long_only(dv: Day, p):
    """Benchmark for day trades: buy the 09:35 open, sell 15:55."""
    side = np.ones(len(dv.days), int)
    inf = np.full(len(side), np.inf)
    return bracket(dv, side, np.ones(len(side), int), -inf, inf)


# --------------------------------------------------------------------------------------------- the catalogue


@dataclass(frozen=True)
class Strategy:
    name: str
    kind: str          # "swing" or "day"
    evaluate: Callable
    points: list
    needs: tuple       # inputs it can't run without
    how: str           # one-line plain description


G = wf.grid
FILTERS = ["none", "gex_low", "gex_high", "vix_high", "vix_low", "contango", "backwardation"]

CATALOGUE = [
    Strategy("Buy and hold", "swing", buy_hold, [{}], (), "Always long one unit."),
    Strategy("EMA crossover", "swing", ema_cross, G(fast=[5, 10, 20], slow=[50, 100, 200], short=[0, 1]), (),
             "Long while the fast EMA is above the slow EMA; optionally short below."),
    Strategy("EMA trend pullback", "swing", ema_pullback,
             G(trend=[100, 200], fast=[5, 10, 20], dip=[0.0, 0.01, 0.02], hold=[5, 10]), (),
             "In an uptrend (over the slow EMA), buy a close under the fast EMA; sell back above it."),
    Strategy("RSI(2) dip", "swing", rsi2_dip, G(entry=[5, 10, 20, 30], exit=[50, 70, 85], trend=[0, 1]), (),
             "Buy when 2-day RSI is washed out, sell when it recovers."),
    Strategy("IBS reversion", "swing", ibs_reversion, G(entry=[0.1, 0.2, 0.3], exit=[0.6, 0.8], trend=[0, 1]), (),
             "Buy a close near the day's low; sell on a strong close or a close over yesterday's high."),
    Strategy("MACD trend", "swing", macd_trend, G(fast=[8, 12, 19], slow=[26, 39], filter=[0, 1]), (),
             "Long while the MACD histogram is positive (optionally only over the 200-day EMA)."),
    Strategy("Donchian breakout", "swing", donchian, G(n=[10, 20, 55], m=[5, 10, 20], vix_cap=[25, 35, 99]),
             ("vix",), "Buy a close over the N-day high, sell under the M-day low; skip when VIX is above a cap."),
    Strategy("Vol-targeted EMA trend", "swing", vol_target_trend,
             G(trend=[50, 100, 200], target=[0.15, 0.2, 0.25]), (),
             "Long over the EMA, sized to a target volatility (up to 2x)."),
    Strategy("VIX term structure", "swing", vix_term, G(th=[0.85, 0.9, 0.95, 1.0, 1.05], short_above=[1.1, 1.2, 99]),
             ("vix", "vix3m"), "Long while VIX is below VIX3M (contango); optionally short in deep backwardation."),
    Strategy("VIX trend", "swing", vix_trend, G(n=[5, 10, 20, 50], cap=[25, 30, 99]), ("vix",),
             "Long while VIX is under its own EMA (fear fading)."),
    Strategy("VIX spike buy", "swing", vix_spike_buy, G(k=[0.1, 0.2, 0.3, 0.4], hold=[3, 5, 10, 20]), ("vix",),
             "Buy when VIX jumps well above its 10-day EMA; hold a set number of days."),
    Strategy("VIX9D inversion buy", "swing", vix9d_inversion, G(th=[1.0, 1.05, 1.1, 1.15], hold=[3, 5, 10]),
             ("vix", "vix9d"), "Buy when 9-day VIX is above 30-day VIX (short-term panic), until it normalizes."),
    Strategy("GEX regime", "swing", gex_regime, G(q=[0.1, 0.2, 0.3, 0.5], trend=[0, 50, 200]), ("gex",),
             "Long while dealer gamma is not in its lowest slice of the past year (optionally with a trend filter)."),
    Strategy("GEX switch", "swing", gex_switch, G(q=[0.2, 0.3, 0.5], trend=[50, 100, 200], entry=[10, 20]),
             ("gex",), "High gamma: hold the trend. Low gamma: only buy RSI(2) washouts."),
    Strategy("Regime vote (EMA+VIX+GEX)", "swing", regime_vote, G(trend=[50, 100, 200], k=[0, 2, 3, 4]),
             ("gex", "vix", "vix3m"), "Four votes: price over EMA, VIX<VIX3M, VIX under its EMA, GEX not low."),
    Strategy("Dip buying in calm regime", "swing", dip_in_calm,
             G(term=[0.9, 1.0, 1.1], q=[0.0, 0.2, 0.4], entry=[10, 20, 30]), ("gex", "vix", "vix3m"),
             "RSI(2) dips, but only when the VIX curve is calm and gamma isn't deeply negative."),
    Strategy("IBS with regime filter", "swing", ibs_filtered,
             G(entry=[0.15, 0.25], trend=[0, 200], filter=["none", "contango", "vix_high", "vix_low", "gex_low",
                                                          "gex_high"]), ("vix", "vix3m", "gex"),
             "IBS dip buying, only in one VIX or GEX regime."),
    Strategy("EMA trend, VIX-sized", "swing", ema_vix_sized,
             G(fast=[8, 20], slow=[50, 100], calm=[16, 20, 25], rest=[0.0, 0.5]), ("vix",),
             "EMA trend, cut to half or nothing when VIX is above a level."),
    Strategy("Overnight hold", "swing", overnight_hold,
             G(trend=[0, 50, 200], filter=["none", "contango", "vix_low", "vix_high", "gex_high", "gex_low"]),
             ("vix", "vix3m", "gex"), "Hold NQ only from close to next open, optionally only in a regime."),
    Strategy("Day: long open to close", "day", day_long_only, [{}], ("ic",),
             "Benchmark: buy 09:35, sell 15:55 every day."),
    Strategy("Day: opening range breakout", "day", opening_range_breakout,
             G(minutes=[15, 30, 60], stop=[0.5, 1.0], target=[0, 1.0, 2.0], filter=FILTERS), ("ic",),
             "Trade the first 5-minute close outside the first N minutes' range, stop inside the range."),
    Strategy("Day: gap fade", "day", gap_fade, G(gap=[0.0025, 0.005, 0.01], stop=[0.5, 1.0], filter=FILTERS),
             ("ic",), "Fade an opening gap back toward the prior close."),
    Strategy("Day: gap and go", "day", gap_go, G(gap=[0.0025, 0.005, 0.01], filter=FILTERS), ("ic",),
             "Ride an opening gap when the first bar confirms it; stop at that bar's far end."),
    Strategy("Day: VWAP + EMA trend", "day", vwap_ema_trend,
             G(fast=[9, 12], slow=[21, 34], start=[15, 30, 60], short=[0, 1], filter=FILTERS), ("ic",),
             "Long above VWAP with fast EMA over slow; short below with it under."),
    Strategy("Day: 5-min EMA cross", "day", ema_cross_5m,
             G(fast=[5, 9], slow=[20, 50], start=[15, 30], short=[0, 1], filter=FILTERS), ("ic",),
             "Plain 5-minute EMA crossover, flat by the close."),
    Strategy("Day: intraday momentum (last 30 min)", "day", intraday_momentum,
             G(th=[0.0, 0.0025, 0.005, 0.01], filter=FILTERS), ("ic",),
             "Trade the last half hour in the direction of the first half hour (from the prior close)."),
    Strategy("Day: prior-day high/low levels", "day", prior_day_levels,
             G(mode=["fade", "break", "gamma"], stop=[0.1, 0.25, 0.5]), ("ic",),
             "Fade or break the prior day's high/low; 'gamma' fades on high-GEX days and breaks on low-GEX days."),
    Strategy("Day: $5 strike magnet (GEX-level proxy)", "day", strike_magnet,
             G(hour=[13, 14, 15], dist=[0.3, 0.5, 0.7], filter=["none", "gex_high", "gex_low"]), ("ic",),
             "Late day, lean toward the nearest whole-$5 QQQ strike; tested on high- and low-gamma days."),
    Strategy("Day: Bollinger fade", "day", bollinger_fade, G(z=[2.0, 2.5, 3.0], filter=FILTERS), ("ic",),
             "Fade 5-minute moves 2-3 standard deviations from the 20-bar mean, exit at the mean."),
]


# --------------------------------------------------------------------------------------------- grading


def stats(r: pd.Series, rf: pd.Series) -> dict:
    r = r.dropna()
    eq = (1 + r).cumprod()
    yrs = len(r) / wf.DAYS_A_YEAR
    ex = r - rf.reindex(r.index).fillna(0.0)
    active = ex.abs() > 1e-9
    return {"CAGR": float(eq.iloc[-1] ** (1 / yrs) - 1) if yrs > 0 else np.nan,
            "Over cash/yr": float(ex.mean() * wf.DAYS_A_YEAR),
            "Sharpe": wf.sharpe(r, rf), "Max drop": float((eq / eq.cummax() - 1).min()),
            "Vol": float(r.std() * math.sqrt(wf.DAYS_A_YEAR)), "Time in market": float(active.mean()),
            "Win days": float((ex[active] > 0).mean()) if active.any() else np.nan,
            "Skew": float(ex.skew()), "Kurt": float(ex.kurt()), "Days": int(len(r))}


def deflated_sharpe(sr: float, srs: list[float], n_days: int, skew: float, kurt: float) -> float:
    """Bailey & Lopez de Prado's deflated Sharpe: the chance ``sr`` (annual) beats the best Sharpe that
    ``len(srs)`` skill-free strategies would show by luck, given the spread of the Sharpes actually tried."""
    from scipy.stats import norm
    n = max(len(srs), 2)
    s = np.array([x for x in srs if np.isfinite(x)]) / math.sqrt(wf.DAYS_A_YEAR)
    v = max(float(np.var(s)), 1e-6)
    g = 0.5772156649
    sr0 = math.sqrt(v) * ((1 - g) * norm.ppf(1 - 1 / n) + g * norm.ppf(1 - 1 / (n * math.e)))
    x = sr / math.sqrt(wf.DAYS_A_YEAR)
    den = math.sqrt(max(1 - skew * x + (kurt + 2) / 4 * x * x, 1e-9))  # kurt here is excess kurtosis
    return float(norm.cdf((x - sr0) * math.sqrt(n_days - 1) / den))


def first_usable(d: dict, needs: tuple) -> pd.Timestamp:
    """The first day all of a strategy's inputs exist, plus a year of warm-up for indicators and the GEX
    percentile."""
    starts = [d["px"].index[0]]
    for k in needs:
        s = d[k]
        s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
        starts.append(s.dropna().index[0])
    return max(starts)


def run_one(st: Strategy, d: dict, t0=None, warmup: int = GEX_LOOKBACK) -> dict:
    """Walk one strategy forward from ``t0`` (default: the first day its inputs exist) after a warm-up."""
    days = d["ic"].index.intersection(d["px"].index) if st.kind == "day" else d["px"].index
    days = days[days >= (t0 if t0 is not None else first_usable(d, st.needs))]
    fl = wf.folds(days, first=warmup if st.kind == "swing" else 60, purge=1)
    res = wf.run(st.evaluate, d, st.points, fl, d["rf"])
    res["fold_list"] = fl
    return res


def _folds_beating_cash(res: dict, rf: pd.Series) -> float:
    """Share of test years whose return beat T-bills over the same days."""
    ex = res["returns"] - rf.reindex(res["returns"].index).fillna(0.0)
    wins = []
    for t in res["folds"]["Tested on"]:
        lo, hi = t.split(" - ")
        wins.append(ex.loc[pd.Timestamp(lo):pd.Timestamp(hi) + pd.offsets.MonthEnd(0)].sum() > 0)
    return float(np.mean(wins)) if wins else np.nan


def rotation(results: dict, k: int) -> pd.Series:
    """Each fold, hold the ``k`` strategies that scored best on that fold's training window (their own
    walk-forward picks, also made on that window), equally weighted. Uses nothing from the test year."""
    names = list(results)
    nf = min(len(results[n]["folds"]) for n in names)
    pieces = []
    for i in range(nf):
        train = {n: results[n]["folds"]["Train Sharpe"].iloc[i] for n in names}
        best = sorted((n for n in names if np.isfinite(train[n])), key=lambda n: -train[n])[:k]
        f = results[best[0]]["folds"].iloc[i]
        lo, hi = f["Tested on"].split(" - ")
        test = pd.concat([results[n]["returns"] for n in best], axis=1)
        a, b = pd.Timestamp(lo), pd.Timestamp(hi) + pd.offsets.MonthEnd(0)
        pieces.append(test.loc[a:b].mean(axis=1))
    r = pd.concat(pieces).sort_index()
    return r[~r.index.duplicated(keep="first")]


def main(folder: str, out: str | None = None, only: str | None = None) -> pd.DataFrame:
    d = load(folder)
    rows, curves, results = [], {}, {}
    for kind in ("swing", "day"):
        sts = [st for st in CATALOGUE if st.kind == kind and all(k in d for k in st.needs)
               and (not only or only.lower() in st.name.lower())]
        if not sts:
            continue
        t0 = max(first_usable(d, st.needs) for st in sts)  # one shared window per kind: same folds for all
        for st in sts:
            res = run_one(st, d, t0)
            results[st.name] = res
            f = res["folds"]
            top = f["Settings"].value_counts()
            rows.append({"Strategy": st.name, "Kind": kind, **stats(res["returns"], d["rf"]),
                         "Settings tried": len(st.points), "Folds": len(f),
                         "Folds beating cash": _folds_beating_cash(res, d["rf"]),
                         "Stable": res["stable"], "Most picked": top.index[0] if len(top) else "",
                         "Picks": " | ".join(f["Settings"]), "How": st.how})
            curves[st.name] = res["returns"]
            s = rows[-1]
            print(f"{st.name:45s} Sharpe {s['Sharpe']:5.2f}  CAGR {s['CAGR']:7.1%}  drop {s['Max drop']:7.1%}",
                  flush=True)
        pool = {n: results[n] for n in (st.name for st in sts) if not n.startswith(("Buy and hold", "Day: long"))}
        if len(pool) > 3:
            for k in (1, 3):
                name = f"{'Day' if kind == 'day' else 'Swing'} rotation: best {k} on training"
                r = rotation(pool, k)
                curves[name] = r
                rows.append({"Strategy": name, "Kind": kind + "-meta", **stats(r, d["rf"]), "Settings tried": len(pool),
                             "How": f"Each year, hold the {k} {kind} strategies with the best training-window Sharpe."})
    t = pd.DataFrame(rows)
    t["Tested"] = [f"{curves[n].index[0]:%Y-%m} to {curves[n].index[-1]:%Y-%m}" for n in t["Strategy"]]
    common = max(r.index[0] for r in curves.values())
    for k, lab in (("Sharpe", "Sharpe common"), ("CAGR", "CAGR common"), ("Max drop", "Max drop common")):
        t[lab] = [stats(curves[n].loc[common:], d["rf"])[k] for n in t["Strategy"]]
    t.attrs["common"] = common
    tried = t[~t["Strategy"].str.startswith(("Buy and hold", "Day: long"))]
    srs = list(tried["Sharpe"])
    t["Deflated Sharpe"] = [deflated_sharpe(r.Sharpe, srs, r.Days, r.Skew, r.Kurt) for r in t.itertuples()]
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        t.to_csv(Path(out) / "results.csv", index=False)
        pd.DataFrame(curves).to_csv(Path(out) / "returns.csv")
    return t


if __name__ == "__main__":  # pragma: no cover
    import sys
    if sys.argv[1] == "fetch":
        fetch(sys.argv[2])
        sys.exit()
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else None)
