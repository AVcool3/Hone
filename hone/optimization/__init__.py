"""Part 3 — portfolio optimization.

Mean-Variance Optimization (gamma-aware), user views, and
Black-Litterman blending of views into equilibrium returns.
"""

from .mvo import MVOResult, mvo_weights, portfolio_stats, efficient_frontier
from .views import View, build_view_matrices
from .black_litterman import (
    implied_equilibrium_returns,
    idzorek_omega,
    black_litterman_posterior,
    BlackLittermanResult,
)

__all__ = [
    "MVOResult",
    "mvo_weights",
    "portfolio_stats",
    "efficient_frontier",
    "View",
    "build_view_matrices",
    "implied_equilibrium_returns",
    "idzorek_omega",
    "black_litterman_posterior",
    "BlackLittermanResult",
]
