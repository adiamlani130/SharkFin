"""Frontier Lab: the experimental side of SharkFin. A live 3D volatility surface with a jump-diffusion model,
a replay of the neuroevolution experiment (including the control that caught its overfitting), a jump-risk
radar, and a forward paper scoreboard for the two signals worth watching. Research, not trade advice."""

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import data, frontier as fl, ui

ui.header("Frontier Lab",
          "Experiments from the edge of the research: jump-diffusion option pricing, evolved trading networks "
          "and a live out-of-sample test. Each part says what it shows, how to read it and how far to trust it.")

TRUST = {"solid": ("Solid result", "pos"), "failure": ("Honest failure, on purpose", "neg"),
         "experimental": ("Experimental", "info"), "live": ("Live test, just started", "neu")}

NAMES = {
    "r0": "yesterday's return", "R5": "last week's return", "R20": "last month's return", "R60": "3-month return",
    "R250": "1-year return", "v0": "volume vs normal", "clv0": "where the close sat in the day's range",
    "rng0": "today's range vs normal", "rng5": "last week's ranges vs normal", "gap0": "overnight gap",
    "body0": "open-to-close move", "volr": "1-month vol vs 1-year vol", "pos250": "place in the 52-week range",
    "m_r0": "SPY's day", "m_R20": "SPY's month", "m_vixz": "VIX vs its past year",
    "m_term": "VIX vs 3-month VIX (fear curve)", "j_jump_share": "jump share of volatility",
    "j_vrp": "VIX minus jump-model fair vol", "j_skew_gap": "SKEW vs jump-implied skew",
}


def name_of(n: str) -> str:
    if n in NAMES:
        return NAMES[n]
    if n[:1] in "rv" and n[1:].isdigit():
        return f"{'return' if n[0] == 'r' else 'volume vs normal'} {n[1:]} days ago"
    if n.startswith("clv"):
        return f"close-in-range {n[3:]} days ago"
    return n


def guide(what: str, read: str, trust: str, why: str):
    label, tone = TRUST[trust]
    st.markdown(
        "<div class='sf-hero sf-rise' style='padding:14px 18px'>"
        "<div class='sf-cols'>"
        f"<div><h5>What it is</h5><div class='sf-note'>{what}</div></div>"
        f"<div><h5>How to read it</h5><div class='sf-note'>{read}</div></div>"
        f"<div><h5>How far to trust it</h5><div class='sf-note'>{ui.pill(label, tone)} {why}</div></div>"
        "</div></div>", unsafe_allow_html=True)


def pct(x, d=1):
    return ui.fmt_pct(x, d, sign=True) if x is not None and np.isfinite(x) else "–"


def scene_axis(title, **kw):
    return dict(title=dict(text=title, font=dict(size=11)), gridcolor=ui.GRID, zerolinecolor=ui.GRID,
                backgroundcolor="rgba(0,0,0,0)", showbackground=False, **kw)


SURF = fl.load("surface.json")
EVO = fl.load("evolution.json")

st.markdown(
    "<div class='sf-hero sf-rise'><div class='k'>Start here</div>"
    "<div class='v' style='font-size:1.35rem'>Four experiments, and an honest scorecard for each.</div>"
    "<ol class='sf-steps'>"
    "<li><b>Volatility surface:</b> a jump model that explains real option prices far better than Black-Scholes. "
    "Spin it, then drag the sliders to see what crash risk does to option prices.</li>"
    "<li><b>Evolution Arena:</b> 412,000 trading networks bred from scratch. Every run had a twin trained on "
    "scrambled data, and the holdout shows which wins survived. That's how overfitting gets caught.</li>"
    "<li><b>Jump radar:</b> is today's market moving in shocks or in a steady grind? Experimental.</li>"
    "<li><b>Live scoreboard:</b> the two signals worth watching, frozen on Nov 16 2026 and tracked forward on real "
    "prices. No more tuning, so this is the real out-of-sample test.</li></ol></div>",
    unsafe_allow_html=True)

tabs = st.tabs(["🌋 Volatility surface", "🧬 Evolution Arena", "📡 Jump radar", "🏁 Live scoreboard"])

