# Graph Report - SharkFin  (2026-11-15)

## Corpus Check
- 85 files · ~140,876 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 57 file(s) not represented in the graph (top: .csv 55, (none) 1, .toml 1)
- WARNING: 57 of 155 files seen (37%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1881 nodes · 4900 edges · 104 communities (76 shown, 28 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 156 edges (avg confidence: 0.85)
- Token cost: 156,881 input · 0 output

## Graph Freshness
- Built from commit: `b8992135`
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
- indicators.py
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
- leader_dip.py
- factors.py
- DataFrame
- steps
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- sharpe_lab.py
- run
- test_store.py
- alerts.py
- assess
- options_lab.py
- load_scan
- numpy
- drivers.py
- MCP Servers
- Current Logo
- risk.py
- test_rss_feeds_download_with_a_timeout
- Series
- Offline Test Design
- test_core.py
- walkforward.py
- ratings.py
- Results
- growth_lab.py
- targets.py
- math
- voice.py
- test_catalyst_lab.py
- strategy_lab.py
- store.py
- pickle
- json
- Phone alerts (free, through ntfy)
- test_voice_import.py
- forward_growth
- test_leaks.py
- catalysts.py
- init_state
- _load
- bs.py
- catalysts_view
- catalyst_lab.py
- pandas
- market_today.py
- Voice commands and screenshot import
- The Sharpe-2 hunt: stock strategies and options strategies (Nov 2026)
- options_earnings.py
- streamlit
- test_alerts.py
- sharkfin/__init__.py
- backtest.py
- sys
- opex_days
- json
- pdufa_dates
- _Client
- kalshi_daily
- sp500_ever
- risk_contributions
- test_headline_class
- first_in

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `build_tab()` - 25 edges
5. `catalysts_view()` - 25 edges
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
- `Code` --references--> `save_list()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `save_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `init_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (104 total, 28 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 2 - "sec_lab.py"
Cohesion: 0.15
Nodes (14): dilution_table(), _era(), full_text(), headline_class(), main(), pdufa_events(), pdufa_study(), pdufa_table() (+6 more)

### Community 3 - "builder.py"
Cohesion: 0.07
Nodes (35): _add(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value() (+27 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.08
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.08
Nodes (41): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+33 more)

### Community 7 - "indicators.py"
Cohesion: 0.08
Nodes (30): positions(), build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema() (+22 more)

### Community 8 - "breakout_rider.py"
Cohesion: 0.20
Nodes (8): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate()

### Community 9 - "ui.py"
Cohesion: 0.11
Nodes (20): switch_strip(), card(), clean_text(), asset(), checklist(), compact_frame(), _finite(), fmt_big() (+12 more)

### Community 10 - "day_night.py"
Cohesion: 0.12
Nodes (16): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+8 more)

### Community 11 - "ttl_cache"
Cohesion: 0.08
Nodes (25): br_backtest(), ld_backtest(), run_forecast(), lab_walk_forward(), leader_dip_run(), download_ohlcv(), history(), last_years() (+17 more)

### Community 12 - "DataFrame"
Cohesion: 0.14
Nodes (12): _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), insider_summary(), revision_balance(), volume_read() (+4 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.17
Nodes (21): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+13 more)

### Community 14 - "data.py"
Cohesion: 0.07
Nodes (29): all_symbols(), alpaca_bars(), alpaca_daily(), _edgar_filings(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials() (+21 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.17
Nodes (13): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+5 more)

### Community 16 - "sentiment.py"
Cohesion: 0.13
Nodes (13): could_run_tab(), aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles() (+5 more)

### Community 17 - "sharkfin/speculation.py"
Cohesion: 0.11
Nodes (11): prices(), theme_turn(), all_tickers(), Play, radar(), stage(), stage_history(), stats() (+3 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.11
Nodes (19): evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix() (+11 more)

### Community 19 - "stock_ratings"
Cohesion: 0.16
Nodes (10): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), infos(), peers_for() (+2 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.18
Nodes (11): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+3 more)

### Community 21 - "leader_dip.py"
Cohesion: 0.11
Nodes (21): _align(), backtest(), _band(), follow_up(), latest(), market_on(), _members(), percentile_against() (+13 more)

### Community 22 - "factors.py"
Cohesion: 0.11
Nodes (21): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+13 more)

### Community 23 - "DataFrame"
Cohesion: 0.21
Nodes (9): breadth_setups(), _forward(), _hold_for(), _hold_until(), kalshi_tests(), _perf(), _portfolio(), stage_panel() (+1 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (16): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+8 more)

### Community 27 - "scanner.py"
Cohesion: 0.11
Nodes (21): breakout_tab(), factor_backtest(), get_universe(), leader_dip_tab(), load_scan(), log_prices(), log_signals(), market_close() (+13 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 31 - "sharpe_lab.py"
Cohesion: 0.12
Nodes (21): both(), cost_of(), fear_day_long(), _hold(), ibs_basket(), inverse_vol_blend(), load(), main() (+13 more)

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "test_store.py"
Cohesion: 0.16
Nodes (13): Identity, load(), save(), FakeResp, test_accounts_are_separate(), test_cloud_outage_raises(), test_cloud_round_trip(), get() (+5 more)

### Community 34 - "alerts.py"
Cohesion: 0.18
Nodes (11): compose(), holding_exits(), new_topic(), portfolio_threat(), run(), send(), signal_lines(), todays_signals() (+3 more)

### Community 35 - "assess"
Cohesion: 0.17
Nodes (12): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), _prices(), test_calm_portfolio_is_low(), test_crash_concentration_and_market_stress_is_high() (+4 more)

### Community 36 - "options_lab.py"
Cohesion: 0.17
Nodes (15): build_days(), context(), day_snapshot(), grade(), iron_condor(), iron_fly(), leg_price(), long_call() (+7 more)

### Community 37 - "load_scan"
Cohesion: 0.17
Nodes (8): _copy(), _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "numpy"
Cohesion: 0.20
Nodes (11): _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only(), test_gex_plays_decide_from_earlier_bars_only(), test_router_only_learns_from_finished_days() (+3 more)

### Community 39 - "drivers.py"
Cohesion: 0.21
Nodes (7): drivers(), earnings_record(), estimate_trend(), _naive(), _num(), _tone(), test_drivers_earnings_record_and_estimates()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "risk.py"
Cohesion: 0.20
Nodes (13): annualized_return(), annualized_vol(), beta_alpha(), calmar_ratio(), cornish_fisher_var(), drawdown_series(), historical_cvar(), historical_var() (+5 more)

### Community 44 - "Series"
Cohesion: 0.07
Nodes (16): atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), known(), load() (+8 more)

### Community 47 - "test_core.py"
Cohesion: 0.09
Nodes (20): fair_value_summary(), _earn_table(), _one_day_matrix(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_day_leg_buys_only_above_band_and_vwap_and_never_rebuys_at_the_sell_check(), test_drawdown_simple() (+12 more)

### Community 49 - "walkforward.py"
Cohesion: 0.11
Nodes (13): gate_grid(), cut(), _day(), Fold, folds(), grid(), _neighbours(), pick() (+5 more)

### Community 50 - "ratings.py"
Cohesion: 0.16
Nodes (10): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), value_inputs() (+2 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "growth_lab.py"
Cohesion: 0.15
Nodes (19): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), entry_zones(), fear_buyer(), filters() (+11 more)

### Community 60 - "targets.py"
Cohesion: 0.23
Nodes (5): blume_adjusted_beta(), entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "math"
Cohesion: 0.19
Nodes (9): bs_delta(), calibrate(), check_fit(), fit_real_smiles(), main(), model_iv(), run(), stats() (+1 more)

### Community 63 - "voice.py"
Cohesion: 0.15
Nodes (12): voice_box(), brief_text(), last2(), _clean(), Command, _component(), mic(), _num() (+4 more)

### Community 64 - "test_catalyst_lab.py"
Cohesion: 0.29
Nodes (8): breadth(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_earnings_frame_reports_five_year_average_eps(), test_falling_knife_gets_no_reversal_credit(), test_stage_panel_matches_the_radar()

### Community 65 - "strategy_lab.py"
Cohesion: 0.19
Nodes (12): build_tab(), _cat(), catalyst_tab(), condition_rows(), _load(), _pct_cols(), _remove(), split_open_trade() (+4 more)

### Community 66 - "store.py"
Cohesion: 0.20
Nodes (12): auth_configured(), cloud_all(), _cloud_read(), _cloud_write(), hash_id(), _headers(), identity(), _secrets() (+4 more)

### Community 67 - "pickle"
Cohesion: 0.07
Nodes (21): chunk(), _alpaca_get(), alpaca_keys(), _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk() (+13 more)

### Community 69 - "json"
Cohesion: 0.29
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "test_voice_import.py"
Cohesion: 0.12
Nodes (9): claude_positions(), clean_rows(), _json_array(), ocr_text(), parse_positions(), _to_float(), test_claude_reply_is_cleaned(), test_oversized_image_refused_before_decoding() (+1 more)

### Community 73 - "test_leaks.py"
Cohesion: 0.11
Nodes (12): daily_cash(), panel_adx(), panel_atr(), run(), stats(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled() (+4 more)

### Community 77 - "catalysts.py"
Cohesion: 0.20
Nodes (10): filing_change(), html_to_text(), new_sentences(), risk_factors_section(), _sentences(), text_similarity(), headline_drivers(), clean_text() (+2 more)

### Community 78 - "init_state"
Cohesion: 0.17
Nodes (8): overview(), color(), day_color(), mode(), setup(), _template(), theme_css(), _waves()

### Community 79 - "_load"
Cohesion: 0.11
Nodes (14): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Code, Moving to your own domain later, Sign-in and private portfolios: setup, choices(), account_box() (+6 more)

### Community 81 - "bs.py"
Cohesion: 0.16
Nodes (8): bs_price(), fit_smile(), implied_vol(), smile_iv(), Surface, test_next_open_engine_ignores_future(), test_put_call_parity_and_iv_round_trip(), test_smile_fit_recovers_shape()

### Community 82 - "catalysts_view"
Cohesion: 0.10
Nodes (16): catalysts_view(), _filings(), pct(), stage_pill(), updown(), analyst_data(), info(), esc() (+8 more)

### Community 83 - "catalyst_lab.py"
Cohesion: 0.16
Nodes (11): beat_model(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), load(), main() (+3 more)

### Community 84 - "pandas"
Cohesion: 0.26
Nodes (9): make_ohlcv(), ohlcv(), price_panel(), prices(), test_pdufa_dates_only_future_dates_near_the_word(), test_pdufa_events_merge_close_dates_and_flag_extensions(), test_pdufa_trade_starts_after_the_announcement_and_ignores_later_bars(), test_pop_study_counts_shelves_filed_before_the_jump_only() (+1 more)

### Community 85 - "market_today.py"
Cohesion: 0.19
Nodes (7): breadth(), direction(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 86 - "Voice commands and screenshot import"
Cohesion: 0.50
Nodes (3): "Hey SharkFin" (sidebar, every page), Import from a screenshot (Portfolio), Voice commands and screenshot import

### Community 87 - "The Sharpe-2 hunt: stock strategies and options strategies (Nov 2026)"
Cohesion: 0.15
Nodes (12): 1. Stocks and ETFs: nothing reaches 2, 2. Black-Scholes and the implied-vol surface, 3. Twenty years of S&P premium selling (model, checked above), 4. Same-day (0DTE) QQQ and SPY: the one near-2 result, 5. Earnings options (821 real reports, 77 stocks), 6. Our own signals, traded with options (real prices, 2024-2026), Data, Files (+4 more)

### Community 88 - "options_earnings.py"
Cohesion: 0.26
Nodes (7): _at(), drift_call(), event_rows(), grade(), _leg(), main(), summarise()

### Community 90 - "streamlit"
Cohesion: 0.21
Nodes (5): render(), _tone_line(), disclaimer(), fetch_all(), hero()

### Community 91 - "test_alerts.py"
Cohesion: 0.26
Nodes (8): threat_line(), Threat, test_compose_signals_exits_and_threat(), test_quiet_day_sends_nothing(), test_run_sends_per_user_and_saves_state(), test_send_refuses_bad_topic(), test_threat_only_when_it_rises_or_is_high(), _th()

### Community 93 - "backtest.py"
Cohesion: 0.36
Nodes (4): compare(), run(), Strategy, test_backtest_no_lookahead()

### Community 94 - "sys"
Cohesion: 0.36
Nodes (3): main(), replay(), summary()

### Community 95 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 96 - "json"
Cohesion: 0.40
Nodes (4): rules_key(), _local_path(), _read_file(), _write_file()

### Community 97 - "pdufa_dates"
Cohesion: 0.40
Nodes (3): _intraday_ttl(), future_dates(), pdufa_dates()

### Community 98 - "_Client"
Cohesion: 0.33
Nodes (3): _Client, user_agent(), test_needs_a_contact()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 643 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sp500_members()` connect `data.py` to `test_app.py`, `test_leaks.py`, `ttl_cache`, `catalyst_lab.py`, `Results`, `pandas`, `growth_lab.py`, `scanner.py`, `targets.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `run()` connect `walkforward.py` to `run`, `builder.py`, `breakout_rider.py`, `day_night.py`, `Series`, `pandas`, `leader_dip.py`, `factors.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06836055656382335 - nodes in this community are weakly interconnected._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._
- **Should `Return Forecasting Models` be split into smaller, more focused modules?**
  _Cohesion score 0.07560975609756097 - nodes in this community are weakly interconnected._