"""Single-stock research: overview, valuation, trade setup, financials, analysts & news, AI note."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from sharkfin import ai, catalysts, data, leader_dip, levels, ratings, risk, sentiment, swing, ui, valuation
from sharkfin import indicators as ind
from sharkfin.explain import tip

ui.header("Research & Valuation",
          "One stock, everything that matters: the chart and key stats, what it's worth, whether there's a swing trade "
          "or a long-term case, how healthy the business is, and what analysts and the news say.")

top = st.columns([4, 1.4], vertical_alignment="bottom")
with top[0]:
    sym = ui.symbol_picker("research")
if not sym:
    st.stop()

with st.spinner(f"Loading {sym}…"):
    inf = data.info(sym)
    hist = data.history(sym, "5y")

if hist.empty:
    st.error(f"No price data for **{sym}**. Check the ticker.")
    st.stop()

price = data.price_of(inf)
if not np.isfinite(price):
    price = float(hist["Close"].iloc[-1])
name = inf.get("longName") or inf.get("shortName") or sym

with top[1]:
    wl = st.session_state.watchlist
    if sym in wl:
        if st.button("Remove from watchlist", width="stretch"):
            wl.remove(sym)
            ui.save_state()
            st.rerun()
    elif st.button("Add to watchlist", type="primary", width="stretch"):
        wl.append(sym)
        ui.save_state()
        st.rerun()

prev = ui.num(inf.get("previousClose"), float(hist["Close"].iloc[-2]) if len(hist) > 1 else price)
chg = price / prev - 1 if prev else np.nan
where = " · ".join(str(x) for x in (inf.get("sector"), inf.get("industry"), inf.get("exchange")) if x)
st.markdown(
    f"<div class='sf-hero'><div class='k'>{sym}{' · ' + where if where else ''}</div>"
    f"<div class='v'>{ui.h(name)}</div>"
    f"<div style='margin-top:6px'><span style='font-size:1.6rem;font-weight:700'>{ui.fmt_money(price).replace('$', '&#36;')}</span> "
    f"&nbsp;{ui.pill(ui.fmt_pct(chg, 2, True), ui.tone(chg))}<span class='sf-muted'>today</span></div></div>",
    unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached computations
# ---------------------------------------------------------------------------


@st.cache_data(ttl=3600, show_spinner=False)
def market_beta(symbol: str):
    px = data.download_prices((symbol, "^GSPC"), period="3y")
    if symbol not in px or "^GSPC" not in px:
        return np.nan, np.nan
    wk = px.resample("W-FRI").last().pct_change().dropna()  # weekly returns avoid async-close bias
    if len(wk) < 52:
        return np.nan, np.nan
    b, _ = risk.beta_alpha(wk[symbol], wk["^GSPC"], periods=52)
    return b, risk.blume_adjusted_beta(b)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def peer_table(symbol: str, inf_: dict) -> pd.DataFrame:
    peers = data.peers_for(symbol, inf_)
    if not peers:
        return pd.DataFrame()
    df = data.infos(tuple(peers))
    if df.empty:
        return pd.DataFrame()
    n = lambda c: pd.to_numeric(df[c], errors="coerce") if c in df else pd.Series(np.nan, index=df.index)
    out = pd.DataFrame({
        "Name": df["shortName"] if "shortName" in df else pd.Series(index=df.index, dtype=object),
        "Market cap": n("marketCap"),
        "P/E (fwd)": n("forwardPE"), "P/E (ttm)": n("trailingPE"),
        "EV/EBITDA": n("enterpriseToEbitda"), "EV/Sales": n("enterpriseToRevenue"),
        "P/FCF": n("marketCap") / n("freeCashflow").where(lambda x: x > 0), "P/B": n("priceToBook"),
        "revenue_growth": n("revenueGrowth"), "ebitda_margin": n("ebitdaMargins"),
        "ROE": n("returnOnEquity"), "Gross margin": n("grossMargins"),
    })
    # Rows where Yahoo returned nothing useful (rate limits, delisted tickers) only add noise.
    return out[out[["P/E (fwd)", "P/E (ttm)", "EV/EBITDA", "EV/Sales", "P/B"]].notna().any(axis=1)]


@st.cache_data(ttl=3600, show_spinner=False)
def index_panel():
    """S&P 500 closes (2 years) and GICS sectors: the yardstick for strength ranks, ratings and breadth."""
    px_ = data.download_prices(tuple(data.universe("S&P 500")), period="2y")
    tab = data.sp500_table().set_index("Symbol")
    sec = tab["Sector"].reindex(px_.columns) if "Sector" in tab and not px_.empty else pd.Series(dtype=object)
    return px_, sec


@st.cache_data(ttl=3600, show_spinner=False)
def sector_etf_prices() -> pd.DataFrame:
    return data.download_prices(tuple(data.SECTOR_ETFS.values()), period="2y")


@st.cache_data(ttl=3600, show_spinner=False)
def stock_ratings(symbol: str, stock_close: pd.Series, inf_: dict, bond: float) -> dict:
    """RT, RS and CI ranked within the stock's S&P 500 sector; RV within its industry peers."""
    px_, sec = index_panel()
    if px_.empty:
        return {}
    panel, secs = px_, sec.copy()
    if symbol not in panel:
        panel = panel.join(stock_close.rename(symbol), how="left")
    if pd.isna(secs.get(symbol)):
        secs[symbol] = ratings.to_gics(inf_.get("sector"))
    rat = ratings.ratings(panel, secs, None, bond)
    if symbol not in rat.index:
        return {}
    row = rat.loc[symbol]
    peers = data.peers_for(symbol, inf_)
    grp = pd.DataFrame([inf_], index=[symbol])
    if peers:
        grp = pd.concat([grp, data.infos(tuple(peers))])
    rv_raw = ratings.graham_value(grp, bond)
    rv = float(rv_raw.rank(pct=True)[symbol] * 2) if rv_raw.notna().sum() >= 5 and np.isfinite(rv_raw[symbol]) else np.nan
    vst = float(np.sqrt((rv ** 2 + row["RT"] ** 2 + row["RS"] ** 2) / 3)) if np.isfinite(rv) else np.nan
    return {"RV": rv, "RT": float(row["RT"]), "RS": float(row["RS"]), "CI": float(row["CI"]), "VST": vst,
            "sector": secs.get(symbol), "n_sector": int((secs == secs.get(symbol)).sum()), "n_peers": int(rv_raw.notna().sum())}


# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------
fin = data.financials(sym)
qfin = data.quarterly_financials(sym)
rf = data.risk_free_rate()
ad = data.analyst_data(sym)
shares = ui.num(inf.get("sharesOutstanding"), ui.num(inf.get("impliedSharesOutstanding")))
if not np.isfinite(shares):
    shares = valuation._v(fin.shares())
mcap = ui.num(inf.get("marketCap"), price * shares if np.isfinite(shares) else np.nan)
total_debt = ui.num(inf.get("totalDebt"), valuation._v(fin.total_debt(), 0, 0.0))
total_cash = ui.num(inf.get("totalCash"), valuation._v(fin.cash(), 0, 0.0))
net_debt = (total_debt if np.isfinite(total_debt) else 0) - (total_cash if np.isfinite(total_cash) else 0)
is_financial = str(inf.get("sector", "")).lower().startswith("financial")
rev_g = ui.num(inf.get("revenueGrowth"))
raw_beta, adj_beta = market_beta(sym)

mkt = data.market_history("5y")
with st.spinner("Ranking against the S&P 500…"):
    idx_px, idx_sec = index_panel()
