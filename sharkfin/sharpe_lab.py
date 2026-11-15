"""Sharpe-2 hunt (Nov 2026): can any daily strategy, or blend of strategies, reach a Sharpe above 2 out of sample?

Research only; the app does not import this. Same rules as the earlier labs:

* Pick window 2006-01-01 to 2021-10-12, grade window 2021-10-13 to the end of the data. Every setting is chosen on
  the pick window only (best Sharpe there), then run untouched on the grade window.
* A signal known at the close fills at the **next open** (no trading at a close you could not have seen), and the
  gap from that close to the next open belongs to the position held before the trade.
* Costs: 3 bp a side on ETFs (5 bp on single-country, commodity and volatility ETFs, 10 bp on crypto).
* Every variant tried is counted (``TRIED``) and the write-up reports how many there were.

Run: ``python -m sharkfin.sharpe_lab .lab3 OUT_DIR`` after ``options_lab`` style downloads into ``.lab3`` (see
``load``)."""
from __future__ import annotations

import itertools
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

PICK = (pd.Timestamp("2006-01-01"), pd.Timestamp("2021-10-12"))
GRADE = (pd.Timestamp("2021-10-13"), pd.Timestamp("2026-12-31"))
A = 252

EQUITY = ["SPY", "QQQ", "IWM", "DIA", "MDY", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB",
          "SMH", "XBI", "KRE", "XHB", "VNQ"]
WORLD = ["EFA", "EEM", "EWJ", "FXI", "EWZ", "EWG", "EWU", "EWC", "EWA"]
BONDS = ["TLT", "IEF", "SHY", "LQD", "HYG", "TIP", "AGG", "EMB"]
REAL = ["GLD", "SLV", "USO", "DBC", "DBA", "GDX", "UUP", "FXE", "FXY"]
TREND_SET = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "TLT", "IEF", "LQD", "HYG", "TIP", "GLD", "SLV", "DBC",
             "USO", "UUP", "FXE", "FXY", "VNQ", "XLE", "XLU"]

TRIED: dict[str, int] = {}


def cost_of(t: str) -> float:
    if t.endswith("-USD"):
        return 0.0010
    if t in WORLD or t in REAL or t in ("SVXY", "VXX", "UVXY", "TQQQ", "XBI", "KRE", "XHB", "GDX"):
        return 0.0005
    return 0.0003


# ------------------------------------------------------------------------------------------------ data


def load(folder: str | Path) -> dict:
    folder = Path(folder)
    etf = pd.read_pickle(folder / "etf.pkl")
    idx = pd.read_pickle(folder / "idx.pkl")
    f = (etf["Adj Close"] / etf["Close"])
    px = {k: etf[k] * f for k in ("Open", "High", "Low", "Close")}
    px = {k: v.drop(columns=[c for c in v.columns if c.endswith("-USD")]) for k, v in px.items()}
    days = px["Close"]["SPY"].dropna().index
    px = {k: v.reindex(days) for k, v in px.items()}
    vix = idx["Close"].reindex(days).ffill(limit=3)
    dix = pd.read_csv(folder / "DIX.csv", parse_dates=["date"]).set_index("date")
    gex = dix["gex"].reindex(days)
    gr = pd.read_csv(Path(__file__).parent / "research_data" / "growth_returns.csv", parse_dates=["Date"])
    gr = gr.set_index("Date").reindex(days)
    rf = gr["tbill"].ffill().fillna(0.0)
    return {"O": px["Open"], "H": px["High"], "L": px["Low"], "C": px["Close"], "vix": vix, "gex": gex,
            "growth": gr, "rf": rf, "days": days}


# --------------------------------------------------------------------------------------------- engine


def run_next_open(d: dict, sig: pd.DataFrame, weights: pd.DataFrame | None = None) -> pd.Series:
    """Daily portfolio return of target positions decided at each close and filled at the next open.

    ``sig`` holds the target exposure per ticker (decided with data up to and including that day's close).
    The position held during day t's session is sig at t-1; the overnight gap into day t belongs to the
    position from the session before (sig at t-2)."""
    O, C = d["O"][sig.columns], d["C"][sig.columns]
    q = sig.shift(1).fillna(0.0)          # held from open t to open t+1
    q_prev = q.shift(1).fillna(0.0)       # held over the gap into day t
    gap = (O / C.shift(1) - 1).fillna(0.0)
    intra = (C / O - 1).fillna(0.0)
    cost = pd.Series({c: cost_of(c) for c in sig.columns})
    r = q_prev * gap + q * intra - (q - q_prev).abs() * cost
    if weights is not None:
        return (r * weights.reindex_like(r).fillna(0.0)).sum(axis=1)
    n = sig.shape[1]
    return r.sum(axis=1) / n


