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

Everything here is a one-period model with a binary event. It knows
nothing about position limits or taxes — see ``docs/PREDICTION_MARKETS.md``.

Liquidity
---------
The utility maximum above assumes any number of contracts can be bought
at the quoted price. :mod:`hone.prediction.liquidity` caps the proposed
position at what the market can actually supply (order-book depth near
the price, and a share of open interest). Because expected utility is
concave in the position, any size between zero and the optimum still
beats not hedging — so a capped hedge is worse than the ideal, never
worse than nothing. The plan reports both sizes and how much of the
wanted protection the capped one covers.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, replace

import numpy as np
from scipy.optimize import minimize_scalar

from .contracts import KALSHI_TAKER_FEE_RATE, kalshi_fee
from .liquidity import Liquidity, average_fill, limit_for

#: Safety margins used ONLY when choosing the size (every dollar figure shown
#: uses the real price and the stated inputs). From the misspecification
#: study (research/prediction/findings/05_misspecification.md): when the
#: model's assumptions are off, these cut the share of people a hedge hurts
#: from 24% to 10% and the average harm ~4x, for ~19% less value when the
#: model is exactly right. Set either to its neutral value (1.0 / 0.0) per
#: exposure when an input is known precisely.
#:   BASIS_SHRINK  — size as if the contract tracks your loss this much less
#:                   closely than you said (people overestimate basis).
#:   PRICE_BUFFER  — size as if every contract cost this much more (slippage,
#:                   stale quotes, a few cents of market bias).
BASIS_SHRINK = 0.75
PRICE_BUFFER = 0.01

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
    if gamma <= 0:
        # risk-neutral or risk-loving: no finite CRRA form; use the mean
        # (neutral) — only reached for display, never for sizing
        return float(np.sum(probs * wealth))
    return math.exp(_log_ce(wealth, probs, gamma))


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
        return float(np.clip(market_prob, 0.01, 0.99))
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
    # Floating-point residue (~1e-17) in states that can't happen would
    # otherwise count as possible and distort sizing at high gamma.
    snap = lambda x: 0.0 if x < 1e-12 else x
    states = [
        State(snap(p11), True, True),
        State(snap(p10), True, False),
        State(snap(p01), False, True),
        State(snap(p00), False, False),
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
    #: None = automatic: selling the protective side is allowed only with
    #: no income at stake. Someone with exposure is never told to sell the
    #: protection they need (half of optimists were, before this).
    allow_selling: bool | None = None
    #: what the market can actually supply; None = unknown (no cap)
    liquidity: Liquidity | None = None
    #: the person's own chance of the bad outcome, when it differs from the
    #: contract's (e.g. a layoff is rarer than "unemployment above 4.5%").
    #: None = the same event, so the same probability.
    loss_prob: float | None = None
    #: sizing safety margins (see BASIS_SHRINK / PRICE_BUFFER above)
    basis_shrink: float = BASIS_SHRINK
    price_buffer: float = PRICE_BUFFER

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
        if self.loss_prob is not None and not 0.0 < self.loss_prob < 1.0:
            raise ValueError("loss probability must be strictly between 0 and 1")


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
    #: decomposition: insurance = the best position at MARKET odds; view =
    #: what the user's own probability adds or removes (capped for hedgers)
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
    #: liquidity: the size the model wanted before the cap, the cap itself,
    #: what decided it, and the average price the proposed size would fill at
    contracts_wanted: int = 0
    liquidity_limit: float | None = None
    liquidity_capped: bool = False
    liquidity_basis: str = "unknown"
    avg_fill_price: float | None = None
    #: proposed / wanted; 1.0 when not capped, 0.0 when nothing can be bought
    coverage: float = 1.0
    #: the contract-for-every-dollar-at-risk size (rho x L, scaled when the
    #: loss and the event have different probabilities) — a reference point
    variance_min_contracts: float = 0.0
    #: true when the view-driven part was limited (MAX_VIEW_TILT)
    view_tilt_capped: bool = False
    #: the probability of the person's own bad outcome that was used
    loss_prob: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ------------------------------------------------------------ the core
#
# How a position is chosen (v2, after the segment sweeps and property tests
# in research/prediction/findings/):
#
#   1. Insurance at market odds: the best position if the market price is
#      the true probability. This is the hedge.
#   2. Your view: the best position at your blended probability. The extra
#      contracts it adds (or removes) are a bet on your view, and for anyone
#      with income at risk that bet is capped at MAX_VIEW_TILT x the
#      insurance, so a wrong view can't turn a hedge into a large wager.
#   3. What the market can supply: the order book is walked contract by
#      contract (each one costs what it really costs), within the liquidity
#      cap, and never past the size from steps 1-2.
#   4. Not worth it: if the result is worth less than MIN_WORTH, propose
#      nothing — a $0.40 improvement isn't advice.
#
# Edit the constants below to change the policy.

#: States less likely than this are treated as impossible. Without this, a
#: state that can't happen (e.g. "lost income but the contract didn't pay"
#: when basis = 1) still set the solvency limit and shrank hedges ~10x.
EPS_PROB = 1e-12
#: For people with income at risk, the view-driven part of a position is at
#: most this multiple of the insurance part. Capping at 1.0 cut the
#: 1st-percentile outcome from -37% to -0.8% of income in the segment sweep;
#: 0.25 keeps nearly the same upside when the view is right (48% vs 50% of
#: the view's value) with a tighter worst case (misspecification study).
MAX_VIEW_TILT = 0.25
#: Positions worth less than max(MIN_WORTH_DOLLARS, MIN_WORTH_FRAC x wealth)
#: to the user (certainty-equivalent gain) are not proposed.
MIN_WORTH_DOLLARS = 5.0
MIN_WORTH_FRAC = 0.0005
#: Below this basis correlation the contract barely tracks the loss.
WEAK_BASIS = 0.2


def _live(states: list[State]) -> list[State]:
    """Only the states that can actually happen."""
    return [st for st in states if st.prob > EPS_PROB]


def _ladder_cost(asks: list[tuple[float, float]], n: float) -> float:
    """Cash to buy n contracts walking up ``asks``; beyond the book, the last price."""
    left, paid, last = n, 0.0, asks[-1][0]
    for price, qty in asks:
        take = min(left, qty)
        paid += take * price
        left -= take
        if left <= 0:
            return paid
    return paid + left * last


class _Pricer:
    """What a signed position really costs: cash out the door, and the fee.

    n > 0 buys the side that pays when you lose; n < 0 buys the *other*
    side (what "selling" this side means on Kalshi). With an order book the
    cost of each extra contract is what the book charges for it; without
    one, every contract costs the quoted price.
    """

    def __init__(self, exp: "IncomeExposure", use_book: bool = True, buffer: float = 0.0):
        self.exp = exp
        #: extra cost per contract assumed when sizing (PRICE_BUFFER); 0 for accounting
        self.buffer = buffer
        liq = exp.liquidity if use_book else None
        self.asks_buy = liq.asks_buy if liq is not None and liq.asks_buy else None
        self.asks_sell = liq.asks_sell if liq is not None and liq.asks_sell else None

    def cash(self, n: float) -> float:
        if n >= 0:
            base = _ladder_cost(self.asks_buy, n) if self.asks_buy else n * self.exp.price
            return base + self.buffer * n
        m = -n
        base = _ladder_cost(self.asks_sell, m) if self.asks_sell else m * (1.0 - self.exp.price)
        return base + self.buffer * m

    def avg_price(self, n: float) -> float:
        """Average price per contract of the side actually bought."""
        if n == 0:
            return self.exp.price if n >= 0 else 1.0 - self.exp.price
        return self.cash(n) / abs(n)

    def fee(self, n: float, smooth: bool) -> float:
        if n == 0:
            return 0.0
        # Kalshi charges on the real price, never the sizing buffer.
        real = (self.cash(n) - self.buffer * abs(n)) / abs(n)
        real = min(max(real, 1e-6), 1.0 - 1e-6)
        return kalshi_fee(abs(n), real, self.exp.fee_multiplier,
                          self.exp.fee_rate, round_up=not smooth)


def _wealth_at(
    exp: "IncomeExposure", states: list[State], n: float, pricer: _Pricer, smooth_fee: bool
) -> tuple[np.ndarray, np.ndarray]:
    """End-of-season wealth in each state, and the state probabilities."""
    cash, fee = pricer.cash(n), pricer.fee(n, smooth_fee)
    w = []
    for st in states:
        base = exp.wealth - (exp.loss if st.loss else 0.0) - cash - fee
        # A long position collects $1 per contract when its side pays; a
        # short (other-side) position collects $1 when it doesn't.
        collect = n if (n >= 0 and st.pays) else (-n if (n < 0 and not st.pays) else 0.0)
        w.append(base + collect)
    return np.array(w), np.array([st.prob for st in states])


def _wealth(
    exp: IncomeExposure, states: list[State], n: float, smooth_fee: bool
) -> tuple[np.ndarray, np.ndarray]:
    """Wealth per state at the quoted price (kept for callers and tests)."""
    return _wealth_at(exp, states, n, _Pricer(exp, use_book=False), smooth_fee)


def _log_ce(w: np.ndarray, p: np.ndarray, gamma: float) -> float:
    """log of the CRRA certainty equivalent, computed so it can't overflow.

    log CE = (1/(1-g)) * log sum_s p_s * w_s^(1-g), evaluated with the
    log-sum-exp trick. The old w**(1-g) form underflowed to 0 around
    g = 60 and crashed (ZeroDivisionError -> HTTP 500).
    """
    if np.any(w <= 0):
        return -np.inf
    lw = np.log(w)
    if abs(gamma - 1.0) < 1e-9:
        return float(np.sum(p * lw))
    a = (1.0 - gamma) * lw + np.log(np.maximum(p, 1e-300))
    m = float(np.max(a))
    return float((m + math.log(float(np.sum(np.exp(a - m))))) / (1.0 - gamma))


def _bounds(
    exp: IncomeExposure, states: list[State] | None = None, pricer: _Pricer | None = None
) -> tuple[float, float]:
    """Largest long and short positions that keep wealth positive in every
    state that can actually happen (impossible states are ignored)."""
    if states is None:
        q = exp.market_prob if exp.market_prob is not None else exp.price
        states, _ = joint_states(q, q, exp.basis_correlation)
    live = _live(states)
    pricer = pricer or _Pricer(exp, use_book=False)
    fee_up = 1.0 + exp.fee_rate * exp.fee_multiplier

    def solvent(n: float) -> bool:
        w, _ = _wealth_at(exp, live, n, pricer, smooth_fee=False)
        return bool(np.all(w > 0))

    def edge(sign: int, rough: float) -> float:
        # Bisection between 0 (solvent: loss < wealth) and a rough bound.
        if rough <= 0:
            return 0.0
        lo_n, hi_n = 0.0, rough
        if solvent(sign * hi_n):
            return sign * 0.995 * hi_n
        for _ in range(60):
            mid = 0.5 * (lo_n + hi_n)
            lo_n, hi_n = (mid, hi_n) if solvent(sign * mid) else (lo_n, mid)
        return sign * 0.995 * lo_n

    w0 = {id(st): exp.wealth - (exp.loss if st.loss else 0.0) for st in live}
    nonpay = [w0[id(st)] for st in live if not st.pays]
    pay = [w0[id(st)] for st in live if st.pays]
    # Long contracts lose their cost in states where they don't pay; with no
    # such state possible, wealth can't go negative from buying (cap at a
    # large multiple of wealth so the search stays finite).
    rough_hi = (min(nonpay) / (exp.price * fee_up)) if nonpay else 50.0 * exp.wealth
    rough_lo = (min(pay) / ((1.0 - exp.price) * fee_up)) if pay else 50.0 * exp.wealth
    hi = edge(+1, rough_hi)
    selling = exp.allow_selling if exp.allow_selling is not None else exp.loss == 0
    lo = edge(-1, rough_lo) if selling else 0.0
    return lo, hi


def _expected_utility(exp: IncomeExposure, states: list[State], n: float) -> float:
    """Expected CRRA utility at the quoted price (kept for callers and tests).
    Sizing uses :func:`_log_ce`, which is the same ranking without overflow."""
    w, p = _wealth(exp, _live(states), n, smooth_fee=True)
    if np.any(w <= 0):
        return -np.inf
    return float(np.sum(p * crra_utility(w, exp.gamma)))


def _marginal_price(asks: list[tuple[float, float]] | None, n: float, flat: float) -> float:
    """Price of the n-th contract (the level of the book it comes from)."""
    if not asks:
        return flat
    left = n
    for price, qty in asks:
        if left < qty:
            return price
        left -= qty
    return asks[-1][0]


def _slope(exp: IncomeExposure, live: list[State], n: float, pricer: _Pricer) -> float:
    """d E[U] / dn, rescaled so it can't overflow (only its sign matters).

    One more contract changes wealth in state s by (what it pays there) -
    (what it costs at the margin). Each state is weighted by p_s * U'(w_s)
    = p_s * w_s^-gamma, divided by the largest weight.
    """
    w, p = _wealth_at(exp, live, n, pricer, smooth_fee=True)
    if np.any(w <= 0):
        return -np.inf if n > 0 else np.inf
    lw = -exp.gamma * np.log(w) + np.log(np.maximum(p, 1e-300))
    weight = np.exp(lw - lw.max())
    h = max(1e-3, 1e-7 * abs(n))
    dfee = (pricer.fee(n + h, True) - pricer.fee(n - h, True)) / (2 * h) if n - h != 0 or n + h != 0 else 0.0
    if n >= 0:
        mp = _marginal_price(pricer.asks_buy, n, exp.price) + pricer.buffer
        dw = np.array([(1.0 if st.pays else 0.0) - mp for st in live]) - dfee
    else:
        mp = _marginal_price(pricer.asks_sell, -n, 1.0 - exp.price) + pricer.buffer
        dw = np.array([mp - (0.0 if st.pays else 1.0) for st in live]) - dfee
    return float(np.sum(weight * dw))


def _argmax(
    exp: IncomeExposure, states: list[State], lo: float, hi: float, pricer: _Pricer
) -> float:
    """Continuous n in [lo, hi] maximizing expected CRRA utility.

    Expected utility is concave in n, so its slope falls as n grows: the
    optimum is where the slope crosses zero (or an edge if it never does).
    Finding that crossing by bisection is exact; searching the utility
    itself was not, because near the optimum it is flat to 16 digits on
    large portfolios (the property tests caught errors of ~12 contracts and
    a sign flip).
    """
    if hi - lo <= 1e-9:
        return float(lo)
    live = _live(states)
    if _slope(exp, live, lo, pricer) <= 0:
        n = lo
    elif _slope(exp, live, hi, pricer) >= 0:
        n = hi
    else:
        a, b = lo, hi
        for _ in range(200):
            mid = 0.5 * (a + b)
            if _slope(exp, live, mid, pricer) > 0:
                a = mid
            else:
                b = mid
            if b - a <= 1e-9 * max(1.0, abs(mid)):
                break
        n = 0.5 * (a + b)
    if abs(n) < 0.01:
        n = 0.0
    return float(n)


def optimal_contracts(exp: IncomeExposure, states: list[State]) -> float:
    """Continuous n maximizing expected CRRA utility within the solvency
    bounds, at the quoted price, ignoring liquidity."""
    if exp.gamma <= 0:
        return 0.0
    pricer = _Pricer(exp, use_book=False)
    lo, hi = _bounds(exp, states, pricer)
    if hi <= 0 and lo >= 0:
        return 0.0
    return _argmax(exp, states, lo, hi, pricer)


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
    live = _live(states)
    w0 = np.array([wealth - (loss if st.loss else 0.0) for st in live])
    p = np.array([st.prob for st in live])
    pays = np.array([1.0 if st.pays else 0.0 for st in live])
    # Scale by the smallest wealth before powering, so high gamma can't
    # overflow: the ratio below is unchanged by the scale.
    mu = (w0 / w0.min()) ** (-gamma) if gamma != 0 else np.ones_like(w0)
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


def _round_solvent(
    exp, states, n: float, wanted: int, limit: float | None, pricer: _Pricer
) -> int:
    """Whole contracts: the best of floor(n), ceil(n) and the ideal size,
    among those that stay solvent, keep n's direction, and respect the
    ideal size and the liquidity limit. Plain rounding could land one
    contract past the solvency edge, or one short of an uncapped ideal."""
    if n == 0 or wanted == 0:
        return 0
    live = _live(states)
    best, best_val = 0, _log_ce(*_wealth_at(exp, live, 0.0, pricer, False), exp.gamma)
    for k in sorted({math.floor(n), math.ceil(n), wanted}, key=lambda k: abs(k - n)):
        if k == 0 or k * n < 0 or abs(k) > abs(wanted):
            continue
        if limit is not None and abs(k) > limit:
            continue
        w, p = _wealth_at(exp, live, float(k), pricer, False)
        if not np.all(w > 0):
            continue
        v = _log_ce(w, p, exp.gamma)
        if v > best_val:
            best, best_val = int(k), v
    return best


def hedge_income(exp: IncomeExposure) -> ContractHedgePlan:
    """Size the contract position for this exposure at this gamma."""
    exp.validate()
    market_prob = float(np.clip(exp.market_prob if exp.market_prob is not None else exp.price, 0.01, 0.99))
    belief = blend_belief(market_prob, exp.own_prob, exp.confidence)
    has_view = exp.own_prob is not None and exp.confidence > 0
    # The person's own chance of the bad outcome. By default it's the same
    # event as the contract's; set loss_prob when you know it differs (a
    # layoff is rarer than "unemployment above X").
    q_loss_mkt = exp.loss_prob if exp.loss_prob is not None else market_prob
    q_loss = exp.loss_prob if exp.loss_prob is not None else belief
    # Accounting (what's shown) uses the stated inputs...
    states, rho_eff = joint_states(belief, q_loss, exp.basis_correlation)
    clipped = rho_eff < exp.basis_correlation - 1e-9
    selling = exp.allow_selling if exp.allow_selling is not None else exp.loss == 0
    book_pricer = _Pricer(exp, use_book=True)
    # ...sizing uses the safety margins: a little less basis, a little more cost.
    rho_size = exp.basis_correlation * exp.basis_shrink
    states_size, _ = joint_states(belief, q_loss, rho_size)
    states_mkt, _ = joint_states(market_prob, q_loss_mkt, rho_size)
    quote_pricer = _Pricer(exp, use_book=False, buffer=exp.price_buffer)
    size_pricer = _Pricer(exp, use_book=True, buffer=exp.price_buffer)
    warnings: list[str] = []

    # ---- 1-2. insurance at market odds, plus a capped view tilt
    var_e, var_l = belief * (1 - belief), q_loss * (1 - q_loss)
    variance_min = rho_eff * exp.loss * (math.sqrt(var_l / var_e) if var_e > 0 else 0.0)

    def policy(pricer: _Pricer, limit_buy: float | None, limit_sell: float | None):
        """The sizing rule, at one set of prices and limits:
        (insurance at market odds, your-view optimum, chosen size, view capped?).
        Run once at the quoted price for the ideal, then again at the real
        order book and liquidity limits for what to actually do — the same
        rule both times, so the view cap holds in both directions."""
        def bnds(st):
            lo_, hi_ = _bounds(exp, st, pricer)
            if limit_buy is not None:
                hi_ = min(hi_, limit_buy)
            if limit_sell is not None:
                lo_ = max(lo_, -limit_sell)
            if not selling:
                lo_ = max(lo_, 0.0)
            return lo_, max(hi_, lo_)
        n_m = _argmax(exp, states_mkt, *bnds(states_mkt), pricer) if exp.loss > 0 else 0.0
        n_v = _argmax(exp, states_size, *bnds(states_size), pricer) if has_view else n_m
        tilt, t_capped = n_v - n_m, False
        if exp.loss > 0 and has_view:
            room = MAX_VIEW_TILT * max(abs(n_m), variance_min)
            if abs(tilt) > room:
                tilt, t_capped = math.copysign(room, tilt), True
        target = n_m + tilt
        if not selling:
            target = max(target, 0.0)
        return n_m, n_v, target, t_capped

    lim_buy = limit_for(exp.liquidity, buying=True)
    lim_sell = limit_for(exp.liquidity, buying=False)
    if exp.gamma <= 0:
        n_mkt = n_view = n_target = 0.0
        tilt_capped = False
        warnings.append(
            "Your measured risk aversion is at or below zero — risk-neutral or "
            "risk-seeking. Preferences like that don't want insurance, so Hone "
            "proposes no position. If that isn't how you feel about a bad season, "
            "retake the questionnaire."
        )
    else:
        n_mkt, n_view, n_target, tilt_capped = policy(quote_pricer, None, None)
    # The ideal in whole contracts: the better of the two neighbours (fees
    # round to cents, so plain rounding isn't always the better one) —
    # never more than ordinary rounding of the target allows.
    contracts_wanted = (
        _round_solvent(exp, states_size, n_target, int(round(abs(n_target))), None, quote_pricer)
        if exp.gamma > 0 else 0
    )

    # ---- 3. what the market can supply, at what it really costs
    lim = lim_buy if n_target >= 0 else lim_sell
    if exp.gamma > 0 and contracts_wanted != 0:
        _, _, n_star, _ = policy(size_pricer, lim_buy.limit, lim_sell.limit)
        # Liquidity and book costs can only shrink the ideal, never flip or grow it.
        n_star = min(max(n_star, 0.0), n_target) if n_target >= 0 else max(min(n_star, 0.0), n_target)
    else:
        n_star = 0.0
    contracts = _round_solvent(exp, states_size, n_star, contracts_wanted, lim.limit, size_pricer)
    # The margins make sizing stricter, never looser — but check the real
    # (stated) world too: the position must be solvent there as well.
    if contracts != 0:
        w_chk, _ = _wealth_at(exp, _live(states), float(contracts), book_pricer, False)
        if not np.all(w_chk > 0):
            contracts = 0
    capped = lim.limit is not None and abs(contracts_wanted) > lim.limit

    # ---- accounting at the real fill
    live = _live(states)
    w_un, probs = _wealth_at(exp, live, 0.0, book_pricer, smooth_fee=False)
    w_hd, _ = _wealth_at(exp, live, float(contracts), book_pricer, smooth_fee=False)
    ce_un = math.exp(_log_ce(w_un, probs, exp.gamma)) if exp.gamma > 0 else float(np.sum(probs * w_un))
    ce_hd = math.exp(_log_ce(w_hd, probs, exp.gamma)) if exp.gamma > 0 else float(np.sum(probs * w_hd))

    # ---- 4. not worth proposing
    floor_worth = max(MIN_WORTH_DOLLARS, MIN_WORTH_FRAC * exp.wealth)
    if contracts != 0 and ce_hd - ce_un < floor_worth:
        worth = max(ce_hd - ce_un, 0)
        if capped:
            # The market, not the economics, is the reason: say so.
            warnings.append(
                f"Your risk profile wants {abs(contracts_wanted):,} contracts, but this market can "
                f"only supply {abs(contracts):,}, and that much is worth just ${worth:,.2f} to you — "
                f"under the ${floor_worth:,.0f} Hone treats as worth acting on. Look for a more "
                "heavily traded market that tracks the same risk."
            )
        else:
            warnings.append(
                f"The best position here is worth only ${worth:,.2f} to you — under the "
                f"${floor_worth:,.0f} Hone treats as worth acting on, so it proposes nothing. "
                "Exchange fees take most of the value of insuring a loss this size relative to "
                "your savings; it becomes worth it with a bigger exposure or a thinner cushion."
            )
        contracts = 0
        not_worth = True
        w_hd, ce_hd = w_un, ce_un
    else:
        not_worth = False

    direction = "buy" if contracts >= 0 else "sell"
    avg_fill = None
    if contracts != 0:
        side_avg = book_pricer.avg_price(float(contracts))
        avg_fill = side_avg if contracts > 0 else 1.0 - side_avg
    fill_price = avg_fill if avg_fill is not None else exp.price
    fee = book_pricer.fee(float(contracts), smooth=False)
    cost = (book_pricer.cash(float(contracts)) + fee) if contracts != 0 else 0.0

    c_max = reservation_price(exp.wealth, exp.loss, exp.gamma, states)

    # pure-speculation reference at the same gamma and price
    kelly = kelly_fraction(belief, exp.price)
    spec_only = replace(exp, loss=0.0, basis_correlation=0.0, liquidity=None, allow_selling=True, loss_prob=None)
    spec_states, _ = joint_states(belief, belief, 0.0)
    n_spec = optimal_contracts(spec_only, spec_states)
    stake = n_spec * exp.price if n_spec >= 0 else n_spec * (1.0 - exp.price)
    crra_frac = float(stake / exp.wealth)

    def _std(w: np.ndarray) -> float:
        m = float(np.sum(probs * w))
        return float(math.sqrt(max(np.sum(probs * (w - m) ** 2), 0.0)))

    # ---- explanations
    if exp.loss > 0 and contracts > 0 and fill_price > c_max:
        warnings.append(
            f"At ${fill_price:.2f} this contract costs more than the "
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
    if tilt_capped:
        warnings.append(
            f"Your view of the odds would push the position to about {round(n_view):,} "
            f"contracts. Hone limits the part that comes from your view to the size "
            "of the insurance itself, so a wrong view can't turn a hedge into a big bet."
        )
    if exp.loss > 0 and clipped:
        warnings.append(
            f"A basis correlation of {exp.basis_correlation:.2f} is not "
            f"achievable at this probability; {rho_eff:.2f} was used."
        )
    if exp.loss > 0 and rho_eff < WEAK_BASIS:
        warnings.append(
            f"This contract tracks your loss only weakly (correlation {rho_eff:.2f}): most "
            "bad seasons for you won't be bad for it. It can't protect much of your income; "
            "look for a market closer to what actually drives your earnings."
        )
    if exp.loss > 0 and rho_eff < 1 and variance_min > 0 and 0 < n_mkt < 0.6 * variance_min:
        warnings.append(
            "Because this contract may not pay in a season that's bad for you, buying "
            "more would make that worst case worse — so Hone suggests less than the "
            "contract-for-every-dollar-at-risk amount. (Known effect of basis risk; "
            "see Clarke 2016.)"
        )
    if cost > 0.25 * exp.wealth:
        warnings.append(
            f"This position ties up {cost / exp.wealth:.0%} of your wealth until "
            "the market settles. Check the close date before committing."
        )
    if capped and not_worth:
        pass  # explained above, with the numbers
    elif capped and contracts == 0 and contracts_wanted != 0:
        where = (
            "on offer near the current price" if "order book" in lim.basis
            else "open in this market"
        )
        warnings.append(
            f"Your risk profile wants {abs(contracts_wanted):,} contracts, but "
            f"there are none {where}, so this market can't hedge you right now. "
            "Look for a more heavily traded market that tracks the same risk."
        )
    elif capped:
        why = {
            "order book": f"only {lim.limit:,.0f} are on offer within "
            f"{exp.liquidity.max_slippage * 100:.0f}¢ of the current price",
            "open interest": f"Hone caps a position at "
            f"{exp.liquidity.max_share_of_open_interest:.0%} of the contracts "
            f"already open in this market ({lim.limit:,.0f})",
        }.get(
            "order book" if lim.depth is not None and lim.limit == lim.depth else
            "open interest" if lim.oi_limit is not None else lim.basis,
            f"the market can only supply about {lim.limit:,.0f}",
        )
        warnings.append(
            f"Your risk profile wants {abs(contracts_wanted):,} contracts, but "
            f"{why}. The position below is capped at {abs(contracts):,}: it "
            f"gives {abs(contracts) / abs(contracts_wanted):.0%} of the "
            "protection you'd ideally want — still better than none."
        )
    elif lim.basis == "unknown" and contracts != 0 and exp.loss > 0:
        warnings.append(
            "Hone couldn't check how many of these contracts are for sale. "
            "Look at the order book before buying — thin markets may not "
            "fill a position this size at this price."
        )
    if (contracts == 0 and contracts_wanted != 0 and not capped and exp.gamma > 0
            and not any("worth acting on" in w for w in warnings)):
        side_asks = book_pricer.asks_buy if contracts_wanted > 0 else book_pricer.asks_sell
        next_price = _marginal_price(side_asks, 1.0, exp.price) if side_asks else exp.price
        warnings.append(
            f"At the quoted ${exp.price:.2f} you'd want {abs(contracts_wanted):,} contracts, "
            f"but almost nothing is offered at that price — the next offers are around "
            f"${next_price:.2f}, above the ${c_max:.2f} the protection is worth to you. "
            "Hone proposes nothing rather than overpay; a limit order at your price might fill."
        )
    if avg_fill is not None and contracts > 0 and avg_fill > exp.price + 0.005:
        warnings.append(
            f"Buying {contracts:,} contracts walks up the order book: the "
            f"average price is about ${avg_fill:.3f}, not the ${exp.price:.2f} "
            "quoted. The size and costs below account for that."
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
        for i, st in enumerate(live)
        if st.prob > 1e-9
    ]

    return ContractHedgePlan(
        gamma=exp.gamma,
        belief=belief,
        market_prob=float(market_prob),
        price=exp.price,
        basis_correlation=rho_eff,
        basis_clipped=clipped,
        n_star=float(n_target),
        contracts=contracts,
        direction=direction,
        cost=float(cost),
        fee=float(fee if contracts != 0 else 0.0),
        payout_if_pays=float(max(contracts, 0)),
        pure_hedge_contracts=float(n_mkt),
        speculative_contracts=float(n_target - n_mkt),
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
        premium_per_contract=float(fill_price - belief),
        total_premium=float(contracts * (fill_price - belief) + fee) if contracts > 0 else float(fee),
        kelly_fraction=kelly,
        crra_fraction=crra_frac,
        states=rows,
        warnings=warnings,
        needs_hedge=bool(exp.loss > 0 and contracts > 0),
        contracts_wanted=contracts_wanted,
        liquidity_limit=lim.limit,
        liquidity_capped=bool(capped),
        liquidity_basis=lim.basis,
        avg_fill_price=avg_fill,
        coverage=(
            float(abs(contracts) / abs(contracts_wanted)) if contracts_wanted else 1.0
        ),
        variance_min_contracts=float(variance_min),
        view_tilt_capped=bool(tilt_capped),
        loss_prob=float(q_loss),
    )
