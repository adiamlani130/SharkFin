# Graph Report - SharkFin  (2026-11-14)

## Corpus Check
- 78 files · ~135,622 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 65 file(s) not represented in the graph (top: .csv 63, (none) 1, .toml 1)
- WARNING: 65 of 156 files seen (42%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1794 nodes · 4737 edges · 90 communities (68 shown, 22 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 147 edges (avg confidence: 0.85)
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
- leader_dip.py
- breakout_rider.py
- ui.py
- day_night.py
- ttl_cache
- DataFrame
- app_pages/playbook.py
- data.py
- walkforward.py
- sentiment.py
- sharkfin/speculation.py
- nq_regimes.py
- stock_ratings
- sharkfin/portfolio.py
- edge_lab.py
- factors.py
- catalyst_lab.py
- steps
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- leader_dip.py
- run
- ttl_cache
- store.py
- assess
- Sign-in and private portfolios: setup
- load_scan
- risk.py
- drivers.py
- MCP Servers
- Current Logo
- DataFrame
- test_rss_feeds_download_with_a_timeout
- Series
- Offline Test Design
- test_core.py
- run_command
- ratings.py
- Results
- growth_lab.py
- targets.py
- market_today.py
- voice.py
- test_catalyst_lab.py
- strategy_lab.py
- composite_scores
- pickle
- json
- Phone alerts (free, through ntfy)
- test_voice_import.py
- sp500_members
- swing_engine.py
- catalysts.py
- init_state
- _load
- download
- run_one
- search
- sys
- backtest_price_composite
- Voice commands and screenshot import
- risk_contributions
- follow_up

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `build_tab()` - 25 edges
5. `catalysts_view()` - 25 edges
6. `main()` - 24 edges
7. `quality_metrics()` - 22 edges
8. `_sw()` - 22 edges
9. `download_prices()` - 20 edges
10. `history()` - 19 edges

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

## Communities (90 total, 22 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (33): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+25 more)

### Community 1 - "sharkfin/__init__.py"
Cohesion: 0.09
Nodes (5): stat(), tile(), pct(), stage_pill(), reload_changed_sharkfin()

### Community 2 - "sec_lab.py"
Cohesion: 0.08
Nodes (28): _intraday_ttl(), _Client, dilution_table(), _era(), full_text(), future_dates(), headline_class(), main() (+20 more)

### Community 3 - "builder.py"
Cohesion: 0.07
Nodes (33): C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value(), Indicator (+25 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.09
Nodes (37): _base_info(), download_ohlcv(), download_prices(), financials(), history(), info(), install(), news() (+29 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.06
Nodes (34): compare(), positions(), run(), Strategy, build_features(), adx(), atr(), bollinger() (+26 more)

### Community 8 - "breakout_rider.py"
Cohesion: 0.20
Nodes (8): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate()

### Community 9 - "ui.py"
Cohesion: 0.09
Nodes (26): catalysts_view(), _filings(), switch_strip(), card(), clean_text(), asset(), checklist(), compact_frame() (+18 more)

### Community 10 - "day_night.py"
Cohesion: 0.08
Nodes (25): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+17 more)

### Community 11 - "ttl_cache"
Cohesion: 0.10
Nodes (18): br_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), last_years(), yahoo_period(), sector_returns(), breakout_today() (+10 more)

### Community 12 - "DataFrame"
Cohesion: 0.13
Nodes (14): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), insider_summary(), revision_balance() (+6 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.16
Nodes (23): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+15 more)

### Community 14 - "data.py"
Cohesion: 0.13
Nodes (10): _copy(), _edgar_filings(), market_status(), news(), _NYSECalendar, _parse_date(), _rss(), sec_cik() (+2 more)

### Community 15 - "walkforward.py"
Cohesion: 0.05
Nodes (38): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+30 more)

### Community 16 - "sentiment.py"
Cohesion: 0.15
Nodes (12): render(), _tone_line(), aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label() (+4 more)

### Community 17 - "sharkfin/speculation.py"
Cohesion: 0.17
Nodes (8): Play, radar(), stage(), stage_history(), stats(), Theme, test_broken_stage(), test_speculation_stages_follow_the_price_action()

### Community 18 - "nq_regimes.py"
Cohesion: 0.10
Nodes (20): evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix() (+12 more)

### Community 19 - "stock_ratings"
Cohesion: 0.12
Nodes (14): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), scan_data(), analyst_data() (+6 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.18
Nodes (11): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+3 more)

### Community 21 - "edge_lab.py"
Cohesion: 0.10
Nodes (27): baseline_events(), _both(), breakout_confluences(), combos(), confluences(), get(), earnings_frames(), load() (+19 more)

### Community 22 - "factors.py"
Cohesion: 0.18
Nodes (11): earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical(), sector_neutral_z(), winsorize() (+3 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.10
Nodes (21): beat_model(), breadth_setups(), entry_delay_table(), fda_study(), fda_table(), first_in(), _forward(), _hold_for() (+13 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.11
Nodes (18): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+10 more)

### Community 27 - "scanner.py"
Cohesion: 0.18
Nodes (14): breakout_tab(), get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+6 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.11
Nodes (19): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+11 more)

