# The Sharpe-2 hunt: stock strategies and options strategies (Nov 2026)

You asked for strategies with a Sharpe above 2, or a very high win rate with big profits, drawing on everything we've tested in this project, plus options strategies: earnings, multiples, news and our own signals as triggers, and a Black-Scholes pricer with an implied-vol surface to look for an edge. This is the write-up. It is research only. The app is unchanged.

## The short version

1. **Without options, nothing gets near 2.** I tried 109 setups and blends of stocks and ETFs, including every earlier lab's best idea. The best result in the grading window is still **Dive Zone, at a Sharpe of 1.12** (1.23 with the round-2 filters). Blends, hedges and leverage don't lift it: leverage doesn't change a Sharpe, and our good strategies all move with the market, so blending them doesn't diversify much.
2. **One options trade got to about 2 out of sample on real prices: selling same-day (0DTE) QQQ iron flies and iron condors, skipping days when dealer gamma (GEX) is negative.** On real option prices from 2024 to 2026, the version chosen on 2024 alone scored a **Sharpe of 1.98 in 2025-2026** (+37% a year, worst drop -11%, wins 63% of days). A close cousin scored 2.49. It made money in all three years, and better each year. The catch: the history is short (under 3 years), and it is **very sensitive to trading costs**. With 3 cents of slippage a leg instead of 1.5, the Sharpe falls to 1.63. At 5 cents it falls to 1.16. It also risks 2% of the account every trading day, and a bad day loses the full 2%.
3. **The "99% win rate" trades are a trap, and the test shows it.** Over 20 years, the best put-selling setup on the picking window (weekly 10-delta/3-delta S&P put spreads in calm markets) had a **Sharpe of 2.15 and won 99% of the time from 2006 to 2021. From late 2021 its Sharpe was 0.18.** That is exactly the overfit, small-wins-and-rare-big-losses shape we were watching for.
4. **Earnings options had no edge after costs.** On 821 real reports (77 stocks, 2024-2026), the usual "implied move is too big, sell it" idea is mostly right on direction, since stocks moved about 81% of what the options priced. But single-stock spreads eat the difference. None of the confluences (beat record, P/E, the drop into the report, news volume, VIX) held up in both windows.
5. **Trading our own signals with options was worse than shares.** Dive Zone trades made +1.6% a trade in shares, -1.2% buying calls and +0.4% selling puts. Breakout Rider calls looked huge (+137% a trade), but only 17 trades had usable option prices, so that proves nothing yet.

Honest bottom line: **the 0DTE QQQ condor/fly with a "skip negative-GEX days" switch is the only thing in this project that has reached about 2 out of sample. It is still young and it lives on execution quality.** If you want to pursue it, the next step is paper-trading it with real fills for a few months, not adding it to the app as a signal.

---

## How everything was tested

- **Pick, then grade.** Every choice of settings was made on the picking window only, then run untouched on the grading window. For stocks and the 20-year options model, that means picking on 2006 to Oct 12 2021 and grading from Oct 13 2021 to Nov 2026, the same split as every earlier lab. Real option prices only start in February 2024, so the real-price tests pick on Feb-Dec 2024 and grade on Jan 2025 to Nov 13 2026.
- **No look-ahead.** A signal seen at a close fills at the next open. Option trades use only what was known at entry: the prior close's VIX, VIX1D, VIX9D and GEX, the first 15 minutes of the day, past earnings moves, past EPS and past news.
- **Costs are in every number.** That's 3-10 basis points a side on ETFs. For QQQ/SPY options it's $0.015 a leg of slippage plus $0.65 a contract. Single-stock options pay 1.5% of the option price a side.
- **Counted tries.** About 350 setups in all: 109 stock/ETF, 49 in the 20-year options model, 128 for 0DTE (each also re-run at two higher cost levels) and about 60 for earnings and our signals. With that many tries, a few setups will look great by luck, which is why only results that hold in the grading window count.

### Data

| What | Source | Real or modelled |
| --- | --- | --- |
| ETF and stock prices, 1999-2026 | Yahoo | Real |
| VIX, VIX1D, VIX9D, VIX3M, VXN, S&P 500 | Cboe via Yahoo | Real |
| GEX (dealer gamma) | SqueezeMetrics daily, S&P 500 | Real, but S&P rather than Nasdaq |
| **Option prices, Feb 2024 to Nov 2026** | **Alpaca (OPRA trade bars)**: 5-minute bars for 0DTE QQQ and SPY on 700 days, hourly bars for 821 earnings reports, daily bars for our own trades and for SPY chains | **Real trade prices.** There is no bid/ask history, so a spread cost is added on top. |
| Option prices, 2006-2024 | Black-Scholes on a vol surface fitted to real 2024 SPY chains | Modelled (checked below) |
| Earnings dates, EPS and surprises | Yahoo | Real |
| News | Alpaca headline counts in the week before each report | Real |

