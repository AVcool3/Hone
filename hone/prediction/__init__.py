"""Hone Prediction Markets — hedging income you already carry.

The stocks and crypto products answer "how much of this risky asset should
I hold, given my risk aversion?".  This product answers the mirror-image
question for people whose *paycheck* is the risky asset: a ski instructor
whose season depends on snowfall, an ad-agency freelancer whose bookings
move with ad budgets, a recruiter whose fees move with hiring.  Each of
those already holds a position they never chose — and an event contract on
Kalshi that pays out when the season goes badly is a hedge for it.

The package is deliberately thin, like ``hone.crypto``: the quantitative
ideas are the same ones the rest of Hone runs on, re-pointed at a binary
payoff instead of a stock return.

* **Risk aversion gamma** comes from the same questionnaire
  (``hone.risk_profile``) and the same CRRA utility
  U(w) = w^(1-gamma)/(1-gamma).  Here it sets how much of an exposure a
  person wants insured, and how far above fair value they will pay for
  the insurance.
* **Certainty equivalent** — the "risk-adjusted return" tile on the
  optimize page — is the number this module maximizes: the dollar amount
  a person would accept for sure instead of their uncertain season.
* **Hedge decomposition** mirrors ``hone.hedging``: a minimum-variance
  hedge (the analogue of the beta-sized index short) plus a speculative
  tilt that depends on whether the person thinks the market price is
  wrong, scaled down by gamma.
* **Blending a view with the market** is the Black-Litterman idea from
  ``hone.optimization``: the market price is the equilibrium prior, the
  user's own probability is the view, and their confidence decides how
  far the posterior moves.  When the decision journal has scored enough
  of their predictions, the same calibration map used on the views page
  is applied to that confidence.
* **Basis risk** — the contract resolves on a weather station, the income
  depends on visitors — reuses the correlation logic of
  ``hone.hedging.short_hedge``: an imperfectly correlated hedge is capped
  at the minimum-variance size, and part of the risk stays.

Market data comes from Kalshi's public REST API (no account needed), with a
bundled snapshot as the fallback so the page always works offline.  Hone
never places orders: it sizes the position and explains it.  See
``docs/PREDICTION_MARKETS.md`` for the derivations, the market catalog,
and the honest list of what this cannot do.
"""

from .contracts import (
    KALSHI_TAKER_FEE_RATE,
    Contract,
    implied_probability,
    kalshi_fee,
)
from .hedge import (
    ContractHedgePlan,
    IncomeExposure,
    blend_belief,
    crra_certainty_equivalent,
    hedge_income,
    kelly_fraction,
    reservation_price,
)
from .kalshi_client import (
    INDUSTRIES,
    KalshiClient,
    KalshiError,
    curated_catalog,
    load_snapshot,
)

__all__ = [
    "KALSHI_TAKER_FEE_RATE",
    "Contract",
    "implied_probability",
    "kalshi_fee",
    "ContractHedgePlan",
    "IncomeExposure",
    "blend_belief",
    "crra_certainty_equivalent",
    "hedge_income",
    "kelly_fraction",
    "reservation_price",
    "INDUSTRIES",
    "KalshiClient",
    "KalshiError",
    "curated_catalog",
    "load_snapshot",
]
