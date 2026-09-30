# SharkFin  (https://sharkfin.streamlit.app/)

**High-grade stock research in your browser.** SharkFin combines validated probabilistic forecasting, a full valuation lab, a multi-factor stock scanner, portfolio risk analytics and optimization, a strategy backtester, and an optional AI analyst, all built on free data (Yahoo Finance and RSS news).

```bash
pip install -r requirements.txt
streamlit run main.py
```

Optional: set `ANTHROPIC_API_KEY` (as an environment variable, or in `.streamlit/secrets.toml`) to enable the AI analyst research notes.

## Pages

| Page | What it does |
|---|---|
| **Market Dashboard** | Index tiles with sparklines, NYSE status (including holidays), market regime (trend, drawdown, VIX regime, volatility risk premium), sector heatmap and rotation map, watchlist, and headline sentiment. |
| **Top Performers** | Scans the S&P 500, Nasdaq-100, Dow 30 or your own list. Scores momentum (12-1 month, residual, 52-week-high), trend, low risk, reversal, value, quality, growth and analyst themes. Scores are winsorized and z-scored **within sector**, and the theme weights are adjustable. Includes a 5-year monthly backtest with rank IC, turnover and trading costs. **Swing setups** lists stocks where the Confluence Pullback setup triggered today or is forming, with entry, stop and targets. **Core longs** ranks passive long-term candidates by sector-relative quality and value, filtered for a positive 12-month trend. |
| **News Desk** | Categorized news ranked by BM25 relevance and recency, with near-duplicate removal and finance-specific sentiment. **Catalysts** shows, for one stock, the next earnings date and last surprise (post-earnings drift), open-market insider buying, estimate revisions, net buybacks, a volume read, SEC EDGAR filings and 8-K events, and how much the latest 10-K's risk-factor wording changed. |
| **Research & Valuation** | Interactive chart (moving averages, Bollinger bands, VWAP, RSI, MACD) and key stats. The **Valuation Lab** has a 3-stage DCF with CAPM WACC (regression beta, live 10-year Treasury), a WACC × terminal-growth sensitivity grid, a **reverse DCF** (the growth the market price implies), a **Monte Carlo DCF**, peer multiples with implied price ranges, and a fundamentals-adjusted regression multiple, all blended into one fair value. The **Trade Setup** tab gives a swing plan (confluence checklist, entry, stop, T1/T2, support and resistance zones) and a long-term core-holding checklist. Other tabs: Piotroski F-score, Altman Z, ROIC, accruals, margins, financial statements, analyst targets and earnings surprises, news sentiment, and the AI research note. |
| **Forecasts** | An ensemble of Random Walk, Bayesian Drift, ARIMA, Damped ETS and Gradient Boosting. Each model is walk-forward backtested against a random walk and weighted by its out-of-sample error. The fan chart comes from GARCH(1,1) filtered historical simulation. Also shows P(price higher), 80/90% ranges, calibration, and a regime-aware technical signal (ADX, Hurst exponent). |
| **Strategy Lab** | Backtests SMA crossover, RSI mean reversion, Donchian breakout, MACD, time-series momentum and vol-targeted trend against buy & hold, plus **Confluence Pullback**: a long-only swing system (uptrend, pullback to the 20 EMA / 50 SMA, close above the prior day's high, points for volume, RSI, MACD, OBV/VPT and room to resistance) with stops, partial profit at T1, a trailing exit and RSI divergence warnings. Every rule can be toggled, and it reports win rate, expectancy in R, a trade list and what each filter adds. Signals trade on the next bar, trading costs are charged, and idle cash earns the risk-free rate. |
| **Portfolio** | Lots, live P/L and CSV import/export. **Risk**: Sharpe, Sortino, max drawdown, VaR/CVaR, beta/alpha, correlation, and risk contribution versus capital weight. **Optimizer**: HRP, risk parity, minimum variance and max Sharpe (Ledoit-Wolf covariance, CAPM-shrunk expected returns), plus the efficient frontier and rebalancing trades. |

## Design notes

- **Forecasts predict returns, not prices, and contain no random noise.** Uncertainty is modelled explicitly, and every model has to beat a random walk out of sample to earn weight.
- **Scores are relative within a sector.** A bank is never compared with a software company on P/E.
- **Everything is testable.** All analytics live in the `sharkfin/` package (no Streamlit imports). The UI lives in `app_pages/`.

```
main.py              # entry point + navigation
app_pages/           # Streamlit pages
sharkfin/
  indicators.py      # Wilder RSI, MACD, ADX, ATR, Bollinger, MFI, VWAP, Hurst, regime signal
  forecasting.py     # GARCH-FHS, ARIMA, ETS, gradient boosting, walk-forward ensemble
  valuation.py       # DCF, reverse/Monte Carlo DCF, WACC, peer multiples, Piotroski, Altman
  factors.py         # cross-sectional factor model + backtest
  portfolio.py       # HRP, risk parity, min-var, max-Sharpe, frontier
  backtest.py        # strategy backtester
  risk.py            # performance & tail-risk statistics
  sentiment.py       # finance lexicon sentiment, BM25, dedupe
  data.py            # yfinance / RSS access with TTL caching
  ai.py              # optional Claude research note
tests/               # unit tests + offline end-to-end page tests
```

## Tests

```bash
pytest -q
```

The page tests run every screen with synthetic offline data (`tests/fakes.py`), so they need no network access.

## Deploy

On Streamlit Community Cloud, set the main file to `main.py` and add `ANTHROPIC_API_KEY` under *Secrets* if you want the AI analyst. The SEC asks automated clients to identify themselves: optionally add `SEC_USER_AGENT = "SharkFin your@email.com"` to Secrets for the EDGAR filing features. Portfolio data is stored in `.sharkfin/*.json` and resets when a Cloud app restarts; export it to CSV to keep it.

## Disclaimer

SharkFin is for education and research. It is not investment advice.
