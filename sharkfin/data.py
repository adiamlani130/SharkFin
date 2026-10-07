"""Market-data access layer (Yahoo Finance via yfinance, plus RSS news).

All network calls go through here, are wrapped in a small thread-safe TTL cache
(shared across Streamlit sessions in the same server process) and fail soft:
callers get empty frames / NaNs instead of exceptions.
"""

from __future__ import annotations

import copy
import functools
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import numpy as np
import pandas as pd

from .valuation import Financials

log = logging.getLogger("sharkfin.data")

# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

_cache: dict = {}
_lock = threading.Lock()


def ttl_cache(seconds: int):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__qualname__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            with _lock:
                hit = _cache.get(key)
            if hit and now - hit[0] < seconds:
                return _copy(hit[1])
            val = fn(*args, **kwargs)
            if not _is_empty(val):
                with _lock:
                    _cache[key] = (now, val)
            return val

        wrapper.cache_clear = lambda: _cache.clear()
        return wrapper

    return deco


def _copy(v):
    if isinstance(v, (pd.DataFrame, pd.Series)):
        return v.copy()
    if isinstance(v, (dict, list)):
        return copy.copy(v)
    return v


def _is_empty(v) -> bool:
    if v is None:
        return True
    if isinstance(v, (pd.DataFrame, pd.Series)):
        return v.empty
    if isinstance(v, (dict, list, tuple)):
        return len(v) == 0
    if isinstance(v, float):
        return not np.isfinite(v)
    return False


def _yf():
    import yfinance as yf

    return yf


def _naive(idx: pd.Index) -> pd.Index:
    if isinstance(idx, pd.DatetimeIndex) and idx.tz is not None:
        return idx.tz_convert("America/New_York").tz_localize(None)
    return idx


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------


@ttl_cache(900)
def history(symbol: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
    try:
        df = _yf().Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
    except Exception as e:  # pragma: no cover - network
        log.warning("history(%s) failed: %s", symbol, e)
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    df.index = _naive(df.index)
    return df[[c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]].dropna(subset=["Close"])


@ttl_cache(1800)
def download_prices(symbols: tuple, period: str = "2y", field: str = "Close", chunk: int = 150) -> pd.DataFrame:
    """Batched adjusted-close download: one request per ``chunk`` tickers
    instead of one per ticker."""
    frames = []
    syms = list(dict.fromkeys(symbols))

    def fetch(part: list, threads: bool) -> pd.DataFrame:
        try:
            raw = _yf().download(part, period=period, auto_adjust=True, progress=False, threads=threads, group_by="column")
        except Exception as e:  # pragma: no cover - network
            log.warning("download chunk failed: %s", e)
            return pd.DataFrame()
        if raw is None or raw.empty:
            return pd.DataFrame()
        if isinstance(raw.columns, pd.MultiIndex):
            return raw[field] if field in raw.columns.get_level_values(0) else pd.DataFrame()
        return raw[[field]].rename(columns={field: part[0]})

    for i in range(0, len(syms), chunk):
        part = syms[i:i + chunk]
        sub = fetch(part, threads=True)
        # yfinance's threaded download sometimes drops tickers on transient
        # errors (e.g. its SQLite timezone cache reports "database is locked");
        # retry those once, single-threaded.
        missing = [s for s in part if s not in sub.columns or sub[s].isna().all()]
        if missing:
            retry = fetch(missing, threads=False)
            if not retry.empty:
                sub = pd.concat([sub.drop(columns=[c for c in retry.columns if c in sub.columns]), retry], axis=1)
        if not sub.empty:
            frames.append(sub)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, axis=1)
    out.index = _naive(out.index)
    return out.loc[:, ~out.columns.duplicated()].dropna(how="all")