### Community 31 - "leader_dip.py"
Cohesion: 0.11
Nodes (22): _align(), backtest(), _band(), latest(), market_on(), _members(), percentile_against(), plus_frames() (+14 more)

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "ttl_cache"
Cohesion: 0.12
Nodes (16): run_forecast(), lab_walk_forward(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials(), history(), industry_members() (+8 more)

### Community 34 - "store.py"
Cohesion: 0.06
Nodes (46): compose(), holding_exits(), new_topic(), portfolio_threat(), run(), send(), signal_lines(), threat_line() (+38 more)

### Community 35 - "assess"
Cohesion: 0.17
Nodes (12): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), _prices(), test_calm_portfolio_is_low(), test_crash_concentration_and_market_stress_is_high() (+4 more)

### Community 36 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

### Community 37 - "load_scan"
Cohesion: 0.20
Nodes (7): _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "risk.py"
Cohesion: 0.21
Nodes (13): annualized_return(), annualized_vol(), beta_alpha(), calmar_ratio(), cornish_fisher_var(), drawdown_series(), historical_cvar(), historical_var() (+5 more)

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

### Community 44 - "Series"
Cohesion: 0.09
Nodes (13): atr(), deflated_sharpe(), fetch(), _folds_beating_cash(), intraday_frames(), known(), load(), main() (+5 more)

### Community 47 - "test_core.py"
Cohesion: 0.11
Nodes (14): _earn_table(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer(), test_features_have_no_lookahead(), test_fmt_money_negative_sign_before_dollar() (+6 more)

### Community 49 - "run_command"
Cohesion: 0.13
Nodes (13): Code, price_of(), account_box(), guest_notice(), init_state(), _resolve(), run_command(), _save() (+5 more)

### Community 50 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "growth_lab.py"
Cohesion: 0.14
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 60 - "targets.py"
Cohesion: 0.21
Nodes (6): updown(), blume_adjusted_beta(), entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "market_today.py"
Cohesion: 0.19
Nodes (7): breadth(), direction(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 63 - "voice.py"
Cohesion: 0.15
Nodes (12): voice_box(), brief_text(), last2(), _clean(), Command, _component(), mic(), _num() (+4 more)

### Community 64 - "test_catalyst_lab.py"
Cohesion: 0.16
Nodes (16): breadth(), earnings_events(), _earnings_table(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_first_in_takes_one_entry_per_episode() (+8 more)

### Community 65 - "strategy_lab.py"
Cohesion: 0.24
Nodes (11): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), _load(), _pct_cols(), _remove() (+3 more)

### Community 66 - "composite_scores"
Cohesion: 0.36
Nodes (6): composite_scores(), price_factor_frame(), test_falling_knife_gets_no_reversal_credit(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_could_run_screen(), test_factor_composite_ranks_planted_winners()

### Community 67 - "pickle"
Cohesion: 0.12
Nodes (16): load_scan(), _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), info(), _panel_file() (+8 more)

### Community 69 - "json"
Cohesion: 0.25
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "test_voice_import.py"
Cohesion: 0.12
Nodes (9): claude_positions(), clean_rows(), _json_array(), ocr_text(), parse_positions(), _to_float(), test_claude_reply_is_cleaned(), test_oversized_image_refused_before_decoding() (+1 more)

### Community 72 - "sp500_members"
Cohesion: 0.29
Nodes (4): factor_backtest(), sp500_ever(), sp500_members(), test_members_only_trade_while_in_the_index()

### Community 73 - "swing_engine.py"
Cohesion: 0.19
Nodes (4): panel_adx(), panel_atr(), run(), stats()

### Community 77 - "catalysts.py"
Cohesion: 0.20
Nodes (9): filing_change(), html_to_text(), new_sentences(), risk_factors_section(), _sentences(), text_similarity(), headline_drivers(), clean_text() (+1 more)

### Community 78 - "init_state"
Cohesion: 0.17
Nodes (8): overview(), color(), day_color(), mode(), setup(), _template(), theme_css(), _waves()

### Community 79 - "_load"
Cohesion: 0.31
Nodes (5): choices(), _load(), my_swing_rules(), swing_choice(), swing_picker()

### Community 81 - "download"
Cohesion: 0.33
Nodes (4): prices(), nasdaq100(), download(), all_tickers()

### Community 82 - "run_one"
Cohesion: 0.33
Nodes (3): first_usable(), run_one(), Strategy

### Community 83 - "search"
Cohesion: 0.40
Nodes (3): all_symbols(), search(), symbol_picker()

### Community 84 - "sys"
Cohesion: 0.38
Nodes (3): make_ohlcv(), ohlcv(), price_panel()

### Community 85 - "backtest_price_composite"
Cohesion: 0.17
Nodes (8): backtest_price_composite(), walk_forward(), evaluate(), weight_presets(), earnings_history(), test_factor_backtest_positive_ic(), test_factor_replay_with_earnings(), test_factor_replay_keeps_a_holding_that_stops_trading_in_the_average()

### Community 86 - "Voice commands and screenshot import"
Cohesion: 0.50
Nodes (3): "Hey SharkFin" (sidebar, every page), Import from a screenshot (Portfolio), Voice commands and screenshot import

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 608 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `run`, `test_catalyst_lab.py`, `builder.py`, `breakout_rider.py`, `day_night.py`, `run_one`, `backtest_price_composite`, `leader_dip.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05401234567901234 - nodes in this community are weakly interconnected._
- **Why does `sp500_members()` connect `sp500_members` to `test_catalyst_lab.py`, `test_app.py`, `DataFrame`, `ttl_cache`, `data.py`, `Results`, `edge_lab.py`, `catalyst_lab.py`, `growth_lab.py`, `targets.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `sharkfin/__init__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09057971014492754 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `walkforward.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07673469387755102 - nodes in this community are weakly interconnected._