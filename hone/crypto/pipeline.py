"""Crypto rebalance pipeline — identical protocol, crypto parameters.

Step for step this is the same sequence the equities product runs:

    covariance (Ledoit-Wolf shrinkage)
      -> equilibrium prior from the user's own holdings
      -> Black-Litterman blend of the user's views (Idzorek confidence)
      -> gamma-aware mean-variance optimization
      -> Merton risk budget -> hedge sizing

Only the *inputs* change: a 365-day year, BTC as the market proxy,
crypto-specific stress scenarios, and stablecoins rather than options as
the hedge instrument (crypto options are not available through the
brokerage integration, and the literature identifies stablecoin
allocation as the effective downside tool — see docs/CRYPTO_RESEARCH.md).
"""

from __future__ import annotations

import pandas as pd

from ..hedging.hedge import suggest_hedges
from ..market_data.covariance import portfolio_covariance
from ..optimization.black_litterman import (
    black_litterman_posterior,
    calibrate_delta,
    implied_equilibrium_returns,
)
from ..optimization.mvo import mvo_weights
from ..optimization.views import View
from ..pipeline import RebalanceReport
from .universe import (
    CRYPTO_PERIODS_PER_YEAR,
    CRYPTO_STRESS_SCENARIOS,
    MARKET_PROXY,
    is_stablecoin,
)

#: Stablecoins yield roughly a T-bill rate when lent; used as the
#: risk-free leg of the crypto risk budget.
CRYPTO_RISK_FREE = 0.04


def rebalance_crypto(
    prices: pd.DataFrame,
    current_weights: pd.Series,
    gamma: float,
    views: list[View] | None = None,
    covariance_method: str = "shrinkage",
    tau: float = 0.05,
    long_only: bool = True,
    max_weight: float | None = 0.35,
    market_proxy: str = MARKET_PROXY,
    portfolio_value: float | None = None,
    risk_free: float = CRYPTO_RISK_FREE,
) -> RebalanceReport:
    """Run the standard Hone pipeline over a crypto universe."""
    views = views or []
    universe = list(prices.columns)
    missing = [v.ticker for v in views if v.ticker not in universe]
    if missing:
        raise ValueError(f"views reference assets with no price history: {missing}")

    # Same estimator, annualized on the 365-day crypto calendar.
    report = portfolio_covariance(
        prices, method=covariance_method, annualize=CRYPTO_PERIODS_PER_YEAR
    )
    sigma = report.covariance
    w0 = current_weights.reindex(universe).fillna(0.0)

    delta = calibrate_delta(sigma, w0)

    bl = None
    if views:
        bl = black_litterman_posterior(sigma, w0, views, delta=delta, tau=tau)
        mu, sigma_opt = bl.posterior_mu, bl.posterior_sigma
    else:
        mu = implied_equilibrium_returns(sigma, w0, delta=delta)
        sigma_opt = sigma

    optimized = mvo_weights(
        mu, sigma_opt, gamma, long_only=long_only, max_weight=max_weight,
        current_weights=w0,
    )

    hedge_plan = suggest_hedges(
        optimized.weights,
        sigma,
        mu,
        gamma,
        hedge_instrument=market_proxy,
        hedge_spot=float(prices[market_proxy].iloc[-1])
        if market_proxy in prices.columns
        else 100.0,
        risk_free=risk_free,
        portfolio_value=portfolio_value,
        scenarios=CRYPTO_STRESS_SCENARIOS,
        cash_hedge_label="USDC or another dollar stablecoin",
        # No listed crypto options through the brokerage integration:
        # the hedge set is the stablecoin leg plus a short of the proxy.
        allow_options=False,
    )

    return RebalanceReport(
        gamma=gamma,
        current_weights=w0,
        optimized=optimized,
        black_litterman=bl,
        covariance=report,
        hedge_plan=hedge_plan,
        views=views,
    )


def stablecoin_share(weights: pd.Series) -> float:
    """Fraction of a portfolio already sitting in dollar-pegged assets."""
    return float(sum(w for sym, w in weights.items() if is_stablecoin(str(sym))))
