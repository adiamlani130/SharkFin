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
