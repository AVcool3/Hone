"""Pydantic request/response models for the web API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ------------------------------------------------------------- questionnaire
class MenuLottery(BaseModel):
    high: float
    low: float
    p_high: float


class MenuRow(BaseModel):
    number: int
    option_a: MenuLottery
    option_b: MenuLottery


class MenuRound(BaseModel):
    scale: float
    label: str
    rows: list[MenuRow]


class QuestionnaireRequest(BaseModel):
    choices: list[list[str]] = Field(
        description='One vector of "A"/"B" per round, 10 entries each'
    )
    scales: list[float] | None = None
    error_spec: str = "fechner"


class TierInfo(BaseModel):
    tier: int
    num_tiers: int
    category: str
    gamma_lower: float
    gamma_upper: float
    percentile_hint: float


class ProfileResponse(BaseModel):
    gamma: float
    mu: float
    se_gamma: float | None
    gamma_ci95: tuple[float, float] | None
    interval: tuple[float, float]
    tier: TierInfo
    monotone: list[bool]
    n_obs: int
    converged: bool
    summary: str


# ------------------------------------------------------------------ market
class AlpacaCredentials(BaseModel):
    """Optional per-request keys; fall back to server env vars.

    Keys are used for the single request and never stored server-side.
    """

    api_key: str | None = None
    secret_key: str | None = None


class PortfolioRequest(BaseModel):
    demo: bool = False
    credentials: AlpacaCredentials | None = None


class PositionOut(BaseModel):
    symbol: str
    weight: float
    market_value: float | None = None
    qty: float | None = None


class PortfolioResponse(BaseModel):
    demo: bool
    positions: list[PositionOut]


# ---------------------------------------------------------------- optimize
class ViewIn(BaseModel):
    ticker: str
    target_price: float = Field(gt=0)
    confidence: float = Field(gt=0, le=1, default=0.5)
    horizon_days: float = Field(gt=0, default=365.25)


class OptimizeRequest(BaseModel):
    gamma: float
    views: list[ViewIn] = []
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    cov_method: str = "shrinkage"
    long_only: bool = True
    max_weight: float | None = 0.35
    lookback_days: int = 504
    hedge_instrument: str = "SPY"


class ReturnRow(BaseModel):
    symbol: str
    prior: float
    posterior: float
    tilt: float


class WeightRow(BaseModel):
    symbol: str
    current: float
    target: float
    trade: float


class HedgeSuggestionOut(BaseModel):
    kind: str
    instrument: str
    description: str
    hedge_notional_fraction: float
    hedged_volatility: float | None
    est_annual_cost_fraction: float
    details: dict


class HedgePlanOut(BaseModel):
    gamma: float
    current_volatility: float
    target_volatility: float
    needs_hedge: bool
    suggestions: list[HedgeSuggestionOut]


class OptimizeResponse(BaseModel):
    gamma: float
    tier: TierInfo
    demo: bool
    views: list[dict]
    returns: list[ReturnRow] | None  # None when no views were supplied
    weights: list[WeightRow]
    expected_return: float
    volatility: float
    utility: float
    hedge_plan: HedgePlanOut


class HedgeRequest(BaseModel):
    gamma: float
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    cov_method: str = "shrinkage"
    lookback_days: int = 504
    hedge_instrument: str = "SPY"
