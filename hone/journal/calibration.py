"""Scoring a forecaster and learning what their confidence actually means.

The Brier score (Brier 1950) is the mean squared error of a probabilistic
forecast, and Murphy's (1973) decomposition splits it into three parts that
answer three different questions:

    BS = reliability − resolution + uncertainty

*Reliability* asks whether 70% means 70% — lower is better, zero is perfect
calibration.  *Resolution* asks whether the forecaster discriminates at all,
i.e. whether the events they call likely actually happen more often than the
ones they call unlikely — higher is better, and it is the part that cannot be
faked by simply predicting the base rate.  *Uncertainty* is the variance of
the outcomes themselves and is a property of the world, not the forecaster.

The distinction matters for what Hone does with the score.  A user with poor
reliability but good resolution knows something and states it badly: their
confidence should be rescaled, not discarded.  A user with zero resolution
knows nothing, and no rescaling helps — their views should be pulled toward
equilibrium regardless of what number they type.

The calibration map is a one-parameter-pair logistic regression in log-odds
space, shrunk toward the identity by a pseudo-count.  Shrinkage is not
optional: a user with six resolved predictions has, statistically, told us
almost nothing, and a tool that responded to that by halving their confidence
would be substituting its own noise for theirs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize

#: Pseudo-observations of a perfectly calibrated forecaster mixed into every
#: fit.  With n real resolutions the fitted map gets weight n/(n+K), so ~10
#: predictions moves you a third of the way and ~40 moves you most of it.
#: Chosen so that a user cannot be told they are overconfident on the strength
#: of a handful of coin flips.
SHRINKAGE_PSEUDO_COUNT = 20.0

#: Below this many resolved predictions the report is informational only and
#: :func:`apply_calibration` returns the stated confidence untouched.
MIN_FOR_ADJUSTMENT = 5

_EPS = 1e-6


def _logit(p: np.ndarray | float) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), _EPS, 1 - _EPS)
    return np.log(p / (1 - p))


def _sigmoid(x: np.ndarray | float) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


# ------------------------------------------------------------------- scoring
def brier_score(confidences, outcomes) -> float:
    """Mean squared error of stated probabilities against binary outcomes.

    0 is perfect, 0.25 is what you get by always saying 50%, and 1 is
    perfectly confident and perfectly wrong every time.
    """
    p = np.asarray(confidences, dtype=float)
    o = np.asarray(outcomes, dtype=float)
    if p.size == 0:
        return float("nan")
    return float(np.mean((p - o) ** 2))


def reliability_bins(confidences, outcomes, n_bins: int = 5) -> list[dict]:
    """Observed hit rate per confidence bucket — the reliability curve.

    Five buckets by default, not ten: retail users will have tens of
    resolved predictions, not thousands, and ten buckets of three
    observations each is a chart of pure noise.
    """
    p = np.asarray(confidences, dtype=float)
    o = np.asarray(outcomes, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    out: list[dict] = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi) if i < n_bins - 1 else (p >= lo) & (p <= hi)
        n = int(mask.sum())
        out.append(
            {
                "lower": float(lo),
                "upper": float(hi),
                "n": n,
                "mean_confidence": float(p[mask].mean()) if n else None,
                "hit_rate": float(o[mask].mean()) if n else None,
            }
        )
    return out


def brier_decomposition(confidences, outcomes, n_bins: int = 5) -> dict:
    """Murphy's reliability / resolution / uncertainty split.

    Computed on the same bins as the reliability curve, so the numbers and
    the chart always agree.  The decomposition is exact only for binned
    forecasts, which is why ``brier`` here may differ slightly from
    :func:`brier_score` on the raw probabilities; both are returned.
    """
    p = np.asarray(confidences, dtype=float)
    o = np.asarray(outcomes, dtype=float)
    n = p.size
    if n == 0:
        return {
            "brier": float("nan"),
            "reliability": float("nan"),
            "resolution": float("nan"),
            "uncertainty": float("nan"),
            "skill_vs_base_rate": float("nan"),
        }

    base = float(o.mean())
    uncertainty = base * (1 - base)

    reliability = 0.0
    resolution = 0.0
    for b in reliability_bins(p, o, n_bins):
        if not b["n"]:
            continue
        w = b["n"] / n
        reliability += w * (b["mean_confidence"] - b["hit_rate"]) ** 2
        resolution += w * (b["hit_rate"] - base) ** 2

    raw = brier_score(p, o)
    # Positive skill means the forecaster beats always predicting the base
    # rate — the honest benchmark, since matching it requires no knowledge.
    skill = 1.0 - raw / uncertainty if uncertainty > 0 else float("nan")
    return {
        "brier": raw,
        "binned_brier": reliability - resolution + uncertainty,
        "reliability": reliability,
        "resolution": resolution,
        "uncertainty": uncertainty,
        "base_rate": base,
        "skill_vs_base_rate": skill,
    }


# --------------------------------------------------------------- calibration
@dataclass
class CalibrationReport:
    """What a user's forecasting record says about their confidence."""

    n: int
    brier: float
    base_rate: float
    mean_confidence: float
    #: Logistic map in log-odds space, already shrunk toward the identity.
    intercept: float
    slope: float
    reliability: float
    resolution: float
    uncertainty: float
    skill_vs_base_rate: float
    bins: list[dict] = field(default_factory=list)
    #: True once there is enough history to act on rather than merely display.
    actionable: bool = False
    #: Direction-only accuracy, reported alongside the harder target event.
    direction_hit_rate: float | None = None
    summary: str = ""

    def adjust(self, stated_confidence: float) -> float:
        return apply_calibration(stated_confidence, self)


