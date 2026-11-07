"""Linked brokerages through SnapTrade: signing, combining, and the web API.

No network: SnapTrade and Alpaca are replaced by fakes.
"""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import importlib

from hone.market_data.brokers import snaptrade as snap
from hone.web.app import create_app

# `hone.web` re-exports a FastAPI object called `app`, which shadows the
# module of the same name, so fetch the module itself.
web = importlib.import_module("hone.web.app")

#: The real client, kept before any test swaps in FakeSnap.
REAL_CLIENT = snap.SnapTradeClient


# --------------------------------------------------------------- signing
class TestSignature:
    # Reference values produced by running SnapTrade's own SDK function
    # (snaptrade_client/request_after_hook.py: compute_request_signature)
    # on these inputs. If these drift, real requests will get 401s.
    def test_matches_sdk_with_body(self):
        sig = snap._signature(
            "test-consumer-key",
            "/snapTrade/registerUser",
            "clientId=HONE-TEST&timestamp=1700000000",
            {"userId": "hone-abc"},
        )
        assert sig == "Zb68yfeqkZqq8AACCUbKA3GEAnwbi7lMiy87MGX659Y="

    def test_matches_sdk_without_body(self):
        sig = snap._signature(
            "test-consumer-key",
            "/accounts",
            "clientId=HONE-TEST&timestamp=1700000000&userId=hone-abc&userSecret=s3cret",
            None,
        )
        assert sig == "u55LgCjn/SWJ9aYs4Frkv/e10HeSKYq4PZ/HhQIYlUs="


class _Resp:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload
        self.text = json.dumps(payload)
        self.content = self.text.encode() if payload is not None else b""

    def json(self):
        return self._payload


class _Session:
    """Records requests; answers from a {(method, path): payload} table."""

    def __init__(self, table):
        self.table = table
        self.calls = []

    def request(self, method, url, headers=None, data=None, timeout=None):
        self.calls.append((method, url, headers, data))
        path = urlparse(url).path
        status, payload = self.table.get((method, path), (404, {"detail": "nope"}))
        return _Resp(status, payload)


class TestClientRequests:
    def test_request_is_signed_over_what_is_sent(self):
        session = _Session({("POST", "/snapTrade/registerUser"): (200, {"userId": "u", "userSecret": "sec"})})
        c = snap.SnapTradeClient("CID", "CKEY", session=session)
        assert c.register_user("u") == "sec"
        method, url, headers, data = session.calls[0]
        parsed = urlparse(url)
        q = parse_qs(parsed.query)
        assert q["clientId"] == ["CID"] and "timestamp" in q
        # Re-derive the signature from exactly what went over the wire.
        expected = snap._signature("CKEY", parsed.path, parsed.query, json.loads(data))
        assert headers["Signature"] == expected

    def test_user_credentials_go_in_the_query(self):
        session = _Session({("GET", "/accounts"): (200, [])})
        snap.SnapTradeClient("CID", "CKEY", session=session).list_accounts("u1", "s1")
        q = parse_qs(urlparse(session.calls[0][1]).query)
        assert q["userId"] == ["u1"] and q["userSecret"] == ["s1"]

    def test_login_asks_for_read_only(self):
        session = _Session({("POST", "/snapTrade/login"): (200, {"redirectURI": "https://portal"})})
        url = snap.SnapTradeClient("CID", "CKEY", session=session).login_link(
            "u", "s", redirect_url="https://me/back"
        )
        assert url == "https://portal"
        body = json.loads(session.calls[0][3])
        assert body["connectionType"] == "read"
        assert body["customRedirect"] == "https://me/back"

    def test_errors_carry_status(self):
        session = _Session({("GET", "/accounts"): (401, {"detail": "bad secret", "code": "1076"})})
        with pytest.raises(snap.SnapTradeError) as e:
            snap.SnapTradeClient("CID", "CKEY", session=session).list_accounts("u", "x")
        assert e.value.status == 401 and e.value.code == "1076"

    def test_missing_keys_is_a_clear_error(self, monkeypatch):
        monkeypatch.delenv("SNAPTRADE_CLIENT_ID", raising=False)
        monkeypatch.delenv("SNAPTRADE_CONSUMER_KEY", raising=False)
        assert not snap.configured()
        with pytest.raises(snap.SnapTradeError, match="SNAPTRADE_CLIENT_ID"):
            snap.SnapTradeClient()


