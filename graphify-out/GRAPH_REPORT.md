# Graph Report - SharkFin  (2026-11-06)

## Corpus Check
- 59 files · ~109,761 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 34 file(s) not represented in the graph (top: .csv 32, (none) 1, .toml 1)
- WARNING: 34 of 101 files seen (34%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1403 nodes · 3706 edges · 76 communities (54 shown, 22 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 130 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `afb59c20`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- ratings.py
- h
- Strategy Builder & Swing
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- risk.py
- leader_dip.py
- ui.py
- day_night.py
- live.py
- catalysts.py
- Playbook Page
- data.py
- backtest_price_composite
- walkforward.py
- pandas
- sharkfin/speculation.py
- stock_ratings
- sharkfin/portfolio.py
- daily_cash
- DataFrame
- fakes.py
- breakout_rider.py
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- Strategy Lab
- levels.py
- run
- sharkfin/__init__.py
- _cached_panel
- market_today.py
- research.py
- load_scan
- pathlib
- drivers.py
- MCP Servers
- Current Logo
- day_view
- json
- Series
- Offline Test Design
- test_core.py
- test_leaks.py
- nq_regimes.py
- factors.py
- Results
- sentiment.py
- load
- targets.py
- _intraday_ttl
- _fetch_prices
- risk_contributions
- asset
- test_rss_feeds_download_with_a_timeout
- swing_returns
- forward_growth
- run
- test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer
- _fear_day
- test_page_renders

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `build_tab()` - 25 edges
5. `catalysts_view()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `backtest()` - 18 edges
9. `Day` - 18 edges
10. `sp500_table()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `stat()` --calls--> `h()`  [EXTRACTED]
  app_pages/home.py → sharkfin/ui.py
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py
- `load_scan()` --indirect_call--> `earnings_history()`  [INFERRED]
  app_pages/scanner.py → sharkfin/data.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (76 total, 22 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 1 - "ratings.py"
Cohesion: 0.16
Nodes (10): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), value_inputs() (+2 more)

### Community 2 - "h"
Cohesion: 0.12
Nodes (12): overview(), breakout_tab(), card(), pct(), prices(), stage_pill(), updown(), explain() (+4 more)

### Community 3 - "Strategy Builder & Swing"
Cohesion: 0.06
Nodes (36): api_key(), available(), _default(), stream_report(), C(), _close(), compare_templates(), condition_mask() (+28 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.08
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.21
Nodes (18): _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_playbook_every_view_and_scan(), test_research_target_and_entry_tab() (+10 more)

### Community 7 - "risk.py"
Cohesion: 0.18
Nodes (15): market_beta(), annualized_return(), annualized_vol(), beta_alpha(), blume_adjusted_beta(), calmar_ratio(), cornish_fisher_var(), drawdown_series() (+7 more)

### Community 8 - "leader_dip.py"
Cohesion: 0.05
Nodes (50): compare(), positions(), run(), Strategy, _market_gap(), build_features(), adx(), atr() (+42 more)

### Community 9 - "ui.py"
Cohesion: 0.09
Nodes (25): _filings(), render(), _tone_line(), switch_strip(), clean_text(), compact_frame(), disclaimer(), esc() (+17 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "live.py"
Cohesion: 0.08
Nodes (23): br_backtest(), ld_backtest(), leader_dip_run(), tech_universe(), download_ohlcv(), last_years(), sp500_ever(), sp500_members() (+15 more)

### Community 12 - "catalysts.py"
Cohesion: 0.09
Nodes (24): catalysts_view(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), insider_summary() (+16 more)

### Community 13 - "Playbook Page"
Cohesion: 0.17
Nodes (21): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+13 more)

### Community 14 - "data.py"
Cohesion: 0.10
Nodes (16): html_to_text(), all_symbols(), _copy(), _edgar_filings(), market_status(), nasdaq100(), news(), _NYSECalendar (+8 more)

### Community 15 - "backtest_price_composite"
Cohesion: 0.15
Nodes (9): backtest_price_composite(), earnings_factor_frame(), _earnings_table(), fundamental_factor_frame(), walk_forward(), evaluate(), weight_presets(), test_factor_backtest_positive_ic() (+1 more)

### Community 16 - "walkforward.py"
Cohesion: 0.05
Nodes (38): gate_grid(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+30 more)

### Community 17 - "pandas"
Cohesion: 0.15
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.19
Nodes (7): Play, radar(), stage(), stage_history(), stats(), Theme, test_speculation_stages_follow_the_price_action()

### Community 19 - "stock_ratings"
Cohesion: 0.19
Nodes (8): index_panel(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), infos(), peers_for(), to_gics()

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.17
Nodes (11): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+3 more)

### Community 21 - "daily_cash"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 22 - "DataFrame"
Cohesion: 0.12
Nodes (13): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _parse_spells() (+5 more)

### Community 23 - "fakes.py"
Cohesion: 0.15
Nodes (17): _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info(), install() (+9 more)

### Community 24 - "breakout_rider.py"
Cohesion: 0.23
Nodes (7): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), walk_forward(), evaluate()

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.10
Nodes (19): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+11 more)

