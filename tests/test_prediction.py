"""The prediction-markets product: contract math, the catalog, the API, the page.

The hedge tests are the theory, stated as assertions: at a fair price with
no fees and perfect basis a risk-averse person hedges the whole loss; fees
and basis risk shrink the hedge; the reservation price sits above fair
value for someone with exposure and equals it for someone without; the
pure bet at gamma = 1 is Kelly and at gamma = 2 about half of it.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hone.prediction import (
    INDUSTRIES,
    Contract,
    IncomeExposure,
    KalshiClient,
    KalshiError,
    blend_belief,
    hedge_income,
    implied_probability,
    kalshi_fee,
    kelly_fraction,
    load_snapshot,
)
from hone.prediction.hedge import joint_states, reservation_price
from hone.prediction.kalshi_client import assemble, curated_catalog, normalize_market
from hone.web.app import create_app

from frontend_source import built_index, source  # React UI source (see tests/frontend_source.py)


def exposure(**kw):
    # The theory tests check the mathematical model itself, so the sizing
    # safety margins are off unless a test sets them (see test_hedge_margins.py).
    base = dict(wealth=38_000.0, loss=9_000.0, price=0.35, gamma=1.5, basis_shrink=1.0, price_buffer=0.0)
    base.update(kw)
    return IncomeExposure(**base)


class TestContracts:
    def test_fee_is_quadratic_in_price_and_rounds_up(self):
        assert kalshi_fee(100, 0.5) == pytest.approx(1.75)
        assert kalshi_fee(100, 0.5, round_up=False) == pytest.approx(1.75)
        # 0.07 * 1 * 0.35 * 0.65 = 0.015925 -> rounds up to 2 cents
        assert kalshi_fee(1, 0.35) == pytest.approx(0.02)
        assert kalshi_fee(1, 0.35, round_up=False) == pytest.approx(0.015925)
        # symmetric: buying NO at 1 - p costs the same
        assert kalshi_fee(50, 0.2) == pytest.approx(kalshi_fee(50, 0.8))
        assert kalshi_fee(10, 0.01) < kalshi_fee(10, 0.5)

    def test_fee_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            kalshi_fee(-1, 0.5)
        with pytest.raises(ValueError):
            kalshi_fee(1, 1.5)

    def test_implied_probability_reads_the_book_sensibly(self):
        assert implied_probability(0.30, 0.40) == pytest.approx(0.35)
        # an empty book (bid 0, ask 1) is not a 50% opinion: fall back to last
        assert implied_probability(0.0, 1.0, 0.74) == pytest.approx(0.74)
        assert implied_probability(None, 0.17) == pytest.approx(0.17)
        assert implied_probability(None, None, None) is None

    def test_contract_cost_includes_fee(self):
        c = Contract(ticker="X", side="no", price=0.65)
        assert c.cost(100) == pytest.approx(65.0 + kalshi_fee(100, 0.65))
        assert c.payout_per_dollar == pytest.approx(0.35 / 0.65)
        with pytest.raises(ValueError):
            Contract(ticker="X", side="maybe", price=0.5)


class TestBeliefs:
    def test_blend_is_the_market_with_no_view_and_the_view_at_full_confidence(self):
        assert blend_belief(0.35, None, 1.0) == pytest.approx(0.35)
        assert blend_belief(0.35, 0.55, 1.0) == pytest.approx(0.55)
        assert blend_belief(0.35, 0.55, 0.5) == pytest.approx(0.45)
        assert blend_belief(0.35, 0.55, 0.0) == pytest.approx(0.35)

    def test_blend_never_reaches_certainty(self):
        assert 0.01 <= blend_belief(0.5, 1.0, 1.0) <= 0.99
        assert blend_belief(0.5, 0.0, 1.0) >= 0.01

    def test_joint_states_respect_marginals_and_clip_rho(self):
        states, rho = joint_states(0.35, 0.35, 1.0)
        assert rho == pytest.approx(1.0)
        assert sum(s.prob for s in states) == pytest.approx(1.0)
        assert sum(s.prob for s in states if s.pays) == pytest.approx(0.35)
        assert sum(s.prob for s in states if s.loss) == pytest.approx(0.35)
        # perfectly correlated: the mixed states vanish
        assert all(s.prob < 1e-12 for s in states if s.pays != s.loss)
        states, rho = joint_states(0.2, 0.6, 1.0)
        assert rho < 1.0  # Frechet bound bites
        assert all(s.prob >= 0 for s in states)


class TestHedgeTheory:
    def test_fair_price_perfect_basis_no_fees_hedges_everything(self):
        plan = hedge_income(exposure(fee_rate=0.0))
        assert plan.contracts == 9_000
        assert plan.pure_hedge_contracts == pytest.approx(9_000)
        assert abs(plan.speculative_contracts) < 1.0
        assert plan.std_hedged == pytest.approx(0.0, abs=1e-6)
        assert plan.ce_gain > 0
        # expected wealth is unchanged at a fair price; only risk is removed
        assert plan.expected_wealth_hedged == pytest.approx(plan.expected_wealth_unhedged, abs=1e-6)

    def test_fees_shrink_the_hedge(self):
        with_fee = hedge_income(exposure())
        no_fee = hedge_income(exposure(fee_rate=0.0))
        assert 0 < with_fee.contracts < no_fee.contracts
        assert with_fee.fee > 0
        assert with_fee.ce_gain < no_fee.ce_gain

    def test_more_risk_averse_hedges_more(self):
        n = [hedge_income(exposure(gamma=g)).contracts for g in (0.3, 1.0, 1.5, 3.5)]
        assert n == sorted(n)
        assert n[0] < n[-1]

    def test_basis_risk_shrinks_the_hedge_to_rho_times_loss(self):
        plan = hedge_income(exposure(basis_correlation=0.6, fee_rate=0.0))
        # rho*L is the variance-minimizing reference; the insurance actually
        # proposed is the CRRA optimum at market odds, close to it here.
        assert plan.variance_min_contracts == pytest.approx(0.6 * 9_000)
        assert plan.pure_hedge_contracts == pytest.approx(0.6 * 9_000, rel=0.05)
        assert plan.contracts < 9_000
        assert plan.std_hedged > 0  # residual risk stays
        full = hedge_income(exposure(fee_rate=0.0))
        assert plan.ce_gain < full.ce_gain

    def test_reservation_price_exceeds_fair_value_only_with_exposure(self):
        plan = hedge_income(exposure())
        assert plan.reservation_price > plan.fair_price
        states, _ = joint_states(0.35, 0.35, 1.0)
        assert reservation_price(38_000, 9_000, 1.5, states) == pytest.approx(plan.reservation_price)
        # gamma = 0: the price is just the probability
        assert reservation_price(38_000, 9_000, 0.0, states) == pytest.approx(0.35)
        spec = hedge_income(exposure(loss=0.0, own_prob=0.55, confidence=1.0))
        assert spec.reservation_price == pytest.approx(spec.fair_price)

    def test_above_the_ceiling_there_is_no_position(self):
        plan = hedge_income(exposure(price=0.60, market_prob=0.35, fee_rate=0.0))
        # belief 35%, price 60% >> ceiling of ~45%: do not buy
        assert plan.contracts <= 0
        assert plan.needs_hedge is False

    def test_a_cheap_contract_adds_a_speculative_tilt(self):
        plan = hedge_income(exposure(own_prob=0.5, confidence=1.0))
        assert plan.belief == pytest.approx(0.5)
        assert plan.speculative_contracts > 0
        assert plan.contracts > 9_000
        assert any("far from the market" in w for w in plan.warnings)

    def test_pure_bet_at_log_utility_is_kelly_and_gamma_two_is_about_half(self):
        kelly = kelly_fraction(0.55, 0.40)
        assert kelly == pytest.approx(0.25)
        one = hedge_income(exposure(wealth=10_000, loss=0.0, price=0.40, gamma=1.0,
                                    own_prob=0.55, confidence=1.0, fee_rate=0.0))
        assert one.crra_fraction == pytest.approx(kelly, abs=0.005)
        two = hedge_income(exposure(wealth=10_000, loss=0.0, price=0.40, gamma=2.0,
                                    own_prob=0.55, confidence=1.0, fee_rate=0.0))
        assert 0.4 < two.crra_fraction / kelly < 0.6
        assert any("nothing to hedge" in w for w in one.warnings)

    def test_kelly_signed_against_the_side(self):
        assert kelly_fraction(0.3, 0.4) < 0

    def test_risk_seeking_gamma_gets_no_position_and_a_warning(self):
        # v2: risk-neutral/seeking preferences don't want insurance, so no
        # position (the old full hedge had negative value at these preferences)
        plan = hedge_income(exposure(gamma=-0.5))
        assert plan.contracts == 0 and not plan.needs_hedge
        assert any("risk-seeking" in w for w in plan.warnings)

    def test_wealth_stays_positive_in_every_state(self):
        plan = hedge_income(exposure(wealth=10_000, loss=9_500, price=0.5, gamma=2.0))
        assert all(s.wealth_hedged > 0 and s.wealth_unhedged > 0 for s in plan.states)

    def test_validation(self):
        with pytest.raises(ValueError):
            hedge_income(exposure(loss=40_000))
        with pytest.raises(ValueError):
            hedge_income(exposure(price=1.0))
        with pytest.raises(ValueError):
            hedge_income(exposure(basis_correlation=1.5))
        with pytest.raises(ValueError):
            hedge_income(exposure(wealth=0))


# -------------------------------------------------------------- catalog
class _FakeResponse:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.responses.pop(0)


RAW_MARKET = {
    "ticker": "KXU3-26NOV-T4.6", "event_ticker": "KXU3-26NOV",
    "title": "Will the unemployment rate (U-3) be above 4.6% in November?",
    "yes_sub_title": "Above 4.6%", "status": "active", "close_time": "2026-12-04T13:29:00Z",
    "yes_bid_dollars": "0.3000", "yes_ask_dollars": "0.3400", "no_bid_dollars": "0.6600",
    "no_ask_dollars": "0.7000", "last_price_dollars": "0.3200", "volume_fp": "1234.00",
    "open_interest_fp": "500.00", "floor_strike": 4.6, "strike_type": "greater",
    "rules_primary": "If ... above 4.6% ... resolves to Yes.",
}


class TestKalshiClient:
    def test_normalize_market_flattens_prices(self):
        m = normalize_market(RAW_MARKET)
        assert m["yes_ask"] == pytest.approx(0.34)
        assert m["no_ask"] == pytest.approx(0.70)
        assert m["implied"] == pytest.approx(0.32)
        assert m["spread"] == pytest.approx(0.04)
        assert m["volume"] == 1234.0
        assert m["label"] == "Above 4.6%"
        assert m["strike"] == 4.6

    def test_markets_call_shape(self):
        sess = _FakeSession([_FakeResponse(200, {"markets": [RAW_MARKET]})])
        client = KalshiClient(session=sess)
        out = client.markets("KXU3")
        assert len(out) == 1 and out[0]["ticker"] == "KXU3-26NOV-T4.6"
        url, params = sess.calls[0]
        assert url.endswith("/markets")
        assert params["series_ticker"] == "KXU3" and params["status"] == "open"

    def test_rate_limit_is_retried_then_raised(self, monkeypatch):
        monkeypatch.setattr("hone.prediction.kalshi_client.time.sleep", lambda *_: None)
        sess = _FakeSession([_FakeResponse(429, {"error": "too many"}),
                             _FakeResponse(200, {"markets": []})])
        assert KalshiClient(session=sess).markets("KXU3") == []
        assert len(sess.calls) == 2
        sess = _FakeSession([_FakeResponse(500, {"error": "boom"})])
        with pytest.raises(KalshiError):
            KalshiClient(session=sess).markets("KXU3")

    def test_snapshot_is_bundled_and_covers_every_curated_series(self):
        snap = load_snapshot()
        assert snap["as_of"]
        curated = {s["ticker"] for ind in INDUSTRIES for s in ind["series"]}
        assert curated <= set(snap["series"])
        n_open = sum(len(s["markets"]) for s in snap["series"].values())
        assert n_open > 100

    def test_catalog_offline_is_the_snapshot_in_industry_order(self):
        cat = curated_catalog(live=False)
        assert cat["source"] == "snapshot"
        assert [i["key"] for i in cat["industries"]] == [i["key"] for i in INDUSTRIES]
        snow = cat["industries"][0]
        assert snow["key"] == "snow"
        aspen = next(s for s in snow["series"] if s["ticker"] == "KXASPSNOWM")
        assert aspen["basis"] == "direct"
        assert "open_count" in aspen

    def test_assemble_falls_back_per_series(self):
        live = {"as_of": "now", "source": "live-partial", "series": {"KXU3": {"ticker": "KXU3", "markets": [normalize_market(RAW_MARKET)]}}}
        snap = load_snapshot()
        cat = assemble(live, fallback=snap)
        labor = next(i for i in cat["industries"] if i["key"] == "labor")
        u3 = next(s for s in labor["series"] if s["ticker"] == "KXU3")
        assert u3["open_count"] == 1
        pay = next(s for s in labor["series"] if s["ticker"] == "KXPAYROLLS")
        assert pay["open_count"] == len(snap["series"]["KXPAYROLLS"]["markets"])

    def test_every_curated_series_has_a_basis_and_a_side(self):
        for ind in INDUSTRIES:
            assert ind["who"]
            for s in ind["series"]:
                assert s["basis"] in ("direct", "close", "proxy"), s
                assert s["bad_side"], s


# ------------------------------------------------------------------ web
@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


class TestWeb:
    def test_third_product_is_routed(self, client):
        assert client.get("/prediction-markets").status_code == 200
        assert client.get("/prediction-markets/").status_code == 200
        cfg = client.get("/api/config?asset_class=prediction").json()
        assert cfg["asset_class"] == "prediction"
        assert cfg["copy"]["product"] == "Hone Markets"
        assert client.get("/api/config").json()["asset_class"] == "equities"

    def test_catalog_endpoint(self, client):
        r = client.get("/api/predict/markets?live=false")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "snapshot"
        assert len(body["industries"]) == len(INDUSTRIES)
        m = next(m for i in body["industries"] for s in i["series"] for m in s["markets"])
        assert set(m) >= {"ticker", "title", "yes_ask", "no_ask", "implied", "close_time"}

    def test_hedge_endpoint_matches_the_engine(self, client):
        r = client.post("/api/predict/hedge", json={"gamma": 1.5, "wealth": 38000, "loss": 9000, "price": 0.35})
        assert r.status_code == 200
        body = r.json()
        # The API sizes with the safety margins on (the default).
        from hone.prediction.hedge import BASIS_SHRINK, PRICE_BUFFER
        plan = hedge_income(exposure(basis_shrink=BASIS_SHRINK, price_buffer=PRICE_BUFFER))
        assert body["contracts"] == plan.contracts
        assert body["tier"]["tier"] == 26
        assert body["ce_gain"] == pytest.approx(plan.ce_gain)
        assert body["confidence_used"] == 0.0

    def test_hedge_endpoint_validates(self, client):
        r = client.post("/api/predict/hedge", json={"gamma": 1.5, "wealth": 8000, "loss": 9000, "price": 0.35})
        assert r.status_code == 422
        assert "whole wealth" in r.json()["detail"]
        r = client.post("/api/predict/hedge", json={"gamma": 1.5, "wealth": 8000, "loss": 900, "price": 1.2})
        assert r.status_code == 422

    def test_fees_can_be_switched_off(self, client):
        on = client.post("/api/predict/hedge", json={"gamma": 1.5, "wealth": 38000, "loss": 9000, "price": 0.35}).json()
        off = client.post("/api/predict/hedge", json={"gamma": 1.5, "wealth": 38000, "loss": 9000, "price": 0.35, "include_fees": False}).json()
        assert off["fee"] == 0 and on["fee"] > 0
        # textbook model (no safety margins), fair price, no fees: insure every dollar
        pure = client.post("/api/predict/hedge", json={"gamma": 1.5, "wealth": 38000, "loss": 9000, "price": 0.35,
                                                        "include_fees": False, "safety_margins": False}).json()
        assert pure["contracts"] == 9000
        assert 0 < off["contracts"] < 9000      # the margins size more cautiously

    def test_calibration_map_shrinks_confidence(self, client):
        body = {"gamma": 1.5, "wealth": 38000, "loss": 9000, "price": 0.35, "own_prob": 0.6, "confidence": 0.8,
                "calibration": {"intercept": -0.5, "slope": 0.6, "actionable": True, "n": 30}}
        r = client.post("/api/predict/hedge", json=body).json()
        assert r["confidence_stated"] == 0.8
        assert r["confidence_used"] < 0.8
        plain = client.post("/api/predict/hedge", json={k: v for k, v in body.items() if k != "calibration"}).json()
        assert r["belief"] < plain["belief"]


class TestPage:
    @pytest.fixture(scope="class")
    def html(self, client):
        return client.get("/prediction-markets").text

    def test_three_product_tabs(self, html):
        switcher = source("ProductSwitcher.jsx")
        assert "PRODUCT_ORDER.map" in switcher
        assert "'prediction-markets': 'Prediction Markets'" in switcher
        assert "PRODUCT_ORDER = ['stocks', 'crypto', 'prediction-markets']" in source("lib/products.js")

    def test_landing_copy_is_crawler_visible(self, html):
        assert "Prediction Markets sizes event" in html  # in the no-JS fallback
        home = source("marketing/Home.jsx")
        assert "Your paycheck is already a <em>position.</em>" in home
        assert "Isn’t this just gambling?" in home
        assert "Size a sample hedge" in home

    def test_pages_and_routing_exist(self, client):
        app = source("App.jsx")
        assert '<Route path="hedge" element={<IncomeHedgePage />} />' in app
        assert '<Route path="markets" element={<MarketsPage />} />' in app
        assert "/api/predict/hedge" in source("IncomeHedgePage.jsx")
        assert "/api/predict/markets" in source("prediction/catalog.js")
        for path in ("/prediction-markets/app/hedge", "/prediction-markets/app/markets"):
            assert client.get(path).status_code == 200

    def test_concept_numbers_come_from_the_engine_not_the_prose(self, html):
        """The homepage's worked example is computed by the engine, live."""
        assert "'/api/predict/hedge'" in source("marketing/Home.jsx")
