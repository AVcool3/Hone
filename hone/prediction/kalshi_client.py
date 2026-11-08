"""Kalshi public market data, and the curated catalog the page shows.

Kalshi exposes its market list without authentication at
``https://api.elections.kalshi.com/trade-api/v2``.  Hone only ever reads
from it — no keys, no orders — and only the handful of series that a
person with cyclical income would plausibly hedge with.  Those series are
listed in :data:`INDUSTRIES` below, grouped by who carries the exposure,
with a note on how direct a hedge each one is (the *basis*: a market on
Denver snowfall is a weak proxy for an Aspen paycheck).

Two sources, one shape
----------------------
``curated_catalog()`` returns the same structure whether the data came
from the live API or from the bundled ``kalshi_snapshot.json``:

* live — fetched per series, cached in-process for ten minutes, refreshed
  in a background thread so a page load never waits on 40 HTTP calls;
* snapshot — the file produced by ``research/prediction/fetch_kalshi_snapshot.py``,
  used before the first live fetch completes, when the network is off, or
  when ``HONE_KALSHI_LIVE=0``.

Every market is normalized to a flat dict of floats (``yes_bid``,
``yes_ask``, ``no_ask``, ``last``, ``volume``, ``open_interest``,
``implied``, ``spread``) plus its title, the label of the YES side, close
time and the resolution rule, so the frontend never has to know Kalshi's
field names.

To add a market: append its series ticker to the right industry below and
re-run the snapshot script.  Series tickers are stable; individual market
tickers roll with each month or season.
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
SNAPSHOT_PATH = Path(__file__).parent / "kalshi_snapshot.json"

#: How long a live fetch is trusted before a refresh is started.
CACHE_TTL_SECONDS = 600
#: Per-request timeout for the public API.
REQUEST_TIMEOUT = 8.0
#: Pause between series fetches: the public API rate-limits bursts.
FETCH_PAUSE = 0.15
#: Markets kept per series (highest volume first) — the page shows a ladder,
#: not the whole book.
MARKETS_PER_SERIES = 12


class KalshiError(RuntimeError):
    """Raised when the Kalshi API returns an error or unexpected payload."""


# ---------------------------------------------------------------------------
# The catalog.  `basis` is a plain-language verdict on how closely the
# market tracks the income it is listed under:  "direct" (same thing),
# "close" (same cause, different measurement), "proxy" (correlated, with a
# lot left over).  `bad_side` says which side a hedger buys.
# ---------------------------------------------------------------------------
INDUSTRIES: list[dict[str, Any]] = [
    {
        "key": "snow",
        "label": "Snow & the ski season",
        "who": (
            "Ski instructors, lift and patrol staff, mountain-town servers, "
            "guides, seasonal retail — anyone whose winter income rises and "
            "falls with how much it snows and when the lifts open."
        ),
        "series": [
            {"ticker": "KXASPSNOWM", "title": "Aspen monthly snowfall",
             "basis": "direct", "bad_side": "NO on 'above X inches'",
             "note": "The direct hedge for an Aspen season. Monthly contracts list as the season approaches."},
            {"ticker": "KXMTN", "title": "Vail Resorts skier visits (quarterly)",
             "basis": "close", "bad_side": "NO on 'above X visits'",
             "note": "Vail, Beaver Creek, Breckenridge and Keystone share Aspen's weather and visitors; a thin Colorado season shows up here."},
            {"ticker": "KXDENSNOWM", "title": "Denver monthly snowfall",
             "basis": "proxy", "bad_side": "NO on 'above X inches'",
             "note": "Front Range snow is a different climate from the Elk Mountains — correlated, but loosely."},
            {"ticker": "KXKEYSTONEOPEN", "title": "Keystone opening date",
             "basis": "close", "bad_side": "NO on 'opens before date'",
             "note": "A late opening is lost weeks of work across the Colorado resorts."},
            {"ticker": "KXBEAVEROPEN", "title": "Beaver Creek opening date",
             "basis": "close", "bad_side": "NO on 'opens before date'", "note": ""},
            {"ticker": "KXNORTHSTARSNOW", "title": "Northstar (Tahoe) season snowfall",
             "basis": "direct", "bad_side": "NO on 'above X inches'",
             "note": "Direct for Tahoe workers. Note the spreads: thin books make the hedge expensive."},
            {"ticker": "KXNORTHSTAROPEN", "title": "Northstar opening date",
             "basis": "direct", "bad_side": "NO on 'opens before date'", "note": ""},
            {"ticker": "KXHEAVENLYOPEN", "title": "Heavenly opening date",
             "basis": "direct", "bad_side": "NO on 'opens before date'", "note": ""},
            {"ticker": "KXSIERRAOPEN", "title": "Sierra-at-Tahoe opening date",
             "basis": "direct", "bad_side": "NO on 'opens before date'", "note": ""},
            {"ticker": "KXSTOWEOPEN", "title": "Stowe opening date",
             "basis": "direct", "bad_side": "NO on 'opens before date'", "note": "For the Vermont season."},
            {"ticker": "KXNHASKIVISITS", "title": "New Hampshire skier visits (season)",
             "basis": "direct", "bad_side": "NO on 'above X visits'",
             "note": "A whole-season visit count — the single best match for a season's tips."},
            {"ticker": "KXUTSKIVISITS", "title": "Utah skier visits (season)",
             "basis": "direct", "bad_side": "NO on 'above X visits'", "note": ""},
        ],
    },
    {
        "key": "ads",
        "label": "Advertising & media",
        "who": (
            "Freelance creatives, production crews, agency contractors and "
            "commission-based ad sales. Ad budgets are the first thing cut "
            "in a slowdown and the last thing restored."
        ),
        "series": [
            {"ticker": "KXSTREAMINGADS", "title": "Film & TV streaming ad spend (monthly index)",
             "basis": "close", "bad_side": "NO on 'above X'",
             "note": "A monthly spend index for the category; a hedge for anyone paid out of streaming marketing budgets."},
            {"ticker": "KXCASINOADS", "title": "Casino ad spend (monthly index)",
             "basis": "close", "bad_side": "NO on 'above X'", "note": ""},
            {"ticker": "KXFOOTWEARADS", "title": "Footwear retail ad spend (monthly index)",
             "basis": "close", "bad_side": "NO on 'above X'", "note": ""},
            {"ticker": "KXVIDEOGAMESADS", "title": "Video games ad spend (monthly index)",
             "basis": "close", "bad_side": "NO on 'above X'", "note": ""},
            {"ticker": "KXTEENCLOTHADS", "title": "Teen clothing ad spend (monthly index)",
             "basis": "close", "bad_side": "NO on 'above X'", "note": ""},
            {"ticker": "KXSPORTSBOOKADS", "title": "Online sportsbook ad spend",
             "basis": "close", "bad_side": "NO on 'above X'", "note": ""},
            {"ticker": "KXAMUSEMENTADS", "title": "Amusement parks ad spend",
             "basis": "close", "bad_side": "NO on 'above X'", "note": ""},
            {"ticker": "KXSUPERBOWLAD", "title": "Which brands buy a Super Bowl ad",
             "basis": "proxy", "bad_side": "NO on 'brand runs an ad'",
             "note": "Per-advertiser. Useful only if your income depends on one specific account."},
        ],
    },
    {
        "key": "labor",
        "label": "Hiring, layoffs & wages",
        "who": (
            "Recruiters, staffing contractors, people between contracts, "
            "retail and warehouse seasonal staff. If your next job depends "
            "on companies hiring, the jobs report is your weather."
        ),
        "series": [
            {"ticker": "KXU3", "basis_default": 0.02, "title": "US unemployment rate (monthly)",
             "basis": "proxy", "bad_side": "YES on 'above X%'",
             "note": "The broadest labor-market hedge, and one of Kalshi's most liquid. It barely tracks one person's job (measured basis 0-0.02: in months people were laid off it paid about as often as in any month), but it tracks a state's job market at ~0.34 — useful if your income follows the local economy (findings/08)."},
            {"ticker": "KXPAYROLLS", "basis_default": 0.02, "title": "Nonfarm payrolls added (monthly)",
             "basis": "proxy", "bad_side": "NO on 'above X jobs'", "note": ""},
            {"ticker": "KXJOBLESSCLAIMS", "basis_default": 0.02, "title": "Weekly initial jobless claims",
             "basis": "proxy", "bad_side": "YES on 'at least X claims'", "note": "Weekly, so it hedges a short horizon."},
            {"ticker": "KXCONTCLAIMS", "basis_default": 0.02, "title": "Continuing jobless claims (weekly)",
             "basis": "proxy", "bad_side": "YES on 'above X'", "note": ""},
            {"ticker": "KXU3MAX", "basis_default": 0.02, "title": "Peak unemployment before year-end",
             "basis": "proxy", "bad_side": "YES on 'above X%'",
             "note": "A tail hedge: pays if the labor market cracks at any point in the year."},
            {"ticker": "KXHOLIDAYRETAIL", "title": "Holiday-season retail jobs added",
             "basis": "direct", "bad_side": "NO on 'above X jobs'",
             "note": "Direct for seasonal retail and warehouse workers."},
            {"ticker": "KXTECHLAYOFF", "basis_default": 0.02, "title": "Tech layoff rate (monthly)",
             "basis": "close", "bad_side": "YES on 'above X'", "note": ""},
            {"ticker": "KXWAGESBEAT", "title": "Real hourly earnings growth positive",
             "basis": "proxy", "bad_side": "NO", "note": ""},
        ],
    },
    {
        "key": "housing",
        "label": "Housing & interest rates",
        "who": (
            "Real-estate agents, mortgage brokers, builders, movers, home "
            "inspectors. Transaction volume — and therefore commission — "
            "moves with the mortgage rate."
        ),
        "series": [
            {"ticker": "KX30YMORTW", "title": "30-year mortgage rate (weekly)",
             "basis": "close", "bad_side": "YES on 'above X%'",
             "note": "Higher rates mean fewer closings; the YES side pays when they rise."},
            {"ticker": "KXFED", "title": "Fed funds rate after each meeting",
             "basis": "proxy", "bad_side": "YES on 'above X%'", "note": ""},
            {"ticker": "KXHOUSESTART", "title": "US housing starts rise (monthly)",
             "basis": "direct", "bad_side": "NO", "note": "Direct for construction trades."},
            {"ticker": "KXEHSALES", "title": "Existing home sales",
             "basis": "direct", "bad_side": "NO on 'above X'", "note": "Direct for agents: this is the commission pool."},
            {"ticker": "KXHPI", "title": "House price index (monthly)",
             "basis": "proxy", "bad_side": "NO on 'rises'", "note": ""},
            {"ticker": "KXCOBUILDPERMITS", "title": "Colorado housing permits (annual)",
             "basis": "direct", "bad_side": "NO on 'above X'", "note": "Regional; for Colorado builders."},
        ],
    },
    {
        "key": "travel",
        "label": "Travel & hospitality",
        "who": (
            "Hotel and resort staff, tour guides, drivers, cruise crew, "
            "theme-park workers — tipped and hourly income that moves with "
            "visitor counts."
        ),
        "series": [
            {"ticker": "KXORLHOTELDEMAND", "title": "Orlando hotel room nights (annual)",
             "basis": "direct", "bad_side": "NO on 'above X million'",
             "note": "Direct for the Orlando service economy."},
            {"ticker": "KXFLVISITORCOUNT", "title": "Visitors to Florida (annual)",
             "basis": "close", "bad_side": "NO on 'above X million'", "note": ""},
            {"ticker": "KXCCL", "title": "Carnival capacity / KPIs (quarterly)",
             "basis": "close", "bad_side": "NO on 'above X'", "note": "For cruise crew and port workers."},
            {"ticker": "KXWH", "title": "Wyndham Hotels KPIs (quarterly)",
             "basis": "proxy", "bad_side": "NO on 'above X'", "note": ""},
            {"ticker": "KXLUV", "title": "Southwest Airlines seats & fares (quarterly)",
             "basis": "proxy", "bad_side": "NO on 'above X'", "note": ""},
        ],
    },
    {
        "key": "prices",
        "label": "Fuel & the cost of living",
        "who": (
            "Rideshare and delivery drivers, truckers, anyone on a fixed "
            "income. These are expense hedges: they pay when your costs go up."
        ),
        "series": [
            {"ticker": "KXAAAGASM", "title": "US average gas price (monthly)",
             "basis": "direct", "bad_side": "YES on 'above $X'",
             "note": "For a driver the bad outcome is a *high* price, so the YES side is the hedge."},
            {"ticker": "KXCPIYOY", "title": "CPI inflation, year over year",
             "basis": "proxy", "bad_side": "YES on 'above X%'", "note": ""},
        ],
    },
]


def _f(x: Any) -> float | None:
    """Kalshi sends numbers as strings; empty or missing becomes None."""
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def normalize_market(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten one Kalshi market into the shape the page and the sizer use."""
    from .contracts import implied_probability

    yes_bid = _f(raw.get("yes_bid_dollars"))
    yes_ask = _f(raw.get("yes_ask_dollars"))
    no_bid = _f(raw.get("no_bid_dollars"))
    no_ask = _f(raw.get("no_ask_dollars"))
    last = _f(raw.get("last_price_dollars"))
    implied = implied_probability(yes_bid, yes_ask, last)
    spread = None
    if yes_bid is not None and yes_ask is not None and yes_ask < 1.0 and yes_bid > 0.0:
        spread = yes_ask - yes_bid
    return {
        "ticker": raw.get("ticker", ""),
        "event_ticker": raw.get("event_ticker", ""),
        "title": raw.get("title", ""),
        "label": raw.get("yes_sub_title") or raw.get("subtitle") or "",
        "status": raw.get("status", ""),
        "close_time": raw.get("close_time", ""),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "last": last,
        "implied": implied,
        "spread": spread,
        "volume": _f(raw.get("volume_fp")) or 0.0,
        "open_interest": _f(raw.get("open_interest_fp")) or 0.0,
        "strike": _f(raw.get("floor_strike")),
        "strike_type": raw.get("strike_type", ""),
        "rules": raw.get("rules_primary", ""),
    }


