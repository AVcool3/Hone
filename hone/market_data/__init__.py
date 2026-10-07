"""Part 2 — market data.

Alpaca paper-trading API client and the covariance matrix calculator.

The covariance calculator (:mod:`hone.market_data.covariance`) is
business-side only: it feeds the optimizer and hedging engine and is not
surfaced directly to end users.
"""

from .alpaca_client import AlpacaClient, AlpacaError, Position
from .covariance import (
    returns_from_prices,
    sample_covariance,
    ewma_covariance,
    shrinkage_covariance,
    portfolio_covariance,
    CovarianceReport,
)

__all__ = [
    "AlpacaClient",
    "AlpacaError",
    "Position",
    "returns_from_prices",
    "sample_covariance",
    "ewma_covariance",
    "shrinkage_covariance",
    "portfolio_covariance",
    "CovarianceReport",
]
