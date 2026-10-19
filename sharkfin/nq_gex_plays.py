"""Three textbook GEX + VIX setups for NQ, tested with the lab's no-look-ahead rules.

1. Call-wall fade: positive gamma and a quiet VIX; short the first tag of the call wall, stop just above it.
2. Negative-gamma breakout: gamma below the flip and VIX rising; short the first 5-minute close below the
   put wall (or ride a break of the call wall up), hold to the close.
3. OpEx pin: on expiration Fridays with high gamma and a quiet VIX, sell an iron butterfly or condor at the
   open (or lean toward the nearest big strike late in the day) and let it decay.

What is real and what is not:
  * "Above / below the gamma flip" is the sign of SqueezeMetrics' S&P 500 GEX for the prior session (real,
    but S&P 500, not Nasdaq-100).
  * Call wall, put wall and magnet strikes need strike-by-strike open interest history, which isn't freely
    available. They are approximated four ways (``wall``): the next whole-$5 or $10 QQQ strike past the
    prior close, one VXN-implied daily move from it, or the 20-session high/low.
  * Option prices for the butterflies and condors are not historical quotes: they are Black-Scholes values
    from the prior close of VXN (the Nasdaq-100's own 30-day implied volatility), times ``IV_SCALE``.
    Short-dated skew and the real bid/ask are not modelled. Treat those results as an approximation.

Everything known before the open is the prior session's (GEX, VIX, VXN); intraday decisions use bars up to
the one they act on and fill at the next bar's open.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from sharkfin import nq_lab as lab
from sharkfin import walkforward as wf

IV_SCALE = 1.0          # VXN as the option's volatility; the report also runs 0.85
LEG_COST = 0.01         # dollars per option leg per side (QQQ options trade in pennies)
RISK_PER_TRADE = 0.02   # an options trade risks 2% of the account (its max loss)
DAY_FRACTION = 1 / 252  # an option bought at 09:35 and expiring at the close: about one trading day


# --------------------------------------------------------------------------------------------- inputs


class View:
    """Everything a setup may know before or during each session, aligned to the lab's day arrays."""

    def __init__(self, d: dict):
        dv = lab.day_view(d)
        self.dv = dv
        days = dv.days
        idx = d["px"].index
        gex = d.get("gex", pd.Series(np.nan, index=idx)).reindex(idx)
        vix = d["vix"].reindex(idx)
        vxn = d.get("vxn", d["vix"]).reindex(idx)
        self.gex = gex.shift(1).reindex(days).to_numpy(float)              # prior session's GEX ($)
        self.vix = vix.shift(1).reindex(days).to_numpy(float)              # prior close
        self.vix_before = vix.shift(2).reindex(days).to_numpy(float)       # the close before that
        self.vix_ema5 = lab.ema(vix, 5).shift(1).reindex(days).to_numpy(float)
        self.vxn = vxn.shift(1).reindex(days).to_numpy(float)
        sess_h = d["ih"].max(axis=1)
        sess_l = d["il"].min(axis=1)
        self.hi20 = sess_h.rolling(20).max().shift(1).reindex(days).to_numpy(float)
        self.lo20 = sess_l.rolling(20).min().shift(1).reindex(days).to_numpy(float)
        self.opex = opex_days(idx).reindex(days).fillna(False).to_numpy(bool)
        self.friday = (days.dayofweek == 4)
        self.opex_week = opex_week(idx).reindex(days).fillna(False).to_numpy(bool)


def view(d: dict) -> View:
    hit = d.get("_gex_view")
    if hit is not None and hit.dv.days.equals(lab.day_view(d).days):
        return hit
    v = View(d)
    d["_gex_view"] = v
    return v


