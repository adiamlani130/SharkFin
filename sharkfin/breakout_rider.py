"""Tech Breakout Rider: buy tech leaders breaking out to a new high and ride the trend for weeks or months.

  Universe: S&P 500 tech stocks (Information Technology and Communication Services) plus AMZN and TSLA.
  Signal, at the close: the stock closes above its highest high of the previous 20 days, on an up day (close
  above yesterday's close), with ADX(14) above 20 (a real trend), and its 6-month gain ranks in the top 30% of
  the tech stocks. New trades only while QQQ's 21-day EMA is above its 50-day EMA (tech in an uptrend).
  Entry, the next day: a limit order half an ATR under the signal close, good for that day only.
  Exit: at the next open after the stock's 21-day EMA closes under its 50-day EMA, or after 90 trading days.
  No stop loss and no profit target: the trend exit does both jobs.
  Portfolio: 10 equal slots; with more signals than free slots, the biggest 1-month gainers go first. Cash
  not in trades earns T-bill interest.

SharkFin's Oct 2026 research picked these settings from 4,200 tech systems on 2016-21 data and graded them on
Oct 2021 - Oct 2026: 33.8% a year, Sharpe 1.09, worst drop 29%, 49% of trades won but winners averaged +36%
against -11.5% for losers. Nearby settings made 27% a year at the median. It leans on a few huge winners
(without its best 5 stocks it made about 15% a year), lost 25% in 2022 and made only 7% a year in 2000-12.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import indicators as ind
from . import swing_engine, walkforward

BREAKOUT_DAYS = 20
ADX_MIN = 20.0
STRENGTH_DAYS = 126
STRENGTH_MIN = 0.70
SCORE_DAYS = 21
LIMIT_ATR = 0.5
FAST, SLOW = 21, 50
MAX_DAYS = 90
SLOTS = 10
COST_BPS = 10.0
TECH_SECTORS = ("Information Technology", "Communication Services")
TECH_EXTRA = ("AMZN", "TSLA")
# Used when the S&P 500 sector table can't be downloaded.
TECH_FALLBACK = (
    "AAPL MSFT NVDA AVGO ORCL CRM ADBE AMD CSCO ACN IBM INTU NOW TXN QCOM AMAT ADI LRCX MU KLAC PANW ANET SNPS CDNS "
    "CRWD APH MSI NXPI ROP FTNT ADSK MCHP TEL IT CTSH GLW HPQ ON MPWR DELL KEYS FICO HPE CDW NTAP STX WDC TER TYL PTC "
    "ZBRA SMCI FSLR GDDY TRMB AKAM JBL FFIV GEN EPAM SWKS PLTR APP DDOG TTD WDAY SNDK "
    "GOOGL GOOG META NFLX TMUS DIS CMCSA VZ T CHTR EA TTWO WBD OMC LYV MTCH FOXA FOX NWSA NWS IPG "
    "AMZN TSLA"
).split()

ENTRY_RULE = (f"Limit buy at the signal close minus {LIMIT_ATR:g} ATR, for the next day only. It fills if the day's "
              "low reaches the limit; if the stock opens below it, you get the open.")
EXIT_RULE = (f"Sell at the next open once the stock's {FAST}-day EMA closes under its {SLOW}-day EMA, or after "
             f"{MAX_DAYS} trading days. No stop and no profit target.")


def tech_universe(sp500: pd.DataFrame | None) -> list[str]:
    """S&P 500 tech and communication stocks plus AMZN and TSLA."""
    if sp500 is not None and "Sector" in sp500 and sp500["Sector"].notna().sum() > 100:
        names = sp500.loc[sp500["Sector"].isin(TECH_SECTORS), "Symbol"].tolist()
        return sorted(set(names) | set(TECH_EXTRA))
    return list(dict.fromkeys(TECH_FALLBACK))


def qqq_gate(qqq_close: pd.Series | None) -> pd.Series:
    """True on days QQQ's 21-day EMA closed above its 50-day EMA."""
    if qqq_close is None or len(qqq_close) == 0:
        return pd.Series(dtype=bool)
    q = qqq_close.astype(float)
    return (q.ewm(span=FAST, adjust=False).mean() > q.ewm(span=SLOW, adjust=False).mean())