# -------------------------------------------------------------- combining
def _pos(symbol, units, price, kind="stock", currency="USD", **extra):
    return {
        "instrument": {"kind": kind, "id": symbol, "symbol": symbol, "raw_symbol": symbol},
        "units": str(units),
        "price": str(price),
        "currency": currency,
        **extra,
    }


ACCOUNTS = [
    {"id": "a1", "name": "Brokerage", "number": "12341234", "institution_name": "Schwab",
     "brokerage_authorization": "c1", "account_category": "INVESTMENT", "balance": {"total": {"amount": 9000, "currency": "USD"}}},
    {"id": "a2", "name": "Roth IRA", "number": "99996789", "institution_name": "Fidelity",
     "brokerage_authorization": "c2", "balance": {"total": {"amount": 4000, "currency": "USD"}}},
    {"id": "bank", "name": "Checking", "number": "5555", "institution_name": "Fidelity",
     "brokerage_authorization": "c2", "account_category": "DEPOSIT"},
]
POSITIONS = {
    "a1": [
        _pos("AAPL", 10, 200),
        _pos("BRK-B", 2, 400),
        _pos("SPAXX", 1000, 1, kind="mutualfund", cash_equivalent=True),
        _pos("AAPL  250117C00200000", 1, 5, kind="option"),
        _pos("VAB.TO", 10, 25, currency="CAD"),
        _pos("BTC", 0.1, 60000, kind="crypto"),
    ],
    "a2": [_pos("AAPL", 5, 200), _pos("MSFT", 4, 500), _pos("FXAIX", 3, 200, kind="mutualfund")],
    "bank": [_pos("AAPL", 999, 200)],
}


class TestCombine:
    def test_same_ticker_at_two_brokers_is_one_holding(self):
        out = snap.combine_positions(ACCOUNTS, POSITIONS)
        aapl = next(h for h in out.holdings if h.symbol == "AAPL")
        assert aapl.market_value == pytest.approx(3000)  # 10*200 + 5*200
        assert aapl.qty == 15
        assert len(aapl.accounts) == 2

    def test_share_class_ticker_matches_price_source(self):
        out = snap.combine_positions(ACCOUNTS, POSITIONS)
        assert "BRK.B" in {h.symbol for h in out.holdings}

    def test_bank_accounts_are_ignored(self):
        out = snap.combine_positions(ACCOUNTS, POSITIONS)
        assert [a["id"] for a in out.accounts] == ["a1", "a2"]
        assert next(h for h in out.holdings if h.symbol == "AAPL").market_value < 10_000

    def test_every_unmodelled_position_says_why(self):
        out = snap.combine_positions(ACCOUNTS, POSITIONS)
        reasons = {k.symbol: k.reason for k in out.skipped}
        assert "Cash" in reasons["SPAXX"]
        assert "Options" in reasons["AAPL  250117C00200000"]
        assert "CAD" in reasons["VAB.TO"]
        assert "Crypto product" in reasons["BTC"]
        assert "Mutual funds" in reasons["FXAIX"]
        assert {h.symbol for h in out.holdings} == {"AAPL", "BRK.B", "MSFT"}

    def test_account_label_never_shows_full_number(self):
        assert snap.account_label(ACCOUNTS[0]) == "Schwab · Brokerage ••1234"

    def test_crypto_product_takes_only_coins(self):
        accounts = [{"id": "cb", "name": "Coinbase", "number": "x", "institution_name": "Coinbase"}]
        positions = {"cb": [_pos("BTC", 0.5, 60000, kind="crypto"), _pos("USDC", 500, 1, kind="crypto"), _pos("AAPL", 1, 200)]}
        out = snap.combine_positions(accounts, positions, crypto=True)
        assert [h.symbol for h in out.holdings] == ["BTC/USD"]
        reasons = {k.symbol: k.reason for k in out.skipped}
        assert "Stablecoin" in reasons["USDC"] and "Stocks product" in reasons["AAPL"]


