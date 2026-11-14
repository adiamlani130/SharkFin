"""Edge lab (Nov 2026): three research questions, each backtested on point-in-time data.

  1. Confluences: do extra conditions (earnings timing and results, news-gap dips, dip-day volume, credit spreads,
     strength against the stock's own sector, breakout volume) improve Dive Zone and Tech Breakout Rider?
  2. Theme detection: does the Speculation Radar's "Turning up" reading, or any other rule, find a theme before it
     runs? Tested on ~80 industry and thematic ETFs (each one is a theme basket that existed at the time), and on the
     Radar's own 12 themes. Also measures how big a "breakthrough" run is and how much of it a signal catches.
  3. Low-bar turnaround: an earnings beat when analysts expected a bad quarter, in a growth sector that had sold
     off. Does buying after that report ride the recovery back to the highs?

Run ``python -m sharkfin.edge_lab DATA_DIR``. DATA_DIR holds ``ohlcv.pkl`` ({"Open"|"High"|"Low"|"Close"|"Volume":
dates x tickers}: every stock in the S&P 500 at some point since 2005, the Nasdaq-100, the Radar plays, market and
theme ETFs, ^VIX/^VIX3M/^IRX, Yahoo, split and dividend adjusted), ``earn.pkl`` ({ticker: Yahoo earnings-dates
table}) and ``lists.pkl`` ({"stocks", "themes", "mkt"}), all written by ``download``. Tables go to
``research_data/edge_lab``.

No look-ahead:
  * every signal uses closes up to the signal day; trades fill on later bars (the swing engine's rules);
  * an earnings report counts from its reaction day (after-4pm reports react the next session) and trades fill at
    the open after the reaction day;
  * a stock's "sector" is the sector ETF its returns tracked most closely over the year before (re-estimated each
    month from past data only), so stocks that later left the index or were delisted still get one;
  * settings and filters are judged on the picking window (2006 - Oct 12 2021) and graded on Oct 13 2021 -
    Nov 6 2026, the same split as growth_lab and catalyst_lab.
One exception, flagged where used: "earnings in the next 5 days" uses the actual report date. Companies announce
the date a few weeks ahead and report on a quarterly rhythm, so it was knowable, but not from prices alone.
Survivorship: Yahoo lacks prices for some stocks that left the S&P 500, and ETFs that closed are not in the theme
list (closed theme ETFs were mostly flops), so both lean a little optimistic.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import breakout_rider as brk
from . import catalyst_lab as cl
from . import leader_dip as ld
from . import walkforward

PICK = ("2006-01-03", "2021-10-12")
GRADE = ("2021-10-13", "2026-11-06")
COST_BPS = 10.0
OUT = Path(__file__).with_name("research_data") / "edge_lab"
SECTOR_ETFS = ("XLK", "SMH", "IGV", "XLC", "XLY", "XBI", "XLV", "XLF", "XLI", "XLE", "XLU", "XLP", "XLB", "XLRE")
GROWTH_ETFS = ("XLK", "SMH", "IGV", "XLC", "XLY", "XBI")
THEME_ETFS = (
    "SMH SOXX IGV XBI IBB ICLN TAN URA LIT XME GDX GDXJ SIL KRE XHB ITB XRT JETS ITA XAR CIBR HACK SKYY FDN ARKK ARKG "
    "ARKQ ARKW BOTZ ROBO UFO QTUM KWEB PBW FAN REMX URNM NLR COPX XOP OIH IYT PAVE CLOU WCLD BLOK IPAY FINX MSOS ESPO "
    "HERO DRIV BATT PRNT SNSR AIQ IHI XSD PSI BUG IBUY SOCL MJ PEJ XTL XSW IYZ PHO KIE IAI XPH IHF XHE XHS SLX WOOD MOO "
    "QCLN GRID SRVR ARKX CQQQ PBJ XES AMLP").split()
MARKET = ("SPY QQQ IWM RSP DIA MDY IJR XLK XLF XLV XLY XLC XLI XLP XLE XLU XLRE XLB HYG LQD IEF TLT SHY UUP GLD "
          "^VIX ^VIX3M ^IRX ^TNX").split()


# ------------------------------------------------------------------------------------------------- data


def download(folder: str | Path) -> None:  # pragma: no cover - network
    """Pull the research files from Yahoo into ``folder`` (a local scratch folder; never commit it)."""
    import time
    from concurrent.futures import ThreadPoolExecutor

    import yfinance as yf

    from . import data as sd
    from . import speculation as sp
    f = Path(folder)
    f.mkdir(parents=True, exist_ok=True)
    stocks = list(dict.fromkeys(sd.sp500_ever("2005-01-01") + list(sd.nasdaq100()) + sp.all_tickers()))
    allt = list(dict.fromkeys(stocks + MARKET + THEME_ETFS))
    frames = []
    for i in range(0, len(allt), 100):
        frames.append(yf.download(allt[i:i + 100], start="2004-01-01", auto_adjust=True, progress=False))
    px = {k: pd.concat([d[k] for d in frames], axis=1) for k in ("Open", "High", "Low", "Close", "Volume")}
    px = {k: v.loc[:, ~v.columns.duplicated()].sort_index() for k, v in px.items()}
    pickle.dump(px, open(f / "ohlcv.pkl", "wb"))
    pickle.dump({"stocks": stocks, "themes": list(THEME_ETFS), "mkt": MARKET}, open(f / "lists.pkl", "wb"))

    def get(t):
        for k in range(3):
            try:
                return t, yf.Ticker(t).get_earnings_dates(limit=100)
            except Exception:
                time.sleep(2 + 3 * k)
        return t, None
    with ThreadPoolExecutor(6) as ex:
        earn = dict(ex.map(get, stocks))
    pickle.dump(earn, open(f / "earn.pkl", "wb"))


def load(folder: str | Path) -> dict:
    """Read the files ``download`` wrote (pickle: only ever load files you made yourself)."""
    from . import data as sd
    f = Path(folder)
    px = pickle.load(open(f / "ohlcv.pkl", "rb"))
    keep = px["Close"]["SPY"].notna()
    px = {k: v.loc[keep].astype(float) for k, v in px.items()}
    lists = pickle.load(open(f / "lists.pkl", "rb"))
    earn = pickle.load(open(f / "earn.pkl", "rb"))
    C = px["Close"]
    dates = C.index
    sp5 = [s for s in sd.sp500_ever("2005-01-01") if s in C and C[s].notna().sum() > 260]
    panel = {k: px[k][sp5] for k in ("Open", "High", "Low", "Close", "Volume")}
    cf = lambda s: walkforward.carry_forward(s)
    d = {"px": px, "panel": panel, "dates": dates, "spy": cf(C["SPY"]), "qqq": cf(C["QQQ"]), "vix": cf(C["^VIX"]),
         "vix3m": cf(C["^VIX3M"]), "tbill": (C["^IRX"] / 100).dropna(), "etf": C[[c for c in MARKET if c in C]],
         "earn": {k: v for k, v in earn.items() if isinstance(v, pd.DataFrame) and len(v)},
         "themes": [t for t in lists["themes"] if t in C and C[t].notna().sum() > 300]}
    d["members"] = sd.sp500_members(dates, sp5)
    tab = sd.sp500_table()
    d["gics"] = dict(zip(tab["Symbol"], tab["Sector"]))
    d["sector_ret3"] = ld.sector_returns(dates, pd.Index(sp5), {s: ld.GICS_ETF.get(sec) for s, sec in d["gics"].items()},
                                         C)
    return d


def pit_sector(close: pd.DataFrame, etf: pd.DataFrame, spy: pd.Series, window: int = 252,
               step: int = 21) -> pd.DataFrame:
    """Each stock's sector, point in time: the ETF whose excess returns (over SPY) its own excess returns tracked
    most closely over the past ``window`` days, re-read every ``step`` days and carried forward. Uses past data only."""
    r = close.pct_change(fill_method=None).sub(spy.pct_change(), axis=0)
    e = etf.pct_change(fill_method=None).sub(spy.pct_change(), axis=0)
    out = {}
    names = np.array(etf.columns)
    for i in range(window, len(close), step):
        rs, es = r.iloc[i - window + 1:i + 1], e.iloc[i - window + 1:i + 1]
        ok_e = es.notna().sum() > window * 0.8
        es = es.loc[:, ok_e]
        if es.empty:
            continue
        ok_s = rs.notna().sum() > window * 0.8
        rs = rs.loc[:, ok_s].fillna(0.0)
        es = es.fillna(0.0)
        rz = (rs - rs.mean()) / rs.std().replace(0, np.nan)
        ez = (es - es.mean()) / es.std().replace(0, np.nan)
        corr = rz.T.to_numpy() @ ez.to_numpy() / (len(rs) - 1)
        best = np.array(es.columns)[np.nanargmax(np.nan_to_num(corr, nan=-9), axis=1)]
        out[close.index[i]] = pd.Series(best, index=rs.columns)
    sec = pd.DataFrame(out).T.reindex(columns=close.columns)
    sec = sec.reindex(close.index).ffill()
    return sec.where(sec.isin(names))


def _stats(r: pd.Series, rf: pd.Series | None, a, z) -> dict:
    x = r.loc[a:z].dropna()
    if len(x) < 20:
        return {}
    e = (1 + x).cumprod()
    ex = x - (rf.reindex(x.index).fillna(0) if rf is not None else 0)
    return {"Return per year": e.iloc[-1] ** (252 / len(x)) - 1, "Sharpe": ex.mean() / x.std() * np.sqrt(252),
            "Worst drop": (e / e.cummax() - 1).min()}


def _both(r: pd.Series, rf: pd.Series | None = None) -> dict:
    out = {}
    for per, (a, z) in {"pick": PICK, "grade": GRADE}.items():
        out.update({f"{k} ({per})": v for k, v in _stats(r, rf, a, z).items()})
    for lab, (a, z) in SELLOFFS.items():
        x = r.loc[a:z].iloc[1:]
        out[lab] = (1 + x).prod() - 1
    return out


SELLOFFS = {"2022 bear market": ("2022-01-03", "2022-12-30"),
            "Nov 2026 selloff (Oct 9 - Nov 6)": ("2026-10-09", "2026-11-06")}


# ------------------------------------------------------------------------------------------------- 1. confluences


def earnings_frames(ev: pd.DataFrame, dates: pd.Index, cols: pd.Index) -> dict:
    """Stock-by-day readings from the earnings table, each known at that day's close: the last report's surprise and
    growth, trading days since it, and trading days until the next one (that last one uses the actual date; see the
    module note)."""
    ev = ev.dropna(subset=["date"]).sort_values("date")
    pos = pd.Series(np.arange(len(dates)), index=dates)
    out = {k: pd.DataFrame(np.nan, index=dates, columns=cols) for k in ("sur", "yoy", "est_yoy", "since", "until")}
    for s, g in ev.groupby("sym"):
        if s not in cols:
            continue
        g = g.drop_duplicates("date", keep="last").set_index("date")
        for k, c in (("sur", "surprise"), ("yoy", "yoy"), ("est_yoy", "est_yoy")):
            out[k][s] = g[c].reindex(dates).ffill(limit=130)
        rp = pos.reindex(g.index).to_numpy()
        last = pd.Series(rp, index=g.index).reindex(dates).ffill().to_numpy()
        out["since"][s] = np.arange(len(dates)) - last
        # Days to the next report: the one deliberate forward read (report dates are announced in advance).
        rp_ok = np.sort(rp[np.isfinite(rp)])
        k = np.searchsorted(rp_ok, np.arange(len(dates)), side="left")
        nxt = np.where(k < len(rp_ok), rp_ok[np.minimum(k, len(rp_ok) - 1)], np.nan)
        out["until"][s] = nxt - np.arange(len(dates))
    return out


def confluences(d: dict, ef: dict) -> dict:
    """Candidate filters, each {"buy_ok": dates x tickers} (stock by stock) or {"entry_ok": series} (market-wide),
    known at the signal close (except the flagged earnings-date one)."""
    P = d["panel"]
    C, V = P["Close"], P["Volume"]
    Cf = C.ffill()
    r = Cf.pct_change(fill_method=None)
    etf = d["etf"].reindex(C.index).ffill()
    vol50 = V.rolling(50, min_periods=30).mean().shift(1)
    volx = V / vol50
    gics_etf = {t: ld.GICS_ETF.get(sec) for t, sec in d["gics"].items()}
    sec6 = pd.DataFrame({c: (etf[gics_etf[c]] / etf[gics_etf[c]].shift(126) - 1) if gics_etf.get(c) in etf else np.nan
                         for c in C.columns}, index=C.index)
    rs_sec = (Cf / Cf.shift(126) - 1) - sec6
    credit = etf["HYG"] / etf["IEF"]
    credit_ok = (credit > credit.rolling(50).mean()) | credit.isna()
    tnx = etf["^TNX"]
    big_drop3 = r.rolling(3).min()
    T = lambda x: x.fillna(True).astype(bool)
    F = lambda x: x.fillna(False).astype(bool)
    return {
        "No earnings in the next 5 trading days (date known in advance)": {"buy_ok": T(~(ef["until"] <= 5))},
        "Earnings in the next 5 trading days only": {"buy_ok": F(ef["until"] <= 5)},
        "Last report was a beat": {"buy_ok": F(ef["sur"] > 0)},
        "Last report was a miss": {"buy_ok": F(ef["sur"] <= 0)},
        "Dip within 30 days after a beat": {"buy_ok": F((ef["sur"] > 0) & (ef["since"] <= 30))},
        "Dip within 30 days after a miss (skip)": {"buy_ok": T(~((ef["sur"] <= 0) & (ef["since"] <= 30)))},
        "Last EPS up 15%+ on a year ago": {"buy_ok": F(ef["yoy"] > 0.15)},
        "No news gap: no single-day drop of 7%+ in the last 3 days": {"buy_ok": T(big_drop3 > -0.07)},
        "News gap only: a single-day drop of 7%+ in the last 3 days": {"buy_ok": F(big_drop3 <= -0.07)},
        "Dip-day volume 1.5x normal or more (capitulation)": {"buy_ok": F(volx >= 1.5)},
        "Dip-day volume under 1.5x normal (quiet dip)": {"buy_ok": F(volx < 1.5)},
        "Stock beating its sector ETF over 6 months": {"buy_ok": T(rs_sec > 0)},
        "Credit calm: junk bonds (HYG/IEF) above their 50-day": {"entry_ok": credit_ok},
        "10-year yield not up 0.4+ points in a month": {"entry_ok": (tnx - tnx.shift(21) < 0.4) | tnx.isna()},
    }


def breakout_confluences(d: dict, ef: dict) -> dict:
    P = d["panel"]
    C, V, H = P["Close"], P["Volume"], P["High"]
    Cf = C.ffill()
    vol50 = V.rolling(50, min_periods=30).mean().shift(1)
    volx = V / vol50
    hi252 = H.rolling(252, min_periods=200).max().shift(1)
    lo_base = Cf.rolling(126, min_periods=100).max().shift(1)
    etf = d["etf"].reindex(C.index).ffill()
    credit = etf["HYG"] / etf["IEF"]
    T = lambda x: x.fillna(True).astype(bool)
    F = lambda x: x.fillna(False).astype(bool)
    return {
        "Breakout-day volume 1.5x normal or more": {"buy_ok": F(volx >= 1.5)},
        "Breakout-day volume under 1.5x normal": {"buy_ok": F(volx < 1.5)},
        "Also a 52-week high": {"buy_ok": F(C > hi252)},
        "Not a 52-week high (breakout below the old high)": {"buy_ok": F(C <= hi252)},
        "Within 20 days after an earnings beat": {"buy_ok": F((ef["sur"] > 0) & (ef["since"] <= 20))},
        "Last report was a beat": {"buy_ok": F(ef["sur"] > 0)},
        "Last EPS up 25%+ on a year ago": {"buy_ok": F(ef["yoy"] > 0.25)},
        "No earnings in the next 5 trading days (date known in advance)": {"buy_ok": T(~(ef["until"] <= 5))},
        "Tight base: 6-month high within 15% of the close a month ago": {
            "buy_ok": F(Cf.shift(21) / lo_base > 0.85)},
        "Credit calm: junk bonds (HYG/IEF) above their 50-day": {
            "entry_ok": (credit > credit.rolling(50).mean()) | credit.isna()},
    }


def trade_buckets(trades: pd.DataFrame, feats: dict) -> pd.DataFrame:
    """Average closed-trade return with and without each feature, pick vs grade (trade-level view, no slot effects)."""
    t = trades[trades["Why it sold"] != "Open"].copy()
    sd_ = pd.to_datetime(t["Signal date"])
    t["Window"] = np.where(sd_ <= pd.Timestamp(PICK[1]), "pick", "grade")
    rows = []
    for name, f in feats.items():
        if "buy_ok" in f:
            fr = f["buy_ok"]
            vals = np.array([bool(fr.at[a, s]) if s in fr.columns and a in fr.index else np.nan
                             for a, s in zip(sd_, t["Symbol"])], dtype=float)
        else:
            vals = f["entry_ok"].reindex(sd_).to_numpy(dtype=float)
        t["_f"] = vals
        for w in ("pick", "grade"):
            x = t[t["Window"] == w]
            on, off = x[x["_f"] == 1], x[x["_f"] == 0]
            rows.append({"Filter": name, "Window": w, "Trades kept": len(on), "Share kept": len(on) / max(len(x), 1),
                         "Avg kept": on["Return"].mean(), "Avg dropped": off["Return"].mean(),
                         "Win rate kept": (on["Return"] > 0).mean(), "Win rate dropped": (off["Return"] > 0).mean()})
    return pd.DataFrame(rows)


def run_confluences(d: dict, ev: pd.DataFrame) -> tuple:
    from . import growth_lab as gl
    rf = pd.Series(gl.swing_engine.daily_cash(d["dates"], d["tbill"]), index=d["dates"])
    P = d["panel"]
    ef = earnings_frames(ev, P["Close"].index, P["Close"].columns)
    feats = confluences(d, ef)
    bfeats = breakout_confluences(d, ef)
    dz = gl.dive_zone(d)
    br = gl.breakout(d)
    rows = [{"Strategy": "Dive Zone", "Filter": "None (as is)", **_both(dz["returns"], rf),
             "Trades": int((dz["trades"]["Why it sold"] != "Open").sum())},
            {"Strategy": "Tech Breakout Rider", "Filter": "None (as is)", **_both(br["returns"], rf),
             "Trades": int((br["trades"]["Why it sold"] != "Open").sum())}]
    for name, f in feats.items():
        res = gl.dive_zone(d, **f)
        rows.append({"Strategy": "Dive Zone", "Filter": name, **_both(res["returns"], rf),
                     "Trades": int((res["trades"]["Why it sold"] != "Open").sum())})
        print("DZ", name, flush=True)
    panel, mem = gl.tech_panel(d)
    for name, f in bfeats.items():
        kw = {"entry_ok": f["entry_ok"]} if "entry_ok" in f else {
            "buy_ok": f["buy_ok"].reindex(columns=panel["Close"].columns)}
        res = brk.backtest(panel, d["qqq"], d["tbill"], brk.SLOTS, COST_BPS, start=PICK[0], market_close=d["spy"],
                           members=mem, **kw)
        rows.append({"Strategy": "Tech Breakout Rider", "Filter": name, **_both(res["returns"], rf),
                     "Trades": int((res["trades"]["Why it sold"] != "Open").sum())})
        print("BR", name, flush=True)
    port = pd.DataFrame(rows)
    buckets = pd.concat([trade_buckets(dz["trades"], feats).assign(Strategy="Dive Zone"),
                         trade_buckets(br["trades"], bfeats).assign(Strategy="Tech Breakout Rider")])
    return port, buckets, dz, br, rf


def combos(d: dict, ev: pd.DataFrame) -> pd.DataFrame:
    """The filters that helped on both windows, together, plus the credit switch (the one that helps in crashes)."""
    from . import growth_lab as gl
    rf = pd.Series(gl.swing_engine.daily_cash(d["dates"], d["tbill"]), index=d["dates"])
    P = d["panel"]
    ef = earnings_frames(ev, P["Close"].index, P["Close"].columns)
    f, bf = confluences(d, ef), breakout_confluences(d, ef)
    miss = f["Dip within 30 days after a miss (skip)"]["buy_ok"]
    rs = f["Stock beating its sector ETF over 6 months"]["buy_ok"]
    cr = f["Credit calm: junk bonds (HYG/IEF) above their 50-day"]["entry_ok"]
    rows = []
    for name, kw in {"As is": {}, "Skip dips within 30 days of a miss": {"buy_ok": miss},
                     "Only stocks beating their sector": {"buy_ok": rs},
                     "Both": {"buy_ok": miss & rs}, "Both + credit switch": {"buy_ok": miss & rs, "entry_ok": cr}}.items():
        rows.append({"Strategy": "Dive Zone", "Version": name, **_both(gl.dive_zone(d, **kw)["returns"], rf)})
    panel, mem = gl.tech_panel(d)
    ne = bf["No earnings in the next 5 trading days (date known in advance)"]["buy_ok"].reindex(columns=panel["Close"].columns)
    crb = bf["Credit calm: junk bonds (HYG/IEF) above their 50-day"]["entry_ok"]
    for name, kw in {"As is": {}, "No earnings in the next 5 days": {"buy_ok": ne}, "Credit switch": {"entry_ok": crb},
                     "Both": {"buy_ok": ne, "entry_ok": crb}}.items():
        r = brk.backtest(panel, d["qqq"], d["tbill"], brk.SLOTS, COST_BPS, start=PICK[0], market_close=d["spy"],
                         members=mem, **kw)
        rows.append({"Strategy": "Tech Breakout Rider", "Version": name, **_both(r["returns"], rf)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------- 2. themes


def stage_frame(close: pd.DataFrame, spy: pd.Series) -> pd.DataFrame:
    """The Radar stage of every series on every day (``catalyst_lab.stage_panel`` plus the Broken stage)."""
    st, off = cl.stage_panel(close, spy)
    return st.mask(off < -0.6, "Broken")


def theme_signals(close: pd.DataFrame, vol: pd.DataFrame, spy: pd.Series, stages: pd.DataFrame) -> dict:
    """Candidate "a theme is starting" rules, each a dates x themes True/False frame known at that close."""
    c = close.ffill(limit=5)
    sma50, sma200 = c.rolling(50).mean(), c.rolling(200, min_periods=200).mean()
    hi = c.rolling(252, min_periods=200).max()
    off = c / hi - 1
    was_down = off.rolling(252, min_periods=200).min().shift(1)
    rs3 = (c / c.shift(63) - 1).sub(spy / spy.shift(63) - 1, axis=0)
    rank3 = rs3.rank(axis=1, pct=True)
    rank6_ago = (c / c.shift(126) - 1).shift(63).rank(axis=1, pct=True)
    dv = (vol * c)
    flow = dv.rolling(20).mean() / dv.rolling(252, min_periods=200).mean()
    above50 = (c > sma50)
    prev = stages.shift(1)
    return {
        "Radar: Quiet or Broken to Turning up": (stages == "Turning up") & prev.isin(["Quiet", "Broken"]),
        "Radar: any move into Running": (stages == "Running") & (prev != "Running"),
        "New 52-week high after being 30%+ off within the year": (c >= hi) & (was_down < -0.3) & (c.shift(1) < hi.shift(1)),
        "Golden cross (50-day over 200-day)": (sma50 > sma200) & (sma50.shift(1) <= sma200.shift(1)),
        "Rotation: top 20% on 3-month strength, bottom half 3 months earlier": (rank3 >= 0.8) & (rank6_ago < 0.5),
        "Money rushing in: 20-day dollar volume 2x its yearly average, above 200-day":
            (flow > 2) & (c > sma200) & (flow.shift(1) <= 2),
        "Turn from a crash: 40%+ off the high, back over the 200-day":
            (off.rolling(126).min() < -0.4) & (c > sma200) & (c.shift(1) <= sma200.shift(1)),
        "Breakout in a quiet theme: back over the 50-day while still 20%+ off the high":
            above50 & ~above50.shift(1).fillna(False).astype(bool) & (off < -0.2),
    }


def theme_events(close: pd.DataFrame, spy: pd.Series, signals: dict, gap: int = 63) -> pd.DataFrame:
    """One row per signal episode (first signal after ``gap`` quiet days): returns vs SPY from the next close
    (3, 6, 12 months), the best gain reached within 12 months, the worst dip before it, and whether it became a run."""
    c = close.ffill(limit=5)
    idx = c.index
    rows = []
    for name, sig in signals.items():
        for t in sig.columns:
            s = cl.first_in(sig[t], gap)
            for day in s[s].index:
                i = idx.get_loc(day) + 1
                if i >= len(idx) or not np.isfinite(c[t].iloc[i]):
                    continue
                p0, b0 = c[t].iloc[i], spy.iloc[i]
                row = {"Rule": name, "Theme": t, "date": day}
                for lab, k in (("3m", 63), ("6m", 126), ("12m", 252)):
                    if i + k < len(idx):
                        row["ret" + lab] = c[t].iloc[i + k] / p0 - 1
                        row["x" + lab] = row["ret" + lab] - (spy.iloc[i + k] / b0 - 1)
                if i + 252 < len(idx):
                    path = c[t].iloc[i:i + 253] / p0 - 1
                    row["best12m"] = path.max()
                    row["dip_before_best"] = path.iloc[:int(path.values.argmax()) + 1].min()
                rows.append(row)
    ev = pd.DataFrame(rows)
    ev["Period"] = np.where(ev["date"] <= pd.Timestamp(PICK[1]), "pick", "grade")
    return ev


def theme_event_table(ev: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (rule, per), g in pd.concat([ev, base]).groupby(["Rule", "Period"]):
        rows.append({"Rule": rule, "Period": per, "Signals": len(g), "Themes": g["Theme"].nunique(),
                     "Avg 6m vs SPY": g["x6m"].mean(), "Median 6m vs SPY": g["x6m"].median(),
                     "Avg 12m vs SPY": g["x12m"].mean(), "Median 12m vs SPY": g["x12m"].median(),
                     "Beat SPY over 12m": (g["x12m"] > 0).mean(),
                     "Ran 40%+ within 12m": (g["best12m"] > 0.4).mean(),
                     "Ran 100%+ within 12m": (g["best12m"] > 1.0).mean(),
                     "Median best gain in 12m": g["best12m"].median(),
                     "Median dip first": g["dip_before_best"].median()})
    return pd.DataFrame(rows)


def baseline_events(close: pd.DataFrame, spy: pd.Series, step: int = 21) -> pd.DataFrame:
    """Every theme on every 21st day: what a signal has to beat."""
    sig = pd.DataFrame(False, index=close.index, columns=close.columns)
    sig.iloc[::step] = True
    sig = sig & close.notna() & close.shift(252).notna()
    ev = theme_events(close, spy, {"Every theme, any month (baseline)": sig}, gap=1)
    return ev


def theme_runs(close: pd.DataFrame, spy: pd.Series, stages: pd.DataFrame, run: float = 1.0) -> pd.DataFrame:
    """The big runs, found with hindsight: a theme that rose ``run`` (100%) or more from a low to a later peak with no
    40% fall in between. For each, when the Radar first said Turning up and Running, and how much of the run was left."""
    rows = []
    c = close.ffill(limit=5)
    for t in c.columns:
        s = c[t].dropna()
        if len(s) < 300:
            continue
        i, n = 0, len(s)
        v = s.to_numpy()
        while i < n - 1:
            lo_i = i
            j = i
            peak_i = i
            while j < n - 1:
                j += 1
                if v[j] < v[lo_i] and peak_i == lo_i:
                    lo_i = peak_i = j
                    continue
                if v[j] > v[peak_i]:
                    peak_i = j
                if v[j] < v[peak_i] * 0.6:
                    break
            if v[peak_i] / v[lo_i] - 1 >= run and s.index[lo_i] >= close.index[252]:
                st = stages[t].reindex(s.index)
                win = st.iloc[max(lo_i - 63, 0):peak_i + 1]
                tu = win[win == "Turning up"].index
                rn = win[win == "Running"].index
                first_tu = tu[0] if len(tu) else None
                first_rn = rn[0] if len(rn) else None
                rows.append({"Theme": t, "Low": s.index[lo_i].date(), "Peak": s.index[peak_i].date(),
                             "Run, low to peak": v[peak_i] / v[lo_i] - 1,
                             "Days, low to peak": peak_i - lo_i,
                             "First Turning up": first_tu.date() if first_tu is not None else None,
                             "Left after Turning up": v[peak_i] / s[first_tu] - 1 if first_tu is not None else np.nan,
                             "First Running": first_rn.date() if first_rn is not None else None,
                             "Left after Running": v[peak_i] / s[first_rn] - 1 if first_rn is not None else np.nan,
                             "Fall from peak, next 12m": s.iloc[peak_i:peak_i + 253].min() / v[peak_i] - 1})
            i = max(peak_i, lo_i + 1)
    return pd.DataFrame(rows)


def theme_portfolios(close: pd.DataFrame, spy: pd.Series, stages: pd.DataFrame, signals: dict) -> pd.DataFrame:
    """Each rule as a portfolio: hold a theme for 6 months after its signal (equal weight across held themes,
    10 bps a side), vs every theme equal weight. Also the Radar's own "hold while Turning up or Running"."""
    ret = close.ffill(limit=5).pct_change(fill_method=None)
    alive = close.notna() & close.shift(252).notna()
    series = {}
    for name, sig in signals.items():
        held = cl._hold_for(sig.fillna(False).astype(bool), 126)
        series[name + " (hold 6 months)"] = cl._portfolio(held, ret, alive)
    on = stages.isin(["Turning up", "Running"])
    series["Radar: hold while Turning up or Running"] = cl._portfolio(on, ret, alive)
    series["Every theme ETF, equal weight"] = ret.where(alive.shift(1).fillna(False).astype(bool)).mean(axis=1)
    series["SPY"] = spy.pct_change()
    rows = []
    for k, r in series.items():
        rows.append({"Rule": k, **_both(r.fillna(0.0))})
    return pd.DataFrame(rows)


