"""Adversarial property-based tests for the income-hedging engine.

Every test draws thousands of seeded random cases with numpy's
``default_rng`` (no new dependencies) and checks a property a quant
reviewer would expect of ``hone.prediction.hedge`` / ``liquidity`` /
``contracts``.  Properties that fail because of a genuine bug are kept,
pinned to a minimal reproducing input and marked
``xfail(strict=True, reason="BUG: ...")`` so the suite stays green while
the bug is documented; the moment a bug is fixed the strict xfail turns
into an XPASS failure and the marker should be removed.

See research/prediction/findings/04_properties.md for the write-up.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from hone.prediction.contracts import kalshi_fee
from hone.prediction.hedge import (
    IncomeExposure,
    _bounds,
    _expected_utility,
    blend_belief,
    crra_certainty_equivalent,
    hedge_income,
    joint_states,
    kelly_fraction,
    optimal_contracts,
    reservation_price,
)
from hone.prediction.liquidity import (
    Liquidity,
    asks_from_orderbook,
    average_fill,
    depth_within,
    limit_for,
)

GAMMAS = (0.05, 0.3, 1.0, 1.5, 2.0, 3.5, 5.0, 20.0)


# ---------------------------------------------------------------- helpers
def _rows(plan):
    w = np.array([r.wealth_hedged for r in plan.states])
    wu = np.array([r.wealth_unhedged for r in plan.states])
    p = np.array([r.prob for r in plan.states])
    return p, wu, w


def _random_liquidity(rng, price):
    """None, open interest only, a flat book at the quoted price, or both.

    The book has a single level at exactly the quoted price on each side,
    so the fill price equals the quote; order-book *walking* is tested
    separately (it is where one of the bugs lives).
    """
    kind = rng.integers(0, 5)
    if kind == 0:
        return None
    oi = float(rng.choice([0.0, 5.0, 37.0, 480.0, 4790.0, 1e5, 1e8]))
    q_buy = float(rng.choice([0.0, 3.0, 120.0, 2500.0, 1e7]))
    q_sell = float(rng.choice([0.0, 3.0, 120.0, 2500.0, 1e7]))
    book_buy = [(price, q_buy)] if q_buy > 0 else []
    book_sell = [(round(1.0 - price, 4), q_sell)] if q_sell > 0 else []
    if kind == 1:
        return Liquidity(open_interest=oi)
    if kind == 2:
        return Liquidity(asks_buy=book_buy, asks_sell=book_sell)
    if kind == 3:
        return Liquidity(open_interest=oi, asks_buy=book_buy, asks_sell=book_sell)
    return Liquidity()  # known nothing


def _random_exposure(rng, *, liquidity=True, min_cushion=250.0):
    """A random but *valid* exposure, away from the known-bug regions that
    have their own xfail tests (gamma <= 0, a cushion under a few hundred
    dollars, order-book walking)."""
    wealth = float(10 ** rng.uniform(2.6, 7.0))
    if rng.random() < 0.1:
        loss = 0.0
    else:
        loss = float(wealth * rng.uniform(0.0, 0.97))
    loss = min(loss, max(wealth - min_cushion, 0.0))
    r = rng.random()
    price = 0.01 if r < 0.05 else 0.99 if r < 0.10 else float(np.round(rng.uniform(0.02, 0.98), 2))
    gamma = float(rng.choice(GAMMAS)) if rng.random() < 0.5 else float(rng.uniform(0.05, 6.0))
    rho = 1.0 if rng.random() < 0.2 else float(rng.uniform(0.0, 1.0))
    own = None if rng.random() < 0.5 else float(rng.uniform(0.0, 1.0))
    mkt = None if rng.random() < 0.5 else float(np.clip(price + rng.normal(0, 0.03), 0.01, 0.99))
    return IncomeExposure(
        wealth=wealth,
        loss=loss,
        price=price,
        gamma=gamma,
        market_prob=mkt,
        own_prob=own,
        confidence=float(rng.uniform(0, 1)),
        basis_correlation=rho,
        fee_multiplier=float(rng.choice([0.0, 1.0, 2.0])),
        fee_rate=float(rng.choice([0.0, 0.07])),
        allow_selling=bool(rng.random() < 0.8),
        liquidity=_random_liquidity(rng, price) if liquidity else None,
    )


@pytest.fixture(scope="module")
def sweep():
    """~1,500 random (exposure, plan) pairs shared by the accounting tests."""
    rng = np.random.default_rng(20261107)
    out = []
    for _ in range(1500):
        exp = _random_exposure(rng)
        out.append((exp, hedge_income(exp)))
    return out


# ================================================================ fees
class TestFees:
    def test_fee_rounds_up_to_the_cent_and_never_by_more_than_a_cent(self):
        rng = np.random.default_rng(1)
        for _ in range(20_000):
            n = float(rng.integers(0, 50_000))
            p = float(np.round(rng.uniform(0.01, 0.99), 2))
            m = float(rng.choice([0.0, 0.5, 1.0, 2.0]))
            raw = kalshi_fee(n, p, m, round_up=False)
            fee = kalshi_fee(n, p, m)
            assert raw == pytest.approx(0.07 * m * n * p * (1 - p))
            assert fee >= raw - 1e-9
            assert fee - raw < 0.01 + 1e-9
            assert abs(fee * 100 - round(fee * 100)) < 1e-6  # whole cents

    def test_fee_symmetric_monotone_and_zero_for_nothing(self):
        rng = np.random.default_rng(2)
        for _ in range(20_000):
            n = int(rng.integers(0, 50_000))
            cents = int(rng.integers(1, 100))
            p, q = cents / 100, (100 - cents) / 100
            assert kalshi_fee(n, p) == kalshi_fee(n, q)  # buying NO at 1-p
            assert kalshi_fee(n + 1, p) >= kalshi_fee(n, p)
            assert kalshi_fee(0, p) == 0.0
        # peaked at a coin flip
        assert max(kalshi_fee(1000, c / 100) for c in range(1, 100)) == kalshi_fee(1000, 0.5)


# ============================================================== beliefs
class TestBlendBelief:
    def test_bounds_monotone_in_confidence_and_market_at_zero(self):
        rng = np.random.default_rng(3)
        for _ in range(20_000):
            m = float(rng.uniform(0.01, 0.99))
            own = float(rng.uniform(0.0, 1.0))
            k1, k2 = sorted(rng.uniform(-0.2, 1.2, size=2))  # out-of-range k is clipped
            q1, q2 = blend_belief(m, own, k1), blend_belief(m, own, k2)
            assert 0.01 <= q1 <= 0.99 and 0.01 <= q2 <= 0.99
            # more confidence moves the posterior (weakly) toward the view
            assert abs(q2 - own) <= abs(q1 - own) + 1e-12
            assert blend_belief(m, own, 0.0) == pytest.approx(m)
            assert blend_belief(m, None, 0.7) == m

    @pytest.mark.xfail(
        strict=True,
        reason="BUG (low): blend_belief clips to [0.01, 0.99] only when a view is "
        "given, so for a market price outside that band 'no view' and 'a view at "
        "confidence 0' disagree (0.995 vs 0.99) - hedge.py:116-124",
    )
    def test_confidence_zero_is_the_same_as_no_view_at_extreme_prices(self):
        for m in (0.001, 0.005, 0.995, 0.999):
            assert blend_belief(m, 0.5, 0.0) == pytest.approx(blend_belief(m, None, 0.0))
            assert 0.01 <= blend_belief(m, None, 0.0) <= 0.99


# ========================================================= joint states
class TestJointStates:
    def test_probabilities_marginals_and_frechet_clipping(self):
        rng = np.random.default_rng(4)
        for _ in range(20_000):
            qe, ql = (float(x) for x in rng.uniform(0.005, 0.995, size=2))
            rho = float(rng.uniform(-0.5, 1.5))
            states, rho_eff = joint_states(qe, ql, rho)
            probs = np.array([s.prob for s in states])
            assert np.all(probs >= 0)
            assert probs.sum() == pytest.approx(1.0, abs=1e-12)
            assert sum(s.prob for s in states if s.pays) == pytest.approx(qe, abs=1e-12)
            assert sum(s.prob for s in states if s.loss) == pytest.approx(ql, abs=1e-12)
            # independently computed Frechet upper bound: P(both) <= min(qe, ql)
            s = math.sqrt(qe * (1 - qe) * ql * (1 - ql))
            rho_max = (min(qe, ql) - qe * ql) / s
            assert rho_eff == pytest.approx(float(np.clip(rho, 0.0, rho_max)), abs=1e-12)
            assert rho_eff <= max(rho, 0.0) + 1e-12
            # the distribution really has correlation rho_eff
            p11 = next(st.prob for st in states if st.pays and st.loss)
            assert (p11 - qe * ql) / s == pytest.approx(rho_eff, abs=1e-9)

    def test_equal_marginals_never_clip(self):
        # hedge_income always calls joint_states(q, q, rho): rho_max is 1, so
        # basis_clipped can never be true from that call site.
        for q in np.linspace(0.01, 0.99, 99):
            _, rho_eff = joint_states(float(q), float(q), 1.0)
            assert rho_eff == pytest.approx(1.0)


# ==================================================== reservation price
class TestReservationPrice:
    def test_above_belief_with_exposure_equal_without(self):
        rng = np.random.default_rng(5)
        for _ in range(5_000):
            w = float(10 ** rng.uniform(2, 7))
            l = float(w * rng.uniform(0.001, 0.99))
            q = float(rng.uniform(0.01, 0.99))
            rho = float(rng.uniform(0.0, 1.0))
            g1, g2 = sorted(float(x) for x in rng.uniform(0.01, 10, size=2))
            states, rho_eff = joint_states(q, q, rho)
            c1 = reservation_price(w, l, g1, states)
            c2 = reservation_price(w, l, g2, states)
            assert q - 1e-12 <= c1 <= 1.0
            if rho_eff > 1e-3:
                assert c1 > q
            assert c2 >= c1 - 1e-12  # more averse -> pays more for cover
            assert reservation_price(w, l * 0.5, g1, states) <= c1 + 1e-12  # more loss -> pays more
            assert reservation_price(w, l, 0.0, states) == pytest.approx(q, abs=1e-12)
            assert reservation_price(w, 0.0, g1, states) == pytest.approx(q, abs=1e-12)
            # risk seekers value cover below its probability
            if rho_eff > 1e-3:
                assert reservation_price(w, l, -0.5, states) < q

    def test_reservation_price_is_where_the_first_contract_stops_paying(self):
        """At price == c_max (no fees) the optimum is ~0; just below it, buy."""
        rng = np.random.default_rng(6)
        for _ in range(300):
            w = 10_000.0
            l = float(w * rng.uniform(0.05, 0.6))
            q = float(rng.uniform(0.05, 0.9))
            g = float(rng.uniform(0.3, 5))
            rho = float(rng.uniform(0.2, 1.0))
            states, _ = joint_states(q, q, rho)
            c = reservation_price(w, l, g, states)
            if not c < 0.97:
                continue
            at = IncomeExposure(wealth=w, loss=l, price=c, market_prob=q, gamma=g,
                                basis_correlation=rho, fee_rate=0.0)
            assert abs(optimal_contracts(at, states)) < 1.0
            below = IncomeExposure(wealth=w, loss=l, price=c - 0.02, market_prob=q, gamma=g,
                                   basis_correlation=rho, fee_rate=0.0)
            assert optimal_contracts(below, states) > 0

    def test_never_buys_above_the_reservation_price(self):
        """E[U'(W0)(B - c)] < 0 for c > c_max and EU is concave, so for any
        gamma > 0 the optimum cannot be long - view or no view (c_max is
        computed with the blended belief).  The 'exists only because you
        believe the market is underpricing' warning is therefore reachable
        only on the gamma <= 0 path."""
        rng = np.random.default_rng(7)
        buys_above = 0
        for _ in range(1_500):
            exp = _random_exposure(rng, liquidity=False)
            if exp.loss == 0:
                continue
            plan = hedge_income(exp)
            if plan.contracts > 0 and exp.price > plan.reservation_price + 1e-9:
                buys_above += 1
                assert any("costs more than" in w for w in plan.warnings)
        assert buys_above == 0


# ============================================== solvency & accounting
class TestPlanAccounting:
    def test_solvent_in_every_state(self, sweep):
        for exp, plan in sweep:
            assert all(r.wealth_hedged > 0 for r in plan.states), exp
            assert all(r.wealth_unhedged > 0 for r in plan.states), exp
            assert plan.worst_hedged > 0

    def test_dollar_fields_agree_with_the_states_table(self, sweep):
        for exp, plan in sweep:
            p, wu, wh = _rows(plan)
            assert p.sum() == pytest.approx(1.0, abs=1e-9)
            assert plan.expected_wealth_unhedged == pytest.approx(float(p @ wu), rel=1e-9)
            assert plan.expected_wealth_hedged == pytest.approx(float(p @ wh), rel=1e-9)
            for std, w in ((plan.std_unhedged, wu), (plan.std_hedged, wh)):
                m = float(p @ w)
                assert std == pytest.approx(math.sqrt(max(float(p @ (w - m) ** 2), 0.0)),
                                            rel=1e-6, abs=1e-6 * exp.wealth)
            assert plan.ce_gain == pytest.approx(plan.ce_hedged - plan.ce_unhedged, abs=1e-9)
            if plan.basis_correlation < 1.0 - 1e-6:
                # at basis 1 the CE also counts phantom states the table hides
                # (see test_phantom_states_do_not_move_the_hedge)
                assert plan.ce_hedged == pytest.approx(
                    crra_certainty_equivalent(wh, p, exp.gamma), rel=1e-9)
                assert plan.ce_unhedged == pytest.approx(
                    crra_certainty_equivalent(wu, p, exp.gamma), rel=1e-9)
            # Jensen: a risk averter's CE is between the worst state and the mean
            tol = 1e-9 * exp.wealth
            assert wh.min() - tol <= plan.ce_hedged <= float(p @ wh) + tol
            assert wu.min() - tol <= plan.ce_unhedged <= float(p @ wu) + tol
            assert plan.worst_unhedged == pytest.approx(wu.min())
            if plan.basis_correlation < 1.0 - 1e-9:
                # with basis risk every state is possible, so the table is complete
                assert plan.worst_hedged == pytest.approx(wh.min())

    def test_cost_fee_and_premium_accounting(self, sweep):
        for exp, plan in sweep:
            c = plan.contracts
            fill = plan.avg_fill_price if plan.avg_fill_price is not None else exp.price
            fee = kalshi_fee(abs(c), fill, exp.fee_multiplier, exp.fee_rate)
            if c == 0:
                assert plan.cost == 0 and plan.fee == 0
                continue
            assert plan.fee == pytest.approx(fee)
            gross = c * fill if c > 0 else -c * (1 - fill)
            assert plan.cost == pytest.approx(gross + fee)
            assert plan.payout_if_pays == max(c, 0)
            assert plan.direction == ("buy" if c > 0 else "sell")
            assert plan.needs_hedge == (exp.loss > 0 and c > 0)
            if c > 0:
                # premium = what you pay above fair value, fee included
                assert plan.total_premium == pytest.approx(plan.cost - c * plan.belief, abs=1e-6)
            # expected wealth moves by the edge on the position, minus the fee
            edge = c * (plan.belief - fill)
            assert plan.expected_wealth_hedged - plan.expected_wealth_unhedged == pytest.approx(
                edge - fee, abs=1e-6 * exp.wealth)
            # a pure-hedge decomposition that adds up
            assert plan.pure_hedge_contracts + plan.speculative_contracts == pytest.approx(plan.n_star)
            assert plan.pure_hedge_contracts == pytest.approx(plan.basis_correlation * exp.loss)

    def test_liquidity_cap_direction_and_coverage(self, sweep):
        for exp, plan in sweep:
            c, wanted = plan.contracts, plan.contracts_wanted
            assert wanted == int(round(plan.n_star))
            assert 0.0 <= plan.coverage <= 1.0
            if plan.liquidity_limit is not None:
                assert abs(c) <= plan.liquidity_limit
            else:
                assert c == wanted
            assert c * wanted >= 0  # never the opposite direction
            assert abs(c) <= abs(wanted)
            assert plan.liquidity_capped == (c != wanted)
            if wanted:
                assert plan.coverage == pytest.approx(abs(c) / abs(wanted))
            if not exp.allow_selling:
                assert c >= 0
            if plan.avg_fill_price is not None:
                assert 0 < plan.avg_fill_price < 1

    def test_no_exposure_is_a_pure_bet(self, sweep):
        for exp, plan in sweep:
            if exp.loss == 0:
                assert plan.reservation_price == pytest.approx(plan.belief, abs=1e-12)
                assert plan.pure_hedge_contracts == 0
                assert not plan.needs_hedge
                assert any("nothing to hedge" in w for w in plan.warnings)

    def test_deterministic(self, sweep):
        for exp, plan in sweep[:200]:
            assert hedge_income(exp).to_dict() == plan.to_dict()

    @pytest.mark.xfail(
        strict=True,
        reason="BUG (medium): worst_hedged is min() over all four joint states, "
        "including the zero-probability 'loss but contract does not pay' state at "
        "basis 1; the page's 'Worst season' shows a state that cannot happen - "
        "hedge.py:561 (states rows are filtered at :538, the worst is not)",
    )
    def test_worst_case_is_a_state_that_can_happen(self):
        # the default exposure of tests/test_prediction.py, fee-free
        plan = hedge_income(IncomeExposure(wealth=38_000, loss=9_000, price=0.35,
                                           gamma=1.5, fee_rate=0.0))
        p, _, wh = _rows(plan)
        assert plan.std_hedged == pytest.approx(0.0, abs=1e-6)  # wealth is certain...
        assert plan.worst_hedged == pytest.approx(wh.min())      # ...34,850, not 25,850


    @pytest.mark.xfail(
        strict=True,
        reason="BUG (low; gamma >~ 10 only): joint_states (hedge.py:152-155) leaves "
        "2.8e-17 instead of 0 in the 'impossible' states at basis 1 for ~8% of "
        "probabilities (e.g. 0.515); at gamma = 20 that phantom state's marginal "
        "utility dominates, so a fair, fee-free, perfect-basis hedge comes out "
        "55,782 instead of 60,000 with std 2,108 instead of 0",
    )
    def test_phantom_states_do_not_move_the_hedge(self):
        states, _ = joint_states(0.515, 0.515, 1.0)
        assert all(s.prob == 0.0 for s in states if s.pays != s.loss)
        plan = hedge_income(IncomeExposure(wealth=100_000, loss=60_000, price=0.515,
                                           gamma=20.0, fee_rate=0.0))
        assert plan.n_star == pytest.approx(60_000, abs=1)
        assert plan.std_hedged == pytest.approx(0.0, abs=1e-6)


# ====================================================== concavity / CE
class TestConcavity:
    def test_fair_price_hedge_and_any_cap_never_hurt(self):
        """At a fair, fee-free price the proposal and every capped size are
        worth at least as much as no hedge (CE gain >= 0)."""
        rng = np.random.default_rng(8)
        for _ in range(1_200):
            w = float(10 ** rng.uniform(3, 7))
            l = float(w * rng.uniform(0.01, 0.9))
            q = float(np.round(rng.uniform(0.02, 0.98), 2))
            liq = None if rng.random() < 0.3 else Liquidity(
                open_interest=float(rng.choice([0, 10, 35, 900, 4790, 1e6])))
            plan = hedge_income(IncomeExposure(
                wealth=w, loss=l, price=q, gamma=float(rng.uniform(0.05, 8)),
                basis_correlation=float(rng.uniform(0.01, 1.0)), fee_rate=0.0,
                liquidity=liq))
            assert plan.ce_gain >= -1e-6 * w, (w, l, q)
            assert plan.contracts >= 0

    def test_with_fees_the_cap_costs_at_most_the_fee_rounding(self):
        """With fees the smooth optimum is still >= no hedge; the integer
        position and the fee rounded up to the cent can cost at most a cent."""
        rng = np.random.default_rng(9)
        worst = 0.0
        for _ in range(1_200):
            w = float(10 ** rng.uniform(3, 6))
            l = float(w * rng.uniform(0.01, 0.9))
            q = float(np.round(rng.uniform(0.02, 0.98), 2))
            liq = Liquidity(open_interest=float(rng.choice([10, 20, 50, 1e9])))
            plan = hedge_income(IncomeExposure(
                wealth=w, loss=l, price=q, gamma=float(rng.uniform(0.05, 8)),
                basis_correlation=float(rng.uniform(0.01, 1.0)), liquidity=liq))
            worst = min(worst, plan.ce_gain)
        assert worst >= -0.011

    @pytest.mark.xfail(
        strict=True,
        reason="BUG (medium): the position is sized at the quoted price, then "
        "costed at the order-book average fill (hedge.py:399-422) without "
        "re-optimizing, so a fill a few cents worse turns a +$1.72 hedge into a "
        "-$36.74 one that is still proposed (needs_hedge=True)",
    )
    def test_walking_the_book_never_proposes_a_hedge_worse_than_none(self):
        plan = hedge_income(IncomeExposure(
            wealth=38_000, loss=9_000, price=0.35, gamma=0.3,
            liquidity=Liquidity(asks_buy=[(0.35, 1.0), (0.38, 1e6)])))
        assert plan.contracts > 0 and plan.avg_fill_price > 0.379
        assert plan.ce_gain >= 0


# ========================================================== solvency bugs
class TestSolvencyBugs:
    @pytest.mark.xfail(
        strict=True,
        reason="BUG (medium-high): _bounds() (hedge.py:304-311) and the -inf "
        "check in _expected_utility (:316) apply to zero-probability states, so "
        "at basis 1 (the default) the impossible 'loss, no payout' state caps the "
        "hedge at (W-L)/price: 995 contracts proposed against a 9,500 loss whose "
        "full hedge is solvent (certain wealth 5,250)",
    )
    def test_full_basis_full_hedge_is_not_capped_by_an_impossible_state(self):
        plan = hedge_income(IncomeExposure(wealth=10_000, loss=9_500, price=0.5,
                                           gamma=2.0, fee_rate=0.0))
        assert plan.contracts >= 9_000

    @pytest.mark.xfail(
        strict=True,
        raises=ValueError,
        reason="BUG (medium): gamma <= 0 sets n_star = rho*loss (hedge.py:391-396) "
        "without the solvency bounds, so a risk-seeking/neutral user with a large "
        "loss gets 'wealth must be positive in every state' (HTTP 422) instead of a plan",
    )
    @pytest.mark.parametrize("gamma,rho", [(0.0, 1.0), (-0.5, 0.5), (-2.0, 1.0)])
    def test_risk_seeking_user_with_a_big_loss_still_gets_a_plan(self, gamma, rho):
        plan = hedge_income(IncomeExposure(wealth=10_000, loss=9_500, price=0.5,
                                           gamma=gamma, basis_correlation=rho))
        assert all(r.wealth_hedged > 0 for r in plan.states)

    @pytest.mark.xfail(
        strict=True,
        raises=ValueError,
        reason="BUG (low): int(round(n_star)) (hedge.py:399) can round past the "
        "solvency bound hi = 0.995*(W-L)/cost; when the cushion is below ~100 "
        "contracts' cost the 0.5% margin does not absorb the extra half-contract "
        "and hedge_income raises",
    )
    @pytest.mark.parametrize("loss,rho", [(9_999.6, 1.0), (9_999.7, 1.0)])
    def test_rounding_never_rounds_past_the_solvency_bound(self, loss, rho):
        plan = hedge_income(IncomeExposure(wealth=10_000, loss=loss, price=0.4,
                                           gamma=2.0, basis_correlation=rho))
        assert all(r.wealth_hedged > 0 for r in plan.states)

    @pytest.mark.xfail(
        strict=True,
        reason="BUG (low): same rounding cause with basis risk, where the state "
        "that goes negative is a real one (~4% of 1,000 small-cushion cases crash)",
    )
    def test_rounding_insolvency_also_happens_with_basis_risk(self):
        """Random search over small cushions with rho < 1."""
        rng = np.random.default_rng(10)
        crashes = 0
        for _ in range(1_000):
            w = float(rng.uniform(1.0, 5.0))
            exp = IncomeExposure(wealth=w, loss=float(w * rng.uniform(0.5, 0.99)),
                                 price=float(np.round(rng.uniform(0.02, 0.9), 2)),
                                 gamma=float(rng.choice([0.05, 0.5, 2.0])),
                                 basis_correlation=float(rng.uniform(0.0, 0.99)))
            try:
                hedge_income(exp)
            except ValueError as e:
                assert "positive in every state" in str(e)
                crashes += 1
        assert crashes == 0

    @pytest.mark.xfail(
        strict=True,
        raises=ValueError,
        reason="BUG (medium): the order-book average fill is applied after sizing "
        "(hedge.py:418-422) and never checked against the solvency bound, so "
        "a fill 3c above the quote pushes the 'loss, no payout' state negative "
        "and hedge_income raises",
    )
    def test_walking_the_book_keeps_wealth_positive(self):
        hedge_income(IncomeExposure(
            wealth=10_000, loss=7_400, price=0.21, gamma=1.0, basis_correlation=0.98,
            own_prob=0.72, confidence=1.0,
            liquidity=Liquidity(asks_buy=[(0.21, 10.0), (0.24, 1e7)])))

    @pytest.mark.xfail(
        strict=True,
        raises=ZeroDivisionError,
        reason="BUG (low): crra_inverse (hedge.py:85-89) computes 0.0 ** negative "
        "when w^(1-gamma) underflows; ZeroDivisionError is not caught by the API's "
        "ValueError handler, so this is an HTTP 500 (gamma is unbounded in the schema)",
    )
    def test_large_gamma_does_not_underflow(self):
        hedge_income(IncomeExposure(wealth=1e6, loss=1e5, price=0.35, gamma=60.0))


# ======================================================== pure hedge
class TestPureHedge:
    def test_full_basis_fair_price_no_fee_is_the_whole_loss(self):
        rng = np.random.default_rng(11)
        for _ in range(800):
            w = float(10 ** rng.uniform(3, 8))
            q = float(np.round(rng.uniform(0.02, 0.98), 2))
            # keep the (buggy) solvency bound slack: L*q < 0.9*(W - L)
            l = float(w * rng.uniform(0.0, 0.9 / (0.9 + q)))
            # gamma <= 8: above ~10 the phantom-state bug moves the answer
            plan = hedge_income(IncomeExposure(wealth=w, loss=l, price=q,
                                               gamma=float(rng.uniform(0.05, 8)),
                                               fee_rate=0.0))
            assert abs(plan.n_star - l) <= max(0.51, 1e-5 * l), (w, l, q)
            assert abs(plan.speculative_contracts) <= max(0.51, 1e-5 * l)

    def test_with_basis_risk_crra_departs_from_rho_times_loss(self):
        """rho*L is the variance-minimizing hedge, not the CRRA optimum: at a
        fair price with no fees the gap grows with L/W (it is what the UI
        labels 'speculative').  Measured bound: |n* - rho L| / L <= 1.5 * L/W."""
        rng = np.random.default_rng(12)
        worst = 0.0
        for _ in range(800):
            w = 1e5
            frac = float(rng.uniform(0.005, 0.5))
            plan = hedge_income(IncomeExposure(
                wealth=w, loss=w * frac, price=float(rng.uniform(0.05, 0.95)),
                gamma=float(rng.uniform(0.2, 8)), basis_correlation=float(rng.uniform(0.05, 1)),
                fee_rate=0.0))
            dev = abs(plan.speculative_contracts) / (w * frac)
            worst = max(worst, dev / frac)
            assert dev <= 1.5 * frac + 0.005
        assert worst > 0.3  # the gap is real, not rounding

    def test_fees_shrink_the_hedge_below_the_pure_hedge(self):
        rng = np.random.default_rng(13)
        for _ in range(400):
            w = 1e5
            l = float(w * rng.uniform(0.01, 0.4))
            q = float(np.round(rng.uniform(0.05, 0.9), 2))
            g = float(rng.uniform(0.3, 8))
            kw = dict(wealth=w, loss=l, price=q, gamma=g)
            n0 = hedge_income(IncomeExposure(**kw, fee_rate=0.0)).n_star
            n1 = hedge_income(IncomeExposure(**kw)).n_star
            n2 = hedge_income(IncomeExposure(**kw, fee_multiplier=3.0)).n_star
            assert n2 <= n1 + 1e-3 <= n0 + 2e-3
            assert n0 == pytest.approx(l, abs=0.51)


# ======================================================== monotonicity
class TestMonotonicity:
    def _n(self, **kw):
        return hedge_income(IncomeExposure(**kw)).n_star

    def test_more_loss_more_contracts(self):
        """Holds for L/W <= 0.3.  Beyond that, with basis risk and a dear
        contract, n* legitimately peaks and falls (e.g. p=0.76, rho=0.72,
        gamma=3: 17,720 at L/W=0.45, 15,125 at 0.6): each contract costs
        money in the 'loss but no payout' state, which a CRRA agent guards."""
        rng = np.random.default_rng(14)
        for _ in range(150):
            w = 1e5
            base = dict(wealth=w, price=float(np.round(rng.uniform(0.05, 0.9), 2)),
                        gamma=float(rng.uniform(0.2, 8)),
                        basis_correlation=float(rng.uniform(0.05, 1.0)))
            ns = [self._n(loss=w * f, **base) for f in np.linspace(0.0, 0.3, 8)]
            assert all(b >= a - 1e-3 for a, b in zip(ns, ns[1:])), (base, ns)

    def test_more_basis_more_contracts(self):
        rng = np.random.default_rng(15)
        for _ in range(150):
            w = 1e5
            base = dict(wealth=w, loss=w * float(rng.uniform(0.01, 0.5)),
                        price=float(np.round(rng.uniform(0.05, 0.9), 2)),
                        gamma=float(rng.uniform(0.2, 8)))
            ns = [self._n(basis_correlation=r, **base) for r in np.linspace(0.0, 1.0, 8)]
            assert all(b >= a - 1e-3 for a, b in zip(ns, ns[1:])), (base, ns)

    def test_dearer_cover_fewer_contracts_at_a_fixed_belief(self):
        rng = np.random.default_rng(16)
        for _ in range(150):
            w = 1e5
            q = float(np.round(rng.uniform(0.1, 0.8), 2))
            base = dict(wealth=w, loss=w * float(rng.uniform(0.0, 0.6)), market_prob=q,
                        gamma=float(rng.uniform(0.2, 8)),
                        basis_correlation=float(rng.uniform(0.0, 1.0)))
            prices = np.round(np.linspace(max(q - 0.08, 0.02), min(q + 0.08, 0.98), 9), 2)
            ns = [self._n(price=float(p), **base) for p in prices]
            assert all(b <= a + 1e-3 for a, b in zip(ns, ns[1:])), (base, ns)

    def test_more_averse_is_closer_to_the_pure_hedge_at_full_basis(self):
        rng = np.random.default_rng(17)
        for _ in range(120):
            w = 1e5
            l = w * float(rng.uniform(0.01, 0.4))
            q = float(np.round(rng.uniform(0.05, 0.9), 2))
            base = dict(wealth=w, loss=l, price=q, own_prob=float(rng.uniform(0.01, 0.99)),
                        confidence=0.5, fee_rate=0.0)
            gaps = [abs(self._n(gamma=g, **base) - l) for g in (0.3, 0.7, 1.5, 3, 6, 12)]
            assert all(b <= a + 1.0 for a, b in zip(gaps, gaps[1:])), (base, gaps)

    def test_scale_invariance_of_crra(self):
        """CRRA is homothetic and fees are linear in n: scaling W and L by k
        scales the continuous optimum by k."""
        rng = np.random.default_rng(18)
        for _ in range(300):
            exp = _random_exposure(rng, liquidity=False)
            if exp.wealth > 1e6:
                continue
            k = float(10 ** rng.uniform(-0.5, 2))
            n1 = optimal_contracts(exp, joint_states(*(2 * [hedge_income(exp).belief]),
                                                     exp.basis_correlation)[0])
            big = IncomeExposure(**{**exp.__dict__, "wealth": exp.wealth * k, "loss": exp.loss * k})
            n2 = optimal_contracts(big, joint_states(*(2 * [hedge_income(big).belief]),
                                                     big.basis_correlation)[0])
            assert n2 == pytest.approx(n1 * k, rel=2e-3, abs=0.02 * max(k, 1))


# ======================================================= kelly / bets
class TestKelly:
    def test_log_utility_bet_is_kelly(self):
        rng = np.random.default_rng(19)
        for _ in range(500):
            q = float(rng.uniform(0.05, 0.95))
            p = float(np.round(rng.uniform(0.05, 0.95), 2))
            plan = hedge_income(IncomeExposure(wealth=10_000, loss=0.0, price=p, gamma=1.0,
                                               own_prob=q, confidence=1.0, fee_rate=0.0))
            k = kelly_fraction(plan.belief, p)
            assert -1.0 <= k <= 1.0
            assert plan.crra_fraction == pytest.approx(k, abs=2e-3)

    def test_kelly_sign(self):
        rng = np.random.default_rng(20)
        for q, p in rng.uniform(0.01, 0.99, size=(5_000, 2)):
            assert np.sign(kelly_fraction(q, p)) == np.sign(q - p) or q == p


# ============================================================ liquidity
class TestLiquidityFunctions:
    def _book(self, rng):
        return {"orderbook_fp": {
            side: [[f"{rng.uniform(-0.1, 1.1):.4f}", f"{rng.uniform(-5, 500):.2f}"]
                   for _ in range(int(rng.integers(0, 8)))]
            for side in ("yes_dollars", "no_dollars")}}

    def test_asks_from_orderbook_is_sorted_aggregated_and_complementary(self):
        rng = np.random.default_rng(21)
        for _ in range(3_000):
            book = self._book(rng)
            for side, opp in (("yes", "no_dollars"), ("no", "yes_dollars")):
                asks = asks_from_orderbook(book, side)
                prices = [p for p, _ in asks]
                assert prices == sorted(set(prices))
                assert all(0 < p < 1 and q > 0 for p, q in asks)
                valid = [(float(b), float(q)) for b, q in book["orderbook_fp"][opp]
                         if 0 < float(b) < 1 and float(q) > 0]
                assert sum(q for _, q in asks) == pytest.approx(sum(q for _, q in valid))

    def test_depth_and_average_fill(self):
        rng = np.random.default_rng(22)
        for _ in range(3_000):
            levels = int(rng.integers(1, 6))
            asks = sorted((round(float(p), 2), float(q)) for p, q in zip(
                rng.uniform(0.01, 0.99, levels), rng.uniform(1, 500, levels)))
            total = sum(q for _, q in asks)
            d1, d2 = depth_within(asks, 0.01), depth_within(asks, 0.05)
            assert 0 < d1 <= d2 <= total + 1e-9
            prev = asks[0][0]
            for n in sorted(rng.uniform(0.5, total, size=4)):
                f = average_fill(asks, float(n))
                assert f is not None and asks[0][0] - 1e-12 <= f <= asks[-1][0] + 1e-12
                assert f >= prev - 1e-12  # buying more never lowers the average
                prev = f
                if n <= d1:
                    assert f <= asks[0][0] + 0.01 + 1e-9
            assert average_fill(asks, total * 1.01 + 1) is None
            assert average_fill(asks, 0) is None and average_fill([], 5) is None

    def test_limit_is_min_of_depth_and_open_interest_share(self):
        rng = np.random.default_rng(23)
        for _ in range(3_000):
            oi = None if rng.random() < 0.3 else float(rng.uniform(0, 1e5))
            asks = None if rng.random() < 0.3 else [(0.30, float(rng.uniform(0, 1e4))),
                                                    (0.32, float(rng.uniform(0, 1e4))),
                                                    (0.50, 1e6)]
            liq = Liquidity(open_interest=oi, asks_buy=asks)
            lim = limit_for(liq, buying=True)
            cands = []
            if asks is not None:
                cands.append(asks[0][1] + asks[1][1])
            if oi is not None:
                cands.append(math.floor(0.1 * oi))
            if not cands:
                assert lim.limit is None
            else:
                assert lim.limit == math.floor(min(cands))
                assert lim.limit >= 0


# =================================================== edge cases & continuity
EDGE_CASES = [
    dict(wealth=38_000, loss=9_000, price=0.01, gamma=1.5),
    dict(wealth=38_000, loss=9_000, price=0.99, gamma=1.5),
    dict(wealth=38_000, loss=9_000, price=0.99, gamma=1.5, own_prob=0.01, confidence=1.0),
    dict(wealth=38_000, loss=9_000, price=0.01, gamma=1.5, own_prob=0.99, confidence=1.0),
    dict(wealth=38_000, loss=9_000, price=0.35, gamma=0.05),
    dict(wealth=38_000, loss=9_000, price=0.35, gamma=1.0),
    dict(wealth=38_000, loss=9_000, price=0.35, gamma=20.0),
    dict(wealth=38_000, loss=0.0, price=0.35, gamma=1.5, own_prob=0.6, confidence=0.5),
    dict(wealth=38_000, loss=37_000, price=0.35, gamma=2.0, basis_correlation=0.5),
    dict(wealth=38_000, loss=37_999, price=0.35, gamma=2.0, basis_correlation=0.5),
    dict(wealth=1e9, loss=1e8, price=0.35, gamma=20.0),
    dict(wealth=1e9, loss=5e8, price=0.5, gamma=0.05, basis_correlation=0.3),
    dict(wealth=50.0, loss=10.0, price=0.35, gamma=1.5),
    dict(wealth=1.0, loss=0.0, price=0.35, gamma=1.5),
    dict(wealth=38_000, loss=9_000, price=0.35, gamma=1.5, basis_correlation=0.0),
    dict(wealth=38_000, loss=9_000, price=0.35, gamma=0.0, fee_rate=0.0),
]


@pytest.mark.parametrize("kw", EDGE_CASES, ids=lambda kw: ",".join(f"{k}={v}" for k, v in kw.items()))
def test_edge_cases_are_finite_and_solvent(kw):
    plan = hedge_income(IncomeExposure(**kw))
    d = plan.to_dict()
    for k, v in d.items():
        if isinstance(v, float):
            assert math.isfinite(v), k
    assert all(r.wealth_hedged > 0 for r in plan.states)
    assert 0.01 <= plan.belief <= 0.99
    if kw.get("basis_correlation", 1.0) == 0.0 and kw.get("own_prob") is None:
        assert plan.contracts == 0  # no basis and no view: nothing to buy


def test_small_perturbations_move_the_position_by_at_most_rounding():
    """A 1e-7 relative nudge moves n* by about 1e-7 * n* (plus solver noise),
    so the integer position may move by that much plus one rounding step.
    Worst found: 5 contracts on a 3.4-million-contract position (1.5e-6
    relative) - no direction flips, no jumps."""
    rng = np.random.default_rng(24)
    worst = 0
    for _ in range(400):
        exp = _random_exposure(rng, liquidity=False)
        a = hedge_income(exp)
        for field_, eps in (("wealth", 1e-7), ("loss", 1e-7), ("confidence", 1e-7)):
            v = getattr(exp, field_)
            if field_ == "loss" and v == 0:
                continue
            b = hedge_income(IncomeExposure(**{**exp.__dict__, field_: v * (1 + eps) + eps * 1e-3}))
            jump = abs(b.contracts - a.contracts)
            worst = max(worst, max(jump - 1, 0) / max(1.0, abs(a.n_star)))
            assert jump <= 1 + 2e-6 * abs(a.n_star), (exp, field_)
            assert a.contracts * b.contracts >= 0 or abs(a.n_star) < 1  # no flips
    assert worst < 2e-6  # beyond one rounding step


def test_gamma_one_branch_is_continuous_up_to_solver_noise():
    """crra_utility switches to log within 1e-9 of gamma = 1; just outside,
    w^(1-g)/(1-g) cancels catastrophically and the solver wanders ~20
    contracts (0.3%) on a 6,600 position - CE moves < 1 cent.  Bounded here."""
    base = dict(wealth=38_000, loss=9_000, price=0.35)
    ref = hedge_income(IncomeExposure(gamma=1.0, **base))
    for d in (-1e-6, -1e-7, -2e-9, -1e-9, 1e-9, 2e-9, 1e-8, 1e-7, 1e-6):
        p = hedge_income(IncomeExposure(gamma=1.0 + d, **base))
        assert abs(p.n_star - ref.n_star) / ref.n_star < 0.01
        assert abs(p.ce_gain - ref.ce_gain) < 0.01


def test_gamma_zero_is_a_cliff():
    """Design finding (documented, not xfailed): gamma <= 0 shows the pure
    hedge with a warning, gamma = 0.01 shows (with fees) no position at all,
    and at gamma = 0 the proposed position has a negative CE gain at the
    user's own preferences (fees, no edge)."""
    base = dict(wealth=38_000, loss=9_000, price=0.35)
    at0 = hedge_income(IncomeExposure(gamma=0.0, **base))
    near = hedge_income(IncomeExposure(gamma=0.01, **base))
    assert at0.contracts == 9_000 and near.contracts == 0
    assert at0.ce_gain < 0 and at0.needs_hedge
    assert any("risk-neutral" in w for w in at0.warnings)


def test_expected_utility_is_concave_in_the_position():
    """The premise of 'a capped hedge is never worse than none'."""
    rng = np.random.default_rng(25)
    for _ in range(300):
        exp = _random_exposure(rng, liquidity=False)
        states, _ = joint_states(*(2 * [hedge_income(exp).belief]), exp.basis_correlation)
        lo, hi = _bounds(exp)
        ns = np.linspace(lo * 0.98, hi * 0.98, 41)
        eu = np.array([_expected_utility(exp, states, float(n)) for n in ns])
        assert np.all(np.isfinite(eu))
        second = eu[:-2] - 2 * eu[1:-1] + eu[2:]
        assert np.all(second <= 1e-12 * np.abs(eu).max())


@pytest.mark.xfail(
    strict=True,
    reason="BUG (low): total_premium uses the quoted price (hedge.py:568) while "
    "cost and fee use the order-book average fill (:423-425), so the premium "
    "understates what the walked book really charges",
)
def test_total_premium_uses_the_fill_price():
    plan = hedge_income(IncomeExposure(
        wealth=38_000, loss=9_000, price=0.35, gamma=1.5,
        liquidity=Liquidity(asks_buy=[(0.35, 100.0), (0.37, 1e6)])))
    assert plan.avg_fill_price > 0.36
    assert plan.total_premium == pytest.approx(plan.cost - plan.contracts * plan.belief)
