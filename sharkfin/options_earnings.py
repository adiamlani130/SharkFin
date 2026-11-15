"""Options lab, part 2: earnings trades on real option prices (Feb 2024 to Nov 2026, 75 liquid US stocks).

Research only. For every report, the lab reads the at-the-money straddle on the first expiry after the report at the
last hour of trading before the report (entry) and at 10:00-11:00 New York the morning after (exit), from Alpaca
OPRA hourly trade bars. It also reads a ~30-45 day call after the report for the post-earnings drift trades.

Everything used to choose a trade is known at entry: the straddle's implied move, the stock's past earnings
moves, its beat record, its trailing P/E, its 3-month return and distance from the 52-week high, VIX, and how many
news headlines it had in the past week. The surprise and the day's reaction are only used by trades entered
after the report (drift calls).

Costs: 1.5% of each option's price per side per leg (single-stock spreads are wider than QQQ's), plus $0.65 per
contract. Pick window: reports Feb-Dec 2024. Grade window: Jan 2025 to Nov 2026."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sharkfin.bs import bs_price, implied_vol

SPREAD, COMM = 0.015, 0.0065
PICK_END = pd.Timestamp("2024-12-31")


def _leg(sym, exp, cp, k):
    return f"{sym}{pd.Timestamp(exp):%y%m%d}{cp}{int(round(k * 1000)):08d}"


def _at(bars: pd.DataFrame, symbol: str, day, hour: int, col: str = "c"):
    b = bars[(bars["symbol"] == symbol)]
    b = b[(b["t"].dt.normalize().dt.tz_localize(None) == pd.Timestamp(day)) & (b["t"].dt.hour == hour)]
    return float(b[col].iloc[0]) if len(b) else np.nan


def event_rows(folder: Path) -> pd.DataFrame:
    stocks = pd.read_pickle(folder / "stocks.pkl")
    C = stocks["Adj Close"]
    idx = pd.read_pickle(folder / "idx.pkl")["Close"]["^VIX"]
    E = pd.read_pickle(folder / "earn_dates.pkl")
    E["ts"] = pd.to_datetime(E["Earnings Date"], utc=True).dt.tz_convert("America/New_York")
    E = E.dropna(subset=["Reported EPS"]).sort_values("ts")
    rows = []
    for f in sorted((folder / "earn").glob("*.pkl")):
        r = pd.read_pickle(f)
        n = r.get("near")
        if n is None or len(n) == 0:
            continue
        sym, S, entry, react, exp = r["sym"], r["S"], r["entry"], r["react"], r["near_exp"]
        strikes = sorted({int(s[-8:]) / 1000 for s in n["symbol"].unique()})
        k = min(strikes, key=lambda x: abs(x - S))
        call, put = _leg(sym, exp, "C", k), _leg(sym, exp, "P", k)
        c0, p0 = _at(n, call, entry, 15), _at(n, put, entry, 15)
        c1, p1 = _at(n, call, react, 10, "vw"), _at(n, put, react, 10, "vw")
        if not all(np.isfinite([c0, p0, c1, p1])) or c0 <= 0 or p0 <= 0:
            continue
        # wings for a defined-risk iron fly at ~ +/- 1.5x the implied move
        im = (c0 + p0) / S
        wing_k = [x for x in strikes if x >= k + 1.5 * im * S]
        wing_p = [x for x in strikes if x <= k - 1.5 * im * S]
        fly = None
        if wing_k and wing_p:
            kc, kp = min(wing_k), max(wing_p)
            wc0, wp0 = _at(n, _leg(sym, exp, "C", kc), entry, 15), _at(n, _leg(sym, exp, "P", kp), entry, 15)
            wc1, wp1 = _at(n, _leg(sym, exp, "C", kc), react, 10, "vw"), _at(n, _leg(sym, exp, "P", kp), react, 10, "vw")
            if all(np.isfinite([wc0, wp0, wc1, wp1])):
                credit = c0 + p0 - wc0 - wp0
                close = c1 + p1 - wc1 - wp1
                cost = SPREAD * (c0 + p0 + wc0 + wp0 + c1 + p1 + wc1 + wp1) + 8 * COMM
                width = max(kc - k, k - kp)
                fly = {"fly_pnl_on_risk": (credit - close - cost) / max(width - credit, 0.05)}
        cost_str = SPREAD * (c0 + p0 + c1 + p1) + 4 * COMM
        # stock-level features known at entry (split-adjusted closes)
        if sym not in C:
            continue
        px = C[sym].dropna()
        e_ix = px.index[px.index <= entry]
        if len(e_ix) < 260:
            continue
        p_entry = px.loc[e_ix[-1]]
        p_react = px.loc[react] if react in px.index else np.nan
        past = E[(E["sym"] == sym) & (E["ts"] < r["ts"] - pd.Timedelta(days=20))].tail(12)
        moves = []
        for t in past["ts"]:
            d0 = t.normalize().tz_localize(None)
            if t.hour >= 12:
                a = px.index[px.index <= d0]
                b = px.index[px.index > d0]
            else:
                a = px.index[px.index < d0]
                b = px.index[px.index >= d0]
            if len(a) and len(b):
                moves.append(abs(px.loc[b[0]] / px.loc[a[-1]] - 1))
        moves = moves[-8:]
        this = E[(E["sym"] == sym) & (E["ts"] == r["ts"])]
        last4 = past["Reported EPS"].tail(4)
        rows.append({
            "sym": sym, "ts": r["ts"], "entry": entry, "react": react, "S": S, "implied_move": im,
            "real_move": abs(p_react / p_entry - 1) if np.isfinite(p_react) else np.nan,
            "react_ret": p_react / p_entry - 1 if np.isfinite(p_react) else np.nan,
            "past_avg_move": np.mean(moves) if len(moves) >= 4 else np.nan,
            "past_max_move": np.max(moves) if len(moves) >= 4 else np.nan,
            "beat_rate": float((past["Surprise(%)"].tail(8) > 0).mean()) if len(past) >= 4 else np.nan,
            "surprise": float(this["Surprise(%)"].iloc[0]) if len(this) else np.nan,
            "pe": p_entry / last4.sum() if len(last4) == 4 and last4.sum() > 0 else np.nan,
            "ret_3m": p_entry / px.loc[e_ix[-63]] - 1, "off_high": p_entry / px.loc[e_ix[-252:]].max() - 1,
            "vix": float(idx.reindex([entry]).iloc[0]) if entry in idx.index else np.nan,
            "short_straddle": (c0 + p0 - c1 - p1 - cost_str) / S,
            "long_straddle": (c1 + p1 - c0 - p0 - cost_str) / S,
            "straddle_ret": (c1 + p1) / (c0 + p0) - 1,
            **(fly or {"fly_pnl_on_risk": np.nan}),
            **drift_call(r, sym, k_hint=S),
        })
    df = pd.DataFrame(rows)
    df["rich"] = df["implied_move"] / df["past_avg_move"]
    nf = folder / "news_counts.csv"
    if nf.exists():  # Alpaca news headlines in the 7 days before the report (attention), known at entry
        news = pd.read_csv(nf)
        news["ts"] = pd.to_datetime(news["ts"], utc=True)
        df["ts_utc"] = pd.to_datetime(df["ts"], utc=True)
        df = df.merge(news.rename(columns={"ts": "ts_utc"}), on=["sym", "ts_utc"], how="left")
        # "busy" = more headlines than this stock's median across its pick-window reports (cut fixed in 2024)
        med = df[df["entry"] <= PICK_END].groupby("sym")["news_7d"].median()
        df["news_busy"] = df["news_7d"] > df["sym"].map(med)
    return df


def drift_call(r: dict, sym: str, k_hint: float, hold: int = 20) -> dict:
    """Buy the ~30-45 day at-the-money call at the reaction day's close, sell ``hold`` trading days later (daily
    close). Returns its return after costs (or NaN)."""
    f = r.get("far")
    if f is None or len(f) == 0:
        return {"drift_call": np.nan, "drift_days": np.nan}
    f = f.copy()
    f["d"] = f["t"].dt.normalize().dt.tz_localize(None)
    f["K"] = f["symbol"].str[-8:].astype(int) / 1000
    f = f[f["symbol"].str[-9] == "C"]
    day0 = f[f["d"] == r["react"]]
    if day0.empty:
        return {"drift_call": np.nan, "drift_days": np.nan}
    # the strike nearest the reaction-day close is unknown here (the stock moved); nearest to the entry close
    # moved by the option-implied reaction is not needed: pick the call whose price is closest to ATM delta by
    # using the most traded strike that day (ATM calls trade most)
    sym0 = day0.sort_values("v").iloc[-1]["symbol"]
    path = f[f["symbol"] == sym0].sort_values("d")
    if len(path) < 2:
        return {"drift_call": np.nan, "drift_days": np.nan}
    p0 = float(path.iloc[0]["c"])
    days = path["d"].tolist()
    j = min(hold, len(days) - 1)
    p1 = float(path.iloc[j]["c"])
    cost = SPREAD * (p0 + p1) + 2 * COMM
    return {"drift_call": (p1 - p0 - cost) / p0, "drift_days": j}


def summarise(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) < 5:
        return {"n": len(x)}
    return {"n": len(x), "win": float((x > 0).mean()), "avg": float(x.mean()), "median": float(x.median()),
            "worst": float(x.min()), "t": float(x.mean() / x.std() * math.sqrt(len(x))) if x.std() > 0 else np.nan}


RULES = {
    "all reports": lambda d: pd.Series(True, index=d.index),
    "implied > past avg move x1.2 (rich)": lambda d: d["rich"] > 1.2,
    "implied > past avg x1.4": lambda d: d["rich"] > 1.4,
    "implied < past avg x0.8 (cheap)": lambda d: d["rich"] < 0.8,
    "implied < past avg x0.7": lambda d: d["rich"] < 0.7,
    "implied > biggest of last 8 moves": lambda d: d["implied_move"] > d["past_max_move"],
    "rich + steady beater (beat 7/8+)": lambda d: (d["rich"] > 1.2) & (d["beat_rate"] >= 0.875),
    "rich + low P/E (< 25)": lambda d: (d["rich"] > 1.2) & (d["pe"] < 25),
    "high P/E (> 50)": lambda d: d["pe"] > 50,
    "down 15%+ into report": lambda d: d["ret_3m"] < -0.15,
    "near 52w high (within 5%)": lambda d: d["off_high"] > -0.05,
    "VIX < 18": lambda d: d["vix"] < 18,
    "VIX >= 22": lambda d: d["vix"] >= 22,
    "busy news week (above own 2024 median)": lambda d: d.get("news_busy", pd.Series(False, index=d.index)) == True,
    "quiet news week": lambda d: d.get("news_busy", pd.Series(True, index=d.index)) == False,
    "rich + quiet news week": lambda d: (d["rich"] > 1.2) & (d.get("news_busy", pd.Series(True, index=d.index)) == False),
}
DRIFT_RULES = {
    "all reports": lambda d: pd.Series(True, index=d.index),
    "beat + up on the day": lambda d: (d["surprise"] > 0) & (d["react_ret"] > 0),
    "beat 10%+ and up 5%+": lambda d: (d["surprise"] > 10) & (d["react_ret"] > 0.05),
    "down 15%+ into report, beat, up on the day": lambda d: (d["ret_3m"] < -0.15) & (d["surprise"] > 0) &
                                                            (d["react_ret"] > 0),
    "miss + down 5%+ (fade check)": lambda d: (d["surprise"] < 0) & (d["react_ret"] < -0.05),
}


def grade(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    pick = df["entry"] <= PICK_END
    for trade, rules in (("short_straddle", RULES), ("fly_pnl_on_risk", RULES), ("long_straddle", RULES),
                         ("drift_call", DRIFT_RULES)):
        for name, fn in rules.items():
            m = fn(df).fillna(False)
            out.append({"trade": trade, "rule": name,
                        **{f"pick_{k}": v for k, v in summarise(df.loc[m & pick, trade]).items()},
                        **{f"grade_{k}": v for k, v in summarise(df.loc[m & ~pick, trade]).items()}})
    return pd.DataFrame(out)


def main(folder: str, out: str) -> None:
    folder, out = Path(folder), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    df = event_rows(folder)
    df.to_csv(out / "earnings_events.csv", index=False)
    g = grade(df)
    g.to_csv(out / "earnings_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(len(df), "events;", "implied/real move:", (df["real_move"] / df["implied_move"]).median())
    print(g.round(3).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:3])
