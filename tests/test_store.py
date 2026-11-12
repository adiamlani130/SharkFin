"""Per-user storage: guests never write the shared file, signed-in users get their own data, and a cloud outage
can't overwrite saved data with an empty list."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sharkfin import store
from sharkfin.store import Identity

ROOT = Path(__file__).resolve().parents[1]
AUTH = {"redirect_uri": "http://localhost:8501/oauth2callback", "cookie_secret": "x" * 32, "client_id": "id",
        "client_secret": "secret", "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration"}


@pytest.fixture(autouse=True)
def tmp_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)


def test_local_mode_keeps_old_files():
    who = Identity("local")
    store.save("portfolio", [{"symbol": "AAPL"}], who)
    assert Path(".sharkfin/portfolio.json").exists()
    assert store.load("portfolio", who) == [{"symbol": "AAPL"}]


def test_guest_never_touches_disk():
    who = Identity("guest")
    assert store.save("portfolio", [{"symbol": "AAPL"}], who) is False
    assert store.load("portfolio", who) == []
    assert not Path(".sharkfin").exists()
    # app-wide lists (the signal log) still save for everyone
    assert store.save("leader_dip_log", [{"t": 1}], who)
    assert store.load("leader_dip_log", who) == [{"t": 1}]


def test_accounts_are_separate():
    a, b = Identity("account", "a" * 32), Identity("account", "b" * 32)
    store.save("portfolio", [{"symbol": "AAPL"}], a)
    store.save("portfolio", [{"symbol": "TSLA"}], b)
    assert store.load("portfolio", a) == [{"symbol": "AAPL"}]
    assert store.load("portfolio", b) == [{"symbol": "TSLA"}]
    assert store.load("portfolio", Identity("local")) == []


def test_hash_id_is_stable_and_hides_sub():
    h = store.hash_id("https://accounts.google.com", "12345")
    assert h == store.hash_id("https://accounts.google.com", "12345") and "12345" not in h and len(h) == 32
    assert h != store.hash_id("https://accounts.google.com", "12346")


class FakeResp:
    def __init__(self, data=None, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_cloud_round_trip(monkeypatch):
    monkeypatch.setattr(store, "supabase_config", lambda: ("https://x.supabase.co", "sb_secret_k"))
    db = {}

    def post(url, headers, params, json, timeout):
        assert headers["apikey"] == "sb_secret_k" and params == {"on_conflict": "user_id,name"}
        assert "merge-duplicates" in headers["Prefer"]
        for row in json:
            db[(row["user_id"], row["name"])] = row["data"]
        return FakeResp()

    def get(url, headers, params, timeout):
        uid, name = params["user_id"][3:], params["name"][3:]
        return FakeResp([{"data": db[(uid, name)]}] if (uid, name) in db else [])

    monkeypatch.setattr(store.requests, "post", post)
    monkeypatch.setattr(store.requests, "get", get)
    me = Identity("cloud", "u" * 32)
    assert store.load("watchlist", me) == []
    store.save("watchlist", ["NVDA"], me)
    assert store.load("watchlist", me) == ["NVDA"]
    assert store.load("watchlist", Identity("cloud", "v" * 32)) == []
    assert not Path(".sharkfin").exists()


def test_cloud_outage_raises(monkeypatch):
    monkeypatch.setattr(store, "supabase_config", lambda: ("https://x.supabase.co", "k"))
    monkeypatch.setattr(store.requests, "get", lambda *a, **k: FakeResp(status=503))
    with pytest.raises(store.StoreError):
        store.load("portfolio", Identity("cloud", "u" * 32))


GUEST_APP = """
import streamlit as st
from sharkfin import ui
ui.setup()
st.session_state.portfolio.append({"symbol": "AAPL", "shares": 1, "buy_price": 1})
ui.save_state()
with st.sidebar:
    ui.account_box()
"""


def test_guest_app_shows_sign_in_and_writes_nothing(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    at = AppTest.from_string(GUEST_APP, default_timeout=60)
    at.secrets["auth"] = AUTH
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert any(b.label == "Sign in with Google" for b in at.sidebar.button)
    assert not Path(".sharkfin").exists()


def test_outage_blocks_saving(monkeypatch):
    """If the saved portfolio can't be loaded, saving is refused for the visit instead of writing []."""
    import streamlit as st

    from sharkfin import ui

    me = Identity("cloud", "u" * 32)
    monkeypatch.setattr(store, "identity", lambda: me)
    monkeypatch.setattr(store, "supabase_config", lambda: ("https://x.supabase.co", "k"))
    monkeypatch.setattr(store.requests, "get", lambda *a, **k: FakeResp(status=503))
    posts = []
    monkeypatch.setattr(store.requests, "post", lambda *a, **k: posts.append(k) or FakeResp())
    st.session_state.clear()
    ui.init_state()
    assert st.session_state.portfolio == []
    ui.save_state()
    assert posts == []
    st.session_state.clear()


def test_signed_in_app_uses_own_files(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    me = Identity("account", "a" * 32, "adi@example.com")
    monkeypatch.setattr(store, "identity", lambda: me)
    at = AppTest.from_string(GUEST_APP, default_timeout=60)
    at.secrets["auth"] = AUTH
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert any(b.label == "Sign out" for b in at.sidebar.button)
    assert store.load("portfolio", me)[0]["symbol"] == "AAPL"
    assert not Path(".sharkfin/portfolio.json").exists()
