"""Long-only, multi-confluence swing strategy on daily bars.

The setup: in a market and stock uptrend, wait for price to pull back to the
20-day EMA or 50-day SMA, then buy when it closes back above the prior day's
high. Extra confluences (quiet pullback volume, RSI holding 40, MACD turning
up, OBV/VPT accumulation, room to the next resistance, breakout volume) each
add a point. Exits use a stop under the pullback, a partial profit at T1, a
trailing exit under the 20-day EMA, an optional T2, and warning rules (RSI
bearish divergence tightens the stop, an RSI overbought fade takes partial
profit, a close below the 50-day exits).

Every rule is evaluated on the close of bar t using data up to t only; the
trade simulator fills entries at the next bar's open and checks stops and
targets against each later bar's open/high/low, so there is no look-ahead.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import indicators as ind
from . import risk


@dataclass(frozen=True)
class Rule:
    label: str
    kind: str  # "required" (must pass) or "point" (counts toward the score)
    default: bool
    explain: str


RULES = {
    "market_uptrend": Rule("Market uptrend", "required", True,
                           "The S&P 500 (SPY) is above its 200-day average. Most stocks fall when the market does, "
                           "so long setups only count in a healthy market."),
    "stock_uptrend": Rule("Stock uptrend", "required", True,
                          "Price is above the 200-day average and the 50-day is above the 200-day: the stock is in a "
                          "confirmed long-term uptrend."),
    "pullback": Rule("Pullback to 20 EMA / 50 SMA", "required", True,
                     "In the last few days price dipped to the 20-day EMA or 50-day SMA and is still holding the "
                     "50-day. This is the 'buy the dip in an uptrend' entry zone."),
    "trigger_pdh": Rule("Close above prior day's high", "required", True,
                        "Today closed above yesterday's high, showing buyers stepped back in. Waiting for this keeps "
                        "you out of pullbacks that keep falling."),
    "light_volume": Rule("Quiet pullback volume", "point", True,
                         "Volume during the dip was below its 50-day average. Light selling means the pullback is "
                         "profit-taking rather than distribution."),
    "rsi_holds": Rule("RSI held above 40", "point", True,
                      "In uptrends RSI tends to bottom around 40-50 on dips. Holding 40 means momentum stayed "
                      "intact; breaking it is an early warning."),
    "macd_turn": Rule("MACD turning up", "point", True,
                      "The MACD histogram is rising or MACD just crossed above its signal line: downside momentum "
                      "from the pullback is fading."),
    "flow_ok": Rule("OBV/VPT accumulation", "point", True,
                    "The volume-flow line (OBV or VPT) is higher than a month ago, so more volume is flowing in on "
                    "up days than out on down days."),
    "room": Rule("Room to resistance", "point", True,
                 "The nearest overhead resistance is at least your T1 multiple of risk away, so the trade has "
                 "space to reach its first target."),
    "trigger_volume": Rule("Breakout-day volume", "point", True,
                           "The trigger day traded above its 50-day average volume. Big volume on the turn "
                           "confirms real demand."),
    "rsi_above_50": Rule("RSI cleanly above 50", "point", False,
                         "RSI closed above 50 on each of the last two days (a clean break, not a one-day poke)."),
    "macd_below_zero_cross": Rule("MACD cross below zero", "point", False,
                                  "MACD crossed above its signal line while still below zero in the last 5 days: "
                                  "momentum turning up from a dip, your original MACD rule."),
}

STOP_MODES = ["Pullback low", "20 EMA − ATR", "200-day MA"]

DEFAULTS = {
    "enabled": {k: r.default for k, r in RULES.items()},
    "min_score": 4,
    "pullback_bars": 3,
    "touch_tol_atr": 0.25,
    "rsi_floor": 40,
    "flow": "OBV",
    "stop_mode": "Pullback low",
    "stop_atr": 1.0,
    "t1_r": 1.5,
    "t1_fraction": 0.5,
    "t2_r": 3.0,
    "trail": True,
    "exit_below_50": True,
    "divergence_tighten": True,
    "rsi_fade_partial": True,
    "div_window": 14,
    "max_hold": 40,
}


def params_with(overrides: dict | None) -> dict:
    p = {**DEFAULTS, **(overrides or {})}
    p["enabled"] = {**DEFAULTS["enabled"], **((overrides or {}).get("enabled") or {})}
    return p


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def vpt(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume Price Trend: volume weighted by the day's percentage move."""
    return (close.pct_change(fill_method=None).fillna(0) * volume).cumsum()


