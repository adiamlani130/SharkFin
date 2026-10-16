"""Market-data access layer (Yahoo Finance via yfinance, plus RSS news).

All network calls go through here, are wrapped in a small thread-safe TTL cache
(shared across Streamlit sessions in the same server process) and fail soft:
callers get empty frames / NaNs instead of exceptions.
"""

from __future__ import annotations

import copy
import functools
import logging
import pickle
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

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

        def cached(*args, **kwargs) -> bool:
            """Whether a call with these arguments would be answered from the cache."""
            with _lock:
                hit = _cache.get((fn.__qualname__, args, tuple(sorted(kwargs.items()))))
            return bool(hit) and time.time() - hit[0] < seconds

        wrapper.cache_clear = lambda: _cache.clear()
        wrapper.cached = cached
        return wrapper

    return deco


def prefetch(jobs: list, workers: int = 8, progress=None) -> None:
    """Warm the cache for many calls at once: ``jobs`` is a list of ``(fn, args)`` or ``(fn, args, kwargs)``.

    Calls already cached are skipped. ``progress(done, total)`` runs on the calling thread after each call
    finishes, so a Streamlit page can update a progress bar from it. If ``progress`` raises (Streamlit stops
    a script that way when the user changes a setting), calls not yet started are dropped and the ones
    running finish in the background; everything finished stays cached, so the next run picks up where
    this one stopped.
    """
    jobs = [(j[0], j[1], j[2] if len(j) > 2 else {}) for j in jobs]
    todo = [(fn, a, kw) for fn, a, kw in jobs if not getattr(fn, "cached", lambda *_, **__: False)(*a, **kw)]
    if not todo:
        return
    ex = ThreadPoolExecutor(max_workers=workers)
    try:
        pending = {ex.submit(fn, *a, **kw) for fn, a, kw in todo}
        done = 0
        while pending:
            finished, pending = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)
            done += len(finished)
            if progress is not None:
                progress(done, len(todo))
    finally:
        ex.shutdown(wait=False, cancel_futures=True)


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
        # Yahoo sometimes blocks cloud servers: fall back to Alpaca's daily bars when keys are set.
        if interval == "1d" and alpaca_keys() and not symbol.startswith("^") and "=" not in symbol:
            return alpaca_daily(symbol, period)
        return pd.DataFrame()
    df.index = _naive(df.index)
    return df[[c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]].dropna(subset=["Close"])


# Big price panels (the S&P 500 and the like) are also kept on disk, so a restart doesn't download them again:
# a copy saved in the last half hour is used as is, an older one (up to a week) only fetches the latest days.
PANEL_DIR = Path(".sharkfin") / "cache" / "panels"
PANEL_FRESH = 1800
PANEL_PATCH_DAYS = 7
PANEL_MIN_SYMBOLS = 20
SAME_PRICE = 1e-4  # Yahoo's overlapping adjusted closes match exactly unless a split or dividend re-adjusted them


def _panel_file(kind: str, symbols: tuple, period: str) -> Path:
    import hashlib

    h = hashlib.sha1(f"{kind}|{period}|{','.join(sorted(symbols))}".encode()).hexdigest()[:16]
    return PANEL_DIR / f"{kind}_{period}_{h}.pkl"


def _panel_load(path: Path):
    try:
        with open(path, "rb") as f:
            saved_at, frames = pickle.load(f)
        return (saved_at, frames) if isinstance(frames, dict) and frames else None
    except Exception:
        return None


def _panel_save(path: Path, frames: dict) -> None:
    import os

    try:
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{threading.get_ident()}.tmp")
        with open(tmp, "wb") as f:
            pickle.dump((time.time(), frames), f)
        os.replace(tmp, path)
    except Exception as e:  # pragma: no cover - read-only disk
        log.warning("couldn't save the price panel: %s", e)


def _patched(old: dict, recent: dict, period: str, key: str) -> tuple[dict | None, list]:
    """``old`` with ``recent``'s rows added (newer values win), trimmed back to ``period``. Also returns the
    tickers to download again in full: those whose overlapping prices changed (Yahoo re-adjusted their past for
    a split or dividend) or that ``recent`` is missing. None when the two don't overlap at all."""
    oc, rc = old[key], recent.get(key, pd.DataFrame())
    common = oc.index.intersection(rc.index)
    if rc.empty or not len(common):
        return None, []
    cols = oc.columns.intersection(rc.columns)
    gap = (oc.loc[common, cols] / rc.loc[common, cols] - 1).abs().max()
    redo = list(gap[gap > SAME_PRICE].index) + [c for c in oc.columns if c not in rc.columns]
    start = rc.index.max() - pd.Timedelta(days=_PERIOD_DAYS.get(period, 7300))
    out = {}
    for f, df in old.items():
        r = recent.get(f)
        m = df if r is None or r.empty else pd.concat([df, r])
        m = m[~m.index.duplicated(keep="last")].sort_index()
        out[f] = m if period == "max" else m.loc[m.index >= start]
    return out, redo


