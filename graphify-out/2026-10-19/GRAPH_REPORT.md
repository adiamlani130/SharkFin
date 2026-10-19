# Graph Report - SharkFin  (2026-10-18)

## Corpus Check
- 49 files · ~91,041 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: .csv 2, (none) 1, .toml 1)

## Summary
- 1097 nodes · 2985 edges · 41 communities (38 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 94 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0914ed88`
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
- Technical Indicators
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
- Earnings Cache
- leader_dip_run
- Membership & Intraday Data
- Breakout Rider Strategy
- Setup Views
- Swing Engine
- factors.py
- risk.py
- swing.py
- swing_tab
- Strategy Lab
- Scan Prefetch
- app_pages/speculation.py
- research.py
- numpy
- Home Page Regime
- _cached_panel
- MCP Servers
- Current Logo
- Offline Test Design

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 37 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `plan_view()` - 21 edges
8. `compute_all()` - 18 edges
9. `breakout_setup()` - 17 edges
10. `leader_dip_tab()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `stock_ratings()` --calls--> `to_gics()`  [EXTRACTED]
  app_pages/research.py → sharkfin/ratings.py
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py
- `stage_pill()` --calls--> `h()`  [EXTRACTED]
  app_pages/speculation.py → sharkfin/ui.py
- `test_fmt_money_negative_sign_before_dollar()` --calls--> `fmt_money()`  [EXTRACTED]
  tests/test_core.py → sharkfin/ui.py
- `drawFin()` --conceptually_related_to--> `SharkFin App`  [INFERRED]
  sharkfin/assets/ocean.html → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (41 total, 3 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (33): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+25 more)

### Community 1 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 2 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 3 - "Strategy Builder & Swing"
Cohesion: 0.11
Nodes (23): C(), _close(), compare_templates(), condition_mask(), describe(), _fmt_value(), Indicator, knobs() (+15 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 6 - "test_app.py"
Cohesion: 0.07
Nodes (38): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+30 more)

### Community 7 - "Technical Indicators"
Cohesion: 0.06
Nodes (36): compare(), positions(), run(), Strategy, build_features(), adx(), atr(), bollinger() (+28 more)

### Community 8 - "Leader Dip Strategy"
Cohesion: 0.07
Nodes (36): _market_gap(), _intraday_ttl(), sma(), _align(), backtest(), _band(), follow_up(), latest() (+28 more)

### Community 9 - "UI Helpers"
Cohesion: 0.10
Nodes (20): clean_text(), asset(), compact_frame(), disclaimer(), _finite(), fmt_big(), fmt_x(), header() (+12 more)

### Community 10 - "Day-Night Strategy"
Cohesion: 0.12
Nodes (16): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+8 more)

### Community 11 - "Live Signals"
Cohesion: 0.13
Nodes (14): breakout_tab(), scan_data(), sp500_table(), fundamental_factor_frame(), breakout_today(), leader_dip_today(), market_inputs(), sector_map() (+6 more)

### Community 12 - "catalysts.py"
Cohesion: 0.06
Nodes (35): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+27 more)

### Community 13 - "Playbook Page"
Cohesion: 0.19
Nodes (21): backtest_summary(), br_signals(), breakout_view(), day_night_view(), dn_today(), kpis(), ld_signals(), leader_dip_view() (+13 more)

### Community 14 - "Market Data Fetching"
Cohesion: 0.11
Nodes (15): all_symbols(), _edgar_filings(), market_status(), nasdaq100(), news(), _NYSECalendar, _parse_date(), _rss() (+7 more)

### Community 15 - "scanner.py"
Cohesion: 0.19
Nodes (12): get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals(), scan() (+4 more)

