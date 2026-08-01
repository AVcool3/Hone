"""Entropy pooling: views Black-Litterman cannot express (Meucci, 2008).

Black-Litterman is a good engine with a narrow throat.  A view has to be a
*linear statement about expected returns* — "NVDA returns 18%" — under a
*joint normal* distribution.  That rules out most of what people actually
believe:

* "There's a one-in-three chance Tesla drops more than 20% this year."
* "I don't know where Nvidia lands, but I'm confident it beats Intel."
* "If Bitcoin falls 20%, Ethereum falls at least as far" — the correlation
  everyone discovers during the crash and not before.
* "Vol is going to be higher than the last two years suggest."

None of those is a point estimate of a mean, and two of them are
statements about the shape of the distribution rather than its centre.
Attila Meucci's answer (*Fully Flexible Views: Theory and Practice*, 2008)
is to stop parameterizing the distribution at all.  Represent the market
as scenarios with probabilities, treat each view as a **constraint on
those probabilities**, and find the posterior that satisfies the
constraints while staying as close to the prior as possible — closest in
the relative-entropy (Kullback-Leibler) sense:

    minimize   Σ p̃ᵢ ln(p̃ᵢ / pᵢ)
    subject to Ã p̃ = b  (or ≤ b),  Σ p̃ = 1,  p̃ ≥ 0

Minimum relative entropy is the right notion of "least distortion": it is
the update that adds no information beyond what the views assert, which
is exactly the discipline you want when the views come from a human.

Why this fits the rest of Hone
------------------------------
The posterior is a **reweighted set of the same scenarios**, and
:mod:`hone.optimization.cvar` already optimizes over scenarios.  Chaining
them gives a path from belief to portfolio that never assumes normality
anywhere: empirical scenarios → entropy-pooled posterior → CVaR
optimization.  The Black-Litterman route remains the default because it
is what the confidence calibration is fitted against; this is the route
for views the default cannot represent.

The dual
--------
The primal has one variable per scenario (thousands).  The dual has one
per view (a handful):

    D(λ) = ln( Σᵢ pᵢ exp(−(Ãᵀλ)ᵢ) ) + λᵀb

minimized over λ, free for equality views and non-negative for
inequalities.  The posterior falls out as p̃ᵢ ∝ pᵢ exp(−(Ãᵀλ)ᵢ), which is
an exponential tilt of the prior — the same object that shows up in
importance sampling and large-deviations theory, for the same reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize

#: Below this, the views have collapsed the scenario set so far that the
#: posterior is carried by a handful of paths and nothing computed from it
#: means very much.  Expressed as a fraction of the prior's effective size.
COLLAPSE_WARNING = 0.20


def effective_number_of_scenarios(probabilities: np.ndarray) -> float:
    """exp(entropy) — how many scenarios the distribution effectively uses.

    Meucci's diagnostic, and the honest answer to "were my views too
    strong?".  A uniform prior over 1000 scenarios has an effective size
    of 1000; if stating three views drops that to 40, the posterior is
    being carried by 40 paths and every statistic computed from it —
    including the tail — is that thin.
    """
    p = np.asarray(probabilities, dtype=float)
    p = p[p > 0]
    if p.size == 0:
        return 0.0
    return float(np.exp(-np.sum(p * np.log(p))))


def relative_entropy(posterior: np.ndarray, prior: np.ndarray) -> float:
    """KL(posterior ‖ prior) in nats — the cost of believing the views."""
    q = np.asarray(posterior, dtype=float)
    p = np.asarray(prior, dtype=float)
    mask = q > 0
    return float(np.sum(q[mask] * np.log(q[mask] / p[mask])))


@dataclass
class View:
    """One constraint on the posterior probabilities.

    ``coefficients`` is a per-scenario vector g, and the view asserts
    ``E[g] = target`` (or ``≤`` / ``≥``).  Every view type below reduces
    to this: a mean view uses the asset's returns, a probability view
    uses a 0/1 indicator, a ranking view uses a difference.
    """

    label: str
    coefficients: np.ndarray
    target: float
    kind: str = "eq"  # "eq", "le", "ge"

    def __post_init__(self) -> None:
        self.coefficients = np.asarray(self.coefficients, dtype=float)
        if self.kind not in ("eq", "le", "ge"):
            raise ValueError("kind must be 'eq', 'le' or 'ge'")


# ------------------------------------------------------------ view builders
def mean_view(
    scenarios: pd.DataFrame, ticker: str, expected_return: float
) -> View:
    """E[r_ticker] = q — the only view Black-Litterman can also express."""
    if ticker not in scenarios.columns:
        raise KeyError(f"{ticker} is not in the scenario set")
    return View(
        label=f"E[{ticker}] = {expected_return:+.1%}",
        coefficients=scenarios[ticker].to_numpy(dtype=float),
        target=float(expected_return),
    )


def probability_view(
    scenarios: pd.DataFrame,
    ticker: str,
    threshold: float,
    probability: float,
    below: bool = True,
) -> View:
    """P(r_ticker ≤ threshold) = q — a statement about the tail, not the mean.

    "A one-in-three chance Tesla drops more than 20%" is a view about how
    much mass sits in the left tail.  Black-Litterman has no way to say
    it; here it is an indicator function and a target probability.
    """
    if ticker not in scenarios.columns:
        raise KeyError(f"{ticker} is not in the scenario set")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    r = scenarios[ticker].to_numpy(dtype=float)
    indicator = (r <= threshold) if below else (r >= threshold)
    direction = "≤" if below else "≥"
    return View(
        label=f"P({ticker} {direction} {threshold:+.0%}) = {probability:.0%}",
        coefficients=indicator.astype(float),
        target=float(probability),
    )


def ranking_view(scenarios: pd.DataFrame, winner: str, loser: str) -> View:
    """E[r_winner] ≥ E[r_loser] — conviction without a price target.

    Most opinions are relative.  Someone who is sure Nvidia beats Intel
    but has no idea what either is worth cannot use the main flow at all,
    because it demands a number they do not have and would be inventing.
    """
    for t in (winner, loser):
        if t not in scenarios.columns:
            raise KeyError(f"{t} is not in the scenario set")
    return View(
        label=f"{winner} outperforms {loser}",
        coefficients=(
            scenarios[loser].to_numpy(dtype=float)
            - scenarios[winner].to_numpy(dtype=float)
        ),
        target=0.0,
        kind="le",  # E[loser − winner] ≤ 0
    )


def volatility_view(
    scenarios: pd.DataFrame, ticker: str, volatility: float
) -> View:
    """E[r²] pinned so the implied volatility matches a stated level.

    Uses the raw second moment, so the view is exactly linear in the
    probabilities.  With returns this small the difference from the
    centred variance is immaterial, and keeping it linear is what keeps
    the dual well behaved.
    """
    if ticker not in scenarios.columns:
        raise KeyError(f"{ticker} is not in the scenario set")
    r = scenarios[ticker].to_numpy(dtype=float)
    return View(
        label=f"vol({ticker}) = {volatility:.1%}",
        coefficients=r**2,
        target=float(volatility) ** 2,
    )


def conditional_view(
    scenarios: pd.DataFrame,
    condition_ticker: str,
    condition_threshold: float,
    target_ticker: str,
    target_return: float,
) -> View:
    """E[r_target | r_condition ≤ threshold] = q — a stress relationship.

    "If Bitcoin falls 20%, Ethereum falls at least as far."  This is the
    correlation that matters and the one a full-sample covariance matrix
    understates, because it only appears in the scenarios where the
    condition holds.

    Written as ``E[1{cond}·(r_target − q)] = 0``, which is linear in the
    probabilities; the conditional expectation itself is not.
    """
    for t in (condition_ticker, target_ticker):
        if t not in scenarios.columns:
            raise KeyError(f"{t} is not in the scenario set")
    cond = (
        scenarios[condition_ticker].to_numpy(dtype=float) <= condition_threshold
    ).astype(float)
    if cond.sum() < 5:
        raise ValueError(
            f"only {int(cond.sum())} scenarios satisfy "
            f"{condition_ticker} ≤ {condition_threshold:.0%} — not enough "
            "history to condition on"
        )
    r = scenarios[target_ticker].to_numpy(dtype=float)
    return View(
        label=(
            f"E[{target_ticker} | {condition_ticker} ≤ "
            f"{condition_threshold:+.0%}] = {target_return:+.0%}"
        ),
        coefficients=cond * (r - float(target_return)),
        target=0.0,
    )


# ---------------------------------------------------------------- the solver
@dataclass
class PoolingResult:
    """Posterior scenario probabilities and how much they cost."""

    probabilities: np.ndarray
    prior: np.ndarray
    views: list[str]
    relative_entropy: float
    effective_scenarios: float
    prior_effective_scenarios: float
    converged: bool
    #: Realized value of each view under the posterior, for verification.
    achieved: dict[str, float] = field(default_factory=dict)

    @property
    def confidence_cost(self) -> float:
        """Fraction of the scenario set the views threw away."""
        if self.prior_effective_scenarios <= 0:
            return 0.0
        return 1.0 - self.effective_scenarios / self.prior_effective_scenarios

    @property
    def collapsed(self) -> bool:
        return (
            self.effective_scenarios
            < COLLAPSE_WARNING * self.prior_effective_scenarios
        )

    def summary(self) -> str:
        lines = [
            f"Entropy pooling over {len(self.prior)} scenarios",
            f"  views            : {len(self.views)}",
            f"  relative entropy : {self.relative_entropy:.4f} nats",
            f"  effective scenarios : {self.effective_scenarios:.0f} "
            f"(from {self.prior_effective_scenarios:.0f}, "
            f"{self.confidence_cost:.0%} discarded)",
        ]
        if self.collapsed:
            lines.append(
                "  WARNING: the posterior rests on a small fraction of the "
                "scenario set. The views are either very strong or mutually "
                "awkward; anything computed from this — especially the tail — "
                "is thin."
            )
        for label, value in self.achieved.items():
            lines.append(f"  {label}  ->  achieved {value:+.4f}")
        return "\n".join(lines)


def entropy_pooling(
    views: list[View],
    prior: np.ndarray | None = None,
    n_scenarios: int | None = None,
) -> PoolingResult:
    """Posterior scenario probabilities satisfying ``views``.

    Solved in the dual, which has one variable per view rather than one
    per scenario — a handful instead of thousands.
    """
    if not views:
        if prior is None and n_scenarios is None:
            raise ValueError("need a prior or a scenario count")
        p = (
            np.asarray(prior, dtype=float)
            if prior is not None
            else np.full(int(n_scenarios), 1.0 / int(n_scenarios))
        )
        p = p / p.sum()
        eff = effective_number_of_scenarios(p)
        return PoolingResult(
            probabilities=p, prior=p, views=[], relative_entropy=0.0,
            effective_scenarios=eff, prior_effective_scenarios=eff,
            converged=True,
        )

    T = len(views[0].coefficients)
    if any(len(v.coefficients) != T for v in views):
        raise ValueError("all views must cover the same scenario set")

    p = (
        np.full(T, 1.0 / T)
        if prior is None
        else np.asarray(prior, dtype=float) / np.sum(prior)
    )
    if p.shape != (T,):
        raise ValueError("prior length does not match the scenario count")

    # Normalize every view to "≤" or "=" so the dual bounds are uniform:
    # a "≥" view is the same constraint with both sides negated.
    A, b, bounds = [], [], []
    for v in views:
        if v.kind == "ge":
            A.append(-v.coefficients)
            b.append(-v.target)
            bounds.append((0.0, None))
        else:
            A.append(v.coefficients)
            b.append(v.target)
            bounds.append((0.0, None) if v.kind == "le" else (None, None))
    A = np.vstack(A)
    b = np.asarray(b, dtype=float)
    log_p = np.log(np.clip(p, 1e-300, None))

    def dual(lam: np.ndarray) -> tuple[float, np.ndarray]:
        # log-sum-exp for stability: the tilt exponent is unbounded in lam
        # and a naive exp() overflows well before the optimizer converges.
        x = log_p - A.T @ lam
        m = x.max()
        w = np.exp(x - m)
        z = w.sum()
        value = float(np.log(z) + m + lam @ b)
        q = w / z
        grad = b - A @ q
        return value, grad

    res = minimize(
        dual,
        np.zeros(len(views)),
        jac=True,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 1000, "ftol": 1e-14, "gtol": 1e-10},
    )

    x = log_p - A.T @ res.x
    x -= x.max()
    post = np.exp(x)
    post /= post.sum()

    achieved = {
        v.label: float(post @ v.coefficients) for v in views
    }
    return PoolingResult(
        probabilities=post,
        prior=p,
        views=[v.label for v in views],
        relative_entropy=relative_entropy(post, p),
        effective_scenarios=effective_number_of_scenarios(post),
        prior_effective_scenarios=effective_number_of_scenarios(p),
        converged=bool(res.success),
        achieved=achieved,
    )


def posterior_moments(
    scenarios: pd.DataFrame, probabilities: np.ndarray
) -> tuple[pd.Series, pd.DataFrame]:
    """Probability-weighted mean and covariance of the posterior.

    The bridge back to the variance-based machinery: an entropy-pooled
    posterior can drive the existing mean-variance optimizer instead of
    the CVaR one, which is useful for comparing the two view engines on
    the same footing.
    """
    p = np.asarray(probabilities, dtype=float)
    R = scenarios.to_numpy(dtype=float)
    mu = R.T @ p
    centred = R - mu
    cov = (centred * p[:, None]).T @ centred
    return (
        pd.Series(mu, index=scenarios.columns),
        pd.DataFrame(cov, index=scenarios.columns, columns=scenarios.columns),
    )


def resample_scenarios(
    scenarios: pd.DataFrame,
    probabilities: np.ndarray,
    size: int | None = None,
    seed: int = 0,
) -> pd.DataFrame:
    """Draw an equal-probability scenario set from a weighted one.

    The CVaR optimizer treats every row as equally likely, so a weighted
    posterior has to be resampled before it can be used there.  This adds
    sampling noise on top of an already-thin tail — prefer passing the
    probabilities directly where an estimator supports them.
    """
    rng = np.random.default_rng(seed)
    n = size or len(scenarios)
    idx = rng.choice(len(scenarios), size=n, replace=True, p=probabilities)
    return scenarios.iloc[idx].reset_index(drop=True)
