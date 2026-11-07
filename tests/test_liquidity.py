"""The liquidity cap: never propose more contracts than the market can supply."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from hone.prediction import liquidity as liq
from hone.prediction.hedge import IncomeExposure, hedge_income
from hone.web.app import create_app

web = importlib.import_module("hone.web.app")

# Shape copied from Kalshi's live /markets/{ticker}/orderbook response.
BOOK = {
    "orderbook_fp": {
        # people bidding for YES (so: offers to *sell* you NO at 1 - bid)
        "yes_dollars": [["0.6000", "100.00"], ["0.6200", "50.00"]],
        # people bidding for NO (so: offers to sell you YES at 1 - bid)
        "no_dollars": [["0.6500", "200.00"], ["0.6800", "300.00"], ["0.5000", "5000.00"]],
    }
}


# ------------------------------------------------------------ order books
class TestOrderBook:
    def test_buying_yes_matches_no_bids(self):
        asks = liq.asks_from_orderbook(BOOK, "yes")
        # NO bids at .68/.65/.50 -> YES offers at .32/.35/.50, cheapest first
        assert asks == [(0.32, 300.0), (0.35, 200.0), (0.5, 5000.0)]

    def test_buying_no_matches_yes_bids(self):
        assert liq.asks_from_orderbook(BOOK, "no") == [(0.38, 50.0), (0.4, 100.0)]

    def test_depth_counts_only_near_the_best_price(self):
        asks = liq.asks_from_orderbook(BOOK, "yes")
        assert liq.depth_within(asks, 0.03) == 500     # .32 and .35, not .50
        assert liq.depth_within(asks, 0.20) == 5500
        assert liq.depth_within([], 0.03) == 0

    def test_average_fill_walks_the_book(self):
        asks = liq.asks_from_orderbook(BOOK, "yes")
        assert liq.average_fill(asks, 300) == pytest.approx(0.32)
        assert liq.average_fill(asks, 400) == pytest.approx((300 * 0.32 + 100 * 0.35) / 400)
        assert liq.average_fill(asks, 10_000) is None    # more than the book holds

    def test_garbage_levels_are_skipped(self):
        book = {"orderbook_fp": {"no_dollars": [["x", "1"], ["0.5"], ["0.40", "0"], ["0.40", "10"]]}}
        assert liq.asks_from_orderbook(book, "yes") == [(0.6, 10.0)]


# --------------------------------------------------------------- the cap
def _exposure(**kw):
    """A ski instructor: $40k season, $12k lost in a bad one, contract at 30¢."""
    base = dict(wealth=40_000, loss=12_000, price=0.30, gamma=3.0, basis_correlation=0.8)
    base.update(kw)
    return IncomeExposure(**base)


class TestCap:
    def test_no_liquidity_info_means_no_cap_but_a_warning(self):
        plan = hedge_income(_exposure())
        assert plan.liquidity_basis == "unknown" and not plan.liquidity_capped
        assert plan.contracts == plan.contracts_wanted > 1000
        assert any("couldn't check" in w for w in plan.warnings)

    def test_open_interest_cap(self):
        plan = hedge_income(_exposure(liquidity=liq.Liquidity(open_interest=4790)))
        assert plan.liquidity_capped and plan.contracts == 479    # 10% of 4,790
        assert plan.contracts_wanted > plan.contracts
        assert plan.coverage == pytest.approx(479 / plan.contracts_wanted)
        assert any("10% of the contracts" in w for w in plan.warnings)

    def test_order_book_cap_and_realistic_price(self):
        asks = [(0.30, 100.0), (0.31, 150.0), (0.40, 9999.0)]
        plan = hedge_income(_exposure(liquidity=liq.Liquidity(open_interest=1e7, asks_buy=asks)))
        assert plan.contracts == 250 and plan.liquidity_basis == "order book and open interest"
        assert plan.avg_fill_price == pytest.approx((100 * 0.30 + 150 * 0.31) / 250)
        assert any("on offer within 3¢" in w for w in plan.warnings)

    def test_empty_market_proposes_nothing_and_says_so(self):
        plan = hedge_income(_exposure(liquidity=liq.Liquidity(open_interest=0)))
        assert plan.contracts == 0 and plan.cost == 0 and plan.coverage == 0
        assert plan.ce_gain == pytest.approx(0.0)
        assert any("can't hedge you right now" in w for w in plan.warnings)

    def test_capped_hedge_is_never_worse_than_no_hedge(self):
        """Expected utility is concave in the position, so any size between
        zero and the optimum beats doing nothing (at a fair price)."""
        for oi in (10, 500, 3000, 20_000):
            plan = hedge_income(_exposure(price=0.30, market_prob=0.30, liquidity=liq.Liquidity(open_interest=oi)))
            assert plan.ce_gain >= -1e-6, oi

    def test_cap_that_does_not_bind_changes_nothing(self):
        free = hedge_income(_exposure())
        roomy = hedge_income(_exposure(liquidity=liq.Liquidity(open_interest=10_000_000)))
        assert roomy.contracts == free.contracts and not roomy.liquidity_capped
        assert roomy.ce_gain == pytest.approx(free.ce_gain)

    def test_sell_recommendation_is_capped_by_the_other_side(self):
        """A 'sell' buys the other side, so its depth is what limits it."""
        plan_free = hedge_income(_exposure(loss=0.0, own_prob=0.05, confidence=0.9, price=0.30))
        assert plan_free.contracts < 0
        plan = hedge_income(_exposure(
            loss=0.0, own_prob=0.05, confidence=0.9, price=0.30,
            liquidity=liq.Liquidity(asks_buy=[(0.30, 1e6)], asks_sell=[(0.70, 40.0)]),
        ))
        assert plan.contracts == -40 and plan.direction == "sell"


# --------------------------------------------------------------- the API
@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("HONE_KALSHI_LIVE", "1")
    liq._BOOK_CACHE.clear()
    monkeypatch.setattr(liq, "fetch_orderbook", lambda ticker, client=None: BOOK if ticker == "KXTEST-1" else None)
    catalog = {"industries": [{"series": [{"markets": [{"ticker": "KXTEST-1", "open_interest": 2000.0}]}]}]}
    monkeypatch.setattr("hone.prediction.kalshi_client.curated_catalog", lambda live=None: catalog)
    return TestClient(create_app())


BODY = {"gamma": 3.0, "wealth": 40_000, "loss": 12_000, "price": 0.32, "basis_correlation": 0.8}


class TestAPI:
    def test_server_looks_up_liquidity_by_ticker(self, api):
        r = api.post("/api/predict/hedge?asset_class=prediction", json={**BODY, "market_ticker": "KXTEST-1", "side": "yes"})
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["liquidity_capped"] and out["open_interest"] == 2000
        assert out["contracts"] == 200                        # min(500 on book, 10% of 2,000)
        assert out["contracts_wanted"] > 200
        assert out["liquidity_basis"] == "order book and open interest"

    def test_custom_contract_without_ticker_is_unchecked(self, api):
        out = api.post("/api/predict/hedge?asset_class=prediction", json=BODY).json()
        assert out["liquidity_basis"] == "unknown" and not out["liquidity_capped"]

    def test_check_can_be_turned_off(self, api):
        out = api.post("/api/predict/hedge?asset_class=prediction",
                       json={**BODY, "market_ticker": "KXTEST-1", "side": "yes", "check_liquidity": False}).json()
        assert not out["liquidity_capped"]

    def test_order_book_failure_falls_back_to_open_interest(self, api, monkeypatch):
        monkeypatch.setattr(liq, "fetch_orderbook", lambda ticker, client=None: None)
        out = api.post("/api/predict/hedge?asset_class=prediction",
                       json={**BODY, "market_ticker": "KXTEST-1", "side": "yes"}).json()
        assert out["liquidity_basis"] == "open interest" and out["contracts"] == 200
