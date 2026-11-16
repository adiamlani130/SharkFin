"""Neuroevolution lab: NEAT evolves trading signals straight from raw price and volume.

Research only, nothing in the app imports this. Run ``python -m sharkfin.neuro_lab <track> <seed> [--null]``.

Two tracks
----------
A. **ETF timing.** One network is shared by 19 liquid ETFs (stock indexes, sectors, bonds, gold). Each
   evening it reads that ETF's raw recent bars and outputs a position from -1 (short) to +1 (long), filled
   at the next open. Because the same network must work on every ETF in every regime, it cannot just
   memorise one chart.
B. **Stock stat-arb.** One network scores every S&P 500 member (point-in-time list) each week. Buy the top
   10%, short the bottom 10%, hold a week. Market-neutral, so any profit is a cross-sectional edge, the
   "hidden arbitrage in the noise" the idea is about.

Honesty rules
-------------
* Evolution only ever sees **2006-2016** (train). Each generation's best few are scored on
  **2017 - Oct 12 2021** (pick window), and the champion is the one that did best there. The
  **Oct 13 2021 - Nov 2026** holdout is run once, after everything is frozen.
* A signal seen at a close trades at the next open. Costs: 3 bp a side on ETFs, 5 bp on stocks.
* Fitness rewards consistency: the score is the average Sharpe over (asset x 4 time blocks) minus half
  their spread, minus a small charge per connection. A lucky single year cannot carry a genome.
* ``--null`` runs the *same* evolution on data where the link between inputs and future returns is
  destroyed (targets shifted in time for A, shuffled across stocks each week for B). Whatever those runs
  "find" is pure overfitting, so it is the bar a real result has to clear.
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import neat_core as nc

LAB = Path(".lab4")
TRAIN = ("2006-01-01", "2016-12-31")
PICK = ("2017-01-01", "2021-10-12")
HOLD = ("2021-10-13", "2026-11-13")
BLOCKS = [("2006-01-01", "2008-12-31"), ("2009-01-01", "2011-12-31"), ("2012-01-01", "2014-12-31"),
          ("2015-01-01", "2016-12-31")]
ETFS = "SPY QQQ IWM DIA MDY XLK XLF XLV XLY XLI XLP XLE XLU XLB TLT IEF GLD HYG LQD".split()


# ----------------------------------------------------------------------------------------- features


def load_px():
    # pickle: only ever files this lab wrote itself into the gitignored .lab4/ folder
    return pickle.load(open(LAB / "ohlcv.pkl", "rb"))


def raw_features(O, H, L, C, V):
    """Raw-bar inputs, each a dates x tickers frame known at that day's close. No hand-built indicators:
    just recent returns (scaled by the stock's own volatility so every asset speaks the same units),
    volume versus normal, where the close sat in the day's range, gaps, range size, and longer returns."""
    lr = np.log(C).diff()
    vol = lr.rolling(60, min_periods=40).std()
    f = {}
    for k in range(10):
        f[f"r{k}"] = lr.shift(k) / vol
    for n in (5, 20, 60, 250):
        f[f"R{n}"] = np.log(C / C.shift(n)) / (vol * math.sqrt(n))
    lv = np.log(V.where(V > 0) / V.where(V > 0).rolling(50, min_periods=20).mean())
    for k in range(5):
        f[f"v{k}"] = lv.shift(k)
    rngd = (H - L).where(H > L)
    clv = (2 * (C - L) / rngd - 1)
    for k in range(3):
        f[f"clv{k}"] = clv.shift(k)
    hl = np.log(H / L)
    f["rng0"] = hl / hl.rolling(60, min_periods=40).mean() - 1
    f["rng5"] = hl.rolling(5).mean() / hl.rolling(60, min_periods=40).mean() - 1
    f["gap0"] = np.log(O / C.shift(1)) / vol
    f["body0"] = np.log(C / O) / vol
    f["volr"] = np.log(lr.rolling(20).std() / lr.rolling(250, min_periods=150).std())
    lo, hi = C.rolling(250, min_periods=150).min(), C.rolling(250, min_periods=150).max()
    f["pos250"] = 2 * (C - lo) / (hi - lo) - 1
    valid = vol.notna() & C.notna() & O.notna()
    return f, valid


def market_features(px, index):
    """Optional context inputs shared by every asset: the market's own day and month, VIX level versus its
    past year and VIX term structure (option-market fear), plus Merton jump-risk features if computed."""
    C = px["Close"]
    spy = C["SPY"]
    lr = np.log(spy).diff()
    vol = lr.rolling(60).std()
    vix = C["^VIX"]
    lv = np.log(vix)
    out = pd.DataFrame(index=C.index)
    out["m_r0"] = lr / vol
    out["m_R20"] = np.log(spy / spy.shift(20)) / (vol * math.sqrt(20))
    out["m_vixz"] = (lv - lv.rolling(252).mean()) / lv.rolling(252).std()
    out["m_term"] = np.log(vix / C["^VIX3M"]) * 5
    jf = LAB / "jump_features.pkl"
    if jf.exists():
        j = pickle.load(open(jf, "rb")).reindex(C.index)
        for c in ("jump_share", "vrp", "skew_gap"):
            if c in j:
                x = j[c]
                out[f"j_{c}"] = (x - x.rolling(252, min_periods=120).mean()) / x.rolling(252, min_periods=120).std()
    return out.reindex(index)


def to_cube(feats: dict, valid: pd.DataFrame, extra: pd.DataFrame | None = None):
    names = list(feats)
    T, N = valid.shape
    F = len(names) + (extra.shape[1] if extra is not None else 0)
    X = np.zeros((T, N, F), np.float32)
    for i, n in enumerate(names):
        X[:, :, i] = feats[n].reindex(index=valid.index, columns=valid.columns).to_numpy(np.float32)
    if extra is not None:
        for j, c in enumerate(extra.columns):
            X[:, :, len(names) + j] = extra[c].to_numpy(np.float32)[:, None]
        names = names + list(extra.columns)
    X = np.clip(np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0), -5, 5)
    return X, names


