"""Browse *every* open Kalshi market, not just the curated income hedges.

:mod:`hone.prediction.kalshi_client` serves a hand-picked catalog of ~40
series grouped by the income they hedge. This module covers the rest of the
exchange: tens of thousands of open events (elections, sports, economics,
weather, crypto, companies, ...).

That is too much to fetch per page view (on 2026-11-03 it was 16,000+
events, ~10 MB, ~2.5 minutes at the public API's rate limit), so it works in
two layers:

1. **An event index**, built in a background thread by walking
   ``GET /events?status=open`` page by page. Each event is trimmed to its
   ticker, title, subtitle and category. Searches run against this index on
   the server, so the browser only ever receives one page of results. The
   index is rebuilt every ``INDEX_TTL_SECONDS``; while the first build is
   running, searches see the events indexed so far (``complete: false``).
2. **Live markets for one event**, fetched when the user opens it
   (``GET /markets?event_ticker=...``) and cached for
   ``EVENT_TTL_SECONDS``.

With ``HONE_KALSHI_LIVE=0`` (tests, offline demos) both layers are served
from the bundled snapshot of the curated catalog instead, so the page still
works without a network.

EDIT HERE:
* ``INDEX_TTL_SECONDS`` / ``EVENT_TTL_SECONDS`` — how fresh things stay.
* ``INDEX_PAGE_PAUSE`` — pause between index pages; raise it if Kalshi
  starts answering 429 (too many requests).
* ``MAX_INDEX_PAGES`` — safety cap on the walk (200 events per page).
* ``_score`` — how search results are ranked.
"""

from __future__ import annotations

import re
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from .kalshi_client import (
    INDUSTRIES,
    KalshiClient,
    KalshiError,
    live_enabled,
    load_snapshot,
)

#: Rebuild the whole event index this often (30 minutes).
INDEX_TTL_SECONDS = 30 * 60
#: Re-fetch one event's markets after this long (1 minute).
EVENT_TTL_SECONDS = 60
#: Pause between index pages, so the walk stays under the rate limit.
INDEX_PAGE_PAUSE = 0.35
#: 200 events per page -> at most 100k events indexed.
MAX_INDEX_PAGES = 500
#: Publish the partial index every N pages during the first build.
PUBLISH_EVERY = 5
#: How many events' markets to keep cached.
EVENT_CACHE_SIZE = 256
#: Largest page of search results one request may ask for.
MAX_RESULTS = 100

#: Kalshi tickers are letters, digits, '-', '.' and '_'. Anything else is
#: rejected before it reaches Kalshi.
EVENT_TICKER_RE = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


# ---------------------------------------------------------------------------
# Curated series lookup: when a browsed event belongs to a series in the
# income-hedging catalog, the UI can say so (and reuse its basis/side).
# ---------------------------------------------------------------------------
def _curated_by_series() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for ind in INDUSTRIES:
        for s in ind["series"]:
            out[s["ticker"]] = {
                "industry": ind["key"],
                "industry_label": ind["label"],
                "series_title": s["title"],
                "basis": s["basis"],
                "bad_side": s["bad_side"],
            }
    return out


CURATED = _curated_by_series()


# ---------------------------------------------------------------------------
# Event records
# ---------------------------------------------------------------------------
def slim_event(raw: dict[str, Any]) -> dict[str, Any]:
    """One raw Kalshi event -> the few fields the browser needs.

    The ``_hay`` key is the lower-cased search text; it is stripped before
    anything is sent to the browser (see :func:`public_event`).
    """
    ev = {
        "event_ticker": str(raw.get("event_ticker") or ""),
        "series_ticker": str(raw.get("series_ticker") or ""),
        "title": str(raw.get("title") or ""),
        "sub_title": str(raw.get("sub_title") or ""),
        "category": str(raw.get("category") or "Other"),
    }
    ev["_hay"] = " ".join(
        (ev["title"], ev["sub_title"], ev["event_ticker"], ev["series_ticker"], ev["category"])
    ).lower()
    return ev


def public_event(ev: dict[str, Any]) -> dict[str, Any]:
    """An index record as sent to the browser (no internals, plus the
    curated-catalog link when there is one)."""
    out = {k: v for k, v in ev.items() if not k.startswith("_")}
    out["curated"] = CURATED.get(ev["series_ticker"])
    return out