def _cached_panel(kind: str, symbols: tuple, period: str, fetch, key: str) -> dict:
    """``fetch(symbols, period)`` (a dict of dates x tickers frames) backed by the disk copy described above."""
    if len(symbols) < PANEL_MIN_SYMBOLS or period not in _PERIOD_DAYS:
        return fetch(symbols, period)
    path = _panel_file(kind, symbols, period)
    saved = _panel_load(path)
    if saved:
        age, frames = time.time() - saved[0], saved[1]
        if age < PANEL_FRESH:
            return frames
        if age < PANEL_PATCH_DAYS * 86400 and key in frames:
            recent = fetch(tuple(frames[key].columns), "1mo" if age > 3 * 86400 else "5d")
            merged, redo = _patched(frames, recent, period, key) if recent else (None, [])
            if merged is not None:
                if redo:
                    full = fetch(tuple(redo), period)
                    for f, df in merged.items():
                        if f in full:
                            merged[f] = pd.concat([df.drop(columns=[c for c in full[f].columns if c in df]), full[f]],
                                                  axis=1).sort_index()
                _panel_save(path, merged)
                return merged
    frames = fetch(symbols, period)
    if frames and not frames.get(key, pd.DataFrame()).empty:
        _panel_save(path, frames)
    return frames


@ttl_cache(1800)
def download_prices(symbols: tuple, period: str = "2y", field: str = "Close", chunk: int = 150) -> pd.DataFrame:
    """Batched adjusted-close download: one request per ``chunk`` tickers instead of one per ticker. Big panels
    are kept on disk and only topped up with the latest days (see ``_cached_panel``)."""
    frames = _cached_panel(f"prices-{field}", tuple(symbols), period,
                           lambda syms, per: {field: _fetch_prices(syms, per, field, chunk)}, field)
    return frames.get(field, pd.DataFrame())


def _fetch_prices(symbols: tuple, period: str, field: str, chunk: int) -> pd.DataFrame:
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
    """Batched OHLCV download: {"Open"|"High"|"Low"|"Close"|"Volume": DataFrame (dates x tickers)}. Big panels
    are kept on disk and only topped up with the latest days (see ``_cached_panel``)."""
    return _cached_panel("ohlcv", tuple(symbols), period, lambda syms, per: _fetch_ohlcv(syms, per, chunk), "Close")


def _fetch_ohlcv(symbols: tuple, period: str, chunk: int) -> dict:
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


EARNINGS_DIR = Path(".sharkfin") / "cache" / "earnings"


def _earnings_fresh(ed: pd.DataFrame, fetched: float, now: float | None = None) -> bool:
    """A saved earnings history is still good unless it is a week old or a report date has passed since it
    was fetched (earnings only change when a company reports)."""
    now = time.time() if now is None else now
    if now - fetched > 7 * 86400:
        return False
    idx = pd.DatetimeIndex(ed.index)
    secs = (idx.tz_convert("UTC") if idx.tz is not None else idx).asi8 / 1e9
    return not bool(((secs > fetched - 86400) & (secs <= now)).any())


def _earnings_from_disk(symbol: str, limit: int) -> pd.DataFrame | None:
    try:
        with open(EARNINGS_DIR / f"{symbol}_{limit}.pkl", "rb") as f:
            fetched, ed = pickle.load(f)
        return ed if isinstance(ed, pd.DataFrame) and _earnings_fresh(ed, fetched) else None
    except Exception:
        return None


def _earnings_to_disk(symbol: str, limit: int, ed: pd.DataFrame) -> None:
    try:
        EARNINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(EARNINGS_DIR / f"{symbol}_{limit}.pkl", "wb") as f:
            pickle.dump((time.time(), ed), f)
    except Exception as e:  # pragma: no cover - read-only disk
        log.warning("couldn't save earnings for %s: %s", symbol, e)