@ttl_cache(1800)
def download_ohlcv(symbols: tuple, period: str = "2y", chunk: int = 150) -> dict:
    """Batched OHLCV download: {"Open"|"High"|"Low"|"Close"|"Volume": DataFrame (dates x tickers)}."""
    fields = ("Open", "High", "Low", "Close", "Volume")
    parts: dict = {f: [] for f in fields}
    syms = list(dict.fromkeys(symbols))
    for i in range(0, len(syms), chunk):
        part = syms[i:i + chunk]
        try:
            raw = _yf().download(part, period=period, auto_adjust=True, progress=False, threads=True, group_by="column")
        except Exception as e:  # pragma: no cover - network
            log.warning("OHLCV chunk failed: %s", e)
            continue
        if raw is None or raw.empty:
            continue
        for f in fields:
            if isinstance(raw.columns, pd.MultiIndex):
                if f in raw.columns.get_level_values(0):
                    parts[f].append(raw[f])
            elif f in raw.columns:
                parts[f].append(raw[[f]].rename(columns={f: part[0]}))
    out = {}
    for f, frames in parts.items():
        if frames:
            df = pd.concat(frames, axis=1)
            df.index = _naive(df.index)
            out[f] = df.loc[:, ~df.columns.duplicated()]
    return out


# ---------------------------------------------------------------------------
# Fundamentals
# ---------------------------------------------------------------------------


@ttl_cache(3600)
def info(symbol: str) -> dict:
    d = {}
    # Yahoo rate-limits shared hosts (e.g. Streamlit Cloud) in bursts; one
    # short back-off usually gets the data instead of a page full of dashes.
    for attempt in range(3):
        try:
            d = _yf().Ticker(symbol).info or {}
        except Exception as e:  # pragma: no cover - network
            log.warning("info(%s) failed: %s", symbol, e)
            d = {}
        if len(d) > 5:
            break
        time.sleep(0.8 * (attempt + 1))
    if not d.get("currentPrice") and not d.get("regularMarketPrice"):
        try:
            fi = _yf().Ticker(symbol).fast_info
            d.setdefault("regularMarketPrice", float(fi["last_price"]))
            d.setdefault("marketCap", float(fi.get("market_cap") or np.nan))
            d.setdefault("previousClose", float(fi["previous_close"]))
        except Exception:
            pass
    return d


def price_of(inf: dict) -> float:
    for k in ("currentPrice", "regularMarketPrice", "previousClose"):
        v = inf.get(k)
        if v:
            return float(v)
    return float("nan")


@ttl_cache(6 * 3600)
def financials(symbol: str) -> Financials:
    try:
        t = _yf().Ticker(symbol)
        return Financials(t.income_stmt, t.balance_sheet, t.cashflow)
    except Exception as e:  # pragma: no cover - network
        log.warning("financials(%s) failed: %s", symbol, e)
        return Financials()


@ttl_cache(6 * 3600)
def quarterly_financials(symbol: str) -> Financials:
    try:
        t = _yf().Ticker(symbol)
        return Financials(t.quarterly_income_stmt, t.quarterly_balance_sheet, t.quarterly_cashflow)
    except Exception:  # pragma: no cover - network
        return Financials()


def ttm(series: pd.Series, n: int = 4) -> float:
    s = series.dropna()
    return float(s.iloc[:n].sum()) if len(s) >= n else float("nan")


@ttl_cache(6 * 3600)
def analyst_data(symbol: str) -> dict:
    out = {}
    t = _yf().Ticker(symbol)
    for attr in ("recommendations_summary", "upgrades_downgrades", "earnings_dates", "calendar",
                 "earnings_estimate", "revenue_estimate", "growth_estimates", "eps_trend", "eps_revisions",
                 "analyst_price_targets", "institutional_holders", "insider_transactions"):
        try:
            out[attr] = getattr(t, attr)
        except Exception:
            out[attr] = None
    return out


@ttl_cache(12 * 3600)
def infos(symbols: tuple, workers: int = 6) -> pd.DataFrame:
    """``info`` for many symbols in parallel (used for peers and the scanner)."""
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(info, symbols))
    return pd.DataFrame(rows, index=list(symbols))


# ---------------------------------------------------------------------------
# Rates / macro
# ---------------------------------------------------------------------------


@ttl_cache(3600)
def risk_free_rate() -> float:
    """10-year US Treasury yield (decimal), used as the DCF/CAPM risk-free rate."""
    try:
        h = history("^TNX", period="5d")
        v = float(h["Close"].iloc[-1]) / 100
        if 0 < v < 0.2:
            return v
    except Exception:
        pass
    return 0.042


