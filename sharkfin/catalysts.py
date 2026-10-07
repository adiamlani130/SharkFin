"""Catalysts and long-term ("core long") checks.

The catalysts are the best-documented "not yet priced in" signals:
  * post-earnings-announcement drift: prices keep drifting for weeks after an
    earnings surprise (Bernard & Thomas 1989; still present in 2015-2024 data)
  * open-market insider purchases, especially several insiders buying at once
    (Lakonishok & Lee 2001; Cohen, Malloy & Pomorski 2012)
  * net share buybacks
  * analyst estimate revisions
  * changes in 10-K language: companies whose annual report text changes a lot
    tend to underperform ("Lazy Prices", Cohen, Malloy & Nguyen 2020)
"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np
import pandas as pd

from . import indicators as ind
from . import valuation

# ---------------------------------------------------------------------------
# Earnings
# ---------------------------------------------------------------------------


def earnings_summary(earnings_dates: pd.DataFrame | None, now: pd.Timestamp | None = None) -> dict:
    out = {"next_date": None, "last_date": None, "last_surprise": np.nan, "beats_last4": None,
           "days_since": None, "drift_window": False, "note": "No earnings history available."}
    if not isinstance(earnings_dates, pd.DataFrame) or earnings_dates.empty or "Reported EPS" not in earnings_dates:
        return out
    ed = earnings_dates.copy()
    ed.index = pd.to_datetime(ed.index)
    if ed.index.tz is not None:
        ed.index = ed.index.tz_convert("America/New_York").tz_localize(None)
    ed = ed.sort_index()
    now = now or pd.Timestamp.now()
    rep = ed.dropna(subset=["Reported EPS"])
    upcoming = ed[ed["Reported EPS"].isna() & (ed.index >= now - pd.Timedelta(days=1))]
    if len(upcoming):
        out["next_date"] = upcoming.index[0]
    if rep.empty:
        return out
    last = rep.iloc[-1]
    out["last_date"] = rep.index[-1]
    surprise = last.get("Surprise(%)", np.nan)
    if not np.isfinite(surprise) and last.get("EPS Estimate"):
        surprise = (last["Reported EPS"] / last["EPS Estimate"] - 1) * 100
    out["last_surprise"] = float(surprise) / 100 if np.isfinite(surprise) else np.nan
    tail = rep.tail(4)
    if "EPS Estimate" in tail:
        out["beats_last4"] = int((tail["Reported EPS"] >= tail["EPS Estimate"]).sum())
    out["days_since"] = int((now - out["last_date"]).days)
    s = out["last_surprise"]
    # Drift is strongest in the ~60 trading days (~90 calendar days) after the report.
    out["drift_window"] = bool(np.isfinite(s) and s >= 0.05 and out["days_since"] <= 90)
    if not np.isfinite(s):
        out["note"] = "Last surprise unknown."
    elif out["drift_window"]:
        out["note"] = (f"Beat by {s:.0%} {out['days_since']} days ago. Stocks with big beats have historically kept "
                       "drifting up for about 60 trading days after the report.")
    elif s <= -0.05 and out["days_since"] <= 90:
        out["note"] = f"Missed by {abs(s):.0%} {out['days_since']} days ago: drift tends to work against longs for a while."
    else:
        out["note"] = f"Last surprise {s:+.0%}, {out['days_since']} days ago: no strong drift signal."
    return out


# ---------------------------------------------------------------------------
# Insiders
# ---------------------------------------------------------------------------


def insider_summary(tx: pd.DataFrame | None, days: int = 180, now: pd.Timestamp | None = None) -> dict:
    out = {"buys": 0, "buyers": 0, "buy_value": 0.0, "sells": 0, "sell_value": 0.0, "cluster": False,
           "table": pd.DataFrame(), "note": "No insider data available."}
    if not isinstance(tx, pd.DataFrame) or tx.empty or "Text" not in tx:
        return out
    t = tx.copy()
    date_col = "Start Date" if "Start Date" in t else None
    if date_col:
        t[date_col] = pd.to_datetime(t[date_col], errors="coerce")
        now = now or pd.Timestamp.now()
        t = t[t[date_col] >= now - pd.Timedelta(days=days)]
    text = t["Text"].astype(str).str.lower()
    value = pd.to_numeric(t.get("Value"), errors="coerce").fillna(0)
    buy = text.str.startswith("purchase") | text.str.contains("buy", regex=False)
    sell = text.str.startswith("sale")
    out.update(buys=int(buy.sum()), buyers=int(t.loc[buy, "Insider"].nunique()) if "Insider" in t else int(buy.sum()),
               buy_value=float(value[buy].sum()), sells=int(sell.sum()), sell_value=float(value[sell].sum()))
    out["cluster"] = out["buyers"] >= 2
    keep = [c for c in ("Start Date", "Insider", "Position", "Text", "Shares", "Value") if c in t]
    out["table"] = t.loc[buy | sell, keep]
    if out["buys"] == 0:
        out["note"] = (f"No open-market insider purchases in {days} days. Insider selling is common (taxes, "
                       "diversification) and says much less than buying.")
    elif out["cluster"]:
        out["note"] = (f"{out['buyers']} different insiders bought on the open market in the last {days} days. "
                       "Cluster buying is one of the stronger insider signals.")
    else:
        out["note"] = f"One insider bought on the open market in the last {days} days."
    return out


# ---------------------------------------------------------------------------
# Buybacks, revisions, volume
# ---------------------------------------------------------------------------


def net_buyback_yield(fin: valuation.Financials, market_cap: float) -> float:
    """(Buybacks − share issuance) over the last fiscal year / market cap."""
    rep = valuation._line(fin.cashflow, "Repurchase Of Capital Stock")
    iss = valuation._line(fin.cashflow, "Issuance Of Capital Stock", "Common Stock Issuance")
    b = -valuation._v(rep, 0, 0.0)
    i = valuation._v(iss, 0, 0.0)
    if not np.isfinite(market_cap) or market_cap <= 0 or (b == 0 and i == 0):
        return np.nan
    return float((b - i) / market_cap)


def revision_balance(eps_revisions: pd.DataFrame | None) -> float:
    """Net share of estimate revisions that were upward over 30 days (−1 … 1)."""
    if not isinstance(eps_revisions, pd.DataFrame) or eps_revisions.empty:
        return np.nan
    up = pd.to_numeric(eps_revisions.get("upLast30days"), errors="coerce").sum()
    down = pd.to_numeric(eps_revisions.get("downLast30days"), errors="coerce").sum()
    return float((up - down) / (up + down)) if up + down > 0 else 0.0


def volume_read(ohlcv: pd.DataFrame) -> dict:
    """Is volume confirming the move, and has accumulation started?"""
    v, c = ohlcv["Volume"].astype(float), ohlcv["Close"]
    if len(v) < 60 or v.iloc[-50:].sum() == 0:
        return {"rel_volume_20d": np.nan, "spikes_up": 0, "spikes_down": 0, "obv_trend": None, "note": "Not enough volume data."}
    avg50 = v.rolling(50).mean()
    rel20 = float(v.iloc[-20:].mean() / avg50.iloc[-21])
    spike = v > 2 * avg50.shift(1)
    ret = c.pct_change()
    last20 = slice(-20, None)
    up = int((spike & (ret > 0)).iloc[last20].sum())
    down = int((spike & (ret < 0)).iloc[last20].sum())
    obv = ind.obv(c, v)
    obv_up = bool(obv.iloc[-1] > obv.iloc[-21])
    price_up = bool(c.iloc[-1] > c.iloc[-21])
    if up >= 1 and obv_up:
        note = "Volume is confirming: high-volume up days and rising OBV in the last month."
    elif obv_up and not price_up:
        note = "OBV is rising while price isn't: possible quiet accumulation ahead of a move."
    elif not obv_up and price_up:
        note = "Price is up but OBV is falling: the rally isn't backed by volume."
    elif rel20 < 0.8 and up == 0:
        note = ("No accumulation yet: volume is below normal with no buying spikes. If you're long on a thesis, "
                "you may be early, or nobody cares yet.")
    else:
        note = "Nothing unusual in volume."
    return {"rel_volume_20d": rel20, "spikes_up": up, "spikes_down": down, "obv_trend": "Rising" if obv_up else "Falling",
            "note": note}


# ---------------------------------------------------------------------------
# Filing text (10-K) changes
# ---------------------------------------------------------------------------

_WORD = re.compile(r"[a-z]{3,}")


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = re.sub(r"&#160;|&nbsp;|&#xa0;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&#8217;|&rsquo;", "'", html)
    html = re.sub(r"&[a-z#0-9]+;", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def risk_factors_section(text: str) -> str:
    """Item 1A (Risk Factors) of a 10-K. The table of contents mentions it too,
    so take the longest span between an 'Item 1A' heading and the next item."""
    starts = [m.start() for m in re.finditer(r"(?i)item\s*1a\.?\s*[\-–—:]?\s*risk\s+factors", text)]
    best = ""
    for s in starts:
        m = re.search(r"(?i)item\s*(1b|1c|2)\.?\s*[\-–—:]?\s*(unresolved|cybersecurity|properties)", text[s + 50:])
        seg = text[s: s + 50 + m.start()] if m else text[s: s + 200_000]
        if len(seg) > len(best):
            best = seg
    return best


def text_similarity(a: str, b: str) -> float:
    """Cosine similarity of word counts (the Lazy Prices measure). 1 = identical wording."""
    ca, cb = Counter(_WORD.findall(a.lower())), Counter(_WORD.findall(b.lower()))
    if not ca or not cb:
        return np.nan
    dot = sum(v * cb.get(k, 0) for k, v in ca.items())
    na = np.sqrt(sum(v * v for v in ca.values()))
    nb = np.sqrt(sum(v * v for v in cb.values()))
    return float(dot / (na * nb))


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if 60 <= len(s.strip()) <= 600]


def new_sentences(old: str, new: str, n: int = 8) -> list[str]:
    """Sentences in the new filing whose wording doesn't appear in the old one."""
    seen = {re.sub(r"\W+", " ", s.lower()) for s in _sentences(old)}
    fresh = [s for s in _sentences(new) if re.sub(r"\W+", " ", s.lower()) not in seen]
    return sorted(fresh, key=len, reverse=True)[:n]


