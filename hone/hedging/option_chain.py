"""Select and price option hedges from a live chain, with a model fallback.

The hedging engine wants, for a target expiry and strike, the market
price and implied volatility of a specific put or call.  A live Alpaca
option-chain snapshot rarely has a contract at the exact strike/expiry
we computed, so this module:

1. picks the listed expiration closest to the requested horizon,
2. picks the listed strike closest to the requested strike, and
3. returns that contract's mid price and implied volatility.

When no chain is available (no keys, no options entitlement, or the
underlying has no listed options) callers fall back to the Black-Scholes
pricer in :mod:`hone.hedging.black_scholes`.  The point of preferring the
chain is that real premiums embed the volatility *skew* and supply/demand
that a single flat-vol model misses — protective puts in particular trade
rich to Black-Scholes, so model costs understate the true hedge cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class QuotedContract:
    symbol: str
    type: str  # "call" | "put"
    strike: float
    expiration: str  # ISO date
    price: float  # per share (mid)
    iv: float | None
    days_to_expiry: int
    source: str = "alpaca_chain"


def _days_between(expiry_iso: str, as_of: date) -> int:
    exp = datetime.strptime(expiry_iso, "%Y-%m-%d").date()
    return (exp - as_of).days


def select_contract(
    chain: list[dict],
    option_type: str,
    target_strike: float,
    target_days: float,
    as_of: date | None = None,
) -> QuotedContract | None:
    """Closest-listed contract to a target (type, strike, horizon).

    Returns ``None`` if the chain has no priced contract of that type
    with a future expiration — the caller then uses the model price.
    """
    as_of = as_of or date.today()
    candidates = [
        c
        for c in chain
        if c.get("type") == option_type
        and c.get("mid")
        and c.get("strike")
        and _days_between(c["expiration"], as_of) > 0
    ]
    if not candidates:
        return None

    # nearest expiration to the target horizon, then nearest strike
    def expiry_gap(c):
        return abs(_days_between(c["expiration"], as_of) - target_days)

    best_expiry = min(candidates, key=expiry_gap)["expiration"]
    same_expiry = [c for c in candidates if c["expiration"] == best_expiry]
    best = min(same_expiry, key=lambda c: abs(c["strike"] - target_strike))
    return QuotedContract(
        symbol=best["symbol"],
        type=best["type"],
        strike=float(best["strike"]),
        expiration=best["expiration"],
        price=float(best["mid"]),
        iv=(float(best["iv"]) if best.get("iv") is not None else None),
        days_to_expiry=_days_between(best["expiration"], as_of),
    )