MARKET_TICKERS = {
    "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow": "^DJI", "Russell 2000": "^RUT", "VIX": "^VIX",
    "10Y Yield": "^TNX", "Dollar": "DX-Y.NYB", "Gold": "GC=F", "Oil (WTI)": "CL=F", "Bitcoin": "BTC-USD",
}
SECTOR_ETFS = {
    "Technology": "XLK", "Financials": "XLF", "Health Care": "XLV", "Consumer Disc.": "XLY",
    "Communication": "XLC", "Industrials": "XLI", "Consumer Staples": "XLP", "Energy": "XLE",
    "Utilities": "XLU", "Real Estate": "XLRE", "Materials": "XLB",
}


# ---------------------------------------------------------------------------
# Universes and search
# ---------------------------------------------------------------------------

FALLBACK_SP500 = (
    "AAPL MSFT NVDA GOOGL GOOG AMZN META AVGO TSLA BRK-B LLY JPM V UNH XOM MA COST HD PG JNJ WMT NFLX ABBV "
    "BAC CRM ORCL CVX MRK KO AMD PEP ADBE TMO LIN ACN MCD CSCO ABT WFC IBM GE DHR PM TXN QCOM INTU CAT NOW "
    "AMGN VZ DIS ISRG AXP NEE GS RTX PFE MS SPGI CMCSA UBER T LOW HON UNP AMAT BKNG PGR ETN SYK BLK TJX "
    "COP VRTX C BSX ELV SCHW PLD REGN ADP MMC LMT MDT PANW CB DE ANET ADI UPS KLAC SBUX FI BX GILD MU LRCX "
    "BMY CI SO MO KKR TMUS ICE SHW DUK ZTS MDLZ CME EQIX CL PYPL SNPS CDNS WM APH MCK CRWD ITW TT PH CMG "
    "USB PNC CVS MSI TDG ORLY EOG GD BDX CTAS NOC AON FDX MAR CSX ECL WELL SLB EMR APD AJG TGT NXPI FCX HCA "
    "PSX MPC CARR ROP NSC OXY COF AFL ADSK TFC PCAR GM SPG DLR HLT MET AZO TRV WMB O PLTR AMP OKE SRE F FTNT "
    "ALL KMB AEP CCI MNST PSA D GWW JCI ROST KMI BK LHX CPRT DHI PAYX FAST PRU MSCI URI HUM KDP NUE STZ IQV "
    "CTVA PWR TEL AME ODFL FIS KVUE PCG HSY GIS YUM CMI LEN MCHP IDXX EW DOW EXC OTIS ACGL VRSK CNC IR SYY "
    "GEHC KR A HPQ CTSH EA XYL ED DD VMC MLM NDAQ HIG DAL BKR ON RMD CSGP LULU WAB GLW EXR MPWR"
).split()
FALLBACK_NDX = (
    "AAPL MSFT NVDA AMZN META AVGO GOOGL GOOG TSLA COST NFLX AMD PEP ADBE LIN CSCO TMUS QCOM INTU TXN AMGN ISRG "
    "AMAT HON BKNG CMCSA VRTX PANW ADP MU LRCX SBUX GILD ADI KLAC MELI MDLZ REGN CRWD CTAS SNPS CDNS PYPL MAR "
    "ABNB ORLY FTNT ASML CEG MRVL WDAY PDD CSX DASH ROP ADSK NXPI CHTR AEP PCAR TTD MNST CPRT KDP PAYX ODFL "
    "FAST ROST AZN KHC DDOG BKR EA VRSK CTSH EXC XEL LULU GEHC IDXX CCEP TEAM FANG CSGP ANSS ON ZS DXCM BIIB "
    "MCHP CDW TTWO GFS WBD ILMN MDB ARM SMCI PLTR APP"
).split()
DOW30 = ("AAPL AMGN AMZN AXP BA CAT CRM CSCO CVX DIS GS HD HON IBM JNJ JPM KO MCD MMM MRK MSFT NKE NVDA PG SHW "
         "TRV UNH V VZ WMT").split()