ref_gains = leader_dip.six_month_gain(idx_px.ffill()).iloc[-1].dropna() if not idx_px.empty else None
ld = leader_dip.stock_status(hist, ref_gains, mkt["Close"] if not mkt.empty else None)
swing_name = ui.swing_choice()
swing_rules = swing.rules(swing_name, ui.my_swing_rules())
sw = swing.stock_status(hist, swing_rules, mkt["Close"] if not mkt.empty else None, rf=rf) if swing_rules else None
zones = levels.sr_zones(hist)
resistance, support = levels.nearest_levels(hist, zones)
weekly = levels.weekly_trend(hist["Close"])
earn = catalysts.earnings_summary(ad.get("earnings_dates"))
ins = catalysts.insider_summary(ad.get("insider_transactions"))
core = catalysts.core_long_checklist(inf, fin, hist, ad, ins, earn)
f_score = valuation.piotroski_f_score(fin)
z = None if is_financial else valuation.altman_z(fin, mcap)
qm = valuation.quality_metrics(fin, mcap)
if is_financial:  # cash-flow and margin ratios aren't meaningful for banks and insurers
    for k in ("FCF margin", "FCF yield", "Gross margin", "Gross profitability (GP/TA)", "Operating margin", "ROIC",
              "Net debt / EBITDA", "Interest coverage (EBIT/int)", "Cash conversion (CFO/NI)", "Sloan accruals (NI-CFO)/TA"):
        qm[k] = np.nan
r_all = hist["Close"].pct_change().dropna()

tab_names = ["Overview", "Valuation", "Trade setup", "Financials", "Analysts & news"]
if ai.available():
    tab_names.append("AI note")
tabs = st.tabs(tab_names)

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
with tabs[0]:
    glance = st.container()  # filled in once valuation is computed

    tf = st.segmented_control("Range", ["1M", "3M", "6M", "YTD", "1Y", "2Y", "5Y"], default="1Y", key="rs_tf",
                              label_visibility="collapsed")
    c2, c3 = st.columns(2)
    overlays = c2.multiselect("Overlays", ["SMA 20", "SMA 50", "SMA 200", "EMA 21", "Bollinger", "VWAP"],
                              default=["SMA 50", "SMA 200"])
    lower = c3.multiselect("Panels", ["Volume", "RSI", "MACD"], default=["Volume", "RSI"])
    days = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252, "2Y": 504, "5Y": 1260}
    if tf == "YTD":
        view = hist[hist.index.year == hist.index[-1].year]
    else:
        view = hist.iloc[-days.get(tf or "1Y", 252):]
    # Compute overlays on full history, then zoom, so long averages aren't truncated.
    full = ui.price_chart(hist, sym, overlays, lower)
    full.update_xaxes(range=[view.index[0], view.index[-1]])
    lo, hi = view["Low"].min(), view["High"].max()
    full.update_yaxes(range=[lo * 0.97, hi * 1.03], row=1, col=1)
    ui.plotly(full)

    st.subheader("Key stats")
    dy = ui.num(inf.get("dividendYield"))
    dy = dy / 100 if np.isfinite(dy) else ui.num(inf.get("trailingAnnualDividendYield"))  # yfinance: percent vs decimal
    ret_1y = hist["Close"].iloc[-1] / hist["Close"].iloc[-253] - 1 if len(hist) > 253 else np.nan
    pe, fpe = ui.num(inf.get("trailingPE")), ui.num(inf.get("forwardPE"))
    ui.metrics([
        ("Market cap", ui.fmt_money(mcap)),
        {"label": "P/E", "value": ui.fmt_x(pe), "help": "Price / last 12 months' earnings per share."},
        {"label": "Forward P/E", "value": ui.fmt_x(fpe), "help": "Price / analysts' expected earnings for the next 12 months."},
        {"label": "EV / EBITDA", "value": ui.fmt_x(ui.num(inf.get("enterpriseToEbitda"))),
         "help": "Enterprise value (market cap + net debt) / operating earnings before depreciation. Comparable across capital structures."},
        {"label": "Dividend yield", "value": ui.fmt_pct(dy, 2) if np.isfinite(dy) and dy > 0 else None},
        {"label": "1-year return", "value": ui.fmt_pct(ret_1y, 1, True)},
        {"label": "Beta", "value": ui.fmt_num(adj_beta), "help": "How much the stock moves with the S&P 500 (3 years of weekly "
                                                                 "returns, Blume-adjusted). 1 = in line, 1.5 = 50% more."},
        {"label": "Short interest", "value": ui.fmt_pct(ui.num(inf.get("shortPercentOfFloat"))),
         "help": "Share of tradable shares sold short. Above ~10% means a lot of investors are betting against it."},
    ], key="keystats")
    lo52, hi52 = ui.num(inf.get("fiftyTwoWeekLow")), ui.num(inf.get("fiftyTwoWeekHigh"))
    ui.kv([
        ("Enterprise value", ui.fmt_money(ui.num(inf.get("enterpriseValue")))),
        ("52-week range", f"{ui.fmt_money(lo52)} – {ui.fmt_money(hi52)}" if np.isfinite(lo52) and np.isfinite(hi52) else None),
        ("Volatility (1 year)", ui.fmt_pct(risk.annualized_vol(r_all.iloc[-252:]))),
        ("Worst drop (5 years)", ui.fmt_pct(risk.max_drawdown(r_all))),
        ("Sharpe ratio (5 years)", ui.fmt_num(risk.sharpe_ratio(r_all, rf))),
        ("Average volume", ui.fmt_big(ui.num(inf.get("averageVolume")), 1)),
        ("Shares outstanding", ui.fmt_big(shares, 2)),
        ("Employees", f"{int(inf['fullTimeEmployees']):,}" if inf.get("fullTimeEmployees") else None),
    ])

    sc = ratings.sector_context(sym, hist["Close"], inf.get("sector"), sector_etf_prices(), idx_px, idx_sec)
    rat = stock_ratings(sym, hist["Close"], {k: inf.get(k) for k in (
        "industry", "industryKey", "sector", "marketCap", "trailingEps", "earningsGrowth", "currentPrice",
        "regularMarketPrice")}, data.risk_free_rate())
    if sc or rat:
        st.subheader("Against its sector",
                     help="Context, not a signal. In SharkFin's research none of these sector readings, and none of the "
                          "ratings on their own, predicted the next month's return; they describe where the stock and its "
                          "sector stand.")
    if sc:
        ui.metrics([
            {"label": f"{sc['gics']} ({sc['etf']}), 6 months", "value": ui.fmt_pct(sc["sector_6m"], 1, True),
             "delta": f"#{sc['rank']} of {sc['n_sectors']} sectors", "delta_color": "off", "delta_arrow": "off",
             "help": "The SPDR sector ETF's gain over the last 6 months, and where that ranks among the sector ETFs."},
            {"label": "Sector breadth", "value": ui.fmt_pct(sc["breadth"], 0) if np.isfinite(sc["breadth"]) else None,
             "delta": f"of {sc['breadth_n']} S&P 500 stocks", "delta_color": "off", "delta_arrow": "off",
             "help": "Share of the sector's S&P 500 stocks above their 200-day average. Above ~60% is a broad uptrend."},
            {"label": "Sector off its high", "value": ui.fmt_pct(sc["off_high"], 1),
             "help": "How far the sector ETF is below its highest close of the past year."},
            {"label": f"{sym} vs its sector, 6 months", "value": ui.fmt_pct(sc["vs_sector"], 1, True) if np.isfinite(sc["vs_sector"]) else None,
             "delta": f"{sym} {ui.fmt_pct(sc['stock_6m'], 1, True)}", "delta_color": "off", "delta_arrow": "off",
             "help": "The stock's 6-month gain minus its sector ETF's."},
        ], key="sector")
    if rat:
        ui.metrics([{"label": ratings.NAMES[k], "value": ui.fmt_num(rat.get(k)), "help": ratings.HELP[k]}
                    for k in ("VST", "RV", "RT", "RS", "CI")], key="vv")
        st.caption(f"VectorVest-style ratings, 0 to 2, where 1 is the middle of the sector. RT, RS and CI are ranked "
                   f"against the {rat['n_sector']} S&P 500 stocks in {rat['sector'] or 'its sector'}; RV against "
                   f"{max(rat['n_peers'] - 1, 0)} industry peers. On their own they barely predicted the next month; "
                   "Top Performers → Sector VST list shows the weekly list that held up.")
    if inf.get("longBusinessSummary"):
        with st.expander("What the company does"):
            st.write(inf["longBusinessSummary"])

# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------
dcf_out, bank_out = {}, {}
with tabs[1]:
    hero_box = st.container()
    beta0 = adj_beta if np.isfinite(adj_beta) else ui.num(inf.get("beta"), 1.0)
    fwd_g = valuation.forward_growth(ad.get("growth_estimates"))
    g_default = valuation.default_growth(fin, fwd_g, rev_g)

    # ---- Intrinsic value ---------------------------------------------------
    if is_financial:
        st.subheader("Intrinsic value: excess-return model",
                     help="Cash-flow DCFs don't work for banks and insurers (borrowing is their raw material, not "
                          "financing). Instead a bank is worth its book value scaled by how much its return on equity "
                          "beats its cost of equity: value = book × (ROE − g) / (cost of equity − g).")
        with st.expander("Adjust assumptions"):
            a = st.columns(3)
            roe_in = a[0].slider("Sustainable ROE", 0.0, 0.30, float(np.clip(ui.num(inf.get("returnOnEquity"), 0.10), 0.0, 0.30)),
                                 0.005, format="%.3f")
            g_bank = a[1].slider("Long-run growth", 0.0, 0.05, 0.03, 0.0025, format="%.4f")
            erp = a[2].slider("Equity risk premium", 0.03, 0.07, valuation.DEFAULT_ERP, 0.0025, format="%.4f")
        ke = rf + float(np.clip(beta0, 0.3, 3.0)) * erp
        bvps = ui.num(inf.get("bookValue"))
        bv = valuation.justified_pb_value(roe_in, ke, g_bank, bvps)
        if np.isfinite(bv):
            lo_b = valuation.justified_pb_value(max(roe_in - 0.02, 0), ke, g_bank, bvps)
            hi_b = valuation.justified_pb_value(roe_in + 0.02, ke, g_bank, bvps)
            bank_out = {"value": bv, "low": lo_b, "high": hi_b}
            ui.metrics([
                {"label": "Value per share", "value": ui.fmt_money(bv), "delta": ui.fmt_pct(bv / price - 1, 1, True)},
                {"label": "Return on equity", "value": ui.fmt_pct(roe_in)},
                {"label": "Cost of equity", "value": ui.fmt_pct(ke), "help": "10-year Treasury + beta × equity risk premium."},
                {"label": "Book value / share", "value": ui.fmt_money(bvps)},
                {"label": "Justified P/B", "value": ui.fmt_x(bv / bvps, 2), "delta": f"actual {ui.fmt_x(price / bvps, 2)}",
                 "delta_color": "off", "delta_arrow": "off"},
            ], key="bank")
        else:
            st.info("Not enough data for the excess-return model (needs book value and a return on equity above growth).")
    else:
        st.subheader("Intrinsic value: discounted cash flow", help=tip("dcf"))
        with st.expander("Adjust DCF assumptions"):
            a1, a2, a3 = st.columns(3)
            growth = a1.slider("Growth for the first years", -0.10, 0.40, float(round(g_default, 3)), 0.005, format="%.3f",
                               help="Default: the median of analysts' next-year growth, the latest revenue growth and the "
                                    "3-year revenue growth rate.")
            hg_years = a1.slider("Years of that growth", 3, 10, 5, help="After this, growth fades to the terminal rate over 5 years.")
            tg = a2.slider("Growth forever after", 0.0, 0.04, float(min(0.025, rf)), 0.0025, format="%.4f",
                           help="Capped near the risk-free rate: no company outgrows the economy forever.")
            erp = a2.slider("Equity risk premium", 0.03, 0.07, valuation.DEFAULT_ERP, 0.0025, format="%.4f",
                            help="Extra return investors demand for owning stocks over Treasuries.")
            beta = a3.number_input("Beta", 0.3, 3.0, float(np.clip(beta0, 0.3, 3.0)), 0.05,
                                   help=f"Default is the 3-year weekly regression beta, Blume-adjusted (raw {ui.fmt_num(raw_beta)}).")
            sbc = a3.toggle("Count stock comp as a cost", value=True,
                            help="Subtracts stock-based compensation from free cash flow, which otherwise overstates owner earnings.")
        fcf0, fcf_src = valuation.starting_fcf(fin, qfin, inf, subtract_sbc=sbc)
        w = valuation.wacc(mcap, total_debt, beta, rf, erp, valuation._v(fin.interest_expense()), fin.effective_tax_rate())
        valid_dcf = np.isfinite(fcf0) and fcf0 > 0 and np.isfinite(shares) and shares > 0 and w.wacc > tg + 0.005
        if valid_dcf:
            res = valuation.dcf(fcf0, growth, w.wacc, tg, net_debt, shares, hg_years, 5)
            implied_g = valuation.reverse_dcf(price, fcf0, w.wacc, tg, net_debt, shares)
            sims = valuation.monte_carlo_dcf(fcf0, growth, w.wacc, tg, net_debt, shares)
            p_under = float((sims > price).mean())
            dcf_out = {"value": res.value_per_share, "upside": res.value_per_share / price - 1, "wacc": w.wacc,
                       "growth": growth, "terminal_growth": tg, "implied_growth": implied_g, "p_undervalued": p_under,
                       "terminal_share_of_ev": res.terminal_share, "fcf0": fcf0,
                       "mc_p10": float(np.percentile(sims, 10)), "mc_p90": float(np.percentile(sims, 90))}
            ui.metrics([
                {"label": "DCF value", "value": ui.fmt_money(res.value_per_share),
                 "delta": ui.fmt_pct(dcf_out["upside"], 1, True)},
                {"label": "WACC", "value": ui.fmt_pct(w.wacc, 2),
                 "help": f"Cost of equity {w.cost_of_equity:.1%} (CAPM) and after-tax cost of debt {w.cost_of_debt_after_tax:.1%}, "
                         f"weighted by market values. The 10-year Treasury is {rf:.2%}."},
                {"label": "Growth priced in", "value": ui.fmt_pct(implied_g), "help": tip("implied_growth")},
                {"label": "Odds undervalued", "value": ui.fmt_pct(p_under, 0), "help": tip("p_undervalued")},
                {"label": "Starting FCF", "value": ui.fmt_money(fcf0), "help": f"Source: {fcf_src}."},
            ], key="dcf")
            if np.isfinite(implied_g):
                gap = "more" if implied_g > growth else "less"
                st.markdown(
                    f"<div class='sf-note'>At today's price the market is pricing in about <b>{implied_g:.1%}</b> a year "
                    f"free-cash-flow growth for {hg_years} years. Your assumption is {growth:.1%}, so the market expects "
                    f"{gap} than you do. The terminal value is {res.terminal_share:.0%} of the total.</div>",
                    unsafe_allow_html=True)
            col_l, col_r = st.columns(2)
            with col_l:
                scale, unit = (1e9, "B") if fcf0 >= 1e9 else (1e6, "M")
                years = [f"Y{i}" for i in range(1, len(res.fcf_path) + 1)]
                fig = go.Figure()
                fig.add_bar(x=years, y=res.fcf_path / scale, name="Projected FCF", marker_color=ui.BLUE)
                fig.add_bar(x=years, y=res.fcf_path * res.discount_factors / scale, name="Worth today", marker_color=ui.GREEN)
                fig.update_layout(title=f"Free cash flow projection (${unit})", barmode="group",
                                  yaxis=dict(tickprefix="$", ticksuffix=unit))
                ui.plotly(fig, 340)
            with col_r:
                grid = valuation.sensitivity_grid(fcf0, growth, w.wacc, tg, net_debt, shares)
                up = grid / price - 1
                fig = go.Figure(go.Heatmap(z=np.clip(up.values * 100, -100, 100), x=grid.columns, y=grid.index, zmid=0,
                                           colorscale=ui.DIVERGING, showscale=False, xgap=2, ygap=2,
                                           text=[[f"${v:,.0f}" if np.isfinite(v) else "n/a" for v in row] for row in grid.values],
                                           texttemplate="%{text}", hovertemplate="WACC %{y}, growth %{x}: %{text}<extra></extra>"))
                fig.update_layout(title="Value per share by discount rate and long-run growth",
                                  xaxis_title="Growth forever after", yaxis_title="Discount rate")
                ui.plotly(fig, 340)
        else:
            if not np.isfinite(fcf0):
                why = "Yahoo has no cash-flow data for this company"
            elif fcf0 <= 0:
                why = f"its free cash flow is negative ({ui.fmt_money(fcf0)} a year)"
            else:
                why = "the share count is missing"
            st.info(f"No DCF for {sym}: {why}. A cash-flow model can't value a business that isn't generating cash yet, "
                    "so the fair value below leans on peer multiples and analyst targets.")

    # ---- Peers ---------------------------------------------------------------
    st.subheader("Relative value: peer multiples", help=tip("peers"))
    with st.spinner("Pulling peer multiples…"):
        peers = peer_table(sym, {k: inf.get(k) for k in ("industry", "industryKey", "sector", "marketCap")})
    rel_value, rel_lo, rel_hi = np.nan, np.nan, np.nan
    fcf_info = ui.num(inf.get("freeCashflow"))
    target = {"price": price, "shares": shares, "net_debt": net_debt,
              "forward_eps": ui.num(inf.get("forwardEps")), "trailing_eps": ui.num(inf.get("trailingEps")),
              "ebitda": ui.num(inf.get("ebitda")), "revenue": ui.num(inf.get("totalRevenue")),
              "fcf_per_share": fcf_info / shares if np.isfinite(shares) and shares else np.nan,
              "book_per_share": ui.num(inf.get("bookValue")),
              "P/E (fwd)": fpe, "P/E (ttm)": pe,
              "EV/EBITDA": ui.num(inf.get("enterpriseToEbitda")), "EV/Sales": ui.num(inf.get("enterpriseToRevenue")),
              "P/FCF": mcap / fcf_info if np.isfinite(fcf_info) and fcf_info > 0 else np.nan,
              "P/B": ui.num(inf.get("priceToBook")),
              "revenue_growth": rev_g, "ebitda_margin": ui.num(inf.get("ebitdaMargins"))}
    imp = valuation.implied_prices(target, peers) if not peers.empty else pd.DataFrame()
    if imp.empty:
        st.info("Couldn't build a peer comparison right now (Yahoo didn't return multiples for this company's peers). "
                "Try again in a minute.")
    else:
        use = imp if is_financial else imp[imp["Multiple"] != "P/B"]
        use = use if len(use) else imp
        geo = lambda col: float(np.exp(np.log(use[col].clip(lower=0.01)).mean()))
        rel_value, rel_lo, rel_hi = geo("Median"), geo("Low (25th)"), geo("High (75th)")
        imp = imp.assign(**{"Upside (median)": imp["Upside (median)"] * 100})
        show = imp.rename(columns={"Target": "This stock", "Peer median multiple": "Peer median",
                                   "Low (25th)": "Implied low", "Median": "Implied price", "High (75th)": "Implied high",
                                   "Upside (median)": "Upside"})
        st.dataframe(show[["Multiple", "This stock", "Peer median", "Implied low", "Implied price", "Implied high", "Upside", "Peers"]],
                     hide_index=True, width="stretch", column_config={
                         "This stock": st.column_config.NumberColumn(format="%.1fx"),
                         "Peer median": st.column_config.NumberColumn(format="%.1fx"),
                         "Implied low": st.column_config.NumberColumn(format="$%.2f", help="At the peers' 25th-percentile multiple."),
                         "Implied price": st.column_config.NumberColumn(format="$%.2f", help="At the peers' median multiple."),
                         "Implied high": st.column_config.NumberColumn(format="$%.2f", help="At the peers' 75th-percentile multiple."),
                         "Upside": st.column_config.NumberColumn(format="%+.0f%%"),
                         "Peers": st.column_config.NumberColumn(help="Peers with a usable value for this multiple.")})
        with st.expander(f"Peer group ({len(peers)} companies)"):
            st.dataframe(peers.rename(columns={"revenue_growth": "Revenue growth", "ebitda_margin": "EBITDA margin"}),
                         width="stretch", column_config={
                             "Market cap": st.column_config.NumberColumn("Market cap ($)", format="compact"),
                             **{c: st.column_config.NumberColumn(format="%.1fx") for c in
                                ("P/E (fwd)", "P/E (ttm)", "EV/EBITDA", "EV/Sales", "P/FCF", "P/B")},
                             **{c: st.column_config.NumberColumn(format="percent") for c in
                                ("Revenue growth", "EBITDA margin", "ROE", "Gross margin")}})
            reg = valuation.regression_multiple(peers, target)
            if reg and np.isfinite(target["revenue"]) and np.isfinite(shares):
                reg_price = (reg["fitted"] * target["revenue"] - net_debt) / shares
                st.caption(f"Growth- and margin-adjusted EV/Sales: {reg['fitted']:.2f}x vs actual {ui.fmt_num(target['EV/Sales'])}x "
                           f"(regression across {reg['n']} peers, R² {reg['r2']:.2f}), which implies "
                           f"{ui.esc(ui.fmt_money(reg_price))} a share.")

    # ---- Blend (rendered at the top of the tab) -----------------------------
    lo_t, mean_t, hi_t = ui.num(inf.get("targetLowPrice")), ui.num(inf.get("targetMeanPrice")), ui.num(inf.get("targetHighPrice"))
    intrinsic_name = "Excess-return model" if is_financial else "DCF"
    intrinsic = bank_out.get("value", np.nan) if is_financial else dcf_out.get("value", np.nan)
    fv = valuation.fair_value_summary(price, {
        intrinsic_name: (intrinsic, 0.4), "Peer multiples": (rel_value, 0.4), "Analyst targets": (mean_t, 0.2)})
    with hero_box:
        used = [n for n, v in ((intrinsic_name, intrinsic), ("peer multiples", rel_value), ("analyst targets", mean_t)) if np.isfinite(v)]
        if np.isfinite(fv["fair_value"]):
            ui.hero("Blended fair value", ui.fmt_money(fv["fair_value"]).replace("$", "&#36;"),
                    f"{ui.fmt_pct(fv['upside'], 1, True)} vs the current {ui.fmt_money(price).replace('$', '&#36;')}. "
                    f"Weighted blend of {', '.join(used)} (intrinsic value 40%, peers 40%, analysts 20%; "
                    "missing methods are re-weighted).",
                    ui.pill(fv["label"], "pos" if fv["upside"] > 0.1 else "neg" if fv["upside"] < -0.1 else "neu"))
        else:
            st.info("Not enough data to value this stock (no cash-flow model, peer multiples or analyst targets).")
        rows = []
        if is_financial and bank_out:
            rows.append((intrinsic_name, bank_out["low"], bank_out["value"], bank_out["high"]))
        elif dcf_out:
            rows.append(("DCF (10th–90th pct)", dcf_out["mc_p10"], dcf_out["value"], dcf_out["mc_p90"]))
        if np.isfinite(rel_value):
            rows.append(("Peer multiples", rel_lo, rel_value, rel_hi))
        if np.isfinite(mean_t):
            rows.append(("Analyst targets", lo_t, mean_t, hi_t))
        lo52, hi52 = ui.num(inf.get("fiftyTwoWeekLow")), ui.num(inf.get("fiftyTwoWeekHigh"))
        if np.isfinite(lo52) and np.isfinite(hi52):
            rows.append(("52-week range", lo52, np.nan, hi52))
        if rows:
            fig = go.Figure()
            for i, (lbl, lo_, mid, hi_) in enumerate(rows):
                colr = ui.MUTED if lbl == "52-week range" else ui.BLUE
                fig.add_trace(go.Bar(y=[lbl], x=[hi_ - lo_], base=[lo_], orientation="h", marker_color=colr, opacity=0.55,
                                     width=0.5, showlegend=False,
                                     hovertemplate=f"{lbl}: ${lo_:,.2f} – ${hi_:,.2f}<extra></extra>"))
                if np.isfinite(mid):
                    fig.add_trace(go.Scatter(y=[lbl], x=[mid], mode="markers", showlegend=False,
                                             marker=dict(symbol="line-ns", size=22, line=dict(width=3, color="#e6e9ef")),
                                             hovertemplate=f"{lbl} midpoint: ${mid:,.2f}<extra></extra>"))
            marks = [(price, f"Price ${price:,.2f}", ui.ORANGE, "dot")]
            if np.isfinite(fv["fair_value"]):
                marks.append((fv["fair_value"], f"Fair value ${fv['fair_value']:,.2f}", ui.GREEN, "solid"))
            hi_mark = max(m[0] for m in marks)
            for x_, txt, colr, dash in marks:
                fig.add_vline(x=x_, line=dict(color=colr, width=2, dash=dash))
                # Label to the outside of each line so the two never overlap.
                right = x_ == hi_mark and len(marks) > 1 or len(marks) == 1
                fig.add_annotation(x=x_, y=1.0, yref="paper", text=txt, showarrow=False, font=dict(color=colr, size=11),
                                   yanchor="bottom", xanchor="left" if right else "right", xshift=4 if right else -4)
            fig.update_layout(title="Valuation ranges", yaxis=dict(autorange="reversed", showgrid=False),
                              xaxis=dict(tickprefix="$"), margin=dict(t=60, b=40))
            ui.plotly(fig, 120 + 46 * len(rows))

