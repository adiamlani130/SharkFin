"""Which swing strategy the app uses: Leader Dip by default, a Strategy Lab template, or the user's own rules.

Leader Dip has its own module (it ranks stocks against the whole S&P 500 and uses a limit entry). Every other
choice is a Strategy Lab rule set run through ``builder``, so the same rules give the same signals on Top
Performers, Research and in the Strategy Lab backtest.
"""

from __future__ import annotations

import pandas as pd

from . import builder

LEADER_DIP = "Leader Dip"
MINE = "My Strategy Lab strategy"
# Templates that trade in and out over days to weeks (the long-hold trend templates are left out).
TEMPLATE_CHOICES = ["RSI dip in an uptrend", "Bollinger bounce", "Pullback in an uptrend", "Volume breakout",
                    "MACD momentum", "55-day breakout"]
ABOUT = {
    LEADER_DIP: "SharkFin's researched default. Buys a sharp two-day drop in one of the S&P 500's strongest stocks "
                "while the market is in an uptrend and sells into the bounce. It had the best risk-adjusted record of "
                "every swing system tested (2000-2026).",
    MINE: "The rules you saved from Strategy Lab → Build and test.",
}
NOTE_UNTESTED = ("This strategy has not been through SharkFin's 2000-2026 portfolio test (Leader Dip has). The backtest "
                 "below shows how it would have traded this one stock.")


def choices(mine: dict | None = None) -> list[str]:
    return [LEADER_DIP, *TEMPLATE_CHOICES, *([MINE] if mine else [])]


def about(name: str) -> str:
    if name in ABOUT:
        return ABOUT[name]
    return builder.TEMPLATES.get(name, {}).get("about", "")


def rules(name: str, mine: dict | None = None) -> dict | None:
    """The builder rule set for a choice (None for Leader Dip, which has its own engine)."""
    if name == LEADER_DIP:
        return None
    if name == MINE:
        return clean(mine) if mine else None
    return builder.template(name) if name in builder.TEMPLATES else None


def clean(s: dict) -> dict:
    """A rule set without Strategy Lab's widget ids, safe to save as JSON."""
    out = {k: v for k, v in s.items() if k not in ("entry", "exit")}
    for k in ("entry", "exit"):
        out[k] = [{kk: vv for kk, vv in c.items() if kk != "id"} for c in s.get(k, [])]
    for k, d in (("stop", 0.0), ("target", 0.0), ("trail", 0.0), ("max_days", 0), ("market_filter", False),
                 ("logic", "ALL")):
        out.setdefault(k, d)
    return out


def _frame(ohlcv: dict, sym: str) -> pd.DataFrame:
    df = pd.DataFrame({f: ohlcv[f][sym] for f in ("Open", "High", "Low", "Close", "Volume") if f in ohlcv
                       and sym in ohlcv[f]})
    return df.dropna(subset=[c for c in ("Open", "High", "Low", "Close") if c in df])


def rule_checks(ohlcv: pd.DataFrame, s: dict, market: pd.Series | None = None) -> list[dict]:
    """Each buy and sell rule with whether it held at the last close."""
    rows = []
    for kind, label in (("entry", "Buy rule"), ("exit", "Sell rule")):
        for c in s.get(kind, []):
            try:
                ok = bool(builder.condition_mask(ohlcv, c, market).iloc[-1])
            except Exception:
                ok = None
            rows.append({"Rule": f"{label}: {builder.describe(c)}", "Pass": ok})
    if s.get("market_filter") and market is not None and len(market):
        m = market.reindex(ohlcv.index).ffill()
        on = bool(m.iloc[-1] > m.rolling(200).mean().iloc[-1]) if m.notna().sum() >= 200 else None
        rows.append({"Rule": "Buy rule: S&P 500 above its 200-day average", "Pass": on})
    return rows


def stock_status(ohlcv: pd.DataFrame, s: dict, market: pd.Series | None = None, cost_bps: float = 5.0,
                 rf: float = 0.0) -> dict:
    """Where one stock stands under a rule set at the last close, plus how the rules traded it historically."""
    out = {"label": "Not enough history", "tone": "neu", "note": "", "checks": rule_checks(ohlcv, s, market) if len(ohlcv) else [],
           "stats": {}, "open_trade": None, "signal": False, "result": None}
    try:
        res = builder.run(ohlcv, s, cost_bps, rf, market)
    except ValueError as e:
        out["note"] = str(e)
        return out
    entry, exit_ = res["entry"], res["exit"]
    out.update(result=res, stats=res["stats"], open_trade=res["open_trade"], signal=bool(entry.iloc[-1]))
    buy_txt, sell_txt = builder.describe_strategy(s)
    if res["open_trade"] is not None:
        t = res["open_trade"]
        if bool(exit_.iloc[-1]):
            out.update(label="Sell signal", tone="neg",
                       note=f"A sell rule fired at the last close, so a trade opened on {t['Entry date']:%b %d} "
                            f"({t['Return']:+.1%} so far) sells at the next open.")
        else:
            out.update(label="In a trade", tone="pos",
                       note=f"The rules bought on {t['Entry date']:%b %d} at {t['Entry']:.2f} and are still holding "
                            f"({t['Return']:+.1%}, {t['Days']} days). Sell when {sell_txt}.")
    elif out["signal"]:
        out.update(label="Buy signal", tone="pos",
                   note=f"Every buy rule held at the last close, so the rules buy at the next open. Sell when {sell_txt}.")
    else:
        out.update(label="No signal", tone="neu", note=f"Waiting. The rules buy when {buy_txt}.")
    return out


def scan(ohlcv: dict, s: dict, market: pd.Series | None = None) -> pd.DataFrame:
    """Stocks whose buy rules all held at the last close."""
    rows = []
    syms = list(ohlcv.get("Close", pd.DataFrame()).columns)
    need = builder.warmup(s) + 5
    for sym in syms:
        df = _frame(ohlcv, sym)
        if len(df) < need:
            continue
        try:
            entry, exit_ = builder.signals(df, s, market)
        except Exception:
            continue
        if not bool(entry.iloc[-1]):
            continue
        c = df["Close"]
        rows.append({"Symbol": sym, "Price": float(c.iloc[-1]), "1-day change": float(c.iloc[-1] / c.iloc[-2] - 1),
                     "1-month change": float(c.iloc[-1] / c.iloc[-22] - 1) if len(c) > 22 else float("nan"),
                     "Signals in the last 20 days": int(entry.tail(20).sum())})
    return pd.DataFrame(rows, columns=["Symbol", "Price", "1-day change", "1-month change",
                                       "Signals in the last 20 days"]).set_index("Symbol")