### Community 16 - "Walk-Forward Engine"
Cohesion: 0.11
Nodes (12): cut(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+4 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.06
Nodes (21): reload_changed_sharkfin(), api_key(), available(), _default(), stream_report(), best_weights(), correlations(), drawdowns() (+13 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.14
Nodes (9): prices(), all_tickers(), Play, radar(), stage(), stage_history(), stats(), Theme (+1 more)

### Community 19 - "download_prices"
Cohesion: 0.18
Nodes (8): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), download_prices(), infos(), peers_for()

### Community 20 - "Earnings Cache"
Cohesion: 0.14
Nodes (16): analyst_data(), _earnings_fresh(), _earnings_from_disk(), earnings_histories(), earnings_history(), _earnings_to_disk(), financials(), industry_members() (+8 more)

### Community 21 - "leader_dip_run"
Cohesion: 0.15
Nodes (12): br_backtest(), dn_backtest(), ld_backtest(), factor_backtest(), leader_dip_run(), download_ohlcv(), last_years(), sp500_ever() (+4 more)

### Community 22 - "Membership & Intraday Data"
Cohesion: 0.14
Nodes (13): spy_regime(), alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), history(), intraday_bars() (+5 more)

### Community 23 - "Breakout Rider Strategy"
Cohesion: 0.19
Nodes (9): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+1 more)

### Community 24 - "Setup Views"
Cohesion: 0.16
Nodes (17): catalysts_view(), _filings(), overview(), switch_strip(), _fmt(), breakout_setup(), swing_rule_setup(), card() (+9 more)

### Community 25 - "Swing Engine"
Cohesion: 0.16
Nodes (5): daily_cash(), panel_adx(), panel_atr(), run(), stats()

### Community 26 - "factors.py"
Cohesion: 0.12
Nodes (16): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), price_factor_frame(), sector_neutral_z(), walk_forward() (+8 more)

### Community 27 - "risk.py"
Cohesion: 0.16
Nodes (16): annualized_return(), annualized_vol(), beta_alpha(), blume_adjusted_beta(), calmar_ratio(), cornish_fisher_var(), drawdown_series(), historical_cvar() (+8 more)

### Community 28 - "swing.py"
Cohesion: 0.22
Nodes (7): clean(), _frame(), rule_checks(), rules(), scan(), stock_status(), test_swing_choice_rules_and_status()

### Community 29 - "swing_tab"
Cohesion: 0.27
Nodes (7): swing_tab(), describe_strategy(), about(), choices(), my_swing_rules(), swing_choice(), swing_picker()

### Community 30 - "Strategy Lab"
Cohesion: 0.18
Nodes (12): _add(), build_tab(), condition_rows(), lab_walk_forward(), _load(), _remove(), rules_key(), split_open_trade() (+4 more)

### Community 31 - "Scan Prefetch"
Cohesion: 0.14
Nodes (8): load_scan(), _copy(), _is_empty(), prefetch(), deco(), cached(), wrapper(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 32 - "app_pages/speculation.py"
Cohesion: 0.40
Nodes (3): pct(), stage_pill(), updown()

### Community 34 - "numpy"
Cohesion: 0.33
Nodes (7): _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled(), test_factor_replay_keeps_a_holding_that_stops_trading_in_the_average(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_night_leg_ignores_everything_after_1530(), test_walk_forward_never_hands_later_rows_to_a_run()

### Community 35 - "Home Page Regime"
Cohesion: 0.22
Nodes (5): load_overview(), playbook_rows(), tile(), latest_trade(), day_night_today()

### Community 36 - "_cached_panel"
Cohesion: 0.17
Nodes (8): _cached_panel(), _fetch_ohlcv(), _fetch_prices(), fetch(), _naive(), _panel_file(), _patched(), test_price_panel_is_kept_on_disk_and_only_topped_up()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 346 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_line()` connect `Valuation & Quality Scores` to `Live Signals`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05401234567901234 - nodes in this community are weakly interconnected._
- **Why does `Financials` connect `Valuation & Quality Scores` to `Earnings Cache`, `Market Data Fetching`, `test_app.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `sharkfin/portfolio.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1455026455026455 - nodes in this community are weakly interconnected._
- **Why does `best_weights()` connect `sharkfin/playbook.py` to `numpy`, `Live Signals`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._