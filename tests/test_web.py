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

    def test_landing_is_crawler_visible(self, client):
        """The value proposition must be readable without JavaScript."""
        html = client.get("/").text
        assert "disciplined position sizes" in html
        assert "Personalized Portfolio Optimization" in html  # title descriptor
        assert '<meta name="description"' in html
        assert 'property="og:image"' in html
        assert 'property="og:title"' in html
        # funnel + trust sections present in raw HTML
        assert "The problem" in html
        assert "How it works" in html
        assert "Built to be trusted" in html
        assert "Is this real money?" in html

    def test_favicon_assets_served_and_linked(self, client):
        html = client.get("/").text
        assert 'href="/favicon.svg"' in html
        assert "apple-touch-icon" in html
        assert "🎯" not in html  # emoji placeholder is gone
        svg = client.get("/favicon.svg")
        assert svg.status_code == 200
        assert svg.headers["content-type"] == "image/svg+xml"
        assert client.get("/favicon-32.png").status_code == 200
        assert client.get("/apple-touch-icon.png").status_code == 200

    def test_og_image_and_robots_served(self, client):
        og = client.get("/og.png")
        assert og.status_code == 200
        assert og.headers["content-type"] == "image/png"
        r = client.get("/robots.txt")
        assert r.status_code == 200
        assert "User-agent" in r.text

    def test_config_js_served(self, client):
        res = client.get("/config.js")
        assert res.status_code == 200
        assert "HONE_CONFIG" in res.text
        assert "application/javascript" in res.headers["content-type"]

    def test_docs_not_shadowed_by_static_catchall(self, client):
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200

    def test_unknown_asset_404(self, client):
        assert client.get("/nope.js").status_code == 404


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
        detail = res.json()["detail"]
        assert "ZZZZ" in detail
        # the message must say what the user *can* pick
        assert "Available here" in detail and "TSLA" in detail

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


class TestInsightFeatures:
    def test_portfolio_analysis_reveals_gamma(self, client):
        res = client.post(
            "/api/portfolio",
            json={"demo": True, "analyze": True, "stated_gamma": 2.5},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["portfolio_value"] == 25000.0
        a = body["analysis"]
        assert a["volatility"] > 0
        assert a["revealed_gamma"] > 0
        assert 1 <= a["revealed_tier"]["tier"] <= 50
        assert a["stated_tier"]["tier"] == 36  # gamma 2.5 -> tier 36
        assert a["market_premium_assumption"] == 0.05

    def test_portfolio_without_analyze_has_no_analysis(self, client):
        res = client.post("/api/portfolio", json={"demo": True})
        assert res.json()["analysis"] is None

    def test_optimize_returns_trade_reasons(self, client):
        res = client.post(
            "/api/optimize",
            json={
                "gamma": 1.2,
                "demo": True,
                "views": [{"ticker": "TSLA", "target_price": 250, "confidence": 0.6}],
            },
        )
        body = res.json()
        traded = [w for w in body["weights"] if abs(w["trade"]) > 1e-3]
        assert traded and all(w["reason"] for w in traded)
        buys = [w for w in traded if w["trade"] > 0]
        assert all(w["reason"].startswith("Buy") for w in buys)

    def test_hedge_plan_has_dollar_scenarios(self, client):
        res = client.post(
            "/api/hedge",
            json={"gamma": 6.0, "demo": True, "portfolio_value": 100000},
        )
        plan = res.json()
        assert plan["portfolio_value"] == 100000
        assert plan["tolerable_annual_loss_usd"] > 0
        assert plan["current_annual_loss_usd"] > plan["tolerable_annual_loss_usd"]
        assert len(plan["scenarios"]) == 3
        crisis = plan["scenarios"][0]
        assert crisis["loss_usd"] < 0  # a loss
        # the short hedge reduces the scenario loss
        assert crisis["hedged_loss_usd"] > crisis["loss_usd"]


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
        assert kinds == {"cash", "short", "protective_put", "collar"}
        assert plan["suggestions"][0]["kind"] == "cash"
        assert plan["target_volatility"] < plan["current_volatility"]

    def test_risk_tolerant_needs_nothing(self, client):
        res = client.post("/api/hedge", json={"gamma": 0.3, "demo": True})
        assert res.status_code == 200
        plan = res.json()
        assert plan["needs_hedge"] is False
        assert plan["suggestions"] == []
