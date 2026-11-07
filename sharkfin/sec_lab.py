"""Biotech catalysts from SEC filings: trial readouts, FDA decision (PDUFA) dates and stock offerings.

Data: EDGAR full-text search over 8-K press releases (2012 on), each company's filing list (424B4/424B5 offerings,
S-3 shelves), Yahoo prices and share counts. Returns are vs XBI (the biotech ETF) after 10 bps a side.

No look-ahead:
- A PDUFA date counts only once a filing has announced it, and trades start the session after that filing.
- A readout is dated by its 8-K; the reaction runs from the close before the filing to the close one session after,
  and any later holding starts at the next open.
- Market cap uses the share count reported on or before the entry day.

Survivorship: Yahoo has no prices for many delisted biotechs, which are mostly failures. So holding returns here
look better than they were.

SEC asks automated clients to name a contact in the User-Agent. Set SEC_USER_AGENT, e.g. "SharkFin you@example.com".
"""

from __future__ import annotations

import os
import pickle
import re
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd

from sharkfin.catalyst_lab import GRADE, OUT

COST = 0.001                     # per side
SIZES = [0, 3e8, 2e9, 1e10, 1e15]
SIZE_LABELS = ["Micro (<$300M)", "Small ($300M-2B)", "Mid ($2-10B)", "Large (>$10B)"]
OFFER_FORMS = ("424B4", "424B5")
SHELF_FORMS = ("S-3", "S-3ASR")
POP = 0.30                       # a 3-day jump of 30%+ vs XBI

_MON = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
_DATE = re.compile(_MON + r"\s+\d{1,2},?\s+\d{4}")
_NOT_A_READOUT = re.compile(r"quarter|financial results|full[- ]year|business update|annual|expected|expects|"
                            r"to present|will present|letter to")
_POS = re.compile(r"positive|met (?:the |its |all |both )?(?:primary|co-primary)|achiev|statistically significant|"
                  r"significant(?:ly)? (?:improv|reduc)|success")
_NEG = re.compile(r"did not|does not|fail|not meet|not achiev|discontinu|miss|not statistically|halt|terminat")


# ---------------------------------------------------------------- fetching

def user_agent() -> dict:
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        raise RuntimeError("Set SEC_USER_AGENT to a name and contact email; SEC refuses anonymous clients.")
    return {"User-Agent": ua}


class _Client:
    """Stays under SEC's 10 requests a second across threads."""

    def __init__(self, gap=0.12):
        import requests
        self.s = requests.Session()
        self.s.headers.update(user_agent())
        self.gap, self.last, self.lock = gap, 0.0, threading.Lock()

    def get(self, url, **kw):
        for a in range(4):
            with self.lock:
                wait = self.gap - (time.time() - self.last)
                if wait > 0:
                    time.sleep(wait)
                self.last = time.time()
            try:
                r = self.s.get(url, timeout=30, **kw)
                if r.status_code == 200:
                    return r
                if r.status_code == 404:
                    return None
            except Exception:
                pass
            time.sleep(2 * (a + 1))
        return None


def full_text(client, q, forms="8-K", years=range(2012, 2027)):
    """Every EDGAR full-text hit for q, one year at a time to stay under the 10,000-hit cap."""
    out = {}
    for y in years:
        frm = 0
        while True:
            r = client.get("https://efts.sec.gov/LATEST/search-index",
                           params={"q": q, "forms": forms, "dateRange": "custom", "startdt": f"{y}-01-01",
                                   "enddt": f"{y}-12-31", "from": frm})
            if r is None:
                break
            d = r.json()
            hits = d["hits"]["hits"]
            if not hits:
                break
            for h in hits:
                s = h["_source"]
                out.setdefault(h["_id"], dict(id=h["_id"], adsh=s.get("adsh"), ciks=s.get("ciks"),
                                              names=s.get("display_names"), date=s.get("file_date"),
                                              ftype=s.get("file_type")))
            frm += len(hits)
            if frm >= min(d["hits"]["total"]["value"], 10000):
                break
    return list(out.values())


