# Graph Report - SharkFin  (2026-11-10)

## Corpus Check
- 63 files · ~119,636 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .csv 48, (none) 1, .toml 1)
- WARNING: 50 of 123 files seen (41%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1529 nodes · 4056 edges · 70 communities (53 shown, 17 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 137 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `06f6f555`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- news.py
- metrics
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
- run_one
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
- carry_forward
- targets.py
- backtest.py
- opex_days
- rsi

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
- `stat()` --calls--> `h()`  [EXTRACTED]
  app_pages/home.py → sharkfin/ui.py
- `stage_pill()` --calls--> `h()`  [EXTRACTED]
  app_pages/speculation.py → sharkfin/ui.py
- `load_scan()` --indirect_call--> `download_prices()`  [INFERRED]
  app_pages/scanner.py → sharkfin/data.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (70 total, 17 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (33): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+25 more)

### Community 1 - "news.py"
Cohesion: 0.24
Nodes (9): render(), _tone_line(), card(), fmt_money(), news_item(), pill(), time_ago(), tone() (+1 more)

### Community 2 - "metrics"
Cohesion: 0.33
Nodes (3): _filings(), esc(), metrics()

### Community 3 - "builder.py"
Cohesion: 0.05
Nodes (47): _add(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value() (+39 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.08
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.17
Nodes (20): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders() (+12 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.14
Nodes (16): _align(), backtest(), latest(), market_on(), _members(), percentile_against(), plus_frames(), quality_points() (+8 more)

### Community 8 - "indicators.py"
Cohesion: 0.14
Nodes (20): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+12 more)

### Community 9 - "ui.py"
Cohesion: 0.08
Nodes (26): choices(), asset(), color(), day_color(), disclaimer(), fetch_all(), header(), hero() (+18 more)

### Community 10 - "day_night.py"
Cohesion: 0.12
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 11 - "live.py"
Cohesion: 0.14
Nodes (12): leader_dip_run(), download_ohlcv(), breakout_today(), leader_dip_today(), market_inputs(), sector_map(), sector_ret3(), sp500_ohlcv() (+4 more)

### Community 12 - "catalysts.py"
Cohesion: 0.05
Nodes (39): catalysts_view(), could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change() (+31 more)

### Community 13 - "Playbook Page"
Cohesion: 0.16
Nodes (23): backtest_summary(), both_view(), br_backtest(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table() (+15 more)

### Community 14 - "data.py"
Cohesion: 0.12
Nodes (12): _copy(), _edgar_filings(), market_status(), news(), _NYSECalendar, _parse_date(), _rss(), sec_cik() (+4 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "walkforward.py"
Cohesion: 0.11
Nodes (13): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 17 - "fakes.py"
Cohesion: 0.20
Nodes (15): _base_info(), download_ohlcv(), download_prices(), financials(), history(), info(), install(), news() (+7 more)

### Community 18 - "test_leaks.py"
Cohesion: 0.14
Nodes (9): daily_cash(), run(), offline(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes() (+1 more)

### Community 19 - "stock_ratings"
Cohesion: 0.11
Nodes (20): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), analyst_data(), download_prices() (+12 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.14
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "breakout_rider.py"
Cohesion: 0.12
Nodes (12): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+4 more)

### Community 22 - "intraday_bars"
Cohesion: 0.11
Nodes (14): factor_backtest(), alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade() (+6 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.05
Nodes (42): prices(), beat_model(), breadth(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study() (+34 more)

### Community 24 - "run_one"
Cohesion: 0.33
Nodes (3): first_usable(), run_one(), Strategy

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (15): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+7 more)

### Community 27 - "scanner.py"
Cohesion: 0.12
Nodes (18): breakout_tab(), get_universe(), leader_dip_tab(), load_scan(), log_prices(), log_signals(), market_close(), ratings_tab() (+10 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.16
Nodes (16): bollinger_fade(), bracket(), Day, day_long_only(), ema_cross_5m(), _ema_rows(), _filter(), first_true() (+8 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.11
Nodes (18): build_tab(), _cat(), catalyst_tab(), condition_rows(), leader_dip_tab(), _load(), _pct_cols(), _remove() (+10 more)

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "sharkfin/__init__.py"
Cohesion: 0.08
Nodes (6): stat(), tile(), pct(), stage_pill(), updown(), reload_changed_sharkfin()

### Community 34 - "_cached_panel"
Cohesion: 0.16
Nodes (12): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save() (+4 more)

### Community 35 - "market_today.py"
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 36 - "predictions.py"
Cohesion: 0.15
Nodes (7): run_forecast(), lab_walk_forward(), history(), market_history(), risk_free_rate(), tbill_yields(), ttm()

### Community 37 - "ttl_cache"
Cohesion: 0.13
Nodes (13): all_symbols(), _is_empty(), nasdaq100(), prefetch(), search(), sp500_table(), ttl_cache(), deco() (+5 more)

### Community 38 - "numpy"
Cohesion: 0.18
Nodes (12): cut(), _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only(), test_gex_plays_decide_from_earlier_bars_only() (+4 more)

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
Cohesion: 0.50
Nodes (3): _band(), regime(), test_regime_band_and_switch()

### Community 44 - "Series"
Cohesion: 0.09
Nodes (14): atr(), deflated_sharpe(), fetch(), _folds_beating_cash(), intraday_frames(), load(), main(), night_returns() (+6 more)

### Community 47 - "test_core.py"
Cohesion: 0.08
Nodes (18): _intraday_ttl(), hurst_exponent(), _earn_table(), _one_day_matrix(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple() (+10 more)

### Community 49 - "nq_regimes.py"
Cohesion: 0.11
Nodes (18): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+10 more)

### Community 50 - "factors.py"
Cohesion: 0.06
Nodes (35): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+27 more)

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
Cohesion: 0.21
Nodes (6): opex_days(), opex_week(), evaluate(), day_view(), known(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 67 - "rsi"
Cohesion: 0.29
Nodes (5): rsi(), follow_up(), test_leader_dip_follow_up(), test_rsi_bounds_and_wilder(), test_rsi_matches_reference_formula()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 510 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `run`, `builder.py`, `numpy`, `leader_dip.py`, `day_night.py`, `factors.py`, `breakout_rider.py`, `run_one`, `sec_lab.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05401234567901234 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `walkforward.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.053613053613053616 - nodes in this community are weakly interconnected._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._
- **Should `Return Forecasting Models` be split into smaller, more focused modules?**
  _Cohesion score 0.07560975609756097 - nodes in this community are weakly interconnected._