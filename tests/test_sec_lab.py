"""SEC catalyst parsing and the no-look-ahead rules in the readout, PDUFA and dilution studies."""

import numpy as np
import pandas as pd
import pytest

from sharkfin import sec_lab as sl


def test_pdufa_dates_only_future_dates_near_the_word():
    text = ("On March 3, 2020 we met the FDA. The PDUFA target action date is September 14, 2020. "
            + "x " * 400 + "Our annual meeting is on October 1, 2020.")
    assert sl.pdufa_dates(text, "2020-03-05") == [pd.Timestamp("2020-09-14")]


def test_pdufa_events_merge_close_dates_and_flag_extensions():
    m = pd.DataFrame({"cik": [1, 1, 1, 2], "filed": pd.to_datetime(["2020-01-10", "2020-02-01", "2020-05-01", "2020-01-10"]),
                      "pdufa": pd.to_datetime(["2020-06-01", "2020-06-03", "2020-08-31", "2020-07-01"])})
    ev = sl.pdufa_events(m).set_index(["cik", "pdufa"])
    assert len(ev) == 3
    assert ev.loc[(1, pd.Timestamp("2020-06-03")), "announced"] == pd.Timestamp("2020-01-10")
    assert ev.loc[(1, pd.Timestamp("2020-06-03")), "extended"]          # new date named 89 days later, before it came
    assert not ev.loc[(1, pd.Timestamp("2020-08-31")), "extended"] and not ev.loc[(2, pd.Timestamp("2020-07-01")), "extended"]


@pytest.mark.parametrize("head,want", [
    ("Exhibit 99.1 Acme Announces Positive Topline Results from Phase 3 Trial", "positive"),
    ("Acme Reports Phase 3 Topline Data; Study Did Not Meet Primary Endpoint", "negative"),
    ("Acme Reports Third Quarter 2024 Financial Results and topline data timing", None),
    ("Acme Announces Topline Data from Phase 2 Trial", "mixed"),
    ("Acme to Present Topline Results at ASCO", None),
])
def test_headline_class(head, want):
    assert sl.headline_class(head) == want


def prices(n=400, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2019-01-01", periods=n)
    c = pd.DataFrame(50 * np.exp(np.cumsum(rng.normal(0, 0.02, (n, 2)), axis=0)), index=idx, columns=["AAA", "XBI"])
    o = c.shift(1).fillna(c)
    return sl.Prices(c, o, {"AAA": pd.Series([1e6], index=[idx[0]])})


def test_pdufa_trade_starts_after_the_announcement_and_ignores_later_bars():
    px = prices()
    ev = pd.DataFrame({"cik": [7], "pdufa": [px.idx[300]], "announced": [px.idx[290]], "mentions": [1], "extended": [False]})
    full = sl.pdufa_study(ev, px, {7: "AAA"}).iloc[0]
    # announced 10 sessions before, so the 20-day entry is pushed to the session after the filing
    want = (px.c.AAA.iloc[299] / px.o.AAA.iloc[291] - 1) - (px.c.XBI.iloc[299] / px.o.XBI.iloc[291] - 1) - 2 * sl.COST
    assert abs(full.last20 - want) < 1e-12
    cut = sl.Prices(px.c.iloc[:310], px.o.iloc[:310], px.sh)
    again = sl.pdufa_study(ev, cut, {7: "AAA"}).iloc[0]
    assert np.allclose(full[["from_announce", "last20", "decision", "hold_through", "mcap"]].astype(float),
                       again[["from_announce", "last20", "decision", "hold_through", "mcap"]].astype(float))


def test_readout_offer_flag_and_reaction_window():
    px = prices()
    d = px.idx[200]
    heads = [dict(cik=7, date=d, phase="Phase 3", head="Acme Announces Positive Topline Results")]
    offers = {7: pd.Series([px.idx[205]])}
    r = sl.readout_study(heads, px, {7: "AAA"}, offers).iloc[0]
    assert r.result == "positive" and r.offer_10d
    want = (px.c.AAA.iloc[201] / px.c.AAA.iloc[199] - 1) - (px.c.XBI.iloc[201] / px.c.XBI.iloc[199] - 1)
    assert abs(r.reaction - want) < 1e-12


def test_pop_study_counts_shelves_filed_before_the_jump_only():
    px = prices()
    c = px.c.copy()
    c.iloc[320:, 0] *= 1.6                       # a 60% jump on day 320
    px2 = sl.Prices(c, c.shift(1).fillna(c), px.sh)
    early = sl.pop_study(px2, {7: "AAA"}, {7: pd.Series([px.idx[325]])}, {7: pd.Series([px.idx[330]])})
    assert len(early) == 1 and early.offer_10d.iloc[0] and not early.shelf.iloc[0]
    later = sl.pop_study(px2, {7: "AAA"}, {}, {7: pd.Series([px.idx[100]])})
    assert later.shelf.iloc[0] and not later.offer_10d.iloc[0]


def test_needs_a_contact(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(RuntimeError):
        sl.user_agent()