Alpha Vantage's historical options are a premium endpoint, so it wasn't used.

---

## 1. Stocks and ETFs: nothing reaches 2

| Strategy (best settings on 2006-2021) | Pick Sharpe | Grade Sharpe | Grade yearly | Grade worst drop |
| --- | --- | --- | --- | --- |
| **Dive Zone (app version)** | **1.20** | **1.12** | +27.5% | -23% |
| Tech Breakout Rider (app version) | 0.80 | 0.94 | +28.8% | -31% |
| 50/50 Dive Zone + Breakout | 1.09 | 1.16 | | -19% |
| Blend of every pick-window winner (inverse volatility) | 0.98 | 0.65 | +10.4% | -15% |
| Same blend without the short-volatility pieces | 1.02 | 0.70 | +10.7% | -13% |
| Dive Zone hedged with QQQ (market-neutral) | 0.81 | 1.11 | +20.8% | -17% |
| IBS dip-buying, 19 US equity ETFs | 0.76 | 0.39 | +7.3% | -11% |
| IBS on QQQ (next-open fill) | 0.80 | 0.18 | +5.5% | -19% |
| IBS on QQQ (market-on-close fill, generous) | 0.95 | 0.69 | | |
| RSI(2) dip-buying, 19 ETFs | 0.61 | 0.26 | +5.9% | -10% |
| Short volatility (SVXY) in VIX contango | 0.70 | 0.24 | +6.3% | -44% |
| SPY only when the VIX curve is steep | 0.68 | 0.39 | +8.3% | -25% |
| Cboe PutWrite index (real ATM put selling) | 0.41 | 0.55 | +9.5% | -16% |
| Trend following, 21 asset ETFs | 0.49 | -0.44 | +1.6% | -11% |
| Turn of the month | 0.40 | -0.36 | | |
| Fear day long (QQQ, daily bars) | 0.22 | -0.06 | | |
| Overnight hold (buy close, sell open) | -0.34 | -0.65 | | |
| Buy and hold SPY / QQQ | 0.55 / 0.74 | 0.55 / 0.50 | | |

Sharpes are over T-bills. What it means in plain terms:

- **Dive Zone is still our best risk-adjusted strategy**, and adding the round-2 filters brings it to 1.23.
- **Blending doesn't help here.** Dive Zone, Breakout Rider and the market are 55-65% correlated, so the blend's risk falls less than you'd hope. Putting the low-risk dip-buyers in the blend dragged it down, because they have faded since 2021.
- **The classic "high Sharpe" ideas you read about mostly died after 2021:** IBS, RSI(2), turn of the month and overnight holds. Several only look good with market-on-close fills or before costs.
- **Short volatility (SVXY)** had a 0.70 Sharpe on the picking window, then fell 44% in the grading window. It's the rare-big-loss shape.

## 2. Black-Scholes and the implied-vol surface

`sharkfin/bs.py` prices options, solves for implied volatility and fits a smile to real prices. The smile is a quadratic in standardised moneyness, ln(K/F)/√T: level, skew and curvature for each expiry, interpolated across expiries in total variance.

What fitting it to real prices showed:

- **The S&P surface is very stable relative to VIX.** I fit the shape (skew and curvature as straight lines in VIX) on 2024 SPY chains only. On the 2025-2026 chains it had never seen, it priced 1-week, 1-month and 2-month options within **0.1-0.5 vol points** across strikes. So a calibrated surface plus the day's VIX is a good stand-in for real S&P option prices over the past 20 years.
- **The model matches Cboe's real PutWrite index.** Selling the at-the-money 1-month put every 21 days on the model has a 0.86 correlation with the real index's 21-day returns, and the same average (+0.68% vs +0.66% a period).
- **The old NQ-lab iron fly was mispriced, and now we know by how much.** It priced same-day QQQ options off VXN. Real 0DTE QQQ options trade at about **0.67x VXN** (and about 1.0x VIX1D), which is why that model's Friday fly showed a Sharpe of 3.8. **On real prices, Fridays only give 0.3-0.6.**
- **Is there an edge in the surface itself?** On QQQ, the 09:45-to-close move averaged **91%** of what the same-day straddle priced. On earnings, the median move was **81%** of the priced move. Options are slightly rich on average. That edge is small, and for single stocks it is smaller than the bid/ask spread.

