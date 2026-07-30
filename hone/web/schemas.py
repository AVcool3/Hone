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
    analyze: bool = False  # also compute vol / revealed gamma (needs history)
    stated_gamma: float | None = None  # questionnaire gamma, for comparison
    lookback_days: int = 504


class PositionOut(BaseModel):
    symbol: str
    weight: float
    market_value: float | None = None
    qty: float | None = None


class PortfolioAnalysis(BaseModel):
    volatility: float
    beta: float
    revealed_gamma: float
    revealed_tier: "TierInfo"
    stated_gamma: float | None = None
    stated_tier: "TierInfo | None" = None
    market_premium_assumption: float


class PortfolioResponse(BaseModel):
    demo: bool
    positions: list[PositionOut]
    portfolio_value: float | None = None
    analysis: PortfolioAnalysis | None = None


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
    portfolio_value: float | None = None  # override; else account equity / demo default
    #: Fitted confidence calibration from the user's decision journal. When
    #: present and actionable, stated confidences are mapped through it
    #: before Black-Litterman sees them.
    calibration: "CalibrationMap | None" = None


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
    reason: str | None = None


class HedgeSuggestionOut(BaseModel):
    kind: str
    instrument: str
    description: str
    hedge_notional_fraction: float
    hedged_volatility: float | None
    est_annual_cost_fraction: float
    warning: str | None = None
    details: dict = {}


class StressScenarioOut(BaseModel):
    name: str
    market_shock: float
    loss_fraction: float
    loss_usd: float
    hedged_loss_fraction: float | None = None
    hedged_loss_usd: float | None = None


class HedgePlanOut(BaseModel):
    """The hedge plan. ``premium_is_negative`` matters: the Merton risk
    budget assumes risk is being paid for, and says nothing useful about a
    portfolio with a negative expected excess return."""

    gamma: float
    current_volatility: float
    target_volatility: float
    needs_hedge: bool
    suggestions: list[HedgeSuggestionOut]
    portfolio_value: float | None = None
    tolerable_annual_loss_usd: float | None = None
    current_annual_loss_usd: float | None = None
    scenarios: list[StressScenarioOut] = []
    expected_excess_return: float = 0.0
    premium_is_negative: bool = False


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
    #: Present only when a calibration map changed at least one confidence.
    confidence_adjustments: "list[ConfidenceAdjustment] | None" = None


class HedgeRequest(BaseModel):
    gamma: float
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    cov_method: str = "shrinkage"
    lookback_days: int = 504
    hedge_instrument: str = "SPY"
    portfolio_value: float | None = None


# ---------------------------------------------------------------- backtest
class BacktestRequest(BaseModel):
    gamma: float
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    symbols: list[str] | None = None  # override universe (else demo/holdings)
    lookback_days: int = 1260  # ~5y of history to backtest over
    max_weight: float = 0.35


class StrategyOut(BaseModel):
    name: str
    label: str
    equity_curve: list[float]
    dates: list[str]
    metrics: dict[str, float]


class BacktestResponse(BaseModel):
    gamma: float
    start: str
    end: str
    rebalances: int
    headline: str
    strategies: list[StrategyOut]


# -------------------------------------------------- conviction compiler (LLM)
class CompileRequest(BaseModel):
    """Plain-English thesis to compile into structured, editable views."""

    text: str = Field(description="What the user believes, in their own words")
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    #: Attach live prices as the entry price for each compiled view.
    with_prices: bool = True
    #: Force the deterministic parser even when a Claude key is configured.
    offline: bool = False
    lookback_days: int = 30


class CompiledViewOut(BaseModel):
    ticker: str
    direction: str = "bullish"
    entry_price: float | None = None
    target_price: float | None = None
    horizon_days: float | None = None
    confidence_pct: float | None = None
    thesis: str = ""
    catalysts: list[str] = []
    risks: list[str] = []
    #: Fields the compiler guessed rather than read — the UI highlights these.
    needs_review: list[str] = []
    #: Live price at compile time, for the "vs. today" readout in the form.
    live_price: float | None = None
    #: False when the symbol has no price history in the current universe.
    #: The optimizer would reject the whole request, so the row says so
    #: rather than letting the user discover it at the last step.
    tradeable: bool = True
    #: Annualized return the view implies; recomputed client-side on edit.
    implied_annual_return: float | None = None
    #: Non-blocking warnings about extreme or contradictory inputs.
    warnings: list[str] = []