def stats(r: pd.Series, rf: pd.Series, lo=None, hi=None) -> dict:
    r = r.loc[lo:hi].dropna()
    if len(r) < 20:
        return {"Sharpe": np.nan}
    ex = r - rf.reindex(r.index).fillna(0.0)
    eq = (1 + r).cumprod()
    yrs = len(r) / A
    sd = ex.std()
    active = r.abs() > 1e-12
    return {"Sharpe": float(ex.mean() / sd * math.sqrt(A)) if sd > 0 else np.nan,
            "CAGR": float(eq.iloc[-1] ** (1 / yrs) - 1), "Vol": float(r.std() * math.sqrt(A)),
            "MaxDD": float((eq / eq.cummax() - 1).min()), "InMarket": float(active.mean()),
            "WinDays": float((r[active] > 0).mean()) if active.any() else np.nan,
            "Skew": float(ex.skew()), "WorstDay": float(r.min())}


def both(r: pd.Series, rf: pd.Series) -> dict:
    p, g = stats(r, rf, *PICK), stats(r, rf, *GRADE)
    return {**{f"pick_{k}": v for k, v in p.items()}, **{f"grade_{k}": v for k, v in g.items()}}


def pick_best(name: str, fn, grid: dict, d: dict) -> tuple[dict, pd.Series, pd.DataFrame]:
    """Try every setting, choose the best pick-window Sharpe, return (params, returns, table of all tries)."""
    keys = list(grid)
    rows, best, best_r = [], None, None
    for vals in itertools.product(*grid.values()):
        p = dict(zip(keys, vals))
        r = fn(d, **p)
        s = stats(r, d["rf"], *PICK)["Sharpe"]
        rows.append({**p, "pick_Sharpe": s, "grade_Sharpe": stats(r, d["rf"], *GRADE)["Sharpe"]})
        if best is None or (np.isfinite(s) and s > best[1]):
            best, best_r = (p, s), r
    TRIED[name] = len(rows)
    return best[0], best_r, pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------ strategies


def _hold(entry: pd.DataFrame, exit_: pd.DataFrame, max_hold: int) -> pd.DataFrame:
    """1 from an entry close until an exit close (or max_hold days), per column."""
    E, X = entry.fillna(False).values, exit_.fillna(False).values
    out = np.zeros(E.shape)
    for j in range(E.shape[1]):
        on, held = False, 0
        for i in range(E.shape[0]):
            if on:
                held += 1
                if X[i, j] or held >= max_hold:
                    on = False
            if not on and E[i, j]:
                on, held = True, 0
            out[i, j] = 1.0 if on else 0.0
    return pd.DataFrame(out, index=entry.index, columns=entry.columns)


def ibs_basket(d, tickers=tuple(EQUITY), lo=0.2, hi=0.8, max_hold=5, trend=0):
    C, H, L = d["C"][list(tickers)], d["H"][list(tickers)], d["L"][list(tickers)]
    ibs = (C - L) / (H - L).replace(0, np.nan)
    entry = ibs < lo
    if trend:
        entry &= C > C.rolling(trend).mean()
    exit_ = (ibs > hi) | (C > H.shift(1))
    return run_next_open(d, _hold(entry, exit_, max_hold))


def rsi(c: pd.DataFrame, n: int) -> pd.DataFrame:
    dlt = c.diff()
    up = dlt.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-dlt.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def rsi2_basket(d, tickers=tuple(EQUITY), lo=10, hi=70, max_hold=10, trend=200):
    C = d["C"][list(tickers)]
    r2 = rsi(C, 2)
    entry = r2 < lo
    if trend:
        entry &= C > C.rolling(trend).mean()
    return run_next_open(d, _hold(entry, r2 > hi, max_hold))


def overnight(d, tickers=("SPY", "QQQ")):
    """Buy each close (MOC is unavailable to a next-open filler, so this one honestly needs MOC orders), sell open."""
    O, C = d["O"][list(tickers)], d["C"][list(tickers)]
    cost = pd.Series({c: cost_of(c) for c in tickers})
    r = (O / C.shift(1) - 1) - 2 * cost
    return r.mean(axis=1).fillna(0.0)


