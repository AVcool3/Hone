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

    def __init__(self, places: dict[str, tuple[float, float]], seasons: dict[tuple[float, float], dict[int, float]]):
        self.places, self.seasons, self.calls = places, seasons, 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
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
        # Bad seasons are 40% short; Rockies resort elasticity 0.25 -> 10% of revenue.
        assert q.avg_shortfall == pytest.approx(0.4, abs=0.01)
        assert q.elasticity == pytest.approx(0.25)
        assert q.loss == pytest.approx(4_000_000 * 0.25 * 0.4, rel=0.01)
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
        assert coast.loss == pytest.approx(rocky.loss * 0.8 / 0.25, rel=0.01)

    def test_snow_removal_uses_its_own_sensitivity(self, weather):
        q = quote("snow_removal", "Snowtown", 500_000, today=TODAY, session=weather)
        assert q.elasticity == 1.0