def pivots(high: pd.Series, low: pd.Series, k: int = 5) -> tuple[pd.Series, pd.Series]:
    """Swing highs/lows: the extreme of a 2k+1 bar window. A pivot at bar j is
    only known at bar j+k, so callers must respect that confirmation lag."""
    win = 2 * k + 1
    ph = high.where(high == high.rolling(win, center=True).max())
    pl = low.where(low == low.rolling(win, center=True).min())
    return ph, pl


def sr_zones(ohlcv: pd.DataFrame, lookback: int = 250, k: int = 5, merge_atr: float = 0.75) -> list[dict]:
    """Support/resistance zones from clustered swing highs and lows over the
    last ``lookback`` bars, as of the last bar."""
    df = ohlcv.iloc[-lookback - k:]
    if len(df) < 2 * k + 2:
        return []
    ph, pl = pivots(df["High"], df["Low"], k)
    a = float(ind.atr(ohlcv["High"], ohlcv["Low"], ohlcv["Close"]).iloc[-1])
    if not np.isfinite(a) or a <= 0:
        a = float((df["High"] - df["Low"]).mean())
    levels = sorted([(float(v), "high") for v in ph.dropna()] + [(float(v), "low") for v in pl.dropna()])
    zones: list[dict] = []
    for lvl, _ in levels:
        if zones and lvl - zones[-1]["high"] <= merge_atr * a:
            z = zones[-1]
            z["high"], z["touches"] = lvl, z["touches"] + 1
            z["levels"].append(lvl)
        else:
            zones.append({"low": lvl, "high": lvl, "touches": 1, "levels": [lvl]})
    price = float(ohlcv["Close"].iloc[-1])
    out = []
    for z in zones:
        mid = float(np.mean(z["levels"]))
        out.append({"low": z["low"], "high": z["high"], "mid": mid, "touches": z["touches"],
                    "kind": "resistance" if mid > price else "support"})
    return out


def nearest_levels(ohlcv: pd.DataFrame, zones: list[dict] | None = None) -> tuple[float, float]:
    """(nearest resistance above, nearest support below) the last close."""
    zones = sr_zones(ohlcv) if zones is None else zones
    price = float(ohlcv["Close"].iloc[-1])
    res = [z["low"] for z in zones if z["low"] > price] + [z["mid"] for z in zones if z["low"] <= price < z["mid"]]
    sup = [z["high"] for z in zones if z["high"] < price] + [z["mid"] for z in zones if z["mid"] < price <= z["high"]]
    return (min(res) if res else np.nan, max(sup) if sup else np.nan)


def _resistance_series(high: pd.Series, close: pd.Series, k: int = 5, lookback: int = 250,
                       last_only: bool = False) -> pd.Series:
    """Nearest confirmed swing high above each bar's close (NaN = none, e.g. at new highs)."""
    ph, _ = pivots(high, high, k)
    piv = [(i, float(v)) for i, v in enumerate(ph.values) if np.isfinite(v)]
    c = close.values
    out = np.full(len(c), np.nan)
    rng = [len(c) - 1] if last_only else range(len(c))
    for t in rng:
        above = [v for i, v in piv if t - lookback <= i <= t - k and v > c[t]]
        if above:
            out[t] = min(above)
    return pd.Series(out, index=close.index)