def signal_frames(ohlc: dict, breakout_days: int = BREAKOUT_DAYS, adx_min: float = ADX_MIN,
                  members: pd.DataFrame | None = None) -> dict:
    """Signals for an OHLC panel of tech stocks (dates x tickers). The strength rank is against the columns, so
    pass the whole tech universe. With ``members`` (point-in-time index membership) a stock is only ranked
    against, and can only be bought while it is, a member that day."""
    c = ohlc["Close"].astype(float)
    h = ohlc["High"].astype(float)
    prior_high = h.rolling(breakout_days, min_periods=breakout_days).max().shift(1)
    adx = swing_engine.panel_adx(ohlc, 14)
    atr = swing_engine.panel_atr(ohlc, 14)
    gain = c / c.shift(STRENGTH_DAYS) - 1
    mem = members.reindex(index=c.index, columns=c.columns).fillna(False).astype(bool) if members is not None else None
    rank = (gain.where(mem) if mem is not None else gain).rank(axis=1, pct=True)
    up = c > c.shift(1)
    ema_f = c.ewm(span=FAST, adjust=False, min_periods=FAST).mean()
    ema_s = c.ewm(span=SLOW, adjust=False, min_periods=SLOW).mean()
    buy = (c > prior_high) & up & (adx > adx_min) & (rank >= STRENGTH_MIN)
    if mem is not None:
        buy &= mem
    return {"buy": buy.fillna(False), "prior_high": prior_high, "adx": adx, "atr": atr, "gain": gain, "rank": rank,
            "score": c / c.shift(SCORE_DAYS) - 1, "limit": c - LIMIT_ATR * atr, "ema_fast": ema_f, "ema_slow": ema_s,
            "exit": (ema_f < ema_s).fillna(False)}


def latest(ohlc: dict, qqq_close: pd.Series | None = None) -> pd.DataFrame:
    """Every stock's Breakout Rider reading at the last close."""
    tail = {f: ohlc[f].astype(float).iloc[-320:] for f in ("Open", "High", "Low", "Close")}
    s = signal_frames(tail)
    c = tail["Close"].ffill().iloc[-1]
    out = pd.DataFrame({"Price": c, "20-day high": s["prior_high"].iloc[-1], "ADX": s["adx"].iloc[-1],
                        "6-month gain": s["gain"].iloc[-1], "Strength": s["rank"].iloc[-1],
                        "1-month gain": s["score"].iloc[-1], "Limit": s["limit"].iloc[-1],
                        "EMA21": s["ema_fast"].iloc[-1], "EMA50": s["ema_slow"].iloc[-1]})
    out["Up day"] = tail["Close"].iloc[-1] > tail["Close"].iloc[-2]
    out["Breakout"] = out["Price"] > out["20-day high"]
    out["Signal"] = s["buy"].iloc[-1].reindex(out.index).fillna(False)
    out["Trend intact"] = out["EMA21"] >= out["EMA50"]
    out["vs 20-day high"] = out["Price"] / out["20-day high"] - 1
    g = qqq_gate(qqq_close)
    out.attrs["gate_on"] = bool(g.iloc[-1]) if len(g) else None
    return out.dropna(subset=["Price"])