class KalshiClient:
    """Read-only client for Kalshi's public market endpoints.

    ``session`` accepts anything with a ``get`` method compatible with
    :class:`requests.Session`; tests inject canned responses with it.
    """

    def __init__(self, base_url: str = KALSHI_BASE_URL, session: Any | None = None,
                 timeout: float = REQUEST_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get(self, path: str, retries: int = 3, **params: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        res = None
        for attempt in range(retries + 1):
            try:
                res = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:  # pragma: no cover - network
                raise KalshiError(f"Kalshi request failed: {exc}") from exc
            # The public API rate-limits bursts with a 429; back off and retry
            # rather than dropping the series from the catalog.
            if res.status_code == 429 and attempt < retries:
                time.sleep(0.8 * (attempt + 1))
                continue
            break
        assert res is not None
        if res.status_code != 200:
            raise KalshiError(f"Kalshi {res.status_code} on {path}: {res.text[:200]}")
        try:
            return res.json()
        except ValueError as exc:
            raise KalshiError("Kalshi returned non-JSON") from exc

    def series(self, ticker: str) -> dict[str, Any]:
        data = self._get(f"/series/{ticker}")
        return data.get("series", data)

    def markets(self, series_ticker: str, status: str | None = "open",
                limit: int = 100) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"series_ticker": series_ticker, "limit": limit}
        if status:
            params["status"] = status
        data = self._get("/markets", **params)
        return [normalize_market(m) for m in data.get("markets", [])]


# ----------------------------------------------------------- the catalog
def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    """The bundled snapshot, keyed by series ticker."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _trim(markets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the most-traded markets, then present them in strike order."""
    top = sorted(markets, key=lambda m: -(m.get("volume") or 0.0))[:MARKETS_PER_SERIES]
    return sorted(top, key=lambda m: (m.get("strike") is None, m.get("strike") or 0.0, m["ticker"]))


def fetch_live(client: KalshiClient | None = None, pause: float = FETCH_PAUSE) -> dict[str, Any]:
    """Fetch every curated series from the live API.  Raises on total failure."""
    client = client or KalshiClient()
    series_out: dict[str, Any] = {}
    tickers = [s["ticker"] for ind in INDUSTRIES for s in ind["series"]]
    # Two passes: anything that failed the first time (usually a 429 that
    # outlasted the per-request retries) gets one more chance after a pause.
    failed: list[str] = []
    for attempt in range(2):
        todo = tickers if attempt == 0 else failed
        failed = []
        for ticker in todo:
            try:
                mk = client.markets(ticker, status="open")
                series_out[ticker] = {"ticker": ticker, "markets": _trim(mk)}
            except KalshiError:
                failed.append(ticker)
            if pause:
                time.sleep(pause)
        if not failed:
            break
        time.sleep(max(pause * 4, 1.0))
    failures = len(failed)
    if not series_out:
        raise KalshiError("no series could be fetched")
    return {
        "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "live" if failures == 0 else "live-partial",
        "series": series_out,
    }


def assemble(data: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge a fetched (or snapshot) dataset into the industry structure."""
    series = data.get("series", {})
    fb_series = (fallback or {}).get("series", {})
    out = []
    for ind in INDUSTRIES:
        rows = []
        for s in ind["series"]:
            got = series.get(s["ticker"]) or fb_series.get(s["ticker"]) or {}
            rows.append({**s, "markets": got.get("markets", []),
                         "open_count": len(got.get("markets", []))})
        out.append({"key": ind["key"], "label": ind["label"], "who": ind["who"], "series": rows})
    return {"as_of": data.get("as_of"), "source": data.get("source", "snapshot"),
            "live_enabled": live_enabled(), "industries": out}


_CACHE: dict[str, Any] = {"data": None, "fetched_at": 0.0}
_LOCK = threading.Lock()
_REFRESHING = threading.Event()


def _refresh_in_background() -> None:
    try:
        live = fetch_live()
        with _LOCK:
            _CACHE["data"] = live
            _CACHE["fetched_at"] = time.time()
    except Exception:  # network, rate limit, schema drift — keep serving the snapshot
        pass
    finally:
        _REFRESHING.clear()


def live_enabled() -> bool:
    return os.environ.get("HONE_KALSHI_LIVE", "1").lower() not in ("0", "false", "no", "")


def curated_catalog(live: bool | None = None) -> dict[str, Any]:
    """The catalog for the page: live if we have it, snapshot otherwise.

    Never blocks on the network: the first call returns the snapshot and
    starts a background refresh; later calls return the live data until it
    is older than ``CACHE_TTL_SECONDS``, when another refresh starts.
    """
    snapshot = load_snapshot()
    if live is None:
        live = live_enabled()
    if not live:
        return assemble(snapshot)
    with _LOCK:
        cached = _CACHE["data"]
        stale = time.time() - _CACHE["fetched_at"] > CACHE_TTL_SECONDS
    if stale and not _REFRESHING.is_set():
        _REFRESHING.set()
        threading.Thread(target=_refresh_in_background, daemon=True).start()
    if cached is not None:
        return assemble(cached, fallback=snapshot)
    return assemble(snapshot)
