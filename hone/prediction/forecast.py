"""Bad-season forecaster: how El Niño / La Niña and the PDO shift a place's odds.

Hone normally prices a bad snow season from the place's own history: "11 of
the last 45 winters were bad, so about 25%". But the tropical Pacific tilts
the odds before a winter starts. El Niño tends to starve the northern West
(Washington, Montana) of snow and feed the Southwest; La Niña does the
opposite. This module learns *how much* from 25,000 station-winters at
~580 USDA SNOTEL stations, 1980–2025, and turns that into a shift of the
historical probability.

The model, in one line:

    log-odds(bad) = log-odds(this place's history) + shift(region, ONI, PDO)

- ``log-odds(history)`` is the "offset": Hone's usual estimate. The model
  never replaces it, it only nudges it.
- ``shift`` is linear in El Niño strength (``ONI`` above 0), La Niña
  strength (``ONI`` below 0, a separate slope because the two aren't
  mirror images), and the PDO. Each slope = a West-wide value plus a
  regional adjustment, all shrunk toward zero (ridge), so a region with few
  stations borrows from the West-wide value.
- A time trend is fitted alongside (so the PDO's recent negative run isn't
  mistaken for climate change) but is NOT applied here: the quote engine
  already handles trends its own way.

Why this shape: it was tested against a gradient-boosted model, spatial
smoothers and others in ``research/prediction/forecast_study.py`` (findings
in ``research/prediction/findings/10_forecast.md``), predicting whole
held-out winters. Only the regions where the shift beat plain history in
that test are adjusted at all (``SKILLFUL_REGIONS``, set from the study).

To retrain: run the study with ``--save``; it rewrites
``hone/prediction/data/forecast_snow.json``, which is all this module
reads. Nothing here downloads training data.
"""

from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

# ------------------------------------------------------------------ regions
#: SNOTEL states grouped into regions whose snow responds alike to ENSO.
#: Change the grouping here, then retrain (the study reads this table).
REGION_OF_STATE = {
    "WA": "pacific_northwest", "OR": "pacific_northwest",
    "ID": "northern_rockies", "MT": "northern_rockies", "WY": "northern_rockies", "SD": "northern_rockies",
    "CA": "sierra_great_basin", "NV": "sierra_great_basin",
    "UT": "utah",
    "CO": "colorado",
    "AZ": "southwest", "NM": "southwest",
    "AK": "alaska",
}
REGIONS = sorted(set(REGION_OF_STATE.values()))
REGION_LABEL = {
    "pacific_northwest": "the Pacific Northwest",
    "northern_rockies": "the northern Rockies",
    "sierra_great_basin": "the Sierra Nevada and Great Basin",
    "utah": "Utah",
    "colorado": "Colorado",
    "southwest": "the Southwest",
    "alaska": "Alaska",
}
#: A place is assigned the region of the nearest training station, if one
#: is within this distance; farther away (e.g. Vermont) no shift is applied.
MAX_STATION_KM = 150.0

#: The signals, and which months of the season's start year they're read
#: from. ONI "ASO" = the Aug–Sep–Oct average, published in early November,
#: just before the snow season. PDO = mean of Sep and Oct.
ONI_SEASON = "ASO"
PDO_MONTHS = (9, 10)
#: ONI windows that are "late enough" to use for the coming winter: El Niño
#: usually locks in by late summer. Earlier than this, the shift is skipped.
ONI_USABLE = ("JAS", "ASO", "SON", "OND", "NDJ", "DJF")

#: Where the coefficients live (written by the study's --save).
MODEL_PATH = Path(__file__).parent / "data" / "forecast_snow.json"


