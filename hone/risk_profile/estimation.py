"""Maximum Likelihood estimation of CRRA risk aversion with a noise
parameter (the "precision engine").

Model
-----
Utility is Constant Relative Risk Aversion:

    U(x) = x^(1-gamma) / (1-gamma)        (U(x) = ln x at gamma = 1)

Subjects make mistakes, so choices are probabilistic.  Two error
specifications are provided:

``"luce"``
    The latent choice ratio from the design document,

        Pr(A) = EU_A^(1/mu) / (EU_A^(1/mu) + EU_B^(1/mu)),

    computed in log space as a logistic in (ln EU_A - ln EU_B)/mu.
    Mathematically this requires positive expected utilities, i.e.
    gamma < 1, so the optimizer is bounded accordingly.

``"fechner"`` (default)
    A Fechner/logistic error on the *contextual* utility difference
    (Wilcox 2011): the EU difference is normalized by the utility range
    of the row's payoffs, which keeps the noise parameter comparable
    across stake scales and keeps the likelihood well-defined for every
    gamma (including gamma >= 1):

        Pr(A) = Lambda( (EU_A - EU_B) / (nu * mu) ),
        nu    = U(x_max) - U(x_min) on that row.

The log-likelihood over the choice vector y (1 = chose A) is

    ln L(gamma, mu; y) = sum_i [ y_i ln Pr_i(A) + (1-y_i) ln(1-Pr_i(A)) ]

and is maximized over (gamma, ln mu) with multi-start L-BFGS-B.
Standard errors come from the inverse numerical Hessian at the optimum.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Sequence

import numpy as np
from scipy.optimize import minimize

from .holt_laury import Decision, standard_menu, DEFAULT_SCALES

ErrorSpec = Literal["fechner", "luce"]

_GAMMA_BOUNDS = {"fechner": (-3.0, 5.0), "luce": (-3.0, 0.999)}
_LOG_MU_BOUNDS = (math.log(1e-3), math.log(10.0))


def crra_utility(x: np.ndarray | float, gamma: float) -> np.ndarray:
    """Vectorized CRRA utility for strictly positive payoffs."""
    x = np.asarray(x, dtype=float)
    if np.any(x <= 0):
        raise ValueError("CRRA utility requires strictly positive payoffs")
    if abs(gamma - 1.0) < 1e-10:
        return np.log(x)
    return x ** (1.0 - gamma) / (1.0 - gamma)


def _expected_utilities(decisions: Sequence[Decision], gamma: float):
    """(EU_A, EU_B, x_min, x_max) arrays across decisions."""
    eu_a, eu_b, xmin, xmax = [], [], [], []
    for d in decisions:
        ua = sum(p * crra_utility(x, gamma) for x, p in d.option_a.outcomes())
        ub = sum(p * crra_utility(x, gamma) for x, p in d.option_b.outcomes())
        eu_a.append(float(ua))
        eu_b.append(float(ub))
        payoffs = [d.option_a.high, d.option_a.low, d.option_b.high, d.option_b.low]
        xmin.append(min(payoffs))
        xmax.append(max(payoffs))
    return (np.array(eu_a), np.array(eu_b), np.array(xmin), np.array(xmax))


def choice_probability(
    decisions: Sequence[Decision],
    gamma: float,
    mu: float,
    error_spec: ErrorSpec = "fechner",
) -> np.ndarray:
    """Pr(choose Option A) for each decision under (gamma, mu)."""
    if mu <= 0:
        raise ValueError("mu must be positive")
    eu_a, eu_b, xmin, xmax = _expected_utilities(decisions, gamma)
    if error_spec == "luce":
        if np.any(eu_a <= 0) or np.any(eu_b <= 0):
            raise ValueError(
                "the Luce ratio specification requires positive expected "
                "utilities (gamma < 1); use error_spec='fechner' instead"
            )
        index = (np.log(eu_a) - np.log(eu_b)) / mu
    elif error_spec == "fechner":
        nu = crra_utility(xmax, gamma) - crra_utility(xmin, gamma)
        nu = np.maximum(np.abs(nu), 1e-12)
        index = (eu_a - eu_b) / (nu * mu)
    else:
        raise ValueError(f"unknown error_spec {error_spec!r}")
    # Numerically stable logistic: sigma(x) = exp(-log(1 + exp(-x))).
    prob = np.exp(-np.logaddexp(0.0, -index))
    return np.clip(prob, 1e-12, 1.0 - 1e-12)


def log_likelihood(
    y: np.ndarray,
    decisions: Sequence[Decision],
    gamma: float,
    mu: float,
    error_spec: ErrorSpec = "fechner",
) -> float:
    """ln L(gamma, mu; y) with y_i = 1 if Option A was chosen."""
    p = choice_probability(decisions, gamma, mu, error_spec)
    y = np.asarray(y, dtype=float)
    return float(np.sum(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


@dataclass
class EstimationResult:
    gamma: float
    mu: float
    se_gamma: float | None
    se_mu: float | None
    log_lik: float
    n_obs: int
    converged: bool
    error_spec: str
    gamma_ci95: tuple[float, float] | None = field(default=None)

    def __post_init__(self):
        if self.se_gamma is not None and self.gamma_ci95 is None:
            self.gamma_ci95 = (
                self.gamma - 1.96 * self.se_gamma,
                self.gamma + 1.96 * self.se_gamma,
            )

    def summary(self) -> str:
        lines = [
            "CRRA Maximum Likelihood Estimation",
            "----------------------------------",
            f"observations : {self.n_obs}",
            f"error spec   : {self.error_spec}",
            f"gamma        : {self.gamma:+.4f}"
            + (f"  (s.e. {self.se_gamma:.4f})" if self.se_gamma else ""),
            f"mu (noise)   : {self.mu:.4f}"
            + (f"  (s.e. {self.se_mu:.4f})" if self.se_mu else ""),
            f"log-lik      : {self.log_lik:.4f}",
            f"converged    : {self.converged}",
        ]
        if self.gamma_ci95:
            lines.insert(
                5, f"gamma 95% CI : ({self.gamma_ci95[0]:+.4f}, {self.gamma_ci95[1]:+.4f})"
            )
        return "\n".join(lines)


def _numerical_hessian(f, theta: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    n = len(theta)
    hess = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            ei = np.zeros(n)
            ej = np.zeros(n)
            ei[i] = eps
            ej[j] = eps
            f_pp = f(theta + ei + ej)
            f_pm = f(theta + ei - ej)
            f_mp = f(theta - ei + ej)
            f_mm = f(theta - ei - ej)
            hess[i, j] = hess[j, i] = (f_pp - f_pm - f_mp + f_mm) / (4 * eps * eps)
    return hess


def estimate(
    choices: Sequence[Sequence[str]],
    scales: Sequence[float] = DEFAULT_SCALES,
    error_spec: ErrorSpec = "fechner",
) -> EstimationResult:
    """Estimate (gamma, mu) from choice vectors across stake scales.

    Parameters
    ----------
    choices
        One choice vector per stake scale; each vector is a sequence of
        "A"/"B" strings, one per menu row.
    scales
        Stake multipliers matching ``choices`` (see
        :data:`~hone.risk_profile.holt_laury.DEFAULT_SCALES`).
    error_spec
        "fechner" (default, valid for all gamma) or "luce" (the ratio
        form, valid for gamma < 1).
    """
    if len(choices) != len(scales):
        raise ValueError("need one choice vector per stake scale")

    decisions: list[Decision] = []
    y_list: list[int] = []
    for vec, scale in zip(choices, scales):
        menu = standard_menu(scale)
        if len(vec) != len(menu):
            raise ValueError(
                f"choice vector for scale {scale} has {len(vec)} entries; "
                f"expected {len(menu)}"
            )
        for c, d in zip(vec, menu):
            c = str(c).strip().upper()
            if c not in ("A", "B"):
                raise ValueError(f"choices must be 'A' or 'B', got {c!r}")
            decisions.append(d)
            y_list.append(1 if c == "A" else 0)
    y = np.array(y_list, dtype=float)

    g_lo, g_hi = _GAMMA_BOUNDS[error_spec]

    def neg_ll(theta: np.ndarray) -> float:
        gamma, log_mu = theta
        gamma = float(np.clip(gamma, g_lo, g_hi))
        mu = math.exp(float(np.clip(log_mu, *_LOG_MU_BOUNDS)))
        try:
            return -log_likelihood(y, decisions, gamma, mu, error_spec)
        except (ValueError, FloatingPointError, OverflowError):
            return 1e10

    starts = [
        (0.3, math.log(0.2)),
        (-0.5, math.log(0.2)),
        (1.5, math.log(0.2)) if error_spec == "fechner" else (0.7, math.log(0.2)),
        (0.0, math.log(1.0)),
    ]
    best = None
    for x0 in starts:
        res = minimize(
            neg_ll,
            np.array(x0),
            method="L-BFGS-B",
            bounds=[(g_lo, g_hi), _LOG_MU_BOUNDS],
        )
        if best is None or res.fun < best.fun:
            best = res

    gamma_hat = float(best.x[0])
    mu_hat = float(math.exp(best.x[1]))

    # Standard errors: invert the Hessian of -lnL in (gamma, mu) space.
    se_gamma = se_mu = None
    try:
        def neg_ll_natural(theta):
            g, m = theta
            if m <= 0:
                return 1e10
            return -log_likelihood(y, decisions, g, m, error_spec)

        hess = _numerical_hessian(neg_ll_natural, np.array([gamma_hat, mu_hat]))
        cov = np.linalg.inv(hess)
        # A perfectly consistent subject drives mu to its boundary and
        # flattens the likelihood; the Hessian-based s.e. is meaningless
        # there, so suppress absurd values instead of reporting them.
        if 0 < cov[0, 0] < 100.0:
            se_gamma = float(math.sqrt(cov[0, 0]))
        if 0 < cov[1, 1] < 100.0:
            se_mu = float(math.sqrt(cov[1, 1]))
    except (np.linalg.LinAlgError, ValueError):
        pass

    return EstimationResult(
        gamma=gamma_hat,
        mu=mu_hat,
        se_gamma=se_gamma,
        se_mu=se_mu,
        log_lik=float(-best.fun),
        n_obs=len(y),
        converged=bool(best.success),
        error_spec=error_spec,
    )
