"""Cross-sectional multi-factor stock ranking and factor backtest.

Replaces the old additive point system (which simultaneously rewarded
"RSI oversold" and "strong momentum") with the approach used by quant equity
desks: compute academically documented factors, winsorise, z-score them
*within sector* so a bank isn't compared to a software company on P/E, group
them into themes and combine into a composite rank.

Factors (with the literature they come from):
  Momentum   12-1 month return (Jegadeesh & Titman 1993), residual momentum
             (Blitz, Huij & Martens 2011), 52-week-high proximity (George &
             Hwang 2004)
  Trend      price vs 200-day average, 50/200 alignment
  Low risk   low volatility / low beta (Frazzini & Pedersen 2014)
  Reversal   1-week reversal (Lehmann 1990), small weight
  Value      forward earnings yield, FCF yield, EBITDA/EV
  Quality    ROE, gross margin, profit margin, low leverage (Asness et al.)
  Growth     revenue & earnings growth
  Analysts   consensus upside to target, recommendation
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PRICE_FACTORS = {
    "Momentum": {"mom_12_1": 1.0, "resid_mom": 1.0, "high_52w": 0.5},
    "Trend": {"trend_200": 1.0, "ma_align": 0.5},
    "Low Risk": {"low_vol": 1.0, "low_beta": 0.5},
    "Reversal": {"rev_1w": 1.0},
}
FUNDAMENTAL_FACTORS = {
    "Value": {"earnings_yield": 1.0, "fcf_yield": 1.0, "ebitda_ev": 1.0},
    "Quality": {"roe": 1.0, "gross_margin": 0.7, "profit_margin": 0.7, "low_leverage": 0.5},
    "Growth": {"revenue_growth": 1.0, "earnings_growth": 0.7},
    "Analysts": {"target_upside": 1.0, "rec_score": 0.7},
}
DEFAULT_THEME_WEIGHTS = {
    "Momentum": 0.25, "Trend": 0.10, "Low Risk": 0.10, "Reversal": 0.05,
    "Value": 0.20, "Quality": 0.15, "Growth": 0.10, "Analysts": 0.05,
}


def winsorize(s: pd.Series, lo: float = 0.025, hi: float = 0.975) -> pd.Series:
    if s.notna().sum() < 5:
        return s
    return s.clip(s.quantile(lo), s.quantile(hi))


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and sd > 0 else s * 0


def sector_neutral_z(s: pd.Series, sectors: pd.Series | None, min_group: int = 5) -> pd.Series:
    s = winsorize(s)
    if sectors is None:
        return zscore(s)
    out = zscore(s)  # global fallback for small sectors
    sec = sectors.reindex(s.index)
    for name, idx in sec.groupby(sec).groups.items():
        grp = s.loc[idx]
        if grp.notna().sum() >= min_group:
            out.loc[idx] = zscore(grp)
    return out


def price_factor_frame(prices: pd.DataFrame, asof: int | None = None) -> pd.DataFrame:
    """Price-based factor exposures for each ticker at row ``asof`` (default last)."""
    p = prices if asof is None else prices.iloc[: asof + 1]
    p = p.dropna(axis=1, thresh=min(len(p), 260) - 10) if len(p) > 260 else p.dropna(axis=1, thresh=int(len(p) * 0.8))
    rets = p.pct_change(fill_method=None)
    last = p.iloc[-1]
    f = pd.DataFrame(index=p.columns)
    n = len(p)
    if n > 252:
        f["mom_12_1"] = p.iloc[-22] / p.iloc[-253] - 1
    elif n > 127:
        f["mom_12_1"] = p.iloc[-22] / p.iloc[0] - 1
    f["high_52w"] = last / p.iloc[-252:].max()
    sma200 = p.iloc[-200:].mean()
    sma50 = p.iloc[-50:].mean()
    f["trend_200"] = last / sma200 - 1
    f["ma_align"] = np.sign(sma50 - sma200)
    vol = rets.iloc[-63:].std() * np.sqrt(252)
    f["volatility"] = vol
    f["low_vol"] = -vol
    f["rev_1w"] = -(p.iloc[-1] / p.iloc[-6] - 1)
    f["ret_1m"] = p.iloc[-1] / p.iloc[-22] - 1
    f["ret_1w"] = p.iloc[-1] / p.iloc[-6] - 1

    # Market = equal-weighted universe. Beta and residual momentum.
    window = rets.iloc[-252:-21] if n > 273 else rets.iloc[:-21]
    mkt = window.mean(axis=1)
    mv = mkt.var()
    if mv > 0 and len(window) > 60:
        wc = window.sub(window.mean())
        mc = mkt - mkt.mean()
        beta = wc.mul(mc, axis=0).sum() / (mc**2).sum()
        resid = window - np.outer(mkt, beta)
        resid = pd.DataFrame(resid, index=window.index, columns=window.columns)
        f["beta"] = beta
        f["low_beta"] = -beta
        f["resid_mom"] = resid.mean() / resid.std()
    return f


def fundamental_factor_frame(fund: pd.DataFrame) -> pd.DataFrame:
    """Map raw fundamentals (from yfinance ``info``) to factor exposures."""
    g = lambda c: pd.to_numeric(fund.get(c), errors="coerce") if c in fund else pd.Series(np.nan, index=fund.index)
    f = pd.DataFrame(index=fund.index)
    fpe = g("forwardPE").where(lambda x: x > 0)
    tpe = g("trailingPE").where(lambda x: x > 0)
    f["earnings_yield"] = (1 / fpe).fillna(1 / tpe)
    mcap = g("marketCap")
    f["fcf_yield"] = g("freeCashflow") / mcap
    f["ebitda_ev"] = 1 / g("enterpriseToEbitda").where(lambda x: x > 0)
    f["roe"] = g("returnOnEquity").clip(-1, 1.5)
    f["gross_margin"] = g("grossMargins")
    f["profit_margin"] = g("profitMargins")
    f["low_leverage"] = -g("debtToEquity") / 100
    f["revenue_growth"] = g("revenueGrowth").clip(-0.5, 2)
    f["earnings_growth"] = g("earningsGrowth").clip(-1, 3)
    price = g("currentPrice").fillna(g("regularMarketPrice"))
    f["target_upside"] = (g("targetMeanPrice") / price - 1).clip(-0.6, 1.5)
    f["rec_score"] = -(g("recommendationMean") - 3)  # 1=strong buy ... 5=sell
    return f


def composite_scores(price_f: pd.DataFrame, fund_f: pd.DataFrame | None = None,
                     sectors: pd.Series | None = None, theme_weights: dict | None = None) -> pd.DataFrame:
    """Combine factor exposures into theme z-scores and a composite score."""
    tw = dict(theme_weights or DEFAULT_THEME_WEIGHTS)
    frames = [price_f]
    groups = dict(PRICE_FACTORS)
    if fund_f is not None and not fund_f.empty:
        frames.append(fund_f)
        groups.update(FUNDAMENTAL_FACTORS)
    raw = pd.concat(frames, axis=1)
    raw = raw.loc[:, ~raw.columns.duplicated()]
    out = pd.DataFrame(index=raw.index)
    for theme, members in groups.items():
        cols = [c for c in members if c in raw.columns and raw[c].notna().sum() >= 5]
        if not cols:
            continue
        zs = pd.concat({c: sector_neutral_z(raw[c], sectors) * members[c] for c in cols}, axis=1)
        wsum = pd.Series({c: members[c] for c in cols})
        # Average available members, re-weighting when some are missing.
        denom = zs.notna().mul(wsum, axis=1).sum(axis=1).replace(0, np.nan)
        out[theme] = zs.sum(axis=1, min_count=1) / denom
    themes = [t for t in out.columns if tw.get(t, 0) > 0]
    w = pd.Series({t: tw[t] for t in themes})
    avail = out[themes].notna().mul(w, axis=1).sum(axis=1).replace(0, np.nan)
    out["Composite"] = out[themes].fillna(0).mul(w, axis=1).sum(axis=1) / avail
    # Require at least half of the theme weight to be present.
    out.loc[avail < w.sum() * 0.5, "Composite"] = np.nan
    out["Percentile"] = out["Composite"].rank(pct=True) * 100
    return out.join(raw, how="left")


def explain(row: pd.Series, top: int = 3) -> tuple[list[str], list[str]]:
    """Strongest positive and negative theme drivers for a stock."""
    themes = [t for t in DEFAULT_THEME_WEIGHTS if t in row.index and pd.notna(row[t])]
    s = row[themes].astype(float).sort_values()
    pos = [f"{t} ({v:+.1f}σ)" for t, v in s[::-1].items() if v > 0.3][:top]
    neg = [f"{t} ({v:+.1f}σ)" for t, v in s.items() if v < -0.3][:top]
    return pos, neg


# ---------------------------------------------------------------------------
# Backtest of the price-factor composite
# ---------------------------------------------------------------------------


def backtest_price_composite(prices: pd.DataFrame, rebalance: int = 21, quantile: float = 0.2,
                             cost_bps: float = 10.0, theme_weights: dict | None = None) -> dict:
    """Monthly-rebalanced long top-quantile portfolio of the price composite.

    Uses only information available at each rebalance date. Reports the
    strategy vs an equal-weight universe benchmark, the rank information
    coefficient (Spearman IC) per period, and turnover-based trading costs.
    Caveat: uses today's index constituents (survivorship bias).
    """
    tw = {k: v for k, v in (theme_weights or DEFAULT_THEME_WEIGHTS).items() if k in PRICE_FACTORS}
    prices = prices.dropna(axis=1, thresh=int(len(prices) * 0.9)).ffill()
    rets = prices.pct_change(fill_method=None)
    start = 273
    if len(prices) < start + rebalance * 3:
        raise ValueError("Need roughly 16+ months of prices for a factor backtest.")
    strat, bench, ics, dates, spreads = [], [], [], [], []
    prev_w = pd.Series(dtype=float)
    turnover = []
    for t in range(start, len(prices) - 1, rebalance):
        pf = price_factor_frame(prices, asof=t)
        sc = composite_scores(pf, None, None, tw)["Composite"].dropna()
        if len(sc) < 10:
            continue
        end = min(t + rebalance, len(prices) - 1)
        fwd = prices.iloc[end] / prices.iloc[t] - 1
        k = max(1, int(len(sc) * quantile))
        top = sc.nlargest(k).index
        bot = sc.nsmallest(k).index
        w = pd.Series(1.0 / k, index=top)
        to = w.subtract(prev_w, fill_value=0).abs().sum() / 2 if len(prev_w) else 1.0
        turnover.append(to)
        prev_w = w
        period = rets.iloc[t + 1: end + 1]
        sp = period[top].mean(axis=1)
        sp.iloc[0] -= to * 2 * cost_bps / 1e4
        strat.append(sp)
        bench.append(period.mean(axis=1))
        common = sc.index.intersection(fwd.dropna().index)
        ics.append(sc[common].rank().corr(fwd[common].rank()))
        spreads.append(fwd[top].mean() - fwd[bot].mean())
        dates.append(prices.index[t])
    s = pd.concat(strat)
    b = pd.concat(bench)
    ic = pd.Series(ics, index=dates)
    return {
        "strategy": s, "benchmark": b, "ic": ic,
        "ic_mean": float(ic.mean()), "ic_t": float(ic.mean() / ic.std() * np.sqrt(len(ic))) if ic.std() > 0 else np.nan,
        "hit_rate": float((ic > 0).mean()), "avg_turnover": float(np.mean(turnover)),
        "long_short_spread": float(np.mean(spreads)),
    }