def sharpe(x, per=252):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 10 or x.std() == 0:
        return 0.0
    return float(x.mean() / x.std() * math.sqrt(per))


def stats_of(r: pd.Series, per=252):
    r = r.dropna()
    if len(r) < 5:
        return {}
    eq = (1 + r).cumprod()
    yrs = len(r) / per
    return dict(cagr=float(eq.iloc[-1] ** (1 / yrs) - 1), sharpe=sharpe(r, per), maxdd=float((eq / eq.cummax() - 1).min()),
                vol=float(r.std() * math.sqrt(per)))


# ----------------------------------------------------------------------------------------- track A: ETF timing


class TimingTask:
    cost = 0.0003

    def __init__(self, px, use_market=False, null_seed=None):
        cols = [t for t in ETFS if t in px["Close"]]
        O, H, L, C, V = (px[k][cols] for k in ("Open", "High", "Low", "Close", "Volume"))
        feats, valid = raw_features(O, H, L, C, V)
        extra = market_features(px, C.index) if use_market else None
        X, self.names = to_cube(feats, valid, extra)
        ret = (O.shift(-2) / O.shift(-1) - 1)            # position chosen at close t earns open t+1 -> t+2
        valid &= ret.notna()
        if null_seed is not None:                         # break the link: shift each target in time
            rng = np.random.default_rng(null_seed)
            r2 = ret.copy()
            for c in r2:
                s = r2[c].dropna()
                k = int(rng.integers(250, len(s) - 250))
                r2.loc[s.index, c] = np.roll(s.to_numpy(), k)
            ret = r2
        self.dates, self.cols = C.index, cols
        self.X, self.valid, self.ret = X, valid.to_numpy(), ret.fillna(0).to_numpy()
        d = self.dates
        self.masks = {k: (d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b)) for k, (a, b) in
                      dict(train=TRAIN, pick=PICK, hold=HOLD).items()}
        self.blocks = [(d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b)) for a, b in BLOCKS]
        self.train_rows = self.masks["train"] | self.masks["pick"] | self.masks["hold"]

    def positions(self, g, rows=None, long_only=False):
        rows = self.masks["train"] if rows is None else rows
        sub = self.X[rows]
        vm = self.valid[rows]
        out = np.zeros(vm.shape, np.float32)
        out[vm] = nc.activate(g, sub[vm])
        out = np.tanh(out) if nc.ACTS else out
        return np.maximum(out, 0) if long_only else out

    def pnl(self, pos, rows):
        r = self.ret[rows]
        dpos = np.abs(np.diff(pos, axis=0, prepend=0))
        return pos * r - self.cost * dpos

    def fitness(self, g):
        rows = self.masks["train"]
        p = self.pnl(self.positions(g, rows), rows)
        vm = self.valid[rows]
        sub_blocks = [b[rows] for b in self.blocks]
        sh = []
        for j in range(p.shape[1]):
            for b in sub_blocks:
                m = b & vm[:, j]
                if m.sum() > 100:
                    sh.append(sharpe(p[m, j]))
        sh = np.array(sh)
        return float(sh.mean() - 0.5 * sh.std() - 0.004 * g.n_active)

    def score(self, g, window, long_only=False):
        rows = self.masks[window]
        p = self.pnl(self.positions(g, rows, long_only), rows)
        vm = self.valid[rows]
        p = np.where(vm, p, np.nan)
        port = np.nanmean(p, axis=1)
        per_asset = [sharpe(p[vm[:, j], j]) for j in range(p.shape[1])]
        return dict(port_sharpe=sharpe(port), mean_asset_sharpe=float(np.mean(per_asset)),
                    per_asset=dict(zip(self.cols, per_asset)),
                    series=pd.Series(port, index=self.dates[rows]))

    def buy_hold(self, window):
        rows = self.masks[window]
        r = np.where(self.valid[rows], self.ret[rows], np.nan)
        return pd.Series(np.nanmean(r, axis=1), index=self.dates[rows])


