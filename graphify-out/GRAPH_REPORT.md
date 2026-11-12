# Graph Report - SharkFin  (2026-11-12)

## Corpus Check
- 72 files · ~125,715 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .csv 48, (none) 1, .toml 1)
- WARNING: 50 of 134 files seen (37%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1684 nodes · 4403 edges · 79 communities (58 shown, 21 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 145 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a34f1d12`
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
- indicators.py
- ui.py
- day_night.py
- ttl_cache
- catalysts.py
- app_pages/playbook.py
- data.py
- sharkfin/playbook.py
- sentiment.py
- sharkfin/speculation.py
- nq_regimes.py
- stock_ratings
- sharkfin/portfolio.py
- streamlit
- factors.py
- catalyst_lab.py
- steps
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- research.py
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
- sma
- targets.py
- hurst_exponent
- backtest.py
- test_catalyst_lab.py
- strategy_lab.py
- store.py
- _cached_panel
- json
- Phone alerts (free, through ntfy)
- regime
- forward_growth
- test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `assess()` - 19 edges
9. `download_prices()` - 19 edges
10. `Day` - 18 edges

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

## Communities (79 total, 21 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 1 - "sharkfin/__init__.py"
Cohesion: 0.08
Nodes (6): stat(), tile(), pct(), stage_pill(), updown(), reload_changed_sharkfin()

### Community 2 - "sec_lab.py"
Cohesion: 0.08
Nodes (27): _intraday_ttl(), _Client, dilution_table(), _era(), full_text(), future_dates(), headline_class(), main() (+19 more)

### Community 3 - "builder.py"
Cohesion: 0.05
Nodes (48): _add(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value() (+40 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.08
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.07
Nodes (44): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+36 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.14
Nodes (16): _align(), backtest(), latest(), market_on(), _members(), percentile_against(), plus_frames(), quality_points() (+8 more)

### Community 8 - "indicators.py"
Cohesion: 0.15
Nodes (18): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+10 more)

### Community 9 - "ui.py"
Cohesion: 0.06
Nodes (30): Code, choices(), account_box(), asset(), color(), day_color(), disclaimer(), fetch_all() (+22 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "ttl_cache"
Cohesion: 0.12
Nodes (16): leader_dip_run(), download_ohlcv(), tbill_yields(), ttl_cache(), ttm(), breakout_today(), leader_dip_today(), market_inputs() (+8 more)

### Community 12 - "catalysts.py"
Cohesion: 0.06
Nodes (32): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+24 more)

### Community 13 - "app_pages/playbook.py"
Cohesion: 0.19
Nodes (18): backtest_summary(), br_backtest(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table(), ld_backtest() (+10 more)

### Community 14 - "data.py"
Cohesion: 0.10
Nodes (17): get_universe(), all_symbols(), _copy(), _edgar_filings(), market_status(), nasdaq100(), news(), _NYSECalendar (+9 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (15): both_view(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+7 more)

### Community 16 - "sentiment.py"
Cohesion: 0.18
Nodes (11): aggregate_sentiment(), BM25, clean_text(), dedupe(), hours_old(), is_noise(), label(), rank_articles() (+3 more)

### Community 17 - "sharkfin/speculation.py"
Cohesion: 0.11
Nodes (11): prices(), theme_turn(), all_tickers(), Play, radar(), stage(), stage_history(), stats() (+3 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.11
Nodes (19): evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix() (+11 more)

### Community 19 - "stock_ratings"
Cohesion: 0.14
Nodes (11): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), download_prices(), industry_members() (+3 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.14
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "streamlit"
Cohesion: 0.11
Nodes (23): catalysts_view(), _filings(), render(), _tone_line(), overview(), switch_strip(), card(), checklist() (+15 more)

### Community 22 - "factors.py"
Cohesion: 0.12
Nodes (18): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+10 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.12
Nodes (21): beat_model(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), first_in() (+13 more)

### Community 24 - "steps"
Cohesion: 0.06
Nodes (30): permissions, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, default (+22 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.10
Nodes (19): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+11 more)

### Community 27 - "scanner.py"
Cohesion: 0.15
Nodes (16): breakout_tab(), factor_backtest(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+8 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.12
Nodes (29): atr(), buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized() (+21 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 30 - "research.py"
Cohesion: 0.11
Nodes (15): run_forecast(), lab_walk_forward(), analyst_data(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), financials() (+7 more)

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "test_store.py"
Cohesion: 0.15
Nodes (13): Identity, load(), save(), FakeResp, test_accounts_are_separate(), test_cloud_outage_raises(), test_cloud_round_trip(), get() (+5 more)

### Community 34 - "alerts.py"
Cohesion: 0.13
Nodes (18): compose(), holding_exits(), new_topic(), portfolio_threat(), run(), send(), signal_lines(), threat_line() (+10 more)

### Community 35 - "assess"
Cohesion: 0.15
Nodes (13): assess(), level_of(), next_earnings(), portfolio_returns(), _ramp(), Threat, _prices(), test_calm_portfolio_is_low() (+5 more)

### Community 36 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

### Community 37 - "load_scan"
Cohesion: 0.16
Nodes (8): load_scan(), _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "numpy"
Cohesion: 0.13
Nodes (16): trailing_pct(), cut(), make_ohlcv(), ohlcv(), price_panel(), _market(), _settings(), _signal() (+8 more)

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
Cohesion: 0.11
Nodes (13): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _parse_spells() (+5 more)

### Community 44 - "Series"
Cohesion: 0.09
Nodes (11): deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main(), rotation() (+3 more)

### Community 47 - "test_core.py"
Cohesion: 0.09
Nodes (20): fair_value_summary(), _earn_table(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_earnings_factors_use_only_past_reports(), test_factor_backtest_positive_ic(), test_fair_value_blend() (+12 more)

### Community 49 - "walkforward.py"
Cohesion: 0.11
Nodes (13): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 50 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "growth_lab.py"
Cohesion: 0.06
Nodes (34): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+26 more)

### Community 59 - "sma"
Cohesion: 0.17
Nodes (7): _market_gap(), rsi(), sma(), follow_up(), price_chart(), carry_forward(), test_leader_dip_follow_up()

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 63 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 64 - "test_catalyst_lab.py"
Cohesion: 0.21
Nodes (11): breadth(), kalshi_daily(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_cyclical_stocks_are_valued_on_through_cycle_earnings(), test_earnings_frame_reports_five_year_average_eps() (+3 more)

### Community 65 - "strategy_lab.py"
Cohesion: 0.17
Nodes (14): research_charts(), build_tab(), _cat(), catalyst_tab(), condition_rows(), leader_dip_tab(), _load(), _pct_cols() (+6 more)

### Community 66 - "store.py"
Cohesion: 0.20
Nodes (12): auth_configured(), cloud_all(), _cloud_read(), _cloud_write(), hash_id(), _headers(), identity(), _secrets() (+4 more)

### Community 67 - "_cached_panel"
Cohesion: 0.16
Nodes (11): _cached_panel(), _fetch_ohlcv(), _fetch_prices(), fetch(), _naive(), _panel_file(), _panel_load(), _panel_save() (+3 more)

### Community 69 - "json"
Cohesion: 0.18
Nodes (8): rules_key(), api_key(), available(), _default(), stream_report(), _local_path(), _read_file(), _write_file()

### Community 70 - "Phone alerts (free, through ntfy)"
Cohesion: 0.29
Nodes (6): Each user (in the app), Keeping it running, One-time setup (about 3 minutes), Phone alerts and the threat level, Phone alerts (free, through ntfy), Portfolio threat level

### Community 71 - "regime"
Cohesion: 0.50
Nodes (3): _band(), regime(), test_regime_band_and_switch()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 571 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `run`, `test_catalyst_lab.py`, `builder.py`, `numpy`, `leader_dip.py`, `day_night.py`, `Series`, `factors.py`, `growth_lab.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `walkforward.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `sharkfin/__init__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07977207977207977 - nodes in this community are weakly interconnected._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07908163265306123 - nodes in this community are weakly interconnected._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05258033106134372 - nodes in this community are weakly interconnected._