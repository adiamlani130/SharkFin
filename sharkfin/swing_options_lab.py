"""Swing option plays (Nov 2026): pairs, hedges and event bets with few trades.

Research only; the app does not import this. Pick window 2012-01-01 to 2021-10-12 for share-based rules (the stock
panel starts in 2012), grade window 2021-10-13 on. Real option prices (Alpaca/OPRA daily trade bars) exist from
Feb 2024, so option versions of a rule are graded on Feb 2024 to Nov 2026 only, with rules fixed beforehand.

Costs: 10 bp a side per share leg; 1.5% of the option price a side plus $0.65 a contract per option leg."""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PICK = (pd.Timestamp("2012-01-01"), pd.Timestamp("2021-10-12"))
GRADE = (pd.Timestamp("2021-10-13"), pd.Timestamp("2026-12-31"))
COST = 0.001

PAIRS = [("NVDA", "AMD"), ("AMD", "INTC"), ("NVDA", "AVGO"), ("AMAT", "LRCX"), ("LRCX", "KLAC"), ("AMAT", "KLAC"),
         ("MU", "INTC"), ("QCOM", "TXN"), ("MSFT", "GOOGL"), ("GOOGL", "META"), ("AAPL", "MSFT"), ("V", "MA"),
         ("KO", "PEP"), ("HD", "LOW"), ("XOM", "CVX"), ("CVX", "COP"), ("JPM", "BAC"), ("GS", "MS"), ("BAC", "C"),
         ("JPM", "WFC"), ("UPS", "FDX"), ("WMT", "COST"), ("WMT", "TGT"), ("MRK", "PFE"), ("CAT", "DE"),
         ("ADBE", "CRM"), ("NOW", "CRM"), ("ORCL", "MSFT"), ("MCD", "SBUX"), ("NKE", "LULU")]


def load(folder: Path) -> dict:
    s = pd.read_pickle(folder / "stocks.pkl")
    f = s["Adj Close"] / s["Close"]
    return {"C": s["Adj Close"], "O": s["Open"] * f, "V": s["Volume"]}


def pair_signals(C: pd.DataFrame, a: str, b: str, look: int, z_in: float, mode: str) -> pd.DataFrame:
    """Daily entries for one pair. z = how far the log price ratio a/b is from its trailing mean, in trailing
    standard deviations (all from data up to that close). mode 'revert' buys the laggard and shorts the leader;
    'momentum' does the opposite. Returns rows: date, long, short, z."""
    x = np.log(C[a] / C[b]).dropna()
    z = (x - x.rolling(look).mean()) / x.rolling(look).std()
    corr = np.log(C[a]).diff().rolling(252).corr(np.log(C[b]).diff())
    rows = []
    last = None
    for d, v in z.items():
        if not np.isfinite(v) or not np.isfinite(corr.get(d, np.nan)) or corr[d] < 0.5:
            continue
        if abs(v) >= z_in and (last is None or (d - last).days > 30):
            laggard, leader = (a, b) if v < 0 else (b, a)
            lo, sh = (laggard, leader) if mode == "revert" else (leader, laggard)
            rows.append({"date": d, "long": lo, "short": sh, "z": v, "pair": f"{a}/{b}"})
            last = d
    return pd.DataFrame(rows)


def hold_return(C: pd.DataFrame, O: pd.DataFrame, s: str, d0, days: int, side: int) -> float:
    """Enter at the next open after d0, exit at the close ``days`` sessions later."""
    idx = C.index
    i = idx.searchsorted(d0) + 1
    j = min(i + days - 1, len(idx) - 1)
    if i >= len(idx):
        return np.nan
    p0, p1 = O[s].iloc[i], C[s].iloc[j]
    if not (np.isfinite(p0) and np.isfinite(p1)) or p0 <= 0:
        return np.nan
    return side * (p1 / p0 - 1) - 2 * COST


