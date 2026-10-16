# Graph Report - SharkFin  (2026-10-15)

## Corpus Check
- 55 files · ~105,958 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: .csv 2, (none) 1, .toml 1)

## Summary
- 1135 nodes · 3055 edges · 54 communities (47 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 97 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `31ffbff3`
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
- sentiment.py
- Live Strategy Signals
- builder.py
- research.py
- test_core.py
- leader_dip.py
- sharkfin/playbook.py
- walkforward.py
- sharkfin/__init__.py
- old-version-dec-2025/main.py
- DataFrame
- Old Research Page
- Old Utils & News
- history
- Old Prediction Page
- ui.py
- Old Top Performers
- Caching & Prefetch
- Old Portfolio Page
- breakout_setup
- leader_dip_run
- ratings.py
- daily_cash
- Old Logo
- Current Logo
- ttl_cache
- breakout_rider.py
- factors.py
- backtest_price_composite
- _cached_panel
- run
- news.py
- .mcp.json
- levels.py
- swing.py
- backtest.py
- test_swing_choice_rules_and_status
- ai.py
- rsi
- carry_forward
- hurst_exponent
- forward_growth

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 35 edges
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

## Communities (54 total, 7 thin omitted)

### Community 0 - "streamlit"
Cohesion: 0.24
Nodes (18): backtest_summary(), br_signals(), breakout_view(), day_night_view(), dn_today(), kpis(), ld_signals(), leader_dip_view() (+10 more)

### Community 1 - "Valuation & Long Checklist"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 2 - "scanner.py"
Cohesion: 0.17
Nodes (15): breakout_tab(), factor_backtest(), get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab() (+7 more)

### Community 3 - "catalysts.py"
Cohesion: 0.05
Nodes (43): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), insider_summary() (+35 more)

### Community 4 - "Portfolio Optimization"
Cohesion: 0.07
Nodes (31): summarize(), _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance() (+23 more)

### Community 5 - "test_app.py"
Cohesion: 0.17
Nodes (19): offline(), _ok(), _page(), _scanned(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders(), test_playbook_every_view_and_scan() (+11 more)

### Community 6 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 7 - "Docs & Feature History"
Cohesion: 0.07
Nodes (34): SharkFin Old Version (Dec 2025) README, calculate_rsi (simple-average RSI, old), Portfolio Management (JSON storage, old), 4-Model Prediction System (old), Random Forest Price Model (old), Research Center (old), TF-IDF News Relevance Scoring (old), Top Performers Scanner (old) (+26 more)

### Community 8 - "data.py"
Cohesion: 0.11
Nodes (13): html_to_text(), _copy(), _edgar_filings(), _is_empty(), market_status(), news(), _NYSECalendar, _parse_date() (+5 more)

### Community 9 - "day_night.py"
Cohesion: 0.14
Nodes (13): backtest(), bands(), close_location(), day_leg(), decision_location(), leg_stats(), night_leg(), session_matrix() (+5 more)

### Community 10 - "pandas"
Cohesion: 0.17
Nodes (18): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+10 more)

### Community 11 - "sentiment.py"
Cohesion: 0.14
Nodes (12): aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles(), score_text() (+4 more)

### Community 12 - "Live Strategy Signals"
Cohesion: 0.11
Nodes (15): load_overview(), playbook_rows(), spy_regime(), tile(), breakout_today(), day_night_today(), leader_dip_today(), market_inputs() (+7 more)

### Community 13 - "builder.py"
Cohesion: 0.17
Nodes (12): _close(), describe(), describe_strategy(), _fmt_value(), Indicator, knobs(), label(), _obv_gap() (+4 more)

### Community 14 - "research.py"
Cohesion: 0.16
Nodes (10): _fmt(), build_tab(), condition_rows(), leader_dip_tab(), _remove(), rules_key(), split_open_trade(), _value_step() (+2 more)

### Community 15 - "test_core.py"
Cohesion: 0.13
Nodes (16): fair_value_summary(), _earn_table(), _panel(), test_drawdown_simple(), test_earnings_beat_flag(), test_earnings_factors_use_only_past_reports(), test_fair_value_blend(), test_features_have_no_lookahead() (+8 more)

