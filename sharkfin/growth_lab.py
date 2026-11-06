"""Growth lab (Nov 2026): SharkFin's strategies re-tested through the Nov 2026 crash, with VIX and GEX confluences,
and two mid-to-long-term growth strategies.

Run ``python -m sharkfin.growth_lab DATA_DIR`` where DATA_DIR holds:
  * sp500_ohlcv.pkl  {"Open"|"High"|"Low"|"Close"|"Volume": dates x tickers}, every stock that was in the
    S&P 500 at some point since 2005, daily since 2004 (Yahoo, split and dividend adjusted)
  * market.pkl       the same for SPY, QQQ, the VIX family, sector ETFs and ^IRX
  * DIX.csv          SqueezeMetrics' daily GEX history (https://squeezemetrics.com/monitor/static/DIX.csv)
It writes its tables to ``research_data/growth_lab`` (the Strategy Playbook page reads them).

No look-ahead, anywhere:
  * every signal is computed from closes up to the signal day, and trades fill on later bars;
  * GEX for a day is published after that day's close, so a decision at the close of day t uses day t-1's GEX;
  * VIX is known at the close it prints;
  * a missing value is carried forward from the past only (never filled from a later date); a stock with no
    price yet is not tradable; ranks only use stocks that were in the S&P 500 on that date;
  * filters and settings are picked on the picking window (2006 - Oct 2021) and graded on the five years after
    (Oct 2021 - Nov 6 2026), which include the 2022 bear market, the April 2025 tariff crash and the Nov 2026 selloff.
Survivorship: Yahoo has no prices for some stocks that left the index (often takeovers or failures), so a little
bias remains; Breakout Rider's tech list comes from today's sector table, so it runs higher still.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import breakout_rider as brk
from . import leader_dip as ld
from . import swing_engine, walkforward

PICK = ("2006-01-03", "2021-10-12")
GRADE = ("2021-10-13", "2026-11-06")
COST_BPS = 10.0
OUT = Path(__file__).with_name("research_data") / "growth_lab"

# Windows people remember: waves the strategies should catch and crashes they should survive.
WINDOWS = {
    "2008 crash (Sep 2008 - Mar 2009)": ("2008-09-01", "2009-03-09"),
    "COVID crash (Feb 19 - Mar 23 2020)": ("2020-02-19", "2020-03-23"),
    "COVID rebound (Mar 23 2020 - Feb 2021)": ("2020-03-23", "2021-02-12"),
    "2022 bear market": ("2022-01-03", "2022-12-30"),
    "AI wave 1 (Jan 2023 - Jul 2024)": ("2023-01-03", "2024-07-10"),
    "Aug 2024 yen-carry shakeout": ("2024-07-10", "2024-08-07"),
    "Tariff crash (Feb 19 - Apr 8 2025)": ("2025-02-19", "2025-04-08"),
    "Tariff rebound (Apr 8 - Dec 2025)": ("2025-04-08", "2025-12-31"),
    "2026 memory and AI wave (Jan - Oct 9 2026)": ("2026-01-02", "2026-10-09"),
    "Nov 2026 selloff (Oct 9 - Nov 6 2026)": ("2026-10-09", "2026-11-06"),
}


# ------------------------------------------------------------------------------------------------- data


def load(folder: str | Path) -> dict:
    f = Path(folder)
    # These pickles are written by SharkFin's own download step into a local folder, never taken from elsewhere.
    panel = pickle.load(open(f / "sp500_ohlcv.pkl", "rb"))
    mk = pickle.load(open(f / "market.pkl", "rb"))
    panel = {k: v.astype(float).sort_index() for k, v in panel.items()}
    dates = panel["Close"].index
    m = {k: v.sort_index() for k, v in mk.items()}
    close = m["Close"]
    cf = lambda s: walkforward.carry_forward(s.reindex(s.index.union(dates))).reindex(dates)
    d = {"panel": panel, "dates": dates, "spy": cf(close["SPY"]), "qqq": cf(close["QQQ"]), "vix": cf(close["^VIX"]),
         "vix3m": cf(close["^VIX3M"]), "tbill": (close["^IRX"] / 100).dropna(), "etf": close,
         "spy_open": cf(m["Open"]["SPY"]), "qqq_open": cf(m["Open"]["QQQ"])}
    from . import data as sd

    d["members"] = sd.sp500_members(dates, panel["Close"].columns)
    tab = sd.sp500_table()
    d["sectors"] = dict(zip(tab["Symbol"], tab["Sector"]))
    d["sector_ret3"] = ld.sector_returns(dates, panel["Close"].columns,
                                         {s: ld.GICS_ETF.get(sec) for s, sec in d["sectors"].items()}, close)
    try:
        g = pd.read_csv(f / "DIX.csv", index_col=0, parse_dates=True)["gex"]
        g = g[~g.index.duplicated()].sort_index()
        # Trailing one-year percentile, then lagged a day: what was known at the close of each session.
        pct = g.rolling(252, min_periods=126).apply(lambda x: (x[:-1] < x[-1]).mean() if len(x) > 1 else np.nan, raw=True)
        d["gex"] = cf(g).shift(1)
        d["gex_pct"] = cf(pct).shift(1)
    except FileNotFoundError:
        d["gex"] = d["gex_pct"] = pd.Series(np.nan, index=dates)
    return d


def tech_panel(d: dict) -> tuple[dict, pd.DataFrame]:
    from . import data as sd

    names = [c for c in brk.tech_universe(sd.sp500_table()) if c in d["panel"]["Close"]]
    panel = {k: v[names] for k, v in d["panel"].items()}
    mem = d["members"][names].copy()
    for c in brk.TECH_EXTRA:
        if c in mem:
            mem[c] = True
    return panel, mem


def rf_daily(d: dict) -> pd.Series:
    return pd.Series(swing_engine.daily_cash(d["dates"], d["tbill"]), index=d["dates"])


# ------------------------------------------------------------------------------------------------- runs


def dive_zone(d: dict, entry_ok: pd.Series | None = None, start=PICK[0], **kw) -> dict:
    return ld.backtest(d["panel"], d["spy"], "spy_trend", d["tbill"], ld.SLOTS, COST_BPS, start=start, rules="plus",
                       vix=d["vix"], sector_ret3=d["sector_ret3"], members=d["members"], entry_ok=entry_ok, **kw)


def breakout(d: dict, entry_ok: pd.Series | None = None, start=PICK[0]) -> dict:
    panel, mem = tech_panel(d)
    return brk.backtest(panel, d["qqq"], d["tbill"], brk.SLOTS, COST_BPS, start=start, market_close=d["spy"],
                        members=mem, entry_ok=entry_ok)


def momentum_leaders(d: dict, top: int = 10, lookback: int = 252, skip: int = 21, gate: str = "spy200",
                     universe: str = "sp500", cost_bps: float = COST_BPS, start=PICK[0],
                     risk_off: pd.Series | None = None) -> dict:
    """Hold the ``top`` S&P 500 stocks with the biggest 12-month gain (skipping the latest month), equal weight,
    re-picked at each month's last close and bought at the next session's open (Jegadeesh & Titman 1993).
    While the gate is off (SPY under its 200-day at the month-end close, or ``risk_off`` true that day) the
    money sits in T-bills. ``universe`` "tech" uses the Breakout Rider tech list. Returns daily returns."""
    if universe == "tech":
        panel, mem = tech_panel(d)
    else:
        panel, mem = d["panel"], d["members"]
    C, O = panel["Close"], panel["Open"]
    dates = C.index
    Cf = C.ffill()  # past only
    mom = Cf.shift(skip) / Cf.shift(lookback) - 1
    ok = mem.reindex(index=dates, columns=C.columns).fillna(False) & C.notna() & mom.notna()
    mom = mom.where(ok)
    month_end = pd.Series(dates, index=dates).groupby(dates.to_period("M")).transform("max") == dates
    spy = d["spy"]
    on = (spy > spy.rolling(200).mean()) if gate == "spy200" else pd.Series(True, index=dates)
    if risk_off is not None:
        on = on & ~risk_off.reindex(dates).fillna(False)
    rf = rf_daily(d).to_numpy()
    # Daily close-to-close returns, with the first day of each holding open-to-close (bought at the open).
    r_cc = (Cf / Cf.shift(1) - 1).to_numpy()
    r_oc = (C / O - 1).to_numpy()
    hold = np.zeros(C.shape[1], bool)
    out = np.zeros(len(dates))
    turnover_log = []
    i0 = max(int(dates.searchsorted(pd.Timestamp(start))), lookback + 1)
    pending = None
    for t in range(i0, len(dates)):
        # 1) today's return on yesterday's book; a rebalance decided at yesterday's close fills at today's open
        if pending is not None:
            new = pending
            o_prev = Cf.iloc[t - 1].to_numpy()
            night = np.nan_to_num(O.iloc[t].to_numpy() / o_prev - 1)
            r_night = night[hold].mean() if hold.any() else 0.0
            r_day = np.nan_to_num(r_oc[t][new]).mean() if new.any() else rf[t]
            trade = ((hold & ~new).sum() / hold.sum() if hold.any() else 0) + ((new & ~hold).sum() / new.sum() if new.any() else 0)
            turnover_log.append(trade)
            out[t] = (1 + r_night) * (1 + r_day) - 1 - trade * cost_bps / 1e4
            hold, pending = new, None
        else:
            out[t] = np.nan_to_num(r_cc[t][hold]).mean() if hold.any() else rf[t]
        # 2) at today's close: decide next month's book
        if month_end.iloc[t]:
            if on.iloc[t]:
                m = mom.iloc[t].dropna()
                pick = m.nlargest(top).index
                pending = C.columns.isin(pick)
            else:
                pending = np.zeros(C.shape[1], bool)
    r = pd.Series(out[i0:], index=dates[i0:])
    return {"returns": r, "turnover": float(np.mean(turnover_log)) * 12 if turnover_log else np.nan}


# ------------------------------------------------------------------------------------------------- stats


def stats(r: pd.Series, rf: pd.Series, start=None, end=None) -> dict:
    r = r.loc[start:end].dropna()
    if len(r) < 20:
        return {}
    e = (1 + r).cumprod()
    yrs = len(r) / 252
    ex = r - rf.reindex(r.index).fillna(0)
    return {"Return per year": float(e.iloc[-1] ** (1 / yrs) - 1), "Sharpe": float(ex.mean() / r.std() * np.sqrt(252)),
            "Worst drop": float((e / e.cummax() - 1).min()), "Volatility": float(r.std() * np.sqrt(252)),
            "Total": float(e.iloc[-1] - 1)}


def window_returns(series: dict) -> pd.DataFrame:
    rows = {}
    for w, (a, b) in WINDOWS.items():
        rows[w] = {k: float((1 + v.loc[a:b].iloc[1:]).prod() - 1) if len(v.loc[a:b]) > 1 else np.nan
                   for k, v in series.items()}
    return pd.DataFrame(rows).T


def trade_features(trades: pd.DataFrame, d: dict) -> pd.DataFrame:
    """The VIX, VIX term structure and GEX readings known at each trade's signal close."""
    t = trades[trades["Why it sold"] != "Open"].copy()
    sd = pd.to_datetime(t["Signal date"])
    t["VIX"] = d["vix"].reindex(sd).to_numpy()
    t["VIX/VIX3M"] = (d["vix"] / d["vix3m"]).reindex(sd).to_numpy()
    t["GEX pct"] = d["gex_pct"].reindex(sd).to_numpy()
    t["GEX"] = d["gex"].reindex(sd).to_numpy()
    t["SPY vs 200d"] = (d["spy"] / d["spy"].rolling(200).mean() - 1).reindex(sd).to_numpy()
    t["Window"] = np.where(sd <= pd.Timestamp(PICK[1]), "pick", "grade")
    return t