POPULAR_EXTRA = "PLTR COIN SNOW ABNB UBER RIVN SOFI HOOD RBLX PINS SNAP DOCU ZM SHOP NET ARM SMCI MSTR".split()


@ttl_cache(24 * 3600)
def sp500_table() -> pd.DataFrame:
    """S&P 500 constituents with GICS sector / sub-industry (used for peers)."""
    try:
        import io

        import requests

        html = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                            headers={"User-Agent": "Mozilla/5.0 SharkFin"}, timeout=10).text
        df = pd.read_html(io.StringIO(html))[0]
        df["Symbol"] = df["Symbol"].str.replace(".", "-", regex=False)
        return df.rename(columns={"Security": "Name", "GICS Sector": "Sector", "GICS Sub-Industry": "SubIndustry"})[
            ["Symbol", "Name", "Sector", "SubIndustry"]]
    except Exception:
        return pd.DataFrame({"Symbol": FALLBACK_SP500, "Name": FALLBACK_SP500, "Sector": None, "SubIndustry": None})


@ttl_cache(24 * 3600)
def nasdaq100() -> list:
    try:
        import io

        import requests

        html = requests.get("https://en.wikipedia.org/wiki/Nasdaq-100", headers={"User-Agent": "Mozilla/5.0 SharkFin"},
                            timeout=10).text
        for t in pd.read_html(io.StringIO(html)):
            col = next((c for c in t.columns if str(c).lower() in ("ticker", "symbol")), None)
            if col is not None and len(t) > 90:
                return t[col].astype(str).str.replace(".", "-", regex=False).tolist()
    except Exception:
        pass
    return FALLBACK_NDX


def universe(name: str) -> list:
    if name == "S&P 500":
        return sp500_table()["Symbol"].tolist()
    if name == "Nasdaq-100":
        return nasdaq100()
    if name == "Dow 30":
        return DOW30
    if name == "S&P 500 + Nasdaq-100":
        return sorted(set(universe("S&P 500")) | set(nasdaq100()) | set(POPULAR_EXTRA))
    raise KeyError(name)


def all_symbols() -> list:
    return universe("S&P 500 + Nasdaq-100")


@ttl_cache(3600)
def search(query: str) -> list:
    """Symbol / company-name search. Returns [(symbol, name)]."""
    q = query.strip()
    if not q:
        return []
    out = []
    try:
        res = _yf().Search(q, max_results=10, news_count=0)
        for r in res.quotes:
            if r.get("quoteType") in ("EQUITY", "ETF", "INDEX", "CRYPTOCURRENCY", "MUTUALFUND", None):
                out.append((r["symbol"], r.get("shortname") or r.get("longname") or r["symbol"]))
    except Exception:
        pass
    if not out:
        tab = sp500_table()
        qu = q.upper()
        m = tab[tab["Symbol"].str.startswith(qu) | tab["Name"].astype(str).str.upper().str.contains(qu, regex=False)]
        out = list(zip(m["Symbol"], m["Name"]))[:15]
        extra = [s for s in all_symbols() if s.startswith(qu) and s not in {o[0] for o in out}]
        out += [(s, s) for s in extra[:10]]
    return out


@ttl_cache(24 * 3600)
def industry_members(industry_key: str) -> list:
    """Largest US-listed companies in a Yahoo industry (works for any stock, not just the S&P 500)."""
    try:
        top = _yf().Industry(industry_key).top_companies
    except Exception as e:  # pragma: no cover - network
        log.warning("industry(%s) failed: %s", industry_key, e)
        return []
    if top is None or top.empty:
        return []
    syms = [str(s) for s in top.index if isinstance(s, str) and s.replace("-", "").isalpha()]
    return syms[:25]