def pairs_study(d: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    C, O = d["C"], d["O"]
    rows, trades = [], []
    grid = list(itertools.product([20, 60], [2.0, 2.5, 3.0], ["revert", "momentum"], [10, 20],
                                  ["pair", "long leg only"]))
    for look, z_in, mode, hold, legs in grid:
        t = []
        for a, b in PAIRS:
            if a not in C or b not in C:
                continue
            sig = pair_signals(C, a, b, look, z_in, mode)
            for _, r in sig.iterrows():
                lr = hold_return(C, O, r["long"], r["date"], hold, 1)
                sr = hold_return(C, O, r["short"], r["date"], hold, -1)
                ret = lr if legs == "long leg only" else 0.5 * (lr + sr)
                t.append({**r, "ret": ret, "long_ret": lr, "short_ret": sr})
        t = pd.DataFrame(t)
        if t.empty:
            continue
        for win, (lo, hi) in (("pick", PICK), ("grade", GRADE)):
            x = t[(t["date"] >= lo) & (t["date"] <= hi)]["ret"].dropna()
            rows.append({"look": look, "z_in": z_in, "mode": mode, "hold": hold, "legs": legs, "window": win,
                         "trades": len(x), "per_year": len(x) / ((min(hi, pd.Timestamp("2026-11-13")) - lo).days / 365.25),
                         "win": (x > 0).mean(), "avg": x.mean(), "median": x.median(), "worst": x.min(),
                         "t": x.mean() / x.std() * math.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan})
        t["look"], t["z_in"], t["mode"], t["hold"], t["legs"] = look, z_in, mode, hold, legs
        trades.append(t)
    return pd.DataFrame(rows), pd.concat(trades, ignore_index=True)


def main(folder: str, out: str) -> None:
    folder, out = Path(folder), Path(out)
    d = load(folder)
    res, trades = pairs_study(d)
    res.to_csv(out / "pairs_results.csv", index=False)
    trades.to_pickle(out / "pairs_trades.pkl")
    p = res[res.window == "pick"].set_index(["look", "z_in", "mode", "hold", "legs"])
    g = res[res.window == "grade"].set_index(["look", "z_in", "mode", "hold", "legs"])
    j = p.join(g, lsuffix="_pick", rsuffix="_grade")
    pd.set_option("display.width", 250)
    print(j[["trades_pick", "win_pick", "avg_pick", "t_pick", "trades_grade", "win_grade", "avg_grade", "median_grade",
             "t_grade"]].sort_values("t_pick", ascending=False).round(3).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:3])


# ------------------------------------------------------------------------------------------- hedges


