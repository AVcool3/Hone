"""Black-Litterman blending of user views with market equilibrium.

Pipeline:

1. Reverse-optimize the equilibrium (prior) returns from the user's
   current holdings:  Pi = delta * Sigma * w.  Using the user's own
   weights as the "market" portfolio means "no views" reproduces roughly
   what they already hold, and each view then tilts from there.
2. Convert user confidence c in (0, 1] into the view-uncertainty matrix
   Omega with Idzorek's mapping:

       omega_k = (1/c_k - 1) * tau * p_k' Sigma p_k

   c -> 1 gives omega -> 0 (view taken as certain); c -> 0 gives
   omega -> inf (view ignored).
3. Posterior mean returns (master formula):

       mu_BL = [ (tau Sigma)^-1 + P' Omega^-1 P ]^-1
               [ (tau Sigma)^-1 Pi + P' Omega^-1 Q ]

   and posterior covariance Sigma + M where
   M = [ (tau Sigma)^-1 + P' Omega^-1 P ]^-1.

The posterior mean and covariance then feed the gamma-aware MVO to
produce the reweighted portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .views import View, build_view_matrices

DEFAULT_TAU = 0.05


#: Long-run Sharpe ratio assumed for the *market* portfolio when
#: calibrating delta. ~0.4 is the standard equity-market figure and is
#: used for every asset class so the protocol stays identical.
TARGET_MARKET_SHARPE = 0.40


def calibrate_delta(
    sigma: pd.DataFrame,
    weights: pd.Series,
    target_sharpe: float = TARGET_MARKET_SHARPE,
    floor: float = 0.05,
) -> float:
    """Market risk-aversion implied by a target market Sharpe ratio.

    Reverse optimization needs the *market's* aggregate risk aversion,
    which is not the individual's gamma. Requiring the market portfolio
    to price at a given Sharpe ratio S gives premium = S * sigma_m and
    therefore

        delta = premium / sigma_m^2 = S / sigma_m.

    This matters enormously across asset classes. Using the investor's
    own gamma instead makes the implied equilibrium return scale with
    variance, so on crypto (variances ~15x equities) the prior implies
    returns near +100%/yr and a genuinely bullish view registers as
    bearish. Calibrating to a Sharpe target keeps the prior sane for any
    volatility level: sigma_m ~ 16% gives delta ~ 2.5 (the canonical
    equity value), sigma_m ~ 60% gives delta ~ 0.67.
    """
    w = weights.reindex(sigma.index).fillna(0.0).to_numpy()
    var_m = float(w @ sigma.to_numpy() @ w)
    if var_m <= 0:
        return max(floor, target_sharpe)
    sigma_m = var_m**0.5
    return max(float(target_sharpe / sigma_m), floor)


def implied_equilibrium_returns(
    sigma: pd.DataFrame, weights: pd.Series, delta: float
) -> pd.Series:
    """Reverse optimization: Pi = delta * Sigma * w."""
    w = weights.reindex(sigma.index).fillna(0.0).to_numpy()
    pi = delta * sigma.to_numpy() @ w
    return pd.Series(pi, index=sigma.index, name="pi")


def idzorek_omega(
    p: np.ndarray, sigma: np.ndarray, confidences: np.ndarray, tau: float
) -> np.ndarray:
    """Diagonal Omega from user confidence levels (Idzorek 2005)."""
    k = p.shape[0]
    omega = np.zeros((k, k))
    for i in range(k):
        var_view = float(p[i] @ sigma @ p[i]) * tau
        c = float(confidences[i])
        if c >= 1.0:
            # Certain view: tiny but non-zero uncertainty keeps the
            # posterior algebra well-conditioned.
            omega[i, i] = var_view * 1e-6
        else:
            omega[i, i] = (1.0 / c - 1.0) * var_view
    return omega


@dataclass
class BlackLittermanResult:
    posterior_mu: pd.Series  # annualized posterior expected returns
    posterior_sigma: pd.DataFrame  # Sigma + M (for use in MVO)
    prior_mu: pd.Series  # equilibrium returns Pi
    views: list[View]
    tau: float
    delta: float

    def summary(self) -> str:
        lines = [
            "Black-Litterman Posterior Returns (annualized)",
            "----------------------------------------------",
            f"tau = {self.tau}, delta (risk aversion) = {self.delta:.3f}",
            "",
            f"{'asset':<8s} {'prior':>9s} {'posterior':>10s} {'tilt':>8s}",
        ]
        for sym in self.posterior_mu.index:
            prior = self.prior_mu[sym]
            post = self.posterior_mu[sym]
            lines.append(
                f"{sym:<8s} {prior:>+9.2%} {post:>+10.2%} {post - prior:>+8.2%}"
            )
        lines.append("")
        lines.append("views:")
        for v in self.views:
            lines.append(f"  {v.describe()}")
        return "\n".join(lines)


def black_litterman_posterior(
    sigma: pd.DataFrame,
    market_weights: pd.Series,
    views: list[View],
    delta: float,
    tau: float = DEFAULT_TAU,
) -> BlackLittermanResult:
    """Blend user views into equilibrium returns.

    Parameters
    ----------
    sigma
        Annualized covariance over the full universe (current holdings
        plus any newly viewed tickers).
    market_weights
        Prior portfolio weights over the same universe (new tickers get
        weight 0, so the prior is "don't hold it" and the view supplies
        the reason to buy).
    views
        User views (ticker, target price, confidence).
    delta
        Risk-aversion used for reverse optimization.  Using the user's
        elicited gamma keeps prior and posterior on the same preference
        scale.
    tau
        Scalar uncertainty of the prior (typically 0.01-0.1).
    """
    if delta <= 0:
        raise ValueError("delta must be positive")
    universe = list(sigma.index)
    s = sigma.to_numpy(dtype=float)

    pi = implied_equilibrium_returns(sigma, market_weights, delta)
    p, q, conf = build_view_matrices(views, universe)
    omega = idzorek_omega(p, s, conf, tau)

    tau_sigma_inv = np.linalg.inv(tau * s)
    omega_inv = np.linalg.inv(omega)
    m_inv = tau_sigma_inv + p.T @ omega_inv @ p
    m = np.linalg.inv(m_inv)
    mu_post = m @ (tau_sigma_inv @ pi.to_numpy() + p.T @ omega_inv @ q)

    return BlackLittermanResult(
        posterior_mu=pd.Series(mu_post, index=universe, name="mu_bl"),
        posterior_sigma=pd.DataFrame(s + m, index=universe, columns=universe),
        prior_mu=pi,
        views=views,
        tau=tau,
        delta=delta,
    )