def bucket_table(t: pd.DataFrame, col: str, bins: list, labels: list) -> pd.DataFrame:
    t = t.assign(B=pd.cut(t[col], bins, labels=labels))
    g = t.groupby(["Window", "B"], observed=True)["Return"].agg(["count", "mean", lambda x: (x > 0).mean()])
    g.columns = ["Trades", "Avg trade", "Win rate"]
    return g.reset_index().assign(Feature=col)


# Entry filters to test, each a True/False series known at the signal close.
def filters(d: dict) -> dict:
    v, v3, g = d["vix"], d["vix3m"], d["gex_pct"]
    gex = d["gex"]
    return {
        "VIX below 30": v < 30,
        "VIX above 15": v > 15,
        "VIX 15-30": (v > 15) & (v < 30),
        "No VIX backwardation (VIX < VIX3M)": v < v3,
        "VIX backwardation only (VIX >= VIX3M)": v >= v3,
        "GEX below its 1-year median": g < 0.5,
        "GEX above its 1-year median": g >= 0.5,
        "GEX in its bottom 20%": g < 0.2,
        "GEX not in its bottom 20%": g >= 0.2,
        "GEX positive": gex > 0,
        "Low GEX or VIX above 20 (stress confluence)": (g < 0.3) | (v > 20),
    }


