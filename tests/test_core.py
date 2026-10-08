import numpy as np
import pandas as pd
import pytest

from sharkfin import backtest, factors, forecasting, indicators, portfolio, risk, sentiment, valuation


# --------------------------------------------------------------------- indicators

def test_rsi_bounds_and_wilder(ohlcv):
    r = indicators.rsi(ohlcv["Close"])
    assert r.dropna().between(0, 100).all()
    up = pd.Series(np.arange(1, 60, dtype=float))
    assert indicators.rsi(up).iloc[-1] == 100


def test_rsi_matches_reference_formula():
    # Wilder's example-style check against an explicit recursive implementation.
    rng = np.random.default_rng(3)
    c = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    d = c.diff().values[1:]
    g, l = np.maximum(d, 0), np.maximum(-d, 0)
    ag, al = g[:14].mean(), l[:14].mean()
    for i in range(14, len(d)):
        ag = (ag * 13 + g[i]) / 14
        al = (al * 13 + l[i]) / 14
    ref = 100 - 100 / (1 + ag / al)
    # ewm with adjust=False seeds from the first value rather than an SMA, so
    # allow a small tolerance after 200 bars of decay.
    assert abs(indicators.rsi(c).iloc[-1] - ref) < 1.0


def test_compute_all_and_signal(ohlcv):
    panel = indicators.compute_all(ohlcv)
    assert {"rsi_14", "adx", "bb_pct_b", "atr_14", "sma_200"}.issubset(panel.columns)
    sig = indicators.technical_signal(panel)
    assert -1 <= sig["score"] <= 1
    assert sig["label"] in {"Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"}


def test_hurst_random_walk_near_half(ohlcv):
    h = indicators.hurst_exponent(ohlcv["Close"])
    assert 0.35 < h < 0.65


# --------------------------------------------------------------------- risk

def test_risk_summary(ohlcv):
    r = ohlcv["Close"].pct_change().dropna()
    s = risk.summary(r, r * 0.9)
    assert s["Max Drawdown"] <= 0
    assert s["CVaR 95% (1d)"] >= s["VaR 95% (1d)"] > 0
    assert s["Beta"] == pytest.approx(1 / 0.9, rel=1e-6)


def test_drawdown_simple():
    r = pd.Series([0.1, -0.5, 0.2])
    assert risk.max_drawdown(r) == pytest.approx(-0.5)


# --------------------------------------------------------------------- forecasting

def test_garch_recovers_parameters():
    rng = np.random.default_rng(1)
    w, a, b = 2e-6, 0.08, 0.9
    s2, r = w / (1 - a - b), []
    for _ in range(3000):
        e = np.sqrt(s2) * rng.standard_normal()
        r.append(e)
        s2 = w + a * e * e + b * s2
    fit = forecasting.fit_garch(np.array(r))
    assert fit.alpha == pytest.approx(a, abs=0.04)
    assert fit.beta == pytest.approx(b, abs=0.05)


def test_ensemble_forecast_is_deterministic_and_coherent(ohlcv):
    a = forecasting.ensemble_forecast(ohlcv, "T", horizon=10, n_origins=4)
    b = forecasting.ensemble_forecast(ohlcv, "T", horizon=10, n_origins=4)
    np.testing.assert_allclose(a.expected_price, b.expected_price)  # no random noise
    q = a.quantiles
    assert (q[0.05] <= q[0.5]).all() and (q[0.5] <= q[0.95]).all()
    # Uncertainty grows with horizon
    width = q[0.95] - q[0.05]
    assert width.iloc[-1] > width.iloc[0]
    assert sum(s.weight for s in a.scores) == pytest.approx(1.0)
    assert 0 <= a.at(10)["prob_up"] <= 1


def test_features_have_no_lookahead(ohlcv):
    f1 = forecasting.build_features(ohlcv)
    f2 = forecasting.build_features(ohlcv.iloc[:600])
    pd.testing.assert_frame_equal(f1.iloc[:600], f2, check_freq=False)


# --------------------------------------------------------------------- valuation

def test_dcf_gordon_consistency():
    # Zero growth everywhere -> perpetuity value FCF/WACC (mid-year adjusted).
    res = valuation.dcf(100, 0.0, 0.10, 0.0, net_debt=0, shares=1, high_growth_years=5, fade_years=0)
    assert res.enterprise_value == pytest.approx(100 / 0.10 * 1.10 ** 0.5, rel=0.01)


