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
| **Market Dashboard** | Index tiles with sparklines and NYSE status (including holidays), a **Today** card (which way the market is going, breadth, trend, the analysts' cap-weighted upside on the biggest stocks, and what's driving the day: unusual moves in oil, rates, the dollar, gold or bitcoin, sector rotation, and themes like tariffs or the Fed in the headlines), sector performance, watchlist and headlines. |
| **Top Performers** | Scans the S&P 500, Nasdaq-100, Dow 30 or your own list. Scores momentum (12-1 month and steadiness of the climb), trend, reversal (last week and month), earnings surprises, value, quality and growth themes, **within sector**, with adjustable weights and plain-English labels; low risk and analyst views are available but start at zero. The default weights come from a 2000-2026 test on point-in-time S&P 500 members. **Swing setups** lists today's signals for the swing strategy you pick (Dive Zone by default, with its limit price, profit target and signal log; Tech Breakout Rider; or any Strategy Lab template or your own saved rules). **Core longs** applies six pass/fail rules (profitable, uptrend, steady climb (frog-in-the-pan), not too volatile, debt under control, not expensive) and ranks survivors by momentum + smoothness + value; over 2002-2026 its picks returned about the same as the average member but lost more than a fifth in a year far less often (7-10% vs 11-14%). **Could run** lists stocks with the profile that came before most big 12-month winners (volatile, uptrend, strong 6 months, beat the last report) with the honest odds of a big win and a big loss. **Shark Score list** shows SharkFin Ratings (Value, Momentum, Earnings, Pullback, Risk), each 0-100 against the stock's own sector, the overall Shark Score (the average of Value, Momentum and Earnings, the three themes that held up in both halves of the test) and a weekly top-20 list of steady, lower-risk climbers. **Does the ranking work?** shows the 24-year test (and what didn't help: analyst targets and ratings, insider buying) and replays the price and earnings themes monthly over ~4 years, with costs. |
| **News** | Headlines by topic, ranked by BM25 relevance and recency, with noise and near-duplicate removal and finance-specific tone. **Stock catalysts** shows, for one stock, the next earnings date and last surprise, insider buying, estimate revisions, net buybacks, a volume read, SEC filings (from EDGAR, or Yahoo's copy when EDGAR is unreachable) how much the latest 10-K's risk-factor wording changed, and a **big-beat flag** (EPS beat over 5% and a 2-day jump over 4% vs the market). |
| **Strategy Playbook** | SharkFin's two researched growth strategies, condensed: how each works, its record graded on Oct 2021 - Nov 6 2026 (out of sample, including the Nov 2026 selloff), today's signals and a backtest you can run. **Dive Zone** (formerly Leader Dip Plus 7; 27.6% a year, Sharpe 1.13, worst drop 22.5%) swing-buys sharp dips in S&P 500 leaders with idle cash in SPY. **Tech Breakout Rider** (28.9% a year, Sharpe 0.95) rides tech leaders that break out to new highs. **Using both** (70 / 30) and **What we tested** (the VIX/GEX filters, crash guards, momentum rotation and fear-buying that didn't make the cut; see `docs/GROWTH_LAB.md`). SharkFin only reads market data; it never places orders. |
| **Research & Valuation** | For long-term and growth investors. Interactive chart, key stats, and the stock **against its sector**. The **Valuation Lab** has a 3-stage DCF with CAPM WACC, a sensitivity grid, a reverse DCF, a Monte Carlo DCF, peer multiples and a regression multiple, blended into one fair value. **Target & entry** gives a 12-month price target (fair value and the analysts' target combined, with bear and bull cases) and an ideal range to buy in (15% margin of safety under the target, floored at the 200-day average or support, with an RSI-40 pullback hint), plus a long-term checklist. Other tabs: Piotroski F-score, Altman Z, ROIC, financial statements, analyst targets and earnings surprises, news sentiment, and the AI research note. |
| **Forecasts** | Where a stock could be in 1 week to 1 year, in plain language: the middle estimate, the chance it ends higher and the likely range, from five walk-forward-tested models and a fat-tailed volatility model. **What moves it** changes with the timeframe, based on SharkFin's research (price patterns barely predict anything; earnings surprises matter for months): the next report, news and market mood over a week; the last surprise and estimate revisions over months; valuation, growth and business quality over a year. Plus earnings and catalysts (next report, typical report-day move, beats, analyst target, estimate changes, headlines). The model details sit in an expander. |
| **Strategy Lab** | **Build and test**: start from buy and hold, above the 200-day EMA, the golden cross or 12-month momentum (the four that held up in a walk-forward test on 24 large stocks) or build your own by combining rules on 19 indicators with above / below / crosses / rising / falling, plus stop loss, trailing stop, take profit and a time limit. Results read in plain English ("$10,000 became…") with every trade on the chart. **Use as my swing strategy** makes Top Performers use your rules instead of Dive Zone. **Compare strategies** runs them side by side. **Dive Zone** backtests SharkFin's swing system as a portfolio of the S&P 500 or Nasdaq-100. Signals fill at the next open, costs are charged, and idle cash earns the risk-free rate. |
| **Speculation Radar** | Twelve early-stage themes that could be the next Micron or SanDisk (light instead of copper, power behind the meter, nuclear fuel, fusion's supply chain, advanced packaging, rare earths, quantum, space, humanoid robots, drones, AI-discovered drugs, next-gen batteries). Each names its bottleneck, why now, what would prove it, what could kill it and a few listed ways to play it, sorted by risk. A **radar** reads each theme's price action from past prices only: Quiet, **Turning up** (back above its 200-day and beating the S&P 500, the window you want), Running or Cooling. A Micron chart shows what the pattern looked like before its 2025-26 run. Research notes for small positions, not tested strategies. |
| **Portfolio** | Lots, live P/L and CSV import/export. **Risk**: Sharpe, Sortino, max drawdown, VaR/CVaR, beta/alpha, correlation, and risk contribution versus capital weight. **Optimizer**: HRP, risk parity, minimum variance and max Sharpe (Ledoit-Wolf covariance, CAPM-shrunk expected returns), plus the efficient frontier and rebalancing trades. |

## Design notes

- **Forecasts predict returns, not prices, and contain no random noise.** Uncertainty is modelled explicitly, and every model has to beat a random walk out of sample to earn weight.
- **Dive Zone** (`sharkfin/leader_dip.py`, formerly Leader Dip): buy a 2-day RSI under 10 in a stock above its 200-day and in the top 30% of the S&P 500 by 6-month gain, with a limit 3% under the close; sell at the next open after the 2-day RSI closes above 70 or after 10 days; no stop; new trades only while SPY is above its 200-day. It replaced the Confluence Pullback system after an Oct 2026 backtest study on point-in-time S&P 500 members. **Plus 7** (the default since the Oct 2026 strategy lab) adds a quality-point filter (a 2.5 ATR flush, 10%+ under the 52-week high, the sector ETF down 2% in 3 days, or VIX above 20), a profit target at the signal close + 1.5 ATR, an exit on a close under the 200-day, a VIX-above-25 panic exception to the market switch, 7 slots, and idle cash in SPY while SPY is above its 200-day.
- **Tech Breakout Rider** (`sharkfin/breakout_rider.py`): S&P 500 tech and communication stocks plus AMZN and TSLA; buy a close above the prior 20-day high on an up day with ADX(14) above 20 and a top-30% 6-month gain among tech, while QQQ's 21-day EMA is above its 50-day, with a limit half an ATR under the close; sell at the next open when the stock's 21-day EMA closes under its 50-day or after 90 days; 10 slots.
- **TQQQ Day + Night** (`sharkfin/day_night.py`, no longer in the Playbook since Nov 2026; the code stays): the day leg buys TQQQ at a half-hour check (10:00-15:30) when it is above both a noise band (the open, or the prior close if higher, plus the average move from the open to that time over 14 days) and VWAP, and sells under the higher of the two, flat by the close; the night leg decides at 15:30 (market-on-close orders are due by 15:50): if TQQQ sits in the bottom 20% of the day's range so far, it buys the close and sells the next open. Researched on 1-minute bars; the app replays it on 30-minute bars, which give the same trades.
- **Strategy Playbook data** (`sharkfin/research_data/strategy_returns.csv`, `sharkfin/playbook.py`): the research's daily returns for each strategy since 2016 (point-in-time members), so the combined plan can be re-weighted without downloading anything. Settings and weights were chosen on 2016 - Oct 2021 and graded on Oct 2021 - Oct 2026.
- **Every backtest is a sliding walk-forward** (`sharkfin/walkforward.py`): settings are picked on the 3 years before each test year (best after-T-bill Sharpe, averaged with neighbouring settings), a purge gap as long as the longest hold is skipped, and the next year is traded untouched; only those test years are reported. Each run is handed data already cut at the last day it may know, and a missing value may only be carried forward from an earlier record for up to 5 days, never back-filled (`tests/test_leaks.py` fails the build otherwise).
- **Delisted holdings in the factor replay**: a stock that stops trading mid-month is treated as sold at its last price and held as cash, rather than dropped from the average (which quietly handed its money to the survivors). Sector ETFs for Dive Zone's sector-dip point use today's sector labels, a small bias around the 2018 GICS change.
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

On Streamlit Community Cloud, set the main file to `main.py` and add `ANTHROPIC_API_KEY` under *Secrets* if you want the AI analyst. For the TQQQ Day + Night live panel and long intraday backtests, add `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` (a free paper account's keys work; SharkFin only reads market data). Without them it falls back to Yahoo's last 60 days of 30-minute bars. The SEC asks automated clients to identify themselves: optionally add `SEC_USER_AGENT = "SharkFin your@email.com"` to Secrets for the EDGAR filing features. To give each visitor a private, permanently saved portfolio, add Google sign-in and a free Supabase database: see [docs/SIGN_IN_SETUP.md](docs/SIGN_IN_SETUP.md). Without those secrets, portfolio data is stored in `.sharkfin/*.json` (shared by everyone using that server, and reset when a Cloud app restarts); with sign-in on, guests' data lasts only for their visit. Daily phone alerts and the Portfolio threat level are described in [docs/ALERTS_SETUP.md](docs/ALERTS_SETUP.md); voice commands and screenshot import in [docs/VOICE_AND_IMPORT.md](docs/VOICE_AND_IMPORT.md).

## Disclaimer

SharkFin is for education and research. It is not investment advice.
