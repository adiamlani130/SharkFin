# Graph Report - SharkFin  (2026-11-15)

## Corpus Check
- 87 files · ~144,670 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 61 file(s) not represented in the graph (top: .csv 59, (none) 1, .toml 1)
- WARNING: 61 of 161 files seen (38%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1910 nodes · 4977 edges · 107 communities (80 shown, 27 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 156 edges (avg confidence: 0.85)
- Token cost: 156,881 input · 0 output

## Graph Freshness
- Built from commit: `444ee681`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- swing_options_lab.py
- sec_lab.py
- builder.py
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- indicators.py
- pickle
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
- store.py
- levels.py
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
- predictions.py
- time
- json
- Phone alerts (free, through ntfy)
- test_voice_import.py
- Options for swing trades: strong plays, hedges and news (Nov 2026)
- test_leaks.py
- _cached_panel
- NQ strategy lab: results (October 2026)
- _load
- bs.py
- catalysts_view
- catalyst_lab.py
- Sign-in and private portfolios: setup
- market_today.py
- Voice commands and screenshot import
- The Sharpe-2 hunt: stock strategies and options strategies (Nov 2026)
- options_earnings.py
- walk_forward
- regime
- sharkfin/__init__.py
- backtest.py
- pathlib
- opex_days
- could_run
- pdufa_dates
- _Client
- carry_forward
- hurst_exponent
- risk_contributions
- test_headline_class
- follow_up
- earnings_history
- test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer
- full_text

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
- `Code` --references--> `save_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `save_list()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `account_box()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (107 total, 27 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (28): net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices(), justified_pb_value() (+20 more)

### Community 1 - "swing_options_lab.py"
Cohesion: 0.16
Nodes (12): breakout_calls(), classify(), folder_daily(), hedge_study(), hold_return(), load(), main(), pair_signals() (+4 more)

### Community 2 - "sec_lab.py"
Cohesion: 0.15
Nodes (17): dilution_table(), _era(), main(), pdufa_events(), pdufa_study(), pdufa_table(), pop_study(), Prices (+9 more)

### Community 3 - "builder.py"
Cohesion: 0.08
Nodes (30): C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value(), Indicator (+22 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.18
Nodes (20): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders() (+12 more)

### Community 7 - "indicators.py"
Cohesion: 0.14
Nodes (21): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+13 more)

### Community 8 - "pickle"
Cohesion: 0.21
Nodes (9): _earnings_fresh(), _earnings_from_disk(), earnings_histories(), earnings_history(), _earnings_to_disk(), _panel_load(), _panel_save(), f() (+1 more)

### Community 9 - "ui.py"
Cohesion: 0.07
Nodes (32): render(), _tone_line(), overview(), switch_strip(), price_of(), clean_text(), alerts_box(), asset() (+24 more)

### Community 10 - "day_night.py"
Cohesion: 0.06
Nodes (41): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+33 more)

### Community 11 - "ttl_cache"
Cohesion: 0.10
Nodes (20): get_universe(), todays_signals(), all_symbols(), download_ohlcv(), nasdaq100(), search(), sp500_table(), ttl_cache() (+12 more)

### Community 12 - "DataFrame"
Cohesion: 0.11
Nodes (17): _col(), core_long_checklist(), core_long_screen(), earnings_beat_flag(), earnings_summary(), filing_change(), insider_summary(), new_sentences() (+9 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.12
Nodes (28): backtest_summary(), both_view(), br_backtest(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table() (+20 more)

### Community 14 - "data.py"
Cohesion: 0.09
Nodes (20): html_to_text(), _copy(), _edgar_filings(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials(), industry_members() (+12 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 16 - "sentiment.py"
Cohesion: 0.14
Nodes (12): aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles(), score_text() (+4 more)

### Community 17 - "sharkfin/speculation.py"
Cohesion: 0.11
Nodes (11): prices(), theme_turn(), all_tickers(), Play, radar(), stage(), stage_history(), stats() (+3 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.09
Nodes (22): evaluate(), day_view(), evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names() (+14 more)

### Community 19 - "stock_ratings"
Cohesion: 0.12
Nodes (13): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), load_scan(), portfolio_threat() (+5 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.18
Nodes (11): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+3 more)

### Community 21 - "leader_dip.py"
Cohesion: 0.13
Nodes (19): _align(), backtest(), latest(), market_on(), _members(), percentile_against(), plus_frames(), quality_points() (+11 more)

### Community 22 - "factors.py"
Cohesion: 0.14
Nodes (17): scan(), scan_data(), backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife() (+9 more)

### Community 23 - "DataFrame"
Cohesion: 0.18
Nodes (8): intraday_bars(), latest_trade(), _parse_spells(), sec_filings(), _session(), sp500_spells(), _yahoo_filings(), day_night_today()

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.14
Nodes (13): bs(), _call_wall_fade(), _days(), fly_trades(), value(), move_vs_implied(), _neg_gamma_breakout(), _opex_fly() (+5 more)

### Community 27 - "scanner.py"
Cohesion: 0.17
Nodes (15): breakout_tab(), card(), factor_backtest(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab() (+7 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.11
Nodes (29): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+21 more)

### Community 29 - "Day"
Cohesion: 0.16
Nodes (16): bollinger_fade(), bracket(), Day, day_long_only(), ema_cross_5m(), _ema_rows(), _filter(), first_true() (+8 more)

### Community 31 - "sharpe_lab.py"
Cohesion: 0.11
Nodes (22): both(), cost_of(), fear_day_long(), _hold(), ibs_basket(), inverse_vol_blend(), load(), main() (+14 more)

### Community 32 - "run"
Cohesion: 0.20
Nodes (9): Does GEX shrink the day? Yes, Fear day long, checked, Part 2: GEX and VIX as a daily playbook, Part 3: three GEX setups (call-wall fade, negative-gamma breakout, OpEx fly/condor), Results (out of sample), Results (unseen test years; swing May 2015 to Oct 2026, day trades Apr 2019 to Oct 2026), What each level meant (whole-sample description, not a tested trade), What was real and what was approximated (+1 more)

### Community 33 - "store.py"
Cohesion: 0.06
Nodes (44): compose(), holding_exits(), new_topic(), run(), send(), signal_lines(), threat_line(), valid_topic() (+36 more)

### Community 34 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 35 - "assess"
Cohesion: 0.17
Nodes (12): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), _prices(), test_calm_portfolio_is_low(), test_crash_concentration_and_market_stress_is_high() (+4 more)

### Community 36 - "options_lab.py"
Cohesion: 0.17
Nodes (15): build_days(), context(), day_snapshot(), grade(), iron_condor(), iron_fly(), leg_price(), long_call() (+7 more)

### Community 37 - "load_scan"
Cohesion: 0.20
Nodes (7): _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

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

### Community 42 - "risk.py"
Cohesion: 0.19
Nodes (14): annualized_return(), annualized_vol(), beta_alpha(), blume_adjusted_beta(), calmar_ratio(), cornish_fisher_var(), drawdown_series(), historical_cvar() (+6 more)

### Community 44 - "Series"
Cohesion: 0.10
Nodes (14): catalogue(), main(), atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames() (+6 more)

### Community 47 - "test_core.py"
Cohesion: 0.08
Nodes (20): fair_value_summary(), forward_growth(), _earn_table(), _ohlc(), _one_day_matrix(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_builder_fills_next_open_and_stops() (+12 more)

### Community 49 - "walkforward.py"
Cohesion: 0.12
Nodes (12): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+4 more)

### Community 50 - "ratings.py"
Cohesion: 0.16
Nodes (10): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+2 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "growth_lab.py"
Cohesion: 0.08
Nodes (28): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+20 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 62 - "math"
Cohesion: 0.19
Nodes (9): bs_delta(), calibrate(), check_fit(), fit_real_smiles(), main(), model_iv(), run(), stats() (+1 more)

### Community 63 - "voice.py"
Cohesion: 0.11
Nodes (16): headline_drivers(), clean_text(), voice_box(), brief_text(), last2(), _clean(), Command, _component() (+8 more)

### Community 64 - "test_catalyst_lab.py"
Cohesion: 0.17
Nodes (13): breadth(), kalshi_daily(), occ(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_earnings_frame_reports_five_year_average_eps() (+5 more)

### Community 65 - "strategy_lab.py"
Cohesion: 0.20
Nodes (11): _add(), build_tab(), _cat(), catalyst_tab(), condition_rows(), _load(), _pct_cols(), _remove() (+3 more)

### Community 66 - "predictions.py"
Cohesion: 0.21
Nodes (6): run_forecast(), lab_walk_forward(), alpaca_daily(), history(), market_history(), risk_free_rate()

### Community 67 - "time"
Cohesion: 0.18
Nodes (7): alpaca_bars(), chunk(), _alpaca_get(), alpaca_keys(), _get(), option_bars(), stock_bars()

### Community 69 - "json"
Cohesion: 0.25
Nodes (5): api_key(), available(), _default(), stream_answer(), stream_report()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "test_voice_import.py"
Cohesion: 0.12
Nodes (9): claude_positions(), clean_rows(), _json_array(), ocr_text(), parse_positions(), _to_float(), test_claude_reply_is_cleaned(), test_oversized_image_refused_before_decoding() (+1 more)

### Community 72 - "Options for swing trades: strong plays, hedges and news (Nov 2026)"
Cohesion: 0.22
Nodes (8): 1. Breakout Rider with calls: the "strong play" version, 2. After a big news day, sell a put instead of buying, 3. Hedges: when they're worth it, Files, If you only want a couple of things to watch, Options for swing trades: strong plays, hedges and news (Nov 2026), What didn't work, What's worth using (few trades, swing timescale)

### Community 73 - "test_leaks.py"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 77 - "_cached_panel"
Cohesion: 0.25
Nodes (6): _cached_panel(), _panel_file(), _patched(), test_intraday_cache_is_short_while_the_market_is_open(), f(), test_price_panel_is_kept_on_disk_and_only_topped_up()

### Community 78 - "NQ strategy lab: results (October 2026)"
Cohesion: 0.25
Nodes (8): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Rerun, Swing results (test years May 2015 to Oct 2026), What GEX showed

### Community 79 - "_load"
Cohesion: 0.14
Nodes (12): Code, choices(), account_box(), guest_notice(), init_state(), _load(), my_swing_rules(), save_list() (+4 more)

### Community 81 - "bs.py"
Cohesion: 0.18
Nodes (7): bs_price(), fit_smile(), implied_vol(), smile_iv(), Surface, test_put_call_parity_and_iv_round_trip(), test_smile_fit_recovers_shape()

### Community 82 - "catalysts_view"
Cohesion: 0.15
Nodes (12): catalysts_view(), _filings(), compact_frame(), esc(), _finite(), fmt_big(), fmt_money(), fmt_num() (+4 more)

### Community 83 - "catalyst_lab.py"
Cohesion: 0.12
Nodes (21): beat_model(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), first_in() (+13 more)

### Community 84 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

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

### Community 90 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

### Community 91 - "regime"
Cohesion: 0.50
Nodes (3): _band(), regime(), test_regime_band_and_switch()

### Community 92 - "sharkfin/__init__.py"
Cohesion: 0.10
Nodes (6): stat(), tile(), pct(), stage_pill(), updown(), reload_changed_sharkfin()

### Community 93 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 94 - "pathlib"
Cohesion: 0.15
Nodes (6): main(), replay(), summary(), make_ohlcv(), ohlcv(), price_panel()

### Community 95 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 96 - "could_run"
Cohesion: 0.50
Nodes (3): could_run_tab(), could_run(), test_could_run_screen()

### Community 97 - "pdufa_dates"
Cohesion: 0.33
Nodes (4): _intraday_ttl(), future_dates(), pdufa_dates(), test_pdufa_dates_only_future_dates_near_the_word()

### Community 98 - "_Client"
Cohesion: 0.33
Nodes (3): _Client, user_agent(), test_needs_a_contact()

### Community 102 - "test_headline_class"
Cohesion: 0.40
Nodes (3): headline_class(), test_headline_class(), test_parse()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 657 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `test_catalyst_lab.py`, `builder.py`, `walk_forward`, `numpy`, `day_night.py`, `Series`, `NQ strategy lab: results (October 2026)`, `leader_dip.py`, `growth_lab.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.06416275430359937 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `NQ strategy lab: results (October 2026)` to `walkforward.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0784313725490196 - nodes in this community are weakly interconnected._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._
- **Should `Return Forecasting Models` be split into smaller, more focused modules?**
  _Cohesion score 0.07317073170731707 - nodes in this community are weakly interconnected._