def clean_text(html: str) -> str:
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    t = re.sub(r"<[^>]+>", " ", t)
    for a, b in (("&nbsp;", " "), ("&#160;", " "), ("&amp;", "&"), ("&#8217;", "'"), ("&rsquo;", "'")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


# ---------------------------------------------------------------- parsing

def pdufa_dates(text: str, filed) -> list[pd.Timestamp]:
    """Dates written near 'PDUFA' that fall 1 week to 18 months after the filing (so it is a future decision date)."""
    near = [d for m in re.finditer("PDUFA", text) for d in _DATE.findall(text[max(0, m.start() - 250):m.end() + 250])]
    return future_dates(near, filed)


def future_dates(strings, filed) -> list[pd.Timestamp]:
    filed = pd.Timestamp(filed)
    out = set()
    for d in strings:
        ts = pd.to_datetime(d.replace(",", ""), format="%B %d %Y", errors="coerce")
        if pd.notna(ts) and filed + pd.Timedelta(days=7) < ts < filed + pd.Timedelta(days=550):
            out.add(ts)
    return sorted(out)


def pdufa_events(mentions: pd.DataFrame) -> pd.DataFrame:
    """mentions: cik, filed, pdufa (one row per date a filing names). Dates within 5 days are one decision. A date
    is 'extended' when the company later names a new one 75-100 days after it (FDA's 3-month extension) before
    it arrives."""
    m = mentions.drop_duplicates().sort_values(["cik", "pdufa"])
    m = m.assign(grp=(m.groupby("cik").pdufa.diff().dt.days.fillna(999) > 5).cumsum())
    ev = m.groupby("grp").agg(cik=("cik", "first"), pdufa=("pdufa", "max"), announced=("filed", "min"),
                              mentions=("filed", "size")).reset_index(drop=True)
    ext = []
    for _, r in ev.iterrows():
        g = ev[ev.cik == r.cik]
        gap = (g.pdufa - r.pdufa).dt.days
        ext.append(bool(((gap >= 75) & (gap <= 100) & (g.announced > r.announced) & (g.announced < r.pdufa)).any()))
    return ev.assign(extended=ext)


def headline_class(head: str) -> str | None:
    """'positive' / 'negative' / 'mixed' for a readout press release, None when the headline is not a readout."""
    h = head[:380].lower()
    if not (re.search(r"announc|report", h) and re.search(r"top[- ]?line|results|data", h)):
        return None
    if _NOT_A_READOUT.search(h):
        return None
    p, n = bool(_POS.search(h)), bool(_NEG.search(h))
    return "positive" if p and not n else "negative" if n and not p else "mixed"


# ---------------------------------------------------------------- studies

class Prices:
    def __init__(self, close, open_, shares):
        close = close[close["XBI"].notna()]
        self.c, self.o, self.idx = close, open_.reindex(close.index), close.index
        self.sh = shares

    def excess(self, s, a, b, at_open=False):
        """Return of s vs XBI from bar a (close, or open when at_open) to the close of bar b, after costs."""
        if not (0 <= a < b < len(self.idx)):
            return np.nan
        p = self.o if at_open else self.c
        x0, x1, b0, b1 = p[s].iloc[a], self.c[s].iloc[b], p["XBI"].iloc[a], self.c["XBI"].iloc[b]
        if not (np.isfinite(x0) and np.isfinite(x1) and x0 > 0):
            return np.nan
        return (x1 / x0 - 1) - (b1 / b0 - 1) - 2 * COST

    def mcap(self, s, i):
        shs = self.sh.get(s)
        if shs is None or not len(shs) or i < 0:
            return np.nan
        x = shs.copy()
        x.index = pd.to_datetime(x.index)
        if x.index.tz is not None:
            x.index = x.index.tz_localize(None)
        x = x[x.index <= self.idx[i]]
        return float(x.iloc[-1]) * self.c[s].iloc[i] if len(x) else np.nan


def size_of(mcap: pd.Series) -> pd.Series:
    return pd.cut(mcap, SIZES, labels=SIZE_LABELS)


def pdufa_study(ev: pd.DataFrame, px: Prices, ticker: dict) -> pd.DataFrame:
    rows = []
    for _, e in ev[~ev.extended].iterrows():
        s = ticker.get(e.cik)
        if s not in px.c:
            continue
        d = px.idx.searchsorted(e.pdufa)                                   # first session on or after the date
        a = px.idx.searchsorted(e.announced + pd.Timedelta(days=1))        # first session after the filing
        if d + 3 >= len(px.idx) or d < 60 or a >= d - 1:
            continue
        e20 = max(a, d - 20)
        rows.append(dict(ticker=s, pdufa=e.pdufa, announced=e.announced, mcap=px.mcap(s, e20 - 1),
                         from_announce=px.excess(s, a, d - 1, at_open=True),
                         last20=px.excess(s, e20, d - 1, at_open=True),
                         decision=px.excess(s, d - 1, d + 2) + 2 * COST,
                         hold_through=px.excess(s, e20, d + 2, at_open=True)))
    return pd.DataFrame(rows)


def readout_study(heads: list[dict], px: Prices, ticker: dict, offers: dict) -> pd.DataFrame:
    """heads: dicts with cik, date, phase, head (press-release text)."""
    rows = []
    for r in heads:
        cls = headline_class(r["head"])
        s = ticker.get(r["cik"])
        if cls is None or s not in px.c:
            continue
        i = px.idx.searchsorted(pd.Timestamp(r["date"]))
        if i < 45 or i + 3 >= len(px.idx):
            continue
        o = offers.get(r["cik"], pd.Series(dtype="datetime64[ns]"))
        nxt = o[o >= pd.Timestamp(r["date"])]
        days_to_offer = px.idx.searchsorted(nxt.iloc[0]) - i if len(nxt) else 10**6
        rows.append(dict(ticker=s, date=px.idx[i], phase=r["phase"], result=cls, mcap=px.mcap(s, i - 1),
                         before40=px.excess(s, i - 41, i - 1), reaction=px.excess(s, i - 1, i + 1) + 2 * COST,
                         after3m=px.excess(s, i + 2, i + 64, at_open=True), offer_10d=days_to_offer <= 10))
    return pd.DataFrame(rows).drop_duplicates(["ticker", "date"])


def pop_study(px: Prices, ticker: dict, offers: dict, shelves: dict) -> pd.DataFrame:
    """Every 3-day jump of 30%+ vs XBI (one per 20 sessions per stock): did an offering follow, and what came next."""
    rows = []
    xb = px.c["XBI"]
    for cik, s in ticker.items():
        if s not in px.c or px.c[s].notna().sum() < 300:
            continue
        cs = px.c[s]
        r3 = (cs / cs.shift(3) - 1) - (xb / xb.shift(3) - 1)
        last = -99
        for d in r3.index[r3 > POP]:
            i = px.idx.get_loc(d)
            if i - last < 20 or i < 260 or i + 64 >= len(px.idx):
                continue
            last = i
            o = offers.get(cik, pd.Series(dtype="datetime64[ns]"))
            nxt = o[o > d]
            gap = px.idx.searchsorted(nxt.iloc[0]) - i if len(nxt) else 10**6
            sh = shelves.get(cik, pd.Series(dtype="datetime64[ns]"))
            rows.append(dict(ticker=s, date=d, mcap=px.mcap(s, i - 3), shelf=bool(((sh <= d) & (sh > d - pd.Timedelta(days=1095))).any()),
                             offer_10d=gap <= 10, offer_60d=gap <= 60, after3m=px.excess(s, i + 1, i + 64, at_open=True)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- tables

def _era(d):
    return np.where(pd.to_datetime(d) < GRADE[0], "2012-21", "2021-26")


def _summ(x, col):
    v = x[col].dropna()
    return len(v), v.median(), (v > 0).mean()


def pdufa_table(st: pd.DataFrame) -> pd.DataFrame:
    st = st.assign(Size=size_of(st.mcap)).dropna(subset=["Size"])
    out = []
    for size, g in st.groupby("Size", observed=True):
        row = {"Size": size, "Decisions": len(g)}
        for col, lab in (("from_announce", "Buy when date announced, sell day before"),
                         ("last20", "Buy 20 days before, sell day before"),
                         ("decision", "Decision (3 days)"),
                         ("hold_through", "Buy 20 days before, hold through")):
            _, med, win = _summ(g, col)
            row[f"{lab}: median"] = med
            row[f"{lab}: % up"] = win
        out.append(row)
    return pd.DataFrame(out)


def readout_table(st: pd.DataFrame) -> pd.DataFrame:
    st = st.assign(Size=size_of(st.mcap)).dropna(subset=["Size"])
    st = st[st.Size != SIZE_LABELS[3]]
    out = []
    for (res, size), g in st.groupby(["result", "Size"], observed=True):
        out.append({"Headline": res, "Size": size, "Readouts": len(g),
                    "40 days before: median": g.before40.median(),
                    "Reaction: median": g.reaction.median(), "Reaction: % up": (g.reaction.dropna() > 0).mean(),
                    "Next 3 months: median": g.after3m.median(), "Next 3 months: % up": (g.after3m.dropna() > 0).mean(),
                    "Stock offering within 10 days": g.offer_10d.mean()})
    return pd.DataFrame(out)


def dilution_table(pops: pd.DataFrame) -> pd.DataFrame:
    p = pops.assign(Size=size_of(pops.mcap)).dropna(subset=["Size"])
    out = []
    for (size, shelf), g in p.groupby(["Size", "shelf"], observed=True):
        out.append({"Size": size, "Shelf (S-3) on file": "Yes" if shelf else "No", "Jumps": len(g),
                    "Offering within 10 days": g.offer_10d.mean(), "Offering within 60 days": g.offer_60d.mean(),
                    "Next 3 months: median": g.after3m.median(), "Next 3 months: % up": (g.after3m.dropna() > 0).mean()})
    return pd.DataFrame(out)


def main(folder: str):
    """Build the tables from a folder of cached pulls (see the module docstring for what each holds)."""
    f = Path(folder)
    load = lambda n: pickle.load(open(f / n, "rb"))  # noqa: E731 - our own cache files, never downloaded pickles
    docs, P, S = load("docs.pkl"), load("px.pkl"), load("subs.pkl")["subs"]
    px = Prices(P["px"]["Close"], P["px"]["Open"], P["sh"])
    tick = P["tick"]
    offers = {c: pd.to_datetime(v["filings"].query("form in @OFFER_FORMS").date).sort_values() for c, v in S.items()}
    shelves = {c: pd.to_datetime(v["filings"].query("form in @SHELF_FORMS").date).sort_values() for c, v in S.items()}
    # each cached record holds the dates found near "PDUFA" in that filing (see pdufa_dates)
    mentions = pd.DataFrame([(int(r["ciks"][0]), pd.Timestamp(r["date"]), d) for r in docs["pdufa"]
                             for d in future_dates(r.get("pdufa_dates") or [], r["date"])],
                            columns=["cik", "filed", "pdufa"])
    ev = pdufa_events(mentions)
    heads, seen = [], set()
    for ph, lab in (("p3", "Phase 3"), ("p2", "Phase 2")):
        for r in docs[ph]:
            if r.get("ok") and r["adsh"] not in seen:
                seen.add(r["adsh"])
                heads.append(dict(cik=int(r["ciks"][0]), date=r["date"], phase=lab, head=r["head"]))
    OUT.mkdir(parents=True, exist_ok=True)
    pdufa_table(pdufa_study(ev, px, tick)).round(4).to_csv(OUT / "sec_pdufa.csv", index=False)
    readout_table(readout_study(heads, px, tick, offers)).round(4).to_csv(OUT / "sec_readouts.csv", index=False)
    dilution_table(pop_study(px, tick, offers, shelves)).round(4).to_csv(OUT / "sec_dilution.csv", index=False)


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