# ---------------------------------------------------------------------------
# Trade setup: swing entry/exit plan and long-term (core long) checklist
# ---------------------------------------------------------------------------
def swing_rule_setup():
    """The chosen Strategy Lab rule set applied to this stock: where it stands, its rules, and how it traded here."""
    st.subheader(f"Swing trade: {swing_name}")
    if not swing_rules or not swing_rules.get("entry"):
        st.info("This strategy has no buy rules yet. Build one in Strategy Lab → Build and test.")
        return
    st.markdown(f"<div class='sf-card'>{ui.pill(ui.h(sw['label']), sw['tone'])}<span class='sf-note'>{ui.h(sw['note'])}"
                "</span></div>", unsafe_allow_html=True)
    stt = sw["stats"]
    if stt:
        ui.metrics([
            {"label": "Trades (5 years)", "value": f"{stt['Trades']}"},
            {"label": "Winning trades", "value": ui.fmt_pct(stt["Win rate"], 0) if stt["Trades"] else None},
            {"label": "Return per year", "value": ui.fmt_pct(stt["Return per year"]),
             "delta": f"buy & hold {ui.fmt_pct(stt['Buy & hold per year'])}", "delta_color": "off", "delta_arrow": "off"},
            {"label": "Worst drop", "value": ui.fmt_pct(stt["Worst drop"]),
             "delta": f"buy & hold {ui.fmt_pct(stt['Buy & hold worst drop'])}", "delta_color": "off", "delta_arrow": "off"},
            {"label": "Sharpe ratio", "value": ui.fmt_num(stt["Sharpe"]),
             "delta": f"buy & hold {ui.fmt_num(stt['Buy & hold Sharpe'])}", "delta_color": "off", "delta_arrow": "off",
             "help": tip("Sharpe")},
        ], key="swr")
    res = sw.get("result")
    view = hist.iloc[-160:]
    fig = go.Figure()
    fig.add_candlestick(x=view.index, open=view["Open"], high=view["High"], low=view["Low"], close=view["Close"], name=sym,
                        increasing_line_color=ui.GREEN, decreasing_line_color=ui.RED, increasing_fillcolor=ui.GREEN,
                        decreasing_fillcolor=ui.RED)
    if res is not None:
        tr = res["trades"]
        tr = tr[tr["Exit date"] >= view.index[0]] if not tr.empty else tr
        buys = list(tr["Entry date"]) + ([res["open_trade"]["Entry date"]] if res["open_trade"] else [])
        buys = [d for d in buys if d >= view.index[0]]
        if buys:
            fig.add_scatter(x=buys, y=view["Low"].reindex(buys) * 0.985, mode="markers", name="Bought",
                            marker=dict(symbol="triangle-up", size=11, color=ui.GREEN))
        if not tr.empty:
            fig.add_scatter(x=tr["Exit date"], y=view["High"].reindex(tr["Exit date"]) * 1.015, mode="markers",
                            name="Sold", marker=dict(symbol="triangle-down", size=11, color=ui.RED))
    lo_v, hi_v = view["Low"].min(), view["High"].max()
    for zn in zones:
        if lo_v * 0.97 <= zn["mid"] <= hi_v * 1.05 and (zn["touches"] >= 2 or abs(zn["mid"] / price - 1) < 0.05):
            color = "rgba(255,92,122,0.12)" if zn["kind"] == "resistance" else "rgba(45,212,163,0.12)"
            fig.add_hrect(y0=zn["low"] - 0.002 * zn["mid"], y1=zn["high"] + 0.002 * zn["mid"], fillcolor=color, line_width=0)
    fig.update_yaxes(range=[lo_v * 0.95, hi_v * 1.03])
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], rangeslider_visible=False)
    fig.update_layout(title="Daily chart with the rules' trades over the last ~8 months, support (green) and resistance (red)",
                      hovermode="x unified")
    ui.plotly(fig, 440)
    ui.kv([("Nearest resistance", ui.fmt_money(resistance)), ("Nearest support", ui.fmt_money(support)),
           ("Weekly trend", weekly["label"])])
    checks = sw["checks"]
    with st.expander(f"Rules at the last close ({sum(bool(c['Pass']) for c in checks)}/{len(checks)} true)"):
        ui.checklist(checks, "Rule")
    st.caption(swing.NOTE_UNTESTED + " Strategy Lab → Build and test shows the full trade list.")


