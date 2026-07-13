"""Backtesting and success analytics.

Walk-forward backtest that answers the product's core empirical claim:
does matching a portfolio to the investor's risk tier produce better
*risk-adjusted* outcomes — and fewer panic-inducing drawdowns — than the
naive alternatives an individual would otherwise hold?
"""

from .engine import (
    BacktestResult,
    StrategyResult,
    performance_metrics,
    run_backtest,
)

__all__ = [
    "BacktestResult",
    "StrategyResult",
    "performance_metrics",
    "run_backtest",
]