class CompileResponse(BaseModel):
    #: "claude" when the LLM compiled it, "fallback" for the offline parser.
    engine: str
    views: list[CompiledViewOut]
    notes: list[str] = []
    #: Symbols the user can name, so the UI can offer a picker on failure.
    universe: list[str] = []


# ------------------------------------------- decision journal / calibration
class PredictionIn(BaseModel):
    """One journalled prediction, as stored in the browser."""

    id: str = ""
    ticker: str
    direction: str = "bullish"
    entry_price: float = Field(gt=0)
    target_price: float = Field(gt=0)
    confidence: float = Field(gt=0, le=1)
    horizon_days: float = Field(gt=0, default=365.0)
    thesis: str = ""
    created_at: str  # ISO 8601, frozen at decision time


class JournalRequest(BaseModel):
    predictions: list[PredictionIn] = []
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    lookback_days: int = 1260
    #: In demo mode with an empty journal, synthesize a plausible track
    #: record so the page shows what it is for.
    seed_demo_history: bool = False


class ResolutionOut(BaseModel):
    prediction: PredictionIn
    final_price: float
    target_hit: bool
    direction_hit: bool
    touched: bool
    realized_return: float
    resolved_at: str
    brier: float


class OpenPredictionOut(BaseModel):
    prediction: PredictionIn
    days_remaining: float
    current_price: float | None = None
    progress: float | None = None  # 0-1 of the way from entry to target


class ReliabilityBin(BaseModel):
    lower: float
    upper: float
    n: int
    mean_confidence: float | None = None
    hit_rate: float | None = None


class CalibrationOut(BaseModel):
    n: int
    brier: float | None = None
    base_rate: float | None = None
    mean_confidence: float | None = None
    intercept: float = 0.0
    slope: float = 1.0
    reliability: float | None = None
    resolution: float | None = None
    uncertainty: float | None = None
    skill_vs_base_rate: float | None = None
    bins: list[ReliabilityBin] = []
    actionable: bool = False
    direction_hit_rate: float | None = None
    summary: str = ""
    #: Worked example of the map: what a few stated levels become.
    examples: list[dict] = []


class JournalResponse(BaseModel):
    resolved: list[ResolutionOut]
    open: list[OpenPredictionOut]
    calibration: CalibrationOut
    seeded: bool = False


class CalibrationMap(BaseModel):
    """The fitted map, sent back with an optimize request.

    The client stores the journal; the server owns the arithmetic, so the
    adjustment applied to a view is computed in one place only.
    """

    intercept: float = 0.0
    slope: float = 1.0
    actionable: bool = False
    n: int = 0


class ConfidenceAdjustment(BaseModel):
    ticker: str
    stated: float
    used: float


# Forward references used above are defined later in this module.
OptimizeRequest.model_rebuild()
OptimizeResponse.model_rebuild()


# ------------------------------------------------- DOSE adaptive elicitation
class DoseAnswerIn(BaseModel):
    question_id: int
    choice: str  # "A" or "B"


class DoseRequest(BaseModel):
    answers: list[DoseAnswerIn] = []
    n_questions: int = Field(default=8, ge=3, le=20)


class DoseQuestionOut(BaseModel):
    question_id: int
    number: int  # 1-based position in this user's sequence
    total: int
    option_a: str
    option_b: str
    #: Bits of information this answer is expected to carry. Shown as a
    #: progress signal, not a demand on the user.
    expected_information_gain: float


class DoseStateOut(BaseModel):
    gamma: float
    gamma_sd: float
    gamma_ci90: tuple[float, float]
    mu: float
    n_answers: int
    tier: TierInfo
    tier_confidence: float
    #: Posterior density over the gamma grid, for the live belief chart.
    gamma_grid: list[float]
    gamma_marginal: list[float]
    summary: str


class DoseResponse(BaseModel):
    finished: bool
    question: DoseQuestionOut | None
    state: DoseStateOut
