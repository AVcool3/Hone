import json

import numpy as np
import pandas as pd
import pytest

from hone.market_data import (
    AlpacaClient,
    AlpacaError,
    ewma_covariance,
    portfolio_covariance,
    returns_from_prices,
    sample_covariance,
    shrinkage_covariance,
)


# ---------------------------------------------------------------- covariance
def make_prices(n_days=300, seed=1):
    rng = np.random.default_rng(seed)
    vols = np.array([0.20, 0.30, 0.15]) / np.sqrt(252)
    corr = np.array([[1.0, 0.6, 0.3], [0.6, 1.0, 0.2], [0.3, 0.2, 1.0]])
    cov = corr * np.outer(vols, vols)
    rets = rng.multivariate_normal([0.0004, 0.0006, 0.0002], cov, size=n_days)
    return pd.DataFrame(
        100 * np.exp(np.cumsum(rets, axis=0)),
        columns=["AAA", "BBB", "CCC"],
        index=pd.bdate_range("2024-01-01", periods=n_days),
    )


class TestCovariance:
    def test_returns_shapes(self):
        prices = make_prices()
        rets = returns_from_prices(prices)
        assert rets.shape == (len(prices) - 1, 3)

    def test_sample_covariance_recovers_vols(self):
        prices = make_prices(n_days=2000)
        cov = sample_covariance(returns_from_prices(prices))
        vols = np.sqrt(np.diag(cov))
        assert vols == pytest.approx([0.20, 0.30, 0.15], abs=0.03)

    def test_covariance_is_symmetric_psd(self):
        prices = make_prices()
        for fn in (sample_covariance, ewma_covariance, shrinkage_covariance):
            cov = fn(returns_from_prices(prices)).to_numpy()
            assert np.allclose(cov, cov.T)
            assert np.linalg.eigvalsh(cov).min() > -1e-10

    def test_shrinkage_pulls_toward_identity(self):
        prices = make_prices(n_days=60)  # short history -> noisy sample
        rets = returns_from_prices(prices)
        s = sample_covariance(rets).to_numpy()
        shrunk = shrinkage_covariance(rets).to_numpy()
        # off-diagonals move toward zero
        off = ~np.eye(3, dtype=bool)
        assert np.abs(shrunk[off]).sum() < np.abs(s[off]).sum()

    def test_report_bundle(self):
        report = portfolio_covariance(make_prices(), method="shrinkage")
        assert report.method == "shrinkage"
        assert set(report.covariance.columns) == {"AAA", "BBB", "CCC"}
        assert (report.volatilities > 0).all()
        assert np.allclose(np.diag(report.correlation), 1.0)

    def test_too_little_history_rejected(self):
        with pytest.raises(ValueError, match="at least 20"):
            portfolio_covariance(make_prices(n_days=10))


# ------------------------------------------------------------- alpaca client
class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeSession:
    """Stands in for requests.Session; records calls, returns canned data."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


POSITIONS = [
    {
        "symbol": "AAPL",
        "qty": "10",
        "market_value": "1500",
        "avg_entry_price": "140",
        "current_price": "150",
        "unrealized_pl": "100",
    },
    {
        "symbol": "TSLA",
        "qty": "-2",
        "market_value": "-500",
        "avg_entry_price": "260",
        "current_price": "250",
        "unrealized_pl": "20",
    },
]


class TestAlpacaClient:
    def test_requires_credentials(self, monkeypatch):
        for var in (
            "ALPACA_API_KEY",
            "ALPACA_SECRET_KEY",
            "APCA_API_KEY_ID",
            "APCA_API_SECRET_KEY",
        ):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(AlpacaError, match="credentials"):
            AlpacaClient()

    def test_positions_and_weights(self):
        session = FakeSession([FakeResponse(POSITIONS), FakeResponse(POSITIONS)])
        client = AlpacaClient(api_key="k", secret_key="s", session=session)
        positions = client.get_positions()
        assert positions[0].symbol == "AAPL"
        assert positions[1].qty == -2

        weights = client.portfolio_weights()
        # normalized by gross exposure (2000): +0.75 long, -0.25 short
        assert weights["AAPL"] == pytest.approx(0.75)
        assert weights["TSLA"] == pytest.approx(-0.25)

    def test_auth_headers_sent(self):
        session = FakeSession([FakeResponse({"status": "ACTIVE"})])
        client = AlpacaClient(api_key="key-id", secret_key="sec", session=session)
        client.get_account()
        _, _, kwargs = session.calls[0]
        assert kwargs["headers"]["APCA-API-KEY-ID"] == "key-id"
        assert kwargs["headers"]["APCA-API-SECRET-KEY"] == "sec"

    def test_error_response_raises(self):
        session = FakeSession([FakeResponse({"message": "forbidden"}, 403)])
        client = AlpacaClient(api_key="k", secret_key="s", session=session)
        with pytest.raises(AlpacaError, match="403"):
            client.get_account()

    def test_get_bars_builds_price_panel_with_pagination(self):
        page1 = {
            "bars": {
                "AAPL": [
                    {"t": "2025-01-02T05:00:00Z", "c": 150.0},
                    {"t": "2025-01-03T05:00:00Z", "c": 151.0},
                ]
            },
            "next_page_token": "tok",
        }
        page2 = {
            "bars": {
                "AAPL": [{"t": "2025-01-06T05:00:00Z", "c": 152.5}],
                "SPY": [
                    {"t": "2025-01-02T05:00:00Z", "c": 500.0},
                    {"t": "2025-01-03T05:00:00Z", "c": 501.0},
                    {"t": "2025-01-06T05:00:00Z", "c": 502.0},
                ],
            },
            "next_page_token": None,
        }
        session = FakeSession([FakeResponse(page1), FakeResponse(page2)])
        client = AlpacaClient(api_key="k", secret_key="s", session=session)
        prices = client.get_bars(["AAPL", "SPY"], start="2025-01-01")
        assert list(prices.columns) == ["AAPL", "SPY"]
        assert len(prices) == 3
        assert prices["AAPL"].iloc[-1] == pytest.approx(152.5)
        # second request carried the page token
        assert session.calls[1][2]["params"]["page_token"] == "tok"

    def test_submit_order_payload(self):
        session = FakeSession([FakeResponse({"id": "order-1"})])
        client = AlpacaClient(api_key="k", secret_key="s", session=session)
        client.submit_order("SPY", qty=5, side="sell")
        method, url, kwargs = session.calls[0]
        assert method == "POST"
        assert url.endswith("/v2/orders")
        assert kwargs["json"]["side"] == "sell"
