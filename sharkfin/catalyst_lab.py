"""Catalyst lab (Nov 2026): earnings beats, washed-out breadth, FDA decisions, Speculation Radar stages and Kalshi odds,
each backtested on point-in-time data.

Run ``python -m sharkfin.catalyst_lab DATA_DIR``. DATA_DIR holds:
  * ohlcv.pkl   {"Open"|"High"|"Low"|"Close"|"Volume": dates x tickers}: every stock in the S&P 500 at some point
                since 2005, the Nasdaq-100, the Speculation Radar plays, SPY/QQQ/IWM/XBI/IBB/RSP and ^VIX, daily since 2004
                (Yahoo, split and dividend adjusted; rows where SPY did not trade are dropped)
  * earn.pkl    {ticker: Yahoo earnings-dates table (limit=100, about 25 years, with report times)}
  * fda.pkl     optional: {"ev": FDA decisions with tickers, "px": prices, "sh": share counts} (see ``fda_events``)
  * kalshi.pkl  optional: Kalshi daily candles for the Fed-decision and recession series
It writes its tables to ``research_data/catalyst_lab``.

No look-ahead:
  * an earnings report counts from its time stamp: one after 4pm reacts the next session; trades fill at the open
    after the reaction day, so the reaction itself is known when the trade is placed;
  * every feature for the beat model is known the day before the report; the model is fit on 2006 - Oct 2021 and
    graded on Oct 2021 - Nov 2026 (the same split as growth_lab);
  * breadth on a day uses only that day's closes and only stocks in the S&P 500 that day;
  * FDA decisions are dated by the FDA's action date (approvals) or letter date (rejections); a test that buys
    before the decision uses both outcomes, so it cannot pick winners it didn't know about;
  * the one forward read (``_forward``) books a trade's outcome, never a decision.
Survivorship: Yahoo has no prices for many stocks that later failed or were bought, so small biotechs that went to
zero after a rejection are under-counted. Results there lean optimistic.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PICK = ("2006-01-03", "2021-10-12")
GRADE = ("2021-10-13", "2026-11-06")
COST_BPS = 10.0
OUT = Path(__file__).with_name("research_data") / "catalyst_lab"
ETFS = ("SPY", "QQQ", "IWM", "XBI", "IBB", "RSP")


def _forward(s: pd.Series | pd.DataFrame, k: int):
    """Return over the next ``k`` rows: a trade's outcome, used only to grade signals."""
    return s.shift(-k) / s - 1


def load(folder: str | Path) -> dict:
    """Read the research files this script's own download step wrote (pickle: only ever load files you made)."""
    f = Path(folder)
    px = pickle.load(open(f / "ohlcv.pkl", "rb"))
    keep = px["Close"]["SPY"].notna()
    px = {k: v.loc[keep] for k, v in px.items()}
    earn = pickle.load(open(f / "earn.pkl", "rb"))
    out = {"px": px, "earn": {k: v for k, v in earn.items() if isinstance(v, pd.DataFrame) and len(v)}}
    for name in ("fda", "kalshi"):
        if (f / f"{name}.pkl").exists():
            out[name] = pickle.load(open(f / f"{name}.pkl", "rb"))
    return out


def members(close: pd.DataFrame) -> pd.DataFrame:
    from . import data
    return data.sp500_members(close.index, close.columns).reindex(index=close.index, columns=close.columns) \
        .fillna(False).astype(bool)


def stocks(close: pd.DataFrame) -> list:
    return [c for c in close.columns if not c.startswith("^") and c not in ETFS]


# ----------------------------------------------------------------------------------------------- breadth


def breadth(close: pd.DataFrame, volume: pd.DataFrame, mem: pd.DataFrame, min_n: int = 100) -> pd.DataFrame:
    """Two daily washout readings over the S&P 500 members of that day.

    adv:   share of members that rose (advancers / (advancers + decliners))
    upvol: share of dollar volume in rising members, the reading behind Lowry's "90% down days"
           (below 0.10 means 90%+ of the day's volume was in falling stocks)."""
    r = close.pct_change(fill_method=None)
    m = mem.reindex_like(r).fillna(False).astype(bool)
    up = ((r > 0) & m).sum(axis=1)
    dn = ((r < 0) & m).sum(axis=1)
    dv = (volume.reindex_like(close) * close.shift(1)).where(m)
    upv = dv.where(r > 0).sum(axis=1)
    dnv = dv.where(r < 0).sum(axis=1)
    out = pd.DataFrame({"adv": up / (up + dn).replace(0, np.nan), "upvol": upv / (upv + dnv).replace(0, np.nan),
                        "n": up + dn})
    return out[out["n"] > min_n]   # drops half-days and holidays where few members printed


