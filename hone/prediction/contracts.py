"""Binary event contracts: prices as probabilities, and what they cost to trade.

A Kalshi contract pays **$1.00** if its event resolves YES and $0 otherwise.
The price of the YES side, between $0.01 and $0.99, is therefore the
market's probability of the event; the NO side is the complement, and the
two always sum to $1.  That one fact is most of what a hedger needs:

* a YES at 35¢ says "the market thinks 35%";
* buying 100 YES costs $35 and pays $100 if the event happens — a gain of
  $65, or $0.65 per contract, which is (1 - price) per dollar at stake;
* buying the NO at 65¢ is the identical bet in reverse.

Two frictions matter for sizing and are modelled here:

**The spread.**  You buy at the ask and sell at the bid.  The midpoint is the
best single estimate of the market's probability; the gap is what you pay
to get in and out.  Thin markets (many of the weather ones) have spreads of
30–50¢ — wide enough to change the answer, which is why the sizing tool
prices at the ask, not the midpoint.

**Fees.**  Kalshi charges a taker fee proportional to ``price * (1 - price)``:
cheapest at the extremes, most expensive on a coin flip.  The published
formula is ``fee = ceil_to_cent(0.07 * contracts * P * (1 - P))`` for most
series, times a per-series multiplier that the API reports as
``fee_multiplier``.  Resting (maker) orders are typically free.  The fee is
charged when the trade happens; holding to settlement costs nothing more.
Exact schedules change — this is an indicative model, and the page says so.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: Kalshi's standard taker fee rate: fee = rate * C * P * (1 - P).
KALSHI_TAKER_FEE_RATE = 0.07


def kalshi_fee(
    contracts: float,
    price: float,
    multiplier: float = 1.0,
    rate: float = KALSHI_TAKER_FEE_RATE,
    round_up: bool = True,
) -> float:
    """Indicative taker fee in dollars for buying ``contracts`` at ``price``.

    ``price`` is the dollar price of whichever side is bought; the formula
    is symmetric, so buying NO at (1 - p) costs the same as buying YES at p.
    With ``round_up`` the total is rounded up to the next cent, as the
    exchange does; the optimizer passes ``round_up=False`` so the objective
    stays smooth, then reports the rounded figure.
    """
    if contracts < 0:
        raise ValueError("contracts must be non-negative")
    if not 0.0 <= price <= 1.0:
        raise ValueError("price must be between 0 and 1")
    raw = rate * multiplier * contracts * price * (1.0 - price)
    if not round_up:
        return float(raw)
    return math.ceil(raw * 100.0 - 1e-9) / 100.0


def implied_probability(
    yes_bid: float | None,
    yes_ask: float | None,
    last_price: float | None = None,
) -> float | None:
    """The market's probability of YES, read from the order book.

    Midpoint of bid and ask when both sides exist and the spread is not
    degenerate (an ask of $1.00 with a bid of $0.00 is an empty book, not a
    50% opinion); otherwise the last trade; otherwise unknown.
    """
    has_bid = yes_bid is not None and yes_bid > 0.0
    has_ask = yes_ask is not None and yes_ask < 1.0
    if has_bid and has_ask:
        return float((yes_bid + yes_ask) / 2.0)
    if last_price is not None and 0.0 < last_price < 1.0:
        return float(last_price)
    if has_ask and yes_ask is not None:
        return float(yes_ask)
    if has_bid and yes_bid is not None:
        return float(yes_bid)
    return None


@dataclass(frozen=True)
class Contract:
    """One side of a binary market, as the hedger would buy it.

    ``price`` is the ask of the side that pays when the hedger's bad
    outcome happens — YES on "snowfall above X inches" is the *wrong* side
    for a ski instructor; the NO at (1 - yes_ask) is the right one.
    """

    ticker: str
    side: str  # "yes" or "no"
    price: float  # ask of the side bought, dollars
    fee_multiplier: float = 1.0
    title: str = ""

    def __post_init__(self) -> None:
        if self.side not in ("yes", "no"):
            raise ValueError("side must be 'yes' or 'no'")
        if not 0.0 < self.price < 1.0:
            raise ValueError("price must be strictly between 0 and 1")

    @property
    def payout_per_dollar(self) -> float:
        """Net gain per dollar spent if the contract pays: (1 - p) / p."""
        return (1.0 - self.price) / self.price

    def cost(self, contracts: int) -> float:
        """Cash to buy ``contracts``, fee included."""
        return contracts * self.price + kalshi_fee(
            contracts, self.price, self.fee_multiplier
        )
