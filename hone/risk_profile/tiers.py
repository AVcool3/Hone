"""50-tier risk classification.

The MLE point estimate of the CRRA parameter gamma is mapped onto 50
ordered tiers.  Tier 1 is the most risk-seeking, tier 50 the most
risk-averse.  The tiers partition the gamma axis over
[GAMMA_MIN, GAMMA_MAX] = [-1.0, 4.0] into 50 equal-width bins of 0.10;
estimates outside the range are clipped into the end tiers.

That range comfortably covers the empirically observed spectrum:
Holt-Laury switch points imply gamma roughly between -1.7 and +1.4, and
portfolio-choice estimates for retail investors rarely exceed 4.

Each tier also carries a human-readable category label and a
representative gamma (the bin midpoint) that downstream modules (MVO,
hedging) can use when only the tier is known.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

NUM_TIERS = 50
GAMMA_MIN = -1.0
GAMMA_MAX = 4.0

#: bin edges: _EDGES[t-1] .. _EDGES[t] is tier t
_EDGES = np.linspace(GAMMA_MIN, GAMMA_MAX, NUM_TIERS + 1)

#: (last tier of band, label) — bands over the 50 tiers
_CATEGORY_BANDS = [
    (5, "Aggressively risk-seeking"),
    (10, "Risk-seeking"),
    (12, "Risk-neutral"),
    (20, "Slightly risk-averse"),
    (30, "Moderately risk-averse"),
    (40, "Risk-averse"),
    (50, "Highly risk-averse"),
]


@dataclass(frozen=True)
class TierPlacement:
    tier: int  # 1 (most risk-seeking) .. 50 (most risk-averse)
    gamma: float  # the estimate that produced this placement
    gamma_lower: float  # tier bin lower edge
    gamma_upper: float  # tier bin upper edge
    category: str
    percentile_hint: float  # tier position as a 0-100 scale

    def describe(self) -> str:
        return (
            f"Tier {self.tier}/{NUM_TIERS} — {self.category} "
            f"(gamma {self.gamma:+.3f}, tier range "
            f"[{self.gamma_lower:+.2f}, {self.gamma_upper:+.2f}))"
        )


def tier_bounds(tier: int) -> tuple[float, float]:
    """Gamma interval [lower, upper) covered by a tier."""
    if not 1 <= tier <= NUM_TIERS:
        raise ValueError(f"tier must be in 1..{NUM_TIERS}")
    return float(_EDGES[tier - 1]), float(_EDGES[tier])


def tier_gamma(tier: int) -> float:
    """Representative gamma for a tier (bin midpoint)."""
    lo, hi = tier_bounds(tier)
    return (lo + hi) / 2.0


def _category(tier: int) -> str:
    for last, label in _CATEGORY_BANDS:
        if tier <= last:
            return label
    return _CATEGORY_BANDS[-1][1]


def gamma_to_tier(gamma: float) -> TierPlacement:
    """Place a gamma estimate into one of the 50 tiers."""
    if not np.isfinite(gamma):
        raise ValueError("gamma must be finite")
    clipped = float(np.clip(gamma, GAMMA_MIN, GAMMA_MAX))
    # searchsorted with side='right' puts a value equal to an edge into
    # the higher tier; clip handles gamma == GAMMA_MAX.
    tier = int(np.searchsorted(_EDGES, clipped, side="right"))
    tier = int(np.clip(tier, 1, NUM_TIERS))
    lo, hi = tier_bounds(tier)
    return TierPlacement(
        tier=tier,
        gamma=float(gamma),
        gamma_lower=lo,
        gamma_upper=hi,
        category=_category(tier),
        percentile_hint=round(100.0 * (tier - 0.5) / NUM_TIERS, 1),
    )