def rsi_bearish_divergence(high: pd.Series, rsi: pd.Series, window: int = 14, min_gap: int = 3) -> pd.Series:
    """True on bars that make a higher high than the highest bar of the prior
    ``window`` bars while RSI is lower than it was at that earlier high."""
    h, r = high.values, rsi.values
    out = np.zeros(len(h), dtype=bool)
    for t in range(window, len(h)):
        seg = h[t - window:t - min_gap + 1]
        j = t - window + int(np.nanargmax(seg))
        if h[t] > h[j] and np.isfinite(r[j]) and np.isfinite(r[t]) and r[j] >= 60 and r[t] < r[j] - 2:
            out[t] = True
    return pd.Series(out, index=high.index)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def rule_frame(ohlcv: pd.DataFrame, market_close: pd.Series | None = None, params: dict | None = None,
               last_only: bool = False) -> pd.DataFrame:
    """Every rule, the score, the stop estimate and the entry signal for each bar."""
    p = params_with(params)
    c, h, l, v = ohlcv["Close"], ohlcv["High"], ohlcv["Low"], ohlcv["Volume"].astype(float)
    ema20, sma50, sma200 = ind.ema(c, 20), ind.sma(c, 50), ind.sma(c, 200)
    atr = ind.atr(h, l, c)
    r = ind.rsi(c)
    m = ind.macd(c)
    vol_avg = v.rolling(50, min_periods=20).mean().shift(1)
    f = pd.DataFrame(index=ohlcv.index)
    f["close"], f["ema20"], f["sma50"], f["sma200"], f["atr"], f["rsi"] = c, ema20, sma50, sma200, atr, r

    if market_close is not None and len(market_close.dropna()) > 200:
        mc = market_close.reindex(ohlcv.index.union(market_close.index)).ffill()
        f["market_uptrend"] = (mc > ind.sma(mc, 200)).reindex(ohlcv.index).fillna(False)
    else:
        f["market_uptrend"] = True  # no market data: don't block
    f["stock_uptrend"] = (c > sma200) & (sma50 > sma200)
    tol = p["touch_tol_atr"] * atr
    touch = (l <= ema20 + tol) | (l <= sma50 + tol)
    f["pullback"] = touch.rolling(p["pullback_bars"], min_periods=1).max().astype(bool) & (c >= sma50 - 0.5 * atr)
    f["trigger_pdh"] = c > h.shift(1)
    f["light_volume"] = v.shift(1).rolling(p["pullback_bars"]).mean() < vol_avg
    f["rsi_holds"] = r.rolling(5).min() >= p["rsi_floor"]
    cross = (m["macd"] > m["signal"]) & (m["macd"].shift(1) <= m["signal"].shift(1))
    f["macd_turn"] = (m["hist"] > m["hist"].shift(1)) | cross.rolling(3).max().astype(bool)
    f["macd_below_zero_cross"] = (cross & (m["macd"] < 0)).rolling(5).max().astype(bool)
    f["rsi_above_50"] = (r > 50) & (r.shift(1) > 50)
    flow = vpt(c, v) if p["flow"] == "VPT" else ind.obv(c, v)
    fe = flow.ewm(span=10, adjust=False).mean()
    f["flow"] = flow
    f["flow_ok"] = fe >= fe.shift(20)
    f["trigger_volume"] = v > vol_avg

    # Stop estimate as of the signal bar.
    if p["stop_mode"] == "200-day MA":
        stop = sma200 * 0.99
    elif p["stop_mode"] == "20 EMA − ATR":
        stop = ema20 - p["stop_atr"] * atr
    else:
        stop = l.rolling(5).min() - 0.1 * atr
    f["stop"] = stop.where(stop < c)
    risk_ = c - f["stop"]
    f["resistance"] = _resistance_series(h, c, last_only=last_only)
    f["room"] = f["resistance"].isna() | (f["resistance"] - c >= p["t1_r"] * risk_)

    en = p["enabled"]
    req = [k for k, rl in RULES.items() if rl.kind == "required" and en.get(k)]
    pts = [k for k, rl in RULES.items() if rl.kind == "point" and en.get(k)]
    f[req + pts] = f[req + pts].fillna(False).astype(bool)
    f["score"] = f[pts].sum(axis=1) if pts else 0
    f["max_score"] = len(pts)
    need = min(p["min_score"], len(pts))
    f["required_ok"] = f[req].all(axis=1) if req else True
    f["signal"] = f["required_ok"] & (f["score"] >= need) & f["stop"].notna() & sma200.notna()
    f["divergence"] = rsi_bearish_divergence(h, r, p["div_window"])
    return f


# ---------------------------------------------------------------------------
# Trade simulator
# ---------------------------------------------------------------------------


