"""NQ strategy lab: every strategy must give the same past whether or not the future exists, and day trades
must decide each bar from bars up to it only."""

import numpy as np
import pandas as pd
import pytest

from sharkfin import nq_gex_plays, nq_lab, nq_regimes, walkforward


def _market(n_days=700, seed=0):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2016-01-04", periods=n_days)
    c = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, n_days)))
    o = c * (1 + rng.normal(0, 0.004, n_days))
    h, l = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.005, n_days))), np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.005, n_days)))
    px = pd.DataFrame({"o": o, "h": h, "l": l, "c": c, "raw": 1.05}, index=days)
    vix = pd.Series(np.clip(18 + np.cumsum(rng.normal(0, 1, n_days)) * 0.3, 9, 60), index=days)
    d = {"px": px, "vix": vix, "vix3m": vix * (1 + rng.normal(0.05, 0.05, n_days)),
         "vix9d": vix * (1 + rng.normal(-0.03, 0.08, n_days)), "rf": pd.Series(0.0001, index=days),
         "gex": pd.Series(rng.normal(2e9, 2e9, n_days), index=days)}
    d["gex_pct"] = nq_lab.trailing_pct(d["gex"])
    # 5-minute bars that wander from each day's open to its close
    steps = rng.normal(0, 0.0012, (n_days, nq_lab.BARS))
    path = o[:, None] * np.exp(np.cumsum(steps, axis=1))
    path[:, -1] = c
    bo = np.concatenate([o[:, None], path[:, :-1]], axis=1)
    wig = np.abs(rng.normal(0, 0.0008, path.shape))
    frame = lambda a: pd.DataFrame(a, index=days, columns=range(nq_lab.BARS))
    d.update({"io": frame(bo), "ic": frame(path), "ih": frame(np.maximum(bo, path) * (1 + wig)),
              "il": frame(np.minimum(bo, path) * (1 - wig)), "iv": frame(rng.integers(1e4, 1e5, path.shape).astype(float)),
              "ivw": frame((bo + path) / 2)})
    return d


