"""Options lab, part 4: 20 years of S&P 500 premium selling, priced with Black-Scholes on a calibrated vol surface.

Research only. Real option prices only exist here from Feb 2024, so for 2006-2026 the lab prices each option
*at entry* with Black-Scholes on a volatility surface:

* The at-the-money level comes from the Cboe index for that tenor (VIX9D for 1 week, VIX for 1 month), which is
  itself computed from real S&P option prices.
* The skew and curvature (how much more out-of-the-money puts cost) come from smiles fit to real SPY option prices
  in Feb-Dec 2024 (the picking era), as a straight-line function of VIX. 2025-2026 real chains are kept back to
  check the fit.

Positions are held to expiry and settle at intrinsic value from the real S&P 500 close, so no exit price is
modelled. The model is checked against Cboe's real PutWrite index (^PUT). Costs: 2% of premium per leg plus $0.0065
a share (SPY terms). Pick window 2006-01-01 to 2021-10-12, grade 2021-10-13 on."""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sharkfin.bs import bs_delta, bs_price, fit_smile, implied_vol

PICK = (pd.Timestamp("2006-01-01"), pd.Timestamp("2021-10-12"))
GRADE = (pd.Timestamp("2021-10-13"), pd.Timestamp("2026-12-31"))
CAL_END = pd.Timestamp("2024-12-31")


# ------------------------------------------------------------------------------------- surface calibration


def fit_real_smiles(folder: Path) -> pd.DataFrame:
    """One row per (Monday, expiry) of real SPY chains: ATM iv, skew b, curvature c, tenor and that day's VIX."""
    vix = pd.read_pickle(folder / "idx.pkl")["Close"][["^VIX", "^VIX9D"]]
    rows = []
    for f in sorted((folder / "surf").glob("SPY_*.pkl")):
        day = pd.Timestamp(f.stem.split("_")[1])
        r = pd.read_pickle(f)
        b = r["bars"]
        if b.empty or day not in vix.index:
            continue
        S = r["S_close"]
        for exp, g in b.groupby("exp"):
            T = max((pd.Timestamp(exp) - day).days, 1) / 365.0
            K = g["symbol"].str[-8:].astype(int).values / 1000
            cp = np.where(g["symbol"].str[-9] == "C", 1, -1)
            otm = ((cp > 0) & (K >= S)) | ((cp < 0) & (K <= S))
            px = g["c"].values  # daily close, the closest in time to the underlying close
            ok = otm & (px >= 0.05)
            if ok.sum() < 6:
                continue
            iv = implied_vol(px[ok], S, K[ok], T, cp[ok])
            x = np.log(K[ok] / S) / math.sqrt(T)
            coef = fit_smile(x, iv, w=np.sqrt(g["v"].values[ok].astype(float)))
            if coef is None:
                continue
            rows.append({"day": day, "exp": exp, "T": T, "a": coef[0], "b": coef[1], "c": coef[2],
                         "vix": vix.loc[day, "^VIX"] / 100, "vix9d": vix.loc[day, "^VIX9D"] / 100})
    return pd.DataFrame(rows)


def calibrate(sm: pd.DataFrame) -> dict:
    """Per tenor bucket, a/vix, b and c as straight lines in VIX, fit on the calibration era only."""
    cal = sm[sm["day"] <= CAL_END].copy()
    cal["tenor"] = np.where(cal["T"] < 14 / 365, "1w", np.where(cal["T"] < 45 / 365, "1m", "2m"))
    out = {}
    for t, g in cal.groupby("tenor"):
        ref = g["vix9d"] if t == "1w" else g["vix"]
        out[t] = {"a_ratio": float((g["a"] / ref).median()),
                  "b": np.polyfit(ref, g["b"], 1).tolist(), "c": np.polyfit(ref, g["c"], 1).tolist(), "n": len(g)}
    return out


def model_iv(cal: dict, tenor: str, ref_vol: float, S, K, T):
    p = cal[tenor]
    a = p["a_ratio"] * ref_vol
    b = np.polyval(p["b"], ref_vol)
    c = np.polyval(p["c"], ref_vol)
    x = np.log(np.asarray(K) / S) / math.sqrt(T)
    return np.maximum(a + b * x + c * x * x, 0.02)