# --------------------------------------------------------------- web API
LINK = {"user_id": "hone-local-0123456789abcdef", "user_secret": "s3cret"}


class FakeSnap:
    """Stands in for SnapTradeClient inside the web app."""

    registered: list[str] = []
    deleted: list[str] = []
    removed: list[str] = []
    last_redirect: str | None = None
    existing: set[str] = set()

    def __init__(self, *a, **k):
        self.client_id = "CID"

    def _auth(self, user_secret):
        if user_secret != "s3cret":
            raise snap.SnapTradeError("bad secret", status=401)

    def register_user(self, user_id):
        if user_id in FakeSnap.existing:
            raise snap.SnapTradeError("exists", status=400)
        FakeSnap.registered.append(user_id)
        return "s3cret"

    def delete_user(self, user_id):
        FakeSnap.deleted.append(user_id)
        FakeSnap.existing.discard(user_id)

    def login_link(self, user_id, user_secret, redirect_url=None, broker=None, reconnect=None):
        self._auth(user_secret)
        FakeSnap.last_redirect = redirect_url
        return "https://portal.example/connect"

    def list_connections(self, user_id, user_secret):
        self._auth(user_secret)
        return [{"id": "c1", "brokerage": {"display_name": "Schwab"}, "disabled": False},
                {"id": "c2", "brokerage": {"display_name": "Fidelity"}, "disabled": True}]

    def remove_connection(self, user_id, user_secret, connection_id):
        self._auth(user_secret)
        FakeSnap.removed.append(connection_id)

    def list_accounts(self, user_id, user_secret):
        self._auth(user_secret)
        return ACCOUNTS

    def account_positions(self, user_id, user_secret, account_id):
        self._auth(user_secret)
        extra = [_pos("ZZZZ", 1, 50)] if account_id == "a2" else []  # no price history
        return POSITIONS.get(account_id, []) + extra


class FakeAlpaca:
    """Market data only: random-walk closes for a fixed set of tickers."""

    def __init__(self, api_key=None, secret_key=None, **k):
        self.api_key = api_key

    def get_bars(self, symbols, start, **k):
        rng = np.random.default_rng(7)
        idx = pd.bdate_range(end="2026-10-30", periods=700)
        known = {"AAPL", "MSFT", "BRK.B", "SPY", "TSLA", "NVDA"}
        data = {
            sym: 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, len(idx))))
            for sym in symbols if sym in known
        }
        return pd.DataFrame(data, index=idx).reindex(columns=list(symbols))

    def get_option_chain(self, *a, **k):
        raise web.AlpacaError("no options in tests")


