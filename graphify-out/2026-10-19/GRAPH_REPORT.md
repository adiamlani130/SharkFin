# Graph Report - SharkFin  (2026-10-19)

## Corpus Check
- 52 files · ~98,666 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: .csv 3, (none) 1, .toml 1)

## Summary
- 1219 nodes · 3318 edges · 53 communities (45 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 99 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `98f80f3d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- ratings.py
- sharkfin/portfolio.py
- Strategy Builder & Swing
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- levels.py
- Leader Dip Strategy
- UI Helpers
- Day-Night Strategy
- Live Signals
- catalysts.py
- Playbook Page
- Market Data Fetching
- scanner.py
- Walk-Forward Engine
- sharkfin/playbook.py
- sharkfin/speculation.py
- download_prices
- ttl_cache
- leader_dip_run
- Membership & Intraday Data
- Breakout Rider Strategy
- Setup Views
- Swing Engine
- factors.py
- risk.py
- nq_lab.py
- numpy
- Strategy Lab
- Scan Prefetch
- run
- streamlit
- test_leaks.py
- Home Page Regime
- _cached_panel
- test_core.py
- test_nq_lab.py
- backtest_price_composite
- MCP Servers
- Current Logo
- main
- day_view
- load
- Offline Test Design
- _intraday_ttl
- night_returns
- swing_returns
- fair_value_summary
- forward_growth
- run

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 37 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `plan_view()` - 21 edges
8. `_sw()` - 20 edges
9. `compute_all()` - 18 edges
10. `Day` - 18 edges

## Surprising Connections (you probably didn't know these)
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py
- `swing_tab()` --calls--> `about()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/swing.py
- `stage_pill()` --calls--> `h()`  [EXTRACTED]
  app_pages/speculation.py → sharkfin/ui.py
- `test_sector_neutral_z()` --calls--> `sector_neutral_z()`  [EXTRACTED]
  tests/test_core.py → sharkfin/factors.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (53 total, 8 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 1 - "ratings.py"
Cohesion: 0.08
Nodes (20): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), api_key(), available(), _default() (+12 more)

### Community 2 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 3 - "Strategy Builder & Swing"
Cohesion: 0.07
Nodes (33): C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value(), Indicator (+25 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 6 - "test_app.py"
Cohesion: 0.08
Nodes (38): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+30 more)

### Community 7 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 8 - "Leader Dip Strategy"
Cohesion: 0.06
Nodes (47): positions(), _market_gap(), build_features(), adx(), atr(), bollinger(), compute_all(), donchian() (+39 more)

### Community 9 - "UI Helpers"
Cohesion: 0.09
Nodes (19): clean_text(), asset(), compact_frame(), esc(), _finite(), fmt_big(), fmt_x(), header() (+11 more)

### Community 10 - "Day-Night Strategy"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "Live Signals"
Cohesion: 0.19
Nodes (8): breakout_today(), leader_dip_today(), market_inputs(), sector_map(), sector_ret3(), sp500_ohlcv(), tech_gains(), tech_ohlcv()

### Community 12 - "catalysts.py"
Cohesion: 0.06
Nodes (33): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+25 more)

### Community 13 - "Playbook Page"
Cohesion: 0.19
Nodes (21): backtest_summary(), br_signals(), breakout_view(), day_night_view(), dn_backtest(), dn_today(), kpis(), ld_signals() (+13 more)

### Community 14 - "Market Data Fetching"
Cohesion: 0.11
Nodes (13): _copy(), _edgar_filings(), _is_empty(), market_status(), news(), _NYSECalendar, _parse_date(), _rss() (+5 more)

### Community 15 - "scanner.py"
Cohesion: 0.13
Nodes (19): get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals(), scan() (+11 more)

### Community 16 - "Walk-Forward Engine"
Cohesion: 0.13
Nodes (10): cut(), _day(), Fold, folds(), grid(), _neighbours(), pick(), test_folds_slide_and_never_overlap() (+2 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.10
Nodes (16): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+8 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.14
Nodes (9): prices(), all_tickers(), Play, radar(), stage(), stage_history(), stats(), Theme (+1 more)

### Community 19 - "download_prices"
Cohesion: 0.33
Nodes (4): download_prices(), _fetch_prices(), fetch(), _naive()

### Community 20 - "ttl_cache"
Cohesion: 0.12
Nodes (18): breakout_tab(), scan_data(), all_symbols(), analyst_data(), earnings_histories(), earnings_history(), financials(), industry_members() (+10 more)

### Community 21 - "leader_dip_run"
Cohesion: 0.16
Nodes (14): br_backtest(), ld_backtest(), factor_backtest(), leader_dip_run(), download_ohlcv(), _fetch_ohlcv(), last_years(), _parse_spells() (+6 more)

### Community 22 - "Membership & Intraday Data"
Cohesion: 0.14
Nodes (12): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), history(), intraday_bars(), market_history() (+4 more)

