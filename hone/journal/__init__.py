"""Decision journal and forecast calibration.

Hone asks users how confident they are, and Black-Litterman takes that number
literally: it is the whole lever controlling how far the portfolio tilts away
from equilibrium.  Everywhere else in the product that number is measured —
gamma comes from an incentivized experiment, covariance from price history —
but confidence is self-reported, and self-reported confidence is the most
reliably wrong number in finance.

This package closes that gap.  Every view a user acts on is logged as a dated
prediction with the price it was made at.  When its horizon elapses the
prediction resolves against the market, and the accumulated record produces a
Brier score, a reliability curve, and a fitted mapping from what the user
*says* to what their history suggests they should have said.

The mapping shrinks toward the identity: with four predictions on file you
are still taken at your word, because four predictions contain no evidence.
"""

from .calibration import (
    CalibrationReport,
    apply_calibration,
    brier_decomposition,
    brier_score,
    fit_calibration,
    reliability_bins,
)
from .records import Prediction, Resolution, resolve_prediction, resolve_all

__all__ = [
    "CalibrationReport",
    "Prediction",
    "Resolution",
    "apply_calibration",
    "brier_decomposition",
    "brier_score",
    "fit_calibration",
    "reliability_bins",
    "resolve_all",
    "resolve_prediction",
]