# ------------------------------------------------------------------------------------------------- main


def main(folder: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = load(folder)
    rf = rf_daily(d)
    dates = d["dates"]
    spy_r = d["spy"].pct_change().fillna(0)
    qqq_r = d["qqq"].pct_change().fillna(0)
    print("loaded", d["panel"]["Close"].shape, flush=True)

    dz = dive_zone(d)
    print("dive zone", flush=True)
    br = breakout(d)
    print("breakout", flush=True)
    series = {"Dive Zone": dz["returns"], "Tech Breakout Rider": br["returns"], "S&P 500 (SPY)": spy_r, "Nasdaq-100 (QQQ)": qqq_r}

    # Momentum leaders: a small grid, picked on the picking window only.
    grid = []
    mom_runs = {}
    for top in (5, 10, 20):
        for lb in (126, 252):
            for uni in ("sp500", "tech"):
                key = f"Momentum top {top}, {lb // 21}-month, {uni}"
                res = momentum_leaders(d, top=top, lookback=lb, universe=uni)
                mom_runs[key] = res["returns"]
                grid.append({"Variant": key, **{f"pick {k}": v for k, v in stats(res["returns"], rf, *PICK).items()},
                             **{f"grade {k}": v for k, v in stats(res["returns"], rf, *GRADE).items()},
                             "Turnover / yr": res["turnover"]})
                print(key, flush=True)
    grid = pd.DataFrame(grid).sort_values("pick Sharpe", ascending=False)
    grid.to_csv(OUT / "momentum_grid.csv", index=False)
    best = grid.iloc[0]["Variant"]
    series["Momentum Leaders"] = mom_runs[best]

    # Confluence filters on Dive Zone and Breakout Rider: trade buckets, then portfolio tests.
    feats = {"Dive Zone": trade_features(dz["trades"], d), "Tech Breakout Rider": trade_features(br["trades"], d)}
    buckets = []
    for name, t in feats.items():
        for col, bins, labels in (("VIX", [0, 15, 20, 25, 30, 200], ["<15", "15-20", "20-25", "25-30", "30+"]),
                                  ("VIX/VIX3M", [0, 0.9, 1.0, 5], ["contango <0.9", "flat 0.9-1", "backwardation >1"]),
                                  ("GEX pct", [-0.01, 0.2, 0.5, 0.8, 1.01], ["bottom 20%", "20-50%", "50-80%", "top 20%"])):
            buckets.append(bucket_table(t, col, bins, labels).assign(Strategy=name))
    pd.concat(buckets).to_csv(OUT / "confluence_buckets.csv", index=False)

    frows = []
    for fname, f in filters(d).items():
        for name, fn in (("Dive Zone", dive_zone), ("Tech Breakout Rider", breakout)):
            res = fn(d, entry_ok=f)
            r = res["returns"]
            frows.append({"Strategy": name, "Filter": fname,
                          **{f"pick {k}": v for k, v in stats(r, rf, *PICK).items()},
                          **{f"grade {k}": v for k, v in stats(r, rf, *GRADE).items()},
                          "Trades": int((res["trades"]["Why it sold"] != "Open").sum())})
            print(name, fname, flush=True)
    for name, r, tr in (("Dive Zone", dz["returns"], dz["trades"]), ("Tech Breakout Rider", br["returns"], br["trades"])):
        frows.append({"Strategy": name, "Filter": "None (as is)", **{f"pick {k}": v for k, v in stats(r, rf, *PICK).items()},
                      **{f"grade {k}": v for k, v in stats(r, rf, *GRADE).items()},
                      "Trades": int((tr["Why it sold"] != "Open").sum())})
    ftab = pd.DataFrame(frows)
    ftab.to_csv(OUT / "confluence_filters.csv", index=False)

    # Momentum with a VIX-backwardation risk-off switch (the one confluence that is about crashes).
    v, v3 = d["vix"], d["vix3m"]
    top, lb, uni = best.replace("Momentum top ", "").split(", ")
    kw = dict(top=int(top), lookback=int(lb.split("-")[0]) * 21, universe=uni)
    mom_rows = []
    for nm, ro in (("none", None), ("VIX backwardation -> T-bills", v >= v3), ("VIX above 30 -> T-bills", v > 30),
                   ("GEX bottom 10% -> T-bills", d["gex_pct"] < 0.1)):
        r = momentum_leaders(d, risk_off=ro, **kw)["returns"]
        mom_rows.append({"Risk-off switch": nm, **{f"pick {k}": x for k, x in stats(r, rf, *PICK).items()},
                         **{f"grade {k}": x for k, x in stats(r, rf, *GRADE).items()}})
    pd.DataFrame(mom_rows).to_csv(OUT / "momentum_switches.csv", index=False)

    # Headline table and the waves / crashes table.
    head = pd.DataFrame({k: {**{f"pick {a}": b for a, b in stats(r, rf, *PICK).items()},
                              **{f"grade {a}": b for a, b in stats(r, rf, *GRADE).items()}} for k, r in series.items()}).T
    head.to_csv(OUT / "headline.csv")
    window_returns(series).to_csv(OUT / "windows.csv")
    # The daily returns the Strategy Playbook page reads.
    ret = pd.DataFrame({"dive_zone": dz["returns"], "tech_breakout_rider": br["returns"], "spy": spy_r, "qqq": qqq_r,
                        "tbill": rf}).loc[PICK[0]:]
    ret.to_csv(Path(__file__).with_name("research_data") / "growth_returns.csv", float_format="%.7g")
    dz["trades"].to_csv(OUT / "dive_zone_trades.csv", index=False)
    br["trades"].to_csv(OUT / "breakout_trades.csv", index=False)
    print(head.round(3).to_string())
    print(window_returns(series).round(3).to_string())
    print(ftab.round(3).to_string())
    print(grid.round(3).head(12).to_string())
    print(run_guards(folder).round(3).to_string())
    print(crash_events(folder).round(3).to_string())
    print(run_fear(folder).round(3).head(10).to_string())



# ------------------------------------------------------------------------------------------------- crash guards


def crash_guards(d: dict) -> dict:
    """Extra conditions that could keep Dive Zone from buying into a sector-wide breakdown like Oct-Nov 2026.
    Each is {"entry_ok": series} (market-wide) or {"buy_ok": frame} (stock by stock), known at the signal close."""
    C = d["panel"]["Close"]
    Cf = C.ffill()
    mem = d["members"].reindex(index=C.index, columns=C.columns).fillna(False)
    above50 = (Cf > Cf.rolling(50, min_periods=40).mean()).where(mem & C.notna())
    breadth = above50.sum(axis=1) / above50.notna().sum(axis=1).replace(0, np.nan)
    q, s, v = d["qqq"], d["spy"], d["vix"]
    etf = d["etf"].reindex(C.index).ffill()
    etf_up = etf > etf.rolling(50, min_periods=40).mean()
    sec_etf = {t: ld.GICS_ETF.get(sec) for t, sec in d["sectors"].items()}
    sec_up = pd.DataFrame({c: etf_up[sec_etf[c]] if sec_etf.get(c) in etf_up else True for c in C.columns}, index=C.index)
    return {
        "Breadth: 40%+ of S&P stocks above their 50-day": {"entry_ok": breadth >= 0.4},
        "Breadth: 50%+ of S&P stocks above their 50-day": {"entry_ok": breadth >= 0.5},
        "QQQ above its 50-day": {"entry_ok": q > q.rolling(50).mean()},
        "SPY 20-day return above -5%": {"entry_ok": s / s.shift(20) - 1 > -0.05},
        "VIX not up 30%+ in 5 days": {"entry_ok": v / v.shift(5) - 1 < 0.30},
        "Stock's sector ETF above its 50-day": {"buy_ok": sec_up},
        "Stock above its 50-day": {"buy_ok": Cf > Cf.rolling(50, min_periods=40).mean()},
    }


def run_guards(folder: str = ".lab") -> pd.DataFrame:
    d = load(folder)
    rf = rf_daily(d)
    rows = []
    cases = {"None (as is)": {}, **crash_guards(d)}
    for name, kw in cases.items():
        res = dive_zone(d, **kw)
        r = res["returns"]
        w = window_returns({"x": r})["x"]
        rows.append({"Guard": name, **{f"pick {k}": v for k, v in stats(r, rf, *PICK).items()},
                     **{f"grade {k}": v for k, v in stats(r, rf, *GRADE).items()},
                     "2022": w["2022 bear market"], "Tariff crash 2025": w["Tariff crash (Feb 19 - Apr 8 2025)"],
                     "Nov 2026 selloff": w["Nov 2026 selloff (Oct 9 - Nov 6 2026)"],
                     "Trades": int((res["trades"]["Why it sold"] != "Open").sum())})
        print(name, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "dive_zone_guards.csv", index=False)
    return out


# ------------------------------------------------------------------------------------------------- crash buying


def crash_events(folder: str = ".lab") -> pd.DataFrame:
    """What QQQ (since 1999) did after fear events, bought at the next open: forward returns over 1, 3, 6 and
    12 months, against every day's forward return. Events are counted once per 20 sessions."""
    mk = pickle.load(open(Path(folder) / "market.pkl", "rb"))  # written by SharkFin's own download step
    c, o = mk["Close"]["QQQ"].dropna(), mk["Open"]["QQQ"].dropna()
    v = mk["Close"]["^VIX"].reindex(c.index).ffill()
    v3 = mk["Close"]["^VIX3M"].reindex(c.index).ffill()
    r1 = c.pct_change()
    hi = c.rolling(252, min_periods=60).max()
    sma200 = c.rolling(200).mean()
    ev = {
        "QQQ fell 4%+ in a day": r1 <= -0.04,
        "QQQ fell 6%+ in a day": r1 <= -0.06,
        "VIX closed above 30": v > 30,
        "VIX closed above 40": v > 40,
        "VIX above VIX3M (backwardation)": v > v3,
        "QQQ 10% under its 1-year high": c / hi - 1 <= -0.10,
        "QQQ 20% under its 1-year high": c / hi - 1 <= -0.20,
        "QQQ 10% off its high but above its 200-day": (c / hi - 1 <= -0.10) & (c > sma200),
        "Every day": pd.Series(True, index=c.index),
    }
    rows = []
    entry = o.shift(-1)  # bought at the next session's open
    for name, flag in ev.items():
        f = flag.fillna(False).to_numpy()
        idx, last = [], -10_000
        for i in np.flatnonzero(f):
            if name == "Every day" or i - last >= 20:
                idx.append(i)
                last = i
        row = {"Event": name, "Events": len(idx)}
        for lbl, h in (("1 month", 21), ("3 months", 63), ("6 months", 126), ("12 months", 252)):
            fw = [c.iloc[i + h] / entry.iloc[i] - 1 for i in idx if i + h < len(c) and np.isfinite(entry.iloc[i])]
            row[f"{lbl} avg"] = float(np.mean(fw)) if fw else np.nan
            row[f"{lbl} median"] = float(np.median(fw)) if fw else np.nan
            row[f"{lbl} up"] = float(np.mean(np.array(fw) > 0)) if fw else np.nan
            row[f"{lbl} worst"] = float(np.min(fw)) if fw else np.nan
        row["Latest"] = c.index[idx[-1]].date() if idx else None
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "crash_events.csv", index=False)
    return out


