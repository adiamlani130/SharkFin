# Edge lab: strategy research, round 2 (Nov 14 2026)

Three questions, all tested on point-in-time data with no look-ahead. Every rule was judged first on the **picking window (2006 to Oct 12 2021)** and then checked on the **grading window (Oct 13 2021 to Nov 6 2026)**, the same split as the earlier labs. A result only counts as "works" if it helps in both windows. Costs are 0.1% per side.

Data: 20 years of daily prices for 1,136 tickers (every stock in the S&P 500 at any point since 2005, the Nasdaq-100, the Radar plays, 85 industry and theme ETFs, market ETFs, VIX and bond ETFs), and 32,681 earnings reports from stocks while they were in the S&P 500.

Code: `sharkfin/edge_lab.py` (tests in `tests/test_edge_lab.py`), tables in `sharkfin/research_data/edge_lab/`, notes in `docs/EDGE_LAB.md`. App behaviour is unchanged.

---

## The short version

1. **Strategies.** Two small filters improve Dive Zone in both windows: skip dips in the 30 days after an earnings **miss**, and only buy stocks that are **beating their own sector** over 6 months. Together they take Dive Zone from 27.6% to 29.2% a year in the grading window (Sharpe 1.13 to 1.23) and cut the worst drop in the picking window from 18% to 15%. They do **not** fix the Oct-Nov 2026 selloff (still about -21%). Nothing I tried reliably improved Tech Breakout Rider, and nothing improved the stock ranking.
2. **Speculation themes.** The Radar's "Turning up" reading catches almost every big theme run early, but it also fires all the time, so as a buy signal it is no better than picking a theme at random. One rule did better in both windows: **a theme ETF making a new 52-week high after falling 30%+ within the past year**. It roughly doubled the odds of a 40%+ run. A real breakthrough is big: the median theme run since 2010 was +164% over about 18 months, and there was still +144% left after the first "Turning up" and +54% after the first "Running". The catch is that runs end with a median 42% fall, and as a portfolio no theme rule beat simply holding SPY.
3. **Your earnings idea.** As written (a beat when analysts expected a weaker quarter, in a growth sector 10%+ off its high) it worked well from 2006 to 2021 but **failed out of sample**: from late 2021 it lagged SPY by 4.4% over 6 months on average. "Analysts expected bad" turned out to be the weak part. A close cousin held up in both windows: use the **stock's own 15%+ fall in the 3 months before the report** as the sign of low expectations, then require a beat, a growth sector that has sold off, and a stock that rises on the day. That beat SPY by 6-7% over 6 months and 15-16% over 12 months in both windows, but the median trade was only about even, so a few big winners do the work, and it was one of about 20 setups tried.

---

## 1. Improving Dive Zone, Breakout Rider and the ranking

Earlier rounds already showed that VIX, GEX, VIX term structure, market breadth, sector-ETF trend and crash guards don't help. This round tried new kinds of confluence: earnings timing and results, news gaps, dip-day volume, credit spreads, interest rates and strength against the sector.

### Dive Zone (as is: 20.5%/yr pick, Sharpe 1.20; 27.6%/yr grade, Sharpe 1.13)

| Filter | Pick: yearly / Sharpe / worst drop | Grade: yearly / Sharpe / worst drop | Nov 2026 selloff |
|---|---|---|---|
| As is | 20.5% / 1.20 / -18.0% | 27.6% / 1.13 / -22.5% | -20.5% |
| **Skip dips within 30 days of a miss** | 21.0% / 1.23 / -17.6% | 28.9% / 1.18 / -22.7% | -20.5% |
| **Only stocks beating their sector over 6m** | 20.6% / 1.26 / -15.8% | 28.0% / 1.17 / -23.6% | -20.8% |
| **Both together** | 20.8% / **1.28** / **-14.9%** | **29.2%** / **1.23** / -23.6% | -20.8% |
| Both + credit switch (junk bonds above their 50-day) | 14.0% / 0.98 / -22.0% | 23.7% / 1.15 / **-14.4%** | **-12.2%** |
| No earnings in the next 5 days | 20.0% / 1.17 | 24.0% / 1.00 | -16.5% |
| Credit switch alone | 14.2% / 0.97 | 25.0% / 1.21 / -13.4% | -12.2% |
| Skip dips after a 7%+ one-day drop ("news gap") | 18.4% / 1.12 | 19.8% / 0.89 | -14.6% |

What this means in plain terms:

- **A dip right after a missed quarter is a real problem, not a dip.** In the grading window those trades lost 0.8% on average and won only 49% of the time, against +1.6% and 65% for the rest. Skipping them helped in both windows.
- **Buy the sector's leaders, not its laggards.** Dips in stocks that were already lagging their sector won 52-58% of the time vs 65-68% for sector leaders. (This one uses today's sector labels for older stocks, so it has a little hindsight.)
- **The credit switch is the only thing that softened the Nov 2026 selloff** (-12% instead of -21%) and the 2022 bear market, but it cost about 6 points a year from 2006-2021 by sitting out good rebounds. Same story as the earlier crash guards: it fails the picking-window test, so I would not turn it on by default. It could be an optional "cautious mode".
- **Surprises.** Avoiding dips just before earnings looks smart trade by trade (those trades win 52% vs 68%), but removing them made the portfolio slightly worse, because the freed slots went to weaker trades. And dips caused by a sharp one-day news drop were actually the *best* trades (+3-4% each), so filtering them out hurt.