### Community 16 - "leader_dip.py"
Cohesion: 0.13
Nodes (19): sma(), _align(), backtest(), _band(), latest(), market_on(), _members(), percentile_against() (+11 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (15): plan_view(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+7 more)

### Community 18 - "walkforward.py"
Cohesion: 0.11
Nodes (13): cut(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 21 - "DataFrame"
Cohesion: 0.13
Nodes (12): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _parse_spells() (+4 more)

### Community 22 - "Old Research Page"
Cohesion: 0.20
Nodes (3): ResearchPage, format_time_ago(), generate_article_summary()

### Community 23 - "Old Utils & News"
Cohesion: 0.17
Nodes (6): calculate_article_relevance(), calculate_bollinger_bands(), calculate_macd(), get_news_from_api(), get_news_from_yahoo(), search_news_google()

### Community 24 - "history"
Cohesion: 0.17
Nodes (8): lab_walk_forward(), _fetch_ohlcv(), _fetch_prices(), fetch(), history(), market_history(), _naive(), risk_free_rate()

### Community 25 - "Old Prediction Page"
Cohesion: 0.17
Nodes (4): PredictionPage, calculate_rsi(), create_forecast_chart(), search_stock_symbol()

### Community 26 - "ui.py"
Cohesion: 0.11
Nodes (21): clean_text(), choices(), asset(), disclaimer(), header(), hero(), init_state(), _load() (+13 more)

### Community 27 - "Old Top Performers"
Cohesion: 0.17
Nodes (4): TopPerformersPage, get_all_symbols(), get_nasdaq100_symbols(), get_sp500_symbols()

### Community 28 - "Caching & Prefetch"
Cohesion: 0.20
Nodes (5): load_scan(), prefetch(), deco(), cached(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 30 - "breakout_setup"
Cohesion: 0.16
Nodes (15): catalysts_view(), _filings(), switch_strip(), breakout_setup(), swing_rule_setup(), card(), checklist(), esc() (+7 more)

### Community 31 - "leader_dip_run"
Cohesion: 0.13
Nodes (13): br_backtest(), dn_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), last_years(), sp500_ever(), sp500_members() (+5 more)

### Community 32 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 33 - "daily_cash"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 34 - "Old Logo"
Cohesion: 0.50
Nodes (3): SharkFin Logo (Dec 2025), Shark Fin Over Waves Emblem, SharkFin Wordmark with Stock-Chart 'i'

### Community 35 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 37 - "ttl_cache"
Cohesion: 0.10
Nodes (23): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), scan_data(), all_symbols(), analyst_data() (+15 more)

### Community 38 - "breakout_rider.py"
Cohesion: 0.20
Nodes (8): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate()

### Community 39 - "factors.py"
Cohesion: 0.24
Nodes (8): composite_scores(), explain(), price_factor_frame(), sector_neutral_z(), winsorize(), zscore(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_factor_composite_ranks_planted_winners()

### Community 40 - "backtest_price_composite"
Cohesion: 0.16
Nodes (8): backtest_price_composite(), earnings_factor_frame(), _earnings_table(), fundamental_factor_frame(), walk_forward(), evaluate(), weight_presets(), test_factor_backtest_positive_ic()

### Community 41 - "_cached_panel"
Cohesion: 0.16
Nodes (12): save_data(), _cached_panel(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), _panel_file(), _panel_load(), _panel_save() (+4 more)

### Community 42 - "run"
Cohesion: 0.21
Nodes (9): compare_templates(), condition_mask(), run(), series(), signals(), warmup(), _ohlc(), test_builder_fills_next_open_and_stops() (+1 more)

### Community 43 - "news.py"
Cohesion: 0.20
Nodes (7): render(), _tone_line(), compact_frame(), _finite(), fmt_big(), fmt_x(), tone()

### Community 44 - ".mcp.json"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 45 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 46 - "swing.py"
Cohesion: 0.27
Nodes (5): about(), _frame(), rule_checks(), scan(), stock_status()

### Community 47 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 48 - "test_swing_choice_rules_and_status"
Cohesion: 0.28
Nodes (7): _add(), _load(), C(), template(), clean(), rules(), test_swing_choice_rules_and_status()

### Community 49 - "ai.py"
Cohesion: 0.31
Nodes (4): api_key(), available(), _default(), stream_report()

### Community 50 - "rsi"
Cohesion: 0.25
Nodes (3): rsi(), follow_up(), price_chart()

## Knowledge Gaps
- **10 isolated node(s):** `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon`, `calculate_rsi (simple-average RSI, old)`, `Random Forest Price Model (old)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 367 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_line()` connect `Valuation & Long Checklist` to `pandas`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Long Checklist` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `scan()` connect `swing.py` to `test_swing_choice_rules_and_status`, `scanner.py`, `pandas`, `run`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Should `catalysts.py` be split into smaller, more focused modules?**
  _Cohesion score 0.052917232021709636 - nodes in this community are weakly interconnected._
- **Why does `quality_metrics()` connect `Valuation & Long Checklist` to `Portfolio Optimization`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._