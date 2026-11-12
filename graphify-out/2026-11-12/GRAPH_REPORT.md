# Graph Report - SharkFin  (2026-11-10)

## Corpus Check
- 63 files · ~119,641 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .csv 48, (none) 1, .toml 1)
- WARNING: 50 of 125 files seen (40%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1530 nodes · 4056 edges · 83 communities (63 shown, 20 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 137 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bcaca87c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- streamlit
- sec_lab.py
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
- sharkfin/playbook.py
- sentiment.py
- sharkfin/speculation.py
- builder.py
- stock_ratings
- sharkfin/portfolio.py
- swing.py
- composite_scores
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
- ttl_cache
- load_scan
- numpy
- drivers.py
- MCP Servers
- Current Logo
- ai.py
- run
- Series
- Offline Test Design
- test_core.py
- nq_regimes.py
- ratings.py
- Results
- growth_lab.py
- backtest
- targets.py
- factors.py
- backtest.py
- test_catalyst_lab.py
- pandas
- opex_days
- rsi
- color
- _finite
- sys
- universe
- _Client
- kalshi_daily
- walk_forward
- test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt
- fair_value_summary

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `Day` - 18 edges
9. `download_prices()` - 18 edges
10. `sp500_table()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `test_fmt_money_negative_sign_before_dollar()` --calls--> `fmt_money()`  [EXTRACTED]
  tests/test_core.py → sharkfin/ui.py
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

## Communities (83 total, 20 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 1 - "streamlit"
Cohesion: 0.12
Nodes (18): stat(), tile(), catalysts_view(), _filings(), render(), _tone_line(), switch_strip(), card() (+10 more)

### Community 2 - "sec_lab.py"
Cohesion: 0.13
Nodes (15): dilution_table(), full_text(), future_dates(), headline_class(), main(), pdufa_dates(), pdufa_events(), pdufa_study() (+7 more)

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
Nodes (13): _align(), _band(), market_on(), percentile_against(), plus_frames(), quality_points(), regime(), sector_returns() (+5 more)

### Community 8 - "indicators.py"
Cohesion: 0.12
Nodes (22): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), hurst_exponent() (+14 more)

### Community 9 - "ui.py"
Cohesion: 0.09
Nodes (24): clean_text(), choices(), asset(), disclaimer(), header(), hero(), init_state(), kv() (+16 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "live.py"
Cohesion: 0.10
Nodes (19): br_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), last_years(), sp500_ever(), sp500_table(), tbill_yields() (+11 more)

### Community 12 - "catalysts.py"
Cohesion: 0.05
Nodes (45): _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text(), insider_summary() (+37 more)

### Community 13 - "Playbook Page"
Cohesion: 0.17
Nodes (21): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+13 more)

### Community 14 - "data.py"
Cohesion: 0.07
Nodes (25): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), _copy(), _edgar_filings(), intraday_bars() (+17 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "sentiment.py"
Cohesion: 0.13
Nodes (13): could_run_tab(), aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles() (+5 more)

### Community 17 - "sharkfin/speculation.py"
Cohesion: 0.14
Nodes (10): prices(), all_tickers(), Play, radar(), stage(), stage_history(), stats(), Theme (+2 more)

### Community 18 - "builder.py"
Cohesion: 0.17
Nodes (12): _close(), describe(), describe_strategy(), _fmt_value(), Indicator, knobs(), label(), _obv_gap() (+4 more)

### Community 19 - "stock_ratings"
Cohesion: 0.17
Nodes (10): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), download_prices(), infos() (+2 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.12
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "swing.py"
Cohesion: 0.20
Nodes (8): about(), clean(), _frame(), rule_checks(), rules(), scan(), stock_status(), test_swing_choice_rules_and_status()

### Community 22 - "composite_scores"
Cohesion: 0.18
Nodes (11): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), price_factor_frame(), test_earnings_frame_reports_five_year_average_eps(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_could_run_screen() (+3 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.11
Nodes (21): beat_model(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), _forward() (+13 more)

### Community 24 - "run_one"
Cohesion: 0.33
Nodes (3): first_usable(), run_one(), Strategy

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (15): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+7 more)

### Community 27 - "scanner.py"
Cohesion: 0.17
Nodes (15): breakout_tab(), factor_backtest(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+7 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.20
Nodes (12): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), _load(), _pct_cols(), _remove() (+4 more)

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "sharkfin/__init__.py"
Cohesion: 0.12
Nodes (3): stage_pill(), updown(), reload_changed_sharkfin()

### Community 34 - "_cached_panel"
Cohesion: 0.13
Nodes (14): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), _intraday_ttl(), _panel_file(), _panel_load(), _panel_save() (+6 more)

### Community 35 - "market_today.py"
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 36 - "ttl_cache"
Cohesion: 0.11
Nodes (18): run_forecast(), lab_walk_forward(), analyst_data(), earnings_histories(), earnings_history(), _fetch_ohlcv(), _fetch_prices(), fetch() (+10 more)

### Community 37 - "load_scan"
Cohesion: 0.24
Nodes (7): load_scan(), _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh()

### Community 38 - "numpy"
Cohesion: 0.17
Nodes (13): trailing_pct(), cut(), _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only() (+5 more)

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

### Community 43 - "run"
Cohesion: 0.23
Nodes (8): compare_templates(), condition_mask(), run(), series(), signals(), template(), warmup(), test_builder_templates_run_and_describe()

### Community 44 - "Series"
Cohesion: 0.08
Nodes (14): atr(), deflated_sharpe(), fetch(), _folds_beating_cash(), intraday_frames(), known(), load(), main() (+6 more)

### Community 47 - "test_core.py"
Cohesion: 0.09
Nodes (16): forward_growth(), _earn_table(), _ohlc(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_builder_fills_next_open_and_stops(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports() (+8 more)

### Community 49 - "nq_regimes.py"
Cohesion: 0.06
Nodes (31): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+23 more)

### Community 50 - "ratings.py"
Cohesion: 0.16
Nodes (10): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), value_inputs() (+2 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "growth_lab.py"
Cohesion: 0.06
Nodes (34): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+26 more)

### Community 59 - "backtest"
Cohesion: 0.29
Nodes (6): _market_gap(), backtest(), carry_forward(), _panel(), test_leader_dip_backtest_fills_limits_and_exits(), test_leader_dip_idle_cash_choices()

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "factors.py"
Cohesion: 0.21
Nodes (9): explain(), falling_knife(), fundamental_factor_frame(), is_cyclical(), sector_neutral_z(), winsorize(), zscore(), test_cyclical_stocks_are_valued_on_through_cycle_earnings() (+1 more)

### Community 63 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 64 - "test_catalyst_lab.py"
Cohesion: 0.23
Nodes (9): breadth(), first_in(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_falling_knife_gets_no_reversal_credit(), test_first_in_takes_one_entry_per_episode() (+1 more)

### Community 65 - "pandas"
Cohesion: 0.30
Nodes (8): _era(), prices(), test_headline_class(), test_pdufa_dates_only_future_dates_near_the_word(), test_pdufa_events_merge_close_dates_and_flag_extensions(), test_pdufa_trade_starts_after_the_announcement_and_ignores_later_bars(), test_pop_study_counts_shelves_filed_before_the_jump_only(), test_readout_offer_flag_and_reaction_window()

### Community 66 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 67 - "rsi"
Cohesion: 0.21
Nodes (8): rsi(), follow_up(), latest(), _members(), signal_frames(), six_month_gain(), test_leader_dip_follow_up(), test_leader_dip_signals_have_no_lookahead()

### Community 68 - "color"
Cohesion: 0.25
Nodes (5): overview(), color(), day_color(), mode(), _template()

### Community 69 - "_finite"
Cohesion: 0.29
Nodes (5): compact_frame(), _finite(), fmt_big(), fmt_x(), tone()

### Community 70 - "sys"
Cohesion: 0.38
Nodes (3): make_ohlcv(), ohlcv(), price_panel()

### Community 71 - "universe"
Cohesion: 0.33
Nodes (5): get_universe(), all_symbols(), nasdaq100(), search(), universe()

### Community 72 - "_Client"
Cohesion: 0.33
Nodes (3): _Client, user_agent(), test_needs_a_contact()

### Community 77 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 511 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `nq_regimes.py` to `run`, `pandas`, `numpy`, `leader_dip.py`, `day_night.py`, `walk_forward`, `builder.py`, `run_one`, `growth_lab.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `sp500_members()` connect `data.py` to `pandas`, `numpy`, `live.py`, `catalysts.py`, `Results`, `catalyst_lab.py`, `growth_lab.py`, `scanner.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Should `streamlit` be split into smaller, more focused modules?**
  _Cohesion score 0.1164021164021164 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `nq_regimes.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13118279569892474 - nodes in this community are weakly interconnected._