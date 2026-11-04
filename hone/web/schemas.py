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
class BrokerLink(BaseModel):
    """A user's SnapTrade identity: which linked brokerages to read.

    Created by ``POST /api/broker/connect`` and kept by the user (browser, and
    their own Supabase row when signed in). Sent with each request like the
    Alpaca keys, and never stored server-side. Useless on its own: every
    SnapTrade call is also signed with the server's consumer key.
    """

    user_id: str = Field(min_length=1, max_length=128)
    user_secret: str = Field(min_length=1, max_length=256)
    #: Limit to these SnapTrade account ids; empty/None = every linked account.
    account_ids: list[str] | None = None


class AlpacaCredentials(BaseModel):
    """Where this request's holdings and prices come from.

    * ``api_key`` / ``secret_key`` — an Alpaca paper account (holdings + prices).
      Fall back to server env vars unless the server runs with HONE_PUBLIC.
    * ``broker`` — holdings from brokerages linked through SnapTrade instead.
      Prices then come from Alpaca market data (these keys if given, else the
      server's market-data-only keys).

    Everything here is used for the single request and never stored server-side.
    """

    api_key: str | None = None
    secret_key: str | None = None
    broker: BrokerLink | None = None
    #: "brokers" when the user chose linked brokerages — lets the server say
    #: "nothing linked yet" instead of falling back to the Alpaca account.
    source: str | None = None


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


class SkippedHoldingOut(BaseModel):
    """A position that exists at the broker but isn't in the model, and why."""

    symbol: str
    reason: str
    market_value: float | None = None
    account: str | None = None


class PortfolioResponse(BaseModel):
    demo: bool
    positions: list[PositionOut]
    portfolio_value: float | None = None
    analysis: PortfolioAnalysis | None = None
    #: "sample", "alpaca" or "brokerages" — where these holdings came from.
    source: str | None = None
    #: Linked-brokerage mode: the accounts combined, and what was left out.
    accounts: list[str] = Field(default_factory=list)
    skipped: list[SkippedHoldingOut] = Field(default_factory=list)


# ------------------------------------------------------------ brokerages
class BrokerConnectRequest(BaseModel):
    """Start (or continue) linking brokerages through SnapTrade."""

    #: The existing link, if this user already has one.
    link: BrokerLink | None = None
    #: Without sign-in (private servers only): a random id the browser made,
    #: so the same browser keeps the same SnapTrade user.
    local_id: str | None = Field(default=None, max_length=64)
    #: Where SnapTrade should send the user back to (must be this site).
    redirect_url: str | None = Field(default=None, max_length=2048)
    #: Repair a connection that stopped syncing (its connection id).
    reconnect: str | None = Field(default=None, max_length=128)
    #: Replace a SnapTrade user whose secret was lost (drops its connections).
    reset: bool = False


class BrokerConnectResponse(BaseModel):
    redirect_url: str
    #: Returned whenever the link is new or changed — the browser must keep it.
    link: BrokerLink


class BrokerLinkRequest(BaseModel):
    link: BrokerLink


class BrokerDisconnectRequest(BaseModel):
    link: BrokerLink
    connection_id: str = Field(min_length=1, max_length=128)


class BrokerConnectionOut(BaseModel):
    id: str
    brokerage: str
    logo_url: str | None = None
    #: True when the broker stopped sharing data (password changed, etc.) —
    #: the user needs to reconnect it.
    disabled: bool = False
    created: str | None = None


class BrokerAccountOut(BaseModel):
    id: str
    connection_id: str | None = None
    label: str           # "Schwab · Brokerage ••1234" — never the full number
    institution: str
    value: float | None = None
    currency: str | None = None
    is_paper: bool = False
    #: False for bank/credit/annuity accounts, which Hone doesn't model.
    investment: bool = True


class BrokerAccountsResponse(BaseModel):
    connections: list[BrokerConnectionOut]
    accounts: list[BrokerAccountOut]


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


class BehaviorRow(BaseModel):
    """One strategy, held perfectly vs. held by a person."""

    name: str
    label: str
    paper_cagr: float
    realized_cagr: float
    behavior_gap: float
    max_drawdown: float
    panics: int
    time_in_cash: float
    cost_drag: float


