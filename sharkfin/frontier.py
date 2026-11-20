"""Frontier Lab research engine (research only; the Frontier Lab page was removed from the app in Nov 2026).

It reads the frozen research results in ``research_data/frontier``
(written by ``sharkfin/frontier_build.py``) and computes three live things from prices with rules that were
frozen on Nov 16 2026:

* a fast, vectorised Merton jump-diffusion option pricer, so the 3D volatility surface can be re-drawn
  live as someone drags the jump sliders;
* the weekly Merton fit on SPY's trailing two years (the "jump radar"), topped up with any weeks since the
  saved history;
* the forward paper record of two signals that were never used to trade: the evolved fear-curve ETF network
  (seed 2 of the Nov 15 VIX-and-jumps runs, the one that reproduced on fresh data) and the jump-share gate. Their rules are committed, so anyone can re-run the record.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from . import neat_core as nc

DIR = Path(__file__).parent / "research_data" / "frontier"
FROZEN = pd.Timestamp("2026-11-16")          # rules frozen; every signal from this close on is out of sample
ETFS = "SPY QQQ IWM DIA MDY XLK XLF XLV XLY XLI XLP XLE XLU XLB TLT IEF GLD HYG LQD".split()
EXTRA = ["^VIX", "^VIX3M", "^SKEW"]
GATE_ASSETS = ("SPY", "QQQ")
COST = 0.0003


@lru_cache(maxsize=4)
def _read_json(name: str, mtime: float) -> dict:
    return json.loads((DIR / name).read_text())


def load(name: str) -> dict:
    p = DIR / name
    return _read_json(name, p.stat().st_mtime) if p.exists() else {}


def load_csv(name: str) -> pd.DataFrame:
    p = DIR / name
    return pd.read_csv(p, index_col=0, parse_dates=True) if p.exists() else pd.DataFrame()


# ----------------------------------------------------------------------------------------- pricing (vectorised)


def bs_price(S, K, T, r, vol, call):
    sq = vol * np.sqrt(T)
    d1 = (np.log(S / K) + (r + 0.5 * vol ** 2) * T) / sq
    d2 = d1 - sq
    c = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
    p = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
    return np.where(call, c, p)


def merton_price(S, K, T, r, sigma, lam, mu_j, delta, call, n_max=40):
    """Merton (1976): a Poisson-weighted sum of Black-Scholes prices, on whole arrays of strikes/expiries."""
    k = math.exp(mu_j + 0.5 * delta ** 2) - 1
    lp = lam * (1 + k)
    out = np.zeros(np.broadcast(K, T).shape)
    for n in range(n_max + 1):
        w = stats.poisson.pmf(n, lp * T)
        if n > lp * np.max(T) + 5 and np.max(w) < 1e-10:
            break
        vol_n = np.sqrt(sigma ** 2 + n * delta ** 2 / T)
        r_n = r - lam * k + n * (mu_j + 0.5 * delta ** 2) / T
        out = out + w * bs_price(S, K, T, r_n, vol_n, call)
    return out


def implied_vol(price, S, K, T, r, call, iters=60):
    """Black-Scholes implied vol by bisection, for whole arrays at once."""
    lo, hi = np.full(np.shape(price), 1e-3), np.full(np.shape(price), 3.0)
    for _ in range(iters):
        mid = (lo + hi) / 2
        up = bs_price(S, K, T, r, mid, call) > price
        hi, lo = np.where(up, mid, hi), np.where(up, lo, mid)
    iv = (lo + hi) / 2
    return np.where((iv < 2.99) & (iv > 0.0011), iv, np.nan)


def merton_iv(S, K, T, r, sigma, lam, mu_j, delta):
    """Implied-vol smile Merton produces, quoted on the out-of-the-money side as a desk would."""
    K, T = np.broadcast_arrays(np.asarray(K, float), np.asarray(T, float))
    call = K >= S
    return implied_vol(merton_price(S, K, T, r, sigma, lam, mu_j, delta, call), S, K, T, r, call)


def surface_grid(S, r, p: dict, m=np.linspace(-0.25, 0.12, 30), T=np.linspace(0.05, 1.0, 24)):
    MM, TT = np.meshgrid(m, T)
    iv = merton_iv(S, S * np.exp(MM), TT, r, p["sigma"], p["lam"], p["mu_j"], p["delta"])
    return m, T, iv


def fit_error(sv: dict, p: dict) -> float:
    q = pd.DataFrame(sv["quotes"])
    iv = merton_iv(sv["S"], q.K.to_numpy(), q["T"].to_numpy(), sv["r"], p["sigma"], p["lam"], p["mu_j"], p["delta"])
    return float(np.sqrt(np.nanmean((iv - q.iv.to_numpy()) ** 2)) * 100)


def return_density(p: dict, t: float, x=np.linspace(-0.9, 0.3, 1201), n_max=40):
    """Density of the log return over ``t`` years under Merton (Poisson mixture of normals, zero drift)."""
    k = math.exp(p["mu_j"] + 0.5 * p["delta"] ** 2) - 1
    out = np.zeros_like(x)
    for n in range(n_max + 1):
        w = stats.poisson.pmf(n, p["lam"] * t)
        if w < 1e-14 and n > p["lam"] * t:
            break
        m = (-0.5 * p["sigma"] ** 2 - p["lam"] * k) * t + n * p["mu_j"]
        out += w * stats.norm.pdf(x, m, math.sqrt(p["sigma"] ** 2 * t + n * p["delta"] ** 2))
    return x, out


def crash_odds(p: dict, t: float, drop: float = -0.15) -> float:
    """Chance the log return over ``t`` falls below ``log(1+drop)``."""
    x, d = return_density(p, t, np.linspace(-1.5, 0.6, 4201))
    cut = math.log(1 + drop)
    return float(np.trapezoid(d[x <= cut], x[x <= cut]))


# ----------------------------------------------------------------------------------------- jump features


def merton_skew(sigma, lam, mu_j, delta, t):
    """Skewness of the Merton log return over t (closed-form cumulants, the ones SymPy derived in jump_lab)."""
    c2 = t * (sigma ** 2 + lam * (mu_j ** 2 + delta ** 2))
    c3 = lam * t * mu_j * (mu_j ** 2 + 3 * delta ** 2)
    return c3 / c2 ** 1.5


def features_from_fits(fits: pd.DataFrame, vix: pd.Series, skew: pd.Series | None) -> pd.DataFrame:
    """Same definitions as ``jump_lab.jump_features`` (jump share, jump-adjusted VRP, skew gap)."""
    jv = fits["lam"] * (fits["mu_j"] ** 2 + fits["delta"] ** 2)
    tot = fits["sigma"] ** 2 + jv
    out = pd.DataFrame(index=fits.index)
    out["jump_share"] = jv / tot
    out["fair_vol"] = np.sqrt(tot)
    out["lam"] = fits["lam"]
    out["vrp"] = vix.reindex(fits.index) / 100 - out["fair_vol"]
    out["skew30"] = merton_skew(fits["sigma"], fits["lam"], fits["mu_j"], fits["delta"], 30 / 365)
    if skew is not None:
        out["skew_gap"] = skew.reindex(fits.index) - (100 - 10 * out["skew30"])
    return out


def zscore(x: pd.Series, n=252, min_n=120) -> pd.Series:
    return (x - x.rolling(n, min_periods=min_n).mean()) / x.rolling(n, min_periods=min_n).std()


def topped_up_fits(spy_close: pd.Series) -> pd.DataFrame:
    """Saved weekly Merton fits plus a fresh fit every 5 trading days since the last saved one (each on the
    trailing 504 daily returns, data up to that close only). Returned daily, forward-filled."""
    from . import jump_lab as jl
    saved = load_csv("jump_fits.csv")
    c = spy_close.dropna()
    lr = np.log(c).diff()
    rows = {}
    last = saved.index.max() if len(saved) else c.index[503]
    start = c.index.searchsorted(last) + 5
    prev = list(saved.iloc[-1][["mu", "sigma", "lam", "mu_j", "delta"]]) if len(saved) else None
    for i in range(max(start, 504), len(c), 5):
        f = jl.fit_merton(lr.iloc[i - 503: i + 1].to_numpy(), start=prev)
        if f:
            prev = [f["mu"], f["sigma"], f["lam"], f["mu_j"], f["delta"]]
            rows[c.index[i]] = {k: f[k] for k in ("mu", "sigma", "lam", "mu_j", "delta")}
    new = pd.DataFrame(rows).T
    allf = pd.concat([saved, new]) if len(new) else saved
    idx = allf.index.union(c.index)
    return allf.reindex(idx).ffill().reindex(c.index)


# ----------------------------------------------------------------------------------------- evolved network


def genome_from_json(d: dict) -> nc.Genome:
    g = nc.Genome()
    for n in d["nodes"]:
        g.nodes[n["id"]] = nc.Node(n["id"], n["kind"], n["act"], n["agg"], n["bias"])
    for i in range(d["n_inputs"]):                  # unused inputs still need a slot
        g.nodes.setdefault(i, nc.Node(i, "in"))
    for i, c in enumerate(d["conns"]):
        g.conns[i] = nc.Conn(i, c["src"], c["dst"], c["w"])
    return g


def market_inputs(C: pd.DataFrame, jf: pd.DataFrame) -> pd.DataFrame:
    """The seven context inputs, exactly as in ``neuro_lab.market_features``."""
    spy = C["SPY"]
    lr = np.log(spy).diff()
    vol = lr.rolling(60).std()
    lv = np.log(C["^VIX"])
    out = pd.DataFrame(index=C.index)
    out["m_r0"] = lr / vol
    out["m_R20"] = np.log(spy / spy.shift(20)) / (vol * math.sqrt(20))
    out["m_vixz"] = (lv - lv.rolling(252).mean()) / lv.rolling(252).std()
    out["m_term"] = np.log(C["^VIX"] / C["^VIX3M"]) * 5
    j = jf.reindex(C.index)
    for c in ("jump_share", "vrp", "skew_gap"):
        out[f"j_{c}"] = zscore(j[c])
    return out


def tracked_positions(px: dict, jf: pd.DataFrame) -> pd.DataFrame:
    """Each evening's position (-1..+1) per ETF from the frozen tracked network(s), averaged."""
    from . import neuro_lab as nl
    ev = load("evolution.json")
    cols = [t for t in ETFS if t in px["Close"]]
    O, H, L, C, V = (px[k][cols] for k in ("Open", "High", "Low", "Close", "Volume"))
    feats, valid = nl.raw_features(O, H, L, C, V)
    X, names = nl.to_cube(feats, valid, market_inputs(px["Close"], jf))
    assert names == ev["names"], "feature order changed since the networks were frozen"
    vm = valid.to_numpy()
    pos = []
    for tag in ev["tracked"]["members"]:
        g = genome_from_json(ev["champions"][tag])
        p = np.zeros(vm.shape, np.float32)
        p[vm] = np.tanh(nc.activate(g, X[vm]))
        pos.append(p)
    return pd.DataFrame(np.mean(pos, axis=0), index=C.index, columns=cols).where(valid)


