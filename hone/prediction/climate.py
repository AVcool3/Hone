"""Historical weather for any place: where it is, and how much it snowed.

Data comes from Open-Meteo (https://open-meteo.com), which is free and
needs no key:

* geocoding — "Aspen" -> latitude/longitude/elevation candidates
* historical archive — daily snowfall back to 1940 (ERA5 reanalysis)

Open-Meteo's free tier is for non-commercial use; a commercial launch
needs their paid API (same endpoints) or another source.

Known limitation, and why it's acceptable here: ERA5 is a ~25 km grid, so
on a mountain it UNDERSTATES absolute snowfall (it might say 2 m for a
season when the summit got 7 m). Hone never uses the absolute number. It
asks "how does this season compare with this place's own history?", and
percentiles of one consistent series are meaningful even when its level is
off. A real contract would settle on a named station or SNOTEL site, and
the quote says so.

``session`` arguments accept anything with a requests-style ``get``, which
is how the tests run offline.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEOUT = 30
#: Extra attempts when the archive drops a connection or rate-limits.
RETRIES = 3

#: First winter (by start year) pulled when building a history. 1980 gives
#: ~45 seasons: enough for a 1-in-4 event to have happened ~11 times.
FIRST_SEASON = 1980


class ClimateError(RuntimeError):
    """A weather lookup failed (network, unknown place, no data)."""


@dataclass(frozen=True)
class Place:
    name: str
    region: str       # state / province
    country: str
    latitude: float
    longitude: float
    elevation: float | None = None
    timezone: str = "auto"

    @property
    def label(self) -> str:
        return ", ".join(x for x in (self.name, self.region, self.country) if x)


def _get_json(url: str, params: dict, session: Any | None, what: str) -> dict:
    """GET with retries. Free APIs (and the network in between) drop
    connections or rate-limit under bursts; a few patient retries almost
    always get through. Raises ClimateError with ``what`` on final failure."""
    sess = session or requests
    last_exc: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            resp = sess.get(url, params=params, timeout=TIMEOUT)
            if resp.status_code == 429 and attempt < RETRIES:
                time.sleep(2.0 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # network, HTTP, bad JSON
            last_exc = exc
            if attempt < RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise ClimateError(f"{what}: {last_exc}") from last_exc


def geocode(query: str, count: int = 5, session: Any | None = None) -> list[Place]:
    """Places matching ``query``, best match first. Empty list if none."""
    query = (query or "").strip()
    if not query:
        return []
    data = _get_json(GEOCODE_URL, {"name": query, "count": count, "language": "en"},
                     session, f"Couldn't look up '{query}'")
    out = []
    for r in data.get("results") or []:
        out.append(Place(
            name=r.get("name", query), region=r.get("admin1", "") or "",
            country=r.get("country", "") or "", latitude=float(r["latitude"]),
            longitude=float(r["longitude"]), elevation=r.get("elevation"),
            timezone=r.get("timezone") or "auto",
        ))
    return out


# Archive responses are large and never change for past dates; cache them.
_CACHE: dict[tuple, pd.Series] = {}
_LOCK = threading.Lock()


def daily_snowfall(
    lat: float, lon: float, start: date, end: date, session: Any | None = None
) -> pd.Series:
    """Daily snowfall in cm, indexed by date."""
    key = (round(lat, 3), round(lon, 3), start.isoformat(), end.isoformat())
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]
    data = _get_json(ARCHIVE_URL, {
        "latitude": lat, "longitude": lon, "start_date": start.isoformat(),
        "end_date": end.isoformat(), "daily": "snowfall_sum", "timezone": "auto",
        # Pin ERA5 for the whole record. Open-Meteo's default "best match"
        # switches to a finer 9 km model from 2017, which would splice two
        # different series together and could fake a trend.
        "models": "era5",
    }, session, "Couldn't fetch snowfall history")
    try:
        daily = data["daily"]
    except (KeyError, TypeError) as exc:
        raise ClimateError(f"Snowfall history came back without daily data: {data}") from exc
    series = pd.Series(
        [float(x) if x is not None else float("nan") for x in daily["snowfall_sum"]],
        index=pd.to_datetime(daily["time"]), name="snowfall_cm",
    )
    with _LOCK:
        _CACHE[key] = series
    return series


def season_totals(
    daily: pd.Series, start_month: int = 11, end_month: int = 4, min_coverage: float = 0.95
) -> pd.Series:
    """Total snowfall per winter season, labelled by the year it starts.

    A Nov-Apr season starting in 2020 runs Nov 2020 - Apr 2021. Seasons
    with more than 5% of days missing (including the current, unfinished
    one) are dropped rather than counted as low-snow years.
    """
    if daily.empty:
        return pd.Series(dtype=float)
    m = daily.index.month
    in_season = (m >= start_month) | (m <= end_month) if start_month > end_month else (m >= start_month) & (m <= end_month)
    s = daily[in_season]
    label = s.index.year - (s.index.month <= end_month).astype(int) if start_month > end_month else s.index.year
    grouped = s.groupby(label)
    expected_days = {y: len(pd.date_range(*_season_bounds(y, start_month, end_month))) for y in grouped.groups}
    totals = {}
    for year, vals in grouped:
        if vals.notna().sum() >= min_coverage * expected_days[year]:
            totals[int(year)] = float(vals.sum(skipna=True))
    return pd.Series(totals, name="season_cm").sort_index()


def _season_bounds(year: int, start_month: int, end_month: int) -> tuple[date, date]:
    end_year = year + 1 if start_month > end_month else year
    end_day = (pd.Timestamp(end_year, end_month, 1) + pd.offsets.MonthEnd(0)).date()
    return date(year, start_month, 1), end_day


def snowfall_history(
    place: Place, start_month: int = 11, end_month: int = 4,
    first_season: int = FIRST_SEASON, today: date | None = None, session: Any | None = None,
) -> pd.Series:
    """Every complete season's total snowfall at ``place`` since ``first_season``."""
    today = today or date.today()
    start = date(first_season, start_month, 1)
    # The archive lags real time by a few days; ask up to a week ago.
    end = min(today, date.fromordinal(today.toordinal() - 7))
    daily = daily_snowfall(place.latitude, place.longitude, start, end, session=session)
    return season_totals(daily, start_month, end_month)