class BehaviorOut(BaseModel):
    panic_threshold: float
    rows: list[BehaviorRow]
    best_on_paper: str
    best_as_held: str
    ranking_changed: bool
    summary: str


class BacktestResponse(BaseModel):
    gamma: float
    start: str
    end: str
    rebalances: int
    headline: str
    strategies: list[StrategyOut]
    #: What the same curves look like once the investor is allowed to
    #: capitulate. None when the panic simulation could not be run.
    behavior: "BehaviorOut | None" = None


# -------------------------------------------------- conviction compiler (LLM)
class CompileRequest(BaseModel):
    """Plain-English thesis to compile into structured, editable views."""

    text: str = Field(description="What the user believes, in their own words")
    #: The user's journal. When enough of it has resolved, their own
    #: examples go into the prompt so the compiler reads their language
    #: the way their history says it should be read.
    predictions: list["PredictionIn"] = []
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
    #: How many of the user's own resolved predictions shaped this compile.
    personalized_from: int = 0
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


# ------------------------------------------------------------ CVaR / tails
class TailRow(BaseModel):
    portfolio: str
    label: str
    mean: float
    volatility: float
    var: float
    cvar: float
    worst: float
    skew: float


class CVaRRequest(BaseModel):
    gamma: float
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    lookback_days: int = 756
    max_weight: float | None = 0.35
    beta: float = Field(default=0.95, ge=0.5, lt=1.0)
    #: Scenario length in periods. 21 ~ a month, which is how people think
    #: about "a bad month" — and a legible unit for the dollar framing.
    horizon: int = Field(default=21, ge=1, le=252)
    portfolio_value: float | None = None


class CVaRResponse(BaseModel):
    beta: float
    horizon: int
    n_scenarios: int
    tail_scenarios: int
    #: Minimum-CVaR weights (risk-first) and the gamma-matched mean-CVaR ones.
    min_cvar_weights: list[WeightRow]
    gamma_cvar_weights: list[WeightRow]
    comparison: list[TailRow]
    portfolio_value: float | None = None
    #: The headline: dollars of tail loss the risk-first book avoids.
    cvar_saved_usd: float | None = None
    summary: str


# --------------------------------------------------- entropy pooling (views)
class FlexibleViewIn(BaseModel):
    """A view the Black-Litterman engine cannot express.

    ``kind`` selects which fields matter:
      mean         ticker, value                 E[r] = value
      probability  ticker, threshold, value      P(r <= threshold) = value
      ranking      ticker, versus                E[ticker] >= E[versus]
      volatility   ticker, value                 vol(ticker) = value
      conditional  ticker, versus, threshold, value
                                                 E[versus | ticker <= threshold] = value
    """

    kind: str
    ticker: str
    value: float | None = None
    threshold: float | None = None
    versus: str | None = None
    below: bool = True


class PoolingRequest(BaseModel):
    views: list[FlexibleViewIn]
    gamma: float
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    lookback_days: int = 756
    horizon: int = Field(default=21, ge=1, le=252)
    max_weight: float | None = 0.35
    beta: float = Field(default=0.95, ge=0.5, lt=1.0)


class PoolingViewOut(BaseModel):
    label: str
    #: What the view asserted, and what the posterior actually delivers.
    target: float
    achieved: float
    #: Equality views land on the target; inequality views (rankings) only
    #: have to clear it, and often the prior already does — in which case
    #: nothing was reweighted and the cost is zero.
    satisfied: bool = True
    binding: bool = True


class PoolingResponse(BaseModel):
    views: list[PoolingViewOut]
    n_scenarios: int
    #: exp(entropy): how many scenarios the posterior effectively uses.
    effective_scenarios: float
    prior_effective_scenarios: float
    #: Fraction of the scenario set the views discarded.
    confidence_cost: float
    relative_entropy: float
    #: True when the posterior rests on too few scenarios to trust.
    collapsed: bool
    #: Prior vs posterior expected return per asset.
    prior_mu: list[ReturnRow]
    weights: list[WeightRow]
    cvar_before: float
    cvar_after: float
    summary: str


BacktestResponse.model_rebuild()


