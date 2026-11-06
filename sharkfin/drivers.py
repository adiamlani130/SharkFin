"""What moves a stock over each timeframe, in plain words, with this stock's own readings.

Different things matter at different horizons. SharkFin's Nov 2026 studies (``growth_lab.horizon_signals`` and
``growth_lab.earnings_horizons``) plus the best-known research behind them:

* Price patterns barely sort S&P 500 stocks at any horizon. Across 2006-26 every one we tested (last week's or
  last month's move, 6- and 12-month momentum, closeness to the 52-week high, the 200-day average, low volatility)
  had a rank correlation with the next 1 week to 12 months of 0.05 or less, and most flipped sign between 2006-15
  and 2016-26. So the page shows them as context, not as drivers.
* Earnings reports are the biggest single events. A stock's report day is typically its largest move of the
  quarter, so over a week or a month the first question is whether a report is due.
* After a report, a big beat keeps paying for months (post-earnings drift, Bernard & Thomas 1989). In SharkFin's
  sample (17,800 reports from 195 S&P 500 stocks, 2007-26, bought at the open after the reaction day), the top
  fifth of EPS surprises beat the bottom fifth vs SPY by 0.6 points over a month, 1.4 over 3 months, 2.7 over 6
  and 7.4 over 12, on average. Most of that came from a few big winners and from 2021-26: the typical
  (median) stock in the top fifth was only about a point ahead at 6 months. The size of the next-day jump
  mattered less than the surprise itself.
* Over 3-12 months what analysts expect, and how that changes, matters most: upward estimate revisions lead
  (Chan, Jegadeesh & Lakonishok 1996), and expected growth sets where the price can go.
* Over a year or more, what you pay (valuation) and how good the business is (profitability, Novy-Marx 2013)
  matter most, with a market-wide fear spike as the best entry: after VIX closed above 30, QQQ was higher six
  months later 78% of the time (growth_lab.crash_events).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HORIZONS = {"1 week": 5, "1 month": 21, "3 months": 63, "6 months": 126, "1 year": 252}

# What matters most at each horizon, in order, and a one-line summary of why.
FOCUS = {
    5: ("A week is mostly noise and news. Unless a report is due, nothing on this list predicts much; the range "
        "above is the honest answer.", ["earnings_due", "news", "market", "last_move"]),
    21: ("Over a month the next report and the reaction to the last one matter most, then the news flow.",
         ["earnings_due", "drift", "news", "revisions", "market"]),
    63: ("Over three months, the next report and whether analysts are raising or cutting their estimates lead.",
         ["earnings_due", "revisions", "drift", "rating", "market"]),
    126: ("Over six months, expected growth, estimate changes and the last earnings surprise lead, with the "
          "market's mood as the backdrop.", ["revisions", "growth", "drift", "target", "fear", "trend"]),
    252: ("Over a year, what you pay for the growth and how good the business is matter most. A fear spike in the "
          "market has been the best time to buy.", ["valuation", "growth", "quality", "target", "fear"]),
}


def _num(x) -> float:
    try:
        v = float(x)
        return v if np.isfinite(v) else np.nan
    except (TypeError, ValueError):
        return np.nan


def _naive(ed: pd.DataFrame) -> pd.DataFrame:
    ed = ed.copy()
    ed.index = pd.to_datetime(ed.index)
    if ed.index.tz is not None:
        ed.index = ed.index.tz_convert("America/New_York").tz_localize(None)
    return ed.sort_index()


def earnings_record(ed: pd.DataFrame | None, close: pd.Series, market: pd.Series | None = None,
                    now: pd.Timestamp | None = None) -> dict:
    """Next report date, the typical report-day move (median size of the last 8, vs the market when given), the
    last four surprises and reactions, and the most recent report's surprise and reaction."""
    out = {"next": None, "days_to_next": None, "typical_move": np.nan, "history": pd.DataFrame(),
           "last_surprise": np.nan, "last_reaction": np.nan, "days_since": None, "beats": None}
    if not isinstance(ed, pd.DataFrame) or ed.empty or "Reported EPS" not in ed:
        return out
    ed = _naive(ed)
    now = now or pd.Timestamp.now()
    up = ed[ed["Reported EPS"].isna() & (ed.index >= now.normalize())]
    if len(up):
        out["next"] = up.index[0]
        out["days_to_next"] = int((up.index[0].normalize() - now.normalize()).days)
    c = close.dropna()
    m = market.reindex(c.index).ffill() if market is not None and len(market) else None
    rows = []
    for when, r in ed.dropna(subset=["Reported EPS"]).iterrows():
        i = int(c.index.searchsorted(when.normalize() + pd.Timedelta(days=1))) if when.hour >= 9 \
            else int(c.index.searchsorted(when.normalize()))
        if i < 1 or i >= len(c):
            continue
        move = c.iloc[i] / c.iloc[i - 1] - 1
        if m is not None and np.isfinite(m.iloc[i]) and np.isfinite(m.iloc[i - 1]):
            move -= m.iloc[i] / m.iloc[i - 1] - 1
        sur = _num(r.get("Surprise(%)"))
        rows.append({"Reported": when, "EPS estimate": _num(r.get("EPS Estimate")),
                     "Reported EPS": _num(r.get("Reported EPS")),
                     "Surprise": sur / 100 if np.isfinite(sur) else np.nan, "Next-day move": float(move)})
    if not rows:
        return out
    h = pd.DataFrame(rows).sort_values("Reported", ascending=False)
    out["history"] = h.head(8).reset_index(drop=True)
    out["typical_move"] = float(h["Next-day move"].head(8).abs().median())
    out["last_surprise"] = float(h["Surprise"].iloc[0])
    out["last_reaction"] = float(h["Next-day move"].iloc[0])
    out["days_since"] = int((now.normalize() - h["Reported"].iloc[0].normalize()).days)
    tail = h.head(4).dropna(subset=["EPS estimate"])
    out["beats"] = int((tail["Reported EPS"] >= tail["EPS estimate"]).sum()) if len(tail) else None
    return out