def radar_replay(px: dict, spy: pd.Series) -> pd.DataFrame:
    """The Radar's own themes (picked in Oct 2026, so the list itself is hindsight) and the Micron/SanDisk case:
    when the stage reader first said Turning up and Running in the past three years, and what happened next."""
    from . import speculation as sp
    C = px["Close"]
    out = []
    groups = {t.name: [p.ticker for p in t.plays] for t in sp.THEMES}
    groups.update({"Micron (case study)": ["MU"], "SanDisk (case study)": ["SNDK"]})
    for name, syms in groups.items():
        syms = [s for s in syms if s in C and C[s].notna().sum() > 260]
        if not syms:
            continue
        r = C[syms].pct_change(fill_method=None).mean(axis=1).fillna(0)
        r = r[C[syms].notna().any(axis=1).cumsum() > 0]
        b = (1 + r).cumprod()
        st = stage_frame(b.to_frame("x"), spy.reindex(b.index))["x"]
        since = b.index[-1] - pd.Timedelta(days=3 * 365)
        prev = st.shift(1)
        st3, prev3 = st[since:], prev[since:]
        row = {"Theme": name, "Stocks": len(syms), "Stage now": st.iloc[-1],
               "3-year return": b.iloc[-1] / b[since:].iloc[0] - 1,
               "12-month return": b.iloc[-1] / b.iloc[-253] - 1 if len(b) > 253 else np.nan,
               "Off its high": b.iloc[-1] / b.iloc[-252:].max() - 1}
        for lab in ("Turning up", "Running"):
            hit = st3[(st3 == lab) & (prev3 != lab) & prev3.notna()]
            if len(hit):
                d0 = hit.index[0]
                row[f"First {lab} (3y)"] = d0.date()
                row[f"Since first {lab}"] = b.iloc[-1] / b[d0] - 1
                row[f"Best after first {lab}"] = b[d0:].max() / b[d0] - 1
        # The rule the Radar implies: in while Turning up or Running, out otherwise (decided at the close, next day).
        on = st.isin(["Turning up", "Running"]).shift(1).fillna(False).astype(bool)
        rr = r.where(on, 0.0)[since:]
        row["Rule return (3y)"] = (1 + rr).prod() - 1
        row["Rule worst drop (3y)"] = ((1 + rr).cumprod() / (1 + rr).cumprod().cummax() - 1).min()
        row["Hold worst drop (3y)"] = (b[since:] / b[since:].cummax() - 1).min()
        out.append(row)
    return pd.DataFrame(out)


