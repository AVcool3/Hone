"""SnapTrade: one integration, every brokerage SnapTrade supports.

SnapTrade (https://snaptrade.com) is a brokerage aggregator. Instead of
writing a client per broker (Schwab, Fidelity, Robinhood, IBKR, Webull,
Coinbase, ...), Hone talks to SnapTrade, and SnapTrade talks to the brokers.
The user picks their broker and signs in on SnapTrade's own page — Hone never
sees a brokerage password.

How the pieces fit
------------------
* **Hone's SnapTrade keys** (``SNAPTRADE_CLIENT_ID`` / ``SNAPTRADE_CONSUMER_KEY``)
  live only in the server's environment. Every request is signed with the
  consumer key, so these never reach the browser.
* **A SnapTrade "user"** is created per Hone user (``register_user``). SnapTrade
  returns a ``userSecret`` for it. Together, ``userId`` + ``userSecret`` say
  *whose* accounts a request is about. Hone keeps them with the user (browser,
  and the user's own Supabase row when signed in), and they travel with each
  request — the server stays stateless.
* **Connections** are the brokerages a user has linked through SnapTrade's
  Connection Portal (``login_link`` returns its URL). One user can link many
  brokers, each with one or more **accounts**.

Hone only *reads* holdings. Connections are requested read-only, and nothing
here can place an order.

Request signing
---------------
SnapTrade authenticates each call with three things: ``clientId`` and
``timestamp`` in the query string, and a ``Signature`` header — an
HMAC-SHA256 (keyed by the consumer key) over a canonical JSON of the request
body, path and query string. ``_signature`` mirrors the official SDK's
``compute_request_signature`` exactly; if the two ever disagree, SnapTrade
answers 401.

Like :mod:`hone.market_data.alpaca_client`, the ``session`` argument accepts
anything with a ``requests.Session``-compatible ``request`` method, which is
how the tests run without a network.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import quote, urlencode

import requests

#: SnapTrade's API root. The old ``/api/v1`` prefix is deprecated; paths are
#: now relative to the root (``/accounts``, ``/snapTrade/login``, ...).
SNAPTRADE_URL = "https://api.snaptrade.com"

#: How long fetched holdings are reused before asking SnapTrade again.
#: Hone recalculates often (every edit can trigger one), and SnapTrade limits
#: some accounts to ~10 requests a minute — brokerages don't update positions
#: second by second anyway. Change this to trade freshness for API calls.
HOLDINGS_CACHE_SECONDS = 60.0

#: Instrument kinds (SnapTrade's ``instrument.kind``) that the Stocks product
#: can model: things with a single daily price series, like an ordinary share.
STOCK_KINDS = {"stock", "etf", "adr", "cef", "equity"}

#: Coins that are dollars in disguise. The crypto product treats these as its
#: cash leg rather than as a risky asset, so they're reported, not modelled.
STABLECOINS = {"USDC", "USDT", "DAI", "PYUSD", "TUSD", "USDP", "FDUSD", "BUSD"}


class SnapTradeError(RuntimeError):
    """A SnapTrade request failed. ``status`` is the HTTP status (0 = network)."""

    def __init__(self, message: str, status: int = 0, code: str | None = None):
        super().__init__(message)
        self.status = status
        self.code = code


#: Environment variable names Hone accepts for each key, first match wins.
#: The second names match how the keys are saved in this project's cloud
#: environment settings; add others here if you name them differently.
CLIENT_ID_VARS = ("SNAPTRADE_CLIENT_ID", "SnapTrade_ClientID")
CONSUMER_KEY_VARS = ("SNAPTRADE_CONSUMER_KEY", "SnapTrade_API")


def _env(names: tuple[str, ...]) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def configured() -> bool:
    """True when this server has SnapTrade keys, i.e. brokerage linking is on."""
    return bool(_env(CLIENT_ID_VARS) and _env(CONSUMER_KEY_VARS))


def _signature(consumer_key: str, path: str, query: str, body: Any) -> str:
    """The ``Signature`` header SnapTrade expects (see module docstring).

    ``content`` is ``None`` for requests without a body; keys are sorted and
    separators compact so both sides serialize identically.
    """
    sig_object = {
        "content": None if body in (None, {}) else body,
        "path": path,
        "query": query,
    }
    sig_content = json.dumps(sig_object, separators=(",", ":"), sort_keys=True)
    digest = hmac.new(consumer_key.encode(), sig_content.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


class SnapTradeClient:
    """Minimal signed REST client for the parts of SnapTrade Hone uses."""

    def __init__(
        self,
        client_id: str | None = None,
        consumer_key: str | None = None,
        base_url: str = SNAPTRADE_URL,
        session: Any | None = None,
    ) -> None:
        self.client_id = client_id or _env(CLIENT_ID_VARS)
        self.consumer_key = consumer_key or _env(CONSUMER_KEY_VARS)
        if not self.client_id or not self.consumer_key:
            raise SnapTradeError(
                "Brokerage linking isn't configured on this server: set "
                "SNAPTRADE_CLIENT_ID and SNAPTRADE_CONSUMER_KEY.",
                status=503,
            )
        self.base_url = base_url.rstrip("/")
        self._session = session or requests.Session()

    # ------------------------------------------------------------------ http
    def _request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> Any:
        # The query string is built here, once, and the exact same string is
        # both signed and sent — any difference (ordering, encoding) would
        # make SnapTrade reject the signature.
        query_params = {"clientId": self.client_id, "timestamp": str(int(time.time()))}
        query_params.update({k: v for k, v in (params or {}).items() if v is not None})
        query = urlencode(query_params)
        headers = {
            "Signature": _signature(self.consumer_key, path, query, body),
            "Accept": "application/json",
        }
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            # Same compact form that was signed.
            data = json.dumps(body, separators=(",", ":"))
        try:
            resp = self._session.request(
                method, f"{self.base_url}{path}?{query}", headers=headers, data=data, timeout=30
            )
        except requests.RequestException as exc:
            raise SnapTradeError(f"Could not reach SnapTrade: {exc}") from exc
        if resp.status_code >= 400:
            # SnapTrade errors look like {"detail": "...", "code": "1012", ...}.
            detail, code = resp.text, None
            try:
                err = resp.json()
                detail = err.get("detail") or err.get("message") or detail
                code = str(err.get("code")) if err.get("code") is not None else None
            except ValueError:
                pass
            raise SnapTradeError(
                f"SnapTrade error {resp.status_code} for {method} {path}: {detail}",
                status=resp.status_code,
                code=code,
            )
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    @staticmethod
    def _user(user_id: str, user_secret: str) -> dict[str, str]:
        return {"userId": user_id, "userSecret": user_secret}

    # ----------------------------------------------------------------- users
    def register_user(self, user_id: str) -> str:
        """Create a SnapTrade user; returns its ``userSecret`` (store it!)."""
        out = self._request("POST", "/snapTrade/registerUser", body={"userId": user_id})
        secret = (out or {}).get("userSecret")
        if not secret:
            raise SnapTradeError("SnapTrade did not return a user secret.", status=502)
        return secret

    def delete_user(self, user_id: str) -> None:
        """Delete a SnapTrade user and every connection it has (stops billing)."""
        self._request("DELETE", "/snapTrade/deleteUser", params={"userId": user_id})

    def login_link(
        self,
        user_id: str,
        user_secret: str,
        *,
        redirect_url: str | None = None,
        broker: str | None = None,
        reconnect: str | None = None,
    ) -> str:
        """URL of SnapTrade's Connection Portal, where the user links a broker.

        ``connectionType: read`` asks for data access only — Hone never trades.
        ``redirect_url`` is where SnapTrade sends the user back afterwards.
        ``broker`` (a SnapTrade slug like ``SCHWAB``) skips the broker picker;
        ``reconnect`` (a connection id) repairs a connection that stopped syncing.
        """
        body: dict[str, Any] = {"connectionType": "read"}
        if redirect_url:
            body["customRedirect"] = redirect_url
        if broker:
            body["broker"] = broker
        if reconnect:
            body["reconnect"] = reconnect
        out = self._request(
            "POST", "/snapTrade/login", params=self._user(user_id, user_secret), body=body
        )
        url = (out or {}).get("redirectURI")
        if not url:
            raise SnapTradeError("SnapTrade did not return a connection link.", status=502)
        return url

    # ----------------------------------------------------------- connections
    def list_connections(self, user_id: str, user_secret: str) -> list[dict]:
        """Linked brokerages ("brokerage authorizations")."""
        return self._request(
            "GET", "/authorizations", params=self._user(user_id, user_secret)
        ) or []

    def remove_connection(self, user_id: str, user_secret: str, connection_id: str) -> None:
        """Unlink one brokerage (and all of its accounts)."""
        self._request(
            "DELETE",
            f"/authorizations/{quote(connection_id, safe='')}",
            params=self._user(user_id, user_secret),
        )

    # -------------------------------------------------------------- accounts
    def list_accounts(self, user_id: str, user_secret: str) -> list[dict]:
        return self._request("GET", "/accounts", params=self._user(user_id, user_secret)) or []

    def account_positions(self, user_id: str, user_secret: str, account_id: str) -> list[dict]:
        """Every position in one account (stocks, ETFs, crypto, funds, options...)."""
        out = self._request(
            "GET",
            f"/accounts/{quote(account_id, safe='')}/positions/all",
            params=self._user(user_id, user_secret),
        )
        # Response is {"results": [...], "data_freshness": {...}}.
        if isinstance(out, dict):
            return out.get("results") or []
        return out or []


# ---------------------------------------------------------------- holdings
@dataclass
class Holding:
    """One modelled position, already merged across accounts."""

    symbol: str            # in the form Hone's price source uses (AAPL, BTC/USD)
    market_value: float    # USD; negative for a short
    qty: float
    accounts: list[str] = field(default_factory=list)  # "Schwab · Brokerage ••1234"


@dataclass
class Skipped:
    """A position Hone saw but can't model, and why — shown to the user."""

    symbol: str
    reason: str
    market_value: float | None = None
    account: str | None = None


