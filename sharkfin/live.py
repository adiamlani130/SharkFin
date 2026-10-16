"""Today's readings for the three playbook strategies, shared by the Strategy Playbook, Top Performers, Research and
the Market Dashboard. Everything here is cached in the data layer, so pages can call it freely."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import breakout_rider, data, day_night, leader_dip

SECTOR_ETFS = tuple(sorted(set(leader_dip.GICS_ETF.values())))


@data.ttl_cache(900)
def market_inputs(period: str = "2y") -> dict:
    """SPY, QQQ and VIX closes and the sector ETFs, the inputs every switch needs."""
    spy = data.market_history(period)
    qqq = data.history("QQQ", period)
    vix = data.history("^VIX", period)
    etf = data.download_prices(SECTOR_ETFS, period=period)
    return {"spy": spy["Close"] if not spy.empty else pd.Series(dtype=float),
            "qqq": qqq["Close"] if not qqq.empty else pd.Series(dtype=float),
            "vix": vix["Close"] if not vix.empty else pd.Series(dtype=float), "etf": etf}


def sector_map() -> dict:
    """{ticker: sector ETF} for S&P 500 members."""
    tab = data.sp500_table()
    if "Sector" not in tab:
        return {}
    return {s: leader_dip.GICS_ETF.get(sec) for s, sec in zip(tab["Symbol"], tab["Sector"]) if leader_dip.GICS_ETF.get(sec)}


def switches() -> dict:
    """Today's on/off state of each strategy's market switch."""
    m = market_inputs()
    out = {}
    if len(m["spy"]) > leader_dip.TREND_DAYS:
        on = leader_dip.market_on(m["spy"], m["vix"] if len(m["vix"]) else None)
        reg = leader_dip.regime(m["spy"], m["vix"] if len(m["vix"]) else None)
        out["leader_dip"] = {"on": bool(on.iloc[-1]), "gap": reg.get("gap200"), "vix": reg.get("vix"),
                             "panic": reg.get("panic"), "idle": reg.get("idle_cash")}
    if len(m["qqq"]) > 60:
        q = m["qqq"].astype(float)
        f, s = q.ewm(span=breakout_rider.FAST, adjust=False).mean(), q.ewm(span=breakout_rider.SLOW, adjust=False).mean()
        out["breakout"] = {"on": bool(breakout_rider.qqq_gate(q).iloc[-1]), "gap": float(f.iloc[-1] / s.iloc[-1] - 1)}
    return out


@data.ttl_cache(1800)
def sp500_ohlcv(period: str = "2y") -> dict:
    return data.download_ohlcv(tuple(data.universe("S&P 500")), period=period)


@data.ttl_cache(1800)
def tech_ohlcv(period: str = "2y") -> dict:
    return data.download_ohlcv(tuple(breakout_rider.tech_universe(data.sp500_table())), period=period)


def sector_ret3(ohlc: dict, period: str = "2y") -> pd.DataFrame | None:
    m = market_inputs(period)
    c = ohlc.get("Close", pd.DataFrame())
    return leader_dip.sector_returns(c.index, c.columns, sector_map(), m["etf"]) if not c.empty else None


@data.ttl_cache(1800)
def leader_dip_today() -> pd.DataFrame:
    """Every S&P 500 stock's Leader Dip Plus reading at the last close (signals have Signal == True)."""
    ohlc = sp500_ohlcv()
    if "Close" not in ohlc or ohlc["Close"].shape[1] < 10:
        return pd.DataFrame()
    m = market_inputs()
    c = ohlc["Close"]
    ref = leader_dip.six_month_gain(c.ffill()).iloc[-1].dropna()
    return leader_dip.latest(c, ref, ohlc=ohlc, vix=m["vix"] if len(m["vix"]) else None, sector_ret3=sector_ret3(ohlc))


@data.ttl_cache(1800)
def breakout_today() -> pd.DataFrame:
    """Every tech stock's Breakout Rider reading at the last close."""
    ohlc = tech_ohlcv()
    if "Close" not in ohlc or ohlc["Close"].shape[1] < 10:
        return pd.DataFrame()
    return breakout_rider.latest(ohlc, market_inputs()["qqq"])


@data.ttl_cache(3600)
def tech_gains() -> pd.Series:
    """Tech stocks' 6-month gains: the yardstick for Breakout Rider's strength rank."""
    ohlc = tech_ohlcv()
    if "Close" not in ohlc:
        return pd.Series(dtype=float)
    c = ohlc["Close"].astype(float)
    return (c / c.shift(breakout_rider.STRENGTH_DAYS) - 1).iloc[-1].dropna()


def day_night_today() -> dict:
    """Where TQQQ stands today for both legs, using the latest real-time trade when Alpaca keys are set."""
    bars = data.intraday_bars(day_night.SYMBOL, 35)
    if bars.empty:
        return {}
    lt = data.latest_trade(day_night.SYMBOL)
    out = day_night.today(bars, lt.get("price"), pd.Timestamp.now(tz="America/New_York"))
    if out:
        out["source"] = bars.attrs.get("source", "")
        out["live_time"] = lt.get("time")
    return out


def summary_rows(ld: pd.DataFrame | None, br: pd.DataFrame | None, dn: dict | None) -> list[dict]:
    """One status line per strategy for dashboards."""
    sw = switches()
    rows = []
    ldsw = sw.get("leader_dip", {})
    n_ld = int(ld["Signal"].sum()) if ld is not None and len(ld) else None
    rows.append({"Strategy": "Leader Dip Plus 7", "Switch": ldsw.get("on"),
                 "Today": (f"{n_ld} signal{'s' if n_ld != 1 else ''}" if n_ld is not None else "Signals on the Strategy Playbook page"),
                 "Note": ("SPY above its 200-day" if ldsw.get("gap", np.nan) and ldsw.get("gap", 0) > 0 else
                          "VIX panic: buying allowed" if ldsw.get("panic") else "SPY below its 200-day: no new trades")
                 if ldsw else "market data unavailable"})
    brsw = sw.get("breakout", {})
    n_br = int(br["Signal"].sum()) if br is not None and len(br) else None
    rows.append({"Strategy": "Tech Breakout Rider", "Switch": brsw.get("on"),
                 "Today": (f"{n_br} signal{'s' if n_br != 1 else ''}" if n_br is not None else "Signals on the Strategy Playbook page"),
                 "Note": ("QQQ 21-day EMA above its 50-day" if brsw.get("on") else "QQQ 21-day EMA under its 50-day: no new trades")
                 if brsw else "QQQ data unavailable"})
    if dn:
        state = "in a day trade" if dn.get("in_trade") else "flat"
        night = "weak close so far: night buy likely" if dn.get("weak_close") else "no weak close so far"
        rows.append({"Strategy": "TQQQ Day + Night", "Switch": True, "Today": f"{state}; {night}",
                     "Note": f"band {dn['next_band']:.2f} at {dn['next_check']}" if dn.get("next_check") else "session over"})
    else:
        rows.append({"Strategy": "TQQQ Day + Night", "Switch": None, "Today": "intraday data unavailable", "Note": ""})
    return rows