def fear_buyer(d: dict, level: float = 30.0, hold: int = 126, asset: str = "qqq", start=PICK[0]) -> pd.Series:
    """Own QQQ (or SPY) for ``hold`` sessions after any VIX close above ``level`` (a new close above it restarts
    the clock), T-bills otherwise. Decided at the close, bought at the next open, sold at the open."""
    c, o = d[asset], d[f"{asset}_open"]
    v = d["vix"]
    rf = rf_daily(d)
    sig = (v > level).fillna(False).to_numpy()
    n = len(c)
    pos = np.zeros(n)  # 1 = held through this session's open-to-open
    left = 0
    for t in range(n - 1):
        if sig[t]:
            left = hold
        if left > 0:
            pos[t + 1] = 1
            left -= 1
    oo = (o.shift(-1) / o - 1).fillna(0).to_numpy()  # open-to-open, credited to the session it starts
    r = np.where(pos > 0, oo, rf.to_numpy())
    flips = np.abs(np.diff(np.r_[0, pos]))
    r = r - flips * COST_BPS / 1e4
    s = pd.Series(r, index=c.index)
    return s.loc[start:]


def run_fear(folder: str = ".lab") -> pd.DataFrame:
    d = load(folder)
    rf = rf_daily(d)
    rows = []
    for asset in ("qqq", "spy"):
        for level in (25.0, 30.0, 35.0, 40.0):
            for hold in (63, 126, 252):
                r = fear_buyer(d, level, hold, asset)
                inm = float((r != rf.reindex(r.index)).mean())
                rows.append({"Asset": asset.upper(), "VIX above": level, "Hold days": hold, "Time in market": inm,
                             **{f"pick {k}": v for k, v in stats(r, rf, *PICK).items()},
                             **{f"grade {k}": v for k, v in stats(r, rf, *GRADE).items()}})
    out = pd.DataFrame(rows).sort_values("pick Sharpe", ascending=False)
    out.to_csv(OUT / "fear_buyer.csv", index=False)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".lab")


