"""High-Speculation Radar: early-stage trends that could be the next Micron or SanDisk, what would prove them,
and whether the market has started to notice yet."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sharkfin import data, speculation as sp, ui

ui.header("Speculation Radar",
          "Big trends caught early: the bottleneck behind each one, what would prove it, what could kill it, "
          "and whether the market has started to notice. Small bets only.")

TONE_COLOR = {"pos": ui.GREEN, "info": ui.BLUE, "neu": ui.MUTED, "neg": ui.RED}
STAGE_COLOR = {k: TONE_COLOR[v[1]] for k, v in sp.STAGES.items()}


@st.cache_data(ttl=1800, show_spinner=False)
def prices() -> pd.DataFrame:
    return data.download_prices(tuple(sp.all_tickers() + ["SPY"]), "3y")


def pct(x, digits=0):
    return ui.fmt_pct(x, digits, sign=True) if np.isfinite(x) else "–"


def updown(x) -> str:
    return "sf-up" if np.isfinite(x) and x > 0 else "sf-down" if np.isfinite(x) and x < 0 else ""


def stage_pill(name: str) -> str:
    return f"<span class='sf-pill sf-{sp.STAGES[name][1]}'>{ui.h(name)}</span>"


with st.spinner("Reading the themes' price action…"):
    try:
        px = prices()
    except Exception:  # noqa: BLE001  (offline or Yahoo down: the research still shows)
        px = pd.DataFrame()
spy = px["SPY"] if "SPY" in px else None
plays, themes = sp.radar(px, spy) if not px.empty else (pd.DataFrame(), pd.DataFrame())
theme_stage = dict(zip(themes["key"], themes["stage"])) if len(themes) else {}

# ---------------------------------------------------------------------------
# How to use it
# ---------------------------------------------------------------------------
st.markdown(
    "<div class='sf-hero sf-rise'><div class='k'>The idea</div>"
    "<div class='v' style='font-size:1.45rem'>Find the bottleneck before the crowd does.</div>"
    "<div class='s'>Micron and SanDisk didn't come out of nowhere: memory was the thing AI couldn't get enough of, "
    "and the stocks started turning up months before the headlines. Each theme below names its bottleneck, the "
    "evidence so far, and a radar reading of whether the market has started to notice. "
    "<b>Keep each name to about 1-3% of your money and the whole section to about 15%.</b> These are research "
    "notes as of " + sp.AS_OF + ", not tested strategies.</div></div>",
    unsafe_allow_html=True)

legend = "".join(f"<div class='sf-stage'>{stage_pill(k)}<span>{ui.h(v[0])}</span></div>" for k, v in sp.STAGES.items())
with st.expander("What the radar stages mean", expanded=False):
    st.markdown(f"<div class='sf-stages'>{legend}</div>", unsafe_allow_html=True)
    st.caption("Each reading uses only prices up to today: the 200-day average, the 6- and 12-month change, the "
               "distance from the 52-week high and the 6-month return against SPY. A theme's reading is an "
               "equal-weight basket of its stocks.")

# ---------------------------------------------------------------------------
# The case study
# ---------------------------------------------------------------------------
st.subheader("The pattern: how Micron looked before its run")
if "MU" in px and px["MU"].dropna().size > 300:
    mu = px["MU"].dropna()
    hist = sp.stage_history(mu, spy, step=5)
    fig = go.Figure()
    # Shade each stretch by the stage the radar read at the time (only past prices for each reading).
    if len(hist):
        runs, start, cur = [], hist.index[0], hist.iloc[0]
        for d, s in hist.items():
            if s != cur:
                runs.append([start, d, cur])
                start, cur = d, s
        runs.append([start, mu.index[-1], cur])
        # merge blips shorter than a month into the stretch before, so the shading reads as phases
        merged = []
        for r in runs:
            if merged and (r[1] - r[0]).days < 30:
                merged[-1][1] = r[1]
            elif merged and merged[-1][2] == r[2]:
                merged[-1][1] = r[1]
            else:
                merged.append(r)
        runs = merged
        for a, b, s in runs:
            fig.add_vrect(x0=a, x1=b, fillcolor=STAGE_COLOR[s], opacity=0.10, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=mu.index, y=mu, name="Micron (MU)", line=dict(color="#e4edf3", width=1.8),
                             hovertemplate="%{x|%b %d, %Y}<br>$%{y:,.0f}<extra></extra>"))
    for s, c in STAGE_COLOR.items():  # legend chips for the shading
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=s,
                                 marker=dict(size=10, color=c, symbol="square", opacity=0.6)))
    first_turn = hist[hist == "Turning up"].index
    first_turn = first_turn[first_turn >= mu.index[-1] - pd.Timedelta(days=700)]
    if len(first_turn):
        t0 = first_turn[0]
        fig.add_annotation(x=t0, y=float(mu.loc[:t0].iloc[-1]), text=f"Radar: Turning up<br>{t0:%b %Y}",
                           showarrow=True, arrowhead=0, ay=-60, font=dict(size=11, color=ui.GREEN),
                           arrowcolor=ui.GREEN)
    lo, hi = float(mu.min()), float(mu.max())
    fig.update_layout(yaxis=dict(type="log", range=[np.log10(lo * 0.85), np.log10(hi * 1.15)], tickprefix="$"),
                      hovermode="x unified", margin=dict(t=20))
    ui.plotly(fig, height=360, key="sp-mu")
    gain = float(mu.iloc[-1] / mu.loc[first_turn[0]:].iloc[0] - 1) if len(first_turn) else np.nan
    st.caption("Shading shows what the radar would have said at the time, using only prices up to each day. "
               + (f"From its first 'Turning up' reading Micron gained {gain:+.0%}. " if np.isfinite(gain) else "")
               + "Micron is picked with hindsight, so this shows what the pattern looks like, not proof the radar "
                 "finds winners: plenty of themes turn up and fade.")
steps = "".join(f"<li><b>{ui.h(t)}.</b> {ui.h(d)}</li>" for t, d in sp.CASE_NOTES)
st.markdown(f"<ol class='sf-steps sf-timeline'>{steps}</ol>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# The radar
# ---------------------------------------------------------------------------
st.subheader("The themes")
order = {s: i for i, s in enumerate(sp.STAGE_ORDER)}
ranked = sorted(sp.THEMES, key=lambda t: order.get(theme_stage.get(t.key, "Quiet"), 9))
cards = []
for t in ranked:
    row = themes.set_index("key").loc[t.key] if t.key in theme_stage else None
    stg = theme_stage.get(t.key)
    nums = (f"<div class='nums'><span>6 mo <b class='{updown(row['6m'])}'>{pct(row['6m'])}</b></span>"
            f"<span>12 mo <b class='{updown(row['12m'])}'>{pct(row['12m'])}</b></span>"
            f"<span>vs 200-day <b>{pct(row['vs200'])}</b></span></div>") if row is not None else ""
    yours = "<span class='sf-pill sf-info'>From your book</span>" if t.from_you else ""
    tickers = " ".join(f"<code>{ui.h(p.ticker)}</code>" for p in t.plays)
    cards.append(f"<div class='sf-theme' style='--c:{STAGE_COLOR.get(stg, ui.MUTED)}'>"
                 f"<div class='top'>{stage_pill(stg) if stg else ''}{yours}<span class='hz'>{ui.h(t.horizon)}</span></div>"
                 f"<div class='nm'>{ui.h(t.name)}</div><div class='tg'>{ui.h(t.tagline)}</div>{nums}"
                 f"<div class='tk'>{tickers}</div></div>")
st.markdown(f"<div class='sf-themes'>{''.join(cards)}</div>", unsafe_allow_html=True)
if px.empty:
    st.info("Live prices are unavailable right now, so the radar readings are hidden. The research below still shows.")

# ---------------------------------------------------------------------------
# One theme in depth
# ---------------------------------------------------------------------------
st.subheader("Dig into a theme")
names = {t.name: t for t in ranked}
pick = st.selectbox("Theme", list(names), key="sp-theme", label_visibility="collapsed")
t = names[pick]

left, right = st.columns([1.15, 1], gap="large")
with left:
    st.markdown(f"<div class='sf-card'><div class='t'>The bottleneck</div><div class='row'>{ui.h(t.bottleneck)}</div></div>",
                unsafe_allow_html=True)
    lis = lambda xs: "".join(f"<li>{ui.h(x)}</li>" for x in xs)
    st.markdown(f"<h5 class='sf-h5'>Why now</h5><ul class='sf-steps'>{lis(t.why_now)}</ul>", unsafe_allow_html=True)
with right:
    syms = [p.ticker for p in t.plays if p.ticker in px and px[p.ticker].dropna().size > 60]
    if syms:
        win = px[syms + ["SPY"]].iloc[-252:]
        fig = go.Figure()
        for s in syms + ["SPY"]:
            c = win[s].dropna()
            if c.empty:
                continue
            fig.add_trace(go.Scatter(x=c.index, y=c / c.iloc[0] * 100 - 100, name=s,
                                     line=dict(width=2.2 if s != "SPY" else 1.4, dash="dot" if s == "SPY" else None,
                                               color=ui.MUTED if s == "SPY" else None),
                                     hovertemplate=f"{s} %{{y:+.0f}}%<extra></extra>"))
        fig.update_layout(title="The last 12 months (% change)", hovermode="x unified", yaxis_ticksuffix="%")
        ui.plotly(fig, height=330, key=f"sp-chart-{t.key}")

st.markdown(f"<div class='sf-cols two'><div><h5>What would prove it</h5><ul class='sf-steps ok'>{lis(t.proof)}</ul></div>"
            f"<div><h5>What could kill it</h5><ul class='sf-steps bad'>{lis(t.risks)}</ul></div></div>",
            unsafe_allow_html=True)

tp = plays[plays["key"] == t.key] if len(plays) else pd.DataFrame()
rows = []
for p in t.plays:
    r = tp[tp["Ticker"] == p.ticker].iloc[0] if len(tp) and (tp["Ticker"] == p.ticker).any() else {}
    g = lambda k: r.get(k, np.nan) if len(r) else np.nan
    rows.append({"Ticker": p.ticker, "Company": p.name, "Risk": p.tier, "Radar": g("stage") if len(r) else "–",
                 "Price": g("price"), "1 month": g("1m"), "6 months": g("6m"), "12 months": g("12m"),
                 "Off its high": g("off_high"), "Why it's here": p.why})
tbl = pd.DataFrame(rows)
for c in ("1 month", "6 months", "12 months", "Off its high"):
    tbl[c] = pd.to_numeric(tbl[c], errors="coerce") * 100
st.dataframe(tbl, hide_index=True, width="stretch", column_config={
    "Price": st.column_config.NumberColumn(format="%.2f"),
    **{c: st.column_config.NumberColumn(format="%+.0f%%") for c in ("1 month", "6 months", "12 months", "Off its high")},
    "Why it's here": st.column_config.TextColumn(width="large"),
    "Risk": st.column_config.TextColumn(help=" ".join(f"{k}: {v}" for k, v in sp.TIER_HELP.items())),
})
if t.sources:
    st.caption("Sources: " + " · ".join(f"[{u.split('/')[2].replace('www.', '')}]({u})" for u in t.sources))

# ---------------------------------------------------------------------------
# Everything on one screen
# ---------------------------------------------------------------------------
with st.expander("Every name on the radar"):
    if len(plays) and "stage" in plays:
        allp = plays[["Ticker", "Company", "Theme", "Tier", "stage", "6m", "12m", "vs200", "off_high"]].copy()
        allp["sort"] = allp["stage"].map(order)
        allp = allp.sort_values(["sort", "6m"], ascending=[True, False]).drop(columns="sort")
        for c in ("6m", "12m", "vs200", "off_high"):
            allp[c] = allp[c] * 100
        st.dataframe(allp.rename(columns={"Tier": "Risk", "stage": "Radar", "6m": "6 months", "12m": "12 months",
                                          "vs200": "vs 200-day", "off_high": "Off its high"}),
                     hide_index=True, width="stretch", column_config={
                         c: st.column_config.NumberColumn(format="%+.0f%%")
                         for c in ("6 months", "12 months", "vs 200-day", "Off its high")})
    else:
        st.info("Live prices are unavailable right now.")

st.caption("How to use this: watch for a theme moving from Quiet to Turning up while its 'what would prove it' list "
           "starts coming true. Buy small, in pieces, and expect 50% drops along the way even when the idea is right.")
ui.disclaimer()
