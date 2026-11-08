"""Hone's math, checked against independent, widely used libraries.

Tests written by the same author as the code share that author's blind
spots. These compare Hone against code written by other people and used by
thousands: PyPortfolioOpt (portfolio optimization, Black-Litterman, CVaR)
and scikit-learn (Ledoit-Wolf covariance). If one of these fails, either
Hone has a bug or the libraries changed behaviour — both worth knowing.

Two kinds of check:
* **Engine vs. reference** — Hone now *uses* PyPortfolioOpt/sklearn as its
  engine, with its own code as a fallback. Each test runs both and
  requires them to agree, so the fallback stays correct.
* **Ground truth** — where the libraries and Hone could share a mistake
  (they implement the same formula), compare against a 50-digit
  computation instead.

To change a tolerance, read the comment beside it first: each one says
what size of disagreement it tolerates and why.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

pypfopt = pytest.importorskip("pypfopt")
from pypfopt import EfficientCVaR, EfficientFrontier  # noqa: E402
from pypfopt import black_litterman as pbl  # noqa: E402
from sklearn.covariance import ledoit_wolf  # noqa: E402

from hone.market_data.covariance import (  # noqa: E402
    _ledoit_wolf_hone,
    returns_from_prices,
    shrinkage_covariance,
)
from hone.optimization.black_litterman import (  # noqa: E402
    black_litterman_posterior,
    idzorek_omega,
    implied_equilibrium_returns,
)
from hone.optimization.cvar import (  # noqa: E402
    cvar_of_weights,
    historical_scenarios,
    min_cvar_weights,
)
from hone.optimization.mvo import mvo_weights  # noqa: E402
from hone.optimization.views import View, build_view_matrices  # noqa: E402
from hone.pipeline import synthetic_universe  # noqa: E402

# cvxpy warns about solver details that don't affect the answers checked here.
pytestmark = pytest.mark.filterwarnings("ignore")


# ------------------------------------------------------------------ fixtures
@pytest.fixture(scope="module")
def market():
    """Hone's own sample universe: prices, current weights, covariance."""
    prices, weights = synthetic_universe()
    returns = returns_from_prices(prices)
    sigma = shrinkage_covariance(returns)
    return prices, returns, weights.reindex(sigma.index).fillna(0.0), sigma


def _views(prices, syms, confidence=0.6):
    last = prices.iloc[-1]
    return [
        View(syms[0], last[syms[0]], last[syms[0]] * 1.25, confidence),
        View(syms[2], last[syms[2]], last[syms[2]] * 0.90, confidence / 2),
    ]


def _utility(w, mu, sigma, gamma):
    w = np.asarray(w, dtype=float)
    return float(w @ mu - 0.5 * gamma * w @ sigma @ w)