with tabs[2]:
    pc1, pc2 = st.columns([2, 5], vertical_alignment="bottom")
    with pc1:
        ui.swing_picker("rs")
    pc2.caption(swing.about(swing_name))
    if swing_name == swing.LEADER_DIP:
        st.subheader("Swing trade: Leader Dip (days)",
                     help="SharkFin's swing system: buy a sharp two-day drop in one of the S&P 500's strongest stocks while "
                          "the market is in an uptrend, and sell into the bounce.")
        st.markdown(f"<div class='sf-card'>{ui.pill(ui.h(ld['label']), ld['tone'])}<span class='sf-note'>{ui.h(ld['note'])}"
                    "</span></div>", unsafe_allow_html=True)
        ui.metrics([
            {"label": "2-day RSI", "value": ui.fmt_num(ld["rsi2"], 0), "delta": "buy below 10, sell above 70",
             "delta_color": "off", "delta_arrow": "off", "help": tip("ld_rsi2")},
            {"label": "vs 200-day average", "value": ui.fmt_pct(ld["vs200"], 1, True),
             "delta": ("uptrend" if ld["vs200"] > 0 else "downtrend") if np.isfinite(ld["vs200"]) else None,
             "delta_color": "normal" if ld["vs200"] > 0 else "inverse",
             "delta_arrow": "off", "help": "The stock must close above its 200-day average."},
            {"label": "6-month strength", "value": ui.fmt_pct(ld["rank"], 0) if np.isfinite(ld["rank"]) else None,
             "delta": f"gain {ui.fmt_pct(ld['gain'], 0, True)}", "delta_color": "off", "delta_arrow": "off",
             "help": tip("ld_strength")},
            {"label": "Limit buy" if ld["signal"] else "Limit if it signals", "value": ui.fmt_money(ld["limit"]),
             "delta": "3% under the close", "delta_color": "off", "delta_arrow": "off", "help": tip("ld_limit")},
            {"label": "Market switch", "value": {True: "On", False: "Off", None: None}[ld["market_on"]],
             "delta": f"SPY {ui.fmt_pct(ld['market_gap'], 1, True)} vs 200-day" if np.isfinite(ld["market_gap"]) else None,
             "delta_color": "off", "delta_arrow": "off", "help": tip("ld_switch")},
        ], key="ld")
        st.caption(f"Exit: {leader_dip.EXIT_RULE} Up to {leader_dip.SLOTS} trades at once, each an equal share of the account.")
        if ld["sell_now"]:
            st.info("The 2-day RSI is above 70: if you hold a Leader Dip trade in this stock, it sells at the next open.")

        view = hist.iloc[-160:]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.74, 0.26], vertical_spacing=0.04)
        fig.add_candlestick(x=view.index, open=view["Open"], high=view["High"], low=view["Low"], close=view["Close"], name=sym,
                            increasing_line_color=ui.GREEN, decreasing_line_color=ui.RED, increasing_fillcolor=ui.GREEN,
                            decreasing_fillcolor=ui.RED, row=1, col=1)
        fig.add_scatter(x=view.index, y=ld["sma200_series"].reindex(view.index), name="SMA 200",
                        line=dict(width=1.3, color=ui.MA_COLORS["SMA 200"]), row=1, col=1)
        lo_v, hi_v = view["Low"].min(), view["High"].max()
        for zn in zones:
            if lo_v * 0.97 <= zn["mid"] <= hi_v * 1.05 and (zn["touches"] >= 2 or abs(zn["mid"] / price - 1) < 0.05):
                color = "rgba(255,92,122,0.12)" if zn["kind"] == "resistance" else "rgba(45,212,163,0.12)"
                fig.add_hrect(y0=zn["low"] - 0.002 * zn["mid"], y1=zn["high"] + 0.002 * zn["mid"], fillcolor=color,
                              line_width=0, row=1, col=1)
        if ld["signal"]:
            fig.add_hline(y=ld["limit"], line=dict(color=ui.BLUE, dash="dash", width=1), annotation_text="Limit buy",
                          annotation_position="right", row=1, col=1)
        fig.add_scatter(x=view.index, y=ld["rsi2_series"].reindex(view.index), name="2-day RSI",
                        line=dict(width=1.1, color=ui.PURPLE), row=2, col=1)
        for lvl in (leader_dip.BUY_BELOW, leader_dip.SELL_ABOVE):
            fig.add_hline(y=lvl, line=dict(color=ui.MUTED, dash="dot", width=1), row=2, col=1)
        fig.update_yaxes(range=[lo_v * 0.95, hi_v * 1.03], row=1, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], rangeslider_visible=False)
        fig.update_layout(title="Daily chart with the 200-day, support (green) and resistance (red) zones, and the 2-day RSI",
                          hovermode="x unified")
        ui.plotly(fig, 500)
        ui.kv([("Nearest resistance", ui.fmt_money(resistance)), ("Nearest support", ui.fmt_money(support)),
               ("Weekly trend", weekly["label"])])
        with st.expander(f"Leader Dip checklist ({sum(bool(c['Pass']) for c in ld['checklist'])}/{len(ld['checklist'])} pass)"):
            ui.checklist(ld["checklist"], "Rule")
            st.caption("Strength is ranked against every S&P 500 stock's 6-month gain. Strategy Lab → Leader Dip backtests "
                       "the system on the whole index.")
    else:
        swing_rule_setup()

    st.subheader("Long-term hold (months to years)", help=tip("core_long"))
    st.markdown(f"<div class='sf-card'>{ui.pill(core['verdict'], core['tone'])}<span class='sf-note'>"
                f"{core['passed']} of {core['total']} long-term checks pass.</span></div>", unsafe_allow_html=True)
    ui.checklist(core["rows"], "Test")
    vr = catalysts.volume_read(hist)
    nxt = f" Next report: {earn['next_date']:%b %d, %Y}." if earn.get("next_date") is not None else ""
    st.markdown(f"<div class='sf-card sf-note'><b>Earnings.</b> {ui.h(earn['note'])}{ui.h(nxt)}<br><b>Insiders.</b> "
                f"{ui.h(ins['note'])}<br><b>Volume.</b> {ui.h(vr['note'])}</div>", unsafe_allow_html=True)
    st.caption("SEC filings, 8-K events, buybacks and annual-report changes are on News Desk → Catalysts.")

