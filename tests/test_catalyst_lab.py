"""Catalyst lab and the Nov 2026 ranking fixes: falling-knife guard, cyclical value, the Broken stage, and no look-ahead
in breadth, earnings events and Kalshi odds."""

import numpy as np
import pandas as pd

from sharkfin import catalyst_lab as cl
from sharkfin import factors, speculation


def panel(n=400, k=30, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=n)
    cols = [f"S{i}" for i in range(k)] + ["SPY", "^VIX"]
    c = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.02, (n, len(cols))), axis=0)), index=idx, columns=cols)
    c["^VIX"] = 20 + rng.normal(0, 2, n)
    o = c.shift(1).fillna(c) * (1 + rng.normal(0, 0.003, c.shape))
    hi, lo = np.maximum(o, c) * 1.01, np.minimum(o, c) * 0.99
    v = pd.DataFrame(rng.integers(1e5, 1e6, c.shape).astype(float), index=idx, columns=cols)
    return {"Open": o, "High": hi, "Low": lo, "Close": c, "Volume": v}


def test_breadth_counts_members_only_and_ignores_later_days():
    px = panel()
    c = px["Close"].iloc[:, :30]
    mem = pd.DataFrame(True, index=c.index, columns=c.columns)
    mem.iloc[:, 20:] = False
    full = cl.breadth(c, px["Volume"].iloc[:, :30], mem, min_n=5)
    cut = cl.breadth(c.iloc[:300], px["Volume"].iloc[:300, :30], mem.iloc[:300], min_n=5)
    pd.testing.assert_frame_equal(full.loc[cut.index], cut)
    assert full["n"].max() <= 20


def test_breadth_flags_a_washout_day():
    px = panel()
    c = px["Close"].iloc[:, :30].copy()
    c.iloc[200:] *= 0.95      # every stock falls 5% on day 200
    mem = pd.DataFrame(True, index=c.index, columns=c.columns)
    b = cl.breadth(c, px["Volume"].iloc[:, :30], mem, min_n=5)
    assert b["adv"].iloc[199] < 0.05 and b["upvol"].iloc[199] < 0.05


def test_first_in_takes_one_entry_per_episode():
    s = pd.Series([0, 1, 1, 0, 1] + [0] * 10 + [1], dtype=bool)
    assert list(cl.first_in(s, gap=10)[lambda x: x].index) == [1, 15]


def test_after_close_report_reacts_next_session_and_features_ignore_later_prices():
    px = panel()
    c = px["Close"]
    day = c.index[300]
    ed = pd.DataFrame({"EPS Estimate": [1.0, 1.0], "Reported EPS": [1.1, 1.3], "Surprise(%)": [10.0, 30.0]},
                      index=[c.index[240] + pd.Timedelta(hours=8), day + pd.Timedelta(hours=16, minutes=5)])
    mem = pd.DataFrame(True, index=c.index, columns=c.columns)
    ev = cl.earnings_events(px, {"S1": ed}, mem)
    row = ev[ev["surprise"] == 30.0].iloc[0]
    assert row["date"] == c.index[301] and row["timing"] == "after close"
    assert abs(row["react"] - (c["S1"].iloc[301] / c["S1"].iloc[300] - 1)) < 1e-12
    cut = {k: v.iloc[:305] for k, v in px.items()}
    ev2 = cl.earnings_events(cut, {"S1": ed}, mem.iloc[:305])
    known = ["streak", "prev_sur", "pre1m", "pre3m", "vs200", "off_hi", "gap", "react", "volx"]
    r2 = ev2[ev2["surprise"] == 30.0].iloc[0]
    assert np.allclose(row[known].astype(float), r2[known].astype(float), equal_nan=True)
    assert row["streak"] == 1


def test_falling_knife_gets_no_reversal_credit():
    px = panel(k=30)["Close"].iloc[:, :30]
    px.iloc[-21:, 0] = px.iloc[-22, 0] * np.linspace(0.98, 0.6, 21)   # -40% in a month, under the 50-day
    pf = factors.price_factor_frame(px)
    off = factors.composite_scores(pf, theme_weights={"Reversal": 1.0}, knife_guard=False)
    on = factors.composite_scores(pf, theme_weights={"Reversal": 1.0})
    assert off.loc["S0", "Reversal"] > 1 and on.loc["S0", "Reversal"] <= 0
    assert bool(on.loc["S0", "Falling knife"]) and on["Falling knife"].sum() >= 1


