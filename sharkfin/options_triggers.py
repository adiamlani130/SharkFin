"""Options lab, part 3: SharkFin's own stock signals traded with options instead of shares (real prices, 2024-2026).

Research only. Takes every Dive Zone and Tech Breakout Rider trade the app's backtest made from Feb 2024 on
(``research_data/growth_lab/*_trades.csv``) and replays it with real option prices (Alpaca daily trade bars,
volume-weighted price on the buy and sell days):

* Dive Zone (5-day dips): buy a ~3-5 week at-the-money call, or sell a ~3-5 week at-the-money put (cash-secured).
* Breakout Rider (holds ~2-3 months): buy a ~4-7 month at-the-money call.

Costs: 1.5% of the option price per side, plus $0.65 a contract."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SPREAD, COMM = 0.015, 0.0065


def replay(folder: Path) -> pd.DataFrame:
    trades = {k: pd.read_csv(Path(__file__).parent / "research_data" / "growth_lab" / f"{f}.csv",
                             parse_dates=["Bought", "Sold"])
              for k, f in (("dz", "dive_zone_trades"), ("br", "breakout_trades"))}
    rows = []
    for f in sorted((folder / "trig").glob("*.pkl")):
        r = pd.read_pickle(f)
        if "bars" not in r or r["bars"] is None or len(r["bars"]) == 0:
            continue
        kind, i = f.stem.split("_")
        t = trades[kind].loc[int(i)]
        b = r["bars"].copy()
        b["d"] = b["t"].dt.normalize().dt.tz_localize(None)
        b["K"] = b["symbol"].str[-8:].astype(int) / 1000
        b["cp"] = b["symbol"].str[-9]
        S = r["S"]
        rec = {"kind": kind, "sym": r["sym"], "bought": r["bought"], "sold": r["sold"], "stock_ret": t["Return"],
               "exp": r["exp"]}
        for cp in ("C", "P"):
            x = b[b["cp"] == cp]
            if x.empty:
                continue
            k = x["K"].iloc[(x["K"] - S).abs().argsort().iloc[0]]
            x = x[x["K"] == k].sort_values("d")
            e = x[x["d"] == r["bought"]]
            ex = x[x["d"] <= r["sold"]]
            if e.empty or ex.empty:
                continue
            p0, p1 = float(e["vw"].iloc[0]), float(ex["vw"].iloc[-1])
            expired = pd.Timestamp(r["exp"]) < r["sold"]
            cost = SPREAD * (p0 + p1) + 2 * COMM
            if cp == "C":
                rec["long_call"] = (p1 - p0 - cost) / p0
            else:
                rec["short_put_on_cash"] = (p0 - p1 - cost) / k
                rec["put_premium_on_cash"] = p0 / k
            rec[f"{cp}_expired_before_sell"] = expired
        rows.append(rec)
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for kind, name in (("dz", "Dive Zone"), ("br", "Tech Breakout Rider")):
        d = df[df["kind"] == kind]
        for col, label in (("stock_ret", "shares (app trade)"), ("long_call", "buy ATM call"),
                           ("short_put_on_cash", "sell ATM put, cash-secured")):
            if col not in d:
                continue
            both = d.dropna(subset=[col])
            x = both[col]
            if len(x) < 5:
                continue
            out.append({"signal": name, "how": label, "trades": len(x), "win": (x > 0).mean(), "avg": x.mean(),
                        "median": x.median(), "worst": x.min(), "best": x.max(),
                        "avg_shares_same_trades": both["stock_ret"].mean()})
    return pd.DataFrame(out)


def main(folder: str, out: str) -> None:
    folder, out = Path(folder), Path(out)
    df = replay(folder)
    df.to_csv(out / "trigger_trades.csv", index=False)
    s = summary(df)
    s.to_csv(out / "trigger_results.csv", index=False)
    print(s.round(3).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:3])
