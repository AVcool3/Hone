"""Snow risk at 30 ski resorts: how Hone would price them, and can we trust the data?

For each resort this pulls:

* ERA5 season snowfall since 1980 (Open-Meteo) — what the quote engine
  prices from;
* for US resorts, the nearest USDA SNOTEL station's peak snow water
  equivalent (SWE) each winter — measured on the mountain, the gold
  standard for snowpack.

and reports, per resort:

* normal snowfall, year-to-year volatility, long-term trend;
* Hone's chance of a bad season (below 70% of normal) and its range;
* the fair price of $1 of bad-season protection;
* how well ERA5 agrees with the mountain station about WHICH seasons were
  bad (rank correlation, and agreement on bad seasons). High agreement
  means a quote at this resort is trustworthy; low means it isn't.

Run:  python research/prediction/resorts.py
Writes research/prediction/data/resorts/resorts_summary.csv and caches raw
downloads next to it (re-runs are offline). Findings: findings/07_resorts.md.

To add a resort, add a line to RESORTS (name, region, lat, lon).
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hone.prediction.climate import Place, snowfall_history  # noqa: E402
from hone.prediction.quote import DEFAULT_TRIGGER_FRACTION, bad_season_probability, region_of  # noqa: E402

DATA = Path(__file__).parent / "data" / "resorts"
SNOTEL_API = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
#: Only use a SNOTEL station this close to the resort, with this many seasons.
MAX_STATION_KM = 35.0
MIN_STATION_SEASONS = 20

RESORTS = [
    # Rockies
    ("Aspen Snowmass", "rockies", 39.21, -106.95), ("Vail", "rockies", 39.64, -106.37),
    ("Breckenridge", "rockies", 39.48, -106.07), ("Telluride", "rockies", 37.94, -107.81),
    ("Steamboat", "rockies", 40.46, -106.80), ("Park City", "rockies", 40.65, -111.51),
    ("Alta / Snowbird", "rockies", 40.58, -111.64), ("Jackson Hole", "rockies", 43.59, -110.83),
    ("Big Sky", "rockies", 45.28, -111.40), ("Sun Valley", "rockies", 43.70, -114.35),
    ("Taos", "rockies", 36.60, -105.45),
    # Pacific
    ("Palisades Tahoe", "pacific", 39.20, -120.24), ("Heavenly", "pacific", 38.94, -119.94),
    ("Northstar", "pacific", 39.27, -120.12), ("Mammoth", "pacific", 37.63, -119.03),
    ("Mt. Bachelor", "pacific", 43.98, -121.69), ("Crystal Mountain", "pacific", 46.94, -121.47),
    ("Mt. Baker", "pacific", 48.86, -121.68), ("Whistler", "pacific", 50.12, -122.95),
    # East / Midwest
    ("Stowe", "east", 44.53, -72.78), ("Killington", "east", 43.62, -72.80),
    ("Sugarloaf", "east", 45.03, -70.31), ("Hunter", "east", 42.20, -74.22),
    ("Snowshoe", "east", 38.41, -79.99), ("Boyne", "east", 45.16, -84.93),
    ("Lutsen", "east", 47.66, -90.71),
    # Elsewhere (no SNOTEL)
    ("Zermatt", "other", 46.02, 7.75), ("Chamonix", "other", 45.92, 6.87),
    ("St. Anton", "other", 47.13, 10.27), ("Niseko", "other", 42.86, 140.70),
]


def _km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    return 6371 * 2 * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def _cached(name: str, fetch):
    path = DATA / f"{name}.json.gz"
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()))
    out = fetch()
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(out).encode()))
    return out


def _get(url: str, params: dict | None = None, tries: int = 4):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(2 * (k + 1))


# ------------------------------------------------------------ ERA5 seasons
def era5_seasons(name: str, lat: float, lon: float, today: date) -> pd.Series:
    def fetch():
        s = snowfall_history(Place(name, "", "", lat, lon), today=today)
        return {str(k): v for k, v in s.items()}
    raw = _cached(f"era5_{name.replace(' ', '_').replace('/', '-')}", fetch)
    return pd.Series({int(k): float(v) for k, v in raw.items()}).sort_index()


# ---------------------------------------------------------- SNOTEL seasons
def snotel_stations() -> list[dict]:
    raw = _cached("snotel_stations", lambda: _get(f"{SNOTEL_API}/stations", {"activeOnly": "true"}))
    return [s for s in raw if s.get("networkCode") == "SNTL"]


def nearest_station(lat: float, lon: float, stations: list[dict]) -> tuple[dict, float] | None:
    best = None
    for s in stations:
        d = _km(lat, lon, s["latitude"], s["longitude"])
        begin = int(str(s.get("beginDate", "2100"))[:4])
        if d <= MAX_STATION_KM and date.today().year - begin >= MIN_STATION_SEASONS:
            if best is None or d < best[1]:
                best = (s, d)
    return best


def snotel_peak_swe(triplet: str) -> pd.Series:
    """Peak snow water equivalent (inches) per winter, labelled by the
    year the winter starts (Oct of that year to Jun of the next)."""
    def fetch():
        return _get(f"{SNOTEL_API}/data", {
            "stationTriplets": triplet, "elements": "WTEQ", "duration": "DAILY",
            "beginDate": "1980-10-01", "endDate": date.today().isoformat(),
        })
    raw = _cached(f"snotel_{triplet.replace(':', '_')}", fetch)
    values = raw[0]["data"][0]["values"] if raw and raw[0].get("data") else []
    s = pd.Series({pd.Timestamp(v["date"]): v.get("value") for v in values if v.get("value") is not None}, dtype=float)
    if s.empty:
        return s
    season = s.index.year - (s.index.month < 10).astype(int)
    counts = s.groupby(season).count()
    peak = s.groupby(season).max()
    # A winter needs most of its days (Oct-Jun = ~273) to count.
    return peak[counts >= 240].sort_index()


# ----------------------------------------------------------------- per resort
def analyse(name, region, lat, lon, stations, today) -> dict:
    era = era5_seasons(name, lat, lon, today)
    normal = float(era.median())
    trigger = DEFAULT_TRIGGER_FRACTION * normal
    current = today.year if today.month >= 11 else today.year - 1
    prob, _ = bad_season_probability(era, trigger, current + (0 if today.month >= 11 else 1))
    row = {
        "resort": name, "region": region, "lat": lat, "lon": lon,
        "engine_region": region_of(lat, lon),
        "seasons": len(era), "normal_cm": round(normal, 1),
        "cv": round(float(era.std() / era.mean()), 3),
        "worst_season": int(era.idxmin()), "worst_pct_of_normal": round(float(era.min() / normal), 2),
        "p_bad": round(prob.estimate, 3), "p_bad_low": round(prob.low, 3), "p_bad_high": round(prob.high, 3),
        "p_bad_historical": round(prob.historical, 3),
        "trend_cm_per_decade": round(prob.trend_cm_per_decade, 1), "trend_p": round(prob.trend_p_value, 3),
        "fair_price_per_dollar": round(prob.estimate, 3),
    }
    near = nearest_station(lat, lon, stations) if region != "other" else None
    if near:
        st, dist = near
        swe = snotel_peak_swe(st["stationTriplet"])
        both = pd.concat([era.rename("era"), swe.rename("swe")], axis=1, join="inner").dropna()
        row.update({"station": st["name"], "station_km": round(dist, 1),
                    "station_elev_ft": st.get("elevation"), "overlap_seasons": len(both)})
        if len(both) >= 10:
            rho = stats.spearmanr(both.era, both.swe).statistic
            bad_e = both.era < DEFAULT_TRIGGER_FRACTION * both.era.median()
            bad_s = both.swe < DEFAULT_TRIGGER_FRACTION * both.swe.median()
            caught = (bad_e & bad_s).sum() / max(bad_s.sum(), 1)       # station-bad seasons ERA5 also calls bad
            false = (bad_e & ~bad_s).sum() / max(bad_e.sum(), 1)       # ERA5-bad seasons the station didn't see
            prob_s, _ = bad_season_probability(both.swe, DEFAULT_TRIGGER_FRACTION * both.swe.median(), current)
            row.update({
                "rank_corr_era5_vs_station": round(float(rho), 2),
                "station_bad_seasons": int(bad_s.sum()), "era5_bad_seasons": int(bad_e.sum()),
                "share_station_bad_caught": round(float(caught), 2),
                "share_era5_bad_false_alarm": round(float(false), 2),
                "p_bad_station": round(prob_s.estimate, 3),
            })
    return row


def main() -> None:
    today = date.today()
    stations = snotel_stations()
    rows = []
    for name, region, lat, lon in RESORTS:
        # Open-Meteo's free tier weighs a 45-year daily request heavily and
        # answers 429 under bursts; cached resorts cost nothing, others wait.
        for attempt in range(6):
            try:
                rows.append(analyse(name, region, lat, lon, stations, today))
                print(f"ok  {name}", flush=True)
                break
            except Exception as exc:  # keep going; report what failed
                if attempt == 5:
                    print(f"ERR {name}: {exc}", flush=True)
                else:
                    time.sleep(30 * (attempt + 1))
        time.sleep(0.5)
    df = pd.DataFrame(rows)
    DATA.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA / "resorts_summary.csv", index=False)
    pd.set_option("display.width", 220)
    cols = ["resort", "region", "normal_cm", "cv", "p_bad", "p_bad_low", "p_bad_high", "trend_cm_per_decade",
            "trend_p", "worst_season", "worst_pct_of_normal", "station", "station_km",
            "rank_corr_era5_vs_station", "share_station_bad_caught", "share_era5_bad_false_alarm", "p_bad_station"]
    print(df[[c for c in cols if c in df]].to_string(index=False))


if __name__ == "__main__":
    main()
