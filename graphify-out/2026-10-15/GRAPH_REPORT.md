# Graph Report - SharkFin  (2026-10-15)

## Corpus Check
- 54 files · ~97,210 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 1, .toml 1, .tgz 1)

## Summary
- 1016 nodes · 2706 edges · 37 communities (33 shown, 4 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 84 edges (avg confidence: 0.85)
- Token cost: 156,881 input · 0 output

## Community Hubs (Navigation)
- News & Playbook Pages
- Valuation & Long Checklist
- Scanner Page
- Catalysts & Screens
- Portfolio Optimization
- Test Fakes & Harness
- Return Forecasting Models
- Docs & Feature History
- Market Data Layer
- Tech Breakout Rider
- Leader Dip Strategy
- Technical Indicators
- Live Strategy Signals
- SharkFin Ratings
- App Entry & AI Analyst
- Factor Ranking
- Core Tests & Stats
- Strategy Playbook Mix
- Scan Data Loading
- TQQQ Day + Night
- Home & Market Status
- Alpaca & Earnings Cache
- Old Research Page
- Old Utils & News
- Macro & Regime Data
- Old Prediction Page
- Support/Resistance Levels
- Old Top Performers
- Caching & Prefetch
- Old Portfolio Page
- Backtest Engine
- Alpaca Realtime Trades
- Old Home Page
- Price Chart
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
- `Top Performers Scanner (old)` --semantically_similar_to--> `Top Performers Page`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `Research Center (old)` --semantically_similar_to--> `Research & Valuation Page`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `TF-IDF News Relevance Scoring (old)` --semantically_similar_to--> `News Page`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `4-Model Prediction System (old)` --semantically_similar_to--> `Forecasts Page (Walk-forward Ensemble)`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md
- `Portfolio Management (JSON storage, old)` --semantically_similar_to--> `Portfolio Page (Risk + Optimizer)`  [INFERRED] [semantically similar]
  old-version-dec-2025/README.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Combined plan of three researched swing/intraday strategies** — readme_combined_plan, readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night [EXTRACTED 1.00]
- **Pages that consume the user's chosen swing strategy** — readme_top_performers, readme_trade_setup, readme_strategy_lab, readme_leader_dip_plus_7, readme_tech_breakout_rider [EXTRACTED 1.00]
- **Dec 2025 features superseded by current SharkFin pages** — old_version_dec_2025_readme_prediction_models, old_version_dec_2025_readme_top_performers_scanner, old_version_dec_2025_readme_tfidf_news_relevance, readme_forecasts, readme_top_performers, readme_news_page [INFERRED 0.75]

## Communities (37 total, 4 thin omitted)

### Community 0 - "News & Playbook Pages"
Cohesion: 0.06
Nodes (64): catalysts_view(), _filings(), render(), _tone_line(), backtest_summary(), br_signals(), breakout_view(), day_night_view() (+56 more)

### Community 1 - "Valuation & Long Checklist"
Cohesion: 0.06
Nodes (31): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+23 more)

### Community 2 - "Scanner Page"
Cohesion: 0.05
Nodes (47): breakout_tab(), factor_backtest(), get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab() (+39 more)

### Community 3 - "Catalysts & Screens"
Cohesion: 0.06
Nodes (32): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+24 more)

### Community 4 - "Portfolio Optimization"
Cohesion: 0.09
Nodes (29): market_beta(), summarize(), _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe() (+21 more)

### Community 5 - "Test Fakes & Harness"
Cohesion: 0.08
Nodes (36): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+28 more)

### Community 6 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 7 - "Docs & Feature History"
Cohesion: 0.07
Nodes (34): SharkFin Old Version (Dec 2025) README, calculate_rsi (simple-average RSI, old), Portfolio Management (JSON storage, old), 4-Model Prediction System (old), Random Forest Price Model (old), Research Center (old), TF-IDF News Relevance Scoring (old), Top Performers Scanner (old) (+26 more)

### Community 8 - "Market Data Layer"
Cohesion: 0.12
Nodes (20): all_symbols(), analyst_data(), earnings_histories(), earnings_history(), _edgar_filings(), financials(), industry_members(), info() (+12 more)

### Community 9 - "Tech Breakout Rider"
Cohesion: 0.10
Nodes (11): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), daily_cash(), panel_adx() (+3 more)

### Community 10 - "Leader Dip Strategy"
Cohesion: 0.15
Nodes (16): sma(), _align(), backtest(), _band(), latest(), market_on(), percentile_against(), plus_frames() (+8 more)

### Community 11 - "Technical Indicators"
Cohesion: 0.17
Nodes (18): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+10 more)

