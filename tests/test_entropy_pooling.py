"""Entropy pooling: the solver, the view types, and the cost disclosure."""

import numpy as np
import pandas as pd
import pytest

from hone.crypto.universe import synthetic_crypto_universe
from hone.optimization.cvar import historical_scenarios, min_cvar_weights
from hone.optimization.entropy_pooling import (
    COLLAPSE_WARNING,
    conditional_view,
    effective_number_of_scenarios,
    entropy_pooling,
    mean_view,
    posterior_moments,
    probability_view,
    ranking_view,
    relative_entropy,
    resample_scenarios,
    volatility_view,
)
from hone.pipeline import synthetic_universe


@pytest.fixture(scope="module")
def scenarios():
    prices, _ = synthetic_universe(n_days=900)
    return historical_scenarios(prices, horizon=21)


@pytest.fixture(scope="module")
def crypto():
    prices, _ = synthetic_crypto_universe(n_days=900)
    return historical_scenarios(prices, horizon=21)


class TestDiagnostics:
    def test_effective_scenarios_of_a_uniform_prior_is_its_size(self):
        assert effective_number_of_scenarios(np.full(500, 1 / 500)) == (
            pytest.approx(500.0)
        )

    def test_a_point_mass_uses_one_scenario(self):
        p = np.zeros(100)
        p[7] = 1.0
        assert effective_number_of_scenarios(p) == pytest.approx(1.0)

    def test_relative_entropy_is_zero_against_itself(self):
        p = np.full(50, 1 / 50)
        assert relative_entropy(p, p) == pytest.approx(0.0, abs=1e-12)

    def test_relative_entropy_is_positive_otherwise(self):
        p = np.full(50, 1 / 50)
        q = np.concatenate([np.full(25, 1.5 / 50), np.full(25, 0.5 / 50)])
        assert relative_entropy(q, p) > 0


class TestMeanView:
    def test_posterior_hits_the_stated_mean(self, scenarios):
        res = entropy_pooling([mean_view(scenarios, "TSLA", 0.03)])
        assert res.converged
        mu, _ = posterior_moments(scenarios, res.probabilities)
        assert mu["TSLA"] == pytest.approx(0.03, abs=1e-6)

    def test_probabilities_are_a_distribution(self, scenarios):
        res = entropy_pooling([mean_view(scenarios, "TSLA", 0.03)])
        assert res.probabilities.sum() == pytest.approx(1.0)
        assert (res.probabilities >= 0).all()

    def test_a_view_the_prior_already_satisfies_costs_nothing(self, scenarios):
        """Minimum relative entropy means asserting the obvious is free."""
        prior_mean = float(scenarios["TSLA"].mean())
        res = entropy_pooling([mean_view(scenarios, "TSLA", prior_mean)])
        assert res.relative_entropy == pytest.approx(0.0, abs=1e-6)
        np.testing.assert_allclose(
            res.probabilities, res.prior, atol=1e-8
        )

    def test_a_bolder_view_costs_more_entropy(self, scenarios):
        mild = entropy_pooling([mean_view(scenarios, "TSLA", 0.012)])
        bold = entropy_pooling([mean_view(scenarios, "TSLA", 0.05)])
        assert bold.relative_entropy > mild.relative_entropy
        assert bold.effective_scenarios < mild.effective_scenarios

    def test_other_assets_move_through_correlation(self, scenarios):
        """The point of pooling: a view on one name repriced the rest.

        Nothing was said about SPY, but SPY moves with TSLA in the
        scenarios, so reweighting those scenarios moves SPY too — the
        same mechanism Black-Litterman gets from Sigma, obtained here
        without assuming a distribution.
        """
        res = entropy_pooling([mean_view(scenarios, "TSLA", 0.05)])
        mu, _ = posterior_moments(scenarios, res.probabilities)
        assert mu["SPY"] != pytest.approx(float(scenarios["SPY"].mean()), abs=1e-6)