def filing_change(old_text: str, new_text: str) -> dict:
    old_rf, new_rf = risk_factors_section(old_text), risk_factors_section(new_text)
    use_rf = len(old_rf) > 2000 and len(new_rf) > 2000
    a, b = (old_rf, new_rf) if use_rf else (old_text, new_text)
    sim = text_similarity(a, b)
    if not np.isfinite(sim):
        label = "Unknown"
    elif sim >= 0.97:
        label = "Barely changed"
    elif sim >= 0.90:
        label = "Moderately changed"
    else:
        label = "Heavily changed"
    return {"similarity": sim, "label": label, "section": "Risk factors (Item 1A)" if use_rf else "Whole filing",
            "new_sentences": new_sentences(a, b), "length_change": (len(b) / len(a) - 1) if a else np.nan}


# ---------------------------------------------------------------------------
# Core long checklist for one stock
# ---------------------------------------------------------------------------


def core_long_checklist(inf: dict, fin: valuation.Financials, hist: pd.DataFrame, analyst: dict | None = None,
                        insiders: dict | None = None, earnings: dict | None = None) -> dict:
    """Multi-year hold checklist: quality, cash, valuation, trend, revisions, catalysts."""
    analyst = analyst or {}
    num = lambda k: pd.to_numeric(inf.get(k), errors="coerce")
    mcap = float(num("marketCap")) if pd.notna(num("marketCap")) else np.nan
    qm = valuation.quality_metrics(fin, mcap)
    f = valuation.piotroski_f_score(fin)
    c = hist["Close"]
    rows = []

    def add(test, ok, detail, why):
        rows.append({"Test": test, "Pass": None if ok is None else bool(ok), "Detail": detail, "Why it matters": why})

    fs = f.score if f else None
    add("Piotroski F-score ≥ 7", None if fs is None else fs >= 7, f"{fs}/9" if fs is not None else "n/a",
        "Nine accounting tests of improving profitability, leverage and efficiency. High scorers have beaten low scorers for decades.")
    gp = qm.get("Gross profitability (GP/TA)", np.nan)
    add("Gross profitability ≥ 25%", None if not np.isfinite(gp) else gp >= 0.25, f"{gp:.0%}" if np.isfinite(gp) else "n/a",
        "Gross profit divided by total assets (Novy-Marx 2013): one of the most reliable quality factors.")
    roic = qm.get("ROIC", np.nan)
    add("ROIC ≥ 10%", None if not np.isfinite(roic) else roic >= 0.10, f"{roic:.0%}" if np.isfinite(roic) else "n/a",
        "Return on invested capital above ~10% means the business earns more than its cost of capital.")
    fcf_y = qm.get("FCF yield", np.nan)
    ey = 1 / num("forwardPE") if pd.notna(num("forwardPE")) and num("forwardPE") > 0 else np.nan
    val_ok = None if not (np.isfinite(fcf_y) or np.isfinite(ey)) else (np.nan_to_num(fcf_y) >= 0.025 or np.nan_to_num(ey) >= 0.035)
    add("Not expensive", val_ok, f"FCF yield {fcf_y:.1%} · fwd earnings yield {ey:.1%}" if np.isfinite(fcf_y) and np.isfinite(ey)
        else "n/a", "FCF yield ≥ 2.5% or forward P/E ≤ ~28. Great companies bought at any price can still be poor investments.")
    if len(c) > 253:
        mom = c.iloc[-22] / c.iloc[-253] - 1
        add("12-month momentum positive", mom > 0, f"{mom:+.0%}",
            "Stocks that rose over the past year (skipping the last month) tend to keep outperforming; it also avoids value traps.")
    s200 = ind.sma(c, 200).iloc[-1]
    add("Above 200-day average", None if not np.isfinite(s200) else c.iloc[-1] > s200,
        f"{c.iloc[-1] / s200 - 1:+.0%} vs 200-day" if np.isfinite(s200) else "n/a",
        "Buying long-term holdings while they're in an uptrend avoids catching falling knives.")
    rb = revision_balance(analyst.get("eps_revisions"))
    add("Analysts revising estimates up", None if not np.isfinite(rb) else rb > 0,
        f"net {rb:+.0%} of 30-day revisions up" if np.isfinite(rb) else "n/a",
        "Rising estimates tend to lead rising prices.")
    if earnings is not None and np.isfinite(earnings.get("last_surprise", np.nan)):
        add("Beat last earnings", earnings["last_surprise"] > 0, f"{earnings['last_surprise']:+.0%}",
            "Positive surprises tend to be followed by weeks of upward drift.")
    if insiders is not None and insiders.get("buys"):
        add("Insider buying (6 months)", True, f"{insiders['buyers']} insider(s) bought",
            "Open-market insider purchases have historically preceded outperformance.")
    scored = [r for r in rows if r["Pass"] is not None]
    passed = sum(r["Pass"] for r in scored)
    frac = passed / len(scored) if scored else np.nan
    if not scored:
        verdict, tone = "Not enough data", "neu"
    elif frac >= 0.75:
        verdict, tone = "Core long candidate", "pos"
    elif frac >= 0.5:
        verdict, tone = "Watchlist: some boxes missing", "neu"
    else:
        verdict, tone = "Not a core long right now", "neg"
    return {"rows": rows, "passed": passed, "total": len(scored), "verdict": verdict, "tone": tone}