# ======================================================================================== 1. surface
with tabs[0]:
    guide("The implied volatility of every listed SPY option, as a 3D landscape: strike across, time to expiry "
          "deep, volatility up. The mesh is Merton's jump-diffusion model fitted to those prices.",
          "Dots are real market quotes and the mesh is the model. Black-Scholes says the landscape should be "
          "flat. The steep wall on the left is crash insurance: far out-of-the-money puts cost much more than a "
          "flat-vol model would charge.",
          "solid", "Four numbers fit hundreds of real quotes. It's one day's snapshot, and a pricing model, not a "
          "trading signal.")
    if not SURF:
        st.info("Surface data hasn't been built yet.")
    else:
        S, r, fit = SURF["S"], SURF["r"], SURF["fit"]
        q = pd.DataFrame(SURF["quotes"])
        ui.metrics([
            dict(label="Merton error", value=f"{SURF['rmse_volpts']:.1f} vol pts",
                 help="Root-mean-square gap between model and market implied vol across all quotes."),
            dict(label="Black-Scholes error", value=f"{SURF['bs_flat_rmse_volpts']:.1f} vol pts",
                 help="Same gap for the best single flat volatility."),
            dict(label="Crashes priced in", value=f"{fit['lam']:.2f} a year",
                 help="Risk-neutral jump rate the option market is charging for."),
            dict(label="Average jump", value=pct(math.exp(fit["mu_j"]) - 1, 0)),
            dict(label="Quotes fitted", value=f"{SURF['n']}", help=f"SPY options, closing mids on {SURF['asof']}."),
        ], key="surf")

        with st.expander("🎛️ Sculpt the surface yourself", expanded=False):
            st.caption("Move a slider and the mesh re-prices every option live. Try zero jumps: the smile flattens "
                       "into Black-Scholes, and the error jumps.")
            if st.button("Reset to the market fit", key="sf_reset"):
                for k in ("sl_sig", "sl_lam", "sl_mu", "sl_del"):
                    st.session_state.pop(k, None)
            c = st.columns(4)
            p = dict(
                sigma=c[0].slider("Everyday volatility σ", 0.03, 0.40, float(round(fit["sigma"], 3)), 0.005, key="sl_sig"),
                lam=c[1].slider("Crashes per year λ", 0.0, 3.0, float(round(fit["lam"], 2)), 0.05, key="sl_lam"),
                mu_j=c[2].slider("Average crash size μJ", -0.40, 0.05, float(round(fit["mu_j"], 3)), 0.005, key="sl_mu"),
                delta=c[3].slider("Crash size spread δ", 0.01, 0.40, float(round(fit["delta"], 3)), 0.005, key="sl_del"),
            )
        defaults = dict(sigma=round(fit["sigma"], 3), lam=round(fit["lam"], 2), mu_j=round(fit["mu_j"], 3),
                        delta=round(fit["delta"], 3))
        changed = any(abs(p[k] - defaults[k]) > 1e-9 for k in p)
        if not changed:
            p = {k: float(fit[k]) for k in defaults}
        m, T, iv = fl.surface_grid(S, r, p)
        err = fl.fit_error(SURF, p) if changed else SURF["rmse_volpts"]
        night = ui.mode() != "day"
        scale = ([[0, "#1e3a8a"], [0.35, "#3b82f6"], [0.7, "#a855f7"], [1, "#f0abfc"]] if night else
                 [[0, "#fde68a"], [0.35, "#fb923c"], [0.7, "#db2777"], [1, "#7e22ce"]])
        fig = go.Figure()
        fig.add_surface(x=m * 100, y=T * 12, z=iv * 100, colorscale=scale, opacity=0.88, showscale=False,
                        name="Merton model", contours=dict(z=dict(show=True, usecolormap=True, project_z=False, width=1)),
                        hovertemplate="strike %{x:.0f}% from spot<br>%{y:.1f} months<br>model vol %{z:.1f}%<extra></extra>")
        q = q[(q.m >= -0.25) & (q.m <= 0.12) & (q["T"] <= 1.0)]
        fig.add_scatter3d(x=q.m * 100, y=q["T"] * 12, z=q.iv * 100, mode="markers", name="Market quotes",
                          marker=dict(size=2.6, color=ui.ORANGE if night else "#0f172a", opacity=0.9),
                          hovertemplate="market vol %{z:.1f}%<br>%{y:.1f} months<extra></extra>")
        flat = SURF["bs_flat_vol"] * 100
        if st.toggle("Show Black-Scholes (one flat volatility)", value=False, key="bsflat"):
            fig.add_surface(x=m * 100, y=T * 12, z=np.full_like(iv, flat), opacity=0.25, showscale=False,
                            colorscale=[[0, ui.MUTED], [1, ui.MUTED]], name="Black-Scholes", hoverinfo="skip")
        fig.update_layout(
            height=620, margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
            scene=dict(xaxis=scene_axis("Strike vs spot (%)"), yaxis=scene_axis("Months to expiry"),
                       zaxis=scene_axis("Implied vol (%)", range=[5, max(55, float(np.nanmax(iv)) * 100 + 3)]),
                       camera=dict(eye=dict(x=-1.25, y=-1.3, z=0.55), center=dict(x=0, y=0, z=-0.12)),
                       aspectmode="manual", aspectratio=dict(x=1.35, y=1.1, z=0.8)))
        ui.plotly(fig, key="surface3d")
        st.caption(f"Model error with these settings: **{err:.1f} vol points** "
                   f"({'your settings' if changed else 'market fit'}; Black-Scholes: {SURF['bs_flat_rmse_volpts']:.1f}). "
                   f"Drag to spin, scroll to zoom. SPY ${S:,.0f}, closing quotes {SURF['asof']}.")

        st.subheader("What the market fears vs what history shows")
        st.markdown("<div class='sf-note'>The same jump model fitted two ways. <b>Option prices</b> imply rare, big "
                    "crashes. <b>The last two years of daily returns</b> only show lots of small jumps, because a "
                    "crash that comes once every few years rarely shows up in two. The gap is the crash-insurance "
                    "premium, which is why selling puts looks like free money in calm years.</div>",
                    unsafe_allow_html=True)
        hist = {k: float(SURF["historical"][k]) for k in ("sigma", "lam", "mu_j", "delta")}
        x, d_rn = fl.return_density(p, 1.0)
        _, d_h = fl.return_density(hist, 1.0)
        f2 = go.Figure()
        f2.add_scatter(x=(np.exp(x) - 1) * 100, y=d_rn, name="Priced by options", line=dict(color=ui.RED, width=2.4))
        f2.add_scatter(x=(np.exp(x) - 1) * 100, y=d_h, name="Seen in the last 2 years", line=dict(color=ui.BLUE, width=2.4))
        f2.add_vrect(x0=-60, x1=-20, fillcolor="rgba(255,92,122,0.06)", line_width=0,
                     annotation_text="crash zone", annotation_position="top left")
        f2.update_layout(height=340, yaxis=dict(type="log", range=[-4, 0.7], title="Likelihood (log scale)"),
                         xaxis=dict(title="SPY return over the next year (%), before drift", ticksuffix="%", range=[-60, 30]),
                         legend=dict(y=1.08, yanchor="bottom"), margin=dict(t=30))
        ui.plotly(f2, key="tails")
        ui.metrics([
            dict(label="Chance of a 20%+ drop in a year, options", value=ui.fmt_pct(fl.crash_odds(p, 1, -0.2), 1)),
            dict(label="Same, from the last 2 years", value=ui.fmt_pct(fl.crash_odds(hist, 1, -0.2), 1)),
        ], key="crash")
        st.caption("Option-implied odds are risk-neutral: they include the premium people pay for protection, so "
                   "they overstate real-world odds. Both curves leave out the market's upward drift.")