@ttl_cache(12 * 3600)
def earnings_history(symbol: str, limit: int = 28) -> pd.DataFrame:
    """Yahoo's earnings dates (EPS estimate, reported EPS, surprise %), about seven years for ``limit=28``.

    Yahoo only serves these from a slow page (about a second per stock), so a copy is kept on disk and reused
    until the stock reports again.
    """
    saved = _earnings_from_disk(symbol, limit)
    if saved is not None:
        return saved
    for attempt in range(2):
        try:
            ed = _yf().Ticker(symbol).get_earnings_dates(limit=limit)
            if isinstance(ed, pd.DataFrame) and not ed.empty:
                _earnings_to_disk(symbol, limit, ed)
                return ed
        except Exception as e:  # pragma: no cover - network
            log.warning("earnings_history(%s) failed: %s", symbol, e)
        time.sleep(0.8 * (attempt + 1))
    return pd.DataFrame()


@ttl_cache(12 * 3600)
def earnings_histories(symbols: tuple, workers: int = 6) -> dict:
    """Earnings dates for many symbols in parallel: {symbol: DataFrame}."""
    with ThreadPoolExecutor(max_workers=workers) as ex:
        frames = list(ex.map(earnings_history, symbols))
    return {s: f for s, f in zip(symbols, frames) if isinstance(f, pd.DataFrame) and not f.empty}


@ttl_cache(12 * 3600)
def infos(symbols: tuple, workers: int = 10) -> pd.DataFrame:
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


@ttl_cache(6 * 3600)
def tbill_yields(period: str = "10y") -> pd.Series:
    """3-month Treasury bill yield (decimal) by day: what idle cash earns in a backtest."""
    h = history("^IRX", period)
    if h.empty:
        return pd.Series(dtype=float)
    y = h["Close"] / 100
    y.index = y.index.normalize()
    y = y[~y.index.duplicated(keep="last")]
    return y[(y >= 0) & (y < 0.2)]


class _NYSECalendar:
    """NYSE full-day holidays (built lazily so importing the data layer stays cheap)."""

    _cal = None

    @classmethod
    def holidays(cls, year: int) -> set:
        if cls._cal is None:
            from pandas.tseries.holiday import (AbstractHolidayCalendar, GoodFriday, Holiday, USLaborDay,
                                                USMartinLutherKingJr, USMemorialDay, USPresidentsDay,
                                                USThanksgivingDay, nearest_workday)

            class NYSE(AbstractHolidayCalendar):
                rules = [
                    Holiday("New Year", month=1, day=1, observance=nearest_workday), USMartinLutherKingJr,
                    USPresidentsDay, GoodFriday, USMemorialDay,
                    Holiday("Juneteenth", month=6, day=19, start_date="2022-01-01", observance=nearest_workday),
                    Holiday("Independence Day", month=7, day=4, observance=nearest_workday), USLaborDay,
                    USThanksgivingDay, Holiday("Christmas", month=12, day=25, observance=nearest_workday),
                ]

            cls._cal = NYSE()
        return set(cls._cal.holidays(f"{year}-01-01", f"{year}-12-31").date)


def market_status() -> tuple[str, datetime]:
    """NYSE session right now ("Open", "Pre-market", "After-hours" or "Closed") and the New York time."""
    from datetime import time as _t

    import pytz

    ny = datetime.now(pytz.timezone("America/New_York"))
    trading_day = ny.weekday() < 5 and ny.date() not in _NYSECalendar.holidays(ny.year)
    is_open = trading_day and _t(9, 30) <= ny.time() < _t(16, 0)
    pre = trading_day and _t(4, 0) <= ny.time() < _t(9, 30)
    post = trading_day and _t(16, 0) <= ny.time() < _t(20, 0)
    return ("Open" if is_open else "Pre-market" if pre else "After-hours" if post else "Closed"), ny


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


SP500_SPELLS_URL = "https://raw.githubusercontent.com/fja05680/sp500/master/sp500_ticker_start_end.csv"
SP500_SPELLS_FILE = Path(__file__).with_name("research_data") / "sp500_ticker_start_end.csv"


def _parse_spells(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=str.lower)
    if not {"ticker", "start_date", "end_date"} <= set(df.columns) or len(df) < 500:
        raise ValueError("unexpected S&P 500 membership file")
    return pd.DataFrame({"ticker": df["ticker"].astype(str).str.strip().str.replace(".", "-", regex=False),
                         "start": pd.to_datetime(df["start_date"]), "end": pd.to_datetime(df["end_date"])})


