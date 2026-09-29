"""Portfolio: holdings & P/L, risk analytics, optimisation, watchlist."""

import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import data, portfolio, risk, ui

st.title("Portfolio")
ss = st.session_state

# ---- Add / import ---------------------------------------------------------------------
with st.expander("➕ Add a position", expanded=not ss.portfolio):
    with st.form("add_pos", clear_on_submit=True):
        c = st.columns([2, 1, 1, 1])
        sym_in = c[0].text_input("Ticker", placeholder="e.g. MSFT").strip().upper()
        shares_in = c[1].number_input("Shares", min_value=0.0001, value=1.0, step=1.0, format="%.4f")
        price_in = c[2].number_input("Cost per share ($, 0 = current price)", min_value=0.0, value=0.0, step=0.01)
        date_in = c[3].date_input("Purchase date", value=None)
        if st.form_submit_button("Add position", type="primary") and sym_in:
            px_now = data.price_of(data.info(sym_in))
            cost = price_in if price_in > 0 else px_now
            if not np.isfinite(cost):
                st.error(f"Couldn't find a price for {sym_in}.")
            else:
                ss.portfolio.append({"symbol": sym_in, "shares": float(shares_in), "buy_price": float(cost),
                                     "date": str(date_in) if date_in else None})
                ui.save_state()
                st.rerun()

with st.expander("⇅ Import / export CSV"):
    up = st.file_uploader("Import CSV with columns symbol, shares, buy_price (optional: date)", type="csv")
    if up is not None and st.button("Import"):
        df = pd.read_csv(up)
        df.columns = [c.strip().lower() for c in df.columns]
        need = {"symbol", "shares", "buy_price"}
        if not need.issubset(df.columns):
            st.error(f"CSV needs columns: {', '.join(sorted(need))}")
        else:
            for _, r in df.iterrows():
                ss.portfolio.append({"symbol": str(r["symbol"]).upper().strip(), "shares": float(r["shares"]),
                                     "buy_price": float(r["buy_price"]), "date": r.get("date")})
            ui.save_state()
            st.rerun()
    if ss.portfolio:
        buf = io.StringIO()
        pd.DataFrame(ss.portfolio).to_csv(buf, index=False)
        st.download_button("Export portfolio CSV", buf.getvalue(), "sharkfin_portfolio.csv", "text/csv")

if not ss.portfolio:
    st.info("Add your first position to see live P/L, risk analytics and optimised allocations.")
    st.stop()

# ---- Holdings -----------------------------------------------------------------------------
lots = pd.DataFrame(ss.portfolio)
lots["cost"] = lots["shares"] * lots["buy_price"]
pos = lots.groupby("symbol").agg(shares=("shares", "sum"), cost=("cost", "sum"))
pos["avg_cost"] = pos["cost"] / pos["shares"]
syms = tuple(pos.index)

with st.spinner("Pricing holdings…"):
    px = data.download_prices(syms + ("SPY",), period="3y")

last = px.ffill().iloc[-1] if not px.empty else pd.Series(dtype=float)
prev = px.ffill().iloc[-2] if len(px) > 1 else last
pos["price"] = [last.get(s, np.nan) if np.isfinite(last.get(s, np.nan)) else data.price_of(data.info(s)) for s in pos.index]
pos["value"] = pos["shares"] * pos["price"]
pos["pnl"] = pos["value"] - pos["cost"]
pos["pnl_pct"] = pos["pnl"] / pos["cost"]
pos["day_pnl"] = pos["shares"] * (pos["price"] - prev.reindex(pos.index))
pos["weight"] = pos["value"] / pos["value"].sum()

tv, tc = pos["value"].sum(), pos["cost"].sum()
m = st.columns(4)
m[0].metric("Market value", ui.fmt_money(tv))
m[1].metric("Unrealised P/L", ui.fmt_money(tv - tc), ui.fmt_pct((tv - tc) / tc, 2, True) if tc else None)
m[2].metric("Today", ui.fmt_money(pos["day_pnl"].sum()), ui.fmt_pct(pos["day_pnl"].sum() / (tv - pos["day_pnl"].sum()), 2, True))
m[3].metric("Positions", len(pos))

