"""How many contracts can actually be bought — the liquidity cap.

The sizing model in :mod:`hone.prediction.hedge` assumes any number of
contracts can be bought at the quoted price. Real markets don't work like
that: the sample ski-season hedge asked for ~10,000 contracts in a
snowfall market with a few hundred open. This module answers "how many can
I really get, and at what average price?" so the hedge can be capped.

Two limits, and the smaller one wins:

1. **Order-book depth** — contracts on offer within ``max_slippage`` (3¢ by
   default) of the best price. Beyond that you're paying meaningfully more
   than the price the hedge was sized at.
2. **Share of open interest** — at most ``max_share_of_open_interest``
   (10% by default) of the contracts already outstanding. Even when a large
   resting order exists, being a big fraction of a thin market means you
   may not be able to exit, and you move the price for everyone.

Reading Kalshi's order book
---------------------------
Kalshi's public order book lists only *bids*: people wanting to buy YES at
some price, and people wanting to buy NO. A YES contract and a NO contract
together always pay exactly $1, so buying YES at price p means matching
someone's NO bid at 1 − p. The contracts you can buy on one side are
therefore the bids on the *other* side, priced at $1 minus the bid.

To change the defaults, edit ``DEFAULT_MAX_SHARE_OF_OI`` and
``DEFAULT_MAX_SLIPPAGE`` below.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Any

#: Never propose more than this share of a market's open interest. 25%, not
#: 10%: the segment sweep found 10% gave up most of the value for every
#: thin-market occupation, while deep markets were unaffected either way.
DEFAULT_MAX_SHARE_OF_OI = 0.25
#: Only count contracts offered within this many dollars of the best price.
DEFAULT_MAX_SLIPPAGE = 0.03


@dataclass
class Liquidity:
    """What is known about one market's tradeable size.

    ``asks_buy`` are offers for the side the hedger *buys* (the side that
    pays when they lose); ``asks_sell`` for the other side, which is what a
    "sell" recommendation actually buys. Each is a list of (price, quantity)
    sorted cheapest first. Any field may be None when unknown.
    """

    open_interest: float | None = None
    asks_buy: list[tuple[float, float]] | None = None
    asks_sell: list[tuple[float, float]] | None = None
    max_share_of_open_interest: float = DEFAULT_MAX_SHARE_OF_OI
    max_slippage: float = DEFAULT_MAX_SLIPPAGE

    @property
    def known(self) -> bool:
        return self.open_interest is not None or self.asks_buy is not None


@dataclass
class LiquidityLimit:
    """The cap for one direction, and how it was decided."""

    limit: float | None  # None = no information, so no cap
    basis: str  # "order book", "open interest", "order book and open interest", "unknown"
    depth: float | None  # contracts within the slippage band (order book)
    oi_limit: float | None  # share-of-open-interest limit


def asks_from_orderbook(orderbook: dict[str, Any], side: str) -> list[tuple[float, float]]:
    """Offers for buying ``side`` ("yes"/"no"), cheapest first.

    Accepts Kalshi's ``orderbook_fp`` shape: {"yes_dollars": [[price, qty]],
    "no_dollars": [[price, qty]]}, prices and quantities as strings.
    """
    side = side.lower()
    if side not in ("yes", "no"):
        raise ValueError("side must be 'yes' or 'no'")
    book = orderbook.get("orderbook_fp", orderbook)
    # Buying YES matches NO bids (and vice versa), at $1 minus the bid.
    opposite = book.get("no_dollars" if side == "yes" else "yes_dollars") or []
    asks: dict[float, float] = {}
    for level in opposite:
        try:
            bid, qty = float(level[0]), float(level[1])
        except (TypeError, ValueError, IndexError):
            continue
        if 0.0 < bid < 1.0 and qty > 0:
            price = round(1.0 - bid, 4)
            asks[price] = asks.get(price, 0.0) + qty
    return sorted(asks.items())


def depth_within(asks: list[tuple[float, float]], max_slippage: float) -> float:
    """Contracts offered within ``max_slippage`` of the best (lowest) offer."""
    if not asks:
        return 0.0
    ceiling = asks[0][0] + max_slippage + 1e-9
    return float(sum(q for p, q in asks if p <= ceiling))


def average_fill(asks: list[tuple[float, float]], n: float) -> float | None:
    """Average price paid to buy ``n`` contracts by walking up the book."""
    if not asks or n <= 0:
        return None
    left, paid = n, 0.0
    for price, qty in asks:
        take = min(left, qty)
        paid += take * price
        left -= take
        if left <= 1e-9:
            return paid / n
    return None  # the book doesn't have n contracts at any price


def limit_for(liq: Liquidity | None, buying: bool) -> LiquidityLimit:
    """The most contracts to propose in one direction."""
    if liq is None or not liq.known:
        return LiquidityLimit(None, "unknown", None, None)
    asks = liq.asks_buy if buying else liq.asks_sell
    depth = depth_within(asks, liq.max_slippage) if asks is not None else None
    oi_limit = (
        math.floor(liq.max_share_of_open_interest * liq.open_interest)
        if liq.open_interest is not None else None
    )
    limits = [x for x in (depth, oi_limit) if x is not None]
    if not limits:
        return LiquidityLimit(None, "unknown", depth, oi_limit)
    basis = (
        "order book and open interest" if depth is not None and oi_limit is not None
        else "order book" if depth is not None else "open interest"
    )
    return LiquidityLimit(float(math.floor(min(limits))), basis, depth, oi_limit)


# ------------------------------------------------------- live order books
_BOOK_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_BOOK_LOCK = threading.Lock()
#: Order books change fast but a hedge page doesn't need tick data.
BOOK_TTL_SECONDS = 30.0


def fetch_orderbook(ticker: str, client: Any | None = None) -> dict[str, Any] | None:
    """Kalshi's public order book for one market, cached briefly; None on failure."""
    now = time.monotonic()
    with _BOOK_LOCK:
        hit = _BOOK_CACHE.get(ticker)
    if hit and now - hit[0] < BOOK_TTL_SECONDS:
        return hit[1]
    from .kalshi_client import KalshiClient, KalshiError

    try:
        book = (client or KalshiClient())._get(f"/markets/{ticker}/orderbook", retries=1)
    except (KalshiError, Exception):  # network, rate limit, unknown ticker
        return None
    with _BOOK_LOCK:
        _BOOK_CACHE[ticker] = (now, book)
        if len(_BOOK_CACHE) > 500:
            _BOOK_CACHE.clear()
    return book


def liquidity_for_market(ticker: str, side: str | None, live: bool | None = None) -> Liquidity:
    """Everything known about a market's size: open interest from the
    catalog (live or the bundled snapshot) and, when live data is enabled,
    the current order book. Unknown pieces stay None."""
    from .kalshi_client import curated_catalog, live_enabled

    side = (side or "yes").lower()
    if side not in ("yes", "no"):
        side = "yes"
    oi = None
    try:
        for ind in curated_catalog(live=live)["industries"]:
            for series in ind["series"]:
                for m in series.get("markets", []):
                    if m.get("ticker") == ticker:
                        oi = float(m.get("open_interest") or 0.0)
    except Exception:
        oi = None
    asks_buy = asks_sell = None
    if live if live is not None else live_enabled():
        book = fetch_orderbook(ticker)
        if book is not None:
            asks_buy = asks_from_orderbook(book, side)
            asks_sell = asks_from_orderbook(book, "no" if side == "yes" else "yes")
    return Liquidity(open_interest=oi, asks_buy=asks_buy, asks_sell=asks_sell)
