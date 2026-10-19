# Graph Report - SharkFin  (2026-10-19)

## Corpus Check
- 53 files · ~102,045 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: .csv 16, (none) 1, .toml 1)

## Summary
- 1263 nodes · 3419 edges · 42 communities (40 shown, 2 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3d250e68`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- ratings.py
- sentiment.py
- Strategy Builder & Swing
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- Leader Dip Strategy
- ui.py
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
- nq_lab.py
- numpy
- Strategy Lab
- run
- sharkfin/__init__.py
- test_leaks.py
- _cached_panel
- test_nq_lab.py
- walk_forward
- MCP Servers
- Current Logo
- run_one
- gex_pct
- Series
- Offline Test Design
- nq_regimes.py

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 37 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `_sw()` - 22 edges
7. `quality_metrics()` - 22 edges
8. `plan_view()` - 21 edges
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
- `test_features_have_no_lookahead()` --calls--> `build_features()`  [EXTRACTED]
  tests/test_core.py → sharkfin/forecasting.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (42 total, 2 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 1 - "ratings.py"
Cohesion: 0.16
Nodes (10): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), value_inputs() (+2 more)

### Community 2 - "sentiment.py"
Cohesion: 0.13
Nodes (17): render(), _tone_line(), aggregate_sentiment(), BM25, clean_text(), dedupe(), hours_old(), is_noise() (+9 more)

### Community 3 - "Strategy Builder & Swing"
Cohesion: 0.06
Nodes (36): _add(), _load(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy() (+28 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 6 - "test_app.py"
Cohesion: 0.08
Nodes (37): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+29 more)

### Community 8 - "Leader Dip Strategy"
Cohesion: 0.05
Nodes (47): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), hurst_exponent() (+39 more)

### Community 9 - "ui.py"
Cohesion: 0.09
Nodes (21): choices(), asset(), disclaimer(), esc(), fmt_x(), hero(), init_state(), _load() (+13 more)

### Community 10 - "Day-Night Strategy"
Cohesion: 0.05
Nodes (39): _intraday_ttl(), backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats() (+31 more)

### Community 11 - "Live Signals"
Cohesion: 0.14
Nodes (15): breakout_tab(), nasdaq100(), sp500_table(), universe(), breakout_today(), leader_dip_today(), market_inputs(), sector_map() (+7 more)

### Community 12 - "catalysts.py"
Cohesion: 0.10
Nodes (21): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+13 more)

### Community 13 - "Playbook Page"
Cohesion: 0.27
Nodes (17): backtest_summary(), br_signals(), breakout_view(), day_night_view(), dn_today(), kpis(), ld_signals(), leader_dip_view() (+9 more)

### Community 14 - "Market Data Fetching"
Cohesion: 0.11
Nodes (14): _copy(), _edgar_filings(), _is_empty(), market_status(), news(), _NYSECalendar, _parse_date(), _rss() (+6 more)

### Community 15 - "scanner.py"
Cohesion: 0.06
Nodes (33): get_universe(), leader_dip_tab(), load_scan(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+25 more)

### Community 16 - "Walk-Forward Engine"
Cohesion: 0.11
Nodes (13): gate_grid(), cut(), _day(), Fold, folds(), grid(), _neighbours(), pick() (+5 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.07
Nodes (23): plan_view(), reload_changed_sharkfin(), api_key(), available(), _default(), stream_report(), best_weights(), correlations() (+15 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.10
Nodes (14): prices(), compare(), positions(), run(), Strategy, all_tickers(), Play, radar() (+6 more)

### Community 19 - "download_prices"
Cohesion: 0.15
Nodes (10): index_panel(), peer_table(), sector_etf_prices(), stock_ratings(), factor_backtest(), download_prices(), earnings_histories(), infos() (+2 more)

### Community 20 - "ttl_cache"
Cohesion: 0.12
Nodes (18): spy_regime(), all_symbols(), analyst_data(), earnings_history(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials() (+10 more)

### Community 21 - "leader_dip_run"
Cohesion: 0.13
Nodes (14): br_backtest(), dn_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), last_years(), sp500_ever(), sp500_members() (+6 more)

### Community 22 - "Membership & Intraday Data"
Cohesion: 0.12
Nodes (13): load_overview(), playbook_rows(), alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars() (+5 more)

### Community 23 - "Breakout Rider Strategy"
Cohesion: 0.20
Nodes (8): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate()

### Community 24 - "Setup Views"
Cohesion: 0.16
Nodes (17): catalysts_view(), _filings(), switch_strip(), breakout_setup(), swing_rule_setup(), card(), checklist(), compact_frame() (+9 more)

### Community 25 - "Swing Engine"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 28 - "nq_lab.py"
Cohesion: 0.17
Nodes (22): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_regime() (+14 more)

### Community 29 - "numpy"
Cohesion: 0.06
Nodes (46): market_beta(), summarize(), bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), ema_cross_5m() (+38 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.13
Nodes (11): _fmt(), build_tab(), condition_rows(), lab_walk_forward(), leader_dip_tab(), _remove(), rules_key(), split_open_trade() (+3 more)

### Community 32 - "run"
Cohesion: 0.14
Nodes (13): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook, Rerun (+5 more)

### Community 33 - "sharkfin/__init__.py"
Cohesion: 0.12
Nodes (4): tile(), pct(), stage_pill(), updown()

### Community 34 - "test_leaks.py"
Cohesion: 0.24
Nodes (7): _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_folds_slide_and_never_overlap(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_members_only_trade_while_in_the_index(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled()

### Community 36 - "_cached_panel"
Cohesion: 0.18
Nodes (11): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save(), _patched() (+3 more)

### Community 38 - "test_nq_lab.py"
Cohesion: 0.21
Nodes (10): _market(), _settings(), _signal(), test_bracket_counts_the_stop_when_stop_and_target_share_a_bar(), test_cutting_off_the_future_changes_no_past_result(), test_day_trades_decide_each_bar_from_earlier_bars_only(), test_router_only_learns_from_finished_days(), test_swing_decisions_fill_at_the_next_open() (+2 more)

### Community 39 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "run_one"
Cohesion: 0.33
Nodes (3): first_usable(), run_one(), Strategy

### Community 43 - "gex_pct"
Cohesion: 0.25
Nodes (4): gex_pct(), known(), _night_signal(), _regime()

### Community 44 - "Series"
Cohesion: 0.10
Nodes (12): atr(), deflated_sharpe(), fetch(), _folds_beating_cash(), intraday_frames(), load(), main(), night_returns() (+4 more)

### Community 49 - "nq_regimes.py"
Cohesion: 0.10
Nodes (21): day_view(), evaluate(), swing_returns(), _allowed(), _bands(), catalogue(), cell_names(), _cut() (+13 more)

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 407 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `Walk-Forward Engine` to `run`, `Strategy Builder & Swing`, `walk_forward`, `Day-Night Strategy`, `run_one`, `Live Signals`, `leader_dip_run`, `Breakout Rider Strategy`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `Walk-Forward Engine`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Should `sentiment.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12561576354679804 - nodes in this community are weakly interconnected._
- **Should `Strategy Builder & Swing` be split into smaller, more focused modules?**
  _Cohesion score 0.06487434248977206 - nodes in this community are weakly interconnected._