## 3. Twenty years of S&P premium selling (model, checked above)

Forty-nine setups were tried: at-the-money puts, 20/5-delta and 10/3-delta put spreads, and 16/5-delta iron condors, weekly and monthly. Each was run with no filter, VIX contango, VIX above or below 20, GEX positive, S&P above its 200-day, and contango with VIX at 16 or more. Spreads risk 5% of the account per trade. Results are held to expiry and settled on the real S&P close.

| Setup | Pick Sharpe | Pick win rate | Grade Sharpe | Grade win rate |
| --- | --- | --- | --- | --- |
| **Weekly 10/3-delta put spread, contango + VIX ≥ 16** (pick-window winner) | **2.15** | **99%** | **0.18** | 96% |
| Weekly iron condor, contango + VIX ≥ 16 | 1.25 | 91% | -0.24 | 85% |
| Weekly iron condor, S&P above 200-day | 1.19 | 86% | 0.40 | 83% |
| Monthly ATM put, S&P above 200-day | 0.91 | 87% | 0.89 | 84% |
| Monthly ATM put, no filter | 0.66 | 79% | 0.87 | 75% |
| Cboe PutWrite index (real) | 0.56 | 73% | 0.75 | 72% |

The setup that won the picking window with a 2.15 Sharpe and a 99% win rate collapsed to 0.18 out of sample. That's what most "insane win rate" option strategies look like when tested honestly: lots of small wins, then a few losses that wipe out months of them. Plain monthly put selling with a 200-day trend filter was the steadiest, at about 0.9 in both windows.

## 4. Same-day (0DTE) QQQ and SPY: the one near-2 result

