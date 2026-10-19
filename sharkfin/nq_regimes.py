"""GEX and VIX as a daily playbook for NQ: trade today or sit out, and which strategy to run today.

Each day is put in a regime cell from what is known before the decision: VIX and the VIX/VIX3M curve as of
the prior close (for a day trade) or that day's close (for a swing decision filled next open), and the prior
session's GEX ranked against the trailing year. A router then learns, from past days only, which candidate
strategy earned the most in each cell, and runs that one (or nothing) today.

The learning is online and causal: every ``REFIT`` days the router re-scores each cell on the trailing
``window`` days that had already finished, so a router run on data cut at any date gives the same past.
``walkforward.run`` then picks the router's own settings (regime scheme, how sure it must be, window) on each
training window, exactly like any other strategy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from sharkfin import nq_lab as lab
from sharkfin import walkforward as wf

REFIT = 21          # re-score the cells about monthly
MIN_ROWS = 20       # a cell needs this many past days before it is trusted

# --------------------------------------------------------------------------------------------- regimes

VIX_BANDS = [0, 15, 20, 25, 30, np.inf]
VIX3_BANDS = [0, 17, 24, np.inf]
GEX_BANDS = [0, 0.2, 0.4, 0.6, 0.8, 1.01]
GEX3_BANDS = [0, 1 / 3, 2 / 3, 1.01]
TERM_BANDS = [0, 0.85, 0.92, 1.0, np.inf]
TERM3_BANDS = [0, 0.9, 1.0, np.inf]

SCHEMES = ["vix", "gex", "term", "vix_gex", "gex_term", "vix_move"]


def _cut(x: pd.Series, edges) -> pd.Series:
    return pd.Series(pd.cut(x, edges, labels=False, right=False), index=x.index)


def inputs(d: dict, idx: pd.DatetimeIndex, day_trade: bool) -> pd.DataFrame:
    """VIX, VIX/VIX3M, its 10-day trend and GEX rank as known when each decision in ``idx`` is made."""
    v, v3 = d["vix"].reindex(d["px"].index), d["vix3m"].reindex(d["px"].index)
    move = v / lab.ema(v, 10) - 1
    f = pd.DataFrame({"vix": v, "term": v / v3, "move": move})
    if day_trade:  # before the open only yesterday's close exists
        f = f.shift(1)
    f["gex"] = lab.gex_pct(d, d["px"].index)
    return f.reindex(idx)


def labels(f: pd.DataFrame, scheme: str) -> pd.Series:
    """Regime cell number per day (NaN when an input is missing)."""
    if scheme == "vix":
        return _cut(f["vix"], VIX_BANDS)
    if scheme == "gex":
        return _cut(f["gex"], GEX_BANDS)
    if scheme == "term":
        return _cut(f["term"], TERM_BANDS)
    if scheme == "vix_gex":
        return _cut(f["vix"], VIX3_BANDS) * 3 + _cut(f["gex"], GEX3_BANDS)
    if scheme == "gex_term":
        return _cut(f["gex"], GEX3_BANDS) * 3 + _cut(f["term"], TERM3_BANDS)
    if scheme == "vix_move":  # VIX rising or falling vs its 10-day EMA, by GEX tercile
        return (f["move"] > 0).astype(float).where(f["move"].notna()) * 3 + _cut(f["gex"], GEX3_BANDS)
    raise ValueError(scheme)


def _bands(edges) -> list:
    out = []
    for a, b in zip(edges, edges[1:]):
        out.append(f"under {b:g}" if a == 0 else f"{a:g}+" if not np.isfinite(b) else f"{a:g}-{b:g}")
    return out


def cell_names(scheme: str) -> dict:
    g5 = ["GEX bottom 20%", "GEX 20-40%", "GEX 40-60%", "GEX 60-80%", "GEX top 20%"]
    g3 = ["low GEX", "mid GEX", "high GEX"]
    if scheme == "vix":
        return dict(enumerate(f"VIX {b}" for b in _bands(VIX_BANDS)))
    if scheme == "gex":
        return dict(enumerate(g5))
    if scheme == "term":
        return dict(enumerate(f"VIX/VIX3M {b}" for b in _bands(TERM_BANDS)))
    if scheme == "vix_gex":
        return {i * 3 + j: f"VIX {v}, {g}" for i, v in enumerate(_bands(VIX3_BANDS)) for j, g in enumerate(g3)}
    if scheme == "gex_term":
        return {i * 3 + j: f"{g}, VIX/VIX3M {t}" for i, g in enumerate(g3) for j, t in enumerate(_bands(TERM3_BANDS))}
    if scheme == "vix_move":
        return {i * 3 + j: f"VIX {m}, {g}" for i, m in enumerate(["falling", "rising"]) for j, g in enumerate(g3)}
    raise ValueError(scheme)


# --------------------------------------------------------------------------------------------- candidates

DAY_CANDIDATES = {
    "Long open to close": (lab.day_long_only, {}),
    "Short open to close": None,  # mirror of the long, built in day_matrix
    "ORB 30 min, 2R target": (lab.opening_range_breakout, {"minutes": 30, "stop": 1.0, "target": 2.0, "filter": "none"}),
    "ORB 15 min, ride to close": (lab.opening_range_breakout, {"minutes": 15, "stop": 1.0, "target": 0, "filter": "none"}),
    "Gap and go": (lab.gap_go, {"gap": 0.0025, "filter": "none"}),
    "Gap fade": (lab.gap_fade, {"gap": 0.0025, "stop": 1.0, "filter": "none"}),
    "Last-30-min momentum": (lab.intraday_momentum, {"th": 0.0, "filter": "none"}),
    "VWAP + EMA trend": (lab.vwap_ema_trend, {"fast": 9, "slow": 21, "start": 30, "short": 1, "filter": "none"}),
    "Bollinger fade": (lab.bollinger_fade, {"z": 2.5, "filter": "none"}),
    "Prior-day level fade": (lab.prior_day_levels, {"mode": "fade", "stop": 0.25}),
    "Prior-day level break": (lab.prior_day_levels, {"mode": "break", "stop": 0.25}),
}

SWING_CANDIDATES = {
    "Long NQ": lambda d: pd.Series(1.0, index=d["px"].index),
    "Short NQ": lambda d: pd.Series(-1.0, index=d["px"].index),
    "IBS reversion": lambda d: lab.ibs_reversion.signal(d, {"entry": 0.2, "exit": 0.8, "trend": 0}),
    "RSI(2) dip": lambda d: lab.rsi2_dip.signal(d, {"entry": 10, "exit": 70, "trend": 0}),
    "EMA 20/100 trend": lambda d: lab.ema_cross.signal(d, {"fast": 20, "slow": 100, "short": 0}),
    "Donchian 20/10": lambda d: lab.donchian.signal(d, {"n": 20, "m": 10, "vix_cap": 99}),
    "VIX spike buy": lambda d: lab.vix_spike_buy.signal(d, {"k": 0.2, "hold": 5}),
}


def day_matrix(d: dict) -> pd.DataFrame:
    """Each day candidate's net return per session (no T-bill), built from the data handed in."""
    dv = lab.day_view(d)
    hit = d.get("_day_matrix")
    if hit is not None and hit.index.equals(dv.days):
        return hit
    cols = {}
    for name, spec in DAY_CANDIDATES.items():
        if spec is None:
            continue
        fn, p = spec
        cols[name] = fn.day_fn(dv, p)
    m = pd.DataFrame(cols, index=dv.days)
    m.insert(1, "Short open to close", -m["Long open to close"] - 4 * lab.COST)
    d["_day_matrix"] = m
    return m


