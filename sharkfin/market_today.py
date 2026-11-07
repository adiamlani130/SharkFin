"""Today's market in a few numbers: which way it is going, how broad the move is, what Wall Street expects,
and the one or two things moving it (oil, rates, the dollar, tariffs, the Fed...).

Everything here reads data up to the latest print only. A "big" move is judged against that asset's own
recent history (its daily moves over the past year), so a 2% day in oil and a 2% day in the S&P 500 don't
count the same.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

# Macro prices that often drive the whole market, and how to read a big move in each.
MACRO = {
    "Oil (WTI)": ("CL=F", "Oil", {1: "Oil is jumping: a cost for consumers and airlines, a tailwind for energy stocks.",
                                  -1: "Oil is sliding: cheaper fuel helps consumers and transports, hurts energy stocks."}),
    "10Y Yield": ("^TNX", "Rates", {1: "Treasury yields are rising, which weighs on expensive growth stocks.",
                                    -1: "Treasury yields are falling, which usually helps growth and tech stocks."}),
    "Dollar": ("DX-Y.NYB", "Dollar", {1: "The dollar is strengthening, a headwind for multinationals' overseas sales.",
                                      -1: "The dollar is weakening, a tailwind for multinationals and commodities."}),
    "Gold": ("GC=F", "Gold", {1: "Gold is rallying, often a sign investors want safety.",
                              -1: "Gold is falling as investors leave safe havens."}),
    "Bitcoin": ("BTC-USD", "Crypto", {1: "Bitcoin is surging, a sign of strong risk appetite.",
                                      -1: "Bitcoin is dropping, often an early sign of falling risk appetite."}),
}

# Headline themes worth flagging when several of the latest stories mention them.
THEMES = {
    "Tariffs and trade": r"tariff|trade war|trade deal|export (ban|control)|import dut",
    "The Fed and rates": r"\bfed\b|federal reserve|powell|rate (cut|hike)|interest rate|fomc",
    "Inflation": r"inflation|\bcpi\b|\bpce\b|consumer prices",
    "Jobs": r"jobs report|payroll|unemployment|jobless",
    "Oil and energy": r"\boil\b|opec|crude|brent",
    "AI trade": r"\bai\b|artificial intelligence|nvidia|data center|chip",
    "Geopolitics": r"\bwar\b|missile|sanction|invasion|ceasefire|conflict",
    "Government": r"shutdown|debt ceiling|stimulus|white house|congress",
    "Earnings": r"earnings|guidance|quarterly results|beats estimates|misses estimates",
    "China": r"\bchina\b|beijing|chinese",
}


def _ret(s: pd.Series, n: int = 1) -> float:
    s = s.dropna()
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1) if len(s) > n else np.nan


def move_z(s: pd.Series, diff: bool = False) -> float:
    """Today's move as a multiple of the typical daily move over the past year (absolute change for ``diff``,
    e.g. yields, otherwise percent)."""
    s = s.dropna()
    if len(s) < 40:
        return np.nan
    ch = s.diff() if diff else s.pct_change()
    ch = ch.dropna()
    typical = ch.iloc[-253:-1].std()
    return float(ch.iloc[-1] / typical) if typical and np.isfinite(typical) else np.nan


def breadth(closes: pd.DataFrame) -> dict:
    """Share of stocks up on the latest day and above their 50-day average (S&P 500 closes, dates x tickers)."""
    if closes is None or closes.empty or len(closes) < 2:
        return {"up_today": np.nan, "above50": np.nan, "n": 0}
    last = closes.ffill().iloc[-1]
    prev = closes.ffill().iloc[-2]
    ok = last.notna() & prev.notna()
    up = float((last[ok] > prev[ok]).mean()) if ok.any() else np.nan
    sma50 = closes.ffill().rolling(50, min_periods=40).mean().iloc[-1]
    ok50 = last.notna() & sma50.notna()
    above = float((last[ok50] > sma50[ok50]).mean()) if ok50.any() else np.nan
    return {"up_today": up, "above50": above, "n": int(ok.sum())}


def direction(spx: pd.Series, ndx: pd.Series | None, vix: pd.Series | None, br: dict) -> dict:
    """One plain read of today's tape: label, tone and a sentence."""
    d1 = _ret(spx)
    n1 = _ret(ndx) if ndx is not None else np.nan
    z = move_z(spx)
    v = float(vix.dropna().iloc[-1]) if vix is not None and len(vix.dropna()) else np.nan
    up = br.get("up_today", np.nan)
    if not np.isfinite(d1):
        return {"label": "No data", "tone": "neu", "text": "Index prices are unavailable right now.", "move": d1}
    big = np.isfinite(z) and abs(z) >= 2
    if d1 > 0:
        label = "Strong rally" if big else "Higher" if d1 > 0.002 else "Flat to higher"
    else:
        label = "Sharp selloff" if big else "Lower" if d1 < -0.002 else "Flat to lower"
    tone = "pos" if d1 > 0.002 else "neg" if d1 < -0.002 else "neu"
    bits = [f"The S&P 500 is {'up' if d1 >= 0 else 'down'} {abs(d1):.1%}"]
    if np.isfinite(n1):
        bits.append(f"the Nasdaq {'up' if n1 >= 0 else 'down'} {abs(n1):.1%}")
    txt = " and ".join(bits) + "."
    if np.isfinite(z) and abs(z) >= 1.5:
        txt += f" That is about {abs(z):.1f}x a normal day's move."
    if np.isfinite(up):
        width = ("Nearly everything is rising" if up > 0.8 else "Nearly everything is falling" if up < 0.2 else
                 "Most stocks are rising" if up > 0.6 else "Most stocks are falling" if up < 0.4 else "Stocks are split")
        txt += f" {width}: {up:.0%} of S&P 500 stocks are up."
    if np.isfinite(v):
        txt += f" VIX {v:.1f}" + (" (fear is high)." if v >= 25 else " (calm)." if v < 15 else ".")
    return {"label": label, "tone": tone, "text": txt, "move": d1, "z": z, "vix": v}