class TrainingExportRequest(BaseModel):
    predictions: list[PredictionIn] = []
    demo: bool = False
    credentials: AlpacaCredentials | None = None
    lookback_days: int = 1260
    #: Which halves of the dataset to build.
    include_compile: bool = True
    include_calibration: bool = True


class TrainingExportResponse(BaseModel):
    n_examples: int
    n_compile: int
    n_calibrate: int
    n_resolved: int
    hit_rate: float | None = None
    #: "few_shot" | "marginal" | "ready"
    recommendation: str
    warnings: list[str] = []
    notes: list[str] = []
    summary: str
    #: The dataset itself, JSONL, ready to write to a file.
    jsonl: str = ""
    #: How many examples the few-shot path is using right now — the thing
    #: that works today, as opposed to the export, which needs far more.
    few_shot_active: int = 0


CompileRequest.model_rebuild()


# ------------------------------------------------------- prediction markets
class ContractHedgeRequest(BaseModel):
    """Size an event contract against income risk — see hone/prediction/hedge.py."""

    gamma: float
    #: money available over the horizon (earnings + the savings a bad season would eat)
    wealth: float = Field(gt=0)
    #: dollars lost if the bad outcome happens; 0 means pure speculation
    loss: float = Field(ge=0)
    #: ask price of the contract side that pays when the bad outcome happens
    price: float = Field(gt=0, lt=1)
    #: the market's probability of that side (midpoint); defaults to the price
    market_prob: float | None = Field(default=None, gt=0, lt=1)
    #: the user's own probability of that side, and how sure they are of it
    own_prob: float | None = Field(default=None, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)
    #: how tightly the market's event tracks the user's own loss
    basis_correlation: float = Field(default=1.0, ge=0, le=1)
    fee_multiplier: float = Field(default=1.0, ge=0)
    include_fees: bool = True
    #: the journal's fitted confidence map, applied to `confidence` first
    calibration: CalibrationMap | None = None
    #: free text, echoed back so the page can label the result
    market_ticker: str | None = None
    side: str | None = None


class ContractStateOut(BaseModel):
    prob: float
    pays: bool
    loss: bool
    wealth_unhedged: float
    wealth_hedged: float


class ContractHedgeResponse(BaseModel):
    gamma: float
    tier: TierInfo
    belief: float
    market_prob: float
    price: float
    basis_correlation: float
    basis_clipped: bool
    n_star: float
    contracts: int
    direction: str
    cost: float
    fee: float
    payout_if_pays: float
    pure_hedge_contracts: float
    speculative_contracts: float
    ce_unhedged: float
    ce_hedged: float
    ce_gain: float
    expected_wealth_unhedged: float
    expected_wealth_hedged: float
    worst_unhedged: float
    worst_hedged: float
    std_unhedged: float
    std_hedged: float
    reservation_price: float
    fair_price: float
    premium_per_contract: float
    total_premium: float
    kelly_fraction: float
    crra_fraction: float
    states: list[ContractStateOut]
    warnings: list[str]
    needs_hedge: bool
    #: confidence actually used after the calibration map, if one applied
    confidence_used: float
    confidence_stated: float
    market_ticker: str | None = None
    side: str | None = None


class PredictionMarketOut(BaseModel):
    ticker: str
    event_ticker: str = ""
    title: str
    label: str = ""
    status: str = ""
    close_time: str = ""
    yes_bid: float | None = None
    yes_ask: float | None = None
    no_bid: float | None = None
    no_ask: float | None = None
    last: float | None = None
    implied: float | None = None
    spread: float | None = None
    volume: float = 0.0
    open_interest: float = 0.0
    strike: float | None = None
    strike_type: str = ""
    rules: str = ""


class PredictionSeriesOut(BaseModel):
    ticker: str
    title: str
    basis: str
    bad_side: str
    note: str = ""
    open_count: int = 0
    markets: list[PredictionMarketOut] = []


class PredictionIndustryOut(BaseModel):
    key: str
    label: str
    who: str
    series: list[PredictionSeriesOut]


class PredictionCatalogResponse(BaseModel):
    as_of: str | None
    #: "live", "live-partial" or "snapshot"
    source: str
    #: whether this deployment refreshes from Kalshi at all (HONE_KALSHI_LIVE)
    live_enabled: bool = True
    industries: list[PredictionIndustryOut]
