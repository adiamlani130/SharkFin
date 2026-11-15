"""Real US option prices for the options lab: Alpaca's historical option trade bars (OPRA, February 2024 on).

Research only, nothing in the app imports this. Bars are trade prices (no bid/ask history), so the lab adds a
spread cost on top. Data is cached as pickles in a folder you pass in (the lab uses ``.lab3/``)."""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

from sharkfin.data import alpaca_bars, alpaca_keys

OPT_URL = "https://data.alpaca.markets/v1beta1/options/bars"
FIRST_DAY = pd.Timestamp("2024-02-01")


def occ(root: str, expiry, cp: str, strike: float) -> str:
    """OCC option symbol, e.g. occ("QQQ", "2024-03-01", "C", 440) -> QQQ240301C00440000."""
    return f"{root}{pd.Timestamp(expiry):%y%m%d}{cp.upper()}{int(round(strike * 1000)):08d}"


def _get(params: dict) -> dict:
    k, s = alpaca_keys()
    for attempt in range(6):
        try:
            r = requests.get(OPT_URL, params=params, timeout=60,
                             headers={"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s})
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"option bars failed: {params.get('symbols', '')[:60]}")


def option_bars(symbols: list[str], timeframe: str, start, end) -> pd.DataFrame:
    """Long frame: symbol, t (New York time), o, h, l, c, v, vw, n. Up to 100 symbols per request."""
    out = []
    for i in range(0, len(symbols), 100):
        params = {"symbols": ",".join(symbols[i:i + 100]), "timeframe": timeframe, "limit": 10000,
                  "start": pd.Timestamp(start).strftime("%Y-%m-%d") if timeframe == "1Day" else
                  pd.Timestamp(start, tz="America/New_York").tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "end": pd.Timestamp(end).strftime("%Y-%m-%d") if timeframe == "1Day" else
                  pd.Timestamp(end, tz="America/New_York").tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")}
        token = None
        while True:
            if token:
                params["page_token"] = token
            j = _get(params)
            for sym, rows in (j.get("bars") or {}).items():
                for r in rows:
                    r["symbol"] = sym
                out += rows
            token = j.get("next_page_token")
            if not token:
                break
    if not out:
        return pd.DataFrame(columns=["symbol", "t", "o", "h", "l", "c", "v", "vw", "n"])
    df = pd.DataFrame(out)
    df["t"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert("America/New_York")
    return df


def stock_bars(symbol: str, timeframe: str, start, end, folder: Path) -> pd.DataFrame:
    """Unadjusted stock bars (option strikes are in unadjusted dollars), cached."""
    f = Path(folder) / f"stk_{symbol}_{timeframe}.pkl"
    if f.exists():
        return pd.read_pickle(f)
    df = alpaca_bars(symbol, timeframe, pd.Timestamp(start, tz="America/New_York"),
                     pd.Timestamp(end, tz="America/New_York"), adjustment="raw")
    df.to_pickle(f)
    return df
