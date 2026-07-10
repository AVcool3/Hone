import pytest
from fastapi.testclient import TestClient

from hone.web.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


class TestStatic:
    def test_index_served(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "Hone" in res.text
        assert "questionnaire" in res.text.lower()


class TestMenu:
    def test_three_rounds_of_ten(self, client):
        res = client.get("/api/menu")
        assert res.status_code == 200
        rounds = res.json()
        assert len(rounds) == 3
        assert [r["scale"] for r in rounds] == [1.0, 20.0, 100.0]
        assert all(len(r["rows"]) == 10 for r in rounds)
        row1 = rounds[0]["rows"][0]
        assert row1["option_a"]["high"] == pytest.approx(2.00)
        assert row1["option_b"]["high"] == pytest.approx(3.85)


class TestQuestionnaire:
    def test_scores_consistent_choices(self, client):
        vec = ["A"] * 5 + ["B"] * 5
        res = client.post("/api/questionnaire", json={"choices": [vec, vec, vec]})
        assert res.status_code == 200
        body = res.json()
        assert 0.14 <= body["gamma"] <= 0.42
        assert body["tier"]["tier"] >= 1
        assert body["tier"]["num_tiers"] == 50
        assert body["monotone"] == [True, True, True]
        assert body["n_obs"] == 30

    def test_bad_choices_rejected(self, client):
        res = client.post("/api/questionnaire", json={"choices": [["X"] * 10] * 3})
        assert res.status_code == 422

    def test_wrong_shape_rejected(self, client):
        res = client.post("/api/questionnaire", json={"choices": [["A"] * 10]})
        assert res.status_code == 422


class TestPortfolio:
    def test_demo_portfolio(self, client):
        res = client.post("/api/portfolio", json={"demo": True})
        assert res.status_code == 200
        body = res.json()
        assert body["demo"] is True
        assert len(body["positions"]) >= 3
        total = sum(p["weight"] for p in body["positions"])
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_live_without_credentials_is_401(self, client, monkeypatch):
        for var in (
            "ALPACA_API_KEY",
            "ALPACA_SECRET_KEY",
            "APCA_API_KEY_ID",
            "APCA_API_SECRET_KEY",
        ):
            monkeypatch.delenv(var, raising=False)
        res = client.post("/api/portfolio", json={"demo": False})
        assert res.status_code == 401


class TestOptimize:
    def test_demo_optimize_with_view(self, client):
        res = client.post(
            "/api/optimize",
            json={
                "gamma": 1.2,
                "demo": True,
                "views": [
                    {"ticker": "TSLA", "target_price": 250, "confidence": 0.6,
                     "horizon_days": 365}
                ],
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["tier"]["tier"] >= 1
        assert body["returns"] is not None
        tsla = next(r for r in body["returns"] if r["symbol"] == "TSLA")
        assert tsla["posterior"] != tsla["prior"]
        weights = {w["symbol"]: w["target"] for w in body["weights"]}
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-4)
        assert all(w <= 0.35 + 1e-6 for w in weights.values())
        assert body["hedge_plan"]["current_volatility"] > 0

    def test_demo_optimize_without_views(self, client):
        res = client.post("/api/optimize", json={"gamma": 2.0, "demo": True})
        assert res.status_code == 200
        assert res.json()["returns"] is None

    def test_unknown_view_ticker_rejected(self, client):
        res = client.post(
            "/api/optimize",
            json={
                "gamma": 1.0,
                "demo": True,
                "views": [{"ticker": "ZZZZ", "target_price": 10}],
            },
        )
        assert res.status_code == 422
        assert "ZZZZ" in res.json()["detail"]

    def test_confidence_validation(self, client):
        res = client.post(
            "/api/optimize",
            json={
                "gamma": 1.0,
                "demo": True,
                "views": [{"ticker": "TSLA", "target_price": 250, "confidence": 1.5}],
            },
        )
        assert res.status_code == 422


class TestDeploymentHardening:
    def test_health_endpoint(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

    def test_password_gate(self, monkeypatch):
        monkeypatch.setenv("HONE_ACCESS_PASSWORD", "hunter2")
        gated = TestClient(create_app())
        assert gated.get("/").status_code == 401
        assert gated.get("/api/menu").status_code == 401
        # health stays open for platform probes
        assert gated.get("/api/health").status_code == 200
        # wrong password rejected, right password accepted (any username)
        assert gated.get("/", auth=("anyone", "wrong")).status_code == 401
        assert gated.get("/", auth=("anyone", "hunter2")).status_code == 200
        assert gated.get("/api/menu", auth=("x", "hunter2")).status_code == 200

    def test_public_mode_refuses_server_keys(self, client, monkeypatch):
        monkeypatch.setenv("HONE_PUBLIC", "1")
        monkeypatch.setenv("ALPACA_API_KEY", "server-key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "server-secret")
        res = client.post("/api/portfolio", json={"demo": False})
        assert res.status_code == 401
        assert "public deployment" in res.json()["detail"]

    def test_public_mode_still_allows_demo(self, client, monkeypatch):
        monkeypatch.setenv("HONE_PUBLIC", "1")
        res = client.post("/api/portfolio", json={"demo": True})
        assert res.status_code == 200


class TestHedge:
    def test_risk_averse_gets_suggestions(self, client):
        res = client.post("/api/hedge", json={"gamma": 6.0, "demo": True})
        assert res.status_code == 200
        plan = res.json()
        assert plan["needs_hedge"] is True
        kinds = {s["kind"] for s in plan["suggestions"]}
        assert kinds == {"short", "protective_put", "collar"}
        assert plan["target_volatility"] < plan["current_volatility"]

    def test_risk_tolerant_needs_nothing(self, client):
        res = client.post("/api/hedge", json={"gamma": 0.3, "demo": True})
        assert res.status_code == 200
        plan = res.json()
        assert plan["needs_hedge"] is False
        assert plan["suggestions"] == []
