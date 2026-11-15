# Options for swing trades: strong plays, hedges and news (Nov 2026)

Follow-up to the Sharpe-2 hunt. You wanted options used as conviction plays or hedges on a swing timescale, with few trades and little screen time. I tested pairs (like NVDA/AMD this week), news-driven moves tagged by their headlines, product keynotes, earnings run-ups, earnings read-through between peers, and put and collar hedges. Research only; the app is unchanged.

Same rules as before:

- Rules were picked on 2012 (or 2006) to Oct 2021 and graded from Oct 2021 on.
- The option versions use **real option prices** (Alpaca/OPRA daily trades, Feb 2024 to Nov 2026), with 1.5% of the option's price per side plus $0.65 a contract as costs.
- Signals known at a close trade the next session.
- I tried about 200 setups in all.

## What's worth using (few trades, swing timescale)

| # | Play | How often | What it did | How sure |
| --- | --- | --- | --- | --- |
| 1 | **Breakout Rider with 5-8 month calls instead of shares**, at about a quarter of the money you'd put in shares | About 30 a year | On a model calibrated to real option prices: grading-window calls averaged +53% to +72% a trade (shares +11%). Losses are capped at the premium, but only about 40% of trades win. Real prices on 17 trades: calls **+137%** a trade vs **+30%** for the same trades in shares. | Medium. The model was about 2x too generous on those 17 trades, so expect roughly half the modelled edge. |
| 2 | **Sell a 1-2 month at-the-money put after a big news day** in a large cap: the stock moves 7%+ against QQQ on 2x normal volume, and it isn't earnings | About 50-90 a year across 77 big names. Take the few you like. | Real prices, 2024-26, 20-day hold: **+2.3% to +2.7% on the cash securing the put, wins 78%** (152 trades). That's about the same return as buying the shares, with a higher win rate. | Medium-good. The share version held in both windows over 12 years. |
| 3 | **Hedge only when the S&P is under its 200-day**: buy 1-month 5% out-of-the-money S&P puts for a QQQ-like portfolio | A few months a year, in bad markets | Worst drop 51% → 41% (2006-21) and 33% → 30% (2021-26), at almost no cost to return | Good, but it's a seatbelt, not a profit source |
| 4 | Calls bought 3 weeks before big keynotes (NVDA GTC and Computex, MSFT Build), sold the day before | 5-8 a year | Calls +59% average, 67% win, but only 18 trades in a bull market. The shares beat a random 3-week window by only about 2.6 points. | Low. An anecdote, not a tested edge. |

### 1. Breakout Rider with calls: the "strong play" version

The Breakout Rider holds its winners for 2-3 months. That gives an option time to pay before decay eats it, and it is why calls fit here and not on Dive Zone's 5-day dips.

The numbers below cover every Breakout Rider trade since 2006 (608 trades), priced with Black-Scholes at implied vol = 0.98 x the stock's trailing 60-day volatility. That ratio is what real option prices showed at our 2024-26 entries.

| Trades | How | Win rate | Average | Median | Worst |
| --- | --- | --- | --- | --- | --- |
| 460 (2006-21) | Shares | 48% | +5.5% | -1.2% | -26% |
| | ATM call, 5 months | 38% | +35% | -42% | -98% |
| | 10% in-the-money call, 5 months | 40% | +25% | -20% | -90% |
| 148 (2021-26) | Shares | 48% | +11.1% | -1.5% | -45% |
| | ATM call, 5 months | 39% | +72% | -41% | -97% |
| | ATM call, 8 months | 44% | +56% | -22% | -88% |
| | 10% in-the-money call, 5 months | 42% | +53% | -20% | -92% |

- **Sized at 25% of what you'd put in shares**, the calls made about the same as shares in the picking window (+8.7% vs +5.5% a trade, but bumpier) and more in the grading window (+18% vs +11%). Each trade can only lose the premium.
- **The real-price check** covered 17 trades from 2024-26: calls +137% on average, shares +30%. Winners included PLTR (+638%), MU (+430%), KEYS (+460%) and APH (+414%). The model overstated these same trades by about 2x, so halve the table above to be safe.
- **Best fit:** an 8-month at-the-money or 10% in-the-money call. They win more often (42-44%) and lose less to decay when a breakout stalls.

### 2. After a big news day, sell a put instead of buying

A **big news day** here means a large cap moves 7%+ against QQQ on twice its normal volume, at least 2 sessions from an earnings report. There were 876 of them since 2012, and I tagged 2015 onward with that day's Alpaca headlines.

