"""Sizing an event contract against income risk, at the user's gamma.

The problem
-----------
Over the coming season a person expects to have wealth ``W`` (what they
will earn plus the savings they would draw on).  If a bad outcome ``D``
happens — a thin December, a cancelled ad budget, a hiring freeze — they
lose ``L`` of it.  A contract ``B`` pays $1 when the market's event
resolves the way that *accompanies* the bad outcome; it costs ``c`` per
contract plus fees.  Buying ``n`` contracts leaves

    wealth = W - L*D + n*(B - c) - fee(n, c).

The person chooses ``n`` to maximize expected CRRA utility
E[U(wealth)], U(w) = w^(1-gamma)/(1-gamma), with gamma from the Hone
questionnaire.  That is exactly the mean-variance problem on the optimize
page with a binary asset in place of stocks, and the same number — the
certainty equivalent U^-1(E[U]) — is what tells the person what the hedge
is worth in dollars.

What the answer looks like
--------------------------
Three results fall out, and each is a concept the rest of Hone already
uses:

1. **The pure hedge** n_h = rho * L: the position that minimizes the
   variance of wealth, where rho is the correlation between the market's
   event and the person's own loss (the *basis*).  With rho = 1 it is the
   whole exposure; with rho = 0.5 half of it, because the rest of the risk
   is not something this contract can see.  This is the analogue of the
   beta-sized index short in ``hone.hedging.short_hedge``.
2. **The speculative tilt** n* - n_h: zero when the contract is fairly
   priced (c equals the person's blended probability q), positive when
   they think it is cheap, negative when they think it is dear, and
   smaller the larger gamma is.  When the person has no exposure at all
   this tilt is the whole position and reduces to the CRRA bet-sizing
   rule — the Kelly fraction at gamma = 1, "half Kelly" near gamma = 2.
3. **The reservation price** c_max = E[U'(W0) B] / E[U'(W0)]: the most the
   person should pay per contract.  It is their probability of the event
   re-weighted by how much each dollar hurts in the state where they have
   lost L.  Above it the hedge is not worth having; the gap between c_max
   and q is the insurance premium their risk aversion is willing to pay.

A view against the market is blended the Black-Litterman way: the market
price is the prior, the person's probability the view, their confidence
the weight.  The journal's calibration map can be applied to that
confidence first, so a person whose record says "your 80% is really a
60%" is tilted less.

Everything here is a one-period model with a binary event.  It knows
nothing about liquidity, position limits, taxes or the chance that the
market never fills — see ``docs/PREDICTION_MARKETS.md``.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

import numpy as np
from scipy.optimize import minimize_scalar

from .contracts import KALSHI_TAKER_FEE_RATE, kalshi_fee

# ------------------------------------------------------------- utility
def crra_utility(w: np.ndarray | float, gamma: float) -> np.ndarray | float:
    """U(w) = w^(1-gamma)/(1-gamma); log utility at gamma = 1."""
    w = np.asarray(w, dtype=float)
    if abs(gamma - 1.0) < 1e-9:
        return np.log(w)
    return w ** (1.0 - gamma) / (1.0 - gamma)


def crra_inverse(u: float, gamma: float) -> float:
    """The sure wealth with utility ``u`` — U^-1."""
    if abs(gamma - 1.0) < 1e-9:
        return float(math.exp(u))
    return float(((1.0 - gamma) * u) ** (1.0 / (1.0 - gamma)))


def crra_certainty_equivalent(
    wealth: np.ndarray, probs: np.ndarray, gamma: float
) -> float:
    """Sure dollar amount worth the same as the lottery (wealth, probs)."""
    wealth = np.asarray(wealth, dtype=float)
    probs = np.asarray(probs, dtype=float)
    if np.any(wealth <= 0):
        raise ValueError("wealth must be positive in every state")
    eu = float(np.sum(probs * crra_utility(wealth, gamma)))
    return crra_inverse(eu, gamma)


# ------------------------------------------------------------ beliefs
def blend_belief(market_prob: float, own_prob: float | None, confidence: float) -> float:
    """Posterior probability after blending a view with the market price.

    Black-Litterman in one line: the market price is the equilibrium
    prior, the user's probability is the view, and confidence in [0, 1]
    is how far the posterior moves from one to the other (Idzorek's
    reading of "confidence" — 100% means the view is adopted outright, 0%
    means it is ignored).  With no view, the market's number is used.
    """
    if not 0.0 < market_prob < 1.0:
        raise ValueError("market probability must be strictly between 0 and 1")
    if own_prob is None:
        return float(market_prob)
    if not 0.0 <= own_prob <= 1.0:
        raise ValueError("own probability must be between 0 and 1")
    k = float(np.clip(confidence, 0.0, 1.0))
    q = (1.0 - k) * market_prob + k * own_prob
    # keep the posterior strictly inside (0, 1): a certainty would let the
    # optimizer bet everything, and nobody is that sure of the weather
    return float(np.clip(q, 0.01, 0.99))


# -------------------------------------------------------------- states
@dataclass(frozen=True)
class State:
    prob: float
    pays: bool  # the contract resolves in the hedger's favour
    loss: bool  # the hedger's own bad outcome happens


def joint_states(q_event: float, q_loss: float, rho: float) -> tuple[list[State], float]:
    """Joint distribution of (contract pays, income lost) with correlation rho.

    Two Bernoullis with marginals q_event and q_loss and correlation rho
    have P(both) = q_event*q_loss + rho*sqrt(var_e*var_l).  Not every rho
    is feasible (the Frechet bounds); it is clipped into [0, rho_max] and
    the value actually used is returned so the page can say so.  Negative
    correlation is excluded on purpose: the user picks the contract side
    so that it pays when they lose, and a side that paid when they *won*
    is not a hedge.
    """
    s = math.sqrt(q_event * (1 - q_event) * q_loss * (1 - q_loss))
    if s <= 0:
        rho_max = 0.0
    else:
        rho_max = min(q_event * (1 - q_loss), q_loss * (1 - q_event)) / s
    rho_eff = float(np.clip(rho, 0.0, rho_max))
    p11 = q_event * q_loss + rho_eff * s
    p10 = q_event - p11
    p01 = q_loss - p11
    p00 = 1.0 - p11 - p10 - p01
    states = [
        State(max(p11, 0.0), True, True),
        State(max(p10, 0.0), True, False),
        State(max(p01, 0.0), False, True),
        State(max(p00, 0.0), False, False),
    ]
    total = sum(st.prob for st in states)
    states = [State(st.prob / total, st.pays, st.loss) for st in states]
    return states, rho_eff


# --------------------------------------------------------------- inputs
@dataclass
class IncomeExposure:
    """What the hedger stands to lose, and on what.

    wealth
        Money available over the horizon: expected earnings plus the
        savings that would absorb a bad season.  The denominator of every
        risk-aversion calculation — a $9,000 loss is a catastrophe on
        $12,000 and an annoyance on $200,000.
    loss
        Dollars lost if the bad outcome happens.  Zero means pure
        speculation, and the result is then a bet size, not a hedge.
    price
        Ask price of the contract side that pays when the bad outcome
        happens.
    market_prob
        The market's probability of that side (midpoint); defaults to the
        price.  Used as the prior the user's view is blended into.
    own_prob / confidence
        The user's own probability of that side and how sure they are of
        it; see :func:`blend_belief`.
    basis_correlation
        How tightly the market's event tracks the user's own loss.
    """

    wealth: float
    loss: float
    price: float
    gamma: float
    market_prob: float | None = None
    own_prob: float | None = None
    confidence: float = 0.0
    basis_correlation: float = 1.0
    fee_multiplier: float = 1.0
    fee_rate: float = KALSHI_TAKER_FEE_RATE
    allow_selling: bool = True

    def validate(self) -> None:
        if not self.wealth > 0:
            raise ValueError("wealth must be positive")
        if self.loss < 0:
            raise ValueError("loss cannot be negative")
        if self.loss >= self.wealth:
            raise ValueError(
                "the loss is at least your whole wealth — a contract cannot "
                "insure more than you have; lower the loss or raise the wealth"
            )
        if not 0.0 < self.price < 1.0:
            raise ValueError("price must be strictly between $0 and $1")
        if self.market_prob is not None and not 0.0 < self.market_prob < 1.0:
            raise ValueError("market probability must be strictly between 0 and 1")
        if not 0.0 <= self.basis_correlation <= 1.0:
            raise ValueError("basis correlation must be between 0 and 1")


# -------------------------------------------------------------- outputs
@dataclass
class StateRow:
    prob: float
    pays: bool
    loss: bool
    wealth_unhedged: float
    wealth_hedged: float


@dataclass
class ContractHedgePlan:
    gamma: float
    #: probability (after blending) that the bought side pays
    belief: float
    market_prob: float
    price: float
    basis_correlation: float  # the value actually used (may be clipped)
    basis_clipped: bool
    #: continuous optimum and the whole-contract position actually proposed
    n_star: float
    contracts: int
    direction: str  # "buy" (the side that pays when you lose) or "sell"
    cost: float  # cash out the door, fee included (0 if no position)
    fee: float
    payout_if_pays: float  # gross dollars received if the side pays
    #: decomposition
    pure_hedge_contracts: float
    speculative_contracts: float
    #: dollars, at the user's gamma
    ce_unhedged: float
    ce_hedged: float
    ce_gain: float
    expected_wealth_unhedged: float
    expected_wealth_hedged: float
    worst_unhedged: float
    worst_hedged: float
    std_unhedged: float
    std_hedged: float
    #: pricing
    reservation_price: float  # most you should pay per contract
    fair_price: float  # your blended probability
    premium_per_contract: float  # price - fair (what you overpay per $1 of cover)
    total_premium: float  # contracts * premium + fee
    #: pure-speculation reference (what the same gamma would bet with no exposure)
    kelly_fraction: float
    crra_fraction: float
    states: list[StateRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    needs_hedge: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


# ------------------------------------------------------------ the core
def _wealth(
    exp: IncomeExposure, states: list[State], n: float, smooth_fee: bool
) -> tuple[np.ndarray, np.ndarray]:
    fee = kalshi_fee(abs(n), exp.price, exp.fee_multiplier, exp.fee_rate, round_up=not smooth_fee)
    w = np.array(
        [
            exp.wealth - (exp.loss if st.loss else 0.0) + n * ((1.0 if st.pays else 0.0) - exp.price) - fee
            for st in states
        ]
    )
    p = np.array([st.prob for st in states])
    return w, p


def _bounds(exp: IncomeExposure) -> tuple[float, float]:
    """Largest long and short positions that keep wealth positive everywhere."""
    cushion = exp.wealth - exp.loss  # wealth in the worst income state
    per_long = exp.price * (1.0 + exp.fee_rate * exp.fee_multiplier * (1.0 - exp.price))
    per_short = (1.0 - exp.price) * (1.0 + exp.fee_rate * exp.fee_multiplier * exp.price)
    hi = 0.995 * cushion / per_long
    lo = -0.995 * cushion / per_short if exp.allow_selling else 0.0
    return lo, hi


def _expected_utility(exp: IncomeExposure, states: list[State], n: float) -> float:
    w, p = _wealth(exp, states, n, smooth_fee=True)
    if np.any(w <= 0):
        return -np.inf
    return float(np.sum(p * crra_utility(w, exp.gamma)))


def optimal_contracts(exp: IncomeExposure, states: list[State]) -> float:
    """Continuous n maximizing expected CRRA utility within the solvency bounds."""
    lo, hi = _bounds(exp)
    if hi <= 0:
        return 0.0
    res = minimize_scalar(
        lambda n: -_expected_utility(exp, states, n),
        bounds=(lo, hi),
        method="bounded",
        options={"xatol": 1e-4},
    )
    n = float(res.x)
    # the bounded method can sit a hair inside an interior optimum of
    # exactly zero; snap tiny positions to nothing
    if abs(n) < 0.01:
        n = 0.0
    return n


def reservation_price(
    wealth: float, loss: float, gamma: float, states: list[State]
) -> float:
    """Most a hedger should pay per contract: E[U'(W0) B] / E[U'(W0)].

    At this price the marginal utility of the first contract is exactly
    zero.  U'(w) = w^-gamma, so each state's probability is re-weighted by
    how much a dollar is worth there — most in the state where income is
    lost — and the contract that pays in those states gets a higher
    personal price than its plain probability.  For gamma = 0 it collapses
    to the probability itself.
    """
    w0 = np.array([wealth - (loss if st.loss else 0.0) for st in states])
    p = np.array([st.prob for st in states])
    pays = np.array([1.0 if st.pays else 0.0 for st in states])
    mu = w0 ** (-gamma) if gamma != 0 else np.ones_like(w0)
    return float(np.sum(p * mu * pays) / np.sum(p * mu))


def kelly_fraction(belief: float, price: float) -> float:
    """Kelly stake, as a fraction of wealth, on a $1 binary paying at ``price``.

    Edge over odds: f* = (q - c) / (1 - c) when q > c (buy the side), and
    (c - q) / c when q < c (buy the other side).  Returned signed: positive
    means buy the side priced at ``price``, negative means buy the other
    side.  Log utility (gamma = 1) chooses exactly this fraction.
    """
    if belief > price:
        return float((belief - price) / (1.0 - price))
    return float(-(price - belief) / price)


def hedge_income(exp: IncomeExposure) -> ContractHedgePlan:
    """Size the contract position for this exposure at this gamma."""
    exp.validate()
    market_prob = exp.market_prob if exp.market_prob is not None else exp.price
    belief = blend_belief(market_prob, exp.own_prob, exp.confidence)
    # The bad outcome for income and the market's event share one
    # probability and are tied together with the basis correlation.
    states, rho_eff = joint_states(belief, belief, exp.basis_correlation)
    clipped = rho_eff < exp.basis_correlation - 1e-9

    warnings: list[str] = []
    if exp.gamma <= 0:
        warnings.append(
            "Your measured risk aversion is at or below zero — risk-neutral or "
            "risk-seeking. Preferences like that do not want insurance, so the "
            "position below is a bet on your belief, not a hedge. If that is "
            "not how you feel about a bad season, retake the questionnaire."
        )

    if exp.gamma <= 0:
        # Convex or linear utility has no interior optimum: the maximizer
        # would run to the solvency bound and call a 76%-of-wealth punt a
        # "hedge".  Show the variance-minimizing position instead, and let
        # the warning above explain why it is not what these preferences want.
        n_star = rho_eff * exp.loss
    else:
        n_star = optimal_contracts(exp, states)
    contracts = int(round(n_star))
    direction = "buy" if contracts >= 0 else "sell"

    # exact accounting for the whole-contract position
    w_un, probs = _wealth(exp, states, 0.0, smooth_fee=False)
    w_hd, _ = _wealth(exp, states, float(contracts), smooth_fee=False)
    fee = kalshi_fee(abs(contracts), exp.price, exp.fee_multiplier, exp.fee_rate)
    gross_cost = contracts * exp.price if contracts > 0 else abs(contracts) * (1.0 - exp.price)
    cost = gross_cost + fee if contracts != 0 else 0.0

    ce_un = crra_certainty_equivalent(w_un, probs, exp.gamma)
    ce_hd = crra_certainty_equivalent(w_hd, probs, exp.gamma)
    pure = rho_eff * exp.loss
    spec = n_star - pure
    c_max = reservation_price(exp.wealth, exp.loss, exp.gamma, states)

    # pure-speculation reference at the same gamma and price
    kelly = kelly_fraction(belief, exp.price)
    spec_only = IncomeExposure(
        wealth=exp.wealth, loss=0.0, price=exp.price, gamma=exp.gamma,
        market_prob=market_prob, own_prob=exp.own_prob, confidence=exp.confidence,
        basis_correlation=0.0, fee_multiplier=exp.fee_multiplier, fee_rate=exp.fee_rate,
    )
    spec_states, _ = joint_states(belief, belief, 0.0)
    n_spec = optimal_contracts(spec_only, spec_states)
    # fraction of wealth staked: long positions pay price per contract,
    # short positions (buying the other side) pay (1 - price)
    stake = n_spec * exp.price if n_spec >= 0 else n_spec * (1.0 - exp.price)
    crra_frac = float(stake / exp.wealth)

    def _std(w: np.ndarray) -> float:
        m = float(np.sum(probs * w))
        return float(math.sqrt(max(np.sum(probs * (w - m) ** 2), 0.0)))

    if exp.loss > 0 and contracts > 0 and exp.price > c_max:
        warnings.append(
            f"At ${exp.price:.2f} this contract costs more than the "
            f"${c_max:.2f} your risk aversion makes it worth to you — the "
            "position shown exists only because you believe the market is "
            "underpricing the event."
        )
    if exp.loss > 0 and contracts < 0:
        warnings.append(
            "The optimizer wants you to SELL the side that would protect you: "
            "your belief says this insurance is so overpriced that collecting "
            "the premium beats holding it. That is a bet against the market "
            "on top of your existing exposure. Be very sure you know "
            "something the market does not."
        )
    if exp.own_prob is not None and abs(belief - market_prob) >= 0.15:
        warnings.append(
            f"Your blended probability ({belief:.0%}) is far from the market's "
            f"({market_prob:.0%}). Prediction-market prices aggregate everyone "
            "else's information; a gap this wide usually means private "
            "knowledge or overconfidence. Hone's journal can tell you which."
        )
    if exp.loss > 0 and clipped:
        warnings.append(
            f"A basis correlation of {exp.basis_correlation:.2f} is not "
            f"achievable at this probability; {rho_eff:.2f} was used."
        )
    if cost > 0.25 * exp.wealth:
        warnings.append(
            f"This position ties up {cost / exp.wealth:.0%} of your wealth until "
            "the market settles. Check the close date before committing."
        )
    if exp.loss == 0:
        warnings.append(
            "With no income at stake there is nothing to hedge — this is "
            "the pure bet your gamma would size, shown for reference. "
            "Kelly would stake "
            f"{abs(kelly):.1%} of wealth; your gamma stakes {abs(crra_frac):.1%}."
        )

    rows = [
        StateRow(
            prob=float(st.prob), pays=st.pays, loss=st.loss,
            wealth_unhedged=float(w_un[i]), wealth_hedged=float(w_hd[i]),
        )
        for i, st in enumerate(states)
        if st.prob > 1e-9
    ]

    return ContractHedgePlan(
        gamma=exp.gamma,
        belief=belief,
        market_prob=float(market_prob),
        price=exp.price,
        basis_correlation=rho_eff,
        basis_clipped=clipped,
        n_star=n_star,
        contracts=contracts,
        direction=direction,
        cost=float(cost),
        fee=float(fee if contracts != 0 else 0.0),
        payout_if_pays=float(max(contracts, 0)),
        pure_hedge_contracts=float(pure),
        speculative_contracts=float(spec),
        ce_unhedged=ce_un,
        ce_hedged=ce_hd,
        ce_gain=ce_hd - ce_un,
        expected_wealth_unhedged=float(np.sum(probs * w_un)),
        expected_wealth_hedged=float(np.sum(probs * w_hd)),
        worst_unhedged=float(w_un.min()),
        worst_hedged=float(w_hd.min()),
        std_unhedged=_std(w_un),
        std_hedged=_std(w_hd),
        reservation_price=c_max,
        fair_price=belief,
        premium_per_contract=float(exp.price - belief),
        total_premium=float(contracts * (exp.price - belief) + fee) if contracts > 0 else float(fee),
        kelly_fraction=kelly,
        crra_fraction=crra_frac,
        states=rows,
        warnings=warnings,
        needs_hedge=bool(exp.loss > 0 and contracts > 0),
    )