def _random_problem(rng, n, gamma=None):
    """A realistic covariance: a few shared factors plus asset-specific noise."""
    k = max(2, n // 6)
    b = rng.normal(size=(n, k))
    sigma = b @ np.diag(rng.uniform(0.01, 0.06, k)) @ b.T + np.diag(rng.uniform(0.001, 0.05, n))
    mu = rng.normal(0.07, 0.08, n)
    idx = [f"A{i}" for i in range(n)]
    g = gamma if gamma is not None else float(rng.uniform(0.5, 10))
    return pd.Series(mu, idx), pd.DataFrame(sigma, idx, idx), g


# ---------------------------------------------------------------- covariance
class TestCovariance:
    def test_ledoit_wolf_matches_sklearn(self, market):
        _, returns, _, _ = market
        x = returns.to_numpy()
        ref, _ = ledoit_wolf(x)
        # Floating-point noise only: the same estimator, two implementations.
        assert np.allclose(_ledoit_wolf_hone(x), ref, rtol=1e-10, atol=1e-16)
        assert np.allclose(shrinkage_covariance(returns, annualize=None), ref, rtol=1e-12, atol=1e-18)

    def test_ledoit_wolf_on_random_data(self):
        rng = np.random.default_rng(3)
        for n, t in [(3, 30), (12, 100), (40, 260)]:
            x = rng.standard_t(4, size=(t, n)) * 0.01   # fat tails, like real returns
            assert np.allclose(_ledoit_wolf_hone(x), ledoit_wolf(x)[0], rtol=1e-9, atol=1e-16)


# ------------------------------------------------------------ Black-Litterman
class TestBlackLitterman:
    def test_implied_returns_match(self, market):
        _, _, w0, sigma = market
        ours = implied_equilibrium_returns(sigma, w0, 2.5)
        theirs = pbl.market_implied_prior_returns(w0, 2.5, sigma, risk_free_rate=0.0)
        assert np.allclose(ours, theirs.reindex(ours.index), atol=1e-14)

    def test_confidence_mapping_is_pypfopts_idzorek(self, market):
        """Hone's confidence -> Omega is PyPortfolioOpt's closed-form Idzorek."""
        prices, _, w0, sigma = market
        views = _views(prices, list(sigma.index))
        p, q, conf = build_view_matrices(views, list(sigma.index))
        model = pbl.BlackLittermanModel(
            sigma, pi=implied_equilibrium_returns(sigma, w0, 2.5), P=p, Q=q,
            omega="idzorek", view_confidences=conf, tau=0.05,
        )
        assert np.allclose(idzorek_omega(p, sigma.to_numpy(), conf, 0.05), model.omega, atol=1e-16)

    @pytest.mark.parametrize("confidence", [0.2, 0.6, 0.95, 0.999, 1.0])
    def test_engine_and_fallback_agree(self, market, confidence):
        prices, _, w0, sigma = market
        views = _views(prices, list(sigma.index), confidence)
        a = black_litterman_posterior(sigma, w0, views, delta=2.5, engine="pypfopt")
        b = black_litterman_posterior(sigma, w0, views, delta=2.5, engine="hone")
        assert a.engine == "pypfopt" and b.engine == "hone"
        assert np.allclose(a.posterior_mu, b.posterior_mu, atol=1e-12)
        assert np.allclose(a.posterior_sigma, b.posterior_sigma, atol=1e-12)

    def test_near_duplicate_assets_against_50_digit_truth(self, market):
        """Regression: the old formula inverted tau*Sigma and was off by ~0.4
        percentage points when two holdings move almost identically (SPY/VOO,
        GOOG/GOOGL). Both engines must now match a 50-digit computation."""
        mp = pytest.importorskip("mpmath")
        prices, _, w0, sigma = market
        s2 = sigma.copy()
        a, b = s2.index[0], s2.index[1]
        s2.loc[b] = s2.loc[a] * 1.0000001
        s2[b] = s2.loc[b]
        s2.loc[b, b] = s2.loc[a, a] * 1.0000002
        assert np.linalg.cond(s2.to_numpy()) > 1e12   # genuinely near-singular

        views = [View(s2.index[3], prices.iloc[-1][s2.index[3]], prices.iloc[-1][s2.index[3]] * 1.3, 0.6)]
        p, q, conf = build_view_matrices(views, list(s2.index))
        omega = idzorek_omega(p, s2.to_numpy(), conf, 0.05)
        pi = implied_equilibrium_returns(s2, w0, 2.5)

        mp.mp.dps = 50
        S, P, Q = mp.matrix(s2.to_numpy().tolist()), mp.matrix(p.tolist()), mp.matrix(q.tolist())
        PI, OM, tau = mp.matrix(pi.to_numpy().tolist()), mp.matrix(omega.tolist()), mp.mpf("0.05")
        truth = PI + tau * S * P.T * (P * (tau * S) * P.T + OM) ** -1 * (Q - P * PI)
        truth = np.array([float(v) for v in truth])

        for engine in ("pypfopt", "hone"):
            got = black_litterman_posterior(s2, w0, views, delta=2.5, engine=engine).posterior_mu
            # 1e-10 is ~a millionth of a basis point; the old code was off by 4e-3.
            assert np.abs(got.to_numpy() - truth).max() < 1e-10, engine


# -------------------------------------------------------------------- MVO
class TestMeanVariance:
    def test_engine_matches_slsqp_on_sample_data(self, market):
        prices, _, w0, sigma = market
        bl = black_litterman_posterior(sigma, w0, _views(prices, list(sigma.index)), delta=2.5)
        a = mvo_weights(bl.posterior_mu, bl.posterior_sigma, 3.0, max_weight=0.35, engine="pypfopt")
        b = mvo_weights(bl.posterior_mu, bl.posterior_sigma, 3.0, max_weight=0.35, engine="hone")
        assert a.engine == "pypfopt" and b.engine == "hone-slsqp"
        # Weights within 0.01 percentage points: solver tolerance, not a disagreement.
        assert np.abs(a.weights - b.weights).max() < 1e-4

    def test_default_engine_is_pypfopt(self, market):
        _, returns, _, sigma = market
        assert mvo_weights(returns.mean() * 252, sigma, 3.0).engine == "pypfopt"

    @pytest.mark.parametrize("case", ["typical", "large", "shorts", "extreme_gamma"])
    def test_neither_solver_beats_the_other(self, case):
        """On random problems, the two solvers reach the same utility.

        Utility, not weights: when two assets are interchangeable the best
        weights aren't unique, but the best achievable utility is.
        """
        rng = np.random.default_rng({"typical": 1, "large": 2, "shorts": 3, "extreme_gamma": 4}[case])
        for _ in range(25):
            n = int(rng.integers(40, 90)) if case == "large" else int(rng.integers(4, 25))
            gamma = float(rng.choice([0.05, 60.0])) if case == "extreme_gamma" else None
            mu, sigma, g = _random_problem(rng, n, gamma)
            long_only = case != "shorts"
            cap = 0.35 if long_only and n * 0.35 >= 1 else None
            a = mvo_weights(mu, sigma, g, long_only=long_only, max_weight=cap, engine="pypfopt")
            b = mvo_weights(mu, sigma, g, long_only=long_only, max_weight=cap, engine="hone")
            ua, ub = (_utility(r.weights, mu, sigma, r.gamma) for r in (a, b))
            # 1e-7 of annual utility = 0.001 basis points.
            assert abs(ua - ub) < 1e-7, (case, ua, ub)
            assert abs(a.weights.sum() - 1) < 1e-9
            if cap:
                assert a.weights.max() <= cap + 1e-7

    def test_independent_library_agrees_with_both(self, market):
        """PyPortfolioOpt called directly, not through Hone's wrapper."""
        _, returns, _, sigma = market
        mu = returns.mean() * 252
        ref = EfficientFrontier(mu, sigma, weight_bounds=(0, 0.4)).max_quadratic_utility(risk_aversion=4.0)
        ref = pd.Series(ref).reindex(mu.index)
        for engine in ("auto", "hone"):
            got = mvo_weights(mu, sigma, 4.0, max_weight=0.4, engine=engine).weights
            assert np.abs(got - ref).max() < 1e-4, engine

    def test_impossible_cap_falls_back_and_says_so(self, market):
        """A 15% cap on 5 assets can't sum to 100%: same behaviour as before
        the engine change — SLSQP tries, and reports it didn't converge."""
        _, returns, _, sigma = market
        res = mvo_weights(returns.mean() * 252, sigma, 3.0, max_weight=0.15)
        assert res.engine == "hone-slsqp" and res.converged is False


# ------------------------------------------------------------------- CVaR
class TestCVaR:
    def test_min_cvar_matches_pypfopt(self, market):
        """Hone keeps its own CVaR linear program (it already uses HiGHS, an
        exact LP solver — the library would add nothing). Checked anyway."""
        prices, _, _, _ = market
        scenarios = historical_scenarios(prices)
        ours = min_cvar_weights(scenarios, beta=0.95, max_weight=0.5)
        ec = EfficientCVaR(scenarios.mean(), scenarios, beta=0.95, weight_bounds=(0, 0.5))
        theirs = pd.Series(ec.min_cvar()).reindex(scenarios.columns)
        # Same tail risk to within 1e-6 (a ten-thousandth of a percent).
        assert abs(ours.cvar - cvar_of_weights(scenarios, theirs)) < 1e-6
        # PyPortfolioOpt reports the Rockafellar-Uryasev objective, which
        # averages a *fractional* tail ((1-beta)*T = 25.15 days here); Hone
        # reports the average of the worst round((1-beta)*T) = 25 days. The
        # two conventions differ by a fraction of a percent of the figure.
        assert abs(ec.portfolio_performance()[1] - ours.cvar) / ours.cvar < 0.01
