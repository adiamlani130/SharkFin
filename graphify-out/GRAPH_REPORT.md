# Graph Report - SharkFin  (2026-11-07)

## Corpus Check
- 63 files · ~117,660 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .csv 48, (none) 1, .toml 1)
- WARNING: 50 of 121 files seen (41%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1519 nodes · 4036 edges · 81 communities (60 shown, 21 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 137 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b011e449`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- ratings.py
- h
- risk.py
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- leader_dip.py
- indicators.py
- ui.py
- day_night.py
- live.py
- catalysts.py
- Playbook Page
- data.py
- walk_forward
- walkforward.py
- pandas
- sharkfin/speculation.py
- stock_ratings
- sharkfin/portfolio.py
- breakout_rider.py
- DataFrame
- catalyst_lab.py
- sentiment.py
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
- predictions.py
- prefetch
- numpy
- drivers.py
- MCP Servers
- Current Logo
- Series
- pandas
- Series
- Offline Test Design
- test_core.py
- nq_regimes.py
- factors.py
- Results
- sec_lab.py
- swing.py
- targets.py
- _intraday_ttl
- builder.py
- backtest.py
- _finite
- test_rss_feeds_download_with_a_timeout
- opex_days
- backtest
- run
- re
- load
- hurst_exponent
- could_run
- swing_choice
- theme_turn
- asset
- follow_up

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `build_tab()` - 25 edges
5. `catalysts_view()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `Day` - 18 edges
9. `sp500_table()` - 18 edges
10. `download_prices()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `load_scan()` --indirect_call--> `earnings_history()`  [INFERRED]
  app_pages/scanner.py → sharkfin/data.py
- `test_sector_neutral_z()` --calls--> `sector_neutral_z()`  [EXTRACTED]
  tests/test_core.py → sharkfin/factors.py
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (81 total, 21 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 1 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 2 - "h"
Cohesion: 0.13
Nodes (11): stat(), tile(), overview(), card(), pct(), stage_pill(), updown(), explain() (+3 more)

### Community 3 - "risk.py"
Cohesion: 0.18
Nodes (15): summarize(), annualized_return(), annualized_vol(), beta_alpha(), blume_adjusted_beta(), calmar_ratio(), cornish_fisher_var(), drawdown_series() (+7 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.17
Nodes (20): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders() (+12 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.14
Nodes (14): _align(), _band(), latest(), _members(), percentile_against(), plus_frames(), quality_points(), regime() (+6 more)

### Community 8 - "indicators.py"
Cohesion: 0.13
Nodes (20): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+12 more)

### Community 9 - "ui.py"
Cohesion: 0.11
Nodes (22): _filings(), render(), _tone_line(), switch_strip(), disclaimer(), esc(), fetch_all(), header() (+14 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "live.py"
Cohesion: 0.09
Nodes (24): br_backtest(), ld_backtest(), leader_dip_run(), all_symbols(), download_ohlcv(), last_years(), market_history(), nasdaq100() (+16 more)

### Community 12 - "catalysts.py"
Cohesion: 0.14
Nodes (14): catalysts_view(), _col(), core_long_screen(), earnings_beat_flag(), earnings_summary(), insider_summary(), revision_balance(), volume_read() (+6 more)

### Community 13 - "Playbook Page"
Cohesion: 0.19
Nodes (19): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+11 more)

### Community 14 - "data.py"
Cohesion: 0.11
Nodes (13): _copy(), _edgar_filings(), market_status(), news(), _NYSECalendar, _parse_date(), _rss(), sec_cik() (+5 more)

### Community 15 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

### Community 16 - "walkforward.py"
Cohesion: 0.07
Nodes (27): gate_grid(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+19 more)

### Community 17 - "pandas"
Cohesion: 0.14
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.14
Nodes (10): prices(), all_tickers(), Play, radar(), stage(), stage_history(), stats(), Theme (+2 more)

### Community 19 - "stock_ratings"
Cohesion: 0.11
Nodes (14): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), factor_backtest(), load_scan() (+6 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "breakout_rider.py"
Cohesion: 0.05
Nodes (40): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+32 more)

### Community 22 - "DataFrame"
Cohesion: 0.11
Nodes (13): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _parse_spells() (+5 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.12
Nodes (21): beat_model(), breadth(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table() (+13 more)

### Community 24 - "sentiment.py"
Cohesion: 0.16
Nodes (11): aggregate_sentiment(), clean_text(), dedupe(), hours_old(), is_noise(), label(), rank_articles(), score_text() (+3 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (15): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+7 more)

### Community 27 - "scanner.py"
Cohesion: 0.21
Nodes (13): breakout_tab(), get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+5 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.15
Nodes (14): build_tab(), _cat(), catalyst_tab(), condition_rows(), lab_walk_forward(), _load(), _pct_cols(), _remove() (+6 more)

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 34 - "_cached_panel"
Cohesion: 0.16
Nodes (12): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save() (+4 more)

### Community 35 - "market_today.py"
Cohesion: 0.19
Nodes (7): breadth(), direction(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 36 - "predictions.py"
Cohesion: 0.15
Nodes (12): run_forecast(), analyst_data(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials(), history(), industry_members() (+4 more)

### Community 37 - "prefetch"
Cohesion: 0.20
Nodes (7): _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "numpy"
Cohesion: 0.13
Nodes (16): trailing_pct(), cut(), make_ohlcv(), ohlcv(), price_panel(), _market(), _settings(), _signal() (+8 more)

### Community 39 - "drivers.py"
Cohesion: 0.21
Nodes (7): drivers(), earnings_record(), estimate_trend(), _naive(), _num(), _tone(), test_drivers_earnings_record_and_estimates()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "Series"
Cohesion: 0.17
Nodes (6): known(), night_returns(), overnight_hold(), rotation(), evaluate(), swing_returns()

### Community 43 - "pandas"
Cohesion: 0.23
Nodes (10): kalshi_daily(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_earnings_frame_reports_five_year_average_eps(), test_falling_knife_gets_no_reversal_credit(), test_first_in_takes_one_entry_per_episode() (+2 more)

### Community 44 - "Series"
Cohesion: 0.10
Nodes (11): atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main() (+3 more)

### Community 47 - "test_core.py"
Cohesion: 0.10
Nodes (15): fair_value_summary(), forward_growth(), _earn_table(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer() (+7 more)

### Community 49 - "nq_regimes.py"
Cohesion: 0.11
Nodes (18): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+10 more)

### Community 50 - "factors.py"
Cohesion: 0.16
Nodes (15): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), falling_knife(), fundamental_factor_frame(), is_cyclical(), price_factor_frame() (+7 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "sec_lab.py"
Cohesion: 0.07
Nodes (30): api_key(), available(), _default(), stream_report(), _Client, dilution_table(), _era(), full_text() (+22 more)

### Community 59 - "swing.py"
Cohesion: 0.17
Nodes (10): _add(), C(), about(), clean(), _frame(), rule_checks(), rules(), scan() (+2 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 61 - "_intraday_ttl"
Cohesion: 0.50
Nodes (3): _intraday_ttl(), test_intraday_cache_is_short_while_the_market_is_open(), f()

### Community 62 - "builder.py"
Cohesion: 0.17
Nodes (12): _close(), describe(), describe_strategy(), _fmt_value(), Indicator, knobs(), label(), _obv_gap() (+4 more)

### Community 63 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 64 - "_finite"
Cohesion: 0.20
Nodes (7): compact_frame(), _finite(), fmt_big(), fmt_money(), fmt_num(), fmt_x(), test_fmt_money_negative_sign_before_dollar()

### Community 66 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 67 - "backtest"
Cohesion: 0.20
Nodes (11): _market_gap(), sma(), backtest(), market_on(), signal_frames(), evaluate(), carry_forward(), _panel() (+3 more)

### Community 68 - "run"
Cohesion: 0.20
Nodes (10): compare_templates(), condition_mask(), run(), series(), signals(), template(), warmup(), _ohlc() (+2 more)

### Community 69 - "re"
Cohesion: 0.20
Nodes (9): filing_change(), html_to_text(), new_sentences(), risk_factors_section(), _sentences(), text_similarity(), headline_drivers(), clean_text() (+1 more)

### Community 72 - "could_run"
Cohesion: 0.29
Nodes (5): could_run_tab(), could_run(), BM25, tokenize(), test_could_run_screen()

### Community 73 - "swing_choice"
Cohesion: 0.38
Nodes (4): choices(), my_swing_rules(), swing_choice(), swing_picker()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 506 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sp500_members()` connect `DataFrame` to `numpy`, `live.py`, `pandas`, `data.py`, `pandas`, `stock_ratings`, `Results`, `breakout_rider.py`, `catalyst_lab.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `Rules` connect `Results` to `DataFrame`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Should `h` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Why does `run()` connect `walkforward.py` to `run`, `numpy`, `leader_dip.py`, `day_night.py`, `pandas`, `Series`, `walk_forward`, `breakout_rider.py`, `builder.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._