def opex_days(trading_days: pd.DatetimeIndex) -> pd.Series:
    """Monthly options expiration: the third Friday, or the trading day before it when it is a holiday.
    The exchange calendar is published in advance, so this is known ahead of time."""
    td = pd.DatetimeIndex(trading_days)
    out = pd.Series(False, index=td)
    months = pd.period_range(td.min(), td.max(), freq="M")
    for m in months:
        first = m.start_time
        fri = first + pd.offsets.Week(weekday=4) if first.dayofweek != 4 else first
        third = fri + pd.Timedelta(days=14)
        before = td[td <= third]
        if len(before) and before[-1].to_period("M") == m:
            out[before[-1]] = True
    return out


def opex_week(trading_days: pd.DatetimeIndex) -> pd.Series:
    td = pd.DatetimeIndex(trading_days)
    ox = opex_days(td)
    weeks = {d.to_period("W") for d in ox.index[ox]}
    return pd.Series([d.to_period("W") in weeks for d in td], index=td)


def regime(v: View, name: str, vmax: float = 20.0) -> np.ndarray:
    """Day filters, all from the prior close."""
    quiet = (v.vix < vmax) & (v.vix <= v.vix_ema5 * 1.02)  # subdued and not climbing
    rising = (v.vix > v.vix_before) & (v.vix > v.vix_ema5)
    pos, neg = v.gex > 0, v.gex < 0
    high = v.dv.gex > 0.5
    low = v.dv.gex < 0.2
    return {"none": np.ones(len(v.gex), bool), "pos": pos, "pos_quiet": pos & quiet, "high_quiet": high & quiet,
            "neg": neg, "neg_rising": neg & rising, "low_rising": low & rising, "rising": rising}[name]


def walls(v: View, kind: str) -> tuple[np.ndarray, np.ndarray]:
    """(call wall, put wall) in adjusted prices, from the prior close and what was known then."""
    dv = v.dv
    prev_raw = dv.prev_c * dv.raw
    if kind in ("r5", "r10"):
        step = 5.0 if kind == "r5" else 10.0
        up = np.floor(prev_raw / step) * step + step
        dn = np.ceil(prev_raw / step) * step - step
        return up / dv.raw, dn / dv.raw
    if kind == "em":
        em = dv.prev_c * v.vxn / 100 / math.sqrt(252)
        return dv.prev_c + em, dv.prev_c - em
    if kind == "range20":
        return v.hi20, v.lo20
    raise ValueError(kind)


# --------------------------------------------------------------------------------------------- 1. call-wall fade


def _call_wall_fade(dv, p, v):
    call, _ = walls(v, p["wall"])
    ok = regime(v, p["regime"], p.get("vmax", 20.0)) & (dv.o[:, 0] < call) & np.isfinite(call)
    touch = dv.h >= (call * (1 - p["near"]))[:, None]
    touch[:, lab.LAST_ENTRY:] = False
    j = lab.first_true(touch)
    entry = j + 1
    ok &= entry <= lab.LAST_ENTRY + 1
    e = np.clip(entry, 0, lab.BARS - 1)
    px_in = dv.o[np.arange(len(e)), e]
    stop = call * (1 + p["stop"])
    ok &= px_in < stop  # already through the invalidation level: no trade
    target = px_in * (1 - p["target"]) if p["target"] else np.full(len(e), -np.inf)
    side = np.where(ok, -1, 0)
    return lab.bracket(dv, side, entry, stop, target)


# --------------------------------------------------------------------------------------------- 2. negative-gamma breakout


def _neg_gamma_breakout(dv, p, v):
    ok = regime(v, p["regime"], 20.0)
    if p["level"] == "pdl":
        call, put = dv.prev_h, dv.prev_l
    elif p["level"] == "or30":
        call, put = dv.h[:, :6].max(axis=1), dv.l[:, :6].min(axis=1)
    else:
        call, put = walls(v, p["level"])
    c = dv.c.copy()
    c[:, :6 if p["level"] == "or30" else 1] = np.nan
    c[:, lab.LAST_ENTRY:] = np.nan
    dn = lab.first_true(c < put[:, None])
    up = lab.first_true(c > call[:, None]) if p["both"] else np.full(len(dn), lab.BARS)
    first_dn = dn <= up
    sig = np.minimum(up, dn)
    side = np.where(ok & (sig < lab.BARS), np.where(first_dn, -1, 1), 0)
    lvl = np.where(first_dn, put, call)
    stop = np.where(side < 0, lvl * (1 + p["stop"]), lvl * (1 - p["stop"]))
    none = np.where(side < 0, -np.inf, np.inf)
    return lab.bracket(dv, side, sig + 1, stop, none)