@ttl_cache(24 * 3600)
def sp500_spells() -> pd.DataFrame:
    """Every spell a ticker spent in the S&P 500 since 1996 (ticker, start, end; end is NaT while still a member).

    From the fja05680/sp500 dataset (Andreas Clenow's history plus index changes since 2019), refreshed daily from
    GitHub; the copy bundled in ``research_data`` is used when the download fails. A ticker is a member from its
    start date up to the day before its end date (changes take effect before the open)."""
    try:
        import io

        import requests

        r = requests.get(SP500_SPELLS_URL, timeout=10)
        r.raise_for_status()
        return _parse_spells(pd.read_csv(io.StringIO(r.text)))
    except Exception as e:  # pragma: no cover - network
        log.info("S&P 500 membership download failed (%s); using the bundled copy", e)
    return _parse_spells(pd.read_csv(SP500_SPELLS_FILE))


def sp500_members(dates: pd.DatetimeIndex, tickers=None) -> pd.DataFrame:
    """Point-in-time S&P 500 membership: a dates x tickers frame, True on days the ticker was in the index.
    ``tickers`` defaults to everyone who was a member at some point in ``dates``."""
    sp = sp500_spells()
    dates = pd.DatetimeIndex(dates).normalize()
    if tickers is None:
        live = sp[(sp["start"] <= dates.max()) & (sp["end"].isna() | (sp["end"] > dates.min()))]
        tickers = list(dict.fromkeys(live["ticker"]))
    out = pd.DataFrame(False, index=dates, columns=list(tickers))
    for row in sp[sp["ticker"].isin(out.columns)].itertuples(index=False):
        inside = (dates >= row.start) & ((dates < row.end) if pd.notna(row.end) else True)
        out[row.ticker] = out[row.ticker].to_numpy() | np.asarray(inside)
    return out


def sp500_ever(start, end=None) -> list:
    """Every ticker that was in the S&P 500 at some point between ``start`` and ``end`` (for point-in-time
    backtests: today's members plus the ones that left). Yahoo only has prices for some of the ones that left."""
    sp = sp500_spells()
    end = pd.Timestamp(end) if end is not None else pd.Timestamp.now().normalize()
    live = sp[(sp["start"] <= end) & (sp["end"].isna() | (sp["end"] > pd.Timestamp(start)))]
    return list(dict.fromkeys(live["ticker"]))


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


# ---------------------------------------------------------------------------
# Alpaca (optional): intraday bars, live trades and a daily-price fallback
# ---------------------------------------------------------------------------

ALPACA_DATA = "https://data.alpaca.markets/v2"
def yahoo_period(years: int) -> str:
    """The Yahoo download period that covers ``years`` (Yahoo has no 20y: longer spans download "max")."""
    return f"{years}y" if f"{years}y" in _PERIOD_DAYS else "max"


def last_years(frames: dict, years: int) -> dict:
    """A dict of date-indexed frames cut to the last ``years`` years."""
    start = pd.Timestamp.now().normalize() - pd.DateOffset(years=years)
    return {f: df.loc[df.index >= start] for f, df in frames.items()}


_PERIOD_DAYS = {"5d": 7, "1mo": 31, "3mo": 92, "6mo": 183, "1y": 366, "2y": 731, "5y": 1827, "10y": 3653, "max": 7300}


