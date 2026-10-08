"""Offline stand-ins for the network data layer, used by the UI smoke tests."""

import zlib
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from sharkfin import data
from sharkfin.valuation import Financials

SYMS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "XOM", "JNJ", "PG", "KO", "PEP", "V", "MA", "HD", "UNH"]


def _series(sym, n=1300):
    seed = abs(hash(sym)) % (2**32)
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0004, 0.015, n)
    return 100 * np.exp(np.cumsum(r)), rng


def history(symbol, period="5y", interval="1d"):
    n = 1300
    c, rng = _series(symbol, n)
    idx = pd.bdate_range(end=pd.Timestamp("2026-09-28"), periods=n)
    vol = rng.integers(1e6, 5e6, n).astype(float)
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.003, n))
    hi = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.006, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.006, n)))
    return pd.DataFrame({"Open": o, "High": hi, "Low": lo, "Close": c, "Volume": vol}, index=idx)


def download_prices(symbols, period="2y", field="Close", chunk=150):
    return pd.DataFrame({s: history(s)["Close"] for s in symbols})


def info(symbol):
    c, _ = _series(symbol)
    p = float(c[-1])
    k = (zlib.crc32(symbol.encode()) % 97) / 97  # per-symbol variation so cross-sectional scores differ
    return {**_base_info(symbol, p), "returnOnEquity": 0.1 + 0.4 * k, "grossMargins": 0.3 + 0.5 * k, "forwardPE": 30 - 15 * k}


def _base_info(symbol, p):
    return {"longName": f"{symbol} Inc.", "shortName": symbol, "currentPrice": p, "previousClose": p * 0.99,
            "sector": "Technology", "industry": "Software", "marketCap": p * 1e9, "sharesOutstanding": 1e9,
            "totalDebt": 5e10, "totalCash": 3e10, "trailingPE": 25.0, "forwardPE": 22.0, "enterpriseToEbitda": 18.0,
            "enterpriseToRevenue": 6.0, "priceToBook": 8.0, "freeCashflow": p * 1e9 * 0.04, "trailingEps": p / 25,
            "forwardEps": p / 22, "ebitda": 6e9 * p / 100, "totalRevenue": 2e10 * p / 100, "bookValue": p / 8,
            "revenueGrowth": 0.08, "earningsGrowth": 0.10, "ebitdaMargins": 0.3, "grossMargins": 0.55,
            "profitMargins": 0.2, "returnOnEquity": 0.3, "debtToEquity": 60.0, "targetMeanPrice": p * 1.1,
            "targetLowPrice": p * 0.8, "targetHighPrice": p * 1.4, "recommendationMean": 2.0,
            "recommendationKey": "buy", "numberOfAnalystOpinions": 30, "beta": 1.1, "dividendYield": 0.6,
            "fiftyTwoWeekLow": p * 0.7, "fiftyTwoWeekHigh": p * 1.1, "longBusinessSummary": "Makes things."}


def financials(symbol):
    cols = pd.to_datetime(["2025-12-31", "2024-12-31", "2023-12-31", "2022-12-31"])
    inc = pd.DataFrame({"Total Revenue": [120, 100, 90, 80], "Gross Profit": [66, 54, 48, 42], "EBIT": [30, 24, 20, 18],
                        "Net Income": [22, 17, 15, 13], "Pretax Income": [28, 21, 19, 16], "Tax Provision": [6, 4, 4, 3],
                        "EBITDA": [36, 30, 26, 23], "Interest Expense": [1, 1, 1, 1]}, index=cols).T * 1e8
    bal = pd.DataFrame({"Total Assets": [200, 190, 180, 170], "Current Assets": [80, 70, 65, 60],
                        "Current Liabilities": [40, 40, 38, 36], "Long Term Debt": [30, 35, 36, 36],
                        "Total Debt": [32, 37, 38, 38], "Stockholders Equity": [110, 95, 90, 85],
                        "Retained Earnings": [70, 55, 45, 40], "Ordinary Shares Number": [10, 10, 10.1, 10.2],
                        "Total Liabilities Net Minority Interest": [90, 95, 90, 85],
                        "Cash And Cash Equivalents": [20, 15, 12, 10]}, index=cols).T * 1e8
    cf = pd.DataFrame({"Operating Cash Flow": [30, 23, 20, 18], "Capital Expenditure": [-6, -5, -4.5, -4],
                       "Free Cash Flow": [24, 18, 15.5, 14], "Stock Based Compensation": [2, 1.8, 1.5, 1.2]}, index=cols).T * 1e8
    return Financials(inc, bal, cf)


def news(query, symbol=None):
    now = datetime.now(timezone.utc)
    return [{"title": t, "summary": "", "link": "https://example.com", "publisher": "Test", "published": now - timedelta(hours=i)}
            for i, t in enumerate(["Company beats estimates and raises guidance", "Shares fall on tariff fears",
                                   "Analyst upgrades stock to buy", "Market steady ahead of Fed"])]


