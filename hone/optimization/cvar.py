"""Mean-CVaR optimization (Rockafellar & Uryasev, 2000).

Variance punishes upside and downside identically, and it is estimated
from a covariance matrix that assumes the joint distribution is captured
by second moments.  Neither assumption survives contact with the things
that actually hurt retail investors: returns are left-skewed and
fat-tailed, and correlations converge toward one exactly when
diversification is being relied on.  A portfolio can look well-behaved in
Σ and still have a tail that takes half of it.

Conditional Value-at-Risk is the average loss in the worst ``1 − β`` of
outcomes.  It asks a different question — *when this goes badly, how badly*
— and it reads the empirical return distribution directly, so skew, fat
tails and crash co-movement are in the answer rather than assumed away.
CVaR is also coherent in the Artzner et al. (1999) sense, which VaR is
not: VaR can penalize diversification, telling an investor that splitting
a position increased their risk.

The reason this is tractable at all is Rockafellar and Uryasev's result:
for a set of scenarios, minimizing

    F_β(w, ζ) = ζ + 1/((1−β)T) · Σ_t max(0, −r_t·w − ζ)

over ``w`` and the auxiliary ``ζ`` jointly minimizes CVaR, and the
optimal ζ is the VaR.  The max() linearizes with one slack variable per
scenario, so the whole thing is a linear program — no local optima, no
convergence tuning, and it stays a linear program when an expected-return
term is added.

Where gamma comes in
--------------------
Hone's entire premise is that the risk knob is measured, not chosen, so a
CVaR mode with a hand-picked risk-aversion coefficient would be a
different product wearing the same clothes.  :func:`kappa_from_gamma`
maps the elicited γ into the mean-CVaR trade-off by matching the marginal
rate of substitution between return and risk at a reference volatility —
see that function for what the match does and does not claim.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.stats import norm

#: Default tail probability. 95% is the retail-legible choice: "the worst
#: one month in twenty". 99% is the regulatory convention but needs far
#: more history to estimate — at 500 daily observations the 99% tail is
#: five points, and an average of five points is not an estimate.
DEFAULT_BETA = 0.95

#: Minimum scenarios before a CVaR estimate means anything. At beta=0.95
#: this leaves ~13 observations in the tail, which is thin but honest;
#: below it the number is noise wearing a decimal point.
MIN_SCENARIOS = 250


def _tail_count(n_scenarios: int, beta: float) -> int:
    return max(1, int(round((1.0 - beta) * n_scenarios)))


def historical_scenarios(
    prices: pd.DataFrame, periods_per_year: int = 252, horizon: int = 1
) -> pd.DataFrame:
    """Overlapping ``horizon``-period simple returns, one row per scenario.

    Simple (not log) returns, because portfolio return is a weighted sum
    of simple returns and CVaR is a statement about portfolio wealth.
    Using log returns here would make the linear program describe a
    portfolio nobody holds.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least 1 period")
    px = prices.dropna(how="all").ffill().dropna()
    rets = px.pct_change(horizon).dropna()
    if rets.empty:
        raise ValueError("not enough price history to build scenarios")
    return rets


def cvar_of_weights(
    scenarios: pd.DataFrame,
    weights: pd.Series,
    beta: float = DEFAULT_BETA,
) -> float:
    """CVaR of a given portfolio, as a positive loss fraction.

    Reported per scenario period — annualize by scaling the scenarios,
    not the answer, since a tail average does not scale by √t.
    """
    w = weights.reindex(scenarios.columns).fillna(0.0).to_numpy(dtype=float)
    port = scenarios.to_numpy(dtype=float) @ w
    losses = -port
    k = _tail_count(len(losses), beta)
    worst = np.sort(losses)[-k:]
    return float(worst.mean())


def var_of_weights(
    scenarios: pd.DataFrame,
    weights: pd.Series,
    beta: float = DEFAULT_BETA,
) -> float:
    """Value-at-Risk: the loss the tail starts at. Reported for context —
    it is what most people mean by "worst case", and showing it beside
    CVaR is the clearest way to make the difference concrete."""
    w = weights.reindex(scenarios.columns).fillna(0.0).to_numpy(dtype=float)
    losses = -(scenarios.to_numpy(dtype=float) @ w)
    return float(np.quantile(losses, beta))


