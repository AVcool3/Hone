"""Minimal Black-Scholes pricer used for indicative option-hedge costs.

Prices here size and cost hedge *suggestions*; live quotes from the
broker should always be preferred for execution.
"""

from __future__ import annotations

import math

from scipy.optimize import brentq


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _d1_d2(
    spot: float, strike: float, vol: float, t_years: float, rate: float, div_yield: float
) -> tuple[float, float]:
    d1 = (
        math.log(spot / strike) + (rate - div_yield + 0.5 * vol * vol) * t_years
    ) / (vol * math.sqrt(t_years))
    return d1, d1 - vol * math.sqrt(t_years)


def bs_price(
    option_type: str,
    spot: float,
    strike: float,
    vol: float,
    t_years: float,
    rate: float = 0.04,
    div_yield: float = 0.0,
) -> float:
    """European option price (per share of underlying)."""
    if min(spot, strike, vol, t_years) <= 0:
        raise ValueError("spot, strike, vol and t_years must be positive")
    d1, d2 = _d1_d2(spot, strike, vol, t_years, rate, div_yield)
    df_r = math.exp(-rate * t_years)
    df_q = math.exp(-div_yield * t_years)
    if option_type == "call":
        return spot * df_q * _norm_cdf(d1) - strike * df_r * _norm_cdf(d2)
    if option_type == "put":
        return strike * df_r * _norm_cdf(-d2) - spot * df_q * _norm_cdf(-d1)
    raise ValueError("option_type must be 'call' or 'put'")


def bs_delta(
    option_type: str,
    spot: float,
    strike: float,
    vol: float,
    t_years: float,
    rate: float = 0.04,
    div_yield: float = 0.0,
) -> float:
    d1, _ = _d1_d2(spot, strike, vol, t_years, rate, div_yield)
    df_q = math.exp(-div_yield * t_years)
    if option_type == "call":
        return df_q * _norm_cdf(d1)
    if option_type == "put":
        return df_q * (_norm_cdf(d1) - 1.0)
    raise ValueError("option_type must be 'call' or 'put'")


def implied_zero_cost_call_strike(
    spot: float,
    put_strike: float,
    vol: float,
    t_years: float,
    rate: float = 0.04,
    div_yield: float = 0.0,
) -> float:
    """Call strike whose premium equals the protective put's premium,
    making the collar (long put + short call) approximately zero-cost."""
    put_premium = bs_price("put", spot, put_strike, vol, t_years, rate, div_yield)

    def gap(call_strike: float) -> float:
        return (
            bs_price("call", spot, call_strike, vol, t_years, rate, div_yield)
            - put_premium
        )

    # The call premium falls monotonically in strike; bracket the root.
    lo, hi = spot * 1.0001, spot * 5.0
    if gap(lo) < 0:  # even ATM call is cheaper than the put
        return lo
    if gap(hi) > 0:
        return hi
    return float(brentq(gap, lo, hi))
