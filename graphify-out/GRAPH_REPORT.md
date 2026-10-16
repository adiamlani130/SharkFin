# Graph Report - SharkFin  (2026-10-16)

## Corpus Check
- 55 files · ~106,901 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: .csv 2, (none) 1, .toml 1)

## Summary
- 1151 nodes · 3093 edges · 49 communities (42 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 98 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `56fdded0`
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
- pandas
- json
- pandas
- builder.py
- strategy_lab.py
- test_core.py
- leader_dip.py
- sharkfin/playbook.py
- test_leaks.py
- sharkfin/__init__.py
- old-version-dec-2025/main.py
- DataFrame
- research_page.py
- utils.py
- _fetch_prices
- prediction_page.py
- ui.py
- TopPerformersPage
- Caching & Prefetch
- create_candlestick_chart
- breakout_setup
- home.py
- ratings.py
- SharkFin Logo (Dec 2025)
- Current Logo
- ttl_cache
- top_performers_page.py
- factors.py
- backtest_price_composite
- _cached_panel
- run
- streamlit
- .mcp.json
- levels.py
- swing.py
- _intraday_ttl
- ai.py

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
- `Research Center (old)` --semantically_similar_to--> `Research & Valuation Page`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `Top Performers Scanner (old)` --semantically_similar_to--> `Top Performers Page`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `Portfolio Management (JSON storage, old)` --semantically_similar_to--> `Portfolio Page (Risk + Optimizer)`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `4-Model Prediction System (old)` --semantically_similar_to--> `Forecasts Page (Walk-forward Ensemble)`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `TF-IDF News Relevance Scoring (old)` --semantically_similar_to--> `News Page`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Combined plan of three researched swing/intraday strategies** — readme_combined_plan, readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night [EXTRACTED 1.00]
- **Pages that consume the user's chosen swing strategy** — readme_top_performers, readme_trade_setup, readme_strategy_lab, readme_leader_dip_plus_7, readme_tech_breakout_rider [EXTRACTED 1.00]
- **Dec 2025 features superseded by current SharkFin pages** — old_version_dec_2025_readme_prediction_models, old_version_dec_2025_readme_top_performers_scanner, old_version_dec_2025_readme_tfidf_news_relevance, readme_forecasts, readme_top_performers, readme_news_page [INFERRED 0.75]

## Communities (49 total, 7 thin omitted)

### Community 0 - "streamlit"
Cohesion: 0.23
Nodes (15): backtest_summary(), br_signals(), breakout_view(), day_night_view(), kpis(), ld_signals(), leader_dip_view(), pct() (+7 more)

### Community 1 - "Valuation & Long Checklist"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 2 - "scanner.py"
Cohesion: 0.19
Nodes (12): get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals(), scan() (+4 more)

### Community 3 - "catalysts.py"
Cohesion: 0.06
Nodes (34): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), insider_summary() (+26 more)

### Community 4 - "Portfolio Optimization"
Cohesion: 0.07
Nodes (31): market_beta(), _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance() (+23 more)

### Community 5 - "test_app.py"
Cohesion: 0.08
Nodes (38): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+30 more)

### Community 6 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 7 - "Docs & Feature History"
Cohesion: 0.07
Nodes (34): SharkFin Old Version (Dec 2025) README, calculate_rsi (simple-average RSI, old), Portfolio Management (JSON storage, old), 4-Model Prediction System (old), Random Forest Price Model (old), Research Center (old), TF-IDF News Relevance Scoring (old), Top Performers Scanner (old) (+26 more)

### Community 8 - "data.py"
Cohesion: 0.12
Nodes (13): html_to_text(), _edgar_filings(), market_status(), news(), _NYSECalendar, _parse_date(), _rss(), sec_cik() (+5 more)

### Community 9 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 10 - "pandas"
Cohesion: 0.08
Nodes (30): compare(), positions(), run(), Strategy, build_features(), adx(), atr(), bollinger() (+22 more)

### Community 11 - "json"
Cohesion: 0.22
Nodes (9): swing_tab(), save_data(), about(), choices(), _load(), my_swing_rules(), _path(), swing_choice() (+1 more)

### Community 12 - "pandas"
Cohesion: 0.09
Nodes (25): br_backtest(), dn_backtest(), ld_backtest(), breakout_tab(), leader_dip_run(), tech_universe(), download_ohlcv(), last_years() (+17 more)

### Community 13 - "builder.py"
Cohesion: 0.15
Nodes (14): _add(), C(), _close(), describe(), describe_strategy(), _fmt_value(), Indicator, knobs() (+6 more)

### Community 14 - "strategy_lab.py"
Cohesion: 0.31
Nodes (6): build_tab(), condition_rows(), _remove(), rules_key(), split_open_trade(), _value_step()

