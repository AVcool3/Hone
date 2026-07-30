"""FastAPI application exposing the full Hone pipeline.

Endpoints
---------
GET  /api/menu           — questionnaire menus (3 stake scales x 10 rows)
POST /api/questionnaire  — choices -> gamma, noise, 50-tier placement
POST /api/portfolio      — current Alpaca paper positions (or demo data)
POST /api/optimize       — views -> Black-Litterman + MVO + hedge plan
POST /api/hedge          — hedge plan only
GET  /                   — the single-page UI

Alpaca credentials resolve per request: explicit fields in the request
body win, otherwise the server's ALPACA_API_KEY / ALPACA_SECRET_KEY
environment variables are used.  Request-supplied keys are never stored.

Deployment environment variables
--------------------------------
HONE_ACCESS_PASSWORD
    When set, every route requires HTTP Basic auth with this password
    (any username).  Use it to gate a small private deployment.
HONE_PUBLIC
    When set to a truthy value ("1", "true", ...), the server refuses to
    fall back to its own ALPACA_* environment variables — each user must
    supply their own keys in the page.  Set this on any deployment that
    strangers can reach so your keys can never be used by visitors.
"""

from __future__ import annotations

import base64
import os
import secrets
from contextvars import ContextVar
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse

from ..hedging.hedge import portfolio_beta, portfolio_volatility, revealed_gamma
from ..market_data.alpaca_client import AlpacaClient, AlpacaError
from ..market_data.covariance import portfolio_covariance
from ..optimization.mvo import trade_reasons
from ..optimization.views import View
from ..pipeline import rebalance, synthetic_universe
from ..risk_profile.holt_laury import DEFAULT_SCALES, standard_menu
from ..risk_profile.questionnaire import profile_from_choices
from ..risk_profile.tiers import NUM_TIERS, gamma_to_tier
from . import schemas as s

STATIC_DIR = Path(__file__).parent / "static"

#: Notional used for dollar framing in demo mode.
DEMO_PORTFOLIO_VALUE = 25_000.0

#: Assumed annual market excess return for the revealed-gamma diagnostic.
MARKET_PREMIUM = 0.05


#: Asset class for the request currently being served. Set per request by
#: middleware from the URL (path prefix or ?asset_class=), so a single
#: deployment can serve both products — "/" for equities, "/crypto" for
#: digital assets — rather than needing two services.
_ASSET_CLASS_CTX: ContextVar[str | None] = ContextVar("asset_class", default=None)