def simulate(ohlcv: pd.DataFrame, rules: pd.DataFrame, params: dict | None = None, cost_bps: float = 5.0,
             rf: float = 0.0) -> dict:
    """Fill signals at the next open and manage each trade with stops, targets and exit rules.

    Same-bar ambiguity is resolved pessimistically: a stop is assumed to hit
    before a target on the same day. All capital goes into one trade at a time;
    idle cash earns ``rf``.
    """
    p = params_with(params)
    o, h, l, c = (ohlcv[k].values for k in ("Open", "High", "Low", "Close"))
    idx = ohlcv.index
    sig = rules["signal"].values
    stop_est = rules["stop"].values
    ema20, sma50, rsi = rules["ema20"].values, rules["sma50"].values, rules["rsi"].values
    div = rules["divergence"].values
    score = rules["score"].values
    point_keys = [k for k, rl in RULES.items() if rl.kind == "point" and p["enabled"].get(k)]
    point_vals = rules[point_keys].values if point_keys else np.zeros((len(c), 0), dtype=bool)
    cost = cost_bps / 1e4
    cash, shares = 1.0, 0.0
    equity = np.empty(len(c))
    held = np.zeros(len(c))
    trades: list[dict] = []
    tr = None
    pending_entry = None
    pending_exit = pending_partial = None

    def sell(qty, px, reason, t):
        nonlocal cash, shares
        qty = min(qty, shares)
        if qty <= 0:
            return
        cash += qty * px * (1 - cost)
        shares -= qty
        tr["fills"].append((qty, px))
        tr["reason"] = reason
        if shares <= 1e-12:
            shares = 0.0
            sold = sum(q for q, _ in tr["fills"])
            avg = sum(q * x for q, x in tr["fills"]) / sold
            trades.append({"Entry date": idx[tr["t0"]], "Entry": tr["entry"], "Stop": tr["stop0"], "Risk ($)": tr["R"],
                           "Exit date": idx[t], "Avg exit": avg, "Return": avg * (1 - cost) / (tr["entry"] * (1 + cost)) - 1,
                           "R multiple": (avg - tr["entry"]) / tr["R"], "Bars held": t - tr["t0"],
                           "Exit reason": reason, "Score": tr["score"], **tr["rules"]})

    for t in range(len(c)):
        cash *= 1 + rf / 252
        if pending_entry is not None and shares == 0:
            stop0, sc, rl_state = pending_entry
            entry = o[t]
            R = entry - stop0
            if np.isfinite(R) and R > 0:
                shares = cash / (entry * (1 + cost))
                cash = 0.0
                tr = {"t0": t, "entry": entry, "stop0": stop0, "stop": stop0, "R": R, "fills": [], "t1_done": False,
                      "fade_done": False, "score": sc, "reason": "", "rules": rl_state}
            pending_entry = None
        if shares > 0:
            start_shares = tr.get("start_shares") or shares
            tr["start_shares"] = start_shares
            if pending_exit:
                sell(shares, o[t], pending_exit, t)
            elif pending_partial:
                sell(shares * 0.5, o[t], pending_partial, t)
            pending_exit = pending_partial = None
            if shares > 0:
                t1 = tr["entry"] + p["t1_r"] * tr["R"]
                t2 = tr["entry"] + p["t2_r"] * tr["R"] if p["t2_r"] else np.inf
                if o[t] <= tr["stop"] and t > tr["t0"]:
                    sell(shares, o[t], "Stop (gap)", t)
                elif l[t] <= tr["stop"]:
                    sell(shares, min(tr["stop"], o[t]), "Stop" if tr["stop"] < tr["entry"] else "Breakeven/trail stop", t)
                else:
                    if not tr["t1_done"] and h[t] >= t1:
                        sell(start_shares * p["t1_fraction"] if p["t1_fraction"] < 1 else shares, max(t1, o[t]), "T1", t)
                        tr["t1_done"] = True
                        tr["stop"] = max(tr["stop"], tr["entry"])
                    if shares > 0 and h[t] >= t2:
                        sell(shares, max(t2, o[t]), "T2", t)
            if shares > 0:  # end-of-day rules act at the next open
                if p["exit_below_50"] and c[t] < sma50[t]:
                    pending_exit = "Closed below 50-day"
                elif p["trail"] and tr["t1_done"] and c[t] < ema20[t]:
                    pending_exit = "Trail (below 20 EMA)"
                elif t - tr["t0"] >= p["max_hold"]:
                    pending_exit = "Time stop"
                else:
                    if p["divergence_tighten"] and div[t]:
                        tr["stop"] = max(tr["stop"], l[t])
                    if p["rsi_fade_partial"] and not tr["fade_done"] and t > 0 and rsi[t - 1] > 70 >= rsi[t]:
                        pending_partial = "RSI overbought fade"
                        tr["fade_done"] = True
        equity[t] = cash + shares * c[t]
        held[t] = shares * c[t] / equity[t] if equity[t] > 0 else 0.0
        if shares == 0 and sig[t] and t + 1 < len(c) and np.isfinite(stop_est[t]):
            pending_entry = (float(stop_est[t]), int(score[t]), dict(zip(point_keys, map(bool, point_vals[t]))))
    if shares > 0:  # mark open trade at the last close
        sold = sum(q for q, _ in tr["fills"])
        rem = shares
        avg = (sum(q * x for q, x in tr["fills"]) + rem * c[-1]) / (sold + rem)
        trades.append({"Entry date": idx[tr["t0"]], "Entry": tr["entry"], "Stop": tr["stop0"], "Risk ($)": tr["R"],
                       "Exit date": pd.NaT, "Avg exit": avg, "Return": avg / tr["entry"] - 1,
                       "R multiple": (avg - tr["entry"]) / tr["R"], "Bars held": len(c) - 1 - tr["t0"],
                       "Exit reason": "Open", "Score": tr["score"], **tr["rules"]})
    eq = pd.Series(equity, index=idx)
    rets = eq.pct_change().fillna(eq.iloc[0] - 1)
    return {"equity": eq, "returns": rets, "position": pd.Series(held, index=idx),
            "trades": pd.DataFrame(trades)}


