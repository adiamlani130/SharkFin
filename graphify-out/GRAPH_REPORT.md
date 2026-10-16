# Graph Report - stoic-neumann-49eda7  (2026-10-15)

## Corpus Check
- 47 files · ~87,323 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .csv 2, .toml 1)

## Summary
- 1033 nodes · 2849 edges · 42 communities (38 shown, 4 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 85 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5d295aa4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- streamlit
- Valuation & Long Checklist
- scanner.py
- catalysts.py
- Portfolio Optimization
- test_app.py
- Return Forecasting Models
- Docs & Feature History
- data.py
- day_night.py
- indicators.py
- sharkfin/__init__.py
- Live Strategy Signals
- builder.py
- strategy_lab.py
- test_core.py
- leader_dip.py
- sharkfin/playbook.py
- walkforward.py
- home.py
- ratings.py
- DataFrame
- swing.py
- run
- history
- swing_tab
- ui.py
- market_inputs
- Caching & Prefetch
- predictions.py
- breakout_setup
- carry_forward
- forward_growth
- test_leaks.py
- Current Logo
- pandas
- breakout_rider.py
- factors.py
- backtest_price_composite
- _finite
- .mcp.json

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
- `test_sector_neutral_z()` --calls--> `sector_neutral_z()`  [EXTRACTED]
  tests/test_core.py → sharkfin/factors.py
- `test_features_have_no_lookahead()` --calls--> `build_features()`  [EXTRACTED]
  tests/test_core.py → sharkfin/forecasting.py
- `test_rsi_bounds_and_wilder()` --calls--> `rsi()`  [EXTRACTED]
  tests/test_core.py → sharkfin/indicators.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Combined plan of three researched swing/intraday strategies** — readme_combined_plan, readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night [EXTRACTED 1.00]
- **Pages that consume the user's chosen swing strategy** — readme_top_performers, readme_trade_setup, readme_strategy_lab, readme_leader_dip_plus_7, readme_tech_breakout_rider [EXTRACTED 1.00]

## Communities (42 total, 4 thin omitted)

### Community 0 - "streamlit"
Cohesion: 0.14
Nodes (20): backtest_summary(), br_backtest(), br_signals(), breakout_view(), day_night_view(), dn_backtest(), kpis(), ld_backtest() (+12 more)

### Community 1 - "Valuation & Long Checklist"
Cohesion: 0.06
Nodes (28): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+20 more)

### Community 2 - "scanner.py"
Cohesion: 0.19
Nodes (12): get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals(), scan() (+4 more)

### Community 3 - "catalysts.py"
Cohesion: 0.06
Nodes (33): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+25 more)

### Community 4 - "Portfolio Optimization"
Cohesion: 0.08
Nodes (30): market_beta(), summarize(), _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe() (+22 more)

### Community 5 - "test_app.py"
Cohesion: 0.08
Nodes (38): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+30 more)

### Community 6 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 7 - "Docs & Feature History"
Cohesion: 0.09
Nodes (25): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, GARCH(1,1) Filtered Historical Simulation, Market Dashboard Page (+17 more)

### Community 8 - "data.py"
Cohesion: 0.10
Nodes (17): analyst_data(), _copy(), _edgar_filings(), financials(), industry_members(), market_status(), news(), _NYSECalendar (+9 more)

### Community 9 - "day_night.py"
Cohesion: 0.12
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 10 - "indicators.py"
Cohesion: 0.08
Nodes (30): compare(), positions(), run(), Strategy, build_features(), adx(), atr(), bollinger() (+22 more)

### Community 11 - "sharkfin/__init__.py"
Cohesion: 0.06
Nodes (14): reload_changed_sharkfin(), api_key(), available(), _default(), stream_report(), nearest_levels(), pivots(), rsi_bearish_divergence() (+6 more)

### Community 12 - "Live Strategy Signals"
Cohesion: 0.12
Nodes (15): all_symbols(), download_ohlcv(), nasdaq100(), search(), sp500_table(), ttl_cache(), universe(), breakout_today() (+7 more)

### Community 13 - "builder.py"
Cohesion: 0.17
Nodes (12): _close(), describe(), describe_strategy(), _fmt_value(), Indicator, knobs(), label(), _obv_gap() (+4 more)

### Community 14 - "strategy_lab.py"
Cohesion: 0.19
Nodes (12): _add(), build_tab(), condition_rows(), lab_walk_forward(), _load(), _remove(), rules_key(), split_open_trade() (+4 more)

