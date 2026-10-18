"""Guards against look-ahead: no back-filling, walk-forward windows that never see later data, and engine
rules that only use bars up to the one they act on."""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sharkfin import builder, data, day_night, factors, leader_dip, swing_engine, walkforward
from tests import fakes

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [p for d in ("sharkfin", "app_pages") for p in (ROOT / d).rglob("*.py")] + [ROOT / "main.py"]

# Every negative shift reads a later row. Each allowed one books a trade's realized outcome, never a decision.
ALLOWED_NEGATIVE_SHIFTS = {
    "sharkfin/day_night.py": 3,     # night leg: next session's open and date (the trade's exit), next row's date
    "sharkfin/forecasting.py": 1,   # training target, purged so it ends before the forecast origin
}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    fakes.install(monkeypatch)
    data._cache.clear()


def test_nothing_is_back_filled():
    pattern = re.compile(r"bfill|backfill|fillna\(\s*method\s*=\s*['\"](?:bfill|backfill)|limit_direction")
    hits = [f"{p.relative_to(ROOT)}:{i}" for p in SOURCES for i, line in enumerate(p.read_text().splitlines(), 1)
            if pattern.search(line)]
    assert not hits, f"Missing data may only be filled from earlier records: {hits}"


def test_negative_shifts_are_only_trade_outcomes():
    for p in SOURCES:
        n = len(re.findall(r"\.shift\(\s*-", p.read_text()))
        rel = str(p.relative_to(ROOT))
        assert n == ALLOWED_NEGATIVE_SHIFTS.get(rel, 0), f"{rel} reads later rows {n} times; review and allow-list it"


def test_folds_slide_and_never_overlap():
    dates = pd.bdate_range("2010-01-01", periods=2600)
    fl = walkforward.folds(dates, purge=10, first=200)
    assert len(fl) >= 6
    for a, b in zip(fl, fl[1:]):
        assert a.test_end < b.test_start and b.train_start > a.train_start  # it slides, it doesn't expand
    for f in fl:
        gap = dates.get_loc(f.test_start) - dates.get_loc(f.train_end) - 1
        assert gap == 10 and f.train_end < f.test_start
        assert dates.get_loc(f.train_end) - dates.get_loc(f.train_start) + 1 == walkforward.TRAIN_YEARS * 252


def test_walk_forward_never_hands_later_rows_to_a_run():
    dates = pd.bdate_range("2012-01-02", periods=1600)
    rng = np.random.default_rng(0)
    px = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(dates)))), index=dates)
    seen = []

    def evaluate(d, p, start):
        seen.append((start, d["px"].index.max()))
        r = d["px"].pct_change().fillna(0.0) * p["x"]
        return {"returns": r.loc[start:]}

    fl = walkforward.folds(dates)
    wf = walkforward.run(evaluate, {"px": px}, walkforward.grid(x=[0.5, 1.0]), fl)
    ends = {f.train_end for f in fl} | {f.test_end for f in fl}
    assert all(last in ends for _, last in seen)  # each run's data stopped at its own window's end
    assert wf["returns"].index.min() == fl[0].test_start  # only test windows are reported
    assert not wf["returns"].index.duplicated().any()


def test_pick_prefers_a_stable_region_over_a_lone_spike():
    pts = walkforward.grid(a=[1, 2, 3, 4, 5])
    scores = [0.2, 0.25, 0.3, 2.0, -1.5]  # 4 is a spike next to a disaster
    assert pts[walkforward.pick(pts, scores)]["a"] == 3


def test_cash_before_the_first_yield_is_not_back_filled():
    dates = pd.bdate_range("2020-01-01", periods=30)
    y = pd.Series(0.05, index=dates[10:])
    r = swing_engine.daily_cash(dates, y, fallback=0.01)
    assert np.allclose(r[:11], (1.01) ** (1 / 252) - 1)  # day 10 uses day 9's (missing) yield: fallback
    assert np.allclose(r[11:], (1.05) ** (1 / 252) - 1)


def _panel(rows):
    idx = pd.bdate_range("2021-01-04", periods=len(rows))
    return {f: pd.DataFrame({"X": [r[i] for r in rows]}, index=idx) for i, f in enumerate(("Open", "High", "Low", "Close"))}