def trade_stats(trades: pd.DataFrame) -> dict:
    closed = trades[trades["Exit reason"] != "Open"] if len(trades) else trades
    if closed is None or closed.empty:
        return {"Trades": 0, "Win rate": np.nan, "Expectancy (R)": np.nan, "Profit factor": np.nan,
                "Avg win": np.nan, "Avg loss": np.nan, "Avg bars held": np.nan}
    rm = closed["R multiple"]
    wins, losses = closed[closed["Return"] > 0], closed[closed["Return"] <= 0]
    gross_loss = -losses["Return"].sum()
    return {
        "Trades": int(len(closed)),
        "Win rate": float((closed["Return"] > 0).mean()),
        "Expectancy (R)": float(rm.mean()),
        "Profit factor": float(wins["Return"].sum() / gross_loss) if gross_loss > 0 else np.inf,
        "Avg win": float(wins["Return"].mean()) if len(wins) else np.nan,
        "Avg loss": float(losses["Return"].mean()) if len(losses) else np.nan,
        "Avg bars held": float(closed["Bars held"].mean()),
    }


def backtest(ohlcv: pd.DataFrame, params: dict | None = None, cost_bps: float = 5.0, rf: float = 0.0,
             market_close: pd.Series | None = None) -> dict:
    rules = rule_frame(ohlcv, market_close, params)
    res = simulate(ohlcv, rules, params, cost_bps, rf)
    asset_ret = ohlcv["Close"].pct_change(fill_method=None).fillna(0.0)
    stats = risk.summary(res["returns"], asset_ret, rf)
    stats["Exposure"] = float((res["position"] > 0).mean())
    ts = trade_stats(res["trades"])
    stats["Trades"] = ts["Trades"]
    return {**res, "stats": stats, "trade_stats": ts, "rules": rules}


def ablation(ohlcv: pd.DataFrame, params: dict | None = None, cost_bps: float = 5.0, rf: float = 0.0,
             market_close: pd.Series | None = None) -> pd.DataFrame:
    """Re-run the backtest with each must-pass rule switched off, and at each
    minimum score, to show what the filters add."""
    p = params_with(params)
    rows = []
    base = backtest(ohlcv, p, cost_bps, rf, market_close)
    rows.append({"Variant": f"Your settings (score ≥ {p['min_score']})", **base["trade_stats"], "CAGR": base["stats"]["CAGR"]})
    for k, on in p["enabled"].items():
        if on and RULES[k].kind == "required":
            r = backtest(ohlcv, {**p, "enabled": {**p["enabled"], k: False}}, cost_bps, rf, market_close)
            rows.append({"Variant": f"Without: {RULES[k].label}", **r["trade_stats"], "CAGR": r["stats"]["CAGR"]})
    n_pts = sum(1 for k, on in p["enabled"].items() if on and RULES[k].kind == "point")
    for ms in range(0, n_pts + 1):
        if ms != p["min_score"]:
            r = backtest(ohlcv, {**p, "min_score": ms}, cost_bps, rf, market_close)
            rows.append({"Variant": f"Score ≥ {ms}", **r["trade_stats"], "CAGR": r["stats"]["CAGR"]})
    return pd.DataFrame(rows).set_index("Variant")