def stock_status(ohlcv: pd.DataFrame, reference_gains: pd.Series | None = None,
                 qqq_close: pd.Series | None = None, is_tech: bool | None = None) -> dict:
    """One stock's Breakout Rider status at the last close, with a checklist. ``reference_gains`` are the tech
    stocks' 6-month gains (for the strength rank)."""
    from .leader_dip import percentile_against

    c = ohlcv["Close"].astype(float).dropna()
    one = {f: ohlcv[f].astype(float).reindex(c.index).to_frame("x") for f in ("Open", "High", "Low", "Close")}
    s = signal_frames(one)
    last = lambda k: float(s[k]["x"].iloc[-1]) if len(c) else np.nan
    price, hi20, adx, atr, gain = float(c.iloc[-1]), last("prior_high"), last("adx"), last("atr"), last("gain")
    ef, es = last("ema_fast"), last("ema_slow")
    rank = (float(percentile_against(pd.Series([gain]), reference_gains).iloc[0])
            if reference_gains is not None and len(reference_gains.dropna()) >= 10 else np.nan)
    g = qqq_gate(qqq_close)
    gate = bool(g.iloc[-1]) if len(g) else None
    up = bool(len(c) > 1 and c.iloc[-1] > c.iloc[-2])
    brk = bool(np.isfinite(hi20) and price > hi20)
    trend = bool(np.isfinite(adx) and adx > ADX_MIN)
    leader = bool(np.isfinite(rank) and rank >= STRENGTH_MIN)
    signal = up and brk and trend and leader and is_tech is not False
    limit = price - LIMIT_ATR * atr if np.isfinite(atr) else np.nan
    rows = [
        {"Rule": "Tech in an uptrend: QQQ 21-day EMA above its 50-day", "Pass": gate,
         "Detail": "on" if gate else "off" if gate is False else "QQQ data unavailable",
         "Why it matters": "Breakouts work when the whole group is rising. The switch kept the system mostly out of "
                           "the 2022 tech crash's worst stretches."},
        {"Rule": "A tech stock (S&P 500 tech or communications, or AMZN / TSLA)", "Pass": is_tech,
         "Detail": "yes" if is_tech else "no" if is_tech is False else "unknown",
         "Why it matters": "The system was built and tested on tech names only."},
        {"Rule": f"Close above the prior {BREAKOUT_DAYS}-day high", "Pass": brk if np.isfinite(hi20) else None,
         "Detail": f"{price / hi20 - 1:+.1%} vs the high of {hi20:,.2f}" if np.isfinite(hi20) else "n/a",
         "Why it matters": "A new one-month high is where big trends start: buyers are in control."},
        {"Rule": "An up day", "Pass": up, "Detail": f"{c.iloc[-1] / c.iloc[-2] - 1:+.1%} today" if len(c) > 1 else "n/a",
         "Why it matters": "The breakout has to close strong, not fade back."},
        {"Rule": f"ADX(14) above {ADX_MIN:.0f}", "Pass": trend if np.isfinite(adx) else None,
         "Detail": f"{adx:.0f}" if np.isfinite(adx) else "n/a",
         "Why it matters": "ADX measures trend strength. Breakouts out of a dead, sideways stock tend to fail."},
        {"Rule": f"6-month gain in the top {1 - STRENGTH_MIN:.0%} of tech stocks", "Pass": leader if np.isfinite(rank) else None,
         "Detail": (f"{gain:+.0%}, beats {rank:.0%} of tech" if np.isfinite(rank) else
                    f"{gain:+.0%}; couldn't rank it against tech right now" if np.isfinite(gain) else "n/a"),
         "Why it matters": "Strong stocks keep leading. The biggest winners were already leaders when they broke out."},
    ]
    if signal and gate is not False:
        label, tone = "Buy signal", "pos"
        note = f"Place a limit buy at ${limit:,.2f} for the next session only. {EXIT_RULE}"
    elif signal:
        label, tone = "Signal, tech switch off", "neu"
        note = "The stock breaks out, but QQQ's 21-day EMA is under its 50-day, so the system takes no new trades."
    elif np.isfinite(ef) and np.isfinite(es) and ef < es:
        label, tone = "Trend broken", "neg"
        note = "The 21-day EMA is under the 50-day: a held Breakout Rider position would sell at the next open."
    elif brk or (np.isfinite(hi20) and price > 0.97 * hi20):
        label, tone = "Near a breakout", "neu"
        note = f"Within 3% of its 20-day high ({hi20:,.2f}). A close above it on an up day with the other rules met is a signal."
    else:
        label, tone = "No setup", "neu"
        note = "Not breaking out. The system waits for a close above the 20-day high."
    return {"label": label, "tone": tone, "note": note, "signal": signal, "gate_on": gate, "price": price,
            "high20": hi20, "adx": adx, "atr": atr, "gain": gain, "rank": rank, "limit": limit, "ema_fast": ef,
            "ema_slow": es, "sell_now": bool(np.isfinite(ef) and np.isfinite(es) and ef < es), "checklist": rows,
            "ema_fast_series": s["ema_fast"]["x"], "ema_slow_series": s["ema_slow"]["x"],
            "high20_series": s["prior_high"]["x"]}