def peers_for(symbol: str, inf: dict, max_peers: int = 15) -> list:
    """Same GICS sub-industry (else sector) peers from the S&P 500 table,
    falling back to yfinance sector/industry matching of the large-cap list."""
    tab = sp500_table()
    row = tab[tab["Symbol"] == symbol]
    peers = []
    if not row.empty and pd.notna(row["SubIndustry"].iloc[0]):
        peers = tab[(tab["SubIndustry"] == row["SubIndustry"].iloc[0]) & (tab["Symbol"] != symbol)]["Symbol"].tolist()
        if len(peers) < 5:
            peers += tab[(tab["Sector"] == row["Sector"].iloc[0]) & (tab["Symbol"] != symbol)]["Symbol"].tolist()
    peers = list(dict.fromkeys(peers))
    if len(peers) < 5 and inf.get("industryKey"):
        peers += [s for s in industry_members(inf["industryKey"]) if s != symbol and s not in peers]
    if len(peers) < 5 and inf.get("industry"):
        cand = [s for s in FALLBACK_SP500 if s != symbol][:60]
        df = infos(tuple(cand))
        same = df[df.get("industry") == inf.get("industry")] if "industry" in df else pd.DataFrame()
        if len(same) < 5 and "sector" in df:
            same = df[df["sector"] == inf.get("sector")]
        peers += [s for s in same.index if s not in peers]
    # Prefer peers closest in size.
    if len(peers) > max_peers:
        caps = infos(tuple(peers[:60]))
        mc = pd.to_numeric(caps.get("marketCap"), errors="coerce")
        target = inf.get("marketCap") or mc.median()
        peers = (np.log(mc / target).abs()).sort_values().index[:max_peers].tolist()
    return peers[:max_peers]


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------


def _parse_date(s) -> datetime | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return datetime.fromtimestamp(s, tz=timezone.utc)
    try:
        return parsedate_to_datetime(s)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _rss(url: str, source: str) -> list:
    try:
        import feedparser

        feed = feedparser.parse(url, agent="Mozilla/5.0 SharkFin")
    except Exception:
        return []
    out = []
    for e in feed.entries:
        pub = e.get("published") or e.get("updated")
        src = source
        if hasattr(e, "source") and getattr(e.source, "title", None):
            src = e.source.title
        out.append({"title": e.get("title", ""), "summary": e.get("summary", ""), "link": e.get("link"),
                    "publisher": src, "published": _parse_date(pub)})
    return out


@ttl_cache(900)
def news(query: str, symbol: str | None = None) -> list:
    """News from yfinance (ticker feed), Yahoo RSS and Google News RSS."""
    import urllib.parse

    arts = []
    if symbol:
        try:
            for n in _yf().Ticker(symbol).news or []:
                c = n.get("content", n)
                link = (c.get("canonicalUrl") or {}).get("url") if isinstance(c.get("canonicalUrl"), dict) else c.get("link")
                arts.append({"title": c.get("title", ""), "summary": c.get("summary", "") or c.get("description", ""),
                             "link": link, "publisher": (c.get("provider") or {}).get("displayName", "Yahoo Finance")
                             if isinstance(c.get("provider"), dict) else c.get("publisher", "Yahoo Finance"),
                             "published": _parse_date(c.get("pubDate") or c.get("providerPublishTime"))})
        except Exception:
            pass
        arts += _rss(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US", "Yahoo Finance")
    q = urllib.parse.quote_plus(query)
    arts += _rss(f"https://news.google.com/rss/search?q={q}+when:7d&hl=en-US&gl=US&ceid=US:en", "Google News")
    seen, out = set(), []
    for a in arts:
        k = a["title"].strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(a)
    return out


# ---------------------------------------------------------------------------
# SEC EDGAR (filings)
# ---------------------------------------------------------------------------

# The SEC asks automated clients to identify themselves. Set SEC_USER_AGENT
# (e.g. "SharkFin you@example.com") as an environment variable or Streamlit
# secret to use your own contact.
SEC_FORM_ITEMS = {
    "1.01": "Material agreement", "1.02": "Agreement terminated", "1.05": "Cybersecurity incident",
    "2.01": "Acquisition or sale of assets", "2.02": "Earnings results", "2.03": "New debt",
    "2.05": "Restructuring / layoffs", "2.06": "Impairment", "3.01": "Listing notice",
    "4.01": "Auditor change", "4.02": "Restatement", "5.01": "Change in control", "5.02": "Executive/director change",
    "5.03": "Bylaw change", "5.07": "Shareholder vote", "7.01": "Reg FD disclosure", "8.01": "Other events",
    "9.01": "Exhibits",
}


def _sec_get(url: str, timeout: int = 20):
    import os

    import requests

    ua = os.environ.get("SEC_USER_AGENT") or "SharkFin research app (github.com/adiamlani130/SharkFin)"
    r = requests.get(url, headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}, timeout=timeout)
    r.raise_for_status()
    return r


