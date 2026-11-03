"""Access to every market: the full Alpaca asset list, pricing any picked
symbol, and browsing every open Kalshi event. No network: Alpaca and Kalshi
are replaced by canned responses throughout."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from hone.market_data import asset_directory as ad
from hone.market_data.alpaca_client import AlpacaClient, AlpacaError
from hone.prediction import kalshi_browse as kb
from hone.prediction.kalshi_client import KalshiClient, KalshiError
from hone.web.app import _symbols_to_price, create_app

# `hone.web.app` the *attribute* is the FastAPI instance (hone/web/__init__.py
# exports it), so patch the module object itself.
web_app = sys.modules["hone.web.app"]


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def _fresh_caches():
    ad.clear_cache()
    kb.reset_state()
    yield
    ad.clear_cache()
    kb.reset_state()


# --------------------------------------------------------------- fakes
class _AlpacaResp:
    def __init__(self, payload, status_code=200):
        self._payload, self.status_code, self.text = payload, status_code, str(payload)

    def json(self):
        return self._payload


class _AlpacaSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


class _KalshiResp:
    def __init__(self, payload, status_code=200):
        self._payload, self.status_code, self.text = payload, status_code, str(payload)

    def json(self):
        return self._payload


class _KalshiSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params or {})))
        return self.responses.pop(0)


RAW_ASSETS = [
    {"symbol": "MSFT", "name": "Microsoft Corporation Common Stock", "exchange": "NASDAQ",
     "status": "active", "tradable": True},
    {"symbol": "AAPL", "name": "Apple Inc. Common Stock", "exchange": "NASDAQ",
     "status": "active", "tradable": True},
    {"symbol": "PINKY", "name": "Some OTC Co", "exchange": "OTC", "status": "active", "tradable": True},
    {"symbol": "HALT", "name": "Halted Inc", "exchange": "NYSE", "status": "active", "tradable": False},
    {"symbol": "aapl", "name": "duplicate", "exchange": "NASDAQ", "status": "active", "tradable": True},
]


def _event(ticker, title, category, series=None, sub=""):
    return {"event_ticker": ticker, "series_ticker": series or ticker.split("-")[0],
            "title": title, "sub_title": sub, "category": category}


EVENTS_P1 = [
    _event("KXFED-26DEC", "Fed decision in December", "Economics"),
    _event("KXNBA-26NOV05LALBOS", "Lakers vs Celtics", "Sports"),
]
EVENTS_P2 = [
    _event("KXBTCD-26NOV0317", "Bitcoin price today at 5pm", "Crypto"),
    _event("KXFEDCHAIR-27", "Who will be the next Fed chair?", "Politics"),
    _event("KXFED-26DEC", "duplicate of page 1", "Economics"),
]

RAW_MARKET = {
    "ticker": "KXFED-26DEC-T4.00", "event_ticker": "KXFED-26DEC",
    "title": "Fed funds above 4.00% after December?", "yes_sub_title": "Above 4.00%",
    "status": "active", "close_time": "2026-12-10T19:00:00Z",
    "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.42", "no_bid_dollars": "0.58",
    "no_ask_dollars": "0.60", "last_price_dollars": "0.41", "volume_fp": "900",
    "open_interest_fp": "100", "floor_strike": 4.0, "strike_type": "greater",
    "rules_primary": "Resolves Yes if ...",
}


# ===================================================== Alpaca asset list
class TestAssetDirectory:
    def test_list_assets_call_shape(self):
        sess = _AlpacaSession([_AlpacaResp(RAW_ASSETS)])
        out = AlpacaClient(api_key="k", secret_key="s", session=sess).list_assets("crypto")
        assert out == RAW_ASSETS
        method, url, kwargs = sess.calls[0]
        assert method == "GET" and url.endswith("/v2/assets")
        assert kwargs["params"] == {"status": "active", "asset_class": "crypto"}

    def test_build_directory_filters_trims_dedupes_and_sorts(self):
        rows = ad.build_directory(RAW_ASSETS)
        assert [r[0] for r in rows] == ["AAPL", "MSFT"]  # no OTC, no untradable, no dupe
        assert rows[0] == ["AAPL", "Apple Inc.", "NASDAQ"]

    def test_names_lose_share_class_boilerplate(self):
        assert ad.tidy_name("Palantir Technologies Inc. Class A Common Stock") == "Palantir Technologies Inc."
        assert ad.tidy_name("Taiwan Semiconductor Manufacturing Company Ltd. American Depositary Shares "
                            "(Each representing 5 ordinary shares)") == "Taiwan Semiconductor Manufacturing Company Ltd."
        assert ad.tidy_name("SPDR S&P 500 ETF Trust") == "SPDR S&P 500 ETF Trust"

    def test_cache_is_reused_until_it_expires(self):
        calls = []

        class Fake:
            def list_assets(self, cls):
                calls.append(cls)
                return RAW_ASSETS

        clock = [1000.0]
        make = lambda: Fake()  # noqa: E731
        first = ad.cached_directory("us_equity", make, now=lambda: clock[0])
        ad.cached_directory("us_equity", lambda: pytest.fail("cache miss"), now=lambda: clock[0])
        assert calls == ["us_equity"] and len(first["assets"]) == 2
        clock[0] += ad.CACHE_TTL_SECONDS + 1
        ad.cached_directory("us_equity", make, now=lambda: clock[0])
        assert calls == ["us_equity", "us_equity"]

    def test_endpoint_demo_is_the_sample_universe(self, client):
        r = client.post("/api/assets?asset_class=stocks", json={"demo": True})
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "demo" and body["count"] == len(body["assets"]) == 5
        r = client.post("/api/assets?asset_class=crypto", json={"demo": True})
        assert "BTC/USD" in [a[0] for a in r.json()["assets"]]

    def test_endpoint_live_serves_every_alpaca_asset(self, client, monkeypatch):
        class Fake:
            def list_assets(self, cls):
                assert cls == "us_equity"
                return RAW_ASSETS

        monkeypatch.setattr(web_app, "_client", lambda creds: Fake())
        r = client.post("/api/assets?asset_class=stocks", json={"demo": False})
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "alpaca" and body["count"] == 2
        assert body["assets"][1] == ["MSFT", "Microsoft Corporation", "NASDAQ"]

    def test_endpoint_live_alpaca_error_is_502(self, client, monkeypatch):
        class Broken:
            def list_assets(self, cls):
                raise AlpacaError("down")

        monkeypatch.setattr(web_app, "_client", lambda creds: Broken())
        assert client.post("/api/assets?asset_class=stocks", json={}).status_code == 502

    def test_endpoint_rejects_prediction_markets(self, client):
        assert client.post("/api/assets?asset_class=prediction", json={"demo": True}).status_code == 400


# =================================================== pricing any symbol
def _fake_prices(symbols):
    """Prices for held AAPL/SPY plus whatever was asked; BOGUS has no bars."""
    idx = pd.date_range("2026-09-01", periods=40, freq="D")
    cols = sorted({"AAPL", "SPY", *symbols})
    data = {c: (np.full(40, np.nan) if c == "BOGUS" else np.linspace(100, 120, 40)) for c in cols}
    return pd.DataFrame(data, index=idx)


class TestPricingAnySymbol:
    def test_symbols_to_price_keeps_well_formed_symbols(self):
        out = _symbols_to_price("I think NVDA goes up", ["amzn", "BTC/USD", "not a ticker!", "AMZN"])
        assert out[:2] == ["AMZN", "BTC/USD"] and "NVDA" in out
        assert "NOT A TICKER!" not in out

    def test_picked_symbol_is_priced_and_tradeable(self, client, monkeypatch):
        seen = []

        def fake_load(demo, creds, extra, proxy, lookback):
            seen.append(list(extra))
            return _fake_prices(extra), pd.Series({"AAPL": 0.6, "SPY": 0.4})

        monkeypatch.setattr(web_app, "_load_market", fake_load)
        r = client.post("/api/compile-view?asset_class=stocks",
                        json={"text": "COST", "offline": True, "symbols": ["COST"]})
        assert r.status_code == 200
        v = r.json()["views"][0]
        assert v["ticker"] == "COST" and v["tradeable"] is True and v["live_price"] == pytest.approx(120)
        assert "COST" in seen[0]

    def test_symbol_without_bars_is_not_tradeable(self, client, monkeypatch):
        monkeypatch.setattr(web_app, "_load_market",
                            lambda d, c, extra, p, lb: (_fake_prices(extra), pd.Series({"AAPL": 1.0})))
        r = client.post("/api/compile-view?asset_class=stocks",
                        json={"text": "BOGUS", "offline": True, "symbols": ["BOGUS"]})
        body = r.json()
        assert body["views"][0]["tradeable"] is False
        assert "BOGUS" not in body["universe"]

    def test_rejected_symbol_falls_back_to_holdings(self, client, monkeypatch):
        calls = []

        def fake_load(demo, creds, extra, proxy, lookback):
            calls.append(list(extra))
            if extra:
                raise AlpacaError("invalid symbol")
            return _fake_prices([]), pd.Series({"AAPL": 1.0})

        monkeypatch.setattr(web_app, "_load_market", fake_load)
        r = client.post("/api/compile-view?asset_class=stocks",
                        json={"text": "AAPL", "offline": True, "symbols": ["ZZZZ"]})
        assert r.status_code == 200
        assert calls == [["ZZZZ", "AAPL"], []]
        assert r.json()["views"][0]["tradeable"] is True


# ====================================================== Kalshi: client
class TestKalshiPaging:
    def test_events_page_passes_the_cursor(self):
        sess = _KalshiSession([_KalshiResp({"events": EVENTS_P1, "cursor": "abc"})])
        events, cursor = KalshiClient(session=sess).events_page(cursor="prev")
        assert len(events) == 2 and cursor == "abc"
        url, params = sess.calls[0]
        assert url.endswith("/events") and params == {"limit": 200, "status": "open", "cursor": "prev"}

    def test_last_page_has_no_cursor(self):
        sess = _KalshiSession([_KalshiResp({"events": [], "cursor": ""})])
        assert KalshiClient(session=sess).events_page() == ([], None)

    def test_event_markets_follows_the_cursor(self):
        sess = _KalshiSession([_KalshiResp({"markets": [RAW_MARKET], "cursor": "n"}),
                               _KalshiResp({"markets": [RAW_MARKET], "cursor": ""})])
        out = KalshiClient(session=sess).event_markets("KXFED-26DEC")
        assert len(out) == 2 and out[0]["yes_ask"] == pytest.approx(0.42)
        assert sess.calls[1][1]["cursor"] == "n"
        assert sess.calls[0][1]["event_ticker"] == "KXFED-26DEC"


# ======================================================= Kalshi: index
@pytest.fixture
def built_index(monkeypatch):
    """A live index of five events built from two fake pages."""
    monkeypatch.setattr(kb, "ensure_index", lambda: None)  # no background thread
    sess = _KalshiSession([_KalshiResp({"events": EVENTS_P1, "cursor": "p2"}),
                           _KalshiResp({"events": EVENTS_P2, "cursor": ""})])
    kb.build_index(KalshiClient(session=sess), pause=0)
    return sess


class TestKalshiIndex:
    def test_build_walks_every_page_and_dedupes(self, built_index):
        res = kb.search_events(live=True)
        assert res["source"] == "live" and res["complete"] is True
        assert res["indexed"] == 4 and res["total"] == 4
        assert len(built_index.calls) == 2

    def test_every_word_must_match(self, built_index):
        res = kb.search_events("fed chair", live=True)
        assert [e["event_ticker"] for e in res["events"]] == ["KXFEDCHAIR-27"]

    def test_ticker_match_ranks_first(self, built_index):
        res = kb.search_events("kxfed", live=True)
        assert [e["event_ticker"] for e in res["events"]][:2] == ["KXFED-26DEC", "KXFEDCHAIR-27"]

    def test_category_filter_keeps_counts_for_every_category(self, built_index):
        res = kb.search_events("fed", category="Politics", live=True)
        assert res["total"] == 1 and res["events"][0]["category"] == "Politics"
        counts = {c["name"]: c["count"] for c in res["categories"]}
        assert counts == {"Economics": 1, "Politics": 1}

    def test_paging(self, built_index):
        res = kb.search_events(offset=3, limit=2, live=True)
        assert res["total"] == 4 and len(res["events"]) == 1

    def test_curated_series_are_linked(self, built_index):
        ev = kb.search_events("KXFED-26DEC", live=True)["events"][0]
        assert ev["curated"]["industry"] == "housing"
        assert "_hay" not in ev

    def test_offline_index_is_the_snapshot(self):
        res = kb.search_events(live=False)
        assert res["source"] == "snapshot" and res["indexed"] > 0
        assert all(e["curated"] for e in res["events"])

    def test_empty_live_index_falls_back_to_snapshot(self, monkeypatch):
        monkeypatch.setattr(kb, "ensure_index", lambda: None)
        res = kb.search_events(live=True)
        assert res["source"] == "snapshot" and res["complete"] is False


# ===================================================== Kalshi: one event
class TestKalshiEvent:
    def test_live_event_is_fetched_once_then_cached(self, built_index):
        sess = _KalshiSession([_KalshiResp({"markets": [RAW_MARKET], "cursor": ""})])
        kc = KalshiClient(session=sess)
        out = kb.event_detail("KXFED-26DEC", live=True, client=kc)
        assert out["source"] == "live" and out["markets"][0]["ticker"] == "KXFED-26DEC-T4.00"
        assert out["event"]["title"] == "Fed decision in December"
        again = kb.event_detail("KXFED-26DEC", live=True, client=kc)  # no response left: must be cached
        assert again["markets"] == out["markets"]

    def test_bad_ticker_is_rejected(self):
        with pytest.raises(ValueError):
            kb.event_detail("../../etc", live=False)

    def test_kalshi_down_and_not_in_snapshot_raises(self, monkeypatch):
        monkeypatch.setattr(kb, "ensure_index", lambda: None)
        sess = _KalshiSession([_KalshiResp({"error": "boom"}, status_code=500)])
        with pytest.raises(KalshiError):
            kb.event_detail("KXNOPE-1", live=True, client=KalshiClient(session=sess))

    def test_endpoints_offline(self, client):
        r = client.get("/api/predict/browse?q=mortgage&live=false&asset_class=prediction")
        assert r.status_code == 200
        ev = r.json()["events"][0]
        r = client.get(f"/api/predict/event/{ev['event_ticker']}?live=false&asset_class=prediction")
        assert r.status_code == 200
        body = r.json()
        assert body["markets"] and body["event"]["curated"]["industry"] == "housing"
        vols = [m["volume"] for m in body["markets"]]
        assert vols == sorted(vols, reverse=True)
        assert client.get("/api/predict/event/bad!ticker?live=false").status_code == 422