def test_cyclical_stocks_are_valued_on_through_cycle_earnings():
    idx = [f"S{i}" for i in range(8)]
    fund = pd.DataFrame({"forwardPE": [3.0] + [15.0] * 7, "trailingPE": [6.0] + [16.0] * 7,
                         "industry": ["Semiconductors"] + ["Software"] * 7, "sector": "Technology"}, index=idx)
    ff = factors.fundamental_factor_frame(fund)
    price = pd.DataFrame({"price": 100.0, "mom_12_1": np.linspace(0, 1, 8)}, index=idx)
    ef = pd.DataFrame({"eps_norm": [2.0] + [6.0] * 7}, index=idx)   # through-cycle EPS 2 -> yield 2% for S0
    on = factors.composite_scores(price, ff, theme_weights={"Value": 1.0}, earn_f=ef)
    off = factors.composite_scores(price, ff, theme_weights={"Value": 1.0}, earn_f=ef, knife_guard=False)
    assert abs(on.loc["S0", "earnings_yield"] - 0.02) < 1e-9 and abs(off.loc["S0", "earnings_yield"] - 1 / 3) < 1e-9
    assert on.loc["S0", "Value"] < off.loc["S0", "Value"]
    assert on.loc["S1", "earnings_yield"] == off.loc["S1", "earnings_yield"]   # non-cyclicals untouched


def test_earnings_frame_reports_five_year_average_eps():
    dates = pd.date_range("2019-01-15", periods=24, freq="QS")
    ed = pd.DataFrame({"Reported EPS": np.arange(24, dtype=float), "EPS Estimate": 1.0, "Surprise(%)": 5.0}, index=dates)
    ef = factors.earnings_factor_frame({"X": ed}, asof=dates[-1] + pd.Timedelta(days=1))
    last5y = ed["Reported EPS"][ed.index > dates[-1] - pd.DateOffset(years=5)]
    assert abs(ef.loc["X", "eps_norm"] - last5y.mean() * 4) < 1e-9


def test_broken_stage():
    assert speculation.stage({"vs200": -0.5, "12m": -0.8, "off_high": -0.83, "rs6m": -0.5}) == "Broken"
    assert speculation.stage({"vs200": -0.2, "12m": -0.3, "off_high": -0.4, "rs6m": -0.1}) == "Quiet"
    assert "Broken" in speculation.STAGES and "Broken" in speculation.STAGE_ORDER


def test_stage_panel_matches_the_radar():
    px = panel(n=600)["Close"]
    st, off = cl.stage_panel(px.iloc[:, :5], px["SPY"])
    for i in (300, 450, 599):
        for s in px.columns[:5]:
            row = speculation.stats(px[s].iloc[: i + 1], px["SPY"].iloc[: i + 1])
            want = row["stage"] if row["stage"] != "Broken" else None
            if want:
                assert st[s].iloc[i] == want, (s, i)


def test_kalshi_uses_the_next_meeting_and_market_codes():
    day = pd.Timestamp("2026-09-01")
    ts = int(day.timestamp())

    def mk(t, close, p):
        return {"m": {"ticker": t, "event_ticker": t.rsplit("-", 1)[0], "yes_sub_title": "", "close_time": close},
                "c": [{"ts": ts, "close": p}]}
    k = {"KXFEDDECISION": [mk("KXFEDDECISION-26SEP-C25", "2026-09-16T18:00:00Z", "0.30"),
                           mk("KXFEDDECISION-26SEP-H25", "2026-09-16T18:00:00Z", "0.10"),
                           mk("KXFEDDECISION-26SEP-H0", "2026-09-16T18:00:00Z", "0.60"),
                           mk("KXFEDDECISION-26OCT-C25", "2026-10-28T18:00:00Z", "0.90")]}
    o = cl.kalshi_daily(k)
    assert abs(o.loc[day, "fed_cut"] - 0.30) < 1e-9 and abs(o.loc[day, "fed_hike"] - 0.10) < 1e-9
