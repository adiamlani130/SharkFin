# Graph Report - SharkFin  (2026-10-16)

## Corpus Check
- 50 files · ~88,531 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: .csv 2, (none) 1, .toml 1)

## Summary
- 1070 nodes · 2928 edges · 48 communities (40 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 94 edges (avg confidence: 0.85)
- Token cost: 104,364 input · 0 output

## Community Hubs (Navigation)
- Valuation & Quality Scores
- Scanner & Research Data
- Portfolio Risk
- Strategy Builder & Swing
- App Pages & Landing Animation
- Return Forecasting Models
- App Page Tests
- Technical Indicators
- Leader Dip Strategy
- UI Helpers
- Day-Night Strategy
- Live Signals
- Catalysts & Long Checklist
- Playbook Page
- Market Data Fetching
- Offline Test Fakes
- Walk-Forward Engine
- Combined Playbook Plan
- News Sentiment
- Price History Cache
- Earnings Cache
- S&P 500 Backtests
- Membership & Intraday Data
- Breakout Rider Strategy
- Setup Views
- Swing Engine
- Factor Scores
- Core Unit Tests
- Support & Resistance Levels
- Catalysts Page Wiring
- Strategy Lab
- Scan Prefetch
- Price Composite Backtest
- Leak Tests
- Home Page Regime
- Price Fetch Helpers
- Intraday Cache TTL
- Weight Presets
- Frame Formatting
- MCP Servers
- Current Logo
- Fair Value Blend
- Forward Growth
- Alpaca Retry Test
- Offline Test Design
- Signal Follow-Up

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 37 edges
3. `_line()` - 28 edges
4. `build_tab()` - 25 edges
5. `catalysts_view()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `plan_view()` - 21 edges
8. `compute_all()` - 18 edges
9. `piotroski_f_score()` - 17 edges
10. `sma()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_features_have_no_lookahead()` --calls--> `build_features()`  [EXTRACTED]
  tests/test_core.py → sharkfin/forecasting.py
- `test_rsi_bounds_and_wilder()` --calls--> `rsi()`  [EXTRACTED]
  tests/test_core.py → sharkfin/indicators.py
- `test_rsi_matches_reference_formula()` --calls--> `rsi()`  [EXTRACTED]
  tests/test_core.py → sharkfin/indicators.py
- `test_drawdown_simple()` --calls--> `max_drawdown()`  [EXTRACTED]
  tests/test_core.py → sharkfin/risk.py
- `test_fmt_money_negative_sign_before_dollar()` --calls--> `fmt_money()`  [EXTRACTED]
  tests/test_core.py → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (48 total, 8 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (28): net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices(), justified_pb_value() (+20 more)

### Community 1 - "Scanner & Research Data"
Cohesion: 0.06
Nodes (34): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), breakout_tab(), factor_backtest(), get_universe() (+26 more)

### Community 2 - "Portfolio Risk"
Cohesion: 0.07
Nodes (33): compare(), positions(), run(), Strategy, summarize(), _cluster_var(), compare_allocations(), efficient_frontier() (+25 more)

### Community 3 - "Strategy Builder & Swing"
Cohesion: 0.07
Nodes (31): C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value(), Indicator (+23 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 6 - "App Page Tests"
Cohesion: 0.08
Nodes (23): reload_changed_sharkfin(), make_ohlcv(), ohlcv(), price_panel(), offline(), _ok(), _page(), _scanned() (+15 more)

### Community 7 - "Technical Indicators"
Cohesion: 0.12
Nodes (23): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), hurst_exponent() (+15 more)

### Community 8 - "Leader Dip Strategy"
Cohesion: 0.12
Nodes (21): _align(), backtest(), _band(), latest(), market_on(), _members(), percentile_against(), plus_frames() (+13 more)

### Community 9 - "UI Helpers"
Cohesion: 0.10
Nodes (23): clean_text(), choices(), asset(), disclaimer(), header(), hero(), init_state(), kv() (+15 more)

### Community 10 - "Day-Night Strategy"
Cohesion: 0.11
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 11 - "Live Signals"
Cohesion: 0.12
Nodes (16): ld_backtest(), leader_dip_tab(), log_signals(), leader_dip_run(), last_years(), sp500_ever(), yahoo_period(), sector_returns() (+8 more)

### Community 12 - "Catalysts & Long Checklist"
Cohesion: 0.11
Nodes (17): _col(), core_long_checklist(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), insider_summary() (+9 more)

### Community 13 - "Playbook Page"
Cohesion: 0.21
Nodes (20): backtest_summary(), br_signals(), breakout_view(), day_night_view(), dn_backtest(), dn_today(), kpis(), ld_signals() (+12 more)

### Community 14 - "Market Data Fetching"
Cohesion: 0.11
Nodes (15): html_to_text(), _copy(), _edgar_filings(), _is_empty(), market_status(), news(), _NYSECalendar, _parse_date() (+7 more)

### Community 15 - "Offline Test Fakes"
Cohesion: 0.13
Nodes (19): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+11 more)

### Community 16 - "Walk-Forward Engine"
Cohesion: 0.11
Nodes (12): cut(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+4 more)

### Community 17 - "Combined Playbook Plan"
Cohesion: 0.15
Nodes (14): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+6 more)

### Community 18 - "News Sentiment"
Cohesion: 0.13
Nodes (13): could_run_tab(), aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles() (+5 more)

### Community 19 - "Price History Cache"
Cohesion: 0.13
Nodes (14): lab_walk_forward(), alpaca_daily(), analyst_data(), financials(), history(), industry_members(), info(), infos() (+6 more)

### Community 20 - "Earnings Cache"
Cohesion: 0.14
Nodes (13): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_histories(), earnings_history(), _earnings_to_disk(), _panel_file(), _panel_load() (+5 more)

### Community 21 - "S&P 500 Backtests"
Cohesion: 0.11
Nodes (13): br_backtest(), all_symbols(), download_ohlcv(), nasdaq100(), search(), sp500_table(), tbill_yields(), ttm() (+5 more)

### Community 22 - "Membership & Intraday Data"
Cohesion: 0.12
Nodes (12): alpaca_bars(), chunk(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _parse_spells(), _session() (+4 more)

### Community 23 - "Breakout Rider Strategy"
Cohesion: 0.20
Nodes (8): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate()

### Community 24 - "Setup Views"
Cohesion: 0.20
Nodes (14): overview(), switch_strip(), _fmt(), breakout_setup(), swing_rule_setup(), card(), checklist(), _finite() (+6 more)

### Community 25 - "Swing Engine"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 26 - "Factor Scores"
Cohesion: 0.23
Nodes (9): composite_scores(), explain(), price_factor_frame(), sector_neutral_z(), winsorize(), zscore(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_could_run_screen() (+1 more)

### Community 27 - "Core Unit Tests"
Cohesion: 0.15
Nodes (14): _earn_table(), _ohlc(), test_builder_fills_next_open_and_stops(), test_core_long_screen_filters_value_traps(), test_drawdown_simple(), test_earnings_beat_flag(), test_earnings_factors_use_only_past_reports(), test_features_have_no_lookahead() (+6 more)

### Community 28 - "Support & Resistance Levels"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 29 - "Catalysts Page Wiring"
Cohesion: 0.27
Nodes (7): catalysts_view(), _filings(), render(), _tone_line(), esc(), metrics(), save_state()

### Community 30 - "Strategy Lab"
Cohesion: 0.24
Nodes (8): _add(), build_tab(), condition_rows(), _load(), _remove(), rules_key(), split_open_trade(), _value_step()

### Community 31 - "Scan Prefetch"
Cohesion: 0.20
Nodes (5): load_scan(), prefetch(), deco(), cached(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 32 - "Price Composite Backtest"
Cohesion: 0.22
Nodes (6): backtest_price_composite(), earnings_factor_frame(), _earnings_table(), fundamental_factor_frame(), test_factor_backtest_positive_ic(), test_factor_replay_with_earnings()

### Community 34 - "Leak Tests"
Cohesion: 0.29
Nodes (6): _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_folds_slide_and_never_overlap(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled()

### Community 35 - "Home Page Regime"
Cohesion: 0.38
Nodes (4): load_overview(), playbook_rows(), spy_regime(), tile()

### Community 36 - "Price Fetch Helpers"
Cohesion: 0.40
Nodes (4): _fetch_ohlcv(), _fetch_prices(), fetch(), _naive()

### Community 37 - "Intraday Cache TTL"
Cohesion: 0.40
Nodes (3): _intraday_ttl(), test_intraday_cache_is_short_while_the_market_is_open(), f()

### Community 38 - "Weight Presets"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

## Knowledge Gaps
- **8 isolated node(s):** `Shark Fin Over Waves Icon`, `Core Longs Screen`, `Could Run Screen`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)`, `GARCH(1,1) Filtered Historical Simulation` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 333 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Financials` connect `Valuation & Quality Scores` to `Price History Cache`, `Catalysts & Long Checklist`, `Market Data Fetching`, `Offline Test Fakes`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shark Fin Over Waves Icon`, `Core Longs Screen`, `Could Run Screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.06416275430359937 - nodes in this community are weakly interconnected._
- **Why does `_line()` connect `Valuation & Quality Scores` to `Live Signals`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Should `Scanner & Research Data` be split into smaller, more focused modules?**
  _Cohesion score 0.05641025641025641 - nodes in this community are weakly interconnected._
- **Why does `quality_points()` connect `Leader Dip Strategy` to `Swing Engine`, `Portfolio Risk`, `Live Signals`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._