def install(monkeypatch):
    monkeypatch.setattr(data, "history", history)
    monkeypatch.setattr(data, "download_prices", download_prices)
    monkeypatch.setattr(data, "info", info)
    monkeypatch.setattr(data, "financials", financials)
    monkeypatch.setattr(data, "quarterly_financials", financials)
    monkeypatch.setattr(data, "news", news)
    monkeypatch.setattr(data, "risk_free_rate", lambda: 0.042)
    monkeypatch.setattr(data, "tbill_yields", lambda period="10y": pd.Series(0.04, index=history("^IRX").index))
    monkeypatch.setattr(data, "analyst_data", analyst_data)
    monkeypatch.setattr(data, "earnings_history", earnings_history)
    monkeypatch.setattr(data, "earnings_histories",
                        lambda syms, workers=6: {s: earnings_history(s) for s in syms})
    monkeypatch.setattr(data, "download_ohlcv", download_ohlcv)
    monkeypatch.setattr(data, "sec_filings", sec_filings)
    monkeypatch.setattr(data, "sec_document_text", sec_document_text)
    monkeypatch.setattr(data, "market_history", lambda period="10y": history("SPY", period))
    monkeypatch.setattr(data, "search", lambda q: [(q.upper(), q.upper())])
    monkeypatch.setattr(data, "infos", lambda syms, workers=8: pd.DataFrame([info(s) for s in syms], index=list(syms)))
    monkeypatch.setattr(data, "peers_for", lambda s, inf, max_peers=15: [x for x in SYMS if x != s][:10])
    monkeypatch.setattr(data, "sp500_table", lambda: pd.DataFrame({"Symbol": SYMS, "Name": SYMS, "Sector": ["Tech"] * len(SYMS),
                                                                    "SubIndustry": ["Software"] * len(SYMS)}))
    monkeypatch.setattr(data, "universe", lambda name: SYMS)


def download_ohlcv(symbols, period="2y", chunk=150):
    frames = {s: history(s) for s in symbols}
    return {f: pd.DataFrame({s: d[f] for s, d in frames.items()}) for f in ("Open", "High", "Low", "Close", "Volume")}


def analyst_data(symbol):
    idx = pd.to_datetime(["2026-10-20", "2026-07-20", "2026-04-20", "2026-01-20", "2025-10-20"])
    ed = pd.DataFrame({"EPS Estimate": [2.0, 1.9, 1.8, 1.7, 1.6], "Reported EPS": [np.nan, 2.1, 1.85, 1.65, 1.7],
                       "Surprise(%)": [np.nan, 10.5, 2.8, -2.9, 6.25]}, index=idx)
    ins = pd.DataFrame({"Shares": [1000, 500, 2000], "Value": [150000.0, 70000.0, 300000.0],
                        "Text": ["Purchase at price 150.00 per share.", "Purchase at price 140.00 per share.",
                                 "Sale at price 150.00 per share."],
                        "Insider": ["DOE JANE", "ROE RICHARD", "DOE JANE"], "Position": ["CEO", "Director", "CEO"],
                        "Start Date": pd.to_datetime(["2026-09-01", "2026-08-15", "2026-06-01"])})
    rev = pd.DataFrame({"upLast7days": [1, 2], "upLast30days": [5, 6], "downLast30days": [1, 0], "downLast7Days": [0, 0]},
                       index=["0q", "+1y"])
    return {"earnings_dates": ed, "insider_transactions": ins, "eps_revisions": rev}


def sec_filings(symbol, forms=("10-K", "10-Q", "8-K"), limit=40):
    return pd.DataFrame({"form": ["10-Q", "8-K", "10-K", "10-K"],
                         "filed": pd.to_datetime(["2026-08-01", "2026-07-20", "2026-02-01", "2025-02-01"]),
                         "reportDate": ["2026-06-30", "2026-07-20", "2025-12-31", "2024-12-31"],
                         "what": ["", "Earnings results", "", ""],
                         "url": ["https://example.com/q", "https://example.com/8k", "https://example.com/k1",
                                 "https://example.com/k0"]})


def sec_document_text(url):
    base = "Item 1A. Risk Factors " + "Our business faces competition from many rivals in every market we serve. " * 60
    extra = "New tariffs on imported components could materially raise our costs and hurt margins next year. " * 20
    return base + (extra if url.endswith("k1") else "") + " Item 1B. Unresolved Staff Comments none."


def earnings_history(symbol, limit=28):
    """Quarterly reports for the past ~5 years (newest first, like Yahoo) with a symbol-dependent run of surprises."""
    rng = np.random.default_rng(sum(map(ord, symbol)))
    idx = pd.date_range(end="2026-11-30", periods=22, freq="QS-JAN") + pd.Timedelta(days=19)
    est = np.linspace(1.0, 2.0, len(idx))
    sur = rng.normal(3, 6, len(idx))
    rep = est * (1 + sur / 100)
    future = idx > pd.Timestamp.now()
    rep[future], sur[future] = np.nan, np.nan
    df = pd.DataFrame({"EPS Estimate": est, "Reported EPS": rep, "Surprise(%)": sur},
                      index=idx.tz_localize("America/New_York"))
    return df.iloc[::-1]