### Community 23 - "Breakout Rider Strategy"
Cohesion: 0.19
Nodes (9): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+1 more)

### Community 24 - "Setup Views"
Cohesion: 0.17
Nodes (16): catalysts_view(), _filings(), switch_strip(), _fmt(), breakout_setup(), swing_rule_setup(), card(), switches() (+8 more)

### Community 25 - "Swing Engine"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 26 - "factors.py"
Cohesion: 0.24
Nodes (8): composite_scores(), explain(), price_factor_frame(), sector_neutral_z(), winsorize(), zscore(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_factor_composite_ranks_planted_winners()

### Community 27 - "risk.py"
Cohesion: 0.13
Nodes (18): compare(), run(), Strategy, annualized_return(), annualized_vol(), beta_alpha(), blume_adjusted_beta(), calmar_ratio() (+10 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.14
Nodes (26): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+18 more)

### Community 29 - "numpy"
Cohesion: 0.16
Nodes (16): bollinger_fade(), bracket(), Day, day_long_only(), ema_cross_5m(), _ema_rows(), _filter(), first_true() (+8 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.18
Nodes (10): _add(), build_tab(), condition_rows(), lab_walk_forward(), _load(), _remove(), rules_key(), split_open_trade() (+2 more)

### Community 31 - "Scan Prefetch"
Cohesion: 0.20
Nodes (5): load_scan(), prefetch(), deco(), cached(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 32 - "run"
Cohesion: 0.13
Nodes (11): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Rerun, Swing results (test years May 2015 to Oct 2026), What GEX showed (+3 more)

### Community 33 - "streamlit"
Cohesion: 0.09
Nodes (9): render(), _tone_line(), overview(), pct(), stage_pill(), updown(), reload_changed_sharkfin(), disclaimer() (+1 more)

### Community 34 - "test_leaks.py"
Cohesion: 0.32
Nodes (5): _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled()

### Community 35 - "Home Page Regime"
Cohesion: 0.18
Nodes (7): load_overview(), playbook_rows(), spy_regime(), tile(), latest_trade(), day_night_today(), summary_rows()

### Community 36 - "_cached_panel"
Cohesion: 0.18
Nodes (11): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save(), _patched() (+3 more)

### Community 37 - "test_core.py"
Cohesion: 0.16
Nodes (14): _earn_table(), _panel(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_features_have_no_lookahead(), test_fmt_money_negative_sign_before_dollar(), test_intraday_cache_is_short_while_the_market_is_open(), f() (+6 more)

### Community 38 - "test_nq_lab.py"
Cohesion: 0.27
Nodes (8): _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only(), test_swing_decisions_fill_at_the_next_open(), test_the_check_catches_a_strategy_that_peeks()

### Community 39 - "backtest_price_composite"
Cohesion: 0.18
Nodes (8): backtest_price_composite(), earnings_factor_frame(), _earnings_table(), walk_forward(), evaluate(), weight_presets(), test_factor_backtest_positive_ic(), test_factor_replay_keeps_a_holding_that_stops_trading_in_the_average()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "main"
Cohesion: 0.17
Nodes (7): deflated_sharpe(), first_usable(), _folds_beating_cash(), main(), rotation(), run_one(), Strategy

### Community 43 - "day_view"
Cohesion: 0.22
Nodes (5): atr(), evaluate(), day_view(), intraday_frames(), known()

### Community 44 - "load"
Cohesion: 0.25
Nodes (3): fetch(), load(), trailing_pct()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 389 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `run` to `Strategy Builder & Swing`, `backtest_price_composite`, `Leader Dip Strategy`, `Day-Night Strategy`, `main`, `Walk-Forward Engine`, `leader_dip_run`, `Breakout Rider Strategy`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `load()` connect `load` to `Leader Dip Strategy`, `main`, `day_view`, `leader_dip_run`, `nq_lab.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Should `ratings.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07505285412262157 - nodes in this community are weakly interconnected._
- **Why does `scan()` connect `Strategy Builder & Swing` to `leader_dip_run`, `scanner.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._