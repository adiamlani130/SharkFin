# Graph Report - SharkFin  (2026-10-19)

## Corpus Check
- 54 files · ~105,452 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 20 file(s) not represented in the graph (top: .csv 18, (none) 1, .toml 1)

## Summary
- 1303 nodes · 3514 edges · 49 communities (46 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 105 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7af29e55`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- ratings.py
- streamlit
- Strategy Builder & Swing
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- risk.py
- Leader Dip Strategy
- ui.py
- day_night.py
- ttl_cache
- catalysts.py
- Playbook Page
- Market Data Fetching
- test_core.py
- Walk-Forward Engine
- sharkfin/playbook.py
- sharkfin/speculation.py
- download_prices
- sharkfin/portfolio.py
- pandas
- Membership & Intraday Data
- Breakout Rider Strategy
- Setup Views
- daily_cash
- nq_gex_plays.py
- fakes.py
- nq_lab.py
- Day
- Strategy Lab
- levels.py
- run
- sharkfin/__init__.py
- test_leaks.py
- research.py
- _cached_panel
- load_scan
- numpy
- home.py
- MCP Servers
- Current Logo
- opex_days
- Series
- Series
- Offline Test Design
- _intraday_ttl
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
10. `ema()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `stock_ratings()` --calls--> `to_gics()`  [EXTRACTED]
  app_pages/research.py → sharkfin/ratings.py
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py
- `swing_tab()` --calls--> `about()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/swing.py
- `stage_pill()` --calls--> `h()`  [EXTRACTED]
  app_pages/speculation.py → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (49 total, 3 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (28): net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices(), justified_pb_value() (+20 more)

### Community 1 - "ratings.py"
Cohesion: 0.09
Nodes (23): get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals(), scan() (+15 more)

### Community 2 - "streamlit"
Cohesion: 0.14
Nodes (15): catalysts_view(), _filings(), render(), _tone_line(), switch_strip(), esc(), header(), kv() (+7 more)

### Community 3 - "Strategy Builder & Swing"
Cohesion: 0.07
Nodes (33): _add(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value() (+25 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (18): run_forecast(), ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult (+10 more)

### Community 6 - "test_app.py"
Cohesion: 0.17
Nodes (19): offline(), _ok(), _page(), _scanned(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders(), test_playbook_every_view_and_scan() (+11 more)

### Community 7 - "risk.py"
Cohesion: 0.12
Nodes (19): compare(), positions(), run(), Strategy, annualized_return(), annualized_vol(), beta_alpha(), blume_adjusted_beta() (+11 more)

### Community 8 - "Leader Dip Strategy"
Cohesion: 0.06
Nodes (49): _market_gap(), build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema() (+41 more)

### Community 9 - "ui.py"
Cohesion: 0.11
Nodes (18): choices(), asset(), disclaimer(), hero(), init_state(), _load(), load_list(), my_swing_rules() (+10 more)

### Community 10 - "day_night.py"
Cohesion: 0.12
Nodes (17): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+9 more)

### Community 11 - "ttl_cache"
Cohesion: 0.15
Nodes (11): all_symbols(), download_ohlcv(), nasdaq100(), risk_free_rate(), search(), ttl_cache(), universe(), leader_dip_today() (+3 more)

### Community 12 - "catalysts.py"
Cohesion: 0.06
Nodes (33): could_run_tab(), _col(), core_long_checklist(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change() (+25 more)

### Community 13 - "Playbook Page"
Cohesion: 0.18
Nodes (19): backtest_summary(), br_signals(), breakout_view(), day_night_view(), dn_backtest(), dn_today(), kpis(), ld_signals() (+11 more)

### Community 14 - "Market Data Fetching"
Cohesion: 0.08
Nodes (23): html_to_text(), analyst_data(), _copy(), _edgar_filings(), _fetch_ohlcv(), _fetch_prices(), fetch(), financials() (+15 more)

### Community 15 - "test_core.py"
Cohesion: 0.06
Nodes (35): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), price_factor_frame(), sector_neutral_z(), walk_forward() (+27 more)

### Community 16 - "Walk-Forward Engine"
Cohesion: 0.11
Nodes (13): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (15): plan_view(), best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix() (+7 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.14
Nodes (9): prices(), all_tickers(), Play, radar(), stage(), stage_history(), stats(), Theme (+1 more)

### Community 19 - "download_prices"
Cohesion: 0.13
Nodes (11): index_panel(), market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), scan_data(), download_prices(), earnings_histories() (+3 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "pandas"
Cohesion: 0.12
Nodes (19): spy_regime(), br_backtest(), ld_backtest(), breakout_tab(), factor_backtest(), leader_dip_run(), alpaca_daily(), history() (+11 more)

### Community 22 - "Membership & Intraday Data"
Cohesion: 0.13
Nodes (12): alpaca_bars(), chunk(), _alpaca_get(), alpaca_keys(), intraday_bars(), latest_trade(), _parse_spells(), sec_filings() (+4 more)

### Community 23 - "Breakout Rider Strategy"
Cohesion: 0.10
Nodes (15): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+7 more)

### Community 24 - "Setup Views"
Cohesion: 0.15
Nodes (14): overview(), _fmt(), breakout_setup(), swing_rule_setup(), card(), checklist(), compact_frame(), _finite() (+6 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (15): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+7 more)

### Community 27 - "fakes.py"
Cohesion: 0.15
Nodes (17): analyst_data(), _base_info(), download_ohlcv(), download_prices(), earnings_history(), financials(), history(), info() (+9 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.22
Nodes (8): build_tab(), condition_rows(), lab_walk_forward(), _load(), _remove(), rules_key(), split_open_trade(), _value_step()

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "sharkfin/__init__.py"
Cohesion: 0.09
Nodes (4): pct(), stage_pill(), updown(), reload_changed_sharkfin()

### Community 34 - "test_leaks.py"
Cohesion: 0.32
Nodes (4): offline(), _panel(), test_a_stock_that_stops_trading_sells_when_that_is_known(), test_limit_fill_and_target_on_the_same_bar_do_not_both_count()

### Community 35 - "research.py"
Cohesion: 0.24
Nodes (4): api_key(), available(), _default(), stream_report()

### Community 36 - "_cached_panel"
Cohesion: 0.15
Nodes (13): _cached_panel(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), info(), _panel_file(), _panel_load() (+5 more)

### Community 37 - "load_scan"
Cohesion: 0.20
Nodes (5): load_scan(), prefetch(), deco(), cached(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "numpy"
Cohesion: 0.13
Nodes (16): trailing_pct(), cut(), make_ohlcv(), ohlcv(), price_panel(), _market(), _settings(), _signal() (+8 more)

### Community 39 - "home.py"
Cohesion: 0.29
Nodes (4): load_overview(), playbook_rows(), tile(), summary_rows()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 43 - "Series"
Cohesion: 0.17
Nodes (6): known(), night_returns(), overnight_hold(), rotation(), evaluate(), swing_returns()

### Community 44 - "Series"
Cohesion: 0.10
Nodes (11): atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main() (+3 more)

### Community 47 - "_intraday_ttl"
Cohesion: 0.40
Nodes (3): _intraday_ttl(), test_intraday_cache_is_short_while_the_market_is_open(), f()

### Community 49 - "nq_regimes.py"
Cohesion: 0.11
Nodes (18): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+10 more)

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 421 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `Walk-Forward Engine` to `run`, `Strategy Builder & Swing`, `numpy`, `Leader Dip Strategy`, `day_night.py`, `Series`, `test_core.py`, `pandas`, `Breakout Rider Strategy`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Financials` (e.g. with `financials()` and `quarterly_financials()`) actually correct?**
  _`Financials` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.06416275430359937 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `run` to `Walk-Forward Engine`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Should `ratings.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09059233449477352 - nodes in this community are weakly interconnected._
- **Should `streamlit` be split into smaller, more focused modules?**
  _Cohesion score 0.14492753623188406 - nodes in this community are weakly interconnected._