# --------------------------------------------------------------------------------------------- 3. OpEx pin


def _days(v: View, which: str) -> np.ndarray:
    return {"opex": v.opex, "friday": v.friday, "opex_week": v.opex_week, "all": np.ones(len(v.opex), bool)}[which]


def _opex_magnet(dv, p, v):
    """Futures version: late on expiration day, lean toward the nearest whole-$5 strike and close on the print."""
    ok = _days(v, p["days"]) & regime(v, p["regime"], p.get("vmax", 20.0))
    j = (p["hour"] - 9) * 12 - 6
    raw = dv.c[:, j] * dv.raw
    strike = np.round(raw / 5) * 5
    off = (raw - strike) / 2.5
    side = np.where(off > p["dist"], -1, np.where(off < -p["dist"], 1, 0)) * ok
    stop = np.where(side > 0, -np.inf, np.inf)
    return lab.bracket(dv, side, np.full(len(side), j + 1), stop, strike / dv.raw, exit_bar=lab.BARS - 1,
                       close_exit=True)


def bs(s, k, t, sig, call: bool):
    """Black-Scholes value with zero rates (arrays welcome)."""
    from scipy.stats import norm
    s, k, t, sig = (np.asarray(x, float) for x in (s, k, t, sig))
    vol = np.maximum(sig * np.sqrt(np.maximum(t, 1e-12)), 1e-12)
    d1 = (np.log(s / k) + 0.5 * vol * vol) / vol
    d2 = d1 - vol
    c = s * norm.cdf(d1) - k * norm.cdf(d2)
    return np.where(t <= 1e-12, np.maximum(s - k, 0) if call else np.maximum(k - s, 0), c if call else c - s + k)


def fly_trades(dv, v: View, p, iv_scale: float = None) -> pd.DataFrame:
    """Sell an iron butterfly (``inner`` 0) or condor at the 09:35 open, priced at Black-Scholes with
    VXN x ``iv_scale``; buy it back at the close (or when price closes a bar beyond ``stop`` expected moves
    from the centre, valued then with the time left). Returns per-day credit, P&L and max risk, in dollars
    per one-QQQ-share structure."""
    iv_scale = IV_SCALE if iv_scale is None else iv_scale
    n = len(dv.days)
    s0 = dv.o[:, 1] * dv.raw
    sig = v.vxn / 100 * iv_scale
    em = s0 * sig * math.sqrt(DAY_FRACTION)
    centre = np.round(s0 / 5) * 5 if p["centre"] == "r5" else np.round(s0)
    inner = np.round(p["inner"] * em)
    wing = np.maximum(np.round(p["wing"] * em), 1.0)
    kc, kp = centre + inner, centre - inner
    kcw, kpw = kc + wing, kp - wing
    t = DAY_FRACTION

    def value(s, tt, r=slice(None)):
        return (bs(s, kc[r], tt, sig[r], True) - bs(s, kcw[r], tt, sig[r], True)
                + bs(s, kp[r], tt, sig[r], False) - bs(s, kpw[r], tt, sig[r], False))

    credit = value(s0, t) - 4 * LEG_COST
    close = dv.c * dv.raw[:, None]
    exit_val = value(close[:, -1], 0.0)
    exit_cost = np.zeros(n)
    if p["stop"]:
        far = np.abs(close - centre[:, None]) > (p["stop"] * em)[:, None]
        far[:, :1] = False
        far[:, -1] = False
        j = lab.first_true(far)
        hit = j < lab.BARS
        rows = np.flatnonzero(hit)
        # decided at that bar's close, bought back at the next bar's open
        nxt = j[rows] + 1
        tl = (lab.BARS - nxt) / lab.BARS * DAY_FRACTION
        exit_val[rows] = value(dv.o[rows, nxt] * dv.raw[rows], tl, rows)
        exit_cost[rows] = 4 * LEG_COST
    pnl = credit - exit_val - exit_cost
    risk = np.maximum(wing - credit, 0.01)
    return pd.DataFrame({"credit": credit, "pnl": pnl, "risk": risk, "em": em, "centre": centre,
                         "close": close[:, -1]}, index=dv.days)


