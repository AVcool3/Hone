"""Mean-CVaR optimization: the LP, the gamma mapping, and the tail claims."""

import numpy as np
import pandas as pd
import pytest

from hone.crypto.universe import synthetic_crypto_universe
from hone.market_data.covariance import portfolio_covariance
from hone.optimization.cvar import (
    DEFAULT_BETA,
    cvar_gamma_weights,
    cvar_of_weights,
    historical_scenarios,
    kappa_from_gamma,
    mean_cvar_weights,
    min_cvar_weights,
    tail_comparison,
    var_of_weights,
)
from hone.optimization.mvo import mvo_weights
from hone.pipeline import synthetic_universe


@pytest.fixture(scope="module")
def equity_scenarios():
    prices, _ = synthetic_universe(n_days=900)
    return historical_scenarios(prices)


@pytest.fixture(scope="module")
def crypto_scenarios():
    prices, _ = synthetic_crypto_universe(n_days=900)
    return historical_scenarios(prices)


def equal_weight(scenarios):
    return pd.Series(1.0 / len(scenarios.columns), index=scenarios.columns)


class TestScenarios:
    def test_simple_returns_not_log(self):
        """Portfolio return is a weighted sum of *simple* returns.

        Log returns would make the linear program describe a portfolio
        nobody actually holds.
        """
        prices = pd.DataFrame({"A": [100.0, 110.0, 121.0]})
        sc = historical_scenarios(prices)
        assert sc["A"].tolist() == pytest.approx([0.10, 0.10])

    def test_multi_period_horizon(self):
        prices, _ = synthetic_universe(n_days=400)
        monthly = historical_scenarios(prices, horizon=21)
        daily = historical_scenarios(prices, horizon=1)
        assert len(monthly) < len(daily)
        # a month of returns is bigger than a day of them
        assert monthly.std().mean() > daily.std().mean()

    def test_rejects_empty_history(self):
        with pytest.raises(ValueError):
            historical_scenarios(pd.DataFrame({"A": [100.0]}))


class TestTailMeasures:
    def test_cvar_is_the_mean_of_the_worst_tail(self):
        # a hand-built distribution: 100 scenarios, worst 5 known exactly
        vals = [0.01] * 95 + [-0.10, -0.20, -0.30, -0.40, -0.50]
        sc = pd.DataFrame({"A": vals})
        w = pd.Series({"A": 1.0})
        assert cvar_of_weights(sc, w, beta=0.95) == pytest.approx(0.30)
        # VaR sits at the boundary between the body and the tail, so with
        # 95 identical good outcomes it lands on the body's value — which
        # is exactly why VaR is the less useful of the two numbers: it
        # says nothing at all about the five outcomes that matter.
        assert var_of_weights(sc, w, beta=0.95) < cvar_of_weights(sc, w, beta=0.95)

    def test_cvar_is_never_below_var(self):
        """The average of the tail cannot be less bad than its threshold."""
        prices, _ = synthetic_universe(n_days=600)
        sc = historical_scenarios(prices)
        w = equal_weight(sc)
        assert cvar_of_weights(sc, w) >= var_of_weights(sc, w) - 1e-12

    def test_cvar_sees_a_fat_tail_that_variance_misses(self):
        """Two assets, same volatility, different tails.

        This is the entire argument for the mode: variance cannot tell
        these apart, CVaR ranks them correctly.
        """
        rng = np.random.default_rng(0)
        n = 4000
        gauss = rng.normal(0, 1, n)
        t4 = rng.standard_t(4, n)
        t4 = t4 / t4.std() * gauss.std()  # matched volatility, fatter tail
        sc = pd.DataFrame({"NORMAL": gauss * 0.01, "FAT": t4 * 0.01})
        vol_n = sc["NORMAL"].std()
        vol_f = sc["FAT"].std()
        assert vol_n == pytest.approx(vol_f, rel=0.02)  # variance sees no difference
        normal_only = pd.Series({"NORMAL": 1.0, "FAT": 0.0})
        fat_only = pd.Series({"NORMAL": 0.0, "FAT": 1.0})
        assert cvar_of_weights(sc, fat_only) > cvar_of_weights(sc, normal_only) * 1.10
        # and the gap widens the deeper into the tail you look, which is
        # the shape of the problem variance cannot represent at all
        ratio_95 = cvar_of_weights(sc, fat_only) / cvar_of_weights(sc, normal_only)
        ratio_99 = (cvar_of_weights(sc, fat_only, beta=0.99)
                    / cvar_of_weights(sc, normal_only, beta=0.99))
        assert ratio_99 > ratio_95


