"""News intelligence: finance-specific sentiment, BM25 relevance, de-duplication.

General-purpose sentiment lexicons misread finance text ("liability",
"tax", "cost" are not negative; "beat", "raises guidance" are positive). This
uses a compact finance lexicon inspired by Loughran & McDonald (2011) with
negation handling and multi-word phrases, plus BM25 (Robertson & Zaragoza)
for query relevance instead of pairwise TF-IDF on two documents.
"""

from __future__ import annotations

import html
import math
import re
from collections import Counter
from datetime import datetime, timezone

POSITIVE_PHRASES = {
    "beats estimates": 2.0, "beat estimates": 2.0, "tops estimates": 2.0, "raises guidance": 2.5,
    "raised guidance": 2.5, "raises outlook": 2.0, "record revenue": 2.0, "record profit": 2.0,
    "all-time high": 1.5, "record high": 1.5, "price target raised": 1.5, "upgraded to buy": 2.0,
    "share buyback": 1.2, "stock buyback": 1.2, "dividend increase": 1.5, "raises dividend": 1.5,
    "strong demand": 1.5, "better than expected": 2.0, "better-than-expected": 2.0, "fda approval": 2.0,
    "wins contract": 1.5, "market share gains": 1.2,
}
NEGATIVE_PHRASES = {
    "misses estimates": -2.0, "missed estimates": -2.0, "cuts guidance": -2.5, "lowers guidance": -2.5,
    "cut guidance": -2.5, "profit warning": -2.5, "worse than expected": -2.0, "worse-than-expected": -2.0,
    "price target cut": -1.5, "downgraded to sell": -2.0, "going concern": -3.0, "chapter 11": -3.0,
    "sec investigation": -2.0, "class action": -1.5, "data breach": -1.5, "layoffs": -1.0,
    "job cuts": -1.0, "dividend cut": -2.0, "suspends dividend": -2.0, "recall": -1.2,
    "short seller": -1.5, "accounting irregularities": -3.0, "all-time low": -1.5,
}
POSITIVE = {
    "beat", "beats", "surge", "surges", "soar", "soars", "jump", "jumps", "rally", "rallies", "gain",
    "gains", "upgrade", "upgrades", "upgraded", "outperform", "outperforms", "bullish", "growth",
    "profit", "profitable", "record", "strong", "strength", "robust", "expand", "expands", "expansion",
    "accelerate", "accelerates", "boost", "boosts", "optimistic", "exceed", "exceeds", "exceeded",
    "breakthrough", "rebound", "rebounds", "recover", "recovers", "recovery", "win", "wins", "approval",
    "approved", "momentum", "tailwind", "tailwinds", "innovative", "partnership", "overweight", "buy",
    "higher", "rise", "rises", "rising", "climb", "climbs", "improve", "improves", "improved", "resilient",
}
NEGATIVE = {
    "miss", "misses", "missed", "plunge", "plunges", "tumble", "tumbles", "slump", "slumps", "sink",
    "sinks", "drop", "drops", "fall", "falls", "decline", "declines", "downgrade", "downgrades",
    "downgraded", "underperform", "bearish", "loss", "losses", "weak", "weakness", "slowdown", "cut",
    "cuts", "lawsuit", "sued", "probe", "investigation", "fraud", "default", "bankruptcy", "warn",
    "warns", "warning", "headwind", "headwinds", "concern", "concerns", "risk", "risks", "volatile",
    "selloff", "sell-off", "crash", "fears", "fear", "recession", "layoff", "downturn", "disappoint",
    "disappoints", "disappointing", "underweight", "sell", "lower", "slash", "slashes", "halt", "halts",
    "delay", "delays", "shortfall", "impairment", "writedown", "write-down", "tariff", "tariffs",
}
NEGATIONS = {"not", "no", "never", "without", "fails", "failed", "despite", "hardly", "isn't", "wasn't", "didn't"}
INTENSIFIERS = {"sharply": 1.5, "significantly": 1.4, "strongly": 1.4, "massive": 1.5, "huge": 1.4, "slightly": 0.6, "modestly": 0.7}
STOPWORDS = set("a an the and or of to in on for with at by from as is are was were be been it its this that "
                "these those his her their our your stock stocks shares share inc corp co ltd says said".split())

_TAG = re.compile(r"<[^>]+>")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9\-']*")