# ------------------------------------------------------------------------------------------------- entry zones


def entry_zones(folder: str = ".lab", split: str = "2016-01-01") -> pd.DataFrame:
    """Where should a long-term buyer enter? For every S&P 500 member at each month's last close, which price zone
    it sat in (from past prices only), and what it did over the next 3, 6 and 12 months against SPY, bought at the
    next open. Zones are judged on 2006-15 and checked on 2016-26."""
    d = load(folder)
    C, O = d["panel"]["Close"], d["panel"]["Open"]
    Cf = C.ffill()
    mem = d["members"].reindex(index=C.index, columns=C.columns).fillna(False) & C.notna()
    sma50, sma200 = Cf.rolling(50, min_periods=45).mean(), Cf.rolling(200, min_periods=180).mean()
    hi52 = Cf.rolling(252, min_periods=200).max()
    delta = Cf.diff()
    up, dn = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean(), (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    gain6 = Cf / Cf.shift(126) - 1
    lead = gain6.where(mem).rank(axis=1, pct=True) >= 0.7  # top 30% by 6-month gain: the growth leaders
    above200 = Cf > sma200
    off = Cf / hi52 - 1
    x50 = Cf / sma50 - 1
    zones = {
        "Any day (baseline)": mem,
        "Pullback to the 50-day in an uptrend (0-5% above it, above the 200-day)": above200 & (x50 >= 0) & (x50 < 0.05),
        "Under the 50-day but above the 200-day": above200 & (x50 < 0),
        "Near the 200-day (within 5%)": (Cf / sma200 - 1).abs() < 0.05,
        "10-25% under the 52-week high, above the 200-day": above200 & (off <= -0.10) & (off > -0.25),
        "RSI(14) under 40, above the 200-day": above200 & (rsi < 40),
        "Within 3% of the 52-week high": off > -0.03,
        "Extended: 15%+ above the 50-day": x50 >= 0.15,
        "Below the 200-day": ~above200 & sma200.notna(),
    }
    month_end = pd.Series(C.index, index=C.index).groupby(C.index.to_period("M")).transform("max") == C.index
    ends = np.flatnonzero(month_end.to_numpy())
    ends = ends[(C.index[ends] >= pd.Timestamp(PICK[0])) & (ends + 1 < len(C))]
    spy = d["spy"]
    rows = []
    for scope, extra in (("All stocks", None), ("Growth leaders (top 30% by 6-month gain)", lead)):
        for zn, z in zones.items():
            zz = z & mem if extra is None else z & mem & extra
            for h in (63, 126, 252):
                rec = []
                for i in ends:
                    if i + h >= len(C):
                        continue
                    pick = zz.iloc[i].to_numpy()
                    if not pick.any():
                        continue
                    buy = O.iloc[i + 1].to_numpy()[pick]
                    later = Cf.iloc[i + h].to_numpy()[pick]
                    r = later / buy - 1
                    r = r[np.isfinite(r)]
                    if not len(r):
                        continue
                    b = spy.iloc[i + h] / d["spy_open"].iloc[i + 1] - 1
                    rec.append((C.index[i], r.mean(), np.median(r), (r > b).mean(), r.mean() - b, len(r)))
                if not rec:
                    continue
                df = pd.DataFrame(rec, columns=["date", "mean", "median", "beat", "excess", "n"])
                for win, part in (("2006-15", df[df.date < split]), ("2016-26", df[df.date >= split])):
                    rows.append({"Scope": scope, "Zone": zn, "Horizon": f"{h // 21} months", "Window": win,
                                 "Avg return": part["mean"].mean(), "Avg vs SPY": part["excess"].mean(),
                                 "Beat SPY": part["beat"].mean(), "Stocks per month": part["n"].mean()})
        print(scope, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "entry_zones.csv", index=False)
    return out


# ------------------------------------------------------------------------------------------------- what matters per horizon


def horizon_signals(folder: str = ".lab") -> pd.DataFrame:
    """Which price-based readings sort S&P 500 stocks by their next 1 week to 12 months? At each month end, the
    rank correlation (IC) between each reading and the forward return, from the next open, across the members
    that day; averaged by decade. Fundamentals aren't point-in-time in Yahoo, so they aren't tested here."""
    d = load(folder)
    C, O = d["panel"]["Close"], d["panel"]["Open"]
    Cf = C.ffill()
    mem = d["members"].reindex(index=C.index, columns=C.columns).fillna(False) & C.notna()
    r = lambda n: Cf / Cf.shift(n) - 1
    sig = {
        "Last week's return (reversal)": -r(5),
        "Last month's return (reversal)": -r(21),
        "12-month momentum, skipping the last month": Cf.shift(21) / Cf.shift(252) - 1,
        "6-month momentum": r(126),
        "Closeness to the 52-week high": Cf / Cf.rolling(252, min_periods=200).max(),
        "Low volatility (3 months)": -(Cf.pct_change().rolling(63).std()),
        "Above the 200-day average": Cf / Cf.rolling(200).mean() - 1,
    }
    month_end = pd.Series(C.index, index=C.index).groupby(C.index.to_period("M")).transform("max") == C.index
    ends = np.flatnonzero(month_end.to_numpy())
    ends = ends[(C.index[ends] >= pd.Timestamp(PICK[0])) & (ends + 1 < len(C))]
    rows = []
    for h, lbl in ((5, "1 week"), (21, "1 month"), (63, "3 months"), (126, "6 months"), (252, "12 months")):
        for name, s in sig.items():
            ics = []
            for i in ends:
                if i + h >= len(C):
                    continue
                m = mem.iloc[i].to_numpy()
                x = s.iloc[i].to_numpy()[m]
                fwd = (Cf.iloc[i + h].to_numpy() / O.iloc[i + 1].to_numpy() - 1)[m]
                ok = np.isfinite(x) & np.isfinite(fwd)
                if ok.sum() < 50:
                    continue
                ics.append((C.index[i], pd.Series(x[ok]).rank().corr(pd.Series(fwd[ok]).rank())))
            ic = pd.DataFrame(ics, columns=["date", "ic"])
            for win, part in (("2006-15", ic[ic.date < "2016-01-01"]), ("2016-26", ic[ic.date >= "2016-01-01"])):
                rows.append({"Horizon": lbl, "Signal": name, "Window": win, "IC": part["ic"].mean(),
                             "Right direction": (part["ic"] > 0).mean(), "Months": len(part)})
        print(lbl, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "horizon_signals.csv", index=False)
    return out


def earnings_horizons(folder: str = ".lab", n: int = 200, seed: int = 7) -> pd.DataFrame:
    """After an earnings report, does the surprise or the market's reaction tell you anything about the next 1 week
    to 12 months? For ``n`` random stocks that were ever in the S&P 500 since 2016 (Yahoo keeps about 10 years of
    reports), each report is sorted by EPS surprise and by the reaction vs SPY (close before the report to
    the close of the first full day after it). The forward return vs SPY is measured from the next open after that
    day, so nothing the bucket uses is from after the buy. Stocks Yahoo no longer lists are missing (a mild
    survivor tilt that affects every bucket alike)."""
    import yfinance as yf

    from . import data

    d = load(folder)
    C, O = d["panel"]["Close"].ffill(), d["panel"]["Open"]
    spy, spyo = d["spy"], d["spy_open"]
    names = [t for t in data.sp500_ever("2016-01-01") if t in C.columns]
    rng = np.random.default_rng(seed)
    names = list(rng.choice(sorted(names), size=min(n, len(names)), replace=False))
    cache = Path(folder) / "earnings"
    cache.mkdir(exist_ok=True)

    def get(t):
        f = cache / f"{t}.pkl"
        if f.exists():
            return t, pd.read_pickle(f)
        try:
            ed = yf.Ticker(t).get_earnings_dates(limit=44)
        except Exception:
            ed = None
        if isinstance(ed, pd.DataFrame):
            ed.to_pickle(f)
        return t, ed

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(6) as ex:
        eds = dict(ex.map(get, names))
    idx = C.index
    rows = []
    for t, ed in eds.items():
        if not isinstance(ed, pd.DataFrame) or ed.empty or "Reported EPS" not in ed:
            continue
        ed = ed.dropna(subset=["Reported EPS"]).copy()
        ed.index = pd.to_datetime(ed.index)
        if ed.index.tz is not None:
            ed.index = ed.index.tz_convert("America/New_York").tz_localize(None)
        c, o = C[t], O[t]
        for when, r in ed.iterrows():
            # Reports before the open react that day; after the close, the next day. i is that first session.
            day = when.normalize()
            i = int(idx.searchsorted(day + pd.Timedelta(days=1))) if when.hour >= 9 else int(idx.searchsorted(day))
            if i < 2 or i + 2 >= len(idx):
                continue
            pre = i - 1  # the last close before the report
            if not (np.isfinite(c.iloc[pre]) and np.isfinite(c.iloc[i])):
                continue
            react = c.iloc[i] / c.iloc[pre] - 1 - (spy.iloc[i] / spy.iloc[pre] - 1)
            sur = r.get("Surprise(%)", np.nan)
            row = {"ticker": t, "date": idx[i], "surprise": sur / 100 if np.isfinite(sur) else np.nan, "reaction": react}
            for h, lbl in ((5, "1 week"), (21, "1 month"), (63, "3 months"), (126, "6 months"), (252, "12 months")):
                j = i + h
                if j < len(idx) and np.isfinite(o.iloc[i + 1]) and np.isfinite(c.iloc[j]):
                    row[lbl] = c.iloc[j] / o.iloc[i + 1] - 1 - (spy.iloc[j] / spyo.iloc[i + 1] - 1)
            rows.append(row)
    ev = pd.DataFrame(rows).dropna(subset=["reaction"])
    ev.to_csv(Path(folder) / "earnings_events.csv", index=False)
    hz = ["1 week", "1 month", "3 months", "6 months", "12 months"]
    out = []
    for what, col in (("EPS surprise", "surprise"), ("Reaction vs SPY", "reaction")):
        e = ev.dropna(subset=[col])
        q = e.groupby(e["date"].dt.to_period("Q"))[col].transform(lambda s: pd.qcut(s.rank(method="first"), 5,
                                                                                    labels=False) if len(s) >= 10 else np.nan)
        for b in range(5):
            part = e[q == b]
            out.append({"Sorted by": what, "Fifth": b + 1, "Reports": len(part), "Median value": part[col].median(),
                        **{h: part[h].mean() for h in hz}, **{f"{h} beat SPY": (part[h] > 0).mean() for h in hz}})
    res = pd.DataFrame(out)
    res.to_csv(OUT / "earnings_horizons.csv", index=False)
    return res