def first_in(sig: pd.Series, gap: int = 10) -> pd.Series:
    """The first day of each run of signals, with at least ``gap`` quiet days before it (one entry per episode)."""
    sig = sig.fillna(False).astype(bool)
    return sig & ~sig.shift(1).rolling(gap, min_periods=1).max().fillna(0).astype(bool)


def breadth_setups(b: pd.DataFrame, spy: pd.Series, vix: pd.Series, start=PICK[0]) -> pd.DataFrame:
    """SPY's return 1, 3, 6 and 12 months after each washout episode, beside every day as the baseline."""
    spy = spy.reindex(b.index)
    vix = vix.reindex(b.index)
    sma200 = spy.rolling(200).mean()
    off = spy / spy.rolling(252, min_periods=50).max() - 1
    H = {"1 month": 21, "3 months": 63, "6 months": 126, "12 months": 252}
    fw = {h: _forward(spy, k) for h, k in H.items()}
    cases = {"Every day (baseline)": pd.Series(True, index=b.index)}
    for thr in (0.2, 0.08):
        s = b["upvol"] < thr
        cases[f"Up-volume share below {thr}"] = first_in(s)
        cases[f"  below {thr}, S&P above its 200-day"] = first_in(s & (spy > sma200))
        cases[f"  below {thr}, S&P below its 200-day"] = first_in(s & (spy <= sma200))
        cases[f"  below {thr}, VIX 25 or higher"] = first_in(s & (vix >= 25))
        cases[f"  below {thr}, S&P 10%+ off its high"] = first_in(s & (off <= -0.10))
        a = b["adv"] < thr
        cases[f"Advancers share below {thr}"] = first_in(a)
    cases["S&P down 2%+ in a day (no breadth)"] = first_in(spy.pct_change() <= -0.02)
    w = b["upvol"] < 0.10
    cases["Second 90% down day within 10 days"] = first_in(w & (w.shift(1).rolling(9).sum() >= 1))
    cases["90% up day within 10 days of a 90% down day"] = first_in((b["upvol"] > 0.9) & (w.shift(1).rolling(10).sum() >= 1))
    rows = []
    for name, sig in cases.items():
        for per, (a, z) in {"2006-2026": (start, GRADE[1]), "Pick 2006-2021": PICK, "Grade 2021-2026": GRADE}.items():
            idx = sig[a:z]
            idx = idx[idx].index
            row = {"Setup": name, "Period": per, "Episodes": len(idx)}
            for h in H:
                x = fw[h].reindex(idx).dropna()
                row[f"SPY {h}"] = x.mean() if len(x) else np.nan
                row[f"Up after {h}"] = (x > 0).mean() if len(x) else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------- earnings


def _earnings_table(ed: pd.DataFrame) -> pd.DataFrame:
    ed = ed.copy()
    ed.index = pd.to_datetime(ed.index)
    if ed.index.tz is not None:
        ed.index = ed.index.tz_convert("America/New_York").tz_localize(None)
    ed = ed.dropna(subset=["Reported EPS"]).sort_index()
    return ed[~ed.index.normalize().duplicated(keep="last")]