- **The stock usually keeps doing well relative to QQQ over the next 3 months, whichever way the day went.** After big up days it beat QQQ by 4.0% (2012-21) and 6.2% (2021-26) over 60 sessions. After big down days it bounced 7.8% and 3.3% vs QQQ. Both held in both windows. Medians are smaller than averages, so some big winners carry it.
- **Buying options after the news loses.** Implied vol is high right after a shock, so calls averaged -0.4% (median -50%) and puts -45% over 20 days. **Selling the put collects that high vol instead**: +2.3% on cash after down days and +2.7% after up days, with 78% wins and a worst trade of -25%.
- **By headline type** (small samples): FDA/trial drops in big pharma rebounded most (+11% vs QQQ over 60 days in both windows, about 15 cases each). Product, AI and launch drops also rebounded in both windows (+6% and +4%). Up moves from deals, partnerships, guidance and legal news were inconsistent: down in 2012-21, up in 2021-26. Patent news was too rare to measure.

### 3. Hedges: when they're worth it

The test held Dive Zone, QQQ or SPY all the time and added 1-month S&P puts (5% or 10% out of the money) or zero-ish-cost collars, only in certain scenarios. Puts were priced on the surface calibrated to real SPY chains.

- **For a QQQ-like portfolio, the hedge that worked is "S&P under its 200-day"**: the worst drop fell from 51% to 41% (2006-21) and 33% to 30% (2021-26), with Sharpe and return about unchanged.
- **For Dive Zone, no hedge was worth it.** The best scenario hedges nudged the 2006-21 Sharpe up (1.49 to 1.56) but did nothing in 2021-26, and none changed the worst drop in either window. Dive Zone's bad spells, like the Oct-Nov 2026 chip selloff, happen while the S&P still looks fine, so the scenarios that turn hedges on don't fire. The round-2 credit switch is still the only thing that softened that selloff.
- **Hedging all the time costs about 2-5 points a year**, more than it saves.

## What didn't work

- **Pairs (NVDA/AMD and 29 others), traded either way.** When two linked stocks split apart (2+ standard deviations over 20 or 60 days), betting on them coming back together made about 0% after costs. So did betting on the split continuing. Earlier "long only" results were just the market going up. NVDA/AMD on its own followed the leader in 2012-21 (+2.8% a trade), but only +0.3% since, and just 5 of 30 pairs were positive in both windows, about what luck gives. **As of Friday's close, NVDA/AMD is stretched (NVDA lagging by about 1.8 standard deviations over 20 days), but history says that tells you nothing about the next month.**
- **Earnings read-through.** When the first company in a pair jumps 5%+ on earnings, the second one's own report reacted only +0.7% on average (vs +0.3% for all). The correlation between their reactions was about 0.
- **Calls bought 10 days before earnings**, sold the day before. Flat in 2024 (+1%), +7% average in 2025-26 but a median of -10%. Shares did +0.9%. Not reliable.
- **Straddles into keynotes**: roughly break-even.
- **FDA decisions and trial readouts in small biotechs.** These are the stocks that move on FDA news, and the earlier catalyst lab found micro-caps run up about 7% into the decision and then drop about 8% on the day. But their options are thin and wide, the free option data has no bid/ask, and listing the decision dates needs SEC filings fetched with a contact address in the request. The big pharma names I could test barely move on approvals. I can do this properly if you want, but the trades would be hard to fill well.

## If you only want a couple of things to watch

1. **Breakout Rider signals → buy an 8-month at-the-money call** with about a quarter of the money you'd use for shares. About 2-3 a month.
2. **A large cap you like drops 7%+ on news (not earnings) → sell a 1-2 month at-the-money put** you'd be happy to be assigned. Recent examples the rule flagged: MU, LRCX, AMAT and MRVL on Nov 5, and NVDA on Nov 9. These came from one sector selloff, so treat them as one bet, not five.
3. **S&P closes under its 200-day → buy 1-month 5% out-of-the-money S&P puts for your index-like holdings** until it's back above.

## Files

- This note: `docs/SWING_OPTIONS.md (copy in the project files folder)`. Tables are in `/mnt/project-files/sharpe-hunt/results/`: pairs, hedges, shock categories, Breakout calls and the swing option trades.
- Code: `sharkfin/swing_options_lab.py` (pairs, hedges, news shocks with headline tags, Breakout calls, real-price option replays).
