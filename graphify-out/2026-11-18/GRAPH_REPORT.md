# Graph Report - SharkFin  (2026-11-16)

## Corpus Check
- 90 files · ~178,102 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 68 file(s) not represented in the graph (top: .csv 66, (none) 1, .toml 1)
- WARNING: 68 of 173 files seen (39%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 2024 nodes · 5305 edges · 92 communities (72 shown, 20 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 161 edges (avg confidence: 0.85)
- Token cost: 156,881 input · 0 output

## Graph Freshness
- Built from commit: `24e5d7a2`
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
- neuro_lab.py
- breakout_rider.py
- home.py
- day_night.py
- live.py
- DataFrame
- app_pages/playbook.py
- data.py
- sharkfin/playbook.py
- sentiment.py
- frontier.py
- nq_regimes.py
- neat_core.py
- sharkfin/portfolio.py
- numpy
- factors.py
- catalyst_lab.py
- steps
- growth_lab.py
- nq_gex_plays.py
- pandas
- nq_lab.py
- Day
- leader_dip.py
- run
- indicators.py
- pandas
- assess
- Sign-in and private portfolios: setup
- prefetch
- Evolving trading strategies with NEAT, plus Merton jump-diffusion (Nov 2026)
- drivers.py
- MCP Servers
- Current Logo
- DataFrame
- walkforward.py
- main
- Offline Test Design
- test_core.py
- backtest.py
- ui.py
- frontier_lab.py
- Results
- edge_lab.py
- targets.py
- market_today.py
- voice.py
- test_voice_import.py
- rsi
- test_nq_lab.py
- frontier_build.py
- json
- Phone alerts (free, through ntfy)
- test_voice_import.py
- test_store.py
- daily_cash
- kalshi_daily
- sharkfin/speculation.py
- 2. How the Speculation Radar finds themes, and whether that works
- test_catalyst_lab.py
- scanner.py
- levels.py
- regime
- sys
- fakes.py
- Voice commands and screenshot import
- describe
- carry_forward
- first_in

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `main()` - 25 edges
5. `build_tab()` - 25 edges
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

## Communities (92 total, 20 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (34): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+26 more)

### Community 1 - "sharkfin/__init__.py"
Cohesion: 0.10
Nodes (7): reload_changed_sharkfin(), _cached_panel(), _panel_file(), _panel_load(), _panel_save(), _patched(), test_price_panel_is_kept_on_disk_and_only_topped_up()

### Community 2 - "sec_lab.py"
Cohesion: 0.08
Nodes (27): _intraday_ttl(), _Client, dilution_table(), _era(), full_text(), future_dates(), headline_class(), main() (+19 more)

### Community 3 - "builder.py"
Cohesion: 0.05
Nodes (48): market_beta(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value() (+40 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.20
Nodes (19): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_playbook_every_view_and_scan() (+11 more)

### Community 7 - "neuro_lab.py"
Cohesion: 0.11
Nodes (11): evolve(), _fit(), load_px(), market_features(), OverlayTask, raw_features(), sharpe(), StatArbTask (+3 more)

### Community 8 - "breakout_rider.py"
Cohesion: 0.18
Nodes (10): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+2 more)

### Community 9 - "home.py"
Cohesion: 0.14
Nodes (9): pct(), stat(), tile(), _filings(), pct(), stage_pill(), updown(), esc() (+1 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 11 - "live.py"
Cohesion: 0.13
Nodes (12): todays_signals(), breakout_today(), day_night_today(), dive_zone_latest(), leader_dip_today(), market_inputs(), sector_ret3(), sp500_ohlcv() (+4 more)

### Community 12 - "DataFrame"
Cohesion: 0.10
Nodes (19): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), insider_summary() (+11 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.10
Nodes (35): backtest_summary(), both_view(), br_backtest(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table() (+27 more)

### Community 14 - "data.py"
Cohesion: 0.04
Nodes (60): catalysts_view(), run_forecast(), index_panel(), peer_table(), sector_etf_prices(), zone_study(), get_universe(), lab_walk_forward() (+52 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "sentiment.py"
Cohesion: 0.11
Nodes (19): render(), _tone_line(), aggregate_sentiment(), BM25, clean_text(), dedupe(), hours_old(), is_noise() (+11 more)

### Community 17 - "frontier.py"
Cohesion: 0.08
Nodes (24): live_state(), bs_price(), crash_odds(), features_from_fits(), fit_error(), forward_record(), implied_vol(), load() (+16 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.10
Nodes (20): evaluate(), day_view(), _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix() (+12 more)

### Community 19 - "neat_core.py"
Cohesion: 0.12
Nodes (12): genome_from_json(), activate(), Config, Conn, Genome, Innovations, Neat, Node (+4 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "numpy"
Cohesion: 0.09
Nodes (21): surface(), merton_skew(), bs_price(), calibrate_surface(), resid(), safe(), cumulant_functions(), fit_merton() (+13 more)

### Community 22 - "factors.py"
Cohesion: 0.06
Nodes (30): stock_ratings(), backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame() (+22 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.16
Nodes (11): beat_model(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), load(), main() (+3 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 25 - "growth_lab.py"
Cohesion: 0.14
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.11
Nodes (16): bs(), _call_wall_fade(), _days(), fly_trades(), value(), _neg_gamma_breakout(), opex_days(), _opex_fly() (+8 more)

### Community 27 - "pandas"
Cohesion: 0.11
Nodes (17): ld_backtest(), leader_dip_run(), last_years(), _parse_spells(), sp500_ever(), sp500_members(), sp500_spells(), yahoo_period() (+9 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.11
Nodes (31): atr(), buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized() (+23 more)

### Community 29 - "Day"
Cohesion: 0.17
Nodes (15): bollinger_fade(), bracket(), Day, day_long_only(), ema_cross_5m(), _ema_rows(), _filter(), gap_fade() (+7 more)

### Community 31 - "leader_dip.py"
Cohesion: 0.12
Nodes (18): _align(), backtest(), drop_recent_misses(), latest(), market_on(), _members(), missed_recently(), misses_from_histories() (+10 more)

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "indicators.py"
Cohesion: 0.14
Nodes (20): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+12 more)

### Community 34 - "pandas"
Cohesion: 0.20
Nodes (11): pit_sector(), bundled_misses(), closes(), _earnings(), test_backtest_misses_only_remove_buys(), test_breakout_buy_ok_only_removes_trades(), test_drop_recent_misses_switches_off_only_those_signals(), test_missed_recently_uses_the_last_report_only() (+3 more)

### Community 35 - "assess"
Cohesion: 0.17
Nodes (12): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), _prices(), test_calm_portfolio_is_low(), test_crash_concentration_and_market_stress_is_high() (+4 more)

### Community 36 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

### Community 37 - "prefetch"
Cohesion: 0.20
Nodes (8): _copy(), _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), fetch_all()

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

### Community 42 - "DataFrame"
Cohesion: 0.21
Nodes (9): breadth_setups(), _forward(), _hold_for(), _hold_until(), kalshi_tests(), _perf(), _portfolio(), stage_panel() (+1 more)

### Community 43 - "walkforward.py"
Cohesion: 0.11
Nodes (13): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 44 - "main"
Cohesion: 0.08
Nodes (15): catalogue(), main(), move_vs_implied(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames() (+7 more)

### Community 47 - "test_core.py"
Cohesion: 0.07
Nodes (21): hurst_exponent(), _earn_table(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_factor_backtest_positive_ic() (+13 more)

### Community 48 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 49 - "ui.py"
Cohesion: 0.05
Nodes (37): Code, price_of(), choices(), account_box(), alerts_box(), asset(), color(), compact_frame() (+29 more)

### Community 50 - "frontier_lab.py"
Cohesion: 0.22
Nodes (4): guide(), traces(), pill(), threat_banner()

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "edge_lab.py"
Cohesion: 0.11
Nodes (26): baseline_events(), _both(), breakout_confluences(), combos(), confluences(), earnings_frames(), main(), publish_dive_zone() (+18 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "market_today.py"
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 63 - "voice.py"
Cohesion: 0.15
Nodes (12): voice_box(), brief_text(), last2(), _clean(), Command, _component(), mic(), _num() (+4 more)

### Community 64 - "test_voice_import.py"
Cohesion: 0.17
Nodes (4): test_page_renders(), tmp_cwd(), offline(), test_parse()

### Community 65 - "rsi"
Cohesion: 0.29
Nodes (5): rsi(), follow_up(), test_leader_dip_follow_up(), test_rsi_bounds_and_wilder(), test_rsi_matches_reference_formula()

### Community 66 - "test_nq_lab.py"
Cohesion: 0.18
Nodes (12): cut(), _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only(), test_gex_plays_decide_from_earlier_bars_only() (+4 more)

### Community 67 - "frontier_build.py"
Cohesion: 0.21
Nodes (8): download(), evolve_all(), _genome(), genome_json(), original_s1(), original_s2(), publish(), tag_of()

### Community 69 - "json"
Cohesion: 0.25
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "test_voice_import.py"
Cohesion: 0.13
Nodes (12): claude_positions(), clean_rows(), _json_array(), ocr_text(), parse_positions(), _to_float(), clean_text(), test_negative_shifts_are_only_trade_outcomes() (+4 more)

### Community 72 - "test_store.py"
Cohesion: 0.06
Nodes (43): compose(), holding_exits(), new_topic(), run(), send(), signal_lines(), threat_line(), valid_topic() (+35 more)

### Community 73 - "daily_cash"
Cohesion: 0.12
Nodes (11): daily_cash(), panel_adx(), panel_atr(), run(), stats(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled() (+3 more)

### Community 78 - "sharkfin/speculation.py"
Cohesion: 0.11
Nodes (11): prices(), theme_turn(), all_tickers(), Play, radar(), stage(), stage_history(), stats() (+3 more)

### Community 79 - "2. How the Speculation Radar finds themes, and whether that works"
Cohesion: 0.13
Nodes (14): 1. Improving Dive Zone, Breakout Rider and the ranking, 2. How the Speculation Radar finds themes, and whether that works, 3. Your idea: a "low bar" earnings beat in a beaten-down growth sector, As a portfolio, Dive Zone (as is: 20.5%/yr pick, Sharpe 1.20; 27.6%/yr grade, Sharpe 1.13), Edge lab: strategy research, round 2 (Nov 14 2026), Firing now (as of Nov 13 2026), How big is a breakthrough? (+6 more)

### Community 80 - "test_catalyst_lab.py"
Cohesion: 0.29
Nodes (8): breadth(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_earnings_frame_reports_five_year_average_eps(), test_falling_knife_gets_no_reversal_credit(), test_stage_panel_matches_the_radar()

### Community 81 - "scanner.py"
Cohesion: 0.11
Nodes (21): breakout_tab(), card(), factor_backtest(), leader_dip_tab(), load_scan(), log_prices(), log_signals(), market_close() (+13 more)

### Community 82 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 83 - "regime"
Cohesion: 0.50
Nodes (3): _band(), regime(), test_regime_band_and_switch()

### Community 84 - "sys"
Cohesion: 0.38
Nodes (3): make_ohlcv(), ohlcv(), price_panel()

### Community 85 - "fakes.py"
Cohesion: 0.14
Nodes (18): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+10 more)

### Community 86 - "Voice commands and screenshot import"
Cohesion: 0.50
Nodes (3): "Hey SharkFin" (sidebar, every page), Import from a screenshot (Portfolio), Voice commands and screenshot import

### Community 87 - "describe"
Cohesion: 0.50
Nodes (3): describe(), expr(), cb()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 692 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `sp500_members()` connect `pandas` to `neuro_lab.py`, `daily_cash`, `app_pages/playbook.py`, `data.py`, `scanner.py`, `Results`, `catalyst_lab.py`, `growth_lab.py`, `Day`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05359831376091539 - nodes in this community are weakly interconnected._
- **Why does `history()` connect `data.py` to `live.py`, `pandas`, `voice.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `sharkfin/__init__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10153846153846154 - nodes in this community are weakly interconnected._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08156028368794327 - nodes in this community are weakly interconnected._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05290490100616683 - nodes in this community are weakly interconnected._