st.dataframe(pos[["shares", "avg_cost", "price", "value", "weight", "pnl", "pnl_pct", "day_pnl"]], width="stretch",
             column_config={"shares": st.column_config.NumberColumn("Shares", format="%.4g"),
                            "avg_cost": st.column_config.NumberColumn("Avg cost", format="$%.2f"),
                            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
                            "value": st.column_config.NumberColumn("Value", format="$%.2f"),
                            "weight": st.column_config.ProgressColumn("Weight", min_value=0, max_value=1, format="percent"),
                            "pnl": st.column_config.NumberColumn("P/L", format="$%.2f"),
                            "pnl_pct": st.column_config.NumberColumn("P/L %", format="percent"),
                            "day_pnl": st.column_config.NumberColumn("Today", format="$%.2f")})

with st.expander("✏️ Edit lots"):
    edited = st.data_editor(pd.DataFrame(ss.portfolio), num_rows="dynamic", width="stretch", key="lots_editor")
    if st.button("Save changes"):
        ss.portfolio = [r for r in edited.to_dict("records") if r.get("symbol") and r.get("shares")]
        ui.save_state()
        st.rerun()

tabs = st.tabs(["🥧 Allocation", "⚠️ Risk", "🧮 Optimizer", "⭐ Watchlist"])

with tabs[0]:
    l, r = st.columns(2)
    fig = go.Figure(go.Pie(labels=pos.index, values=pos["value"], hole=0.55, textinfo="label+percent"))
    fig.update_layout(title="By holding", showlegend=False)
    with l:
        ui.plotly(fig, 380)
    infos = data.infos(syms)
    sec = infos.get("sector", pd.Series(index=infos.index, dtype=object)).fillna("Other / ETF")
    by_sec = pos["value"].groupby(sec.reindex(pos.index).fillna("Other / ETF")).sum()
    fig = go.Figure(go.Pie(labels=by_sec.index, values=by_sec.values, hole=0.55, textinfo="label+percent"))
    fig.update_layout(title="By sector", showlegend=False)
    with r:
        ui.plotly(fig, 380)
    hhi = float((pos["weight"] ** 2).sum())
    st.caption(f"Effective number of positions: **{1 / hhi:.1f}** (1/HHI). Largest position: "
               f"**{pos['weight'].idxmax()}** at {pos['weight'].max():.0%}.")

rets = px.pct_change(fill_method=None).dropna(how="all")
held = [s for s in syms if s in rets and rets[s].notna().sum() > 120]

with tabs[1]:
    if len(held) < 1 or "SPY" not in rets:
        st.info("Not enough price history to compute risk analytics.")
    else:
        window = st.segmented_control("Lookback", ["1Y", "3Y"], default="1Y", key="risk_lb")
        n = 252 if window == "1Y" else 756
        R = rets[held].iloc[-n:].fillna(0)
        w = pos["weight"].reindex(held).fillna(0)
        w = w / w.sum()
        port = R @ w
        spy = rets["SPY"].iloc[-n:]
        rf = data.risk_free_rate()
        s_p, s_b = risk.summary(port, spy, rf), risk.summary(spy, rf=rf)
        st.caption("Current weights applied historically (a 'what if I had held this mix' view).")
        rows = ["CAGR", "Volatility", "Sharpe", "Sortino", "Max Drawdown", "Beta", "Alpha (ann.)", "VaR 95% (1d)",
                "CVaR 95% (1d)", "Tracking Error", "Information Ratio"]
        tbl = pd.DataFrame({"Portfolio": [s_p.get(k) for k in rows], "S&P 500 (SPY)": [s_b.get(k) for k in rows]}, index=rows)
        l, r = st.columns([1, 2])
        with l:
            st.dataframe(tbl.style.format(lambda v: "—" if v is None or not np.isfinite(v) else f"{v:.2f}" if abs(v) > 1.5 else f"{v:.2%}"),
                         width="stretch")
            var_d = s_p["CVaR 95% (1d)"] * tv
            st.metric("1-day 95% expected shortfall", ui.fmt_money(var_d),
                      help="Average loss on the worst 5% of days, at today's portfolio value.")
            st.metric("If the S&P 500 falls 10%", ui.fmt_money(-0.10 * s_p.get("Beta", 1) * tv), help="Beta-implied move.")
        with r:
            eq = pd.DataFrame({"Portfolio": (1 + port).cumprod(), "S&P 500": (1 + spy).cumprod()})
            fig = go.Figure([go.Scatter(x=eq.index, y=eq[c], name=c) for c in eq])
            fig.update_layout(title="Growth of $1")
            ui.plotly(fig, 300)
            dd = risk.drawdown_series(port)
            fig = go.Figure(go.Scatter(x=dd.index, y=dd * 100, fill="tozeroy", line=dict(color=ui.RED)))
            fig.update_layout(title="Drawdown (%)")
            ui.plotly(fig, 240)
        if len(held) > 1:
            l, r = st.columns(2)
            corr = R.corr()
            fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1, colorscale="RdBu_r",
                                       text=np.round(corr.values, 2), texttemplate="%{text}"))
            fig.update_layout(title="Correlation matrix")
            with l:
                ui.plotly(fig, 420)
            cov = portfolio.shrunk_covariance(R)
            rc = risk.risk_contributions(w.values, cov.values)
            fig = go.Figure([go.Bar(x=held, y=w.values * 100, name="Capital weight %"),
                             go.Bar(x=held, y=rc * 100, name="Risk contribution %")])
            fig.update_layout(title="Where your risk actually comes from", barmode="group")
            with r:
                ui.plotly(fig, 420)