class TestProbabilityView:
    def test_reshapes_the_tail_black_litterman_cannot_touch(self, scenarios):
        """'A one-in-three chance TSLA drops more than 15%.'

        Not a statement about a mean, so the main engine has no way to
        accept it at all.
        """
        prior_p = float((scenarios["TSLA"] <= -0.15).mean())
        res = entropy_pooling([probability_view(scenarios, "TSLA", -0.15, 0.33)])
        post_p = float(
            res.probabilities[(scenarios["TSLA"] <= -0.15).to_numpy()].sum()
        )
        assert prior_p < 0.15  # the prior thought this was unlikely
        assert post_p == pytest.approx(0.33, abs=1e-6)

    def test_upside_direction(self, scenarios):
        res = entropy_pooling(
            [probability_view(scenarios, "TSLA", 0.10, 0.25, below=False)]
        )
        post = float(
            res.probabilities[(scenarios["TSLA"] >= 0.10).to_numpy()].sum()
        )
        assert post == pytest.approx(0.25, abs=1e-6)

    def test_impossible_probability_rejected(self, scenarios):
        with pytest.raises(ValueError):
            probability_view(scenarios, "TSLA", -0.15, 1.4)

    def test_a_drastic_tail_view_is_flagged_as_collapsing(self, scenarios):
        """Insisting on a tail the history barely contains has to warn.

        The posterior then rests on a handful of paths, and every number
        computed from it is that thin — which the user must be told
        rather than left to infer.
        """
        res = entropy_pooling(
            [probability_view(scenarios, "TSLA", -0.25, 0.60)]
        )
        assert res.collapsed
        assert res.confidence_cost > 1 - COLLAPSE_WARNING
        assert "WARNING" in res.summary()


class TestRankingView:
    def test_conviction_without_a_price_target(self, scenarios):
        """The most common real opinion, and the one the main flow refuses.

        Someone sure that JNJ beats TSLA but with no idea what either is
        worth cannot use a price-target engine without inventing a number.
        """
        res = entropy_pooling([ranking_view(scenarios, "JNJ", "TSLA")])
        mu, _ = posterior_moments(scenarios, res.probabilities)
        assert mu["JNJ"] >= mu["TSLA"] - 1e-8

    def test_a_ranking_the_prior_already_agrees_with_is_free(self, scenarios):
        """An inequality that already holds is slack: nothing to enforce."""
        means = scenarios.mean()
        winner, loser = means.idxmax(), means.idxmin()
        res = entropy_pooling([ranking_view(scenarios, winner, loser)])
        assert res.relative_entropy == pytest.approx(0.0, abs=1e-8)

    def test_unknown_ticker_rejected(self, scenarios):
        with pytest.raises(KeyError):
            ranking_view(scenarios, "ZZZZ", "TSLA")


class TestVolatilityView:
    def test_raises_implied_volatility(self, scenarios):
        prior_vol = float(np.sqrt((scenarios["TSLA"] ** 2).mean()))
        res = entropy_pooling(
            [volatility_view(scenarios, "TSLA", prior_vol * 1.4)]
        )
        post_second = float(res.probabilities @ (scenarios["TSLA"] ** 2))
        assert np.sqrt(post_second) == pytest.approx(prior_vol * 1.4, rel=1e-6)


class TestConditionalView:
    def test_states_a_crash_relationship(self, crypto):
        """'If Bitcoin falls 20%, Ethereum falls at least as far.'

        The correlation that matters, and the one a full-sample
        covariance matrix understates because it only shows up in the
        scenarios where the condition holds.
        """
        mask = (crypto["BTC/USD"] <= -0.20).to_numpy()
        prior = float(crypto["ETH/USD"].to_numpy()[mask].mean())
        res = entropy_pooling(
            [conditional_view(crypto, "BTC/USD", -0.20, "ETH/USD", -0.30)]
        )
        w = res.probabilities[mask]
        post = float((crypto["ETH/USD"].to_numpy()[mask] * w).sum() / w.sum())
        assert post == pytest.approx(-0.30, abs=1e-5)
        assert prior > post  # the view is more pessimistic than history

    def test_refuses_to_condition_on_almost_nothing(self, crypto):
        with pytest.raises(ValueError, match="not enough history"):
            conditional_view(crypto, "BTC/USD", -0.95, "ETH/USD", -0.50)