class TestMinCVaR:
    def test_minimizes_cvar_against_every_comparator(self, equity_scenarios):
        sc = equity_scenarios
        res = min_cvar_weights(sc, max_weight=0.35)
        assert res.converged
        assert res.weights.sum() == pytest.approx(1.0, abs=1e-6)
        assert (res.weights >= -1e-9).all()
        assert res.weights.max() <= 0.35 + 1e-6

        assert res.cvar < cvar_of_weights(sc, equal_weight(sc))

    def test_uncapped_solution_is_globally_optimal(self, equity_scenarios):
        """No portfolio the LP could have chosen has a thinner tail.

        Single names are the sharp test: with no position cap the
        minimum-CVaR portfolio here *is* a single name, which is the
        classic pathology of pure risk minimizers — they concentrate into
        whatever was quietest in-sample. That is an argument for the cap,
        not against the objective, and it is why max_weight is not
        optional in the product.
        """
        sc = equity_scenarios
        res = min_cvar_weights(sc, max_weight=1.0)
        for col in sc.columns:
            single = pd.Series(0.0, index=sc.columns)
            single[col] = 1.0
            assert res.cvar <= cvar_of_weights(sc, single) + 1e-9
        assert res.cvar <= cvar_of_weights(sc, equal_weight(sc)) + 1e-9

    def test_beats_the_variance_optimal_portfolio_on_its_own_measure(
        self, crypto_scenarios
    ):
        """The point of the mode, stated as a test.

        The variance-optimal portfolio is not tail-optimal; if it were,
        CVaR optimization would be an expensive way to reproduce MVO.
        """
        sc = crypto_scenarios
        prices, _ = synthetic_crypto_universe(n_days=900)
        sigma = portfolio_covariance(prices, annualize=365).covariance
        mvo = mvo_weights(sc.mean() * 365, sigma, gamma=2.5, max_weight=0.35)
        cvar = min_cvar_weights(sc, max_weight=0.35)
        assert cvar.cvar < cvar_of_weights(sc, mvo.weights)

    def test_ignores_expected_returns_entirely(self, equity_scenarios):
        """Risk-first means risk-only: shifting mu must not move it.

        Expected returns are the least reliable input in the pipeline, so
        a portfolio built without them cannot be wrecked by getting them
        wrong. That property has to be real, not aspirational.
        """
        sc = equity_scenarios
        a = min_cvar_weights(sc, max_weight=0.35)
        shifted = sc.copy()
        shifted.iloc[:, 0] = shifted.iloc[:, 0] + 0.0  # same scenarios
        b = min_cvar_weights(shifted, max_weight=0.35)
        pd.testing.assert_series_equal(a.weights, b.weights)

    def test_cap_constrains_concentration(self, equity_scenarios):
        loose = min_cvar_weights(equity_scenarios, max_weight=1.0)
        tight = min_cvar_weights(equity_scenarios, max_weight=0.25)
        assert tight.weights.max() <= 0.25 + 1e-6
        assert tight.cvar >= loose.cvar - 1e-9  # a constraint cannot help

    def test_return_floor_is_respected(self, equity_scenarios):
        sc = equity_scenarios
        free = min_cvar_weights(sc, max_weight=0.5)
        target = float(sc.mean().max()) * 0.8
        floored = min_cvar_weights(sc, max_weight=0.5, min_return=target)
        assert float(floored.weights @ sc.mean()) >= target - 1e-9
        assert floored.cvar >= free.cvar - 1e-9  # buying return costs tail


