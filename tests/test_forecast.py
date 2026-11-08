"""The El Niño / PDO bad-season forecaster (hone/prediction/forecast.py).

What these tests pin down:
- the fitting routine recovers known coefficients (so the study's numbers
  mean what they say);
- climate readings are matched to the RIGHT winter (a March reading is
  about the winter that's ending, not the next one);
- the forecaster leaves the price alone wherever it has no tested skill,
  and never moves odds more than 3x where it does;
- the saved model file is consistent with its own test results.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pytest

from hone.prediction import climate, forecast as fc
from hone.prediction.quote import quote

from test_quote import FakeWeather, _steady  # reuse the fake weather service


# ------------------------------------------------------------ the fitting
def test_offset_logit_recovers_known_coefficients():
    rng = np.random.default_rng(1)
    n = 40_000
    X = rng.normal(size=(n, 2))
    offset = rng.normal(-1.5, 0.5, n)                 # each row's "history" log-odds
    true = np.array([0.8, -0.5])
    y = (rng.random(n) < fc.expit(offset + X @ true)).astype(float)
    beta = fc.fit_offset_logit(X, y, offset, np.array([1e-6, 1e-6]))
    assert beta == pytest.approx(true, abs=0.05)


def test_ridge_penalty_shrinks_toward_zero():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(500, 1))
    y = (rng.random(500) < fc.expit(X[:, 0])).astype(float)
    loose = fc.fit_offset_logit(X, y, np.zeros(500), np.array([0.0]))
    tight = fc.fit_offset_logit(X, y, np.zeros(500), np.array([1e4]))
    assert abs(tight[0]) < 0.1 * abs(loose[0])


def test_feature_layout_matches_names():
    row = fc.features(1.5, -0.7, "colorado")
    names = fc.feature_names()
    assert len(row) == len(names) == fc.N_SIGNALS * (1 + len(fc.REGIONS))
    vals = dict(zip(names, row))
    assert vals["west:baseline"] == 1 and vals["colorado:baseline"] == 1 and vals["utah:baseline"] == 0
    assert vals["colorado:el_nino"] == 1.5 and vals["colorado:la_nina"] == 0
    assert vals["colorado:pdo"] == -0.7
    la = dict(zip(names, fc.features(-1.2, 0.0, "utah")))
    assert la["utah:la_nina"] == 1.2 and la["utah:el_nino"] == 0


# ------------------------------------------------- reading the live indices
ONI_TEXT = """ SEAS  YR   TOTAL   ANOM
  JJA 2026  28.10   1.80
  JAS 2026  28.40   2.16
  ASO 2026  28.70   2.46
"""
PDO_TEXT = """ Year   Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
 2026 -1.24 -1.00 -1.42 -1.62 -1.68 -1.72 -2.16 -1.88 -1.52 -2.26 99.99 99.99