def snapshot_events(snapshot: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """An offline index built from the bundled snapshot (curated series only).

    The snapshot stores markets, not events, so events are recovered by
    grouping markets on ``event_ticker`` and titled after their series.
    """
    snapshot = snapshot if snapshot is not None else load_snapshot()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ticker, block in snapshot.get("series", {}).items():
        cur = CURATED.get(ticker, {})
        for m in block.get("markets", []):
            et = m.get("event_ticker")
            if not et or et in seen:
                continue
            seen.add(et)
            out.append(slim_event({
                "event_ticker": et,
                "series_ticker": ticker,
                "title": cur.get("series_title") or ticker,
                "sub_title": et,
                "category": cur.get("industry_label") or "Curated",
            }))
    return out


# ---------------------------------------------------------------------------
# The live index (built in the background)
# ---------------------------------------------------------------------------
_INDEX: dict[str, Any] = {
    "events": [],        # list of slim_event records
    "as_of": None,       # when the last build finished (or the partial was taken)
    "complete": False,   # True once a full walk has finished
    "built_at": 0.0,     # time.time() of the last finished build
    "error": None,       # last build error, for diagnostics
}
_INDEX_LOCK = threading.Lock()
_BUILDING = threading.Event()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_index(
    client: KalshiClient | None = None,
    pause: float = INDEX_PAGE_PAUSE,
    max_pages: int = MAX_INDEX_PAGES,
) -> list[dict[str, Any]]:
    """Walk every page of open events and install the result as the index.

    During the *first* build (no complete index yet) the events gathered so
    far are published every ``PUBLISH_EVERY`` pages, so search works while
    the walk is still running. Later rebuilds swap in only when finished, so
    a refresh never shrinks what users can see.
    """
    client = client or KalshiClient()
    acc: list[dict[str, Any]] = []
    seen: set[str] = set()
    cursor: str | None = None
    for page in range(max_pages):
        events, cursor = client.events_page(status="open", limit=200, cursor=cursor)
        for raw in events:
            ev = slim_event(raw)
            if ev["event_ticker"] and ev["event_ticker"] not in seen:
                seen.add(ev["event_ticker"])
                acc.append(ev)
        if not cursor or not events:
            break
        if page % PUBLISH_EVERY == 0:
            with _INDEX_LOCK:
                if not _INDEX["complete"]:
                    _INDEX["events"] = list(acc)
                    _INDEX["as_of"] = _now_iso()
        if pause:
            time.sleep(pause)
    with _INDEX_LOCK:
        _INDEX.update(events=acc, as_of=_now_iso(), complete=True,
                      built_at=time.time(), error=None)
    return acc


def _build_in_background() -> None:
    try:
        build_index()
    except Exception as exc:  # network, rate limit, schema drift
        with _INDEX_LOCK:
            _INDEX["error"] = str(exc)[:300]
            # Try again on the next request rather than in a tight loop.
            _INDEX["built_at"] = time.time() - INDEX_TTL_SECONDS + 60
    finally:
        _BUILDING.clear()


def ensure_index() -> None:
    """Start a background (re)build if the index is missing or stale."""
    with _INDEX_LOCK:
        stale = time.time() - _INDEX["built_at"] > INDEX_TTL_SECONDS
    if stale and not _BUILDING.is_set():
        _BUILDING.set()
        threading.Thread(target=_build_in_background, daemon=True).start()


def current_index(live: bool | None = None) -> dict[str, Any]:
    """The index to search right now, and where it came from.

    ``source`` is ``"live"`` (complete walk), ``"live-partial"`` (first walk
    still running) or ``"snapshot"`` (offline, or nothing indexed yet).
    """
    if live is None:
        live = live_enabled()
    if live:
        ensure_index()
        with _INDEX_LOCK:
            events = _INDEX["events"]
            complete = _INDEX["complete"]
            as_of = _INDEX["as_of"]
        if events:
            return {"events": events, "source": "live" if complete else "live-partial",
                    "complete": complete, "as_of": as_of, "building": _BUILDING.is_set()}
    snap = load_snapshot()
    return {"events": snapshot_events(snap), "source": "snapshot", "complete": not live,
            "as_of": snap.get("as_of"), "building": bool(live and _BUILDING.is_set())}


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def _score(ev: dict[str, Any], q: str, tokens: list[str]) -> int | None:
    """Rank one event against a query; ``None`` means "not a match".

    Lower is better: 0 exact ticker, 1 ticker prefix, 2 title starts with
    the query, 3 a word in the title starts with it, 4 anything else that
    contains every word of the query.
    """
    if not all(t in ev["_hay"] for t in tokens):
        return None
    if not q:
        return 4
    et, st = ev["event_ticker"].lower(), ev["series_ticker"].lower()
    if q in (et, st):
        return 0
    if et.startswith(q) or st.startswith(q):
        return 1
    title = ev["title"].lower()
    if title.startswith(q):
        return 2
    if re.search(r"\b" + re.escape(tokens[0]), title):
        return 3
    return 4


def search_events(q: str = "", category: str | None = None, offset: int = 0,
                  limit: int = 30, live: bool | None = None) -> dict[str, Any]:
    """One page of events matching ``q`` (every word must appear), optionally
    within one ``category``, plus the per-category counts for ``q``."""
    idx = current_index(live)
    q = (q or "").strip().lower()
    tokens = q.split()
    limit = max(1, min(int(limit), MAX_RESULTS))
    offset = max(0, int(offset))

    scored: list[tuple[int, int, dict[str, Any]]] = []
    counts: dict[str, int] = {}
    for i, ev in enumerate(idx["events"]):
        sc = _score(ev, q, tokens)
        if sc is None:
            continue
        # Category counts ignore the category filter, so the chips always
        # show how many matches each category would give.
        counts[ev["category"]] = counts.get(ev["category"], 0) + 1
        if category and ev["category"] != category:
            continue
        scored.append((sc, i, ev))
    scored.sort(key=lambda t: (t[0], t[1]))  # rank, then Kalshi's own order

    page = [public_event(ev) for _, _, ev in scored[offset:offset + limit]]
    return {
        "source": idx["source"],
        "complete": idx["complete"],
        "building": idx["building"],
        "as_of": idx["as_of"],
        "live_enabled": live_enabled() if live is None else live,
        "indexed": len(idx["events"]),
        "total": len(scored),
        "offset": offset,
        "limit": limit,
        "categories": [{"name": k, "count": v}
                       for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))],
        "events": page,
    }


