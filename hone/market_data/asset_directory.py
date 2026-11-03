"""The full list of symbols a user can pick, from Alpaca, cached.

The asset picker in the web app used to suggest a dozen hand-typed tickers.
This module serves *every* active asset Alpaca lists instead:

* stocks: ``GET /v2/assets?asset_class=us_equity`` (~11k US stocks + ETFs)
* crypto: ``GET /v2/assets?asset_class=crypto``   (the pairs Alpaca trades)

The list is reference data (the same for every account) and changes a few
times a day at most, so it is fetched once and cached in memory for
``CACHE_TTL_SECONDS``. Every visitor then shares that one copy.

Each asset is trimmed to ``(symbol, name, exchange)`` — the three things the
picker shows — so the payload stays small enough for a phone.

EDIT HERE:
* ``CACHE_TTL_SECONDS`` — how long a fetched list is reused.
* ``EXCLUDED_EXCHANGES`` — exchanges left out of the picker. OTC symbols are
  excluded by default because the free IEX market-data feed has no price
  history for them, so a thesis on one could never be priced.
* ``keep_asset`` — any other filtering rule.
"""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

#: Reuse a fetched asset list for this long (12 hours).
CACHE_TTL_SECONDS = 12 * 60 * 60

#: Exchanges whose symbols are hidden from the picker (see module docstring).
EXCLUDED_EXCHANGES = frozenset({"OTC"})

#: Hone's product names -> Alpaca's ``asset_class`` values.
ALPACA_CLASS = {"stocks": "us_equity", "crypto": "crypto"}

# One cache entry per Alpaca asset class:
#   {"us_equity": {"assets": [...], "as_of": "...", "fetched_at": 1700000000.0}}
_CACHE: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def keep_asset(raw: dict[str, Any]) -> bool:
    """Should this Alpaca asset appear in the picker?

    Only assets you could actually trade, on an exchange with free price
    history. Change this to widen or narrow what the picker offers.
    """
    if raw.get("status", "active") != "active":
        return False
    if raw.get("tradable") is False:
        return False
    if str(raw.get("exchange", "")).upper() in EXCLUDED_EXCHANGES:
        return False
    return bool(raw.get("symbol"))


#: Share-class boilerplate at the end of Alpaca's legal names. Removed so
#: the thesis sentence reads "I think Costco Wholesale Corporation will..."
#: rather than "...Corporation Common Stock will...". Add patterns here.
_NAME_SUFFIX = re.compile(
    r"\s+(Class [A-Z]\s+)?(Common Stock|Ordinary Shares|Common Shares|"
    r"American Depositary Shares.*|Depositary Shares.*)$",
    re.IGNORECASE,
)


def tidy_name(name: str) -> str:
    """``"Apple Inc. Common Stock"`` -> ``"Apple Inc."`` (ETF names untouched)."""
    return _NAME_SUFFIX.sub("", name.strip()) or name.strip()


def trim_asset(raw: dict[str, Any]) -> list[str]:
    """One Alpaca asset -> ``[symbol, name, exchange]`` (compact on the wire)."""
    return [
        str(raw.get("symbol", "")).upper(),
        tidy_name(str(raw.get("name") or "")),
        str(raw.get("exchange") or "").upper(),
    ]


def build_directory(raw_assets: list[dict[str, Any]]) -> list[list[str]]:
    """Filter, trim, de-duplicate and sort a raw ``/v2/assets`` response."""
    seen: set[str] = set()
    out: list[list[str]] = []
    for raw in raw_assets:
        if not keep_asset(raw):
            continue
        row = trim_asset(raw)
        if row[0] in seen:
            continue
        seen.add(row[0])
        out.append(row)
    # Alphabetical by symbol: the frontend ranks matches itself, so the
    # order here only matters for a blank search.
    out.sort(key=lambda r: r[0])
    return out


def cached_directory(
    alpaca_class: str,
    make_client: Callable[[], Any],
    now: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """The asset list for one Alpaca asset class, fetched at most every
    ``CACHE_TTL_SECONDS``.

    ``make_client`` is only called on a cache miss, so a visitor whose
    request is served from the cache needs no Alpaca keys at all. It may
    raise (missing keys, Alpaca down); the error propagates to the caller.

    Returns ``{"assets": [[symbol, name, exchange], ...], "as_of": iso}``.
    """
    with _LOCK:
        hit = _CACHE.get(alpaca_class)
        if hit and now() - hit["fetched_at"] < CACHE_TTL_SECONDS:
            return hit
    # Fetch outside the lock: it is a slow network call, and two visitors
    # fetching at once is harmless (the second write wins).
    client = make_client()
    assets = build_directory(client.list_assets(alpaca_class))
    entry = {
        "assets": assets,
        "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fetched_at": now(),
    }
    with _LOCK:
        _CACHE[alpaca_class] = entry
    return entry


def clear_cache() -> None:
    """Forget every cached list (used by tests)."""
    with _LOCK:
        _CACHE.clear()