def _settings(st):
    pts = st.points
    return [pts[0], pts[len(pts) // 2], pts[-1]] if len(pts) > 2 else pts


@pytest.mark.parametrize("st", nq_lab.CATALOGUE + nq_regimes.catalogue() + nq_gex_plays.catalogue(),
                         ids=lambda s: s.name)
def test_cutting_off_the_future_changes_no_past_result(st):
    d = _market()
    start = d["px"].index[300]
    for end in (d["px"].index[450], d["px"].index[600]):
        for p in _settings(st):
            full = st.evaluate(d, p, start)["returns"]
            short = st.evaluate(walkforward.cut(d, end), p, start)["returns"]
            pd.testing.assert_series_equal(full.loc[:end], short, check_names=False, rtol=1e-10, atol=1e-12)
            if hasattr(st.evaluate, "signal"):  # the positions themselves, down to the decision on ``end``
                a, b = _signal(st.evaluate, d, p), _signal(st.evaluate, walkforward.cut(d, end), p)
                pd.testing.assert_series_equal(a.loc[:end], b, check_names=False, rtol=1e-10, atol=1e-12)


def _signal(evaluate, d, p):
    return evaluate.signal(d, p).reindex(d["px"].index).fillna(0.0).astype(float)


def test_the_check_catches_a_strategy_that_peeks():
    d = _market()

    @nq_lab._sw
    def peeks(dd, p):  # long on days before the market rises: tomorrow's close, known today
        c = dd["px"]["c"]
        return (c.pct_change().iloc[1:].reset_index(drop=True).reindex(range(len(c))).set_axis(c.index) > 0).astype(float)

    end = d["px"].index[450]
    full, short = _signal(peeks, d, {}), _signal(peeks, walkforward.cut(d, end), {})
    assert not np.allclose(full.loc[:end].to_numpy(), short.to_numpy())  # the decision on ``end`` differs


@pytest.mark.parametrize("st", [s for s in nq_lab.CATALOGUE if s.kind == "day"], ids=lambda s: s.name)
def test_day_trades_decide_each_bar_from_earlier_bars_only(st):
    """Scramble every bar from ``m`` on, on every third day: no decision those days made at the close of an
    earlier bar may change. (The day after a scrambled one is left out: its prior-day levels moved.)"""
    d = _market(400, seed=3)
    m = 40
    rng = np.random.default_rng(9)
    hit = np.arange(len(d["px"])) % 3 == 1
    e = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in d.items()}
    for k in ("io", "ih", "il", "ic", "ivw"):
        e[k].iloc[hit, m:] *= np.exp(rng.normal(0, 0.01, e[k].iloc[hit, m:].shape))
    e["ih"] = np.maximum(e["ih"], np.maximum(e["io"], e["ic"]))
    e["il"] = np.minimum(e["il"], np.minimum(e["io"], e["ic"]))
    start = d["px"].index[260]
    for p in _settings(st):
        runs = []
        for data in (d, e):
            nq_lab.TRACE = []
            try:
                st.evaluate(data, p, start)
            finally:
                runs.append(nq_lab.TRACE)
                nq_lab.TRACE = None
        rows = hit[np.isin(d["px"].index, d["ic"].index)]
        for a, b in zip(*runs):
            if a[0] == "positions":
                np.testing.assert_array_equal(a[1][rows, :m], b[1][rows, :m])
            else:
                early = (a[1] <= m) & rows  # entered at the open of bar <= m: decided at the close of a bar < m
                np.testing.assert_array_equal(a[1][early], b[1][early])
                np.testing.assert_array_equal(a[2][early], b[2][early])
                np.testing.assert_array_equal(a[3][early], b[3][early])


def test_bracket_counts_the_stop_when_stop_and_target_share_a_bar():
    d = _market(30)
    dv = nq_lab.day_view(d)
    dv.o, dv.h, dv.l = dv.o.copy(), dv.h.copy(), dv.l.copy()
    n = len(dv.days)
    i, j = 5, 10
    dv.o[i, j] = 100.0
    dv.h[i, j + 1], dv.l[i, j + 1] = 103.0, 97.0
    r = nq_lab.bracket(dv, np.r_[np.zeros(i), 1, np.zeros(n - i - 1)].astype(int), np.full(n, j),
                       np.full(n, 98.0), np.full(n, 102.0))
    assert r[i] == pytest.approx(98 / 100 - 1 - 2 * nq_lab.COST)


def test_swing_decisions_fill_at_the_next_open():
    d = _market(60)
    pos = pd.Series(0.0, index=d["px"].index)
    pos.iloc[10] = 1.0  # decided at day 10's close
    r = nq_lab.swing_returns(d, pos, d["px"].index[0])
    px, i = d["px"], 11
    assert r.iloc[10] == pytest.approx(d["rf"].iloc[10])  # nothing held on the decision day
    assert r.iloc[i] == pytest.approx(px["c"].iloc[i] / px["o"].iloc[i] - 1 - 2 * 0 - nq_lab.COST, rel=1e-9)


def test_router_only_learns_from_finished_days():
    """A candidate that wins in a cell only after day i must not be picked for that cell before day i."""
    n = 200
    rets = np.zeros((n, 2))
    rets[:, 0] = 0.001
    rets[120:, 1] = 0.01  # candidate 1 starts winning on row 120
    cells = np.zeros(n)
    choice = nq_regimes.route(rets, cells, cells, window=0, min_t=0.0)
    assert (choice[:121] != 1).all()  # row 120's own result is not known when row 120 is decided


def test_swing_router_never_uses_the_return_it_is_deciding_on():
    d = _market()
    p = {"scheme": "vix", "min_t": 0.0, "window": 0}
    a = nq_regimes.swing_router.signal(d, p)
    e = dict(d)
    e["px"] = d["px"].copy()
    e.pop("_swing_matrix", None)
    e["px"].iloc[-1, :4] *= 1.5  # the last day: its decision may use it, earlier ones may not
    b = nq_regimes.swing_router.signal(e, p)
    pd.testing.assert_series_equal(a.iloc[:-1], b.iloc[:-1])


@pytest.mark.parametrize("st", nq_gex_plays.catalogue(), ids=lambda s: s.name)
def test_gex_plays_decide_from_earlier_bars_only(st):
    """Scramble the last session from bar ``m`` on: none of its decisions made before ``m`` may change, and an
    options trade opened at 09:35 keeps its strikes and credit. (Earlier sessions feed the next day's levels,
    so only the last one is scrambled; the cut-off test covers the days.)"""
    d = _market(400, seed=5)
    start = d["px"].index[260]
    for m in (12, 30, 50):
        rng = np.random.default_rng(m)
        e = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in d.items() if not k.startswith("_")}
        for k in ("io", "ih", "il", "ic", "ivw"):
            e[k].iloc[-1, m:] *= np.exp(rng.normal(0, 0.01, nq_lab.BARS - m))
        e["ih"] = np.maximum(e["ih"], np.maximum(e["io"], e["ic"]))
        e["il"] = np.minimum(e["il"], np.minimum(e["io"], e["ic"]))
        for p in _settings(st):
            runs = []
            for data in (d, e):
                nq_lab.TRACE = []
                try:
                    st.evaluate(data, p, start)
                finally:
                    runs.append(nq_lab.TRACE)
                    nq_lab.TRACE = None
            for a, b in zip(*runs):
                if a[1][-1] <= m:  # entered at the open of bar <= m on the last day: decided before m
                    for x, y in zip(a[1:], b[1:]):
                        assert x[-1] == y[-1]
                np.testing.assert_array_equal(a[1][:-1], b[1][:-1])
        if "3b" in st.name:
            p = st.points[0]
            a = nq_gex_plays.fly_trades(nq_lab.day_view(d), nq_gex_plays.view(d), p)
            b = nq_gex_plays.fly_trades(nq_lab.day_view(e), nq_gex_plays.view(e), p)
            cols = ["credit", "risk", "centre"]
            np.testing.assert_allclose(a[cols].to_numpy(), b[cols].to_numpy())


def test_opex_is_the_third_friday_or_the_day_before_a_holiday():
    days = pd.bdate_range("2025-01-01", "2025-12-31").drop(pd.Timestamp("2025-04-18"))  # Good Friday
    ox = nq_gex_plays.opex_days(days)
    got = list(ox.index[ox].strftime("%m-%d"))
    assert got[:4] == ["01-17", "02-21", "03-21", "04-17"] and len(got) == 12