def estimate_trend(eps_trend: pd.DataFrame | None, eps_revisions: pd.DataFrame | None) -> dict:
    """How next year's EPS estimate changed over 30 and 90 days, and the net share of upward revisions in 30 days."""
    out = {"chg30": np.nan, "chg90": np.nan, "balance": np.nan, "row": None}
    if isinstance(eps_trend, pd.DataFrame) and not eps_trend.empty and "current" in eps_trend:
        for row in ("+1y", "0y"):
            if row in eps_trend.index:
                cur = _num(eps_trend.at[row, "current"])
                for k, col in (("chg30", "30daysAgo"), ("chg90", "90daysAgo")):
                    old = _num(eps_trend.at[row, col]) if col in eps_trend else np.nan
                    if np.isfinite(cur) and np.isfinite(old) and abs(old) > 1e-9:
                        out[k] = cur / abs(old) - np.sign(old)
                out["row"] = row
                break
    if isinstance(eps_revisions, pd.DataFrame) and not eps_revisions.empty:
        u = pd.to_numeric(eps_revisions.get("upLast30days"), errors="coerce").sum()
        d = pd.to_numeric(eps_revisions.get("downLast30days"), errors="coerce").sum()
        if u + d > 0:
            out["balance"] = float((u - d) / (u + d))
    return out


def _tone(x: float, good: float, bad: float) -> str:
    if not np.isfinite(x):
        return "neu"
    if good > bad:
        return "pos" if x >= good else "neg" if x <= bad else "neu"
    return "pos" if x <= good else "neg" if x >= bad else "neu"