def earnings_events(px: dict, earnings: dict, mem: pd.DataFrame) -> pd.DataFrame:
    """One row per report by a stock that was in the S&P 500 that day: what was known the day before, the reaction,
    and returns vs SPY from the open after the reaction day."""
    C, O, H, L, V = (px[k] for k in ("Close", "Open", "High", "Low", "Volume"))
    idx = C.index
    spy, vix = C["SPY"], C["^VIX"]
    spy200 = spy.rolling(200).mean()
    rows = []
    for s, ed in earnings.items():
        if s not in C:
            continue
        ed = _earnings_table(ed)
        sur = pd.to_numeric(ed["Surprise(%)"], errors="coerce")
        eps = pd.to_numeric(ed["Reported EPS"], errors="coerce")
        est = pd.to_numeric(ed["EPS Estimate"], errors="coerce")
        c, o, h, lo, v = C[s], O[s], H[s], L[s], V[s]
        for j, t in enumerate(ed.index):
            hr = t.hour + t.minute / 60
            i = int(idx.searchsorted(t.normalize()))
            if hr >= 16 and i < len(idx) and idx[i] == t.normalize():
                i += 1                                   # after the close: the market reacts next session
            if i < 260 or i >= len(idx) - 1 or not mem[s].iloc[i] or not np.isfinite(c.iloc[i - 1]):
                continue
            p0 = c.iloc[i - 1]
            prev = sur.iloc[:j]
            streak = 0
            for x in prev.iloc[::-1].head(8):
                if not np.isfinite(x) or x <= 0:
                    break
                streak += 1
            base = abs(eps.iloc[j - 4]) if j >= 4 else np.nan
            rng = h.iloc[i] - lo.iloc[i]
            vol50 = v.iloc[i - 50:i].mean()
            r = dict(sym=s, date=idx[i], timing="after close" if hr >= 16 else ("before open" if 0 < hr < 9.5 else "unknown"),
                     surprise=sur.iloc[j], streak=streak,
                     prev_sur=prev.iloc[-1] if len(prev) else np.nan, avg_sur4=prev.tail(4).mean() if len(prev) else np.nan,
                     beat_rate8=(prev.tail(8) > 0).mean() if len(prev) else np.nan,
                     yoy=(eps.iloc[j] - eps.iloc[j - 4]) / base if base and base > 0.01 else np.nan,
                     est_yoy=(est.iloc[j] - eps.iloc[j - 4]) / base if base and base > 0.01 else np.nan,
                     pre1m=p0 / c.iloc[i - 22] - 1, pre3m=p0 / c.iloc[i - 64] - 1, pre12m=p0 / c.iloc[i - 253] - 1,
                     vs50=p0 / c.iloc[i - 50:i].mean() - 1, vs200=p0 / c.iloc[i - 200:i].mean() - 1,
                     off_hi=p0 / c.iloc[i - 252:i].max() - 1,
                     gap=o.iloc[i] / p0 - 1, react=c.iloc[i] / p0 - 1, spy_react=spy.iloc[i] / spy.iloc[i - 1] - 1,
                     close_pos=(c.iloc[i] - lo.iloc[i]) / rng if rng > 0 else np.nan,
                     volx=v.iloc[i] / vol50 if vol50 > 0 else np.nan,
                     spy_up=float(spy.iloc[i - 1] > spy200.iloc[i - 1]), vix=vix.iloc[i - 1])
            entry = o.iloc[i + 1]
            for lab, k in (("1m", 21), ("3m", 63), ("6m", 126)):
                e = i + 1 + k
                if e < len(idx) and np.isfinite(entry):
                    last = c.iloc[i + 1:e + 1].dropna()
                    if len(last):    # a stock that stops trading is sold at its last price
                        r["x" + lab] = (last.iloc[-1] / entry - 1) - (spy.iloc[e] / spy.iloc[i + 1] - 1)
            for d in (5, 10, 21):     # waiting d days after the reaction, same exit day as the 3-month trade
                e = i + 1 + 63
                if e < len(idx) and np.isfinite(c.iloc[i + d]) and np.isfinite(c.iloc[e]):
                    r[f"x3m_wait{d}"] = (c.iloc[e] / c.iloc[i + d] - 1) - (spy.iloc[e] / spy.iloc[i + d] - 1)
            rows.append(r)
    df = pd.DataFrame(rows)
    df["xreact"] = df["react"] - df["spy_react"]
    return df


