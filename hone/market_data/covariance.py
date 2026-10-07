"""Covariance matrix calculator — BUSINESS SIDE ONLY.

This module is internal: its output feeds the MVO / Black-Litterman
optimizer and the hedging engine.  End users never see raw covariance
matrices; they see the resulting weights and hedge suggestions.

Three estimators are provided:

``sample``
    Classic unbiased sample covariance of (log) returns, annualized.
``ewma``
    RiskMetrics-style exponentially weighted covariance (lambda = 0.94
    by default) that reacts faster to recent volatility.
``shrinkage`` (default for the pipeline)
    Ledoit-Wolf (2004) shrinkage toward a scaled identity target.  For
    the short histories retail accounts typically have, the sample
    covariance is noisy and often ill-conditioned; shrinkage keeps the
    optimizer from amplifying estimation error.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def returns_from_prices(prices: pd.DataFrame, kind: str = "log") -> pd.DataFrame:
    """Per-period returns from a price panel (rows: dates, cols: symbols)."""
    prices = prices.sort_index()
    if kind == "log":
        rets = np.log(prices / prices.shift(1))
    elif kind == "simple":
        rets = prices.pct_change()
    else:
        raise ValueError("kind must be 'log' or 'simple'")
    return rets.dropna(how="all").dropna(axis=0)


def sample_covariance(
    returns: pd.DataFrame, annualize: int | None = TRADING_DAYS
) -> pd.DataFrame:
    cov = returns.cov()
    if annualize:
        cov = cov * annualize
    return cov


def ewma_covariance(
    returns: pd.DataFrame,
    lam: float = 0.94,
    annualize: int | None = TRADING_DAYS,
) -> pd.DataFrame:
    """RiskMetrics exponentially weighted covariance."""
    if not 0 < lam < 1:
        raise ValueError("lambda must be in (0, 1)")
    x = returns.to_numpy(dtype=float)
    x = x - x.mean(axis=0, keepdims=True)
    t = x.shape[0]
    weights = lam ** np.arange(t - 1, -1, -1)
    weights /= weights.sum()
    cov = (x * weights[:, None]).T @ x
    if annualize:
        cov = cov * annualize
    return pd.DataFrame(cov, index=returns.columns, columns=returns.columns)


def shrinkage_covariance(
    returns: pd.DataFrame, annualize: int | None = TRADING_DAYS
) -> pd.DataFrame:
    """Ledoit-Wolf (2004) shrinkage toward a scaled identity matrix.

    S* = (1 - a) S + a * m I, with the optimal intensity ``a`` estimated
    from the data ("A Well-Conditioned Estimator for Large-Dimensional
    Covariance Matrices").
    """
    x = returns.to_numpy(dtype=float)
    t, n = x.shape
    if t < 2:
        raise ValueError("need at least two return observations")
    x = x - x.mean(axis=0, keepdims=True)
    s = (x.T @ x) / t

    m = np.trace(s) / n
    d2 = np.sum((s - m * np.eye(n)) ** 2) / n
    b2_sum = 0.0
    for k in range(t):
        xk = x[k][:, None]
        b2_sum += np.sum((xk @ xk.T - s) ** 2) / n
    b2 = min(b2_sum / (t * t), d2)
    intensity = 0.0 if d2 == 0 else b2 / d2

    shrunk = (1.0 - intensity) * s + intensity * m * np.eye(n)
    if annualize:
        shrunk = shrunk * annualize
    return pd.DataFrame(shrunk, index=returns.columns, columns=returns.columns)


@dataclass
class CovarianceReport:
    """Internal bundle passed from the data layer to the optimizer."""

    covariance: pd.DataFrame  # annualized
    returns: pd.DataFrame  # per-period returns used
    mean_returns: pd.Series  # annualized historical means
    method: str
    n_observations: int

    @property
    def volatilities(self) -> pd.Series:
        return pd.Series(
            np.sqrt(np.diag(self.covariance)), index=self.covariance.index
        )

    @property
    def correlation(self) -> pd.DataFrame:
        vol = self.volatilities
        outer = np.outer(vol, vol)
        return self.covariance / outer


def portfolio_covariance(
    prices: pd.DataFrame,
    method: str = "shrinkage",
    return_kind: str = "log",
    annualize: int = TRADING_DAYS,
    ewma_lambda: float = 0.94,
) -> CovarianceReport:
    """End-to-end: price panel -> annualized covariance report."""
    returns = returns_from_prices(prices, kind=return_kind)
    if len(returns) < 20:
        raise ValueError(
            f"only {len(returns)} return observations; need at least 20 for "
            "a usable covariance estimate"
        )
    if method == "sample":
        cov = sample_covariance(returns, annualize)
    elif method == "ewma":
        cov = ewma_covariance(returns, lam=ewma_lambda, annualize=annualize)
    elif method == "shrinkage":
        cov = shrinkage_covariance(returns, annualize)
    else:
        raise ValueError("method must be 'sample', 'ewma' or 'shrinkage'")
    return CovarianceReport(
        covariance=cov,
        returns=returns,
        mean_returns=returns.mean() * annualize,
        method=method,
        n_observations=len(returns),
    )
