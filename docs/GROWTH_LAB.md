# Growth lab (Nov 2026)

This is the research behind the November 2026 revamp. SharkFin is aimed at mid- to long-term growth investing,
not day trading. Every number here comes from `python -m sharkfin.growth_lab .lab`. The tables it writes ship in
`sharkfin/research_data/growth_lab/`, and the two strategies' daily returns ship in `growth_returns.csv`.

## Rules

- **Who could be bought:** only stocks that were in the S&P 500 on each date. Stocks that later left the index
  are kept, using `data.sp500_members`.
- **When trades happen:** a signal is set at the close and traded at the next open, or at a limit order the next
  day.
- **Costs:** 0.1% per side.
- **Windows:** settings were picked on Jan 2006 to Oct 12 2021 (the "picking window") and graded on Oct 13 2021
  to Nov 6 2026. The grading window includes the Oct to Nov 2026 selloff.
- **No future data:**
  - A missing price is only ever carried forward from the past, never filled backward from the future.
  - GEX (SqueezeMetrics' daily S&P 500 gamma estimate) and its 1-year percentile are lagged one day.
  - `tests/test_leaks.py` bans backward filling and allows only the two forward shifts that set fill prices
    and outcomes.

## Results

### Strategies (graded Oct 2021 to Nov 6 2026)

| | Return / yr | Sharpe | Worst drop | 2022 | Nov 2026 selloff |
|---|---|---|---|---|---|
| Dive Zone | 27.6% | 1.13 | -22.5% | -6.5% | -20.4% |
| Tech Breakout Rider | 28.9% | 0.95 | -30.6% | -26.2% | -13.3% |
| SPY | 12.5% | 0.56 | -24.5% | -18.2% | -5.5% |
| QQQ | 13.5% | 0.50 | -35.1% | -32.6% | -12.1% |
| Both, 70 / 30 | 29.0% | 1.20 | -19.7% | -12.5% | |

**Dive Zone** (formerly Leader Dip Plus 7) is the only strategy that clearly earns its place:

- On the picking window it made 20.5% a year with a Sharpe of 1.20. SPY made 10.4% with a Sharpe of 0.55.
- It won 64% of its trades and gained 1.5% per trade on average.
- In 2008 it lost 9.5% while SPY lost 46%.
- With fills 0.25% worse on every trade it still made 18.8% a year.

**The Nov 2026 selloff** cut Dive Zone's graded return from 34.1% a year (to Oct 12) to 27.6%. It lost 20% while
SPY lost 5.5%, because it kept buying chip and software leaders as they fell.

**Tech Breakout Rider** earns its place on returns in the waves, but it is lumpy:

- AI wave 1: +84%. The 2026 memory wave: +88%.
- 2006 to 2012: only 4.7% a year.
- Without its five best stocks it made 8.6% a year.

### Waves and crashes

| Window | Dive Zone | Breakout Rider | SPY | QQQ |
|---|---|---|---|---|
| 2008 crash | -9.5% | -4.2% | -46.0% | -43.4% |
| COVID crash | -15.2% | -27.5% | -33.7% | -27.9% |
| 2022 bear | -7.0% | -27.5% | -18.6% | -33.2% |
| AI wave 1 (Jan 2023 to Jul 2024) | +73% | +84% | +51% | +92% |
| Tariff crash (Feb to Apr 2025) | -10.5% | -16.5% | -18.8% | -22.8% |
| Tariff rebound (Apr to Dec 2025) | +60% | +37% | +39% | +48% |
| 2026 memory and AI wave (Jan to Oct 9) | +38% | +88% | +15% | +23% |
| Nov 2026 selloff (Oct 9 to Nov 6) | -20.5% | -14.4% | -5.6% | -12.7% |

### Tested and not adopted

None of these improved results on the picking window:

- **VIX and GEX filters:** 11 tested (VIX ranges, VIX-over-VIX3M backwardation, GEX above or below its 1-year
  median, GEX bottom 20%, GEX positive). None raised the Sharpe on the picking window for either strategy. The
  low-GEX filters cut Dive Zone's Sharpe from 1.20 to 0.82-0.95.
- **Crash guards:** 7 tested: breadth, QQQ or the stock or its sector above its 50-day, SPY 20-day drop, and
  a VIX spike. None helped on the picking window. A 40% breadth guard would have cut the Nov 2026 loss from 20%
  to 14%, but it lowered the picking-window return from 20.5% to 15.7% a year. Adopting it would be fitting the
  last month.
- **Momentum rotation:** the best version on the picking window (top 5 tech stocks by 6-month gain) graded
  21.9% a year with a Sharpe of 0.61. It had a 38% worst drop and lost 31% in Nov 2026. Dropped.
- **Buying fear:** this works as a guide but not as a strategy.
  - After VIX closed above 30, QQQ was higher 6 months later 78% of the time, up 13% on average (6.7% on any
    day).
  - After VIX closed above 40, QQQ was higher 6 months later 95% of the time, up 24% on average.
  - QQQ's 4-6% down days had no edge.
  - A fear-buyer strategy (buy QQQ after VIX spikes, hold 3-12 months) trailed simply holding QQQ.
  - VIX closed above its 3-month version (backwardation) on Nov 5 2026. Six months after past backwardation
    days, QQQ was higher 79% of the time.
- **Day trading:** the TQQQ Day + Night pair left the Playbook. Its edge was 0.2-0.3% a trade and it needed a
  check every 30 minutes.

### Strategy Lab starting points

These were tested walk-forward on 24 large stocks and ETFs:

- Buy and hold had the highest median return, 16.4% a year, but also a 65% median worst drop.
- Trend filters (above the 200-day EMA, golden cross, 12-month momentum) made about 12% a year with 37-49% worst
  drops.
- Dip, breakout and oscillator templates made 4-7%.

The Lab now starts from buy and hold, the 200-day EMA, the golden cross and 12-month momentum.

### Entry ranges

Price-path timing barely matters at 6-12 months. Every S&P 500 stock was checked at each month end since 2006,
by where it stood in its price path. Most entry zones were within a few points of each other and swapped places
between 2006-15 and 2016-26.

The one small, steady edge was buying a leader on a pullback: RSI(14) under 40 while above its 200-day average.
That beat buying any day by 2.5 points over 12 months in 2006-15 and by 0.2 in 2016-26.

So Research's entry range is set by value first:

- The top is the price that leaves 15% upside to the price target.
- The bottom is the 200-day average or the nearest support.
- The RSI-40 pullback price is a timing hint inside the range.

### What moves a stock at each horizon (Forecasts)

**Price patterns barely predict anything** (`horizon_signals.csv`):

- The test: S&P 500 members at each month end, 2006-26, measured by the rank correlation (IC) with the return
  from the next open.
- The signals tested: last week's and last month's move, 6- and 12-month momentum, closeness to the 52-week
  high, the 200-day average, and low volatility.
- Every one had an IC of 0.05 or less at every horizon from a week to a year, and most flipped sign between
  2006-15 and 2016-26.

**Earnings surprises matter for months** (`earnings_horizons.csv`):

- The test: 17,800 reports from 195 random S&P 500 stocks, 2007-26, measured vs SPY from the open after the
  reaction day.
- The top fifth of EPS surprises beat the bottom fifth by:
  - 0.6 points over 1 month
  - 1.4 points over 3 months
  - 2.7 points over 6 months
  - 7.4 points over 12 months
- Most of that came from a few big winners and from 2021-26. The median stock in the top fifth was only about
  a point ahead at 6 months.
- The size of the next-day jump mattered less than the surprise itself.

**Forecasts therefore leads each timeframe with different drivers:**

| Timeframe | Drivers |
|---|---|
| 1 week | The next report, then news, then the market's mood |
| 1-3 months | The next report, the last surprise, then estimate revisions |
| 6 months | Revisions, expected growth and the last surprise |
| 1 year | Valuation (P/E vs growth), growth, business quality and the analyst target, with a VIX spike as the best entry |

These timeframes follow the published research: post-earnings drift (Bernard & Thomas 1989), estimate revisions
(Chan, Jegadeesh & Lakonishok 1996) and profitability (Novy-Marx 2013).

## Caveats

- Both strategies were picked from many variants. The graded window is a single period.
- The earnings study only covers stocks Yahoo still lists, which tilts it slightly toward survivors.
- Yahoo has no point-in-time history for estimates or analyst targets, so those drivers rest on published
  research, not on SharkFin's own backtest.
- GEX is SqueezeMetrics' S&P 500 estimate, not a measure for single stocks.