# ---------------------------------------------------------------------------
# Financials (health scores + statements)
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Financial health")
    ui.metrics([
        {"label": "Piotroski F-score", "value": f"{f_score.score}/9 · {f_score.label}" if f_score else None,
         "help": "Nine pass/fail tests of profitability, debt and efficiency (Piotroski 2000). 7-9 is strong, 0-3 weak."},
        {"label": "Altman Z-score", "value": f"{z.score:.1f} · {z.label}" if z else None,
         "help": "Bankruptcy-risk score. Above 3 is safe, 1.8-3 grey zone, below 1.8 distress. Not used for banks."},
        {"label": "ROIC", "value": ui.fmt_pct(qm.get("ROIC")),
         "help": "After-tax operating profit / (debt + equity − cash). Above ~10% means the business earns more than it costs to fund."},
        {"label": "Return on equity", "value": ui.fmt_pct(qm.get("ROE"))},
        {"label": "Operating margin", "value": ui.fmt_pct(qm.get("Operating margin"))},
        {"label": "FCF margin", "value": ui.fmt_pct(qm.get("FCF margin"))},
        {"label": "Net debt / EBITDA", "value": ui.fmt_x(qm.get("Net debt / EBITDA"), 1) if ui.num(qm.get("Net debt / EBITDA")) > 0
         else ("Net cash" if np.isfinite(ui.num(qm.get("Net debt / EBITDA"))) else None),
         "help": "Years of operating earnings needed to pay off net debt. Below 2x is comfortable, above 4x is stretched."},
        {"label": "3-yr revenue growth", "value": ui.fmt_pct(qm.get("Revenue CAGR (3y)"), 1, True)},
    ], key="health")
    ui.kv([
        ("Gross margin", ui.fmt_pct(qm.get("Gross margin"))),
        ("Gross profit / assets", ui.fmt_pct(qm.get("Gross profitability (GP/TA)"))),
        ("Interest coverage", ui.fmt_x(qm.get("Interest coverage (EBIT/int)"), 1)),
        ("Cash conversion (CFO / net income)", ui.fmt_x(qm.get("Cash conversion (CFO/NI)"), 2)),
        ("Accruals (NI − CFO) / assets", ui.fmt_pct(qm.get("Sloan accruals (NI-CFO)/TA"))),
        ("Stock comp / revenue", ui.fmt_pct(qm.get("SBC / revenue"))),
        ("Free cash flow yield", ui.fmt_pct(qm.get("FCF yield"))),
        ("Earnings yield", ui.fmt_pct(qm.get("Earnings yield"))),
    ])
    st.caption("A business creates value when its return on capital beats its cost of capital. Negative accruals (cash "
               "earnings above book earnings) have historically gone with better future returns.")
    if f_score or z:
        with st.expander("Score details"):
            if f_score:
                st.dataframe(pd.DataFrame(f_score.components, columns=["Piotroski test", "Pass", "Detail"]),
                             hide_index=True, width="stretch")
            if z:
                st.dataframe(pd.DataFrame([(n, ui.fmt_num(v), w_) for n, v, w_ in z.components],
                                          columns=["Altman component", "Value", "Weight"]), hide_index=True, width="stretch")

    period = st.segmented_control("Statements", ["Annual", "Quarterly"], default="Annual", key="fin_period")
    F = fin if period != "Quarterly" else qfin
    lines = {"Revenue": F.revenue(), "Gross profit": F.gross_profit(), "Operating income": F.ebit(),
             "Net income": F.net_income(), "Free cash flow": F.fcf()}
    df = pd.DataFrame(lines).sort_index().dropna(how="all")
    if df.empty:
        st.info("Yahoo has no financial statements for this company.")
    else:
        df.index = pd.to_datetime(df.index).strftime("%b %Y" if period == "Quarterly" else "FY%Y")
        scale, unit = (1e9, "B") if np.nanmax(np.abs(df.values)) >= 1e9 else (1e6, "M")
        l, r_ = st.columns(2)
        with l:
            fig = go.Figure()
            for c in df.columns:
                fig.add_bar(x=df.index, y=df[c] / scale, name=c)
            fig.update_layout(title=f"Income and cash flow (${unit})", barmode="group", yaxis=dict(tickprefix="$", ticksuffix=unit))
            ui.plotly(fig, 360)
        with r_:
            rev = df["Revenue"].where(df["Revenue"] > 0)
            margins = pd.DataFrame({"Gross": df["Gross profit"] / rev, "Operating": df["Operating income"] / rev,
                                    "Net": df["Net income"] / rev, "FCF": df["Free cash flow"] / rev}).dropna(axis=1, how="all")
            fig = go.Figure([go.Scatter(x=margins.index, y=margins[c] * 100, name=c, mode="lines+markers") for c in margins])
            fig.update_layout(title="Margins", yaxis=dict(ticksuffix="%"))
            ui.plotly(fig, 360)
        with st.expander("Full statements"):
            for label, frame in (("Income statement", F.income), ("Balance sheet", F.balance), ("Cash flow", F.cashflow)):
                if frame is not None and not frame.empty:
                    fr = frame.dropna(how="all")
                    fr.columns = pd.to_datetime(fr.columns).strftime("%b %Y" if period == "Quarterly" else "FY%Y")
                    st.markdown(f"**{label}**")
                    st.dataframe(ui.compact_frame(fr), width="stretch")
            st.caption("Values in US dollars (K = thousand, M = million, B = billion, T = trillion), except per-share and ratio lines.")

