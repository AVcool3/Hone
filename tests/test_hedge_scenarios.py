"""Scenario suite: what the income hedge must do for real kinds of people.

Every scenario here was taught by a study in research/prediction/findings/:

    01_research.md          market rules, prior work (index insurance), alternatives
    02_history.md           backtests on settled Kalshi markets
    03_segments.md          78k simulated people across 8 occupations
    04_properties.md        adversarial property tests (14 engine bugs)
    05_misspecification.md  what happens when the model's assumptions are wrong

Each test names the lesson it locks in. If a change to the engine breaks
one, it has un-learned something — read the referenced finding before
"fixing" the test. To add a lesson: write the scenario as a person, state
what the model must do for them, and cite where you learned it.

Numbers are deliberately loose (directions, bounds, explanations), so the
suite pins behaviour, not today's exact figures.
"""

from __future__ import annotations

import numpy as np
import pytest

from hone.prediction.hedge import (
    BASIS_SHRINK,
    MAX_VIEW_TILT,
    PRICE_BUFFER,
    IncomeExposure,
    hedge_income,
)
from hone.prediction.liquidity import Liquidity


def says(plan, *fragments: str) -> bool:
    """True if some warning contains every fragment (case-insensitive)."""
    return any(all(f.lower() in w.lower() for f in fragments) for w in plan.warnings)


# ---------------------------------------------------------------- personas
def rideshare(**kw):
    """Driver, $45k a year; a gas spike costs ~$4.5k. Gas markets are deep."""
    base = dict(wealth=45_000 * 1.25, loss=4_500, price=0.48, gamma=3.0, basis_correlation=0.85,
                liquidity=Liquidity(open_interest=30_861, asks_buy=[(0.48, 13_873)], asks_sell=[(0.52, 13_873)]))
    base.update(kw)
    return IncomeExposure(**base)


def ski_instructor(**kw):
    """$35k season, a bad one costs $12k; nearest market is thin snowfall."""
    base = dict(wealth=35_000 * 1.25, loss=12_250, price=0.49, gamma=3.0, basis_correlation=0.6,
                liquidity=Liquidity(open_interest=138, asks_buy=[(0.49, 25)], asks_sell=[(0.51, 25)]))
    base.update(kw)
    return IncomeExposure(**base)


def contractor(**kw):
    """$70k contract worker; losing the contract costs half. Hedged with an
    unemployment-rate contract, which tracks one person's job only loosely."""
    base = dict(wealth=70_000 * 1.25, loss=35_000, price=0.10, gamma=4.0, basis_correlation=0.3)
    base.update(kw)
    return IncomeExposure(**base)


# --------------------------------------------------------------- scenarios
class TestWhoItHelps:
    def test_typical_driver_is_told_its_not_worth_it_and_why(self):
        """Lesson from writing this suite: once fees, the safety margins and
        realistic basis are all in, insuring a $4.5k fuel spike on $56k of
        income-plus-savings is worth ~$26 a year — Kalshi's fee (~1.75c on a
        48c contract) eats most of it. The model must say so plainly."""
        plan = hedge_income(rideshare())
        assert plan.contracts == 0
        assert says(plan, "worth", "fees")

    def test_full_time_driver_with_no_savings_gets_real_protection(self):
        """03_segments: value concentrates where the loss is large relative to
        the cushion and risk aversion is high."""
        plan = hedge_income(rideshare(wealth=45_000, loss=9_000, gamma=6.0))
        assert plan.needs_hedge and plan.contracts > 1_000
        assert plan.ce_gain > 0
        # What improves: the usual bad season (loss, and the contract pays)
        # and the overall swing. NOT the very worst case — with basis risk the
        # contract can fail to pay in your bad season, and then you've also
        # paid the premium. (A naive version of this test assumed otherwise.)
        bad_paid = next(s for s in plan.states if s.loss and s.pays)
        assert bad_paid.wealth_hedged > bad_paid.wealth_unhedged
        assert plan.std_hedged < plan.std_unhedged

    def test_with_basis_risk_demand_rises_then_falls_with_caution(self):
        """Clarke (2016), and found independently by 03_segments: with basis
        risk, the most risk-averse buy LESS index insurance, because a bad
        season without a payout gets worse with every dollar of premium. With
        perfect tracking (the textbook case) caution always means more cover."""
        gammas = (1.0, 3.0, 6.0, 15.0)
        risky = [hedge_income(rideshare(wealth=45_000, loss=9_000, gamma=g, liquidity=None)).contracts for g in gammas]
        assert max(risky) > risky[-1]                       # peaks, then falls
        perfect = [hedge_income(rideshare(wealth=45_000, loss=9_000, gamma=g, liquidity=None, basis_correlation=1.0,
                                          basis_shrink=1.0, price_buffer=0.0, fee_rate=0.0)).contracts for g in gammas]
        assert perfect == sorted(perfect)


class TestThinMarkets:
    def test_ski_instructor_is_told_the_market_is_too_small(self):
        """Live Kalshi check: snowfall markets can supply ~0% of a $12k hedge.
        The model must say so, not propose trades that can't fill."""
        plan = hedge_income(ski_instructor())
        assert plan.liquidity_capped and plan.contracts <= 25
        assert plan.coverage < 0.05
        assert says(plan, "risk profile wants", "market")   # the market is named as the reason

    def test_a_capped_hedge_is_never_worse_than_none(self):
        """Concavity: any size between zero and the optimum beats nothing."""
        for oi in (40, 400, 4_000):
            plan = hedge_income(ski_instructor(liquidity=Liquidity(open_interest=oi), market_prob=0.49))
            assert plan.ce_gain >= -1e-6


