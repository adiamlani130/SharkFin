"""Options lab (Nov 2026): same-day (0DTE) QQQ/SPY premium trades on real option prices.

Research only. Option prices are Alpaca/OPRA 5-minute trade bars (volume-weighted price in the entry bar), from
February 2024 to November 2026. Decisions use only what is known at the entry bar (09:45 New York): the prior
close's VIX, VIX1D, VIX9D and GEX, and the first 15 minutes of the day. Short legs settle at the 16:00 close.

Picking window: Feb-Dec 2024 (the only real-price data before the grading window). Grading window: Jan 2025 to
Nov 13 2026. Costs: $0.015 slippage per leg on entry plus $0.65 commission per contract (= $0.0065 a share) per
leg; legs that finish out of the money expire with no exit cost."""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sharkfin.bs import YEAR_MIN, Surface, bs_price, fit_smile, implied_vol, smile_iv

NY = "America/New_York"
ENTRY = "09:45"
PICK_END = pd.Timestamp("2024-12-31")
import os
SLIP, COMM = float(os.environ.get("SF_SLIP", "0.015")), 0.0065
RISK = 0.02  # account risked (max loss) per trade


def parse(sym: str):
    root = sym[:-15]
    return root, pd.Timestamp("20" + sym[-15:-9]), 1 if sym[-9] == "C" else -1, int(sym[-8:]) / 1000


def day_snapshot(root: str, day: str, folder: Path, stock: pd.DataFrame) -> dict | None:
    """Entry-bar option prices, the fitted smile, and the settlement price for one day."""
    f = folder / "0dte" / f"{root}_{day}.pkl"
    if not f.exists():
        return None
    ob = pd.read_pickle(f)
    if ob.empty:
        return None
    t_entry = pd.Timestamp(f"{day} {ENTRY}", tz=NY)
    sb = stock.loc[day].between_time("09:30", "15:55")
    if len(sb) < 70 or t_entry not in sb.index:
        return None
    S = float(sb.loc[t_entry, "vw"])
    o930 = float(sb["o"].iloc[0])
    first = sb.loc[:pd.Timestamp(f"{day} 09:40", tz=NY)]
    settle = float(sb["c"].iloc[-1])
    e = ob[ob["t"] == t_entry].copy()
    if len(e) < 8:
        return None
    meta = e["symbol"].map(parse)
    e["cp"] = [m[2] for m in meta]
    e["K"] = [m[3] for m in meta]
    T = (16 * 60 - (9 * 60 + 47.5)) / YEAR_MIN  # mid-bar to the close, in trading-year units
    otm = ((e["cp"] > 0) & (e["K"] >= S)) | ((e["cp"] < 0) & (e["K"] <= S))
    e = e[otm & (e["vw"] >= 0.03)]
    if len(e) < 5:
        return None
    iv = implied_vol(e["vw"].values, S, e["K"].values, T, e["cp"].values)
    x = np.log(e["K"].values / S) / math.sqrt(T)
    coef = fit_smile(x, iv, w=np.sqrt(e["v"].values.astype(float)))
    if coef is None:
        return None
    px = {(int(c), float(k)): float(p) for c, k, p in zip(e["cp"], e["K"], e["vw"])}
    return {"day": pd.Timestamp(day), "S": S, "open": o930, "settle": settle, "T": T, "coef": coef,
            "atm_iv": float(smile_iv(coef, 0.0)), "px": px,
            "first_range": float(first["h"].max() - first["l"].min()) / o930,
            "move_to_entry": S / o930 - 1, "n_quotes": len(e)}


def leg_price(snap: dict, cp: int, K: float) -> tuple[float, bool]:
    """Real entry price when that strike traded in the entry bar (OTM side), else the fitted smile's price."""
    p = snap["px"].get((cp, float(K)))
    if p is not None:
        return p, True
    # an ITM option: use put-call parity off the OTM twin if it traded, else the smile
    twin = snap["px"].get((-cp, float(K)))
    if twin is not None:
        return twin + cp * (snap["S"] - K), True
    iv = smile_iv(snap["coef"], math.log(K / snap["S"]) / math.sqrt(snap["T"]))
    return float(bs_price(snap["S"], K, snap["T"], iv, cp)), False


def structure_pnl(snap: dict, legs: list[tuple[int, int, float]]) -> dict:
    """legs: (qty, cp, K) with qty -1 for short. Per-share P&L after costs, max loss, credit."""
    credit, real, cost = 0.0, True, 0.0
    payoff = 0.0
    for qty, cp, K in legs:
        p, ok = leg_price(snap, cp, K)
        real &= ok
        credit += -qty * p
        payoff += qty * max(cp * (snap["settle"] - K), 0.0)
        cost += SLIP + COMM
        if max(cp * (snap["settle"] - K), 0.0) > 0:
            cost += COMM  # closing or assignment of a leg that finished in the money
    pnl = credit + payoff - cost
    return {"credit": credit, "pnl": pnl, "real": real}


