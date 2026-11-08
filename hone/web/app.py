"""FastAPI application exposing the full Hone pipeline.

Endpoints
---------
GET  /api/menu           — questionnaire menus (3 stake scales x 10 rows)
POST /api/questionnaire  — choices -> gamma, noise, 50-tier placement
POST /api/portfolio      — current Alpaca paper positions (or demo data)
POST /api/optimize       — views -> Black-Litterman + MVO + hedge plan
POST /api/hedge          — hedge plan only
POST /api/broker/...     — link brokerages through SnapTrade (connect,
                           accounts, disconnect, unlink)
GET  /, /:product/...     — the React single-page app (built from frontend/)

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
SNAPTRADE_CLIENT_ID, SNAPTRADE_CONSUMER_KEY
    Turn on "link your brokerages" (Schwab, Fidelity, Robinhood, IBKR, ...)
    through SnapTrade.  Never sent to the browser.  With HONE_PUBLIC set,
    linking requires Supabase sign-in, so strangers can't create paid
    SnapTrade users on your account.
ALPACA_DATA_API_KEY, ALPACA_DATA_SECRET_KEY
    Alpaca keys used *only* for price history (never to read an account),
    so they are safe on a public server.  Linked-brokerage portfolios need a
    price source; without these, visitors must enter their own Alpaca keys.
SUPABASE_URL, SUPABASE_ANON_KEY
    Where to verify sign-in tokens.  Optional: by default they are read from
    static/config.js, the same values the browser uses.
"""

from __future__ import annotations

import base64
import mimetypes
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
from ..market_data.brokers import snaptrade as snap
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
    if v in ("prediction", "prediction-markets", "prediction_markets", "predict", "events"):
        return "prediction"
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


def is_prediction() -> bool:
    """The prediction-markets product: same questionnaire, no brokerage."""
    return asset_class() == "prediction"


def _periods_per_year() -> int:
    from ..crypto.universe import CRYPTO_PERIODS_PER_YEAR

    return CRYPTO_PERIODS_PER_YEAR if is_crypto() else 252


def _market_proxy(default: str = "SPY") -> str:
    from ..crypto.universe import MARKET_PROXY

    return MARKET_PROXY if is_crypto() else default


def _demo_journal(prices: pd.DataFrame, n: int = 14) -> list[s.PredictionIn]:
    """A synthetic track record for demo mode.

    An empty journal is a blank page that explains nothing, so demo mode
    ships a history: predictions made at real dates in the demo price
    series, with targets sized off each name's own volatility and stated
    confidences drawn deliberately too high — the pattern the page exists to
    detect.  The outcomes are whatever the demo prices actually did; they are
    not rigged, so the resulting Brier score is a real score of a fake
    forecaster.
    """
    import numpy as np

    rng = np.random.default_rng(4)
    symbols = [str(c) for c in prices.columns]
    if not symbols or len(prices) < 200:
        return []

    out: list[s.PredictionIn] = []
    horizons = [60.0, 90.0, 120.0, 180.0]
    for i in range(n):
        sym = symbols[i % len(symbols)]
        series = prices[sym].dropna()
        if len(series) < 200:
            continue
        horizon = float(rng.choice(horizons))
        # Place the decision far enough back that the horizon has elapsed.
        offset = int(rng.integers(int(horizon) + 5, min(len(series) - 1, 1200)))
        made_at = series.index[-offset]
        entry = float(series.iloc[-offset])
        vol = float(series.pct_change().dropna().tail(120).std()) or 0.02
        # Target a move of 0.3-1.3 sigma over the horizon — ambitious but
        # reachable, so the demo record shows a forecaster who is somewhat
        # overconfident rather than one who is hopeless.
        move = vol * (horizon**0.5) * float(rng.uniform(0.3, 1.3))
        bullish = bool(rng.random() < 0.75)  # retail views skew long
        target = entry * (1 + move) if bullish else entry * (1 - move)
        out.append(
            s.PredictionIn(
                id=f"demo-{i}",
                ticker=sym,
                direction="bullish" if bullish else "bearish",
                entry_price=round(entry, 2),
                target_price=round(target, 2),
                confidence=float(rng.choice([0.55, 0.6, 0.7, 0.75, 0.8, 0.85])),
                horizon_days=horizon,
                thesis="Example entry (demo history)",
                created_at=pd.Timestamp(made_at).date().isoformat(),
            )
        )
    return out


def _resolve_journal(
    predictions: list[s.PredictionIn], prices: pd.DataFrame
) -> list:
    """Resolve journal entries against a price panel, ignoring bad rows.

    Used by both the personalization path and the training export; a
    malformed entry should degrade the feature, never break the request
    the user actually made.
    """
    from ..journal.records import Prediction, resolve_all

    built = []
    for raw in predictions:
        try:
            built.append(
                Prediction(
                    ticker=raw.ticker,
                    entry_price=raw.entry_price,
                    target_price=raw.target_price,
                    confidence=raw.confidence,
                    horizon_days=raw.horizon_days,
                    direction=raw.direction,
                    thesis=raw.thesis,
                    created_at=raw.created_at,
                    id=raw.id,
                )
            )
        except ValueError:
            continue
    if not built:
        return []
    resolved, _ = resolve_all(built, prices)
    return resolved


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


# ------------------------------------------------------------ sign-in
#: Verified Supabase tokens -> (user id, expiry). Saves a round trip to
#: Supabase on every brokerage call. Tokens themselves expire within the hour.
_SESSION_CACHE: dict[str, tuple[str, float]] = {}
_SESSION_TTL = 300.0

#: The header the browser sends its Supabase access token in. Not
#: `Authorization`: that one carries the HONE_ACCESS_PASSWORD Basic-auth
#: login when the site is password-gated, and overriding it would lock the
#: user out.
SESSION_HEADER = "x-hone-session"