# ----------------------------------------------------------------------------------------- track B: stock stat-arb


class StatArbTask:
    cost = 0.0005
    q = 0.10

    def __init__(self, px, null_seed=None, use_market=False):
        from . import data as sd
        L_ = pickle.load(open(LAB / "lists.pkl", "rb"))
        C = px["Close"]
        cols = [t for t in dict.fromkeys(L_["stocks"]) if t in C and C[t].notna().sum() > 300]
        O, H, L, Cc, V = (px[k][cols].ffill(limit=5) for k in ("Open", "High", "Low", "Close", "Volume"))
        feats, valid = raw_features(O, H, L, Cc, V)
        fwd = O.shift(-6) / O.shift(-1) - 1
        mem = sd.sp500_members(Cc.index, cols)
        idx = Cc.index
        wk = np.arange(260, len(idx) - 6, 5)               # weekly rebalance dates
        d = idx[wk]
        valid = (valid & mem & fwd.notna()).iloc[wk]
        X = np.zeros((len(wk), len(cols), len(feats)), np.float32)
        for i, n in enumerate(feats):
            v = feats[n].iloc[wk].where(valid)
            v = v.sub(v.mean(axis=1), axis=0).div(v.std(axis=1) + 1e-9, axis=0)   # cross-sectional z-score
            X[:, :, i] = v.to_numpy(np.float32)
        self.names = list(feats)
        if use_market:
            ex = market_features(px, d)
            X = np.concatenate([X, np.repeat(ex.to_numpy(np.float32)[:, None, :], len(cols), axis=1)], axis=2)
            self.names += list(ex.columns)
        self.X = np.clip(np.nan_to_num(X), -5, 5)
        f = fwd.iloc[wk].to_numpy()
        f = np.clip(f, -0.9, 3.0)
        self.valid = valid.to_numpy()
        if null_seed is not None:                         # shuffle returns across stocks within each week
            rng = np.random.default_rng(null_seed)
            for w in range(len(wk)):
                ix = np.where(self.valid[w])[0]
                f[w, ix] = f[w, rng.permutation(ix)]
        self.fwd = np.nan_to_num(f)
        self.dates, self.cols = d, cols
        self.jitter = np.random.default_rng(7).random(self.valid.shape).astype(np.float32) * 1e-5
        self.masks = {k: (d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b)) for k, (a, b) in
                      dict(train=TRAIN, pick=PICK, hold=HOLD).items()}
        self.blocks = [(d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b)) for a, b in BLOCKS]

    def scores(self, g, rows):
        vm = self.valid[rows]
        s = np.full(vm.shape, np.nan, np.float32)
        s[vm] = nc.activate(g, self.X[rows][vm])
        return s + self.jitter[rows]

    def weekly(self, g, rows, long_only=False):
        s = self.scores(g, rows)
        vm = self.valid[rows]
        n = vm.sum(1)
        k = np.maximum((n * self.q).astype(int), 1)
        hi = np.where(vm, s, -np.inf)
        order = np.argsort(-hi, axis=1)
        rank = np.empty_like(order)
        np.put_along_axis(rank, order, np.arange(order.shape[1])[None, :].repeat(order.shape[0], 0), axis=1)
        top = rank < k[:, None]
        lo = np.where(vm, s, np.inf)
        order2 = np.argsort(lo, axis=1)
        rank2 = np.empty_like(order2)
        np.put_along_axis(rank2, order2, np.arange(order2.shape[1])[None, :].repeat(order2.shape[0], 0), axis=1)
        bot = (rank2 < k[:, None]) & vm
        w = top / k[:, None]
        mkt = np.where(vm, self.fwd[rows], 0).sum(1) / np.maximum(n, 1)
        if long_only:
            gross = (w * self.fwd[rows]).sum(1)
            to = np.abs(np.diff(w, axis=0, prepend=0)).sum(1)
            return gross - self.cost * to, mkt
        w = w - bot / k[:, None]
        gross = (w * self.fwd[rows]).sum(1)
        to = np.abs(np.diff(w, axis=0, prepend=0)).sum(1)
        return gross - self.cost * to, mkt

    def fitness(self, g):
        rows = self.masks["train"]
        r, _ = self.weekly(g, rows)
        sh = np.array([sharpe(r[b[rows]], 52) for b in self.blocks])
        return float(sh.mean() - 0.5 * sh.std() - 0.004 * g.n_active)

    def score(self, g, window, long_only=False):
        rows = self.masks[window]
        r, m = self.weekly(g, rows, long_only)
        return dict(port_sharpe=sharpe(r, 52), series=pd.Series(r, index=self.dates[rows]),
                    mkt=pd.Series(m, index=self.dates[rows]))