class TestBasisRisk:
    def test_loose_tracking_gets_a_smaller_hedge_and_an_explanation(self):
        """Index-insurance literature (01_research, Clarke 2016): with basis
        risk, buying more can make the worst season worse."""
        loose = hedge_income(contractor(basis_correlation=0.3))
        tight = hedge_income(contractor(basis_correlation=0.9))
        assert loose.contracts < tight.contracts

    def test_barely_related_contract_is_flagged(self):
        """03_segments: tech workers (basis ~0.15) get almost nothing."""
        plan = hedge_income(contractor(basis_correlation=0.15))
        assert says(plan, "only weakly")

    def test_rarer_personal_loss_means_a_smaller_hedge(self):
        """01_research / 05_misspecification: a layoff is rarer than
        'unemployment above X'; treating them as the same event over-hedges."""
        same = hedge_income(contractor())
        rarer = hedge_income(contractor(loss_prob=0.03))
        assert rarer.contracts < same.contracts


class TestViews:
    def test_optimist_with_income_at_risk_is_never_told_to_sell(self):
        """03_segments: half of optimists were told to sell the protection
        they need (10th percentile -8.1% of income)."""
        plan = hedge_income(rideshare(own_prob=0.10, confidence=1.0))
        assert plan.direction == "buy" and plan.contracts >= 0

    def test_a_confident_view_cannot_turn_a_hedge_into_a_bet(self):
        """03_segments + 05_misspecification: views were 2-8x the insurance;
        an overconfident user lost up to 107% of income. The view-driven part
        is capped at MAX_VIEW_TILT x the insurance."""
        plan = hedge_income(rideshare(own_prob=0.95, confidence=1.0, liquidity=None))
        assert plan.view_tilt_capped
        assert abs(plan.speculative_contracts) <= MAX_VIEW_TILT * max(
            plan.pure_hedge_contracts, plan.variance_min_contracts) + 1
        assert says(plan, "your view")

    def test_without_a_view_nothing_is_called_speculation(self):
        """04_properties design finding: basis effects used to be labelled
        'added by your view' for users with no view."""
        plan = hedge_income(contractor())
        assert plan.speculative_contracts == 0


class TestPreferences:
    def test_risk_seeking_user_gets_no_insurance(self):
        """04_properties B3 / 03_segments: gamma <= 0 used to show the full
        hedge (negative value) or crash; it must propose nothing and explain."""
        plan = hedge_income(rideshare(gamma=-1.0))
        assert plan.contracts == 0 and says(plan, "risk-seeking")

    @pytest.mark.parametrize("gamma", [60.0, 100.0])
    def test_extreme_risk_aversion_does_not_crash(self, gamma):
        """04_properties B8: gamma ~60 raised ZeroDivisionError (HTTP 500)."""
        plan = hedge_income(rideshare(gamma=gamma))
        assert plan.contracts >= 0 and np.isfinite(plan.ce_gain)


class TestPricesAndCosts:
    def test_walking_up_the_book_is_paid_for_and_never_overpays(self):
        """04_properties B4: sizing at the quote then filling higher produced
        hedges with negative value."""
        book = Liquidity(asks_buy=[(0.48, 200), (0.60, 1e6)], asks_sell=[(0.52, 1e6)])
        plan = hedge_income(rideshare(liquidity=book))
        assert plan.ce_gain >= 0
        if plan.contracts > 200:
            assert plan.avg_fill_price > 0.48

    def test_trivial_positions_are_not_proposed(self):
        """03_segments: 12.5% of personas were offered trades worth < $1."""
        plan = hedge_income(rideshare(loss=30, wealth=1_000_000))
        assert plan.contracts == 0
        assert plan.ce_gain == 0

    def test_full_basis_hedge_is_not_capped_by_an_impossible_state(self):
        """04_properties B1 (medium-high): impossible states set the solvency
        limit and shrank hedges ~10x for large losses."""
        plan = hedge_income(IncomeExposure(wealth=10_000, loss=9_500, price=0.5, gamma=2.0,
                                           fee_rate=0.0, basis_shrink=1.0, price_buffer=0.0))
        assert plan.contracts >= 9_000


class TestSafetyMargins:
    """05_misspecification: sizing as if basis were 25% weaker and prices 1c
    worse cut the share of people hurt by a wrong model from 24% to 10%."""

    def test_margins_only_ever_make_the_position_smaller(self):
        rng = np.random.default_rng(7)
        for _ in range(150):
            kw = dict(wealth=float(rng.uniform(2e4, 2e5)), price=float(rng.uniform(0.05, 0.9)),
                      gamma=float(rng.uniform(0.5, 10)), basis_correlation=float(rng.uniform(0.1, 1.0)))
            kw["loss"] = kw["wealth"] * float(rng.uniform(0.02, 0.6))
            careful = hedge_income(IncomeExposure(**kw))
            textbook = hedge_income(IncomeExposure(**kw, basis_shrink=1.0, price_buffer=0.0))
            assert careful.contracts <= textbook.contracts + 1, kw

    def test_what_you_see_uses_the_real_price(self):
        """The margins choose the size; every dollar shown uses the real price."""
        plan = hedge_income(rideshare(liquidity=None, fee_rate=0.0))
        assert plan.cost == pytest.approx(plan.contracts * 0.48)

    def test_defaults(self):
        assert BASIS_SHRINK == 0.75 and PRICE_BUFFER == 0.01 and MAX_VIEW_TILT == 0.25
