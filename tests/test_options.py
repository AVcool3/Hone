from datetime import date, timedelta

import pytest

from hone.hedging.hedge import protective_put, zero_cost_collar
from hone.hedging.option_chain import select_contract
from hone.market_data.alpaca_client import _parse_option_symbol


def make_chain(spot=100.0, as_of=None):
    """A small two-expiry chain of puts and calls around spot."""
    as_of = as_of or date.today()
    near = (as_of + timedelta(days=60)).isoformat()
    far = (as_of + timedelta(days=200)).isoformat()
    chain = []
    for expiry in (near, far):
        for strike in range(80, 121, 5):
            # crude but monotone premia: puts richer below spot, calls above
            put_mid = max(spot - strike, 0) * 0.1 + 2.0 + (spot - strike) * -0.02
            call_mid = max(strike - spot, 0) * 0.1 + 2.0 + (strike - spot) * -0.02
            chain.append({"symbol": f"SPY{expiry.replace('-','')[2:]}P{strike*1000:08d}",
                          "type": "put", "strike": float(strike),
                          "expiration": expiry, "mid": max(put_mid, 0.5), "iv": 0.2})
            chain.append({"symbol": f"SPY{expiry.replace('-','')[2:]}C{strike*1000:08d}",
                          "type": "call", "strike": float(strike),
                          "expiration": expiry, "mid": max(call_mid, 0.5), "iv": 0.2})
    return chain


class TestSymbolParsing:
    def test_occ_symbol_roundtrip(self):
        assert _parse_option_symbol("SPY240920P00450000") == ("put", 450.0, "2024-09-20")
        assert _parse_option_symbol("AAPL251219C00200000") == ("call", 200.0, "2025-12-19")

    def test_bad_symbol(self):
        assert _parse_option_symbol("not-an-option") is None


class TestSelectContract:
    def test_picks_nearest_strike_and_expiry(self):
        chain = make_chain()
        q = select_contract(chain, "put", target_strike=94.0, target_days=60)
        assert q is not None
        assert q.type == "put"
        assert q.strike == 95.0  # nearest listed to 94
        assert 55 <= q.days_to_expiry <= 65  # near expiry, not far

    def test_returns_none_when_no_match(self):
        assert select_contract([], "put", 90, 60) is None
        # a chain with only calls yields no put
        calls_only = [c for c in make_chain() if c["type"] == "call"]
        assert select_contract(calls_only, "put", 90, 60) is None

    def test_ignores_expired_and_unpriced(self):
        past = (date.today() - timedelta(days=5)).isoformat()
        chain = [{"symbol": "SPYX", "type": "put", "strike": 90.0,
                  "expiration": past, "mid": 3.0, "iv": 0.2}]
        assert select_contract(chain, "put", 90, 60) is None


class TestChainPricing:
    def test_protective_put_uses_live_quote(self):
        chain = make_chain(spot=100.0)
        model = protective_put(2.0, 100.0, 0.2, chain=None)
        live = protective_put(2.0, 100.0, 0.2, chain=chain)
        assert model.details["pricing_source"] == "black_scholes"
        assert live.details["pricing_source"] == "alpaca_chain"
        assert live.details["contract"] is not None

    def test_collar_uses_live_quotes(self):
        chain = make_chain(spot=100.0)
        live = zero_cost_collar(2.0, 100.0, 0.2, chain=chain)
        assert live.details["pricing_source"] == "alpaca_chain"
        assert live.details["call_strike"] > 100.0
        assert live.est_annual_cost_fraction == 0.0

    def test_falls_back_without_chain(self):
        s = zero_cost_collar(2.0, 100.0, 0.2, chain=None)
        assert s.details["pricing_source"] == "black_scholes"
