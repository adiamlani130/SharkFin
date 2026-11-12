# Graph Report - SharkFin  (2026-11-12)

## Corpus Check
- 66 files · ~121,953 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .csv 48, (none) 1, .toml 1)
- WARNING: 50 of 128 files seen (39%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1588 nodes · 4190 edges · 75 communities (52 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 144 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `947b92e8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Valuation & Quality Scores
- sharkfin/__init__.py
- sec_lab.py
- builder.py
- App Pages & Landing Animation
- Return Forecasting Models
- test_app.py
- leader_dip.py
- indicators.py
- ui.py
- day_night.py
- ttl_cache
- catalysts.py
- streamlit
- data.py
- sharkfin/playbook.py
- sentiment.py
- sharkfin/speculation.py
- nq_regimes.py
- stock_ratings
- sharkfin/portfolio.py
- Series
- factors.py
- catalyst_lab.py
- inputs
- nq_gex_plays.py
- scanner.py
- nq_lab.py
- Day
- NQ strategy lab: results (October 2026)
- levels.py
- run
- store.py
- growth_lab.py
- market_today.py
- Sign-in and private portfolios: setup
- load_scan
- numpy
- drivers.py
- MCP Servers
- Current Logo
- theme_turn
- test_rss_feeds_download_with_a_timeout
- Series
- Offline Test Design
- test_core.py
- walkforward.py
- ratings.py
- Results
- growth_lab.py
- backtest
- targets.py
- hurst_exponent
- backtest.py
- test_catalyst_lab.py
- _fear_day
- opex_days
- follow_up
- walk_forward

## God Nodes (most connected - your core abstractions)
1. `Financials` - 39 edges
2. `ttl_cache()` - 39 edges
3. `_line()` - 28 edges
4. `catalysts_view()` - 25 edges
5. `build_tab()` - 25 edges
6. `quality_metrics()` - 22 edges
7. `_sw()` - 22 edges
8. `Day` - 18 edges
9. `sp500_table()` - 18 edges
10. `download_prices()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `sp500_members()`  [INFERRED]
  docs/GROWTH_LAB.md → sharkfin/data.py
- `How the backtests avoid leakage` --references--> `run()`  [INFERRED]
  docs/NQ_STRATEGY_LAB.md → sharkfin/walkforward.py
- `Code` --references--> `init_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `save_list()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py
- `Code` --references--> `save_state()`  [INFERRED]
  docs/SIGN_IN_SETUP.md → sharkfin/ui.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three Researched Swing/Intraday Strategies in Combined Plan** — readme_leader_dip_plus_7, readme_tech_breakout_rider, readme_tqqq_day_night, readme_combined_plan [EXTRACTED 1.00]
- **Far-to-Near Swell Rendering Pipeline** — sharkfin_assets_ocean_draw, sharkfin_assets_ocean_surface, sharkfin_assets_ocean_fillbelow, sharkfin_assets_ocean_reach, sharkfin_assets_ocean_swell [EXTRACTED 1.00]
- **Backtest Integrity Safeguards** — readme_sliding_walk_forward, readme_no_lookahead_leak_test, readme_point_in_time_sp500 [INFERRED 0.85]

## Communities (75 total, 23 thin omitted)

### Community 0 - "Valuation & Quality Scores"
Cohesion: 0.06
Nodes (30): core_long_checklist(), net_buyback_yield(), altman_z(), dcf(), DCFResult, default_growth(), Financials, implied_prices() (+22 more)

### Community 2 - "sec_lab.py"
Cohesion: 0.06
Nodes (35): _cached_panel(), _intraday_ttl(), _panel_file(), _panel_load(), _panel_save(), _patched(), _Client, dilution_table() (+27 more)

### Community 3 - "builder.py"
Cohesion: 0.06
Nodes (46): market_beta(), C(), _close(), compare_templates(), condition_mask(), describe(), describe_strategy(), _fmt_value() (+38 more)

### Community 4 - "App Pages & Landing Animation"
Cohesion: 0.06
Nodes (40): SharkFin README, AI Analyst Research Note (Claude), Alpaca Market Data (read-only), Combined Plan (50/20/30), Core Longs Screen, Could Run Screen, Forecasts Page (Walk-forward Ensemble), GARCH(1,1) Filtered Historical Simulation (+32 more)

### Community 5 - "Return Forecasting Models"
Cohesion: 0.07
Nodes (17): ArimaModel, BayesianDrift, DampedTrendETS, ensemble_forecast(), fit_garch(), nll(), ForecastResult, _garch_recursion() (+9 more)

### Community 6 - "test_app.py"
Cohesion: 0.17
Nodes (20): offline(), _ok(), _page(), _scanned(), test_forecast_drivers_change_with_the_timeframe(), test_news_catalysts_view_and_10k_compare(), test_news_flags_big_beats(), test_page_renders() (+12 more)

### Community 7 - "leader_dip.py"
Cohesion: 0.14
Nodes (14): _align(), _band(), latest(), _members(), percentile_against(), plus_frames(), quality_points(), regime() (+6 more)

### Community 8 - "indicators.py"
Cohesion: 0.13
Nodes (20): build_features(), adx(), atr(), bollinger(), compute_all(), donchian(), ema(), macd() (+12 more)

### Community 9 - "ui.py"
Cohesion: 0.05
Nodes (46): overview(), switch_strip(), card(), pct(), stage_pill(), updown(), Code, clean_text() (+38 more)

### Community 10 - "day_night.py"
Cohesion: 0.11
Nodes (18): backtest(), bands(), close_location(), day_leg(), decision_location(), hold_after_check(), leg_stats(), night_leg() (+10 more)

### Community 11 - "ttl_cache"
Cohesion: 0.09
Nodes (25): catalysts_view(), run_forecast(), all_symbols(), analyst_data(), financials(), history(), industry_members(), info() (+17 more)

### Community 12 - "catalysts.py"
Cohesion: 0.05
Nodes (47): _col(), core_long_screen(), could_run(), earnings_beat_flag(), earnings_summary(), filing_change(), html_to_text(), insider_summary() (+39 more)

### Community 13 - "streamlit"
Cohesion: 0.07
Nodes (45): backtest_summary(), both_view(), br_backtest(), br_signals(), breakout_view(), dive_zone_view(), kpis(), lab_table() (+37 more)

### Community 14 - "data.py"
Cohesion: 0.05
Nodes (38): _filings(), render(), _tone_line(), alpaca_bars(), chunk(), alpaca_daily(), _alpaca_get(), alpaca_keys() (+30 more)

### Community 15 - "sharkfin/playbook.py"
Cohesion: 0.17
Nodes (13): best_weights(), correlations(), drawdowns(), _grid(), growth(), load(), mix(), sleeve() (+5 more)

### Community 16 - "sentiment.py"
Cohesion: 0.13
Nodes (13): could_run_tab(), aggregate_sentiment(), BM25, dedupe(), hours_old(), is_noise(), label(), rank_articles() (+5 more)

### Community 17 - "sharkfin/speculation.py"
Cohesion: 0.14
Nodes (10): prices(), all_tickers(), Play, radar(), stage(), stage_history(), stats(), Theme (+2 more)

### Community 18 - "nq_regimes.py"
Cohesion: 0.17
Nodes (12): _allowed(), _bands(), cell_names(), _cut(), day_matrix(), day_router(), labels(), level_map() (+4 more)

### Community 19 - "stock_ratings"
Cohesion: 0.15
Nodes (11): index_panel(), peer_table(), sector_etf_prices(), stock_ratings(), zone_study(), get_universe(), infos(), nasdaq100() (+3 more)

### Community 20 - "sharkfin/portfolio.py"
Cohesion: 0.15
Nodes (13): _cluster_var(), compare_allocations(), efficient_frontier(), expected_returns(), hrp(), max_sharpe(), min_variance(), _portfolio_stats() (+5 more)

### Community 21 - "Series"
Cohesion: 0.17
Nodes (6): known(), night_returns(), overnight_hold(), rotation(), evaluate(), swing_returns()

### Community 22 - "factors.py"
Cohesion: 0.12
Nodes (19): backtest_price_composite(), composite_scores(), earnings_factor_frame(), _earnings_table(), explain(), falling_knife(), fundamental_factor_frame(), is_cyclical() (+11 more)

### Community 23 - "catalyst_lab.py"
Cohesion: 0.12
Nodes (21): beat_model(), breadth_setups(), earnings_events(), _earnings_table(), entry_delay_table(), fda_study(), fda_table(), first_in() (+13 more)

### Community 24 - "inputs"
Cohesion: 0.22
Nodes (5): catalogue(), fear_bounce(), inputs(), regime_sized(), swing_router()

### Community 26 - "nq_gex_plays.py"
Cohesion: 0.13
Nodes (15): bs(), _call_wall_fade(), catalogue(), _days(), fly_trades(), value(), main(), move_vs_implied() (+7 more)

### Community 27 - "scanner.py"
Cohesion: 0.10
Nodes (20): breakout_tab(), factor_backtest(), leader_dip_tab(), load_scan(), log_prices(), log_signals(), market_close(), ratings_tab() (+12 more)

### Community 28 - "nq_lab.py"
Cohesion: 0.15
Nodes (25): buy_hold(), dip_in_calm(), donchian(), ema(), ema_cross(), ema_pullback(), ema_vix_sized(), gex_pct() (+17 more)

### Community 29 - "Day"
Cohesion: 0.12
Nodes (18): bollinger_fade(), bracket(), Day, evaluate(), day_long_only(), day_view(), ema_cross_5m(), _ema_rows() (+10 more)

### Community 30 - "NQ strategy lab: results (October 2026)"
Cohesion: 0.25
Nodes (8): Data: what was real and what was approximated, Day-trade results (test years Apr 2019 to Oct 2026), How the backtests avoid leakage, How the strategies that held up work, NQ strategy lab: results (October 2026), Rerun, Swing results (test years May 2015 to Oct 2026), What GEX showed

### Community 31 - "levels.py"
Cohesion: 0.22
Nodes (6): nearest_levels(), pivots(), rsi_bearish_divergence(), sr_zones(), weekly_trend(), test_levels_zones_and_divergence()

### Community 32 - "run"
Cohesion: 0.20
Nodes (9): Does GEX shrink the day? Yes, Fear day long, checked, Part 2: GEX and VIX as a daily playbook, Part 3: three GEX setups (call-wall fade, negative-gamma breakout, OpEx fly/condor), Results (out of sample), Results (unseen test years; swing May 2015 to Oct 2026, day trades Apr 2019 to Oct 2026), What each level meant (whole-sample description, not a tested trade), What was real and what was approximated (+1 more)

### Community 33 - "store.py"
Cohesion: 0.06
Nodes (31): reload_changed_sharkfin(), api_key(), available(), _default(), stream_report(), auth_configured(), _cloud_read(), _cloud_write() (+23 more)

### Community 34 - "growth_lab.py"
Cohesion: 0.13
Nodes (20): breakout(), bucket_table(), crash_events(), crash_guards(), dive_zone(), earnings_horizons(), entry_zones(), fear_buyer() (+12 more)

### Community 35 - "market_today.py"
Cohesion: 0.16
Nodes (8): breadth(), direction(), headline_drivers(), macro_drivers(), move_z(), _ret(), sector_leaders(), street_view()

### Community 36 - "Sign-in and private portfolios: setup"
Cohesion: 0.33
Nodes (5): 1. Supabase (about 3 minutes), 2. Google sign-in (about 5 minutes), 3. Streamlit secrets, Moving to your own domain later, Sign-in and private portfolios: setup

### Community 37 - "load_scan"
Cohesion: 0.17
Nodes (8): _is_empty(), prefetch(), deco(), cached(), wrapper(), fresh(), fetch_all(), test_prefetch_skips_cached_reports_progress_and_stops_on_interrupt()

### Community 38 - "numpy"
Cohesion: 0.13
Nodes (16): trailing_pct(), cut(), make_ohlcv(), ohlcv(), price_panel(), _market(), _settings(), _signal() (+8 more)

### Community 39 - "drivers.py"
Cohesion: 0.21
Nodes (7): drivers(), earnings_record(), estimate_trend(), _naive(), _num(), _tone(), test_drivers_earnings_record_and_estimates()

### Community 40 - "MCP Servers"
Cohesion: 0.50
Nodes (3): alphavantage, context7, firecrawl

### Community 41 - "Current Logo"
Cohesion: 0.67
Nodes (4): SharkFin Brand Identity (finance / stock-gains theme), SharkFin Logo, Shark Fin Over Waves Icon, SharkFin Wordmark (rising chart line in 'i')

### Community 44 - "Series"
Cohesion: 0.10
Nodes (11): atr(), deflated_sharpe(), fetch(), first_usable(), _folds_beating_cash(), intraday_frames(), load(), main() (+3 more)

### Community 47 - "test_core.py"
Cohesion: 0.10
Nodes (15): fair_value_summary(), forward_growth(), _earn_table(), test_alpaca_bars_retries_a_failed_span_and_never_returns_a_holed_history(), run(), test_drawdown_simple(), test_earnings_factors_use_only_past_reports(), test_failed_downloads_are_remembered_briefly_and_keep_the_last_good_answer() (+7 more)

### Community 49 - "walkforward.py"
Cohesion: 0.11
Nodes (13): gate_grid(), _day(), Fold, folds(), grid(), _neighbours(), pick(), run() (+5 more)

### Community 50 - "ratings.py"
Cohesion: 0.16
Nodes (10): _blend(), price_components(), ratings(), score_list(), sector_context(), sector_rank(), shark_score(), value_inputs() (+2 more)

### Community 52 - "Results"
Cohesion: 0.18
Nodes (10): Caveats, Entry ranges, Growth lab (Nov 2026), Results, Rules, Strategies (graded Oct 2021 to Nov 6 2026), Strategy Lab starting points, Tested and not adopted (+2 more)

### Community 58 - "growth_lab.py"
Cohesion: 0.10
Nodes (14): backtest(), latest(), qqq_gate(), signal_frames(), stock_status(), tech_universe(), walk_forward(), evaluate() (+6 more)

### Community 59 - "backtest"
Cohesion: 0.20
Nodes (11): _market_gap(), sma(), backtest(), market_on(), signal_frames(), evaluate(), carry_forward(), _panel() (+3 more)

### Community 60 - "targets.py"
Cohesion: 0.29
Nodes (4): entry_range(), _ok(), price_target(), rsi_pullback_price()

### Community 63 - "backtest.py"
Cohesion: 0.31
Nodes (5): compare(), positions(), run(), Strategy, test_backtest_no_lookahead()

### Community 64 - "test_catalyst_lab.py"
Cohesion: 0.22
Nodes (10): breadth(), kalshi_daily(), panel(), test_after_close_report_reacts_next_session_and_features_ignore_later_prices(), test_breadth_counts_members_only_and_ignores_later_days(), test_breadth_flags_a_washout_day(), test_falling_knife_gets_no_reversal_credit(), test_first_in_takes_one_entry_per_episode() (+2 more)

### Community 66 - "opex_days"
Cohesion: 0.43
Nodes (3): opex_days(), opex_week(), test_opex_is_the_third_friday_or_the_day_before_a_holiday()

### Community 77 - "walk_forward"
Cohesion: 0.40
Nodes (3): walk_forward(), evaluate(), weight_presets()

## Knowledge Gaps
- **8 isolated node(s):** `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation`, `Strategy Returns Research Data`, `Valuation Lab (DCF, Reverse DCF, Monte Carlo DCF)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 531 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `walkforward.py` to `test_catalyst_lab.py`, `builder.py`, `numpy`, `leader_dip.py`, `day_night.py`, `Series`, `walk_forward`, `growth_lab.py`, `NQ strategy lab: results (October 2026)`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **What connects `Core Longs Screen`, `Could Run Screen`, `GARCH(1,1) Filtered Historical Simulation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Valuation & Quality Scores` be split into smaller, more focused modules?**
  _Cohesion score 0.060350877192982454 - nodes in this community are weakly interconnected._
- **Why does `How the backtests avoid leakage` connect `NQ strategy lab: results (October 2026)` to `walkforward.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Should `sec_lab.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05683563748079877 - nodes in this community are weakly interconnected._
- **Should `builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055135135135135134 - nodes in this community are weakly interconnected._
- **Should `App Pages & Landing Animation` be split into smaller, more focused modules?**
  _Cohesion score 0.062040816326530614 - nodes in this community are weakly interconnected._