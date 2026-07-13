import numpy as np
import pandas as pd
import pytest

from hone.backtest.engine import performance_metrics, run_backtest
from hone.pipeline import synthetic_universe


class TestMetrics:
    def test_flat_curve_has_zero_return(self):
        idx = pd.bdate_range("2022-01-01", periods=300)
        eq = pd.Series(100.0, index=idx)
        m = performance_metrics(eq)
        assert m["cagr"] == pytest.approx(0.0, abs=1e-9)
        assert m["max_drawdown"] == pytest.approx(0.0, abs=1e-9)

    def test_drawdown_is_negative_after_a_fall(self):
        idx = pd.bdate_range("2022-01-01", periods=4)
        eq = pd.Series([100, 120, 60, 90], index=idx)
        m = performance_metrics(eq)
        assert m["max_drawdown"] == pytest.approx(-0.5, abs=1e-9)  # 120 -> 60

    def test_final_multiple(self):
        idx = pd.bdate_range("2022-01-01", periods=300)
        eq = pd.Series(np.linspace(100, 200, 300), index=idx)
        assert performance_metrics(eq)["final_multiple"] == pytest.approx(2.0)


class TestBacktest:
    def test_runs_all_strategies_walk_forward(self):
        prices, _ = synthetic_universe(n_days=700)
        r = run_backtest(prices, gamma=1.2)
        names = {s.name for s in r.strategies}
        assert names == {"tier_matched", "equal_weight", "concentrated", "sixty_forty"}
        assert r.rebalances > 5
        for s in r.strategies:
            assert len(s.equity_curve) == len(s.dates)
            assert s.metrics  # non-empty

    def test_concentrated_is_riskier_than_tier_matched(self):
        prices, _ = synthetic_universe(n_days=900, seed=3)
        r = run_backtest(prices, gamma=2.0)
        m = {s.name: s.metrics for s in r.strategies}
        # a single-name bet should have a worse (deeper) drawdown than the
        # diversified, risk-aware portfolio
        assert m["concentrated"]["max_drawdown"] <= m["tier_matched"]["max_drawdown"]
        assert m["concentrated"]["volatility"] >= m["tier_matched"]["volatility"]

    def test_rejects_short_history(self):
        prices, _ = synthetic_universe(n_days=120)
        with pytest.raises(ValueError, match="price rows"):
            run_backtest(prices, gamma=1.2, lookback=252)

    def test_headline_present(self):
        prices, _ = synthetic_universe(n_days=700)
        assert isinstance(run_backtest(prices, gamma=1.2).headline, str)


class TestBacktestApi:
    def test_demo_backtest_endpoint(self):
        from fastapi.testclient import TestClient
        from hone.web.app import create_app

        client = TestClient(create_app())
        res = client.post("/api/backtest", json={"gamma": 1.5, "demo": True})
        assert res.status_code == 200
        body = res.json()
        assert len(body["strategies"]) == 4
        assert body["rebalances"] > 0
        hone = next(s for s in body["strategies"] if s["name"] == "tier_matched")
        assert "sharpe" in hone["metrics"]