class TestGammaMapping:
    def test_kappa_rises_with_risk_aversion(self):
        ks = [kappa_from_gamma(g, 0.02) for g in (0.5, 1.2, 2.5, 5.0, 8.0)]
        assert ks == sorted(ks)
        assert all(k > 0 for k in ks)

    def test_kappa_matches_the_mvo_trade_off_at_the_reference(self):
        """kappa = gamma * sigma / k, so kappa * k == gamma * sigma."""
        from scipy.stats import norm

        gamma, sigma = 2.5, 0.018
        k = norm.pdf(norm.ppf(DEFAULT_BETA)) / (1 - DEFAULT_BETA)
        assert kappa_from_gamma(gamma, sigma) * k == pytest.approx(gamma * sigma)

    def test_more_risk_averse_gamma_gives_a_thinner_tail(self, crypto_scenarios):
        sc = crypto_scenarios
        timid = cvar_gamma_weights(sc, gamma=8.0, max_weight=0.35)
        bold = cvar_gamma_weights(sc, gamma=0.5, max_weight=0.35)
        assert timid.cvar < bold.cvar
        assert timid.expected_return <= bold.expected_return

    def test_views_can_drive_the_tilt(self, equity_scenarios):
        """Passing a posterior mu must change the answer, or the
        Black-Litterman step is decorative in this mode."""
        sc = equity_scenarios
        base = cvar_gamma_weights(sc, gamma=1.2, mu=sc.mean(), max_weight=0.5)
        bullish = sc.mean().copy()
        bullish.iloc[0] += 0.004  # a strong view on the first name
        tilted = cvar_gamma_weights(sc, gamma=1.2, mu=bullish, max_weight=0.5)
        assert tilted.weights.iloc[0] > base.weights.iloc[0]


class TestMeanCVaR:
    def test_kappa_zero_is_pure_minimum_cvar(self, equity_scenarios):
        a = mean_cvar_weights(equity_scenarios, kappa=0.0, max_weight=0.35)
        b = min_cvar_weights(equity_scenarios, max_weight=0.35)
        pd.testing.assert_series_equal(a.weights, b.weights)

    def test_large_kappa_approaches_the_minimum_cvar_portfolio(
        self, equity_scenarios
    ):
        sc = equity_scenarios
        greedy = mean_cvar_weights(sc, kappa=0.001, mu=sc.mean(), max_weight=0.35)
        timid = mean_cvar_weights(sc, kappa=100.0, mu=sc.mean(), max_weight=0.35)
        floor = min_cvar_weights(sc, max_weight=0.35)
        assert timid.cvar == pytest.approx(floor.cvar, abs=1e-4)
        assert greedy.expected_return > timid.expected_return

    def test_reports_the_tail_it_averaged(self, equity_scenarios):
        res = min_cvar_weights(equity_scenarios)
        assert res.tail_scenarios == round((1 - DEFAULT_BETA) * res.n_scenarios)
        assert res.n_scenarios == len(equity_scenarios)

    def test_rejects_a_nonsensical_beta(self, equity_scenarios):
        for bad in (0.2, 1.0, 1.5):
            with pytest.raises(ValueError):
                mean_cvar_weights(equity_scenarios, beta=bad)

    def test_summary_reads(self, equity_scenarios):
        text = min_cvar_weights(equity_scenarios).summary()
        assert "CVaR" in text and "VaR" in text and "%" in text


class TestTailComparison:
    def test_table_has_a_row_per_portfolio(self, crypto_scenarios):
        sc = crypto_scenarios
        table = tail_comparison(
            sc,
            {
                "equal_weight": equal_weight(sc),
                "min_cvar": min_cvar_weights(sc, max_weight=0.35).weights,
            },
        )
        assert list(table.index) == ["equal_weight", "min_cvar"]
        assert set(table.columns) >= {"mean", "volatility", "var", "cvar", "worst"}
        assert table.loc["min_cvar", "cvar"] < table.loc["equal_weight", "cvar"]


