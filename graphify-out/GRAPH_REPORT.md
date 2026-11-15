# Graph Report - SharkFin  (2026-11-15)

## Corpus Check
- 84 files · ~148,762 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 66 file(s) not represented in the graph (top: .csv 64, (none) 1, .toml 1)
- WARNING: 66 of 165 files seen (40%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1958 nodes · 5084 edges · 91 communities (72 shown, 19 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 157 edges (avg confidence: 0.85)
- Token cost: 156,881 input · 0 output

## Graph Freshness
- Built from commit: `c78ef49f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- pathlib
- sec_lab.py
- builder.py
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- neuro_lab.py
- breakout_rider.py
- streamlit
- day_night.py
- live.py
- DataFrame
- app_pages/playbook.py
- data.py
- sharkfin/playbook.py
- sentiment.py
- sharkfin/__init__.py
- nq_regimes.py
- stock_ratings
- sharkfin/portfolio.py
- numpy
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
- history
- pandas
- risk.py
- Sign-in and private portfolios: setup
- load_scan
- Evolving trading strategies with NEAT, plus Merton jump-diffusion (Nov 2026)
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
- edge_lab.py
- targets.py
- market_today.py
- voice.py
- test_leaks.py
- strategy_lab.py
- test_nq_lab.py
- pickle
- json
- Phone alerts (free, through ntfy)
- test_voice_import.py
- test_store.py
- daily_cash
- filing_change
- sharkfin/speculation.py
- 2. How the Speculation Radar finds themes, and whether that works
- test_catalyst_lab.py
- ttl_cache
- levels.py
- universe
- sys
- fakes.py
- Voice commands and screenshot import
- opex_days
- walk_forward
- test_rss_feeds_download_with_a_timeout

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

## Communities (91 total, 19 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 2 - "sec_lab.py"
Cohesion: 0.08
Nodes (28): _intraday_ttl(), _Client, dilution_table(), _era(), full_text(), future_dates(), headline_class(), main() (+20 more)

### Community 3 - "builder.py"
Cohesion: 0.06
Nodes (46): breakout_tab(), get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+38 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 6 - "test_app.py"
Cohesion: 0.18
Nodes (20): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders() (+12 more)

### Community 7 - "neuro_lab.py"
Cohesion: 0.05
Nodes (25): activate(), Config, Conn, describe(), expr(), Genome, Innovations, Neat (+17 more)

### Community 8 - "breakout_rider.py"
Cohesion: 0.20
Nodes (8): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate()

### Community 9 - "streamlit"
Cohesion: 0.07
Nodes (31): stat(), tile(), catalysts_view(), _filings(), render(), _tone_line(), overview(), switch_strip() (+23 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 11 - "live.py"
Cohesion: 0.09
Nodes (22): br_backtest(), ld_backtest(), leader_dip_run(), todays_signals(), download_ohlcv(), last_years(), sp500_members(), tbill_yields() (+14 more)

### Community 12 - "DataFrame"
Cohesion: 0.13
Nodes (15): _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), insider_summary(), new_sentences(), revision_balance() (+7 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.14
Nodes (22): backtest_summary(), both_view(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_signals() (+14 more)

### Community 14 - "data.py"
Cohesion: 0.11
Nodes (14): html_to_text(), _copy(), _edgar_filings(), market_status(), news(), _NYSECalendar, _parse_date(), _rss() (+6 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.17
Nodes (13): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+5 more)

### Community 16 - "sentiment.py"
Cohesion: 0.13
Nodes (13): could_run_tab(), aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles() (+5 more)

### Community 17 - "sharkfin/__init__.py"
Cohesion: 0.12
Nodes (13): compose(), holding_exits(), new_topic(), signal_lines(), threat_line(), Threat, test_compose_signals_exits_and_threat(), test_quiet_day_sends_nothing() (+5 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.11
Nodes (19): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+11 more)

### Community 19 - "stock_ratings"
Cohesion: 0.24
Nodes (7): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), download_prices()

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "numpy"
Cohesion: 0.10
Nodes (18): bs_price(), calibrate_surface(), resid(), safe(), cumulant_functions(), fit_merton(), nll(), implied_vol() (+10 more)

### Community 22 - "factors.py"
Cohesion: 0.13
Nodes (18): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+10 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.09
Nodes (24): beat_model(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), first_in() (+16 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 25 - "growth_lab.py"
Cohesion: 0.14
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (16): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+8 more)

### Community 27 - "sp500_ever"
Cohesion: 0.25
Nodes (5): factor_backtest(), earnings_histories(), _parse_spells(), sp500_ever(), sp500_spells()

### Community 28 - "nq_lab.py"
Cohesion: 0.11
Nodes (31): atr(), buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized() (+23 more)

### Community 29 - "Day"
Cohesion: 0.13
Nodes (17): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+9 more)

### Community 31 - "leader_dip.py"
Cohesion: 0.05
Nodes (51): _market_gap(), build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema() (+43 more)

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "history"
Cohesion: 0.17
Nodes (7): lab_walk_forward(), portfolio_threat(), _fetch_ohlcv(), history(), market_history(), _naive(), risk_free_rate()

### Community 34 - "pandas"
Cohesion: 0.22
Nodes (14): pit_sector(), bundled_misses(), closes(), _earnings(), test_backtest_misses_only_remove_buys(), test_breakout_buy_ok_only_removes_trades(), test_drop_recent_misses_switches_off_only_those_signals(), test_earnings_frames_count_from_the_reaction_day() (+6 more)

### Community 35 - "risk.py"
Cohesion: 0.07
Nodes (31): compare(), positions(), run(), Strategy, annualized_return(), annualized_vol(), beta_alpha(), blume_adjusted_beta() (+23 more)

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

### Community 42 - "DataFrame"
Cohesion: 0.15
Nodes (9): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _session() (+1 more)

### Community 43 - "walkforward.py"
Cohesion: 0.11
Nodes (12): _day(), Fold, folds(), grid(), _neighbours(), pick(), run(), sharpe() (+4 more)

### Community 44 - "main"
Cohesion: 0.09
Nodes (11): fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main(), rotation(), run_one() (+3 more)

### Community 47 - "test_core.py"
Cohesion: 0.09
Nodes (20): fair_value_summary(), forward_growth(), _earn_table(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports() (+12 more)

### Community 49 - "ui.py"
Cohesion: 0.06
Nodes (31): Code, price_of(), account_box(), asset(), color(), day_color(), esc(), fetch_all() (+23 more)

### Community 50 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

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
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 63 - "voice.py"
Cohesion: 0.14
Nodes (13): clean_text(), voice_box(), brief_text(), last2(), _clean(), Command, _component(), mic() (+5 more)

### Community 64 - "test_leaks.py"
Cohesion: 0.18
Nodes (9): offline(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_factor_replay_keeps_a_holding_that_stops_trading_in_the_average(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled(), tmp_cwd() (+1 more)

### Community 65 - "strategy_lab.py"
Cohesion: 0.22
Nodes (11): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), _load(), _pct_cols(), _remove() (+3 more)

### Community 66 - "test_nq_lab.py"
Cohesion: 0.18
Nodes (12): cut(), _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only(), test_gex_plays_decide_from_earlier_bars_only() (+4 more)

### Community 67 - "pickle"
Cohesion: 0.16
Nodes (14): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), _fetch_prices(), fetch(), _panel_file() (+6 more)

### Community 69 - "json"
Cohesion: 0.25
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "test_voice_import.py"
Cohesion: 0.13
Nodes (9): claude_positions(), clean_rows(), _json_array(), ocr_text(), parse_positions(), _to_float(), test_claude_reply_is_cleaned(), test_oversized_image_refused_before_decoding() (+1 more)

### Community 72 - "test_store.py"
Cohesion: 0.09
Nodes (31): run(), send(), valid_topic(), auth_configured(), cloud_all(), _cloud_read(), _cloud_write(), hash_id() (+23 more)

### Community 73 - "daily_cash"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 77 - "filing_change"
Cohesion: 0.38
Nodes (5): filing_change(), risk_factors_section(), text_similarity(), sec_document_text(), test_filing_change_finds_new_risk_language()

### Community 78 - "sharkfin/speculation.py"
Cohesion: 0.17
Nodes (8): Play, radar(), stage(), stage_history(), stats(), Theme, test_broken_stage(), test_speculation_stages_follow_the_price_action()

### Community 79 - "2. How the Speculation Radar finds themes, and whether that works"
Cohesion: 0.13
Nodes (14): 1. Improving Dive Zone, Breakout Rider and the ranking, 2. How the Speculation Radar finds themes, and whether that works, 3. Your idea: a "low bar" earnings beat in a beaten-down growth sector, As a portfolio, Dive Zone (as is: 20.5%/yr pick, Sharpe 1.20; 27.6%/yr grade, Sharpe 1.13), Edge lab: strategy research, round 2 (Nov 14 2026), Firing now (as of Nov 13 2026), How big is a breakthrough? (+6 more)

### Community 80 - "test_catalyst_lab.py"
Cohesion: 0.23
Nodes (9): breadth(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_earnings_frame_reports_five_year_average_eps(), test_falling_knife_gets_no_reversal_credit(), test_kalshi_uses_the_next_meeting_and_market_codes() (+1 more)

### Community 81 - "ttl_cache"
Cohesion: 0.18
Nodes (12): scan_data(), analyst_data(), financials(), industry_members(), info(), infos(), peers_for(), quarterly_financials() (+4 more)

### Community 82 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 83 - "universe"
Cohesion: 0.22
Nodes (7): prices(), all_symbols(), nasdaq100(), universe(), download(), get(), all_tickers()

### Community 84 - "sys"
Cohesion: 0.38
Nodes (3): make_ohlcv(), ohlcv(), price_panel()

### Community 85 - "fakes.py"
Cohesion: 0.15
Nodes (17): _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info(), install() (+9 more)

### Community 86 - "Voice commands and screenshot import"
Cohesion: 0.50
Nodes (3): "Hey SharkFin" (sidebar, every page), Import from a screenshot (Portfolio), Voice commands and screenshot import

### Community 87 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 88 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 671 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `composite_scores()` connect `factors.py` to `test_catalyst_lab.py`, `pandas`, `builder.py`, `numpy`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `_folds_beating_cash()` connect `main` to `pandas`, `nq_regimes.py`, `numpy`, `nq_gex_plays.py`, `nq_lab.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07673469387755102 - nodes in this community are weakly interconnected._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055855855855855854 - nodes in this community are weakly interconnected._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._