def hedge_study(folder: Path) -> pd.DataFrame:
    """Dive Zone / QQQ / SPY held all the time, plus 1-month S&P puts (or collars) bought only in certain
    scenarios, priced on the surface calibrated to real 2024 SPY chains (options_model). Rolled every 21 sessions,
    settled at intrinsic on the real S&P close. Scenario flags use only the close the hedge is bought on."""
    from sharkfin import options_model as M
    from sharkfin.bs import bs_price
    sm = M.fit_real_smiles(folder)
    cal = M.calibrate(sm)
    idx = pd.read_pickle(folder / "idx.pkl")["Close"]
    etf = pd.read_pickle(folder / "etf.pkl")["Adj Close"]
    gr = pd.read_csv(Path(__file__).parent / "research_data" / "growth_returns.csv", parse_dates=["Date"]).set_index("Date")
    days = gr.index[gr.index >= "2006-01-03"]
    spx = idx["^SPX"].reindex(days).ffill()
    vix, vix3m = idx["^VIX"].reindex(days).ffill(), idx["^VIX3M"].reindex(days).ffill()
    credit = (etf["HYG"] / etf["IEF"]).reindex(days).ffill()
    flags = pd.DataFrame({
        "always": True,
        "VIX under 15 (cheap insurance)": vix < 15,
        "credit warning (junk bonds under their 50-day vs Treasuries)": credit < credit.rolling(50).mean(),
        "S&P under its 200-day": spx < spx.rolling(200).mean(),
        "S&P 10%+ above its 200-day (stretched)": spx > 1.10 * spx.rolling(200).mean(),
        "VIX curve inverted (panic)": vix > vix3m,
        "credit warning + VIX under 20": (credit < credit.rolling(50).mean()) & (vix < 20),
    }, index=days).fillna(False)
    rows = []
    T = 30 / 365
    for book in ("dive_zone", "qqq", "spy"):
        r = gr[book].reindex(days).fillna(0.0)
        beta = 0.74 if book == "dive_zone" else (1.1 if book == "qqq" else 1.0)
        for scen, kind, otm in itertools.product(list(flags.columns) + ["never"], ("put", "collar"), (0.95, 0.90)):
            if scen == "never" and (kind != "put" or otm != 0.95):
                continue
            blocks = []
            for i in range(0, len(days) - 21, 21):
                d0, d1 = days[i], days[i + 21]
                base = float((1 + r.iloc[i + 1:i + 22]).prod() - 1)
                h = 0.0
                if scen != "never" and bool(flags[scen].iloc[i]) and np.isfinite(vix.iloc[i]):
                    S0, S1, ref = spx.iloc[i], spx.iloc[i + 21], vix.iloc[i] / 100
                    K = S0 * otm
                    p = float(bs_price(S0, K, T, M.model_iv(cal, "1m", ref, S0, K, T), -1)) * (1 + 0.03)
                    h = (max(K - S1, 0.0) - p) / S0
                    if kind == "collar":
                        Kc = S0 * (2 - otm)
                        c = float(bs_price(S0, Kc, T, M.model_iv(cal, "1m", ref, S0, Kc, T), 1)) * (1 - 0.03)
                        h += (c - max(S1 - Kc, 0.0)) / S0
                    h *= beta  # hedge the portfolio's market exposure
                blocks.append({"date": d1, "ret": base + h, "hedged": h != 0.0, "hedge_pnl": h})
            b = pd.DataFrame(blocks).set_index("date")
            for win, (lo, hi) in (("pick", (pd.Timestamp("2006-01-01"), PICK[1])), ("grade", GRADE)):
                x = b.loc[lo:hi]
                eq = (1 + x["ret"]).cumprod()
                n_y = len(x) / 12
                rows.append({"book": book, "hedge": "none" if scen == "never" else f"{kind} {int(round((1 - otm) * 100))}% OTM",
                             "when": scen, "window": win, "Sharpe": x["ret"].mean() / x["ret"].std() * math.sqrt(12),
                             "CAGR": eq.iloc[-1] ** (1 / n_y) - 1, "MaxDD": (eq / eq.cummax() - 1).min(),
                             "worst_month": x["ret"].min(), "share_hedged": x["hedged"].mean(),
                             "hedge_cost_per_year": x["hedge_pnl"].sum() / n_y})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------- news shocks

CATEGORIES = {
    "FDA / trial": r"\bfda\b|approval|approves|trial|phase \d|data readout|clinical",
    "deal / partnership / contract": r"partner|deal|contract|agreement|collaborat|order|supply|award|stake|invest",
    "takeover / merger": r"acqui|merger|buyout|takeover|to buy|bid for",
    "guidance / pre-announcement": r"guidance|outlook|forecast|preannounc|raises|cuts|warns|sees",
    "analyst call": r"upgrade|downgrade|price target|initiat|analyst",
    "product / AI / launch": r"launch|unveil|announc|product|\bai\b|chip|model|keynote|event|conference",
    "legal / regulatory / government": r"lawsuit|probe|investigat|antitrust|regulat|ban|tariff|export|doj|sec |ftc|court|government",
    "patent": r"patent",
}