def test_reverse_dcf_roundtrip():
    v = valuation.dcf(50, 0.12, 0.09, 0.025, net_debt=100, shares=10).value_per_share
    g = valuation.reverse_dcf(v, 50, 0.09, 0.025, 100, 10)
    assert g == pytest.approx(0.12, abs=1e-4)


def test_monte_carlo_dcf_centered():
    base = valuation.dcf(50, 0.08, 0.09, 0.025, 0, 10).value_per_share
    sims = valuation.monte_carlo_dcf(50, 0.08, 0.09, 0.025, 0, 10, fcf_sd=0.0, growth_sd=0.001, wacc_sd=0.0001, tg_sd=0.0001)
    assert np.median(sims) == pytest.approx(base, rel=0.02)


def test_wacc_bounds():
    w = valuation.wacc(1e11, 2e10, beta=1.2, rf=0.04, erp=0.05, interest_expense=1e9, tax_rate=0.21)
    assert 0.04 < w.wacc < 0.12
    assert w.weight_equity + w.weight_debt == pytest.approx(1)


def _statements():
    cols = pd.to_datetime(["2025-12-31", "2024-12-31", "2023-12-31"])
    inc = pd.DataFrame({
        "Total Revenue": [1200, 1000, 900], "Gross Profit": [600, 480, 420], "EBIT": [300, 240, 200],
        "Net Income": [220, 170, 150], "Pretax Income": [280, 215, 190], "Tax Provision": [60, 45, 40],
        "EBITDA": [360, 300, 260], "Interest Expense": [10, 11, 12],
    }, index=cols).T
    bal = pd.DataFrame({
        "Total Assets": [2000, 1900, 1800], "Current Assets": [800, 700, 650], "Current Liabilities": [400, 400, 380],
        "Long Term Debt": [300, 350, 360], "Total Debt": [320, 370, 380], "Stockholders Equity": [1100, 950, 900],
        "Retained Earnings": [700, 550, 450], "Ordinary Shares Number": [100, 100, 101],
        "Total Liabilities Net Minority Interest": [900, 950, 900], "Cash And Cash Equivalents": [200, 150, 120],
    }, index=cols).T
    cf = pd.DataFrame({"Operating Cash Flow": [300, 230, 200], "Capital Expenditure": [-60, -50, -45],
                       "Free Cash Flow": [240, 180, 155], "Stock Based Compensation": [20, 18, 15]}, index=cols).T
    return valuation.Financials(inc, bal, cf)


def test_piotroski_and_altman():
    fin = _statements()
    f = valuation.piotroski_f_score(fin)
    assert f is not None and f.score >= 7 and f.label == "Strong"
    z = valuation.altman_z(fin, market_cap=5000)
    assert z.label == "Safe"
    q = valuation.quality_metrics(fin, 5000)
    assert q["Gross margin"] == pytest.approx(0.5)
    assert fin.revenue_cagr(2) == pytest.approx((1200 / 900) ** 0.5 - 1)


def test_forward_growth_prefers_next_year_consensus():
    ge = pd.DataFrame({"stockTrend": [0.97, -0.08, np.nan], "indexTrend": [0.5, 0.34, 0.12]}, index=["0q", "+1y", "LTG"])
    assert valuation.forward_growth(ge) == pytest.approx(-0.08)
    ge.loc["+1y", "stockTrend"] = np.nan
    assert np.isnan(valuation.forward_growth(ge))
    assert np.isnan(valuation.forward_growth(None))


def test_fmt_money_negative_sign_before_dollar():
    from sharkfin import ui
    assert ui.fmt_money(-104.5) == "-$104.50"
    assert ui.fmt_money(-2.5e9) == "-$2.50B"


def test_implied_prices_from_peers():
    peers = pd.DataFrame({"EV/EBITDA": [8, 10, 12, 14, 200], "P/E (ttm)": [15, 18, 20, 22, 25]})
    target = {"price": 50, "shares": 10, "net_debt": 100, "ebitda": 50, "trailing_eps": 2.5}
    df = valuation.implied_prices(target, peers).set_index("Multiple")
    assert df.loc["P/E (ttm)", "Median"] == pytest.approx(20 * 2.5)
    # Outlier multiple of 200 is removed by the IQR filter
    assert df.loc["EV/EBITDA", "Median"] == pytest.approx((11 * 50 - 100) / 10)


def test_fair_value_blend():
    out = valuation.fair_value_summary(100, {"a": (120, 1), "b": (150, 1), "c": (np.nan, 1)})
    assert out["fair_value"] == pytest.approx(np.sqrt(120 * 150))
    assert out["label"] == "Significantly undervalued"