# ---------------------------------------------------------------------------
# Analysts & news
# ---------------------------------------------------------------------------
analyst = {"target_low": lo_t, "target_mean": mean_t, "target_high": hi_t,
           "recommendation": inf.get("recommendationKey"), "n_analysts": inf.get("numberOfAnalystOpinions")}
news_agg, ranked = {}, []
with tabs[4]:
    st.subheader("Wall Street view")
    rec = str(inf.get("recommendationKey") or "").replace("_", " ").title()
    n_an = inf.get("numberOfAnalystOpinions")
    ui.metrics([
        {"label": "Consensus", "value": rec if rec and rec != "None" else None,
         "delta": f"{n_an} analysts" if n_an else None, "delta_color": "off", "delta_arrow": "off"},
        {"label": "Average target", "value": ui.fmt_money(mean_t),
         "delta": ui.fmt_pct(mean_t / price - 1, 1, True) if np.isfinite(mean_t) else None},
        {"label": "Target range", "value": f"{ui.fmt_money(lo_t, 0)} – {ui.fmt_money(hi_t, 0)}"
         if np.isfinite(lo_t) and np.isfinite(hi_t) else None},
        {"label": "Next earnings", "value": f"{earn['next_date']:%b %d}" if earn.get("next_date") is not None else None},
        {"label": "EPS surprise", "value": ui.fmt_pct(earn["last_surprise"], 1, True),
         "help": "How far reported earnings per share beat (+) or missed (−) the average estimate."},
    ], key="street")
    rb = catalysts.revision_balance(ad.get("eps_revisions"))
    revs = ad.get("eps_revisions")
    if isinstance(revs, pd.DataFrame) and not revs.empty and {"upLast30days", "downLast30days"} <= set(revs.columns):
        up_, dn_ = int(pd.to_numeric(revs["upLast30days"], errors="coerce").sum()), int(pd.to_numeric(revs["downLast30days"], errors="coerce").sum())
        st.markdown(f"<div class='sf-note'>Estimate revisions, last 30 days: <b class='sf-up'>{up_} up</b> and "
                    f"<b class='sf-down'>{dn_} down</b> across the current and next quarter and year. Rising estimates "
                    "tend to lead rising prices.</div>", unsafe_allow_html=True)
        analyst["revision_balance_30d"] = rb
    l, r_ = st.columns(2)
    rs = ad.get("recommendations_summary")
    if isinstance(rs, pd.DataFrame) and not rs.empty:
        cols = [c for c in ("strongBuy", "buy", "hold", "sell", "strongSell") if c in rs.columns]
        names = {"strongBuy": "Strong buy", "buy": "Buy", "hold": "Hold", "sell": "Sell", "strongSell": "Strong sell"}
        months = {"0m": "This month", "-1m": "1 month ago", "-2m": "2 months ago", "-3m": "3 months ago"}
        x = [months.get(p, p) for p in rs.get("period", rs.index)]
        fig = go.Figure()
        for col, colr in zip(cols, [ui.GREEN, "#7ee0bf", "#5b6574", "#ff9fb0", ui.RED]):
            fig.add_bar(x=x, y=rs[col], name=names[col], marker_color=colr)
        fig.update_layout(barmode="stack", title="Analyst ratings", xaxis=dict(autorange="reversed"))
        with l:
            ui.plotly(fig, 330)
    ed = ad.get("earnings_dates")
    if isinstance(ed, pd.DataFrame) and not ed.empty and "Reported EPS" in ed:
        e = ed.dropna(subset=["Reported EPS"]).head(8).iloc[::-1]
        analyst["recent_eps_surprises_pct"] = e.get("Surprise(%)", pd.Series(dtype=float)).tail(4).tolist()
        xs = pd.to_datetime(e.index).strftime("%b '%y")
        fig = go.Figure()
        fig.add_scatter(x=xs, y=e["EPS Estimate"], name="Estimate", mode="markers", marker=dict(size=12, color="#5b6574"))
        fig.add_scatter(x=xs, y=e["Reported EPS"], name="Reported", mode="markers",
                        marker=dict(size=12, color=np.where(e["Reported EPS"] >= e["EPS Estimate"], ui.GREEN, ui.RED)))
        fig.update_layout(title="Earnings per share: estimate vs reported", yaxis=dict(tickprefix="$"))
        with r_:
            ui.plotly(fig, 330)
    ud = ad.get("upgrades_downgrades")
    if isinstance(ud, pd.DataFrame) and not ud.empty and "Firm" in ud:
        acts = {"up": "Upgrade", "down": "Downgrade", "main": "Maintained", "reit": "Reiterated", "init": "Initiated"}
        u = ud.head(15).copy()
        tbl = pd.DataFrame({
            "Date": pd.to_datetime(u.index).date, "Firm": u["Firm"].values,
            "Action": [acts.get(str(a), str(a).title()) for a in u.get("Action", "")],
            "Rating": [f"{f} → {t}" if f and f != t else t for f, t in zip(u.get("FromGrade", ""), u.get("ToGrade", ""))],
            "Target": pd.to_numeric(u.get("currentPriceTarget"), errors="coerce").replace(0, np.nan).values})
        with st.expander("Recent rating changes"):
            st.dataframe(tbl, hide_index=True, width="stretch",
                         column_config={"Target": st.column_config.NumberColumn("Price target", format="$%.0f")})

    st.subheader("News")
    arts = data.news(f"{name} {sym}", symbol=sym)
    ranked = sentiment.rank_articles(arts, f"{sym} {name}")
    news_agg = sentiment.aggregate_sentiment(ranked[:30])
    if not ranked:
        st.info("No recent news found.")
    else:
        st.markdown(ui.pill(f"Tone: {news_agg['label']}", ui.tone(news_agg["score"], 0.1)) +
                    f"<span class='sf-muted'>{news_agg['positive']} positive · {news_agg['negative']} negative · "
                    f"{news_agg['n']} stories after removing duplicates</span>", unsafe_allow_html=True)
        for a in ranked[:15]:
            ui.news_item(a)

