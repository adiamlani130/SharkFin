"""Phone alerts after the close, sent through ntfy.sh (free, no account; iPhone and Android apps).

Run by the daily GitHub Action (.github/workflows/daily-alerts.yml) on weekdays after the close:

    python -m sharkfin.alerts            # send
    python -m sharkfin.alerts --dry-run  # print instead of sending

What it sends:
* to NTFY_TOPIC (yours, optional): today's Dive Zone and Tech Breakout Rider buy signals.
* to every signed-in user who turned on alerts (their own topic, saved in Supabase): the same signals if they want
  them, exit signals on stocks they hold, and their portfolio threat level when it rises a level or sits at HIGH.

Each run also reads Supabase, which keeps a free project from pausing for inactivity.
An ntfy topic works like a password: anyone who knows the name can read it, so topics are long and random.
"""

from __future__ import annotations

import os
import secrets
import sys

import numpy as np
import pandas as pd
import requests

from . import data, store, threat

NTFY = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
DEFAULTS = {"topic": "", "signals": True, "holdings": True, "threat": True}


def new_topic() -> str:
    return "sharkfin-" + secrets.token_urlsafe(15).replace("_", "x").replace("-", "y").lower()


def valid_topic(t: str) -> bool:
    return bool(t) and len(t) >= 16 and len(t) <= 64 and all(c.isalnum() or c in "-_" for c in t)


def send(topic: str, title: str, body: str, priority: str = "default", tags: str = "shark") -> bool:
    if not valid_topic(topic):
        return False
    try:
        r = requests.post(f"{NTFY}/{topic}", data=body.encode("utf-8"), timeout=15,
                          headers={"Title": title.encode("utf-8"), "Priority": priority, "Tags": tags})
        return r.ok
    except Exception:
        return False


# ---------------------------------------------------------------------------
# What to say
# ---------------------------------------------------------------------------


def todays_signals() -> dict:
    """{"dive": [tickers], "breakout": [tickers], "dive_table": df, "breakout_table": df} at the last close."""
    from . import live

    ld, br = live.leader_dip_today(), live.breakout_today()
    out = {"dive_table": ld, "breakout_table": br}
    out["dive"] = sorted(ld.index[ld["Signal"].astype(bool)]) if len(ld) else []
    out["breakout"] = sorted(br.index[br["Signal"].astype(bool)]) if len(br) else []
    return out


def signal_lines(sig: dict) -> list[str]:
    lines = []
    if sig.get("dive"):
        lines.append("Dive Zone buys: " + ", ".join(sig["dive"]))
    if sig.get("breakout"):
        lines.append("Breakout Rider buys: " + ", ".join(sig["breakout"]))
    return lines


def holding_exits(symbols: list[str], sig: dict) -> list[str]:
    """Exit readings on held stocks: Dive Zone's sell rule (RSI(2) above 70 or a close under the 200-day) and
    Breakout Rider's (the stock's 21-day EMA under its 50-day). They matter only if you bought it as that kind of trade."""
    out = []
    ld, br = sig.get("dive_table", pd.DataFrame()), sig.get("breakout_table", pd.DataFrame())
    for s in symbols:
        why = []
        if len(ld) and s in ld.index and bool(ld.at[s, "Sell signal"]):
            why.append("Dive Zone exit")
        if len(br) and s in br.index and "Trend intact" in br and not bool(br.at[s, "Trend intact"]):
            why.append("Breakout trend broke")
        if why:
            out.append(f"{s} ({', '.join(why)})")
    return out


def portfolio_threat(rows: list[dict]) -> threat.Threat | None:
    """Threat level for a saved portfolio (list of {symbol, shares, buy_price})."""
    lots = pd.DataFrame([r for r in rows if isinstance(r, dict) and r.get("symbol") and r.get("shares")])
    if lots.empty:
        return None
    sh = lots.groupby(lots["symbol"].astype(str).str.upper())["shares"].sum().astype(float)
    px = data.download_prices(tuple(sh.index) + ("SPY",), period="2y")
    if px.empty:
        return None
    last = px.ffill().iloc[-1]
    val = (sh * last.reindex(sh.index)).dropna()
    if val.sum() <= 0:
        return None
    infos = data.infos(tuple(val.index))
    vix_h = data.history("^VIX", "1y")
    vix = float(vix_h["Close"].iloc[-1]) if not vix_h.empty else np.nan
    return threat.assess(px, val / val.sum(), infos.get("sector"), threat.next_earnings(infos), vix)


