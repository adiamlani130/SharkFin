"""Builds the precomputed Frontier Lab research data read by ``sharkfin/frontier.py``.

Research tooling, not imported by the app. Run the steps in order::

    python -m sharkfin.frontier_build data       # prices + weekly Merton jump fits -> .lab4/
    python -m sharkfin.frontier_build evolve     # re-run the NEAT runs the page replays (a few minutes each)
    python -m sharkfin.frontier_build publish    # write sharkfin/research_data/frontier/*.json|csv
    python -m sharkfin.frontier_build surface    # snapshot SPY's option chain and fit Merton to it

Everything the page shows is either written here (frozen research results) or computed live from prices with
the frozen rules in ``sharkfin/frontier.py``. Nothing here is tuned on data after the Nov 13 2026 holdout end.
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import jump_lab as jl
from . import neat_core as nc
from . import neuro_lab as nl

# The pickles read and written here are only ever files this script wrote itself into the gitignored .lab4/ folder.

LAB = nl.LAB
OUT = Path(__file__).parent / "research_data" / "frontier"
EXTRA = ["^VIX", "^VIX3M", "^SKEW"]
RUNS = [("A", s, False, False) for s in (1, 2, 3)] + [("A", 1, True, False)] + \
       [("A", s, False, True) for s in (1, 2, 3)] + [("A", 1, True, True), ("A", 2, True, True)]


def tag_of(track, seed, null, market):
    return f"{track}{'m' if market else ''}{'_null' if null else ''}_s{seed}"


# ----------------------------------------------------------------------------------------- step 1: data


def download():
    import yfinance as yf
    LAB.mkdir(exist_ok=True)
    tick = nl.ETFS + EXTRA
    d = yf.download(" ".join(tick), start="2004-01-01", end="2026-11-14", auto_adjust=True, progress=False,
                    group_by="column", threads=True)
    px = {k: d[k].copy() for k in ("Open", "High", "Low", "Close", "Volume")}
    pickle.dump(px, open(LAB / "ohlcv.pkl", "wb"))
    spy = px["Close"]["SPY"].dropna()
    fits = jl.rolling_fits(spy)
    jf = jl.jump_features(fits, px["Close"]["^VIX"], px["Close"]["^SKEW"])
    pickle.dump(jf, open(LAB / "jump_features.pkl", "wb"))
    fits.to_pickle(LAB / "fits.pkl")
    print("prices", px["Close"].shape, "fits", fits.dropna().shape)


# ----------------------------------------------------------------------------------------- step 2: evolution


def evolve_all(only: str | None = None):
    for track, seed, null, market in RUNS:
        tag = tag_of(track, seed, null, market)
        if only and tag != only:
            continue
        if (LAB / f"run_{tag}.pkl").exists():
            continue
        nl.evolve(track, seed, null=null, use_market=market, pop=300, gens=120)


# ----------------------------------------------------------------------------------------- step 3: publish

# What the Nov 15 write-up reported for the two rebuilt champions: (train, pick, holdout) Sharpe skill.
ORIGINAL_REPORTED = {"orig_s1": dict(train=0.35, pick=0.47, hold=0.11), "orig_s2": dict(train=0.21, pick=0.51, hold=0.17)}


def _genome(names, out_bias, links, hidden):
    """Build a genome from links written as (source name or hidden id, target id or "out", weight)."""
    ix = {n: i for i, n in enumerate(names)}
    g = nc.Genome()
    for i in range(len(names)):
        g.nodes[i] = nc.Node(i, "in")
    out = len(names)
    g.nodes[out] = nc.Node(out, "out", "tanh", "sum", out_bias)
    for hid, (act, agg, bias) in hidden.items():
        g.nodes[out + hid] = nc.Node(out + hid, "hid", act, agg, bias)
    for k, (src, dst, w) in enumerate(links):
        s = ix[src] if isinstance(src, str) else out + src
        g.conns[k] = nc.Conn(k, s, out if dst == "out" else out + dst, w)
    return g


def original_s1(names):
    """tanh(-2.84*m_term -1.02*R5 +1.76*m_R20 +0.86*tanh(+1.71*sin(max(+1.56*r9, -0.33*r6, +1.04*j_skew_gap)
    +0.26) +0.49) -0.27*rng0 +1.25)"""
    return _genome(names, 1.25, [("m_term", "out", -2.84), ("R5", "out", -1.02), ("m_R20", "out", 1.76),
                                 (1, "out", 0.86), ("rng0", "out", -0.27), (2, 1, 1.71), ("r9", 2, 1.56),
                                 ("r6", 2, -0.33), ("j_skew_gap", 2, 1.04)],
                   {1: ("tanh", "sum", 0.49), 2: ("sin", "max", 0.26)})


def original_s2(names):
    """tanh(+0.23*m_vixz -3.07*m_term +0.65*m_R20 -5.00*log(max(-0.09*m_term) -0.05) -0.91*body0 +1.33)"""
    return _genome(names, 1.33, [("m_vixz", "out", 0.23), ("m_term", "out", -3.07), ("m_R20", "out", 0.65),
                                 (1, "out", -5.0), ("body0", "out", -0.91), ("m_term", 1, -0.09)],
                   {1: ("log", "max", -0.05)})



def genome_json(g: nc.Genome, names: list) -> dict:
    used = g.used_inputs()
    live = {c.src for c in g.conns.values() if c.on} | {c.dst for c in g.conns.values() if c.on}
    nodes = [dict(id=n.id, kind=n.kind, act=n.act, agg=n.agg, bias=round(n.bias, 5),
                  label=names[n.id] if n.kind == "in" else None)
             for n in g.nodes.values() if n.kind != "in" or n.id in used or n.id in live]
    conns = [dict(src=c.src, dst=c.dst, w=round(c.w, 5)) for c in g.conns.values() if c.on]
    return dict(nodes=nodes, conns=conns, formula=nc.describe(g, names), n_inputs=len(names))


def publish():
    OUT.mkdir(parents=True, exist_ok=True)
    px = nl.load_px()
    tasks = {}
    runs, champs = [], {}
    for track, seed, null, market in RUNS:
        tag = tag_of(track, seed, null, market)
        f = LAB / f"run_{tag}.pkl"
        if not f.exists():
            print("missing", tag)
            continue
        R = pickle.load(open(f, "rb"))
        key = (market, null, seed if null else None)
        if key not in tasks:
            tasks[key] = nl.TimingTask(px, market, seed + 1000 if null else None)
        task = tasks[key]
        champ = R["hof"][0]
        sc = {w: task.score(champ, w) for w in ("train", "pick", "hold")}
        bh = {w: nl.sharpe(task.buy_hold(w)) for w in ("train", "pick", "hold")}
        hs = nl.stats_of(sc["hold"]["series"])
        runs.append(dict(tag=tag, seed=seed, null=null, market=market, evaluated=R["summary"]["evaluated"],
                         history=[dict(gen=h["gen"], best=round(h["best"], 4), mean=round(h["mean"], 4),
                                       species=h["species"], conns=h["conns"]) for h in R["summary"]["history"]],
                         train_skill=sc["train"]["port_sharpe"] - bh["train"],
                         pick_skill=sc["pick"]["port_sharpe"] - bh["pick"],
                         hold_skill=sc["hold"]["port_sharpe"] - bh["hold"],
                         hold_sharpe=sc["hold"]["port_sharpe"], hold_cagr=hs.get("cagr"), hold_dd=hs.get("maxdd"),
                         champ_gen=champ.info["gen"], hof=len(R["hof"])))
        if not null:
            champs[tag] = champ
        print(tag, f"pick {runs[-1]['pick_skill']:+.2f} hold {runs[-1]['hold_skill']:+.2f} sharpe {runs[-1]['hold_sharpe']:.2f}")

    # The original Nov 15 champions' genomes were in a cache that no longer exists, but two of them were
    # printed in full as formulas (docs/NEURO_LAB.md, results/table_Am.csv), so they are rebuilt exactly here
    # and re-scored on the freshly downloaded data. That doubles as a reproducibility check.
    task = tasks[(True, False, None)]
    originals = {"orig_s1": original_s1(task.names), "orig_s2": original_s2(task.names)}
    orig = {}
    for k, g in originals.items():
        sc = {w: task.score(g, w)["port_sharpe"] - nl.sharpe(task.buy_hold(w)) for w in ("train", "pick", "hold")}
        orig[k] = dict(fresh=sc, reported=ORIGINAL_REPORTED[k])
        champs[k] = g
        print(k, {w: round(v, 2) for w, v in sc.items()})
    tracked = ["orig_s2"]
    rows = task.masks["hold"]
    pos = np.mean([task.positions(champs[k], rows) for k in tracked], axis=0)
    p = task.pnl(pos, rows)
    p = np.where(task.valid[rows], p, np.nan)
    ens_ret = pd.Series(np.nanmean(p, axis=1), index=task.dates[rows]).dropna()
    bh_ret = task.buy_hold("hold").dropna()
    curve = pd.DataFrame({"tracked": (1 + ens_ret).cumprod(), "buy_hold": (1 + bh_ret).cumprod(),
                          "avg_position": pd.Series(pos.mean(axis=1), index=task.dates[rows])}).dropna()
    curve.index.name = "date"
    curve.round(5).to_csv(OUT / "tracked_holdout.csv")
    yearly = pd.DataFrame({"tracked": ens_ret.groupby(ens_ret.index.year).apply(nl.sharpe),
                           "buy_hold": bh_ret.groupby(bh_ret.index.year).apply(nl.sharpe)}).round(3)

    # random-network baseline: unevolved networks of similar size, scored once on the holdout
    rng_neat = nc.Neat(task.X.shape[-1], nc.Config(pop=400), seed=99)
    rand = []
    for g in rng_neat.pop:
        for _ in range(int(rng_neat.rng.integers(0, 6))):
            g = rng_neat.mutate(g)
        rand.append(task.score(g, "hold")["port_sharpe"] - nl.sharpe(bh_ret))

    es, bs = nl.stats_of(ens_ret), nl.stats_of(bh_ret)
    out = dict(
        built=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        windows=dict(train=nl.TRAIN, pick=nl.PICK, hold=nl.HOLD),
        names=task.names, runs=runs,
        champions={k: genome_json(g, task.names) for k, g in champs.items()},
        tracked=dict(members=tracked, hold=es, buy_hold=bs, yearly={int(k): v for k, v in yearly.T.to_dict().items()}),
        originals=orig,
        random_skill=[round(x, 4) for x in rand],
        totals=dict(real=412100, noise=338800, pick_scored=8300, holdout_scored=30),
    )
    json.dump(out, open(OUT / "evolution.json", "w"), default=float)

    # weekly jump-fit history for the radar (the app appends newer weeks itself)
    fits = pd.read_pickle(LAB / "fits.pkl")
    wk = fits.dropna().drop_duplicates(subset=["sigma", "lam", "mu_j", "delta"])
    wk = wk[["mu", "sigma", "lam", "mu_j", "delta"]].astype(float)
    wk.index.name = "date"
    wk.round(6).to_csv(OUT / "jump_fits.csv")
    print("tracked hold", es, "B&H", bs)


# ----------------------------------------------------------------------------------------- step 4: surface


def surface():
    """Snapshot SPY's listed options (bid/ask mids, OTM side), fit risk-neutral Merton, save quotes + fit."""
    import yfinance as yf
    OUT.mkdir(parents=True, exist_ok=True)
    t = yf.Ticker("SPY")
    S = float(t.history(period="5d")["Close"].iloc[-1])
    asof = pd.Timestamp(t.history(period="5d").index[-1]).tz_localize(None).normalize()
    r = float(yf.Ticker("^IRX").history(period="5d")["Close"].iloc[-1]) / 100
    rows = []
    for e in t.options:
        T = (pd.Timestamp(e) + pd.Timedelta(hours=16) - (asof + pd.Timedelta(hours=16))).days / 365
        if T < 10 / 365 or T > 1.1:
            continue
        ch = t.option_chain(e)
        for side, df in (("call", ch.calls), ("put", ch.puts)):
            df = df[(df.bid > 0) & (df.ask > df.bid)]
            for k, b, a, oi in zip(df.strike, df.bid, df.ask, df.openInterest.fillna(0)):
                m = math.log(k / S)
                if (side == "call" and k < S) or (side == "put" and k > S) or abs(m) > 0.35 or oi < 50:
                    continue
                mid = (a + b) / 2
                if (a - b) / mid > 0.25:
                    continue
                iv = jl.implied_vol(mid, S, k, T, r, call=side == "call")
                if np.isfinite(iv) and 0.03 < iv < 1.5:
                    rows.append(dict(K=float(k), T=round(T, 5), expiry=e, side=side, iv=round(iv, 5),
                                     m=round(m, 5), oi=int(oi)))
    q = pd.DataFrame(rows)
    # thin to an even grid so one expiry with 200 strikes doesn't dominate the fit
    q["mb"] = (q.m / 0.02).round()
    q = q.sort_values("oi", ascending=False).drop_duplicates(["expiry", "mb"]).drop(columns="mb")
    fit = jl.calibrate_surface(q, S, r)
    bs = float(np.sqrt(np.mean((q.iv - q.iv.mean()) ** 2)))
    qm = q.copy()
    qm["merton_iv"] = [jl.merton_iv(S, k, tt, r, fit["sigma"], fit["lam"], fit["mu_j"], fit["delta"])
                       for k, tt in zip(q.K, q["T"])]
    hist = pd.read_pickle(LAB / "fits.pkl").dropna().iloc[-1][["mu", "sigma", "lam", "mu_j", "delta"]].astype(float).to_dict()
    out = dict(asof=str(asof.date()), S=S, r=r, n=len(q), fit=fit,
               rmse_volpts=float(np.sqrt(np.mean((qm.merton_iv - qm.iv) ** 2)) * 100), bs_flat_rmse_volpts=bs * 100,
               bs_flat_vol=float(q.iv.mean()), historical=hist,
               quotes=qm.sort_values(["T", "K"]).round(5).to_dict(orient="records"))
    json.dump(out, open(OUT / "surface.json", "w"), default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "quotes"}, default=float))


if __name__ == "__main__":  # pragma: no cover
    step = sys.argv[1]
    {"data": download, "evolve": lambda: evolve_all(sys.argv[2] if len(sys.argv) > 2 else None),
     "publish": publish, "surface": surface}[step]()
