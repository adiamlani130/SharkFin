"""SharkFin Ratings: five ratings and an overall Shark Score, each a percentile within the stock's own sector
(0-100, where 50 is the sector's middle stock).

  Value     earnings yield (trailing EPS / price) and dividend yield.
  Momentum  the past year's gain skipping the last month, and how steady the climb was (share of up days minus
            down days).
  Earnings  the last quarter's EPS surprise and the run of quarters that beat estimates.
  Pullback  how far the stock fell over the last month (a bigger drop scores higher).
  Risk      volatility and the worst drop over the past year (higher = riskier). Shown for context only.

The Shark Score averages Value, Momentum and Earnings, the three themes that pointed the right way in both
halves of SharkFin's 2002-2026 test on point-in-time S&P 500 members. Pullback helped in 2002-12 but not after,
and lower risk cost return, so neither counts toward the score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SCORE_PARTS = ("Value", "Momentum", "Earnings")
LIST_RESULT = ("The list takes the 20 highest Shark Scores among stocks with a steady past-year climb and no more risk "
               "than their sector's middle stock, re-checked each Friday. A stock is sold once it drops out of the top 60, "
               "and the list sits in cash while the S&amp;P 500 is below its 10-month average. Over 2005-2026 that made "
               "about 9-10% a year in both halves with a worst drop of 20%; holding every S&amp;P 500 stock equally made "
               "12% a year but fell 56% at worst.")
NAMES = {"Shark Score": "Shark Score", "Value": "Value", "Momentum": "Momentum", "Earnings": "Earnings",
         "Pullback": "Pullback", "Risk": "Risk"}
HELP = {
    "Shark Score": "The average of the Value, Momentum and Earnings ratings: 0-100 against the stock's sector, where "
                   "50 is the middle stock. It counts only the three themes that held up in both halves of SharkFin's "
                   "2002-2026 test.",
    "Value": "Earnings yield (trailing EPS / price) and dividend yield, against the sector. Higher = cheaper. The "
             "steadiest theme in the 2002-2026 test.",
    "Momentum": "The past year's gain, skipping the last month, and how steady the climb was, against the sector. "
                "Higher = a stronger, smoother uptrend.",
    "Earnings": "The last quarter's EPS surprise and the run of quarters that beat estimates, against the sector. "
                "Higher = beating estimates more, and more often.",
    "Pullback": "How far the stock fell over the last month, against the sector. Higher = a bigger recent drop. Recent "
                "losers bounced in 2002-12 but not reliably since, so it is not part of the Shark Score.",
    "Risk": "Volatility and the worst drop over the past year, against the sector. Higher = riskier. Context only: "
            "in the test, lower risk cost return.",
}

# Sector names from Yahoo and from the S&P 500 (GICS) list, mapped to the SPDR sector ETFs.
SECTOR_ETF = {
    "Technology": "XLK", "Information Technology": "XLK",
    "Financial Services": "XLF", "Financials": "XLF",
    "Healthcare": "XLV", "Health Care": "XLV",
    "Consumer Cyclical": "XLY", "Consumer Discretionary": "XLY",
    "Communication Services": "XLC",
    "Industrials": "XLI",
    "Consumer Defensive": "XLP", "Consumer Staples": "XLP",
    "Energy": "XLE", "Utilities": "XLU", "Real Estate": "XLRE",
    "Basic Materials": "XLB", "Materials": "XLB",
}
GICS_OF_ETF = {"XLK": "Information Technology", "XLF": "Financials", "XLV": "Health Care", "XLY": "Consumer Discretionary",
               "XLC": "Communication Services", "XLI": "Industrials", "XLP": "Consumer Staples", "XLE": "Energy",
               "XLU": "Utilities", "XLRE": "Real Estate", "XLB": "Materials"}


def to_gics(sector) -> str | None:
    etf = SECTOR_ETF.get(str(sector)) if sector is not None else None
    return GICS_OF_ETF.get(etf) if etf else None


def sector_rank(x: pd.Series, sectors: pd.Series | None, min_group: int = 5) -> pd.Series:
    """Percentile within each sector on a 0-100 scale (50 = the sector's middle).
    Sectors with fewer than ``min_group`` stocks fall back to the whole list."""
    x = pd.to_numeric(x, errors="coerce")
    out = x.rank(pct=True) * 100
    if sectors is None:
        return out
    sec = sectors.reindex(x.index)
    for _, idx in sec.groupby(sec).groups.items():
        grp = x.loc[idx]
        if grp.notna().sum() >= min_group:
            out.loc[idx] = grp.rank(pct=True) * 100
    return out.where(x.notna())


def _blend(parts: list[pd.Series]) -> pd.Series:
    """Average of the available percentile ranks (NaN where none is available)."""
    return pd.concat(parts, axis=1).mean(axis=1, skipna=True) if parts else pd.Series(dtype=float)


def price_components(close: pd.DataFrame) -> pd.DataFrame:
    """Raw price inputs at the last row of a dates x tickers panel."""
    close = close.astype(float)
    c = close.ffill()
    n = len(c)
    out = pd.DataFrame(index=close.columns)
    out["mom_12_1"] = c.iloc[-22] / c.iloc[-253] - 1 if n > 252 else np.nan
    rets = close.pct_change(fill_method=None)
    w = rets.iloc[-252:-21]
    out["steady_climb"] = ((w > 0).mean() - (w < 0).mean()).where(w.notna().sum() >= 150) if len(w) else np.nan
    out["ret_1m"] = c.iloc[-1] / c.iloc[-22] - 1 if n > 22 else np.nan
    yr = close.iloc[-252:]
    out["volatility"] = yr.pct_change(fill_method=None).std() * np.sqrt(252)
    out["worst_drop"] = (yr / yr.cummax() - 1).min()
    out.loc[yr.notna().sum() < 200, ["volatility", "worst_drop"]] = np.nan
    return out


def value_inputs(info_df: pd.DataFrame) -> pd.DataFrame:
    """Earnings yield (trailing) and dividend yield from Yahoo company data."""
    g = lambda c: pd.to_numeric(info_df[c], errors="coerce") if c in info_df else pd.Series(np.nan, index=info_df.index)
    price = g("currentPrice").fillna(g("regularMarketPrice"))
    ey = (g("trailingEps") / price.where(price > 0)).fillna(1 / g("trailingPE").where(lambda x: x > 0))
    dy = g("dividendYield")
    dy = dy.where(dy < 0.3, dy / 100).fillna(0.0).clip(0, 0.15) if "dividendYield" in info_df else pd.Series(np.nan, index=info_df.index)
    return pd.DataFrame({"earnings_yield": ey.clip(-0.5, 0.5), "dividend_yield": dy})


def ratings(close: pd.DataFrame, sectors: pd.Series | None, info_df: pd.DataFrame | None = None,
            earn_f: pd.DataFrame | None = None) -> pd.DataFrame:
    """Value, Momentum, Earnings, Pullback, Risk and the Shark Score (0-100 within sector) for every column of
    ``close``. ``info_df`` is Yahoo company data and ``earn_f`` is ``factors.earnings_factor_frame`` output; without
    them Value and Earnings are left empty and the Shark Score uses Momentum alone."""
    pc = price_components(close)
    secs = sectors.reindex(pc.index) if sectors is not None else None
    rk = lambda x: sector_rank(x, secs)
    out = pd.DataFrame(index=pc.index)
    if info_df is not None and not info_df.empty:
        vi = value_inputs(info_df.reindex(pc.index))
        out["Value"] = _blend([rk(vi["earnings_yield"]), rk(vi["dividend_yield"])])
        pc = pc.join(vi)
    else:
        out["Value"] = np.nan
    out["Momentum"] = _blend([rk(pc["mom_12_1"]), rk(pc["steady_climb"])])
    if earn_f is not None and not earn_f.empty:
        ef = earn_f.reindex(pc.index)
        out["Earnings"] = _blend([rk(ef[c]) for c in ("eps_surprise", "beat_streak") if c in ef])
        pc = pc.join(ef[[c for c in ("eps_surprise", "beat_streak") if c in ef]])
    else:
        out["Earnings"] = np.nan
    out["Pullback"] = rk(-pc["ret_1m"])
    out["Risk"] = _blend([rk(pc["volatility"]), rk(-pc["worst_drop"])])
    out["Shark Score"] = shark_score(out)
    return out.join(pc)


def shark_score(r: pd.DataFrame | dict) -> pd.Series | float:
    """Average of the available Value, Momentum and Earnings ratings (needs at least two, or Momentum alone when
    no company data was loaded at all)."""
    if isinstance(r, dict):
        vals = [r.get(k) for k in SCORE_PARTS if r.get(k) is not None and np.isfinite(r.get(k))]
        return float(np.mean(vals)) if len(vals) >= 2 else np.nan
    parts = r[list(SCORE_PARTS)]
    n = parts.notna().sum(axis=1)
    need = 2 if parts[["Value", "Earnings"]].notna().any().any() else 1
    return parts.mean(axis=1, skipna=True).where(n >= need)


def score_list(rat: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """The weekly list: the ``n`` highest Shark Scores among stocks whose past year was a steady climb (steadiness
    in the top half of the list) and whose Risk is no higher than their sector's middle stock."""
    r = rat.dropna(subset=["Shark Score"]).copy()
    if "steady_climb" in r:
        r = r[pd.to_numeric(r["steady_climb"], errors="coerce").rank(pct=True) >= 0.5]
    r = r[r["Risk"].fillna(100) <= 50]
    r["List rank"] = r["Shark Score"].rank(ascending=False, method="first")
    return r.sort_values("Shark Score", ascending=False).head(n)


def sector_context(symbol: str, stock_close: pd.Series, sector, etf_close: pd.DataFrame,
                   member_close: pd.DataFrame | None = None, member_sectors: pd.Series | None = None) -> dict:
    """How the stock's sector is doing, and the stock against it.

    ``etf_close`` holds the SPDR sector ETFs (columns = tickers);
    ``member_close``/``member_sectors`` are the S&P 500 closes and GICS sectors
    for the breadth reading."""
    etf = SECTOR_ETF.get(str(sector)) if sector else None
    if not etf or etf not in etf_close or etf_close[etf].dropna().shape[0] < 130:
        return {}
    six = {c: float(s.iloc[-1] / s.iloc[-127] - 1) for c in etf_close for s in [etf_close[c].dropna()] if len(s) > 127}
    ranked = sorted(six, key=six.get, reverse=True)
    e = etf_close[etf].dropna()
    out = {"etf": etf, "gics": GICS_OF_ETF[etf], "sector_6m": six[etf], "rank": ranked.index(etf) + 1, "n_sectors": len(six),
           "off_high": float(e.iloc[-1] / e.iloc[-252:].max() - 1)}
    s = stock_close.dropna()
    out["stock_6m"] = float(s.iloc[-1] / s.iloc[-127] - 1) if len(s) > 127 else np.nan
    out["vs_sector"] = out["stock_6m"] - out["sector_6m"] if np.isfinite(out["stock_6m"]) else np.nan
    out["breadth"], out["breadth_n"] = np.nan, 0
    if member_close is not None and member_sectors is not None:
        cols = [c for c in member_sectors.index[member_sectors == out["gics"]] if c in member_close]
        if cols:
            mc = member_close[cols].iloc[-260:]
            last, sma = mc.ffill().iloc[-1], mc.iloc[-200:].mean()
            ok = sma.notna() & (mc.notna().sum() >= 200)
            if ok.sum() >= 5:
                out["breadth"], out["breadth_n"] = float((last[ok] > sma[ok]).mean()), int(ok.sum())
    return out
