"""Hone Crypto — the same protocol, applied to digital assets.

This package is deliberately thin. The quantitative engines in
``hone.risk_profile``, ``hone.market_data.covariance``,
``hone.optimization`` and ``hone.hedging`` are asset-class agnostic, so
the crypto variant reuses them **unchanged** and supplies only what is
genuinely different about the asset class:

* a 365-day year (crypto trades every day, so annualization uses 365
  rather than 252 periods);
* a crypto universe and market proxy (BTC instead of SPY);
* Alpaca's crypto market-data endpoints (``BTC/USD`` style symbols);
* crypto-specific historical stress scenarios; and
* stablecoin allocation as the primary hedge, since listed options on
  crypto are not available through the brokerage integration.

The elicitation protocol (Holt-Laury multiple price list -> CRRA
maximum likelihood with Fechner noise -> 50 tiers), the covariance
estimator (Ledoit-Wolf shrinkage), the view-blending model
(Black-Litterman with Idzorek confidence) and the optimizer
(gamma-aware mean-variance) are identical to the equities product by
design — see ``docs/CRYPTO_RESEARCH.md`` for the literature supporting
that choice, and its caveats.
"""

from .universe import (
    CRYPTO_PERIODS_PER_YEAR,
    CRYPTO_STRESS_SCENARIOS,
    DEFAULT_CRYPTO_UNIVERSE,
    MARKET_PROXY,
    STABLECOINS,
    is_stablecoin,
    synthetic_crypto_universe,
)
from .pipeline import rebalance_crypto

__all__ = [
    "CRYPTO_PERIODS_PER_YEAR",
    "CRYPTO_STRESS_SCENARIOS",
    "DEFAULT_CRYPTO_UNIVERSE",
    "MARKET_PROXY",
    "STABLECOINS",
    "is_stablecoin",
    "synthetic_crypto_universe",
    "rebalance_crypto",
]