with tabs[2]:
    if len(held) < 2:
        st.info("Add at least two holdings with a year of history to run the optimiser.")
    else:
        cap = st.slider("Max weight per holding", 0.1, 1.0, 0.35, 0.05)
        R = rets[held].iloc[-756:].dropna()
        cur = pos["value"].reindex(held)
        w_tbl, stats, mu, cov = portfolio.compare_allocations(R, cur, rf=data.risk_free_rate(), max_weight=cap)
        l, r = st.columns([3, 2])
        with l:
            st.dataframe(w_tbl, width="stretch", column_config={c: st.column_config.NumberColumn(format="percent") for c in w_tbl})
            st.dataframe(stats.T, width="stretch", column_config={
                "Exp. return": st.column_config.NumberColumn(format="percent"),
                "Volatility": st.column_config.NumberColumn(format="percent"),
                "Sharpe": st.column_config.NumberColumn(format="%.2f"),
                "Effective N": st.column_config.NumberColumn(format="%.1f")})
        with r:
            fr = portfolio.efficient_frontier(mu, cov, max_weight=cap)
            fig = go.Figure(go.Scatter(x=fr["volatility"] * 100, y=fr["return"] * 100, mode="lines", name="Efficient frontier"))
            for name in stats.columns:
                fig.add_trace(go.Scatter(x=[stats.loc["Volatility", name] * 100], y=[stats.loc["Exp. return", name] * 100],
                                         mode="markers+text", text=[name], textposition="top center", name=name,
                                         marker=dict(size=11)))
            fig.update_layout(title="Risk / return (ex-ante)", xaxis_title="Volatility %", yaxis_title="Expected return %",
                              showlegend=False)
            ui.plotly(fig, 420)
        method = st.selectbox("Rebalance to", [c for c in w_tbl.columns if c != "Current"], index=1)
        trades = pd.DataFrame({"Target weight": w_tbl[method], "Current weight": w_tbl.get("Current")})
        trades["Target $"] = trades["Target weight"] * cur.sum()
        trades["Trade $"] = trades["Target $"] - cur
        trades["Trade shares"] = trades["Trade $"] / pos["price"].reindex(held)
        st.dataframe(trades, width="stretch", column_config={
            "Target weight": st.column_config.NumberColumn(format="percent"),
            "Current weight": st.column_config.NumberColumn(format="percent"),
            "Target $": st.column_config.NumberColumn(format="$%.0f"),
            "Trade $": st.column_config.NumberColumn(format="$%.0f"),
            "Trade shares": st.column_config.NumberColumn(format="%.2f")})
        st.caption("Expected returns blend historical means with CAPM equilibrium returns; covariance uses Ledoit-Wolf shrinkage. "
                   "HRP and risk parity don't need return forecasts at all, which makes them the most robust choices.")

with tabs[3]:
    wl = ss.watchlist
    add = st.text_input("Add ticker to watchlist").strip().upper()
    if st.button("Add") and add and add not in wl:
        wl.append(add)
        ui.save_state()
        st.rerun()
    for s in list(wl):
        c = st.columns([4, 1])
        c[0].markdown(f"**{s}**")
        if c[1].button("Remove", key=f"rm_{s}"):
            wl.remove(s)
            ui.save_state()
            st.rerun()

ui.disclaimer()
