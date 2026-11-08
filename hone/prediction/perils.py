"""Weather risks ("perils") Hone can price, and where their history comes from.

Each peril says what to measure, over which months, and which direction
hurts. The quote engine (quote.py) is otherwise the same for all of them:
history -> chance of a bad season -> typical loss -> price -> size.

    peril          measured as                            bad when
    snow           season snowfall (Nov-Apr)              too little
    rain_summer    rainy days, 2.5+ mm (May-Sep)          too many
    rain_work      days with 5+ mm of rain (Mar-Nov)      too many
    heat           days over 32 C (Jun-Aug)               too many
    cool_summer    days over 30 C (Jun-Aug)               too few
    spring_frost   nights at or below -2 C (Apr-May)      too many
    drought        rainfall (May-Aug)                     too little

Where the history comes from, best first (``history``):
  1. snow only, western US: a USDA SNOTEL station on the mountain
  2. a NOAA GHCN station within 40 km with a long, current record
  3. the ERA5 reanalysis grid (Open-Meteo), available everywhere

To add a peril, add an entry to PERILS; to use it, give a Business in
quote.py ``peril="<key>"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from .climate import (
    ClimateError, Place, era5_daily, nearest_snotel, noaa_seasonal, seasonal_index,
    snotel_peak_swe, snowfall_history,
)

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


@dataclass(frozen=True)
class Peril:
    key: str
    label: str              # "Low snowfall"
    element: str            # NOAA element: SNOW, PRCP, TMAX, TMIN
    months: tuple[int, int]
    how: str                # "sum" | "count_above" | "count_below"
    threshold: float | None
    high_is_bad: bool
    unit: str               # what one index point is: "cm of snowfall", "rainy days"
    scale: float = 1.0      # NOAA/ERA5 metric value -> unit (snow mm -> cm = 0.1)
    worse_word: str = ""    # "less snow", "more rainy days" — for "x% ___ than normal"

    @property
    def season_label(self) -> str:
        return f"{MONTHS[self.months[0] - 1]}–{MONTHS[self.months[1] - 1]}"

    def condition(self, trigger: float, unit: str | None = None) -> str:
        """Plain English for 'the bad season happens', e.g. 'has more than
        41 rainy days (May–Sep)'."""
        import math

        u = unit or self.unit
        if self.how.startswith("count"):
            # Whole days/nights: say the first count that's bad. Bad is
            # "more than T" when too many hurts, "fewer than T" otherwise.
            if self.high_is_bad:
                return f"has {math.floor(trigger) + 1:,} or more {u} ({self.season_label})"
            return f"has {max(math.ceil(trigger) - 1, 0):,} or fewer {u} ({self.season_label})"
        amount = f"{trigger:,.0f}" if trigger >= 100 else f"{trigger:,.1f}"
        verb = "gets more than" if self.high_is_bad else "gets less than"
        return f"{verb} {amount} {u} ({self.season_label})"


PERILS = {p.key: p for p in [
    Peril("snow", "Low snowfall", "SNOW", (11, 4), "sum", None, False, "cm of snowfall", 0.1, "less snow"),
    Peril("rain_summer", "Rainy summer", "PRCP", (5, 9), "count_above", 2.5, True, "rainy days", 1.0, "more rainy days"),
    Peril("rain_work", "Wet working season", "PRCP", (3, 11), "count_above", 5.0, True,
          "days with 5+ mm of rain", 1.0, "more rain-stopped days"),
    Peril("heat", "Hot summer", "TMAX", (6, 8), "count_above", 32.0, True, "days over 32°C", 1.0, "more very hot days"),
    Peril("cool_summer", "Cool summer", "TMAX", (6, 8), "count_above", 30.0, False, "days over 30°C", 1.0, "fewer hot days"),
    Peril("spring_frost", "Late spring frost", "TMIN", (4, 5), "count_below", -2.0, True,
          "nights at or below −2°C", 1.0, "more frost nights"),
    Peril("drought", "Dry growing season", "PRCP", (5, 8), "sum", None, False, "mm of rain", 1.0, "less rain"),
]}


@dataclass
class History:
    values: pd.Series       # one number per season, labelled by start year
    unit: str
    source: str             # "SNOTEL ...", "NOAA station ...", "ERA5 ..."
    settles_on_station: bool


def history(peril: Peril, place: Place, index: str = "auto", today: date | None = None,
            session: Any | None = None, min_seasons: int = 10) -> History:
    """Season-by-season history of ``peril`` at ``place`` from the best source.

    index: "auto" (best available), "station" (SNOTEL or NOAA only — error
    if neither), "era5" (the grid only).
    """
    if index not in ("auto", "era5", "station"):
        raise ValueError("index must be 'auto', 'era5' or 'station'")
    today = today or date.today()
    from .quote import region_of  # local import: quote imports this module

    if index != "era5":
        # 1. SNOTEL peak snow water, western US mountains
        if peril.key == "snow" and region_of(place.latitude, place.longitude) != "other":
            try:
                st = nearest_snotel(place, today=today, session=session)
                if st is not None:
                    swe = snotel_peak_swe(st, today=today, session=session)
                    if len(swe) >= min_seasons:
                        return History(swe, "in. of snow water (season peak)", st.label, True)
            except ClimateError:
                pass
        # 2. NOAA station with a long, current record of this measurement
        try:
            found = noaa_seasonal(place, peril.element, peril.months, peril.how, peril.threshold,
                                  today=today, session=session, min_seasons=max(min_seasons, 20))
        except ClimateError:
            found = None
        if found is not None:
            st, idx = found
            return History(idx * peril.scale, peril.unit, st.label, True)
        if index == "station":
            raise ValueError("No weather station with a long, current record near this place.")
    # 3. The ERA5 grid
    if peril.key == "snow":
        s = snowfall_history(place, *peril.months, today=today, session=session)  # already cm
        return History(s, peril.unit, "ERA5 reanalysis snowfall (~25 km grid)", False)
    daily = era5_daily(place, peril.element, today=today, session=session)
    idx = seasonal_index(daily, peril.months, peril.how, peril.threshold, today=today)
    return History(idx * peril.scale, peril.unit, "ERA5 reanalysis (~25 km grid)", False)