POST_BEAT = {
    "Every report": lambda d: d["surprise"].notna(),
    "Any beat": lambda d: d["surprise"] > 0,
    "Beat by 10%+": lambda d: d["surprise"] > 10,
    "Beat 10%+ and gapped up 3%+": lambda d: (d["surprise"] > 10) & (d["gap"] > 0.03),
    "Beat 10%+ and beat SPY by 5%+ that day": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05),
    "  + closed in the top half of the day's range": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["close_pos"] > 0.5),
    "  + volume 2x normal": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["volx"] > 2),
    "  + stock above its 200-day": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["vs200"] > 0),
    "  + S&P above its 200-day": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["spy_up"] > 0),
    "  + EPS up 25%+ on a year ago": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["yoy"] > 0.25),
    "  + 3+ beats in a row before": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["streak"] >= 3),
    "  + within 10% of its 52-week high": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["off_hi"] > -0.10),
    "  + 30%+ below its 52-week high": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["off_hi"] < -0.30),
    "  + 30%+ below high and EPS up 25%+": lambda d: (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["off_hi"] < -0.30) & (d["yoy"] > 0.25),
    "Beat SPY by 8%+ on the reaction day (any surprise)": lambda d: d["xreact"] > 0.08,
    "Beat but fell 5%+ (sell the news)": lambda d: (d["surprise"] > 0) & (d["xreact"] < -0.05),
    "Missed and fell 5%+": lambda d: (d["surprise"] < 0) & (d["xreact"] < -0.05),
}