def classify(headlines: list[str]) -> list[str]:
    import re
    text = " ".join(headlines).lower()
    return [k for k, pat in CATEGORIES.items() if re.search(pat, text)] or (["no headline"] if not headlines else ["other"])


def shock_study(folder: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Big non-earnings days (stock beats or trails QQQ by 7%+ on 2x+ normal volume, more than 2 sessions from an
    earnings report). Trade at the next open: follow the move or fade it, for 5, 20 or 60 sessions, vs QQQ."""
    d = load(folder)
    C, O = d["C"], d["O"]
    q = pd.read_pickle(folder / "etf.pkl")["Adj Close"]["QQQ"].reindex(C.index)
    qo = (pd.read_pickle(folder / "etf.pkl")["Open"]["QQQ"] * pd.read_pickle(folder / "etf.pkl")["Adj Close"]["QQQ"]
          / pd.read_pickle(folder / "etf.pkl")["Close"]["QQQ"]).reindex(C.index)
    ev = pd.read_csv(folder / "news_shocks.csv", parse_dates=["date"])
    idx = C.index
    rows = []
    for r in ev.itertuples():
        i = idx.searchsorted(r.date) + 1
        rec = {"sym": r.sym, "date": r.date, "excess": r.excess, "up": r.excess > 0}
        nf = folder / "swing" / f"news_{r.sym}_{r.date.date()}.pkl"
        heads = pd.read_pickle(nf) if nf.exists() else None
        rec["n_headlines"] = len(heads) if heads is not None else np.nan
        rec["cats"] = classify(heads) if heads is not None else ["(not fetched)"]
        for h in (5, 20, 60):
            j = i + h - 1
            if j < len(idx):
                rec[f"fwd{h}"] = (C[r.sym].iloc[j] / O[r.sym].iloc[i] - 1) - (q.iloc[j] / qo.iloc[i] - 1) - 2 * COST
        rows.append(rec)
    df = pd.DataFrame(rows)
    out = []
    for win, (lo, hi) in (("pick", PICK), ("grade", GRADE)):
        w = df[(df.date >= lo) & (df.date <= hi)]
        for direction in (True, False):
            x = w[w.up == direction]
            for h in (5, 20, 60):
                y = x[f"fwd{h}"].dropna()
                out.append({"window": win, "move": "up" if direction else "down", "hold": h, "n": len(y),
                            "follow_avg": y.mean(), "follow_win": (y > 0).mean(), "median": y.median(),
                            "t": y.mean() / y.std() * math.sqrt(len(y)) if len(y) > 2 else np.nan})
    return df, pd.DataFrame(out)


# ----------------------------------------------------------------------------- option replays (real)

OPT_SPREAD, OPT_COMM = 0.015, 0.0065


def replay_option_file(f: Path, entry_shift: int = 0, exit_rule: str = "last") -> dict | None:
    """ATM call / put / straddle return between two days of real daily bars (volume-weighted prices).

    entry_shift=1 enters the session after the file's entry date (for signals only known at that day's close).
    exit_rule: 'last' = the file's exit date; 'pre_event' = 6 sessions before the last bar (the day before an
    event that the file ran 5 sessions past)."""
    r = pd.read_pickle(f)
    if "bars" not in r or r["bars"] is None or len(r["bars"]) == 0:
        return None
    b = r["bars"].copy()
    b["d"] = b["t"].dt.normalize().dt.tz_localize(None)
    b["K"] = b["symbol"].str[-8:].astype(int) / 1000
    b["cp"] = b["symbol"].str[-9]
    days = sorted(b["d"].unique())
    if len(days) < 2 + entry_shift:
        return None
    d0 = days[entry_shift]
    d1 = days[-1] if exit_rule == "last" else (days[-6] if len(days) >= 7 + entry_shift else None)
    if d1 is None or d1 <= d0:
        return None
    S = r["S"]
    k = b["K"].iloc[(b["K"] - S).abs().argsort().iloc[0]]
    out = {"sym": r["sym"], "entry": d0, "exit": d1, "S": S, "K": k}
    px = {}
    for cp in ("C", "P"):
        x = b[(b["cp"] == cp) & (b["K"] == k)].set_index("d")["vw"]
        if d0 in x.index and d1 in x.index:
            px[cp] = (float(x[d0]), float(x[d1]))
    for cp, name in (("C", "call"), ("P", "put")):
        if cp in px:
            p0, p1 = px[cp]
            out[name] = (p1 - p0 - OPT_SPREAD * (p0 + p1) - 2 * OPT_COMM) / p0
    if len(px) == 2:
        p0 = px["C"][0] + px["P"][0]
        p1 = px["C"][1] + px["P"][1]
        out["straddle"] = (p1 - p0 - OPT_SPREAD * (p0 + p1) - 4 * OPT_COMM) / p0
    daily = folder_daily(f.parent.parent, r["sym"])
    if daily is not None and d0 in daily.index and d1 in daily.index:
        out["shares"] = daily.loc[d1, "c"] / daily.loc[d0, "c"] - 1 - 2 * COST
    return out


def folder_daily(folder: Path, sym: str):
    f = folder / "daily" / f"{sym}.pkl"
    return pd.read_pickle(f) if f.exists() else None


def summarise_trades(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) < 3:
        return {"n": len(x)}
    return {"n": len(x), "win": (x > 0).mean(), "avg": x.mean(), "median": x.median(), "worst": x.min(),
            "best": x.max(), "t": x.mean() / x.std() * math.sqrt(len(x)) if x.std() > 0 else np.nan}


# ------------------------------------------------------------- Breakout Rider with long-dated calls (model)

IV_TO_RV = 0.98  # real 2024-26 at-the-money implied vol / trailing 60-day realised vol at our entries (median)


def breakout_calls(folder: Path) -> pd.DataFrame:
    """Every Breakout Rider trade since 2006, replayed with a call bought on the buy day and sold on the sell day.
    Priced with Black-Scholes at IV = 0.98 x the trailing 60-day realised volatility (the ratio real option prices
    showed at our 2024-26 entries), both at entry and exit, so no future volatility is used."""
    from sharkfin.bs import bs_price
    t = pd.read_csv(Path(__file__).parent / "research_data" / "growth_lab" / "breakout_trades.csv",
                    parse_dates=["Bought", "Sold"])
    px = pd.read_pickle(folder / "breakout_px.pkl")
    rv = np.log(px).diff().rolling(60).std() * math.sqrt(252)
    rows = []
    for r in t.itertuples():
        s = r.Symbol.replace(".", "-")
        if s not in px or r.Bought not in px.index or r.Sold not in px.index:
            continue
        sig = px.index[px.index < r.Bought]
        if not len(sig):
            continue
        S0, S1 = px[s][r.Bought], px[s][r.Sold]
        v0 = max(IV_TO_RV * rv[s][sig[-1]], 0.15)
        prior = px.index[px.index < r.Sold]
        v1 = max(IV_TO_RV * rv[s][prior[-1]], 0.15) if len(prior) else v0
        held = (r.Sold - r.Bought).days
        rec = {"sym": s, "bought": r.Bought, "sold": r.Sold, "shares": r.Return}
        for label, dte, mny in (("call ATM 5m", 150, 1.0), ("call ATM 8m", 240, 1.0), ("call 10% OTM 5m", 150, 1.1),
                                ("call 10% ITM 5m", 150, 0.9)):
            K = S0 * mny
            p0 = float(bs_price(S0, K, dte / 365, v0, 1))
            p1 = float(bs_price(S1, K, max(dte - held, 0) / 365, v1, 1))
            rec[label] = (p1 - p0 - OPT_SPREAD * (p0 + p1)) / p0 if p0 > 0 else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)
