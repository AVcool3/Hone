"""Bureau of Labor Statistics data: job-loss odds by industry, and how
closely a place's unemployment and prices move with the national numbers.

Why this module exists
----------------------
Kalshi lists contracts on NATIONAL numbers: the US unemployment rate (U3)
and the US consumer price index (CPI). A person's income risk is LOCAL and
PERSONAL: their own job, in their own industry, in their own state, and the
prices where they live. The hedge engine (``hone/prediction/hedge.py``)
needs two inputs that bridge that gap:

``loss_prob``
    The person's own chance of the bad outcome over the contract's horizon
    (e.g. "I lose my job this year"), when it differs from the contract's
    event ("unemployment rises").
``basis_correlation``
    How closely the contract's payoff tracks the person's loss, 0 to 1.

Until now the page used generic guesses for both. This module replaces
them with numbers measured from public BLS data:

1. **Job-loss probability by industry** from JOLTS (Job Openings and Labor
   Turnover Survey) layoffs-and-discharges rates.
   See :func:`annual_prob_from_monthly` and :func:`layoff_summary`.
2. **Basis between one person's job loss and a national-unemployment
   contract**, by industry: how much more often the contract pays in the
   months layoffs happen. See :func:`job_loss_basis`.
3. **Basis between a state's (or metro's) unemployment and the national
   rate** (LAUS, Local Area Unemployment Statistics): for hedging a state's
   labor market, e.g. a business whose sales follow local employment.
   See :func:`change_correlation`.
4. **Basis between regional and national CPI**: for a retiree whose costs
   follow prices where they live. Same function.

The measured values are frozen into the tables at the bottom of this file
(``JOB_LOSS``, ``STATE_UNEMPLOYMENT_BASIS``, ``METRO_UNEMPLOYMENT_BASIS``,
``CPI_BASIS``) so the app never needs the network. They were produced by
``research/prediction/labor_study.py``; the method and caveats are in
``research/prediction/findings/08_labor.md``. Re-run that script to refresh
them and paste its printed tables over the ones here.

The lookups most callers want are :func:`job_loss_prob`,
:func:`basis_to_national` and :func:`hedge_defaults`.

Talking to BLS
--------------
The public API needs no key (version 1), but it is stingy: about 25
queries a day, at most 25 series and 10 years per query. A free key
(version 2, https://data.bls.gov/registrationEngine/) raises that to 500
queries, 50 series and 20 years. If the environment variable
``BLS_API_KEY`` is set, :func:`fetch_series` uses v2 automatically.

Because queries are scarce, :func:`fetch_series` packs as many series into
each query as allowed and caches every response twice: in memory for the
life of the process, and (when a ``cache_dir`` is given) on disk, so that a
second run of the study needs no network at all.

If the quota is already used up (it is counted per IP address, so a shared
network can exhaust it for you), :func:`fetch_series` fills the gaps from
FRED, which republishes the same BLS series without a quota; see
:data:`FRED_MIRROR`.

``session`` arguments accept anything with a requests-style ``post``
(``session.post(url, json=..., timeout=...)`` returning an object with
``status_code``, ``raise_for_status()`` and ``json()``). That is how the
tests run offline, the same pattern as ``kalshi_client`` and ``climate``.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# API settings
# ---------------------------------------------------------------------------
API_V1_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
API_V2_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
#: Environment variable holding an optional (free) v2 registration key.
API_KEY_ENV = "BLS_API_KEY"

#: Per-query limits. v1 is keyless; v2 needs a key. Exceeding the series or
#: year limit doesn't error — BLS silently truncates — so we split ourselves.
LIMITS = {
    "v1": {"series": 25, "years": 10},
    "v2": {"series": 50, "years": 20},
}

TIMEOUT = 30
#: Extra attempts after a network error, an HTTP 5xx or a 429.
RETRIES = 3
#: A cached window that reaches into the current year is still filling in
#: (new months are published every few weeks); refetch it after this long.
#: Windows that ended in a past year never change and are never refetched.
OPEN_WINDOW_MAX_AGE_DAYS = 14


class BLSError(RuntimeError):
    """A BLS request failed (network, bad payload, unknown series)."""


class BLSLimitError(BLSError):
    """BLS refused the query because the daily quota is used up.

    Not retried: the quota resets at midnight Eastern time. Callers should
    stop and use whatever is cached (the study script does exactly that).
    """


# ---------------------------------------------------------------------------
# Series ID builders. Formats checked against the BLS series-ID docs
# (https://www.bls.gov/help/hlpforma.htm) and the code lists under
# https://download.bls.gov/pub/time.series/{la,jt,cu}/.
# ---------------------------------------------------------------------------

#: State FIPS codes (two digits), the key LAUS uses for states.
STATE_FIPS: dict[str, str] = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15",
    "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
    "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56",
}

STATE_NAMES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

#: Census regions, which are also the four CPI regions.
STATE_REGION: dict[str, str] = {}
for _region, _states in {
    "northeast": "CT ME MA NH RI VT NJ NY PA",
    "midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
    "south": "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX",
    "west": "AZ CO ID MT NV NM UT WY AK CA HI OR WA",
}.items():
    for _s in _states.split():
        STATE_REGION[_s] = _region

#: Census divisions (nine), which CPI also publishes (from Dec 2017 only).
STATE_DIVISION: dict[str, str] = {}
for _div, _states in {
    "new_england": "CT ME MA NH RI VT",
    "middle_atlantic": "NJ NY PA",
    "east_north_central": "IL IN MI OH WI",
    "west_north_central": "IA KS MN MO NE ND SD",
    "south_atlantic": "DE DC FL GA MD NC SC VA WV",
    "east_south_central": "AL KY MS TN",
    "west_south_central": "AR LA OK TX",
    "mountain": "AZ CO ID MT NV NM UT WY",
    "pacific": "AK CA HI OR WA",
}.items():
    for _s in _states.split():
        STATE_DIVISION[_s] = _div


def laus_state_id(state: str, seasonally_adjusted: bool = True) -> str:
    """LAUS unemployment-rate series for a state, e.g. ``LASST060000000000003``.

    Layout: ``LA`` (survey) + ``S``/``U`` (seasonally adjusted or not) +
    ``ST`` + 2-digit FIPS + 11 zeros (the area code is 15 characters) +
    ``03`` (measure 03 = unemployment rate; 04 = unemployed count, ...).
    """
    fips = STATE_FIPS[state.upper()]
    return f"LA{'S' if seasonally_adjusted else 'U'}ST{fips}00000000000" + "03"


def laus_metro_id(state_fips: str, cbsa: str) -> str:
    """LAUS unemployment rate for a metro area, not seasonally adjusted.

    ``LAU`` + ``MT`` + 2-digit FIPS of the metro's principal state + 5-digit
    CBSA code + 6 zeros + ``03``, e.g. Los Angeles = ``LAUMT063108000000003``.
    BLS seasonally adjusts only some metros, so we take the unadjusted
    series and compare 12-month changes, which cancel seasonality.
    """
    return f"LAUMT{state_fips}{cbsa}000000" + "03"


def jolts_id(industry_code: str, element: str = "LD", rate: bool = True,
             seasonally_adjusted: bool = True, state: str = "00") -> str:
    """JOLTS series, e.g. ``JTS000000000000000LDR`` (total nonfarm L&D rate).

    Layout (since the 2020 redesign): ``JT`` + ``S``/``U`` + 6-digit industry
    + 2-digit state (00 = US) + 5-digit area (00000) + 2-digit size class
    (00 = all) + 2-letter element (``LD`` layoffs & discharges, ``QU`` quits,
    ``HI`` hires, ``JO`` openings, ``TS`` total separations) + ``R``/``L``
    (rate in percent of employment, or level in thousands).
    """
    return (f"JT{'S' if seasonally_adjusted else 'U'}{industry_code}{state}"
            f"00000" f"00" f"{element}{'R' if rate else 'L'}")


def cpi_id(area_code: str, seasonally_adjusted: bool = False, item: str = "SA0") -> str:
    """CPI-U series, e.g. ``CUUR0000SA0`` (US city average, all items, NSA).

    ``CU`` + ``U``/``S`` (unadjusted / adjusted) + ``R`` (monthly periodicity;
    bimonthly metros are still coded R) + 4-character area + item (``SA0`` =
    all items). Regional series are only published unadjusted, so national
    is pulled unadjusted too and seasonality is removed in the analysis.
    """
    return f"CU{'S' if seasonally_adjusted else 'U'}R{area_code}{item}"


#: National series.
NATIONAL_UNRATE_SA = "LNS14000000"     # U3, seasonally adjusted (what Kalshi settles on)
NATIONAL_UNRATE_NSA = "LNU04000000"    # U3, unadjusted (to compare with NSA metros)
NATIONAL_EMPLOYMENT_SA = "LNS12000000"  # CPS employment level, thousands
NATIONAL_CPI_NSA = cpi_id("0000")      # CUUR0000SA0

#: Industries with a JOLTS layoffs-and-discharges rate. Key -> (JOLTS code,
#: label, words a user might type). Codes from jt.industry.
INDUSTRIES: dict[str, dict[str, Any]] = {
    "total_nonfarm": {"code": "000000", "label": "All jobs (total nonfarm)",
                      "aliases": ["all", "any", "total", "nonfarm", "everyone"]},
    "total_private": {"code": "100000", "label": "All private-sector jobs",
                      "aliases": ["private", "private sector", "other", "unknown"]},
    "mining_logging": {"code": "110099", "label": "Mining and logging",
                       "aliases": ["mining", "logging", "oil", "gas extraction", "energy"]},
    "construction": {"code": "230000", "label": "Construction",
                     "aliases": ["construction", "builder", "contractor", "trades", "carpenter", "electrician"]},
    "manufacturing": {"code": "300000", "label": "Manufacturing",
                      "aliases": ["manufacturing", "factory", "plant"]},
    "trade_transport_utilities": {"code": "400000", "label": "Trade, transportation and utilities",
                                  "aliases": ["trade", "transportation and utilities"]},
    "wholesale": {"code": "420000", "label": "Wholesale trade", "aliases": ["wholesale", "distribution"]},
    "retail": {"code": "440000", "label": "Retail trade",
               "aliases": ["retail", "store", "shop", "cashier"]},
    "transport_utilities": {"code": "480099", "label": "Transportation, warehousing and utilities",
                            "aliases": ["transportation", "trucking", "driver", "logistics", "warehouse", "utilities", "delivery"]},
    "information": {"code": "510000", "label": "Information (media, publishing, telecom, software publishing)",
                    "aliases": ["information", "media", "tech", "software", "telecom", "publishing", "journalism"]},
    "financial": {"code": "510099", "label": "Financial activities",
                  "aliases": ["finance", "financial", "banking", "insurance", "real estate", "realtor"]},
    "professional_business": {"code": "540099", "label": "Professional and business services",
                              "aliases": ["professional", "business services", "consulting", "legal", "accounting",
                                          "advertising", "marketing", "staffing", "freelance", "contractor services"]},
    "education_health": {"code": "600000", "label": "Private education and health services",
                         "aliases": ["education", "teacher", "school"]},
    "health_care": {"code": "620000", "label": "Health care and social assistance",
                    "aliases": ["health", "healthcare", "nurse", "hospital", "medical", "social work"]},
    "leisure_hospitality": {"code": "700000", "label": "Leisure and hospitality",
                            "aliases": ["leisure", "hospitality", "tourism", "ski", "resort", "entertainment", "recreation"]},
    "accommodation_food": {"code": "720000", "label": "Accommodation and food services",
                           "aliases": ["restaurant", "food service", "server", "bartender", "hotel", "accommodation", "chef", "cook"]},
    "other_services": {"code": "810000", "label": "Other services",
                       "aliases": ["other services", "repair", "personal services", "salon"]},
    "government": {"code": "900000", "label": "Government",
                   "aliases": ["government", "public sector", "federal", "state government", "civil service"]},
}

#: The fallback industry when we don't know or can't match one.
DEFAULT_INDUSTRY = "total_private"


# ---------------------------------------------------------------------------
# Fetching and caching
# ---------------------------------------------------------------------------


@dataclass
class FetchReport:
    """What a :func:`fetch_series` call did, for the study to print."""

    queries_sent: int = 0
    served_from_cache: int = 0          # (series, window) pairs not re-fetched
    missing: list[str] = field(default_factory=list)   # series BLS doesn't know / returned empty
    messages: list[str] = field(default_factory=list)  # BLS's own notes, deduplicated
    limit_hit: bool = False
    stale_used: list[str] = field(default_factory=list)  # open windows we couldn't refresh
    mirrored: list[str] = field(default_factory=list)   # filled from FRED (see fetch_fred_mirror)


# In-memory cache: series_id -> {"windows": {"2007-2016": iso_time}, "obs": {"2007-01": 4.6}}
# The same shape is written to disk, one JSON file per series.
_MEM: dict[str, dict] = {}
_LOCK = threading.Lock()


def clear_memory_cache() -> None:
    """Forget everything fetched in this process (tests use this)."""
    with _LOCK:
        _MEM.clear()


def _api_config(api_key: str | None) -> tuple[str, dict, str | None]:
    """URL, limits and key for this run. A key (argument or env var) means v2."""
    key = api_key if api_key is not None else os.environ.get(API_KEY_ENV) or None
    if key:
        return API_V2_URL, LIMITS["v2"], key
    return API_V1_URL, LIMITS["v1"], None


def year_windows(start_year: int, end_year: int, max_years: int) -> list[tuple[int, int]]:
    """Split ``start_year..end_year`` (inclusive) into windows BLS accepts.

    >>> year_windows(2007, 2026, 10)
    [(2007, 2016), (2017, 2026)]
    """
    if end_year < start_year:
        raise ValueError("end_year is before start_year")
    out, y = [], start_year
    while y <= end_year:
        out.append((y, min(y + max_years - 1, end_year)))
        y += max_years
    return out


def _chunks(items: list[str], n: int) -> Iterable[list[str]]:
    for i in range(0, len(items), n):
        yield items[i:i + n]


def _series_path(cache_dir: Path, series_id: str) -> Path:
    return cache_dir / "series" / f"{series_id}.json"


def _load_disk(cache_dir: Path | None, series_id: str) -> dict | None:
    if cache_dir is None:
        return None
    p = _series_path(cache_dir, series_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None   # a corrupt file is treated as a cache miss


def _save_disk(cache_dir: Path | None, series_id: str, entry: dict) -> None:
    if cache_dir is None:
        return
    p = _series_path(cache_dir, series_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Sorted keys keep diffs readable when the cache is refreshed.
    p.write_text(json.dumps({"series_id": series_id, **entry}, sort_keys=True, separators=(",", ":")))


def _save_raw(cache_dir: Path | None, payload: dict, body: dict) -> None:
    """Keep every raw response (gzipped) as an audit trail of what BLS sent."""
    if cache_dir is None:
        return
    raw = cache_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    # Never write the key to disk.
    request = {k: v for k, v in payload.items() if k != "registrationkey"}
    digest = hashlib.sha1(json.dumps(request, sort_keys=True).encode()).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    with gzip.open(raw / f"{stamp}_{digest}.json.gz", "wt") as fh:
        json.dump({"request": request, "response": body}, fh)


def _window_key(w: tuple[int, int]) -> str:
    return f"{w[0]}-{w[1]}"


def _window_is_fresh(entry: dict, w: tuple[int, int], now: datetime, current_year: int) -> bool:
    """Is window ``w`` cached and still trustworthy?

    A window wholly in the past never changes (BLS revises seasonal factors
    once a year, by a hair; we accept that). A window reaching into the
    current year is refetched once it is older than OPEN_WINDOW_MAX_AGE_DAYS.
    """
    stamp = entry.get("windows", {}).get(_window_key(w))
    if stamp is None:
        return False
    if w[1] < current_year:
        return True
    age = now - datetime.fromisoformat(stamp)
    return age.days < OPEN_WINDOW_MAX_AGE_DAYS


def parse_observations(series_json: dict) -> dict[str, float]:
    """One series from a BLS response -> {"YYYY-MM": value}.

    BLS rows look like ``{"year": "2024", "period": "M01", "value": "3.7",
    ...}``. Periods ``M01``-``M12`` are months. ``M13`` is an annual
    average and ``S01``/``S02``/``S03`` are half-year averages (bimonthly
    CPI metros); those are skipped. Values of ``-`` or ``(NA)`` mean "not
    available" (e.g. October 2025, when the federal shutdown cancelled
    collection) and are skipped too, leaving a gap rather than a zero.
    """
    out: dict[str, float] = {}
    for row in series_json.get("data") or []:
        period = str(row.get("period", ""))
        if not (period.startswith("M") and period[1:].isdigit() and 1 <= int(period[1:]) <= 12):
            continue
        try:
            value = float(str(row.get("value", "")).replace(",", ""))
        except ValueError:
            continue
        out[f"{int(row['year']):04d}-{int(period[1:]):02d}"] = value
    return out


def to_series(obs: dict[str, float], name: str | None = None) -> pd.Series:
    """{"YYYY-MM": value} -> float Series on month-start timestamps, sorted."""
    if not obs:
        return pd.Series(dtype=float, name=name)
    idx = pd.to_datetime([f"{k}-01" for k in obs])
    return pd.Series(list(obs.values()), index=idx, name=name, dtype=float).sort_index()


def _post_json(url: str, payload: dict, session: Any | None) -> dict:
    """POST with retries on transient failures; raise BLSLimitError on quota.

    BLS answers HTTP 200 even when it refuses a query; the refusal is in the
    body: ``{"status": "REQUEST_NOT_PROCESSED", "message": ["...daily
    threshold..."]}``. That case is not retried.
    """
    sess = session or requests
    last_exc: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            resp = sess.post(url, json=payload, timeout=TIMEOUT)
            if (resp.status_code == 429 or resp.status_code >= 500) and attempt < RETRIES:
                time.sleep(2.0 * (attempt + 1))
                continue
            resp.raise_for_status()
            body = resp.json()
        except Exception as exc:  # network, HTTP error, bad JSON
            last_exc = exc
            if attempt < RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise BLSError(f"BLS request failed: {exc}") from exc
        status = str(body.get("status", ""))
        messages = " ".join(str(m) for m in body.get("message") or [])
        if status != "REQUEST_SUCCEEDED":
            if "threshold" in messages.lower() or "limit" in messages.lower():
                raise BLSLimitError(f"BLS daily query limit reached: {messages}")
            raise BLSError(f"BLS did not process the request ({status}): {messages}")
        return body
    raise BLSError(f"BLS request failed: {last_exc}")  # pragma: no cover


def fetch_series(
    series_ids: Iterable[str],
    start_year: int,
    end_year: int,
    session: Any | None = None,
    cache_dir: str | Path | None = None,
    api_key: str | None = None,
    offline: bool = False,
    report: FetchReport | None = None,
    now: datetime | None = None,
    mirror: bool = True,
    fred_session: Any | None = None,
) -> dict[str, pd.Series]:
    """Monthly values for each series over ``start_year..end_year``.

    Returns ``{series_id: Series}`` (a series with no data comes back
    empty, and is listed in ``report.missing``).

    How it saves queries:

    * the year range is split into BLS-sized windows (10 years on v1);
    * for each window, only series not already cached are requested,
      packed 25 (v1) or 50 (v2) to a query;
    * every response is written to the in-memory cache and, if
      ``cache_dir`` is given, to ``cache_dir/series/<id>.json`` (plus the
      raw response under ``cache_dir/raw/``).

    ``offline=True`` never touches the network: it returns whatever is
    cached. If the daily limit is hit mid-way, the remaining windows are
    skipped, ``report.limit_hit`` is set, and the cached data is returned
    — the caller decides whether that's enough.

    ``mirror=True`` (default): anything still missing after the BLS API
    (quota used up, or a BLS outage) is filled from FRED, the St. Louis
    Fed's republication of the same BLS series, when FRED carries it (see
    :data:`FRED_MIRROR`). ``report.mirrored`` lists those series.
    ``fred_session`` defaults to ``session``.
    """
    ids = list(dict.fromkeys(s.strip().upper() for s in series_ids))  # dedupe, keep order
    cache = Path(cache_dir) if cache_dir is not None else None
    report = report if report is not None else FetchReport()
    now = now or datetime.now(timezone.utc)
    url, limits, key = _api_config(api_key)

    # 1. Load what we have (memory first, then disk).
    entries: dict[str, dict] = {}
    with _LOCK:
        for sid in ids:
            entry = _MEM.get(sid) or _load_disk(cache, sid) or {"windows": {}, "obs": {}}
            entries[sid] = entry
            _MEM[sid] = entry

    # 2. Fetch what is missing or stale. Batches are taken in the caller's
    #    order and each batch gets its full history before the next one
    #    starts, so if the daily quota runs out, the series listed first
    #    (put the important ones first) are the complete ones.
    windows = year_windows(start_year, end_year, limits["years"])
    for batch_ids in _chunks(ids, limits["series"]):
        for w in windows:
            need = [s for s in batch_ids if not _window_is_fresh(entries[s], w, now, now.year)]
            report.served_from_cache += len(batch_ids) - len(need)
            if not need:
                continue
            if offline or report.limit_hit:
                # Can't refresh: fall back to an older copy of this window if any.
                report.stale_used += [s for s in need if _window_key(w) in entries[s].get("windows", {})]
                continue
            payload: dict[str, Any] = {"seriesid": need, "startyear": str(w[0]), "endyear": str(w[1])}
            if key:
                payload["registrationkey"] = key
            try:
                body = _post_json(url, payload, session)
            except BLSLimitError as exc:
                report.limit_hit = True
                report.messages.append(str(exc))
                report.stale_used += [s for s in need if _window_key(w) in entries[s].get("windows", {})]
                continue
            report.queries_sent += 1
            _save_raw(cache, payload, body)
            for m in body.get("message") or []:
                if str(m) not in report.messages:
                    report.messages.append(str(m))
            returned = {s.get("seriesID", "").upper(): s for s in (body.get("Results") or {}).get("series") or []}
            stamp = now.isoformat()
            with _LOCK:
                for sid in need:
                    entry = entries[sid]
                    entry["obs"].update(parse_observations(returned.get(sid, {})))
                    # Record the window as fetched even when it was empty, so
                    # a series that simply has no data there (e.g. CPI
                    # divisions before 2018) isn't re-asked every run.
                    entry["windows"][_window_key(w)] = stamp
                    _MEM[sid] = entry
                    _save_disk(cache, sid, entry)

    # 2b. Fill the gaps from the FRED mirror (same BLS numbers, no quota).
    if mirror and not offline:
        for sid in ids:
            missing_w = [w for w in windows if _window_key(w) not in entries[sid].get("windows", {})]
            if not missing_w or sid not in FRED_MIRROR:
                continue
            try:
                # The same session object serves both unless told otherwise
                # (the tests' fake answers BLS POSTs and FRED GETs).
                obs = fetch_fred_mirror(sid, missing_w[0][0], missing_w[-1][1],
                                        session=fred_session if fred_session is not None else session)
            except BLSError as exc:
                report.messages.append(str(exc))
                continue
            stamp = now.isoformat()
            with _LOCK:
                entry = entries[sid]
                entry["obs"].update(obs)
                for w in missing_w:
                    # Only a window FRED actually had data for counts as
                    # fetched; the rest stays open for the BLS API next time
                    # (some FRED copies stop where BLS renamed an area).
                    if any(f"{w[0]:04d}-01" <= k <= f"{w[1]:04d}-12" for k in obs):
                        entry["windows"][_window_key(w)] = stamp
                        entry.setdefault("source", {})[_window_key(w)] = f"fred:{FRED_MIRROR[sid]}"
                _MEM[sid] = entry
                _save_disk(cache, sid, entry)
            if obs:
                report.mirrored.append(sid)
            time.sleep(FRED_PAUSE)

    # 3. Cut each series to the requested years.
    out: dict[str, pd.Series] = {}
    lo, hi = f"{start_year:04d}-01", f"{end_year:04d}-12"
    for sid in ids:
        obs = {k: v for k, v in entries[sid]["obs"].items() if lo <= k <= hi}
        if not obs and sid not in report.missing:
            report.missing.append(sid)
        out[sid] = to_series(obs, name=sid)
    return out


# ---------------------------------------------------------------------------
# FRED mirror. FRED (Federal Reserve Bank of St. Louis) republishes BLS
# series unchanged, as CSV, without a key or a daily quota. When the BLS
# API's keyless quota is used up — it is counted per IP address, and a
# shared network can exhaust it before you send anything — fetch_series
# falls back to FRED for the series listed here. FRED uses its own IDs
# for most of them, so the table maps BLS ID -> FRED ID.
#
# Not every BLS series is on FRED: the nine CPI divisions and the Phoenix
# CPI are not, and FRED has seasonally adjusted JOLTS only for the totals
# (so the study uses the unadjusted JOLTS series, which both sources carry).
# ---------------------------------------------------------------------------
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
#: Pause between FRED downloads, to be polite.
FRED_PAUSE = 0.2


def _fred_jolts_code(code: str) -> str:
    """BLS 6-digit JOLTS industry code -> FRED's short form.
    "000000" -> "" (total nonfarm), "230000" -> "2300", "540099" -> "540099"."""
    if code == "000000":
        return ""
    return code[:4] if code.endswith("00") else code


def _build_fred_mirror() -> dict[str, str]:
    m = {
        NATIONAL_UNRATE_SA: "UNRATE",
        NATIONAL_UNRATE_NSA: "UNRATENSA",
        NATIONAL_EMPLOYMENT_SA: "CE16OV",
        NATIONAL_CPI_NSA: "CPIAUCNS",
        # JOLTS levels (thousands) for the total, used to scale to displacements
        jolts_id("000000", rate=False, seasonally_adjusted=False): "JTULDL",
        jolts_id("000000", rate=False): "JTSLDL",
        jolts_id("000000"): "JTSLDR",
        jolts_id("100000"): "JTS1000LDR",
        jolts_id("900000"): "JTS9000LDR",
    }
    for info in INDUSTRIES.values():
        m[jolts_id(info["code"], seasonally_adjusted=False)] = f"JTU{_fred_jolts_code(info['code'])}LDR"
    for st in STATE_FIPS:
        m[laus_state_id(st)] = f"{st}UR"            # seasonally adjusted state rate
    for code in ("0100", "0200", "0300", "0400"):
        m[cpi_id(code)] = cpi_id(code)               # CPI regions: same ID on FRED
    # CPI metros: BLS renamed its metro areas in 2018 (S-codes); FRED still
    # files most continuing series under the old A-codes, through today.
    # Two exceptions stop in Dec 2017 because the area itself was redrawn:
    # Los Angeles (A421 was LA-Riverside-Orange County; Riverside became its
    # own area) and Washington (A311 was Washington-Baltimore). For those,
    # the mirror gives 2001-2017 on the old definition; the BLS API fills
    # in the new one when quota allows. Denver and Phoenix have no
    # usable FRED copy.
    for new, old in {"S12A": "A101", "S49A": "A421", "S23A": "A207", "S37A": "A316", "S37B": "A318",
                     "S35A": "A311", "S35B": "A320", "S35C": "A319", "S49B": "A422", "S49D": "A423",
                     "S11A": "A103", "S12B": "A102", "S23B": "A208"}.items():
        m[cpi_id(new)] = cpi_id(old)
    # LAUS metros (unadjusted rate): FRED's own area codes.
    for (fips, cbsa), fred_id in {
        ("36", "35620"): "NEWY636URN", ("06", "31080"): "LOSA106URN", ("17", "16980"): "CHIC917URN",
        ("48", "19100"): "DALL148URN", ("48", "26420"): "HOUS448URN", ("11", "47900"): "WASH911URN",
        ("12", "33100"): "MIAM112URN", ("42", "37980"): "PHIL942URN", ("13", "12060"): "ATLA013URN",
        ("04", "38060"): "PHOE004URN", ("06", "41860"): "SANF806URN", ("53", "42660"): "SEAT653URN",
        ("08", "19740"): "DENV708URN", ("26", "19820"): "DETR826URN", ("32", "29820"): "LASV832URN",
    }.items():
        m[laus_metro_id(fips, cbsa)] = fred_id
    return m


def fetch_fred_mirror(series_id: str, start_year: int, end_year: int,
                      session: Any | None = None) -> dict[str, float]:
    """One BLS series from its FRED copy -> {"YYYY-MM": value}.

    FRED's CSV looks like ``observation_date,UNRATE`` then
    ``2001-01-01,4.2``; a missing month is blank or ``.``. Retries like the
    BLS path; raises BLSError if FRED doesn't carry the series.
    """
    fred_id = FRED_MIRROR.get(series_id.upper())
    if fred_id is None:
        raise BLSError(f"No FRED mirror for {series_id}")
    sess = session or requests
    params = {"id": fred_id, "cosd": f"{start_year}-01-01", "coed": f"{end_year}-12-31"}
    last_exc: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            resp = sess.get(FRED_CSV_URL, params=params, timeout=TIMEOUT)
            if (resp.status_code == 429 or resp.status_code >= 500) and attempt < RETRIES:
                time.sleep(2.0 * (attempt + 1))
                continue
            resp.raise_for_status()
            text = resp.text
            break
        except Exception as exc:
            last_exc = exc
            if attempt < RETRIES:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise BLSError(f"FRED request for {fred_id} failed: {exc}") from exc
    else:  # pragma: no cover
        raise BLSError(f"FRED request for {fred_id} failed: {last_exc}")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines or not lines[0].lower().startswith("observation_date"):
        raise BLSError(f"FRED has no series {fred_id} (mirror of {series_id})")
    out: dict[str, float] = {}
    lo, hi = f"{start_year:04d}-01", f"{end_year:04d}-12"
    for ln in lines[1:]:
        day, _, value = ln.partition(",")
        month = day[:7]
        if not lo <= month <= hi:
            continue   # FRED ignores the date range for some ended series
        try:
            out[month] = float(value)
        except ValueError:
            continue   # "." or blank = not available
    return out


#: BLS series ID -> FRED series ID.
FRED_MIRROR: dict[str, str] = _build_fred_mirror()


# ---------------------------------------------------------------------------
# Analysis: pure functions (no network). Rates from BLS are in PERCENT
# (1.2 means 1.2%); these functions take FRACTIONS unless they say otherwise.
# ---------------------------------------------------------------------------

#: The pandemic shock: March-May 2020 layoffs were 3-10x anything else in
#: the record. Kept out of "typical" figures and reported separately.
PANDEMIC_SHOCK = ("2020-03-01", "2020-05-01")
#: The wider pandemic disruption, excluded from the "ex-COVID" correlations
#: because one simultaneous national shock makes every place look alike.
PANDEMIC_WINDOW = ("2020-03-01", "2021-12-01")
#: NBER recessions inside the JOLTS record (Dec 2000 on), by month.
RECESSIONS = [("2001-04-01", "2001-11-01"), ("2008-01-01", "2009-06-01"), ("2020-03-01", "2020-04-01")]


def annual_prob_from_monthly(monthly_rate: float, months: int = 12) -> float:
    """Chance of at least one event in ``months`` months at a constant
    monthly rate (a fraction: 0.012 for 1.2%).

    JOLTS reports layoffs and discharges in a month as a percent of
    employment. Read as a monthly hazard ``m`` — the chance a given job
    ends involuntarily this month — the chance of getting through a year
    without one is ``(1 - m)^12``, so the chance of at least one is::

        P(year) = 1 - (1 - m)^12          (e.g. m = 1.2% -> 13.5%)

    It is a little below ``12 * m`` (14.4%) because you can only lose a
    job "for the first time" once; the gap matters for high rates.

    This treats every worker as equally exposed, which overstates the risk
    for a settled worker: JOLTS counts separations, not people, and they
    pile up among new hires, seasonal and temporary jobs, and people laid
    off more than once. :func:`displacement_scale` corrects for that.
    """
    if not 0.0 <= monthly_rate < 1.0:
        raise ValueError("monthly_rate must be a fraction in [0, 1)")
    if months < 0:
        raise ValueError("months must be non-negative")
    return 1.0 - (1.0 - monthly_rate) ** months


def monthly_from_annual_prob(annual_prob: float, months: int = 12) -> float:
    """Inverse of :func:`annual_prob_from_monthly`: the constant monthly
    hazard that gives ``annual_prob`` over ``months`` months."""
    if not 0.0 <= annual_prob < 1.0:
        raise ValueError("annual_prob must be a fraction in [0, 1)")
    return 1.0 - (1.0 - annual_prob) ** (1.0 / months)


def _drop_periods(s: pd.Series, periods: Iterable[tuple[str, str]] | None) -> pd.Series:
    if not periods:
        return s
    keep = pd.Series(True, index=s.index)
    for a, b in periods:
        keep &= ~((s.index >= pd.Timestamp(a)) & (s.index <= pd.Timestamp(b)))
    return s[keep]


def _in_periods(idx: pd.DatetimeIndex, periods: Iterable[tuple[str, str]]) -> np.ndarray:
    mask = np.zeros(len(idx), dtype=bool)
    for a, b in periods:
        mask |= (idx >= pd.Timestamp(a)) & (idx <= pd.Timestamp(b))
    return mask


def layoff_summary(rate_pct: pd.Series, scale: float = 1.0) -> dict[str, float]:
    """Turn a JOLTS layoffs-and-discharges rate series (percent) into odds.

    Returns fractions:

    ``monthly_typical``
        Average monthly rate, leaving out the March-May 2020 shock.
    ``monthly_median``
        Median month: what a calm year looks like.
    ``monthly_recession``
        Average over NBER recession months (2001, 2008-09; not 2020).
    ``monthly_pandemic_peak``
        The worst month of 2020.
    ``annual_any``
        :func:`annual_prob_from_monthly` of ``monthly_typical``: the
        chance a job ends in a layoff or discharge within a year.
    ``annual_recession``
        The same at recession rates.
    ``annual_displacement`` / ``annual_displacement_recession``
        ``annual_any`` after multiplying the monthly rate by ``scale``
        (see :func:`displacement_scale`): the chance for a settled worker.
    ``months``
        Number of monthly observations used.
    """
    s = rate_pct.dropna() / 100.0
    if s.empty:
        raise ValueError("no layoff data")
    typical = _drop_periods(s, [PANDEMIC_SHOCK])
    rec = s[_in_periods(s.index, [r for r in RECESSIONS if not r[0].startswith("2020")])]
    shock = s[_in_periods(s.index, [PANDEMIC_SHOCK])]
    m_typ = float(typical.mean())
    m_rec = float(rec.mean()) if len(rec) else m_typ
    return {
        "monthly_typical": m_typ,
        "monthly_median": float(typical.median()),
        "monthly_recession": m_rec,
        "monthly_pandemic_peak": float(shock.max()) if len(shock) else float("nan"),
        "annual_any": annual_prob_from_monthly(m_typ),
        "annual_recession": annual_prob_from_monthly(m_rec),
        "annual_displacement": annual_prob_from_monthly(min(m_typ * scale, 0.99)),
        "annual_displacement_recession": annual_prob_from_monthly(min(m_rec * scale, 0.99)),
        "months": int(len(s)),
    }


def displacement_scale(displaced_per_year: float, jolts_ld_per_year: float) -> float:
    """Share of JOLTS layoffs that are "displacements" of the kind that
    cost a settled worker their livelihood.

    The CPS Displaced Worker Survey counts people (aged 20+) who lost a job
    because their plant closed, their position was abolished or there was
    not enough work — and counts each person once per three-year window.
    JOLTS counts every layoff and discharge, including firing for cause,
    the end of seasonal and temporary jobs, and the same person twice.
    Dividing the first by the second (same years, both in people per year)
    gives the factor that turns a JOLTS rate into a displacement rate. We
    apply the national factor to every industry, which assumes the mix of
    "churn" vs. "displacement" layoffs is similar across industries — a
    simplification noted in the findings.
    """
    if jolts_ld_per_year <= 0:
        raise ValueError("jolts_ld_per_year must be positive")
    return float(displaced_per_year / jolts_ld_per_year)


def changes(s: pd.Series, months: int = 1, log: bool = False) -> pd.Series:
    """``months``-month changes of a monthly series, on a regular calendar.

    ``log=False``: differences (percentage POINTS, right for unemployment
    rates). ``log=True``: log differences (≈ percent changes, right for a
    price index like CPI). Missing months stay missing rather than being
    bridged, so a change is only computed between two real observations
    exactly ``months`` apart.
    """
    s = s.dropna()
    if s.empty:
        return s
    full = s.asfreq("MS")   # month-start calendar; gaps become NaN
    x = np.log(full) if log else full
    return (x - x.shift(months)).dropna()


def deseasonalize(ch: pd.Series) -> pd.Series:
    """Subtract each calendar month's average change.

    Unadjusted monthly CPI changes share a seasonal rhythm everywhere
    (prices rise in spring, dip in November-December). Left in, that common
    rhythm would make every region look like the nation for a reason that
    has nothing to do with a surprise. Removing the month-of-year mean is a
    crude seasonal adjustment, but it is applied the same way to both sides.
    """
    if ch.empty:
        return ch
    return ch - ch.groupby(ch.index.month).transform("mean")


def change_correlation(
    local: pd.Series,
    national: pd.Series,
    months: int = 1,
    log: bool = False,
    deseason: bool = False,
    exclude: Iterable[tuple[str, str]] | None = None,
    min_obs: int = 24,
) -> dict[str, float]:
    """How closely a local series moves with the national one.

    Computes ``months``-month changes of both (see :func:`changes`), lines
    them up on common months, optionally removes seasonality, optionally
    drops changes that touch the ``exclude`` periods, and returns:

    ``corr``  Pearson correlation of the changes, -1..1. This is the basis
              of a hedge that pays on the national number against a loss
              proportional to the local number (before the single-strike
              discount, see :func:`single_strike_basis`).
    ``beta``  Slope of local on national changes: how many points the local
              number moves per point of national. The variance-minimizing
              hedge ratio.
    ``local_sd`` / ``national_sd``  Standard deviation of each side's changes.
    ``n``     Number of changes used. Fewer than ``min_obs`` -> NaNs.
    """
    a = changes(local, months, log)
    b = changes(national, months, log)
    df = pd.concat({"local": a, "national": b}, axis=1).dropna()
    if exclude:
        # Drop a change if either its start or its end month is excluded.
        end_bad = _in_periods(df.index, exclude)
        start_bad = _in_periods(df.index - pd.DateOffset(months=months), exclude)
        df = df[~(end_bad | start_bad)]
    if deseason and len(df):
        df = df.apply(deseasonalize)
    n = len(df)
    nan = {"corr": float("nan"), "beta": float("nan"), "local_sd": float("nan"),
           "national_sd": float("nan"), "n": n}
    if n < min_obs or df["national"].std() == 0 or df["local"].std() == 0:
        return nan
    c = float(df["local"].corr(df["national"]))
    beta = float(np.cov(df["local"], df["national"])[0, 1] / df["national"].var())
    return {"corr": c, "beta": beta, "local_sd": float(df["local"].std()),
            "national_sd": float(df["national"].std()), "n": n}


#: corr(contract pays, one-sided loss) for a single at-the-money binary
#: contract when the national surprise and the loss are perfectly correlated
#: normals: phi(0) / sqrt(1/2 - phi(0)^2) = 0.683. (Derivation in
#: :func:`single_strike_basis`.) The same 0.68 ceiling that
#: findings/02_history.md measured for gas.
SINGLE_STRIKE_CEILING = (1 / math.sqrt(2 * math.pi)) / math.sqrt(0.5 - 1 / (2 * math.pi))


def single_strike_basis(r: float) -> float:
    """Basis for ONE binary contract against a loss that grows with the overrun.

    ``r`` is the correlation of the underlying changes (local vs national,
    from :func:`change_correlation`). A binary contract only says "it
    happened" or "it didn't", while a retiree's loss grows with how far
    prices overshoot. With national surprise N and local overrun L as
    standard normals with correlation r, the contract pays ``1{N > 0}``
    and the loss is ``max(L, 0)``. Stein's lemma gives
    ``cov = phi(0) * r / 2``; the standard deviations are 1/2 and
    ``sqrt(1/2 - phi(0)^2)``, so::

        basis = 0.683 * r

    This is what to pass as ``basis_correlation`` for a single strike. A
    ladder of strikes, or a variance-minimizing size, gets closer to ``r``.
    """
    return float(SINGLE_STRIKE_CEILING * max(r, 0.0))


def unemployment_rises(u_pct: pd.Series, months: int = 1, threshold_pp: float = 0.0) -> pd.Series:
    """Payoff of an at-the-money "unemployment above the last print" contract.

    For each start month t: 1.0 if the rate ``months`` later is more than
    ``threshold_pp`` points above the rate at t, else 0.0. Indexed by t.
    (U3 is published to one decimal, so "unchanged" is common and does not
    pay.)
    """
    u = u_pct.dropna().asfreq("MS")
    ahead = u.shift(-months)
    pays = (ahead - u > threshold_pp + 1e-9).astype(float)
    return pays[ahead.notna() & u.notna()]


def job_loss_basis(
    layoff_rate_pct: pd.Series,
    u_pct: pd.Series,
    months: int = 1,
    hazard_scale: float = 1.0,
    exclude: Iterable[tuple[str, str]] | None = None,
    threshold_pp: float = 0.0,
) -> dict[str, float]:
    """Basis between one worker's job loss and a national-unemployment contract.

    Setup, month by month (or window by window for ``months`` > 1):

    * the contract pays B_t = 1 if U3 rises over the next ``months`` months
      (:func:`unemployment_rises`);
    * the worker's chance of losing their job in that window is
      p_t = 1 - prod(1 - hazard_scale * layoff_rate) over the window's months,
      with the layoff rate of their industry.

    The basis is the correlation between the payoff and the job-loss
    indicator, both 0/1. With q = mean(B) and p = mean(p_t)::

        P(pays and lose) = mean(B_t * p_t)
        corr = (P(pays and lose) - p*q) / sqrt(p(1-p) * q(1-q))

    exactly the measure used in findings/02_history.md, and the same
    correlation ``hedge.joint_states`` consumes. Also returned is
    ``p_pay_given_loss`` = P(pays | lose) = P(pays and lose) / p, the
    friendlier way to say it: "in the windows people in your industry lost
    jobs, the contract paid X% of the time, vs. q% overall."

    Overlapping windows (months > 1) are serially correlated; the estimate
    is fine, but treat ``n`` as smaller than it looks.
    """
    rate = layoff_rate_pct.dropna().asfreq("MS") / 100.0 * hazard_scale
    pays = unemployment_rises(u_pct, months, threshold_pp)
    # p_t: chance of at least one layoff in months t+1..t+months.
    survive = np.log1p(-rate.clip(upper=0.99))
    window_survive = sum(survive.shift(-k) for k in range(1, months + 1))
    p_t = (1.0 - np.exp(window_survive)).rename("p")
    df = pd.concat({"pays": pays, "p": p_t}, axis=1).dropna()
    if exclude:
        start_bad = _in_periods(df.index, exclude)
        end_bad = _in_periods(df.index + pd.DateOffset(months=months), exclude)
        df = df[~(start_bad | end_bad)]
    n = len(df)
    if n < 12:
        return {"corr": float("nan"), "p": float("nan"), "q": float("nan"),
                "p_pay_given_loss": float("nan"), "n": n}
    q = float(df["pays"].mean())
    p = float(df["p"].mean())
    both = float((df["pays"] * df["p"]).mean())
    denom = math.sqrt(p * (1 - p) * q * (1 - q))
    corr = (both - p * q) / denom if denom > 0 else float("nan")
    return {"corr": float(corr), "p": p, "q": q, "p_pay_given_loss": both / p if p > 0 else float("nan"), "n": n}


# ---------------------------------------------------------------------------
# Lookups (offline): the measured tables, and the functions that read them.
# ---------------------------------------------------------------------------

#: Used when nothing better is known. Matches what the backtest measured
#: for a single job vs national U3 (findings/02_history.md, ~0.02).
FALLBACK_JOB_BASIS = 0.02
#: Used only if a place table is empty; otherwise an unknown place gets the
#: median of its table (see basis_to_national).
FALLBACK_PLACE_BASIS = {"unemployment": 0.6, "cpi": 0.8}


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().replace("_", " ").replace("-", " ").replace(",", " ").split())


def resolve_industry(industry: str | None) -> str:
    """Match free text ("restaurant server", "Construction") to an industry
    key in :data:`INDUSTRIES`. Unknown or empty -> ``DEFAULT_INDUSTRY``.

    Exact keys and labels win; then the longest alias found in the text
    (so "real estate agent" matches "real estate", not "state").
    """
    t = _norm(industry or "")
    if not t:
        return DEFAULT_INDUSTRY
    for key, info in INDUSTRIES.items():
        if t == _norm(key) or t == _norm(info["label"]):
            return key
    best, best_len = DEFAULT_INDUSTRY, 0
    for key, info in INDUSTRIES.items():
        for alias in info["aliases"]:
            a = _norm(alias)
            if (f" {a} " in f" {t} ") and len(a) > best_len:
                best, best_len = key, len(a)
    return best


def resolve_state(place: str | None) -> str | None:
    """"CA", "california", "Austin, TX", "Washington, DC" -> a state code.

    Order matters: an exact code ("LA" is Louisiana, not Los Angeles), then
    a code after the last comma ("Kansas City, MO" is Missouri even though
    it contains "Kansas"), then DC spelled out, then a state name, then a
    known metro's principal state ("Denver" -> CO). None if nothing fits.
    """
    if not place:
        return None
    raw = str(place).strip()
    if raw.upper() in STATE_FIPS:
        return raw.upper()
    if "," in raw:
        last = raw.rsplit(",", 1)[1].strip().replace(".", "").upper()
        if last in STATE_FIPS:
            return last
    t = _norm(raw.replace(".", ""))
    if f" {t} ".count(" dc ") or "district of columbia" in t:
        return "DC"
    for abbr, name in sorted(STATE_NAMES.items(), key=lambda kv: -len(kv[1])):
        if f" {_norm(name)} " in f" {t} ":
            return abbr
    for metro, st in METRO_STATE.items():
        if f" {_norm(metro)} " in f" {t} ":
            return st
    return None


#: Metros in the tables -> principal state, for falling back from a metro
#: we have no number for (e.g. Denver CPI) to its state or region.
METRO_STATE = {
    "new_york": "NY", "los_angeles": "CA", "chicago": "IL", "dallas": "TX", "houston": "TX",
    "washington_dc": "DC", "miami": "FL", "philadelphia": "PA", "atlanta": "GA", "phoenix": "AZ",
    "san_francisco": "CA", "seattle": "WA", "denver": "CO", "detroit": "MI", "las_vegas": "NV",
    "boston": "MA",
}


def job_loss_prob(
    industry: str | None = None,
    horizon_months: int = 12,
    kind: str = "displacement",
    scenario: str = "typical",
) -> float:
    """A worker's chance of losing their job involuntarily within
    ``horizon_months``, from the frozen :data:`JOB_LOSS` table.

    ``kind="displacement"`` (default): for a settled worker — the JOLTS rate
    scaled down to match how often the Displaced Worker Survey finds people
    losing a job to a closure, abolished position or slack work.
    ``kind="any"``: every layoff and discharge counts; right for seasonal,
    temporary, gig and short-tenure workers, and an upper bound otherwise.

    ``scenario="recession"`` uses the 2001 and 2008-09 recession rates.

    The monthly hazard implied by the annual figure is held constant over
    the horizon, so ``horizon_months=1`` gives the monthly chance a monthly
    contract needs as ``loss_prob``.
    """
    key = resolve_industry(industry)
    row = JOB_LOSS.get(key) or JOB_LOSS[DEFAULT_INDUSTRY]
    if kind not in ("displacement", "any"):
        raise ValueError("kind must be 'displacement' or 'any'")
    if scenario not in ("typical", "recession"):
        raise ValueError("scenario must be 'typical' or 'recession'")
    col = {("displacement", "typical"): "annual_displacement",
           ("displacement", "recession"): "annual_displacement_recession",
           ("any", "typical"): "annual_any",
           ("any", "recession"): "annual_recession"}[(kind, scenario)]
    annual = row[col]
    return annual_prob_from_monthly(monthly_from_annual_prob(annual), horizon_months)


def _place_table(measure: str) -> tuple[dict, dict]:
    if measure == "unemployment":
        return STATE_UNEMPLOYMENT_BASIS, METRO_UNEMPLOYMENT_BASIS
    if measure == "cpi":
        return CPI_BASIS, CPI_METRO_BASIS
    raise ValueError("measure must be 'unemployment' or 'cpi'")


def basis_to_national(place: str | None, measure: str = "unemployment",
                      horizon: str = "monthly", single_strike: bool = True) -> dict[str, Any]:
    """How well a NATIONAL contract hedges a LOCAL exposure.

    ``place``: a state ("TX", "Texas", "Austin, TX"), a CPI region or
    division ("west", "pacific"), or a metro in the tables ("new york").
    ``measure``: "unemployment" (national U3 vs the place's unemployment
    rate) or "cpi" (national CPI vs the place's CPI).
    ``horizon``: "monthly" (a monthly contract) or "annual" (12-month changes).

    Fallbacks, in order: metro -> state -> CPI division/region (for CPI a
    state uses its division if measured, else its region; for
    unemployment a region uses the median of its states) -> the national
    median of the table.

    Returns ``{"corr": correlation of changes, "basis": what to pass as
    basis_correlation, "matched": what the place resolved to, "source":
    "measured"/"fallback"}``. ``basis`` applies the single-strike discount
    (:func:`single_strike_basis`) unless ``single_strike=False``.

    For ONE PERSON'S JOB, don't use this: use :func:`hedge_defaults` /
    :data:`JOB_LOSS`. A state's unemployment can track the nation closely
    while one job barely does.
    """
    if horizon not in ("monthly", "annual"):
        raise ValueError("horizon must be 'monthly' or 'annual'")
    main, metros = _place_table(measure)
    t = _norm(place or "")
    matched, source, corr = None, "measured", None

    # 1. A metro named in the text (whole words: "MI" must not match "miami";
    #    "Washington" alone is the state, "Washington DC" the metro).
    for name, row in metros.items():
        words = _norm(name)
        hit = f" {words} " in f" {t} " or (name == "washington_dc" and resolve_state(place) == "DC")
        if t and hit and row.get(horizon) is not None:
            matched, corr = f"metro:{name}", row[horizon]
            break
    # 2. A CPI region/division typed directly ("west", "pacific").
    key = t.replace(" ", "_")
    if corr is None and key in main and main[key].get(horizon) is not None:
        matched, corr = key, main[key][horizon]
    # 2b. A census region for unemployment: the median of its states.
    if corr is None and measure == "unemployment" and t in STATE_REGION.values():
        vals = [main[s][horizon] for s, r in STATE_REGION.items() if r == t and s in main]
        if vals:
            matched, corr = f"region:{t} (median of states)", float(np.median(vals))
    # 3. A state.
    if corr is None:
        st = resolve_state(place)
        if st:
            if measure == "unemployment" and st in main:
                matched, corr = st, main[st][horizon]
            elif measure == "cpi":
                for key in (STATE_DIVISION.get(st), STATE_REGION.get(st)):
                    if key in main and main[key].get(horizon) is not None:
                        matched, corr = f"{st} -> {key}", main[key][horizon]
                        break
    # 4. National fallback.
    if corr is None:
        vals = [r[horizon] for r in main.values() if r.get(horizon) is not None]
        corr = float(np.median(vals)) if vals else FALLBACK_PLACE_BASIS[measure]
        matched, source = "national median", "fallback"
    basis = single_strike_basis(corr) if single_strike else max(float(corr), 0.0)
    return {"corr": float(corr), "basis": round(basis, 3), "matched": matched, "source": source}


def hedge_defaults(
    industry: str | None = None,
    place: str | None = None,
    contract: str = "unemployment",
    horizon_months: int = 1,
    exposure: str = "job",
) -> dict[str, Any]:
    """Suggested ``loss_prob`` and ``basis_correlation`` for the hedge engine.

    ``contract``: "unemployment" (a national U3 contract) or "cpi".
    ``exposure``:
      * "job" — the person's own paycheck stops if they're laid off
        (unemployment contracts only). ``loss_prob`` = their industry's
        displacement probability over the horizon; ``basis_correlation`` =
        the measured job-loss basis for their industry (tiny: national U3
        barely tracks one job).
      * "local_economy" — income that rises and falls with the local labor
        market (a shop's sales, a commission book, hours worked).
        ``loss_prob`` = None (same event as the contract);
        ``basis_correlation`` from :func:`basis_to_national`.
      * "cost" — a retiree's or household's costs (CPI contracts).
        ``loss_prob`` = None; basis from regional CPI.

    Returns a dict with the two inputs and an ``evidence`` string the page
    can show.
    """
    horizon = "monthly" if horizon_months <= 1 else "annual"
    if contract == "cpi" or exposure == "cost":
        b = basis_to_national(place, "cpi", horizon)
        return {"loss_prob": None, "basis_correlation": b["basis"],
                "evidence": (f"Regional CPI ({b['matched']}) vs national: correlation of "
                             f"{horizon} changes {b['corr']:.2f}; x{SINGLE_STRIKE_CEILING:.2f} for a single strike.")}
    if contract != "unemployment":
        raise ValueError("contract must be 'unemployment' or 'cpi'")
    if exposure == "local_economy":
        b = basis_to_national(place, "unemployment", horizon)
        return {"loss_prob": None, "basis_correlation": b["basis"],
                "evidence": (f"Unemployment in {b['matched']} vs national: correlation of {horizon} "
                             f"changes {b['corr']:.2f}; x{SINGLE_STRIKE_CEILING:.2f} for a single strike.")}
    if exposure != "job":
        raise ValueError("exposure must be 'job', 'local_economy' or 'cost'")
    key = resolve_industry(industry)
    row = JOB_LOSS.get(key) or JOB_LOSS[DEFAULT_INDUSTRY]
    col = "basis_u3_1m" if horizon == "monthly" else "basis_u3_12m"
    basis = row.get(col)
    if basis is None or not np.isfinite(basis):
        basis = FALLBACK_JOB_BASIS
    lp = job_loss_prob(key, horizon_months)
    return {"loss_prob": round(lp, 4), "basis_correlation": round(max(basis, 0.0), 3),
            "evidence": (f"{INDUSTRIES[key]['label']}: JOLTS layoffs average {row['monthly_typical'] * 100:.2f}%/month "
                         f"(any layoff {row['annual_any'] * 100:.1f}%/yr; settled-worker displacement "
                         f"{row['annual_displacement'] * 100:.1f}%/yr). In months these layoffs happened, a "
                         f"'U3 up' contract paid {row['p_pay_given_loss_1m'] * 100:.0f}% of the time vs "
                         f"{row['q_1m'] * 100:.0f}% overall.")}


# ---------------------------------------------------------------------------
# Measured tables. GENERATED by research/prediction/labor_study.py from BLS
# data cached in research/prediction/data/bls/ — re-run it and paste its
# printed output here to refresh. Values are fractions (0.135 = 13.5%).
# ---------------------------------------------------------------------------

#: Displacement scale: Displaced Worker Survey displacements per year
#: (6.3M over 2021-2023) / JOLTS layoffs and discharges per year (same years).
#: About 1 JOLTS layoff in 9 is a displacement of a settled worker.
DISPLACEMENT_SCALE = 0.1154

#: By industry, JOLTS Dec 2000 - Sep 2026 (unadjusted). monthly_* = layoffs &
#: discharges per month as a share of jobs (typical = average excluding the
#: Mar-May 2020 shock; recession = 2001 and 2008-09 recession months);
#: annual_any = chance of at least one in a year; annual_displacement* = the
#: same for a settled worker (rate x DISPLACEMENT_SCALE). basis_u3_* =
#: corr(national "U3 rises" contract pays, settled worker loses job) over
#: 1 and 12 months, ex Mar 2020-Dec 2021; *_any = same for a worker exposed to
#: every layoff; *_12m_deep = contract "U3 up >= 0.5pt within 12 months".
#: p_pay_given_loss_* / q_* = P(contract pays | job lost) vs P(contract pays).
JOB_LOSS: dict[str, dict[str, float]] = {
    "total_nonfarm": {"monthly_typical": 0.0132, "monthly_recession": 0.0161, "annual_any": 0.147, "annual_recession": 0.1767, "annual_displacement": 0.0181, "annual_displacement_recession": 0.022, "basis_u3_1m": 0.0009, "basis_u3_12m": 0.0028, "basis_u3_1m_any": 0.0025, "basis_u3_12m_any": 0.0077, "basis_u3_12m_deep": 0.0097, "p_pay_given_loss_1m": 0.3353, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3417, "q_12m": 0.3321},
    "total_private": {"monthly_typical": 0.0147, "monthly_recession": 0.0183, "annual_any": 0.1632, "annual_recession": 0.1992, "annual_displacement": 0.0202, "annual_displacement_recession": 0.0251, "basis_u3_1m": 0.001, "basis_u3_12m": 0.0038, "basis_u3_1m_any": 0.0031, "basis_u3_12m_any": 0.0105, "basis_u3_12m_deep": 0.0111, "p_pay_given_loss_1m": 0.3367, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3445, "q_12m": 0.3321},
    "mining_logging": {"monthly_typical": 0.0142, "monthly_recession": 0.0178, "annual_any": 0.1575, "annual_recession": 0.1936, "annual_displacement": 0.0195, "annual_displacement_recession": 0.0243, "basis_u3_1m": 0.002, "basis_u3_12m": 0.0003, "basis_u3_1m_any": 0.006, "basis_u3_12m_any": 0.0008, "basis_u3_12m_deep": 0.0123, "p_pay_given_loss_1m": 0.3486, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3329, "q_12m": 0.3321},
    "construction": {"monthly_typical": 0.0318, "monthly_recession": 0.0421, "annual_any": 0.3215, "annual_recession": 0.4033, "annual_displacement": 0.0432, "annual_displacement_recession": 0.0568, "basis_u3_1m": 0.0019, "basis_u3_12m": 0.0047, "basis_u3_1m_any": 0.0056, "basis_u3_12m_any": 0.0099, "basis_u3_12m_deep": 0.0252, "p_pay_given_loss_1m": 0.3394, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3423, "q_12m": 0.3321},
    "manufacturing": {"monthly_typical": 0.0108, "monthly_recession": 0.0175, "annual_any": 0.1223, "annual_recession": 0.1909, "annual_displacement": 0.0149, "annual_displacement_recession": 0.024, "basis_u3_1m": 0.0031, "basis_u3_12m": 0.0183, "basis_u3_1m_any": 0.0091, "basis_u3_12m_any": 0.0517, "basis_u3_12m_deep": 0.0242, "p_pay_given_loss_1m": 0.3655, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.4018, "q_12m": 0.3321},
    "trade_transport_utilities": {"monthly_typical": 0.0132, "monthly_recession": 0.0161, "annual_any": 0.1477, "annual_recession": 0.1771, "annual_displacement": 0.0182, "annual_displacement_recession": 0.0221, "basis_u3_1m": 0.0005, "basis_u3_12m": 0.005, "basis_u3_1m_any": 0.0016, "basis_u3_12m_any": 0.0141, "basis_u3_12m_deep": 0.0103, "p_pay_given_loss_1m": 0.3315, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3492, "q_12m": 0.3321},
    "wholesale": {"monthly_typical": 0.0096, "monthly_recession": 0.0138, "annual_any": 0.109, "annual_recession": 0.1541, "annual_displacement": 0.0132, "annual_displacement_recession": 0.019, "basis_u3_1m": 0.0016, "basis_u3_12m": 0.0099, "basis_u3_1m_any": 0.0046, "basis_u3_12m_any": 0.0283, "basis_u3_12m_deep": 0.0166, "p_pay_given_loss_1m": 0.3468, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3722, "q_12m": 0.3321},
    "retail": {"monthly_typical": 0.0143, "monthly_recession": 0.0177, "annual_any": 0.1583, "annual_recession": 0.1924, "annual_displacement": 0.0196, "annual_displacement_recession": 0.0242, "basis_u3_1m": 0.0009, "basis_u3_12m": 0.004, "basis_u3_1m_any": 0.0025, "basis_u3_12m_any": 0.0107, "basis_u3_12m_deep": 0.0119, "p_pay_given_loss_1m": 0.3349, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3451, "q_12m": 0.3321},
    "transport_utilities": {"monthly_typical": 0.0139, "monthly_recession": 0.014, "annual_any": 0.1544, "annual_recession": 0.1556, "annual_displacement": 0.0191, "annual_displacement_recession": 0.0192, "basis_u3_1m": -0.0011, "basis_u3_12m": 0.0037, "basis_u3_1m_any": -0.0034, "basis_u3_12m_any": 0.0104, "basis_u3_12m_deep": 0.0017, "p_pay_given_loss_1m": 0.3117, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3445, "q_12m": 0.3321},
    "information": {"monthly_typical": 0.0116, "monthly_recession": 0.0124, "annual_any": 0.1303, "annual_recession": 0.1393, "annual_displacement": 0.0159, "annual_displacement_recession": 0.0171, "basis_u3_1m": 0.0006, "basis_u3_12m": 0.0052, "basis_u3_1m_any": 0.0017, "basis_u3_12m_any": 0.0151, "basis_u3_12m_deep": 0.0033, "p_pay_given_loss_1m": 0.3325, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3516, "q_12m": 0.3321},
    "financial": {"monthly_typical": 0.0077, "monthly_recession": 0.011, "annual_any": 0.0887, "annual_recession": 0.1247, "annual_displacement": 0.0106, "annual_displacement_recession": 0.0152, "basis_u3_1m": 0.0012, "basis_u3_12m": 0.0094, "basis_u3_1m_any": 0.0035, "basis_u3_12m_any": 0.0268, "basis_u3_12m_deep": 0.0163, "p_pay_given_loss_1m": 0.3434, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3742, "q_12m": 0.3321},
    "professional_business": {"monthly_typical": 0.0216, "monthly_recession": 0.0256, "annual_any": 0.2301, "annual_recession": 0.2676, "annual_displacement": 0.0294, "annual_displacement_recession": 0.0349, "basis_u3_1m": 0.0005, "basis_u3_12m": -0.0, "basis_u3_1m_any": 0.0016, "basis_u3_12m_any": -0.0004, "basis_u3_12m_deep": 0.0086, "p_pay_given_loss_1m": 0.33, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.332, "q_12m": 0.3321},
    "education_health": {"monthly_typical": 0.0078, "monthly_recession": 0.009, "annual_any": 0.0898, "annual_recession": 0.1028, "annual_displacement": 0.0108, "annual_displacement_recession": 0.0124, "basis_u3_1m": 0.0002, "basis_u3_12m": 0.0018, "basis_u3_1m_any": 0.0005, "basis_u3_12m_any": 0.0052, "basis_u3_12m_deep": 0.0051, "p_pay_given_loss_1m": 0.328, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3402, "q_12m": 0.3321},
    "health_care": {"monthly_typical": 0.0075, "monthly_recession": 0.0084, "annual_any": 0.086, "annual_recession": 0.0965, "annual_displacement": 0.0103, "annual_displacement_recession": 0.0116, "basis_u3_1m": 0.0001, "basis_u3_12m": 0.0026, "basis_u3_1m_any": 0.0003, "basis_u3_12m_any": 0.0075, "basis_u3_12m_deep": 0.0046, "p_pay_given_loss_1m": 0.3266, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.344, "q_12m": 0.3321},
    "leisure_hospitality": {"monthly_typical": 0.0198, "monthly_recession": 0.0229, "annual_any": 0.213, "annual_recession": 0.2426, "annual_displacement": 0.027, "annual_displacement_recession": 0.0312, "basis_u3_1m": 0.001, "basis_u3_12m": -0.0034, "basis_u3_1m_any": 0.0029, "basis_u3_12m_any": -0.0101, "basis_u3_12m_deep": 0.0066, "p_pay_given_loss_1m": 0.3348, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3224, "q_12m": 0.3321},
    "accommodation_food": {"monthly_typical": 0.0166, "monthly_recession": 0.0196, "annual_any": 0.1819, "annual_recession": 0.2116, "annual_displacement": 0.0227, "annual_displacement_recession": 0.0268, "basis_u3_1m": 0.001, "basis_u3_12m": -0.0033, "basis_u3_1m_any": 0.003, "basis_u3_12m_any": -0.01, "basis_u3_12m_deep": 0.008, "p_pay_given_loss_1m": 0.3359, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3219, "q_12m": 0.3321},
    "other_services": {"monthly_typical": 0.0126, "monthly_recession": 0.0132, "annual_any": 0.1414, "annual_recession": 0.1477, "annual_displacement": 0.0173, "annual_displacement_recession": 0.0182, "basis_u3_1m": -0.0005, "basis_u3_12m": -0.0057, "basis_u3_1m_any": -0.0015, "basis_u3_12m_any": -0.0166, "basis_u3_12m_deep": 0.0032, "p_pay_given_loss_1m": 0.3188, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.312, "q_12m": 0.3321},
    "government": {"monthly_typical": 0.0048, "monthly_recession": 0.005, "annual_any": 0.0558, "annual_recession": 0.0579, "annual_displacement": 0.0066, "annual_displacement_recession": 0.0068, "basis_u3_1m": 0.0002, "basis_u3_12m": -0.0045, "basis_u3_1m_any": 0.0007, "basis_u3_12m_any": -0.0132, "basis_u3_12m_deep": 0.0009, "p_pay_given_loss_1m": 0.3296, "q_1m": 0.3251, "p_pay_given_loss_12m": 0.3061, "q_12m": 0.3321},
}

#: By state: corr of monthly and 12-month changes in the state's seasonally
#: adjusted unemployment rate vs national U3, Jan 2001 - Oct 2026, ex Mar
#: 2020 - Dec 2021. beta_annual = state points per national point.
STATE_UNEMPLOYMENT_BASIS: dict[str, dict[str, float]] = {
    "AL": {"monthly": 0.48, "annual": 0.928, "beta_annual": 1.094},
    "AK": {"monthly": 0.412, "annual": 0.798, "beta_annual": 0.412},
    "AZ": {"monthly": 0.491, "annual": 0.937, "beta_annual": 1.123},
    "AR": {"monthly": 0.469, "annual": 0.862, "beta_annual": 0.621},
    "CA": {"monthly": 0.605, "annual": 0.966, "beta_annual": 1.255},
    "CO": {"monthly": 0.496, "annual": 0.891, "beta_annual": 1.02},
    "CT": {"monthly": 0.469, "annual": 0.859, "beta_annual": 0.84},
    "DE": {"monthly": 0.508, "annual": 0.924, "beta_annual": 0.885},
    "DC": {"monthly": 0.397, "annual": 0.842, "beta_annual": 0.809},
    "FL": {"monthly": 0.547, "annual": 0.936, "beta_annual": 1.198},
    "GA": {"monthly": 0.534, "annual": 0.927, "beta_annual": 0.995},
    "HI": {"monthly": 0.403, "annual": 0.817, "beta_annual": 0.656},
    "ID": {"monthly": 0.517, "annual": 0.921, "beta_annual": 1.162},
    "IL": {"monthly": 0.511, "annual": 0.903, "beta_annual": 1.051},
    "IN": {"monthly": 0.515, "annual": 0.928, "beta_annual": 1.114},
    "IA": {"monthly": 0.463, "annual": 0.899, "beta_annual": 0.598},
    "KS": {"monthly": 0.523, "annual": 0.929, "beta_annual": 0.669},
    "KY": {"monthly": 0.545, "annual": 0.916, "beta_annual": 1.068},
    "LA": {"monthly": 0.133, "annual": 0.442, "beta_annual": 0.556},
    "ME": {"monthly": 0.491, "annual": 0.932, "beta_annual": 0.791},
    "MD": {"monthly": 0.499, "annual": 0.882, "beta_annual": 0.765},
    "MA": {"monthly": 0.584, "annual": 0.93, "beta_annual": 0.826},
    "MI": {"monthly": 0.534, "annual": 0.899, "beta_annual": 1.39},
    "MN": {"monthly": 0.504, "annual": 0.877, "beta_annual": 0.661},
    "MS": {"monthly": 0.265, "annual": 0.731, "beta_annual": 0.729},
    "MO": {"monthly": 0.466, "annual": 0.917, "beta_annual": 0.857},
    "MT": {"monthly": 0.49, "annual": 0.892, "beta_annual": 0.653},
    "NE": {"monthly": 0.43, "annual": 0.883, "beta_annual": 0.391},
    "NV": {"monthly": 0.477, "annual": 0.894, "beta_annual": 1.228},
    "NH": {"monthly": 0.473, "annual": 0.883, "beta_annual": 0.634},
    "NJ": {"monthly": 0.482, "annual": 0.882, "beta_annual": 1.013},
    "NM": {"monthly": 0.415, "annual": 0.814, "beta_annual": 0.698},
    "NY": {"monthly": 0.493, "annual": 0.915, "beta_annual": 0.884},
    "NC": {"monthly": 0.434, "annual": 0.912, "beta_annual": 1.246},
    "ND": {"monthly": 0.23, "annual": 0.722, "beta_annual": 0.229},
    "OH": {"monthly": 0.519, "annual": 0.917, "beta_annual": 1.024},
    "OK": {"monthly": 0.457, "annual": 0.816, "beta_annual": 0.705},
    "OR": {"monthly": 0.503, "annual": 0.93, "beta_annual": 1.185},
    "PA": {"monthly": 0.521, "annual": 0.942, "beta_annual": 0.712},
    "RI": {"monthly": 0.481, "annual": 0.878, "beta_annual": 1.092},
    "SC": {"monthly": 0.497, "annual": 0.903, "beta_annual": 1.137},
    "SD": {"monthly": 0.356, "annual": 0.858, "beta_annual": 0.391},
    "TN": {"monthly": 0.528, "annual": 0.91, "beta_annual": 1.045},
    "TX": {"monthly": 0.433, "annual": 0.903, "beta_annual": 0.827},
    "UT": {"monthly": 0.444, "annual": 0.877, "beta_annual": 1.1},
    "VT": {"monthly": 0.443, "annual": 0.882, "beta_annual": 0.568},
    "VA": {"monthly": 0.55, "annual": 0.95, "beta_annual": 0.737},
    "WA": {"monthly": 0.53, "annual": 0.898, "beta_annual": 1.033},
    "WV": {"monthly": 0.519, "annual": 0.853, "beta_annual": 0.774},
    "WI": {"monthly": 0.498, "annual": 0.919, "beta_annual": 0.958},
    "WY": {"monthly": 0.393, "annual": 0.801, "beta_annual": 0.755},
}

#: Large metros (unadjusted series, so 12-month changes only, vs unadjusted U3).
METRO_UNEMPLOYMENT_BASIS: dict[str, dict[str, float | None]] = {
    "new_york": {"monthly": None, "annual": 0.921, "beta_annual": 0.998},
    "los_angeles": {"monthly": None, "annual": 0.948, "beta_annual": 1.247},
    "chicago": {"monthly": None, "annual": 0.908, "beta_annual": 1.105},
    "dallas": {"monthly": None, "annual": 0.916, "beta_annual": 0.897},
    "houston": {"monthly": None, "annual": 0.855, "beta_annual": 0.858},
    "washington_dc": {"monthly": None, "annual": 0.927, "beta_annual": 0.647},
    "miami": {"monthly": None, "annual": 0.919, "beta_annual": 1.248},
    "philadelphia": {"monthly": None, "annual": 0.949, "beta_annual": 0.818},
    "atlanta": {"monthly": None, "annual": 0.936, "beta_annual": 1.044},
    "phoenix": {"monthly": None, "annual": 0.944, "beta_annual": 1.136},
    "san_francisco": {"monthly": None, "annual": 0.97, "beta_annual": 1.201},
    "seattle": {"monthly": None, "annual": 0.855, "beta_annual": 1.234},
    "denver": {"monthly": None, "annual": 0.892, "beta_annual": 1.072},
    "detroit": {"monthly": None, "annual": 0.893, "beta_annual": 1.602},
    "las_vegas": {"monthly": None, "annual": 0.906, "beta_annual": 1.299},
}

#: CPI regions vs national CPI-U: corr of monthly log changes (unadjusted,
#: month-of-year means removed) and of 12-month log changes, 2001-2026.
#: The nine divisions (published from Dec 2017) could not be fetched in the
#: first run; states fall back to their region until they are added.
CPI_BASIS: dict[str, dict[str, float | None]] = {
    "northeast": {"monthly": 0.895, "annual": 0.96, "beta_monthly": 0.886},
    "midwest": {"monthly": 0.918, "annual": 0.984, "beta_monthly": 1.135},
    "south": {"monthly": 0.964, "annual": 0.993, "beta_monthly": 1.095},
    "west": {"monthly": 0.891, "annual": 0.959, "beta_monthly": 0.856},
}

#: CPI metros. Most are bimonthly, so 12-month changes only. Los Angeles and
#: Washington are 2001-2017 on their pre-2018 area definitions (see FRED_MIRROR).
CPI_METRO_BASIS: dict[str, dict[str, float | None]] = {
    "new_york": {"monthly": 0.743, "annual": 0.898, "beta_monthly": 0.766},
    "los_angeles": {"monthly": 0.788, "annual": 0.885, "beta_monthly": 0.999},
    "chicago": {"monthly": 0.76, "annual": 0.949, "beta_monthly": 1.01},
    "dallas": {"monthly": None, "annual": 0.923, "beta_monthly": None},
    "houston": {"monthly": None, "annual": 0.887, "beta_monthly": None},
    "washington_dc": {"monthly": None, "annual": 0.927, "beta_monthly": None},
    "miami": {"monthly": None, "annual": 0.915, "beta_monthly": None},
    "atlanta": {"monthly": None, "annual": 0.932, "beta_monthly": None},
    "san_francisco": {"monthly": None, "annual": 0.71, "beta_monthly": None},
    "seattle": {"monthly": None, "annual": 0.882, "beta_monthly": None},
    "boston": {"monthly": None, "annual": 0.898, "beta_monthly": None},
    "philadelphia": {"monthly": None, "annual": 0.933, "beta_monthly": None},
    "detroit": {"monthly": None, "annual": 0.916, "beta_monthly": None},
}
