"""Mean-Variance Optimization keyed to the user's risk-aversion gamma.

The optimizer maximizes the standard quadratic utility

    U(w) = w' mu  -  (gamma / 2) w' Sigma w

subject to full investment (sum w = 1) and optional long-only /
position-size constraints.  Because gamma comes straight from the
questionnaire's MLE estimate, the portfolio's aggressiveness is tied to
measured preferences rather than an arbitrary "moderate/aggressive"
bucket.

Note: quadratic utility with relative risk aversion gamma is the
standard second-order approximation of CRRA expected-utility
maximization for portfolio returns, which is what makes the elicited
CRRA gamma directly usable here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

#: Floor used when a caller passes a risk-neutral or risk-loving gamma.
#: An unbounded-risk optimum is not meaningful for a fully-invested
#: retail portfolio, so gamma is floored at a small positive value.
MIN_GAMMA = 0.05


def portfolio_stats(
    weights: pd.Series, mu: pd.Series, sigma: pd.DataFrame, gamma: float
) -> dict[str, float]:
    w = weights.reindex(mu.index).fillna(0.0).to_numpy()
    m = mu.to_numpy()
    s = sigma.to_numpy()
    exp_ret = float(w @ m)
    var = float(w @ s @ w)
    vol = float(np.sqrt(max(var, 0.0)))
    return {
        "expected_return": exp_ret,
        "volatility": vol,
        "variance": var,
        "utility": exp_ret - 0.5 * gamma * var,
        "sharpe_proxy": exp_ret / vol if vol > 0 else float("nan"),
    }


@dataclass
class MVOResult:
    weights: pd.Series
    gamma: float
    expected_return: float
    volatility: float
    utility: float
    converged: bool

    def summary(self) -> str:
        lines = [
            "Mean-Variance Optimal Portfolio",
            "-------------------------------",
            f"gamma            : {self.gamma:.3f}",
            f"expected return  : {self.expected_return:+.2%}",
            f"volatility       : {self.volatility:.2%}",
            f"certainty equiv. : {self.utility:+.2%}",
            "",
            "weights:",
        ]
        for symbol, w in self.weights.sort_values(ascending=False).items():
            lines.append(f"  {symbol:<8s} {w:+8.2%}")
        return "\n".join(lines)


def mvo_weights(
    mu: pd.Series,
    sigma: pd.DataFrame,
    gamma: float,
    long_only: bool = True,
    max_weight: float | None = None,
    current_weights: pd.Series | None = None,
) -> MVOResult:
    """Solve max_w  w'mu - (gamma/2) w'Sigma w  s.t.  sum(w) = 1.

    Parameters
    ----------
    mu, sigma
        Annualized expected returns and covariance, index-aligned.
    gamma
        Risk-aversion parameter from the questionnaire (floored at
        ``MIN_GAMMA``).
    long_only
        Disallow short positions in the optimized core portfolio
        (shorting is handled separately by the hedging engine).
    max_weight
        Optional per-name cap (e.g. 0.35).
    current_weights
        Optional warm start.
    """
    assets = list(mu.index)
    sigma = sigma.reindex(index=assets, columns=assets)
    if sigma.isna().any().any():
        raise ValueError("sigma is missing entries for some assets in mu")
    gamma_eff = max(float(gamma), MIN_GAMMA)

    m = mu.to_numpy(dtype=float)
    s = sigma.to_numpy(dtype=float)
    n = len(assets)

    def neg_utility(w: np.ndarray) -> float:
        return -(w @ m - 0.5 * gamma_eff * w @ s @ w)

    def grad(w: np.ndarray) -> np.ndarray:
        return -(m - gamma_eff * s @ w)

    if current_weights is not None:
        w0 = current_weights.reindex(assets).fillna(0.0).to_numpy(dtype=float)
        if w0.sum() != 0:
            w0 = w0 / w0.sum()
        else:
            w0 = np.full(n, 1.0 / n)
    else:
        w0 = np.full(n, 1.0 / n)

    upper = max_weight if max_weight is not None else (1.0 if long_only else 3.0)
    lower = 0.0 if long_only else -1.0
    bounds = [(lower, upper)] * n
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    res = minimize(
        neg_utility,
        w0,
        jac=grad,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-12},
    )
    weights = pd.Series(res.x, index=assets)
    weights[weights.abs() < 1e-8] = 0.0
    stats = portfolio_stats(weights, mu, sigma, gamma_eff)
    return MVOResult(
        weights=weights,
        gamma=gamma_eff,
        expected_return=stats["expected_return"],
        volatility=stats["volatility"],
        utility=stats["utility"],
        converged=bool(res.success),
    )


def efficient_frontier(
    mu: pd.Series,
    sigma: pd.DataFrame,
    n_points: int = 25,
    gamma_range: tuple[float, float] = (0.5, 15.0),
    long_only: bool = True,
) -> pd.DataFrame:
    """Trace the frontier by sweeping gamma; useful for showing the user
    where their tier places them relative to other risk levels."""
    gammas = np.geomspace(gamma_range[0], gamma_range[1], n_points)
    rows = []
    for g in gammas:
        r = mvo_weights(mu, sigma, g, long_only=long_only)
        rows.append(
            {"gamma": g, "expected_return": r.expected_return, "volatility": r.volatility}
        )
    return pd.DataFrame(rows)