# ----------------------------------------------------------------------------------------- track C: overlay


class OverlayTask:
    """C. **Exposure overlay for the app's own strategies.** One network reads the market's raw bars (SPY),
    VIX/term-structure and the Merton jump features each evening and sets tomorrow's exposure, 0-100%, for
    both Dive Zone and Tech Breakout Rider (uninvested cash earns T-bills). This is the "confluence" use:
    the evolved model does not pick stocks, it decides how much of a proven strategy to run."""
    cost = 0.0003
    STRATS = ("dive_zone", "tech_breakout_rider")

    def __init__(self, px, null_seed=None, use_market=True):
        gr = pd.read_csv(Path(__file__).parent / "research_data" / "growth_returns.csv", index_col=0, parse_dates=True)
        C = px["Close"][["SPY"]]
        feats, valid = raw_features(*(px[k][["SPY"]] for k in ("Open", "High", "Low", "Close", "Volume")))
        extra = market_features(px, C.index)
        X, self.names = to_cube(feats, valid, extra)
        X = X[:, 0, :]
        idx = gr.index.intersection(C.index)
        pos = C.index.get_indexer(idx)
        # features at the previous close decide exposure for today's close-to-close strategy return
        self.X = X[np.maximum(pos - 1, 0)]
        self.ret = gr.loc[idx, list(self.STRATS)].to_numpy()
        self.tb = gr.loc[idx, "tbill"].fillna(0).to_numpy()
        if null_seed is not None:
            rng = np.random.default_rng(null_seed)
            k = int(rng.integers(500, len(idx) - 500))
            self.X = np.roll(self.X, k, axis=0)          # break the link between features and returns
        self.dates = idx
        self.cols = list(self.STRATS)
        d = idx
        self.masks = {k: (d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b)) for k, (a, b) in
                      dict(train=TRAIN, pick=PICK, hold=HOLD).items()}
        self.blocks = [(d >= pd.Timestamp(a)) & (d <= pd.Timestamp(b)) for a, b in BLOCKS]

    def exposure(self, g, rows):
        return (np.tanh(nc.activate(g, self.X[rows])) + 1) / 2

    def pnl(self, g, rows, expo=None):
        e = self.exposure(g, rows) if expo is None else expo
        e = e[:, None]
        r = self.ret[rows]
        # excess return over T-bills: a mostly-in-cash overlay must not get a Sharpe bonus from the cash yield
        return e * (r - self.tb[rows][:, None]) - self.cost * np.abs(np.diff(e, axis=0, prepend=e[:1]))

    def fitness(self, g):
        rows = self.masks["train"]
        p = self.pnl(g, rows)
        sh = np.array([sharpe(p[b[rows], j]) for j in range(p.shape[1]) for b in self.blocks])
        return float(sh.mean() - 0.5 * sh.std() - 0.004 * g.n_active)

    def score(self, g, window, long_only=False):
        rows = self.masks[window]
        p = self.pnl(g, rows)
        each = [sharpe(p[:, j]) for j in range(p.shape[1])]
        return dict(port_sharpe=float(np.mean(each)), per_asset=dict(zip(self.cols, each)),
                    series=pd.Series(p.mean(1), index=self.dates[rows]), exposure=float(self.exposure(g, rows).mean()))