"""


def test_parsers_skip_unpublished_months():
    assert fc.parse_oni(ONI_TEXT)[-1] == ("ASO", 2026, 2.46)
    pdo = fc.parse_pdo(PDO_TEXT)
    assert len(pdo) == 10 and pdo[-1] == (2026, 10, -2.26)


def test_november_reading_is_for_the_coming_winter():
    sig = fc.signals_from(fc.parse_oni(ONI_TEXT), fc.parse_pdo(PDO_TEXT), date(2026, 11, 8))
    assert sig.usable and sig.oni == 2.46 and sig.oni_window == "ASO 2026"
    assert sig.pdo == pytest.approx((-1.52 - 2.26) / 2)


def test_summer_reading_is_too_early():
    rows = fc.parse_oni(" SEAS YR TOTAL ANOM\n  MJJ 2026 28 1.39\n")
    sig = fc.signals_from(rows, fc.parse_pdo(PDO_TEXT), date(2026, 7, 20))
    assert not sig.usable


def test_march_reading_describes_the_winter_ending_not_the_next():
    rows = fc.parse_oni(" SEAS YR TOTAL ANOM\n  DJF 2027 28 2.0\n")
    assert fc.winter_of("DJF", 2027) == 2026
    # Still usable for the winter under way...
    assert fc.signals_from(rows, fc.parse_pdo(PDO_TEXT), date(2027, 3, 1), season_year=2026).usable
    # ...but not for pricing next winter (2027-28).
    assert not fc.signals_from(rows, fc.parse_pdo(PDO_TEXT), date(2027, 3, 1), season_year=2027).usable


# --------------------------------------------------------- shifting odds
def _model(skillful=True):
    """A tiny hand-made model: El Niño lowers the odds in 'southwest'."""
    coef = np.zeros(len(fc.feature_names()))
    coef[fc.feature_names().index("southwest:el_nino")] = -0.5
    return {
        "coef": coef.tolist(), "oni_range": [-1.5, 2.0], "pdo_range": [-2.5, 2.0],
        "n_station_winters": 1000, "seasons": [1980, 2025],
        "stations": [[35.5, -105.5, "southwest"], [40.0, -106.0, "colorado"]],
        "regions": {"southwest": {"skillful": skillful, "evidence": "tested"},
                    "colorado": {"skillful": False, "evidence": "no skill"}},
        "winters": {"southwest": {"1997": [2.04, 1.79, 0.0], "2015": [2.02, 0.9, 0.12], "1999": [-1.0, -2.4, 0.68]}},
    }


SIG = fc.Signals(oni=1.0, oni_window="ASO 2026", pdo=0.0, pdo_window="Sep–Oct 2026", usable=True)


def test_shift_in_a_skillful_region():
    s = fc.shift_probability(0.30, 35.6, -105.4, SIG, _model())
    assert s.applied and s.region == "southwest"
    expect = fc.expit(fc.logit(0.30) - 0.5)
    assert s.probability_after == pytest.approx(expect)
    assert s.odds_ratio == pytest.approx(math.exp(-0.5))
    assert "lowers" in s.explanation and "30%" in s.explanation
    assert s.analogs[0]["season"] in (1997, 2015)


def test_no_shift_without_tested_skill():
    s = fc.shift_probability(0.30, 40.0, -106.0, SIG, _model())     # colorado: not skillful
    assert not s.applied and s.probability_after == 0.30
    assert "history alone" in s.explanation
    assert not fc.shift_probability(0.30, 35.6, -105.4, SIG, _model(skillful=False)).applied


def test_no_shift_far_from_training_stations_or_without_signals():
    assert not fc.shift_probability(0.30, 44.5, -72.8, SIG, _model()).applied      # Vermont
    assert not fc.shift_probability(0.30, 35.6, -105.4, None, _model()).applied
    early = fc.Signals(1.0, "MJJ 2026", 0.0, "May–Jun 2026", usable=False)
    assert "too early" in fc.shift_probability(0.30, 35.6, -105.4, early, _model()).explanation


def test_extreme_readings_are_clipped_and_odds_capped():
    m = _model()
    big = fc.Signals(oni=3.0, oni_window="ASO 2026", pdo=0.0, pdo_window="", usable=True)
    s = fc.shift_probability(0.30, 35.6, -105.4, big, m)
    # ONI clipped to the training max (2.0): shift = -0.5 * 2.0 = -1.0
    assert s.probability_after == pytest.approx(fc.expit(fc.logit(0.30) - 1.0))
    assert "beyond anything since 1980" in s.explanation
    # A huge coefficient still can't move the odds more than 3x.
    m["coef"][fc.feature_names().index("southwest:el_nino")] = -10.0
    s = fc.shift_probability(0.30, 35.6, -105.4, SIG, m)
    assert s.odds_ratio == pytest.approx(1 / 3)


# ------------------------------------------------------ the saved model
def test_saved_model_is_consistent_with_its_own_tests():
    m = fc.load_model()
    assert m is not None, "run: python research/prediction/forecast_study.py --save"
    assert len(m["coef"]) == len(fc.feature_names()) and m["features"] == fc.feature_names()
    for r, info in m["regions"].items():
        # "skillful" must mean it beat history in BOTH held-out tests.
        assert info["skillful"] == (info["bss_5"] > 0 and info["bss_forward"] > 0), r
    assert m["n_station_winters"] > 20_000
    assert m["oni_range"][0] < -1 and m["oni_range"][1] > 1.5


# ------------------------------------------------------ inside a quote
@pytest.fixture
def taos_weather():
    climate._CACHE.clear()
    climate._STATIONS = None
    return FakeWeather({"Taos Ski Valley": (36.58, -105.45)}, {(36.58, -105.45): _steady()})


def test_quote_uses_the_forecast_where_it_has_skill(taos_weather, monkeypatch):
    model = _model()
    model["stations"] = [[36.6, -105.5, "southwest"]]
    monkeypatch.setattr(fc, "_MODEL", model)
    monkeypatch.setattr(fc, "current_signals", lambda *a, **k: SIG)
    with_fc = quote("ski_resort", "Taos Ski Valley", 5_000_000, index="era5", today=date(2026, 11, 7), session=taos_weather)
    without = quote("ski_resort", "Taos Ski Valley", 5_000_000, index="era5", today=date(2026, 11, 7),
                    session=taos_weather, forecast=False)
    assert with_fc.forecast["applied"] and without.forecast is None
    assert with_fc.fair_price < without.fair_price
    assert with_fc.fair_price == pytest.approx(with_fc.forecast["probability_after"])
    assert any("El Niño" in a for a in with_fc.assumptions)
    # The history itself is unchanged: only the odds for the coming winter move.
    assert with_fc.probability.estimate == without.probability.estimate


def test_non_snow_quotes_skip_the_forecaster(taos_weather, monkeypatch):
    called = []
    monkeypatch.setattr(fc, "current_signals", lambda *a, **k: called.append(1) or SIG)
    q = quote("outdoor_venue", "Taos Ski Valley", 1_000_000, index="era5", today=date(2026, 11, 7), session=taos_weather)
    assert q.forecast is None and not called
