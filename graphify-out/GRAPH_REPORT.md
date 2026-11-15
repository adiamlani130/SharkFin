# Graph Report - SharkFin  (2026-11-14)

## Corpus Check
- 79 files · ~140,032 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 66 file(s) not represented in the graph (top: .csv 64, (none) 1, .toml 1)
- WARNING: 66 of 158 files seen (42%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1834 nodes · 4826 edges · 94 communities (73 shown, 21 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 147 edges (avg confidence: 0.85)
- Token cost: 156,881 input · 0 output

## Graph Freshness
- Built from commit: `6dc60ee9`
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
- catalysts_view
- day_night.py
- live.py
- DataFrame
- app_pages/playbook.py
- data.py
- sharkfin/playbook.py
- sentiment.py
- test_alerts.py
- nq_regimes.py
- stock_ratings
- sharkfin/portfolio.py
- carry_forward
- factors.py
- catalyst_lab.py
- steps
- leader_dip_run
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- leader_dip.py
- run
- predictions.py
- alerts.py
- assess
- Sign-in and private portfolios: setup
- load_scan
- store.py
- drivers.py
- MCP Servers
- Current Logo
- DataFrame
- walkforward.py
- main
- Offline Test Design
- test_core.py
- ui.py
- ratings.py
- Results
- pandas
- targets.py
- market_today.py
- voice.py
- test_voice_import.py
- strategy_lab.py
- test_nq_lab.py
- pickle
- json
- Phone alerts (free, through ntfy)
- test_voice_import.py
- test_store.py
- swing_engine.py
- catalysts.py
- color
- 2. How the Speculation Radar finds themes, and whether that works
- NQ strategy lab: results (October 2026)
- ttl_cache
- levels.py
- backtest.py
- main.py
- fakes.py
- Voice commands and screenshot import
- opex_days
- rsi
- regime
- could_run
- _fetch_prices
- test_day_leg_buys_only_above_band_and_vwap_and_never_rebuys_at_the_sell_check

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `build_tab()` - 25 edges
5. `main()` - 25 edges
6. `catalysts_view()` - 25 edges
7. `quality_metrics()` - 22 edges
8. `_sw()` - 22 edges
9. `backtest()` - 21 edges
10. `download_prices()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `Code` --references--> `account_box()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `guest_notice()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `init_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (94 total, 21 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (33): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+25 more)

### Community 1 - "sharkfin/__init__.py"
Cohesion: 0.11
Nodes (4): stat(), tile(), pct(), stage_pill()

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
Cohesion: 0.08
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.18
Nodes (20): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders() (+12 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.13
Nodes (20): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+12 more)

### Community 8 - "breakout_rider.py"
Cohesion: 0.12
Nodes (12): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+4 more)

### Community 9 - "catalysts_view"
Cohesion: 0.10
Nodes (19): catalysts_view(), _filings(), render(), _tone_line(), compact_frame(), esc(), _finite(), fmt_big() (+11 more)

### Community 10 - "day_night.py"
Cohesion: 0.12
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 11 - "live.py"
Cohesion: 0.16
Nodes (10): breakout_today(), dive_zone_latest(), leader_dip_today(), market_inputs(), sector_map(), sector_ret3(), sp500_ohlcv(), summary_rows() (+2 more)

### Community 12 - "DataFrame"
Cohesion: 0.15
Nodes (11): _col(), core_long_screen(), earnings_beat_flag(), earnings_summary(), insider_summary(), revision_balance(), volume_read(), _z() (+3 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.19
Nodes (21): backtest_summary(), both_view(), br_backtest(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table() (+13 more)

### Community 14 - "data.py"
Cohesion: 0.11
Nodes (14): get_universe(), all_symbols(), _copy(), _edgar_filings(), market_status(), nasdaq100(), news(), _NYSECalendar (+6 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "sentiment.py"
Cohesion: 0.15
Nodes (13): aggregate_sentiment(), BM25, clean_text(), dedupe(), hours_old(), is_noise(), label(), rank_articles() (+5 more)

### Community 17 - "test_alerts.py"
Cohesion: 0.26
Nodes (8): threat_line(), Threat, test_compose_signals_exits_and_threat(), test_quiet_day_sends_nothing(), test_run_sends_per_user_and_saves_state(), test_send_refuses_bad_topic(), test_threat_only_when_it_rises_or_is_high(), _th()

### Community 18 - "nq_regimes.py"
Cohesion: 0.11
Nodes (19): evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix() (+11 more)

### Community 19 - "stock_ratings"
Cohesion: 0.22
Nodes (7): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), download_prices()

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.14
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 22 - "factors.py"
Cohesion: 0.10
Nodes (22): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+14 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.05
Nodes (42): prices(), beat_model(), breadth(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study() (+34 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 25 - "leader_dip_run"
Cohesion: 0.27
Nodes (6): ld_backtest(), leader_dip_run(), last_years(), sp500_members(), yahoo_period(), dive_zone_misses()

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (16): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+8 more)

### Community 27 - "scanner.py"
Cohesion: 0.12
Nodes (20): switch_strip(), breakout_tab(), card(), factor_backtest(), leader_dip_tab(), log_prices(), log_signals(), market_close() (+12 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.13
Nodes (27): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+19 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 31 - "leader_dip.py"
Cohesion: 0.10
Nodes (24): _align(), backtest(), drop_recent_misses(), latest(), market_on(), _members(), missed_recently(), misses_from_histories() (+16 more)

### Community 32 - "run"
Cohesion: 0.20
Nodes (9): Does GEX shrink the day? Yes, Fear day long, checked, Part 2: GEX and VIX as a daily playbook, Part 3: three GEX setups (call-wall fade, negative-gamma breakout, OpEx fly/condor), Results (out of sample), Results (unseen test years; swing May 2015 to Oct 2026, day trades Apr 2019 to Oct 2026), What each level meant (whole-sample description, not a tested trade), What was real and what was approximated (+1 more)

### Community 33 - "predictions.py"
Cohesion: 0.18
Nodes (6): run_forecast(), history(), market_history(), risk_free_rate(), tbill_yields(), ttm()

### Community 34 - "alerts.py"
Cohesion: 0.18
Nodes (11): compose(), holding_exits(), new_topic(), portfolio_threat(), run(), send(), signal_lines(), todays_signals() (+3 more)

### Community 35 - "assess"
Cohesion: 0.17
Nodes (12): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), _prices(), test_calm_portfolio_is_low(), test_crash_concentration_and_market_stress_is_high() (+4 more)

### Community 36 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

### Community 37 - "load_scan"
Cohesion: 0.16
Nodes (8): load_scan(), _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "store.py"
Cohesion: 0.22
Nodes (11): auth_configured(), cloud_all(), _cloud_read(), _cloud_write(), hash_id(), _headers(), identity(), _secrets() (+3 more)

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
Nodes (13): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _parse_spells() (+5 more)

### Community 43 - "walkforward.py"
Cohesion: 0.11
Nodes (13): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 44 - "main"
Cohesion: 0.08
Nodes (13): atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), known(), load() (+5 more)

### Community 47 - "test_core.py"
Cohesion: 0.09
Nodes (14): hurst_exponent(), _earn_table(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer(), test_features_have_no_lookahead() (+6 more)

### Community 49 - "ui.py"
Cohesion: 0.07
Nodes (30): Code, price_of(), choices(), account_box(), asset(), disclaimer(), fetch_all(), guest_notice() (+22 more)

### Community 50 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "pandas"
Cohesion: 0.05
Nodes (63): sp500_ever(), baseline_events(), _both(), breakout_confluences(), combos(), confluences(), download(), get() (+55 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "market_today.py"
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 63 - "voice.py"
Cohesion: 0.15
Nodes (12): voice_box(), brief_text(), last2(), _clean(), Command, _component(), mic(), _num() (+4 more)

### Community 65 - "strategy_lab.py"
Cohesion: 0.19
Nodes (12): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), lab_walk_forward(), _load(), _pct_cols() (+4 more)

### Community 66 - "test_nq_lab.py"
Cohesion: 0.13
Nodes (17): updown(), trailing_pct(), cut(), make_ohlcv(), ohlcv(), price_panel(), _market(), _settings() (+9 more)

### Community 67 - "pickle"
Cohesion: 0.16
Nodes (12): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save() (+4 more)

### Community 69 - "json"
Cohesion: 0.29
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "test_voice_import.py"
Cohesion: 0.21
Nodes (7): claude_positions(), clean_rows(), _json_array(), parse_positions(), _to_float(), test_claude_reply_is_cleaned(), test_parse_positions_one_line_and_two_line_layouts()

### Community 72 - "test_store.py"
Cohesion: 0.14
Nodes (16): Identity, load(), _local_path(), _read_file(), save(), _write_file(), FakeResp, test_accounts_are_separate() (+8 more)

### Community 73 - "swing_engine.py"
Cohesion: 0.17
Nodes (8): daily_cash(), run(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled()

### Community 77 - "catalysts.py"
Cohesion: 0.26
Nodes (8): filing_change(), html_to_text(), new_sentences(), risk_factors_section(), _sentences(), text_similarity(), clean_text(), test_filing_change_finds_new_risk_language()

### Community 78 - "color"
Cohesion: 0.33
Nodes (4): overview(), color(), day_color(), _template()

### Community 79 - "2. How the Speculation Radar finds themes, and whether that works"
Cohesion: 0.13
Nodes (14): 1. Improving Dive Zone, Breakout Rider and the ranking, 2. How the Speculation Radar finds themes, and whether that works, 3. Your idea: a "low bar" earnings beat in a beaten-down growth sector, As a portfolio, Dive Zone (as is: 20.5%/yr pick, Sharpe 1.20; 27.6%/yr grade, Sharpe 1.13), Edge lab: strategy research, round 2 (Nov 14 2026), Firing now (as of Nov 13 2026), How big is a breakthrough? (+6 more)

### Community 80 - "NQ strategy lab: results (October 2026)"
Cohesion: 0.25
Nodes (8): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Rerun, Swing results (test years May 2015 to Oct 2026), What GEX showed

### Community 81 - "ttl_cache"
Cohesion: 0.16
Nodes (13): scan_data(), analyst_data(), earnings_histories(), financials(), industry_members(), info(), infos(), peers_for() (+5 more)

### Community 82 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 83 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 85 - "fakes.py"
Cohesion: 0.13
Nodes (21): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+13 more)

### Community 86 - "Voice commands and screenshot import"
Cohesion: 0.50
Nodes (3): "Hey SharkFin" (sidebar, every page), Import from a screenshot (Portfolio), Voice commands and screenshot import

### Community 87 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 88 - "rsi"
Cohesion: 0.29
Nodes (5): rsi(), follow_up(), test_leader_dip_follow_up(), test_rsi_bounds_and_wilder(), test_rsi_matches_reference_formula()

### Community 90 - "regime"
Cohesion: 0.50
Nodes (3): _band(), regime(), test_regime_band_and_switch()

### Community 91 - "could_run"
Cohesion: 0.40
Nodes (3): could_run_tab(), could_run(), test_could_run_screen()

### Community 92 - "_fetch_prices"
Cohesion: 0.40
Nodes (4): _fetch_ohlcv(), _fetch_prices(), fetch(), _naive()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 629 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sp500_members()` connect `leader_dip_run` to `test_nq_lab.py`, `swing_engine.py`, `DataFrame`, `app_pages/playbook.py`, `data.py`, `Results`, `fakes.py`, `catalyst_lab.py`, `pandas`, `scanner.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05401234567901234 - nodes in this community are weakly interconnected._
- **Why does `Rules` connect `Results` to `leader_dip_run`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `sharkfin/__init__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07673469387755102 - nodes in this community are weakly interconnected._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05468215994531784 - nodes in this community are weakly interconnected._