# ------------------------------------------------------------ the features
def features(oni: float, pdo: float, region: str) -> np.ndarray:
    """The design row for one winter at one place.

    Layout: [baseline, El Niño, La Niña, PDO] West-wide, then the same four
    for each region in ``REGIONS`` (zeros except the place's own region).
    El Niño strength = max(ONI, 0); La Niña strength = max(-ONI, 0), so both
    are positive numbers and their coefficients read the same way.

    The "baseline" column (always 1) matters: El Niño and La Niña can BOTH
    mean fewer bad winters than a neutral year (Colorado does this). Without
    a baseline the model could only say "every year with a signal is
    better", which drags the average below the place's history.
    """
    base = np.array([1.0, max(oni, 0.0), max(-oni, 0.0), pdo])
    row = [base]
    for r in REGIONS:
        row.append(base if r == region else np.zeros(N_SIGNALS))
    return np.concatenate(row)


#: Columns per block in ``features`` (baseline, El Niño, La Niña, PDO).
N_SIGNALS = 4
SIGNAL_NAMES = ("baseline", "el_nino", "la_nina", "pdo")


def feature_names() -> list[str]:
    return [f"{scope}:{sig}" for scope in ["west", *REGIONS] for sig in SIGNAL_NAMES]


# ------------------------------------------------------------- the fitting
def fit_offset_logit(X: np.ndarray, y: np.ndarray, offset: np.ndarray, l2: np.ndarray,
                     iters: int = 50) -> np.ndarray:
    """Ridge logistic regression with a fixed offset, by Newton's method.

    Maximizes  sum[y·η − log(1+e^η)] − ½·Σ l2_j·β_j²  with  η = offset + Xβ.
    ``l2`` is one penalty per column (larger = shrunk harder toward 0).
    sklearn's LogisticRegression can't take an offset, hence this ~15 lines.
    """
    beta = np.zeros(X.shape[1])
    lam = np.diag(l2)
    for _ in range(iters):
        eta = offset + X @ beta
        p = 1.0 / (1.0 + np.exp(-eta))
        grad = X.T @ (y - p) - l2 * beta
        hess = (X * (p * (1 - p))[:, None]).T @ X + lam
        step = np.linalg.solve(hess, grad)
        beta += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return beta


