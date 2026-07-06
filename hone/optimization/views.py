"""User views: "I like stock X, I'm c% confident it reaches price P".

A :class:`View` converts a target price + horizon into an annualized
expected-return view (the Black-Litterman ``Q`` entry) and carries the
user's confidence level, which the Idzorek mapping in
:mod:`hone.optimization.black_litterman` turns into the view-uncertainty
matrix Omega.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DAYS_PER_YEAR = 365.25


@dataclass(frozen=True)
class View:
    """An absolute view on one ticker.

    Parameters
    ----------
    ticker
        Symbol the view is about.  It does not need to be in the current
        portfolio — the pipeline adds it to the investable universe.
    current_price, target_price
        Today's price and the user's price target.
    confidence
        User confidence in (0, 1].  1.0 means certainty (the optimizer
        will take the view at face value); 0.25 means the view is only
        weakly trusted and the posterior stays close to equilibrium.
    horizon_days
        Time the user expects the target to be reached (default 1 year).
    """

    ticker: str
    current_price: float
    target_price: float
    confidence: float
    horizon_days: float = 365.25

    def __post_init__(self) -> None:
        if self.current_price <= 0 or self.target_price <= 0:
            raise ValueError("prices must be positive")
        if not 0.0 < self.confidence <= 1.0:
            raise ValueError("confidence must be in (0, 1]")
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")

    @property
    def expected_return(self) -> float:
        """Annualized (CAGR) return implied by reaching the target on
        the stated horizon."""
        total = self.target_price / self.current_price
        years = self.horizon_days / DAYS_PER_YEAR
        return float(total ** (1.0 / years) - 1.0)

    def describe(self) -> str:
        return (
            f"{self.ticker}: ${self.current_price:,.2f} -> "
            f"${self.target_price:,.2f} in {self.horizon_days:.0f}d "
            f"({self.expected_return:+.1%}/yr, confidence {self.confidence:.0%})"
        )


def build_view_matrices(
    views: list[View], universe: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Assemble Black-Litterman inputs from user views.

    Returns ``(P, Q, confidences)`` where P is the k x n pick matrix
    (absolute views: one 1 per row), Q the k-vector of annualized view
    returns, and confidences the k-vector of user confidence levels.
    """
    if not views:
        raise ValueError("need at least one view")
    index = {sym: i for i, sym in enumerate(universe)}
    k, n = len(views), len(universe)
    p = np.zeros((k, n))
    q = np.zeros(k)
    conf = np.zeros(k)
    for row, view in enumerate(views):
        if view.ticker not in index:
            raise ValueError(
                f"view ticker {view.ticker!r} is not in the universe {universe}"
            )
        p[row, index[view.ticker]] = 1.0
        q[row] = view.expected_return
        conf[row] = view.confidence
    return p, q, conf
