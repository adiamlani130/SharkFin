# NQ strategy lab: results (October 2026)

29 short-term strategies on the Nasdaq-100 (19 swing, 10 day trades) were graded with SharkFin's walk-forward
engine: settings picked on 3 trailing years, then run untouched on the next year, sliding forward. Every number
below is from those unseen test years only. Code: `sharkfin/nq_lab.py`. Leak tests: `tests/test_nq_lab.py`.
Full table: `docs/nq_lab/results.csv`.

**Bottom line.** Nothing beat simply holding NQ on raw return. Three swing strategies beat it on risk:
IBS reversion, IBS with a VIX filter and RSI(2) dip buying in a calm regime. They earned less, but with
less than half the drawdown and far less time in the market. No day-trade strategy is worth trading after costs.
GEX is a good map of how wild a day will be. As a buy or sell signal on its own, it did little.

## Data: what was real and what was approximated

| Input | Source | Real or approximated |
| --- | --- | --- |
| NQ price | QQQ (split/dividend adjusted), Yahoo daily 1999+ | Proxy. QQQ and NQ both track the Nasdaq-100. P&L is QQQ's return over T-bills, which is what an NQ future earns. |
| Intraday NQ | QQQ 5-minute bars (SIP feed), Alpaca, Jan 2016 to Oct 2026, regular hours, 2,713 full sessions | Proxy at 5-minute granularity. No NQ overnight session. |
| VIX, VIX9D, VIX3M | Cboe indexes via Yahoo | Real |
| GEX | SqueezeMetrics daily S&P 500 dealer-gamma estimate, May 2011+ | Real history, but for the S&P 500, not the Nasdaq-100, and as one total. |
| GEX levels (call wall, put wall, zero-gamma strike) | No free strike-level history exists | Approximated with QQQ's whole-$5 strikes, where open interest clusters. Prior-day high and low were also tried as levels. |
| Costs | 1 bp per side (about 1-2 NQ ticks plus commission) | Assumption |

## How the backtests avoid leakage

- **Walk-forward, sliding:** the repo's `walkforward.run`, with 3 years to train and 1 year to test. Folds never
  overlap, and only test years are reported. Settings are chosen by neighbour-smoothed Sharpe, so a stable region
  beats a lone spike.
- **Cut data:** each run only receives data up to the last day it may know.
- **Fills:** a swing decision made at the close fills at the next open. A day-trade decision made at a bar's close
  fills at the next bar's open. If a stop and a target are hit in the same bar, the stop counts. Day trades are
  flat by 15:55.
- **Timing:** VIX is taken from the prior close for day trades. GEX is the prior session's value, ranked only
  against the 252 sessions before it.
- **Tests:**
  - For every strategy, results and positions up to a date are identical whether or not later data exists.
  - A planted strategy that peeks one day ahead fails that check.
  - Scrambling every bar after 12:50 changes no decision made before it.
  - The repo's no-back-fill and no-negative-shift scans still pass.
- **Multiple testing:** 29 strategies and about 1,500 setting combinations were tried. The deflated Sharpe column in
  `results.csv` is the chance a result beats the best that luck alone would give. No strategy clears it. The best,
  IBS reversion, scores 0.49.

## Swing results (test years May 2015 to Oct 2026)

| Strategy | Sharpe | Return over cash / yr | Worst drop | Time in market | Test years beating cash |
| --- | --- | --- | --- | --- | --- |
| IBS reversion | 0.97 | +11.9% | -15% | 35% | 100% |
| IBS with regime filter | 0.92 | +7.7% | -13% | 17% | 83% |
| Buy and hold | 0.80 | +17.6% | -35% | 100% | 92% |
| Dip buying in calm regime | 0.75 | +9.6% | -18% | 35% | 83% |
| Vol-targeted EMA trend | 0.74 | +14.8% | -39% | 83% | 92% |
| EMA crossover | 0.74 | +12.5% | -25% | 84% | 92% |
| Regime vote (EMA+VIX+GEX) | 0.69 | +10.5% | -35% | 91% | 83% |
| GEX switch | 0.67 | +12.2% | -23% | 84% | 100% |
| Swing rotation: best 3 on training | 0.67 | +6.5% | -14% | 72% | |
| RSI(2) dip | 0.60 | +8.3% | -24% | 36% | 75% |
| VIX term structure | 0.60 | +10.8% | -35% | 87% | 83% |
| MACD trend | 0.58 | +6.6% | -20% | 50% | 83% |
| VIX trend | 0.57 | +7.8% | -32% | 69% | 75% |
| Donchian breakout | 0.53 | +7.1% | -23% | 65% | 83% |
| EMA trend, VIX-sized | 0.52 | +6.8% | -24% | 77% | 83% |
| EMA trend pullback | 0.51 | +6.5% | -24% | 27% | 75% |
| Overnight hold | 0.45 | +3.1% | -11% | 42% | 83% |
| Swing rotation: best 1 on training | 0.43 | +4.7% | -17% | 30% | |
| GEX regime | 0.29 | +4.5% | -39% | 78% | 67% |
| VIX9D inversion buy | 0.28 | +4.1% | -25% | 21% | 67% |
| VIX spike buy | 0.24 | +3.5% | -29% | 28% | 67% |