### Community 12 - "Live Strategy Signals"
Cohesion: 0.13
Nodes (14): ld_backtest(), leader_dip_run(), download_ohlcv(), universe(), breakout_today(), leader_dip_today(), market_inputs(), sector_map() (+6 more)

### Community 13 - "SharkFin Ratings"
Cohesion: 0.13
Nodes (12): stock_ratings(), _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score() (+4 more)

### Community 14 - "App Entry & AI Analyst"
Cohesion: 0.10
Nodes (8): reload_changed_sharkfin(), api_key(), available(), _default(), stream_report(), make_ohlcv(), ohlcv(), price_panel()

### Community 15 - "Factor Ranking"
Cohesion: 0.14
Nodes (14): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), fundamental_factor_frame(), price_factor_frame(), sector_neutral_z() (+6 more)

### Community 16 - "Core Tests & Stats"
Cohesion: 0.11
Nodes (18): hurst_exponent(), rsi(), follow_up(), forward_growth(), _earn_table(), _panel(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports() (+10 more)

### Community 17 - "Strategy Playbook Mix"
Cohesion: 0.16
Nodes (12): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+4 more)

### Community 18 - "Scan Data Loading"
Cohesion: 0.12
Nodes (11): index_panel(), peer_table(), sector_etf_prices(), load_scan(), scan_data(), download_prices(), fetch(), infos() (+3 more)

### Community 19 - "TQQQ Day + Night"
Cohesion: 0.17
Nodes (9): backtest(), bands(), close_location(), day_leg(), leg_stats(), night_leg(), session_matrix(), today() (+1 more)

### Community 20 - "Home & Market Status"
Cohesion: 0.15
Nodes (4): market_status(), NYSECalendar, tile(), save_data()

### Community 21 - "Alpaca & Earnings Cache"
Cohesion: 0.16
Nodes (11): alpaca_bars(), alpaca_daily(), _earnings_fresh(), _earnings_from_disk(), _earnings_to_disk(), intraday_bars(), sec_filings(), _session() (+3 more)

### Community 22 - "Old Research Page"
Cohesion: 0.18
Nodes (3): ResearchPage, format_time_ago(), generate_article_summary()

### Community 23 - "Old Utils & News"
Cohesion: 0.17
Nodes (6): calculate_article_relevance(), calculate_bollinger_bands(), calculate_macd(), get_news_from_api(), get_news_from_yahoo(), search_news_google()

### Community 24 - "Macro & Regime Data"
Cohesion: 0.16
Nodes (9): load_overview(), spy_regime(), br_backtest(), dn_backtest(), history(), market_history(), risk_free_rate(), tbill_yields() (+1 more)

### Community 25 - "Old Prediction Page"
Cohesion: 0.17
Nodes (4): PredictionPage, calculate_rsi(), create_forecast_chart(), search_stock_symbol()

### Community 26 - "Support/Resistance Levels"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 27 - "Old Top Performers"
Cohesion: 0.17
Nodes (4): TopPerformersPage, get_all_symbols(), get_nasdaq100_symbols(), get_sp500_symbols()

### Community 28 - "Caching & Prefetch"
Cohesion: 0.17
Nodes (7): _copy(), _is_empty(), prefetch(), deco(), cached(), wrapper(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 30 - "Backtest Engine"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 31 - "Alpaca Realtime Trades"
Cohesion: 0.22
Nodes (6): playbook_rows(), chunk(), _alpaca_get(), alpaca_keys(), latest_trade(), day_night_today()

### Community 34 - "Old Logo"
Cohesion: 0.50
Nodes (3): SharkFin Logo (Dec 2025), Shark Fin Over Waves Emblem, SharkFin Wordmark with Stock-Chart 'i'

### Community 35 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

## Knowledge Gaps
- **10 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)`, `GARCH(1,1) Filtered Historical Simulation`, `SEC EDGAR Filings` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 323 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_tab()` connect `News & Playbook Pages` to `Macro & Regime Data`, `Scanner Page`, `Technical Indicators`, `Portfolio Optimization`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Core Longs Screen`, `Could Run Screen`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `News & Playbook Pages` be split into smaller, more focused modules?**
  _Cohesion score 0.0594059405940594 - nodes in this community are weakly interconnected._
- **Why does `_line()` connect `Valuation & Long Checklist` to `Technical Indicators`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Should `Valuation & Long Checklist` be split into smaller, more focused modules?**
  _Cohesion score 0.05727605727605728 - nodes in this community are weakly interconnected._
- **Why does `Financials` connect `Valuation & Long Checklist` to `Market Data Layer`, `Test Fakes & Harness`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._