def _opex_fly(dv, p, v):
    ok = _days(v, p["days"]) & regime(v, p["regime"], p.get("vmax", 20.0)) & np.isfinite(v.vxn)
    t = fly_trades(dv, v, p)
    r = (t["pnl"] / t["risk"]).to_numpy(float) * RISK_PER_TRADE
    return np.where(ok, np.nan_to_num(r), 0.0)


# --------------------------------------------------------------------------------------------- wiring


def _wrap(fn):
    def evaluate(d, p, start):
        v = view(d)
        r = pd.Series(fn(v.dv, p, v), index=v.dv.days)
        rf = d["rf"].reindex(v.dv.days).fillna(0.0)
        return {"returns": (r + rf).loc[start:]}
    evaluate.__name__ = fn.__name__
    return evaluate


call_wall_fade = _wrap(_call_wall_fade)
neg_gamma_breakout = _wrap(_neg_gamma_breakout)
opex_magnet = _wrap(_opex_magnet)
opex_fly = _wrap(_opex_fly)

G = wf.grid
WALLS = ["r5", "r10", "em", "range20"]
NEEDS = ("vix", "gex", "ic", "vxn")


def catalogue() -> list:
    S = lab.Strategy
    out = []
    for reg, label in (("pos_quiet", "positive GEX + quiet VIX"), ("high_quiet", "top-half GEX + quiet VIX"),
                       ("none", "every day (control)")):
        out.append(S(f"1. Call-wall fade: {label}", "day", call_wall_fade,
                     G(wall=WALLS, near=[0.0, 0.001], stop=[0.001, 0.0025, 0.005], target=[0.0, 0.0025, 0.005],
                       regime=[reg], vmax=[16, 20] if reg != "none" else [99]), NEEDS,
                     "Short the first tag of the call wall; stop just above it."))
    for reg, label in (("neg_rising", "GEX below flip + VIX rising"), ("low_rising", "bottom-20% GEX + VIX rising"),
                       ("neg", "GEX below flip"), ("none", "every day (control)")):
        out.append(S(f"2. Negative-gamma breakout: {label}", "day", neg_gamma_breakout,
                     G(level=WALLS + ["pdl", "or30"], stop=[0.001, 0.0025, 0.005], both=[0, 1], regime=[reg]), NEEDS,
                     "Short the first 5-minute close under the put wall (and optionally buy a break of the "
                     "call wall); hold to the close."))
    for reg, label in (("high_quiet", "top-half GEX + quiet VIX"), ("pos_quiet", "positive GEX + quiet VIX"),
                       ("none", "every expiration (control)")):
        out.append(S(f"3a. OpEx magnet (futures): {label}", "day", opex_magnet,
                     G(days=["opex", "friday"], hour=[13, 14, 15], dist=[0.3, 0.5], regime=[reg], vmax=[20]), NEEDS,
                     "On expiration Fridays, lean toward the nearest $5 strike late in the day."))
        out.append(S(f"3b. OpEx iron fly/condor: {label}", "day", opex_fly,
                     G(days=["opex", "friday"], centre=["atm", "r5"], inner=[0.0, 0.5], wing=[1.0, 2.0],
                       stop=[0.0, 1.5], regime=[reg], vmax=[20]), NEEDS,
                     "Sell a same-day iron butterfly/condor at 09:35, priced off VXN; risk 2% a trade."))
    return out


# --------------------------------------------------------------------------------------------- diagnostics


