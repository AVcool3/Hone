import os

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from hone.crypto.pipeline import rebalance_crypto, stablecoin_share
from hone.crypto.universe import (
    CRYPTO_PERIODS_PER_YEAR,
    CRYPTO_STRESS_SCENARIOS,
    MARKET_PROXY,
    is_stablecoin,
    normalize_symbol,
    synthetic_crypto_universe,
)
from hone.hedging.hedge import cash_hedge
from hone.market_data.alpaca_client import AlpacaClient
from hone.optimization.views import View
from hone.web.app import create_app


class TestUniverse:
    def test_365_day_year(self):
        assert CRYPTO_PERIODS_PER_YEAR == 365

    def test_symbol_normalization(self):
        assert normalize_symbol("BTCUSD") == "BTC/USD"
        assert normalize_symbol("BTC/USD") == "BTC/USD"
        assert normalize_symbol("eth/usd") == "ETH/USD"
        assert normalize_symbol("SOLUSDT") == "SOL/USDT"

    def test_stablecoin_detection(self):
        assert is_stablecoin("USDC/USD")
        assert is_stablecoin("USDCUSD")
        assert not is_stablecoin("BTC/USD")

    def test_synthetic_universe_has_crypto_character(self):
        prices, weights = synthetic_crypto_universe()
        assert MARKET_PROXY in prices.columns
        assert weights.sum() == pytest.approx(1.0)
        rets = np.log(prices / prices.shift(1)).dropna()
        vols = rets.std() * np.sqrt(CRYPTO_PERIODS_PER_YEAR)
        # crypto vols should be far above equity levels
        assert vols.min() > 0.35, f"too tame for crypto: {vols.to_dict()}"
        assert vols.max() < 2.0
        # fat tails: kurtosis above the normal's 3
        assert rets.kurt().mean() > 0.5


class TestCashHedge:
    def test_exact_vol_reduction(self):
        s = cash_hedge(0.60, 0.45, instrument_label="USDC")
        # c = 1 - 0.45/0.60 = 25%
        assert s.hedge_notional_fraction == pytest.approx(0.25)
        assert s.hedged_volatility == pytest.approx(0.45)
        assert s.kind == "cash"
        assert "USDC" in s.description

    def test_no_hedge_when_already_at_target(self):
        s = cash_hedge(0.40, 0.40)
        assert s.hedge_notional_fraction == pytest.approx(0.0)

    def test_rejects_zero_vol(self):
        with pytest.raises(ValueError):
            cash_hedge(0.0, 0.1)


class TestCryptoPipeline:
    def test_same_protocol_end_to_end(self):
        prices, weights = synthetic_crypto_universe()
        sol = float(prices["SOL/USD"].iloc[-1])
        view = View("SOL/USD", sol, sol * 1.5, confidence=0.6, horizon_days=365)
        r = rebalance_crypto(
            prices, weights, gamma=3.0, views=[view], portfolio_value=20_000.0
        )
        # identical protocol pieces are all present
        assert r.black_litterman is not None
        assert r.optimized.weights.sum() == pytest.approx(1.0, abs=1e-4)
        tilt = (
            r.black_litterman.posterior_mu["SOL/USD"]
            - r.black_litterman.prior_mu["SOL/USD"]
        )
        assert tilt > 0
        # annualized on the crypto calendar -> high vols
        assert r.covariance.volatilities.min() > 0.35

    def test_hedge_uses_stablecoins_not_options(self):
        prices, weights = synthetic_crypto_universe()
        r = rebalance_crypto(prices, weights, gamma=8.0, portfolio_value=20_000.0)
        plan = r.hedge_plan
        assert plan.needs_hedge
        kinds = [x.kind for x in plan.suggestions]
        assert kinds[0] == "cash"  # simplest option leads
        assert "protective_put" not in kinds and "collar" not in kinds
        stable = next(x for x in plan.suggestions if x.kind == "cash")
        assert "stablecoin" in stable.description.lower()

    def test_crypto_stress_scenarios_are_severe(self):
        prices, weights = synthetic_crypto_universe()
        r = rebalance_crypto(prices, weights, gamma=8.0, portfolio_value=20_000.0)
        names = [x.name for x in r.hedge_plan.scenarios]
        assert any("2018" in n for n in names)
        assert any("Terra" in n or "FTX" in n for n in names)
        worst = min(x.market_shock for x in r.hedge_plan.scenarios)
        assert worst <= -0.80  # crypto winters are deeper than equity crashes
        assert all(x.loss_usd < 0 for x in r.hedge_plan.scenarios)

    def test_rejects_view_without_history(self):
        prices, weights = synthetic_crypto_universe()
        with pytest.raises(ValueError, match="no price history"):
            rebalance_crypto(
                prices, weights, gamma=2.0,
                views=[View("DOGE/USD", 1.0, 2.0, 0.5)],
            )

    def test_stablecoin_share(self):
        w = pd.Series({"BTC/USD": 0.7, "USDC/USD": 0.3})
        assert stablecoin_share(w) == pytest.approx(0.3)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        import json
        self._p, self.status_code, self.text = payload, status_code, json.dumps(payload)

    def json(self):
        return self._p


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        return self.responses.pop(0)