@dataclass
class BrokerHoldings:
    holdings: list[Holding]
    skipped: list[Skipped]
    accounts: list[dict]  # the raw SnapTrade account objects included

    @property
    def total_value(self) -> float:
        return sum(abs(h.market_value) for h in self.holdings)


def _num(x: Any) -> float | None:
    """SnapTrade sends units and prices as strings; tolerate numbers and nulls."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def account_label(account: Mapping[str, Any]) -> str:
    """'Fidelity · Roth IRA ••6789' — never the full account number."""
    inst = account.get("institution_name") or "Brokerage"
    name = account.get("name") or "Account"
    number = str(account.get("number") or "")
    tail = f" ••{number[-4:]}" if len(number) >= 4 else ""
    # SnapTrade sometimes already appends the institution to the name.
    label = name if inst.lower() in name.lower() else f"{inst} · {name}"
    return f"{label}{tail}"


def _hone_symbol(instrument: Mapping[str, Any], crypto: bool) -> str | None:
    """Translate a SnapTrade instrument to the ticker Hone's prices use."""
    raw = str(instrument.get("raw_symbol") or instrument.get("symbol") or "").upper().strip()
    if not raw:
        return None
    if crypto:
        # SnapTrade: "BTC" (or "BTC-USD"); Alpaca crypto data: "BTC/USD".
        base = raw.replace("-", "/").split("/")[0]
        return f"{base}/USD"
    # US share classes: brokers write BRK-B / BRK/B; Alpaca writes BRK.B.
    return raw.replace("-", ".").replace("/", ".")