def macro_drivers(prices: pd.DataFrame, threshold: float = 2.0) -> list[dict]:
    """Macro prices (columns named by ticker, as in ``MACRO``) whose move today is at least ``threshold``
    times a normal day."""
    out = []
    for name, (sym, tag, read) in MACRO.items():
        if sym not in prices:
            continue
        s = prices[sym].dropna()
        diff = sym == "^TNX"
        z = move_z(s, diff=diff)
        if not np.isfinite(z) or abs(z) < threshold:
            continue
        ch = float(s.iloc[-1] - s.iloc[-2]) if diff else _ret(s)
        size = f"{ch * 100:+.0f} bp" if diff else f"{ch:+.1%}"
        out.append({"driver": tag, "name": name, "move": size, "z": z, "text": read[1 if z > 0 else -1]})
    return sorted(out, key=lambda d: -abs(d["z"]))


def headline_drivers(articles: list[dict], min_hits: int = 3, top: int = 3) -> list[dict]:
    """Themes that several of the latest headlines share, with an example headline each."""
    counts = []
    for theme, pat in THEMES.items():
        rx = re.compile(pat, re.I)
        hits = [a for a in articles if rx.search(f"{a.get('title', '')} {a.get('summary', '')}")]
        if len(hits) >= min_hits:
            counts.append({"driver": theme, "hits": len(hits), "example": hits[0].get("title", ""),
                           "share": len(hits) / max(len(articles), 1)})
    return sorted(counts, key=lambda d: -d["hits"])[:top]


def sector_leaders(sector_closes: pd.DataFrame, names: dict) -> dict:
    """Best and worst sector ETF today: {"best": (name, ret), "worst": (name, ret)}."""
    rows = {n: _ret(sector_closes[s]) for n, s in names.items() if s in sector_closes}
    rows = {k: v for k, v in rows.items() if np.isfinite(v)}
    if not rows:
        return {}
    best = max(rows, key=rows.get)
    worst = min(rows, key=rows.get)
    return {"best": (best, rows[best]), "worst": (worst, rows[worst]), "spread": rows[best] - rows[worst]}


def street_view(infos: pd.DataFrame) -> dict:
    """Wall Street's view of the biggest stocks: cap-weighted upside to the average analyst target, and the
    share rated buy or better (recommendationMean of 2.5 or lower, where 1 = strong buy and 5 = sell)."""
    if infos is None or infos.empty:
        return {}
    n = lambda c: pd.to_numeric(infos[c], errors="coerce") if c in infos else pd.Series(np.nan, index=infos.index)
    px = n("currentPrice").fillna(n("regularMarketPrice"))
    tgt, cap, rec = n("targetMeanPrice"), n("marketCap"), n("recommendationMean")
    ok = px.gt(0) & tgt.gt(0) & cap.gt(0)
    if ok.sum() < 5:
        return {}
    up = tgt[ok] / px[ok] - 1
    w = cap[ok] / cap[ok].sum()
    rated = rec.dropna()
    return {"upside": float((up * w).sum()), "median_upside": float(up.median()),
            "buy_share": float((rated <= 2.5).mean()) if len(rated) else np.nan, "n": int(ok.sum()),
            "top": up.sort_values(ascending=False).head(3).to_dict(), "bottom": up.sort_values().head(3).to_dict()}