def clean_text(text: str) -> str:
    t = html.unescape(_TAG.sub(" ", text or ""))
    return re.sub(r"\s+", " ", t.replace("<![CDATA[", "").replace("]]>", "")).strip()


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def score_text(text: str) -> float:
    """Sentiment in [-1, 1]."""
    t = clean_text(text).lower()
    total, hits = 0.0, 0
    for phrase, w in {**POSITIVE_PHRASES, **NEGATIVE_PHRASES}.items():
        if phrase in t:
            total += w
            hits += 1
            t = t.replace(phrase, " ")
    toks = tokenize(t)
    for i, tok in enumerate(toks):
        pol = 1.0 if tok in POSITIVE else -1.0 if tok in NEGATIVE else 0.0
        if not pol:
            continue
        window = toks[max(0, i - 3): i]
        if any(w in NEGATIONS for w in window):
            pol = -pol * 0.8
        for w in window:
            pol *= INTENSIFIERS.get(w, 1.0)
        total += pol
        hits += 1
    if not hits:
        return 0.0
    return float(math.tanh(total / math.sqrt(hits + 1)))


def label(score: float) -> str:
    if score > 0.25:
        return "Positive"
    if score < -0.25:
        return "Negative"
    return "Neutral"


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [[t for t in tokenize(d) if t not in STOPWORDS] for d in docs]
        self.avgdl = sum(map(len, self.docs)) / max(1, len(self.docs))
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def scores(self, query: str) -> list[float]:
        q = [t for t in tokenize(query) if t not in STOPWORDS]
        out = []
        for tf, d in zip(self.tf, self.docs):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf.get(t, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / max(self.avgdl, 1)))
            out.append(s)
        return out


def _shingles(text: str, k: int = 3) -> set:
    toks = [t for t in tokenize(text) if t not in STOPWORDS]
    return {" ".join(toks[i:i + k]) for i in range(max(1, len(toks) - k + 1))}


def dedupe(articles: list[dict], threshold: float = 0.6) -> list[dict]:
    """Drop near-duplicate headlines (Jaccard similarity of word 3-grams)."""
    kept, sigs = [], []
    for a in articles:
        sh = _shingles(a.get("title", ""))
        if any(len(sh & s) / max(1, len(sh | s)) >= threshold for s in sigs):
            continue
        kept.append(a)
        sigs.append(sh)
    return kept


def hours_old(published: datetime | None, now: datetime | None = None) -> float:
    if published is None:
        return 48.0
    now = now or datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return max(0.0, (now - published).total_seconds() / 3600)


def rank_articles(articles: list[dict], query: str | None = None, half_life_h: float = 36.0) -> list[dict]:
    """Attach sentiment + relevance and sort by relevance x recency."""
    articles = dedupe(articles)
    texts = [f"{a.get('title', '')} {a.get('title', '')} {clean_text(a.get('summary', ''))}" for a in articles]
    rel = BM25(texts).scores(query) if query and articles else [1.0] * len(articles)
    mx = max(rel) if rel and max(rel) > 0 else 1.0
    for a, r in zip(articles, rel):
        a["sentiment"] = score_text(f"{a.get('title', '')}. {a.get('summary', '')}")
        a["sentiment_label"] = label(a["sentiment"])
        a["relevance"] = r / mx
        decay = 0.5 ** (hours_old(a.get("published")) / half_life_h)
        a["rank_score"] = (0.35 + 0.65 * a["relevance"]) * (0.4 + 0.6 * decay)
    return sorted(articles, key=lambda a: a["rank_score"], reverse=True)


def aggregate_sentiment(articles: list[dict], half_life_h: float = 48.0) -> dict:
    """Recency- and relevance-weighted news sentiment index in [-1, 1]."""
    if not articles:
        return {"score": 0.0, "label": "Neutral", "n": 0, "positive": 0, "negative": 0, "neutral": 0}
    num = den = 0.0
    for a in articles:
        w = (0.5 ** (hours_old(a.get("published")) / half_life_h)) * (0.3 + a.get("relevance", 1.0))
        num += w * a.get("sentiment", 0.0)
        den += w
    s = num / den if den else 0.0
    c = Counter(a.get("sentiment_label", "Neutral") for a in articles)
    return {"score": s, "label": label(s), "n": len(articles), "positive": c["Positive"],
            "negative": c["Negative"], "neutral": c["Neutral"]}