# ======================================================================================== 2. evolution
with tabs[1]:
    guide("NEAT, an algorithm that breeds neural networks: it evolves their wiring and their math (sin, gauss, "
          "products, thresholds), not just weights. Built from scratch for SharkFin, it evolved hundreds of thousands "
          "of ETF-timing networks.",
          "Every run had a twin trained on <b>scrambled</b> data, where any pattern is fake. If the twin scores as "
          "well, the 'edge' is overfitting. Real runs have to beat their twins on 2021-2026 data that evolution "
          "never saw, and then do it again on a fresh download.",
          "failure", "Raw price and volume gave no real edge. One simple network built on the VIX curve held up "
          "twice, so it's on the live scoreboard. Everything else failed.")
    if not EVO:
        st.info("Evolution results haven't been built yet.")
    else:
        runs = pd.DataFrame(EVO["runs"])
        trk, bh = EVO["tracked"]["hold"], EVO["tracked"]["buy_hold"]
        tot = EVO["totals"]
        ui.metrics([
            dict(label="Networks evolved", value=f"{(tot['real'] + tot['noise']) / 1000:,.0f}K",
                 help=f"{tot['real']:,} on real data and {tot['noise']:,} on scrambled data in the Nov 15 study, "
                      f"plus {runs.evaluated.sum():,} in the re-runs replayed here."),
            dict(label="Survivor's Sharpe, holdout", value=f"{trk['sharpe']:.2f}",
                 delta=f"{trk['sharpe'] - bh['sharpe']:+.2f} vs buy-and-hold"),
            dict(label="Worst drop", value=pct(trk["maxdd"], 1), delta=f"buy-and-hold {pct(bh['maxdd'], 1)}", delta_color="off"),
            dict(label="Yearly return", value=pct(trk["cagr"], 1), delta=f"buy-and-hold {pct(bh['cagr'], 1)}", delta_color="off"),
        ], key="evo")

        st.subheader("Round 1: real data vs scrambled data")
        st.markdown("<div class='sf-note'>Press play. Each line is one evolution run's best training score, "
                    "generation by generation. <b>Colored lines learned from real prices, grey dashed lines from "
                    "scrambled ones.</b> Scrambled data has no pattern to find, yet those runs still climb. Any "
                    "search finds <i>something</i> in noise, so a training score can't prove an edge.</div>",
                    unsafe_allow_html=True)
        inp = st.radio("Inputs", ["Price & volume only", "Plus VIX curve & jump features"], horizontal=True,
                       key="evo_inputs", label_visibility="collapsed")
        sel = runs[runs.market == inp.startswith("Plus")]
        maxg = max(len(h) for h in sel.history)
        colors = [ui.GREEN, ui.BLUE, ui.PURPLE, ui.ORANGE, ui.RED]

        def traces(upto):
            out = []
            for i, rw in enumerate(sel.itertuples()):
                h = pd.DataFrame(rw.history).iloc[:upto]
                out.append(go.Scatter(x=h.gen, y=h.best, mode="lines",
                                      name=("Scrambled " if rw.null else "Real ") + f"seed {rw.seed}",
                                      line=dict(color=ui.MUTED if rw.null else colors[i % 5], width=2.2,
                                                dash="dash" if rw.null else "solid")))
            return out
        steps = list(range(4, maxg + 1, 4)) + ([maxg] if maxg % 4 else [])
        lo = min(min(x["best"] for x in h) for h in sel.history)
        hi = max(max(x["best"] for x in h) for h in sel.history)
        f3 = go.Figure(data=traces(maxg), frames=[go.Frame(data=traces(s), name=str(s)) for s in steps])
        f3.update_layout(
            height=380, xaxis=dict(range=[0, maxg], title="Generation"),
            yaxis=dict(range=[lo - 0.05, hi + 0.05], title="Training fitness"),
            legend=dict(y=1.02, yanchor="bottom"), margin=dict(t=40),
            updatemenus=[dict(type="buttons", showactive=False, x=1, xanchor="right", y=1.2, yanchor="top",
                              buttons=[dict(label="▶ Play evolution", method="animate",
                                            args=[None, dict(frame=dict(duration=60, redraw=False), fromcurrent=False,
                                                             transition=dict(duration=0), mode="immediate")])])])
        ui.plotly(f3, key="evo_anim")
        st.caption("Training fitness is the average Sharpe across every ETF and four time blocks, minus a penalty for "
                   "inconsistency and for size. These are the re-runs made for this page (same recipe, fresh data).")

        st.subheader("Round 2: the test it never saw")
        st.markdown("<div class='sf-note'>Skill is Sharpe minus buy-and-hold's Sharpe on the same ETFs. Training is "
                    "2006-16, picking is 2017-21, and the <b>holdout, Oct 2021 to Nov 2026</b>, was run once at the end. "
                    "Every group looks skilled while picking, then the skill drains away.</div>",
                    unsafe_allow_html=True)
        runs["group"] = np.where(runs.null, "Scrambled data",
                                 np.where(runs.market, "Real + VIX & jumps", "Real, price only"))
        f4 = go.Figure()
        gcol = {"Real, price only": ui.BLUE, "Real + VIX & jumps": ui.GREEN, "Scrambled data": ui.MUTED}
        for gname, gdf in runs.groupby("group", sort=False):
            f4.add_bar(name=gname, x=["Training", "Picking", "Holdout"],
                       y=[gdf.train_skill.mean(), gdf.pick_skill.mean(), gdf.hold_skill.mean()],
                       marker_color=gcol[gname],
                       customdata=[len(gdf)] * 3,
                       hovertemplate="%{x}: %{y:+.2f} (average of %{customdata} runs)<extra>" + gname + "</extra>")
        f4.add_hline(y=0, line_color=ui.MUTED, line_width=1)
        f4.update_layout(barmode="group", height=330, yaxis=dict(title="Average skill vs buy-and-hold"),
                         legend=dict(y=1.02, yanchor="bottom"), margin=dict(t=40))
        ui.plotly(f4, key="evo_bars")
        st.caption("Scrambled runs are scored on their own scrambled data, so their 'picking' score shows how much a "
                   "search can find in pure noise.")

        st.subheader("Round 3: does it reproduce?")
        st.markdown("<div class='sf-note'>Two of the Nov 15 champions were written out in full, so they were rebuilt "
                    "exactly and re-scored on a fresh download of the same prices. Small data differences (dividend "
                    "adjustments, the jump-model refits) are a cheap robustness test. <b>Seed 2, a simple fear-curve "
                    "rule, held its holdout skill. Seed 1 leaned on a jump feature passed through a sine wave, and it "
                    "fell apart.</b> Re-evolving from scratch didn't find either again.</div>",
                    unsafe_allow_html=True)
        rows = []
        for k, v in EVO["originals"].items():
            rows.append(dict(Network=f"Nov 15 champion, seed {k[-1]}", **{f"{w} (reported)": v["reported"][w] for w in ("hold",)},
                             **{"holdout (fresh data)": v["fresh"]["hold"], "picking (fresh data)": v["fresh"]["pick"]}))
        for rw in runs[runs.market & ~runs.null].itertuples():
            rows.append({"Network": f"Re-evolved, seed {rw.seed}", "hold (reported)": np.nan,
                         "holdout (fresh data)": rw.hold_skill, "picking (fresh data)": rw.pick_skill})
        rep = pd.DataFrame(rows)
        f4b = go.Figure()
        f4b.add_bar(name="Holdout skill, Nov 15 write-up", y=rep.Network, x=rep["hold (reported)"], orientation="h",
                    marker_color=ui.MUTED)
        f4b.add_bar(name="Holdout skill, fresh data", y=rep.Network, x=rep["holdout (fresh data)"], orientation="h",
                    marker_color=[ui.GREEN if v > 0 else ui.RED for v in rep["holdout (fresh data)"]])
        f4b.add_vline(x=0, line_color=ui.MUTED, line_width=1)
        f4b.update_layout(barmode="group", height=300, xaxis=dict(title="Sharpe vs buy-and-hold, Oct 2021 - Nov 2026"),
                          yaxis=dict(autorange="reversed"), legend=dict(y=1.02, yanchor="bottom"), margin=dict(t=40))
        ui.plotly(f4b, key="repro")

        st.subheader("Meet a champion")
        champs = list(EVO["champions"])
        pretty = {k: ("Nov 15 seed " + k[-1] + (", the survivor" if k in EVO["tracked"]["members"] else "")
                      if k.startswith("orig") else
                      ("Re-evolved, VIX & jumps, seed " if k.startswith("Am") else "Re-evolved, price only, seed ") + k[-1])
                  for k in champs}
        dflt = EVO["tracked"]["members"][0]
        pick = st.selectbox("Network", champs, format_func=pretty.get, index=champs.index(dflt), key="champ")
        gj = EVO["champions"][pick]
        pos_, conns = fl.network_layout(gj)
        nodes = {n["id"]: n for n in gj["nodes"]}
        f5 = go.Figure()
        wmax = max([abs(c["w"]) for c in conns] + [1e-9])
        for c in conns:
            (x0, y0), (x1, y1) = pos_[c["src"]], pos_[c["dst"]]
            f5.add_scatter(x=[x0, x1], y=[y0, y1], mode="lines", hoverinfo="skip", showlegend=False,
                           line=dict(color=ui.GREEN if c["w"] > 0 else ui.RED, width=1 + 6 * abs(c["w"]) / wmax),
                           opacity=0.7)
        xs, ys, txt, hov, col, size = [], [], [], [], [], []
        for i, n in nodes.items():
            if i not in pos_:
                continue
            xs.append(pos_[i][0])
            ys.append(pos_[i][1])
            if n["kind"] == "in":
                txt.append(name_of(n["label"]))
                hov.append(f"input: {n['label']}")
                col.append("#5eead4")
                size.append(16)
            else:
                txt.append(("position" if n["kind"] == "out" else n["act"]) + ("" if n["agg"] == "sum" else f" · {n['agg']}"))
                hov.append(f"{'output' if n['kind'] == 'out' else 'hidden node'}: {n['act']}({n['agg']} of its inputs {n['bias']:+.2f})")
                col.append(ui.ORANGE if n["kind"] == "out" else ui.PURPLE)
                size.append(28 if n["kind"] == "out" else 20)
        f5.add_scatter(x=xs, y=ys, mode="markers+text", text=txt, hovertext=hov, hoverinfo="text", showlegend=False,
                       textposition=["middle left" if x_ == 0 else "top center" for x_ in xs],
                       marker=dict(size=size, color=col, line=dict(width=2, color=ui.BG)))
        n_in = sum(1 for n in nodes.values() if n["kind"] == "in")
        f5.update_layout(height=max(300, 40 * n_in), xaxis=dict(visible=False, range=[-0.8, 1.12]),
                         yaxis=dict(visible=False, range=[0, 1.05]), margin=dict(t=10, b=10))
        ui.plotly(f5, key="net")
        st.caption("Teal = inputs, purple = hidden nodes (each picks its own math), orange = the output, a position "
                   "from -1 (short) to +1 (long). Green links push toward long, red toward short, and thicker ones "
                   "weigh more.")
        with st.expander("The whole network as one formula"):
            st.code(gj["formula"], language="text")
            used = sorted({n["label"] for n in gj["nodes"] if n["kind"] == "in" and n["label"]})
            st.markdown("  \n".join(f"`{u}` = {name_of(u)}" for u in used))
            if pick == "orig_s2":
                st.markdown("**In plain English:** stay mostly long, and step aside fast when 1-month VIX climbs "
                            "above 3-month VIX (the fear curve inverts). Lean a little with the market's last month, "
                            "and fade big open-to-close moves.")

        st.subheader("The survivor on the holdout")
        cur = fl.load_csv("tracked_holdout.csv")
        skill = trk["sharpe"] - bh["sharpe"]
        yr = EVO["tracked"]["yearly"]
        yrs = sorted(yr, key=int)
        c1, c2 = st.columns([3, 2])
        with c1:
            f6 = go.Figure()
            f6.add_scatter(x=cur.index, y=cur.tracked * 10000, name="Fear-curve network", line=dict(color=ui.GREEN, width=2.2))
            f6.add_scatter(x=cur.index, y=cur.buy_hold * 10000, name="Buy and hold, same 19 ETFs", line=dict(color=ui.MUTED, width=1.8))
            f6.update_layout(height=330, yaxis=dict(title="$10,000 grows to", tickprefix="$"),
                             legend=dict(y=1.02, yanchor="bottom"), margin=dict(t=40))
            ui.plotly(f6, key="trk_curve")
        with c2:
            f7 = go.Figure()
            f7.add_bar(x=yrs, y=[yr[y]["tracked"] for y in yrs], name="Network", marker_color=ui.GREEN)
            f7.add_bar(x=yrs, y=[yr[y]["buy_hold"] for y in yrs], name="Buy and hold", marker_color=ui.MUTED)
            f7.update_layout(height=330, barmode="group", yaxis=dict(title="Sharpe that year"),
                             legend=dict(y=1.02, yanchor="bottom"), margin=dict(t=40))
            ui.plotly(f7, key="yearly")
        best_y = max(yrs, key=lambda y: yr[y]["tracked"] - yr[y]["buy_hold"])
        wins = sum(yr[y]["tracked"] > yr[y]["buy_hold"] for y in yrs)
        st.markdown(
            "<div class='sf-note'><b>The honest read.</b> It's a calmer way of being long: higher Sharpe, smaller drops, "
            f"but a lower yearly return. It beat buy-and-hold's Sharpe in {wins} of {len(yrs)} calendar years, and its "
            f"best year was {best_y}, so a few escapes from sell-offs carry much of the edge. The Nov 15 study's "
            "bootstrap put about a 13% chance on there being no edge at all. It reproduced and it's simple, and "
            "that's why it gets a live test rather than a spot in the Playbook.</div>", unsafe_allow_html=True)