### Community 15 - "test_core.py"
Cohesion: 0.12
Nodes (14): fair_value_summary(), _earn_table(), _one_day_matrix(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_fair_value_blend() (+6 more)

### Community 16 - "leader_dip.py"
Cohesion: 0.09
Nodes (25): _intraday_ttl(), _align(), backtest(), _band(), latest(), market_on(), _members(), percentile_against() (+17 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (15): plan_view(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+7 more)

### Community 18 - "walkforward.py"
Cohesion: 0.11
Nodes (13): cut(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 19 - "home.py"
Cohesion: 0.22
Nodes (6): load_overview(), playbook_rows(), spy_regime(), tile(), latest_trade(), day_night_today()

### Community 20 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 21 - "DataFrame"
Cohesion: 0.15
Nodes (13): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), _earnings_fresh(), _earnings_from_disk(), earnings_history() (+5 more)

### Community 22 - "swing.py"
Cohesion: 0.21
Nodes (8): template(), clean(), _frame(), rule_checks(), rules(), scan(), stock_status(), test_swing_choice_rules_and_status()

### Community 23 - "run"
Cohesion: 0.21
Nodes (10): C(), compare_templates(), condition_mask(), run(), series(), signals(), warmup(), _ohlc() (+2 more)

### Community 24 - "history"
Cohesion: 0.40
Nodes (3): history(), _naive(), risk_free_rate()

### Community 25 - "swing_tab"
Cohesion: 0.27
Nodes (7): breakout_tab(), swing_tab(), about(), choices(), my_swing_rules(), swing_choice(), swing_picker()

### Community 26 - "ui.py"
Cohesion: 0.13
Nodes (19): render(), _tone_line(), overview(), clean_text(), asset(), disclaimer(), header(), hero() (+11 more)

### Community 27 - "market_inputs"
Cohesion: 0.25
Nodes (5): leader_dip_run(), leader_dip_tab(), market_history(), market_inputs(), switches()

### Community 28 - "Caching & Prefetch"
Cohesion: 0.17
Nodes (7): load_scan(), _is_empty(), prefetch(), deco(), cached(), wrapper(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 30 - "breakout_setup"
Cohesion: 0.15
Nodes (18): catalysts_view(), _filings(), dn_today(), switch_strip(), breakout_setup(), swing_rule_setup(), card(), checklist() (+10 more)

### Community 33 - "test_leaks.py"
Cohesion: 0.16
Nodes (8): daily_cash(), run(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_cash_before_the_first_yield_is_not_back_filled(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled()

### Community 35 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 37 - "pandas"
Cohesion: 0.10
Nodes (17): index_panel(), peer_table(), sector_etf_prices(), stock_ratings(), factor_backtest(), scan_data(), download_prices(), fetch() (+9 more)

### Community 38 - "breakout_rider.py"
Cohesion: 0.12
Nodes (12): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+4 more)

### Community 39 - "factors.py"
Cohesion: 0.24
Nodes (8): composite_scores(), explain(), price_factor_frame(), sector_neutral_z(), winsorize(), zscore(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_factor_composite_ranks_planted_winners()

### Community 40 - "backtest_price_composite"
Cohesion: 0.19
Nodes (7): backtest_price_composite(), earnings_factor_frame(), _earnings_table(), walk_forward(), evaluate(), weight_presets(), test_factor_backtest_positive_ic()

### Community 43 - "_finite"
Cohesion: 0.33
Nodes (4): compact_frame(), _finite(), fmt_big(), fmt_x()

### Community 44 - ".mcp.json"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

## Knowledge Gaps
- **7 isolated node(s):** `Shark Fin Over Waves Icon`, `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Portfolio Page (Risk + Optimizer)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 324 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_line()` connect `Valuation & Long Checklist` to `pandas`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shark Fin Over Waves Icon`, `Core Longs Screen`, `Could Run Screen` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `streamlit` be split into smaller, more focused modules?**
  _Cohesion score 0.14393939393939395 - nodes in this community are weakly interconnected._
- **Why does `build_tab()` connect `strategy_lab.py` to `streamlit`, `Portfolio Optimization`, `pandas`, `builder.py`, `swing.py`, `run`, `swing_tab`, `ui.py`, `breakout_setup`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `Valuation & Long Checklist` be split into smaller, more focused modules?**
  _Cohesion score 0.06354642313546423 - nodes in this community are weakly interconnected._
- **Why does `quality_points()` connect `leader_dip.py` to `Portfolio Optimization`, `pandas`, `breakout_rider.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._