# --------------------------------------------------------------------- factors

def test_factor_composite_ranks_planted_winners(price_panel):
    pf = factors.price_factor_frame(price_panel)
    sc = factors.composite_scores(pf)
    top = sc["Composite"].nlargest(8).index
    # Planted drift increases with the column number
    assert np.mean([int(s[1:]) for s in top]) > 25


def test_sector_neutral_z():
    s = pd.Series([1, 2, 3, 4, 5, 10, 20, 30, 40, 50], index=list("abcdefghij"), dtype=float)
    sec = pd.Series(["x"] * 5 + ["y"] * 5, index=s.index)
    z = factors.sector_neutral_z(s, sec)
    assert z[:5].mean() == pytest.approx(0, abs=1e-9) and z[5:].mean() == pytest.approx(0, abs=1e-9)


def test_factor_backtest_positive_ic(price_panel):
    res = factors.backtest_price_composite(price_panel)
    assert res["ic_mean"] > 0
    assert len(res["strategy"]) > 100


# --------------------------------------------------------------------- portfolio

def test_optimizers_sum_to_one(price_panel):
    rets = price_panel.iloc[:, :8].pct_change().dropna()
    w, stats, mu, cov = portfolio.compare_allocations(rets, max_weight=0.4)
    np.testing.assert_allclose(w.sum().values, 1.0, atol=1e-6)
    assert (w >= -1e-9).all().all()
    assert stats.loc["Volatility", "Min Variance"] <= stats.loc["Volatility", "Equal Weight"] + 1e-9
    rc = risk.risk_contributions(w["Risk Parity"].values, cov.values)
    assert np.allclose(rc, 1 / 8, atol=0.02)


# --------------------------------------------------------------------- backtest

def test_backtest_no_lookahead(ohlcv):
    res = backtest.run(ohlcv, "Buy & Hold", cost_bps=0)
    # First day can't earn the first return (position is lagged a bar)
    assert res["returns"].iloc[0] == 0
    eq, st = backtest.compare(ohlcv)
    assert set(backtest.STRATEGIES).issubset(eq.columns)


# --------------------------------------------------------------------- sentiment

@pytest.mark.parametrize("text,sign", [
    ("Apple beats estimates and raises guidance", 1),
    ("Company cuts guidance as sales plunge", -1),
    ("Profits did not decline despite fears", 1),
])
def test_sentiment_direction(text, sign):
    assert np.sign(sentiment.score_text(text)) == sign


def test_rank_and_dedupe():
    arts = [
        {"title": "Nvidia beats estimates on AI demand", "summary": ""},
        {"title": "Nvidia beats estimates on AI demand, shares rise", "summary": ""},
        {"title": "Oil prices fall on supply glut", "summary": ""},
    ]
    ranked = sentiment.rank_articles(arts, "nvidia earnings")
    assert len(ranked) == 2
    assert "Nvidia" in ranked[0]["title"]


# --------------------------------------------------------------------- leader dip / levels

def _panel(n=900, k=40, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2021-01-04", periods=n)
    mkt = rng.normal(0.0004, 0.01, n)
    r = mkt[:, None] * rng.uniform(0.6, 1.4, k) + np.linspace(-0.0005, 0.001, k) + rng.normal(0, 0.018, (n, k))
    c = 100 * np.exp(np.cumsum(r, 0))
    o = np.vstack([c[:1], c[:-1]]) * np.exp(rng.normal(0, 0.01, (n, k)))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.008, (n, k))))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.015, (n, k))))
    cols = [f"S{i:02d}" for i in range(k)]
    f = lambda a: pd.DataFrame(a, index=idx, columns=cols)
    return {"Open": f(o), "High": f(h), "Low": f(lo), "Close": f(c)}, pd.Series(100 * np.exp(np.cumsum(mkt)), index=idx)


def test_leader_dip_signals_have_no_lookahead():
    from sharkfin import leader_dip
    px, _ = _panel()
    full = leader_dip.signal_frames(px["Close"])
    part = leader_dip.signal_frames(px["Close"].iloc[:600])
    pd.testing.assert_frame_equal(full["buy"].iloc[:600], part["buy"])
    assert full["buy"].values.sum() > 20
    lat = leader_dip.latest(px["Close"].iloc[:600])
    assert lat["Signal"].equals(part["buy"].iloc[-1].reindex(lat.index))
    assert np.allclose(lat["Limit"], lat["Price"] * 0.97)