def alpaca_keys() -> tuple[str, str] | None:
    """Alpaca market-data keys from the environment or Streamlit secrets (ALPACA_API_KEY / ALPACA_SECRET_KEY).
    SharkFin only reads market data with them; it never places orders."""
    import os

    pairs = (("ALPACA_API_KEY", "ALPACA_SECRET_KEY"), ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY"))
    for k, s in pairs:
        if os.environ.get(k) and os.environ.get(s):
            return os.environ[k], os.environ[s]
    try:
        import streamlit as st

        for k, s in pairs:
            if st.secrets.get(k) and st.secrets.get(s):  # type: ignore[attr-defined]
                return str(st.secrets[k]), str(st.secrets[s])
    except Exception:
        pass
    return None


def _alpaca_get(path: str, params: dict) -> dict:
    import requests

    keys = alpaca_keys()
    if not keys:
        return {}
    for attempt in range(4):
        try:
            r = requests.get(f"{ALPACA_DATA}{path}", params=params, timeout=30,
                             headers={"APCA-API-KEY-ID": keys[0], "APCA-API-SECRET-KEY": keys[1]})
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            if r.status_code >= 400:
                log.warning("Alpaca %s -> %s %s", path, r.status_code, r.text[:200])
                return {}
            return r.json()
        except Exception as e:  # pragma: no cover - network
            log.warning("Alpaca %s failed: %s", path, e)
            time.sleep(1 + attempt)
    return {}


def alpaca_bars(symbol: str, timeframe: str, start: datetime, end: datetime | None = None, feed: str = "sip",
                adjustment: str = "all") -> pd.DataFrame:
    """Bars from Alpaca as a DataFrame (o, h, l, c, v, vw) indexed by New York time (bar start).

    Intraday pages hold only about a month each, so long ranges are split into quarters fetched in parallel."""
    utc = lambda d: pd.Timestamp(d).tz_convert("UTC") if pd.Timestamp(d).tzinfo else pd.Timestamp(d).tz_localize("UTC")
    t0, t1 = utc(start), utc(end) if end is not None else pd.Timestamp.now(tz="UTC")
    edges = [t0]
    while timeframe != "1Day" and edges[-1] + pd.Timedelta(days=92) < t1:
        edges.append(edges[-1] + pd.Timedelta(days=92))
    edges.append(t1)

    def chunk(a: pd.Timestamp, b: pd.Timestamp) -> list:
        params = {"timeframe": timeframe, "start": a.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "end": b.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 10000, "feed": feed, "adjustment": adjustment}
        rows, token = [], None
        for _ in range(500):
            if token:
                params["page_token"] = token
            j = _alpaca_get(f"/stocks/{symbol.replace('-', '.')}/bars", params)
            if not j and token:  # a failed page: try it once more rather than return a silently cut-off history
                j = _alpaca_get(f"/stocks/{symbol.replace('-', '.')}/bars", params)
            rows += j.get("bars") or []
            token = j.get("next_page_token")
            if not token:
                break
        return rows

    spans = list(zip(edges[:-1], edges[1:]))
    if len(spans) == 1:
        rows = chunk(*spans[0])
    else:
        with ThreadPoolExecutor(max_workers=6) as ex:
            rows = [r for part in ex.map(lambda ab: chunk(*ab), spans) for r in part]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.pop("t"), utc=True).dt.tz_convert("America/New_York")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df[[c for c in ("o", "h", "l", "c", "v", "vw") if c in df.columns]].astype(float)


@ttl_cache(6 * 3600)
def alpaca_daily(symbol: str, period: str = "5y") -> pd.DataFrame:
    """Split- and dividend-adjusted daily bars from Alpaca, shaped like ``history``."""
    start = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=_PERIOD_DAYS.get(period, 1827))
    end = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=16)  # the free plan has no SIP data in the last 15 minutes
    df = alpaca_bars(symbol, "1Day", start, end)
    if df.empty:
        return df
    df.index = df.index.tz_localize(None).normalize()
    return df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})[
        ["Open", "High", "Low", "Close", "Volume"]]


@ttl_cache(1800)
def intraday_bars(symbol: str, days: int = 60) -> pd.DataFrame:
    """30-minute regular-session bars (o, h, l, c, v, vw; New York time); ``.attrs["source"]`` says where they
    came from.

    Alpaca (with keys) has years of history; without keys Yahoo has the last 60 days, and its bars carry no
    VWAP, so the typical price stands in for it."""
    if alpaca_keys():
        now = pd.Timestamp.now(tz="UTC")
        df = alpaca_bars(symbol, "30Min", now - pd.Timedelta(days=days), now - pd.Timedelta(minutes=16))
        if not df.empty:
            return _session(df, "Alpaca (SIP feed)")
    try:
        raw = _yf().Ticker(symbol).history(period=f"{min(days, 59)}d", interval="30m", auto_adjust=True, prepost=False)
    except Exception as e:  # pragma: no cover - network
        log.warning("intraday %s failed: %s", symbol, e)
        raw = None
    if raw is None or raw.empty:
        return pd.DataFrame()
    idx = raw.index.tz_convert("America/New_York") if raw.index.tz is not None else raw.index.tz_localize("America/New_York")
    df = pd.DataFrame({"o": raw["Open"], "h": raw["High"], "l": raw["Low"], "c": raw["Close"],
                       "v": raw["Volume"].astype(float)}, index=idx)
    df["vw"] = (df["h"] + df["l"] + df["c"]) / 3
    return _session(df, "Yahoo (last 60 days only)")


def _session(df: pd.DataFrame, source: str) -> pd.DataFrame:
    m = df.index.hour * 60 + df.index.minute
    out = df[(m >= 570) & (m < 960)].copy()
    out.attrs["source"] = source
    return out


@ttl_cache(60)
def latest_trade(symbol: str) -> dict:
    """The latest trade (price and time) from Alpaca's real-time IEX feed, or {} without keys."""
    j = _alpaca_get(f"/stocks/{symbol}/trades/latest", {"feed": "iex"})
    t = j.get("trade") or {}
    if not t.get("p"):
        return {}
    return {"price": float(t["p"]), "time": pd.Timestamp(t["t"]).tz_convert("America/New_York")}