def check_fit(sm: pd.DataFrame, cal: dict) -> pd.DataFrame:
    """How well the 2024 calibration prices 2025-2026 real smiles: compare 25-delta-ish put iv (x = -0.1)."""
    rows = []
    g = sm[sm["day"] > CAL_END]
    for _, r in g.iterrows():
        tenor = "1w" if r["T"] < 14 / 365 else ("1m" if r["T"] < 45 / 365 else "2m")
        ref = r["vix9d"] if tenor == "1w" else r["vix"]
        for x in (-0.15, -0.075, 0.0, 0.05):
            real = r["a"] + r["b"] * x + r["c"] * x * x
            mod = model_iv(cal, tenor, ref, 1.0, math.exp(x * math.sqrt(r["T"])), r["T"])
            rows.append({"tenor": tenor, "x": x, "real_iv": real, "model_iv": float(mod)})
    d = pd.DataFrame(rows)
    return d.groupby(["tenor", "x"]).agg(real=("real_iv", "mean"), model=("model_iv", "mean"),
                                         abs_err=("real_iv", lambda s: 0)).assign(
        abs_err=lambda t: (t["model"] - t["real"]).abs())


# ------------------------------------------------------------------------------------------- backtest


def strike_for_delta(cal, tenor, ref, S, T, cp, target):
    """Strike whose model delta is closest to target (|delta|)."""
    ks = S * np.exp(np.linspace(-6, 6, 601) * max(ref, 0.08) * math.sqrt(T))
    iv = model_iv(cal, tenor, ref, S, ks, T)
    dl = np.abs(bs_delta(S, ks, T, iv, cp))
    return float(ks[np.argmin(np.abs(dl - target))])