def test_leader_dip_backtest_fills_limits_and_exits():
    from sharkfin import leader_dip
    px, spy = _panel()
    res = leader_dip.backtest(px, spy, cash="tbills", tbill_yields=pd.Series(0.0, index=spy.index), slots=1, cost_bps=0)
    tr = res["trades"]
    done = tr[tr["Why it sold"] != "Open"]
    assert len(done) > 10
    sig = leader_dip.signal_frames(px["Close"])
    on = leader_dip.market_on(spy)
    for _, t in done.iterrows():
        d0, d1 = t["Signal date"], t["Bought"]
        assert sig["buy"].loc[d0, t["Symbol"]] and on.loc[d0]
        limit = px["Close"].loc[d0, t["Symbol"]] * 0.97
        assert px["Low"].loc[d1, t["Symbol"]] <= limit + 1e-9
        assert t["Buy price"] == pytest.approx(min(px["Open"].loc[d1, t["Symbol"]], limit))
        assert t["Sell price"] == pytest.approx(px["Open"].loc[t["Sold"], t["Symbol"]])
        assert t["Days held"] <= leader_dip.MAX_DAYS
    # One slot, no costs, idle cash earning nothing: the account compounds the trades, except that each trade is
    # sized from the prior close's account value, so a gap up at the exit open leaves a sliver in cash.
    assert res["equity"].iloc[-1] == pytest.approx(float(np.prod(1 + tr["Return"])), rel=0.01)
    st = res["stats"]
    assert 0 <= st["Win rate"] <= 1 and st["Trades"] == len(done)


def test_leader_dip_idle_cash_choices():
    from sharkfin import leader_dip
    px, spy = _panel()
    runs = {c: leader_dip.backtest(px, spy, cash=c, tbill_yields=pd.Series(0.02, index=spy.index))["equity"]
            for c in ("tbills", "spy_trend", "spy")}
    assert runs["tbills"].iloc[-1] != runs["spy"].iloc[-1]
    assert runs["spy_trend"].iloc[-1] != runs["tbills"].iloc[-1]


def test_regime_band_and_switch():
    from sharkfin import leader_dip
    idx = pd.bdate_range("2020-01-01", periods=600)
    up = pd.Series(np.linspace(100, 200, 600), index=idx)
    r = leader_dip.regime(up)
    assert r["leader_dip_on"] and r["band_on"] and r["ten_month_on"] and r["idle_cash"] == "SPY"
    down = up.copy()
    down.iloc[-30:] = np.linspace(190, 150, 30)
    r = leader_dip.regime(down)
    assert not r["leader_dip_on"] and r["band_on"] is False and r["idle_cash"] == "T-bills"
    # Inside the 2% band the banded switch keeps its last state.
    sma = pd.Series(100.0, index=idx[:5])
    assert list(leader_dip._band(pd.Series([103, 101, 99, 97, 99.5], index=idx[:5]), sma, 0.02)) == [True, True, True, False, False]


def test_leader_dip_follow_up():
    from sharkfin import leader_dip
    idx = pd.bdate_range("2026-01-05", periods=15)
    c = pd.Series([100, 96, 95, 97, 99, 101, 103, 104, 103, 102, 101, 100, 99, 98, 97], index=idx, dtype=float)
    o, lo = c.shift(1).fillna(100), c * 0.98
    lo.iloc[2] = 92.0  # reaches the 93.12 limit the day after the signal
    px = {"Open": pd.DataFrame({"AAA": o, "BBB": o}), "Low": pd.DataFrame({"AAA": lo, "BBB": c}),
          "Close": pd.DataFrame({"AAA": c, "BBB": c})}
    log = pd.DataFrame({"Date": [f"{idx[1]:%Y-%m-%d}"] * 2, "Symbol": ["AAA", "BBB"], "Close": [96.0, 96.0],
                        "Limit": [93.12, 93.12]})
    fu = leader_dip.follow_up(log, px).set_index("Symbol")
    assert fu.loc["AAA", "Filled"] and fu.loc["AAA", "Fill price"] == pytest.approx(min(o.iloc[2], 93.12))
    assert fu.loc["AAA", "Status"] in ("Closed", "Open", "Sell at the next open")
    assert fu.loc["BBB", "Filled"] is False or fu.loc["BBB", "Filled"] == False  # noqa: E712