def test_limit_fill_and_target_on_the_same_bar_do_not_both_count():
    # day 1 signal; day 2 opens above the limit, dips to fill it, and also spikes through the target
    ohlc = _panel([(100, 101, 99, 100), (100, 101, 99, 100), (99, 120, 90, 100), (100, 101, 99, 100), (100, 101, 99, 100)])
    idx = ohlc["Close"].index
    buy = pd.DataFrame({"X": [False, True, False, False, False]}, index=idx)
    res = swing_engine.run(ohlc, buy, buy.astype(float), np.ones(5, bool), np.zeros(5),
                           limit=pd.DataFrame({"X": 95.0}, index=idx), target=pd.DataFrame({"X": 110.0}, index=idx),
                           max_days=10, slots=1, cost_bps=0)
    tr = res["trades"]
    assert len(tr) == 1 and tr.iloc[0]["Why it sold"] != "Profit target"


def test_a_stock_that_stops_trading_sells_when_that_is_known():
    rows = [(100, 101, 99, 100)] * 3 + [(np.nan,) * 4] * 2
    ohlc = _panel(rows)
    idx = ohlc["Close"].index
    buy = pd.DataFrame({"X": [True, False, False, False, False]}, index=idx)
    tr = swing_engine.run(ohlc, buy, buy.astype(float), np.ones(5, bool), np.zeros(5), max_days=10, slots=1,
                          cost_bps=0)["trades"]
    assert tr.iloc[0]["Why it sold"] == "No more data" and tr.iloc[0]["Sold"] == idx[3]  # found out on day 3, not day 2


def test_night_leg_ignores_everything_after_1530():
    bars = fakes.intraday_bars("TQQQ", 60)
    M = day_night.session_matrix(bars)
    base = day_night.decision_location(M)
    late = bars.copy()
    after = late.index.hour * 60 + late.index.minute >= 15 * 60 + 30
    late.loc[after, ["h", "l", "c"]] *= np.where(late.loc[after, "c"].to_numpy()[:, None] > 0, 0.5, 1)
    assert day_night.decision_location(day_night.session_matrix(late)).equals(base)


def test_members_only_trade_while_in_the_index():
    ohlc = fakes.download_ohlcv(fakes.SYMS)
    c = ohlc["Close"]
    mem = data.sp500_members(c.index, c.columns)
    late = fakes.SYMS[-1]
    assert not mem.loc[:"2023-05-31", late].any() and mem.loc["2023-06-01":, late].all()
    sig = leader_dip.signal_frames(c, members=mem)
    assert not sig["buy"].loc[:"2023-05-31", late].any()
    assert sig["rank"].loc[:"2023-05-31", late].isna().all()  # not ranked against the index before it joined


def test_every_strategy_walks_forward():
    ohlc = fakes.download_ohlcv(fakes.SYMS)
    spy = fakes.history("SPY")["Close"]
    tb = pd.Series(0.04, index=spy.index)
    mem = data.sp500_members(ohlc["Close"].index, ohlc["Close"].columns)
    ld = leader_dip.walk_forward(ohlc, spy, tbill_yields=tb, members=mem)
    assert len(ld["folds"]) and ld["equity"].index.min() > ohlc["Close"].index[walkforward.TRAIN_YEARS * 252]
    lab = builder.walk_forward(fakes.history("AAPL"), builder.template("RSI dip in an uptrend"), 5, 0.04, spy)
    assert len(lab["folds"]) and lab["knobs"]
    fx = factors.walk_forward(ohlc["Close"], members=mem)
    assert len(fx["folds"]) and np.isfinite(fx["ic_mean"])


def test_factor_replay_keeps_a_holding_that_stops_trading_in_the_average():
    # Every stock gains 0.1% a day after day 280. The strongest stock (a big earlier run puts it in the top
    # fifth) stops trading on day 290. Its money should sit in cash, not move into the other holdings.
    dates = pd.bdate_range("2018-01-01", periods=400)
    rng = np.random.default_rng(1)
    r = np.full((400, 30), 0.001)
    r[:280] += rng.normal(0, 0.01, (280, 30))
    r[:280, -1] += 0.004
    px = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=dates, columns=[f"S{i}" for i in range(30)])
    px.iloc[290:, -1] = np.nan
    res = factors.backtest_price_composite(px, rebalance=21, quantile=0.2, cost_bps=0)
    k = int(30 * 0.2)
    after = res["strategy"].loc[dates[296]:dates[300]]  # same month: the rebalance before was day 273 + 21 = 294
    assert len(after) and np.allclose(after, 0.001 * (k - 1) / k), after