@ttl_cache(24 * 3600)
def sec_cik(symbol: str) -> int | None:
    try:
        table = _sec_get("https://www.sec.gov/files/company_tickers.json").json()
    except Exception as e:  # pragma: no cover - network
        log.warning("SEC ticker map failed: %s", e)
        return None
    sym = symbol.upper().replace("-", ".")
    for row in table.values():
        if str(row.get("ticker", "")).upper() in (sym, symbol.upper()):
            return int(row["cik_str"])
    return None


@ttl_cache(6 * 3600)
def sec_filings(symbol: str, forms: tuple = ("10-K", "10-Q", "8-K"), limit: int = 40) -> pd.DataFrame:
    """Recent filings with links, newest first: straight from SEC EDGAR, or from
    Yahoo's copy of the same filings when EDGAR is unreachable. Empty frame if
    neither answers (or the company isn't a US filer)."""
    df = _edgar_filings(symbol, forms, limit)
    if df.empty:
        df = _yahoo_filings(symbol, forms, limit)
    return df


def _yahoo_filings(symbol: str, forms: tuple, limit: int) -> pd.DataFrame:
    try:
        raw = _yf().Ticker(symbol).sec_filings or []
    except Exception as e:  # pragma: no cover - network
        log.warning("Yahoo filings(%s) failed: %s", symbol, e)
        return pd.DataFrame()
    rows = []
    for f in raw:
        form = str(f.get("type", "")).replace("/A", "")
        if form not in forms:
            continue
        ex = f.get("exhibits") or {}
        doc = ex.get(f.get("type")) or ex.get(form) or next(iter(ex.values()), None)
        rows.append({"form": form, "filed": pd.to_datetime(f.get("date"), errors="coerce"), "reportDate": None,
                     "what": f.get("title") if form == "8-K" else "", "url": doc or f.get("edgarUrl"),
                     "source": "Yahoo Finance"})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("filed", ascending=False).head(limit).reset_index(drop=True)


def _edgar_filings(symbol: str, forms: tuple, limit: int) -> pd.DataFrame:
    cik = sec_cik(symbol)
    if not cik:
        return pd.DataFrame()
    try:
        sub = _sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()
    except Exception as e:  # pragma: no cover - network
        log.warning("SEC submissions(%s) failed: %s", symbol, e)
        return pd.DataFrame()
    rec = pd.DataFrame(sub.get("filings", {}).get("recent", {}))
    if rec.empty:
        return rec
    rec = rec[rec["form"].isin(forms)].head(limit).copy()
    acc = rec["accessionNumber"].str.replace("-", "", regex=False)
    rec["url"] = [f"https://www.sec.gov/Archives/edgar/data/{cik}/{a}/{d}" for a, d in zip(acc, rec["primaryDocument"])]
    rec["filed"] = pd.to_datetime(rec["filingDate"], errors="coerce")
    items = rec.get("items", pd.Series("", index=rec.index)).fillna("")
    rec["what"] = [", ".join(SEC_FORM_ITEMS.get(i.strip(), i.strip()) for i in str(s).split(",") if i.strip() and i.strip() != "9.01")
                   for s in items]
    rec["source"] = "SEC EDGAR"
    return rec[["form", "filed", "reportDate", "what", "url", "source"]].reset_index(drop=True)


@ttl_cache(24 * 3600)
def sec_document_text(url: str) -> str:
    from .catalysts import html_to_text

    try:
        if "sec.gov" in url:
            return html_to_text(_sec_get(url, timeout=40).text)
        import requests

        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 SharkFin"}, timeout=40)
        r.raise_for_status()
        return html_to_text(r.text)
    except Exception as e:  # pragma: no cover - network
        log.warning("SEC document %s failed: %s", url, e)
        return ""


@ttl_cache(900)
def market_history(period: str = "10y") -> pd.DataFrame:
    """SPY history, used as the market-uptrend filter."""
    return history("SPY", period)