def run(folder: Path, cal: dict, structure: str, tenor: str, filt: str, spx: pd.Series, ctx: pd.DataFrame,
        risk: float = 0.05) -> pd.Series:
    """Daily account return. Enters every ``hold`` trading days at the close, settles at the close ``hold`` days
    later. Short legs at the given delta; wings at 5-delta. Risk per trade = ``risk`` of the account (max loss)
    for spreads; cash-secured (notional = strike) for naked puts."""
    hold = 5 if tenor == "1w" else 21
    T = (7 if tenor == "1w" else 30) / 365
    days = spx.index
    ret = pd.Series(0.0, index=days[hold::hold][:(len(days) - 1) // hold])
    i = 0
    while i + hold < len(days):
        d0, d1 = days[i], days[i + hold]
        S0, S1 = spx.iloc[i], spx.iloc[i + hold]
        c = ctx.loc[d0]
        ref = (c["vix9d"] if tenor == "1w" else c["vix"]) / 100
        ok = np.isfinite(ref) and FILTERS[filt](c)
        if ok:
            legs = LEGS[structure](cal, tenor, ref, S0, T)
            credit, payoff, cost = 0.0, 0.0, 0.0
            for qty, cp, K in legs:
                iv = float(model_iv(cal, tenor, ref, S0, K, T))
                p = float(bs_price(S0, K, T, iv, cp))
                credit -= qty * p
                payoff += qty * max(cp * (S1 - K), 0.0)
                cost += 0.02 * p + 0.0065 * S0 / 500
            pnl = credit + payoff - cost
            if structure == "ATM put, cash-secured":
                r_trade = pnl / legs[0][2]
            else:
                width = max(abs(legs[0][2] - legs[2][2]), abs(legs[1][2] - legs[3][2])) if len(legs) == 4 else \
                    abs(legs[0][2] - legs[1][2])
                r_trade = risk * pnl / max(width - credit, 0.01 * S0)
            ret.loc[d1] = r_trade
        i += hold
    return ret


LEGS = {
    "ATM put, cash-secured": lambda cal, t, ref, S, T: [(-1, -1, S)],
    "put spread 20d/5d": lambda cal, t, ref, S, T: [(-1, -1, strike_for_delta(cal, t, ref, S, T, -1, 0.20)),
                                                      (1, -1, strike_for_delta(cal, t, ref, S, T, -1, 0.05))],
    "put spread 10d/3d": lambda cal, t, ref, S, T: [(-1, -1, strike_for_delta(cal, t, ref, S, T, -1, 0.10)),
                                                      (1, -1, strike_for_delta(cal, t, ref, S, T, -1, 0.03))],
    "iron condor 16d/5d": lambda cal, t, ref, S, T: [
        (-1, -1, strike_for_delta(cal, t, ref, S, T, -1, 0.16)), (-1, 1, strike_for_delta(cal, t, ref, S, T, 1, 0.16)),
        (1, -1, strike_for_delta(cal, t, ref, S, T, -1, 0.05)), (1, 1, strike_for_delta(cal, t, ref, S, T, 1, 0.05))],
}
FILTERS = {
    "always": lambda c: True,
    "VIX curve in contango (VIX < VIX3M)": lambda c: c["vix"] < c["vix3m"],
    "VIX >= 20": lambda c: c["vix"] >= 20,
    "VIX < 20": lambda c: c["vix"] < 20,
    "GEX positive": lambda c: c["gex"] > 0 if np.isfinite(c["gex"]) else True,
    "contango + VIX >= 16": lambda c: (c["vix"] < c["vix3m"]) and c["vix"] >= 16,
    "SPX above 200-day": lambda c: c["above200"],
}


def stats(r: pd.Series, rf: pd.Series, lo, hi) -> dict:
    """Per-period returns (one row per holding period); rf is the T-bill return over the same period."""
    r = r.loc[lo:hi]
    per_year = len(r) / max((r.index[-1] - r.index[0]).days / 365.25, 1e-9)
    ex = r - rf.reindex(r.index).fillna(0.0)
    eq = (1 + r).cumprod()
    traded = r[r != 0]
    return {"Sharpe": float(ex.mean() / ex.std() * math.sqrt(per_year)) if ex.std() > 0 else np.nan,
            "CAGR": float(eq.iloc[-1] ** (per_year / len(r)) - 1), "MaxDD": float((eq / eq.cummax() - 1).min()),
            "win": float((traded > 0).mean()) if len(traded) else np.nan, "trades": int(len(traded)),
            "worst": float(r.min())}


def main(folder: str, out: str) -> None:
    folder, out = Path(folder), Path(out)
    sm = fit_real_smiles(folder)
    sm.to_csv(out / "spy_real_smiles.csv", index=False)
    cal = calibrate(sm)
    print("calibration:", cal)
    print(check_fit(sm, cal).round(4))
    idx = pd.read_pickle(folder / "idx.pkl")["Close"]
    spx = idx["^SPX"].dropna().loc["2005-06-01":]
    dix = pd.read_csv(folder / "DIX.csv", parse_dates=["date"]).set_index("date")["gex"]
    ctx = pd.DataFrame({"vix": idx["^VIX"], "vix9d": idx["^VIX9D"].fillna(idx["^VIX"]), "vix3m": idx["^VIX3M"],
                        "gex": dix}).reindex(spx.index).ffill(limit=3)
    ctx["vix3m"] = ctx["vix3m"].fillna(ctx["vix"] * 1.05)
    ctx["above200"] = spx > spx.rolling(200).mean()
    gr = pd.read_csv(Path(__file__).parent / "research_data" / "growth_returns.csv", parse_dates=["Date"])
    rf_d = gr.set_index("Date")["tbill"].reindex(spx.index).ffill().fillna(0.0)
    cum = (1 + rf_d).cumprod()
    rows, series = [], {}
    for structure, tenor, filt in itertools.product(LEGS, ("1m", "1w"), FILTERS):
        if tenor == "1w" and structure == "ATM put, cash-secured":
            continue
        r = run(folder, cal, structure, tenor, filt, spx, ctx)
        rf = (cum.reindex(r.index) / cum.reindex(r.index).shift(1) - 1).fillna(0.0)
        if structure == "ATM put, cash-secured":
            r = r + rf  # the cash securing the put earns T-bills, as in ^PUT
        else:
            r = r + rf  # spreads: the account's idle cash earns T-bills too
        series[(structure, tenor, filt)] = r
        p, g = stats(r, rf, *PICK), stats(r, rf, *GRADE)
        rows.append({"structure": structure, "tenor": tenor, "filter": filt,
                     **{f"pick_{k}": v for k, v in p.items()}, **{f"grade_{k}": v for k, v in g.items()}})
    put_lvl = idx["^PUT"].reindex(spx.index).ffill()
    m = series[("ATM put, cash-secured", "1m", "always")]
    put = (put_lvl.reindex(m.index) / put_lvl.reindex(m.index).shift(1) - 1).fillna(0.0)
    rf = (cum.reindex(m.index) / cum.reindex(m.index).shift(1) - 1).fillna(0.0)
    print("model vs real ^PUT, 21-day returns: correlation", round(float(m.corr(put)), 3),
          "mean model", round(float(m.mean()), 4), "mean real", round(float(put.mean()), 4))
    rows.append({"structure": "Cboe PutWrite index (real)", "tenor": "1m", "filter": "always",
                 **{f"pick_{k}": v for k, v in stats(put, rf, *PICK).items()},
                 **{f"grade_{k}": v for k, v in stats(put, rf, *GRADE).items()}})
    res = pd.DataFrame(rows)
    res.to_csv(out / "spx_model_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.round(3).to_string())
    print("variants:", len(rows) - 1)


if __name__ == "__main__":
    main(*sys.argv[1:3])