### Community 27 - "scanner.py"
Cohesion: 0.13
Nodes (17): factor_backtest(), get_universe(), leader_dip_tab(), load_scan(), log_prices(), log_signals(), market_close(), ratings_tab() (+9 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.16
Nodes (24): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_regime() (+16 more)

### Community 29 - "Day"
Cohesion: 0.16
Nodes (16): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), ema_cross_5m(), _ema_rows(), _filter() (+8 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.24
Nodes (8): _add(), build_tab(), condition_rows(), _load(), _remove(), rules_key(), split_open_trade(), _value_step()

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "sharkfin/__init__.py"
Cohesion: 0.10
Nodes (3): stat(), tile(), reload_changed_sharkfin()

### Community 34 - "_cached_panel"
Cohesion: 0.17
Nodes (11): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save(), _patched() (+3 more)

### Community 35 - "market_today.py"
Cohesion: 0.19
Nodes (7): breadth(), direction(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 36 - "research.py"
Cohesion: 0.15
Nodes (13): run_forecast(), lab_walk_forward(), analyst_data(), earnings_history(), financials(), history(), industry_members(), info() (+5 more)

### Community 37 - "load_scan"
Cohesion: 0.20
Nodes (7): _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "pathlib"
Cohesion: 0.38
Nodes (3): make_ohlcv(), ohlcv(), price_panel()

### Community 39 - "drivers.py"
Cohesion: 0.21
Nodes (7): drivers(), earnings_record(), estimate_trend(), _naive(), _num(), _tone(), test_drivers_earnings_record_and_estimates()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "day_view"
Cohesion: 0.33
Nodes (4): atr(), day_view(), gex_pct(), known()

### Community 43 - "json"
Cohesion: 0.20
Nodes (11): swing_tab(), choices(), _load(), my_swing_rules(), _path(), save_list(), save_my_swing_rules(), save_state() (+3 more)

### Community 44 - "Series"
Cohesion: 0.13
Nodes (10): deflated_sharpe(), first_usable(), _folds_beating_cash(), main(), night_returns(), overnight_hold(), rotation(), run_one() (+2 more)

### Community 47 - "test_core.py"
Cohesion: 0.15
Nodes (13): fair_value_summary(), _earn_table(), _panel(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_fair_value_blend(), test_features_have_no_lookahead(), test_leader_dip_idle_cash_choices() (+5 more)

### Community 48 - "test_leaks.py"
Cohesion: 0.21
Nodes (7): headline_drivers(), offline(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled()

### Community 49 - "nq_regimes.py"
Cohesion: 0.12
Nodes (17): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+9 more)

### Community 50 - "factors.py"
Cohesion: 0.29
Nodes (7): composite_scores(), price_factor_frame(), sector_neutral_z(), winsorize(), zscore(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_factor_composite_ranks_planted_winners()

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "sentiment.py"
Cohesion: 0.13
Nodes (13): could_run_tab(), aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles() (+5 more)

### Community 59 - "load"
Cohesion: 0.18
Nodes (4): fetch(), intraday_frames(), load(), trailing_pct()

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 61 - "_intraday_ttl"
Cohesion: 0.40
Nodes (3): _intraday_ttl(), test_intraday_cache_is_short_while_the_market_is_open(), f()

### Community 62 - "_fetch_prices"
Cohesion: 0.50
Nodes (4): _fetch_ohlcv(), _fetch_prices(), fetch(), _naive()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 469 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `run`, `Strategy Builder & Swing`, `leader_dip.py`, `day_night.py`, `Series`, `backtest_price_composite`, `pandas`, `breakout_rider.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `walkforward.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Should `h` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
- **Should `Strategy Builder & Swing` be split into smaller, more focused modules?**
  _Cohesion score 0.06144393241167435 - nodes in this community are weakly interconnected._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._