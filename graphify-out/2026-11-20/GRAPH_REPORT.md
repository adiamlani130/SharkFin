# Graph Report - SharkFin  (2026-11-18)

## Corpus Check
- 91 files · ~178,503 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 68 file(s) not represented in the graph (top: .csv 66, (none) 1, .toml 1)
- WARNING: 68 of 174 files seen (39%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 2044 nodes · 5324 edges · 101 communities (78 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 161 edges (avg confidence: 0.85)
- Token cost: 156,881 input · 0 output

## Graph Freshness
- Built from commit: `9de6407a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- _cached_panel
- sec_lab.py
- builder.py
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- neuro_lab.py
- breakout_rider.py
- app_pages/speculation.py
- day_night.py
- live.py
- DataFrame
- strategy_lab.py
- data.py
- sharkfin/playbook.py
- streamlit
- frontier.py
- nq_regimes.py
- neat_core.py
- sharkfin/portfolio.py
- surface
- factors.py
- catalyst_lab.py
- steps
- growth_lab.py
- nq_gex_plays.py
- sp500_ever
- nq_lab.py
- Day
- leader_dip.py
- run
- indicators.py
- pandas
- assess
- Sign-in and private portfolios: setup
- load_scan
- Evolving trading strategies with NEAT, plus Merton jump-diffusion (Nov 2026)
- drivers.py
- MCP Servers
- Current Logo
- ttl_cache
- walkforward.py
- main
- Offline Test Design
- test_core.py
- backtest.py
- ui.py
- sharkfin/__init__.py
- Results
- edge_lab.py
- targets.py
- market_today.py
- voice.py
- test_voice_import.py
- rsi
- numpy
- frontier_build.py
- json
- Phone alerts (free, through ntfy)
- test_voice_import.py
- store.py
- daily_cash
- kalshi_daily
- alerts.py
- 2. How the Speculation Radar finds themes, and whether that works
- predictions.py
- scanner.py
- levels.py
- regime
- ratings.py
- test_store.py
- Voice commands and screenshot import
- describe
- carry_forward
- app_pages/playbook.py
- ping
- tracked_positions
- re
- _load
- jump_features
- _fetch_prices
- download
- _one_day_matrix

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `build_tab()` - 25 edges
5. `catalysts_view()` - 25 edges
6. `main()` - 25 edges
7. `quality_metrics()` - 22 edges
8. `_sw()` - 22 edges
9. `backtest()` - 21 edges
10. `download_prices()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `Code` --references--> `init_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `account_box()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `guest_notice()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (101 total, 23 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (33): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+25 more)

### Community 1 - "_cached_panel"
Cohesion: 0.18
Nodes (11): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save() (+3 more)

### Community 2 - "sec_lab.py"
Cohesion: 0.08
Nodes (27): _intraday_ttl(), _Client, dilution_table(), _era(), full_text(), future_dates(), headline_class(), main() (+19 more)

### Community 3 - "builder.py"
Cohesion: 0.05
Nodes (48): C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value(), Indicator (+40 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.08
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.08
Nodes (40): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+32 more)

### Community 7 - "neuro_lab.py"
Cohesion: 0.11
Nodes (9): load_px(), market_features(), OverlayTask, raw_features(), sharpe(), StatArbTask, stats_of(), TimingTask (+1 more)

### Community 8 - "breakout_rider.py"
Cohesion: 0.23
Nodes (7): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), walk_forward(), evaluate()

### Community 9 - "app_pages/speculation.py"
Cohesion: 0.12
Nodes (14): pct(), tile(), card(), pct(), stage_pill(), updown(), compact_frame(), _finite() (+6 more)

### Community 10 - "day_night.py"
Cohesion: 0.12
Nodes (16): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+8 more)

### Community 11 - "live.py"
Cohesion: 0.09
Nodes (21): br_backtest(), ld_backtest(), leader_dip_run(), tech_universe(), download_ohlcv(), last_years(), sp500_members(), sp500_table() (+13 more)

### Community 12 - "DataFrame"
Cohesion: 0.06
Nodes (31): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), insider_summary() (+23 more)

### Community 13 - "strategy_lab.py"
Cohesion: 0.15
Nodes (15): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), leader_dip_tab(), _load(), _pct_cols() (+7 more)

### Community 14 - "data.py"
Cohesion: 0.09
Nodes (18): html_to_text(), all_symbols(), _copy(), _edgar_filings(), market_status(), nasdaq100(), news(), _NYSECalendar (+10 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "streamlit"
Cohesion: 0.19
Nodes (12): guide(), stat(), catalysts_view(), _filings(), render(), _tone_line(), switch_strip(), checklist() (+4 more)

### Community 17 - "frontier.py"
Cohesion: 0.10
Nodes (16): bs_price(), fit_error(), implied_vol(), load(), merton_iv(), merton_price(), merton_skew(), network_layout() (+8 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.10
Nodes (20): evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix() (+12 more)

### Community 19 - "neat_core.py"
Cohesion: 0.11
Nodes (14): genome_from_json(), activate(), Config, Conn, Genome, Innovations, Neat, Node (+6 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "surface"
Cohesion: 0.16
Nodes (11): surface(), bs_price(), calibrate_surface(), resid(), safe(), implied_vol(), merton_iv(), merton_price() (+3 more)

### Community 22 - "factors.py"
Cohesion: 0.05
Nodes (40): prices(), backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame() (+32 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.10
Nodes (23): beat_model(), breadth(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table() (+15 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 25 - "growth_lab.py"
Cohesion: 0.13
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.11
Nodes (18): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+10 more)

### Community 27 - "sp500_ever"
Cohesion: 0.33
Nodes (4): factor_backtest(), _parse_spells(), sp500_ever(), sp500_spells()

### Community 28 - "nq_lab.py"
Cohesion: 0.12
Nodes (29): atr(), buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized() (+21 more)

### Community 29 - "Day"
Cohesion: 0.11
Nodes (19): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+11 more)

### Community 31 - "leader_dip.py"
Cohesion: 0.10
Nodes (22): _align(), backtest(), bundled_misses(), drop_recent_misses(), latest(), market_on(), _members(), missed_recently() (+14 more)

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "indicators.py"
Cohesion: 0.14
Nodes (20): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+12 more)

### Community 34 - "pandas"
Cohesion: 0.26
Nodes (13): pit_sector(), closes(), _earnings(), test_backtest_misses_only_remove_buys(), test_breakout_buy_ok_only_removes_trades(), test_drop_recent_misses_switches_off_only_those_signals(), test_earnings_frames_count_from_the_reaction_day(), test_missed_recently_uses_the_last_report_only() (+5 more)

### Community 35 - "assess"
Cohesion: 0.17
Nodes (12): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), _prices(), test_calm_portfolio_is_low(), test_crash_concentration_and_market_stress_is_high() (+4 more)

### Community 36 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

### Community 37 - "load_scan"
Cohesion: 0.16
Nodes (8): load_scan(), _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "Evolving trading strategies with NEAT, plus Merton jump-diffusion (Nov 2026)"
Cohesion: 0.12
Nodes (16): 1. The NEAT engine (`sharkfin/neat_core.py`), 2. What evolution found, 3. Merton jump-diffusion (`sharkfin/jump_lab.py`), A+ and B+: with VIX term structure and jump features as inputs, A. ETF timing from raw bars: no edge, B. Stock stat-arb from raw bars: no better than noise, C. Evolved exposure overlay for Dive Zone and Breakout Rider: failed, Code and files (+8 more)

### Community 39 - "drivers.py"
Cohesion: 0.21
Nodes (7): drivers(), earnings_record(), estimate_trend(), _naive(), _num(), _tone(), test_drivers_earnings_record_and_estimates()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "ttl_cache"
Cohesion: 0.12
Nodes (18): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), scan_data(), analyst_data() (+10 more)

### Community 43 - "walkforward.py"
Cohesion: 0.11
Nodes (12): _day(), Fold, folds(), grid(), _neighbours(), pick(), run(), sharpe() (+4 more)

### Community 44 - "main"
Cohesion: 0.10
Nodes (10): fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main(), rotation(), run_one() (+2 more)

### Community 47 - "test_core.py"
Cohesion: 0.10
Nodes (15): hurst_exponent(), _earn_table(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_earnings_factors_use_only_past_reports(), test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer(), test_features_have_no_lookahead() (+7 more)

### Community 48 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 49 - "ui.py"
Cohesion: 0.06
Nodes (32): overview(), Code, price_of(), clean_text(), account_box(), asset(), color(), day_color() (+24 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "edge_lab.py"
Cohesion: 0.10
Nodes (26): baseline_events(), _both(), breakout_confluences(), combos(), confluences(), earnings_frames(), load(), main() (+18 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "market_today.py"
Cohesion: 0.19
Nodes (7): breadth(), direction(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 63 - "voice.py"
Cohesion: 0.15
Nodes (12): voice_box(), brief_text(), last2(), _clean(), Command, _component(), mic(), _num() (+4 more)

### Community 64 - "test_voice_import.py"
Cohesion: 0.17
Nodes (4): test_page_renders(), tmp_cwd(), offline(), test_parse()

### Community 65 - "rsi"
Cohesion: 0.29
Nodes (5): rsi(), follow_up(), test_leader_dip_follow_up(), test_rsi_bounds_and_wilder(), test_rsi_matches_reference_formula()

### Community 66 - "numpy"
Cohesion: 0.08
Nodes (23): crash_odds(), return_density(), fit_merton(), nll(), merton_logpdf(), deflated_sharpe(), trailing_pct(), cut() (+15 more)

### Community 67 - "frontier_build.py"
Cohesion: 0.23
Nodes (7): evolve_all(), _genome(), genome_json(), original_s1(), original_s2(), publish(), tag_of()

### Community 69 - "json"
Cohesion: 0.25
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "test_voice_import.py"
Cohesion: 0.21
Nodes (7): claude_positions(), clean_rows(), _json_array(), ocr_text(), _to_float(), test_claude_reply_is_cleaned(), test_oversized_image_refused_before_decoding()

### Community 72 - "store.py"
Cohesion: 0.16
Nodes (16): auth_configured(), cloud_all(), _cloud_read(), _cloud_write(), hash_id(), _headers(), identity(), _local_path() (+8 more)

### Community 73 - "daily_cash"
Cohesion: 0.13
Nodes (9): daily_cash(), panel_adx(), panel_atr(), run(), stats(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled() (+1 more)

### Community 78 - "alerts.py"
Cohesion: 0.12
Nodes (19): compose(), holding_exits(), new_topic(), portfolio_threat(), run(), send(), signal_lines(), threat_line() (+11 more)

### Community 79 - "2. How the Speculation Radar finds themes, and whether that works"
Cohesion: 0.13
Nodes (14): 1. Improving Dive Zone, Breakout Rider and the ranking, 2. How the Speculation Radar finds themes, and whether that works, 3. Your idea: a "low bar" earnings beat in a beaten-down growth sector, As a portfolio, Dive Zone (as is: 20.5%/yr pick, Sharpe 1.20; 27.6%/yr grade, Sharpe 1.13), Edge lab: strategy research, round 2 (Nov 14 2026), Firing now (as of Nov 13 2026), How big is a breakthrough? (+6 more)

### Community 80 - "predictions.py"
Cohesion: 0.11
Nodes (14): run_forecast(), lab_walk_forward(), alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), history() (+6 more)

### Community 81 - "scanner.py"
Cohesion: 0.16
Nodes (15): breakout_tab(), get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+7 more)

### Community 82 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 83 - "regime"
Cohesion: 0.50
Nodes (3): _band(), regime(), test_regime_band_and_switch()

### Community 84 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 85 - "test_store.py"
Cohesion: 0.15
Nodes (13): Identity, load(), init_state(), FakeResp, test_accounts_are_separate(), test_cloud_outage_raises(), test_cloud_round_trip(), get() (+5 more)

### Community 86 - "Voice commands and screenshot import"
Cohesion: 0.50
Nodes (3): "Hey SharkFin" (sidebar, every page), Import from a screenshot (Portfolio), Voice commands and screenshot import

### Community 87 - "describe"
Cohesion: 0.50
Nodes (3): describe(), expr(), cb()

### Community 90 - "app_pages/playbook.py"
Cohesion: 0.25
Nodes (16): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+8 more)

### Community 92 - "ping"
Cohesion: 0.10
Nodes (19): concurrency, cancel-in-progress, group, SUPABASE_KEY, SUPABASE_URL, jobs, ping, name (+11 more)

### Community 93 - "tracked_positions"
Cohesion: 0.17
Nodes (10): live_state(), features_from_fits(), forward_record(), load_csv(), market_inputs(), summary(), topped_up_fits(), tracked_positions() (+2 more)

### Community 94 - "re"
Cohesion: 0.20
Nodes (6): headline_drivers(), parse_positions(), clean_text(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled(), test_parse_positions_one_line_and_two_line_layouts()

### Community 95 - "_load"
Cohesion: 0.27
Nodes (6): choices(), _load(), my_swing_rules(), set_swing_choice(), swing_choice(), swing_picker()

### Community 96 - "jump_features"
Cohesion: 0.38
Nodes (3): download(), jump_features(), rolling_fits()

### Community 97 - "_fetch_prices"
Cohesion: 0.40
Nodes (4): _fetch_ohlcv(), _fetch_prices(), fetch(), _naive()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 704 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `folds()` connect `walkforward.py` to `pandas`, `builder.py`, `breakout_rider.py`, `day_night.py`, `main`, `sharkfin/playbook.py`, `factors.py`, `leader_dip.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05401234567901234 - nodes in this community are weakly interconnected._
- **Why does `publish()` connect `frontier_build.py` to `numpy`, `pandas`, `neuro_lab.py`, `store.py`, `neat_core.py`, `growth_lab.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08156028368794327 - nodes in this community are weakly interconnected._
- **Why does `day_view()` connect `Day` to `pandas`, `numpy`, `nq_regimes.py`, `nq_gex_plays.py`, `nq_lab.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05258033106134372 - nodes in this community are weakly interconnected._