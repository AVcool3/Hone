"""Backtesting and success analytics.

Walk-forward backtest that answers the product's core empirical claim:
does matching a portfolio to the investor's risk tier produce better
*risk-adjusted* outcomes — and fewer panic-inducing drawdowns — than the
naive alternatives an individual would otherwise hold?

A second, comparative harness (:mod:`hone.backtest.conviction`) answers
the companion question the Conviction Compiler raises: across a
population of investors with differing risk aversion *and* differing
forecasting skill, does routing their convictions through Black-Litterman
at their self-reported confidence actually beat not using views at all?
"""

from .conviction import (
    InvestorRun,
    run_investor_backtest,
    run_panel,
    summarize,
)
from .engine import (
    BacktestResult,
    StrategyResult,
    performance_metrics,
    run_backtest,
)

__all__ = [
    "BacktestResult",
    "StrategyResult",
    "InvestorRun",
    "performance_metrics",
    "run_backtest",
    "run_investor_backtest",
    "run_panel",
    "summarize",
]