def iron_fly(snap, wing_pct):
    k = round(snap["S"])
    w = max(1.0, round(snap["S"] * wing_pct))
    legs = [(-1, 1, k), (-1, -1, k), (1, 1, k + w), (1, -1, k - w)]
    r = structure_pnl(snap, legs)
    r["max_loss"] = w - r["credit"]
    return r


def iron_condor(snap, em_mult, wing):
    S = snap["S"]
    straddle = leg_price(snap, 1, round(S))[0] + leg_price(snap, -1, round(S))[0]
    dist = max(1.0, round(straddle * em_mult))
    kc, kp = round(S) + dist, round(S) - dist
    legs = [(-1, 1, kc), (-1, -1, kp), (1, 1, kc + wing), (1, -1, kp - wing)]
    r = structure_pnl(snap, legs)
    r["max_loss"] = wing - r["credit"]
    return r


def long_straddle(snap):
    k = round(snap["S"])
    r = structure_pnl(snap, [(1, 1, k), (1, -1, k)])
    r["max_loss"] = -r["credit"]
    return r


def long_call(snap, otm=0.0):
    k = round(snap["S"] * (1 + otm))
    r = structure_pnl(snap, [(1, 1, k)])
    r["max_loss"] = -r["credit"]
    return r


# ---------------------------------------------------------------------------------------- inputs per day


def context(folder: Path) -> pd.DataFrame:
    idx = pd.read_pickle(folder / "idx.pkl")["Close"]
    dix = pd.read_csv(folder / "DIX.csv", parse_dates=["date"]).set_index("date")["gex"]
    c = pd.DataFrame({"vix": idx["^VIX"], "vix1d": idx["^VIX1D"], "vix9d": idx["^VIX9D"], "vxn": idx["^VXN"],
                      "vix3m": idx["^VIX3M"]}).join(dix.rename("gex"), how="outer").ffill(limit=3)
    c["gex_rank"] = c["gex"].rolling(252, min_periods=200).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    c["vix_5d"] = c["vix"].rolling(5).mean()
    return c.shift(1)  # everything here is known only after the prior close


def realised_history(stock: pd.DataFrame) -> pd.Series:
    """Each day's 09:45-to-close absolute move as a fraction of price (to forecast the next day's move from the
    past only)."""
    s = stock.between_time("09:30", "15:55")
    g = s.groupby(s.index.date)
    entry = g.apply(lambda x: x.between_time(ENTRY, ENTRY)["vw"].iloc[0] if len(x.between_time(ENTRY, ENTRY)) else np.nan)
    close = g["c"].last()
    out = (close / entry - 1).abs()
    out.index = pd.to_datetime(out.index)
    return out


def build_days(folder: Path, root: str) -> pd.DataFrame:
    from sharkfin.options_data import stock_bars
    stock = stock_bars(root, "5Min", "2024-01-25", "2026-11-14", folder)
    days = sorted({f.stem.split("_")[1] for f in (folder / "0dte").glob(f"{root}_*.pkl")})
    ctx = context(folder)
    rh = realised_history(stock)
    # forecast of today's 09:45->close move from past days only: average of last 5 and last 22 days (HAR-lite)
    fc = (0.5 * rh.rolling(5).mean() + 0.5 * rh.rolling(22).mean()).shift(1)
    rows = []
    for day in days:
        s = day_snapshot(root, day, folder, stock)
        if s is None:
            continue
        D = s["day"]
        fly = {f"fly_{w}": iron_fly(s, w) for w in (0.005, 0.01, 0.015)}
        ic = {f"ic_{m}_{w}": iron_condor(s, m, w) for m in (0.5, 1.0) for w in (2, 5)}
        rec = {"day": D, "root": root, "S": s["S"], "settle": s["settle"], "atm_iv": s["atm_iv"],
               "skew": s["coef"][1], "curv": s["coef"][2], "first_range": s["first_range"],
               "move_to_entry": s["move_to_entry"], "fc_move": fc.get(D, np.nan),
               "real_move": abs(s["settle"] / s["S"] - 1), "n_quotes": s["n_quotes"]}
        # implied 09:45->close move from the ATM straddle
        k = round(s["S"])
        rec["implied_move"] = (leg_price(s, 1, k)[0] + leg_price(s, -1, k)[0]) / s["S"]
        for name, r in {**fly, **ic, "straddle": long_straddle(s), "call_atm": long_call(s)}.items():
            rec[f"{name}_pnl"] = r["pnl"]
            rec[f"{name}_ml"] = r["max_loss"]
            rec[f"{name}_real"] = r["real"]
        rows.append(rec)
    df = pd.DataFrame(rows).set_index("day")
    return df.join(ctx, how="left")