def swing_matrix(d: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Each swing candidate's positions (decided at each close) and the daily returns they earn (no T-bill)."""
    idx = d["px"].index
    hit = d.get("_swing_matrix")
    if hit is not None and hit[0].index.equals(idx):
        return hit
    pos = pd.DataFrame({n: f(d).reindex(idx).fillna(0.0) for n, f in SWING_CANDIDATES.items()})
    rets = pd.DataFrame({n: lab.swing_returns(d, pos[n], idx[0]) - d["rf"] for n in pos})
    d["_swing_matrix"] = (pos, rets)
    return pos, rets


# --------------------------------------------------------------------------------------------- the router


def route(rets: np.ndarray, lab_ret: np.ndarray, lab_now: np.ndarray, window: int, min_t: float,
          allowed: np.ndarray | None = None) -> np.ndarray:
    """Online choice of a candidate per day.

    ``rets[s, k]``: candidate k's return on day s. ``lab_ret[s]``: the cell day s's return was earned in.
    ``lab_now[i]``: the cell known when deciding for decision ``i``. The choice for decision ``i`` uses only
    rows ``s < i`` (rows ``<= i - 1``, all finished before the decision), re-scored every ``REFIT`` rows.
    A cell picks the candidate with the best mean return if its t-stat clears ``min_t``, else -1 (no trade).
    """
    n, k = rets.shape
    out = np.full(n, -1)
    table: dict = {}
    for i in range(n):
        if i % REFIT == 0:
            lo = 0 if window <= 0 else max(0, i - window)
            r, g = rets[lo:i], lab_ret[lo:i]
            table = {}
            for c in np.unique(g[np.isfinite(g)]):
                rows = r[g == c]
                rows = rows[np.isfinite(rows).all(axis=1)] if len(rows) else rows
                if len(rows) < MIN_ROWS:
                    continue
                mu, sd = rows.mean(axis=0), rows.std(axis=0, ddof=1)
                t = np.divide(mu * np.sqrt(len(rows)), sd, out=np.zeros_like(mu), where=sd > 0)
                if allowed is not None:
                    t = np.where(allowed, t, -np.inf)
                best = int(np.argmax(np.where(t > min_t, mu, -np.inf)))
                table[c] = best if t[best] > min_t and mu[best] > 0 else -1
        c = lab_now[i]
        out[i] = table.get(c, -1) if np.isfinite(c) else -1
    return out


TRACE: list | None = None  # tests and reports read the router's choices from here


def _allowed(names, only):
    return None if only == "all" else np.array([n == only for n in names])


def day_router(d, p, start):
    m = day_matrix(d)
    f = inputs(d, m.index, day_trade=True)
    g = labels(f, p["scheme"]).to_numpy(float)
    choice = route(m.to_numpy(float), g, g, p["window"], p["min_t"], _allowed(list(m.columns), p.get("only", "all")))
    r = np.where(choice >= 0, m.to_numpy(float)[np.arange(len(m)), np.maximum(choice, 0)], 0.0)
    if TRACE is not None:
        TRACE.append(pd.DataFrame({"cell": g, "choice": [m.columns[c] if c >= 0 else "No trade" for c in choice]},
                                  index=m.index))
    rf = d["rf"].reindex(m.index).fillna(0.0)
    return {"returns": (pd.Series(np.nan_to_num(r), index=m.index) + rf).loc[start:]}


def swing_router(d, p, start):
    return {"returns": lab.swing_returns(d, swing_router.signal(d, p), start)}


def _swing_router_signal(d, p):
    pos, rets = swing_matrix(d)
    idx = pos.index
    now = labels(inputs(d, idx, day_trade=False), p["scheme"]).to_numpy(float)  # cell known at close t
    earned_in = np.r_[np.nan, now[:-1]]  # day s's return comes from the decision at close s-1
    # route() decides row i from rows < i. The decision at close t may use returns of days <= t, so it is
    # row t + 1 of a table padded with one empty row at the end; its cell is now[t].
    r = np.vstack([rets.to_numpy(float), np.full((1, rets.shape[1]), np.nan)])
    choice = route(r, np.r_[earned_in, np.nan], np.r_[np.nan, now], p["window"], p["min_t"],
                   _allowed(list(pos.columns), p.get("only", "all")))
    dec = choice[1:]  # dec[t]: the candidate chosen at close t
    sig = np.where(dec >= 0, pos.to_numpy(float)[np.arange(len(pos)), np.maximum(dec, 0)], 0.0)
    if TRACE is not None:
        TRACE.append(pd.DataFrame({"cell": now,
                                   "choice": [pos.columns[c] if c >= 0 else "No trade" for c in dec]}, index=idx))
    return pd.Series(sig, index=idx)


swing_router.signal = _swing_router_signal

@lab._sw
def fear_bounce(d, p):
    """Long NQ for the next session only after a fearful close: VIX at or over ``vix`` while GEX ranks under
    ``gex`` (dealers short gamma, so moves overshoot and snap back)."""
    f = inputs(d, d["px"].index, day_trade=False)
    return ((f["vix"] >= p["vix"]) & (f["gex"] < p["gex"])).astype(float)


@lab._sw
def regime_sized(d, p):
    """Always long NQ, but ``boost``x in fear with low gamma, and flat in fear with high gamma."""
    f = inputs(d, d["px"].index, day_trade=False)
    fear = f["vix"] >= p["vix"]
    size = pd.Series(1.0, index=f.index)
    size[fear & (f["gex"] < 1 / 3)] = p["boost"]
    size[fear & (f["gex"] > 2 / 3)] = p["high_gex"]
    return size.where(f["gex"].notna(), 1.0)


def _fear_day(dv, p):
    """Buy the 09:35 open and sell 15:55 only when yesterday closed with VIX at or over ``vix`` and GEX under
    ``gex``."""
    ok = (dv.vix >= p["vix"]) & (dv.gex < p["gex"])
    side = ok.astype(int)
    inf = np.full(len(side), np.inf)
    return lab.bracket(dv, side, np.ones(len(side), int), -inf, inf)


fear_day = lab._day(_fear_day)

ROUTER_GRID = wf.grid(scheme=SCHEMES, min_t=[0.0, 1.0, 2.0], window=[756, 0])


def gate_grid(names):
    return [dict(p, only=n) for n in names for p in wf.grid(scheme=SCHEMES, min_t=[0.0, 1.0], window=[756, 0])]


def catalogue() -> list:
    """Routers and one-strategy gates, as ``nq_lab.Strategy`` entries."""
    S = lab.Strategy
    needs_s, needs_d = ("vix", "vix3m", "gex"), ("vix", "vix3m", "gex", "ic")
    out = [S("Swing router: regime picks today's strategy", "swing", swing_router, ROUTER_GRID, needs_s,
             "Each day, run the swing candidate that earned most in today's VIX/GEX cell (or stay out)."),
           S("Day router: regime picks today's strategy", "day", day_router, ROUTER_GRID, needs_d,
             "Each morning, run the day-trade candidate that earned most in today's VIX/GEX cell (or sit out).")]
    out += [S("Fear bounce (swing)", "swing", fear_bounce, wf.grid(vix=[20, 25, 30], gex=[0.2, 0.35, 0.5, 1.01]),
              needs_s, "Hold NQ for one session after a close with VIX high and GEX low."),
            S("Regime-sized long", "swing", regime_sized,
              wf.grid(vix=[20, 25, 30], boost=[1.0, 1.5, 2.0], high_gex=[0.0, 0.5, 1.0]), needs_s,
              "Always long; bigger in fear with low gamma, smaller or flat in fear with high gamma."),
            S("Fear day long (day)", "day", fear_day, wf.grid(vix=[20, 25, 30], gex=[0.2, 0.35, 0.5, 1.01]),
              needs_d, "Buy the open, sell 15:55, only after a close with VIX high and GEX low.")]
    for n in ("IBS reversion", "Long NQ", "RSI(2) dip", "EMA 20/100 trend"):
        out.append(S(f"Swing gate: {n}", "swing", swing_router, [dict(p, only=n) for p in ROUTER_GRID], needs_s,
                     f"{n}, only in VIX/GEX cells where it has earned money before."))
    for n in ("Long open to close", "Last-30-min momentum", "ORB 30 min, 2R target", "Gap and go",
              "VWAP + EMA trend", "Short open to close"):
        out.append(S(f"Day gate: {n}", "day", day_router, [dict(p, only=n) for p in ROUTER_GRID], needs_d,
                     f"{n}, only on days whose VIX/GEX cell has paid for it before."))
    return out


# --------------------------------------------------------------------------------------------- level map


def level_map(d: dict, scheme: str, kind: str, start=None) -> pd.DataFrame:
    """Descriptive (whole-sample) table: per cell, how many days, next-session range and drift, and each
    candidate's average return. It describes history; the routers above are the tested version."""
    if kind == "day":
        m = day_matrix(d)
        f = inputs(d, m.index, day_trade=True)
        dv = lab.day_view(d)
        extra = pd.DataFrame({"Range %": (dv.h.max(1) - dv.l.min(1)) / dv.o[:, 0] * 100,
                              "Open-close %": (dv.c[:, -1] / dv.o[:, 0] - 1) * 100}, index=m.index)
    else:
        _, m = swing_matrix(d)
        f = inputs(d, m.index, day_trade=False).shift(1)  # the cell each day's return was earned in
        px = d["px"]
        extra = pd.DataFrame({"Range %": (px["h"] - px["l"]) / px["o"] * 100,
                              "Open-close %": (px["c"] / px["o"] - 1) * 100}).reindex(m.index)
    g = labels(f, scheme)
    t = pd.concat([m * 1e4, extra], axis=1)  # candidate returns in basis points
    if start is not None:
        t, g = t.loc[start:], g.loc[start:]
    out = t.groupby(g).mean()
    out.insert(0, "Days", g.value_counts().reindex(out.index))
    out.index = [cell_names(scheme)[int(c)] for c in out.index]
    return out


def main(folder: str, out: str) -> pd.DataFrame:  # pragma: no cover - research run
    """Walk every router and gate forward, and write the level maps, into ``out``."""
    from pathlib import Path

    global TRACE
    d = lab.load(folder)
    o = Path(out)
    o.mkdir(parents=True, exist_ok=True)
    rows, curves, picks = [], {}, []
    for kind in ("swing", "day"):
        sts = [s for s in catalogue() if s.kind == kind]
        t0 = max(lab.first_usable(d, s.needs) for s in sts)
        for st in sts:
            res = lab.run_one(st, d, t0)
            # replay the test years with the settings each fold picked, recording the router's choices
            for f, fold in zip(res["folds"].itertuples(), res["fold_list"] if "scheme" in st.points[0] else []):
                TRACE = []
                st.evaluate(lab.wf.cut(d, fold.test_end), f.settings, fold.test_start)
                tr = TRACE[-1].loc[fold.test_start:fold.test_end]
                TRACE = None
                tr = tr.assign(Strategy=st.name, scheme=f.settings["scheme"],
                               cell_name=[cell_names(f.settings["scheme"]).get(int(c), "?") if np.isfinite(c) else "n/a"
                                          for c in tr["cell"]])
                picks.append(tr)
            s = lab.stats(res["returns"], d["rf"])
            fo = res["folds"]
            rows.append({"Strategy": st.name, "Kind": kind, **s,
                         "Folds beating cash": lab._folds_beating_cash(res, d["rf"]), "Stable": res["stable"],
                         "Most picked": fo["Settings"].value_counts().index[0], "Picks": " | ".join(fo["Settings"]),
                         "How": st.how})
            curves[st.name] = res["returns"]
            print(f"{st.name:55s} Sharpe {s['Sharpe']:5.2f}  over cash {s['Over cash/yr']:6.1%}  "
                  f"drop {s['Max drop']:6.1%}  in mkt {s['Time in market']:4.0%}", flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(o / "regime_results.csv", index=False)
    pd.DataFrame(curves).to_csv(o / "regime_returns.csv")
    pd.concat(picks).to_csv(o / "router_choices.csv")
    for kind in ("day", "swing"):
        for sc in SCHEMES:
            level_map(d, sc, kind).to_csv(o / f"levels_{kind}_{sc}.csv")
    return t


if __name__ == "__main__":  # pragma: no cover
    import sys
    main(sys.argv[1], sys.argv[2])
