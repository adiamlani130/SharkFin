"""Where each person's portfolio, watchlist and saved swing strategy are kept.

Four modes, picked from the app's secrets and whether the visitor is signed in:

* ``local``   - no sign-in configured (running on your own computer): one set of JSON files in ``.sharkfin/``,
                exactly as before.
* ``guest``   - sign-in is configured but this visitor hasn't signed in: kept for this visit only, never written
                to the server, so strangers on the public site no longer share (and overwrite) one portfolio.
* ``account`` - signed in, no Supabase keys: JSON files in ``.sharkfin/users/<id>/`` (fine locally; Streamlit
                Cloud wipes these on restart).
* ``cloud``   - signed in and Supabase is set up: one row per (user, list) in the ``sharkfin_user_data`` table.

Only the lists in ``USER_LISTS`` belong to a person. App-wide lists (e.g. the Dive Zone signal log) stay in
``.sharkfin/`` for everyone. Users are stored under a hash of their sign-in ID, never their email.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import requests

DATA_DIR = Path(".sharkfin")
USER_LISTS = frozenset({"portfolio", "watchlist", "my_swing_strategy", "swing_choice", "alerts", "alert_state"})
TABLE = "sharkfin_user_data"
TIMEOUT = 8


class StoreError(RuntimeError):
    """Saved data couldn't be read or written."""


@dataclass(frozen=True)
class Identity:
    mode: str  # local | guest | account | cloud
    user_id: str = ""  # hashed sign-in ID ("" unless signed in)
    email: str = ""
    name: str = ""

    @property
    def signed_in(self) -> bool:
        return bool(self.user_id)

    @property
    def key(self) -> str:
        """Changes whenever whose data is showing changes (sign in / sign out)."""
        return f"{self.mode}:{self.user_id}"


# ---------------------------------------------------------------------------
# Secrets and identity
# ---------------------------------------------------------------------------


def _secrets():
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return {}


def _section(name: str) -> dict:
    try:
        s = _secrets()
        return dict(s[name]) if name in s else {}
    except Exception:  # no secrets.toml at all
        return {}


def auth_configured() -> bool:
    a = _section("auth")
    return bool(a.get("client_id") or any(isinstance(v, dict) and v.get("client_id") for v in a.values()))


def supabase_config() -> tuple[str, str] | None:
    """[supabase] url/key from Streamlit secrets, else SUPABASE_URL / SUPABASE_KEY from the environment
    (the daily alerts job runs outside Streamlit)."""
    import os

    s = _section("supabase")
    url = str(s.get("url") or os.environ.get("SUPABASE_URL", "")).rstrip("/")
    key = str(s.get("key") or os.environ.get("SUPABASE_KEY", ""))
    return (url, key) if url and key else None


def hash_id(issuer: str, sub: str) -> str:
    return hashlib.sha256(f"{issuer}|{sub}".encode()).hexdigest()[:32]


def identity() -> Identity:
    if not auth_configured():
        return Identity("local")
    try:
        import streamlit as st

        u = st.user
        logged_in = bool(getattr(u, "is_logged_in", False))
        sub = str(u.get("sub") or "") if logged_in else ""
    except Exception:
        logged_in, sub, u = False, "", {}
    if not (logged_in and sub):
        return Identity("guest")
    uid = hash_id(str(u.get("iss") or ""), sub)
    return Identity("cloud" if supabase_config() else "account", uid, str(u.get("email") or ""),
                    str(u.get("name") or u.get("given_name") or ""))


# ---------------------------------------------------------------------------
# Local JSON files
# ---------------------------------------------------------------------------


def _local_path(name: str, who: Identity) -> Path:
    if who.mode == "account" and name in USER_LISTS:
        return DATA_DIR / "users" / who.user_id / f"{name}.json"
    legacy = Path(f"{name}.json")  # old root-level files from early versions
    return legacy if legacy.exists() else DATA_DIR / f"{name}.json"


def _read_file(p: Path) -> list:
    try:
        d = json.loads(p.read_text())
        return d if isinstance(d, list) else []
    except FileNotFoundError:
        return []
    except Exception:
        return []


def _write_file(p: Path, rows: list) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, indent=1, default=str))
    tmp.replace(p)


# ---------------------------------------------------------------------------
# Supabase (PostgREST over HTTPS; the secret key never leaves the server)
# ---------------------------------------------------------------------------


def _headers(key: str) -> dict:
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _cloud_read(name: str, uid: str) -> list:
    url, key = supabase_config()
    try:
        r = requests.get(f"{url}/rest/v1/{TABLE}", headers=_headers(key), timeout=TIMEOUT,
                         params={"user_id": f"eq.{uid}", "name": f"eq.{name}", "select": "data"})
        r.raise_for_status()
        rows = r.json()
    except Exception as e:
        raise StoreError(f"couldn't load your saved {name.replace('_', ' ')} ({e.__class__.__name__})") from e
    d = rows[0].get("data") if rows else []
    return d if isinstance(d, list) else []


def _cloud_write(name: str, uid: str, rows: list) -> None:
    url, key = supabase_config()
    body = [{"user_id": uid, "name": name, "data": json.loads(json.dumps(rows, default=str))}]
    try:
        r = requests.post(f"{url}/rest/v1/{TABLE}", headers={**_headers(key), "Prefer": "resolution=merge-duplicates"},
                          params={"on_conflict": "user_id,name"}, json=body, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        raise StoreError(f"couldn't save your {name.replace('_', ' ')} ({e.__class__.__name__})") from e


def cloud_all(name: str) -> dict:
    """{user_id: list} for every user who saved ``name`` (for the daily alerts job). Raises StoreError."""
    url, key = supabase_config()
    try:
        r = requests.get(f"{url}/rest/v1/{TABLE}", headers=_headers(key), timeout=TIMEOUT * 3,
                         params={"name": f"eq.{name}", "select": "user_id,data"})
        r.raise_for_status()
        return {row["user_id"]: row.get("data") or [] for row in r.json()}
    except Exception as e:
        raise StoreError(f"couldn't list saved {name} ({e.__class__.__name__})") from e


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load(name: str, who: Identity | None = None) -> list:
    """The saved list, or [] when there is none. Raises StoreError only when cloud storage can't be reached
    (so the caller can avoid overwriting good data with an empty list)."""
    who = who or identity()
    if name in USER_LISTS:
        if who.mode == "guest":
            return []
        if who.mode == "cloud":
            return _cloud_read(name, who.user_id)
    return _read_file(_local_path(name, who))


def save(name: str, rows: list, who: Identity | None = None) -> bool:
    """Save a list. Returns False for a guest's personal lists (kept for this visit only). Raises StoreError."""
    who = who or identity()
    if name in USER_LISTS:
        if who.mode == "guest":
            return False
        if who.mode == "cloud":
            _cloud_write(name, who.user_id, rows)
            return True
    try:
        _write_file(_local_path(name, who), rows)
    except Exception as e:
        raise StoreError(f"couldn't save {name.replace('_', ' ')} ({e})") from e
    return True


SETUP_SQL = f"""
create table if not exists public.{TABLE} (
  user_id    text        not null,
  name       text        not null,
  data       jsonb       not null default '[]'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, name)
);
-- Row level security on with no policies: the public (anon/publishable) key can read and write nothing.
-- Only SharkFin's server, holding the secret key, can reach this table.
alter table public.{TABLE} enable row level security;
grant select, insert, update on public.{TABLE} to service_role;
"""