def turn_of_month(d, tickers=("SPY",), before=1, after=3):
    C = d["C"][list(tickers)]
    days = C.index
    m = pd.Series(days.to_period("M"), index=days)
    pos_in = m.groupby(m).cumcount()
    from_end = m.groupby(m).cumcount(ascending=False)
    # hold from the open after the decision; decide at close t for session t+1
    nxt_in = pos_in.shift(-1)
    nxt_end = from_end.shift(-1)
    want = ((nxt_end < before) | (nxt_in < after)).astype(float)
    sig = pd.DataFrame({t: want for t in tickers})
    return run_next_open(d, sig)


def tsmom(d, look=252, vol_target=0.10, tickers=tuple(TREND_SET)):
    C = d["C"][list(tickers)]
    mom = C / C.shift(look) - 1
    vol = C.pct_change().rolling(60).std() * math.sqrt(A)
    w = np.sign(mom) * (vol_target / vol).clip(upper=2.0)
    w = w.where(C.notna(), 0.0).fillna(0.0)
    # monthly rebalance
    me = pd.Series(C.index.to_period("M"), index=C.index)
    w = w.where(me != me.shift(-1)).ffill().fillna(0.0)
    n = (C.notna()).sum(axis=1).replace(0, np.nan)
    return run_next_open(d, w, weights=pd.DataFrame(1.0, index=w.index, columns=w.columns).div(n, axis=0))


def fear_day_long(d, vix_min=24, gex_q=0.3, ticker="QQQ"):
    """After a close with VIX >= vix_min and GEX in its lowest gex_q of the past year: buy the open, sell the
    close (daily-bar version of the NQ lab's rule)."""
    vix = d["vix"]["^VIX"]
    g = d["gex"]
    rank = g.rolling(252, min_periods=200).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    sig = ((vix >= vix_min) & (rank <= gex_q)).shift(1).fillna(False)   # known at the prior close
    O, C = d["O"][ticker], d["C"][ticker]
    return ((C / O - 1) - 2 * cost_of(ticker)).where(sig, 0.0).fillna(0.0)


def svxy_contango(d, ratio=0.95):
    """Short volatility (SVXY) only while VIX is below ratio x VIX3M. Classic high-Sharpe, rare-crash trade."""
    v, v3 = d["vix"]["^VIX"], d["vix"]["^VIX3M"]
    sig = pd.DataFrame({"SVXY": ((v / v3) < ratio).astype(float)})
    return run_next_open(d, sig)


def vix_carry_tilt(d, ratio=0.9):
    """Hold SPY with 2x exposure while the VIX curve is in steep contango, cash otherwise."""
    v, v3 = d["vix"]["^VIX"], d["vix"]["^VIX3M"]
    sig = pd.DataFrame({"SPY": ((v / v3) < ratio).astype(float)})
    return run_next_open(d, sig)


def put_index(d):
    """Cboe S&P 500 PutWrite index (^PUT): real, sells one-month at-the-money SPX puts, fully cash-secured."""
    return d["vix"]["^PUT"].pct_change().fillna(0.0)


# ---------------------------------------------------------------------------------------------- blends


def inverse_vol_blend(rets: pd.DataFrame, lookback=63, target=None) -> pd.Series:
    """Weights from trailing volatility only (no returns used), rebalanced daily, applied next day."""
    vol = rets.rolling(lookback, min_periods=20).std()
    w = (1 / vol).replace([np.inf], np.nan)
    w = w.div(w.sum(axis=1), axis=0).shift(1).fillna(0.0)
    r = (rets * w).sum(axis=1)
    if target:
        rv = r.rolling(lookback, min_periods=20).std().shift(1) * math.sqrt(A)
        r = r * (target / rv).clip(upper=4.0).fillna(0.0)
    return r