# ======================================================================================== live data (shared)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def live_state(day_key: str):
    px = data.download_ohlcv(tuple(fl.ETFS + fl.EXTRA), "3y")
    C = px["Close"]
    fits = fl.topped_up_fits(C["SPY"])
    jf = fl.features_from_fits(fits, C["^VIX"], C.get("^SKEW"))
    pos = fl.tracked_positions(px, jf)
    z = fl.zscore(jf["jump_share"])
    gate = (z > 0).astype(float).where(z.notna())
    rec = fl.forward_record(px, pos, gate)
    hist = fl.forward_record(px, pos, gate, since=C.index[-1] - pd.DateOffset(years=2))
    return dict(px=px, fits=fits, jf=jf, pos=pos, z=z, gate=gate, rec=rec, hist=hist)


live, live_err = None, None
try:
    with st.spinner("Refitting the jump model on the latest prices…"):
        live = live_state(pd.Timestamp.now(tz="America/New_York").strftime("%Y-%m-%d"))
except Exception as e:  # noqa: BLE001  (offline or Yahoo down: the frozen research still shows)
    live_err = e

# ======================================================================================== 3. jump radar
with tabs[2]:
    guide("Every week SharkFin refits the jump model to SPY's last two years of daily returns, and splits "
          "volatility into a steady 'grind' part and a sudden 'jump' part.",
          "<b>Jump share</b> is how much of recent risk came from sudden shocks. The needle shows it against its "
          "past year. <b>Fear premium</b> is VIX minus the volatility the jump model calls fair. When it's high, "
          "options are expensive, and it has tended to come before bumpier months.",
          "experimental", "Jump share is a pattern found after the fact. Fear premium has forecast risk in both test "
          "windows, but it doesn't forecast returns.")
    if live is None:
        st.warning("Live prices aren't available right now, so the radar can't refresh.")
    else:
        jf, z = live["jf"], live["z"]
        zi, js = float(z.dropna().iloc[-1]), float(jf["jump_share"].dropna().iloc[-1])
        vrp = jf["vrp"].dropna()
        vr_pct = float((vrp.iloc[-504:] <= vrp.iloc[-1]).mean())
        mode_txt = ("Shock-driven" if zi > 0.5 else "Grinding" if zi < -0.5 else "Mixed")
        c1, c2 = st.columns(2)
        for col, val, title, sub, rng in (
                (c1, zi, f"Jump share: {mode_txt}", f"{js:.0%} of variance from jumps", [-3, 3]),
                (c2, vr_pct * 100, "Fear premium: percentile vs 2 years", f"VIX {vrp.iloc[-1] * 100:+.1f} pts vs jump-model fair vol", [0, 100])):
            g = go.Figure(go.Indicator(
                mode="gauge+number", value=val, number=dict(valueformat="+.1f" if rng[0] < 0 else ".0f",
                                                            suffix="σ" if rng[0] < 0 else "", font=dict(size=40)),
                title=dict(text=f"<b>{title}</b><br><span style='font-size:0.85em'>{sub}</span>", font=dict(size=15)),
                gauge=dict(axis=dict(range=rng, tickcolor=ui.MUTED), bar=dict(color=ui.ORANGE, thickness=0.28),
                           bgcolor="rgba(0,0,0,0)", borderwidth=0,
                           steps=[dict(range=[rng[0], rng[0] + (rng[1] - rng[0]) / 3], color="rgba(78,168,255,0.18)"),
                                  dict(range=[rng[0] + (rng[1] - rng[0]) / 3, rng[0] + 2 * (rng[1] - rng[0]) / 3], color="rgba(139,149,167,0.12)"),
                                  dict(range=[rng[0] + 2 * (rng[1] - rng[0]) / 3, rng[1]], color="rgba(255,92,122,0.18)")])))
            g.update_layout(height=290, margin=dict(t=80, b=10, l=40, r=40))
            with col:
                ui.plotly(g, key=f"gauge_{title[:4]}")
        st.markdown(
            f"<div class='sf-note'><b>Reading now.</b> Jump share is {zi:+.1f} standard deviations from its past year "
            f"({'above' if zi > 0 else 'below'} normal), so recent risk has been more {'shock-like' if zi > 0 else 'steady and grinding'}. "
            f"The fear premium is higher than on {vr_pct:.0%} of days in the last two years. "
            "In the research, the top fifth of fear-premium days were followed by about double the usual next-month "
            "volatility, both before and after 2021.</div>", unsafe_allow_html=True)

        spy = live["px"]["Close"]["SPY"].dropna().iloc[-756:]
        zz = z.reindex(spy.index)
        f8 = go.Figure()
        f8.add_bar(x=zz.index, y=zz, marker_color=np.where(zz > 0, ui.ORANGE, ui.BLUE), name="Jump share vs past year (σ)",
                   yaxis="y2", opacity=0.6, marker_line_width=0)
        f8.add_scatter(x=spy.index, y=spy, name="SPY", line=dict(color="#e4edf3", width=1.8))
        f8.update_layout(height=360, yaxis=dict(title="SPY", side="left"),
                         yaxis2=dict(title="Jump share (σ)", overlaying="y", side="right", showgrid=False, range=[-4, 4], dtick=2),
                         legend=dict(y=1.02, yanchor="bottom"), bargap=0, margin=dict(t=40))
        ui.plotly(f8, key="radar_hist")
        st.caption("Orange = shock-driven weeks, blue = grinding weeks. The research's pattern: grinding volatility "
                   "(like 2022) tended to keep trending down, while shock-driven drops tended to snap back. From 2009 to "
                   "2018 the same rule kept you out of V-shaped recoveries, so treat it as a hypothesis.")