def _normalize_asset_class(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    if v in ("crypto", "cryptocurrency", "digital"):
        return "crypto"
    if v in ("equities", "equity", "stocks"):
        return "equities"
    return None


def asset_class() -> str:
    """Asset class for this request: 'equities' (default) or 'crypto'.

    Resolution order: the current request's context (path/query) first,
    then the HONE_ASSET_CLASS environment variable (which pins a whole
    deployment to one product), then equities.

    One codebase, two products: the quantitative protocol is identical
    and only the market data, calendar, proxy asset, stress scenarios and
    copy differ.
    """
    return (
        _ASSET_CLASS_CTX.get()
        or _normalize_asset_class(os.environ.get("HONE_ASSET_CLASS"))
        or "equities"
    )


def is_crypto() -> bool:
    return asset_class() == "crypto"


def _periods_per_year() -> int:
    from ..crypto.universe import CRYPTO_PERIODS_PER_YEAR

    return CRYPTO_PERIODS_PER_YEAR if is_crypto() else 252


def _market_proxy(default: str = "SPY") -> str:
    from ..crypto.universe import MARKET_PROXY

    return MARKET_PROXY if is_crypto() else default


def _tier_info(gamma: float) -> s.TierInfo:
    t = gamma_to_tier(gamma)
    return s.TierInfo(
        tier=t.tier,
        num_tiers=NUM_TIERS,
        category=t.category,
        gamma_lower=t.gamma_lower,
        gamma_upper=t.gamma_upper,
        percentile_hint=t.percentile_hint,
    )


def _public_mode() -> bool:
    return os.environ.get("HONE_PUBLIC", "").strip().lower() in ("1", "true", "yes", "on")


def _client(creds: s.AlpacaCredentials | None) -> AlpacaClient:
    has_request_keys = bool(creds and creds.api_key and creds.secret_key)
    if _public_mode() and not has_request_keys:
        raise HTTPException(
            status_code=401,
            detail="This is a public deployment: enter your own Alpaca "
            "paper-trading keys in the Data source panel (the server's "
            "keys are disabled).",
        )
    try:
        return AlpacaClient(
            api_key=creds.api_key if creds else None,
            secret_key=creds.secret_key if creds else None,
        )
    except AlpacaError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


def _load_market(
    demo: bool,
    creds: s.AlpacaCredentials | None,
    extra_symbols: list[str],
    hedge_instrument: str,
    lookback_days: int,
) -> tuple[pd.DataFrame, pd.Series]:
    """(prices, current weights) from demo data or the Alpaca account."""
    if demo:
        if is_crypto():
            from ..crypto.universe import synthetic_crypto_universe

            return synthetic_crypto_universe()
        prices, weights = synthetic_universe()
        return prices, weights
    if is_crypto():
        return _load_crypto_market(creds, extra_symbols, hedge_instrument, lookback_days)
    client = _client(creds)
    try:
        weights = client.portfolio_weights()
        if weights.empty:
            raise HTTPException(
                status_code=400,
                detail="No positions in the Alpaca paper account. Buy a few "
                "paper positions first, or use demo mode.",
            )
        symbols = sorted(
            set(weights.index) | {t.upper() for t in extra_symbols} | {hedge_instrument}
        )
        start = date.today() - timedelta(days=int(lookback_days * 1.6))
        prices = client.get_bars(symbols, start=start)
    except AlpacaError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return prices.tail(lookback_days), weights


def _load_crypto_market(
    creds: s.AlpacaCredentials | None,
    extra_symbols: list[str],
    market_proxy: str,
    lookback_days: int,
) -> tuple[pd.DataFrame, pd.Series]:
    """(prices, weights) for the crypto side of the paper account."""
    from ..crypto.universe import normalize_symbol

    client = _client(creds)
    try:
        positions = client.get_crypto_positions()
        if not positions:
            raise HTTPException(
                status_code=400,
                detail="No crypto positions in the Alpaca paper account. Buy a "
                "few paper crypto positions first, or use demo mode.",
            )
        gross = sum(abs(p.market_value) for p in positions) or 1.0
        weights = pd.Series({p.symbol: p.market_value / gross for p in positions})
        symbols = sorted(
            set(weights.index)
            | {normalize_symbol(t) for t in extra_symbols}
            | {normalize_symbol(market_proxy)}
        )
        start = date.today() - timedelta(days=int(lookback_days * 1.2))
        prices = client.get_crypto_bars(symbols, start=start)
        prices = prices.dropna(axis=1, how="all")
        weights = weights.reindex(
            [c for c in prices.columns if c in weights.index]
        ).fillna(0.0)
    except AlpacaError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return prices.tail(lookback_days), weights


def create_app() -> FastAPI:
    app = FastAPI(title="Hone", version="0.2.0")

    # ------------------------------------------- per-request asset class
    @app.middleware("http")
    async def resolve_asset_class(request: Request, call_next):
        """Pick the product from the URL: /crypto/... or ?asset_class=."""
        explicit = _normalize_asset_class(request.query_params.get("asset_class"))
        by_path = "crypto" if request.url.path.rstrip("/").startswith("/crypto") else None
        token = _ASSET_CLASS_CTX.set(explicit or by_path)
        try:
            return await call_next(request)
        finally:
            _ASSET_CLASS_CTX.reset(token)

    # ------------------------------------------------------- access gate
    @app.middleware("http")
    async def access_gate(request: Request, call_next):
        password = os.environ.get("HONE_ACCESS_PASSWORD")
        if password and request.url.path != "/api/health":
            supplied = ""
            auth = request.headers.get("authorization", "")
            if auth.startswith("Basic "):
                try:
                    supplied = base64.b64decode(auth[6:]).decode().split(":", 1)[1]
                except Exception:
                    supplied = ""
            if not secrets.compare_digest(supplied, password):
                return Response(
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Hone"'},
                )
        return await call_next(request)

    # ------------------------------------------------------------- static
    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/crypto", include_in_schema=False)
    @app.get("/crypto/", include_in_schema=False)
    def index_crypto() -> FileResponse:
        """Same single-page app, crypto product (see resolve_asset_class)."""
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health", include_in_schema=False)
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/config", include_in_schema=False)
    def config() -> dict:
        """Asset-class configuration the frontend uses to swap copy."""
        crypto = is_crypto()
        return {
            "asset_class": asset_class(),
            "auth_enabled": True,
            "market_proxy": _market_proxy(),
            "periods_per_year": _periods_per_year(),
            "copy": {
                "product": "Hone Crypto" if crypto else "Hone",
                "descriptor": (
                    "Personalized Crypto Portfolio Optimization"
                    if crypto
                    else "Personalized Portfolio Optimization"
                ),
                "asset_word": "coins" if crypto else "stocks",
                "asset_word_singular": "coin" if crypto else "stock",
                "holdings_word": "coins you hold" if crypto else "stocks you hold",
                "example_ticker": "SOL" if crypto else "TSLA",
                "example_target": "$260" if crypto else "$220",
                "market_name": "Bitcoin" if crypto else "the S&P 500",
                "cash_word": "stablecoins" if crypto else "cash",
                "account_word": (
                    "Alpaca crypto paper account" if crypto else "Alpaca paper account"
                ),
                "hedge_note": (
                    "Crypto hedges are the stablecoin leg and a short of the market "
                    "proxy — listed crypto options are not available through the "
                    "brokerage integration."
                    if crypto
                    else "Hedges include cash, an index short, and option overlays."
                ),
                "volatility_note": (
                    "Crypto volatility runs 50-100%+ a year, several times equity "
                    "levels, and drawdowns of 80% have happened twice. Position "
                    "sizes here will look small for a reason."
                    if crypto
                    else ""
                ),
            },
        }

    # Serve whitelisted static assets (config, optional demo video).
    _STATIC_WHITELIST = {
        "config.js": "application/javascript",
        "demo.mp4": "video/mp4",
        "og.png": "image/png",
        "robots.txt": "text/plain",
    }

    @app.get("/{asset}", include_in_schema=False)
    def static_asset(asset: str):
        if asset not in _STATIC_WHITELIST:
            raise HTTPException(status_code=404, detail="not found")
        path = STATIC_DIR / asset
        if not path.exists():
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(path, media_type=_STATIC_WHITELIST[asset])

    # --------------------------------------------------------------- menu
    @app.get("/api/menu", response_model=list[s.MenuRound])
    def get_menu() -> list[s.MenuRound]:
        rounds = []
        for scale in DEFAULT_SCALES:
            rows = [
                s.MenuRow(
                    number=d.number,
                    option_a=s.MenuLottery(
                        high=d.option_a.high, low=d.option_a.low, p_high=d.option_a.p_high
                    ),
                    option_b=s.MenuLottery(
                        high=d.option_b.high, low=d.option_b.low, p_high=d.option_b.p_high
                    ),
                )
                for d in standard_menu(scale)
            ]
            rounds.append(
                s.MenuRound(scale=scale, label=f"Stakes x{scale:g}", rows=rows)
            )
        return rounds

    # ------------------------------------------------------ questionnaire
    @app.post("/api/questionnaire", response_model=s.ProfileResponse)
    def score_questionnaire(req: s.QuestionnaireRequest) -> s.ProfileResponse:
        scales = req.scales or list(DEFAULT_SCALES)
        try:
            profile = profile_from_choices(
                req.choices, scales=scales, error_spec=req.error_spec
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        est = profile.estimation
        return s.ProfileResponse(
            gamma=profile.gamma,
            mu=profile.mu,
            se_gamma=profile.se_gamma,
            gamma_ci95=est.gamma_ci95,
            interval=profile.interval,
            tier=_tier_info(profile.gamma),
            monotone=profile.monotone,
            n_obs=est.n_obs,
            converged=est.converged,
            summary=profile.summary(),
        )

    # ----------------------------------------------------------- portfolio
    def _analysis(
        prices: pd.DataFrame,
        weights: pd.Series,
        stated_gamma: float | None,
        hedge_instrument: str | None = None,
    ) -> s.PortfolioAnalysis:
        hedge_instrument = hedge_instrument or _market_proxy()
        report = portfolio_covariance(prices, annualize=_periods_per_year())
        sigma = report.covariance
        vol = portfolio_volatility(weights, sigma)
        beta = portfolio_beta(weights, sigma, hedge_instrument)
        rev = revealed_gamma(vol, market_premium=MARKET_PREMIUM)
        return s.PortfolioAnalysis(
            volatility=vol,
            beta=beta,
            revealed_gamma=rev,
            revealed_tier=_tier_info(rev),
            stated_gamma=stated_gamma,
            stated_tier=_tier_info(stated_gamma) if stated_gamma is not None else None,
            market_premium_assumption=MARKET_PREMIUM,
        )

    @app.post("/api/portfolio", response_model=s.PortfolioResponse)
    def get_portfolio(req: s.PortfolioRequest) -> s.PortfolioResponse:
        if req.demo:
            prices, weights = _load_market(
                True, req.credentials, [], _market_proxy(), req.lookback_days
            )
            positions = [
                s.PositionOut(symbol=sym, weight=float(w))
                for sym, w in weights.sort_values(ascending=False).items()
            ]
            analysis = (
                _analysis(prices, weights, req.stated_gamma) if req.analyze else None
            )
            return s.PortfolioResponse(
                demo=True,
                positions=positions,
                portfolio_value=DEMO_PORTFOLIO_VALUE,
                analysis=analysis,
            )
        client = _client(req.credentials)
        try:
            raw = client.get_crypto_positions() if is_crypto() else client.get_positions()
            equity = None
            try:
                equity = float(client.get_account().get("equity") or 0) or None
            except (AlpacaError, ValueError, TypeError):
                pass
        except AlpacaError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        gross = sum(abs(p.market_value) for p in raw) or 1.0
        positions = [
            s.PositionOut(
                symbol=p.symbol,
                weight=p.market_value / gross,
                market_value=p.market_value,
                qty=p.qty,
            )
            for p in sorted(raw, key=lambda p: -abs(p.market_value))
        ]
        analysis = None
        if req.analyze and positions:
            weights = pd.Series({p.symbol: p.weight for p in positions})
            prices, _ = _load_market(
                False, req.credentials, [], _market_proxy(), req.lookback_days
            )
            try:
                analysis = _analysis(prices, weights, req.stated_gamma)
            except ValueError as exc:  # too little history etc.
                raise HTTPException(status_code=422, detail=str(exc))
        return s.PortfolioResponse(
            demo=False,
            positions=positions,
            portfolio_value=equity,
            analysis=analysis,
        )

    # ------------------------------------------------------------ optimize
    @app.post("/api/optimize", response_model=s.OptimizeResponse)
    def optimize(req: s.OptimizeRequest) -> s.OptimizeResponse:
        proxy = _market_proxy(req.hedge_instrument)
        prices, weights = _load_market(
            req.demo,
            req.credentials,
            [v.ticker for v in req.views],
            proxy,
            req.lookback_days,
        )
        views: list[View] = []
        for v in req.views:
            ticker = v.ticker.upper()
            if is_crypto():
                from ..crypto.universe import normalize_symbol

                ticker = normalize_symbol(ticker)
            if ticker not in prices.columns or prices[ticker].dropna().empty:
                raise HTTPException(
                    status_code=422, detail=f"No price history for {ticker}"
                )
            views.append(
                View(
                    ticker=ticker,
                    current_price=float(prices[ticker].dropna().iloc[-1]),
                    target_price=v.target_price,
                    confidence=v.confidence,
                    horizon_days=v.horizon_days,
                )
            )
        value = req.portfolio_value
        option_chain = None
        if req.demo:
            if value is None:
                value = DEMO_PORTFOLIO_VALUE
        else:
            try:
                client = _client(req.credentials)
                if value is None:
                    value = float(client.get_account().get("equity") or 0) or None
                # Live option chain for accurate hedge pricing (best-effort:
                # falls back to Black-Scholes if unavailable/not entitled).
                # Crypto has no listed options through this integration.
                try:
                    if is_crypto():
                        raise AlpacaError("crypto: no listed options")
                    from datetime import date, timedelta

                    option_chain = client.get_option_chain(
                        req.hedge_instrument,
                        expiration_gte=date.today() + timedelta(days=30),
                        expiration_lte=date.today() + timedelta(days=270),
                    )
                except AlpacaError:
                    option_chain = None
            except (AlpacaError, ValueError, TypeError, HTTPException):
                value = value if value is not None else None

        try:
            if is_crypto():
                from ..crypto.pipeline import rebalance_crypto

                report = rebalance_crypto(
                    prices,
                    weights,
                    gamma=req.gamma,
                    views=views,
                    covariance_method=req.cov_method,
                    long_only=req.long_only,
                    max_weight=req.max_weight,
                    market_proxy=proxy,
                    portfolio_value=value,
                )
            else:
                report = rebalance(
                    prices,
                    weights,
                    gamma=req.gamma,
                    views=views,
                    covariance_method=req.cov_method,
                    long_only=req.long_only,
                    max_weight=req.max_weight,
                    hedge_instrument=proxy,
                    hedge_spot=float(prices[proxy].iloc[-1])
                    if proxy in prices.columns
                    else 100.0,
                    portfolio_value=value,
                    option_chain=option_chain,
                )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        returns = None
        if report.black_litterman is not None:
            bl = report.black_litterman
            returns = [
                s.ReturnRow(
                    symbol=sym,
                    prior=float(bl.prior_mu[sym]),
                    posterior=float(bl.posterior_mu[sym]),
                    tilt=float(bl.posterior_mu[sym] - bl.prior_mu[sym]),
                )
                for sym in bl.posterior_mu.index
            ]
        trades = report.trade_list()
        mu_used = (
            report.black_litterman.posterior_mu
            if report.black_litterman is not None
            else report.covariance.mean_returns.reindex(report.optimized.weights.index)
        )
        reasons = trade_reasons(
            report.optimized.weights,
            report.current_weights,
            mu_used,
            report.covariance.covariance,
            req.gamma,
        )
        weight_rows = [
            s.WeightRow(
                symbol=sym,
                current=float(row["current"]),
                target=float(row["target"]),
                trade=float(row["trade"]),
                reason=reasons.get(sym),
            )
            for sym, row in trades.sort_values("target", ascending=False).iterrows()
        ]
        plan = report.hedge_plan
        return s.OptimizeResponse(
            gamma=req.gamma,
            tier=_tier_info(req.gamma),
            demo=req.demo,
            views=[
                {"description": v.describe(), "expected_return": v.expected_return}
                for v in views
            ],
            returns=returns,
            weights=weight_rows,
            expected_return=report.optimized.expected_return,
            volatility=report.optimized.volatility,
            utility=report.optimized.utility,
            hedge_plan=s.HedgePlanOut(
                gamma=plan.gamma,
                current_volatility=plan.current_volatility,
                target_volatility=plan.target_volatility,
                needs_hedge=plan.needs_hedge,
                portfolio_value=plan.portfolio_value,
                tolerable_annual_loss_usd=plan.tolerable_annual_loss_usd,
                current_annual_loss_usd=plan.current_annual_loss_usd,
                scenarios=[
                    s.StressScenarioOut(
                        name=x.name,
                        market_shock=x.market_shock,
                        loss_fraction=x.loss_fraction,
                        loss_usd=x.loss_usd,
                        hedged_loss_fraction=x.hedged_loss_fraction,
                        hedged_loss_usd=x.hedged_loss_usd,
                    )
                    for x in plan.scenarios
                ],
                suggestions=[
                    s.HedgeSuggestionOut(
                        kind=x.kind,
                        instrument=x.instrument,
                        description=x.description,
                        hedge_notional_fraction=x.hedge_notional_fraction,
                        hedged_volatility=x.hedged_volatility,
                        est_annual_cost_fraction=x.est_annual_cost_fraction,
                        warning=x.warning,
                        details=x.details,
                    )
                    for x in plan.suggestions
                ],
            ),
        )

    # --------------------------------------------------------------- hedge
    @app.post("/api/hedge", response_model=s.HedgePlanOut)
    def hedge(req: s.HedgeRequest) -> s.HedgePlanOut:
        opt = optimize(
            s.OptimizeRequest(
                gamma=req.gamma,
                views=[],
                demo=req.demo,
                credentials=req.credentials,
                cov_method=req.cov_method,
                lookback_days=req.lookback_days,
                hedge_instrument=req.hedge_instrument,
                portfolio_value=req.portfolio_value,
            )
        )
        return opt.hedge_plan

    # ------------------------------------------------------------- backtest
    @app.post("/api/backtest", response_model=s.BacktestResponse)
    def backtest(req: s.BacktestRequest) -> s.BacktestResponse:
        from ..backtest.engine import run_backtest

        if req.demo:
            if is_crypto():
                from ..crypto.universe import synthetic_crypto_universe

                prices, _ = synthetic_crypto_universe(
                    n_days=max(req.lookback_days + 80, 700)
                )
            else:
                prices, _ = synthetic_universe(n_days=max(req.lookback_days + 80, 600))
        else:
            prices, _ = _load_market(
                False, req.credentials, req.symbols or [], _market_proxy(),
                req.lookback_days,
            )
        try:
            result = run_backtest(
                prices,
                gamma=req.gamma,
                max_weight=req.max_weight,
                market=_market_proxy(),
                periods_per_year=_periods_per_year(),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return s.BacktestResponse(
            gamma=result.gamma,
            start=result.start,
            end=result.end,
            rebalances=result.rebalances,
            headline=result.headline,
            strategies=[
                s.StrategyOut(
                    name=st.name, label=st.label, equity_curve=st.equity_curve,
                    dates=st.dates, metrics=st.metrics,
                )
                for st in result.strategies
            ],
        )

    return app


app = create_app()
