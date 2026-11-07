# Graph Report - SharkFin  (2026-11-06)

## Corpus Check
- 54 files · ~102,836 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 20 file(s) not represented in the graph (top: .csv 18, (none) 1, .toml 1)
- WARNING: 20 of 82 files seen (24%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1317 nodes · 3539 edges · 59 communities (48 shown, 11 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 119 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `35e80656`
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
- indicators.py
- ui.py
- day_night.py
- pandas
- catalysts.py
- Playbook Page
- data.py
- test_core.py
- walkforward.py
- sharkfin/playbook.py
- sharkfin/speculation.py
- download_prices
- sharkfin/portfolio.py
- home.py
- DataFrame
- test_leaks.py
- rsi
- leader_dip.py
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- Strategy Lab
- levels.py
- run
- sharkfin/__init__.py
- _cached_panel
- sma
- research.py
- load_scan
- pathlib
- latest_trade
- MCP Servers
- Current Logo
- opex_days
- swing_tab
- Series
- Offline Test Design
- test_core.py
- run_one
- nq_regimes.py
- predictions.py

## God Nodes (most connected - your core abstractions)
1. `ttl_cache()` - 39 edges
2. `Financials` - 39 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `plan_view()` - 21 edges
9. `history()` - 18 edges
10. `Day` - 18 edges

## Surprising Connections (you probably didn't know these)
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `stock_ratings()` --calls--> `to_gics()`  [EXTRACTED]
  app_pages/research.py → sharkfin/ratings.py
- `stage_pill()` --calls--> `h()`  [EXTRACTED]
  app_pages/speculation.py → sharkfin/ui.py
- `get_universe()` --calls--> `universe()`  [EXTRACTED]
  app_pages/scanner.py → sharkfin/data.py
- `test_fmt_money_negative_sign_before_dollar()` --calls--> `fmt_money()`  [EXTRACTED]
  tests/test_core.py → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (59 total, 11 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.05
Nodes (33): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), fair_value_summary(), Financials (+25 more)

### Community 1 - "ratings.py"
Cohesion: 0.15
Nodes (11): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), to_gics() (+3 more)

### Community 2 - "streamlit"
Cohesion: 0.16
Nodes (18): catalysts_view(), _filings(), render(), _tone_line(), overview(), switch_strip(), breakout_setup(), swing_rule_setup() (+10 more)

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

### Community 8 - "indicators.py"
Cohesion: 0.15
Nodes (18): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+10 more)

### Community 9 - "ui.py"
Cohesion: 0.09
Nodes (20): clean_text(), asset(), compact_frame(), esc(), fetch_all(), _finite(), fmt_big(), fmt_money() (+12 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "pandas"
Cohesion: 0.14
Nodes (14): tile(), index_panel(), breakout_tab(), nasdaq100(), peers_for(), sp500_table(), universe(), breakout_today() (+6 more)

### Community 12 - "catalysts.py"
Cohesion: 0.06
Nodes (33): could_run_tab(), _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text() (+25 more)

### Community 13 - "Playbook Page"
Cohesion: 0.21
Nodes (21): backtest_summary(), br_signals(), breakout_view(), day_night_view(), dn_backtest(), dn_today(), kpis(), ld_signals() (+13 more)

### Community 14 - "data.py"
Cohesion: 0.11
Nodes (14): all_symbols(), _copy(), _edgar_filings(), market_status(), news(), _NYSECalendar, _parse_date(), _rss() (+6 more)

### Community 15 - "test_core.py"
Cohesion: 0.12
Nodes (17): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), price_factor_frame(), sector_neutral_z(), walk_forward() (+9 more)

### Community 16 - "walkforward.py"
Cohesion: 0.06
Nodes (27): api_key(), available(), _default(), stream_report(), gate_grid(), cut(), _day(), Fold (+19 more)

### Community 17 - "sharkfin/playbook.py"
Cohesion: 0.16
Nodes (13): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+5 more)

### Community 18 - "sharkfin/speculation.py"
Cohesion: 0.15
Nodes (9): prices(), all_tickers(), Play, radar(), stage(), stage_history(), stats(), Theme (+1 more)