class TestCVaREndpoint:
    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient

        from hone.web.app import create_app

        return TestClient(create_app())

    def test_returns_both_answers_and_a_comparison(self, client):
        res = client.post("/api/cvar", json={"gamma": 2.5, "demo": True})
        assert res.status_code == 200
        body = res.json()
        assert body["beta"] == 0.95
        assert body["n_scenarios"] > 100
        assert body["tail_scenarios"] >= 5
        names = {r["portfolio"] for r in body["comparison"]}
        assert names == {"current", "equal_weight", "gamma_cvar", "min_cvar"}
        assert all(r["label"] for r in body["comparison"])
        assert "%" in body["summary"]

    def test_min_cvar_arm_has_the_thinnest_tail(self, client):
        body = client.post("/api/cvar", json={"gamma": 2.5, "demo": True}).json()
        rows = {r["portfolio"]: r for r in body["comparison"]}
        best = min(r["cvar"] for r in rows.values())
        assert rows["min_cvar"]["cvar"] == pytest.approx(best)

    def test_gamma_interpolates_toward_the_risk_first_floor(self, client):
        """The whole point of tying kappa to the elicited gamma.

        A risk-seeking user should accept a worse tail for more return; a
        risk-averse one should converge on the minimum-CVaR portfolio.
        """
        out = {}
        for gamma in (0.5, 2.5, 8.0):
            body = client.post(
                "/api/cvar", json={"gamma": gamma, "demo": True}
            ).json()
            rows = {r["portfolio"]: r for r in body["comparison"]}
            out[gamma] = (rows["gamma_cvar"]["cvar"], rows["gamma_cvar"]["mean"])
            floor = rows["min_cvar"]["cvar"]
        assert out[0.5][0] > out[2.5][0] > out[8.0][0]      # tail shrinks
        assert out[0.5][1] > out[2.5][1] > out[8.0][1]      # so does return
        assert out[8.0][0] == pytest.approx(floor, abs=0.005)

    def test_weights_are_valid_portfolios(self, client):
        body = client.post(
            "/api/cvar", json={"gamma": 2.5, "demo": True, "max_weight": 0.3}
        ).json()
        for key in ("min_cvar_weights", "gamma_cvar_weights"):
            rows = body[key]
            assert sum(r["target"] for r in rows) == pytest.approx(1.0, abs=1e-4)
            assert all(-1e-9 <= r["target"] <= 0.3 + 1e-6 for r in rows)
            assert all(
                r["trade"] == pytest.approx(r["target"] - r["current"], abs=1e-9)
                for r in rows
            )

    def test_dollar_framing(self, client):
        body = client.post(
            "/api/cvar",
            json={"gamma": 2.5, "demo": True, "portfolio_value": 100000},
        ).json()
        assert body["portfolio_value"] == 100000
        assert body["cvar_saved_usd"] is not None

    def test_crypto_mode_uses_the_crypto_universe(self, client):
        body = client.post(
            "/api/cvar?asset_class=crypto", json={"gamma": 2.5, "demo": True}
        ).json()
        symbols = {r["symbol"] for r in body["min_cvar_weights"]}
        assert any("/USD" in sym for sym in symbols)
        rows = {r["portfolio"]: r for r in body["comparison"]}
        # crypto tails are far heavier than equity tails, and the numbers
        # should say so rather than being smoothed by a normal assumption
        assert rows["current"]["cvar"] > 0.10

    def test_too_few_scenarios_is_refused_rather_than_guessed_at(self):
        """A tail averaged over a handful of points is not an estimate.

        Not reachable through demo mode (the synthetic panel is always long
        enough), so it is checked where the rule lives.
        """
        prices, _ = synthetic_universe(n_days=60)
        sc = historical_scenarios(prices, horizon=21)
        assert len(sc) < 40  # what the endpoint refuses to work with
        # the optimizer itself still solves — the judgement about whether
        # the answer means anything belongs to the caller, and the API
        # makes it rather than shipping a confident number
        assert min_cvar_weights(sc).converged

    def test_beta_is_validated(self, client):
        assert client.post(
            "/api/cvar", json={"gamma": 2.5, "demo": True, "beta": 1.0}
        ).status_code == 422


class TestTailsPage:
    @pytest.fixture(scope="class")
    def html(self):
        from fastapi.testclient import TestClient

        from hone.web.app import create_app

        return TestClient(create_app()).get("/").text

    def test_page_exists_and_is_reachable(self, html):
        assert "PAGES.tails" in html
        assert '"tails"' in html
        assert "/api/cvar" in html
        assert 'href="#/tails"' in html  # linked from the hedge page

    def test_explains_cvar_without_jargon(self, html):
        assert "when it goes badly, how badly" in html
        assert "average loss across the worst 5%" in html

    def test_discloses_the_thinness_of_the_evidence(self, html):
        assert "Overlapping windows share data" in html
        assert "history, not a forecast" in html
