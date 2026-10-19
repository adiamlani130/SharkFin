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
| **Top Performers** | Scans the S&P 500, Nasdaq-100, Dow 30 or your own list. Scores momentum (12-1 month and steadiness of the climb), trend, reversal (last week and month), earnings surprises, value, quality and growth themes, **within sector**, with adjustable weights and plain-English labels; low risk and analyst views are available but start at zero. The default weights come from a 2000-2026 test on point-in-time S&P 500 members. **Swing setups** lists today's signals for the swing strategy you pick (Leader Dip Plus 7 by default, with its limit price, profit target and signal log; Tech Breakout Rider; or any Strategy Lab template or your own saved rules). **Core longs** applies six pass/fail rules (profitable, uptrend, steady climb (frog-in-the-pan), not too volatile, debt under control, not expensive) and ranks survivors by momentum + smoothness + value; over 2002-2026 its picks returned about the same as the average member but lost more than a fifth in a year far less often (7-10% vs 11-14%). **Could run** lists stocks with the profile that came before most big 12-month winners (volatile, uptrend, strong 6 months, beat the last report) with the honest odds of a big win and a big loss. **Shark Score list** shows SharkFin Ratings (Value, Momentum, Earnings, Pullback, Risk), each 0-100 against the stock's own sector, the overall Shark Score (the average of Value, Momentum and Earnings, the three themes that held up in both halves of the test) and a weekly top-20 list of steady, lower-risk climbers. **Does the ranking work?** shows the 24-year test (and what didn't help: analyst targets and ratings, insider buying) and replays the price and earnings themes monthly over ~4 years, with costs. |
| **News** | Headlines by topic, ranked by BM25 relevance and recency, with noise and near-duplicate removal and finance-specific tone. **Stock catalysts** shows, for one stock, the next earnings date and last surprise, insider buying, estimate revisions, net buybacks, a volume read, SEC filings (from EDGAR, or Yahoo's copy when EDGAR is unreachable) how much the latest 10-K's risk-factor wording changed, and a **big-beat flag** (EPS beat over 5% and a 2-day jump over 4% vs the market). |
| **Strategy Playbook** | SharkFin's three researched strategies, each explained in plain language (how it works step by step, why it has an edge, the risks) with its research record over the last 5 years (return, Sharpe, worst drop, win rate, edge per trade, risk : reward), growth and year-by-year charts, today's signals, and a backtest you can run. **Leader Dip Plus 7** (33% a year, Sharpe 1.40): swing-buys sharp two-day dips in S&P 500 leaders with idle cash in SPY. **Tech Breakout Rider** (34% a year, Sharpe 1.09): rides tech leaders that break out to new 20-day highs until the 21 / 50-day EMAs cross. **TQQQ Day + Night** (35% a year, Sharpe 1.06): a buy-only intraday breakout plus an overnight bounce trade on TQQQ, with a live panel (band, VWAP, next check, weak-close trigger) from Alpaca's 30-minute bars. **The combined plan** puts them together (50 / 20 / 30, monthly rebalance: 35.4% a year, Sharpe 1.60, worst drop 18% vs SPY's 14%, 0.63 and 25%), with correlation maps, a weight explorer, a money-split calculator and a daily routine. SharkFin only reads market data; it never places orders. |
| **Research & Valuation** | Interactive chart (moving averages, Bollinger bands, VWAP, RSI, MACD), key stats, and the stock **against its sector** (sector strength, breadth and distance from its high, plus the SharkFin Ratings and Shark Score). The **Valuation Lab** has a 3-stage DCF with CAPM WACC (regression beta, live 10-year Treasury), a WACC × terminal-growth sensitivity grid, a **reverse DCF** (the growth the market price implies), a **Monte Carlo DCF**, peer multiples with implied price ranges, and a fundamentals-adjusted regression multiple, all blended into one fair value. The **Trade Setup** tab shows the stock's status under your chosen swing strategy: for Leader Dip Plus 7 the 2-day RSI, 200-day trend, 6-month strength rank against the S&P 500, quality points, limit price, profit target, exit rule and market switch; for Tech Breakout Rider the breakout line, ADX, strength against tech, EMA trend and tech switch; for a Strategy Lab rule set, its signal, each rule's state and how the rules traded this stock over 5 years. Both come with support and resistance zones and a long-term core-holding checklist. Other tabs: Piotroski F-score, Altman Z, ROIC, accruals, margins, financial statements, analyst targets and earnings surprises, news sentiment, and the AI research note. |
| **Forecasts** | An ensemble of Random Walk, Bayesian Drift, ARIMA, Damped ETS and Gradient Boosting. Each model is walk-forward backtested against a random walk and weighted by its out-of-sample error. The fan chart comes from GARCH(1,1) filtered historical simulation. Also shows P(price higher), 80/90% ranges, calibration, and a regime-aware technical signal (ADX, Hurst exponent). |
| **Strategy Lab** | **Build and test**: start from one of 10 ready-made strategies (golden cross, 200-day trend, RSI dip, MACD momentum, 55-day breakout, Bollinger bounce, pullback, volume breakout, 12-month momentum) or build your own by combining rules on 19 indicators (moving averages, Bollinger bands, N-day highs/lows, RSI, stochastic, ADX, MACD, returns, ATR, relative volume, OBV, the S&P 500's trend) with above / below / crosses / rising / falling, plus stop loss, trailing stop, take profit and a time limit. Results read in plain English ("$10,000 became…") with every trade on the chart, and can be re-run on other tickers. **Use as my swing strategy** makes Top Performers and Research use your rules instead of Leader Dip. **Compare strategies** runs them side by side on the same dates. **Leader Dip Plus 7** backtests SharkFin's swing system (Plus 7 or the classic rules) as a portfolio of the S&P 500 or Nasdaq-100, with a choice of where idle cash waits (T-bills, SPY while SPY is above its 200-day, or SPY always). Signals fill at the next open, costs are charged, and idle cash earns the risk-free rate. |
| **Speculation Radar** | Twelve early-stage themes that could be the next Micron or SanDisk (light instead of copper, power behind the meter, nuclear fuel, fusion's supply chain, advanced packaging, rare earths, quantum, space, humanoid robots, drones, AI-discovered drugs, next-gen batteries). Each names its bottleneck, why now, what would prove it, what could kill it and a few listed ways to play it, sorted by risk. A **radar** reads each theme's price action from past prices only: Quiet, **Turning up** (back above its 200-day and beating the S&P 500, the window you want), Running or Cooling. A Micron chart shows what the pattern looked like before its 2025-26 run. Research notes for small positions, not tested strategies. |
| **Portfolio** | Lots, live P/L and CSV import/export. **Risk**: Sharpe, Sortino, max drawdown, VaR/CVaR, beta/alpha, correlation, and risk contribution versus capital weight. **Optimizer**: HRP, risk parity, minimum variance and max Sharpe (Ledoit-Wolf covariance, CAPM-shrunk expected returns), plus the efficient frontier and rebalancing trades. |

## Design notes

- **Forecasts predict returns, not prices, and contain no random noise.** Uncertainty is modelled explicitly, and every model has to beat a random walk out of sample to earn weight.
- **Leader Dip** (`sharkfin/leader_dip.py`): buy a 2-day RSI under 10 in a stock above its 200-day and in the top 30% of the S&P 500 by 6-month gain, with a limit 3% under the close; sell at the next open after the 2-day RSI closes above 70 or after 10 days; no stop; new trades only while SPY is above its 200-day. It replaced the Confluence Pullback system after an Oct 2026 backtest study on point-in-time S&P 500 members. **Plus 7** (the default since the Oct 2026 strategy lab) adds a quality-point filter (a 2.5 ATR flush, 10%+ under the 52-week high, the sector ETF down 2% in 3 days, or VIX above 20), a profit target at the signal close + 1.5 ATR, an exit on a close under the 200-day, a VIX-above-25 panic exception to the market switch, 7 slots, and idle cash in SPY while SPY is above its 200-day.
- **Tech Breakout Rider** (`sharkfin/breakout_rider.py`): S&P 500 tech and communication stocks plus AMZN and TSLA; buy a close above the prior 20-day high on an up day with ADX(14) above 20 and a top-30% 6-month gain among tech, while QQQ's 21-day EMA is above its 50-day, with a limit half an ATR under the close; sell at the next open when the stock's 21-day EMA closes under its 50-day or after 90 days; 10 slots.
- **TQQQ Day + Night** (`sharkfin/day_night.py`): the day leg buys TQQQ at a half-hour check (10:00-15:30) when it is above both a noise band (the open, or the prior close if higher, plus the average move from the open to that time over 14 days) and VWAP, and sells under the higher of the two, flat by the close; the night leg decides at 15:30 (market-on-close orders are due by 15:50): if TQQQ sits in the bottom 20% of the day's range so far, it buys the close and sells the next open. Researched on 1-minute bars; the app replays it on 30-minute bars, which give the same trades.
- **Strategy Playbook data** (`sharkfin/research_data/strategy_returns.csv`, `sharkfin/playbook.py`): the research's daily returns for each strategy since 2016 (point-in-time members), so the combined plan can be re-weighted without downloading anything. Settings and weights were chosen on 2016 - Oct 2021 and graded on Oct 2021 - Oct 2026.
- **Every backtest is a sliding walk-forward** (`sharkfin/walkforward.py`): settings are picked on the 3 years before each test year (best after-T-bill Sharpe, averaged with neighbouring settings), a purge gap as long as the longest hold is skipped, and the next year is traded untouched; only those test years are reported. Each run is handed data already cut at the last day it may know, and a missing value may only be carried forward from an earlier record for up to 5 days, never back-filled (`tests/test_leaks.py` fails the build otherwise).
- **Delisted holdings in the factor replay**: a stock that stops trading mid-month is treated as sold at its last price and held as cash, rather than dropped from the average (which quietly handed its money to the survivors). Sector ETFs for Leader Dip's sector-dip point use today's sector labels, a small bias around the 2018 GICS change.
- **Point-in-time S&P 500 members** (`sharkfin/research_data/sp500_ticker_start_end.csv`, from the fja05680/sp500 dataset, refreshed daily): S&P 500 backtests only rank and trade stocks while they were in the index. Yahoo lacks prices for some that left, so a little survivorship bias remains; Breakout Rider's tech list and the Nasdaq-100 still use today's members.
- **Alpaca market data** (`sharkfin/data.py`): with `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` set (environment or Streamlit secrets), SharkFin reads intraday bars (SIP), daily bars as a Yahoo fallback, and the latest trade (IEX). It is read-only: SharkFin never places orders.
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
  walkforward.py     # sliding-window walk-forward engine (every app backtest runs through it)
  risk.py            # performance & tail-risk statistics
  sentiment.py       # finance lexicon sentiment, BM25, dedupe
  speculation.py     # speculation themes and the Quiet / Turning up / Running / Cooling radar
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

On Streamlit Community Cloud, set the main file to `main.py` and add `ANTHROPIC_API_KEY` under *Secrets* if you want the AI analyst. For the TQQQ Day + Night live panel and long intraday backtests, add `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` (a free paper account's keys work; SharkFin only reads market data). Without them it falls back to Yahoo's last 60 days of 30-minute bars. The SEC asks automated clients to identify themselves: optionally add `SEC_USER_AGENT = "SharkFin your@email.com"` to Secrets for the EDGAR filing features. Portfolio data is stored in `.sharkfin/*.json` and resets when a Cloud app restarts; export it to CSV to keep it.

## Disclaimer

SharkFin is for education and research. It is not investment advice.
