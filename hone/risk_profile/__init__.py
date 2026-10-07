"""Part 1 — risk-aversion elicitation.

Holt-Laury Multiple Price List menus, CRRA + Fechner-noise Maximum
Likelihood estimation of the risk-aversion parameter gamma, and the
50-tier classification.
"""

from .holt_laury import (
    Lottery,
    Decision,
    standard_menu,
    expected_value,
    safe_choice_count,
    gamma_interval,
    indifference_gamma,
)
from .estimation import EstimationResult, crra_utility, choice_probability, estimate
from .tiers import NUM_TIERS, TierPlacement, gamma_to_tier, tier_bounds, tier_gamma
from .questionnaire import RiskProfile, run_questionnaire, profile_from_choices

__all__ = [
    "Lottery",
    "Decision",
    "standard_menu",
    "expected_value",
    "safe_choice_count",
    "gamma_interval",
    "indifference_gamma",
    "EstimationResult",
    "crra_utility",
    "choice_probability",
    "estimate",
    "NUM_TIERS",
    "TierPlacement",
    "gamma_to_tier",
    "tier_bounds",
    "tier_gamma",
    "RiskProfile",
    "run_questionnaire",
    "profile_from_choices",
]
