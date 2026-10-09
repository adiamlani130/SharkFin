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
| **Market Dashboard** | Index tiles with sparklines, NYSE status (including holidays), market pulse (trend, drawdown, VIX regime, volatility risk premium), a **market regime light** (SPY vs its 200-day, the 200-day with a 2% band, and the 10-month average; Leader Dip's on/off switch and where idle cash belongs), sector heatmap and rotation map, watchlist, and headline sentiment. |
| **Top Performers** | Scans the S&P 500, Nasdaq-100, Dow 30 or your own list. Scores momentum (12-1 month and steadiness of the climb), trend, reversal (last week and month), earnings surprises, value, quality and growth themes, **within sector**, with adjustable weights and plain-English labels; low risk and analyst views are available but start at zero. The default weights come from a 2000-2026 test on point-in-time S&P 500 members. **Swing setups** lists today's signals for the swing strategy you pick (Leader Dip by default, with its limit price and signal log, or any Strategy Lab template or your own saved rules). **Core longs** applies six pass/fail rules (profitable, uptrend, steady climb (frog-in-the-pan), not too volatile, debt under control, not expensive) and ranks survivors by momentum + smoothness + value; over 2002-2026 its picks returned about the same as the average member but lost more than a fifth in a year far less often (7-10% vs 11-14%). **Could run** lists stocks with the profile that came before most big 12-month winners (volatile, uptrend, strong 6 months, beat the last report) with the honest odds of a big win and a big loss. **Shark Score list** shows SharkFin Ratings (Value, Momentum, Earnings, Pullback, Risk), each 0-100 against the stock's own sector, the overall Shark Score (the average of Value, Momentum and Earnings, the three themes that held up in both halves of the test) and a weekly top-20 list of steady, lower-risk climbers. **Does the ranking work?** shows the 24-year test (and what didn't help: analyst targets and ratings, insider buying) and replays the price and earnings themes monthly over ~4 years, with costs. |
| **News** | Headlines by topic, ranked by BM25 relevance and recency, with noise and near-duplicate removal and finance-specific tone. **Stock catalysts** shows, for one stock, the next earnings date and last surprise, insider buying, estimate revisions, net buybacks, a volume read, SEC filings (from EDGAR, or Yahoo's copy when EDGAR is unreachable) how much the latest 10-K's risk-factor wording changed, and a **big-beat flag** (EPS beat over 5% and a 2-day jump over 4% vs the market). |
| **Research & Valuation** | Interactive chart (moving averages, Bollinger bands, VWAP, RSI, MACD), key stats, and the stock **against its sector** (sector strength, breadth and distance from its high, plus the SharkFin Ratings and Shark Score). The **Valuation Lab** has a 3-stage DCF with CAPM WACC (regression beta, live 10-year Treasury), a WACC × terminal-growth sensitivity grid, a **reverse DCF** (the growth the market price implies), a **Monte Carlo DCF**, peer multiples with implied price ranges, and a fundamentals-adjusted regression multiple, all blended into one fair value. The **Trade Setup** tab shows the stock's status under your chosen swing strategy: for Leader Dip the 2-day RSI, 200-day trend, 6-month strength rank against the S&P 500, limit price, exit rule and market switch; for a Strategy Lab rule set, its signal, each rule's state and how the rules traded this stock over 5 years. Both come with support and resistance zones and a long-term core-holding checklist. Other tabs: Piotroski F-score, Altman Z, ROIC, accruals, margins, financial statements, analyst targets and earnings surprises, news sentiment, and the AI research note. |
| **Forecasts** | An ensemble of Random Walk, Bayesian Drift, ARIMA, Damped ETS and Gradient Boosting. Each model is walk-forward backtested against a random walk and weighted by its out-of-sample error. The fan chart comes from GARCH(1,1) filtered historical simulation. Also shows P(price higher), 80/90% ranges, calibration, and a regime-aware technical signal (ADX, Hurst exponent). |
| **Strategy Lab** | **Build and test**: start from one of 10 ready-made strategies (golden cross, 200-day trend, RSI dip, MACD momentum, 55-day breakout, Bollinger bounce, pullback, volume breakout, 12-month momentum) or build your own by combining rules on 19 indicators (moving averages, Bollinger bands, N-day highs/lows, RSI, stochastic, ADX, MACD, returns, ATR, relative volume, OBV, the S&P 500's trend) with above / below / crosses / rising / falling, plus stop loss, trailing stop, take profit and a time limit. Results read in plain English ("$10,000 became…") with every trade on the chart, and can be re-run on other tickers. **Use as my swing strategy** makes Top Performers and Research use your rules instead of Leader Dip. **Compare strategies** runs them side by side on the same dates. **Leader Dip** backtests SharkFin's swing system as a 10-slot portfolio of the S&P 500 or Nasdaq-100, with a choice of where idle cash waits (T-bills, SPY while SPY is above its 200-day, or SPY always). Signals fill at the next open, costs are charged, and idle cash earns the risk-free rate. |
| **Portfolio** | Lots, live P/L and CSV import/export. **Risk**: Sharpe, Sortino, max drawdown, VaR/CVaR, beta/alpha, correlation, and risk contribution versus capital weight. **Optimizer**: HRP, risk parity, minimum variance and max Sharpe (Ledoit-Wolf covariance, CAPM-shrunk expected returns), plus the efficient frontier and rebalancing trades. |

## Design notes

- **Forecasts predict returns, not prices, and contain no random noise.** Uncertainty is modelled explicitly, and every model has to beat a random walk out of sample to earn weight.
- **Leader Dip** (`sharkfin/leader_dip.py`): buy a 2-day RSI under 10 in a stock above its 200-day and in the top 30% of the S&P 500 by 6-month gain, with a limit 3% under the close; sell at the next open after the 2-day RSI closes above 70 or after 10 days; no stop; new trades only while SPY is above its 200-day. It replaced the Confluence Pullback system after an Oct 2026 backtest study on point-in-time S&P 500 members.
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
