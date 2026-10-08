"""VectorVest-style ratings, each ranked within the stock's own sector, plus
sector context for a single stock.

The ratings are SharkFin's own versions of VectorVest's published ideas, on a
0-2 scale where 1 is the middle of the stock's sector:

  RT (relative timing): price trend against the market, blended over a day, a
      week, a quarter and a year (weights 5/15/40/40%).
  RV (relative value): a Graham-style value, EPS x (8.5 + 2 x growth) x 4.4 /
      the AAA bond yield (approximated as the 10-year Treasury + 1%), divided
      by the price.
  RS (relative safety): low volatility, low beta, a shallow worst drop over the
      past year, and, when company data is available, trading liquidity and
      positive earnings.
  CI (comfort index): how well the stock has avoided deep or long declines over
      the past year (the Ulcer index, lower is better).
  VST: the root-mean-square of RV, RT and RS.

In SharkFin's Oct 2026 research these ratings barely predicted the next
month's return on their own (the best was RT). Their use was as a steady
weekly list: the 20 highest sector-relative VSTs with a steady past-year climb,
held while the S&P 500 stayed above its 10-month average, made 10-11% a year
in every test period with a worst drop of 16%.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RT_WEIGHTS = {1: 0.05, 5: 0.15, 63: 0.40, 252: 0.40}
NAMES = {"RV": "Value (RV)", "RT": "Timing (RT)", "RS": "Safety (RS)", "CI": "Comfort (CI)", "VST": "VST"}
HELP = {
    "RV": "Graham-style value per dollar of price (EPS, earnings growth and bond yields), ranked within the sector. "
          "Above 1 = cheaper than the sector's middle stock.",
    "RT": "Price trend against the market over a day, a week, a quarter and a year, ranked within the sector. "
          "Above 1 = acting better than the sector's middle stock.",
    "RS": "Low volatility, low beta and a shallow worst drop over the past year, ranked within the sector. "
          "Above 1 = steadier than the sector's middle stock.",
    "CI": "How well the stock avoided deep or drawn-out declines over the past year (Ulcer index), ranked within "
          "the sector. Above 1 = a smoother ride than the sector's middle stock.",
    "VST": "The three main ratings combined: the root-mean-square of RV, RT and RS. Above 1 = better than the "
           "sector's middle stock overall. On its own it barely predicted the next month.",
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
    """Percentile rank within each sector on a 0-2 scale (1 = the sector's middle).
    Sectors with fewer than ``min_group`` stocks fall back to the whole list."""
    x = pd.to_numeric(x, errors="coerce")
    out = x.rank(pct=True) * 2
    if sectors is None:
        return out
    sec = sectors.reindex(x.index)
    for _, idx in sec.groupby(sec).groups.items():
        grp = x.loc[idx]
        if grp.notna().sum() >= min_group:
            out.loc[idx] = grp.rank(pct=True) * 2
    return out.where(x.notna())


def _market(close: pd.DataFrame) -> pd.Series:
    r = close.pct_change(fill_method=None).clip(-0.5, 1.0).mean(axis=1).fillna(0.0)
    return (1 + r).cumprod()


def price_components(close: pd.DataFrame, market: pd.Series | None = None) -> pd.DataFrame:
    """Raw inputs for RT, RS and CI at the last row of a dates x tickers panel."""
    close = close.astype(float)
    m = (market.reindex(close.index).ffill() if market is not None else _market(close)).astype(float)
    last, n = close.ffill().iloc[-1], len(close)
    out = pd.DataFrame(index=close.columns)
    rt = pd.Series(0.0, index=close.columns)
    wsum = 0.0
    for h, w in RT_WEIGHTS.items():
        if n > h:
            rel = np.log((last / close.ffill().iloc[-1 - h]) / (m.iloc[-1] / m.iloc[-1 - h]))
            rt = rt + w * rel
            wsum += w
    out["rt_raw"] = rt / wsum if wsum else np.nan
    yr = close.iloc[-252:]
    rets = yr.pct_change(fill_method=None)
    mr = m.iloc[-252:].pct_change()
    out["vol"] = rets.std() * np.sqrt(252)
    out["beta"] = rets.apply(lambda s: s.cov(mr) / mr.var() if mr.var() > 0 else np.nan)
    dd = yr / yr.cummax() - 1
    out["worst_drop"] = dd.min()
    out["ulcer"] = np.sqrt((dd ** 2).mean())
    out.loc[yr.notna().sum() < 200, ["vol", "beta", "worst_drop", "ulcer"]] = np.nan
    return out


def graham_value(info_df: pd.DataFrame, bond_yield: float) -> pd.Series:
    """Graham value / price. ``bond_yield`` is the 10-year Treasury as a decimal."""
    g_ = lambda c: pd.to_numeric(info_df[c], errors="coerce") if c in info_df else pd.Series(np.nan, index=info_df.index)
    eps = g_("trailingEps")
    growth = (g_("earningsGrowth").fillna(0.0).clip(-0.2, 0.25) * 100).clip(lower=0)
    aaa = float(np.clip(bond_yield * 100 + 1.0, 2.0, 15.0))
    value = np.where(eps > 0, eps * (8.5 + 2 * growth) * 4.4 / aaa, 0.0)
    price = g_("currentPrice").fillna(g_("regularMarketPrice"))
    out = pd.Series(value, index=info_df.index) / price.where(price > 0)
    return out.where(eps.notna()).clip(0, 3)


def ratings(close: pd.DataFrame, sectors: pd.Series | None, info_df: pd.DataFrame | None = None,
            bond_yield: float = 0.042, market: pd.Series | None = None) -> pd.DataFrame:
    """RV, RT, RS, CI and VST (0-2, 1 = the sector's middle) for every column of ``close``."""
    pc = price_components(close, market)
    secs = sectors.reindex(pc.index) if sectors is not None else None
    parts = [1 - pc["vol"].rank(pct=True), 1 - pc["beta"].rank(pct=True), pc["worst_drop"].rank(pct=True)]
    out = pd.DataFrame(index=pc.index)
    if info_df is not None and not info_df.empty:
        inf = info_df.reindex(pc.index)
        out["RV_raw"] = graham_value(inf, bond_yield)
        n = lambda c: pd.to_numeric(inf[c], errors="coerce") if c in inf else pd.Series(np.nan, index=inf.index)
        dollar_vol = n("averageVolume") * close.ffill().iloc[-1]
        if dollar_vol.notna().any():
            parts.append(dollar_vol.rank(pct=True).fillna(0.5))
        eps = n("trailingEps")
        if eps.notna().any():
            parts.append(pd.Series(np.where(eps > 0, 0.75, np.where(eps.notna(), 0.0, 0.5)), index=pc.index))
    else:
        out["RV_raw"] = np.nan
    safety = pd.concat(parts, axis=1).mean(axis=1, skipna=True).where(pc["vol"].notna())
    out["RV"] = sector_rank(out["RV_raw"], secs)
    out["RT"] = sector_rank(pc["rt_raw"], secs)
    out["RS"] = sector_rank(safety, secs)
    out["CI"] = sector_rank(-pc["ulcer"], secs)
    out["VST"] = np.sqrt((out["RV"] ** 2 + out["RT"] ** 2 + out["RS"] ** 2) / 3)
    return out.join(pc)


def vst_list(rat: pd.DataFrame, fip: pd.Series | None = None, n: int = 20) -> pd.DataFrame:
    """Today's weekly core list: the ``n`` highest VSTs among stocks whose past
    year was a steady climb (FIP in the top half of the list)."""
    r = rat.dropna(subset=["VST"]).copy()
    r["VST rank"] = r["VST"].rank(ascending=False, method="first")
    if fip is not None:
        f = pd.to_numeric(fip.reindex(r.index), errors="coerce")
        r = r[f.rank(pct=True) >= 0.5]
    return r.sort_values("VST", ascending=False).head(n)


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