### Tech Breakout Rider (as is: 14.7%/yr pick, Sharpe 0.80; 28.9%/yr grade, Sharpe 0.95)

Nothing passed both windows. "No earnings in the next 5 days" plus the credit switch looked great on the grading window (36.0%/yr, Sharpe 1.18) but was slightly worse on 2006-2021 (13.5%, Sharpe 0.76), so it is probably luck. Two classic breakout rules hurt: requiring heavy volume on the breakout day (Sharpe 0.80 to 0.52 in pick) and requiring a 52-week high (0.80 to 0.74).

### Stock ranking

I measured whether six add-on signals line up with the next 1 and 3 months' returns across S&P 500 members (rank correlation, or IC). All were between -0.02 and +0.03, which is noise: the last earnings surprise, a fresh beat, analysts' expected growth, a low-bar beat, sector strength, and strength vs the sector. None is worth adding to the ranking.

---

## 2. How the Speculation Radar finds themes, and whether that works

**How it works today.** The 12 Radar themes (optics, power, nuclear, quantum, drones, and so on) were researched by hand in October 2026. The app then reads each theme's equal-weight basket: *Quiet* (below its 200-day), *Turning up* (back above the 200-day and beating the S&P 500 over 6 months), *Running* (up 60%+ in a year and near its high), *Cooling*, and *Broken* (60%+ off its high). The themes themselves are hindsight picks, so they can't be backtested fairly. To test the *criteria* without leakage, I ran them on 85 industry and theme ETFs (semis, solar, uranium, lithium, cyber, cloud, robotics, space, genomics, gold miners, regional banks and more). Each ETF is a theme basket that really existed at the time.

### Which rule finds a theme before it runs?

Average result after each signal, against every theme on any month (the baseline):

| Rule | Window | Signals | 12m vs SPY | Ran 40%+ in 12m | Ran 100%+ in 12m |
|---|---|---|---|---|---|
| Baseline: any theme, any month | pick | 9,797 | -0.7% | 21% | 3.6% |
| | grade | 5,095 | -2.4% | 21% | 2.9% |
| Radar: Quiet to Turning up | pick | 851 | +1.1% | 23% | 3.5% |
| | grade | 458 | +1.8% | 26% | 3.9% |
| **New 52-week high after a 30%+ fall in the past year** | pick | 200 | **+8.5%** | **46%** | **10.5%** |
| | grade | 107 | **+4.5%** | **34%** | **6.5%** |
| Golden cross (50-day over 200-day) | grade | 319 | -1.9% | 24% | 3.4% |
| Money rushing in (20-day dollar volume 2x normal) | grade | 184 | -1.2% | 22% | 3.3% |
| Turn from a crash (40%+ off, back over 200-day) | grade | 86 | -2.1% | 28% | 9.3% |

- **Turning up is about as good as random** for picking which theme will run (the earlier catalyst lab found the same on single stocks).
- **"Back to a new high after a big fall"** is the one rule that worked in both windows. In plain terms: the theme crashed, everyone gave up, and then it climbed all the way back to a new 52-week high. That's the "breakthrough" moment. It roughly doubled the odds of a 40% run and tripled the odds of doubling.
- On **single stocks** the same rule did not help (S&P 500 members: about baseline). It works on baskets, where one company's noise cancels out, so the Radar should apply it to the theme basket, not to each play.

### How big is a breakthrough?

Every theme ETF run of 100%+ with no 40% fall along the way (found with hindsight), for runs since 2010 that took under 3 years (35 runs):

- **Median run: +164%, about 434 trading days (roughly 18 months) from low to peak.**
- The Radar said Turning up before the peak in 98% of all big runs, a median of about 6 months (193 calendar days) after the low. **Median gain still left after the first Turning up: +144%. After the first Running: +54%.**
- **Then the fall: a median -42% within 12 months of the peak.** That's why Cooling and Broken matter as exits.

### As a portfolio

No theme rule beat holding SPY. Holding each theme 6 months after the "new high after a fall" signal made 6.3%/yr in pick and 14.0%/yr in grade (SPY: 10.4% and 12.5%), with drawdowns of 37-66%. Holding themes only while Turning up or Running made 2.7% and 1.3% a year, worse than holding every theme ETF (8.3% and 6.7%). Theme investing is a high-variance bet. The edge is better odds of catching a big run, not a smoother ride.

### Your 12 Radar themes (hindsight list, so read this as a story, not a test)

Over the past 3 years most of them had huge runs (Space +1,533%, Light instead of copper +1,091%, Quantum +834%, Micron +918%). The "in while Turning up or Running" rule made a lot less than holding (Space +373% vs +1,533%) but cut the worst drop from 55-80% to 25-50%. **Today 7 of the 12 are Broken (60%+ off their highs)** after the Oct-Nov 2026 selloff, and nuclear, rare earths and batteries are also down over 12 months.

