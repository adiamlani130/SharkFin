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
python -m sharkfin.nq_regimes DATA_DIR OUT_DIR          # routers, gates and level maps (part 2)
```

# Part 2: GEX and VIX as a daily playbook

**Bottom line.** Using VIX and GEX to choose today's strategy, or to decide whether to trade at all, did not
beat simply running the strategies. The routers and gates mostly sat out good days. One rule worked out of
sample: **buy NQ at the open and sell at 15:55 only after a fearful close**, meaning VIX high and GEX low. It
earned a 0.83 Sharpe and +7.7% a year over cash, in the market 9% of the time, with a -9% worst drop.
Code: `sharkfin/nq_regimes.py`. Tables: `docs/nq_lab/regime_results.csv` and `docs/nq_lab/levels_*.csv`.

## What was tested

- **Regime cells**, from what is known before the decision:
  - VIX bands: under 15, 15-20, 20-25, 25-30 and 30+.
  - GEX rank against the past year, in fifths.
  - VIX/VIX3M curve bands.
  - VIX band × GEX third.
  - GEX third × curve.
  - VIX rising or falling × GEX third.
- **Router:** each morning (day trades) or close (swing), it looks up today's cell. It runs the candidate that
  earned the most in that cell on past days only, or sits out if nothing cleared a confidence bar. It re-learns
  monthly from finished days, and walk-forward picks its scheme, bar and memory length each year.
  - 11 day-trade candidates: long or short open-to-close, two opening-range versions, gap and go, gap fade,
    last-30-minute momentum, VWAP trend, Bollinger fade, and prior-day level fade and break.
  - 7 swing candidates: long, short, IBS, RSI(2), EMA trend, Donchian and VIX-spike buy.
- **Gates:** one strategy, traded only in cells where it has made money before.
- **Fixed regime rules**, with thresholds picked walk-forward: fear-day long (day), fear bounce (swing), and a
  regime-sized long.

## Results (unseen test years; swing May 2015 to Oct 2026, day trades Apr 2019 to Oct 2026)

| Strategy | Sharpe | Return over cash / yr | Worst drop | Time in market | Same strategy without the regime |
| --- | --- | --- | --- | --- | --- |
| Fear day long (day) | 0.83 | +7.7% | -9% | 9% | Long open to close: 0.14 |
| Swing gate: IBS reversion | 0.83 | +10.7% | -18% | 33% | IBS reversion: 0.97 |
| Regime-sized long | 0.76 | +20.0% | -39% | 100% | Buy and hold: 0.80 |
| Swing gate: Long NQ | 0.59 | +10.5% | -28% | 79% | Buy and hold: 0.80 |
| Swing router | 0.54 | +8.8% | -28% | 72% | Best fixed swing strategy: 0.97 |
| Day gate: last-30-min momentum | 0.47 | +2.0% | -8% | 3% | Ungated: 0.41 |
| Fear bounce (swing) | 0.43 | +6.1% | -23% | 16% | Buy and hold: 0.80 |
| Day gate: gap and go | 0.15 | +0.5% | -5% | 14% | Ungated: 0.26 |
| Day router | -0.05 | -0.5% | -19% | 49% | |
| Day gate: ORB 30 min | -0.09 | -0.4% | -8% | 23% | |

The routers didn't settle on a scheme. The day router used VIX, GEX × curve, VIX × GEX and VIX-move in
different years, and its favourite pick was "no trade" (29% of days). Cells hold a few hundred days at most, so
the "best strategy in this cell" mostly changes with noise.

## Fear day long, checked

- **Rule:** after a close with VIX at or over 20 to 30 and GEX in its lowest 20 to 50% of the year, buy the
  09:35 open and sell at 15:55.
- **By year (over cash):**
  - 2020: +21.7% on 45 trades
  - 2021: +4.2% on 4 trades
  - 2022: +8.8% on 42 trades
  - 2025: +12.5% on 36 trades
  - 2026 so far: +9.5% on 37 trades
  - 2019, 2023 and 2024 had almost no fear days. It is not a 2020-only effect.
- **Fixed thresholds, 2017 to 2026:** every combination tried was positive, with Sharpes of 0.25 to 0.70.
  Adding "GEX low" beat "any GEX" at every VIX level. For example, at VIX 25 or more it was 0.45 with GEX in its
  bottom 20% against 0.25 with any GEX.
- **Caution:** it trades only about 40 days in a fearful year, so most years it does nothing.

## What each level meant (whole-sample description, not a tested trade)

Average NQ open-to-close return the next session, in basis points, with the number of days in brackets. The
history is split in two halves to see whether the pattern held:

| Cell (VIX at prior close, GEX rank) | 2016 to mid-2019 | Mid-2019 to 2026 |
| --- | --- | --- |
| VIX under 17, low GEX | +9.1 (90) | -7.5 (39) |
| VIX under 17, mid GEX | -4.5 (241) | -7.1 (193) |
| VIX under 17, high GEX | +0.4 (343) | -4.1 (489) |
| VIX 17-24, low GEX | -12.4 (117) | +1.8 (231) |
| VIX 17-24, mid GEX | +0.3 (33) | +9.4 (252) |
| VIX 17-24, high GEX | +2.8 (6) | -1.1 (218) |
| VIX 24+, low GEX | **+19.6 (40)** | **+16.8 (247)** |
| VIX 24+, mid GEX | none | +0.3 (98) |
| VIX 24+, high GEX | none | -17.8 (60) |

- **High VIX with low GEX** is the only cell that was strongly positive in both halves. It also had the widest
  days: a 2.9% average range against 0.9% for calm, high-gamma days.
- **Calm days** (VIX under 17) drifted slightly down during the session. NQ's gains on those days came
  overnight.
- **Day strategies by cell:**
  - Breakouts (prior-day level break, opening range) did best with VIX 17-24 and low GEX: +6 to +7 bp a day.
  - VWAP trend lost most on high-GEX days.
  - Shorting open-to-close only paid with VIX 24+ and high GEX (+14 bp, but only 60 days).
- **VIX/VIX3M above 1** (curve inverted) was the best curve band for buying the open (+18 bp) and for IBS and
  RSI(2) dips the next day.

# Part 3: three GEX setups (call-wall fade, negative-gamma breakout, OpEx fly/condor)

Code: `sharkfin/nq_gex_plays.py`. Rerun with `python -m sharkfin.nq_gex_plays DATA_DIR OUT_DIR`. Same walk-forward
grading and leak rules as Parts 1 and 2 (out-of-sample years about 2019-04 to 2026-10, decisions only from
finished bars, flat by 15:55, GEX from the prior session).

## What was real and what was approximated

- **Gamma flip:** real. "Above the flip" means SqueezeMetrics GEX (S&P, not Nasdaq) was positive the prior
  session; "below the flip" means it was negative (274 days since 2016, 104 of them in 2022). "Top-half" and
  "bottom-20%" rank GEX against the prior 252 sessions only.
- **VIX regime:** real. Quiet = VIX under a cap and not above its 5-day average; rising = VIX up on the day and
  above its 5-day average.
- **Call and put walls:** approximated. There is no free strike-level open-interest history, so the walls are
  stand-ins, each tried and picked by the walk-forward: the next round $5 or $10 QQQ strike past the prior
  close, one VXN-implied daily move, or the 20-session high/low.
- **Options (setup 3):** modelled, not real quotes. A same-day iron butterfly/condor on QQQ is priced with
  Black-Scholes using the prior VXN close as the volatility, entered at 09:35 and held to the close (or stopped
  out). $0.01 a leg each way, 2% of the account risked per trade. No skew and no real bid/ask, so treat those
  numbers as an upper bound. A second run marks the options 15% cheaper (IV x0.85) to show how sensitive it is.

## Does GEX shrink the day? Yes

NQ's 09:35-to-close move as a fraction of the VXN-implied daily move:

| Days | Count | Move / implied | Stayed inside 1 implied move |
| --- | --- | --- | --- |
| All days | 2,595 | 0.50 | 88% |
| Positive GEX + quiet VIX | 1,374 | 0.46 | 90% |
| Top-half GEX + quiet VIX | 1,051 | 0.43 | 92% |
| GEX below flip | 254 | 0.68 | 79% |
| GEX below flip + VIX rising | 140 | 0.68 | 81% |
| OpEx Fridays | 125 | 0.50 | 84% |
| OpEx Fridays, top-half GEX + quiet VIX | 59 | 0.43 | 90% |

The "vol map" idea holds: high-gamma quiet days move about 15% less than implied, below-flip days about 35% more.
OpEx Fridays on their own were not special.

## Results (out of sample)

| Setup | Sharpe | Over cash / yr | Max drop | Trades | Hit rate |
| --- | --- | --- | --- | --- | --- |
| 1. Call-wall fade, positive GEX + quiet VIX | -0.56 | -0.8% | -1.9% | 127 | 31% |
| 1. Call-wall fade, top-half GEX + quiet VIX | -0.87 | -1.2% | -2.9% | 116 | 33% |
| 1. Call-wall fade, every day (control) | -1.10 | -3.7% | -10.3% | 454 | 28% |
| 2. Breakdown short, below flip + VIX rising | -0.78 | -2.5% | -17.6% | 67 | 21% |
| 2. Breakdown short, bottom-20% GEX + VIX rising | -1.01 | -2.6% | -13.6% | 58 | 14% |
| 2. Breakdown short, below flip | -0.55 | -2.7% | -18.0% | 168 | 28% |
| 2. Breakout either way, every day (control) | 0.14 | +1.3% | -22.2% | 915 | 44% |
| 3a. Pin toward nearest strike, top-half GEX + quiet | -0.37 | -0.3% | -1.3% | 30 | 37% |
| 3a. Pin toward nearest strike, every expiration (control) | 0.07 | +0.2% | -10.5% | 133 | 54% |
| 3b. Iron fly/condor, top-half GEX + quiet VIX | 2.91 | +7.1% | -1.3% | 148 | 85% |
| 3b. Iron fly/condor, positive GEX + quiet VIX | 2.91 | +7.2% | -1.7% | 175 | 82% |
| 3b. Iron fly/condor, every Friday (control) | 3.80 | +14.8% | -2.3% | 374 | 81% |
| 3b. Same, top-half GEX + quiet, IV x0.85 | 2.05 | +4.6% | -2.0% | 148 | 82% |
| 3b. Same, every Friday, IV x0.85 | 2.24 | +9.3% | -4.9% | 374 | 74% |

- **1. Call-wall fade:** lost money. Price tagging the "wall" kept going more often than it reversed (hit rate
  about 30%). Gating to positive-gamma quiet days lost less than fading every day, but it still lost.
- **2. Negative-gamma breakout:** lost money. Below-flip days are wide, but they whip both ways: shorting the
  break under the put wall was right only about 1 time in 5, and the misses included sharp squeezes. Taking
  breakouts both ways every day was roughly flat.
- **3a. OpEx pin with futures:** nothing. Leaning toward the nearest strike late on expiration Fridays was
  flat to slightly negative.
- **3b. Iron fly/condor:** the only setup that made money, but the GEX/VIX filter did not help. Selling every
  Friday beat selling only on positive-gamma quiet Fridays. Per trade, the filtered days did pay more (with IV
  x0.85, about +31% of risk on filtered Fridays against +17% on the rest for an ATM fly), and below-flip Fridays
  lost. So GEX works as a "skip today" switch for short premium, not as an edge by itself.
- **Why 3b looks so good:** the model sells at VXN, a 30-day implied vol, while the realised 09:35-to-close move
  is about half of that. Real 0DTE QQQ options are priced closer to realised intraday vol, carry skew, and cost
  more than a cent to trade, so the real edge is likely much smaller. Mark it 30% cheaper (IV x0.7) and selling
  every Friday is roughly break-even, while the filtered Fridays still earn about +15% of risk a trade. This
  needs checking against real option quotes before anyone trades it.
