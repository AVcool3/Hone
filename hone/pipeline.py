"""End-to-end pipeline: gamma -> covariance -> views -> reweight -> hedge.

The flow mirrors how the product is meant to be used:

1. The questionnaire produces the risk-aversion parameter gamma
   (:mod:`hone.risk_profile`).
2. The user's holdings and price history come from Alpaca; the
   business-side covariance calculator turns history into Sigma
   (:mod:`hone.market_data`).
3. The user names a stock they like with a target price and a
   confidence level; Black-Litterman blends that view with the
   equilibrium implied by their current holdings, and the gamma-aware
   MVO produces the reweighted portfolio (:mod:`hone.optimization`).
4. The hedging engine proposes shorts / option overlays that bring the
   portfolio's risk down to the gamma-implied budget
   (:mod:`hone.hedging`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .market_data.covariance import CovarianceReport, portfolio_covariance
from .optimization.black_litterman import (
    BlackLittermanResult,
    black_litterman_posterior,
    calibrate_delta,
)
from .optimization.mvo import MVOResult, mvo_weights
from .optimization.views import View
from .hedging.hedge import HedgePlan, suggest_hedges


@dataclass
class RebalanceReport:
    gamma: float
    current_weights: pd.Series
    optimized: MVOResult
    black_litterman: BlackLittermanResult | None
    covariance: CovarianceReport
    hedge_plan: HedgePlan
    views: list[View]

    def trade_list(self) -> pd.DataFrame:
        """Weight changes needed to move from current to optimized."""
        current = self.current_weights.reindex(self.optimized.weights.index).fillna(0.0)
        delta = (self.optimized.weights - current).round(6)
        return pd.DataFrame(
            {
                "current": current,
                "target": self.optimized.weights,
                "trade": delta,
            }
        ).sort_values("trade")

    def summary(self) -> str:
        parts = []
        if self.black_litterman is not None:
            parts.append(self.black_litterman.summary())
        parts.append(self.optimized.summary())
        trade_lines = ["Rebalance trades (fraction of portfolio):"]
        for sym, row in self.trade_list().iterrows():
            if abs(row["trade"]) < 1e-4:
                continue
            action = "BUY " if row["trade"] > 0 else "SELL"
            trade_lines.append(
                f"  {action} {sym:<8s} {abs(row['trade']):6.2%} "
                f"({row['current']:+.2%} -> {row['target']:+.2%})"
            )
        if len(trade_lines) == 1:
            trade_lines.append("  (none — portfolio already at target)")
        parts.append("\n".join(trade_lines))
        parts.append(self.hedge_plan.summary())
        return "\n\n".join(parts)


def rebalance(
    prices: pd.DataFrame,
    current_weights: pd.Series,
    gamma: float,
    views: list[View] | None = None,
    covariance_method: str = "shrinkage",
    tau: float = 0.05,
    long_only: bool = True,
    max_weight: float | None = None,
    hedge_instrument: str = "SPY",
    hedge_spot: float = 100.0,
    risk_free: float = 0.04,
    portfolio_value: float | None = None,
    option_chain: list[dict] | None = None,
) -> RebalanceReport:
    """Run steps 2-4 of the pipeline.

    Parameters
    ----------
    prices
        Price history for the full universe: current holdings plus any
        tickers named in views (columns = symbols).
    current_weights
        The user's current portfolio weights (new view tickers may be
        absent; they are treated as weight 0).
    gamma
        Risk-aversion parameter from the questionnaire.
    views
        Optional user views (ticker, target price, confidence).
    """
    views = views or []
    universe = list(prices.columns)
    missing = [v.ticker for v in views if v.ticker not in universe]
    if missing:
        raise ValueError(f"views reference tickers with no price history: {missing}")

    report = portfolio_covariance(prices, method=covariance_method)
    sigma = report.covariance
    w0 = current_weights.reindex(universe).fillna(0.0)

    # Market risk aversion for reverse optimization, calibrated to a
    # target market Sharpe (see black_litterman.calibrate_delta).
    delta = calibrate_delta(sigma, w0)

    bl: BlackLittermanResult | None = None
    if views:
        bl = black_litterman_posterior(sigma, w0, views, delta=delta, tau=tau)
        mu, sigma_opt = bl.posterior_mu, bl.posterior_sigma
    else:
        # No views: fall back to equilibrium returns implied by current
        # holdings (pure risk-based rebalance).
        from .optimization.black_litterman import implied_equilibrium_returns

        mu = implied_equilibrium_returns(sigma, w0, delta=delta)
        sigma_opt = sigma

    optimized = mvo_weights(
        mu,
        sigma_opt,
        gamma,
        long_only=long_only,
        max_weight=max_weight,
        current_weights=w0,
    )

    hedge_plan = suggest_hedges(
        optimized.weights,
        sigma,
        mu,
        gamma,
        hedge_instrument=hedge_instrument,
        hedge_spot=hedge_spot,
        risk_free=risk_free,
        portfolio_value=portfolio_value,
        option_chain=option_chain,
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


def synthetic_universe(
    symbols: list[str] | None = None,
    n_days: int = 504,
    seed: int = 7,
) -> tuple[pd.DataFrame, pd.Series]:
    """Synthetic price history + weights for demos and tests (no
    network or API keys required)."""
    symbols = symbols or ["AAPL", "MSFT", "SPY", "TSLA", "JNJ"]
    rng = np.random.default_rng(seed)
    n = len(symbols)
    annual_mu = rng.uniform(0.04, 0.16, n)
    annual_vol = rng.uniform(0.15, 0.45, n)
    corr = np.full((n, n), 0.45)
    np.fill_diagonal(corr, 1.0)
    cov = corr * np.outer(annual_vol, annual_vol) / 252.0
    rets = rng.multivariate_normal(annual_mu / 252.0, cov, size=n_days)
    # Pin the sample mean to the intended drift: over ~2 years the noise
    # on mean returns would otherwise dwarf the 4-16% targets and make
    # demo output erratic.
    rets = rets - rets.mean(axis=0, keepdims=True) + annual_mu / 252.0
    prices = pd.DataFrame(
        100.0 * np.exp(np.cumsum(rets, axis=0)),
        columns=symbols,
        index=pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n_days),
    )
    weights = pd.Series(rng.dirichlet(np.ones(n)), index=symbols)
    return prices, weights