# ======================================================================================== 4. scoreboard
with tabs[3]:
    guide("Two signals from the research, frozen in the code on Nov 16 2026 and tracked forward on real prices "
          "every day since. Nothing gets re-tuned, so every day here is a true out-of-sample test.",
          "Each card compares the signal with simply holding the same thing. Sharpe shows once there are 20 trading "
          "days. Give it months, since a few weeks of results are mostly noise.",
          "live", "Paper results only, with no real money. This is how a quant earns the right to call something "
          "an edge.")
    if live is None:
        st.warning("Live prices aren't available right now, so the scoreboard can't refresh.")
    else:
        rec = live["rec"]
        days = len(rec["network"])
        st.markdown(f"<div class='sf-note'>Tracking since <b>{fl.FROZEN:%b %d %Y}</b> · <b>{days}</b> trading days of "
                    f"results so far · signals refresh after each close.</div>", unsafe_allow_html=True)
        cards = [
            ("Evolved fear-curve network", "Sets a position in each of 19 ETFs every evening, filled at the next open.",
             rec["network"], rec["net_bh"], "Buy-and-hold, same ETFs"),
            ("Jump-share gate on SPY", "Hold SPY only when jump share is above its 1-year average.",
             rec["gate_SPY"], rec["bh_SPY"], "Hold SPY"),
            ("Jump-share gate on QQQ", "Hold QQQ only when jump share is above its 1-year average.",
             rec["gate_QQQ"], rec["bh_QQQ"], "Hold QQQ"),
        ]
        cols = st.columns(3)
        for col, (title, rule, sr, br, bname) in zip(cols, cards):
            a, b = fl.summary(sr), fl.summary(br)
            sh = f"{a['sharpe']:.2f} vs {b['sharpe']:.2f}" if np.isfinite(a["sharpe"]) else f"after 20 days ({a['days']} so far)"
            lead = a["total"] - b["total"] if a["days"] else np.nan
            tone = "pos" if np.isfinite(lead) and lead > 0 else "neg" if np.isfinite(lead) and lead < 0 else "neu"
            col.markdown(
                f"<div class='sf-card'><div class='t'>{ui.h(title)}</div>"
                f"<div class='row'>{ui.h(rule)}</div>"
                f"<div class='row'>Signal: <b>{pct(a['total'])}</b> · {ui.h(bname)}: <b>{pct(b['total'])}</b> "
                f"{ui.pill(('ahead ' if lead > 0 else 'behind ') + pct(abs(lead)) if np.isfinite(lead) else 'no results yet', tone)}</div>"
                f"<div class='row'>Sharpe: {sh}</div></div>", unsafe_allow_html=True)

        st.subheader("Research record, then the live record")
        st.markdown("<div class='sf-note'>Each line is how far a signal is ahead of (or behind) simply holding. "
                    "Left of the line is the research period: these signals were <b>chosen</b> by looking at it, so it "
                    "flatters them. Right of the line is the live test, the only part that counts.</div>",
                    unsafe_allow_html=True)
        hist = live["hist"]
        f9 = go.Figure()
        names = [("network", "net_bh", "Fear-curve network", ui.GREEN), ("gate_SPY", "bh_SPY", "Jump gate, SPY", ui.ORANGE),
                 ("gate_QQQ", "bh_QQQ", "Jump gate, QQQ", ui.PURPLE)]
        for k, kb, title, c in names:
            sr, br = hist[k], hist[kb].reindex(hist[k].index).fillna(0)
            f9.add_scatter(x=sr.index, y=(1 + sr).cumprod() / (1 + br).cumprod() - 1, name=title,
                           line=dict(color=c, width=2.2))
        f9.add_vrect(x0=fl.FROZEN, x1=max(fl.FROZEN + pd.Timedelta(days=45), hist["network"].index.max()),
                     fillcolor="rgba(45,212,163,0.08)", line_width=0, annotation_text="LIVE",
                     annotation_position="top left")
        f9.add_vline(x=fl.FROZEN, line_color=ui.GREEN, line_width=2, line_dash="dot")
        f9.add_hline(y=0, line_color=ui.MUTED, line_width=1)
        f9.update_layout(height=340, yaxis=dict(title="Lead over holding", tickformat="+.0%"),
                         legend=dict(y=1.02, yanchor="bottom"), margin=dict(t=40))
        ui.plotly(f9, key="score_curve")

        st.subheader("Tonight's signals")
        pos = live["pos"].dropna(how="all")
        last = pos.iloc[-1].sort_values()
        g_on = bool(live["gate"].dropna().iloc[-1])
        ui.metrics([
            dict(label="Network's average position", value=f"{last.mean():+.2f}",
                 help="-1 is fully short, +1 fully long. It sits near the top most of the time and drops when the VIX curve inverts."),
            dict(label="Jump-share gate", value="In the market" if g_on else "Out (cash)"),
            dict(label="As of close", value=f"{pos.index[-1]:%b %d}"),
        ], key="tonight")
        f10 = go.Figure(go.Bar(x=last.values, y=last.index, orientation="h",
                               marker_color=[ui.GREEN if v > 0 else ui.RED for v in last.values],
                               hovertemplate="%{y}: %{x:+.2f}<extra></extra>"))
        f10.update_layout(height=380, xaxis=dict(range=[-1, 1], title="Position (-1 short … +1 long)"), margin=dict(t=10))
        ui.plotly(f10, key="tonight_bars")
        st.caption("Positions are set at the close and earn from the next open to the one after, with 3 bp costs a "
                   "side, exactly as in the research. The rules live in sharkfin/frontier.py and the networks in "
                   "research_data/frontier/evolution.json, so anyone can re-run this record.")

if live_err is not None:
    st.caption(f"Live data error: {type(live_err).__name__}")

ui.disclaimer()