def logit(p: np.ndarray | float) -> np.ndarray | float:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def expit(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


# ----------------------------------------------------------- the live model
@dataclass
class Signals:
    """The climate signals for the coming winter, as published."""

    oni: float
    oni_window: str      # e.g. "ASO 2026"
    pdo: float
    pdo_window: str      # e.g. "Sep–Oct 2026"
    usable: bool         # late enough in the year to tilt the coming winter
    note: str = ""


@dataclass
class Shift:
    """What the forecaster did to one quote's probability."""

    applied: bool
    probability_before: float
    probability_after: float
    region: str = ""
    region_label: str = ""
    odds_ratio: float = 1.0
    signals: dict = field(default_factory=dict)
    explanation: str = ""
    #: the held-out test result for this region, so the UI can show its evidence
    evidence: str = ""
    #: the most similar past winters in this region: [{season, oni, pdo, bad_share}]
    analogs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_MODEL: dict | None = None


def load_model(path: Path = MODEL_PATH) -> dict | None:
    """The saved coefficients, or None if the study hasn't been run."""
    global _MODEL
    if _MODEL is None and path.exists():
        _MODEL = json.loads(path.read_text())
    return _MODEL


def region_for(lat: float, lon: float, model: dict | None = None) -> tuple[str | None, float]:
    """(region, km to the nearest training station), or (None, km) if too far."""
    model = model or load_model()
    if not model:
        return None, math.inf
    best = (None, math.inf)
    for s in model["stations"]:
        p1, p2 = math.radians(lat), math.radians(s[0])
        dp, dl = p2 - p1, math.radians(s[1] - lon)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        d = 2 * 6371.0 * math.asin(math.sqrt(a))
        if d < best[1]:
            best = (s[2], d)
    return (best[0], best[1]) if best[1] <= MAX_STATION_KM else (None, best[1])


def shift_probability(p: float, lat: float, lon: float, signals: Signals | None,
                      model: dict | None = None) -> Shift:
    """Tilt a history-based bad-season probability by this winter's signals.

    Returns the probability unchanged (``applied=False``, with the reason in
    ``explanation``) whenever the model has no tested skill for this place,
    the signals are missing or too early, or the model file is absent.
    """
    model = model or load_model()
    same = lambda why, **kw: Shift(False, p, p, explanation=why, **kw)
    if not model:
        return same("The El Niño forecaster hasn't been trained on this install.")
    if signals is None:
        return same("Couldn't fetch this year's El Niño and PDO readings, so the price uses history alone.")
    region, km = region_for(lat, lon, model)
    if region is None:
        return same("The El Niño forecaster is trained on western US and Alaska snow stations; "
                    f"the nearest is {km:,.0f} km away, so the price uses history alone.")
    label = REGION_LABEL.get(region, region)
    sig = asdict(signals)
    if not signals.usable:
        return same(f"It's too early in the year to read El Niño for the coming winter "
                    f"(latest reading: {signals.oni_window}); the price uses history alone.",
                    region=region, region_label=label, signals=sig)
    info = model["regions"].get(region, {})
    if not info.get("skillful"):
        return same(f"In testing on past winters, El Niño and the PDO didn't predict bad seasons "
                    f"in {label} better than history alone, so the price uses history alone.",
                    region=region, region_label=label, signals=sig, evidence=info.get("evidence", ""))
    # Clip to the range the model has seen: 2026's ONI (2.46) is stronger
    # than any winter since 1980, and a straight line shouldn't be trusted
    # beyond its data.
    lo, hi = model["oni_range"]
    oni = float(np.clip(signals.oni, lo, hi))
    plo, phi = model["pdo_range"]
    pdo = float(np.clip(signals.pdo, plo, phi))
    beta = np.array(model["coef"])
    delta = float(features(oni, pdo, region) @ beta)
    # Cap the tilt: no single climate signal should move odds more than 3x.
    delta = float(np.clip(delta, -math.log(3), math.log(3)))
    after = float(expit(logit(p) + delta))
    analogs = similar_winters(region, signals.oni, signals.pdo, model)
    phase = ("El Niño" if signals.oni >= 0.5 else "La Niña" if signals.oni <= -0.5 else "neutral Pacific")
    direction = "raises" if after > p else "lowers"
    text = (f"{signals.oni_window} shows {phase} conditions (ONI {signals.oni:+.1f}) and a PDO of "
            f"{signals.pdo:+.1f}. In {label}, winters like this have had fewer bad seasons than usual"
            if after < p else
            f"{signals.oni_window} shows {phase} conditions (ONI {signals.oni:+.1f}) and a PDO of "
            f"{signals.pdo:+.1f}. In {label}, winters like this have had more bad seasons than usual")
    text += f", so Hone {direction} the chance of a bad winter from {p:.0%} (history alone) to {after:.0%}."
    if oni != signals.oni:
        text += (f" This ONI is beyond anything since {model['seasons'][0]}, so Hone uses the effect "
                 f"of the strongest past reading ({oni:+.1f}) rather than extend the line.")
    if analogs:
        text += " Most similar past winters here: " + ", ".join(
            f"{a['season']}–{str(a['season'] + 1)[-2:]} ({a['bad_share']:.0%} of stations bad)" for a in analogs) + "."
    return Shift(True, p, after, region, label, float(math.exp(delta)), sig, text,
                 info.get("evidence", ""), analogs)


def similar_winters(region: str, oni: float, pdo: float, model: dict | None = None, k: int = 3) -> list[dict]:
    """The k past winters in a region closest in (ONI, PDO), with how many of
    the region's stations had a bad winter. ONI counts twice as much as PDO
    (it's the stronger signal), so distance = sqrt((2·ΔONI)² + ΔPDO²)."""
    model = model or load_model()
    winters = (model or {}).get("winters", {}).get(region, {})
    scored = sorted(
        ((math.hypot(2 * (v[0] - oni), v[1] - pdo), int(s), v) for s, v in winters.items()),
        key=lambda t: t[0],
    )[:k]
    return [{"season": s, "oni": v[0], "pdo": v[1], "bad_share": v[2]} for _, s, v in scored]


# ---------------------------------------------------- the live climate data
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
PDO_URL = "https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/index/ersst.v5.pdo.dat"
#: (fetched at, (oni rows, pdo rows) or None)
_SIGNALS: tuple[float, tuple | None] | None = None
_LOCK = threading.Lock()
SIGNALS_TTL = 6 * 3600  # these indices update monthly; six hours is plenty
MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def parse_oni(text: str) -> list[tuple[str, int, float]]:
    out = []
    for ln in text.strip().splitlines()[1:]:
        parts = ln.split()
        if len(parts) >= 4:
            try:
                out.append((parts[0], int(parts[1]), float(parts[3])))
            except ValueError:
                continue
    return out


def parse_pdo(text: str) -> list[tuple[int, int, float]]:
    out = []
    for ln in text.splitlines():
        parts = ln.split()
        if len(parts) == 13 and parts[0].isdigit():
            for m, v in enumerate(parts[1:], start=1):
                x = float(v)
                if abs(x) < 99:  # 99.99 = not yet published
                    out.append((int(parts[0]), m, x))
    return out


def winter_of(seas: str, yr: int) -> int:
    """Which winter (labelled by its start year) an ONI window describes.
    NDJ and DJF are labelled with the January year but belong to the winter
    that began the autumn before."""
    return yr - 1 if seas in ("NDJ", "DJF") else yr


def signals_from(oni_rows, pdo_rows, today: date, season_year: int | None = None) -> Signals | None:
    """The readings that bear on the winter that starts in ``season_year``
    (default: this year's, or the one under way in Jan–Jun). Pure function,
    so tests can feed it text."""
    if not oni_rows or not pdo_rows:
        return None
    if season_year is None:
        season_year = today.year if today.month >= 7 else today.year - 1
    seas, yr, oni = oni_rows[-1]
    # Usable only if the latest reading is late enough AND about this winter
    # (in March, the latest reading describes the winter that's ending, not
    # the next one).
    usable = seas in ONI_USABLE and winter_of(seas, yr) == season_year
    # Prefer the exact window the model was trained on, when it's out.
    for s, y, v in reversed(oni_rows):
        if s == ONI_SEASON and y == season_year:
            seas, yr, oni = s, y, v
            break
    recent = [r for r in pdo_rows if (r[0], r[1]) <= (today.year, today.month)][-2:]
    pdo = float(np.mean([r[2] for r in recent]))
    pdo_window = "–".join(f"{MONTH[m - 1]}" for _, m, _ in recent) + f" {recent[-1][0]}"
    return Signals(oni=oni, oni_window=f"{seas} {yr}", pdo=pdo, pdo_window=pdo_window, usable=usable)


def current_signals(today: date | None = None, session: Any | None = None,
                    season_year: int | None = None) -> Signals | None:
    """The latest ONI and PDO for the coming winter; None if they can't be
    fetched. The raw files are cached for six hours (a failed fetch for ten
    minutes, so a blip doesn't switch the forecaster off all afternoon)."""
    global _SIGNALS
    today = today or date.today()
    with _LOCK:
        cached = _SIGNALS
    if cached and time.time() - cached[0] < (SIGNALS_TTL if cached[1] else 600):
        rows = cached[1]
    else:
        import requests

        http = session or requests
        try:
            rows = (parse_oni(http.get(ONI_URL, timeout=20).text),
                    parse_pdo(http.get(PDO_URL, timeout=20).text))
        except Exception:
            rows = None
        with _LOCK:
            _SIGNALS = (time.time(), rows)
    return signals_from(*rows, today, season_year) if rows else None