### Firing now (as of Nov 13 2026)

New 52-week high after a 30%+ fall: **ARKK (Oct 5), cloud software WCLD (Oct 20), software XSW (Oct 21), cybersecurity BUG (Oct 26).** Software-heavy, so the software selloff part of the market has already recovered at the basket level. Semis (SMH) only just turned up and is still 27% off its high.

---

## 3. Your idea: a "low bar" earnings beat in a beaten-down growth sector

**Setup tested:** the company beats the estimate, analysts expected EPS **below a year ago** (a low bar), and the stock's sector ETF (tech, semis, software, internet/communications, consumer, biotech) is **10%+ off its high**. Buy at the next open after the reaction day. A stock's sector is the ETF it tracked most closely over the year before, so it works for delisted stocks too (it matches today's GICS sector 73% of the time). Returns are vs SPY.

| Setup | Window | Reports | Day of report | 6m vs SPY | 12m vs SPY | Median 6m | Back to 52w high in 12m |
|---|---|---|---|---|---|---|---|
| Any beat | pick | 16,638 | +0.8% | +0.7% | +1.4% | +0.1% | 75% |
| | grade | 7,904 | +0.6% | -1.8% | -3.9% | -3.4% | 65% |
| Growth sector hit + beat | pick | 1,003 | +1.8% | +4.7% | +10.5% | +3.4% | 57% |
| | grade | 860 | +0.2% | +0.7% | +4.8% | -2.1% | 46% |
| **Your setup** (growth sector hit + low bar + beat) | pick | 403 | +2.6% | **+6.7%** | +13.4% | +4.1% | 51% |
| | grade | 258 | +0.5% | **-4.4%** | -7.7% | -6.0% | 35% |
| Your setup + stock rose 5%+ vs SPY that day | grade | 67 | +10.9% | -3.0% | -8.0% | -7.3% | 42% |
| **Market expected bad: stock fell 15%+ in 3 months, then beat, growth sector hit, rose that day** | pick | 157 | +7.1% | **+7.4%** | **+15.9%** | +8.4% | 45% |
| | grade | 119 | +6.4% | **+6.4%** | **+15.5%** | 0.0% | 34% |
| Catalyst-lab combo (30%+ off high, beat 10%+, up 5%+, EPS +25%) | grade | 43 | +10.7% | +11.7% | +25.0% | +0.4% | 47% |

What I take from it:

- **The idea worked for 15 years, then stopped.** From late 2021 your setup lagged SPY, and adding "the stock rose on the day" didn't save it.
- **The analyst low bar is the part that hurts.** "Growth sector hit + beat" alone did better than with the low-bar condition in both windows. A low estimate often means the business really is shrinking, and beating a shrinking number isn't a turnaround.
- **The market's own expectations work better than the analysts'.** A stock that fell 15%+ into the report, then beat and rose on the day while its growth sector was down, beat SPY by about 6-7% over 6 months and 15-16% over 12 months in both windows. But the median grading-window trade was flat: a minority of big recoveries carry the average. Only about a third got back to their 52-week high within a year, so "it keeps pushing back to highs" happens, but not most of the time.
- **As a portfolio** (hold each pick 6 months) that variant made 17.1%/yr from 2006-2021 but only 3.6%/yr from late 2021, with a 41% worst drop, well behind SPY's 12.5%. Picks bunch up in the same selloffs, so they fall together.
- **Multiple-testing warning.** I tried about 20 versions of this idea. The one that held up could partly be luck; it needs live tracking before real money.
- Data limit: Yahoo only has the final consensus estimate, not how it moved before the report, so "analysts thought it would be bad" is measured as "the estimate was below last year's EPS". True estimate-revision history (estimates cut in the month before the report) needs a paid source.

**Right now** (sectors are down: semis 27% off their high, tech 16%, software 10%, biotech 11%), recent reports that fit the version that held up: **Carnival (CCL, Sep 29, +13.6% vs SPY on the day)** and **Akamai (AKAM, Nov 6, +6.4%)**. Recent ones that fit your exact setup but fell on the day (AXON, HPQ, NKE, SWKS, QCOM) are the kind that did worst.

---

## Ways this could go into the app (your call)

1. Dive Zone: add the two filters (skip dips within 30 days of a miss, sector leaders only). Small, steady gain, both windows. Optionally a "cautious mode" switch using the credit signal.
2. Speculation Radar: add a "Breakthrough" flag when a theme basket makes a new 52-week high after a 30%+ fall, show the typical run size (+164% median, 18 months) and the typical fall after the peak (-42%), and use Cooling/Broken as exit warnings.
3. Earnings: an "Earnings recovery" watchlist using the version that held up (stock down 15%+ into the report, beat, growth sector down 10%+, up on the day), clearly labelled as an experiment with a live scoreboard.
4. Leave Breakout Rider and the ranking as they are.
