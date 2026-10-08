"""Cross-sectional multi-factor stock ranking and factor backtest.

Replaces the old additive point system (which simultaneously rewarded
"RSI oversold" and "strong momentum") with the approach used by quant equity
desks: compute academically documented factors, winsorise, z-score them
*within sector* so a bank isn't compared to a software company on P/E, group
them into themes and combine into a composite rank.

Factors (with the literature they come from):
  Momentum   12-1 month return (Jegadeesh & Titman 1993) and frog-in-the-pan
             smoothness (Da, Gurun & Warachka 2014)
  Trend      price vs 200-day average, 50/200 alignment
  Low risk   low volatility / low beta (Frazzini & Pedersen 2014)
  Reversal   1-week and 1-month reversal (Lehmann 1990, Jegadeesh 1990)
  Earnings   last EPS surprise and run of beats (post-earnings drift, Bernard & Thomas 1989)
  Value      forward earnings yield, FCF yield, EBITDA/EV, dividend yield
  Quality    ROE, gross margin, profit margin, low leverage (Asness et al.)
  Growth     revenue & earnings growth
  Analysts   consensus upside to target, recommendation

Default weights come from a 2000-2026 test on point-in-time S&P 500 members
(see RESEARCH below): themes that pointed the wrong way in both halves of that
period (Low Risk, Analysts) start at zero but stay available as sliders.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PRICE_FACTORS = {
    "Momentum": {"mom_12_1": 1.0, "fip": 1.0},
    "Trend": {"trend_200": 1.0, "ma_align": 0.5},
    "Low Risk": {"low_vol": 1.0, "low_beta": 0.5},
    "Reversal": {"rev_1w": 1.0, "rev_1m": 1.0},
}
EARNINGS_FACTORS = {
    "Earnings": {"eps_surprise": 1.0, "beat_streak": 0.5},
}
FUNDAMENTAL_FACTORS = {
    "Value": {"earnings_yield": 1.0, "fcf_yield": 1.0, "ebitda_ev": 1.0, "div_yield": 0.5},
    "Quality": {"roe": 1.0, "gross_margin": 0.7, "profit_margin": 0.7, "low_leverage": 0.5},
    "Growth": {"revenue_growth": 1.0, "earnings_growth": 0.7},
    "Analysts": {"target_upside": 1.0, "rec_score": 0.7},
}
DEFAULT_THEME_WEIGHTS = {
    "Momentum": 0.20, "Trend": 0.05, "Low Risk": 0.0, "Reversal": 0.10, "Earnings": 0.20,
    "Value": 0.20, "Quality": 0.15, "Growth": 0.05, "Analysts": 0.0,
}
# Themes the replay can rebuild from history (prices, plus Yahoo's earnings dates when available).
REPLAYABLE = (*PRICE_FACTORS, *EARNINGS_FACTORS)


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
    # Frog-in-the-pan (Da, Gurun & Warachka): smooth, steady gains persist better than a few big jumps.
    w = rets.iloc[-252:-21] if n > 273 else rets.iloc[:-21]
    if len(w) > 60:
        f["fip"] = (w > 0).mean() - (w < 0).mean()
    f["low_vol"] = -vol
    f["rev_1w"] = -(p.iloc[-1] / p.iloc[-6] - 1)
    f["ret_1m"] = p.iloc[-1] / p.iloc[-22] - 1
    f["rev_1m"] = -f["ret_1m"]
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
    dy = g("dividendYield")
    # Yahoo has reported this both as a fraction and as a percent.
    f["div_yield"] = (dy.where(dy < 0.3, dy / 100)).fillna(0.0).clip(0, 0.15) if "dividendYield" in fund else np.nan
    return f


def _earnings_table(ed) -> pd.DataFrame:
    if not isinstance(ed, pd.DataFrame) or ed.empty or "Reported EPS" not in ed:
        return pd.DataFrame()
    ed = ed.copy()
    ed.index = pd.to_datetime(ed.index)
    if ed.index.tz is not None:
        ed.index = ed.index.tz_convert("America/New_York").tz_localize(None)
    ed = ed.dropna(subset=["Reported EPS"]).sort_index()
    ed = ed[~ed.index.normalize().duplicated(keep="last")]
    if "Surprise(%)" not in ed or ed["Surprise(%)"].isna().all():
        est = pd.to_numeric(ed.get("EPS Estimate"), errors="coerce")
        ed["Surprise(%)"] = (ed["Reported EPS"] - est) / est.abs() * 100
    return ed


def earnings_factor_frame(histories: dict, asof: pd.Timestamp | None = None, stale_days: int = 120) -> pd.DataFrame:
    """Earnings-surprise exposures from Yahoo's earnings dates, using only reports public by ``asof``.

    eps_surprise: the last report's surprise in percent (capped at +/-100%), blank once older than ``stale_days``.
    beat_streak: how many reports in a row beat the estimate (up to 8).
    eps_yoy: last quarter's EPS vs the same quarter a year earlier (shown, not scored: past growth didn't predict returns)."""
    rows = {}
    for sym, ed in (histories or {}).items():
        t = _earnings_table(ed)
        if asof is not None and not t.empty:
            t = t[t.index.normalize() < pd.Timestamp(asof).normalize()]
        if t.empty:
            rows[sym] = {"eps_surprise": np.nan, "beat_streak": np.nan, "eps_yoy": np.nan}
            continue
        sur = pd.to_numeric(t["Surprise(%)"], errors="coerce")
        ref = pd.Timestamp(asof) if asof is not None else pd.Timestamp.now()
        fresh = (ref - t.index[-1]).days <= stale_days
        streak = 0
        for v in sur.iloc[::-1].head(8):
            if not np.isfinite(v) or v <= 0:
                break
            streak += 1
        last = sur.iloc[-1]
        eps = pd.to_numeric(t["Reported EPS"], errors="coerce")
        yoy = np.nan
        if len(eps) >= 5 and abs(eps.iloc[-5]) > 0.01 and (t.index[-1] - t.index[-5]).days < 420:
            yoy = float(np.clip((eps.iloc[-1] - eps.iloc[-5]) / abs(eps.iloc[-5]), -2, 5))
        rows[sym] = {"eps_surprise": float(np.clip(last, -100, 100)) if fresh and np.isfinite(last) else np.nan,
                     "beat_streak": float(streak), "eps_yoy": yoy if fresh else np.nan}
    return pd.DataFrame.from_dict(rows, orient="index", columns=["eps_surprise", "beat_streak", "eps_yoy"])


def composite_scores(price_f: pd.DataFrame, fund_f: pd.DataFrame | None = None,
                     sectors: pd.Series | None = None, theme_weights: dict | None = None,
                     earn_f: pd.DataFrame | None = None) -> pd.DataFrame:
    """Combine factor exposures into theme z-scores and a composite score."""
    tw = dict(DEFAULT_THEME_WEIGHTS if theme_weights is None else theme_weights)
    frames = [price_f]
    groups = dict(PRICE_FACTORS)
    if earn_f is not None and not earn_f.empty:
        frames.append(earn_f.reindex(price_f.index))
        groups.update(EARNINGS_FACTORS)
    if fund_f is not None and not fund_f.empty:
        frames.append(fund_f.reindex(price_f.index))
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


THEME_WORDS = {
    "Momentum": ("Strong momentum", "Weak momentum"), "Trend": ("Uptrend", "Downtrend"),
    "Low Risk": ("Low volatility", "High volatility"), "Reversal": ("Recent dip", "Short-term stretched"),
    "Earnings": ("Beating estimates", "Missing estimates"),
    "Value": ("Cheap vs sector", "Pricey vs sector"), "Quality": ("High quality", "Low quality"),
    "Growth": ("Fast growth", "Slow growth"), "Analysts": ("Analysts bullish", "Analysts cautious"),
}
THEME_HELP = {
    "Momentum": "12-month return excluding the last month, and how steadily it climbed (more up days than down days). "
                "In the 2000-26 S&P 500 test it was close to neutral: it helped after 2013 and hurt in 2002-12.",
    "Trend": "Price vs its 200-day average and whether the 50-day is above the 200-day. Neutral over 2000-26, so a small weight.",
    "Low Risk": "Low volatility and low beta. Off by default: in the 2000-26 S&P 500 test the calmest stocks lagged the "
                "average stock in both halves (about 1.4% a year). Turn it up if you want a calmer list, not a better one.",
    "Reversal": "Stocks that fell over the last week and month tend to bounce a little. One of the steadier signals in the "
                "test, though the effect is small.",
    "Earnings": "The last report's EPS surprise and how many reports in a row beat the estimate. Stocks that beat tend to "
                "keep drifting the same way for a couple of months. In the test it pointed the right way in 56% of months "
                "after 2013.",
    "Value": "Forward earnings yield, free-cash-flow yield, EBITDA/EV and dividend yield, compared with the stock's own "
             "sector. The most consistent theme in the test: cheap stocks beat the average by about 2% a year in 2002-12 "
             "and 1.5% after 2013 (using earnings and dividend yield, the parts with history).",
    "Quality": "Return on equity, gross and net margins and low debt, compared with the stock's own sector. Its closest "
               "testable cousin, steady earnings growth, helped in both halves.",
    "Growth": "Revenue and earnings growth. Fast past growth did not predict returns in the test (it is usually priced in), "
              "so a small weight.",
    "Analysts": "Upside to the average price target and the consensus rating. Off by default: tested on 2012-26 rating "
                "and target history, a big gap to the target came before big losers slightly more often than big "
                "winners, and the stocks analysts liked most did no better than the rest.",
}

# 2000-2026 test on point-in-time S&P 500 members (Yahoo prices for 710 of 1,097 past and present members, earnings
# dates from 2002, analyst history from 2012): every month, buy the top 20% by score, hold a month, compare with the
# equal-weight average of the members. "Right direction" = share of months where higher scores did better
# (positive rank correlation with next month's return).
RESEARCH = pd.DataFrame([
    {"Ranking": "Old default weights", "Period": "2002-2012", "Top 20% vs average": -0.006, "Right direction": 0.50},
    {"Ranking": "Old default weights", "Period": "2013-2026", "Top 20% vs average": -0.007, "Right direction": 0.53},
    {"Ranking": "New default weights", "Period": "2002-2012", "Top 20% vs average": -0.004, "Right direction": 0.60},
    {"Ranking": "New default weights", "Period": "2013-2026", "Top 20% vs average": 0.009, "Right direction": 0.60},
    {"Ranking": "Machine-learning model, all 50 signals", "Period": "2007-2026", "Top 20% vs average": -0.002,
     "Right direction": 0.48},
])


def explain(row: pd.Series, top: int = 3, weights: dict | None = None) -> tuple[list[str], list[str]]:
    """Strongest positive and negative drivers among the themes that count toward the score, in plain words."""
    w = DEFAULT_THEME_WEIGHTS if weights is None else weights
    themes = [t for t in DEFAULT_THEME_WEIGHTS if w.get(t, 0) > 0 and t in row.index and pd.notna(row[t])]
    s = row[themes].astype(float).sort_values()
    pos = [THEME_WORDS[t][0] for t, v in s[::-1].items() if v > 0.3][:top]
    neg = [THEME_WORDS[t][1] for t, v in s.items() if v < -0.3][:top]
    return pos, neg


# ---------------------------------------------------------------------------
# Backtest of the price-factor composite
# ---------------------------------------------------------------------------


def backtest_price_composite(prices: pd.DataFrame, rebalance: int = 21, quantile: float = 0.2,
                             cost_bps: float = 10.0, theme_weights: dict | None = None,
                             earnings: dict | None = None) -> dict:
    """Monthly-rebalanced long top-quantile portfolio of the price (and, given ``earnings``, earnings) composite.

    Uses only information available at each rebalance date: ``earnings`` maps symbols to Yahoo earnings-date
    tables, and only reports dated before each rebalance count. Reports the
    strategy vs an equal-weight universe benchmark, the rank information
    coefficient (Spearman IC) per period, and turnover-based trading costs.
    Caveat: uses today's index constituents (survivorship bias).
    """
    keep = REPLAYABLE if earnings else tuple(PRICE_FACTORS)
    tw = {k: v for k, v in (DEFAULT_THEME_WEIGHTS if theme_weights is None else theme_weights).items() if k in keep}
    if not any(v > 0 for v in tw.values()):
        raise ValueError("Give at least one of the price or earnings themes some weight to replay the ranking.")
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
        ef = earnings_factor_frame(earnings, asof=prices.index[t]) if earnings else None
        sc = composite_scores(pf, None, None, tw, earn_f=ef)["Composite"].dropna()
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
        "beat_rate": float(np.mean([a.add(1).prod() > b_.add(1).prod() for a, b_ in zip(strat, bench)])),
        "themes": sorted(k for k, v in tw.items() if v > 0),
        "long_short_spread": float(np.mean(spreads)),
    }
