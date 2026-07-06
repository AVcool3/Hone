"""Hedging engine.

Turns the gamma-implied risk budget into concrete hedge suggestions:
short (beta) hedges and option overlays (protective puts, zero-cost
collars) sized so the hedged portfolio's volatility matches what the
user's risk-aversion parameter says they can tolerate.
"""

from .black_scholes import bs_price, bs_delta, implied_zero_cost_call_strike
from .hedge import (
    HedgePlan,
    HedgeSuggestion,
    gamma_target_volatility,
    portfolio_volatility,
    short_hedge,
    protective_put,
    zero_cost_collar,
    suggest_hedges,
)

__all__ = [
    "bs_price",
    "bs_delta",
    "implied_zero_cost_call_strike",
    "HedgePlan",
    "HedgeSuggestion",
    "gamma_target_volatility",
    "portfolio_volatility",
    "short_hedge",
    "protective_put",
    "zero_cost_collar",
    "suggest_hedges",
]
