import numpy as np
import pandas as pd
import pytest

from hone.optimization import (
    View,
    black_litterman_posterior,
    build_view_matrices,
    efficient_frontier,
    idzorek_omega,
    implied_equilibrium_returns,
    mvo_weights,
)


@pytest.fixture
def market():
    assets = ["AAPL", "MSFT", "SPY", "TSLA"]
    vols = np.array([0.28, 0.25, 0.17, 0.50])
    corr = np.array(
        [
            [1.00, 0.65, 0.75, 0.40],
            [0.65, 1.00, 0.75, 0.35],
            [0.75, 0.75, 1.00, 0.45],
            [0.40, 0.35, 0.45, 1.00],
        ]
    )
    sigma = pd.DataFrame(corr * np.outer(vols, vols), index=assets, columns=assets)
    mu = pd.Series([0.10, 0.09, 0.07, 0.15], index=assets)
    w = pd.Series([0.3, 0.3, 0.3, 0.1], index=assets)
    return mu, sigma, w


class TestMVO:
    def test_weights_sum_to_one(self, market):
        mu, sigma, _ = market
        res = mvo_weights(mu, sigma, gamma=3.0)
        assert res.weights.sum() == pytest.approx(1.0, abs=1e-6)
        assert res.converged

    def test_long_only_respected(self, market):
        mu, sigma, _ = market
        res = mvo_weights(mu, sigma, gamma=3.0, long_only=True)
        assert (res.weights >= -1e-9).all()

    def test_higher_gamma_means_lower_volatility(self, market):
        mu, sigma, _ = market
        low = mvo_weights(mu, sigma, gamma=1.0)
        high = mvo_weights(mu, sigma, gamma=10.0)
        assert high.volatility < low.volatility

    def test_max_weight_cap(self, market):
        mu, sigma, _ = market
        res = mvo_weights(mu, sigma, gamma=0.5, max_weight=0.4)
        assert (res.weights <= 0.4 + 1e-8).all()

    def test_frontier_is_monotone(self, market):
        mu, sigma, _ = market
        frontier = efficient_frontier(mu, sigma, n_points=8)
        # sweeping gamma up moves down the frontier
        assert frontier["volatility"].is_monotonic_decreasing


class TestViews:
    def test_expected_return_annualizes_target(self):
        v = View("TSLA", current_price=100, target_price=121, confidence=0.5,
                 horizon_days=730.5)
        # +21% over two years ~ +10% a year
        assert v.expected_return == pytest.approx(0.10, abs=1e-3)

    def test_validation(self):
        with pytest.raises(ValueError):
            View("X", 100, 120, confidence=0.0)
        with pytest.raises(ValueError):
            View("X", -1, 120, confidence=0.5)

    def test_matrices(self):
        views = [View("TSLA", 100, 130, 0.6), View("AAPL", 200, 220, 0.3)]
        p, q, c = build_view_matrices(views, ["AAPL", "TSLA", "SPY"])
        assert p.shape == (2, 3)
        assert p[0].tolist() == [0.0, 1.0, 0.0]
        assert q[0] == pytest.approx(0.30, abs=1e-2)
        assert c.tolist() == [0.6, 0.3]

    def test_unknown_ticker_rejected(self):
        with pytest.raises(ValueError, match="not in the universe"):
            build_view_matrices([View("ZZZ", 10, 12, 0.5)], ["AAPL"])


class TestBlackLitterman:
    def test_equilibrium_returns_formula(self, market):
        _, sigma, w = market
        pi = implied_equilibrium_returns(sigma, w, delta=2.5)
        expected = 2.5 * sigma.to_numpy() @ w.to_numpy()
        assert pi.to_numpy() == pytest.approx(expected)

    def test_omega_shrinks_with_confidence(self, market):
        _, sigma, _ = market
        p = np.array([[0.0, 0.0, 0.0, 1.0]])
        low = idzorek_omega(p, sigma.to_numpy(), np.array([0.2]), tau=0.05)
        high = idzorek_omega(p, sigma.to_numpy(), np.array([0.9]), tau=0.05)
        assert high[0, 0] < low[0, 0]

    def test_posterior_tilts_toward_view(self, market):
        _, sigma, w = market
        view = View("TSLA", current_price=100, target_price=140, confidence=0.7)
        res = black_litterman_posterior(sigma, w, [view], delta=2.5)
        assert res.posterior_mu["TSLA"] > res.prior_mu["TSLA"]
        # posterior stays between prior and the raw view
        assert res.posterior_mu["TSLA"] < view.expected_return

    def test_higher_confidence_moves_posterior_closer_to_view(self, market):
        _, sigma, w = market
        weak = black_litterman_posterior(
            sigma, w, [View("TSLA", 100, 140, 0.1)], delta=2.5
        )
        strong = black_litterman_posterior(
            sigma, w, [View("TSLA", 100, 140, 0.95)], delta=2.5
        )
        assert strong.posterior_mu["TSLA"] > weak.posterior_mu["TSLA"]

    def test_full_confidence_hits_the_view(self, market):
        _, sigma, w = market
        view = View("TSLA", 100, 140, confidence=1.0)
        res = black_litterman_posterior(sigma, w, [view], delta=2.5)
        assert res.posterior_mu["TSLA"] == pytest.approx(
            view.expected_return, abs=1e-3
        )

    def test_correlated_assets_move_with_the_view(self, market):
        _, sigma, w = market
        res = black_litterman_posterior(
            sigma, w, [View("TSLA", 100, 140, 0.7)], delta=2.5
        )
        tilt = res.posterior_mu - res.prior_mu
        # SPY is positively correlated with TSLA so its posterior rises too
        assert tilt["SPY"] > 0
        assert tilt["TSLA"] == tilt.max()
