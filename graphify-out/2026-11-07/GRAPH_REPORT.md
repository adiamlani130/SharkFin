# Graph Report - SharkFin  (2026-11-07)

## Corpus Check
- 61 files · ~115,258 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 47 file(s) not represented in the graph (top: .csv 45, (none) 1, .toml 1)
- WARNING: 47 of 116 files seen (41%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1472 nodes · 3905 edges · 77 communities (56 shown, 21 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `72ec35cc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- ratings.py
- home.py
- Strategy Builder & Swing
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
- streamlit
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- Strategy Lab
- levels.py
- run
- _cached_panel
- market_today.py
- ttl_cache
- test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt
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
- main.py
- sharkfin/__init__.py
- targets.py
- _intraday_ttl
- DataFrame
- backtest.py
- _finite
- test_rss_feeds_download_with_a_timeout
- opex_days
- sma
- regime
- prefetch
- load
- hurst_exponent

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
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py
- `load_scan()` --indirect_call--> `earnings_history()`  [INFERRED]
  app_pages/scanner.py → sharkfin/data.py
- `load_scan()` --indirect_call--> `info()`  [INFERRED]
  app_pages/scanner.py → sharkfin/data.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (77 total, 21 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 1 - "ratings.py"
Cohesion: 0.17
Nodes (9): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), value_inputs() (+1 more)

### Community 2 - "home.py"
Cohesion: 0.15
Nodes (8): stat(), tile(), pct(), prices(), stage_pill(), updown(), all_tickers(), fmt_pct()

### Community 3 - "Strategy Builder & Swing"
Cohesion: 0.06
Nodes (44): market_beta(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value(), Indicator (+36 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.06
Nodes (45): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+37 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.13
Nodes (19): _align(), backtest(), latest(), market_on(), _members(), percentile_against(), plus_frames(), quality_points() (+11 more)

### Community 8 - "indicators.py"
Cohesion: 0.13
Nodes (20): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+12 more)

### Community 9 - "ui.py"
Cohesion: 0.10
Nodes (19): choices(), asset(), esc(), header(), init_state(), kv(), _load(), missing() (+11 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "live.py"
Cohesion: 0.10
Nodes (21): br_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), last_years(), sp500_ever(), sp500_table(), tbill_yields() (+13 more)

### Community 12 - "catalysts.py"
Cohesion: 0.06
Nodes (34): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+26 more)

### Community 13 - "Playbook Page"
Cohesion: 0.15
Nodes (22): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+14 more)

### Community 14 - "data.py"
Cohesion: 0.11
Nodes (15): _copy(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials(), industry_members(), market_status(), _naive() (+7 more)

### Community 15 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

### Community 16 - "walkforward.py"
Cohesion: 0.07
Nodes (26): gate_grid(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+18 more)

### Community 17 - "pandas"
Cohesion: 0.13
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.13
Nodes (9): theme_turn(), Play, radar(), stage(), stage_history(), stats(), Theme, test_broken_stage() (+1 more)

### Community 19 - "stock_ratings"
Cohesion: 0.18
Nodes (9): index_panel(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), info(), infos(), peers_for() (+1 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "breakout_rider.py"
Cohesion: 0.10
Nodes (14): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+6 more)

### Community 22 - "DataFrame"
Cohesion: 0.18
Nodes (8): alpaca_bars(), chunk(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _session(), day_night_today()

### Community 23 - "catalyst_lab.py"
Cohesion: 0.12
Nodes (20): beat_model(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), first_in() (+12 more)

### Community 24 - "streamlit"
Cohesion: 0.13
Nodes (15): render(), _tone_line(), overview(), switch_strip(), card(), checklist(), disclaimer(), fmt_money() (+7 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (15): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+7 more)

### Community 27 - "scanner.py"
Cohesion: 0.12
Nodes (19): breakout_tab(), factor_backtest(), get_universe(), leader_dip_tab(), load_scan(), log_prices(), log_signals(), market_close() (+11 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.16
Nodes (13): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), lab_walk_forward(), _load(), _pct_cols() (+5 more)

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
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 36 - "ttl_cache"
Cohesion: 0.14
Nodes (13): run_forecast(), alpaca_daily(), analyst_data(), history(), _is_empty(), market_history(), nasdaq100(), risk_free_rate() (+5 more)

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
Cohesion: 0.21
Nodes (11): breadth(), kalshi_daily(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_earnings_frame_reports_five_year_average_eps(), test_falling_knife_gets_no_reversal_credit() (+3 more)

### Community 44 - "Series"
Cohesion: 0.10
Nodes (11): atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main() (+3 more)

### Community 47 - "test_core.py"
Cohesion: 0.09
Nodes (18): fair_value_summary(), forward_growth(), _earn_table(), _ohlc(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_builder_fills_next_open_and_stops(), test_drawdown_simple() (+10 more)

### Community 49 - "nq_regimes.py"
Cohesion: 0.11
Nodes (18): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+10 more)

### Community 50 - "factors.py"
Cohesion: 0.14
Nodes (17): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+9 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "main.py"
Cohesion: 0.19
Nodes (5): reload_changed_sharkfin(), api_key(), available(), _default(), stream_report()

### Community 59 - "sharkfin/__init__.py"
Cohesion: 0.18
Nodes (6): catalysts_view(), _filings(), all_symbols(), search(), sec_document_text(), symbol_picker()

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 61 - "_intraday_ttl"
Cohesion: 0.40
Nodes (3): _intraday_ttl(), test_intraday_cache_is_short_while_the_market_is_open(), f()

### Community 62 - "DataFrame"
Cohesion: 0.24
Nodes (8): _edgar_filings(), _parse_spells(), sec_cik(), sec_filings(), _sec_get(), sp500_members(), sp500_spells(), _yahoo_filings()

### Community 63 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 64 - "_finite"
Cohesion: 0.29
Nodes (4): compact_frame(), _finite(), fmt_big(), fmt_x()

### Community 66 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 67 - "sma"
Cohesion: 0.33
Nodes (4): _market_gap(), sma(), follow_up(), carry_forward()

### Community 68 - "regime"
Cohesion: 0.50
Nodes (3): _band(), regime(), test_regime_band_and_switch()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 492 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `run`, `Strategy Builder & Swing`, `numpy`, `leader_dip.py`, `day_night.py`, `pandas`, `Series`, `walk_forward`, `breakout_rider.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `sp500_members()` connect `DataFrame` to `numpy`, `test_app.py`, `live.py`, `pandas`, `data.py`, `pandas`, `Results`, `breakout_rider.py`, `catalyst_lab.py`, `scanner.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Should `Strategy Builder & Swing` be split into smaller, more focused modules?**
  _Cohesion score 0.05621621621621622 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `walkforward.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._