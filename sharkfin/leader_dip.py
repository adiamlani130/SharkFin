"""Leader Dip: SharkFin's swing system.

Buy a short, sharp dip in one of the market's strongest stocks while the
market itself is in an uptrend, and sell into the bounce.

  Signal, at the close: the 2-day RSI is below 10, the stock closes above its
  200-day average, and its 6-month gain is in the top 30% of the S&P 500.
  New trades are only placed while SPY closes above its own 200-day average.
  Entry, the next day: a limit order 3% under the signal close. It fills only
  if the day's low reaches the limit, at the open when the stock opens below it.
  Exit: at the next open after the 2-day RSI closes above 70, or after 10
  trading days. There is no stop loss.
  Portfolio: 10 equal slots. When more stocks signal than there are free slots,
  the biggest 6-month gainers go first.

In SharkFin's Oct 2026 research (point-in-time S&P 500 members, 0.1% cost per
side) these rules made 12.7% a year in 2013-26 with a Sharpe ratio of 1.02,
and won on 67% of trades. The settings were picked after seeing the data, so
the median of 576 nearby variants (9.9% a year, Sharpe 0.78) is the fairer
expectation.

Everything is computed from data up to the signal close, and fills only use
the next day's open and low, so there is no look-ahead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import indicators as ind

RSI_DAYS = 2
BUY_BELOW = 10.0
SELL_ABOVE = 70.0
TREND_DAYS = 200
STRENGTH_DAYS = 126
STRENGTH_MIN = 0.70
LIMIT = 0.97
MAX_DAYS = 10
SLOTS = 10
COST_BPS = 10.0

EXIT_RULE = (f"Sell at the next open once the 2-day RSI closes above {SELL_ABOVE:.0f}, or after {MAX_DAYS} trading days. "
             "No stop loss.")
ENTRY_RULE = (f"Limit buy at {LIMIT:.0%} of the signal close for the next day only. It fills if the day's low reaches "
              "the limit; if the stock opens below it, you get the open.")

CASH_CHOICES = {
    "T-bills": "tbills",
    "SPY while SPY is above its 200-day": "spy_trend",
    "SPY always": "spy",
}
CASH_HELP = ("Where money waits when fewer than 10 trades are open. T-bills earn the 3-month Treasury rate. "
             "'SPY while above its 200-day' holds the S&P 500 ETF whenever SPY closed above its 200-day average the "
             "day before, and T-bills otherwise; it was the best mix in the research. 'SPY always' never leaves the "
             "market, so it also takes the market's crashes.")


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


def market_on(market_close: pd.Series | None) -> pd.Series:
    """The on/off switch: True on days SPY closed above its 200-day average."""
    if market_close is None or len(market_close) == 0:
        return pd.Series(dtype=bool)
    m = market_close.astype(float)
    return (m > ind.sma(m, TREND_DAYS)).fillna(False)


def signal_frames(close: pd.DataFrame) -> dict:
    """Leader Dip inputs and signals for a panel of closes (dates x tickers).

    The strength rank is each stock's 6-month gain ranked against the other
    columns that day, so pass the whole index, not a handful of tickers."""
    close = close.astype(float)
    rsi2 = ind.rsi(close, RSI_DAYS)
    sma200 = ind.sma(close, TREND_DAYS)
    gain = six_month_gain(close)
    rank = gain.rank(axis=1, pct=True)
    buy = (rsi2 < BUY_BELOW) & (close > sma200) & (rank > STRENGTH_MIN)
    return {"rsi2": rsi2, "sma200": sma200, "gain": gain, "rank": rank, "buy": buy.fillna(False),
            "sell": (rsi2 > SELL_ABOVE).fillna(False), "limit": close * LIMIT}


def latest(close: pd.DataFrame, reference_gains: pd.Series | None = None) -> pd.DataFrame:
    """Every stock's Leader Dip reading at the last close.

    ``reference_gains`` (the S&P 500's 6-month gains) sets the strength rank;
    without it the stocks are ranked against each other."""
    close = close.astype(float).dropna(how="all")
    tail = close.iloc[-(TREND_DAYS + 60):]
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
    return out.dropna(subset=["Price"])


def stock_status(ohlcv: pd.DataFrame, reference_gains: pd.Series | None = None,
                 market_close: pd.Series | None = None) -> dict:
    """One stock's Leader Dip status at the last close, with a checklist."""
    c = ohlcv["Close"].astype(float).dropna()
    rsi2 = ind.rsi(c, RSI_DAYS)
    sma200 = ind.sma(c, TREND_DAYS)
    gain_s = six_month_gain(c)
    price, r2, s200, gain = (float(x.iloc[-1]) if len(x) else np.nan for x in (c, rsi2, sma200, gain_s))
    rank = (float(percentile_against(pd.Series([gain]), reference_gains).iloc[0])
            if reference_gains is not None and len(reference_gains.dropna()) >= 10 else np.nan)
    mkt = market_on(market_close)
    m_ok = bool(mkt.iloc[-1]) if len(mkt) else None
    m_gap = (float(market_close.iloc[-1] / ind.sma(market_close.astype(float), TREND_DAYS).iloc[-1] - 1)
             if market_close is not None and len(market_close) > TREND_DAYS else np.nan)
    up = bool(np.isfinite(s200) and price > s200)
    leader = bool(np.isfinite(rank) and rank > STRENGTH_MIN)
    dip = bool(np.isfinite(r2) and r2 < BUY_BELOW)
    signal = up and leader and dip
    limit = price * LIMIT
    rows = [
        {"Rule": "Market switch: SPY above its 200-day average", "Pass": m_ok,
         "Detail": f"SPY {m_gap:+.1%} vs its 200-day" if np.isfinite(m_gap) else "SPY data unavailable",
         "Why it matters": "New trades are only placed in a market uptrend. In the research this kept the system out "
                           "of most of 2008 and 2022."},
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
    ]
    if signal and m_ok is not False:
        label, tone = "Buy signal", "pos"
        note = f"Place a limit buy at ${limit:,.2f} for the next session only. {EXIT_RULE}"
    elif signal:
        label, tone = "Signal, market switch off", "neu"
        note = "The stock qualifies, but SPY is below its 200-day average, so the system takes no new trades."
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
            "gain": gain, "rank": rank, "limit": limit, "sell_now": bool(np.isfinite(r2) and r2 > SELL_ABOVE),
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


def regime(market_close: pd.Series) -> dict:
    """SPY's trend read three ways, for the dashboard's regime light.

    * the 200-day line, which is Leader Dip's on/off switch
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
    return {
        "price": float(m.iloc[-1]), "sma200": float(sma.iloc[-1]), "gap200": float(m.iloc[-1] / sma.iloc[-1] - 1),
        "above200": above, "band_on": bool(band.iloc[-1]) if band.iloc[-1] is not None else None,
        "ten_month_on": ten, "ten_month_avg": float(ma10.iloc[-1]) if len(ma10) and np.isfinite(ma10.iloc[-1]) else np.nan,
        "month_close": float(monthly.iloc[-1]) if len(monthly) else np.nan,
        "month_end": monthly.index[-1] if len(monthly) else None, "band_flips_1y": flips,
        "leader_dip_on": above, "idle_cash": "SPY" if above else "T-bills",
    }


# ---------------------------------------------------------------------------
# Portfolio backtest
# ---------------------------------------------------------------------------


def _daily_cash(dates: pd.DatetimeIndex, tbill_yields: pd.Series | None, fallback: float = 0.04) -> np.ndarray:
    y = pd.Series(fallback, index=dates)
    if tbill_yields is not None and len(tbill_yields.dropna()):
        t = tbill_yields.dropna().astype(float)
        t.index = pd.DatetimeIndex(t.index)
        y = t.reindex(dates.union(t.index)).ffill().reindex(dates).bfill().fillna(fallback)
    return ((1 + y.shift(1).fillna(y.iloc[0])) ** (1 / 252) - 1).to_numpy()


def backtest(ohlcv: dict, market_close: pd.Series, cash: str = "tbills", tbill_yields: pd.Series | None = None,
             slots: int = SLOTS, cost_bps: float = COST_BPS, start=None) -> dict:
    """Run Leader Dip on a panel {"Open"|"High"|"Low"|"Close": dates x tickers}.

    Orders are decided at the close of day t and executed on day t+1: exits at
    the open, then limit entries in strength order while slots are free. Each
    new trade gets 1/``slots`` of the account; idle cash earns ``cash``:
    "tbills", "spy_trend" (SPY when it closed above its 200-day the day
    before) or "spy". ``cost_bps`` is charged on each buy and each sell."""
    C = ohlcv["Close"].astype(float).sort_index()
    C = C.loc[:, C.notna().sum() > TREND_DAYS]
    dates, syms = C.index, list(C.columns)
    O, H, L = (ohlcv[f].reindex(index=dates, columns=syms).astype(float).to_numpy() for f in ("Open", "High", "Low"))
    sig = signal_frames(C)
    Cn = C.to_numpy()
    buy = sig["buy"].to_numpy()
    sell = sig["sell"].to_numpy()
    score = sig["gain"].to_numpy()
    lim = sig["limit"].to_numpy()
    m = market_close.astype(float).reindex(dates.union(market_close.index)).ffill().reindex(dates)
    gate = market_on(m).to_numpy()
    spy_r = m.pct_change(fill_method=None).fillna(0.0).to_numpy()
    rf = _daily_cash(dates, tbill_yields)
    if cash == "spy":
        cash_r = spy_r
    elif cash == "spy_trend":
        cash_r = np.where(np.r_[False, gate[:-1]], spy_r, rf)
    else:
        cash_r = rf
    cost = cost_bps / 1e4
    T, N, K = len(dates), len(syms), int(slots)
    t0 = TREND_DAYS
    if start is not None:
        t0 = max(t0, int(dates.searchsorted(pd.Timestamp(start))))
    if T - t0 < 30:
        raise ValueError("Not enough price history for a Leader Dip backtest (needs about a year).")

    slot_j = np.full(K, -1)
    shares, entry_px, entry_t = np.zeros(K), np.zeros(K), np.zeros(K, int)
    last_c, exit_next, exit_why = np.zeros(K), np.zeros(K, bool), [""] * K
    held = np.zeros(N, bool)
    pend: list[tuple[int, float]] = []
    cash_bal, last_eq = 1.0, 1.0
    eq, expo = np.full(T, np.nan), np.zeros(T)
    trades = []

    for t in range(t0, T):
        cash_bal *= 1 + cash_r[t]
        # 1) exits decided yesterday, at today's open
        for k in range(K):
            if slot_j[k] >= 0 and exit_next[k]:
                j = slot_j[k]
                px = O[t, j] if np.isfinite(O[t, j]) and O[t, j] > 0 else last_c[k]
                cash_bal += shares[k] * px * (1 - cost)
                trades.append((syms[j], dates[entry_t[k] - 1], dates[entry_t[k]], entry_px[k], dates[t], px,
                               px * (1 - cost) / (entry_px[k] * (1 + cost)) - 1, t - entry_t[k], exit_why[k]))
                held[j], slot_j[k], shares[k], exit_next[k] = False, -1, 0.0, False
        # 2) limit entries placed yesterday
        for j, limit in pend:
            free = np.flatnonzero(slot_j < 0)
            if not len(free):
                break
            o, lo = O[t, j], L[t, j]
            if not (np.isfinite(o) and o > 0 and np.isfinite(lo)) or lo > limit:
                continue
            px = min(o, limit)
            alloc = min(last_eq / K, cash_bal)
            if alloc <= 1e-9:
                break
            k = free[0]
            slot_j[k], shares[k], entry_px[k], entry_t[k], last_c[k] = j, alloc / (px * (1 + cost)), px, t, px
            cash_bal -= alloc
            held[j] = True
        pend = []
        # 3) mark to market
        inv = 0.0
        for k in range(K):
            if slot_j[k] >= 0:
                c = Cn[t, slot_j[k]]
                if np.isfinite(c):
                    last_c[k] = c
                inv += shares[k] * last_c[k]
        last_eq = cash_bal + inv
        eq[t], expo[t] = last_eq, inv / last_eq if last_eq > 0 else 0.0
        if t == T - 1:
            break
        # 4) exits for tomorrow's open
        n_free = int((slot_j < 0).sum())
        for k in range(K):
            j = slot_j[k]
            if j < 0:
                continue
            why = ("RSI(2) above 70" if sell[t, j] else f"{MAX_DAYS} days" if t - entry_t[k] + 1 >= MAX_DAYS
                   else "No more data" if not np.isfinite(Cn[t + 1, j]) else "")
            if why:
                exit_next[k], exit_why[k] = True, why
                n_free += 1
        # 5) new limit orders for tomorrow, strongest first
        if n_free and gate[t]:
            cand = np.flatnonzero(buy[t] & ~held & np.isfinite(score[t]))
            if len(cand):
                order = cand[np.argsort(-score[t, cand], kind="stable")][:n_free]
                pend = [(int(j), float(lim[t, j])) for j in order]

    for k in range(K):  # still open at the end
        j = slot_j[k]
        if j >= 0:
            trades.append((syms[j], dates[entry_t[k] - 1], dates[entry_t[k]], entry_px[k], pd.NaT, last_c[k],
                           last_c[k] / (entry_px[k] * (1 + cost)) - 1, T - 1 - entry_t[k], "Open"))
    cols = ["Symbol", "Signal date", "Bought", "Buy price", "Sold", "Sell price", "Return", "Days held", "Why it sold"]
    tr = pd.DataFrame(trades, columns=cols).sort_values("Bought", kind="stable").reset_index(drop=True)
    equity = pd.Series(eq[t0:], index=dates[t0:])
    rets = equity.pct_change().fillna(0.0)
    spy_eq = pd.Series(np.cumprod(1 + spy_r[t0:]) / (1 + spy_r[t0]), index=dates[t0:])
    ew_r = C.pct_change(fill_method=None).iloc[t0:].mean(axis=1).fillna(0.0)
    ew_r.iloc[0] = 0.0
    rf_s = pd.Series(rf[t0:], index=dates[t0:])
    return {"equity": equity, "returns": rets, "exposure": pd.Series(expo[t0:], index=dates[t0:]), "trades": tr,
            "spy_equity": spy_eq, "basket_equity": (1 + ew_r).cumprod(), "stats": stats(equity, rf_s, tr),
            "spy_stats": stats(spy_eq, rf_s), "basket_stats": stats((1 + ew_r).cumprod(), rf_s),
            "symbols": len(syms)}


def stats(equity: pd.Series, rf_daily: pd.Series | None = None, trades: pd.DataFrame | None = None) -> dict:
    e = equity.dropna()
    r = e.pct_change().dropna()
    years = len(r) / 252
    out = {"Return per year": float((e.iloc[-1] / e.iloc[0]) ** (1 / years) - 1) if years > 0 else np.nan,
           "Total return": float(e.iloc[-1] / e.iloc[0] - 1), "Worst drop": float((e / e.cummax() - 1).min()),
           "Volatility": float(r.std() * np.sqrt(252)), "Years": years}
    ex = r - (rf_daily.reindex(r.index).fillna(0.0) if rf_daily is not None else 0.0)
    out["Sharpe"] = float(ex.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan
    if trades is not None:
        done = trades[trades["Why it sold"] != "Open"]
        out.update({"Trades": int(len(done)), "Trades per year": len(done) / years if years else np.nan,
                    "Win rate": float((done["Return"] > 0).mean()) if len(done) else np.nan,
                    "Avg trade": float(done["Return"].mean()) if len(done) else np.nan,
                    "Avg days held": float(done["Days held"].mean()) if len(done) else np.nan})
    return out


# ---------------------------------------------------------------------------
# Signal log: check live signals against what happened next
# ---------------------------------------------------------------------------


def follow_up(log: pd.DataFrame, ohlcv: dict) -> pd.DataFrame:
    """For each logged signal (Date, Symbol, Close, Limit), whether the limit
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
        out.update({"Filled": True, "Fill price": fill})
        r2 = ind.rsi(c, RSI_DAYS)
        exit_t = None
        for t in range(t_in, len(c)):
            if r2.iloc[t] > SELL_ABOVE or t - t_in + 1 >= MAX_DAYS:
                exit_t = t + 1
                break
        if exit_t is not None and exit_t < len(c):
            px = float(o.iloc[exit_t]) if np.isfinite(o.iloc[exit_t]) else float(c.iloc[exit_t])
            out.update({"Exit date": c.index[exit_t], "Exit price": px, "Return": px / fill - 1, "Status": "Closed"})
        else:
            out.update({"Return": float(c.iloc[-1]) / fill - 1,
                        "Status": "Sell at the next open" if exit_t is not None else "Open"})
        rows.append(out)
    return pd.DataFrame(rows)
