# Graph Report - SharkFin  (2026-10-15)

## Corpus Check
- 52 files · ~99,284 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 1, .toml 1, .tgz 1)

## Summary
- 1024 nodes · 2717 edges · 36 communities (31 shown, 5 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 84 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a7417602`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- News & Playbook Pages
- Valuation & Long Checklist
- scanner.py
- pandas
- Portfolio Optimization
- Test Fakes & Harness
- Return Forecasting Models
- Docs & Feature History
- data.py
- Tech Breakout Rider
- indicators.py
- sentiment.py
- Live Strategy Signals
- builder.py
- json
- test_core.py
- swing.py
- Strategy Playbook Mix
- ttl_cache
- home.py
- old-version-dec-2025/main.py
- Alpaca & Earnings Cache
- Old Research Page
- Old Utils & News
- Macro & Regime Data
- Old Prediction Page
- swing_tab
- Old Top Performers
- Caching & Prefetch
- Old Portfolio Page
- test_swing_choice_rules_and_status
- intraday_bars
- top_performers_page.py
- Old Logo
- Current Logo

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 34 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 23 edges
6. `quality_metrics()` - 22 edges
7. `plan_view()` - 20 edges
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

## Communities (36 total, 5 thin omitted)

### Community 0 - "News & Playbook Pages"
Cohesion: 0.06
Nodes (65): catalysts_view(), _filings(), render(), _tone_line(), backtest_summary(), br_signals(), breakout_view(), day_night_view() (+57 more)

### Community 1 - "Valuation & Long Checklist"
Cohesion: 0.06
Nodes (28): net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices(), justified_pb_value() (+20 more)

### Community 2 - "scanner.py"
Cohesion: 0.19
Nodes (13): factor_backtest(), get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals() (+5 more)

### Community 3 - "pandas"
Cohesion: 0.06
Nodes (34): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), could_run_tab(), _col(), core_long_checklist() (+26 more)

### Community 4 - "Portfolio Optimization"
Cohesion: 0.07
Nodes (32): compare(), positions(), run(), Strategy, _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns() (+24 more)

### Community 5 - "Test Fakes & Harness"
Cohesion: 0.05
Nodes (39): reload_changed_sharkfin(), make_ohlcv(), ohlcv(), price_panel(), analyst_data(), _base_info(), download_ohlcv(), download_prices() (+31 more)

### Community 6 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 7 - "Docs & Feature History"
Cohesion: 0.07
Nodes (34): SharkFin Old Version (Dec 2025) README, calculate_rsi (simple-average RSI, old), Portfolio Management (JSON storage, old), 4-Model Prediction System (old), Random Forest Price Model (old), Research Center (old), TF-IDF News Relevance Scoring (old), Top Performers Scanner (old) (+26 more)

### Community 8 - "data.py"
Cohesion: 0.11
Nodes (14): html_to_text(), _copy(), _edgar_filings(), _is_empty(), market_status(), nasdaq100(), news(), _NYSECalendar (+6 more)

### Community 9 - "Tech Breakout Rider"
Cohesion: 0.06
Nodes (20): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), backtest(), bands() (+12 more)

### Community 10 - "indicators.py"
Cohesion: 0.06
Nodes (43): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), hurst_exponent() (+35 more)

### Community 11 - "sentiment.py"
Cohesion: 0.14
Nodes (12): aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles(), score_text() (+4 more)

### Community 12 - "Live Strategy Signals"
Cohesion: 0.12
Nodes (16): br_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), market_history(), sp500_table(), universe(), breakout_today() (+8 more)

### Community 13 - "builder.py"
Cohesion: 0.19
Nodes (13): _close(), compare_templates(), condition_mask(), Indicator, _market_gap(), _obv_gap(), run(), series() (+5 more)

### Community 14 - "json"
Cohesion: 0.25
Nodes (5): save_data(), api_key(), available(), _default(), stream_report()

### Community 15 - "test_core.py"
Cohesion: 0.06
Nodes (36): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), fundamental_factor_frame(), price_factor_frame(), sector_neutral_z() (+28 more)

### Community 16 - "swing.py"
Cohesion: 0.19
Nodes (8): describe(), describe_strategy(), _fmt_value(), label(), _frame(), rule_checks(), scan(), stock_status()

### Community 17 - "Strategy Playbook Mix"
Cohesion: 0.16
Nodes (12): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+4 more)

### Community 18 - "ttl_cache"
Cohesion: 0.15
Nodes (14): scan_data(), all_symbols(), analyst_data(), earnings_histories(), earnings_history(), financials(), industry_members(), info() (+6 more)

### Community 19 - "home.py"
Cohesion: 0.20
Nodes (7): load_overview(), playbook_rows(), spy_regime(), tile(), download_prices(), fetch(), _naive()

### Community 21 - "Alpaca & Earnings Cache"
Cohesion: 0.29
Nodes (7): _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), sec_filings(), _yahoo_filings(), f(), test_saved_earnings_are_reused_until_the_next_report()

### Community 22 - "Old Research Page"
Cohesion: 0.18
Nodes (4): ResearchPage, format_time_ago(), generate_article_summary(), get_news_from_api()

### Community 23 - "Old Utils & News"
Cohesion: 0.13
Nodes (8): calculate_article_relevance(), calculate_bollinger_bands(), calculate_macd(), get_all_symbols(), get_nasdaq100_symbols(), get_news_from_yahoo(), get_sp500_symbols(), search_news_google()

### Community 24 - "Macro & Regime Data"
Cohesion: 0.22
Nodes (6): dn_backtest(), alpaca_daily(), history(), risk_free_rate(), tbill_yields(), ttm()

### Community 25 - "Old Prediction Page"
Cohesion: 0.21
Nodes (3): PredictionPage, create_forecast_chart(), search_stock_symbol()

### Community 26 - "swing_tab"
Cohesion: 0.23
Nodes (9): breakout_tab(), swing_tab(), about(), choices(), _load(), my_swing_rules(), _path(), swing_choice() (+1 more)

### Community 28 - "Caching & Prefetch"
Cohesion: 0.20
Nodes (5): load_scan(), prefetch(), deco(), cached(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 30 - "test_swing_choice_rules_and_status"
Cohesion: 0.25
Nodes (7): _add(), C(), clean(), rules(), _ohlc(), test_builder_fills_next_open_and_stops(), test_swing_choice_rules_and_status()

### Community 31 - "intraday_bars"
Cohesion: 0.18
Nodes (8): alpaca_bars(), chunk(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _session(), day_night_today()

### Community 34 - "Old Logo"
Cohesion: 0.50
Nodes (3): SharkFin Logo (Dec 2025), Shark Fin Over Waves Emblem, SharkFin Wordmark with Stock-Chart 'i'

### Community 35 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

## Knowledge Gaps
- **10 isolated node(s):** `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon`, `calculate_rsi (simple-average RSI, old)`, `Random Forest Price Model (old)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 327 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `tbill_yields()` connect `Macro & Regime Data` to `data.py`, `ttl_cache`, `pandas`, `Live Strategy Signals`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shark Fin Over Waves Emblem`, `SharkFin Wordmark with Stock-Chart 'i'`, `Shark Fin Over Waves Icon` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `News & Playbook Pages` be split into smaller, more focused modules?**
  _Cohesion score 0.057373737373737375 - nodes in this community are weakly interconnected._
- **Why does `today()` connect `Tech Breakout Rider` to `pandas`, `Portfolio Optimization`, `intraday_bars`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Should `Valuation & Long Checklist` be split into smaller, more focused modules?**
  _Cohesion score 0.06416275430359937 - nodes in this community are weakly interconnected._
- **Why does `_line()` connect `Valuation & Long Checklist` to `pandas`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._