# ----------------------------------------------------------------- SNOTEL
#
# USDA NRCS SNOTEL: ~900 automated snow stations in the western US, on the
# mountains themselves, many with records back to the 1980s. Public, no key.
# Where one is close to a resort it beats the reanalysis grid: a study of 30
# resorts (research/prediction/findings/07_resorts.md) found the grid and
# the mountain station often disagree about WHICH seasons were bad — and a
# real snow contract would settle on a named station, so that's what to price.
SNOTEL_API = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
#: Use a station only if it's this close and has this many complete winters.
SNOTEL_MAX_KM = 35.0
SNOTEL_MIN_SEASONS = 20


@dataclass(frozen=True)
class Station:
    triplet: str          # e.g. "1101:CO:SNTL"
    name: str
    latitude: float
    longitude: float
    elevation_ft: float | None
    begin_year: int
    distance_km: float = 0.0

    @property
    def label(self) -> str:
        elev = f", {self.elevation_ft:,.0f} ft" if self.elevation_ft else ""
        return f"SNOTEL {self.name} ({self.distance_km:.0f} km away{elev})"


_STATIONS: list[dict] | None = None


def snotel_stations(session: Any | None = None) -> list[dict]:
    """All active SNOTEL stations (fetched once per process)."""
    global _STATIONS
    if _STATIONS is None:
        raw = _get_json(f"{SNOTEL_API}/stations", {"activeOnly": "true"}, session,
                        "Couldn't list snow stations")
        _STATIONS = [s for s in raw if s.get("networkCode") == "SNTL"]
    return _STATIONS


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def nearest_snotel(place: Place, today: date | None = None, session: Any | None = None) -> Station | None:
    """The closest station with a long enough record, or None."""
    today = today or date.today()
    best = None
    for s in snotel_stations(session):
        try:
            begin = int(str(s.get("beginDate", "2100"))[:4])
            d = _km(place.latitude, place.longitude, float(s["latitude"]), float(s["longitude"]))
        except (TypeError, ValueError, KeyError):
            continue
        if d <= SNOTEL_MAX_KM and today.year - begin >= SNOTEL_MIN_SEASONS and (best is None or d < best[1]):
            best = (s, d)
    if best is None:
        return None
    s, d = best
    return Station(s["stationTriplet"], s.get("name", "station"), float(s["latitude"]),
                   float(s["longitude"]), s.get("elevation"), int(str(s.get("beginDate"))[:4]), d)


def snotel_peak_swe(station: Station, today: date | None = None, session: Any | None = None) -> pd.Series:
    """Peak snow water equivalent (inches) for each complete winter,
    labelled by the year the winter starts (Oct of that year - Jun next)."""
    today = today or date.today()
    key = ("snotel", station.triplet, today.isoformat())
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]
    raw = _get_json(f"{SNOTEL_API}/data", {
        "stationTriplets": station.triplet, "elements": "WTEQ", "duration": "DAILY",
        "beginDate": f"{FIRST_SEASON}-10-01", "endDate": today.isoformat(),
    }, session, "Couldn't fetch snow-station history")
    try:
        values = raw[0]["data"][0]["values"]
    except (IndexError, KeyError, TypeError):
        values = []
    s = pd.Series({pd.Timestamp(v["date"]): float(v["value"]) for v in values
                   if v.get("value") is not None}, dtype=float)
    if s.empty:
        out = pd.Series(dtype=float, name="peak_swe_in")
    else:
        season = s.index.year - (s.index.month < 10).astype(int)
        counts = s.groupby(season).count()
        peak = s.groupby(season).max()
        # ~273 days Oct-Jun; a winter needs most of them, and must be over.
        done = peak.index < (today.year if today.month >= 7 else today.year - 1)
        out = peak[(counts >= 240) & done].sort_index().rename("peak_swe_in")
        out.index = out.index.astype(int)
    with _LOCK:
        _CACHE[key] = out
    return out