# --------------------------------------------------------------------------------------------- grading


def trade_returns(df: pd.DataFrame, name: str, mask: pd.Series) -> pd.Series:
    """Daily account return: risk RISK of the account on each taken trade, sized by its max loss."""
    ml = df[f"{name}_ml"].clip(lower=0.05)
    r = RISK * df[f"{name}_pnl"] / ml
    return r.where(mask, 0.0).fillna(0.0)


def summarise(r: pd.Series, mask: pd.Series, lo=None, hi=None) -> dict:
    r, m = r.loc[lo:hi], mask.loc[lo:hi]
    n = int(m.sum())
    if n < 5:
        return {"trades": n}
    eq = (1 + r).cumprod()
    tr = r[m]
    return {"trades": n, "win": float((tr > 0).mean()), "avg_on_risk": float(tr.mean() / RISK),
            "Sharpe": float(r.mean() / r.std() * math.sqrt(252)) if r.std() > 0 else np.nan,
            "CAGR": float(eq.iloc[-1] ** (252 / len(r)) - 1), "MaxDD": float((eq / eq.cummax() - 1).min()),
            "worst_trade_on_risk": float(tr.min() / RISK)}


FILTERS = {
    "every day": lambda d: pd.Series(True, index=d.index),
    "Fridays": lambda d: pd.Series(d.index.dayofweek == 4, index=d.index),
    "GEX top half + quiet VIX": lambda d: (d["gex_rank"] >= 0.5) & (d["vix"] < 20) & (d["vix"] <= d["vix_5d"]),
    "GEX positive": lambda d: d["gex"] > 0,
    "no event priced (VIX1D <= VIX9D)": lambda d: d["vix1d"] <= d["vix9d"],
    "quiet first 15 min (range < 0.4x implied)": lambda d: d["first_range"] < 0.4 * d["implied_move"],
    "implied > forecast move x1.2 (rich)": lambda d: d["implied_move"] > 1.2 * d["fc_move"],
    "rich + GEX positive + no event": lambda d: (d["implied_move"] > 1.2 * d["fc_move"]) & (d["gex"] > 0) &
                                               (d["vix1d"] <= d["vix9d"]),
}
LONG_FILTERS = {
    "every day": FILTERS["every day"],
    "implied < forecast move x0.8 (cheap)": lambda d: d["implied_move"] < 0.8 * d["fc_move"],
    "event priced (VIX1D > VIX9D)": lambda d: d["vix1d"] > d["vix9d"],
    "GEX bottom 20%": lambda d: d["gex_rank"] <= 0.2,
}


def grade(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    shorts = [c[:-4] for c in df.columns if c.endswith("_pnl") and (c.startswith("fly") or c.startswith("ic"))]
    for name, (fn_name, fn) in itertools.product(shorts, FILTERS.items()):
        m = fn(df).fillna(False)
        r = trade_returns(df, name, m)
        rows.append({"structure": name, "filter": fn_name,
                     **{f"pick_{k}": v for k, v in summarise(r, m, None, PICK_END).items()},
                     **{f"grade_{k}": v for k, v in summarise(r, m, PICK_END + pd.Timedelta(days=1), None).items()}})
    for name, (fn_name, fn) in itertools.product(["straddle", "call_atm"], LONG_FILTERS.items()):
        m = fn(df).fillna(False)
        r = trade_returns(df, name, m)
        rows.append({"structure": name, "filter": fn_name,
                     **{f"pick_{k}": v for k, v in summarise(r, m, None, PICK_END).items()},
                     **{f"grade_{k}": v for k, v in summarise(r, m, PICK_END + pd.Timedelta(days=1), None).items()}})
    return pd.DataFrame(rows)


def main(folder: str, out: str) -> None:
    folder, out = Path(folder), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    allg = []
    for root in ("QQQ", "SPY"):
        df = build_days(folder, root)
        df.to_pickle(out / f"0dte_days_{root}.pkl")
        g = grade(df)
        g.insert(0, "root", root)
        allg.append(g)
    g = pd.concat(allg)
    g.to_csv(out / "0dte_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(g[["root", "structure", "filter", "pick_trades", "pick_Sharpe", "pick_win", "grade_trades", "grade_Sharpe",
             "grade_win", "grade_avg_on_risk", "grade_MaxDD"]].round(2).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:3])
