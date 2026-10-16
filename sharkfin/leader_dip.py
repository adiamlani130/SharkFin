"""Leader Dip Plus 7: SharkFin's swing system (revamped Oct 2026).

Buy a short, sharp dip in one of the market's strongest stocks while the market itself is healthy, take
profits into the bounce, and keep the rest of the money working in SPY.

  Signal, at the close: the 2-day RSI is below 10, the stock closes above its 200-day average, its 6-month
  gain is in the top 30% of the S&P 500, and at least one "quality point" says the dip is a real flush:
    * a deep dip: the close is 2.5+ ATRs under its 10-day high
    * off the high: the close is more than 10% under its 52-week high
    * a sector-wide dip: the stock's sector ETF fell 2%+ over 3 days
    * fear: VIX closed above 20
  New trades are only placed while SPY closes above its 200-day average, or during a panic (VIX above 25).
  Entry, the next day: a limit order 3% under the signal close. It fills only if the day's low reaches the
  limit, at the open when the stock opens below it.
  Exit: a profit target at the signal close + 1.5 ATR (sell limit, good until it fills), or at the next open
  after the 2-day RSI closes above 70, after a close under the 200-day average, or after 10 trading days.
  There is no stop loss.
  Portfolio: 7 equal slots, biggest 6-month gainers first. Money not in trades sits in SPY while SPY closed
  above its 200-day the day before, and in T-bills otherwise.

SharkFin's Oct 2026 research (point-in-time S&P 500 members, 0.1% cost per side), settings picked on 2013-20
and graded on Oct 2021 - Oct 2026: 33.1% a year, Sharpe 1.40 (after T-bills), worst drop 18%, 64% of trades
won, +1.7% a trade. SPY made 13.9% a year with a 25% worst drop. With slightly worse fills it made 28.7% a
year, so 20-28% a year is the realistic plan.

The original rules ("Classic": no quality points, no target or 200-day exit, SPY-only switch, 10 slots, cash
in T-bills) stay available for comparison. Everything is computed from data up to the signal close, and
fills only use later bars, so there is no look-ahead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import indicators as ind
from . import swing_engine, walkforward

RSI_DAYS = 2
BUY_BELOW = 10.0
SELL_ABOVE = 70.0
TREND_DAYS = 200
STRENGTH_DAYS = 126
STRENGTH_MIN = 0.70
LIMIT = 0.97
MAX_DAYS = 10
COST_BPS = 10.0

# Plus
SLOTS = 7
TARGET_ATR = 1.5
ATR_DAYS = 14
PANIC_VIX = 25.0
DEEP_DIP_ATR = 2.5
OFF_HIGH = 0.10
SECTOR_DROP = -0.02
FEAR_VIX = 20.0

CLASSIC_SLOTS = 10
RULESETS = {"Leader Dip Plus 7": "plus", "Classic Leader Dip": "classic"}

EXIT_RULE = (f"Sell at the profit target (signal close + {TARGET_ATR:g} ATR), or at the next open once the 2-day RSI "
             f"closes above {SELL_ABOVE:.0f}, the stock closes under its 200-day average, or after {MAX_DAYS} trading "
             "days. No stop loss.")
CLASSIC_EXIT_RULE = (f"Sell at the next open once the 2-day RSI closes above {SELL_ABOVE:.0f}, or after {MAX_DAYS} "
                     "trading days. No stop loss.")
ENTRY_RULE = (f"Limit buy at {LIMIT:.0%} of the signal close for the next day only. It fills if the day's low reaches "
              "the limit; if the stock opens below it, you get the open.")
QUALITY_RULE = ("Needs at least one quality point: a deep dip (2.5+ ATRs under the 10-day high), more than 10% under "
                "the 52-week high, the sector ETF down 2%+ in 3 days, or VIX above 20.")

CASH_CHOICES = {
    "SPY while SPY is above its 200-day": "spy_trend",
    "T-bills": "tbills",
    "SPY always": "spy",
}
CASH_HELP = ("Where money waits when not every slot is in a trade. 'SPY while above its 200-day' (Plus 7's setting) "
             "holds the S&P 500 ETF whenever SPY closed above its 200-day average the day before, and T-bills "
             "otherwise. It turned 25% a year into 33% in the research, but it also adds the market's swings. "
             "T-bills earn the 3-month Treasury rate. 'SPY always' never leaves the market, so it takes the crashes too.")

GICS_ETF = {"Information Technology": "XLK", "Financials": "XLF", "Health Care": "XLV", "Consumer Discretionary": "XLY",
            "Communication Services": "XLC", "Industrials": "XLI", "Consumer Staples": "XLP", "Energy": "XLE",
            "Utilities": "XLU", "Real Estate": "XLRE", "Materials": "XLB",
            # Yahoo's sector names
            "Technology": "XLK", "Financial Services": "XLF", "Healthcare": "XLV", "Consumer Cyclical": "XLY",
            "Consumer Defensive": "XLP", "Basic Materials": "XLB"}


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


def six_month_gain(close: pd.Series | pd.DataFrame):
    return close / close.shift(STRENGTH_DAYS) - 1


def percentile_against(values: pd.Series, reference: pd.Series) -> pd.Series:
    """Share of ``reference`` (e.g. every S&P 500 stock's 6-month gain) below each value, 0 to 1."""
    ref = np.sort(pd.to_numeric(reference, errors="coerce").dropna().to_numpy())
    vals = pd.to_numeric(values, errors="coerce")
    if not len(ref):
        return pd.Series(np.nan, index=vals.index)
    pos = np.searchsorted(ref, vals.to_numpy(), side="left") + 0.5 * (
        np.searchsorted(ref, vals.to_numpy(), side="right") - np.searchsorted(ref, vals.to_numpy(), side="left"))
    return pd.Series(np.where(vals.notna(), pos / len(ref), np.nan), index=vals.index)


def _align(s: pd.Series | None, index: pd.Index) -> pd.Series | None:
    if s is None or len(s) == 0:
        return None
    s = s.astype(float).copy()
    s.index = pd.DatetimeIndex(s.index).normalize()
    s = s[~s.index.duplicated(keep="last")]
    full = s.reindex(s.index.union(pd.DatetimeIndex(index).normalize()))
    return walkforward.carry_forward(full).reindex(pd.DatetimeIndex(index).normalize()).set_axis(index)


def market_on(market_close: pd.Series | None, vix: pd.Series | None = None) -> pd.Series:
    """The on/off switch: True on days SPY closed above its 200-day average, or (with VIX) during a panic."""
    if market_close is None or len(market_close) == 0:
        return pd.Series(dtype=bool)
    m = market_close.astype(float)
    on = (m > ind.sma(m, TREND_DAYS)).fillna(False)
    v = _align(vix, m.index)
    if v is not None:
        on = on | (v > PANIC_VIX).fillna(False)
    return on


def sector_returns(index: pd.Index, columns: pd.Index, sector_etf: dict | pd.Series | None,
                   etf_close: pd.DataFrame | None, days: int = 3) -> pd.DataFrame | None:
    """Each stock's sector-ETF return over ``days`` (dates x tickers), from a {ticker: ETF} map."""
    if sector_etf is None or etf_close is None or etf_close.empty:
        return None
    etf = etf_close.astype(float)
    etf.index = pd.DatetimeIndex(etf.index).normalize()
    etf = etf[~etf.index.duplicated(keep="last")]
    r = (etf / etf.shift(days) - 1).reindex(pd.DatetimeIndex(index).normalize()).set_axis(index)
    m = dict(sector_etf)
    return pd.DataFrame({c: r[m[c]] if m.get(c) in r else np.nan for c in columns}, index=index)


def _members(members: pd.DataFrame | None, like: pd.DataFrame) -> pd.DataFrame | None:
    """Point-in-time membership aligned to a panel (False where unknown)."""
    if members is None:
        return None
    return members.reindex(index=like.index, columns=like.columns).fillna(False).astype(bool)


def signal_frames(close: pd.DataFrame, buy_below: float = BUY_BELOW, members: pd.DataFrame | None = None) -> dict:
    """Classic Leader Dip inputs and signals for a panel of closes (dates x tickers).

    The strength rank is each stock's 6-month gain ranked against the other columns that day, so pass the
    whole index, not a handful of tickers. With ``members`` (point-in-time index membership) a stock is only
    ranked against, and can only be bought while it is, a member that day."""
    close = close.astype(float)
    rsi2 = ind.rsi(close, RSI_DAYS)
    sma200 = ind.sma(close, TREND_DAYS)
    gain = six_month_gain(close)
    mem = _members(members, close)
    rank = (gain.where(mem) if mem is not None else gain).rank(axis=1, pct=True)
    buy = (rsi2 < buy_below) & (close > sma200) & (rank > STRENGTH_MIN)
    if mem is not None:
        buy &= mem
    return {"rsi2": rsi2, "sma200": sma200, "gain": gain, "rank": rank, "buy": buy.fillna(False),
            "sell": (rsi2 > SELL_ABOVE).fillna(False), "limit": close * LIMIT}


def quality_points(ohlc: dict, vix: pd.Series | None = None, sector_ret3: pd.DataFrame | None = None) -> dict:
    """The four Plus quality points (bool frames) and their count, for an OHLC panel."""
    c = ohlc["Close"].astype(float)
    atr = swing_engine.panel_atr(ohlc, ATR_DAYS)
    deep = ((c.rolling(10, min_periods=10).max() - c) / atr >= DEEP_DIP_ATR)
    off = c < (1 - OFF_HIGH) * c.rolling(252, min_periods=126).max()
    sec = (sector_ret3.reindex(index=c.index, columns=c.columns) < SECTOR_DROP) if sector_ret3 is not None else \
        pd.DataFrame(False, index=c.index, columns=c.columns)
    v = _align(vix, c.index)
    fear = pd.DataFrame(np.repeat(((v > FEAR_VIX).fillna(False) if v is not None else pd.Series(False, index=c.index))
                                  .to_numpy()[:, None], c.shape[1], 1), index=c.index, columns=c.columns)
    parts = {"Deep dip": deep.fillna(False), "Off the high": off.fillna(False), "Sector dip": sec.fillna(False),
             "Fear (VIX > 20)": fear}
    return {"parts": parts, "count": sum(p.astype(int) for p in parts.values()), "atr": atr}


def plus_frames(ohlc: dict, vix: pd.Series | None = None, sector_ret3: pd.DataFrame | None = None,
                buy_below: float = BUY_BELOW, target_atr: float = TARGET_ATR, members: pd.DataFrame | None = None) -> dict:
    """Leader Dip Plus signals for an OHLC panel: the classic signal plus a quality point, the profit target
    and the exit signal."""
    base = signal_frames(ohlc["Close"], buy_below, members)
    q = quality_points(ohlc, vix, sector_ret3)
    c = ohlc["Close"].astype(float)
    below = (c < base["sma200"]).fillna(False)
    return {**base, "quality": q["count"], "quality_parts": q["parts"], "atr": q["atr"],
            "buy": base["buy"] & (q["count"] >= 1), "target": c + target_atr * q["atr"],
            "exit": base["sell"] | below, "below200": below}


def latest(close: pd.DataFrame, reference_gains: pd.Series | None = None, ohlc: dict | None = None,
           vix: pd.Series | None = None, sector_ret3: pd.DataFrame | None = None) -> pd.DataFrame:
    """Every stock's Leader Dip reading at the last close.

    ``reference_gains`` (the S&P 500's 6-month gains) sets the strength rank; without it the stocks are ranked
    against each other. With ``ohlc`` (highs and lows) the Plus rules apply: quality points, the profit target
    and the 200-day exit. Without it the classic signal is returned."""
    close = close.astype(float).dropna(how="all")
    tail = close.iloc[-(TREND_DAYS + 300):]
    rsi2 = ind.rsi(tail, RSI_DAYS).iloc[-1]
    sma200 = ind.sma(tail, TREND_DAYS).iloc[-1]
    px = tail.ffill().iloc[-1]
    gain = six_month_gain(tail.ffill()).iloc[-1]
    ref = reference_gains if reference_gains is not None and len(reference_gains.dropna()) >= 10 else gain
    rank = percentile_against(gain, ref)
    out = pd.DataFrame({"Price": px, "RSI2": rsi2, "SMA200": sma200, "vs 200-day": px / sma200 - 1,
                        "6-month gain": gain, "Strength": rank})
    out["Uptrend"] = out["Price"] > out["SMA200"]
    out["Leader"] = out["Strength"] > STRENGTH_MIN
    out["Signal"] = out["Uptrend"] & out["Leader"] & (out["RSI2"] < BUY_BELOW)
    out["Limit"] = out["Price"] * LIMIT
    out["Sell signal"] = out["RSI2"] > SELL_ABOVE
    if ohlc is not None:
        sub = {f: ohlc[f].reindex(index=tail.index, columns=tail.columns) for f in ("Open", "High", "Low", "Close")}
        sr = sector_ret3.reindex(index=tail.index, columns=tail.columns) if sector_ret3 is not None else None
        q = quality_points(sub, vix, sr)
        out["Quality"] = q["count"].iloc[-1]
        out["Quality points"] = [", ".join(k for k, p in q["parts"].items() if bool(p[s].iloc[-1])) for s in out.index]
        out["ATR"] = q["atr"].iloc[-1]
        out["Target"] = out["Price"] + TARGET_ATR * out["ATR"]
        out["Base signal"] = out["Signal"]
        out["Signal"] = out["Signal"] & (out["Quality"] >= 1)
        out["Sell signal"] = out["Sell signal"] | ~out["Uptrend"]
    return out.dropna(subset=["Price"])


def stock_status(ohlcv: pd.DataFrame, reference_gains: pd.Series | None = None,
                 market_close: pd.Series | None = None, vix: pd.Series | None = None,
                 sector_close: pd.Series | None = None) -> dict:
    """One stock's Leader Dip Plus status at the last close, with a checklist. ``sector_close`` is the
    stock's sector ETF (for the sector-dip quality point)."""
    c = ohlcv["Close"].astype(float).dropna()
    h = ohlcv["High"].astype(float).reindex(c.index)
    lo = ohlcv["Low"].astype(float).reindex(c.index)
    rsi2 = ind.rsi(c, RSI_DAYS)
    sma200 = ind.sma(c, TREND_DAYS)
    gain_s = six_month_gain(c)
    price, r2, s200, gain = (float(x.iloc[-1]) if len(x) else np.nan for x in (c, rsi2, sma200, gain_s))
    rank = (float(percentile_against(pd.Series([gain]), reference_gains).iloc[0])
            if reference_gains is not None and len(reference_gains.dropna()) >= 10 else np.nan)
    sr3 = None
    if sector_close is not None and len(sector_close.dropna()) > 5:
        s_ = _align(sector_close, c.index)
        sr3 = pd.DataFrame({"x": s_ / s_.shift(3) - 1})
    panel = {"Open": c.to_frame("x"), "High": h.to_frame("x"), "Low": lo.to_frame("x"), "Close": c.to_frame("x")}
    q = quality_points(panel, vix, sr3)
    atr = float(q["atr"]["x"].iloc[-1]) if len(c) else np.nan
    parts = {k: bool(p["x"].iloc[-1]) for k, p in q["parts"].items()} if len(c) else {}
    n_q = sum(parts.values())
    hi10 = float(c.iloc[-10:].max()) if len(c) >= 10 else np.nan
    hi252 = float(c.iloc[-252:].max()) if len(c) else np.nan
    v_al = _align(vix, c.index)
    v_now = float(v_al.iloc[-1]) if v_al is not None and len(v_al) else np.nan
    mkt = market_on(market_close, vix)
    m_ok = bool(mkt.iloc[-1]) if len(mkt) else None
    m_gap = (float(market_close.iloc[-1] / ind.sma(market_close.astype(float), TREND_DAYS).iloc[-1] - 1)
             if market_close is not None and len(market_close) > TREND_DAYS else np.nan)
    up = bool(np.isfinite(s200) and price > s200)
    leader = bool(np.isfinite(rank) and rank > STRENGTH_MIN)
    dip = bool(np.isfinite(r2) and r2 < BUY_BELOW)
    signal = up and leader and dip and n_q >= 1
    limit = price * LIMIT
    target = price + TARGET_ATR * atr if np.isfinite(atr) else np.nan
    sec_txt = (f"sector ETF {float(sr3['x'].iloc[-1]):+.1%} in 3 days" if sr3 is not None and np.isfinite(sr3["x"].iloc[-1])
               else "sector ETF n/a")
    q_detail = (f"{n_q} of 4: deep dip {(hi10 - price) / atr:.1f} ATR" if np.isfinite(atr) and atr > 0 else f"{n_q} of 4") + \
        (f"; {price / hi252 - 1:+.0%} vs 52-week high" if np.isfinite(hi252) else "") + f"; {sec_txt}" + \
        (f"; VIX {v_now:.0f}" if np.isfinite(v_now) else "; VIX n/a")
    rows = [
        {"Rule": "Market switch: SPY above its 200-day (or VIX above 25)", "Pass": m_ok,
         "Detail": (f"SPY {m_gap:+.1%} vs its 200-day" if np.isfinite(m_gap) else "SPY data unavailable") +
                   (f", VIX {v_now:.0f}" if np.isfinite(v_now) else ""),
         "Why it matters": "New trades only in a market uptrend, or in a panic when even leaders get dumped. In the "
                           "research this kept the system out of most of 2008 and 2022."},
        {"Rule": "Stock above its 200-day average", "Pass": up if np.isfinite(s200) else None,
         "Detail": f"{price / s200 - 1:+.1%}" if np.isfinite(s200) else "needs 200 days of history",
         "Why it matters": "Dips in long-term uptrends tend to bounce; dips in downtrends tend to keep going."},
        {"Rule": f"6-month gain in the top {1 - STRENGTH_MIN:.0%} of the S&P 500", "Pass": leader if np.isfinite(rank) else None,
         "Detail": (f"{gain:+.0%}, beats {rank:.0%} of the index" if np.isfinite(rank) else
                    f"{gain:+.0%}; couldn't rank it against the index right now" if np.isfinite(gain) else "n/a"),
         "Why it matters": "Leaders get bought on dips. This filter mattered more than any other in the research."},
        {"Rule": f"2-day RSI below {BUY_BELOW:.0f}", "Pass": dip if np.isfinite(r2) else None,
         "Detail": f"{r2:.0f}" if np.isfinite(r2) else "n/a",
         "Why it matters": "A sharp two-day drop: the kind of overreaction that has tended to reverse within days."},
        {"Rule": "At least one quality point", "Pass": n_q >= 1 if len(c) else None, "Detail": q_detail,
         "Why it matters": "A deep flush, a stock well off its high, a sector-wide selloff or a fearful market made "
                           "for better bounces in 2000-12, and the rule held up after 2013."},
    ]
    if signal and m_ok is not False:
        label, tone = "Buy signal", "pos"
        note = (f"Place a limit buy at ${limit:,.2f} for the next session only. If it fills, set a sell limit at "
                f"${target:,.2f} (+{TARGET_ATR:g} ATR). {EXIT_RULE}")
    elif signal:
        label, tone = "Signal, market switch off", "neu"
        note = "The stock qualifies, but SPY is below its 200-day average and VIX is calm, so the system takes no new trades."
    elif up and leader and dip:
        label, tone = "Dip without a quality point", "neu"
        note = "The classic signal fired, but none of the four quality points did, so Plus skips it."
    elif up and leader and np.isfinite(r2) and r2 < 30:
        label, tone = "Dip forming", "neu"
        note = f"A leader in an uptrend with its 2-day RSI at {r2:.0f}; the signal needs it below {BUY_BELOW:.0f}."
    elif up and leader:
        label, tone = "Leader, no dip", "neu"
        note = "A leader in an uptrend. The system waits for a sharp short-term drop before buying."
    else:
        missing = [r["Rule"] for r in rows[1:3] if r["Pass"] is False]
        label, tone = "No setup", "neg"
        note = "Not a candidate: " + ("; ".join(m[0].lower() + m[1:] for m in missing) if missing else "not enough data") + "."
    return {"label": label, "tone": tone, "note": note, "signal": signal, "market_on": m_ok, "market_gap": m_gap,
            "price": price, "rsi2": r2, "sma200": s200, "vs200": price / s200 - 1 if np.isfinite(s200) else np.nan,
            "gain": gain, "rank": rank, "limit": limit, "target": target, "atr": atr, "quality": n_q,
            "quality_parts": parts, "vix": v_now,
            "sell_now": bool((np.isfinite(r2) and r2 > SELL_ABOVE) or (np.isfinite(s200) and price < s200)),
            "checklist": rows, "rsi2_series": rsi2, "sma200_series": sma200}


# ---------------------------------------------------------------------------
# Market regime
# ---------------------------------------------------------------------------


def _band(close: pd.Series, sma: pd.Series, band: float) -> pd.Series:
    """On above sma*(1+band), off below sma*(1-band), unchanged in between."""
    state, out = None, []
    for c, s in zip(close.to_numpy(), sma.to_numpy()):
        if np.isfinite(s):
            if c > s * (1 + band):
                state = True
            elif c < s * (1 - band):
                state = False
            elif state is None:
                state = bool(c > s)
        out.append(state)
    return pd.Series(out, index=close.index, dtype=object)


def regime(market_close: pd.Series, vix: pd.Series | None = None) -> dict:
    """SPY's trend read three ways, for the dashboard's regime light.

    * the 200-day line, Leader Dip's on/off switch (also on during a panic, VIX above 25)
    * the 200-day with a 2% band, which only flips on a clear break and so trades far less
    * the 10-month average, checked once a month (Faber 2007)
    """
    m = market_close.astype(float).dropna()
    if len(m) < TREND_DAYS + 5:
        return {}
    sma = ind.sma(m, TREND_DAYS)
    above = bool(m.iloc[-1] > sma.iloc[-1])
    band = _band(m, sma, 0.02)
    monthly = m.resample("ME").last()
    last = m.index[-1]
    if pd.offsets.BMonthEnd().rollforward(last).normalize() != last.normalize():
        monthly = monthly.iloc[:-1]  # the current month isn't finished
    ma10 = monthly.rolling(10).mean()
    ten = bool(monthly.iloc[-1] > ma10.iloc[-1]) if len(monthly) >= 10 and np.isfinite(ma10.iloc[-1]) else None
    flips = int((band.astype(float).diff().abs() > 0).iloc[-252:].sum())
    v = _align(vix, m.index)
    v_now = float(v.iloc[-1]) if v is not None and np.isfinite(v.iloc[-1]) else np.nan
    panic = bool(np.isfinite(v_now) and v_now > PANIC_VIX)
    return {
        "price": float(m.iloc[-1]), "sma200": float(sma.iloc[-1]), "gap200": float(m.iloc[-1] / sma.iloc[-1] - 1),
        "above200": above, "band_on": bool(band.iloc[-1]) if band.iloc[-1] is not None else None,
        "ten_month_on": ten, "ten_month_avg": float(ma10.iloc[-1]) if len(ma10) and np.isfinite(ma10.iloc[-1]) else np.nan,
        "month_close": float(monthly.iloc[-1]) if len(monthly) else np.nan,
        "month_end": monthly.index[-1] if len(monthly) else None, "band_flips_1y": flips,
        "vix": v_now, "panic": panic,
        "leader_dip_on": above or panic, "idle_cash": "SPY" if above else "T-bills",
    }


# ---------------------------------------------------------------------------
# Portfolio backtest
# ---------------------------------------------------------------------------


def backtest(ohlcv: dict, market_close: pd.Series, cash: str = "spy_trend", tbill_yields: pd.Series | None = None,
             slots: int = SLOTS, cost_bps: float = COST_BPS, start=None, rules: str = "plus",
             vix: pd.Series | None = None, sector_ret3: pd.DataFrame | None = None, buy_below: float = BUY_BELOW,
             target_atr: float = TARGET_ATR, members: pd.DataFrame | None = None, liquidate: bool = False) -> dict:
    """Run Leader Dip on a panel {"Open"|"High"|"Low"|"Close": dates x tickers}.

    ``rules`` is "plus" (quality points, profit target, 200-day exit, panic-aware switch) or "classic".
    Orders are decided at the close of day t and executed on day t+1 (see ``swing_engine``). Idle cash earns
    ``cash``: "spy_trend" (SPY when it closed above its 200-day the day before, T-bills otherwise), "tbills"
    or "spy". ``cost_bps`` is charged on each buy and each sell. ``members`` limits trading and ranking to
    point-in-time index members. One fixed set of settings over the whole span is an in-sample test: use
    ``walk_forward`` for out-of-sample results."""
    C = ohlcv["Close"].astype(float).sort_index().dropna(axis=1, how="all")
    dates = C.index
    panel = {f: ohlcv[f].reindex(index=dates, columns=C.columns).astype(float) for f in ("Open", "High", "Low")}
    panel["Close"] = C
    m = walkforward.carry_forward(market_close.astype(float).reindex(dates.union(market_close.index))).reindex(dates)
    plus = rules == "plus"
    gate = market_on(m, vix if plus else None).to_numpy()
    spy_r = m.pct_change(fill_method=None).fillna(0.0).to_numpy()
    rf = swing_engine.daily_cash(dates, tbill_yields)
    trend = (m > ind.sma(m, TREND_DAYS)).fillna(False).to_numpy()
    cash_r = spy_r if cash == "spy" else np.where(np.r_[False, trend[:-1]], spy_r, rf) if cash == "spy_trend" else rf
    t0 = TREND_DAYS
    if start is not None:
        t0 = max(t0, int(dates.searchsorted(pd.Timestamp(start))))
    if len(dates) - t0 < 30:
        raise ValueError("Not enough price history for a Leader Dip backtest (needs about a year).")
    if plus:
        sig = plus_frames(panel, vix, sector_ret3, buy_below, target_atr, members)
        labels = pd.DataFrame(np.where(sig["sell"].to_numpy(), "RSI(2) above 70",
                                       np.where(sig["below200"].to_numpy(), "Closed under 200-day", "")),
                              index=dates, columns=C.columns)
        run = swing_engine.run(panel, sig["buy"], sig["gain"], gate, cash_r, exit_signal=sig["exit"], limit=sig["limit"],
                               target=sig["target"], max_days=MAX_DAYS, slots=slots, cost_bps=cost_bps, t0=t0,
                               exit_labels=labels, liquidate=liquidate)
    else:
        sig = signal_frames(C, buy_below, members)
        run = swing_engine.run(panel, sig["buy"], sig["gain"], gate, cash_r, exit_signal=sig["sell"], limit=sig["limit"],
                               max_days=MAX_DAYS, slots=slots, cost_bps=cost_bps, t0=t0, exit_label="RSI(2) above 70",
                               liquidate=liquidate)
    equity, tr = run["equity"], run["trades"]
    spy_eq = pd.Series(np.cumprod(1 + spy_r[t0:]) / (1 + spy_r[t0]), index=dates[t0:])
    ew_r = C.pct_change(fill_method=None).iloc[t0:].mean(axis=1).fillna(0.0)
    ew_r.iloc[0] = 0.0
    rf_s = pd.Series(rf[t0:], index=dates[t0:])
    return {"equity": equity, "returns": equity.pct_change().fillna(0.0), "exposure": run["exposure"], "trades": tr,
            "spy_equity": spy_eq, "basket_equity": (1 + ew_r).cumprod(), "stats": stats(equity, rf_s, tr),
            "spy_stats": stats(spy_eq, rf_s), "basket_stats": stats((1 + ew_r).cumprod(), rf_s),
            "symbols": C.shape[1], "rules": rules}


stats = swing_engine.stats

RSI_GRID = (5.0, 10.0, 15.0)
TARGET_GRID = (1.0, 1.5, 2.0)


def walk_forward(ohlcv: dict, market_close: pd.Series, cash: str = "spy_trend", tbill_yields: pd.Series | None = None,
                 slots: int = SLOTS, cost_bps: float = COST_BPS, rules: str = "plus", vix: pd.Series | None = None,
                 sector_ret3: pd.DataFrame | None = None, members: pd.DataFrame | None = None,
                 progress=None) -> dict:
    """Leader Dip graded out of sample: each year's RSI(2) level (and, for Plus, profit target) is picked on the
    three years before it (see ``walkforward``), then traded on that year only. The purge gap is the
    10-day holding limit."""
    plus = rules == "plus"
    points = walkforward.grid(**({"RSI(2) below": RSI_GRID, "Target ATR": TARGET_GRID} if plus
                                 else {"RSI(2) below": RSI_GRID}))
    data = {"ohlcv": ohlcv, "market": market_close, "vix": vix, "sector": sector_ret3, "tbill": tbill_yields,
            "members": members}

    def evaluate(d, p, start):
        res = backtest(d["ohlcv"], d["market"], cash, d["tbill"], slots, cost_bps, start=start, rules=rules,
                       vix=d["vix"], sector_ret3=d["sector"], buy_below=p["RSI(2) below"],
                       target_atr=p.get("Target ATR", TARGET_ATR), members=d["members"], liquidate=True)
        return {"returns": res["returns"], "trades": res["trades"], "exposure": res["exposure"]}

    dates = ohlcv["Close"].sort_index().index
    rf = pd.Series(swing_engine.daily_cash(dates, tbill_yields), index=dates)
    wf = walkforward.run(evaluate, data, points, walkforward.folds(dates, purge=MAX_DAYS, first=TREND_DAYS), rf, progress)
    return _with_benchmarks(wf, market_close, rf, ohlcv["Close"], members)


def _with_benchmarks(wf: dict, market_close: pd.Series, rf: pd.Series, close: pd.DataFrame,
                     members: pd.DataFrame | None) -> dict:
    """Add SPY and an equal-weight basket of the index members over exactly the walk-forward's test days."""
    r = wf["returns"]
    rf_s = rf.reindex(r.index).fillna(0.0)
    spy_r = market_close.astype(float).pct_change(fill_method=None).reindex(r.index).fillna(0.0)
    c = close.sort_index().astype(float)
    ew = c.pct_change(fill_method=None)
    if members is not None:
        ew = ew.where(members.reindex(index=ew.index, columns=ew.columns).fillna(False).astype(bool).shift(1, fill_value=False))
    ew_r = ew.mean(axis=1).reindex(r.index).fillna(0.0)
    for name, br in (("spy", spy_r), ("basket", ew_r)):
        br.iloc[0] = 0.0
        wf[f"{name}_equity"] = (1 + br).cumprod()
        wf[f"{name}_stats"] = stats(wf[f"{name}_equity"], rf_s)
    wf["stats"] = stats(wf["equity"], rf_s, wf["trades"] if len(wf["trades"]) else None)
    wf["symbols"] = int(c.shape[1])
    return wf


# ---------------------------------------------------------------------------
# Signal log: check live signals against what happened next
# ---------------------------------------------------------------------------


def follow_up(log: pd.DataFrame, ohlcv: dict) -> pd.DataFrame:
    """For each logged signal (Date, Symbol, Close, Limit and, for Plus signals, Target), whether the limit
    filled the next session and how the trade went under the exit rules."""
    if log.empty:
        return log
    C = ohlcv.get("Close", pd.DataFrame())
    rows = []
    for _, s in log.iterrows():
        sym, d = s["Symbol"], pd.Timestamp(s["Date"])
        out = {**s.to_dict(), "Filled": None, "Fill price": np.nan, "Exit date": pd.NaT, "Exit price": np.nan,
               "Return": np.nan, "Status": "Waiting for the next session"}
        if sym not in C or C[sym].dropna().empty:
            out["Status"] = "No price data"
            rows.append(out)
            continue
        c = C[sym].dropna()
        o, lo = ohlcv["Open"][sym].reindex(c.index), ohlcv["Low"][sym].reindex(c.index)
        hi = ohlcv["High"][sym].reindex(c.index) if "High" in ohlcv else c
        after = c.index[c.index > d]
        if not len(after):
            rows.append(out)
            continue
        t_in = c.index.get_loc(after[0])
        limit = float(s["Limit"])
        if not np.isfinite(lo.iloc[t_in]) or lo.iloc[t_in] > limit:
            out.update(Filled=False, Status="Not filled")
            rows.append(out)
            continue
        fill = float(min(o.iloc[t_in], limit)) if np.isfinite(o.iloc[t_in]) else limit
        at_open = bool(np.isfinite(o.iloc[t_in]) and o.iloc[t_in] <= limit)  # else it filled somewhere in the day
        out.update({"Filled": True, "Fill price": fill})
        tgt = float(s["Target"]) if "Target" in s and pd.notna(s.get("Target")) else np.nan
        r2 = ind.rsi(c, RSI_DAYS)
        s200 = ind.sma(c, TREND_DAYS) if np.isfinite(tgt) else pd.Series(np.nan, index=c.index)
        exit_t, done = None, False
        for t in range(t_in, len(c)):
            if np.isfinite(tgt):
                if t > t_in and np.isfinite(o.iloc[t]) and o.iloc[t] >= tgt:
                    out.update({"Exit date": c.index[t], "Exit price": float(o.iloc[t]), "Return": float(o.iloc[t]) / fill - 1,
                                "Status": "Closed"})
                    done = True
                    break
                if np.isfinite(hi.iloc[t]) and hi.iloc[t] >= tgt and (t > t_in or at_open):
                    out.update({"Exit date": c.index[t], "Exit price": tgt, "Return": tgt / fill - 1, "Status": "Closed"})
                    done = True
                    break
            if r2.iloc[t] > SELL_ABOVE or t - t_in + 1 >= MAX_DAYS or (np.isfinite(s200.iloc[t]) and c.iloc[t] < s200.iloc[t]):
                exit_t = t + 1
                break
        if done:
            rows.append(out)
            continue
        if exit_t is not None and exit_t < len(c):
            px = float(o.iloc[exit_t]) if np.isfinite(o.iloc[exit_t]) else float(c.iloc[exit_t])
            out.update({"Exit date": c.index[exit_t], "Exit price": px, "Return": px / fill - 1, "Status": "Closed"})
        else:
            out.update({"Return": float(c.iloc[-1]) / fill - 1,
                        "Status": "Sell at the next open" if exit_t is not None else "Open"})
        rows.append(out)
    return pd.DataFrame(rows)
