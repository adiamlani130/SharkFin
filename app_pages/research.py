"""Single-stock research: chart, fundamentals, valuation lab, quality, analysts, news, AI note."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import ai, data, risk, sentiment, ui, valuation
from sharkfin import indicators as ind

st.title("Research & Valuation")

top = st.columns([3, 1])
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
    st.write("")
    st.write("")
    wl = st.session_state.watchlist
    if sym in wl:
        if st.button("★ On watchlist", width="stretch"):
            wl.remove(sym)
            ui.save_state()
            st.rerun()
    elif st.button("☆ Add to watchlist", type="primary", width="stretch"):
        wl.append(sym)
        ui.save_state()
        st.rerun()

prev = inf.get("previousClose") or (hist["Close"].iloc[-2] if len(hist) > 1 else price)
chg = price / prev - 1 if prev else np.nan
st.markdown(f"### {name} ({sym})  \n"
            f"<span style='font-size:1.8rem;font-weight:700'>${price:,.2f}</span> "
            f"{ui.pill(ui.fmt_pct(chg, 2, True), ui.tone(chg))}"
            f"<span class='sf-muted'>{inf.get('sector', '')} · {inf.get('industry', '')} · {inf.get('exchange', '')}</span>",
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
    n = lambda c: pd.to_numeric(df.get(c), errors="coerce") if c in df else pd.Series(np.nan, index=df.index)
    out = pd.DataFrame({
        "Name": df.get("shortName", pd.Series(index=df.index, dtype=object)),
        "Market cap": n("marketCap"),
        "P/E (fwd)": n("forwardPE"), "P/E (ttm)": n("trailingPE"),
        "EV/EBITDA": n("enterpriseToEbitda"), "EV/Sales": n("enterpriseToRevenue"),
        "P/FCF": n("marketCap") / n("freeCashflow").where(lambda x: x > 0), "P/B": n("priceToBook"),
        "revenue_growth": n("revenueGrowth"), "ebitda_margin": n("ebitdaMargins"),
        "ROE": n("returnOnEquity"), "Gross margin": n("grossMargins"),
    })
    return out


fin = data.financials(sym)
qfin = data.quarterly_financials(sym)
rf = data.risk_free_rate()
shares = ui.num(inf.get("sharesOutstanding"), ui.num(inf.get("impliedSharesOutstanding")))
mcap = ui.num(inf.get("marketCap"), price * shares if shares else np.nan)
total_debt = ui.num(inf.get("totalDebt"), valuation._v(fin.total_debt(), 0, 0.0))
total_cash = ui.num(inf.get("totalCash"), valuation._v(fin.cash(), 0, 0.0))
net_debt = (total_debt if np.isfinite(total_debt) else 0) - (total_cash if np.isfinite(total_cash) else 0)
is_financial = str(inf.get("sector", "")).lower().startswith("financial")

tabs = st.tabs(["📈 Chart & Stats", "💰 Valuation Lab", "🧪 Quality", "🧾 Financials", "🎯 Analysts", "📰 News", "🤖 AI Analyst"])

# ---------------------------------------------------------------------------
# Chart & stats
# ---------------------------------------------------------------------------
with tabs[0]:
    c1, c2, c3 = st.columns([2, 2, 3])
    tf = c1.segmented_control("Range", ["1M", "3M", "6M", "YTD", "1Y", "2Y", "5Y"], default="1Y", key="rs_tf")
    overlays = c2.multiselect("Overlays", ["SMA 20", "SMA 50", "SMA 200", "EMA 21", "Bollinger", "VWAP"],
                              default=["SMA 50", "SMA 200"])
    lower = c3.multiselect("Panels", ["Volume", "RSI", "MACD"], default=["Volume", "RSI"])
    days = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252, "2Y": 504, "5Y": 1260}
    if tf == "YTD":
        view = hist[hist.index.year == hist.index[-1].year]
    else:
        view = hist.iloc[-days.get(tf or "1Y", 252):]
    # Compute overlays on full history, then slice, so long MAs aren't truncated.
    full = ui.price_chart(hist, sym, overlays, lower)
    full.update_xaxes(range=[view.index[0], view.index[-1]])
    lo, hi = view["Low"].min(), view["High"].max()
    full.update_yaxes(range=[lo * 0.97, hi * 1.03], row=1, col=1)
    ui.plotly(full)

    r = hist["Close"].pct_change().dropna()
    cols = st.columns(6)
    stats = [
        ("Market cap", ui.fmt_money(mcap)), ("Enterprise value", ui.fmt_money(ui.num(inf.get("enterpriseValue")))),
        ("P/E (ttm / fwd)", f"{ui.fmt_num(ui.num(inf.get('trailingPE')), 1)} / {ui.fmt_num(ui.num(inf.get('forwardPE')), 1)}"),
        ("EV/EBITDA", ui.fmt_num(ui.num(inf.get("enterpriseToEbitda")), 1)),
        # yfinance reports dividendYield in percent; trailingAnnualDividendYield is a decimal.
        ("Dividend yield", ui.fmt_pct(ui.num(inf.get("dividendYield")) / 100 if inf.get("dividendYield") is not None
                                      else ui.num(inf.get("trailingAnnualDividendYield")), 2)),
        ("52w range", f"{ui.fmt_num(ui.num(inf.get('fiftyTwoWeekLow')))} – {ui.fmt_num(ui.num(inf.get('fiftyTwoWeekHigh')))}"),
        ("1Y return", ui.fmt_pct(hist["Close"].iloc[-1] / hist["Close"].iloc[-253] - 1 if len(hist) > 253 else np.nan, sign=True)),
        ("Volatility (1y)", ui.fmt_pct(risk.annualized_vol(r.iloc[-252:]))),
        ("Max drawdown (5y)", ui.fmt_pct(risk.max_drawdown(r))),
        ("Sharpe (5y)", ui.fmt_num(risk.sharpe_ratio(r, rf))),
        ("Beta (3y weekly, adj.)", ui.fmt_num(market_beta(sym)[1])),
        ("Short % float", ui.fmt_pct(ui.num(inf.get("shortPercentOfFloat")))),
    ]
    for i, (k, v) in enumerate(stats):
        cols[i % 6].metric(k, v)
    if inf.get("longBusinessSummary"):
        with st.expander("Business description"):
            st.write(inf["longBusinessSummary"])

# ---------------------------------------------------------------------------
# Valuation lab
# ---------------------------------------------------------------------------
dcf_out = {}
with tabs[1]:
    raw_beta, adj_beta = market_beta(sym)
    beta0 = adj_beta if np.isfinite(adj_beta) else ui.num(inf.get("beta"), 1.0)
    ttm_fcf = data.ttm(qfin.fcf())
    analyst_g = ui.num(inf.get("earningsGrowth"))
    rev_g = ui.num(inf.get("revenueGrowth"))
    # Yahoo's earningsGrowth is last quarter's YoY change, which swings wildly
    # for cyclicals (XOM +113%), so it is no basis for five years of FCF growth.
    # Use consensus next-year growth and revenue growth instead.
    fwd_g = valuation.forward_growth(data.analyst_data(sym).get("growth_estimates"))
    g_default = valuation.default_growth(fin, fwd_g, rev_g)

    if is_financial:
        st.warning("Free-cash-flow DCFs are not meaningful for banks and insurers (debt is raw material, not financing). "
                   "Lean on P/B, P/E and the quality scores for this company.")

    with st.expander("⚙️ DCF assumptions", expanded=False):
        a1, a2, a3, a4 = st.columns(4)
        growth = a1.slider("Stage-1 FCF growth", -0.10, 0.40, float(round(g_default, 3)), 0.005, format="%.3f",
                           help="Default is the median of consensus next-year growth, latest revenue growth and 3-year revenue CAGR.")
        hg_years = a1.slider("High-growth years", 3, 10, 5)
        tg = a2.slider("Terminal growth", 0.0, 0.04, float(min(0.025, rf)), 0.0025,
                       help="Capped near the risk-free rate: no company outgrows the economy forever.")
        erp = a2.slider("Equity risk premium", 0.03, 0.07, valuation.DEFAULT_ERP, 0.0025)
        beta = a3.number_input("Beta (Blume-adjusted, 3y weekly)", 0.3, 3.0, float(np.clip(beta0, 0.3, 3.0)), 0.05)
        sbc = a3.toggle("Treat stock comp as a cash cost", value=True,
                        help="Subtracts stock-based compensation from FCF, which otherwise overstates owner earnings.")
        a4.metric("Risk-free (10Y UST)", ui.fmt_pct(rf, 2))
        a4.metric("Raw regression beta", ui.fmt_num(raw_beta))

    fcf0 = valuation.normalized_fcf(fin, ttm_fcf, subtract_sbc=sbc)
    w = valuation.wacc(mcap, total_debt, beta, rf, erp, valuation._v(fin.interest_expense()), fin.effective_tax_rate())

    valid_dcf = np.isfinite(fcf0) and fcf0 > 0 and shares and np.isfinite(shares) and w.wacc > tg + 0.005
    if valid_dcf:
        res = valuation.dcf(fcf0, growth, w.wacc, tg, net_debt, shares, hg_years, 5)
        implied_g = valuation.reverse_dcf(price, fcf0, w.wacc, tg, net_debt, shares)
        sims = valuation.monte_carlo_dcf(fcf0, growth, w.wacc, tg, net_debt, shares)
        p_under = float((sims > price).mean())
        dcf_out = {"value": res.value_per_share, "upside": res.value_per_share / price - 1, "wacc": w.wacc,
                   "growth": growth, "terminal_growth": tg, "implied_growth": implied_g, "p_undervalued": p_under,
                   "terminal_share_of_ev": res.terminal_share, "fcf0": fcf0,
                   "mc_p10": float(np.percentile(sims, 10)), "mc_p90": float(np.percentile(sims, 90))}
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("DCF value / share", ui.fmt_money(res.value_per_share), ui.fmt_pct(dcf_out["upside"], 1, True))
        m2.metric("WACC", ui.fmt_pct(w.wacc, 2), f"Ke {w.cost_of_equity:.1%}, Kd {w.cost_of_debt_after_tax:.1%}",
                  delta_color="off", help="Cost of equity (CAPM) and after-tax cost of debt, market-value weighted.")
        m3.metric("Implied growth", ui.fmt_pct(implied_g), f"vs your {growth:.1%}", delta_color="off",
                  help="Reverse DCF: the stage-1 growth the current price requires.")
        m4.metric("P(undervalued)", ui.fmt_pct(p_under, 0), help="Share of 5,000 Monte Carlo DCFs above the current price.")
        m5.metric("Terminal % of EV", ui.fmt_pct(res.terminal_share, 0))
        m6.metric("Starting FCF", ui.fmt_money(fcf0))
        col_l, col_r = st.columns([1, 1])
        with col_l:
            years = [f"Y{i}" for i in range(1, len(res.fcf_path) + 1)]
            fig = go.Figure()
            fig.add_bar(x=years, y=res.fcf_path, name="Projected FCF", marker_color=ui.BLUE)
            fig.add_bar(x=years, y=res.fcf_path * res.discount_factors, name="Present value", marker_color=ui.GREEN)
            fig.add_scatter(x=years, y=res.growth_path * 100, name="Growth %", yaxis="y2", line=dict(color=ui.ORANGE))
            fig.update_layout(title="Free cash flow projection", barmode="group",
                              yaxis2=dict(overlaying="y", side="right", showgrid=False, title="growth %"))
            ui.plotly(fig, 360)
        with col_r:
            grid = valuation.sensitivity_grid(fcf0, growth, w.wacc, tg, net_debt, shares)
            up = grid / price - 1
            fig = go.Figure(go.Heatmap(z=np.clip(up.values * 100, -100, 100), x=grid.columns, y=grid.index, zmid=0,
                                       colorscale=[[0, ui.RED], [0.5, "#1f2937"], [1, ui.GREEN]],
                                       text=[[f"${v:,.0f}" if np.isfinite(v) else "n/a" for v in row] for row in grid.values], texttemplate="%{text}",
                                       colorbar=dict(title="Upside %")))
            fig.update_layout(title="Sensitivity: WACC × terminal growth", xaxis_title="Terminal growth", yaxis_title="WACC")
            ui.plotly(fig, 330)
            fig = go.Figure(go.Histogram(x=np.clip(sims, 0, np.percentile(sims, 99)), nbinsx=60, marker_color=ui.BLUE))
            fig.add_vline(x=price, line=dict(color=ui.ORANGE, width=2), annotation_text="Price")
            fig.update_layout(title="Monte Carlo DCF (growth, WACC, terminal g, FCF uncertainty)", showlegend=False)
            ui.plotly(fig, 300)
    else:
        st.info("DCF skipped: normalised free cash flow is negative or data is missing. "
                "Use relative valuation below; a reverse DCF isn't meaningful without positive cash flow.")

    st.markdown("#### Relative valuation vs peers")
    with st.spinner("Pulling peer multiples…"):
        peers = peer_table(sym, {k: inf.get(k) for k in ("industry", "sector", "marketCap")})
    rel_value = np.nan
    if not peers.empty:
        target = {"price": price, "shares": shares, "net_debt": net_debt,
                  "forward_eps": ui.num(inf.get("forwardEps")), "trailing_eps": ui.num(inf.get("trailingEps")),
                  "ebitda": ui.num(inf.get("ebitda")), "revenue": ui.num(inf.get("totalRevenue")),
                  "fcf_per_share": ui.num(inf.get("freeCashflow")) / shares if shares else np.nan,
                  "book_per_share": ui.num(inf.get("bookValue")),
                  "P/E (fwd)": ui.num(inf.get("forwardPE")), "P/E (ttm)": ui.num(inf.get("trailingPE")),
                  "EV/EBITDA": ui.num(inf.get("enterpriseToEbitda")), "EV/Sales": ui.num(inf.get("enterpriseToRevenue")),
                  "P/FCF": mcap / ui.num(inf.get("freeCashflow")) if ui.num(inf.get("freeCashflow"), 0) > 0 else np.nan,
                  "P/B": ui.num(inf.get("priceToBook")),
                  "revenue_growth": rev_g, "ebitda_margin": ui.num(inf.get("ebitdaMargins"))}
        imp = valuation.implied_prices(target, peers)
        reg = valuation.regression_multiple(peers, target)
        l, r_ = st.columns([3, 2])
        with l:
            if not imp.empty:
                use = imp[~imp["Multiple"].isin(["P/B"])] if not is_financial else imp
                rel_value = float(np.exp(np.log(use["Median"].clip(lower=0.01)).mean())) if len(use) else np.nan
                fig = go.Figure()
                for _, row in imp.iterrows():
                    fig.add_trace(go.Scatter(x=[row["Low (25th)"], row["High (75th)"]], y=[row["Multiple"]] * 2, mode="lines",
                                             line=dict(color=ui.BLUE, width=10), showlegend=False))
                    fig.add_trace(go.Scatter(x=[row["Median"]], y=[row["Multiple"]], mode="markers",
                                             marker=dict(color="white", size=11, symbol="line-ns-open"), showlegend=False))
                fig.add_vline(x=price, line=dict(color=ui.ORANGE, width=2), annotation_text=f"Price ${price:,.0f}")
                fig.update_layout(title="Implied price range from peer multiples (25th–75th pct, median)")
                ui.plotly(fig, 320)
                st.dataframe(imp, hide_index=True, width="stretch", column_config={
                    c: st.column_config.NumberColumn(format="$%.2f") for c in ("Low (25th)", "Median", "High (75th)")} | {
                    "Upside (median)": st.column_config.NumberColumn(format="percent"),
                    "Target": st.column_config.NumberColumn(format="%.1fx"),
                    "Peer median multiple": st.column_config.NumberColumn(format="%.1fx")})
        with r_:
            if reg:
                ev_fit = reg["fitted"] * target["revenue"]
                reg_price = (ev_fit - net_debt) / shares if shares else np.nan
                st.metric("Fundamentals-adjusted EV/Sales", f"{reg['fitted']:.2f}x",
                          f"actual {ui.fmt_num(target['EV/Sales'])}x", delta_color="off",
                          help=f"OLS of log(EV/Sales) on revenue growth and EBITDA margin across {reg['n']} peers (R² {reg['r2']:.2f}).")
                st.metric("Regression-implied price", ui.fmt_money(reg_price), ui.fmt_pct(reg_price / price - 1, 1, True))
                sc = peers[["EV/Sales", "revenue_growth", "Name"]].dropna()
                fig = go.Figure(go.Scatter(x=sc["revenue_growth"] * 100, y=sc["EV/Sales"], mode="markers+text",
                                           text=sc.index, textposition="top center", marker=dict(color=ui.BLUE, size=9),
                                           name="Peers"))
                fig.add_trace(go.Scatter(x=[rev_g * 100], y=[target["EV/Sales"]], mode="markers+text", text=[sym],
                                         marker=dict(color=ui.ORANGE, size=14, symbol="star"), name=sym, textposition="top center"))
                fig.update_layout(title="EV/Sales vs revenue growth", xaxis_title="Revenue growth %", yaxis_title="EV/Sales")
                ui.plotly(fig, 320)
        with st.expander("Peer comparison table"):
            st.dataframe(peers, width="stretch")
    else:
        st.info("No peer set available for this ticker.")

    st.markdown("#### Blended fair value")
    tgt_mean = ui.num(inf.get("targetMeanPrice"))
    fv = valuation.fair_value_summary(price, {
        "DCF": (dcf_out.get("value", np.nan), 0.0 if is_financial else 0.4),
        "Peer multiples": (rel_value, 0.4),
        "Analyst consensus": (tgt_mean, 0.2),
    })
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Blended fair value", ui.fmt_money(fv["fair_value"]), ui.fmt_pct(fv["upside"], 1, True))
    b2.metric("Verdict", fv["label"])
    b3.metric("Peer-multiple value", ui.fmt_money(rel_value))
    b4.metric("Analyst mean target", ui.fmt_money(tgt_mean))
    st.caption("Weighted geometric mean of DCF (40%), peer multiples (40%) and analyst consensus (20%); missing methods are re-weighted.")

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------
quality = {}
with tabs[2]:
    f_score = valuation.piotroski_f_score(fin)
    z = valuation.altman_z(fin, mcap)
    qm = valuation.quality_metrics(fin, mcap)
    z = None if is_financial else z
    quality = {"piotroski": f_score.score if f_score else None, "altman_z": z.score if z else None,
               "altman_zone": z.label if z else None, **qm}
    c1, c2 = st.columns(2)
    with c1:
        if f_score:
            st.metric("Piotroski F-score", f"{f_score.score}/9 · {f_score.label}",
                      help="9 binary tests of profitability, leverage/liquidity and operating efficiency (Piotroski 2000).")
            st.dataframe(pd.DataFrame(f_score.components, columns=["Test", "Pass", "Detail"]), hide_index=True, width="stretch")
        else:
            st.info("Not enough statement history for a Piotroski score.")
    with c2:
        if is_financial:
            st.info("Altman Z-score is skipped for banks and insurers: their balance sheets are mostly debt by design, "
                    "so the model flags nearly all of them as distressed.")
        elif z:
            st.metric("Altman Z-score", f"{z.score:.2f} · {z.label}",
                      help=">2.99 safe, 1.81–2.99 grey, <1.81 distress (original public-company model; less reliable for financials).")
            st.dataframe(pd.DataFrame(z.components, columns=["Component", "Value", "Weight"]), hide_index=True, width="stretch")
    st.markdown("#### Profitability, cash quality & leverage")
    pct_keys = {"ROIC", "ROE", "Gross profitability (GP/TA)", "Gross margin", "Operating margin", "FCF margin",
                "Sloan accruals (NI-CFO)/TA", "SBC / revenue", "Revenue CAGR (3y)", "FCF yield", "Earnings yield"}
    cols = st.columns(4)
    for i, (k, v) in enumerate(qm.items()):
        cols[i % 4].metric(k, ui.fmt_pct(v) if k in pct_keys else ui.fmt_num(v))
    st.caption("ROIC above WACC means value creation. Negative Sloan accruals (cash earnings > book earnings) historically predict higher returns.")

# ---------------------------------------------------------------------------
# Financials
# ---------------------------------------------------------------------------
with tabs[3]:
    period = st.segmented_control("Period", ["Annual", "Quarterly"], default="Annual", key="fin_period")
    F = fin if period != "Quarterly" else qfin
    lines = {"Revenue": F.revenue(), "Gross profit": F.gross_profit(), "Operating income": F.ebit(),
             "Net income": F.net_income(), "Free cash flow": F.fcf()}
    df = pd.DataFrame(lines).sort_index()
    if df.dropna(how="all").empty:
        st.info("No financial statements available.")
    else:
        df.index = pd.to_datetime(df.index).strftime("%Y-%m" if period == "Quarterly" else "%Y")
        fig = go.Figure()
        for c in df.columns:
            fig.add_bar(x=df.index, y=df[c], name=c)
        fig.update_layout(title="Income & cash flow", barmode="group")
        ui.plotly(fig, 380)
        rev = df["Revenue"]
        margins = pd.DataFrame({"Gross": df["Gross profit"] / rev, "Operating": df["Operating income"] / rev,
                                "Net": df["Net income"] / rev, "FCF": df["Free cash flow"] / rev}) * 100
        fig = go.Figure([go.Scatter(x=margins.index, y=margins[c], name=c, mode="lines+markers") for c in margins])
        fig.update_layout(title="Margins (%)")
        ui.plotly(fig, 320)
        with st.expander("Raw statements"):
            for label, frame in (("Income statement", F.income), ("Balance sheet", F.balance), ("Cash flow", F.cashflow)):
                if frame is not None and not frame.empty:
                    st.markdown(f"**{label}**")
                    st.dataframe(frame, width="stretch")

# ---------------------------------------------------------------------------
# Analysts
# ---------------------------------------------------------------------------
analyst = {}
with tabs[4]:
    ad = data.analyst_data(sym)
    lo_t, mean_t, hi_t = ui.num(inf.get("targetLowPrice")), ui.num(inf.get("targetMeanPrice")), ui.num(inf.get("targetHighPrice"))
    analyst = {"target_low": lo_t, "target_mean": mean_t, "target_high": hi_t,
               "recommendation": inf.get("recommendationKey"), "n_analysts": inf.get("numberOfAnalystOpinions")}
    c = st.columns(4)
    c[0].metric("Consensus", str(inf.get("recommendationKey", "—")).replace("_", " ").title(),
                f"{inf.get('numberOfAnalystOpinions', '—')} analysts", delta_color="off")
    c[1].metric("Mean target", ui.fmt_money(mean_t), ui.fmt_pct(mean_t / price - 1 if np.isfinite(mean_t) else np.nan, 1, True))
    c[2].metric("Low target", ui.fmt_money(lo_t))
    c[3].metric("High target", ui.fmt_money(hi_t))
    l, r_ = st.columns(2)
    rs = ad.get("recommendations_summary")
    if isinstance(rs, pd.DataFrame) and not rs.empty:
        cols = [c for c in ("strongBuy", "buy", "hold", "sell", "strongSell") if c in rs.columns]
        fig = go.Figure()
        colors = [ui.GREEN, "#6ee7b7", ui.MUTED, "#fca5a5", ui.RED]
        for col, colr in zip(cols, colors):
            fig.add_bar(x=rs.get("period", rs.index), y=rs[col], name=col, marker_color=colr)
        fig.update_layout(barmode="stack", title="Analyst ratings by month")
        with l:
            ui.plotly(fig, 330)
    ed = ad.get("earnings_dates")
    if isinstance(ed, pd.DataFrame) and not ed.empty and "Reported EPS" in ed:
        e = ed.dropna(subset=["Reported EPS"]).head(12).iloc[::-1]
        analyst["recent_eps_surprises_pct"] = e.get("Surprise(%)", pd.Series(dtype=float)).tail(4).tolist()
        fig = go.Figure()
        fig.add_scatter(x=e.index.strftime("%Y-%m-%d"), y=e["EPS Estimate"], name="Estimate", mode="markers",
                        marker=dict(size=12, color=ui.MUTED))
        fig.add_scatter(x=e.index.strftime("%Y-%m-%d"), y=e["Reported EPS"], name="Reported", mode="markers",
                        marker=dict(size=12, color=np.where(e["Reported EPS"] >= e["EPS Estimate"], ui.GREEN, ui.RED)))
        fig.update_layout(title="Earnings: estimate vs reported EPS")
        with r_:
            ui.plotly(fig, 330)
        upcoming = ed[ed["Reported EPS"].isna()]
        if len(upcoming):
            st.info(f"Next earnings date: **{upcoming.index[-1]:%b %d, %Y}**")
    for key, title in (("eps_revisions", "EPS revisions (up/down, last 7/30 days)"), ("eps_trend", "EPS estimate trend"),
                       ("growth_estimates", "Growth estimates"), ("upgrades_downgrades", "Recent rating changes")):
        v = ad.get(key)
        if isinstance(v, pd.DataFrame) and not v.empty:
            with st.expander(title):
                st.dataframe(v.head(25), width="stretch")

# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------
news_agg, ranked = {}, []
with tabs[5]:
    arts = data.news(f"{name} {sym}", symbol=sym)
    ranked = sentiment.rank_articles(arts, f"{sym} {name}")
    news_agg = sentiment.aggregate_sentiment(ranked[:30])
    c = st.columns(4)
    c[0].metric("News sentiment", f"{news_agg['score']:+.2f}", news_agg["label"], delta_color="off")
    c[1].metric("Positive", news_agg["positive"])
    c[2].metric("Negative", news_agg["negative"])
    c[3].metric("Articles (deduplicated)", news_agg["n"])
    for a in ranked[:25]:
        t = ui.tone(a["sentiment"], 0.25)
        when = f"{a['published']:%b %d %H:%M}" if a.get("published") else ""
        st.markdown(f"{ui.pill(a['sentiment_label'], t)} **[{ui.esc(a['title'])}]({a.get('link') or '#'})**  \n"
                    f"<span class='sf-muted'>{a.get('publisher', '')} · {when} · relevance {a['relevance']:.2f}</span>",
                    unsafe_allow_html=True)
    if not ranked:
        st.info("No recent news found.")

# ---------------------------------------------------------------------------
# AI analyst
# ---------------------------------------------------------------------------
with tabs[6]:
    st.markdown("Claude reads everything SharkFin computed for this stock (valuation, quality, analyst data, "
                "news and the price data) and writes a structured research note.")
    if not ai.available():
        st.info("Set `ANTHROPIC_API_KEY` as an environment variable or in `.streamlit/secrets.toml` to enable the AI analyst.")
    elif st.button("Write research note", type="primary"):
        r = hist["Close"].pct_change().dropna()
        panel = ind.compute_all(hist)
        dossier = {
            "symbol": sym, "name": name, "sector": inf.get("sector"), "industry": inf.get("industry"),
            "price": price, "market_cap": mcap, "net_debt": net_debt,
            "returns": {"1m": hist["Close"].iloc[-1] / hist["Close"].iloc[-22] - 1,
                        "1y": hist["Close"].iloc[-1] / hist["Close"].iloc[-253] - 1 if len(hist) > 253 else None},
            "risk": {k: v for k, v in risk.summary(r.iloc[-756:], rf=rf).items()},
            "technical_signal": {k: v for k, v in ind.technical_signal(panel).items() if k != "evidence"},
            "multiples": {k: inf.get(k) for k in ("trailingPE", "forwardPE", "pegRatio", "enterpriseToEbitda",
                                                   "enterpriseToRevenue", "priceToBook")},
            "growth": {"revenue_growth_yoy": rev_g, "earnings_growth_yoy": analyst_g, "revenue_cagr_3y": fin.revenue_cagr(3)},
            "dcf": dcf_out or "not applicable", "quality": quality, "analysts": analyst,
            "news_sentiment": news_agg,
            "headlines": [{"title": a["title"], "sentiment": round(a["sentiment"], 2), "publisher": a.get("publisher")}
                          for a in ranked[:15]],
        }
        st.write_stream(ai.stream_report(dossier))

ui.disclaimer()