class TestMultipleViews:
    def test_several_views_are_satisfied_together(self, scenarios):
        views = [
            mean_view(scenarios, "TSLA", 0.02),
            probability_view(scenarios, "SPY", -0.08, 0.10),
            ranking_view(scenarios, "MSFT", "AAPL"),
        ]
        res = entropy_pooling(views)
        assert res.converged
        mu, _ = posterior_moments(scenarios, res.probabilities)
        assert mu["TSLA"] == pytest.approx(0.02, abs=1e-5)
        post_p = float(
            res.probabilities[(scenarios["SPY"] <= -0.08).to_numpy()].sum()
        )
        assert post_p == pytest.approx(0.10, abs=1e-5)
        assert mu["MSFT"] >= mu["AAPL"] - 1e-8

    def test_more_views_cost_more_than_fewer(self, scenarios):
        one = entropy_pooling([mean_view(scenarios, "TSLA", 0.03)])
        two = entropy_pooling(
            [
                mean_view(scenarios, "TSLA", 0.03),
                probability_view(scenarios, "SPY", -0.08, 0.15),
            ]
        )
        assert two.relative_entropy >= one.relative_entropy

    def test_no_views_returns_the_prior(self, scenarios):
        res = entropy_pooling([], n_scenarios=len(scenarios))
        assert res.relative_entropy == 0.0
        assert res.effective_scenarios == pytest.approx(len(scenarios))

    def test_mismatched_view_lengths_rejected(self, scenarios):
        from hone.optimization.entropy_pooling import View

        with pytest.raises(ValueError):
            entropy_pooling(
                [
                    mean_view(scenarios, "TSLA", 0.02),
                    View("bogus", np.ones(5), 1.0),
                ]
            )


class TestChainingToTheOptimizer:
    def test_pooled_posterior_drives_a_cvar_portfolio(self, crypto):
        """The path the whole module exists for.

        Empirical scenarios -> entropy-pooled posterior -> CVaR
        optimization assumes normality at no point along the way.
        """
        res = entropy_pooling(
            [probability_view(crypto, "BTC/USD", -0.25, 0.20)]
        )
        resampled = resample_scenarios(crypto, res.probabilities, seed=1)
        assert len(resampled) == len(crypto)
        stressed = min_cvar_weights(resampled, max_weight=0.35)
        base = min_cvar_weights(crypto, max_weight=0.35)
        # a heavier BTC tail must make the tail-optimal portfolio worse
        assert stressed.cvar > base.cvar

    def test_posterior_moments_feed_the_variance_engine(self, scenarios):
        res = entropy_pooling([mean_view(scenarios, "TSLA", 0.03)])
        mu, cov = posterior_moments(scenarios, res.probabilities)
        assert list(mu.index) == list(scenarios.columns)
        assert cov.shape == (len(scenarios.columns),) * 2
        # a covariance matrix has to be symmetric positive semi-definite
        np.testing.assert_allclose(cov.to_numpy(), cov.to_numpy().T, atol=1e-12)
        assert np.linalg.eigvalsh(cov.to_numpy()).min() > -1e-10

    def test_resampling_preserves_the_posterior_mean_approximately(
        self, scenarios
    ):
        res = entropy_pooling([mean_view(scenarios, "TSLA", 0.03)])
        drawn = resample_scenarios(scenarios, res.probabilities, size=40000, seed=3)
        assert float(drawn["TSLA"].mean()) == pytest.approx(0.03, abs=0.004)


