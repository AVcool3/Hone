import numpy as np
import pandas as pd
import pytest

from hone.hedging import (
    bs_price,
    gamma_target_volatility,
    implied_zero_cost_call_strike,
    portfolio_volatility,
    protective_put,
    short_hedge,
    suggest_hedges,
    zero_cost_collar,
)
from hone.optimization.views import View
from hone.pipeline import rebalance, synthetic_universe


class TestBlackScholes:
    def test_put_call_parity(self):
        s, k, vol, t, r = 100.0, 105.0, 0.25, 0.5, 0.04
        call = bs_price("call", s, k, vol, t, r)
        put = bs_price("put", s, k, vol, t, r)
        assert call - put == pytest.approx(s - k * np.exp(-r * t), abs=1e-9)

    def test_zero_cost_collar_strike_balances_premiums(self):
        s, vol, t, r = 100.0, 0.2, 0.5, 0.04
        put_strike = 90.0
        call_strike = implied_zero_cost_call_strike(s, put_strike, vol, t, r)
        assert call_strike > s
        put = bs_price("put", s, put_strike, vol, t, r)
        call = bs_price("call", s, call_strike, vol, t, r)
        assert call == pytest.approx(put, rel=1e-6)


class TestRiskBudget:
    def test_merton_target(self):
        # alpha* = (0.10-0.04)/(3 * 0.2^2) = 0.5 -> target = 10%
        target = gamma_target_volatility(3.0, 0.10, 0.20, risk_free=0.04)
        assert target == pytest.approx(0.10)

    def test_tolerant_investor_keeps_current_vol(self):
        assert gamma_target_volatility(0.5, 0.12, 0.20) == pytest.approx(0.20)

    def test_more_averse_means_lower_target(self):
        t2 = gamma_target_volatility(2.0, 0.10, 0.30)
        t5 = gamma_target_volatility(5.0, 0.10, 0.30)
        assert t5 < t2


class TestShortHedge:
    def test_reaches_target_when_feasible(self):
        s = short_hedge(
            portfolio_vol=0.30, target_vol=0.22, hedge_vol=0.18, correlation=0.9
        )
        assert s.hedged_volatility == pytest.approx(0.22)
        assert 0 < s.hedge_notional_fraction < 1.5
        assert not s.details["capped"]

    def test_caps_at_minimum_variance(self):
        s = short_hedge(
            portfolio_vol=0.30, target_vol=0.01, hedge_vol=0.18, correlation=0.8
        )
        assert s.details["capped"]
        # min-var hedged vol = 0.30 * sqrt(1 - 0.8^2) = 0.18
        assert s.hedged_volatility == pytest.approx(0.30 * np.sqrt(1 - 0.64))

    def test_uncorrelated_instrument_rejected(self):
        with pytest.raises(ValueError):
            short_hedge(0.3, 0.2, 0.18, correlation=-0.2)


class TestOptionHedges:
    def test_risk_averse_gets_tighter_floor(self):
        tight = protective_put(gamma=4.0, spot=100, implied_vol=0.2)
        loose = protective_put(gamma=0.3, spot=100, implied_vol=0.2)
        assert tight.details["floor"] < loose.details["floor"]
        assert tight.est_annual_cost_fraction > loose.est_annual_cost_fraction

    def test_collar_is_free_and_capped(self):
        c = zero_cost_collar(gamma=2.0, spot=100, implied_vol=0.2)
        assert c.est_annual_cost_fraction == 0.0
        assert c.details["call_strike"] > 100


class TestSuggestHedges:
    def make_market(self):
        assets = ["AAPL", "SPY"]
        vols = np.array([0.30, 0.18])
        corr = np.array([[1.0, 0.8], [0.8, 1.0]])
        sigma = pd.DataFrame(
            corr * np.outer(vols, vols), index=assets, columns=assets
        )
        mu = pd.Series([0.11, 0.08], index=assets)
        w = pd.Series([0.8, 0.2], index=assets)
        return w, sigma, mu

    def test_no_hedge_for_risk_tolerant(self):
        w, sigma, mu = self.make_market()
        plan = suggest_hedges(w, sigma, mu, gamma=0.4)
        assert not plan.needs_hedge
        assert plan.suggestions == []

    def test_full_plan_for_risk_averse(self):
        w, sigma, mu = self.make_market()
        plan = suggest_hedges(w, sigma, mu, gamma=6.0)
        assert plan.needs_hedge
        kinds = {s.kind for s in plan.suggestions}
        # cash leads (no derivatives needed), then the derivative overlays
        assert kinds == {"cash", "short", "protective_put", "collar"}
        assert plan.suggestions[0].kind == "cash"
        assert plan.target_volatility < plan.current_volatility
        # hedge instrument stats come from the covariance matrix itself
        short = next(s for s in plan.suggestions if s.kind == "short")
        assert short.details["correlation"] == pytest.approx(
            float(
                (w @ sigma["SPY"])
                / (portfolio_volatility(w, sigma) * np.sqrt(sigma.loc["SPY", "SPY"]))
            )
        )


class TestPipeline:
    def test_end_to_end_with_view(self):
        prices, weights = synthetic_universe()
        tsla = float(prices["TSLA"].iloc[-1])
        view = View("TSLA", tsla, tsla * 1.4, confidence=0.7)
        report = rebalance(prices, weights, gamma=2.0, views=[view], max_weight=0.5)

        assert report.optimized.weights.sum() == pytest.approx(1.0, abs=1e-6)
        assert report.black_litterman is not None
        # the view should tilt TSLA's expected return upward...
        tilt = (
            report.black_litterman.posterior_mu["TSLA"]
            - report.black_litterman.prior_mu["TSLA"]
        )
        assert tilt > 0
        # ...and the optimizer should allocate more to TSLA than today
        assert (
            report.optimized.weights["TSLA"] > report.current_weights["TSLA"]
        )
        trades = report.trade_list()
        assert trades["trade"].sum() == pytest.approx(
            1.0 - report.current_weights.sum(), abs=1e-4
        )
        assert "Hedge Plan" in report.summary()

    def test_view_without_history_rejected(self):
        prices, weights = synthetic_universe()
        view = View("ZZZZ", 10, 15, 0.5)
        with pytest.raises(ValueError, match="no price history"):
            rebalance(prices, weights, gamma=2.0, views=[view])

    def test_no_views_falls_back_to_equilibrium(self):
        prices, weights = synthetic_universe()
        report = rebalance(prices, weights, gamma=3.0)
        assert report.black_litterman is None
        assert report.optimized.converged
