"""Holt-Laury (2002) Multiple Price List experimental design.

The menu presents 10 paired choices between a "safe" lottery (Option A,
low variance) and a "risky" lottery (Option B, high variance).  Moving
down the menu the probability of the high payoff rises from 10% to 100%,
so at some decision a rational subject switches from A to B.  The switch
point brackets the CRRA risk-aversion parameter gamma in a tight
interval; the MLE engine in :mod:`hone.risk_profile.estimation` then
turns the full choice vector (across several stake scales) into a point
estimate.

Because CRRA utility is scale-invariant, the gamma interval implied by a
switch point is identical at every stake scale.  Presenting several
scales ($2 stakes up to $200 stakes) still matters: real subjects are
noisy and often not perfectly scale-consistent, and the extra choices
sharpen the maximum-likelihood estimate and identify the noise
parameter mu separately from gamma.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from scipy.optimize import brentq

# Canonical Holt-Laury payoffs (in dollars, at scale 1.0).
SAFE_HIGH = 2.00
SAFE_LOW = 1.60
RISKY_HIGH = 3.85
RISKY_LOW = 0.10

#: Stake multipliers used by default when eliciting choices.  1x is the
#: original Holt-Laury menu; 20x and 100x test scale sensitivity
#: ($2 -> $40 -> $200 top prize on the safe option).
DEFAULT_SCALES = (1.0, 20.0, 100.0)

# Practical bounds used when a subject never switches (gamma is only
# bounded on one side by the data).
GAMMA_LOWER_BOUND = -3.0
GAMMA_UPPER_BOUND = 5.0


@dataclass(frozen=True)
class Lottery:
    """A two-outcome lottery: pays ``high`` with probability ``p_high``."""

    high: float
    low: float
    p_high: float

    def outcomes(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """(payoff, probability) pairs."""
        return ((self.high, self.p_high), (self.low, 1.0 - self.p_high))


@dataclass(frozen=True)
class Decision:
    """One row of the menu: Option A (safe) vs Option B (risky)."""

    number: int  # 1-based row number
    option_a: Lottery
    option_b: Lottery
    scale: float = 1.0


def standard_menu(scale: float = 1.0, rows: int = 10) -> list[Decision]:
    """Build the Holt-Laury menu at a given stake scale.

    Row ``i`` (1-based) assigns probability ``i / rows`` to the high
    payoff in both options.
    """
    if scale <= 0:
        raise ValueError("scale must be positive")
    menu = []
    for i in range(1, rows + 1):
        p = i / rows
        menu.append(
            Decision(
                number=i,
                option_a=Lottery(SAFE_HIGH * scale, SAFE_LOW * scale, p),
                option_b=Lottery(RISKY_HIGH * scale, RISKY_LOW * scale, p),
                scale=scale,
            )
        )
    return menu


def expected_value(lottery: Lottery) -> float:
    return lottery.high * lottery.p_high + lottery.low * (1.0 - lottery.p_high)


def safe_choice_count(choices: Sequence[str]) -> int:
    """Number of safe (Option A) choices in a 10-row choice vector.

    ``choices`` is a sequence of "A"/"B" strings.  This is the summary
    statistic used for the interval method; the MLE uses the full vector.
    """
    return sum(1 for c in choices if str(c).strip().upper() == "A")


def is_monotone(choices: Sequence[str]) -> bool:
    """True if the subject switched from A to B at most once (no
    irrational back-and-forth switching)."""
    seen_b = False
    for c in choices:
        if str(c).strip().upper() == "B":
            seen_b = True
        elif seen_b:
            return False
    return True


def _crra(x: float, gamma: float) -> float:
    import math

    if x <= 0:
        raise ValueError("CRRA utility requires strictly positive payoffs")
    if abs(gamma - 1.0) < 1e-10:
        return math.log(x)
    return (x ** (1.0 - gamma)) / (1.0 - gamma)


def _eu_difference(gamma: float, decision: Decision) -> float:
    """EU(A) - EU(B) under CRRA with parameter gamma."""
    eu_a = sum(p * _crra(x, gamma) for x, p in decision.option_a.outcomes())
    eu_b = sum(p * _crra(x, gamma) for x, p in decision.option_b.outcomes())
    return eu_a - eu_b


def indifference_gamma(decision: Decision) -> float:
    """The gamma at which a CRRA agent is indifferent on this row.

    A subject with gamma above this value strictly prefers the safe
    Option A on this row; below it, the risky Option B.
    """
    # Row where B stochastically dominates A (p_high == 1): no finite
    # indifference point, everyone prefers B.
    if decision.option_b.p_high >= 1.0 - 1e-12:
        return float("inf")
    lo, hi = GAMMA_LOWER_BOUND, GAMMA_UPPER_BOUND
    f_lo, f_hi = _eu_difference(lo, decision), _eu_difference(hi, decision)
    if f_lo > 0 and f_hi > 0:  # safe preferred everywhere in range
        return lo
    if f_lo < 0 and f_hi < 0:  # risky preferred everywhere in range
        return hi
    return brentq(_eu_difference, lo, hi, args=(decision,), xtol=1e-10)


def gamma_interval(n_safe: int, scale: float = 1.0) -> tuple[float, float]:
    """CRRA gamma interval implied by choosing Option A ``n_safe`` times
    on a monotone (single-switch) 10-row menu.

    A subject who chooses A on rows 1..n and B on rows n+1..10 must have
    gamma above the indifference point of row n and below that of row
    n+1.  For example ``n_safe=5`` brackets gamma in roughly
    (0.15, 0.41) — the canonical Holt-Laury interval.
    """
    if not 0 <= n_safe <= 10:
        raise ValueError("n_safe must be between 0 and 10")
    menu = standard_menu(scale)
    if n_safe == 0:
        return (GAMMA_LOWER_BOUND, indifference_gamma(menu[0]))
    # Choosing A on row 10 is dominated; treat 10 safe choices like 9.
    n_safe = min(n_safe, 9)
    lower = indifference_gamma(menu[n_safe - 1])
    upper = (
        indifference_gamma(menu[n_safe])
        if n_safe < 9
        else GAMMA_UPPER_BOUND
    )
    return (lower, min(upper, GAMMA_UPPER_BOUND))
