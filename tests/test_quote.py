"""The quote engine: 'I own a ski resort in X' -> priced, sized protection.

A fake weather service stands in for Open-Meteo, serving seasons whose
totals the tests choose, so every number here is checkable by hand.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from hone.prediction import climate
from hone.prediction.climate import Place, season_totals
from hone.prediction.quote import BUSINESSES, bad_season_probability, quote
from hone.web.app import create_app

TODAY = date(2026, 11, 7)


def _daily_for(totals: dict[int, float]) -> pd.Series:
    """Daily snowfall where each Nov-Apr season sums to the given total."""
    parts = []
    for year, total in totals.items():
        days = pd.date_range(f"{year}-11-01", f"{year + 1}-04-30")
        parts.append(pd.Series(total / len(days), index=days))
    s = pd.concat(parts)
    full = pd.date_range(s.index.min(), s.index.max())
    return s.reindex(full, fill_value=0.0)


class FakeWeather:
    """Answers the two Open-Meteo endpoints from in-memory data."""

    def __init__(self, places: dict[str, tuple[float, float]], seasons: dict[tuple[float, float], dict[int, float]],
                 stations: list[dict] | None = None, swe: dict[str, dict[int, float]] | None = None):
        self.places, self.seasons, self.calls = places, seasons, 0
        # SNOTEL: station records and peak snow water per winter, by triplet
        self.stations, self.swe = stations or [], swe or {}

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        if "awdbRestApi" in url:
            if url.endswith("/stations"):
                return _Resp(self.stations)
            peaks = self.swe.get(params["stationTriplets"], {})
            values = []
            for year, peak in peaks.items():
                # a winter's daily values rising to `peak` on Mar 31, Oct 1 - Jun 30
                for d in pd.date_range(f"{year}-10-01", f"{year + 1}-06-30"):
                    frac = min((d - pd.Timestamp(f"{year}-10-01")).days / 181, 1.0)
                    values.append({"date": d.strftime("%Y-%m-%d"), "value": round(peak * frac, 2)})
            return _Resp([{"stationTriplet": params["stationTriplets"], "data": [{"values": values}]}])
        if "geocoding" in url:
            hits = [
                {"name": n, "admin1": "Colorado", "country": "United States", "latitude": la, "longitude": lo, "elevation": 2400}
                for n, (la, lo) in self.places.items() if params["name"].lower() in n.lower()
            ]
            return _Resp({"results": hits} if hits else {})
        key = min(self.seasons, key=lambda k: abs(k[0] - params["latitude"]) + abs(k[1] - params["longitude"]))
        daily = _daily_for(self.seasons[key])
        daily = daily[(daily.index >= params["start_date"]) & (daily.index <= params["end_date"])]
        return _Resp({"daily": {"time": [d.strftime("%Y-%m-%d") for d in daily.index], "snowfall_sum": daily.round(4).tolist()}})


class _Resp:
    def __init__(self, data):
        self._d, self.status_code = data, 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


def _steady(n=40, normal=200.0, bad_every=4, start=1985):
    """Seasons at `normal`, except every `bad_every`-th one at 60% of normal."""
    return {start + i: (normal * 0.6 if i % bad_every == 0 else normal) for i in range(n)}


@pytest.fixture(autouse=True)
def _fresh_cache():
    climate._CACHE.clear()
    climate._STATIONS = None


@pytest.fixture
def weather():
    return FakeWeather(
        {"Snowtown": (39.2, -106.8), "Desert Springs": (33.0, -112.0)},
        {(39.2, -106.8): _steady(), (39.6, -106.5): _steady(), (33.0, -112.0): _steady()},
    )


# ------------------------------------------------------------- climate
class TestClimate:
    def test_season_totals_label_by_start_year_and_drop_partial_seasons(self):
        daily = _daily_for({2000: 100.0, 2001: 200.0})
        totals = season_totals(daily[daily.index < "2002-02-01"])   # 2001 season incomplete
        assert list(totals.index) == [2000]
        assert totals[2000] == pytest.approx(100.0)

    def test_geocode_returns_places(self, weather):
        found = climate.geocode("snowtown", session=weather)
        assert found[0].latitude == 39.2 and "Colorado" in found[0].label
        assert climate.geocode("", session=weather) == []

    def test_retries_then_fails_clearly(self, monkeypatch):
        monkeypatch.setattr(climate.time, "sleep", lambda s: None)

        class Flaky:
            calls = 0

            def get(self, *a, **k):
                Flaky.calls += 1
                raise ConnectionError("reset by peer")

        with pytest.raises(climate.ClimateError, match="Couldn't look up"):
            climate.geocode("x", session=Flaky())
        assert Flaky.calls == climate.RETRIES + 1


# ---------------------------------------------------------- probability
class TestProbability:
    def test_no_trend_matches_history(self):
        totals = pd.Series(_steady(n=40))
        prob, _ = bad_season_probability(totals, trigger_cm=160, current_season=2026)
        assert not prob.trend_used
        assert prob.historical == pytest.approx(0.25)
        # Jeffreys posterior mean (10.5 / 41) and a sensible range around it
        assert prob.estimate == pytest.approx(10.5 / 41)
        assert prob.low < 0.25 < prob.high

    def test_drying_trend_makes_bad_seasons_likelier(self):
        rng = np.random.default_rng(0)
        years = np.arange(1980, 2026)
        totals = pd.Series(300 - 3.0 * (years - 1980) + rng.normal(0, 15, len(years)), index=years)
        trigger = float(totals.quantile(0.25))
        prob, sample = bad_season_probability(totals, trigger, current_season=2026)
        assert prob.trend_used and prob.trend_cm_per_decade < -20
        assert prob.estimate > 0.8 > prob.historical   # the past understates today's risk
        assert sample.min() >= 0

    def test_short_history_refused(self):
        with pytest.raises(ValueError, match="10 seasons"):
            bad_season_probability(pd.Series([100.0] * 5, index=range(2020, 2025)), 80, 2026)


# ----------------------------------------------------------------- quote
class TestQuote:
    def test_three_inputs_give_a_full_quote(self, weather):
        q = quote("ski_resort", "Snowtown", 4_000_000, today=TODAY, session=weather)
        assert q.place["label"].startswith("Snowtown")
        assert q.normal_cm == pytest.approx(200, abs=0.5)
        assert q.trigger_cm == pytest.approx(140, abs=0.5)           # 70% of normal
        assert q.probability.historical == pytest.approx(0.25)
        assert q.fair_price == pytest.approx(q.probability.estimate)
        assert q.loaded_price == pytest.approx(q.fair_price * 1.3)
        # Bad seasons are 40% short; Rockies resort elasticity 0.25, damped for
        # the default 25% pre-sold passes: 0.25 x (1 - 0.7 x 0.25).
        assert q.avg_shortfall == pytest.approx(0.4, abs=0.01)
        assert q.elasticity == pytest.approx(0.25 * (1 - 0.7 * 0.25))
        assert q.loss == pytest.approx(4_000_000 * q.elasticity * 0.4, rel=0.01)
        # Cushion = 10% reserves + 15% margin
        assert q.wealth == pytest.approx(400_000 + 600_000)
        assert q.protection > 0 and q.cost_loaded == pytest.approx(q.protection * q.loaded_price)
        assert q.plan["ce_gain"] > 0
        assert any("ERA5" in a for a in q.assumptions)

    def test_never_recommends_selling_protection(self, weather):
        """Regression: with a margin on the price, the sizing engine used to
        tell a resort with a big cushion to SELL protection."""
        for gamma in (0.5, 1, 2, 3, 6):
            for loading in (0.0, 0.3, 1.0):
                q = quote("ski_resort", "Snowtown", 4_000_000, gamma=gamma, loading=loading,
                          reserves=10_000_000, today=TODAY, session=weather)
                assert q.plan["contracts"] >= 0, (gamma, loading)

    def test_with_perfect_basis_more_risk_averse_buys_more(self, weather):
        """No basis risk: the textbook result — more risk-averse, more cover."""
        sizes = [quote("ski_resort", "Snowtown", 4_000_000, gamma=g, basis=1.0, reserves=2_000_000,
                       today=TODAY, session=weather).protection for g in (1, 3, 8)]
        assert sizes == sorted(sizes) and sizes[-1] > sizes[0]

    def test_basis_risk_can_make_the_vulnerable_buy_less_and_says_why(self, weather):
        """Clarke (2016): with basis risk, index-insurance demand can FALL
        with risk aversion, because a bad season without a payout gets worse
        with every dollar of premium. Hone must reproduce this AND explain it."""
        q = quote("ski_resort", "Snowtown", 4_000_000, gamma=8, basis=0.7, margin=0.05, reserves=50_000,
                  today=TODAY, session=weather)
        assert q.protection < 0.6 * q.protection_if_perfect
        assert any("always paid in your bad seasons" in w for w in q.warnings)
        assert any("more than your cushion" in w for w in q.warnings)   # thin cushion here

    def test_ample_cushion_bigger_exposure_means_more_cover(self, weather):
        """Away from ruin, at a fair price, a bigger loss means more cover."""
        small = quote("ski_resort", "Snowtown", 2_000_000, reserves=5_000_000, loading=0.0, today=TODAY, session=weather)
        big = quote("ski_resort", "Snowtown", 6_000_000, reserves=5_000_000, loading=0.0, today=TODAY, session=weather)
        assert big.loss > small.loss and big.protection > small.protection
        assert not any("more than your cushion" in w for w in big.warnings)

    def test_nearby_kalshi_market(self, weather):
        q = quote("ski_resort", "Snowtown", 4_000_000, today=TODAY, session=weather)
        assert q.nearby_market.ticker == "KXASPSNOWM"
        assert q.nearby_market.settles_on == "one month's snowfall"
        assert q.nearby_market.correlation == pytest.approx(1.0)
        far = quote("ski_resort", "Desert Springs", 4_000_000, today=TODAY, session=weather)
        assert far.nearby_market is None

    def test_percentile_trigger(self, weather):
        q = quote("ski_resort", "Snowtown", 4_000_000, trigger_percentile=0.25, today=TODAY, session=weather)
        assert "worst 25%" in q.trigger_rule

    @pytest.mark.parametrize("kw,msg", [
        (dict(business="casino"), "unknown business"),
        (dict(revenue=0), "revenue"),
        (dict(place="Atlantis"), "Couldn't find"),
        (dict(margin=1.5), "margin"),
        (dict(trigger_fraction=0.1), "trigger fraction"),
        (dict(basis=1.5), "basis"),
    ])
    def test_bad_inputs_are_explained(self, weather, kw, msg):
        args = dict(business="ski_resort", place="Snowtown", revenue=1e6)
        args.update(kw)
        with pytest.raises(ValueError, match=msg):
            quote(args.pop("business"), args.pop("place"), args.pop("revenue"), today=TODAY, session=weather, **args)

    def test_every_business_type_quotes(self, weather):
        for key in BUSINESSES:
            q = quote(key, "Snowtown", 500_000, today=TODAY, session=weather)
            assert q.plan["contracts"] >= 0 and q.loss > 0


# ------------------------------------------------------------------- API
class TestAPI:
    @pytest.fixture
    def api(self, weather, monkeypatch):
        import requests
        monkeypatch.setattr(requests, "get", weather.get)
        return TestClient(create_app())

    def test_quote_endpoint(self, api):
        r = api.post("/api/predict/quote?asset_class=prediction",
                     json={"business": "ski_resort", "place": "Snowtown", "revenue": 4_000_000, "gamma": 3})
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["protection"] > 0 and out["tier"]["tier"] >= 1
        assert len(out["history"]) == 40

    def test_coordinates_skip_the_lookup(self, api):
        r = api.post("/api/predict/quote?asset_class=prediction", json={
            "business": "ski_resort", "latitude": 39.2, "longitude": -106.8,
            "place_label": "My hill", "revenue": 1_000_000})
        assert r.status_code == 200 and r.json()["place"]["label"] == "My hill"

    def test_places_and_businesses(self, api):
        assert api.get("/api/predict/places?q=snow").json()[0]["label"].startswith("Snowtown")
        keys = [b["key"] for b in api.get("/api/predict/businesses").json()]
        assert "ski_resort" in keys

    def test_errors(self, api):
        r = api.post("/api/predict/quote", json={"business": "ski_resort", "revenue": 1e6})
        assert r.status_code == 422 and "where" in r.json()["detail"]
        r = api.post("/api/predict/quote", json={"business": "ski_resort", "place": "Atlantis", "revenue": 1e6})
        assert r.status_code == 422


class TestRegions:
    """Snow sensitivity by region, from the published evidence."""

    def test_regions(self):
        from hone.prediction.quote import region_of
        assert region_of(39.19, -106.82) == "rockies"     # Aspen
        assert region_of(39.27, -120.12) == "pacific"     # Tahoe
        assert region_of(44.53, -72.78) == "east"         # Stowe
        assert region_of(47.0, 11.0) == "other"           # Alps

    def test_pacific_resorts_lose_more_than_rockies(self):
        places = {"Rocky": (39.2, -106.8), "Coast": (39.3, -120.1)}
        w = FakeWeather(places, {(39.2, -106.8): _steady(), (39.3, -120.1): _steady(), (39.6, -106.5): _steady()})
        rocky = quote("ski_resort", "Rocky", 1_000_000, today=TODAY, session=w)
        coast = quote("ski_resort", "Coast", 1_000_000, today=TODAY, session=w)
        assert coast.loss == pytest.approx(rocky.loss * 0.55 / 0.25, rel=0.01)

    def test_snow_removal_uses_its_own_sensitivity(self, weather):
        q = quote("snow_removal", "Snowtown", 500_000, today=TODAY, session=weather)
        assert q.elasticity == 1.0


# ------------------------------------------------------------ snow stations
STATION = {"stationTriplet": "1:CO:SNTL", "networkCode": "SNTL", "name": "Snowtown Summit",
           "latitude": 39.25, "longitude": -106.8, "elevation": 10_500, "beginDate": "1980-10-01 00:00"}


def _station_weather(swe):
    return FakeWeather({"Snowtown": (39.2, -106.8)},
                       {(39.2, -106.8): _steady(), (39.6, -106.5): _steady()},
                       stations=[STATION, {**STATION, "networkCode": "SCAN", "stationTriplet": "2:CO:SCAN"}],
                       swe={"1:CO:SNTL": swe})


class TestStations:
    """findings/07_resorts.md: the grid and the mountain often disagree about
    which seasons were bad; a real contract settles on a named station."""

    def test_prices_from_the_mountain_station_when_one_is_close(self):
        # Station sees bad winters 1 in 3 (grid: 1 in 4); peaks in inches of water.
        swe = {1985 + i: (12.0 if i % 3 == 0 else 24.0) for i in range(36)}
        q = quote("ski_resort", "Snowtown", 4_000_000, today=TODAY, session=_station_weather(swe))
        assert "SNOTEL Snowtown Summit" in q.index_source
        assert q.unit.startswith("in.")
        assert q.normal_cm == pytest.approx(24.0)
        assert q.probability.historical == pytest.approx(12 / 36)
        assert any("settle on this station" in a for a in q.assumptions)

    def test_falls_back_to_the_grid_without_a_long_station_record(self):
        swe = {2020 + i: 20.0 for i in range(5)}                 # only 5 winters
        q = quote("ski_resort", "Snowtown", 4_000_000, today=TODAY, session=_station_weather(swe))
        assert q.index_source.startswith("ERA5") and q.unit.startswith("cm")

    def test_grid_can_be_forced(self):
        swe = {1985 + i: 20.0 for i in range(36)}
        q = quote("ski_resort", "Snowtown", 4_000_000, index="era5", today=TODAY, session=_station_weather(swe))
        assert q.index_source.startswith("ERA5")

    def test_station_index_required_but_missing_is_explained(self, weather):
        with pytest.raises(ValueError, match="No snow station"):
            quote("ski_resort", "Snowtown", 4_000_000, index="station", today=TODAY, session=weather)


class TestResortEvidence:
    """findings/06_resort_financials.md: Vail's 22 seasons of filings."""

    def test_presold_passes_soften_the_loss(self, weather):
        none = quote("ski_resort", "Snowtown", 4_000_000, pass_share=0.0, today=TODAY, session=weather)
        heavy = quote("ski_resort", "Snowtown", 4_000_000, pass_share=0.7, today=TODAY, session=weather)
        assert heavy.loss == pytest.approx(none.loss * (1 - 0.7 * 0.7), rel=0.01)

    def test_extreme_shortfalls_stop_scaling(self):
        """Tahoe at 19% of normal lost 16-28% of visits, not ~65%."""
        dire = {1985 + i: (200.0 * 0.15 if i % 4 == 0 else 200.0) for i in range(40)}  # bad = 85% short
        w = FakeWeather({"Coast": (39.3, -120.1)}, {(39.3, -120.1): dire, (39.6, -106.5): dire})
        q = quote("ski_resort", "Coast", 1_000_000, pass_share=0.0, today=TODAY, session=w)
        assert q.avg_shortfall == pytest.approx(0.85, abs=0.01)
        assert q.loss == pytest.approx(1_000_000 * 0.55 * 0.5, rel=0.01)   # counted as 50%
        assert q.loss <= 0.35 * 1_000_000