# ---------------------------------------------------------------------------
# At a glance (top of the overview tab)
# ---------------------------------------------------------------------------
with glance:
    ui.metrics([
        {"label": "Fair value", "value": ui.fmt_money(fv["fair_value"]) if np.isfinite(fv["fair_value"]) else None,
         "delta": f"{ui.fmt_pct(fv['upside'], 0, True)} · {fv['label'].replace('Significantly ', 'very ').lower()}"
         if np.isfinite(fv["fair_value"]) else None,
         "delta_color": "normal" if abs(fv["upside"]) >= 0.1 else "off",
         "help": "Blend of intrinsic value, peer multiples and analyst targets. Details on the Valuation tab."},
        {"label": f"Swing ({swing_name})", "value": ld["label"],
         "delta": f"2-day RSI {ld['rsi2']:.0f}" if np.isfinite(ld["rsi2"]) else None,
         "delta_color": "off", "delta_arrow": "off", "help": "SharkFin's Leader Dip swing system. Details on Trade setup."}
        if sw is None else
        {"label": f"Swing ({swing_name})", "value": sw["label"], "help": "Your chosen swing strategy. Details on Trade setup."},
        {"label": "Long-term", "value": {"pos": "Candidate", "neu": "Watch", "neg": "Not now"}[core["tone"]]
         if core["total"] else None, "delta": f"{core['passed']}/{core['total']} checks",
         "delta_color": "off", "delta_arrow": "off", "help": tip("core_long")},
        {"label": "Analysts", "value": rec if rec and rec != "None" else None,
         "delta": f"target {ui.fmt_pct(mean_t / price - 1, 0, True)}" if np.isfinite(mean_t) else None,
         "help": "Consensus rating and the average price target vs today's price."},
        {"label": "Financial strength", "value": f"F-score {f_score.score}/9" if f_score else None,
         "delta": f_score.label if f_score else None, "delta_color": "off", "delta_arrow": "off",
         "help": "Piotroski F-score. Details on the Financials tab."},
    ], key="glance")

# ---------------------------------------------------------------------------
# AI analyst
# ---------------------------------------------------------------------------
if ai.available():
    with tabs[5]:
        st.markdown("Claude reads everything SharkFin computed for this stock (valuation, quality, analyst data, "
                    "news and the price data) and writes a structured research note.")
        if st.button("Write research note", type="primary"):
            panel = ind.compute_all(hist)
            dossier = {
                "symbol": sym, "name": name, "sector": inf.get("sector"), "industry": inf.get("industry"),
                "price": price, "market_cap": mcap, "net_debt": net_debt,
                "returns": {"1m": hist["Close"].iloc[-1] / hist["Close"].iloc[-22] - 1,
                            "1y": hist["Close"].iloc[-1] / hist["Close"].iloc[-253] - 1 if len(hist) > 253 else None},
                "risk": dict(risk.summary(r_all.iloc[-756:], rf=rf)),
                "technical_signal": {k: v for k, v in ind.technical_signal(panel).items() if k != "evidence"},
                "multiples": {k: inf.get(k) for k in ("trailingPE", "forwardPE", "pegRatio", "enterpriseToEbitda",
                                                       "enterpriseToRevenue", "priceToBook")},
                "growth": {"revenue_growth_yoy": rev_g, "earnings_growth_yoy": ui.num(inf.get("earningsGrowth")),
                           "revenue_cagr_3y": fin.revenue_cagr(3)},
                "dcf": dcf_out or "not applicable", "bank_model": bank_out or None, "fair_value": fv,
                "quality": {"piotroski": f_score.score if f_score else None, "altman_z": z.score if z else None, **qm},
                "analysts": analyst, "news_sentiment": news_agg,
                "swing_setup_leader_dip": {k: ld.get(k) for k in ("label", "note", "rsi2", "vs200", "gain", "rank",
                                                                   "limit", "market_on")},
                "swing_setup_chosen": {"strategy": swing_name, **({k: sw.get(k) for k in ("label", "note")} if sw else {})},
                "levels": {"resistance": resistance, "support": support},
                "weekly_trend": weekly,
                "core_long": {"verdict": core.get("verdict"), "passed": core.get("passed"), "total": core.get("total")},
                "headlines": [{"title": a["title"], "sentiment": round(a["sentiment"], 2), "publisher": a.get("publisher")}
                              for a in ranked[:15]],
            }
            st.write_stream(ai.stream_report(dossier))

ui.disclaimer()