def stock_breakthroughs(close: pd.DataFrame, spy: pd.Series, mem: pd.DataFrame) -> pd.DataFrame:
    """The theme rules that matter, run on single stocks (point-in-time S&P 500 members, an unbiased list): forward
    returns and run odds after each signal, beside every member-month as the baseline."""
    c = close.ffill(limit=5)
    st = stage_frame(c, spy)
    hi = c.rolling(252, min_periods=200).max()
    was_down = (c / hi - 1).rolling(252, min_periods=200).min().shift(1)
    m = mem.reindex_like(c).fillna(False).astype(bool)
    prev = st.shift(1)
    sigs = {"New 52-week high after being 30%+ off within the year":
                (c >= hi) & (was_down < -0.3) & (c.shift(1) < hi.shift(1)) & m,
            "New 52-week high after being 50%+ off within the year":
                (c >= hi) & (was_down < -0.5) & (c.shift(1) < hi.shift(1)) & m,
            "Radar: Quiet or Broken to Turning up": (st == "Turning up") & prev.isin(["Quiet", "Broken"]) & m}
    base = pd.DataFrame(False, index=c.index, columns=c.columns)
    base.iloc[::21] = True
    ev = theme_events(c, spy, sigs, gap=63)
    b = theme_events(c, spy, {"Every member, any month (baseline)": base & m & c.shift(252).notna()}, gap=1)
    return theme_event_table(ev, b)