class TestAlpacaCrypto:
    def test_crypto_bars_endpoint_and_shape(self):
        payload = {
            "bars": {
                "BTC/USD": [
                    {"t": "2026-01-01T00:00:00Z", "c": 95000.0},
                    {"t": "2026-01-02T00:00:00Z", "c": 96000.0},
                ],
                "ETH/USD": [
                    {"t": "2026-01-01T00:00:00Z", "c": 3300.0},
                    {"t": "2026-01-02T00:00:00Z", "c": 3350.0},
                ],
            },
            "next_page_token": None,
        }
        sess = FakeSession([FakeResponse(payload)])
        client = AlpacaClient(api_key="k", secret_key="s", session=sess)
        prices = client.get_crypto_bars(["BTC/USD", "ETH/USD"], start="2026-01-01")
        assert list(prices.columns) == ["BTC/USD", "ETH/USD"]
        assert len(prices) == 2
        _, url, kw = sess.calls[0]
        assert "/v1beta3/crypto/us/bars" in url
        assert kw["params"]["symbols"] == "BTC/USD,ETH/USD"

    def test_crypto_positions_filtered_and_normalized(self):
        raw = [
            {"symbol": "BTCUSD", "qty": "0.5", "market_value": "48000",
             "avg_entry_price": "90000", "current_price": "96000",
             "unrealized_pl": "3000", "asset_class": "crypto"},
            {"symbol": "AAPL", "qty": "10", "market_value": "2000",
             "avg_entry_price": "180", "current_price": "200",
             "unrealized_pl": "200", "asset_class": "us_equity"},
        ]
        sess = FakeSession([FakeResponse(raw)])
        client = AlpacaClient(api_key="k", secret_key="s", session=sess)
        pos = client.get_crypto_positions()
        assert [p.symbol for p in pos] == ["BTC/USD"]


@pytest.fixture
def crypto_client(monkeypatch):
    monkeypatch.setenv("HONE_ASSET_CLASS", "crypto")
    return TestClient(create_app())


class TestPathRouting:
    """One deployment serves both products: / and /crypto."""

    def test_crypto_path_serves_the_app(self):
        c = TestClient(create_app())
        assert c.get("/crypto").status_code == 200
        assert c.get("/crypto/").status_code == 200
        assert "disciplined position sizes" in c.get("/crypto").text

    def test_asset_class_resolves_per_request(self, monkeypatch):
        monkeypatch.delenv("HONE_ASSET_CLASS", raising=False)
        c = TestClient(create_app())
        assert c.get("/api/config").json()["asset_class"] == "equities"
        assert c.get("/api/config?asset_class=crypto").json()["asset_class"] == "crypto"
        # and the two do not leak into each other across requests
        assert c.get("/api/config").json()["market_proxy"] == "SPY"

    def test_endpoints_follow_the_query_param(self, monkeypatch):
        monkeypatch.delenv("HONE_ASSET_CLASS", raising=False)
        c = TestClient(create_app())
        crypto = c.post("/api/portfolio?asset_class=crypto", json={"demo": True}).json()
        equities = c.post("/api/portfolio", json={"demo": True}).json()
        assert all("/" in p["symbol"] for p in crypto["positions"])
        assert all("/" not in p["symbol"] for p in equities["positions"])

    def test_env_var_still_pins_a_deployment(self, monkeypatch):
        monkeypatch.setenv("HONE_ASSET_CLASS", "crypto")
        c = TestClient(create_app())
        assert c.get("/api/config").json()["asset_class"] == "crypto"


class TestCryptoApi:
    def test_config_reports_crypto(self, crypto_client):
        cfg = crypto_client.get("/api/config").json()
        assert cfg["asset_class"] == "crypto"
        assert cfg["market_proxy"] == "BTC/USD"
        assert cfg["periods_per_year"] == 365
        assert cfg["copy"]["product"] == "Hone Crypto"

    def test_equities_is_the_default(self, monkeypatch):
        monkeypatch.delenv("HONE_ASSET_CLASS", raising=False)
        cfg = TestClient(create_app()).get("/api/config").json()
        assert cfg["asset_class"] == "equities"
        assert cfg["market_proxy"] == "SPY"

    def test_demo_portfolio_is_crypto(self, crypto_client):
        body = crypto_client.post(
            "/api/portfolio", json={"demo": True, "analyze": True, "stated_gamma": 2.0}
        ).json()
        syms = [p["symbol"] for p in body["positions"]]
        assert all("/" in s for s in syms)
        assert "BTC/USD" in syms
        assert body["analysis"]["volatility"] > 0.35

    def test_optimize_and_hedge_in_crypto_mode(self, crypto_client):
        res = crypto_client.post(
            "/api/optimize",
            json={"gamma": 8.0, "demo": True,
                  "views": [{"ticker": "SOL/USD", "target_price": 3000,
                             "confidence": 0.6}]},
        )
        assert res.status_code == 200
        body = res.json()
        assert any(w["symbol"] == "SOL/USD" for w in body["weights"])
        plan = body["hedge_plan"]
        assert plan["needs_hedge"]
        assert [x["kind"] for x in plan["suggestions"]][0] == "cash"
        assert any("2018" in x["name"] for x in plan["scenarios"])

    def test_backtest_includes_buy_and_hold(self, crypto_client):
        body = crypto_client.post(
            "/api/backtest", json={"gamma": 3.0, "demo": True}
        ).json()
        names = {x["name"] for x in body["strategies"]}
        assert "market_hold" in names  # the benchmark that matters
        assert "tier_matched" in names

    def test_questionnaire_protocol_is_unchanged(self, crypto_client):
        """The elicitation instrument must be identical across products."""
        vec = ["A"] * 5 + ["B"] * 5
        body = crypto_client.post(
            "/api/questionnaire", json={"choices": [vec, vec, vec]}
        ).json()
        assert 0.14 <= body["gamma"] <= 0.42  # same canonical interval
        assert body["tier"]["num_tiers"] == 50
        assert body["n_obs"] == 30
        menu = crypto_client.get("/api/menu").json()
        assert len(menu) == 3 and all(len(r["rows"]) == 10 for r in menu)
        assert menu[0]["rows"][0]["option_a"]["high"] == pytest.approx(2.00)
