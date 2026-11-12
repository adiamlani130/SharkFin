# Graph Report - SharkFin  (2026-11-12)

## Corpus Check
- 76 files · ~129,648 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .csv 48, (none) 1, .toml 1)
- WARNING: 50 of 139 files seen (36%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1735 nodes · 4519 edges · 90 communities (65 shown, 25 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 146 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fdedb346`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- sharkfin/__init__.py
- sec_lab.py
- builder.py
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- leader_dip.py
- breakout_rider.py
- ui.py
- day_night.py
- ttl_cache
- DataFrame
- app_pages/playbook.py
- data.py
- sharkfin/playbook.py
- sentiment.py
- sharkfin/speculation.py
- nq_regimes.py
- stock_ratings
- sharkfin/portfolio.py
- _finite
- factors.py
- catalyst_lab.py
- steps
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- levels.py
- run
- test_store.py
- alerts.py
- assess
- Sign-in and private portfolios: setup
- load_scan
- numpy
- drivers.py
- MCP Servers
- Current Logo
- DataFrame
- test_rss_feeds_download_with_a_timeout
- Series
- Offline Test Design
- test_core.py
- walkforward.py
- ratings.py
- Results
- growth_lab.py
- targets.py
- fakes.py
- voice.py
- test_catalyst_lab.py
- strategy_lab.py
- store.py
- pickle
- json
- Phone alerts (free, through ntfy)
- screenshot_import.py
- forward_growth
- test_leaks.py
- catalysts.py
- init_state
- _load
- test_voice_import.py
- catalysts_view
- sp500_table
- sys
- walk_forward
- Voice commands and screenshot import
- theme_turn
- fair_value_summary

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `download_prices()` - 20 edges
9. `history()` - 19 edges
10. `assess()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `Code` --references--> `init_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `save_list()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `save_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (90 total, 25 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 2 - "sec_lab.py"
Cohesion: 0.08
Nodes (28): _intraday_ttl(), _Client, dilution_table(), _era(), full_text(), future_dates(), headline_class(), main() (+20 more)

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
Cohesion: 0.18
Nodes (20): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders() (+12 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.05
Nodes (51): compare(), positions(), run(), Strategy, _market_gap(), build_features(), adx(), atr() (+43 more)

### Community 8 - "breakout_rider.py"
Cohesion: 0.13
Nodes (11): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+3 more)

### Community 9 - "ui.py"
Cohesion: 0.07
Nodes (31): render(), _tone_line(), switch_strip(), Code, price_of(), clean_text(), account_box(), asset() (+23 more)

### Community 10 - "day_night.py"
Cohesion: 0.12
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 11 - "ttl_cache"
Cohesion: 0.11
Nodes (16): alpaca_daily(), download_ohlcv(), history(), market_history(), risk_free_rate(), ttl_cache(), breakout_today(), leader_dip_today() (+8 more)

### Community 12 - "DataFrame"
Cohesion: 0.12
Nodes (14): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), insider_summary(), revision_balance() (+6 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.11
Nodes (28): backtest_summary(), both_view(), br_backtest(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table() (+20 more)

### Community 14 - "data.py"
Cohesion: 0.11
Nodes (16): run_forecast(), analyst_data(), _copy(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials(), industry_members() (+8 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "sentiment.py"
Cohesion: 0.07
Nodes (21): stat(), breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders() (+13 more)

### Community 17 - "sharkfin/speculation.py"
Cohesion: 0.11
Nodes (12): prices(), stage_pill(), updown(), all_tickers(), Play, radar(), stage(), stage_history() (+4 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.10
Nodes (20): evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix() (+12 more)

### Community 19 - "stock_ratings"
Cohesion: 0.16
Nodes (10): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), download_prices(), infos() (+2 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "_finite"
Cohesion: 0.20
Nodes (7): compact_frame(), _finite(), fmt_big(), fmt_money(), fmt_num(), fmt_x(), test_fmt_money_negative_sign_before_dollar()

### Community 22 - "factors.py"
Cohesion: 0.13
Nodes (18): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+10 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.11
Nodes (20): beat_model(), breadth_setups(), entry_delay_table(), fda_study(), fda_table(), first_in(), _forward(), _hold_for() (+12 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.11
Nodes (18): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+10 more)

### Community 27 - "scanner.py"
Cohesion: 0.15
Nodes (17): breakout_tab(), card(), factor_backtest(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab() (+9 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.12
Nodes (29): atr(), buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized() (+21 more)

### Community 29 - "Day"
Cohesion: 0.16
Nodes (16): bollinger_fade(), bracket(), Day, day_long_only(), ema_cross_5m(), _ema_rows(), _filter(), first_true() (+8 more)

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "test_store.py"
Cohesion: 0.18
Nodes (11): Identity, load(), FakeResp, test_accounts_are_separate(), test_cloud_outage_raises(), test_cloud_round_trip(), get(), post() (+3 more)

### Community 34 - "alerts.py"
Cohesion: 0.12
Nodes (19): compose(), holding_exits(), new_topic(), portfolio_threat(), run(), send(), signal_lines(), threat_line() (+11 more)

### Community 35 - "assess"
Cohesion: 0.17
Nodes (12): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), _prices(), test_calm_portfolio_is_low(), test_crash_concentration_and_market_stress_is_high() (+4 more)

### Community 36 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

### Community 37 - "load_scan"
Cohesion: 0.20
Nodes (7): _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "numpy"
Cohesion: 0.16
Nodes (14): evaluate(), day_view(), cut(), _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result() (+6 more)

### Community 39 - "drivers.py"
Cohesion: 0.21
Nodes (7): drivers(), earnings_record(), estimate_trend(), _naive(), _num(), _tone(), test_drivers_earnings_record_and_estimates()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "DataFrame"
Cohesion: 0.12
Nodes (15): alpaca_bars(), chunk(), _alpaca_get(), alpaca_keys(), _edgar_filings(), intraday_bars(), latest_trade(), _parse_spells() (+7 more)

### Community 44 - "Series"
Cohesion: 0.09
Nodes (12): deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main(), rotation() (+4 more)

### Community 47 - "test_core.py"
Cohesion: 0.10
Nodes (17): _earn_table(), _one_day_matrix(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer() (+9 more)

### Community 49 - "walkforward.py"
Cohesion: 0.11
Nodes (13): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 50 - "ratings.py"
Cohesion: 0.17
Nodes (9): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), value_inputs() (+1 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "growth_lab.py"
Cohesion: 0.14
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "fakes.py"
Cohesion: 0.13
Nodes (21): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+13 more)

### Community 63 - "voice.py"
Cohesion: 0.15
Nodes (12): voice_box(), brief_text(), last2(), _clean(), Command, _component(), mic(), _num() (+4 more)

### Community 64 - "test_catalyst_lab.py"
Cohesion: 0.22
Nodes (12): breadth(), earnings_events(), _earnings_table(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_earnings_frame_reports_five_year_average_eps() (+4 more)

### Community 65 - "strategy_lab.py"
Cohesion: 0.19
Nodes (12): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), lab_walk_forward(), _load(), _pct_cols() (+4 more)

### Community 66 - "store.py"
Cohesion: 0.16
Nodes (16): auth_configured(), cloud_all(), _cloud_read(), _cloud_write(), hash_id(), _headers(), identity(), _local_path() (+8 more)

### Community 67 - "pickle"
Cohesion: 0.13
Nodes (14): load_scan(), _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), info(), _panel_file() (+6 more)

### Community 69 - "json"
Cohesion: 0.29
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "screenshot_import.py"
Cohesion: 0.17
Nodes (6): claude_positions(), clean_rows(), _json_array(), ocr_text(), _to_float(), test_claude_reply_is_cleaned()

### Community 73 - "test_leaks.py"
Cohesion: 0.17
Nodes (8): sp500_members(), daily_cash(), run(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_members_only_trade_while_in_the_index()

### Community 77 - "catalysts.py"
Cohesion: 0.22
Nodes (10): filing_change(), html_to_text(), new_sentences(), risk_factors_section(), _sentences(), text_similarity(), clean_text(), test_filing_change_finds_new_risk_language() (+2 more)

### Community 78 - "init_state"
Cohesion: 0.13
Nodes (10): overview(), color(), day_color(), init_state(), mode(), setup(), _template(), theme_css() (+2 more)

### Community 79 - "_load"
Cohesion: 0.24
Nodes (6): choices(), _load(), load_list(), my_swing_rules(), swing_choice(), swing_picker()

### Community 82 - "catalysts_view"
Cohesion: 0.29
Nodes (7): tile(), catalysts_view(), _filings(), pct(), sec_document_text(), fmt_pct(), symbol_picker()

### Community 83 - "sp500_table"
Cohesion: 0.29
Nodes (6): get_universe(), all_symbols(), nasdaq100(), search(), sp500_table(), universe()

### Community 84 - "sys"
Cohesion: 0.38
Nodes (3): make_ohlcv(), ohlcv(), price_panel()

### Community 85 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

### Community 86 - "Voice commands and screenshot import"
Cohesion: 0.50
Nodes (3): "Hey SharkFin" (sidebar, every page), Import from a screenshot (Portfolio), Voice commands and screenshot import

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 588 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `run`, `test_catalyst_lab.py`, `builder.py`, `numpy`, `leader_dip.py`, `breakout_rider.py`, `day_night.py`, `Series`, `walk_forward`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `walkforward.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07673469387755102 - nodes in this community are weakly interconnected._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05468215994531784 - nodes in this community are weakly interconnected._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._