**Setup.** At 09:45 New York each day, sell an iron fly (short the at-the-money call and put, long wings 0.5%, 1% or 1.5% away) or an iron condor (shorts at 0.5x or 1x the straddle's implied move, wings $2 or $5 further out). Hold to the close. Entry prices are the real volume-weighted trade prices in the 09:45-09:50 bar. Each trade risks 2% of the account. The 8 day filters were every day, Fridays, GEX positive, GEX top half with quiet VIX, no event priced (VIX1D ≤ VIX9D), a quiet first 15 minutes, implied above our forecast move, and rich + GEX positive + no event.

**Picked on 2024 (at least 50 trades), graded on 2025 to Nov 2026:**

| Pick-window winner | 2024 Sharpe | 2025-26 Sharpe | 2025-26 yearly | Win rate | Worst drop | 2025-26 Sharpe at 3¢ / 5¢ slippage |
| --- | --- | --- | --- | --- | --- | --- |
| **QQQ iron fly, ±1.5% wings, GEX positive days** | 1.28 | **1.98** | +37% | 63% | -11% | 1.63 / 1.16 |
| QQQ iron condor (0.5x move, $5 wings), GEX positive | 1.19 | 2.49 | +54% | 64% | -11% | 1.96 / 1.26 |
| SPY iron condor (1x move, $5 wings), GEX top half + quiet VIX | 1.71 | 1.10 | +5% | 75% | -4% | 0.60 / -0.07 |

- **By year**, the QQQ fly on GEX-positive days scored a Sharpe of 1.28 in 2024, 1.88 in 2025 and 2.09 in 2026. Its worst month was April 2025 (-7%).
- **GEX works as a "skip today" switch, again.** That matches the NQ lab. On QQQ, GEX-positive days beat every day for every structure in the grading window: 1.98 against 1.54 for the 1.5% fly.
- **Most short setups made money in 2025-26** (94% of them had a positive Sharpe), and 8 of 128 cleared 2. **Buying same-day options lost**: straddles every day had a Sharpe of about -2, and buying calls on "fear days" averaged about 0 with a median of -100%.
- **QQQ beat SPY**, even though both were priced about equally rich (each moved about 91% of its implied move). My guess is that QQQ's bigger premiums cover the fixed cents of cost better, but I didn't test that.

**Why to be careful before trusting the 1.98:**

1. **It's a short record**: 2.8 years, with only 11 months to pick on. A Sharpe measured over 2 years has an error band of roughly ±0.7.
2. **Costs decide it.** The edge is a few cents a trade. Good limit-order fills keep it. Market orders or wider spreads kill it.
3. **Some wing prices are modelled.** The far wings didn't always trade in the 09:45 bar. Those (about 40% of trades on the 1.5% QQQ fly, more on SPY) are priced off that morning's fitted smile. Wings are cheap, so the error is small, but it isn't zero.
4. **It's real short-volatility risk, sized hard.** Every trading day risks 2% of the account, and the worst days lose all of it. The +37% a year comes from taking about 250 of those bets a year.

## 5. Earnings options (821 real reports, 77 stocks)

**What I tested.** Sell or buy the at-the-money straddle on the first expiry after the report: enter in the last hour before the report, exit 10-11 AM the morning after. I also tested a defined-risk fly (wings at 1.5x the implied move), and a 30-45 day call bought after the report for post-earnings drift.

**The confluences** were all known before entry:

- the implied move vs the stock's last 8 earnings moves (rich or cheap)
- the beat record
- trailing P/E, from the past 4 reported EPS
- a 15%+ drop in the 3 months before the report
- distance from the 52-week high
- VIX
- the number of news headlines in the week before, compared with the stock's own norm

| Trade | Best idea | Pick (2024) | Grade (2025-26) |
| --- | --- | --- | --- |
| Sell straddle, all reports | | -0.6% of the stock price a trade, 51% win | -0.1%, 62% win |
| Sell straddle when implied > 1.2x past moves | the classic "IV crush" trade | +0.3%, 60% win | -0.3%, 61% win |
| Sell straddle, rich + P/E under 25 | multiples | +0.5%, 67% win | -0.1%, 64% win |
| Sell defined-risk fly, all reports | | -11% of risk | -4% of risk |
| Buy straddle when implied < 0.8x past moves | "cheap" options | +1.0%, 61% win | -0.7%, 33% win |
| Drift call after a beat and an up day | post-earnings drift | +29% a trade (median +13%) | +12% (median -20%) |
| Busy or quiet news week | news | no edge either way | no edge |

None held up in both windows. Selling earnings premium wins about 60% of the time but averages roughly zero after single-stock spreads. The only rules that looked good in 2025-26 (selling after a 15%+ drop into the report, selling when VIX is 22+) lost money in 2024, so I'd call them luck. Buying calls after a beat earned money on average in both windows, but the median trade lost about 20% in the grading window, so a few big winners carried it, the same shape as round 2's earnings-recovery finding.

## 6. Our own signals, traded with options (real prices, 2024-2026)

| Signal | How | Trades | Win rate | Average a trade | Shares, same trades |
| --- | --- | --- | --- | --- | --- |
| Dive Zone | Shares (the app's trade) | 318 | 64% | +1.5% | |
| Dive Zone | Buy a 3-5 week ATM call | 239 | 47% | -1.2% | +1.6% |
| Dive Zone | Sell a 3-5 week ATM put (cash-secured) | 220 | 65% | +0.4% of cash | +1.6% |
| Breakout Rider | Shares | 73 | 60% | +21.9% | |
| Breakout Rider | Buy a 4-7 month ATM call | 17 | 53% | +137% | +30.5% |

Dive Zone holds trades for about 5 days, which is too short for options: time decay and the spread eat the bounce. Breakout Rider holds for months, so leveraged calls could multiply its winners. But long-dated single-stock options traded too rarely in this data (17 of 73 trades had prices on both days) to say more than "worth a closer look".

---

## What I'd do next

- **If you want a Sharpe-2 candidate, it's the QQQ 0DTE fly or condor on GEX-positive days.** Paper-trade it for 2-3 months with real limit-order fills at 09:45. If fills average within 1.5-2 cents of the bar's VWAP, the backtest is realistic. If they're worse, it isn't. Don't size it at 2% a day until then.
- **Keep Dive Zone as the core.** With the round-2 filters it's the best stock strategy we have (1.23), and nothing found here beats it on stocks.
- **Skip earnings straddles and short-dated calls on our dips.**

## Files

- This write-up: `/mnt/project-files/sharpe-hunt/SHARPE_HUNT.md`. Result tables are in `/mnt/project-files/sharpe-hunt/results/`.
- Code (research only, nothing in the app imports it):
  - `sharkfin/sharpe_lab.py`: stocks and ETFs
  - `sharkfin/bs.py`: Black-Scholes, implied vol and the surface
  - `sharkfin/options_data.py`: Alpaca option data
  - `sharkfin/options_lab.py`: 0DTE
  - `sharkfin/options_model.py`: 20-year model and calibration
  - `sharkfin/options_earnings.py`: earnings
  - `sharkfin/options_triggers.py`: our own signals