def combine_positions(
    accounts: list[Mapping[str, Any]],
    positions_by_account: Mapping[str, list[Mapping[str, Any]]],
    *,
    crypto: bool = False,
) -> BrokerHoldings:
    """Merge positions from every account into one portfolio.

    The same ticker held at two brokers becomes one holding (values added).
    Anything the current product can't model is kept in ``skipped`` with a
    reason, so the user can see what was left out rather than wonder.

    Valuation is ``units × price`` from the brokerage. Only US-dollar
    positions are included: mixing currencies without converting would
    silently mis-weight the portfolio.
    """
    merged: dict[str, Holding] = {}
    skipped: list[Skipped] = []
    included_accounts = []

    for account in accounts:
        acct_id = account.get("id")
        label = account_label(account)
        # Skip bank (deposit) accounts, lines of credit, annuities.
        category = account.get("account_category")
        if category and category != "INVESTMENT":
            continue
        if (account.get("status") or "open") in ("closed", "archived"):
            continue
        included_accounts.append(account)

        for pos in positions_by_account.get(acct_id, []):
            inst = pos.get("instrument") or {}
            kind = str(inst.get("kind") or "").lower()
            raw = str(inst.get("symbol") or inst.get("raw_symbol") or "?")
            units = _num(pos.get("units"))
            price = _num(pos.get("price"))
            value = units * price if units is not None and price is not None else None
            if units is not None and price is not None and kind == "option":
                value = units * price * 100  # option prices are per share
            currency = str(pos.get("currency") or inst.get("currency") or "USD").upper()

            def skip(reason: str) -> None:
                skipped.append(Skipped(raw, reason, value, label))

            # Decide whether this product can model it. Order matters: the
            # most specific reason wins so the message is actually useful.
            if kind == "cash" or pos.get("cash_equivalent"):
                skip("Cash or cash equivalent — counted as cash, not modelled")
                continue
            if crypto:
                if kind != "crypto":
                    skip("Not a crypto asset — open the Stocks product to model it")
                    continue
                base = (inst.get("raw_symbol") or raw).upper().split("-")[0].split("/")[0]
                if base in STABLECOINS:
                    skip("Stablecoin — treated as cash")
                    continue
            else:
                if kind == "crypto":
                    skip("Crypto — open the Crypto product to model it")
                    continue
                if kind == "option":
                    skip("Options aren't modelled yet")
                    continue
                if kind == "mutualfund":
                    skip("Mutual funds have no daily price feed in Hone yet")
                    continue
                if kind and kind not in STOCK_KINDS:
                    skip(f"{kind.replace('_', ' ').capitalize()} positions aren't modelled")
                    continue
            if currency != "USD":
                skip(f"Priced in {currency} — Hone works in US dollars")
                continue
            if value is None or units == 0:
                skip("The brokerage didn't report a price or quantity")
                continue
            symbol = _hone_symbol(inst, crypto)
            if not symbol:
                skip("No ticker reported")
                continue

            h = merged.setdefault(symbol, Holding(symbol=symbol, market_value=0.0, qty=0.0))
            h.market_value += value
            h.qty += units
            if label not in h.accounts:
                h.accounts.append(label)

    holdings = sorted(
        (h for h in merged.values() if abs(h.market_value) > 0.005),
        key=lambda h: -abs(h.market_value),
    )
    return BrokerHoldings(holdings=holdings, skipped=skipped, accounts=included_accounts)


