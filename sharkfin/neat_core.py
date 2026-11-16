"""A small, dependency-free NEAT (NeuroEvolution of Augmenting Topologies) engine, vectorised for backtests.

Research only: nothing in the app imports this.

What it is
----------
NEAT (Stanley & Miikkulainen, 2002) evolves both the weights *and the wiring* of a neural network.
Each genome is a list of node genes and connection genes. Every new connection gets a global
"innovation number", so two genomes can be lined up gene by gene for crossover, and genomes are grouped
into *species* by how different their genes are. Species share fitness, which protects new structure
(a fresh hidden node usually hurts at first) long enough for its weights to be tuned.

Two changes make it suit trading signals:

* **Many math functions, not one.** Each hidden node draws its own activation (sin, gauss, abs, tanh,
  square, step, log, ...) and its own way of combining inputs (sum, product, max, min). This is the
  CPPN flavour of NEAT. A network can build a ratio, a threshold, a "this AND that" product, or a
  periodic pattern, so it is not limited to the moving-average shapes a person would write.
* **Feature-selective start (FS-NEAT).** With ~30 raw inputs, genomes start with only a couple of
  random input->output links and must *earn* every extra input, instead of starting fully connected.

Networks are feed-forward (no loops), evaluated on a whole matrix of samples at once with numpy, so one
genome is scored on hundreds of thousands of (day, asset) rows in a few milliseconds.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ----------------------------------------------------------------------------------------- math palette


def _sgn(x):
    return np.tanh(4.0 * x)


ACTS = {
    "id": lambda x: x,
    "tanh": np.tanh,
    "sin": np.sin,
    "gauss": lambda x: np.exp(-x * x),
    "abs": np.abs,
    "relu": lambda x: np.maximum(x, 0.0),
    "square": lambda x: np.minimum(x * x, 25.0),
    "step": _sgn,
    "log": lambda x: np.sign(x) * np.log1p(np.abs(x)),
    "inv": lambda x: x / (1.0 + np.abs(x)),
}
ACT_NAMES = list(ACTS)
AGGS = ("sum", "prod", "max", "min")


@dataclass
class Node:
    id: int
    kind: str            # "in", "out", "hid"
    act: str = "id"
    agg: str = "sum"
    bias: float = 0.0


@dataclass
class Conn:
    innov: int
    src: int
    dst: int
    w: float
    on: bool = True


@dataclass
class Genome:
    nodes: dict = field(default_factory=dict)   # id -> Node
    conns: dict = field(default_factory=dict)   # innov -> Conn
    fitness: float = -math.inf
    adj_fitness: float = 0.0
    species: int = -1
    info: dict = field(default_factory=dict)

    def copy(self) -> "Genome":
        g = Genome({k: Node(**vars(v)) for k, v in self.nodes.items()},
                   {k: Conn(**vars(v)) for k, v in self.conns.items()})
        return g

    @property
    def n_active(self) -> int:
        return sum(c.on for c in self.conns.values())

    def used_inputs(self) -> set:
        """Input ids that actually reach the output through enabled links."""
        live = {c.dst: [] for c in self.conns.values()}
        for c in self.conns.values():
            if c.on:
                live.setdefault(c.dst, []).append(c.src)
        out = [n.id for n in self.nodes.values() if n.kind == "out"]
        seen, stack = set(), list(out)
        while stack:
            v = stack.pop()
            for s in live.get(v, []):
                if s not in seen:
                    seen.add(s)
                    stack.append(s)
        return {i for i in seen if self.nodes[i].kind == "in"}


class Innovations:
    """Global registry so the same structural change gets the same innovation number in one run."""

    def __init__(self, start_node: int):
        self.conn = {}
        self.split = {}
        self.next_innov = 0
        self.next_node = start_node

    def conn_id(self, src, dst):
        k = (src, dst)
        if k not in self.conn:
            self.conn[k] = self.next_innov
            self.next_innov += 1
        return self.conn[k]

    def split_node(self, innov):
        if innov not in self.split:
            self.split[innov] = self.next_node
            self.next_node += 1
        return self.split[innov]


# ----------------------------------------------------------------------------------------- evaluation


def topo_order(g: Genome) -> list:
    """Hidden and output node ids in an order where every node comes after its inputs."""
    incoming = {i: [] for i in g.nodes}
    for c in g.conns.values():
        if c.on:
            incoming[c.dst].append(c.src)
    order, state = [], {}

    def visit(v):
        if state.get(v) == 2:
            return
        if state.get(v) == 1:
            raise ValueError("cycle")
        state[v] = 1
        for s in incoming[v]:
            visit(s)
        state[v] = 2
        if g.nodes[v].kind != "in":
            order.append(v)
    for v in g.nodes:
        visit(v)
    return order


def activate(g: Genome, X: np.ndarray, clip: float = 10.0) -> np.ndarray:
    """Run the network on every row of ``X`` (rows = samples, columns = inputs in id order 0..n-1)."""
    vals = {}
    for n in g.nodes.values():
        if n.kind == "in":
            vals[n.id] = X[:, n.id]
    incoming = {}
    for c in g.conns.values():
        if c.on:
            incoming.setdefault(c.dst, []).append(c)
    out_id = None
    for v in topo_order(g):
        n = g.nodes[v]
        terms = [vals[c.src] * c.w for c in incoming.get(v, []) if c.src in vals]
        if not terms:
            z = np.zeros(X.shape[0], dtype=X.dtype)
        elif len(terms) == 1 or n.agg == "sum":
            z = terms[0] if len(terms) == 1 else np.sum(terms, axis=0)
        elif n.agg == "prod":
            z = np.prod(np.clip(terms, -clip, clip), axis=0)
        elif n.agg == "max":
            z = np.max(terms, axis=0)
        else:
            z = np.min(terms, axis=0)
        z = ACTS[n.act](z + n.bias)
        vals[v] = np.clip(np.nan_to_num(z, nan=0.0, posinf=clip, neginf=-clip), -clip, clip).astype(X.dtype)
        if n.kind == "out":
            out_id = v
    return vals[out_id]


def describe(g: Genome, names: list) -> str:
    """Human-readable formula of the network (for the write-up)."""
    incoming = {}
    for c in g.conns.values():
        if c.on:
            incoming.setdefault(c.dst, []).append(c)
    memo = {}

    def expr(v, depth=0):
        if v in memo:
            return memo[v]
        n = g.nodes[v]
        if n.kind == "in":
            return names[v]
        parts = [f"{c.w:+.2f}*{expr(c.src, depth + 1)}" for c in incoming.get(v, [])]
        if not parts:
            inner = "0"
        elif n.agg == "sum":
            inner = " ".join(parts)
        else:
            inner = f"{n.agg}(" + ", ".join(parts) + ")"
        if abs(n.bias) > 0.01:
            inner += f" {n.bias:+.2f}"
        s = inner if n.act == "id" else f"{n.act}({inner})"
        memo[v] = s
        return s
    out = [n.id for n in g.nodes.values() if n.kind == "out"][0]
    return expr(out)


# ----------------------------------------------------------------------------------------- evolution


@dataclass
class Config:
    pop: int = 200
    gens: int = 60
    init_links: int = 2
    p_add_conn: float = 0.25
    p_add_node: float = 0.08
    p_toggle: float = 0.03
    p_act: float = 0.08
    p_weight: float = 0.8
    w_sigma: float = 0.4
    w_replace: float = 0.1
    p_crossover: float = 0.6
    c_excess: float = 1.0
    c_weight: float = 0.4
    target_species: int = 10
    compat: float = 2.0
    stagnation: int = 15
    elitism: int = 1
    survival: float = 0.3
    max_conns: int = 40
    out_act: str = "tanh"


def safe_fitness(fitness_fn, g) -> float:
    try:
        v = float(fitness_fn(g))
    except (ValueError, FloatingPointError):
        return -10.0
    return v if np.isfinite(v) else -10.0


class Neat:
    """Population, speciation and reproduction. ``fitness_fn(genome) -> float`` is supplied by the caller."""

    def __init__(self, n_inputs: int, cfg: Config, seed: int = 0):
        self.n_in, self.cfg = n_inputs, cfg
        self.rng = np.random.default_rng(seed)
        self.out_id = n_inputs
        self.inn = Innovations(start_node=n_inputs + 1)
        self.species = {}       # sid -> dict(rep=Genome, members=[...], best=float, since=int)
        self.next_sid = 0
        self.evaluated = 0      # every genome ever scored (for the multiple-testing count)
        self.history = []
        self.map_fn = None      # optional parallel map: map_fn(fitness_fn, genomes) -> list of floats
        self.pop = [self._new() for _ in range(cfg.pop)]

    # ---- genome construction / mutation
    def _base(self) -> Genome:
        g = Genome()
        for i in range(self.n_in):
            g.nodes[i] = Node(i, "in")
        g.nodes[self.out_id] = Node(self.out_id, "out", self.cfg.out_act, "sum", 0.0)
        return g

    def _new(self) -> Genome:
        g = self._base()
        for i in self.rng.choice(self.n_in, size=self.cfg.init_links, replace=False):
            k = self.inn.conn_id(int(i), self.out_id)
            g.conns[k] = Conn(k, int(i), self.out_id, float(self.rng.normal(0, 1)))
        return g

    def _creates_cycle(self, g, src, dst):
        if src == dst:
            return True
        adj = {}
        for c in g.conns.values():
            adj.setdefault(c.src, []).append(c.dst)
        stack, seen = [dst], set()
        while stack:
            v = stack.pop()
            if v == src:
                return True
            for w in adj.get(v, []):
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        return False

    def mutate(self, g: Genome) -> Genome:
        r, c = self.rng, self.cfg
        for cn in g.conns.values():
            if r.random() < c.p_weight:
                if r.random() < c.w_replace:
                    cn.w = float(r.normal(0, 1))
                else:
                    cn.w = float(np.clip(cn.w + r.normal(0, c.w_sigma), -5, 5))
        for n in g.nodes.values():
            if n.kind != "in" and r.random() < 0.3:
                n.bias = float(np.clip(n.bias + r.normal(0, 0.2), -3, 3))
        if r.random() < c.p_add_conn and len(g.conns) < c.max_conns:
            srcs = [n.id for n in g.nodes.values() if n.kind != "out"]
            dsts = [n.id for n in g.nodes.values() if n.kind != "in"]
            for _ in range(20):
                s, d = int(r.choice(srcs)), int(r.choice(dsts))
                k = self.inn.conn_id(s, d)
                if k in g.conns or self._creates_cycle(g, s, d):
                    continue
                g.conns[k] = Conn(k, s, d, float(r.normal(0, 1)))
                break
        if r.random() < c.p_add_node and g.conns:
            on = [cn for cn in g.conns.values() if cn.on]
            if on:
                cn = on[int(r.integers(len(on)))]
                nid = self.inn.split_node(cn.innov)
                if nid not in g.nodes:
                    cn.on = False
                    g.nodes[nid] = Node(nid, "hid", str(r.choice(ACT_NAMES)), str(r.choice(AGGS, p=[.55, .2, .125, .125])))
                    k1, k2 = self.inn.conn_id(cn.src, nid), self.inn.conn_id(nid, cn.dst)
                    g.conns[k1] = Conn(k1, cn.src, nid, 1.0)
                    g.conns[k2] = Conn(k2, nid, cn.dst, cn.w)
        if r.random() < c.p_toggle and g.conns:
            cn = list(g.conns.values())[int(r.integers(len(g.conns)))]
            if cn.on or not self._creates_cycle(g, cn.src, cn.dst):
                cn.on = not cn.on
        for n in g.nodes.values():
            if n.kind == "hid" and r.random() < c.p_act:
                if r.random() < 0.7:
                    n.act = str(r.choice(ACT_NAMES))
                else:
                    n.agg = str(r.choice(AGGS))
        return g

    def crossover(self, a: Genome, b: Genome) -> Genome:
        if b.fitness > a.fitness:
            a, b = b, a
        child = self._base()
        for k, ca in a.conns.items():
            src = b.conns[k] if (k in b.conns and self.rng.random() < 0.5) else ca
            child.conns[k] = Conn(**vars(src))
            if not ca.on or (k in b.conns and not b.conns[k].on):
                child.conns[k].on = self.rng.random() > 0.75
        for nid, n in a.nodes.items():
            if n.kind != "in":
                pick = b.nodes[nid] if (nid in b.nodes and self.rng.random() < 0.5) else n
                child.nodes[nid] = Node(**vars(pick))
        try:
            topo_order(child)
        except ValueError:
            return a.copy()
        return child

    def distance(self, a: Genome, b: Genome) -> float:
        ka, kb = set(a.conns), set(b.conns)
        common = ka & kb
        n = max(len(ka), len(kb), 1)
        disjoint = len(ka ^ kb)
        wd = np.mean([abs(a.conns[k].w - b.conns[k].w) for k in common]) if common else 0.0
        act_diff = sum(1 for k in set(a.nodes) & set(b.nodes)
                       if a.nodes[k].kind == "hid" and a.nodes[k].act != b.nodes[k].act)
        return self.cfg.c_excess * disjoint / n + self.cfg.c_weight * wd + 0.3 * act_diff

    # ---- speciation and generation loop
    def speciate(self):
        for s in self.species.values():
            s["members"] = []
        for g in self.pop:
            for sid, s in self.species.items():
                if self.distance(g, s["rep"]) < self.cfg.compat:
                    s["members"].append(g)
                    g.species = sid
                    break
            else:
                sid = self.next_sid
                self.next_sid += 1
                self.species[sid] = dict(rep=g, members=[g], best=-math.inf, since=0)
                g.species = sid
        self.species = {k: v for k, v in self.species.items() if v["members"]}
        n = len(self.species)
        self.cfg.compat *= 1.05 if n > self.cfg.target_species else (0.95 if n < self.cfg.target_species else 1.0)
        self.cfg.compat = float(np.clip(self.cfg.compat, 0.3, 10))

    def _score(self, fitness_fn, genomes):
        todo = [g for g in genomes if g.fitness == -math.inf]
        if not todo:
            return
        if self.map_fn is not None:
            vals = list(self.map_fn(fitness_fn, todo))
        else:
            vals = [safe_fitness(fitness_fn, g) for g in todo]
        for g, v in zip(todo, vals):
            g.fitness = v
        self.evaluated += len(todo)

    def step(self, fitness_fn, gen: int):
        self._score(fitness_fn, self.pop)
        self.speciate()
        best = max(self.pop, key=lambda g: g.fitness)
        self.history.append(dict(gen=gen, best=best.fitness, mean=float(np.mean([g.fitness for g in self.pop])),
                                 species=len(self.species), conns=best.n_active,
                                 hidden=sum(n.kind == "hid" for n in best.nodes.values())))
        # stagnation
        for sid, s in list(self.species.items()):
            top = max(m.fitness for m in s["members"])
            if top > s["best"] + 1e-6:
                s["best"], s["since"] = top, 0
            else:
                s["since"] += 1
        alive = {k: v for k, v in self.species.items() if v["since"] < self.cfg.stagnation}
        if not alive:
            alive = {best.species: self.species[best.species]}
        if best.species not in alive:
            alive[best.species] = self.species[best.species]
        lo = min(g.fitness for g in self.pop)
        share = {}
        for sid, s in alive.items():
            share[sid] = np.mean([(m.fitness - lo + 1e-3) for m in s["members"]])
        tot = sum(share.values())
        quota = {sid: max(1, int(round(self.cfg.pop * share[sid] / tot))) for sid in alive}
        new = []
        for sid, s in alive.items():
            mem = sorted(s["members"], key=lambda g: g.fitness, reverse=True)
            for e in mem[:self.cfg.elitism]:
                c = e.copy()
                c.fitness = e.fitness
                new.append(c)
            keep = mem[:max(1, int(math.ceil(len(mem) * self.cfg.survival)))]
            for _ in range(quota[sid] - self.cfg.elitism):
                a = keep[int(self.rng.integers(len(keep)))]
                if len(keep) > 1 and self.rng.random() < self.cfg.p_crossover:
                    b = keep[int(self.rng.integers(len(keep)))]
                    child = self.crossover(a, b)
                else:
                    child = a.copy()
                new.append(self.mutate(child))
            s["rep"] = mem[0]
        self.species = alive
        while len(new) < self.cfg.pop:
            new.append(self.mutate(best.copy()))
        self.pop = new[: self.cfg.pop]
        return best

    def run(self, fitness_fn, callback=None):
        for gen in range(self.cfg.gens):
            best = self.step(fitness_fn, gen)
            if callback:
                callback(gen, best, self)
        self._score(fitness_fn, self.pop)
        return max(self.pop, key=lambda g: g.fitness)