@pytest.fixture
def broker_client(monkeypatch):
    for v in ("HONE_PUBLIC", "ALPACA_API_KEY", "ALPACA_SECRET_KEY", "APCA_API_KEY_ID", "APCA_API_SECRET_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("SNAPTRADE_CLIENT_ID", "CID")
    monkeypatch.setenv("SNAPTRADE_CONSUMER_KEY", "CKEY")
    monkeypatch.setenv("ALPACA_DATA_API_KEY", "data-key")
    monkeypatch.setenv("ALPACA_DATA_SECRET_KEY", "data-secret")
    monkeypatch.setattr(web.snap, "SnapTradeClient", FakeSnap)
    monkeypatch.setattr(web, "AlpacaClient", FakeAlpaca)
    snap._cache.clear()
    FakeSnap.registered, FakeSnap.deleted, FakeSnap.removed = [], [], []
    FakeSnap.existing = set()
    return TestClient(create_app())


def _market(link=LINK):
    return {"demo": False, "credentials": {"broker": link}}


class TestWebPortfolio:
    def test_config_reports_brokers(self, broker_client):
        cfg = broker_client.get("/api/config").json()
        assert cfg["brokers"] == {"enabled": True, "requires_sign_in": False}

    def test_portfolio_combines_every_account(self, broker_client):
        r = broker_client.post("/api/portfolio", json=_market())
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["source"] == "brokerages"
        assert {p["symbol"] for p in body["positions"]} == {"AAPL", "BRK.B", "MSFT"}
        assert sum(p["weight"] for p in body["positions"]) == pytest.approx(1.0)
        assert body["portfolio_value"] == pytest.approx(3000 + 800 + 2000)
        assert len(body["accounts"]) == 2
        skipped = {k["symbol"]: k["reason"] for k in body["skipped"]}
        assert "price history" in skipped["ZZZZ"]  # held, but no prices
        assert "SPAXX" in skipped

    def test_optimize_runs_on_linked_holdings(self, broker_client):
        body = {**_market(), "gamma": 3.0, "views": [{"ticker": "NVDA", "target_price": 200, "confidence": 0.6, "horizon_days": 180}]}
        r = broker_client.post("/api/optimize", json=body)
        assert r.status_code == 200, r.text
        assert "NVDA" in {w["symbol"] for w in r.json()["weights"]}

    def test_bad_secret_tells_user_to_reconnect(self, broker_client):
        r = broker_client.post("/api/portfolio", json=_market({**LINK, "user_secret": "wrong"}))
        assert r.status_code == 401 and "Reconnect" in r.json()["detail"]

    def test_no_price_source_on_public_server_is_explained(self, broker_client, monkeypatch):
        monkeypatch.setenv("HONE_PUBLIC", "1")
        monkeypatch.delenv("ALPACA_DATA_API_KEY")
        r = broker_client.post("/api/portfolio", json=_market())
        assert r.status_code == 503 and "price-history" in r.json()["detail"]


class TestWebLinking:
    def test_connect_private_server_without_sign_in(self, broker_client):
        r = broker_client.post("/api/broker/connect", json={
            "local_id": "0123456789abcdef", "redirect_url": "http://testserver/stocks/app/settings",
        })
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["redirect_url"] == "https://portal.example/connect"
        assert out["link"] == {**LINK, "account_ids": None}
        assert FakeSnap.registered == [LINK["user_id"]]
        assert FakeSnap.last_redirect == "http://testserver/stocks/app/settings"

    def test_connect_reuses_an_existing_link(self, broker_client):
        r = broker_client.post("/api/broker/connect", json={"link": LINK})
        assert r.status_code == 200 and FakeSnap.registered == []

    def test_redirect_to_another_site_is_dropped(self, broker_client):
        broker_client.post("/api/broker/connect", json={"link": LINK, "redirect_url": "https://evil.example/"})
        assert FakeSnap.last_redirect is None

    def test_public_server_requires_sign_in(self, broker_client, monkeypatch):
        monkeypatch.setenv("HONE_PUBLIC", "1")
        r = broker_client.post("/api/broker/connect", json={"local_id": "0123456789abcdef"})
        assert r.status_code == 401 and "Sign in" in r.json()["detail"]
        assert FakeSnap.registered == []

    def test_public_server_signed_in_user_gets_their_own_id(self, broker_client, monkeypatch):
        monkeypatch.setenv("HONE_PUBLIC", "1")
        monkeypatch.setattr(web, "_signed_in_user", lambda request: "uuid-1")
        r = broker_client.post("/api/broker/connect", json={})
        assert r.status_code == 200
        assert r.json()["link"]["user_id"] == "hone-uuid-1"
        # ...and can't use somebody else's link.
        r = broker_client.post("/api/broker/accounts", json={"link": LINK})
        assert r.status_code == 403

    def test_lost_secret_needs_explicit_reset(self, broker_client):
        FakeSnap.existing = {LINK["user_id"]}
        r = broker_client.post("/api/broker/connect", json={"local_id": "0123456789abcdef"})
        assert r.status_code == 409 and FakeSnap.deleted == []
        r = broker_client.post("/api/broker/connect", json={"local_id": "0123456789abcdef", "reset": True})
        assert r.status_code == 200 and FakeSnap.deleted == [LINK["user_id"]]

    def test_accounts_lists_connections_and_accounts(self, broker_client):
        r = broker_client.post("/api/broker/accounts", json={"link": LINK})
        assert r.status_code == 200, r.text
        body = r.json()
        assert [c["brokerage"] for c in body["connections"]] == ["Schwab", "Fidelity"]
        assert body["connections"][1]["disabled"] is True
        bank = next(a for a in body["accounts"] if a["id"] == "bank")
        assert bank["investment"] is False
        assert body["accounts"][0]["label"] == "Schwab · Brokerage ••1234"

    def test_disconnect_and_unlink(self, broker_client):
        assert broker_client.post("/api/broker/disconnect", json={"link": LINK, "connection_id": "c1"}).status_code == 200
        assert FakeSnap.removed == ["c1"]
        # Unlink must prove it holds the secret before deleting anything.
        bad = broker_client.post("/api/broker/unlink", json={"link": {**LINK, "user_secret": "nope"}})
        assert bad.status_code == 401 and FakeSnap.deleted == []
        ok = broker_client.post("/api/broker/unlink", json={"link": LINK})
        assert ok.status_code == 200 and FakeSnap.deleted == [LINK["user_id"]]

    def test_not_configured(self, broker_client, monkeypatch):
        monkeypatch.setattr(web.snap, "SnapTradeClient", REAL_CLIENT)
        monkeypatch.delenv("SNAPTRADE_CLIENT_ID")
        r = broker_client.post("/api/broker/connect", json={"local_id": "0123456789abcdef"})
        assert r.status_code == 503 and "SNAPTRADE_CLIENT_ID" in r.json()["detail"]


def test_choosing_brokers_with_nothing_linked_is_explained(broker_client):
    r = broker_client.post("/api/portfolio", json={"demo": False, "credentials": {"source": "brokers"}})
    assert r.status_code == 400 and "No brokerages are linked" in r.json()["detail"]


def test_price_lookup_for_a_stock_not_held(broker_client):
    """A thesis on a stock you don't own still gets a price (NVDA isn't held)."""
    r = broker_client.post("/api/compile-view", json={**_market(), "text": "NVDA", "offline": True, "with_prices": True})
    assert r.status_code == 200, r.text
    v = r.json()["views"][0]
    assert v["ticker"] == "NVDA" and v["live_price"] and v["tradeable"] is not False


def test_price_lookup_for_unknown_ticker_is_not_tradeable(broker_client):
    r = broker_client.post("/api/compile-view", json={**_market(), "text": "QQQZ", "offline": True, "with_prices": True})
    assert r.status_code == 200
    assert "QQQZ" not in r.json()["universe"]


def test_optimize_and_portfolio_agree_on_value(broker_client):
    """Unpriced holdings (ZZZZ) count in neither figure."""
    port = broker_client.post("/api/portfolio", json=_market()).json()
    opt = broker_client.post("/api/optimize", json={**_market(), "gamma": 3.0, "views": []}).json()
    assert opt["hedge_plan"]["portfolio_value"] == pytest.approx(port["portfolio_value"])


def test_keys_can_use_the_cloud_environment_names(monkeypatch):
    """SnapTrade_ClientID / SnapTrade_API (as saved in the cloud environment)."""
    for v in ("SNAPTRADE_CLIENT_ID", "SNAPTRADE_CONSUMER_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("SnapTrade_ClientID", "cid")
    monkeypatch.setenv("SnapTrade_API", "ckey")
    assert snap.configured()
    c = REAL_CLIENT()
    assert (c.client_id, c.consumer_key) == ("cid", "ckey")