class TestPoolingEndpoint:
    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient

        from hone.web.app import create_app

        return TestClient(create_app())

    def _post(self, client, views, path="/api/pooling", **kw):
        payload = {"views": views, "gamma": 2.5, "demo": True}
        payload.update(kw)
        return client.post(path, json=payload)

    def test_probability_view_end_to_end(self, client):
        res = self._post(
            client,
            [{"kind": "probability", "ticker": "TSLA",
              "threshold": -0.15, "value": 0.30}],
        )
        assert res.status_code == 200
        body = res.json()
        view = body["views"][0]
        assert view["achieved"] == pytest.approx(0.30, abs=1e-5)
        assert view["satisfied"]
        assert body["effective_scenarios"] < body["prior_effective_scenarios"]
        assert body["confidence_cost"] > 0
        # a heavier TSLA tail must reprice TSLA downward
        tilts = {r["symbol"]: r["tilt"] for r in body["prior_mu"]}
        assert tilts["TSLA"] < 0

    def test_ranking_view_needs_no_price_target(self, client):
        res = self._post(
            client, [{"kind": "ranking", "ticker": "JNJ", "versus": "TSLA"}]
        )
        assert res.status_code == 200
        body = res.json()
        assert body["views"][0]["satisfied"]
        mu = {r["symbol"]: r["posterior"] for r in body["prior_mu"]}
        assert mu["JNJ"] >= mu["TSLA"] - 1e-8

    def test_conditional_crash_view_in_crypto(self, client):
        res = self._post(
            client,
            [{"kind": "conditional", "ticker": "BTC/USD", "threshold": -0.20,
              "versus": "ETH/USD", "value": -0.35}],
            path="/api/pooling?asset_class=crypto",
        )
        assert res.status_code == 200
        body = res.json()
        assert body["views"][0]["satisfied"]
        assert body["cvar_before"] > 0 and body["cvar_after"] > 0

    def test_weights_are_a_valid_portfolio(self, client):
        body = self._post(
            client,
            [{"kind": "probability", "ticker": "SPY",
              "threshold": -0.08, "value": 0.15}],
            max_weight=0.3,
        ).json()
        total = sum(w["target"] for w in body["weights"])
        assert total == pytest.approx(1.0, abs=1e-4)
        assert all(-1e-9 <= w["target"] <= 0.3 + 1e-6 for w in body["weights"])

    def test_the_cost_of_the_views_is_disclosed(self, client):
        """A view the history barely supports has to say what it cost."""
        body = self._post(
            client,
            [{"kind": "probability", "ticker": "TSLA",
              "threshold": -0.25, "value": 0.60}],
        ).json()
        assert body["collapsed"] is True
        assert body["confidence_cost"] > 0.5
        assert "thin" in body["summary"]

    def test_unknown_ticker_lists_what_is_available(self, client):
        res = self._post(client, [{"kind": "mean", "ticker": "ZZZZ", "value": 0.1}])
        assert res.status_code == 422
        assert "Available here" in res.json()["detail"]

    def test_unknown_view_kind_rejected(self, client):
        res = self._post(client, [{"kind": "vibes", "ticker": "TSLA"}])
        assert res.status_code == 422

    def test_no_views_rejected(self, client):
        assert self._post(client, []).status_code == 422

    def test_impossible_conditioning_is_explained(self, client):
        res = self._post(
            client,
            [{"kind": "conditional", "ticker": "BTC/USD", "threshold": -0.95,
              "versus": "ETH/USD", "value": -0.5}],
            path="/api/pooling?asset_class=crypto",
        )
        assert res.status_code == 422
        assert "not enough history" in res.json()["detail"]


class TestFlexibleViewsPage:
    @pytest.fixture(scope="class")
    def html(self):
        from fastapi.testclient import TestClient

        from hone.web.app import create_app

        return TestClient(create_app()).get("/").text

    def test_page_exists_and_is_reachable_from_the_main_flow(self, html):
        assert "PAGES.flexible" in html
        assert '"flexible"' in html
        assert "/api/pooling" in html
        assert 'href="#/flexible"' in html

    def test_offers_every_view_type_the_backend_supports(self, html):
        for kind in ("probability", "ranking", "conditional", "volatility", "mean"):
            assert f'value="{kind}"' in html

    def test_explains_the_cost_rather_than_hiding_it(self, html):
        assert "Views only ever cost history" in html
        assert "stress test rather" in html

    def test_paired_dropdowns_do_not_both_default_to_the_same_symbol(self, html):
        """"If BTC falls, BTC falls" is degenerate and looks broken."""
        assert "function shiftFirst" in html
        assert 'sym("…then this", "fx-b", true)' in html
        assert 'sym("…against this one", "fx-b", true)' in html