# ----------------------------------------------------------------------------------------- driver

_TASK = None


def _fit(g):
    return nc.safe_fitness(_TASK.fitness, g)


def evolve(track: str, seed: int, null: bool = False, use_market: bool = False, pop=200, gens=80, hof_per_gen=3):
    """One evolution run. Returns the run summary and saves the hall of fame (genomes + scores)."""
    global _TASK
    import multiprocessing as mp
    px = load_px()
    nseed = seed + 1000 if null else None
    _TASK = (TimingTask(px, use_market, nseed) if track == "A" else
             StatArbTask(px, nseed, use_market) if track == "B" else OverlayTask(px, nseed))
    task = _TASK
    cfg = nc.Config(pop=pop, gens=gens)
    neat = nc.Neat(task.X.shape[-1], cfg, seed=seed)
    ctx = mp.get_context("fork")
    pool = ctx.Pool(4)
    neat.map_fn = lambda f, gs: pool.map(_fit, gs, chunksize=4)
    hof, seen = [], set()
    tag = f"{track}{'m' if use_market else ''}{'_null' if null else ''}_s{seed}"

    def cb(gen, best, ne):
        ranked = sorted(ne.pop, key=lambda g: g.fitness, reverse=True)
        added = 0
        for g in ranked:
            if g.fitness == -math.inf:
                continue
            key = nc.describe(g, task.names)
            if key in seen:
                continue
            seen.add(key)
            g2 = g.copy()
            g2.fitness = g.fitness
            g2.info = dict(gen=gen, pick=task.score(g2, "pick")["port_sharpe"])
            hof.append(g2)
            added += 1
            if added >= hof_per_gen:
                break
        h = ne.history[-1]
        print(f"[{tag}] gen {gen:3d} train fit {h['best']:+.3f} mean {h['mean']:+.3f} species {h['species']:2d} "
              f"conns {h['conns']:2d} hid {h['hidden']} | best pick {max(x.info['pick'] for x in hof):+.2f}", flush=True)
    neat.run(_fit, cb)
    pool.close()
    hof.sort(key=lambda g: g.info["pick"], reverse=True)
    out = dict(tag=tag, evaluated=neat.evaluated, hof_size=len(hof), history=neat.history,
               names=task.names)
    pickle.dump(dict(hof=hof, summary=out), open(LAB / f"run_{tag}.pkl", "wb"))
    return out


if __name__ == "__main__":  # pragma: no cover
    tr, sd_ = sys.argv[1], int(sys.argv[2])
    flags = set(sys.argv[3:])
    gens = next((int(f.split("=")[1]) for f in flags if f.startswith("--gens=")), 80)
    pop = next((int(f.split("=")[1]) for f in flags if f.startswith("--pop=")), 200)
    res = evolve(tr, sd_, null="--null" in flags, use_market="--market" in flags, pop=pop, gens=gens)
    print(json.dumps({k: v for k, v in res.items() if k != "history"}, default=str)[:500])