def kappa_from_gamma(
    gamma: float, reference_volatility: float, beta: float = DEFAULT_BETA
) -> float:
    """Translate risk aversion γ into a mean-CVaR trade-off coefficient.

    The mean-variance objective ``μ − (γ/2)σ²`` gives up return for risk
    at a rate ``dU/dσ = −γσ``.  The mean-CVaR objective ``μ − κ·CVaR``
    gives it up at ``−κ·k``, where ``k = φ(z_β)/(1−β)`` is the factor
    linking CVaR to σ *for a normal distribution*.  Setting the two equal
    at a reference volatility gives

        κ = γ · σ_ref / k

    ``reference_volatility`` must be in the same period units as the
    scenarios (daily scenarios, daily sigma).  Mean-variance weights are
    horizon-invariant because both terms scale linearly in time;
    mean-CVaR weights are not, since CVaR scales roughly with the square
    root of time, so the horizon has to be pinned down somewhere and this
    is where.

    This is a **local** match, and the claim is deliberately narrow: it
    makes the two objectives trade return against risk at the same rate
    for a portfolio of about that volatility, so a user's γ means roughly
    the same thing in both modes.  It is not an equivalence — the whole
    point of CVaR is that the distribution is not normal, and where the
    two modes disagree, that disagreement is the information.
    """
    z = norm.ppf(beta)
    k = norm.pdf(z) / (1.0 - beta)
    sigma_ref = max(float(reference_volatility), 1e-6)
    return max(float(gamma) * sigma_ref / k, 1e-6)


@dataclass
class CVaRResult:
    weights: pd.Series
    beta: float
    #: Expected CVaR and VaR of the solution, per scenario period.
    cvar: float
    var: float
    expected_return: float
    #: The trade-off coefficient actually used (0 for pure minimum-CVaR).
    kappa: float
    n_scenarios: int
    converged: bool
    #: How many scenarios sit in the averaged tail. Small is a warning.
    tail_scenarios: int = 0

    def summary(self) -> str:
        return (
            f"CVaR({self.beta:.0%}) portfolio over {self.n_scenarios} scenarios\n"
            f"  expected return : {self.expected_return:+.2%} per period\n"
            f"  VaR             : {self.var:.2%}  (loss the tail starts at)\n"
            f"  CVaR            : {self.cvar:.2%}  "
            f"(average of the worst {self.tail_scenarios})\n"
            f"  weights         : "
            + ", ".join(
                f"{k} {v:.1%}" for k, v in self.weights.items() if abs(v) > 5e-4
            )
        )


def mean_cvar_weights(
    scenarios: pd.DataFrame,
    beta: float = DEFAULT_BETA,
    kappa: float = 0.0,
    mu: pd.Series | None = None,
    long_only: bool = True,
    max_weight: float | None = None,
    min_return: float | None = None,
) -> CVaRResult:
    """Maximize ``w'μ − κ·CVaR_β(w)`` as a linear program.

    With ``kappa = 0`` this is the pure minimum-CVaR portfolio — the
    risk-first mode, which ignores expected returns entirely.  That is
    often the honest choice: expected returns are the least reliable
    input in the whole pipeline, and a portfolio built without them
    cannot be wrecked by getting them wrong.

    Parameters
    ----------
    scenarios
        One row per scenario, one column per asset, simple returns.
    mu
        Per-period expected returns.  Defaults to the scenario means;
        pass the Black-Litterman posterior to let views drive the tilt.
    min_return
        Optional floor on ``w'μ`` — the other classical formulation,
        minimum CVaR subject to a required return.
    """
    assets = list(scenarios.columns)
    n, T = len(assets), len(scenarios)
    if n == 0:
        raise ValueError("no assets to optimize")
    if T < 2:
        raise ValueError("need at least two scenarios")
    if not 0.5 <= beta < 1.0:
        raise ValueError("beta must be in [0.5, 1)")

    R = scenarios.to_numpy(dtype=float)
    m = (
        scenarios.mean().to_numpy(dtype=float)
        if mu is None
        else mu.reindex(assets).fillna(0.0).to_numpy(dtype=float)
    )

    # Decision vector: [w (n) | zeta (1) | u (T)].
    # Rockafellar-Uryasev: CVaR = min over zeta of
    #   zeta + 1/((1-beta)T) * sum_t max(0, -r_t.w - zeta)
    # with u_t >= 0 absorbing the max(). At the optimum zeta is the VaR.
    scale = 1.0 / ((1.0 - beta) * T)
    c = np.concatenate([-m + 0.0, [kappa], np.full(T, kappa * scale)])
    if kappa == 0.0:
        # Pure minimum CVaR: drop the return term entirely rather than
        # letting a zero coefficient leave mu silently in the objective.
        c = np.concatenate([np.zeros(n), [1.0], np.full(T, scale)])

    # -r_t.w - zeta - u_t <= 0
    A_ub = np.hstack([-R, -np.ones((T, 1)), -np.eye(T)])
    b_ub = np.zeros(T)

    if min_return is not None:
        A_ub = np.vstack([A_ub, np.concatenate([-m, [0.0], np.zeros(T)])])
        b_ub = np.concatenate([b_ub, [-float(min_return)]])

    A_eq = np.zeros((1, n + 1 + T))
    A_eq[0, :n] = 1.0
    b_eq = np.array([1.0])

    upper = max_weight if max_weight is not None else (1.0 if long_only else 3.0)
    lower = 0.0 if long_only else -1.0
    bounds = (
        [(lower, upper)] * n
        + [(None, None)]          # zeta is free: VaR can be either sign
        + [(0.0, None)] * T       # u_t >= 0
    )

    res = linprog(
        c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
        bounds=bounds, method="highs",
    )
    if not res.success or res.x is None:
        raise ValueError(f"CVaR optimization failed: {res.message}")

    w = pd.Series(res.x[:n], index=assets)
    w[w.abs() < 1e-8] = 0.0
    # Renormalize against accumulated LP tolerance rather than trusting it.
    total = w.sum()
    if abs(total - 1.0) > 1e-9 and total != 0:
        w = w / total

    return CVaRResult(
        weights=w,
        beta=beta,
        cvar=cvar_of_weights(scenarios, w, beta),
        var=var_of_weights(scenarios, w, beta),
        expected_return=float(w.to_numpy() @ m),
        kappa=float(kappa),
        n_scenarios=T,
        converged=True,
        tail_scenarios=_tail_count(T, beta),
    )