def drivers(horizon: int, *, info: dict, earnings: dict, estimates: dict, news: dict, close: pd.Series,
            vix: float = np.nan, spy_week: float = np.nan, growth: float = np.nan) -> dict:
    """{"summary", "items"}: the drivers that matter most over ``horizon`` trading days, in order, each
    {"name", "reading", "tone", "why"}. Drivers with no data are left out."""
    summary, keys = FOCUS[min(FOCUS, key=lambda k: abs(k - horizon))]
    c = close.dropna()
    price = float(c.iloc[-1]) if len(c) else np.nan
    cal_days = horizon * 365 / 252
    items = []

    def add(name, reading, tone, why):
        items.append({"name": name, "reading": reading, "tone": tone, "why": why})

    for k in keys:
        if k == "earnings_due":
            d, mv = earnings.get("days_to_next"), earnings.get("typical_move", np.nan)
            typical = f" Its typical report-day move is {mv:.1%}." if np.isfinite(mv) else ""
            if d is not None and d <= cal_days:
                add("Earnings report", f"Due {earnings['next']:%b %d}, in {d} days", "neu",
                    "The biggest scheduled event in this window." + typical)
            elif d is not None:
                add("Earnings report", f"Next one {earnings['next']:%b %d}, after this window", "neu",
                    "No report inside the window, so one big source of surprise is off the table." + typical)
        elif k == "drift":
            s, r, since = earnings.get("last_surprise"), earnings.get("last_reaction"), earnings.get("days_since")
            if since is not None and (np.isfinite(s) or np.isfinite(r)):
                fresh = since <= 100
                sur = f"EPS {s:+.0%} vs estimates" if np.isfinite(s) else "Surprise unknown"
                rx = f", stock {r:+.1%} vs the market next day" if np.isfinite(r) else ""
                tone = (_tone(s, 0.15, 0.0) if np.isfinite(s) else _tone(r, 0.03, -0.03)) if fresh else "neu"
                why = ("In SharkFin's study of 17,800 reports, big beats (the top fifth, roughly +15% or more) beat "
                       "the weakest fifth by 1.4 points over 3 months and 2.7 over 6, on average. Mostly a few big "
                       "winners, so it tilts the odds a little rather than calling the move.")
                if not fresh:
                    why = f"That report is {since} days old; the next one will matter more."
                add("Last earnings surprise", f"{sur}{rx}, {since} days ago", tone, why)
        elif k == "news":
            if news.get("n"):
                add("News tone", f"{news['label']} ({news['positive']} positive, {news['negative']} negative of "
                    f"{news['n']} stories)", _tone(news.get("score", 0), 0.1, -0.1),
                    "Headlines move prices for days. Lasting moves need the news to change earnings.")
        elif k == "market":
            if np.isfinite(vix):
                mood = "calm" if vix < 17 else "nervous" if vix < 25 else "fearful"
                wk = f", S&P 500 {spy_week:+.1%} this week" if np.isfinite(spy_week) else ""
                add("Market mood", f"VIX {vix:.1f}, {mood}{wk}", _tone(vix, 17, 25),
                    "Most stocks move with the market over short stretches; high VIX means wider swings both ways.")
        elif k == "last_move":
            if len(c) > 6:
                r5 = c.iloc[-1] / c.iloc[-6] - 1
                add("Last week's move", f"{r5:+.1%}", "neu",
                    "Context only: in SharkFin's 2006-26 test last week's move told you almost nothing about next "
                    "week's.")
        elif k == "revisions":
            c30, c90, bal = estimates.get("chg30"), estimates.get("chg90"), estimates.get("balance")
            chg = c90 if horizon >= 100 and np.isfinite(c90) else c30
            span = "90" if chg is c90 and np.isfinite(c90) else "30"
            parts = []
            if np.isfinite(chg):
                parts.append(f"next year's EPS estimate {chg:+.1%} in {span} days")
            if np.isfinite(bal):
                parts.append(f"{bal:+.0%} net upward revisions")
            if parts:
                x = chg if np.isfinite(chg) else bal / 10
                add("Analyst estimates", ", ".join(parts).capitalize(), _tone(x, 0.01, -0.01),
                    "Rising estimates tend to lead the price over the next few months.")
        elif k == "rating":
            rm, n = _num(info.get("recommendationMean")), _num(info.get("numberOfAnalystOpinions"))
            if np.isfinite(rm):
                word = info.get("recommendationKey", "").replace("_", " ") or ("buy" if rm < 2.5 else "hold")
                add("Analyst rating", f"{word.title()} ({rm:.1f} on a 1-5 scale" +
                    (f", {n:.0f} analysts)" if np.isfinite(n) else ")"), _tone(rm, 2.0, 3.0),
                    "Upgrades and downgrades move a stock for days to weeks. The level matters less: most stocks "
                    "are rated buy.")
        elif k == "target":
            t = _num(info.get("targetMeanPrice"))
            if np.isfinite(t) and np.isfinite(price):
                add("Analyst target", f"${t:,.0f}, {t / price - 1:+.0%} from here", _tone(t / price - 1, 0.15, 0.0),
                    "A 12-month view. Targets tend to run high, so treat 10-15% upside as about neutral.")
        elif k == "growth":
            g = growth if np.isfinite(growth) else _num(info.get("earningsGrowth"))
            rg = _num(info.get("revenueGrowth"))
            if np.isfinite(g) or np.isfinite(rg):
                txt = ", ".join(x for x in (f"EPS {g:+.0%} expected next year" if np.isfinite(g) else "",
                                            f"sales {rg:+.0%} last quarter" if np.isfinite(rg) else "") if x)
                add("Growth", txt, _tone(g if np.isfinite(g) else rg, 0.15, 0.0),
                    "Over months, prices follow earnings. Faster expected growth has more room to surprise.")
        elif k == "trend":
            if len(c) >= 200:
                gap = price / c.rolling(200).mean().iloc[-1] - 1
                add("Long-term trend", f"{gap:+.0%} vs the 200-day average", _tone(gap, 0.0, -0.05),
                    "Context more than a driver: in SharkFin's test being above the 200-day barely changed the "
                    "next 6 months on average, but most big crashes happened under it.")
        elif k == "fear":
            if np.isfinite(vix):
                add("Market fear", f"VIX {vix:.1f}", "pos" if vix >= 30 else "neu",
                    "After VIX closed above 30, QQQ was higher six months later 78% of the time (up 13% on average, "
                    "vs 6.7% on any day). Fear is usually the better time to buy, not the worse." if vix >= 25 else
                    "No fear spike now. After VIX closed above 30 QQQ was higher six months later 78% of the time.")
        elif k == "valuation":
            fpe, peg = _num(info.get("forwardPE")), _num(info.get("trailingPegRatio", info.get("pegRatio")))
            g = growth if np.isfinite(growth) else _num(info.get("earningsGrowth"))
            if not np.isfinite(peg) and np.isfinite(fpe) and np.isfinite(g) and g > 0:
                peg = fpe / (g * 100)
            if np.isfinite(fpe):
                txt = f"{fpe:.0f}x next year's earnings" + (f", PEG {peg:.1f}" if np.isfinite(peg) else "")
                add("Valuation", txt, _tone(peg, 1.2, 2.5) if np.isfinite(peg) else _tone(fpe, 18, 35),
                    "What you pay matters most over years: a high price for the growth leaves less room. PEG "
                    "(P/E over growth) under about 1.5 is reasonable for a growth stock.")
        elif k == "quality":
            roe, pm = _num(info.get("returnOnEquity")), _num(info.get("profitMargins"))
            if np.isfinite(roe) or np.isfinite(pm):
                txt = ", ".join(x for x in (f"return on equity {roe:.0%}" if np.isfinite(roe) else "",
                                            f"profit margin {pm:.0%}" if np.isfinite(pm) else "") if x)
                add("Business quality", txt.capitalize(), _tone(roe if np.isfinite(roe) else pm, 0.15, 0.05),
                    "Profitable businesses have beaten unprofitable ones over the long run, and hold up better in "
                    "selloffs.")
    return {"summary": summary, "items": items}