def forward_record(px: dict, pos: pd.DataFrame, gate: pd.Series, since: pd.Timestamp = FROZEN) -> dict:
    """Paper results since the freeze. The network's position set at close t earns open t+1 -> open t+2
    (same timing as the research); the gate set at close t earns close t -> close t+1."""
    O, C = px["Open"], px["Close"]
    cols = list(pos.columns)
    ret = O[cols].shift(-2) / O[cols].shift(-1) - 1
    dpos = pos.fillna(0).diff().abs()
    pnl = (pos * ret - COST * dpos).where(ret.notna())
    live = pnl.index >= since
    net = pnl[live].mean(axis=1).dropna()
    bh = ret[live].mean(axis=1).dropna()
    out = dict(network=net, net_bh=bh)
    for a in GATE_ASSETS:
        r = C[a].pct_change().shift(-1)
        g = gate.reindex(C.index).fillna(0)
        gr = (g * r - COST * g.diff().abs().fillna(0)).where(r.notna())
        out[f"gate_{a}"] = gr[live].dropna()
        out[f"bh_{a}"] = r[live].dropna()
    return out


def summary(r: pd.Series) -> dict:
    r = r.dropna()
    if not len(r):
        return dict(days=0, total=np.nan, sharpe=np.nan, maxdd=np.nan)
    eq = (1 + r).cumprod()
    sh = float(r.mean() / r.std() * math.sqrt(252)) if len(r) >= 20 and r.std() > 0 else np.nan
    return dict(days=len(r), total=float(eq.iloc[-1] - 1), sharpe=sh, maxdd=float((eq / eq.cummax() - 1).min()))


def network_layout(gj: dict) -> tuple[dict, list]:
    """(x, y) for each node of a champion network: inputs on the left, output on the right, hidden nodes by
    depth. Returns positions and the enabled connections."""
    nodes = {n["id"]: n for n in gj["nodes"]}
    conns = [c for c in gj["conns"] if c["src"] in nodes and c["dst"] in nodes]
    depth = {i: 0 for i, n in nodes.items() if n["kind"] == "in"}
    for _ in range(len(nodes) + 1):
        for c in conns:
            if c["src"] in depth:
                depth[c["dst"]] = max(depth.get(c["dst"], 0), depth[c["src"]] + 1)
    out_id = next(i for i, n in nodes.items() if n["kind"] == "out")
    maxd = max(depth.values()) if depth else 1
    depth[out_id] = maxd
    cols: dict = {}
    for i in nodes:
        cols.setdefault(depth.get(i, 1), []).append(i)
    pos = {}
    for d, ids in cols.items():
        ids.sort()
        for k, i in enumerate(ids):
            pos[i] = (d / max(maxd, 1), (k + 1) / (len(ids) + 1))
    return pos, conns
