import numpy as np
import pytest

from hone.risk_profile import (
    NUM_TIERS,
    estimate,
    expected_value,
    gamma_interval,
    gamma_to_tier,
    indifference_gamma,
    profile_from_choices,
    safe_choice_count,
    standard_menu,
    tier_bounds,
    tier_gamma,
)
from hone.risk_profile.estimation import choice_probability, log_likelihood
from hone.risk_profile.holt_laury import is_monotone


class TestMenu:
    def test_ten_rows_with_rising_probability(self):
        menu = standard_menu()
        assert len(menu) == 10
        assert [d.option_a.p_high for d in menu] == pytest.approx(
            [i / 10 for i in range(1, 11)]
        )

    def test_scaling_multiplies_payoffs(self):
        menu = standard_menu(scale=20.0)
        assert menu[0].option_a.high == pytest.approx(40.0)
        assert menu[0].option_b.high == pytest.approx(77.0)

    def test_expected_value_difference_flips_at_row_five(self):
        # EV favors A on rows 1-4 and B from row 5 on (the doc's table).
        menu = standard_menu()
        diffs = [expected_value(d.option_a) - expected_value(d.option_b) for d in menu]
        assert all(d > 0 for d in diffs[:4])
        assert all(d < 0 for d in diffs[4:])
        assert diffs[0] == pytest.approx(1.17, abs=0.005)


class TestIntervals:
    def test_canonical_holt_laury_interval(self):
        # The design doc's anchor: switching after 5 safe choices bounds
        # gamma in (0.15, 0.41).
        lo, hi = gamma_interval(5)
        assert lo == pytest.approx(0.146, abs=0.01)
        assert hi == pytest.approx(0.411, abs=0.01)

    def test_intervals_are_increasing_and_contiguous(self):
        prev_hi = None
        for n in range(1, 9):
            lo, hi = gamma_interval(n)
            assert lo < hi
            if prev_hi is not None:
                assert lo == pytest.approx(prev_hi, abs=1e-9)
            prev_hi = hi

    def test_scale_invariance(self):
        assert gamma_interval(5, scale=1.0) == pytest.approx(
            gamma_interval(5, scale=100.0)
        )

    def test_risk_neutral_indifference_row(self):
        # Row 4 indifference gamma is slightly negative, row 5 slightly
        # positive: a risk-neutral agent switches between them.
        menu = standard_menu()
        assert indifference_gamma(menu[3]) < 0 < indifference_gamma(menu[4])


class TestChoiceHelpers:
    def test_safe_choice_count(self):
        assert safe_choice_count(["A"] * 5 + ["B"] * 5) == 5

    def test_monotone_detection(self):
        assert is_monotone(["A", "A", "B", "B"])
        assert not is_monotone(["A", "B", "A", "B"])


class TestEstimation:
    def test_probability_increases_with_gamma(self):
        # More risk-averse agents choose the safe option more often.
        menu = standard_menu()
        p_low = choice_probability(menu, gamma=-0.5, mu=0.3)
        p_high = choice_probability(menu, gamma=1.5, mu=0.3)
        assert np.all(p_high >= p_low)

    def test_log_likelihood_matches_doc_formula(self):
        menu = standard_menu()
        y = np.array([1] * 5 + [0] * 5, dtype=float)
        p = choice_probability(menu, 0.3, 0.2)
        expected = float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))
        assert log_likelihood(y, menu, 0.3, 0.2) == pytest.approx(expected)

    def test_consistent_subject_recovers_interval(self):
        vec = ["A"] * 5 + ["B"] * 5
        res = estimate([vec, vec, vec])
        lo, hi = gamma_interval(5)
        assert lo <= res.gamma <= hi
        assert res.n_obs == 30
        assert res.mu < 0.1  # consistent choices -> low noise

    def test_noisy_subject_gets_higher_mu(self):
        consistent = ["A"] * 5 + ["B"] * 5
        noisy = ["A", "B", "A", "A", "B", "A", "B", "B", "A", "B"]
        res_c = estimate([consistent] * 3)
        res_n = estimate([noisy] * 3)
        assert res_n.mu > res_c.mu

    def test_risk_loving_subject(self):
        vec = ["A"] * 2 + ["B"] * 8
        res = estimate([vec, vec, vec])
        assert res.gamma < 0

    def test_luce_spec_matches_doc_ratio(self):
        # Pr(A) = EU_A^(1/mu) / (EU_A^(1/mu) + EU_B^(1/mu)) for gamma<1.
        from hone.risk_profile.estimation import _expected_utilities

        menu = standard_menu()
        gamma, mu = 0.3, 0.4
        eu_a, eu_b, _, _ = _expected_utilities(menu, gamma)
        expected = eu_a ** (1 / mu) / (eu_a ** (1 / mu) + eu_b ** (1 / mu))
        got = choice_probability(menu, gamma, mu, error_spec="luce")
        assert got == pytest.approx(expected, rel=1e-9)

    def test_luce_spec_rejects_gamma_above_one(self):
        with pytest.raises(ValueError):
            choice_probability(standard_menu(), 1.5, 0.3, error_spec="luce")


class TestTiers:
    def test_fifty_tiers_cover_the_range(self):
        assert NUM_TIERS == 50
        assert gamma_to_tier(-1.0).tier == 1
        assert gamma_to_tier(4.0).tier == 50
        assert gamma_to_tier(-99.0).tier == 1  # clipped
        assert gamma_to_tier(99.0).tier == 50  # clipped

    def test_tiers_are_monotone_in_gamma(self):
        gammas = np.linspace(-1.5, 4.5, 200)
        tiers = [gamma_to_tier(g).tier for g in gammas]
        assert tiers == sorted(tiers)

    def test_bounds_contain_representative_gamma(self):
        for tier in (1, 13, 25, 50):
            lo, hi = tier_bounds(tier)
            assert lo <= tier_gamma(tier) <= hi

    def test_risk_neutral_sits_at_the_neutral_band(self):
        assert gamma_to_tier(0.05).category == "Risk-neutral"
        assert gamma_to_tier(-0.9).category == "Aggressively risk-seeking"
        assert gamma_to_tier(3.9).category == "Highly risk-averse"


class TestProfile:
    def test_full_profile_from_choices(self):
        vec = ["A"] * 6 + ["B"] * 4
        profile = profile_from_choices([vec, vec, vec])
        assert profile.interval[0] <= profile.gamma <= profile.interval[1]
        assert 1 <= profile.tier.tier <= 50
        assert all(profile.monotone)
        assert "Tier" in profile.summary()

    def test_inconsistent_choices_flagged(self):
        vec = ["A", "B", "A", "A", "B", "B", "A", "B", "B", "B"]
        profile = profile_from_choices([vec, vec, vec])
        assert not any(profile.monotone)
