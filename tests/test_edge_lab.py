"""Edge lab: no look-ahead in the point-in-time sector, the theme signals, the earnings frames, and the new Breakout
Rider ``buy_ok`` filter."""

import numpy as np
import pandas as pd

from sharkfin import breakout_rider as brk
from sharkfin import edge_lab as el


def closes(n=700, k=12, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2018-01-01", periods=n)
    cols = [f"T{i}" for i in range(k)]
    return pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, (n, k)), axis=0)), index=idx, columns=cols)


def test_pit_sector_uses_past_data_only():
    c = closes()
    spy = c.mean(axis=1)
    etf = c.iloc[:, :3].rename(columns=lambda x: "E" + x)
    stocks = c.iloc[:, 3:]
    full = el.pit_sector(stocks, etf, spy)
    cut = el.pit_sector(stocks.iloc[:500], etf.iloc[:500], spy.iloc[:500])
    pd.testing.assert_frame_equal(full.iloc[:500], cut, check_freq=False)


def test_pit_sector_finds_the_etf_a_stock_tracks():
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2018-01-01", periods=400)
    mkt = rng.normal(0, 0.01, 400)
    a, b = rng.normal(0, 0.01, 400), rng.normal(0, 0.01, 400)
    lvl = lambda r: pd.Series(100 * np.exp(np.cumsum(r)), index=idx)
    etf = pd.DataFrame({"EA": lvl(mkt + a), "EB": lvl(mkt + b)})
    stock = pd.DataFrame({"X": lvl(mkt + a + rng.normal(0, 0.003, 400))})
    sec = el.pit_sector(stock, etf, lvl(mkt))
    assert sec["X"].dropna().eq("EA").all()


def test_theme_signals_ignore_later_days():
    c = closes()
    v = pd.DataFrame(1e6, index=c.index, columns=c.columns)
    spy = c.mean(axis=1)
    full = el.theme_signals(c, v, spy, el.stage_frame(c, spy))
    cut = el.theme_signals(c.iloc[:550], v.iloc[:550], spy.iloc[:550], el.stage_frame(c.iloc[:550], spy.iloc[:550]))
    for k in full:
        pd.testing.assert_frame_equal(full[k].iloc[:550].fillna(False).astype(bool),
                                      cut[k].fillna(False).astype(bool), check_freq=False)


def test_earnings_frames_count_from_the_reaction_day():
    idx = pd.bdate_range("2024-01-01", periods=60)
    ev = pd.DataFrame({"sym": ["A", "A"], "date": [idx[10], idx[40]], "surprise": [5.0, -3.0], "yoy": [0.2, 0.1],
                       "est_yoy": [0.1, -0.1]})
    f = el.earnings_frames(ev, idx, pd.Index(["A", "B"]))
    assert np.isnan(f["sur"]["A"].iloc[9]) and f["sur"]["A"].iloc[10] == 5.0 and f["sur"]["A"].iloc[39] == 5.0
    assert f["sur"]["A"].iloc[40] == -3.0
    assert f["since"]["A"].iloc[15] == 5 and f["until"]["A"].iloc[35] == 5
    assert f["sur"]["B"].isna().all()


def test_breakout_buy_ok_only_removes_trades():
    c = closes(k=20)
    hi, lo = c * 1.01, c * 0.99
    px = {"Open": c.shift(1).fillna(c), "High": hi, "Low": lo, "Close": c}
    q = c.mean(axis=1)
    base = brk.backtest(px, q, start=c.index[200])
    none = pd.DataFrame(False, index=c.index, columns=c.columns)
    blocked = brk.backtest(px, q, start=c.index[200], buy_ok=none)
    assert len(blocked["trades"]) == 0
    allow = brk.backtest(px, q, start=c.index[200], buy_ok=~none)
    pd.testing.assert_series_equal(allow["equity"], base["equity"])