def min_cvar_weights(
    scenarios: pd.DataFrame,
    beta: float = DEFAULT_BETA,
    long_only: bool = True,
    max_weight: float | None = None,
    min_return: float | None = None,
) -> CVaRResult:
    """The risk-first portfolio: minimize CVaR, ignore expected returns."""
    return mean_cvar_weights(
        scenarios, beta=beta, kappa=0.0, long_only=long_only,
        max_weight=max_weight, min_return=min_return,
    )


def cvar_gamma_weights(
    scenarios: pd.DataFrame,
    gamma: float,
    mu: pd.Series | None = None,
    beta: float = DEFAULT_BETA,
    long_only: bool = True,
    max_weight: float | None = None,
    reference_volatility: float | None = None,
) -> CVaRResult:
    """Mean-CVaR at the trade-off implied by the user's elicited gamma."""
    if reference_volatility is None:
        # The equal-weight portfolio's own scenario volatility: a
        # neutral reference that does not depend on the answer.
        eq = pd.Series(1.0 / len(scenarios.columns), index=scenarios.columns)
        reference_volatility = float(
            (scenarios.to_numpy() @ eq.to_numpy()).std(ddof=1)
        )
    kappa = kappa_from_gamma(gamma, reference_volatility, beta)
    return mean_cvar_weights(
        scenarios, beta=beta, kappa=kappa, mu=mu,
        long_only=long_only, max_weight=max_weight,
    )


def tail_comparison(
    scenarios: pd.DataFrame,
    portfolios: dict[str, pd.Series],
    beta: float = DEFAULT_BETA,
) -> pd.DataFrame:
    """Side-by-side tail statistics for several candidate portfolios.

    This is the whole argument for the mode in one table: two portfolios
    with near-identical volatility can have materially different tails,
    and the variance-optimal one is not usually the better of the two on
    that measure.
    """
    rows = []
    for name, w in portfolios.items():
        wv = w.reindex(scenarios.columns).fillna(0.0)
        port = scenarios.to_numpy(dtype=float) @ wv.to_numpy(dtype=float)
        rows.append(
            {
                "portfolio": name,
                "mean": float(port.mean()),
                "volatility": float(port.std(ddof=1)),
                "var": var_of_weights(scenarios, wv, beta),
                "cvar": cvar_of_weights(scenarios, wv, beta),
                "worst": float(port.min()),
                "skew": float(pd.Series(port).skew()),
            }
        )
    return pd.DataFrame(rows).set_index("portfolio")