def test_levels_zones_and_divergence(ohlcv):
    from sharkfin import levels
    zones = levels.sr_zones(ohlcv)
    assert zones and all(z["low"] <= z["high"] for z in zones)
    res, sup = levels.nearest_levels(ohlcv, zones)
    price = ohlcv["Close"].iloc[-1]
    assert (not np.isfinite(res) or res > price) and (not np.isfinite(sup) or sup < price)
    high = pd.Series([10, 11, 12, 13, 12, 11, 11.5, 12, 12.5, 13.5], dtype=float)
    rsi = pd.Series([50, 60, 70, 75, 65, 55, 58, 62, 64, 68], dtype=float)
    div = levels.rsi_bearish_divergence(high, rsi, window=8)
    assert div.iloc[-1] and not div.iloc[:-1].any()


# --------------------------------------------------------------------- ratings

def test_sector_relative_ratings(price_panel):
    from sharkfin import ratings
    sectors = pd.Series(["A"] * 20 + ["B"] * 20, index=price_panel.columns)
    info = pd.DataFrame({"trailingEps": np.linspace(-1, 8, 40), "earningsGrowth": 0.1,
                         "currentPrice": price_panel.iloc[-1].values, "averageVolume": 1e6}, index=price_panel.columns)
    rat = ratings.ratings(price_panel, sectors, info, 0.04)
    for k in ("RV", "RT", "RS", "CI", "VST"):
        assert rat[k].between(0, 2).all(), k
    # Ranked within each sector: every sector's ranks span the same range.
    assert rat.groupby(sectors)["RT"].max().round(6).nunique() == 1
    assert (rat.loc[info["trailingEps"] <= 0, "RV_raw"] == 0).all()
    # RT follows relative strength: the planted winners (higher columns) trend better.
    assert np.corrcoef(rat["rt_raw"], np.arange(40))[0, 1] > 0.3
    top = ratings.vst_list(rat, pd.Series(np.linspace(-0.1, 0.1, 40), index=price_panel.columns), n=5)
    assert len(top) == 5 and top["VST"].is_monotonic_decreasing


def test_sector_context(price_panel):
    from sharkfin import ratings
    etfs = price_panel.iloc[:, :11].copy()
    etfs.columns = list(ratings.GICS_OF_ETF)
    sec = pd.Series(["Information Technology"] * 10 + ["Energy"] * 30, index=price_panel.columns)
    ctx = ratings.sector_context("S00", price_panel["S00"], "Technology", etfs, price_panel, sec)
    assert ctx["etf"] == "XLK" and 1 <= ctx["rank"] <= 11 and ctx["breadth_n"] == 10
    assert ctx["vs_sector"] == pytest.approx(ctx["stock_6m"] - ctx["sector_6m"])
    assert ratings.sector_context("S00", price_panel["S00"], "Unknown", etfs) == {}


# --------------------------------------------------------------------- catalysts

def test_earnings_and_insider_summaries():
    from sharkfin import catalysts
    from tests import fakes
    ad = fakes.analyst_data("AAPL")
    e = catalysts.earnings_summary(ad["earnings_dates"], now=pd.Timestamp("2026-09-01"))
    assert e["last_surprise"] == pytest.approx(0.105)
    assert e["drift_window"] and e["beats_last4"] == 3
    assert e["next_date"] == pd.Timestamp("2026-10-20")
    ins = catalysts.insider_summary(ad["insider_transactions"], now=pd.Timestamp("2026-09-30"))
    assert ins["buys"] == 2 and ins["buyers"] == 2 and ins["cluster"] and ins["sells"] == 1
    assert catalysts.revision_balance(ad["eps_revisions"]) == pytest.approx(10 / 12)


def test_earnings_beat_flag():
    from sharkfin import catalysts
    from tests import fakes
    ed = fakes.analyst_data("AAPL")["earnings_dates"]  # last report Jul 20 2026, +10.5% surprise
    idx = pd.bdate_range("2026-06-01", "2026-09-30")
    flat = pd.Series(100.0, index=idx)
    jump = flat.copy()
    jump[jump.index >= "2026-07-21"] = 107.0  # +7% on the first trading day after the report
    hit = catalysts.earnings_beat_flag(ed, jump.loc[:"2026-08-20"])
    assert hit["flag"] and hit["active"] and hit["jump"] == pytest.approx(0.07) and hit["surprise"] == pytest.approx(0.105)
    # The same jump is no flag when the whole market rose with it.
    assert not catalysts.earnings_beat_flag(ed, jump.loc[:"2026-08-20"], jump)["flag"]
    assert not catalysts.earnings_beat_flag(ed, flat)["flag"]
    stale = catalysts.earnings_beat_flag(ed, jump)  # ~50 trading days later: still inside the window
    late = catalysts.earnings_beat_flag(ed, pd.concat([jump, pd.Series(107.0, index=pd.bdate_range("2026-10-01", "2026-12-31"))]))
    assert stale["active"] and late["flag"] and not late["active"]


