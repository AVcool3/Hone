"""Download the data the bad-season forecaster trains on.

Three public sources, no keys:

1. **Snow**: every USDA SNOTEL station with a record back to 1990 or
   earlier (~580 stations across the western US and Alaska). For each
   winter we keep the *peak* snow water equivalent, using the monthly
   values (Jan–Jun). The monthly peak matches the daily peak that Hone's
   quotes use with correlation 0.97–0.99, and the two agree on which
   seasons were "bad" (below 70% of normal) 93–100% of the time.
2. **ONI** (NOAA CPC): the El Niño / La Niña index. A 3-month running mean
   of tropical Pacific sea-surface temperature anomalies. Positive = El Niño.
3. **PDO** (NOAA NCEI, ERSST v5): the Pacific Decadal Oscillation, a slower
   North Pacific pattern that also shifts western snow.

Run it once (≈2 minutes); results are cached in
``research/prediction/data/forecast/`` and committed, so the study is
reproducible offline:

    python research/prediction/forecast_data.py
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

OUT = Path(__file__).parent / "data" / "forecast"
SNOTEL_API = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
PDO_URL = "https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/index/ersst.v5.pdo.dat"
#: Only stations this old: a forecaster needs many ENSO events per station.
MAX_BEGIN_YEAR = 1990
BATCH = 25  # stations per request


def _get(url: str, **params):
    """GET with a few patient retries (these servers occasionally reset)."""
    for attempt in range(4):
        try:
            r = requests.get(url, params=params or None, timeout=120)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))


def stations() -> pd.DataFrame:
    raw = _get(f"{SNOTEL_API}/stations", activeOnly="true").json()
    rows = [
        {"triplet": s["stationTriplet"], "name": s.get("name"), "state": s.get("stateCode"),
         "lat": s["latitude"], "lon": s["longitude"], "elev_ft": s.get("elevation"),
         "begin": int(str(s.get("beginDate", "2100"))[:4])}
        for s in raw if s.get("networkCode") == "SNTL"
    ]
    df = pd.DataFrame(rows)
    return df[df.begin <= MAX_BEGIN_YEAR].reset_index(drop=True)


def peak_swe(st: pd.DataFrame) -> pd.DataFrame:
    """One row per (station, winter): the monthly peak SWE in inches.

    A winter is labelled by the year it STARTS (winter 2015 = Oct 2015–Jun 2016),
    the same convention as ``hone.prediction.climate.snotel_peak_swe``.
    """
    out = []
    triplets = st.triplet.tolist()
    for i in range(0, len(triplets), BATCH):
        chunk = triplets[i:i + BATCH]
        data = _get(f"{SNOTEL_API}/data", stationTriplets=",".join(chunk), elements="WTEQ",
                    duration="MONTHLY", beginDate="1980-10-01", endDate="2026-07-01").json()
        for entry in data:
            try:
                values = entry["data"][0]["values"]
            except (KeyError, IndexError, TypeError):
                continue
            v = pd.DataFrame(values)
            if v.empty or "value" not in v:
                continue
            v = v.dropna(subset=["value"])
            v = v[v.month.between(1, 6)]
            v["season"] = v.year - 1  # Jan–Jun belong to the winter that began last autumn
            g = v.groupby("season").agg(peak=("value", "max"), months=("value", "size"))
            g = g[g.months >= 5]  # need nearly all of Jan–Jun to trust the peak
            for season, row in g.iterrows():
                out.append({"triplet": entry["stationTriplet"], "season": int(season), "peak_swe_in": float(row.peak)})
        print(f"  {min(i + BATCH, len(triplets))}/{len(triplets)} stations", flush=True)
    return pd.DataFrame(out)


def oni() -> pd.DataFrame:
    """ONI as a table: one row per (3-month season, year)."""
    lines = _get(ONI_URL).text.strip().splitlines()[1:]
    rows = [ln.split() for ln in lines]
    return pd.DataFrame([{"seas": r[0], "year": int(r[1]), "anom": float(r[3])} for r in rows])


def pdo() -> pd.DataFrame:
    """PDO monthly: one row per (year, month). 99.99 means not yet published."""
    rows = []
    for ln in _get(PDO_URL).text.splitlines():
        parts = ln.split()
        if len(parts) == 13 and parts[0].isdigit():
            for m, val in enumerate(parts[1:], start=1):
                x = float(val)
                if abs(x) < 99:
                    rows.append({"year": int(parts[0]), "month": m, "pdo": x})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    st = stations()
    print(f"{len(st)} SNOTEL stations with records back to {MAX_BEGIN_YEAR}")
    st.to_csv(OUT / "snotel_stations.csv", index=False)
    oni().to_csv(OUT / "oni.csv", index=False)
    pdo().to_csv(OUT / "pdo.csv", index=False)
    peaks = peak_swe(st)
    peaks.to_csv(OUT / "snotel_peak_swe.csv.gz", index=False)
    print(f"wrote {len(peaks):,} station-winters to {OUT}")