def main(folder: str, out: str) -> None:
    d = load(folder)
    rf = d["rf"]
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    sleeves, rows, tries = {}, [], []

    def add(name, r, params=None, note=""):
        sleeves[name] = r
        rows.append({"Strategy": name, "Params": params or "", **both(r, rf), "Note": note})

    def search(name, fn, grid, note=""):
        p, r, t = pick_best(name, fn, grid, d)
        t.insert(0, "Strategy", name)
        tries.append(t)
        add(name, r, p, note)

    search("IBS basket, US equity ETFs", ibs_basket,
           {"lo": [0.1, 0.2, 0.3], "max_hold": [3, 5, 10], "trend": [0, 200]})
    search("IBS basket, all ETFs", lambda d, **k: ibs_basket(d, tickers=tuple(EQUITY + WORLD + BONDS + REAL), **k),
           {"lo": [0.1, 0.2, 0.3], "max_hold": [3, 5], "trend": [0, 200]})
    search("IBS on QQQ only", lambda d, **k: ibs_basket(d, tickers=("QQQ",), **k),
           {"lo": [0.1, 0.2, 0.3], "max_hold": [3, 5, 10], "trend": [0, 200]})
    search("RSI(2) basket, US equity ETFs", rsi2_basket,
           {"lo": [5, 10, 20], "hi": [60, 70, 80], "trend": [0, 200]})
    search("Overnight hold (MOC buy, sell open)", overnight,
           {"tickers": [("SPY",), ("QQQ",), ("SPY", "QQQ", "IWM")]}, "Needs market-on-close orders.")
    search("Turn of month", turn_of_month, {"before": [1, 2], "after": [2, 3, 4], "tickers": [("SPY",), ("QQQ",)]})
    search("Trend following, 21 asset ETFs", tsmom, {"look": [63, 126, 252], "vol_target": [0.10]})
    search("Fear day long (QQQ, daily bars)", fear_day_long, {"vix_min": [20, 24, 28], "gex_q": [0.2, 0.3, 0.5]})
    search("Short vol: SVXY in contango", svxy_contango, {"ratio": [0.85, 0.9, 0.95, 1.0]},
           "SVXY was -1x VIX futures until Feb 2018, -0.5x after.")
    search("SPY only in steep VIX contango", vix_carry_tilt, {"ratio": [0.85, 0.9, 0.95]})
    add("Cboe PutWrite index (real, sells ATM SPX puts)", put_index(d))
    gr = d["growth"]
    add("Dive Zone (app version)", gr["dive_zone"].fillna(0.0))
    add("Tech Breakout Rider (app version)", gr["tech_breakout_rider"].fillna(0.0))
    add("Buy and hold SPY", gr["spy"].fillna(0.0))
    add("Buy and hold QQQ", gr["qqq"].fillna(0.0))
    TRIED["fixed sleeves"] = 5

    res = pd.DataFrame(rows)
    # correlations on the pick window
    S = pd.DataFrame(sleeves).loc[:"2026-11-06"]
    corr = S.loc[PICK[0]:PICK[1]].corr()

    # blends: choose sleeves on the pick window only (Sharpe > 0.5 there, not the buy-and-holds)
    cand = [r["Strategy"] for r in rows if r.get("pick_Sharpe", 0) > 0.5 and not r["Strategy"].startswith("Buy")]
    blends = []
    for target in (None, 0.10, 0.15):
        name = f"Blend of pick-window winners (inverse vol{', ' + str(int(target*100)) + '% vol target' if target else ''})"
        r = inverse_vol_blend(S[cand].fillna(0.0), target=target)
        blends.append({"Strategy": name, "Params": " + ".join(cand), **both(r, rf)})
        sleeves[name] = r
    no_tail = [c for c in cand if "SVXY" not in c and "PutWrite" not in c and "contango" not in c]
    r = inverse_vol_blend(S[no_tail].fillna(0.0))
    blends.append({"Strategy": "Blend without short-vol sleeves (inverse vol)", "Params": " + ".join(no_tail), **both(r, rf)})
    sleeves["Blend without short-vol sleeves (inverse vol)"] = r
    TRIED["blends"] = 4
    res = pd.concat([res, pd.DataFrame(blends)], ignore_index=True)
    res.to_csv(out_dir / "sharpe_results.csv", index=False)
    pd.concat(tries).to_csv(out_dir / "sharpe_all_tries.csv", index=False)
    corr.to_csv(out_dir / "sharpe_corr_pick.csv")
    pd.DataFrame(sleeves).to_pickle(out_dir / "sharpe_sleeves.pkl")
    print(res[["Strategy", "Params", "pick_Sharpe", "pick_CAGR", "pick_MaxDD", "grade_Sharpe", "grade_CAGR",
               "grade_MaxDD", "grade_WinDays"]].to_string())
    print("variants tried:", sum(TRIED.values()), TRIED)


if __name__ == "__main__":
    main(*sys.argv[1:3])