def test_filing_change_finds_new_risk_language():
    from sharkfin import catalysts
    from tests import fakes
    toc = "Table of contents Item 1A. Risk Factors 12 Item 1B. Unresolved Staff Comments 20 "
    old = toc + fakes.sec_document_text("https://example.com/k0")
    new = toc + fakes.sec_document_text("https://example.com/k1")
    assert len(catalysts.risk_factors_section(new)) > 1000
    ch = catalysts.filing_change(old, new)
    assert ch["section"].startswith("Risk factors")
    assert 0 < ch["similarity"] < 0.99
    assert any("tariffs" in s for s in ch["new_sentences"])
    assert catalysts.text_similarity("same words here", "same words here") == pytest.approx(1.0)
    assert catalysts.html_to_text("<p>Hello&nbsp;<b>world</b></p><script>x()</script>") == "Hello world"


def test_core_long_screen_filters_value_traps():
    from sharkfin import catalysts
    idx = list("ABCDE")
    df = pd.DataFrame({"Value": [0.5, 0.2, 1.0, -1.5, 0.3], "mom_12_1": [0.2, -0.1, 0.3, 0.1, 0.4],
                       "trend_200": [0.05, -0.02, 0.1, 0.02, 0.1], "fip": [0.1, 0.1, 0.1, 0.1, 0.12],
                       "volatility": [0.2, 0.2, 0.25, 0.2, 0.9], "Sector": ["Technology"] * 5}, index=idx)
    inf = pd.DataFrame({"netIncomeToCommon": [1e9, 1e9, -1e8, 1e9, 1e9], "freeCashflow": [1e9] * 5,
                        "totalDebt": [1e9] * 5, "totalCash": [5e8] * 5, "ebitda": [2e9] * 5}, index=idx)
    out, funnel = catalysts.core_long_screen(df, inf)
    # B downtrend, C loses money, D expensive, E too volatile
    assert list(out.index) == ["A"]
    assert funnel[0]["Still in"] == 5 and funnel[-1]["Still in"] == 1
    assert [f["Still in"] for f in funnel] == sorted([f["Still in"] for f in funnel], reverse=True)


def _ohlc(close):
    idx = pd.bdate_range("2020-01-01", periods=len(close))
    c = pd.Series(close, index=idx, dtype=float)
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c, "Volume": 1e6})


def test_builder_fills_next_open_and_stops():
    from sharkfin import builder
    close = [100.0] * 60 + [101.0] + [102.0] * 5 + [90.0] * 10 + [95.0] * 20
    d = _ohlc(close)
    d.iloc[61, d.columns.get_loc("Open")] = 100.5  # day after the signal opens here
    s = {"logic": "ALL", "entry": [builder.C("Price", "crosses above", value=100.5)], "exit": [], "stop": 5.0}
    r = builder.run(d, s, cost_bps=0)
    t = r["trades"].iloc[0]
    assert t["Entry date"] == d.index[61] and t["Entry"] == 100.5  # signal on day 60's close, filled next open
    assert t["Exit reason"] == "Stop loss" and t["Exit"] == 90.0  # gapped through the stop: filled at the open
    assert r["stats"]["Trades"] == 1


def test_builder_templates_run_and_describe():
    from sharkfin import builder
    rng = np.random.default_rng(0)
    d = _ohlc(100 * np.exp(np.cumsum(rng.normal(0.0005, 0.015, 900))))
    for name in builder.TEMPLATES:
        r = builder.run(d, builder.template(name), 5, 0.02)
        assert np.isfinite(r["stats"]["Return per year"])
        assert len(r["equity"]) == len(r["bh_equity"])
    buy, sell = builder.describe_strategy(builder.template("Golden cross"))
    assert buy == "SMA(50) crosses above SMA(200)" and sell == "SMA(50) crosses below SMA(200)"
    runs = builder.compare_templates(d, ["Golden cross", "55-day breakout"], 5, 0.0)
    a, b = runs.values()
    assert a["equity"].index[0] == b["equity"].index[0]