def post_beat_table(ev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, rule in POST_BEAT.items():
        m = rule(ev).fillna(False)
        row = {"Setup": name}
        for per, (a, z) in {"pick": PICK, "grade": GRADE}.items():
            x = ev[m & ev["date"].between(a, z)]
            row[f"Reports ({per})"] = len(x)
            for h in ("x1m", "x3m", "x6m"):
                row[f"{h[1:]} vs SPY ({per})"] = x[h].mean()
            row[f"Beat SPY over 3m ({per})"] = (x["x3m"] > 0).mean()
            row[f"Median 3m vs SPY ({per})"] = x["x3m"].median()
        rows.append(row)
    return pd.DataFrame(rows)


def entry_delay_table(ev: pd.DataFrame, rule: str = "Beat 10%+ and beat SPY by 5%+ that day") -> pd.DataFrame:
    m = POST_BEAT[rule](ev).fillna(False)
    rows = []
    for col, lab in (("x3m", "Next open"), ("x3m_wait5", "5 days later"), ("x3m_wait10", "10 days later"),
                     ("x3m_wait21", "A month later")):
        rows.append({"Buy": lab, "Pick 2006-21": ev.loc[m & ev["date"].between(*PICK), col].mean(),
                     "Grade 2021-26": ev.loc[m & ev["date"].between(*GRADE), col].mean(),
                     "Share that beat SPY": (ev.loc[m, col] > 0).mean()})
    return pd.DataFrame(rows)


BEAT_FEATURES = ["streak", "prev_sur", "avg_sur4", "beat_rate8", "pre1m", "pre3m", "pre12m", "vs50", "vs200",
                 "off_hi", "est_yoy", "vix", "spy_up"]
BEAT_TARGETS = {"Beats the estimate": lambda d: d["surprise"] > 0,
                "Beats by 10%+": lambda d: d["surprise"] > 10,
                "Rises vs SPY on the day": lambda d: d["xreact"] > 0,
                "Jumps 10%+ vs SPY": lambda d: d["xreact"] > 0.10,
                "Falls 10%+ vs SPY": lambda d: d["xreact"] < -0.10}


def beat_model(ev: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Gradient-boosted odds of each outcome from what was known the day before the report.
    Fit on the picking window, graded on the five years after it."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    d = ev[ev["surprise"].notna()].copy()
    d["prev_sur"] = d["prev_sur"].clip(-100, 100)
    d["avg_sur4"] = d["avg_sur4"].clip(-100, 100)
    d["est_yoy"] = d["est_yoy"].clip(-2, 5)
    tr, te = d["date"].between(*PICK), d["date"].between(*GRADE)
    rows, models = [], {}
    for name, rule in BEAT_TARGETS.items():
        y = rule(d).astype(int)
        g = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=100,
                                           l2_regularization=1.0, random_state=0)
        g.fit(d.loc[tr, BEAT_FEATURES], y[tr])
        p = g.predict_proba(d.loc[te, BEAT_FEATURES])[:, 1]
        dec = pd.qcut(p, 10, labels=False, duplicates="drop")
        yt = y[te].to_numpy()
        rows.append({"Outcome": name, "Base rate (grade)": yt.mean(), "AUC (grade)": roc_auc_score(yt, p),
                     "Top 10% of odds": yt[dec == dec.max()].mean(), "Bottom 10% of odds": yt[dec == 0].mean()})
        d.loc[te, "p_" + name] = p
        models[name] = g
    g = d[te].copy()
    g["Decile"] = pd.qcut(g["p_Beats the estimate"], 10, labels=False) + 1
    dec = g.groupby("Decile").agg(Reports=("sym", "size"), **{"Predicted beat odds": ("p_Beats the estimate", "mean"),
                                  "Actually beat": ("surprise", lambda x: (x > 0).mean()),
                                  "Rose vs SPY on the day": ("xreact", lambda x: (x > 0).mean()),
                                  "Avg day vs SPY": ("xreact", "mean"),
                                  "Next 3m vs SPY": ("x3m", "mean")}).reset_index()
    return pd.DataFrame(rows), dec, models


# ----------------------------------------------------------------------------------------------- FDA


SIZES = [(0, 3e8, "Micro (under $300M)"), (3e8, 2e9, "Small ($300M-2B)"), (2e9, 1e10, "Mid ($2-10B)"),
         (1e10, 1e15, "Large (over $10B)")]


def fda_study(fda: dict) -> pd.DataFrame:
    """Returns vs XBI around FDA decisions (approvals of new drugs and biologics, and complete response letters)
    for listed sponsors, by company size the day before."""
    ev, px, sh = fda["ev"], fda["px"], fda["sh"]
    C = px["Close"]
    C = C[C["XBI"].notna()]
    xbi, idx = C["XBI"], C.index
    rows = []
    for _, e in ev.iterrows():
        s = e["ticker"]
        if s not in C:
            continue
        c = C[s]
        i = int(idx.searchsorted(e["date"]))
        if i < 45 or i + 3 >= len(idx) or not np.isfinite(c.iloc[i - 1]):
            continue
        mcap = np.nan
        shs = sh.get(s)
        if shs is not None and len(shs):
            sx = shs.copy()
            sx.index = pd.to_datetime(sx.index)
            if sx.index.tz is not None:
                sx.index = sx.index.tz_localize(None)
            sx = sx[sx.index <= idx[i - 1]]
            if len(sx):
                mcap = float(sx.iloc[-1]) * c.iloc[i - 1]

        def vs_xbi(a, b):
            if b >= len(idx) or not (np.isfinite(c.iloc[a]) and np.isfinite(c.iloc[b])):
                return np.nan
            return (c.iloc[b] / c.iloc[a] - 1) - (xbi.iloc[b] / xbi.iloc[a] - 1)

        size = next((lab for lo, hi, lab in SIZES if lo <= mcap < hi), "Unknown") if np.isfinite(mcap) else "Unknown"
        rows.append(dict(ticker=s, date=idx[i], kind=e["kind"], size=size, mcap=mcap,
                         run40=vs_xbi(i - 41, i - 1), run20=vs_xbi(i - 21, i - 1), decision=vs_xbi(i - 1, i + 2),
                         after1m=vs_xbi(i + 2, i + 23), after3m=vs_xbi(i + 2, i + 65), after6m=vs_xbi(i + 2, i + 128),
                         hold_through=vs_xbi(i - 21, i + 2)))
    return pd.DataFrame(rows)


def fda_table(st: pd.DataFrame) -> pd.DataFrame:
    def agg(x):
        return pd.Series({"Decisions": len(x), "Run-up, 20 days before": x["run20"].mean(),
                          "Run-up, 40 days before": x["run40"].mean(), "Decision (3 days)": x["decision"].mean(),
                          "Decision rose": (x["decision"] > 0).mean(), "Worst decision": x["decision"].min(),
                          "Hold through (20 days in)": x["hold_through"].mean(), "After 1 month": x["after1m"].mean(),
                          "After 3 months": x["after3m"].mean(), "After 6 months": x["after6m"].mean()})
    order = [lab for *_, lab in SIZES] + ["Unknown"]
    by = st.groupby(["size", "kind"]).apply(agg, include_groups=False).reset_index()
    both = st.groupby("size").apply(agg, include_groups=False).reset_index().assign(kind="Both (outcome unknown in advance)")
    allk = st.groupby("kind").apply(agg, include_groups=False).reset_index().assign(size="All sizes")
    out = pd.concat([allk, both, by], ignore_index=True)
    out["_o"] = out["size"].map({k: i for i, k in enumerate(["All sizes"] + order)})
    return out.sort_values(["_o", "kind"]).drop(columns="_o").rename(columns={"size": "Company size", "kind": "Decision"})


# ----------------------------------------------------------------------------------------------- radar stages


def stage_panel(close: pd.DataFrame, spy: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Speculation Radar stages for every stock and day (vectorised ``speculation.stage``), plus the 52-week drawdown."""
    from . import speculation as sp
    sma200 = close.rolling(200, min_periods=200).mean()
    vs200 = close / sma200 - 1
    r12 = close / close.shift(252) - 1
    hi = close.rolling(252, min_periods=200).max()
    off = close / hi - 1
    peak = hi / close.shift(251) - 1
    rs = (close / close.shift(126) - 1).sub(spy / spy.shift(126) - 1, axis=0)
    st = pd.DataFrame("Quiet", index=close.index, columns=close.columns)
    above = vs200 >= 0
    ran = (r12 > sp.RUN_12M) | ((peak > sp.RUN_12M) & (off < -0.2))
    st = st.mask(~above & ran, "Cooling")
    st = st.mask(above & (r12 > sp.RUN_12M) & (off > -sp.NEAR_HIGH), "Running")
    st = st.mask(above & (r12 > sp.RUN_12M) & ~(off > -sp.NEAR_HIGH), "Cooling")
    st = st.mask(above & ~(r12 > sp.RUN_12M) & (rs > 0), "Turning up")
    return st.where(vs200.notna()), off


def _portfolio(held: pd.DataFrame, ret: pd.DataFrame, mem: pd.DataFrame) -> pd.Series:
    """Equal weight in every stock held at the prior close (members only), 10 bps per side on turnover."""
    pos = (held & mem).shift(1).fillna(False).astype(bool)
    w = pos.div(pos.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    turn = w.diff().abs().sum(axis=1) / 2
    return (w * ret.fillna(0.0)).sum(axis=1) - turn * 2 * COST_BPS / 1e4


def _hold_for(entry: pd.DataFrame, days: int) -> pd.DataFrame:
    return entry.astype(float).replace(0, np.nan).ffill(limit=days - 1).fillna(0).astype(bool)


def _hold_until(entry: pd.DataFrame, exit_: pd.DataFrame) -> pd.DataFrame:
    h = pd.DataFrame(np.nan, index=entry.index, columns=entry.columns)
    h[entry] = 1.0
    h[exit_ & ~entry] = 0.0
    return h.ffill().fillna(0).astype(bool)


def _perf(r: pd.Series) -> dict:
    out = {}
    for per, (a, z) in {"pick": PICK, "grade": GRADE}.items():
        x = r[a:z].fillna(0)
        eq = (1 + x).cumprod()
        yrs = len(x) / 252
        out[f"Yearly return ({per})"] = eq.iloc[-1] ** (1 / yrs) - 1
        out[f"Worst drop ({per})"] = (eq / eq.cummax() - 1).min()
        out[f"Sharpe ({per})"] = x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
    return out


def stage_rules(close: pd.DataFrame, spy: pd.Series, mem: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Speculation Lab entry rules run on every point-in-time S&P 500 member (an unbiased list), and each stage's
    next 6 and 12 months vs the average member."""
    st, off = stage_panel(close, spy)
    ret = close.pct_change(fill_method=None)
    sma50 = close.rolling(50).mean()
    reclaim = (close > sma50) & (close.shift(1) <= sma50.shift(1))
    broken = off < -0.6
    rules = {
        "Buy the turn: Quiet to Turning up, sell on Cooling or Quiet":
            _hold_until((st == "Turning up") & (st.shift(1) != "Turning up"), st.isin(["Quiet", "Cooling"]) | st.isna()),
        "Buy low: 30%+ off the high, hold 6 months": _hold_for(off < -0.3, 126),
        "Buy low and turning: 30%+ off the high, back over the 50-day, hold 6 months": _hold_for((off < -0.3) & reclaim, 126),
        "Broken: just fell 60%+ off the high, hold 6 months": _hold_for(broken & ~broken.shift(1).fillna(False).astype(bool), 126),
        "Broken and turning: 60%+ off the high, back over the 50-day, hold 6 months": _hold_for(broken & reclaim, 126),
        "Hold while Running": st == "Running",
    }
    series = {k: _portfolio(v, ret, mem) for k, v in rules.items()}
    series["Every S&P 500 member, equal weight"] = ret.where(mem.shift(1).fillna(False).astype(bool)).mean(axis=1)
    tab = pd.DataFrame({k: _perf(v) for k, v in series.items()}).T
    for k, v in rules.items():
        tab.loc[k, "Stocks held on average"] = (v & mem).sum(axis=1).loc[PICK[0]:].mean()
    tab = tab.reset_index().rename(columns={"index": "Rule"})
    fw6, fw12 = _forward(close, 126), _forward(close, 252)
    rows = []
    for d in close.index[close.index >= pd.Timestamp(PICK[0])][::21]:
        m = mem.loc[d]
        s_, b_ = st.loc[d][m], broken.loc[d][m]
        a6, a12 = fw6.loc[d][m].mean(), fw12.loc[d][m].mean()
        groups = {lab: s_.index[(s_ == lab) & ~b_] for lab in ("Quiet", "Turning up", "Running", "Cooling")}
        groups["Broken (60%+ off the high)"] = b_.index[b_]
        for lab, sel in groups.items():
            rows.append(dict(date=d, Stage=lab, n=len(sel), x6=fw6.loc[d][sel].mean() - a6,
                             x12=fw12.loc[d][sel].mean() - a12, up12=(fw12.loc[d][sel] > 0).mean()))
    f = pd.DataFrame(rows)
    f["Period"] = np.where(f["date"] <= pd.Timestamp(PICK[1]), "pick", "grade")
    fwd = f.groupby(["Stage", "Period"]).agg(**{"Stocks per month": ("n", "mean"), "Next 6m vs average": ("x6", "mean"),
                                                "Next 12m vs average": ("x12", "mean"), "Up after 12m": ("up12", "mean")})
    return tab, fwd.reset_index()


def theme_turn(close: pd.DataFrame, spy: pd.Series) -> pd.DataFrame:
    """Each Radar theme basket held always vs only while Turning up or Running. The baskets are today's picks, so
    holding them looks better than anyone could have done (hindsight); the rule's drawdown cut is the fair read."""
    from . import speculation as sp
    rows = []
    for t in sp.THEMES:
        syms = [p.ticker for p in t.plays if p.ticker in close and close[p.ticker].notna().sum() > 300]
        if len(syms) < 2:
            continue
        r = close[syms].pct_change(fill_method=None).mean(axis=1).fillna(0)
        r = r[close[syms].notna().any(axis=1).cumsum() > 0]
        basket = (1 + r).cumprod()
        hist = sp.stage_history(basket, spy, step=1)
        on = hist.isin(["Turning up", "Running"]).reindex(basket.index).ffill().fillna(False).shift(1).fillna(False)
        start = hist.index[0]
        held, rule = r[start:], r.where(on, 0.0)[start:]

        def cagr(x):
            return (1 + x).prod() ** (252 / len(x)) - 1

        def dd(x):
            e = (1 + x).cumprod()
            return (e / e.cummax() - 1).min()
        rows.append({"Theme": t.name, "Since": start.date().isoformat(), "Stocks": len(syms),
                     "Hold: yearly": cagr(held), "Hold: worst drop": dd(held), "Rule: yearly": cagr(rule),
                     "Rule: worst drop": dd(rule), "Rule: time invested": float(on[start:].mean())})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------- Kalshi


def kalshi_daily(k: dict) -> pd.DataFrame:
    """Daily Kalshi odds (prices are dollars per $1 contract, so 0.30 = 30%): the chance the next Fed meeting cuts, and of it hiking, plus this year's recession odds.
    Each day uses the meeting that is next as of that day, and the last traded price (or the bid/ask middle)."""
    def frame(series):
        rows = []
        for m in k.get(series, []):
            for c in m["c"]:
                p = c.get("close")
                if p is None and c.get("bid") is not None and c.get("ask") is not None:
                    p = (float(c["bid"]) + float(c["ask"])) / 2
                if p is None:
                    continue
                rows.append(dict(event=m["m"]["event_ticker"], market=m["m"]["ticker"].rsplit("-", 1)[-1],
                                 close_time=pd.to_datetime(m["m"]["close_time"], utc=True).tz_convert(None),
                                 date=pd.to_datetime(c["ts"], unit="s").normalize(), p=float(p)))
        return pd.DataFrame(rows)
    fed = pd.concat([frame("KXFEDDECISION"), frame("FEDDECISION")], ignore_index=True)
    out = pd.DataFrame()
    if not fed.empty:
        fed = fed[fed["date"] < fed["close_time"].dt.normalize()]
        nxt = fed.groupby("date")["close_time"].transform("min")
        fed = fed[fed["close_time"] == nxt]
        # Market codes: C25 / C26 = cut 25bp / more, H25 / H26 = hike, H0 = hold (other codes are side bets).
        cut = fed[fed["market"].str.fullmatch(r"C\d+")].groupby("date")["p"].sum().clip(upper=1)
        hike = fed[fed["market"].str.fullmatch(r"H[1-9]\d*")].groupby("date")["p"].sum().clip(upper=1)
        out = pd.DataFrame({"fed_cut": cut, "fed_hike": hike})
    rec = pd.concat([frame("KXRECSSNBER"), frame("RECSSNBER")], ignore_index=True)
    if not rec.empty:
        rec["year"] = rec["close_time"].dt.year
        rec = rec[rec["year"] - 1 == rec["date"].dt.year]          # "recession this year" for the current year
        out = out.join(rec.groupby("date")["p"].mean().rename("recession"), how="outer")
    return out.sort_index()


def kalshi_tests(odds: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    """Do moves in the odds lead QQQ? Each signal is known at that day's close and the trade earns the next days."""
    q = close["QQQ"]
    o = odds.reindex(q.index).ffill(limit=3)
    nxt1, nxt5, nxt21 = _forward(q, 1), _forward(q, 5), _forward(q, 21)
    rows = []
    for col in [c for c in ("fed_cut", "fed_hike", "recession") if c in o]:
        x = o[col]
        for lag in (1, 5, 20):
            chg = x - x.shift(lag)
            ok = chg.notna() & nxt5.notna()
            if ok.sum() < 60:
                continue
            for name, sig in {f"{col} up over {lag}d": chg > 0.05, f"{col} down over {lag}d": chg < -0.05}.items():
                rows.append({"Signal": name, "Days": int(sig[ok].sum()), "From": x.dropna().index[0].date().isoformat(),
                             "QQQ next day": nxt1[ok & sig].mean(), "QQQ next week": nxt5[ok & sig].mean(),
                             "QQQ next month": nxt21[ok & sig].mean(), "All days next week": nxt5[ok].mean(),
                             "Corr. with next week": chg[ok].corr(nxt5[ok])})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------- main


def main(folder: str) -> None:
    d = load(folder)
    px = d["px"]
    C = px["Close"]
    eq = stocks(C)
    mem = members(C[eq])
    OUT.mkdir(parents=True, exist_ok=True)
    b = breadth(C[eq], px["Volume"][eq], mem)
    breadth_setups(b, C["SPY"], C["^VIX"]).to_csv(OUT / "breadth_setups.csv", index=False)
    b.tail(30).to_csv(OUT / "breadth_recent.csv")
    ev = earnings_events(px, d["earn"], mem.reindex(columns=C.columns).fillna(False))
    ev = ev[ev["date"] >= pd.Timestamp(PICK[0])]
    post_beat_table(ev).to_csv(OUT / "post_beat.csv", index=False)
    entry_delay_table(ev).to_csv(OUT / "post_beat_entry_delay.csv", index=False)
    score, deciles, _ = beat_model(ev)
    score.to_csv(OUT / "beat_model.csv", index=False)
    deciles.to_csv(OUT / "beat_model_deciles.csv", index=False)
    tab, fwd = stage_rules(C[eq].ffill(limit=5), C["SPY"], mem)
    tab.to_csv(OUT / "radar_rules.csv", index=False)
    fwd.to_csv(OUT / "radar_stage_forward.csv", index=False)
    theme_turn(C, C["SPY"]).to_csv(OUT / "radar_theme_turn.csv", index=False)
    if "fda" in d:
        fda_table(fda_study(d["fda"])).to_csv(OUT / "fda_decisions.csv", index=False)
    if "kalshi" in d:
        odds = kalshi_daily(d["kalshi"])
        odds.to_csv(OUT / "kalshi_odds.csv")
        kalshi_tests(odds, C).to_csv(OUT / "kalshi_tests.csv", index=False)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1] if len(sys.argv) > 1 else ".lab")