### Community 15 - "test_core.py"
Cohesion: 0.10
Nodes (18): fair_value_summary(), forward_growth(), _earn_table(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports() (+10 more)

### Community 16 - "leader_dip.py"
Cohesion: 0.12
Nodes (19): _align(), backtest(), _band(), latest(), market_on(), _members(), percentile_against(), plus_frames() (+11 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (15): plan_view(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+7 more)

### Community 18 - "test_leaks.py"
Cohesion: 0.05
Nodes (29): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), walk_forward(), evaluate(), daily_cash() (+21 more)

### Community 21 - "DataFrame"
Cohesion: 0.15
Nodes (10): spy_regime(), lab_walk_forward(), alpaca_bars(), alpaca_daily(), alpaca_keys(), history(), intraday_bars(), market_history() (+2 more)

### Community 22 - "research_page.py"
Cohesion: 0.18
Nodes (4): ResearchPage, format_time_ago(), generate_article_summary(), get_news_from_api()

### Community 23 - "utils.py"
Cohesion: 0.13
Nodes (8): calculate_article_relevance(), calculate_bollinger_bands(), calculate_macd(), get_all_symbols(), get_nasdaq100_symbols(), get_news_from_yahoo(), get_sp500_symbols(), search_news_google()

### Community 24 - "_fetch_prices"
Cohesion: 0.40
Nodes (4): _fetch_ohlcv(), _fetch_prices(), fetch(), _naive()

### Community 25 - "prediction_page.py"
Cohesion: 0.21
Nodes (3): PredictionPage, create_forecast_chart(), search_stock_symbol()

### Community 26 - "ui.py"
Cohesion: 0.10
Nodes (19): clean_text(), asset(), compact_frame(), disclaimer(), _finite(), fmt_big(), fmt_x(), header() (+11 more)

### Community 28 - "Caching & Prefetch"
Cohesion: 0.14
Nodes (8): load_scan(), _copy(), _is_empty(), prefetch(), deco(), cached(), wrapper(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 30 - "breakout_setup"
Cohesion: 0.22
Nodes (15): dn_today(), overview(), switch_strip(), _fmt(), breakout_setup(), swing_rule_setup(), card(), leader_dip_tab() (+7 more)

### Community 31 - "home.py"
Cohesion: 0.22
Nodes (5): load_overview(), playbook_rows(), tile(), latest_trade(), day_night_today()

### Community 32 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 34 - "SharkFin Logo (Dec 2025)"
Cohesion: 0.50
Nodes (3): SharkFin Logo (Dec 2025), Shark Fin Over Waves Emblem, SharkFin Wordmark with Stock-Chart 'i'

### Community 35 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 37 - "ttl_cache"
Cohesion: 0.09
Nodes (23): index_panel(), peer_table(), sector_etf_prices(), stock_ratings(), factor_backtest(), scan_data(), all_symbols(), analyst_data() (+15 more)

### Community 39 - "factors.py"
Cohesion: 0.24
Nodes (8): composite_scores(), explain(), price_factor_frame(), sector_neutral_z(), winsorize(), zscore(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_factor_composite_ranks_planted_winners()

### Community 40 - "backtest_price_composite"
Cohesion: 0.19
Nodes (7): backtest_price_composite(), earnings_factor_frame(), _earnings_table(), walk_forward(), evaluate(), weight_presets(), test_factor_backtest_positive_ic()

### Community 41 - "_cached_panel"
Cohesion: 0.14
Nodes (14): chunk(), _alpaca_get(), _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), _panel_file() (+6 more)

### Community 42 - "run"
Cohesion: 0.16
Nodes (12): compare_templates(), condition_mask(), _market_gap(), run(), series(), signals(), summarize(), warmup() (+4 more)

### Community 43 - "streamlit"
Cohesion: 0.18
Nodes (10): catalysts_view(), _filings(), render(), _tone_line(), esc(), hero(), metrics(), num() (+2 more)

### Community 44 - ".mcp.json"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 45 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 46 - "swing.py"
Cohesion: 0.19
Nodes (9): _load(), template(), clean(), _frame(), rule_checks(), rules(), scan(), stock_status() (+1 more)

### Community 47 - "_intraday_ttl"
Cohesion: 0.40
Nodes (3): _intraday_ttl(), test_intraday_cache_is_short_while_the_market_is_open(), f()

### Community 49 - "ai.py"
Cohesion: 0.31
Nodes (4): api_key(), available(), _default(), stream_report()

## Knowledge Gaps
- **10 isolated node(s):** `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon`, `calculate_rsi (simple-average RSI, old)`, `Random Forest Price Model (old)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 373 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_candlestick_chart()` connect `create_candlestick_chart` to `utils.py`, `breakout_setup`, `top_performers_page.py`, `research_page.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Long Checklist` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `simulate_garch_paths()` connect `Return Forecasting Models` to `Portfolio Optimization`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `catalysts.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05649717514124294 - nodes in this community are weakly interconnected._
- **Should `Portfolio Optimization` be split into smaller, more focused modules?**
  _Cohesion score 0.07377049180327869 - nodes in this community are weakly interconnected._