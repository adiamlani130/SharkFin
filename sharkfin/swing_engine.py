"""The portfolio engine behind SharkFin's swing systems (Leader Dip Plus and Tech Breakout Rider).

A fixed number of equal slots. Signals are read at the close of day t and act on day t+1:

  1. exits decided yesterday sell at today's open
  2. limit entries placed yesterday fill if today's low reaches the limit (at the open when it opens below),
     strongest signal first while slots are free; with no limit the order fills at the open
  3. profit targets: a position sells at its target the first day the high reaches it (at the open when it
     opens above it on a later day)
  4. mark to market at the close
  5. exit signals at today's close (or the holding limit) sell at tomorrow's open
  6. new orders for tomorrow, only while the market gate is on

Each new trade gets 1/slots of the account (capped by the cash on hand), idle cash earns ``cash_returns``,
and ``cost_bps`` is charged on every buy and every sell. Nothing uses data after the bar it acts on.
This mirrors the simulator used in SharkFin's Oct 2026 research, so the app replays the same rules.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def run(ohlc: dict, buy: pd.DataFrame, score: pd.DataFrame, gate: np.ndarray, cash_returns: np.ndarray, *,
        exit_signal: pd.DataFrame | None = None, limit: pd.DataFrame | None = None, target: pd.DataFrame | None = None,
        max_days: int = 10, slots: int = 10, cost_bps: float = 10.0, t0: int = 0, exit_label: str = "Exit signal",
        exit_labels: pd.DataFrame | None = None) -> dict:
    """Replay the rules. ``ohlc`` holds "Open", "High", "Low", "Close" frames (dates x tickers) on the same grid
    as ``buy``. ``exit_labels`` (optional, strings) names the exit signal per cell for the trade list."""
    C = ohlc["Close"]
    dates, syms = C.index, list(C.columns)
    O, H, L = (ohlc[f].reindex(index=dates, columns=syms).astype(float).to_numpy() for f in ("Open", "High", "Low"))
    Cn = C.astype(float).to_numpy()
    b = buy.reindex(index=dates, columns=syms).fillna(False).to_numpy(bool)
    sc = score.reindex(index=dates, columns=syms).astype(float).to_numpy()
    ex = (exit_signal.reindex(index=dates, columns=syms).fillna(False).to_numpy(bool) if exit_signal is not None
          else np.zeros_like(b))
    lim = limit.reindex(index=dates, columns=syms).astype(float).to_numpy() if limit is not None else None
    tgt = target.reindex(index=dates, columns=syms).astype(float).to_numpy() if target is not None else None
    lab = exit_labels.reindex(index=dates, columns=syms).to_numpy(object) if exit_labels is not None else None
    gate = np.asarray(gate, bool)
    cash_r = np.asarray(cash_returns, float)
    cost = cost_bps / 1e4
    T, N, K = len(dates), len(syms), int(slots)

    slot_j = np.full(K, -1)
    shares, entry_px, entry_t = np.zeros(K), np.zeros(K), np.zeros(K, int)
    last_c, tgt_px = np.zeros(K), np.full(K, np.nan)
    exit_next, exit_why = np.zeros(K, bool), [""] * K
    held = np.zeros(N, bool)
    pend: list[tuple[int, float, float]] = []
    cash_bal, last_eq = 1.0, 1.0
    eq, expo = np.full(T, np.nan), np.zeros(T)
    trades = []

    def close_slot(k, t, px, why):
        nonlocal cash_bal
        j = slot_j[k]
        cash_bal += shares[k] * px * (1 - cost)
        trades.append((syms[j], dates[entry_t[k] - 1], dates[entry_t[k]], entry_px[k], dates[t], px,
                       px * (1 - cost) / (entry_px[k] * (1 + cost)) - 1, t - entry_t[k], why))
        held[j], slot_j[k], shares[k], exit_next[k] = False, -1, 0.0, False

    for t in range(t0, T):
        cash_bal *= 1 + cash_r[t]
        # 1) exits decided yesterday, at today's open
        for k in range(K):
            if slot_j[k] >= 0 and exit_next[k]:
                j = slot_j[k]
                close_slot(k, t, O[t, j] if np.isfinite(O[t, j]) and O[t, j] > 0 else last_c[k], exit_why[k])
        # 2) entries placed yesterday
        for j, lv, tv in pend:
            free = np.flatnonzero(slot_j < 0)
            if not len(free):
                break
            o, lo = O[t, j], L[t, j]
            if not (np.isfinite(o) and o > 0 and np.isfinite(lo)):
                continue
            if np.isfinite(lv):
                if lo > lv:
                    continue
                px = min(o, lv)
            else:
                px = o
            alloc = min(last_eq / K, cash_bal)
            if alloc <= 1e-9:
                break
            k = free[0]
            slot_j[k], shares[k], entry_px[k], entry_t[k], last_c[k], tgt_px[k] = j, alloc / (px * (1 + cost)), px, t, px, tv
            cash_bal -= alloc
            held[j] = True
        pend = []
        # 3) profit targets during the day
        for k in range(K):
            j = slot_j[k]
            if j < 0 or not np.isfinite(tgt_px[k]):
                continue
            o, hi = O[t, j], H[t, j]
            if t > entry_t[k] and np.isfinite(o) and o >= tgt_px[k]:
                close_slot(k, t, o, "Profit target")
            elif np.isfinite(hi) and hi >= tgt_px[k]:
                close_slot(k, t, tgt_px[k], "Profit target")
        # 4) mark to market
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
        # 5) exits for tomorrow's open
        n_free = int((slot_j < 0).sum())
        for k in range(K):
            j = slot_j[k]
            if j < 0:
                continue
            why = ((lab[t, j] if lab is not None and isinstance(lab[t, j], str) else exit_label) if ex[t, j]
                   else f"{max_days} days" if t - entry_t[k] + 1 >= max_days
                   else "No more data" if not np.isfinite(Cn[t + 1, j]) else "")
            if why:
                exit_next[k], exit_why[k] = True, why
                n_free += 1
        # 6) new orders for tomorrow, strongest first
        if n_free and gate[t]:
            cand = np.flatnonzero(b[t] & ~held & np.isfinite(sc[t]))
            if len(cand):
                order = cand[np.argsort(-sc[t, cand], kind="stable")][:n_free]
                pend = [(int(j), float(lim[t, j]) if lim is not None else np.nan,
                         float(tgt[t, j]) if tgt is not None else np.nan) for j in order]

    for k in range(K):  # still open at the end
        j = slot_j[k]
        if j >= 0:
            trades.append((syms[j], dates[entry_t[k] - 1], dates[entry_t[k]], entry_px[k], pd.NaT, last_c[k],
                           last_c[k] / (entry_px[k] * (1 + cost)) - 1, T - 1 - entry_t[k], "Open"))
    cols = ["Symbol", "Signal date", "Bought", "Buy price", "Sold", "Sell price", "Return", "Days held", "Why it sold"]
    tr = pd.DataFrame(trades, columns=cols).sort_values("Bought", kind="stable").reset_index(drop=True)
    return {"equity": pd.Series(eq[t0:], index=dates[t0:]), "exposure": pd.Series(expo[t0:], index=dates[t0:]),
            "trades": tr}


def daily_cash(dates: pd.DatetimeIndex, tbill_yields: pd.Series | None, fallback: float = 0.04) -> np.ndarray:
    """Daily T-bill return for each date (yesterday's 3-month yield, compounded daily)."""
    y = pd.Series(fallback, index=dates)
    if tbill_yields is not None and len(tbill_yields.dropna()):
        t = tbill_yields.dropna().astype(float)
        t.index = pd.DatetimeIndex(t.index)
        y = t.reindex(dates.union(t.index)).ffill().reindex(dates).bfill().fillna(fallback)
    return ((1 + y.shift(1).fillna(y.iloc[0])) ** (1 / 252) - 1).to_numpy()


def stats(equity: pd.Series, rf_daily: pd.Series | None = None, trades: pd.DataFrame | None = None) -> dict:
    """Return per year, Sharpe (after T-bills), worst drop and, with a trade list, the trade statistics."""
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
        wins, losses = done.loc[done["Return"] > 0, "Return"], done.loc[done["Return"] <= 0, "Return"]
        out.update({"Trades": int(len(done)), "Trades per year": len(done) / years if years else np.nan,
                    "Win rate": float((done["Return"] > 0).mean()) if len(done) else np.nan,
                    "Avg trade": float(done["Return"].mean()) if len(done) else np.nan,
                    "Avg win": float(wins.mean()) if len(wins) else np.nan,
                    "Avg loss": float(losses.mean()) if len(losses) else np.nan,
                    "Payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) and losses.mean() < 0 else np.nan,
                    "Profit factor": float(wins.sum() / -losses.sum()) if len(losses) and losses.sum() < 0 else np.nan,
                    "Avg days held": float(done["Days held"].mean()) if len(done) else np.nan})
    return out


def panel_atr(ohlc: dict, period: int = 14) -> pd.DataFrame:
    """Wilder ATR for every column of an OHLC panel."""
    c, h, lo = (ohlc[f].astype(float) for f in ("Close", "High", "Low"))
    pc = c.shift(1)
    tr = np.fmax(h - lo, np.fmax((h - pc).abs(), (lo - pc).abs()))
    tr = tr.where(h.notna() & lo.notna())
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def panel_adx(ohlc: dict, period: int = 14) -> pd.DataFrame:
    """Wilder ADX for every column of an OHLC panel."""
    c, h, lo = (ohlc[f].astype(float) for f in ("Close", "High", "Low"))
    up, down = h.diff(), -lo.diff()
    pdm = up.where((up > down) & (up > 0), 0.0).where(up.notna())
    mdm = down.where((down > up) & (down > 0), 0.0).where(down.notna())
    w = lambda x: x.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    tr = panel_atr(ohlc, period)
    pdi, mdi = 100 * w(pdm) / tr, 100 * w(mdm) / tr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return w(dx)