# ---------------------------------------------------------------------------
# One event's markets
# ---------------------------------------------------------------------------
_EVENT_CACHE: "OrderedDict[str, tuple[float, list[dict[str, Any]]]]" = OrderedDict()
_EVENT_LOCK = threading.Lock()


def _find_event(event_ticker: str, live: bool) -> dict[str, Any] | None:
    for ev in current_index(live)["events"]:
        if ev["event_ticker"] == event_ticker:
            return public_event(ev)
    return None


def _snapshot_markets(event_ticker: str) -> list[dict[str, Any]]:
    snap = load_snapshot()
    return [m for block in snap.get("series", {}).values() for m in block.get("markets", [])
            if m.get("event_ticker") == event_ticker]


def event_detail(event_ticker: str, live: bool | None = None,
                 client: KalshiClient | None = None) -> dict[str, Any]:
    """Every open market in one event, most-traded first.

    Raises ``ValueError`` for a malformed ticker and ``KalshiError`` when
    the event can't be fetched and isn't in the snapshot either.
    """
    if not EVENT_TICKER_RE.match(event_ticker or ""):
        raise ValueError("Not a Kalshi event ticker.")
    if live is None:
        live = live_enabled()

    markets: list[dict[str, Any]] | None = None
    source = "snapshot"
    as_of: str | None = None
    if live:
        with _EVENT_LOCK:
            hit = _EVENT_CACHE.get(event_ticker)
        if hit and time.time() - hit[0] < EVENT_TTL_SECONDS:
            markets, source = hit[1], "live"
            as_of = datetime.fromtimestamp(hit[0], timezone.utc).isoformat(timespec="seconds")
        else:
            try:
                markets = (client or KalshiClient()).event_markets(event_ticker)
                source, as_of = "live", _now_iso()
                with _EVENT_LOCK:
                    _EVENT_CACHE[event_ticker] = (time.time(), markets)
                    _EVENT_CACHE.move_to_end(event_ticker)
                    while len(_EVENT_CACHE) > EVENT_CACHE_SIZE:
                        _EVENT_CACHE.popitem(last=False)
            except KalshiError:
                markets = None  # fall through to the snapshot
    if markets is None:
        markets = _snapshot_markets(event_ticker)
        as_of = load_snapshot().get("as_of")
        if not markets and live:
            raise KalshiError("Could not load this event from Kalshi. Try again shortly.")

    markets = sorted(markets, key=lambda m: -(m.get("volume") or 0.0))
    event = _find_event(event_ticker, live) or {
        "event_ticker": event_ticker, "series_ticker": "", "title": event_ticker,
        "sub_title": "", "category": "", "curated": None,
    }
    return {"event": event, "markets": markets, "source": source, "as_of": as_of}


def reset_state() -> None:
    """Forget the index and event cache (used by tests)."""
    with _INDEX_LOCK:
        _INDEX.update(events=[], as_of=None, complete=False, built_at=0.0, error=None)
    with _EVENT_LOCK:
        _EVENT_CACHE.clear()
