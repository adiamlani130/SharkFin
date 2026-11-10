# Graph Report - SharkFin  (2026-11-07)

## Corpus Check
- 63 files · ~118,039 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .csv 48, (none) 1, .toml 1)
- WARNING: 50 of 121 files seen (41%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1519 nodes · 4036 edges · 71 communities (53 shown, 18 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 137 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d2ce675`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- ratings.py
- h
- builder.py
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
- sharkfin/playbook.py
- walkforward.py
- fakes.py
- test_leaks.py
- stock_ratings
- sharkfin/portfolio.py
- breakout_rider.py
- intraday_bars
- catalyst_lab.py
- DataFrame
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
- ttl_cache
- numpy
- drivers.py
- MCP Servers
- Current Logo
- ai.py
- switches
- Series
- Offline Test Design
- test_core.py
- nq_regimes.py
- factors.py
- Results
- sec_lab.py
- _one_day_matrix
- targets.py
- backtest.py
- opex_days
- sma
- json
- asset

## God Nodes (most connected - your core abstractions)
1. `ttl_cache()` - 39 edges
2. `Financials` - 39 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `download_prices()` - 18 edges
9. `sp500_table()` - 18 edges
10. `Day` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `stock_ratings()` --calls--> `to_gics()`  [EXTRACTED]
  app_pages/research.py → sharkfin/ratings.py
- `load_scan()` --indirect_call--> `download_prices()`  [INFERRED]
  app_pages/scanner.py → sharkfin/data.py
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (71 total, 18 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (33): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+25 more)

### Community 1 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 2 - "h"
Cohesion: 0.18
Nodes (7): stat(), breakout_tab(), pct(), stage_pill(), updown(), checklist(), h()

### Community 3 - "builder.py"
Cohesion: 0.05
Nodes (46): C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value(), Indicator (+38 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.19
Nodes (19): _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders(), test_playbook_every_view_and_scan() (+11 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.15
Nodes (15): _align(), backtest(), latest(), market_on(), _members(), percentile_against(), plus_frames(), quality_points() (+7 more)

### Community 8 - "indicators.py"
Cohesion: 0.15
Nodes (19): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+11 more)

### Community 9 - "ui.py"
Cohesion: 0.09
Nodes (29): tile(), catalysts_view(), _filings(), render(), _tone_line(), card(), clean_text(), compact_frame() (+21 more)

### Community 10 - "day_night.py"
Cohesion: 0.12
Nodes (16): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+8 more)

### Community 11 - "live.py"
Cohesion: 0.11
Nodes (18): br_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), last_years(), sp500_table(), tbill_yields(), universe() (+10 more)

### Community 12 - "catalysts.py"
Cohesion: 0.06
Nodes (34): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+26 more)

### Community 13 - "Playbook Page"
Cohesion: 0.17
Nodes (22): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+14 more)

### Community 14 - "data.py"
Cohesion: 0.10
Nodes (15): all_symbols(), _copy(), _edgar_filings(), _fetch_ohlcv(), _naive(), nasdaq100(), news(), _NYSECalendar (+7 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "walkforward.py"
Cohesion: 0.10
Nodes (14): gate_grid(), cut(), _day(), Fold, folds(), grid(), _neighbours(), pick() (+6 more)

### Community 17 - "fakes.py"
Cohesion: 0.14
Nodes (19): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+11 more)

### Community 18 - "test_leaks.py"
Cohesion: 0.13
Nodes (10): daily_cash(), run(), offline(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_members_only_trade_while_in_the_index() (+2 more)

### Community 19 - "stock_ratings"
Cohesion: 0.21
Nodes (8): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), download_prices(), peers_for()

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "breakout_rider.py"
Cohesion: 0.12
Nodes (12): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+4 more)

### Community 22 - "intraday_bars"
Cohesion: 0.12
Nodes (10): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), market_status() (+2 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.05
Nodes (42): prices(), beat_model(), breadth(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study() (+34 more)

### Community 24 - "DataFrame"
Cohesion: 0.23
Nodes (7): factor_backtest(), _parse_spells(), sec_filings(), sp500_ever(), sp500_members(), sp500_spells(), _yahoo_filings()

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.16
Nodes (12): bs(), _call_wall_fade(), _days(), fly_trades(), value(), _neg_gamma_breakout(), _opex_fly(), _opex_magnet() (+4 more)

### Community 27 - "scanner.py"
Cohesion: 0.19
Nodes (12): get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals(), scan() (+4 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.11
Nodes (30): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+22 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.18
Nodes (12): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), lab_walk_forward(), _load(), _pct_cols() (+4 more)

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 34 - "_cached_panel"
Cohesion: 0.15
Nodes (13): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), _fetch_prices(), fetch(), _panel_file(), _panel_load() (+5 more)

### Community 35 - "market_today.py"
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 36 - "predictions.py"
Cohesion: 0.28
Nodes (4): run_forecast(), history(), market_history(), risk_free_rate()

### Community 37 - "ttl_cache"
Cohesion: 0.10
Nodes (19): load_scan(), scan_data(), analyst_data(), earnings_histories(), earnings_history(), financials(), industry_members(), info() (+11 more)

### Community 38 - "numpy"
Cohesion: 0.19
Nodes (12): trailing_pct(), _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only(), test_gex_plays_decide_from_earlier_bars_only() (+4 more)

### Community 39 - "drivers.py"
Cohesion: 0.21
Nodes (7): drivers(), earnings_record(), estimate_trend(), _naive(), _num(), _tone(), test_drivers_earnings_record_and_estimates()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "ai.py"
Cohesion: 0.31
Nodes (4): api_key(), available(), _default(), stream_report()

### Community 43 - "switches"
Cohesion: 0.33
Nodes (4): _band(), regime(), switches(), test_regime_band_and_switch()

### Community 44 - "Series"
Cohesion: 0.09
Nodes (15): catalogue(), main(), move_vs_implied(), atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash() (+7 more)

### Community 47 - "test_core.py"
Cohesion: 0.08
Nodes (18): _intraday_ttl(), hurst_exponent(), _earn_table(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports() (+10 more)

### Community 49 - "nq_regimes.py"
Cohesion: 0.11
Nodes (18): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+10 more)

### Community 50 - "factors.py"
Cohesion: 0.10
Nodes (22): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+14 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "sec_lab.py"
Cohesion: 0.05
Nodes (49): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+41 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 63 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 66 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 67 - "sma"
Cohesion: 0.14
Nodes (9): _market_gap(), rsi(), sma(), follow_up(), price_chart(), carry_forward(), test_leader_dip_follow_up(), test_rsi_bounds_and_wilder() (+1 more)

### Community 73 - "json"
Cohesion: 0.19
Nodes (11): swing_tab(), choices(), init_state(), _load(), my_swing_rules(), save_list(), save_my_swing_rules(), set_swing_choice() (+3 more)

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 506 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `alpaca_bars()` connect `intraday_bars` to `DataFrame`, `sec_lab.py`, `data.py`, `test_core.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05401234567901234 - nodes in this community are weakly interconnected._
- **Why does `sp500_members()` connect `DataFrame` to `numpy`, `live.py`, `data.py`, `fakes.py`, `test_leaks.py`, `Results`, `catalyst_lab.py`, `sec_lab.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05468215994531784 - nodes in this community are weakly interconnected._
- **Why does `Rules` connect `Results` to `DataFrame`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._