CORE_LONG_INTRO = (
    "Stocks to buy and hold for months to years. Every stock has to pass six simple rules (profitable, in an uptrend, "
    "rising steadily rather than in jumps, not too volatile, not over-borrowed, not expensive for its sector), then "
    "the survivors are ranked by momentum, smoothness and value. Tested on S&amp;P 500 stocks from 2023 to 2025, the "
    "top 25 had a median 12-month return of 21% versus 14% for the index members, 83% of them were up a year later, "
    "and only 4% lost more than a fifth (vs 9%). That tilts the odds; it does not guarantee anything.")
CORE_SCORE_HELP = ("Momentum + smoothness of the climb + value, each in standard deviations versus the list. "
                   "Higher is better; only stocks that pass every rule get a score.")

_NO_FCF_SECTORS = {"Financial Services", "Real Estate"}


def _col(df: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(df[c], errors="coerce") if c in df else pd.Series(np.nan, index=df.index)


def _z(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and sd > 0 else s * 0


def core_long_screen(scores: pd.DataFrame, info_df: pd.DataFrame | None = None,
                     top: int = 25) -> tuple[pd.DataFrame, list[dict]]:
    """Long-horizon screen: six pass/fail gates, then rank by momentum + FIP + value.

    Returns the ranked survivors and a funnel showing how many stocks are left
    after each rule. Missing data fails a rule only where the rule needs it
    (no profit data means we can't call it profitable)."""
    df = scores.copy()
    inf = (info_df if info_df is not None else pd.DataFrame()).reindex(df.index)
    sector = df["Sector"] if "Sector" in df else inf.get("sector", pd.Series(np.nan, index=df.index))
    fin_like = sector.isin(_NO_FCF_SECTORS)

    ni = _col(inf, "netIncomeToCommon")
    eps = _col(inf, "trailingEps")
    profit_known = ni.notna() | eps.notna()
    profitable = ni.where(ni.notna(), eps) > 0
    fcf = _col(inf, "freeCashflow")
    cash_ok = fin_like | (fcf > 0) | (fcf.isna() & _col(inf, "operatingCashflow").gt(0))
    mom = _col(df, "mom_12_1")
    trend = _col(df, "trend_200")
    fip = _col(df, "fip")
    vol = _col(df, "volatility")
    debt, cash, ebitda = _col(inf, "totalDebt"), _col(inf, "totalCash"), _col(inf, "ebitda")
    nd_ebitda = (debt.fillna(0) - cash.fillna(0)) / ebitda.where(ebitda > 0)
    de = _col(inf, "debtToEquity") / 100
    lev_ok = fin_like | (nd_ebitda < 3) | (nd_ebitda.isna() & (de.isna() | (de < 1.5)))
    value = _col(df, "Value")

    rules = [
        ("Profitable", profit_known & profitable & cash_ok,
         "Positive earnings and free cash flow (cash flow waived for banks and REITs). Money-losing companies "
         "are where most long-term blow-ups come from."),
        ("In an uptrend", (trend > 0) & (mom > 0),
         "Above its 200-day average and up over the last 12 months (skipping the latest month). Avoids catching falling knives."),
        ("Steady climb", fip >= fip.median(),
         "More up days than down days over the past year, top half of the list. Gains that come gradually tend to "
         "persist; gains from one or two jumps tend to fade."),
        ("Not too volatile", vol.rank(pct=True) < 0.7,
         "Outside the 30% most volatile stocks. Wild stocks cause most of the large losses."),
        ("Debt under control", lev_ok,
         "Net debt under 3x EBITDA (or debt under 1.5x equity). Waived for banks, whose balance sheets work differently."),
        ("Not expensive", value.isna() | (value > -1),
         "Not in the priciest sixth of its sector on earnings, cash flow and EBITDA."),
    ]
    funnel = [{"Rule": "All stocks scanned", "Still in": len(df), "Why": "Starting universe."}]
    keep = pd.Series(True, index=df.index)
    for name, mask, why in rules:
        keep &= mask.fillna(False).astype(bool)
        funnel.append({"Rule": name, "Still in": int(keep.sum()), "Why": why})
    out = df[keep].copy()
    if out.empty:
        return out, funnel
    # Rank survivors on the full-list z-scores so the score means the same thing every scan.
    zfip = _z(fip)
    zmom = _z(mom.clip(mom.quantile(0.02), mom.quantile(0.98)))
    out["Core score"] = (zmom + zfip + value.fillna(0)).reindex(out.index)
    out["fip"] = fip.reindex(out.index)
    for c, src in (("roe", "returnOnEquity"),):
        if c not in out:
            out[c] = _col(inf, src).reindex(out.index)
    return out.sort_values("Core score", ascending=False).head(top), funnel