def move_vs_implied(d: dict, start="2016-06") -> pd.DataFrame:
    """How far QQQ actually moved from 09:35 to the close, as a share of the VXN-implied one-day move, by
    regime and day type (whole sample; a description, not a trade)."""
    v = view(d)
    dv = v.dv
    em = dv.o[:, 1] * v.vxn / 100 / math.sqrt(252)
    move = np.abs(dv.c[:, -1] - dv.o[:, 1]) / em
    rng = (dv.h[:, 1:].max(axis=1) - dv.l[:, 1:].min(axis=1)) / em
    f = pd.DataFrame({"move": move, "range": rng, "opex": v.opex, "friday": v.friday,
                      "pos_quiet": regime(v, "pos_quiet"), "high_quiet": regime(v, "high_quiet"),
                      "neg_rising": regime(v, "neg_rising"), "neg": regime(v, "neg")}, index=dv.days).loc[start:]
    f = f[np.isfinite(f["move"])]
    rows = {}
    for name, mask in {"All days": slice(None), "Positive GEX + quiet VIX": f.pos_quiet,
                       "Top-half GEX + quiet VIX": f.high_quiet, "GEX below flip": f.neg,
                       "GEX below flip + VIX rising": f.neg_rising, "OpEx Fridays": f.opex,
                       "OpEx Fridays, top-half GEX + quiet VIX": f.opex & f.high_quiet,
                       "Other Fridays": f.friday & ~f.opex}.items():
        x = f.loc[mask]
        rows[name] = {"Days": len(x), "Move / implied": x["move"].mean(), "Range / implied": x["range"].mean(),
                      "Stayed inside 1 implied move": (x["move"] < 1).mean()}
    return pd.DataFrame(rows).T


def main(folder: str, out: str) -> pd.DataFrame:  # pragma: no cover - research run
    from pathlib import Path

    global IV_SCALE
    d = lab.load(folder)
    o = Path(out)
    o.mkdir(parents=True, exist_ok=True)
    move_vs_implied(d).to_csv(o / "gex_plays_moves.csv")
    print(move_vs_implied(d).round(3).to_string())
    rows, curves = [], {}
    sts = catalogue()
    t0 = max(lab.first_usable(d, s.needs) for s in sts)
    for scale in (1.0, 0.85):
        IV_SCALE = scale
        for st in sts:
            if scale != 1.0 and "3b" not in st.name:
                continue
            res = lab.run_one(st, d, t0)
            s = lab.stats(res["returns"], d["rf"])
            fo = res["folds"]
            name = st.name + ("" if scale == 1.0 else f" (option IV x{scale})")
            ex = res["returns"] - d["rf"].reindex(res["returns"].index).fillna(0.0)
            trades = int((ex.abs() > 1e-12).sum())
            rows.append({"Strategy": name, **s, "Trades": trades,
                         "Avg per trade": float(ex[ex.abs() > 1e-12].mean()) if trades else np.nan,
                         "Hit rate": float((ex[ex.abs() > 1e-12] > 0).mean()) if trades else np.nan,
                         "Folds beating cash": lab._folds_beating_cash(res, d["rf"]), "Stable": res["stable"],
                         "Most picked": fo["Settings"].value_counts().index[0], "Picks": " | ".join(fo["Settings"]),
                         "How": st.how})
            curves[name] = res["returns"]
            print(f"{name:70s} Sharpe {s['Sharpe']:5.2f} over cash {s['Over cash/yr']:6.1%} drop {s['Max drop']:6.1%}"
                  f" trades {trades:4d} hit {rows[-1]['Hit rate']:.2f}", flush=True)
    IV_SCALE = 1.0
    t = pd.DataFrame(rows)
    t.to_csv(o / "gex_plays_results.csv", index=False)
    pd.DataFrame(curves).to_csv(o / "gex_plays_returns.csv")
    return t


if __name__ == "__main__":  # pragma: no cover
    import sys
    main(sys.argv[1], sys.argv[2])