def fit_calibration(
    confidences,
    outcomes,
    direction_hits=None,
    pseudo_count: float = SHRINKAGE_PSEUDO_COUNT,
) -> CalibrationReport:
    """Fit stated confidence -> historically justified confidence.

    The model is ``logit(p_true) = a + b · logit(p_stated)``, fitted by
    maximum likelihood and then pulled toward the identity map (a=0, b=1) in
    proportion to how little data supports it.
    """
    p = np.clip(np.asarray(confidences, dtype=float), _EPS, 1 - _EPS)
    o = np.asarray(outcomes, dtype=float)
    n = int(p.size)

    decomp = brier_decomposition(p, o)
    dir_rate = (
        float(np.mean(np.asarray(direction_hits, dtype=float)))
        if direction_hits is not None and len(direction_hits)
        else None
    )

    if n == 0:
        return CalibrationReport(
            n=0, brier=float("nan"), base_rate=float("nan"),
            mean_confidence=float("nan"), intercept=0.0, slope=1.0,
            reliability=float("nan"), resolution=float("nan"),
            uncertainty=float("nan"), skill_vs_base_rate=float("nan"),
            bins=[], actionable=False, direction_hit_rate=dir_rate,
            summary="No resolved predictions yet.",
        )

    x = _logit(p)

    def neg_log_lik(theta: np.ndarray) -> float:
        a, b = theta
        q = np.clip(_sigmoid(a + b * x), _EPS, 1 - _EPS)
        return float(-np.sum(o * np.log(q) + (1 - o) * np.log(1 - q)))

    # Bounds keep the fit finite under perfect separation (e.g. a user whose
    # every prediction so far has hit), where the unconstrained MLE diverges.
    best = minimize(
        neg_log_lik, x0=np.array([0.0, 1.0]), method="L-BFGS-B",
        bounds=[(-4.0, 4.0), (0.0, 3.0)],
    )
    a_hat, b_hat = (best.x if best.success else (0.0, 1.0))

    w = n / (n + pseudo_count)
    intercept = float(w * a_hat)
    slope = float(w * b_hat + (1 - w) * 1.0)

    report = CalibrationReport(
        n=n,
        brier=decomp["brier"],
        base_rate=decomp["base_rate"],
        mean_confidence=float(p.mean()),
        intercept=intercept,
        slope=slope,
        reliability=decomp["reliability"],
        resolution=decomp["resolution"],
        uncertainty=decomp["uncertainty"],
        skill_vs_base_rate=decomp["skill_vs_base_rate"],
        bins=reliability_bins(p, o),
        actionable=n >= MIN_FOR_ADJUSTMENT,
        direction_hit_rate=dir_rate,
    )
    report.summary = describe(report)
    return report


def apply_calibration(stated_confidence: float, report: CalibrationReport) -> float:
    """Map a stated confidence through a fitted calibration report.

    Returns the stated value unchanged when there is not yet enough history
    to justify overriding the user.
    """
    if not report.actionable:
        return float(stated_confidence)
    adjusted = _sigmoid(report.intercept + report.slope * _logit(stated_confidence))
    # Never collapse a view to nothing: Black-Litterman needs a positive
    # confidence, and a floor keeps a bad run from erasing a user's voice.
    return float(np.clip(adjusted, 0.05, 0.95))


def describe(report: CalibrationReport) -> str:
    """One honest paragraph about this forecasting record."""
    if report.n == 0:
        return "No resolved predictions yet."

    gap = report.mean_confidence - report.base_rate
    parts = [
        f"{report.n} resolved prediction{'s' if report.n != 1 else ''}: "
        f"you hit your target {report.base_rate:.0%} of the time while "
        f"averaging {report.mean_confidence:.0%} confidence."
    ]
    if abs(gap) < 0.05:
        parts.append("That is well calibrated — your confidence means what it says.")
    elif gap > 0:
        parts.append(
            f"That is {gap:.0%} overconfident, which is the normal direction "
            f"and the reason this page exists."
        )
    else:
        parts.append(
            f"That is {abs(gap):.0%} underconfident — you are better than you "
            f"think and your views are being under-weighted."
        )

    if not np.isnan(report.skill_vs_base_rate):
        if report.resolution < 0.01:
            parts.append(
                "Your high-confidence calls have not landed more often than "
                "your low-confidence ones, so the number you type is not yet "
                "carrying information."
            )
        elif report.skill_vs_base_rate > 0:
            parts.append(
                "Your confident calls do land more often than your tentative "
                "ones — the ranking is real even where the level is off."
            )

    if not report.actionable:
        parts.append(
            f"Below {MIN_FOR_ADJUSTMENT} resolved predictions nothing is "
            f"adjusted — this is a record, not yet a correction."
        )
    return " ".join(parts)