def rule_report(trades: pd.DataFrame) -> pd.DataFrame:
    """For each point rule: how trades did when it passed vs failed at entry."""
    if trades is None or trades.empty:
        return pd.DataFrame()
    closed = trades[trades["Exit reason"] != "Open"]
    rows = []
    for k, rl in RULES.items():
        if rl.kind != "point" or k not in closed:
            continue
        on, off = closed[closed[k].astype(bool)], closed[~closed[k].astype(bool)]
        rows.append({"Rule": rl.label, "Trades when passed": len(on),
                     "Win rate (passed)": (on["Return"] > 0).mean() if len(on) else np.nan,
                     "Avg R (passed)": on["R multiple"].mean() if len(on) else np.nan,
                     "Trades when failed": len(off),
                     "Win rate (failed)": (off["Return"] > 0).mean() if len(off) else np.nan,
                     "Avg R (failed)": off["R multiple"].mean() if len(off) else np.nan})
    return pd.DataFrame(rows).set_index("Rule") if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# Today's trade plan
# ---------------------------------------------------------------------------


def weekly_trend(close: pd.Series) -> dict:
    wk = close.resample("W-FRI").last().dropna()
    if len(wk) < 45:
        return {"label": "Not enough history", "above_40w": None, "ma10_above_ma40": None}
    ma10, ma40 = wk.rolling(10).mean(), wk.rolling(40).mean()
    above = bool(wk.iloc[-1] > ma40.iloc[-1])
    aligned = bool(ma10.iloc[-1] > ma40.iloc[-1])
    rising = bool(ma40.iloc[-1] > ma40.iloc[-5])
    if above and aligned and rising:
        label = "Uptrend"
    elif not above and not aligned:
        label = "Downtrend"
    else:
        label = "Mixed"
    return {"label": label, "above_40w": above, "ma10_above_ma40": aligned, "ma40_rising": rising,
            "ma40": float(ma40.iloc[-1])}


def trade_plan(ohlcv: pd.DataFrame, market_close: pd.Series | None = None, params: dict | None = None) -> dict:
    """Checklist, verdict and entry/stop/targets for the latest bar."""
    p = params_with(params)
    f = rule_frame(ohlcv, market_close, p, last_only=True)
    last = f.iloc[-1]
    price = float(last["close"])
    hi = float(ohlcv["High"].iloc[-1])
    zones = sr_zones(ohlcv)
    res_lvl, sup_lvl = nearest_levels(ohlcv, zones)
    checklist = []
    for k, rl in RULES.items():
        if not p["enabled"].get(k):
            continue
        checklist.append({"key": k, "Rule": rl.label, "Type": "Must pass" if rl.kind == "required" else "Point",
                          "Pass": bool(last[k]), "Why it matters": rl.explain})
    req_ok = bool(last["required_ok"])
    triggered = bool(last["signal"])
    setup_only = all(bool(last[k]) for k in ("market_uptrend", "stock_uptrend", "pullback") if p["enabled"].get(k))
    need = min(p["min_score"], int(last["max_score"]))
    if triggered:
        status, tone = "Buy trigger hit today: enter at the next open", "pos"
        entry = price
    elif setup_only and int(last["score"]) >= need - 1:
        status, tone = f"Setup forming: buy only if price trades above today's high (${hi:,.2f})", "neu"
        entry = hi * 1.001
    else:
        missing = [RULES[c["key"]].label for c in checklist if c["Type"] == "Must pass" and not c["Pass"]]
        status = "No swing setup right now" + (f" (missing: {', '.join(missing)})" if missing else " (too few confluences)")
        tone, entry = "neg", np.nan
    stop = float(last["stop"]) if np.isfinite(last["stop"]) and np.isfinite(entry) else np.nan
    if np.isfinite(entry) and np.isfinite(stop) and stop < entry:
        R = entry - stop
        t1, t2 = entry + p["t1_r"] * R, entry + p["t2_r"] * R
    else:
        R = t1 = t2 = np.nan
    wt = weekly_trend(ohlcv["Close"])
    return {
        "status": status, "tone": tone, "triggered": triggered, "required_ok": req_ok,
        "score": int(last["score"]), "max_score": int(last["max_score"]), "need": need,
        "checklist": checklist, "price": price, "entry": entry, "stop": stop, "risk": R,
        "risk_pct": R / entry if np.isfinite(R) else np.nan, "t1": t1, "t2": t2,
        "resistance": res_lvl, "support": sup_lvl, "zones": zones, "weekly": wt,
        "divergence_recent": bool(f["divergence"].iloc[-10:].any()), "rsi": float(last["rsi"]),
        "ema20": float(last["ema20"]), "sma50": float(last["sma50"]), "sma200": float(last["sma200"]),
    }
