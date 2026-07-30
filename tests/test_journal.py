"""Decision journal: resolution rules, Brier scoring, and the calibration map."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from hone.journal.calibration import (
    MIN_FOR_ADJUSTMENT,
    apply_calibration,
    brier_decomposition,
    brier_score,
    fit_calibration,
    reliability_bins,
)
from hone.journal.records import Prediction, resolve_all, resolve_prediction
from hone.web.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


def _series(values, start_days_ago=200):
    """A daily price series ending today."""
    end = pd.Timestamp.now(tz=timezone.utc).normalize()
    idx = pd.date_range(end=end, periods=len(values), freq="D")
    return pd.Series(values, index=idx)


def _made_days_ago(n):
    return datetime.now(timezone.utc) - timedelta(days=n)


class TestPrediction:
    def test_rejects_impossible_inputs(self):
        with pytest.raises(ValueError):
            Prediction(ticker="X", entry_price=0, target_price=10, confidence=0.5)
        with pytest.raises(ValueError):
            Prediction(ticker="X", entry_price=10, target_price=12, confidence=1.5)
        with pytest.raises(ValueError):
            Prediction(
                ticker="X", entry_price=10, target_price=12,
                confidence=0.5, direction="sideways",
            )

    def test_maturity(self):
        p = Prediction(
            ticker="X", entry_price=100, target_price=120, confidence=0.6,
            horizon_days=30, created_at=_made_days_ago(40),
        )
        assert p.is_mature()
        q = Prediction(
            ticker="X", entry_price=100, target_price=120, confidence=0.6,
            horizon_days=30, created_at=_made_days_ago(5),
        )
        assert not q.is_mature()


class TestResolution:
    def test_immature_prediction_is_not_scored(self):
        p = Prediction(
            ticker="X", entry_price=100, target_price=120, confidence=0.6,
            horizon_days=90, created_at=_made_days_ago(10),
        )
        assert resolve_prediction(p, _series(np.linspace(100, 130, 200))) is None

    def test_bullish_hit(self):
        p = Prediction(
            ticker="X", entry_price=100, target_price=120, confidence=0.7,
            horizon_days=60, created_at=_made_days_ago(90),
        )
        res = resolve_prediction(p, _series(np.linspace(100, 140, 200)))
        assert res is not None
        assert res.target_hit and res.direction_hit
        assert res.brier == pytest.approx((0.7 - 1) ** 2)

    def test_bullish_miss_but_right_direction(self):
        """Right way, short of target — scored a miss, but distinguished."""
        p = Prediction(
            ticker="X", entry_price=100, target_price=200, confidence=0.8,
            horizon_days=60, created_at=_made_days_ago(90),
        )
        res = resolve_prediction(p, _series(np.linspace(100, 130, 200)))
        assert res.target_hit is False
        assert res.direction_hit is True
        assert res.brier == pytest.approx(0.64)

    def test_bearish_hit(self):
        p = Prediction(
            ticker="X", entry_price=100, target_price=80, confidence=0.6,
            horizon_days=60, created_at=_made_days_ago(90), direction="bearish",
        )
        res = resolve_prediction(p, _series(np.linspace(100, 70, 200)))
        assert res.target_hit and res.direction_hit

    def test_touched_then_gave_it_back(self):
        """A target reached intraday and surrendered is not a hit."""
        # rises through 120, then falls back under it before the deadline
        values = list(np.linspace(100, 130, 100)) + list(np.linspace(130, 105, 100))
        p = Prediction(
            ticker="X", entry_price=100, target_price=120, confidence=0.7,
            horizon_days=60, created_at=_made_days_ago(90),
        )
        res = resolve_prediction(p, _series(values))
        assert res.touched is True
        assert res.target_hit is False

    def test_missing_data_leaves_it_open_rather_than_failing_the_user(self):
        p = Prediction(
            ticker="X", entry_price=100, target_price=120, confidence=0.7,
            horizon_days=60, created_at=_made_days_ago(90),
        )
        empty = pd.Series(dtype=float)
        assert resolve_prediction(p, empty) is None

    def test_resolve_all_splits_open_and_scored(self):
        prices = pd.DataFrame({"X": np.linspace(100, 140, 200)},
                              index=_series(np.zeros(200)).index)
        mature = Prediction(ticker="X", entry_price=100, target_price=120,
                            confidence=0.7, horizon_days=30,
                            created_at=_made_days_ago(90))
        young = Prediction(ticker="X", entry_price=100, target_price=120,
                           confidence=0.7, horizon_days=300,
                           created_at=_made_days_ago(5))
        unknown = Prediction(ticker="ZZZZ", entry_price=100, target_price=120,
                             confidence=0.7, horizon_days=30,
                             created_at=_made_days_ago(90))
        resolved, still_open = resolve_all([mature, young, unknown], prices)
        assert len(resolved) == 1
        assert {p.ticker for p in still_open} == {"X", "ZZZZ"}


class TestBrier:
    def test_perfect_and_worst(self):
        assert brier_score([1.0, 0.0], [1, 0]) == pytest.approx(0.0, abs=1e-9)
        assert brier_score([1.0, 1.0], [0, 0]) == pytest.approx(1.0)

    def test_always_fifty_percent_scores_a_quarter(self):
        assert brier_score([0.5] * 8, [1, 0] * 4) == pytest.approx(0.25)

    def test_decomposition_adds_up(self):
        rng = np.random.default_rng(3)
        p = rng.choice([0.1, 0.3, 0.5, 0.7, 0.9], 400)
        o = (rng.random(400) < p).astype(float)
        d = brier_decomposition(p, o)
        assert d["binned_brier"] == pytest.approx(
            d["reliability"] - d["resolution"] + d["uncertainty"]
        )
        # a well-calibrated forecaster has near-zero reliability error
        assert d["reliability"] < 0.01
        assert d["skill_vs_base_rate"] > 0

    def test_bins_cover_the_unit_interval(self):
        bins = reliability_bins([0.05, 0.5, 0.99], [1, 0, 1], n_bins=5)
        assert sum(b["n"] for b in bins) == 3
        assert bins[0]["lower"] == 0.0 and bins[-1]["upper"] == 1.0


class TestCalibrationFit:
    def _overconfident(self, n=120, seed=1):
        rng = np.random.default_rng(seed)
        p = rng.choice([0.5, 0.6, 0.7, 0.8, 0.9], n)
        o = (rng.random(n) < p * 0.5).astype(float)  # true hit rate is half
        return p, o

    def test_overconfidence_is_pulled_down(self):
        p, o = self._overconfident()
        report = fit_calibration(p, o)
        assert report.actionable
        assert apply_calibration(0.8, report) < 0.65
        assert "overconfident" in report.summary

    def test_calibrated_forecaster_is_left_alone(self):
        rng = np.random.default_rng(2)
        p = rng.choice([0.3, 0.5, 0.7, 0.9], 200)
        o = (rng.random(200) < p).astype(float)
        report = fit_calibration(p, o)
        assert apply_calibration(0.7, report) == pytest.approx(0.7, abs=0.08)

    def test_underconfidence_is_pushed_up(self):
        rng = np.random.default_rng(5)
        p = np.full(150, 0.4)
        o = (rng.random(150) < 0.8).astype(float)
        report = fit_calibration(p, o)
        assert apply_calibration(0.4, report) > 0.5

    def test_short_history_is_not_acted_on(self):
        report = fit_calibration([0.9, 0.9, 0.9], [0, 0, 0])
        assert report.n == 3
        assert not report.actionable
        # three wrong calls is not evidence, and must not silence the user
        assert apply_calibration(0.9, report) == pytest.approx(0.9)
        assert str(MIN_FOR_ADJUSTMENT) in report.summary

    def test_shrinkage_makes_a_long_record_bite_harder(self):
        p_short, o_short = self._overconfident(n=8, seed=7)
        p_long, o_long = self._overconfident(n=300, seed=7)
        short = apply_calibration(0.8, fit_calibration(p_short, o_short))
        long = apply_calibration(0.8, fit_calibration(p_long, o_long))
        assert long < short < 0.8

    def test_perfect_record_does_not_blow_up(self):
        """Every call correct: the unconstrained MLE diverges, the fit must not."""
        report = fit_calibration([0.6] * 20, [1] * 20)
        adjusted = apply_calibration(0.6, report)
        assert np.isfinite(adjusted) and adjusted <= 0.95
        assert adjusted > 0.6  # rewarded, not punished

    def test_empty_history(self):
        report = fit_calibration([], [])
        assert report.n == 0 and not report.actionable
        assert apply_calibration(0.7, report) == pytest.approx(0.7)

    def test_confidence_never_collapses_to_zero(self):
        rng = np.random.default_rng(9)
        p = np.full(200, 0.9)
        o = (rng.random(200) < 0.02).astype(float)
        report = fit_calibration(p, o)
        assert apply_calibration(0.9, report) >= 0.05


class TestJournalEndpoint:
    def test_demo_seed_builds_a_scored_record(self, client):
        res = client.post(
            "/api/journal",
            json={"demo": True, "seed_demo_history": True, "predictions": []},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["seeded"] is True
        assert len(body["resolved"]) >= 5
        cal = body["calibration"]
        assert cal["n"] == len(body["resolved"])
        assert 0 <= cal["brier"] <= 1
        assert cal["summary"]
        assert len(cal["examples"]) == 4
        assert cal["direction_hit_rate"] is not None

    def test_empty_journal_is_not_an_error(self, client):
        res = client.post("/api/journal", json={"demo": True, "predictions": []})
        assert res.status_code == 200
        body = res.json()
        assert body["resolved"] == [] and body["open"] == []
        assert body["calibration"]["n"] == 0
        assert body["calibration"]["actionable"] is False

    def test_open_prediction_reports_progress(self, client):
        res = client.post(
            "/api/journal",
            json={
                "demo": True,
                "predictions": [
                    {
                        "id": "a", "ticker": "TSLA", "entry_price": 300,
                        "target_price": 400, "confidence": 0.6,
                        "horizon_days": 3650,
                        "created_at": "2025-01-02",
                    }
                ],
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert len(body["open"]) == 1
        o = body["open"][0]
        assert o["days_remaining"] > 0
        assert o["current_price"] > 0
        assert o["progress"] is not None

    def test_bad_prediction_is_rejected(self, client):
        res = client.post(
            "/api/journal",
            json={
                "demo": True,
                "predictions": [
                    {"ticker": "TSLA", "entry_price": -1, "target_price": 400,
                     "confidence": 0.6, "created_at": "2025-01-02"}
                ],
            },
        )
        assert res.status_code == 422

    def test_crypto_mode_seeds_crypto_symbols(self, client):
        body = client.post(
            "/api/journal?asset_class=crypto",
            json={"demo": True, "seed_demo_history": True},
        ).json()
        tickers = {r["prediction"]["ticker"] for r in body["resolved"]}
        assert any("/USD" in t for t in tickers)


class TestCalibrationInOptimize:
    def _optimize(self, client, calibration=None):
        payload = {
            "gamma": 1.2,
            "demo": True,
            "views": [{"ticker": "TSLA", "target_price": 450, "confidence": 0.8}],
        }
        if calibration:
            payload["calibration"] = calibration
        return client.post("/api/optimize", json=payload).json()

    def test_no_calibration_uses_stated_confidence(self, client):
        body = self._optimize(client)
        assert body["confidence_adjustments"] is None
        assert body["views"][0]["confidence"] == pytest.approx(0.8)

    def test_calibration_rescales_the_view(self, client):
        body = self._optimize(
            client,
            # an overconfident record: slope 1, big negative intercept
            {"intercept": -1.0, "slope": 1.0, "actionable": True, "n": 40},
        )
        adj = body["confidence_adjustments"]
        assert adj and adj[0]["ticker"] == "TSLA"
        assert adj[0]["stated"] == pytest.approx(0.8)
        assert adj[0]["used"] < 0.8
        assert body["views"][0]["confidence"] == pytest.approx(adj[0]["used"])

    def test_non_actionable_calibration_is_ignored(self, client):
        body = self._optimize(
            client,
            {"intercept": -2.0, "slope": 1.0, "actionable": False, "n": 2},
        )
        assert body["confidence_adjustments"] is None

    def test_rescaling_moves_the_portfolio_less(self, client):
        """The whole point: a discounted view tilts the portfolio less."""
        plain = self._optimize(client)
        damped = self._optimize(
            client, {"intercept": -1.5, "slope": 1.0, "actionable": True, "n": 40}
        )
        tilt = {x["symbol"]: x["tilt"] for x in plain["returns"]}
        tilt_damped = {x["symbol"]: x["tilt"] for x in damped["returns"]}
        assert abs(tilt_damped["TSLA"]) < abs(tilt["TSLA"])

    def test_optimize_returns_prices_for_the_journal(self, client):
        body = self._optimize(client)
        v = body["views"][0]
        assert v["ticker"] == "TSLA"
        assert v["current_price"] > 0
        assert v["target_price"] == pytest.approx(450)
        assert v["horizon_days"] > 0


class TestJournalUI:
    def test_journal_page_exists_and_is_linked(self, client):
        html = client.get("/").text
        assert "PAGES.journal" in html
        assert "/api/journal" in html
        assert '"journal"' in html  # registered as an aside page

    def test_predictions_are_logged_at_the_server_price(self, client):
        html = client.get("/").text
        assert "journalRecord(RUNTIME.optimize.views)" in html
        assert "entry_price: v.current_price" in html

    def test_calibration_is_sent_with_optimize(self, client):
        html = client.get("/").text
        assert "body.calibration = S.calibration" in html
        assert "S.useCalibration !== false" in html

    def test_adjustment_is_disclosed_not_silent(self, client):
        html = client.get("/").text
        assert "confidence_adjustments" in html
        assert "rescaled from your track record" in html


class TestNoFeedbackLoop:
    """The journal must score what the user said, not what we used.

    Recording the calibrated confidence would make each pass discount the
    user a little further on the strength of its own previous discount.
    """

    def test_response_carries_the_stated_confidence(self, client):
        body = client.post(
            "/api/optimize",
            json={
                "gamma": 1.2,
                "demo": True,
                "views": [
                    {"ticker": "TSLA", "target_price": 450, "confidence": 0.8}
                ],
                "calibration": {
                    "intercept": -1.0, "slope": 1.0, "actionable": True, "n": 40,
                },
            },
        ).json()
        v = body["views"][0]
        assert v["stated_confidence"] == pytest.approx(0.8)
        assert v["confidence"] < 0.8  # what the optimizer actually used

    def test_the_page_journals_the_stated_value(self, client):
        html = client.get("/").text
        assert "v.stated_confidence != null ? v.stated_confidence" in html