# ------------------------------------------------------------------- cache
_cache: dict[tuple, tuple[float, tuple[list, dict]]] = {}
_cache_lock = threading.Lock()


def _cache_key(client: SnapTradeClient, user_id: str, user_secret: str) -> tuple:
    # The secret is hashed so it isn't sitting in memory as a dict key, and so
    # a wrong secret can never be served another request's cached data.
    return (
        client.client_id,
        user_id,
        hashlib.sha256(user_secret.encode()).hexdigest(),
    )


def fetch_raw(
    client: SnapTradeClient, user_id: str, user_secret: str, *, fresh: bool = False
) -> tuple[list[dict], dict[str, list[dict]]]:
    """(accounts, positions per account id), cached for HOLDINGS_CACHE_SECONDS."""
    key = _cache_key(client, user_id, user_secret)
    now = time.monotonic()
    if not fresh:
        with _cache_lock:
            hit = _cache.get(key)
        if hit and now - hit[0] < HOLDINGS_CACHE_SECONDS:
            return hit[1]
    accounts = client.list_accounts(user_id, user_secret)
    positions = {
        a["id"]: client.account_positions(user_id, user_secret, a["id"])
        for a in accounts
        if a.get("id")
    }
    with _cache_lock:
        _cache[key] = (now, (accounts, positions))
        # Keep the cache from growing without bound on a busy server.
        if len(_cache) > 2000:
            for k, (t, _) in list(_cache.items()):
                if now - t >= HOLDINGS_CACHE_SECONDS:
                    del _cache[k]
    return accounts, positions


def forget(user_id: str) -> None:
    """Drop cached holdings for a user (after they link or unlink a broker)."""
    with _cache_lock:
        for k in [k for k in _cache if k[1] == user_id]:
            del _cache[k]


def fetch_holdings(
    client: SnapTradeClient,
    user_id: str,
    user_secret: str,
    *,
    crypto: bool = False,
    account_ids: list[str] | None = None,
    fresh: bool = False,
) -> BrokerHoldings:
    """Holdings across every linked account (or just ``account_ids``)."""
    accounts, positions = fetch_raw(client, user_id, user_secret, fresh=fresh)
    if account_ids:
        wanted = set(account_ids)
        accounts = [a for a in accounts if a.get("id") in wanted]
    return combine_positions(accounts, positions, crypto=crypto)