def _supabase_settings() -> tuple[str, str]:
    """(project URL, anon key) from env, else from static/config.js."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if url and key:
        return url.rstrip("/"), key
    try:
        import re

        text = (STATIC_DIR / "config.js").read_text()
        url_m = re.search(r'supabaseUrl\s*:\s*["\']([^"\']*)', text)
        key_m = re.search(r'supabaseAnonKey\s*:\s*["\']([^"\']*)', text)
        if url_m and key_m:
            return url_m.group(1).rstrip("/"), key_m.group(1)
    except OSError:
        pass
    return "", ""


def _signed_in_user(request: Request) -> str | None:
    """The Supabase user id behind this request's session token, or None.

    Raises 401 when a token is present but Supabase rejects it (expired or
    forged), so the user is told to sign in again rather than silently
    treated as anonymous.
    """
    token = request.headers.get(SESSION_HEADER, "").strip()
    if not token:
        return None
    import hashlib
    import time

    digest = hashlib.sha256(token.encode()).hexdigest()
    hit = _SESSION_CACHE.get(digest)
    if hit and hit[1] > time.monotonic():
        return hit[0]
    url, key = _supabase_settings()
    if not url or not key:
        return None
    import requests

    try:
        resp = requests.get(
            f"{url}/auth/v1/user",
            headers={"apikey": key, "Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Couldn't check your sign-in. Try again.")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=401, detail="Your sign-in has expired. Sign in again under Data & account."
        )
    user_id = str(resp.json().get("id") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Sign-in not recognised. Sign in again.")
    if len(_SESSION_CACHE) > 5000:
        _SESSION_CACHE.clear()
    _SESSION_CACHE[digest] = (user_id, time.monotonic() + _SESSION_TTL)
    return user_id


def _snaptrade_user_id(request: Request, local_id: str | None) -> str:
    """Which SnapTrade user this person is.

    Signed in: derived from their Supabase id, so each account gets exactly
    one SnapTrade user (and so one bill) no matter how often they click
    Connect. Not signed in: only allowed on private servers, keyed by a
    random id the browser generated.
    """
    import re

    uid = _signed_in_user(request)
    if uid:
        return f"hone-{uid}"
    if _public_mode():
        raise HTTPException(
            status_code=401,
            detail="Sign in to link your brokerages (Data & account → Account).",
        )
    if not local_id or not re.fullmatch(r"[A-Za-z0-9-]{16,64}", local_id):
        raise HTTPException(status_code=422, detail="local_id: a random id is required.")
    return f"hone-local-{local_id}"


def _check_link_owner(request: Request, link: s.BrokerLink) -> None:
    """On public servers, a link may only be used by the account it belongs to."""
    if not _public_mode():
        return
    uid = _signed_in_user(request)
    if not uid or link.user_id != f"hone-{uid}":
        raise HTTPException(
            status_code=403,
            detail="This brokerage link belongs to a different sign-in. Sign in "
            "with that account, or connect your brokerages again.",
        )


def _same_site_redirect(url: str | None, request: Request) -> str | None:
    """Only let SnapTrade send users back to *this* site (no open redirect)."""
    if not url:
        return None
    from urllib.parse import urlparse

    target = urlparse(url)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    if target.scheme in ("http", "https") and target.netloc == host:
        return url
    return None


# ------------------------------------------------------------ brokerages
def _broker(creds: s.AlpacaCredentials | None) -> s.BrokerLink | None:
    """The request's linked-brokerage identity, if it's using one."""
    if creds and creds.source == "brokers" and not creds.broker:
        raise HTTPException(
            status_code=400,
            detail="No brokerages are linked on this device yet. Connect one "
            "under Data & account, or switch to sample data.",
        )
    return creds.broker if creds and creds.broker else None


def _snaptrade() -> snap.SnapTradeClient:
    try:
        return snap.SnapTradeClient()
    except snap.SnapTradeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def _snaptrade_http(exc: snap.SnapTradeError) -> HTTPException:
    """Turn a SnapTrade failure into a message the user can act on."""
    if exc.status in (401, 403):
        return HTTPException(
            status_code=401,
            detail="Your brokerage link is no longer valid. Reconnect your "
            "brokerages under Data & account.",
        )
    if exc.status == 429:
        return HTTPException(
            status_code=429,
            detail="The brokerage connection is busy (rate limit). Wait a "
            "minute and try again.",
        )
    if exc.status == 503 and "configured" in str(exc):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=502, detail=f"Brokerage data unavailable: {exc}")


def _broker_holdings(creds: s.AlpacaCredentials | None) -> snap.BrokerHoldings:
    link = _broker(creds)
    assert link is not None
    try:
        return snap.fetch_holdings(
            _snaptrade(),
            link.user_id,
            link.user_secret,
            crypto=is_crypto(),
            account_ids=link.account_ids,
        )
    except snap.SnapTradeError as exc:
        raise _snaptrade_http(exc)


def _data_client(creds: s.AlpacaCredentials | None) -> AlpacaClient:
    """An Alpaca client for *price history only* (linked-brokerage mode).

    Holdings come from SnapTrade, so this client is never asked what anyone
    owns. In order of preference: the user's own Alpaca keys, the server's
    market-data-only keys (safe on a public server), then — on private
    servers only — the server's regular ALPACA_* keys.
    """
    if creds and creds.api_key and creds.secret_key:
        return AlpacaClient(api_key=creds.api_key, secret_key=creds.secret_key)
    key = os.environ.get("ALPACA_DATA_API_KEY")
    secret = os.environ.get("ALPACA_DATA_SECRET_KEY")
    if key and secret:
        return AlpacaClient(api_key=key, secret_key=secret)
    if not _public_mode():
        try:
            return AlpacaClient()
        except AlpacaError:
            pass
    raise HTTPException(
        status_code=503,
        detail="This server has no price-history source for linked "
        "brokerages. Enter your own Alpaca keys (used only for prices), or "
        "set ALPACA_DATA_API_KEY / ALPACA_DATA_SECRET_KEY on the server.",
    )


def _load_broker_market(
    creds: s.AlpacaCredentials | None,
    extra_symbols: list[str],
    market_proxy: str,
    lookback_days: int,
) -> tuple[pd.DataFrame, pd.Series, snap.BrokerHoldings, list[snap.Holding]]:
    """Holdings from every linked brokerage, priced from Alpaca market data.

    Returns (prices, weights, holdings, unpriced). ``unpriced`` are holdings
    the price source has no history for (delisted, OTC, too new...); they're
    left out of the weights and reported, not silently dropped.
    """
    held = _broker_holdings(creds)
    if not held.holdings:
        what = "crypto" if is_crypto() else "stock or ETF"
        raise HTTPException(
            status_code=400,
            detail=f"No {what} positions Hone can model in your linked "
            "brokerage accounts. Link another account, or use sample data.",
        )
    client = _data_client(creds)
    try:
        if is_crypto():
            from ..crypto.universe import normalize_symbol

            symbols = sorted(
                {h.symbol for h in held.holdings}
                | {normalize_symbol(t) for t in extra_symbols}
                | {normalize_symbol(market_proxy)}
            )
            start = date.today() - timedelta(days=int(lookback_days * 1.2))
            prices = client.get_crypto_bars(symbols, start=start)
        else:
            symbols = sorted(
                {h.symbol for h in held.holdings}
                | {t.upper() for t in extra_symbols}
                | {market_proxy}
            )
            start = date.today() - timedelta(days=int(lookback_days * 1.6))
            prices = client.get_bars(symbols, start=start)
    except AlpacaError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    prices = prices.dropna(axis=1, how="all").tail(lookback_days)
    priced = [h for h in held.holdings if h.symbol in prices.columns]
    unpriced = [h for h in held.holdings if h.symbol not in prices.columns]
    if not priced:
        raise HTTPException(
            status_code=502,
            detail="No price history was found for any of your linked "
            "holdings, so there is nothing to model.",
        )
    weights = pd.Series({h.symbol: h.market_value for h in priced}, dtype=float)
    weights = weights / (weights.abs().sum() or 1.0)
    return prices, weights, held, unpriced


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
    if _broker(creds):
        prices, weights, _, _ = _load_broker_market(
            creds, extra_symbols, hedge_instrument, lookback_days
        )
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
        path = request.url.path.rstrip("/")
        by_path = None
        if path.startswith("/crypto"):
            by_path = "crypto"
        elif path.startswith("/prediction-markets"):
            by_path = "prediction"
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
    # The frontend is a React single-page app built from frontend/ into
    # STATIC_DIR (index.html + hashed files under assets/). Every page URL
    # returns the same index.html and the browser router picks the page.
    def spa_index() -> FileResponse:
        # Never cache the shell, so a deploy is picked up on the next load;
        # the hashed assets it points at are cached forever instead.
        return FileResponse(
            STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"}
        )

    @app.get("/", include_in_schema=False)
    @app.get("/stocks", include_in_schema=False)
    def index() -> FileResponse:
        return spa_index()

    @app.get("/crypto", include_in_schema=False)
    @app.get("/crypto/", include_in_schema=False)
    def index_crypto() -> FileResponse:
        """Same single-page app, crypto product (see resolve_asset_class)."""
        return spa_index()

    @app.get("/prediction-markets", include_in_schema=False)
    @app.get("/prediction-markets/", include_in_schema=False)
    def index_prediction() -> FileResponse:
        """Same single-page app, prediction-markets product."""
        return spa_index()

    @app.get("/assets/{name}", include_in_schema=False)
    def built_asset(name: str) -> FileResponse:
        """Hashed JS/CSS from the Vite build. `name` cannot contain '/'."""
        path = STATIC_DIR / "assets" / name
        if name.startswith(".") or not path.is_file():
            raise HTTPException(status_code=404, detail="not found")
        media_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if name.endswith(".js"):
            media_type = "application/javascript"
        return FileResponse(
            path,
            media_type=media_type,
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    @app.get("/api/health", include_in_schema=False)
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/config", include_in_schema=False)
    def config() -> dict:
        """Asset-class configuration the frontend uses to swap copy."""
        crypto = is_crypto()
        if is_prediction():
            return {
                "asset_class": "prediction",
                "auth_enabled": True,
                "market_proxy": None,
                "periods_per_year": None,
                "copy": {
                    "product": "Hone Markets",
                    "descriptor": "Hedge the income risk you already carry",
                    "asset_word": "contracts",
                    "asset_word_singular": "contract",
                    "holdings_word": "the exposure you carry",
                    "example_ticker": "KXASPSNOWM",
                    "example_target": "35¢",
                    "market_name": "Kalshi",
                    "cash_word": "cash",
                    "account_word": "Kalshi account (not connected — Hone only sizes)",
                    "hedge_note": (
                        "Hone sizes event contracts against your income risk and explains "
                        "the position. It never places orders, and it holds no Kalshi keys."
                    ),
                    "volatility_note": "",
                },
            }
        return {
            "asset_class": asset_class(),
            "auth_enabled": True,
            # Linking real brokerages (SnapTrade). `requires_sign_in` is true
            # on public servers: each link is a paid SnapTrade user.
            "brokers": {
                "enabled": snap.configured(),
                "requires_sign_in": _public_mode(),
            },
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
        "favicon.svg": "image/svg+xml",
        "favicon-32.png": "image/png",
        "apple-touch-icon.png": "image/png",
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
                source="sample",
            )
        if _broker(req.credentials):
            return _broker_portfolio(req)
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
            source="alpaca",
        )

    def _broker_portfolio(req: s.PortfolioRequest) -> s.PortfolioResponse:
        """Linked brokerages: every account combined into one portfolio."""
        prices, weights, held, unpriced = _load_broker_market(
            req.credentials, [], _market_proxy(), req.lookback_days
        )
        modelled = [h for h in held.holdings if h.symbol in weights.index]
        positions = [
            s.PositionOut(
                symbol=h.symbol,
                weight=float(weights[h.symbol]),
                market_value=h.market_value,
                qty=h.qty,
            )
            for h in modelled
        ]
        skipped = [
            s.SkippedHoldingOut(
                symbol=k.symbol, reason=k.reason, market_value=k.market_value, account=k.account
            )
            for k in held.skipped
        ] + [
            s.SkippedHoldingOut(
                symbol=h.symbol,
                reason="No price history from the market-data source",
                market_value=h.market_value,
                account=", ".join(h.accounts) or None,
            )
            for h in unpriced
        ]
        analysis = None
        if req.analyze:
            try:
                analysis = _analysis(prices, weights, req.stated_gamma)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc))
        return s.PortfolioResponse(
            demo=False,
            positions=positions,
            # Value of what's modelled. Cash and skipped positions are listed
            # separately, so hedges are sized to the part Hone can see.
            portfolio_value=sum(abs(h.market_value) for h in modelled) or None,
            analysis=analysis,
            source="brokerages",
            accounts=[snap.account_label(a) for a in held.accounts],
            skipped=skipped,
        )

    # ---------------------------------------------------------- brokerages
    # Linking flow (see hone/market_data/brokers/snaptrade.py):
    #   1. POST /api/broker/connect -> a SnapTrade Connection Portal URL (and,
    #      the first time, a new link the browser must keep).
    #   2. The browser goes there; the user picks a broker and signs in on
    #      SnapTrade's page; SnapTrade redirects back to redirect_url.
    #   3. POST /api/broker/accounts lists what got linked. From then on every
    #      market request carries credentials.broker, and holdings come from
    #      all linked accounts combined.
    @app.post("/api/broker/connect", response_model=s.BrokerConnectResponse)
    def broker_connect(req: s.BrokerConnectRequest, request: Request) -> s.BrokerConnectResponse:
        client = _snaptrade()
        link = req.link
        if link is not None:
            _check_link_owner(request, link)
        try:
            if link is None or req.reset:
                user_id = _snaptrade_user_id(request, req.local_id)
                if req.reset:
                    # The secret was lost: start this person's SnapTrade user
                    # over. Their old connections go with it.
                    try:
                        client.delete_user(user_id)
                    except snap.SnapTradeError:
                        pass
                try:
                    secret = client.register_user(user_id)
                except snap.SnapTradeError as exc:
                    if exc.status in (400, 409):
                        raise HTTPException(
                            status_code=409,
                            detail="Your brokerages are already linked from another "
                            "device, but this one doesn't have the key to read "
                            "them. Sign in with the same account, or reset the link "
                            "(you'll reconnect your brokerages).",
                        )
                    raise
                link = s.BrokerLink(user_id=user_id, user_secret=secret)
            url = client.login_link(
                link.user_id,
                link.user_secret,
                redirect_url=_same_site_redirect(req.redirect_url, request),
                reconnect=req.reconnect,
            )
        except snap.SnapTradeError as exc:
            raise _snaptrade_http(exc)
        snap.forget(link.user_id)
        return s.BrokerConnectResponse(
            redirect_url=url,
            link=s.BrokerLink(user_id=link.user_id, user_secret=link.user_secret),
        )

    @app.post("/api/broker/accounts", response_model=s.BrokerAccountsResponse)
    def broker_accounts(req: s.BrokerLinkRequest, request: Request) -> s.BrokerAccountsResponse:
        """The linked brokerages and their accounts (always fresh)."""
        _check_link_owner(request, req.link)
        client = _snaptrade()
        link = req.link
        try:
            conns = client.list_connections(link.user_id, link.user_secret)
            accounts = client.list_accounts(link.user_id, link.user_secret)
        except snap.SnapTradeError as exc:
            raise _snaptrade_http(exc)
        # A user looking at this list may have just linked something: make
        # the next calculation fetch holdings again instead of using cache.
        snap.forget(link.user_id)
        out_conns = []
        for c in conns:
            b = c.get("brokerage") or {}
            out_conns.append(
                s.BrokerConnectionOut(
                    id=str(c.get("id")),
                    brokerage=b.get("display_name") or b.get("name") or c.get("name") or "Brokerage",
                    logo_url=b.get("aws_s3_square_logo_url") or b.get("aws_s3_logo_url"),
                    disabled=bool(c.get("disabled")),
                    created=str(c.get("created_date") or "") or None,
                )
            )
        out_accts = []
        for a in accounts:
            total = (a.get("balance") or {}).get("total") or {}
            amount = total.get("amount") if isinstance(total, dict) else None
            try:
                amount = float(amount) if amount is not None else None
            except (TypeError, ValueError):
                amount = None
            category = a.get("account_category")
            out_accts.append(
                s.BrokerAccountOut(
                    id=str(a.get("id")),
                    connection_id=a.get("brokerage_authorization"),
                    label=snap.account_label(a),
                    institution=a.get("institution_name") or "Brokerage",
                    value=amount,
                    currency=total.get("currency") if isinstance(total, dict) else None,
                    is_paper=bool(a.get("is_paper")),
                    investment=not category or category == "INVESTMENT",
                )
            )
        return s.BrokerAccountsResponse(connections=out_conns, accounts=out_accts)

    @app.post("/api/broker/disconnect")
    def broker_disconnect(req: s.BrokerDisconnectRequest, request: Request) -> dict:
        """Unlink one brokerage. Its accounts drop out of the portfolio."""
        _check_link_owner(request, req.link)
        try:
            _snaptrade().remove_connection(
                req.link.user_id, req.link.user_secret, req.connection_id
            )
        except snap.SnapTradeError as exc:
            raise _snaptrade_http(exc)
        snap.forget(req.link.user_id)
        return {"ok": True}

    @app.post("/api/broker/unlink")
    def broker_unlink(req: s.BrokerLinkRequest, request: Request) -> dict:
        """Delete this person's SnapTrade user and every connection it has."""
        _check_link_owner(request, req.link)
        client = _snaptrade()
        try:
            # deleteUser needs only the user id, so prove the caller holds the
            # secret first — otherwise anyone who guessed an id could unlink it.
            client.list_connections(req.link.user_id, req.link.user_secret)
            client.delete_user(req.link.user_id)
        except snap.SnapTradeError as exc:
            raise _snaptrade_http(exc)
        snap.forget(req.link.user_id)
        return {"ok": True}

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
        # The user's own forecasting record, if they have one, rescales what
        # their stated confidence is worth before Black-Litterman uses it.
        # The map lives in the browser; the arithmetic lives here, so there
        # is exactly one implementation of it.
        cal_report = None
        if req.calibration is not None and req.calibration.actionable:
            from ..journal.calibration import CalibrationReport

            cal_report = CalibrationReport(
                n=req.calibration.n, brier=float("nan"), base_rate=float("nan"),
                mean_confidence=float("nan"),
                intercept=req.calibration.intercept, slope=req.calibration.slope,
                reliability=float("nan"), resolution=float("nan"),
                uncertainty=float("nan"), skill_vs_base_rate=float("nan"),
                actionable=True,
            )
        adjustments: list[s.ConfidenceAdjustment] = []
        # What the user actually typed, kept separate from what the optimizer
        # used. The journal must record the stated number: scoring the
        # adjusted one would feed the calibration its own output and discount
        # the user a little further on every pass.
        stated_by_ticker: dict[str, float] = {}

        views: list[View] = []
        for v in req.views:
            ticker = v.ticker.upper()
            if is_crypto():
                from ..crypto.universe import normalize_symbol

                ticker = normalize_symbol(ticker)
            if ticker not in prices.columns or prices[ticker].dropna().empty:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"No price history for {ticker}. Available here: "
                        + ", ".join(map(str, prices.columns))
                    ),
                )
            confidence = v.confidence
            stated_by_ticker[ticker] = v.confidence
            if cal_report is not None:
                from ..journal.calibration import apply_calibration

                confidence = apply_calibration(v.confidence, cal_report)
                if abs(confidence - v.confidence) > 1e-4:
                    adjustments.append(
                        s.ConfidenceAdjustment(
                            ticker=ticker, stated=v.confidence, used=confidence
                        )
                    )
            views.append(
                View(
                    ticker=ticker,
                    current_price=float(prices[ticker].dropna().iloc[-1]),
                    target_price=v.target_price,
                    confidence=confidence,
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
                if _broker(req.credentials):
                    # Linked brokerages: value is what Hone models (see
                    # _broker_portfolio); prices/options from market data.
                    client = _data_client(req.credentials)
                    if value is None:
                        # Only holdings that made it into the model (have
                        # prices), matching /api/portfolio's figure.
                        value = sum(
                            abs(h.market_value)
                            for h in _broker_holdings(req.credentials).holdings
                            if h.symbol in weights.index
                        ) or None
                else:
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
            # The prices here are the server's, not the browser's guess —
            # the decision journal records what the view was actually priced
            # off, so a later score cannot be argued with.
            views=[
                {
                    "description": v.describe(),
                    "expected_return": v.expected_return,
                    "ticker": v.ticker,
                    "current_price": v.current_price,
                    "target_price": v.target_price,
                    "confidence": v.confidence,
                    "stated_confidence": stated_by_ticker.get(
                        v.ticker, v.confidence
                    ),
                    "horizon_days": v.horizon_days,
                }
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
                expected_excess_return=plan.expected_excess_return,
                premium_is_negative=plan.premium_is_negative,
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
            confidence_adjustments=adjustments or None,
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

    # ----------------------------------------------------------- tail risk
    @app.post("/api/cvar", response_model=s.CVaRResponse)
    def cvar(req: s.CVaRRequest) -> s.CVaRResponse:
        """Tail-risk view of the portfolio: CVaR-optimal weights and why.

        Variance and CVaR disagree exactly when the return distribution is
        not normal, which is most of the time and nearly all of the time
        in crypto.  This endpoint shows both answers side by side rather
        than picking one, because the disagreement is the information.
        """
        from ..optimization.cvar import (
            cvar_gamma_weights,
            cvar_of_weights,
            historical_scenarios,
            min_cvar_weights,
            tail_comparison,
        )

        prices, weights = _load_market(
            req.demo, req.credentials, [], _market_proxy(), req.lookback_days
        )
        try:
            scenarios = historical_scenarios(
                prices, periods_per_year=_periods_per_year(), horizon=req.horizon
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        if len(scenarios) < 40:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Only {len(scenarios)} scenarios at a {req.horizon}-period "
                    "horizon — far too few to say anything about a tail. Use a "
                    "longer lookback or a shorter horizon."
                ),
            )

        # The mean-CVaR arm needs expected returns, and sample means over a
        # couple of years are noise — feeding them in is the classic error
        # that gives mean-variance optimization its reputation. Use the same
        # equilibrium prior the rest of the pipeline uses, converted to the
        # scenario period, so "no views" means "hold roughly what the market
        # holds" here exactly as it does in Black-Litterman.
        from ..market_data.covariance import portfolio_covariance
        from ..optimization.black_litterman import (
            calibrate_delta,
            implied_equilibrium_returns,
        )

        ppy = _periods_per_year()
        try:
            sigma = portfolio_covariance(
                prices[scenarios.columns], annualize=ppy
            ).covariance
            prior_w = weights.reindex(scenarios.columns).fillna(0.0)
            if prior_w.sum() <= 0:
                prior_w = pd.Series(
                    1.0 / len(scenarios.columns), index=scenarios.columns
                )
            prior_w = prior_w / prior_w.sum()
            delta = calibrate_delta(sigma, prior_w)
            pi_annual = implied_equilibrium_returns(sigma, prior_w, delta)
            pi_period = pi_annual * (req.horizon / ppy)
        except (ValueError, KeyError):
            pi_period = scenarios.mean()

        try:
            risk_first = min_cvar_weights(
                scenarios, beta=req.beta, max_weight=req.max_weight
            )
            gamma_matched = cvar_gamma_weights(
                scenarios, gamma=req.gamma, mu=pi_period,
                beta=req.beta, max_weight=req.max_weight,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        current = weights.reindex(scenarios.columns).fillna(0.0)
        if current.sum() > 0:
            current = current / current.sum()
        equal = pd.Series(1.0 / len(scenarios.columns), index=scenarios.columns)

        labels = {
            "current": "What you hold now",
            "equal_weight": "Equal weight (1/N)",
            "gamma_cvar": f"Mean-CVaR at your γ = {req.gamma:.2f}",
            "min_cvar": "Minimum CVaR (risk-first)",
        }
        table = tail_comparison(
            scenarios,
            {
                "current": current,
                "equal_weight": equal,
                "gamma_cvar": gamma_matched.weights,
                "min_cvar": risk_first.weights,
            },
            beta=req.beta,
        )

        value = req.portfolio_value
        if value is None and req.demo:
            value = DEMO_PORTFOLIO_VALUE
        saved = None
        current_cvar = cvar_of_weights(scenarios, current, req.beta)
        if value:
            saved = float((current_cvar - risk_first.cvar) * value)

        def rows(target: pd.Series) -> list[s.WeightRow]:
            return [
                s.WeightRow(
                    symbol=str(sym),
                    current=float(current.get(sym, 0.0)),
                    target=float(target.get(sym, 0.0)),
                    trade=float(target.get(sym, 0.0) - current.get(sym, 0.0)),
                    reason="",
                )
                for sym in scenarios.columns
            ]

        period = (
            "day" if req.horizon == 1
            else ("month" if 18 <= req.horizon <= 24 else f"{req.horizon}-period")
        )
        summary = (
            f"Across {len(scenarios)} overlapping {period} windows, the worst "
            f"{1 - req.beta:.0%} averaged a {current_cvar:.1%} loss on what you "
            f"hold. The minimum-CVaR portfolio would have averaged "
            f"{risk_first.cvar:.1%}."
        )

        return s.CVaRResponse(
            beta=req.beta,
            horizon=req.horizon,
            n_scenarios=risk_first.n_scenarios,
            tail_scenarios=risk_first.tail_scenarios,
            min_cvar_weights=rows(risk_first.weights),
            gamma_cvar_weights=rows(gamma_matched.weights),
            comparison=[
                s.TailRow(
                    portfolio=name,
                    label=labels.get(name, name),
                    mean=float(row["mean"]),
                    volatility=float(row["volatility"]),
                    var=float(row["var"]),
                    cvar=float(row["cvar"]),
                    worst=float(row["worst"]),
                    skew=float(row["skew"]) if pd.notna(row["skew"]) else 0.0,
                )
                for name, row in table.iterrows()
            ],
            portfolio_value=value,
            cvar_saved_usd=saved,
            summary=summary,
        )

    # -------------------------------------------- flexible views (pooling)
    @app.post("/api/pooling", response_model=s.PoolingResponse)
    def pooling(req: s.PoolingRequest) -> s.PoolingResponse:
        """Views Black-Litterman cannot express, via entropy pooling.

        Probability-of-an-event views, rankings without price targets,
        volatility views and conditional crash relationships all become
        constraints on scenario probabilities.  The posterior is the
        minimum-relative-entropy distribution satisfying them — the update
        that adds no information beyond what the views assert — and it
        drives the CVaR optimizer directly, so nothing along this path
        assumes normality.
        """
        from ..optimization.cvar import (
            cvar_gamma_weights,
            cvar_of_weights,
            historical_scenarios,
        )
        from ..optimization import entropy_pooling as ep

        prices, weights = _load_market(
            req.demo, req.credentials, [], _market_proxy(), req.lookback_days
        )
        try:
            scenarios = historical_scenarios(
                prices, periods_per_year=_periods_per_year(), horizon=req.horizon
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        available = ", ".join(map(str, scenarios.columns))
        built: list[ep.View] = []
        for v in req.views:
            try:
                if v.kind == "mean":
                    built.append(ep.mean_view(scenarios, v.ticker, v.value or 0.0))
                elif v.kind == "probability":
                    built.append(
                        ep.probability_view(
                            scenarios, v.ticker, v.threshold or 0.0,
                            v.value or 0.0, below=v.below,
                        )
                    )
                elif v.kind == "ranking":
                    built.append(
                        ep.ranking_view(scenarios, v.ticker, v.versus or "")
                    )
                elif v.kind == "volatility":
                    built.append(
                        ep.volatility_view(scenarios, v.ticker, v.value or 0.0)
                    )
                elif v.kind == "conditional":
                    built.append(
                        ep.conditional_view(
                            scenarios, v.ticker, v.threshold or 0.0,
                            v.versus or "", v.value or 0.0,
                        )
                    )
                else:
                    raise HTTPException(
                        status_code=422, detail=f"unknown view kind {v.kind!r}"
                    )
            except KeyError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=f"{exc.args[0]} Available here: {available}",
                )
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc))

        if not built:
            raise HTTPException(status_code=422, detail="no views supplied")

        result = ep.entropy_pooling(built)
        prior_mu = scenarios.mean()
        post_mu, _ = ep.posterior_moments(scenarios, result.probabilities)

        resampled = ep.resample_scenarios(scenarios, result.probabilities, seed=7)
        portfolio = cvar_gamma_weights(
            resampled, gamma=req.gamma, mu=post_mu,
            beta=req.beta, max_weight=req.max_weight,
        )
        current = weights.reindex(scenarios.columns).fillna(0.0)
        if current.sum() > 0:
            current = current / current.sum()

        cost_note = (
            " The views discard "
            f"{result.confidence_cost:.0%} of the scenario set to hold, so what "
            "is left is thin — especially in the tail."
            if result.confidence_cost > 0.25
            else ""
        )
        summary = (
            f"{len(built)} view{'s' if len(built) != 1 else ''} applied to "
            f"{len(scenarios)} scenarios; the posterior effectively uses "
            f"{result.effective_scenarios:.0f} of them.{cost_note}"
        )

        return s.PoolingResponse(
            views=[
                s.PoolingViewOut(
                    label=v.label,
                    target=v.target,
                    achieved=result.achieved.get(v.label, float("nan")),
                    satisfied=(
                        abs(result.achieved.get(v.label, 0.0) - v.target) < 1e-4
                        if v.kind == "eq"
                        else (
                            result.achieved.get(v.label, 0.0) <= v.target + 1e-8
                            if v.kind == "le"
                            else result.achieved.get(v.label, 0.0) >= v.target - 1e-8
                        )
                    ),
                    binding=(
                        v.kind == "eq"
                        or abs(result.achieved.get(v.label, 0.0) - v.target) < 1e-6
                    ),
                )
                for v in built
            ],
            n_scenarios=len(scenarios),
            effective_scenarios=result.effective_scenarios,
            prior_effective_scenarios=result.prior_effective_scenarios,
            confidence_cost=result.confidence_cost,
            relative_entropy=result.relative_entropy,
            collapsed=result.collapsed,
            prior_mu=[
                s.ReturnRow(
                    symbol=str(sym),
                    prior=float(prior_mu[sym]),
                    posterior=float(post_mu[sym]),
                    tilt=float(post_mu[sym] - prior_mu[sym]),
                )
                for sym in scenarios.columns
            ],
            weights=[
                s.WeightRow(
                    symbol=str(sym),
                    current=float(current.get(sym, 0.0)),
                    target=float(portfolio.weights.get(sym, 0.0)),
                    trade=float(
                        portfolio.weights.get(sym, 0.0) - current.get(sym, 0.0)
                    ),
                    reason="",
                )
                for sym in scenarios.columns
            ],
            cvar_before=cvar_of_weights(scenarios, current, req.beta),
            cvar_after=cvar_of_weights(resampled, portfolio.weights, req.beta),
            summary=summary,
        )

    # ----------------------------------------------- adaptive elicitation
    @app.post("/api/dose", response_model=s.DoseResponse)
    def dose(req: s.DoseRequest) -> s.DoseResponse:
        """Serve the next adaptive question, or the finished estimate.

        Stateless: the client holds the answers and posts all of them each
        time.  The posterior is a pure function of that list, so replaying
        it is exact and there is no session to expire mid-questionnaire.
        Answers reference the server's question bank by index, so a client
        cannot rewrite the experiment it is being scored on.
        """
        from ..risk_profile import dose as D

        try:
            answers = [
                D.DoseAnswer(question_id=a.question_id, choice=a.choice)
                for a in req.answers
            ]
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        post = D.posterior(answers)
        result = D.summarize(answers)
        state = s.DoseStateOut(
            gamma=result.gamma,
            gamma_sd=result.gamma_sd,
            gamma_ci90=result.gamma_ci90,
            mu=result.mu,
            n_answers=result.n_answers,
            tier=_tier_info(result.gamma),
            tier_confidence=result.tier_confidence,
            gamma_grid=[float(g) for g in D.GAMMA_GRID],
            gamma_marginal=result.gamma_marginal,
            summary=result.summary,
        )

        if D.is_finished(post, n_questions=req.n_questions):
            return s.DoseResponse(finished=True, question=None, state=state)

        qid, gain = D.next_question(answers, post)
        text_a, text_b = D.question_text(D.QUESTION_BANK[qid])
        return s.DoseResponse(
            finished=False,
            question=s.DoseQuestionOut(
                question_id=qid,
                number=len(answers) + 1,
                total=req.n_questions,
                option_a=text_a,
                option_b=text_b,
                expected_information_gain=gain,
            ),
            state=state,
        )

    # ---------------------------------------------------- training export
    @app.post("/api/export/training", response_model=s.TrainingExportResponse)
    def export_training(req: s.TrainingExportRequest) -> s.TrainingExportResponse:
        """Export the journal as fine-tuning data, with an honest verdict.

        The export always runs — it is the user's data — but it says
        plainly when training on it would produce a worse model than the
        one they started with, which at retail volumes is nearly always.
        """
        from ..llm.export import build_dataset
        from ..llm.personalize import MIN_EXAMPLES, build_personalization

        symbols = sorted({p.ticker.upper() for p in req.predictions})
        try:
            prices, _ = _load_market(
                req.demo, req.credentials, symbols, _market_proxy(),
                req.lookback_days,
            )
        except (AlpacaError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        resolved = _resolve_journal(req.predictions, prices)
        report = build_dataset(
            resolved,
            include_compile=req.include_compile,
            include_calibration=req.include_calibration,
        )
        few_shot = build_personalization(resolved)

        return s.TrainingExportResponse(
            n_examples=report.n,
            n_compile=report.n_compile,
            n_calibrate=report.n_calibrate,
            n_resolved=report.n_resolved,
            hit_rate=report.hit_rate,
            recommendation=report.recommendation,
            warnings=report.warnings,
            notes=report.notes,
            summary=report.summary(),
            jsonl=report.to_jsonl(),
            few_shot_active=few_shot.n_used if few_shot.active else 0,
        )

    # ------------------------------------------------------------- journal
    @app.post("/api/journal", response_model=s.JournalResponse)
    def journal(req: s.JournalRequest) -> s.JournalResponse:
        """Resolve matured predictions and score the user's calibration.

        Stateless like everything else: the browser holds the journal and
        sends it, the server resolves it against market data and returns the
        verdict.  Nothing is stored here.
        """
        from ..journal.calibration import apply_calibration, fit_calibration
        from ..journal.records import Prediction, resolve_all

        symbols = sorted({p.ticker.upper() for p in req.predictions})
        try:
            prices, _ = _load_market(
                req.demo, req.credentials, symbols, _market_proxy(),
                req.lookback_days,
            )
        except (AlpacaError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        seeded = False
        incoming = list(req.predictions)
        if req.demo and req.seed_demo_history and not incoming:
            incoming = _demo_journal(prices)
            seeded = True

        preds: list[Prediction] = []
        by_id: dict[int, s.PredictionIn] = {}
        for raw in incoming:
            try:
                p = Prediction(
                    ticker=raw.ticker,
                    entry_price=raw.entry_price,
                    target_price=raw.target_price,
                    confidence=raw.confidence,
                    horizon_days=raw.horizon_days,
                    direction=raw.direction,
                    thesis=raw.thesis,
                    created_at=raw.created_at,
                    id=raw.id,
                    asset_class=asset_class(),
                )
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc))
            preds.append(p)
            by_id[id(p)] = raw

        resolved, still_open = resolve_all(preds, prices)

        last = prices.ffill().iloc[-1] if not prices.empty else None
        open_out: list[s.OpenPredictionOut] = []
        for p in still_open:
            now_price = None
            if last is not None and p.ticker in last.index and pd.notna(last[p.ticker]):
                now_price = float(last[p.ticker])
            progress = None
            if now_price is not None and p.target_price != p.entry_price:
                progress = (now_price - p.entry_price) / (
                    p.target_price - p.entry_price
                )
            open_out.append(
                s.OpenPredictionOut(
                    prediction=by_id[id(p)],
                    days_remaining=max(
                        0.0,
                        (p.resolves_at - pd.Timestamp.now("UTC").to_pydatetime())
                        .total_seconds()
                        / 86400.0,
                    ),
                    current_price=now_price,
                    progress=progress,
                )
            )

        report = fit_calibration(
            [r.confidence for r in resolved],
            [float(r.target_hit) for r in resolved],
            [float(r.direction_hit) for r in resolved],
        )
        examples = [
            {"stated": lvl, "used": round(apply_calibration(lvl, report), 4)}
            for lvl in (0.3, 0.5, 0.7, 0.9)
        ]

        def _f(x: float) -> float | None:
            return None if x is None or x != x else float(x)

        return s.JournalResponse(
            resolved=[
                s.ResolutionOut(
                    prediction=by_id[id(r.prediction)],
                    final_price=r.final_price,
                    target_hit=r.target_hit,
                    direction_hit=r.direction_hit,
                    touched=r.touched,
                    realized_return=r.realized_return,
                    resolved_at=r.resolved_at.date().isoformat(),
                    brier=r.brier,
                )
                for r in resolved
            ],
            open=open_out,
            calibration=s.CalibrationOut(
                n=report.n,
                brier=_f(report.brier),
                base_rate=_f(report.base_rate),
                mean_confidence=_f(report.mean_confidence),
                intercept=report.intercept,
                slope=report.slope,
                reliability=_f(report.reliability),
                resolution=_f(report.resolution),
                uncertainty=_f(report.uncertainty),
                skill_vs_base_rate=_f(report.skill_vs_base_rate),
                bins=[s.ReliabilityBin(**b) for b in report.bins],
                actionable=report.actionable,
                direction_hit_rate=_f(report.direction_hit_rate),
                summary=report.summary,
                examples=examples,
            ),
            seeded=seeded,
        )

    # --------------------------------------------------- conviction compiler
    @app.post("/api/compile-view", response_model=s.CompileResponse)
    def compile_view(req: s.CompileRequest) -> s.CompileResponse:
        """Turn a plain-English thesis into structured, editable views.

        The result is a *proposal*: the UI renders every field as an input and
        the user confirms or rewrites it before /api/optimize sees anything.
        Nothing here can move a portfolio on its own.
        """
        from ..llm.compiler import ConvictionCompiler, sanity_check

        universe: list[str] = []
        prices_map: dict[str, float] = {}
        if req.with_prices:
            # A bare ticker ("NVDA", "SOL/USD") is a price lookup for a thesis.
            # Fetch it even if it isn't held, so a view on a stock you don't
            # own yet gets a reference price and counts as tradeable.
            # (Synthetic sample data has a fixed universe, so not in demo.)
            import re

            bare = req.text.strip().upper()
            extra = (
                [bare]
                if not req.demo and re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}(/[A-Z]{3,4})?", bare)
                else []
            )
            try:
                prices, _ = _load_market(
                    req.demo, req.credentials, extra, _market_proxy(),
                    max(req.lookback_days, 10),
                )
                # Symbols the data source returned nothing for aren't tradeable.
                prices = prices.dropna(axis=1, how="all")
                universe = [str(c) for c in prices.columns]
                last = prices.ffill().iloc[-1]
                prices_map = {
                    str(sym): float(val)
                    for sym, val in last.items()
                    if pd.notna(val) and val > 0
                }
            except (HTTPException, AlpacaError, ValueError):
                # Compiling must work even with no market connection — the
                # user can type the entry price themselves.
                universe, prices_map = [], {}

        # Personalize from the user's own resolved predictions. This is
        # in-context learning, not fine-tuning: it works from a handful of
        # examples, which is the scale a retail journal actually reaches.
        personalization = ""
        n_personalized = 0
        if req.predictions:
            try:
                from ..journal.calibration import fit_calibration
                from ..llm.personalize import build_personalization

                resolved = _resolve_journal(req.predictions, prices)
                report = fit_calibration(
                    [r.confidence for r in resolved],
                    [float(r.target_hit) for r in resolved],
                )
                personal = build_personalization(resolved, report)
                personalization = personal.as_prompt_block()
                n_personalized = personal.n_used
            except (ValueError, KeyError, NameError):
                personalization, n_personalized = "", 0

        compiler = ConvictionCompiler(prefer_llm=not req.offline)
        result = compiler.compile(
            req.text,
            universe or None,
            asset_class=asset_class(),
            prices=prices_map or None,
            personalization=personalization,
        )

        out: list[s.CompiledViewOut] = []
        for v in result.views:
            implied = v.implied_return()
            annual = None
            if implied is not None and v.horizon_days:
                years = max(v.horizon_days / 365.0, 1e-6)
                annual = float((1.0 + implied) ** (1.0 / years) - 1.0)
            out.append(
                s.CompiledViewOut(
                    ticker=v.ticker,
                    direction=v.direction,
                    entry_price=v.entry_price,
                    target_price=v.target_price,
                    horizon_days=v.horizon_days,
                    confidence_pct=v.confidence_pct,
                    thesis=v.thesis,
                    catalysts=v.catalysts,
                    risks=v.risks,
                    needs_review=v.needs_review,
                    live_price=prices_map.get(v.ticker.upper()),
                    tradeable=(
                        not universe or v.ticker.upper() in
                        {u.upper() for u in universe}
                    ),
                    implied_annual_return=annual,
                    warnings=sanity_check(v),
                )
            )
        return s.CompileResponse(
            engine=result.engine,
            personalized_from=n_personalized,
            views=out,
            notes=result.notes,
            universe=universe,
        )

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
        # The same curves, with the investor allowed to be a person.
        behavior = None
        try:
            from ..backtest.behavior import (
                behavior_gap,
                matching_advantage,
                panic_threshold,
            )

            dates = pd.to_datetime(result.strategies[0].dates)
            curves = {
                st.name: pd.Series(st.equity_curve, index=dates)
                for st in result.strategies
            }
            sims = behavior_gap(
                curves, gamma=req.gamma, periods_per_year=_periods_per_year()
            )
            adv = matching_advantage(sims)
            labels = {st.name: st.label for st in result.strategies}
            threshold = panic_threshold(req.gamma)
            worst = max(sims.values(), key=lambda b: b.behavior_gap)
            summary = (
                f"At your risk tier you're modelled as selling out after a "
                f"{threshold:.0%} drawdown, and buying back once the market has "
                f"recovered 10% off its low. That costs the worst of these "
                f"strategies {worst.behavior_gap:.1%} a year"
                + (
                    " — and it changes which one wins."
                    if adv.get("ranking_changed")
                    else ", without changing which one wins."
                )
            )
            behavior = s.BehaviorOut(
                panic_threshold=threshold,
                rows=[
                    s.BehaviorRow(
                        name=name,
                        label=labels.get(name, name),
                        paper_cagr=b.paper_metrics.get("cagr", 0.0),
                        realized_cagr=b.realized_metrics.get("cagr", 0.0),
                        behavior_gap=b.behavior_gap,
                        max_drawdown=b.paper_metrics.get("max_drawdown", 0.0),
                        panics=len(b.panics),
                        time_in_cash=b.time_in_cash,
                        cost_drag=b.cost_drag,
                    )
                    for name, b in sims.items()
                ],
                best_on_paper=labels.get(
                    adv.get("best_on_paper", ""), adv.get("best_on_paper", "")
                ),
                best_as_held=labels.get(
                    adv.get("best_as_held", ""), adv.get("best_as_held", "")
                ),
                ranking_changed=bool(adv.get("ranking_changed")),
                summary=summary,
            )
        except (ValueError, KeyError, IndexError):
            behavior = None

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
            behavior=behavior,
        )

    # --------------------------------------------------- prediction markets
    @app.get("/api/predict/markets", response_model=s.PredictionCatalogResponse)
    def predict_markets(live: bool | None = None) -> s.PredictionCatalogResponse:
        """Curated Kalshi markets, grouped by the income they can hedge.

        Returns at once: the bundled snapshot until a background refresh
        has pulled live prices, then the live data (cached ten minutes).
        ``source`` says which one you got.
        """
        from ..prediction.kalshi_client import curated_catalog

        return s.PredictionCatalogResponse(**curated_catalog(live=live))

    @app.post("/api/predict/hedge", response_model=s.ContractHedgeResponse)
    def predict_hedge(req: s.ContractHedgeRequest) -> s.ContractHedgeResponse:
        """Size an event contract against income risk at the user's gamma.

        The optimizer maximizes expected CRRA utility of end-of-season
        wealth — the same objective as the stocks product, with a binary
        payoff in place of stock returns — and reports the position, its
        decomposition into pure hedge and speculative tilt, the dollar
        value of hedging (certainty-equivalent gain) and the most the user
        should pay per contract.  See hone/prediction/hedge.py.
        """
        from ..prediction.hedge import IncomeExposure, hedge_income
        from ..prediction.liquidity import liquidity_for_market

        confidence = req.confidence
        if (
            req.calibration is not None
            and req.calibration.actionable
            and req.own_prob is not None
        ):
            # The journal has scored enough of this user's predictions to
            # know what their stated confidence is worth; apply the same
            # map the views page uses before blending the belief.
            from ..journal.calibration import CalibrationReport, apply_calibration

            report = CalibrationReport(
                n=req.calibration.n, brier=float("nan"), base_rate=float("nan"),
                mean_confidence=float("nan"), intercept=req.calibration.intercept,
                slope=req.calibration.slope, reliability=float("nan"),
                resolution=float("nan"), uncertainty=float("nan"),
                skill_vs_base_rate=float("nan"), actionable=True,
            )
            confidence = float(apply_calibration(confidence, report))

        exp = IncomeExposure(
            wealth=req.wealth,
            loss=req.loss,
            price=req.price,
            gamma=req.gamma,
            market_prob=req.market_prob,
            own_prob=req.own_prob,
            confidence=confidence,
            basis_correlation=req.basis_correlation,
            fee_multiplier=req.fee_multiplier if req.include_fees else 0.0,
            loss_prob=req.loss_prob,
            **({} if req.safety_margins else {"basis_shrink": 1.0, "price_buffer": 0.0}),
            # What the market can actually supply, looked up server-side
            # from the ticker (catalog open interest + live order book).
            liquidity=(
                liquidity_for_market(req.market_ticker, req.side)
                if req.check_liquidity and req.market_ticker else None
            ),
        )
        try:
            plan = hedge_income(exp)
        except (ValueError, ArithmeticError) as exc:
            # ArithmeticError: belt and braces — numerical failures must be a
            # clear 422, never an HTTP 500 (property-test bug B8).
            raise HTTPException(status_code=422, detail=str(exc))
        payload = plan.to_dict()
        return s.ContractHedgeResponse(
            tier=_tier_info(req.gamma),
            confidence_used=confidence,
            confidence_stated=req.confidence,
            market_ticker=req.market_ticker,
            side=req.side,
            open_interest=exp.liquidity.open_interest if exp.liquidity else None,
            **payload,
        )

    # ---------------------------------------------------------- quotes
    @app.get("/api/predict/businesses")
    def predict_businesses() -> list[dict]:
        """Business types the quote engine knows, with their default assumptions."""
        from ..prediction.perils import PERILS
        from ..prediction.quote import BUSINESSES

        return [
            {"key": b.key, "label": b.label, "elasticity_scale": b.elasticity_scale, "basis": b.basis,
             "pass_share": b.pass_share, "peril": b.peril, "peril_label": PERILS[b.peril].label,
             "high_is_bad": PERILS[b.peril].high_is_bad, "season": PERILS[b.peril].season_label,
             "margin": b.margin, "reserves_frac": b.reserves_frac}
            for b in BUSINESSES.values()
        ]

    @app.get("/api/predict/places", response_model=list[s.PlaceOut])
    def predict_places(q: str) -> list[s.PlaceOut]:
        """Places matching a name, so the user can confirm which one they mean."""
        from ..prediction.climate import ClimateError, geocode

        try:
            found = geocode(q, count=6)
        except ClimateError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        return [s.PlaceOut(label=p.label, latitude=p.latitude, longitude=p.longitude,
                           elevation=p.elevation) for p in found]

    @app.post("/api/predict/quote")
    def predict_quote(req: s.QuoteRequest) -> dict:
        """Price and size protection from a minimal description of a business."""
        from ..prediction.climate import ClimateError, Place
        from ..prediction.quote import DEFAULT_LOADING, DEFAULT_TRIGGER_FRACTION, quote

        if req.latitude is not None and req.longitude is not None:
            place = Place(req.place_label or req.place or "Selected place", "", "",
                          req.latitude, req.longitude)
        elif req.place:
            place = req.place
        else:
            raise HTTPException(status_code=422, detail="Tell us where the business is.")
        try:
            q = quote(
                req.business, place, req.revenue, reserves=req.reserves, gamma=req.gamma,
                margin=req.margin,
                trigger_fraction=req.trigger_fraction or DEFAULT_TRIGGER_FRACTION,
                loading=DEFAULT_LOADING if req.loading is None else req.loading,
                index=req.index,
                pass_share=req.pass_share,
            )
        except ClimateError as exc:
            raise HTTPException(status_code=503, detail=f"Weather history unavailable right now: {exc}")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        out = q.to_dict()
        out["tier"] = _tier_info(q.gamma).model_dump()
        return out

    # --------------------------------------------------- SPA page routes
    # Registered last so no /api route can ever be shadowed by it. Deep
    # links such as /crypto/app/theses or /stocks/methodology/calibration
    # load the app; anything else under an unknown prefix is a 404.
    _SPA_PRODUCTS = {"stocks", "crypto", "prediction-markets"}

    @app.get("/{product}/{rest:path}", include_in_schema=False)
    def spa_page(product: str, rest: str) -> FileResponse:
        if product not in _SPA_PRODUCTS:
            raise HTTPException(status_code=404, detail="not found")
        return spa_index()

    return app


app = create_app()