### Community 19 - "download_prices"
Cohesion: 0.14
Nodes (10): market_beta(), peer_table(), sector_etf_prices(), stock_ratings(), factor_backtest(), scan_data(), download_prices(), earnings_histories() (+2 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.14
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "home.py"
Cohesion: 0.13
Nodes (14): spy_regime(), br_backtest(), ld_backtest(), leader_dip_run(), download_ohlcv(), history(), last_years(), market_history() (+6 more)

### Community 22 - "DataFrame"
Cohesion: 0.15
Nodes (10): alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys(), intraday_bars(), _parse_spells(), _session() (+2 more)

### Community 23 - "test_leaks.py"
Cohesion: 0.05
Nodes (40): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+32 more)

### Community 24 - "rsi"
Cohesion: 0.18
Nodes (6): rsi(), follow_up(), price_chart(), test_leader_dip_follow_up(), test_rsi_bounds_and_wilder(), test_rsi_matches_reference_formula()

### Community 25 - "leader_dip.py"
Cohesion: 0.14
Nodes (14): _align(), _band(), latest(), _members(), percentile_against(), plus_frames(), quality_points(), regime() (+6 more)

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (15): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+7 more)

### Community 27 - "scanner.py"
Cohesion: 0.17
Nodes (13): get_universe(), leader_dip_tab(), log_prices(), log_signals(), market_close(), ratings_tab(), rule_signals(), scan() (+5 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.16
Nodes (16): bollinger_fade(), bracket(), Day, day_long_only(), ema_cross_5m(), _ema_rows(), _filter(), first_true() (+8 more)

### Community 30 - "Strategy Lab"
Cohesion: 0.17
Nodes (11): build_tab(), condition_rows(), lab_walk_forward(), _load(), _remove(), rules_key(), split_open_trade(), _value_step() (+3 more)

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.11
Nodes (17): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), Does GEX shrink the day? Yes, Fear day long, checked, How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Part 2: GEX and VIX as a daily playbook (+9 more)

### Community 33 - "sharkfin/__init__.py"
Cohesion: 0.11
Nodes (4): pct(), stage_pill(), updown(), reload_changed_sharkfin()

### Community 34 - "_cached_panel"
Cohesion: 0.17
Nodes (8): _cached_panel(), _fetch_ohlcv(), _fetch_prices(), fetch(), _naive(), _panel_file(), _patched(), test_price_panel_is_kept_on_disk_and_only_topped_up()

### Community 35 - "sma"
Cohesion: 0.24
Nodes (8): _market_gap(), sma(), backtest(), market_on(), signal_frames(), evaluate(), carry_forward(), test_leader_dip_backtest_fills_limits_and_exits()

### Community 36 - "research.py"
Cohesion: 0.15
Nodes (15): analyst_data(), _earnings_fresh(), _earnings_from_disk(), earnings_history(), _earnings_to_disk(), financials(), industry_members(), info() (+7 more)

### Community 37 - "load_scan"
Cohesion: 0.16
Nodes (8): load_scan(), _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "pathlib"
Cohesion: 0.22
Nodes (3): make_ohlcv(), ohlcv(), price_panel()

### Community 39 - "latest_trade"
Cohesion: 0.29
Nodes (4): playbook_rows(), latest_trade(), day_night_today(), summary_rows()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 42 - "opex_days"
Cohesion: 0.21
Nodes (6): opex_days(), opex_week(), evaluate(), day_view(), known(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 43 - "swing_tab"
Cohesion: 0.29
Nodes (7): swing_tab(), choices(), _load(), my_swing_rules(), _path(), swing_choice(), swing_picker()

### Community 44 - "Series"
Cohesion: 0.09
Nodes (14): atr(), deflated_sharpe(), fetch(), _folds_beating_cash(), intraday_frames(), load(), main(), night_returns() (+6 more)

### Community 47 - "test_core.py"
Cohesion: 0.08
Nodes (18): _intraday_ttl(), hurst_exponent(), _earn_table(), _panel(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports() (+10 more)

### Community 48 - "run_one"
Cohesion: 0.33
Nodes (3): first_usable(), run_one(), Strategy

### Community 49 - "nq_regimes.py"
Cohesion: 0.10
Nodes (19): _allowed(), _bands(), catalogue(), cell_names(), _cut(), day_matrix(), day_router(), fear_bounce() (+11 more)

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 434 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_line()` connect `Valuation & Quality Scores` to `pandas`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.05401234567901234 - nodes in this community are weakly interconnected._
- **Why does `market_on()` connect `sma` to `scanner.py`, `leader_dip.py`, `pandas`, `test_app.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `Strategy Builder & Swing` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
- **Why does `Financials` connect `Valuation & Quality Scores` to `research.py`, `data.py`, `test_leaks.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._