def signals_now(close: pd.DataFrame, signals: dict, days: int = 30) -> pd.DataFrame:
    rows = []
    for name, sig in signals.items():
        recent = sig.iloc[-days:]
        for t in recent.columns[recent.any()]:
            rows.append({"Rule": name, "Theme ETF": t, "Last signal": recent.index[recent[t].to_numpy()][-1].date()})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------- 3. turnaround


def turnaround_events(d: dict, ev: pd.DataFrame, sector: pd.DataFrame) -> pd.DataFrame:
    """Add to each report: its point-in-time sector, how that sector had done, whether analysts expected a weaker
    quarter, and what happened over the next 12 months (vs SPY and vs the sector, and whether it regained its
    52-week high)."""
    C = d["px"]["Close"]
    idx = C.index
    pos = pd.Series(np.arange(len(idx)), index=idx)
    spy = d["spy"]
    E = C[[c for c in SECTOR_ETFS if c in C]].ffill(limit=5)
    E_hi = E.rolling(252, min_periods=200).max()
    out = ev.copy()
    i = pos.reindex(out["date"]).to_numpy().astype(int)
    out["sector"] = [sector.at[idx[k - 1], s] if s in sector.columns else np.nan for k, s in zip(i, out["sym"])]
    get = lambda F, k, s: F.at[idx[k], s] if isinstance(s, str) and s in F.columns else np.nan
    out["sec_off_hi"] = [get(E, k - 1, s) / get(E_hi, k - 1, s) - 1 for k, s in zip(i, out["sector"])]
    out["sec_3m"] = [get(E, k - 1, s) / get(E, k - 64, s) - 1 for k, s in zip(i, out["sector"])]
    out["growth"] = out["sector"].isin(GROWTH_ETFS)
    Cs = C.ffill(limit=5)
    hi = Cs.rolling(252, min_periods=200).max()
    rows = []
    for k, s, sec in zip(i, out["sym"], out["sector"]):
        e0 = k + 1
        r = {}
        if s in Cs and e0 < len(idx):
            p0 = Cs[s].iloc[e0 - 1]   # entry: the open after the reaction day; close of reaction day as stand-in
            o = d["px"]["Open"][s].iloc[e0]
            p_in = o if np.isfinite(o) else p0
            h0 = hi[s].iloc[k - 1]
            for lab, n in (("12m", 252),):
                if e0 + n < len(idx):
                    path = Cs[s].iloc[e0:e0 + n + 1].dropna()
                    if len(path):
                        r["x" + lab] = (path.iloc[-1] / p_in - 1) - (spy.iloc[e0 + n] / spy.iloc[e0] - 1)
                        if isinstance(sec, str) and sec in E:
                            r["xs" + lab] = (path.iloc[-1] / p_in - 1) - (E[sec].iloc[e0 + n] / E[sec].iloc[e0] - 1)
            for lab, n in (("6m", 126), ("12m", 252)):
                if e0 + n < len(idx):
                    path = Cs[s].iloc[e0:e0 + n + 1].dropna()
                    r["new_high" + lab] = float((path >= h0).any()) if np.isfinite(h0) and len(path) else np.nan
            if e0 + 126 < len(idx) and isinstance(sec, str) and sec in E:
                path = Cs[s].iloc[e0:e0 + 127].dropna()
                if len(path):
                    r["xs6m"] = (path.iloc[-1] / p_in - 1) - (E[sec].iloc[e0 + 126] / E[sec].iloc[e0] - 1)
        rows.append(r)
    return pd.concat([out.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


TURN = {
    "Every report": lambda d: d["surprise"].notna(),
    "Any beat": lambda d: d["surprise"] > 0,
    "Beat, and the stock rose vs SPY that day": lambda d: (d["surprise"] > 0) & (d["xreact"] > 0),
    "Low bar: analysts expected EPS below a year ago": lambda d: d["est_yoy"] < 0,
    "Low bar + beat": lambda d: (d["est_yoy"] < 0) & (d["surprise"] > 0),
    "Low bar + beat + stock rose vs SPY that day": lambda d: (d["est_yoy"] < 0) & (d["surprise"] > 0) & (d["xreact"] > 0),
    "Sector hit: sector ETF 10%+ off its high": lambda d: d["sec_off_hi"] < -0.10,
    "Growth sector hit (tech, semis, software, internet, consumer, biotech)":
        lambda d: d["growth"] & (d["sec_off_hi"] < -0.10),
    "Growth sector hit + beat": lambda d: d["growth"] & (d["sec_off_hi"] < -0.10) & (d["surprise"] > 0),
    "Growth sector hit + beat + rose that day":
        lambda d: d["growth"] & (d["sec_off_hi"] < -0.10) & (d["surprise"] > 0) & (d["xreact"] > 0),
    "Adi's setup: growth sector hit + low bar + beat":
        lambda d: d["growth"] & (d["sec_off_hi"] < -0.10) & (d["est_yoy"] < 0) & (d["surprise"] > 0),
    "Adi's setup + the stock rose vs SPY that day":
        lambda d: d["growth"] & (d["sec_off_hi"] < -0.10) & (d["est_yoy"] < 0) & (d["surprise"] > 0) & (d["xreact"] > 0),
    "Adi's setup + rose 5%+ vs SPY that day":
        lambda d: d["growth"] & (d["sec_off_hi"] < -0.10) & (d["est_yoy"] < 0) & (d["surprise"] > 0) & (d["xreact"] > 0.05),
    "Adi's setup + stock itself 25%+ off its high":
        lambda d: d["growth"] & (d["sec_off_hi"] < -0.10) & (d["est_yoy"] < 0) & (d["surprise"] > 0) & (d["off_hi"] < -0.25),
    "Adi's setup, any sector": lambda d: (d["sec_off_hi"] < -0.10) & (d["est_yoy"] < 0) & (d["surprise"] > 0),
    "Adi's setup, sector 20%+ off its high":
        lambda d: d["growth"] & (d["sec_off_hi"] < -0.20) & (d["est_yoy"] < 0) & (d["surprise"] > 0),
    "Market already expected bad: stock fell 15%+ in the 3 months before, then beat":
        lambda d: (d["pre3m"] < -0.15) & (d["surprise"] > 0),
    "  + growth sector hit": lambda d: (d["pre3m"] < -0.15) & (d["surprise"] > 0) & d["growth"] & (d["sec_off_hi"] < -0.10),
    "  + growth sector hit + rose that day":
        lambda d: (d["pre3m"] < -0.15) & (d["surprise"] > 0) & d["growth"] & (d["sec_off_hi"] < -0.10) & (d["xreact"] > 0),
    "Catalyst lab combo (30%+ off high, beat 10%+, up 5%+ vs SPY, EPS up 25%+)":
        lambda d: (d["off_hi"] < -0.3) & (d["surprise"] > 10) & (d["xreact"] > 0.05) & (d["yoy"] > 0.25),
}


def turnaround_table(t: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, rule in TURN.items():
        m = rule(t).fillna(False).astype(bool)
        for per, (a, z) in {"pick": PICK, "grade": GRADE}.items():
            x = t[m & t["date"].between(a, z)]
            rows.append({"Setup": name, "Period": per, "Reports": len(x),
                         "Days that day vs SPY": x["xreact"].mean(),
                         "3m vs SPY": x["x3m"].mean(), "6m vs SPY": x["x6m"].mean(), "12m vs SPY": x["x12m"].mean(),
                         "Median 6m vs SPY": x["x6m"].median(), "Beat SPY over 6m": (x["x6m"] > 0).mean(),
                         "6m vs its sector": x["xs6m"].mean(), "12m vs its sector": x["xs12m"].mean(),
                         "Back to 52w high within 6m": x["new_high6m"].mean(),
                         "Back to 52w high within 12m": x["new_high12m"].mean()})
    return pd.DataFrame(rows)


def turnaround_portfolio(d: dict, t: pd.DataFrame, rules: list, hold: int = 126) -> pd.DataFrame:
    """Each setup as a portfolio: buy at the open after the reaction day, hold ``hold`` days, equal weight across open
    positions (10 bps a side); days with nothing open sit in T-bills."""
    C = d["px"]["Close"].ffill(limit=5)
    O = d["px"]["Open"]
    idx = C.index
    rf = pd.Series(walkforward.carry_forward((d["tbill"]).reindex(idx)).fillna(0).to_numpy() / 252, index=idx)
    ret = C.pct_change(fill_method=None)
    rows = []
    for name in rules:
        m = TURN[name](t).fillna(False).astype(bool)
        x = t[m]
        held = pd.DataFrame(False, index=idx, columns=sorted(set(x["sym"])))
        first = {}
        for s, day in zip(x["sym"], x["date"]):
            k = idx.get_loc(day) + 1
            if k >= len(idx):
                continue
            held.iloc[k:k + hold, held.columns.get_loc(s)] = True
            first[(s, idx[k])] = True
        r_ = ret[held.columns].copy()
        # first day: open-to-close, not yesterday's close
        for (s, day) in first:
            o = O.at[day, s]
            if np.isfinite(o) and o > 0:
                r_.at[day, s] = C.at[day, s] / o - 1
        w = held.astype(float).div(held.sum(axis=1).replace(0, np.nan), axis=0)
        turn = w.fillna(0).diff().abs().sum(axis=1) / 2
        port = (w * r_.fillna(0)).sum(axis=1) - turn * 2 * COST_BPS / 1e4
        port = port.where(held.any(axis=1), rf)
        rows.append({"Setup": name, **_both(port, rf), "Avg positions": held.sum(axis=1).loc[PICK[0]:].mean(),
                     "Time invested": held.any(axis=1).loc[PICK[0]:].mean()})
    rows.append({"Setup": "SPY", **_both(d["spy"].pct_change().fillna(0), rf)})
    return pd.DataFrame(rows)


def turnaround_now(t: pd.DataFrame, since: str) -> pd.DataFrame:
    m = TURN["Adi's setup: growth sector hit + low bar + beat"](t).fillna(False).astype(bool)
    cols = ["sym", "date", "sector", "sec_off_hi", "surprise", "est_yoy", "xreact", "off_hi", "pre3m"]
    return t.loc[m & (t["date"] >= pd.Timestamp(since)), cols].sort_values("date")


# ------------------------------------------------------------------------------------------------- 4. ranking add-ons


def ranking_ic(d: dict, ef: dict, sector: pd.DataFrame) -> pd.DataFrame:
    """Rank correlation (IC) between candidate add-on signals and the next 1 and 3 months' return, across the S&P 500
    members of each month-end. Positive = higher signal, higher later return."""
    C = d["panel"]["Close"].ffill(limit=5)
    mem = d["members"].reindex(index=C.index, columns=C.columns).fillna(False)
    E = d["px"]["Close"][[c for c in SECTOR_ETFS if c in d["px"]["Close"]]].ffill(limit=5)
    e6 = E / E.shift(126) - 1
    sec6 = pd.DataFrame(np.nan, index=C.index, columns=C.columns)
    for etf_name in e6.columns:
        sec6 = sec6.mask(sector.reindex_like(sec6) == etf_name, e6[etf_name], axis=0)
    feats = {"Last earnings surprise": ef["sur"].clip(-100, 100),
             "Fresh beat (beat within 30 days)": ((ef["sur"] > 0) & (ef["since"] <= 30)).astype(float),
             "Analysts' expected growth at the last report": ef["est_yoy"].clip(-2, 5),
             "Low-bar beat (expected decline, then beat)": ((ef["est_yoy"] < 0) & (ef["sur"] > 0)).astype(float),
             "Sector 6-month strength": sec6,
             "Stock 6m strength minus its sector's": (C / C.shift(126) - 1) - sec6}
    f1, f3 = C.shift(-21) / C - 1, C.shift(-63) / C - 1
    rows = []
    month_ends = C.index[C.index >= pd.Timestamp(PICK[0])][::21]
    for name, F in feats.items():
        for per, (a, z) in {"pick": PICK, "grade": GRADE}.items():
            ic1, ic3 = [], []
            for day in month_ends[(month_ends >= pd.Timestamp(a)) & (month_ends <= pd.Timestamp(z))]:
                m = mem.loc[day]
                x = F.loc[day][m]
                for fw, acc in ((f1, ic1), (f3, ic3)):
                    y = fw.loc[day][m]
                    ok = x.notna() & y.notna()
                    if ok.sum() > 50 and x[ok].nunique() > 1:
                        acc.append(x[ok].rank().corr(y[ok].rank()))
            rows.append({"Signal": name, "Period": per, "IC 1 month": np.mean(ic1), "IC 3 months": np.mean(ic3),
                         "Months IC>0 (3m)": np.mean(np.array(ic3) > 0) if ic3 else np.nan, "Months": len(ic3)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------- main


def main(folder: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = load(folder)
    C = d["px"]["Close"]
    print("loaded", d["panel"]["Close"].shape, flush=True)
    mem_all = d["members"].reindex(index=C.index, columns=C.columns).fillna(False).astype(bool)
    ev = cl.earnings_events(d["px"], d["earn"], mem_all)
    ev = ev[ev["date"] >= pd.Timestamp("2005-06-01")]
    print("earnings events", len(ev), flush=True)

    # 3. turnaround (fast, so first)
    stocks = d["panel"]["Close"]
    E = C[[c for c in SECTOR_ETFS if c in C]]
    sector = pit_sector(stocks, E, d["spy"])
    sector.iloc[::21].to_pickle(Path(folder) / "sector_monthly.pkl")
    agree = []
    for s, g in d["gics"].items():
        e = ld.GICS_ETF.get(g)
        if s in sector and isinstance(sector[s].iloc[-1], str) and e:
            fam = {"XLK": {"XLK", "SMH", "IGV"}, "XLV": {"XLV", "XBI"}}.get(e, {e})
            agree.append(sector[s].iloc[-1] in fam)
    print("sector agreement with GICS (today's members):", np.mean(agree), len(agree), flush=True)
    t = turnaround_events(d, ev, sector)
    t.to_pickle(Path(folder) / "turn_events.pkl")
    turnaround_table(t).to_csv(OUT / "turnaround.csv", index=False)
    port_rules = ["Any beat", "Low bar + beat", "Growth sector hit + beat", "Adi's setup: growth sector hit + low bar + beat",
                  "Adi's setup + the stock rose vs SPY that day", "Adi's setup + rose 5%+ vs SPY that day",
                  "Market already expected bad: stock fell 15%+ in the 3 months before, then beat",
                  "  + growth sector hit + rose that day",
                  "Catalyst lab combo (30%+ off high, beat 10%+, up 5%+ vs SPY, EPS up 25%+)"]
    turnaround_portfolio(d, t, port_rules).to_csv(OUT / "turnaround_portfolio.csv", index=False)
    turnaround_now(t, "2026-08-01").to_csv(OUT / "turnaround_now.csv", index=False)
    print("turnaround done", flush=True)

    # 2. themes
    th = C[d["themes"]]
    stages = stage_frame(th.ffill(limit=5), d["spy"])
    sigs = theme_signals(th, d["px"]["Volume"][d["themes"]], d["spy"], stages)
    tev = theme_events(th, d["spy"], sigs)
    base = baseline_events(th, d["spy"])
    tev.to_csv(OUT / "theme_signal_events.csv", index=False)
    theme_event_table(tev, base).to_csv(OUT / "theme_signals.csv", index=False)
    theme_runs(th, d["spy"], stages).to_csv(OUT / "theme_runs.csv", index=False)
    theme_portfolios(th, d["spy"], stages, sigs).to_csv(OUT / "theme_portfolios.csv", index=False)
    radar_replay(d["px"], d["spy"]).to_csv(OUT / "radar_replay.csv", index=False)
    signals_now(th, sigs).to_csv(OUT / "theme_signals_now.csv", index=False)
    stock_breakthroughs(stocks, d["spy"], d["members"]).to_csv(OUT / "stock_breakthroughs.csv", index=False)
    pd.DataFrame({"Theme": stages.columns, "Stage now": stages.iloc[-1].to_numpy(),
                  "12m": (th.ffill().iloc[-1] / th.ffill().iloc[-253] - 1).to_numpy(),
                  "Off high": (th.ffill().iloc[-1] / th.ffill().iloc[-252:].max() - 1).to_numpy()}) \
        .to_csv(OUT / "theme_stages_now.csv", index=False)
    print("themes done", flush=True)

    # 4. ranking add-ons
    ef = earnings_frames(ev, stocks.index, stocks.columns)
    ranking_ic(d, ef, sector).to_csv(OUT / "ranking_ic.csv", index=False)
    print("ranking done", flush=True)

    # 1. confluences (slowest)
    port, buckets, dz, br, rf = run_confluences(d, ev)
    port.to_csv(OUT / "confluences.csv", index=False)
    buckets.to_csv(OUT / "confluence_trades.csv", index=False)
    combos(d, ev).to_csv(OUT / "confluence_combos.csv", index=False)
    print("confluences done", flush=True)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1] if len(sys.argv) > 1 else ".lab2")