def threat_line(th: threat.Threat | None, last_level: str | None) -> tuple[str | None, bool]:
    """(line, urgent): report when the level rose since the last run, or is HIGH."""
    if th is None:
        return None, False
    rose = last_level in ORDER and ORDER[th.level] > ORDER[last_level]
    if not (rose or th.level == "HIGH"):
        return None, False
    top = sorted(th.triggered, key=lambda x: -x["points"])[:2]
    why = "; ".join(f"{x['name'].lower()}: {x['detail']}" for x in top)
    arrow = f"{last_level} -> {th.level}" if rose else th.level
    return f"Threat level {arrow} ({th.score:.0f}/100). {why}", th.level == "HIGH"


def compose(settings: dict, portfolio: list, sig: dict, last_level: str | None) -> tuple[str, str, str, str | None]:
    """(title, body, priority, new_level) for one user; body is "" when there's nothing worth a ping."""
    st_ = {**DEFAULTS, **(settings or {})}
    lines, urgent, level = [], False, None
    if st_["signals"]:
        lines += signal_lines(sig)
    held = sorted({str(r.get("symbol", "")).upper() for r in portfolio if isinstance(r, dict) and r.get("symbol")})
    if st_["holdings"] and held:
        ex = holding_exits(held, sig)
        if ex:
            lines.append("Exit signals on your holdings: " + "; ".join(ex))
    if st_["threat"] and held:
        th = portfolio_threat(portfolio)
        level = th.level if th else None
        line, urgent = threat_line(th, last_level)
        if line:
            lines.append(line)
    n_sig = len(sig.get("dive", [])) + len(sig.get("breakout", []))
    title = "SharkFin after the close" + (f": {n_sig} signal{'s' if n_sig != 1 else ''}" if st_["signals"] and n_sig else "")
    return title, "\n".join(lines), ("high" if urgent else "default"), level


# ---------------------------------------------------------------------------
# The daily run
# ---------------------------------------------------------------------------


def run(dry: bool = False) -> int:
    sig = todays_signals()
    sent = 0
    owner = os.environ.get("NTFY_TOPIC", "")
    if owner:
        body = "\n".join(signal_lines(sig)) or "No new Dive Zone or Breakout Rider signals today."
        title = "SharkFin after the close"
        print(f"[owner] {title}\n{body}\n")
        if not dry:
            sent += send(owner, title, body)

    if store.supabase_config():
        settings = store.cloud_all("alerts")  # also keeps the free Supabase project awake
        states = store.cloud_all("alert_state") if settings else {}
        for uid, rows in settings.items():
            s = rows[0] if rows and isinstance(rows[0], dict) else {}
            if not valid_topic(s.get("topic", "")):
                continue
            who = store.Identity("cloud", uid)
            try:
                portfolio = store.load("portfolio", who)
                last = (states.get(uid) or [{}])[0].get("level") if states.get(uid) else None
                title, body, prio, level = compose(s, portfolio, sig, last)
            except Exception as e:  # one user's bad data never stops the rest
                print(f"[{uid[:6]}] skipped: {e}")
                continue
            print(f"[{uid[:6]}] {title} ({prio})\n{body or '(nothing to send)'}\n")
            if not dry:
                if body:
                    sent += send(s["topic"], title, body, prio, "warning" if prio == "high" else "shark")
                if level:
                    store.save("alert_state", [{"level": level}], who)
    else:
        print("Supabase not configured: skipping per-user alerts.")
    print(f"Sent {sent} notification(s).")
    return 0


if __name__ == "__main__":
    sys.exit(run(dry="--dry-run" in sys.argv))