def backtest(ohlcv: dict, qqq_close: pd.Series, tbill_yields: pd.Series | None = None, slots: int = SLOTS,
             cost_bps: float = COST_BPS, start=None, market_close: pd.Series | None = None,
             breakout_days: int = BREAKOUT_DAYS, adx_min: float = ADX_MIN, members: pd.DataFrame | None = None,
             liquidate: bool = False) -> dict:
    """Replay Tech Breakout Rider on a panel of tech stocks {"Open"|"High"|"Low"|"Close": dates x tickers}.
    One fixed set of settings over the whole span is an in-sample test: use ``walk_forward`` for
    out-of-sample results."""
    C = ohlcv["Close"].astype(float).sort_index().dropna(axis=1, how="all")
    dates = C.index
    panel = {f: ohlcv[f].reindex(index=dates, columns=C.columns).astype(float) for f in ("Open", "High", "Low")}
    panel["Close"] = C
    q = walkforward.carry_forward(qqq_close.astype(float).reindex(dates.union(qqq_close.index))).reindex(dates)
    gate = qqq_gate(q).fillna(False).to_numpy(bool)
    rf = swing_engine.daily_cash(dates, tbill_yields)
    t0 = STRENGTH_DAYS + 20
    if start is not None:
        t0 = max(t0, int(dates.searchsorted(pd.Timestamp(start))))
    if len(dates) - t0 < 30:
        raise ValueError("Not enough price history for a Breakout Rider backtest (needs about a year).")
    sig = signal_frames(panel, breakout_days, adx_min, members)
    run = swing_engine.run(panel, sig["buy"], sig["score"], gate, rf, exit_signal=sig["exit"], limit=sig["limit"],
                           max_days=MAX_DAYS, slots=slots, cost_bps=cost_bps, t0=t0, exit_label="21 EMA under 50 EMA",
                           liquidate=liquidate)
    equity, tr = run["equity"], run["trades"]
    rf_s = pd.Series(rf[t0:], index=dates[t0:])
    qr = q.pct_change(fill_method=None).fillna(0.0).iloc[t0:]
    qr.iloc[0] = 0.0
    out = {"equity": equity, "returns": equity.pct_change().fillna(0.0), "exposure": run["exposure"], "trades": tr,
           "qqq_equity": (1 + qr).cumprod(),
           "stats": swing_engine.stats(equity, rf_s, tr), "qqq_stats": swing_engine.stats((1 + qr).cumprod(), rf_s),
           "symbols": C.shape[1]}
    if market_close is not None and len(market_close):
        m = walkforward.carry_forward(market_close.astype(float).reindex(dates.union(market_close.index))).reindex(dates)
        mr = m.pct_change(fill_method=None).fillna(0.0).iloc[t0:]
        mr.iloc[0] = 0.0
        out["spy_equity"] = (1 + mr).cumprod()
        out["spy_stats"] = swing_engine.stats(out["spy_equity"], rf_s)
    return out


BREAKOUT_GRID = (20, 40)
ADX_GRID = (15.0, 20.0, 25.0)


def walk_forward(ohlcv: dict, qqq_close: pd.Series, tbill_yields: pd.Series | None = None, slots: int = SLOTS,
                 cost_bps: float = COST_BPS, market_close: pd.Series | None = None,
                 members: pd.DataFrame | None = None, progress=None) -> dict:
    """Breakout Rider graded out of sample: each year's breakout length and ADX floor are picked on the three
    years before it (see ``walkforward``), then traded on that year only. The purge gap is the 90-day
    holding limit."""
    points = walkforward.grid(**{"Breakout days": BREAKOUT_GRID, "ADX above": ADX_GRID})
    data = {"ohlcv": ohlcv, "qqq": qqq_close, "tbill": tbill_yields, "members": members}

    def evaluate(d, p, start):
        res = backtest(d["ohlcv"], d["qqq"], d["tbill"], slots, cost_bps, start=start,
                       breakout_days=int(p["Breakout days"]), adx_min=p["ADX above"], members=d["members"],
                       liquidate=True)
        return {"returns": res["returns"], "trades": res["trades"]}

    dates = ohlcv["Close"].sort_index().index
    rf = pd.Series(swing_engine.daily_cash(dates, tbill_yields), index=dates)
    wf = walkforward.run(evaluate, data, points,
                         walkforward.folds(dates, purge=MAX_DAYS, first=STRENGTH_DAYS + 20), rf, progress)
    r = wf["returns"]
    rf_s = rf.reindex(r.index).fillna(0.0)
    for name, px in (("qqq", qqq_close), ("spy", market_close)):
        if px is None or not len(px):
            continue
        br = px.astype(float).pct_change(fill_method=None).reindex(r.index).fillna(0.0)
        br.iloc[0] = 0.0
        wf[f"{name}_equity"] = (1 + br).cumprod()
        wf[f"{name}_stats"] = swing_engine.stats(wf[f"{name}_equity"], rf_s)
    wf["stats"] = swing_engine.stats(wf["equity"], rf_s, wf["trades"] if len(wf["trades"]) else None)
    return wf
