# Graph Report - SharkFin  (2026-10-15)

## Corpus Check
- 55 files · ~104,750 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: .csv 2, (none) 1, .toml 1)

## Summary
- 1118 nodes · 3006 edges · 47 communities (40 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 93 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8cdb2495`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- streamlit
- Valuation & Long Checklist
- scanner.py
- pandas
- Portfolio Optimization
- test_app.py
- Return Forecasting Models
- Docs & Feature History
- data.py
- day_night.py
- indicators.py
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
- fakes.py
- top_performers_page.py
- daily_cash
- Old Logo
- Current Logo
- sp500_table
- breakout_rider.py
- factors.py
- backtest_price_composite
- test_leaks.py
- pill
- _finite
- .mcp.json
- _NYSECalendar
- earnings_history

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

## Communities (47 total, 7 thin omitted)

### Community 0 - "streamlit"
Cohesion: 0.20
Nodes (22): backtest_summary(), br_backtest(), br_signals(), breakout_view(), day_night_view(), dn_backtest(), dn_today(), kpis() (+14 more)

### Community 1 - "Valuation & Long Checklist"
Cohesion: 0.06
Nodes (29): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+21 more)

### Community 2 - "scanner.py"
Cohesion: 0.17
Nodes (15): breakout_tab(), factor_backtest(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+7 more)

### Community 3 - "pandas"
Cohesion: 0.07
Nodes (31): catalysts_view(), could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change() (+23 more)

### Community 4 - "Portfolio Optimization"
Cohesion: 0.07
Nodes (31): market_beta(), _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance() (+23 more)

### Community 5 - "test_app.py"
Cohesion: 0.19
Nodes (18): _ok(), _page(), _scanned(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders(), test_playbook_every_view_and_scan(), test_research_trade_setup_tab() (+10 more)

### Community 6 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (16): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+8 more)

### Community 7 - "Docs & Feature History"
Cohesion: 0.07
Nodes (34): SharkFin Old Version (Dec 2025) README, calculate_rsi (simple-average RSI, old), Portfolio Management (JSON storage, old), 4-Model Prediction System (old), Random Forest Price Model (old), Research Center (old), TF-IDF News Relevance Scoring (old), Top Performers Scanner (old) (+26 more)

### Community 8 - "data.py"
Cohesion: 0.10
Nodes (24): html_to_text(), all_symbols(), analyst_data(), _copy(), earnings_history(), _edgar_filings(), financials(), industry_members() (+16 more)

### Community 9 - "day_night.py"
Cohesion: 0.13
Nodes (14): backtest(), bands(), close_location(), day_leg(), decision_location(), leg_stats(), night_leg(), session_matrix() (+6 more)

### Community 10 - "indicators.py"
Cohesion: 0.07
Nodes (33): compare(), positions(), run(), Strategy, build_features(), adx(), atr(), bollinger() (+25 more)

### Community 11 - "sentiment.py"
Cohesion: 0.14
Nodes (12): aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles(), score_text() (+4 more)

### Community 12 - "Live Strategy Signals"
Cohesion: 0.14
Nodes (12): ld_backtest(), download_ohlcv(), breakout_today(), leader_dip_today(), market_inputs(), sector_map(), sector_ret3(), sp500_ohlcv() (+4 more)

### Community 13 - "builder.py"
Cohesion: 0.07
Nodes (34): _add(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value() (+26 more)

### Community 14 - "research.py"
Cohesion: 0.14
Nodes (12): _fmt(), build_tab(), condition_rows(), leader_dip_tab(), _load(), _remove(), rules_key(), split_open_trade() (+4 more)

### Community 15 - "test_core.py"
Cohesion: 0.10
Nodes (18): fair_value_summary(), forward_growth(), _earn_table(), test_core_long_screen_filters_value_traps(), test_drawdown_simple(), test_earnings_beat_flag(), test_earnings_factors_use_only_past_reports(), test_ensemble_forecast_is_deterministic_and_coherent() (+10 more)

### Community 16 - "leader_dip.py"
Cohesion: 0.10
Nodes (26): _market_gap(), sma(), _align(), backtest(), _band(), follow_up(), latest(), market_on() (+18 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.07
Nodes (18): reload_changed_sharkfin(), api_key(), available(), _default(), stream_report(), best_weights(), correlations(), drawdowns() (+10 more)

### Community 18 - "walkforward.py"
Cohesion: 0.11
Nodes (12): cut(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+4 more)

### Community 19 - "sharkfin/__init__.py"
Cohesion: 0.13
Nodes (8): load_overview(), playbook_rows(), tile(), chunk(), _alpaca_get(), alpaca_keys(), latest_trade(), day_night_today()

### Community 21 - "DataFrame"
Cohesion: 0.12
Nodes (14): alpaca_bars(), alpaca_daily(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), intraday_bars(), _parse_spells(), _session() (+6 more)

### Community 22 - "Old Research Page"
Cohesion: 0.18
Nodes (4): ResearchPage, format_time_ago(), generate_article_summary(), get_news_from_api()

### Community 23 - "Old Utils & News"
Cohesion: 0.13
Nodes (8): calculate_article_relevance(), calculate_bollinger_bands(), calculate_macd(), get_all_symbols(), get_nasdaq100_symbols(), get_news_from_yahoo(), get_sp500_symbols(), search_news_google()

### Community 24 - "history"
Cohesion: 0.16
Nodes (9): spy_regime(), lab_walk_forward(), leader_dip_run(), history(), market_history(), _naive(), risk_free_rate(), tbill_yields() (+1 more)

### Community 25 - "Old Prediction Page"
Cohesion: 0.21
Nodes (3): PredictionPage, create_forecast_chart(), search_stock_symbol()

### Community 26 - "ui.py"
Cohesion: 0.12
Nodes (16): asset(), disclaimer(), init_state(), _load(), load_list(), my_swing_rules(), num(), _path() (+8 more)

### Community 28 - "Caching & Prefetch"
Cohesion: 0.17
Nodes (7): load_scan(), _is_empty(), prefetch(), deco(), cached(), wrapper(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 30 - "breakout_setup"
Cohesion: 0.13
Nodes (14): _filings(), switch_strip(), breakout_setup(), swing_rule_setup(), card(), tech_universe(), checklist(), esc() (+6 more)

### Community 31 - "fakes.py"
Cohesion: 0.16
Nodes (16): analyst_data(), _base_info(), download_ohlcv(), download_prices(), financials(), history(), info(), install() (+8 more)

### Community 33 - "daily_cash"
Cohesion: 0.15
Nodes (6): daily_cash(), panel_adx(), panel_atr(), run(), stats(), test_cash_before_the_first_yield_is_not_back_filled()

### Community 34 - "Old Logo"
Cohesion: 0.50
Nodes (3): SharkFin Logo (Dec 2025), Shark Fin Over Waves Emblem, SharkFin Wordmark with Stock-Chart 'i'

### Community 35 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 37 - "sp500_table"
Cohesion: 0.15
Nodes (10): index_panel(), peer_table(), sector_etf_prices(), stock_ratings(), get_universe(), download_prices(), fetch(), nasdaq100() (+2 more)

### Community 38 - "breakout_rider.py"
Cohesion: 0.23
Nodes (7): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), walk_forward(), evaluate()

### Community 39 - "factors.py"
Cohesion: 0.23
Nodes (9): composite_scores(), explain(), price_factor_frame(), sector_neutral_z(), winsorize(), zscore(), test_composite_adds_earnings_theme_and_drops_zero_weight_themes(), test_could_run_screen() (+1 more)

### Community 40 - "backtest_price_composite"
Cohesion: 0.16
Nodes (8): backtest_price_composite(), earnings_factor_frame(), _earnings_table(), fundamental_factor_frame(), walk_forward(), evaluate(), weight_presets(), test_factor_backtest_positive_ic()

### Community 41 - "test_leaks.py"
Cohesion: 0.29
Nodes (6): _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_folds_slide_and_never_overlap(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count(), test_negative_shifts_are_only_trade_outcomes(), test_nothing_is_back_filled()

### Community 42 - "pill"
Cohesion: 0.31
Nodes (8): render(), _tone_line(), clean_text(), header(), news_item(), pill(), time_ago(), tone()

### Community 43 - "_finite"
Cohesion: 0.29
Nodes (4): compact_frame(), _finite(), fmt_big(), fmt_x()

### Community 44 - ".mcp.json"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

## Knowledge Gaps
- **10 isolated node(s):** `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon`, `calculate_rsi (simple-average RSI, old)`, `Random Forest Price Model (old)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 362 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_line()` connect `Valuation & Long Checklist` to `pandas`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Long Checklist` be split into smaller, more focused modules?**
  _Cohesion score 0.0609009009009009 - nodes in this community are weakly interconnected._
- **Why does `build_tab()` connect `research.py` to `streamlit`, `pandas`, `Portfolio Optimization`, `builder.py`, `history`, `ui.py`, `breakout_setup`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Should `pandas` be split into smaller, more focused modules?**
  _Cohesion score 0.06610169491525424 - nodes in this community are weakly interconnected._
- **Why does `create_candlestick_chart()` connect `Old Portfolio Page` to `top_performers_page.py`, `streamlit`, `Old Research Page`, `Old Utils & News`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._