## Day-trade results (test years Apr 2019 to Oct 2026)

| Strategy | Sharpe | Return over cash / yr | Worst drop | Time in market | Test years beating cash |
| --- | --- | --- | --- | --- | --- |
| Intraday momentum (last 30 min) | 0.41 | +1.8% | -8% | 6% | 50% |
| Gap and go | 0.26 | +0.7% | -7% | 9% | 50% |
| Long open to close (benchmark) | 0.14 | +2.5% | -27% | 100% | 50% |
| VWAP + EMA trend | -0.02 | -0.2% | -20% | 19% | 50% |
| 5-min EMA cross | -0.10 | -1.0% | -22% | 38% | 50% |
| Opening range breakout | -0.22 | -1.6% | -20% | 53% | 75% |
| Bollinger fade | -0.41 | -0.9% | -5% | 5% | 25% |
| Prior-day high/low levels | -0.43 | -5.0% | -33% | 85% | 38% |
| $5 strike magnet (GEX-level proxy) | -0.68 | -3.2% | -17% | 21% | 12% |
| Gap fade | -0.74 | -3.9% | -26% | 16% | 38% |

With zero costs, gap and go reaches a 0.67 Sharpe, the 5-minute EMA cross 0.28 and opening range breakout 0.08.
Costs are what sink them. Intraday momentum made almost all of its money in 2020.

## How the strategies that held up work

- **IBS reversion.** IBS is where the close sits in the day's range: (close - low) / (high - low).
  - Entry: IBS closes under about 0.2.
  - Fill: the next open.
  - Exit: a close over 0.8, a close over the prior day's high, or after 5 days.
  - Record: every test year beat cash. Most of the edge came in 2015 to 2021, and it has been smaller since 2023
    (2 to 7% a year).
- **IBS with regime filter.** The same trade, taken only in one VIX or GEX regime. Training picked VIX above 20
  in 2015 to 2019, then changed its pick almost every year, so the filter itself isn't reliable. It is in the
  market 17% of the time, with a worst drop of 13%.
- **Dip buying in calm regime.** Buys an RSI(2) reading under 30, unless the VIX curve is deeply inverted
  (VIX/VIX3M over 1.1). It sells when RSI(2) gets back over 65. The GEX filter was picked in early years and
  dropped from 2021 on, so the VIX curve does the work. It made money in 2022 (+3.9% over cash) while NQ fell 36%.
- **GEX switch.** When GEX is above its 20th to 50th percentile for the past year, it holds NQ while price is over
  the 100- or 200-day EMA. On low-gamma days it only buys RSI(2) washouts. Every test year beat cash, and its worst drop was
  23% against 35% for holding.

## What GEX showed

GEX (prior session, ranked against the past year) sorts the next day's QQQ range cleanly:

| GEX rank | Days | Average high-low range | Average open-to-close move | Average VIX |
| --- | --- | --- | --- | --- |
| Bottom 20% | 494 | 2.42% | 1.29% | 25.3 |
| 20-50% | 678 | 1.57% | 0.83% | 19.4 |
| 50-80% | 760 | 1.26% | 0.67% | 16.8 |
| Top 20% | 765 | 1.02% | 0.50% | 15.0 |

On the lowest-gamma days, the first half hour's move points the same way as the last half hour's (correlation
0.13). On high-gamma days it doesn't (-0.08). That fits dealers' short-gamma hedging chasing the move. This table
describes the whole sample, so it is a description, not a tested trade. GEX used alone to time entries (the GEX
regime and $5 strike magnet strategies) did poorly out of sample.

## Rerun

```
python -m sharkfin.nq_lab fetch DATA_DIR                # Yahoo daily + Alpaca 5-minute bars
# save https://squeezemetrics.com/monitor/static/DIX.csv as DATA_DIR/DIX.csv
python -m sharkfin.nq_lab DATA_DIR OUT_DIR              # writes results.csv and returns.csv
```
