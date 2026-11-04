"""Thin Alpaca paper-trading REST client.

Uses the plain REST API (no alpaca-py dependency) against the paper
endpoints:

* trading:     https://paper-api.alpaca.markets
* market data: https://data.alpaca.markets

Credentials are read from the environment by default:

* ``ALPACA_API_KEY``    (also accepts ``APCA_API_KEY_ID``)
* ``ALPACA_SECRET_KEY`` (also accepts ``APCA_API_SECRET_KEY``)

The ``session`` argument accepts anything with a ``request`` method
compatible with :class:`requests.Session`, which is how the test suite
injects canned responses without touching the network.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping

import pandas as pd
import requests

PAPER_TRADING_URL = "https://paper-api.alpaca.markets"
MARKET_DATA_URL = "https://data.alpaca.markets"


class AlpacaError(RuntimeError):
    """Raised when the Alpaca API returns an error response."""


@dataclass(frozen=True)
class Position:
    symbol: str
    qty: float
    market_value: float
    avg_entry_price: float
    current_price: float
    unrealized_pl: float
    asset_class: str | None = None

    @classmethod
    def from_api(cls, raw: Mapping[str, Any]) -> "Position":
        return cls(
            symbol=raw["symbol"],
            qty=float(raw["qty"]),
            market_value=float(raw["market_value"]),
            avg_entry_price=float(raw["avg_entry_price"]),
            current_price=float(raw["current_price"]),
            unrealized_pl=float(raw.get("unrealized_pl", 0.0)),
            asset_class=raw.get("asset_class"),
        )


class AlpacaClient:
    """Client for the Alpaca paper-trading and market-data APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        trading_url: str = PAPER_TRADING_URL,
        data_url: str = MARKET_DATA_URL,
        session: Any | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("ALPACA_API_KEY") or os.environ.get(
            "APCA_API_KEY_ID", ""
        )
        self.secret_key = secret_key or os.environ.get(
            "ALPACA_SECRET_KEY"
        ) or os.environ.get("APCA_API_SECRET_KEY", "")
        if not self.api_key or not self.secret_key:
            raise AlpacaError(
                "Alpaca credentials missing: set ALPACA_API_KEY and "
                "ALPACA_SECRET_KEY (paper-trading keys) or pass them "
                "explicitly."
            )
        self.trading_url = trading_url.rstrip("/")
        self.data_url = data_url.rstrip("/")
        self._session = session or requests.Session()

    # ------------------------------------------------------------------ http
    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        base: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        url = f"{base}{path}"
        resp = self._session.request(
            method, url, headers=self._headers(), params=params, json=json, timeout=30
        )
        if resp.status_code >= 400:
            raise AlpacaError(
                f"Alpaca API error {resp.status_code} for {method} {path}: {resp.text}"
            )
        return resp.json()

    # --------------------------------------------------------------- trading
    def get_account(self) -> dict[str, Any]:
        return self._request("GET", self.trading_url, "/v2/account")

    def get_positions(self) -> list[Position]:
        raw = self._request("GET", self.trading_url, "/v2/positions")
        return [Position.from_api(p) for p in raw]

    def portfolio_weights(self) -> pd.Series:
        """Current portfolio weights by market value (long positions
        positive, shorts negative), normalized by gross exposure."""
        positions = self.get_positions()
        if not positions:
            return pd.Series(dtype=float)
        values = pd.Series({p.symbol: p.market_value for p in positions})
        gross = values.abs().sum()
        if gross == 0:
            return values
        return values / gross

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: float | None = None,
    ) -> dict[str, Any]:
        """Submit a paper-trading order (used to execute rebalances and
        short hedges)."""
        payload: dict[str, Any] = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        }
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        return self._request("POST", self.trading_url, "/v2/orders", json=payload)

    # ----------------------------------------------------------- market data
    def get_bars(
        self,
        symbols: Iterable[str],
        start: str | date | datetime,
        end: str | date | datetime | None = None,
        timeframe: str = "1Day",
        feed: str = "iex",
        limit: int = 10_000,
    ) -> pd.DataFrame:
        """Daily (or intraday) close prices, one column per symbol.

        Returns a DataFrame indexed by timestamp with symbols as columns,
        suitable for the covariance calculator.
        """
        symbols = list(symbols)
        params: dict[str, Any] = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "start": _iso(start),
            "limit": limit,
            "feed": feed,
            "adjustment": "split",
        }
        if end is not None:
            params["end"] = _iso(end)

        frames: dict[str, pd.Series] = {}
        page_token: str | None = None
        while True:
            if page_token:
                params["page_token"] = page_token
            data = self._request("GET", self.data_url, "/v2/stocks/bars", params=params)
            for symbol, bars in (data.get("bars") or {}).items():
                closes = pd.Series(
                    {pd.Timestamp(b["t"]): float(b["c"]) for b in bars}, name=symbol
                )
                frames[symbol] = (
                    pd.concat([frames[symbol], closes]) if symbol in frames else closes
                )
            page_token = data.get("next_page_token")
            if not page_token:
                break

        if not frames:
            return pd.DataFrame(columns=symbols)
        prices = pd.DataFrame(frames).sort_index()
        return prices.reindex(columns=symbols)

    def get_latest_prices(self, symbols: Iterable[str], feed: str = "iex") -> pd.Series:
        symbols = list(symbols)
        data = self._request(
            "GET",
            self.data_url,
            "/v2/stocks/trades/latest",
            params={"symbols": ",".join(symbols), "feed": feed},
        )
        trades = data.get("trades") or {}
        return pd.Series(
            {s: float(t["p"]) for s, t in trades.items()}, dtype=float
        ).reindex(symbols)

    # ------------------------------------------------------------ crypto
    def get_crypto_bars(
        self,
        symbols: Iterable[str],
        start: str | date | datetime,
        end: str | date | datetime | None = None,
        timeframe: str = "1Day",
        loc: str = "us",
        limit: int = 10_000,
    ) -> pd.DataFrame:
        """Daily close prices for crypto pairs (e.g. ``BTC/USD``).

        Uses Alpaca's crypto market-data endpoint, which requires no
        market-data subscription. Returns a DataFrame indexed by
        timestamp with one column per symbol, matching the shape
        :func:`~hone.market_data.covariance.portfolio_covariance` expects.
        """
        symbols = list(symbols)
        params: dict[str, Any] = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "start": _iso(start),
            "limit": limit,
        }
        if end is not None:
            params["end"] = _iso(end)

        frames: dict[str, pd.Series] = {}
        page_token: str | None = None
        while True:
            if page_token:
                params["page_token"] = page_token
            data = self._request(
                "GET", self.data_url, f"/v1beta3/crypto/{loc}/bars", params=params
            )
            for symbol, bars in (data.get("bars") or {}).items():
                closes = pd.Series(
                    {pd.Timestamp(b["t"]): float(b["c"]) for b in bars}, name=symbol
                )
                frames[symbol] = (
                    pd.concat([frames[symbol], closes]) if symbol in frames else closes
                )
            page_token = data.get("next_page_token")
            if not page_token:
                break

        if not frames:
            return pd.DataFrame(columns=symbols)
        prices = pd.DataFrame(frames).sort_index()
        prices = prices[~prices.index.duplicated(keep="last")]
        return prices.reindex(columns=symbols)

    def get_crypto_positions(self) -> list[Position]:
        """Crypto positions from the paper account.

        Alpaca reports crypto positions on the same ``/v2/positions``
        endpoint with concatenated symbols (``BTCUSD``); this filters to
        crypto and normalizes symbols to the ``BTC/USD`` data form.
        """
        from ..crypto.universe import normalize_symbol

        out = []
        for p in self.get_positions():
            asset_class = getattr(p, "asset_class", None)
            looks_crypto = (asset_class == "crypto") or p.symbol.upper().endswith(
                ("USD", "USDT", "USDC")
            )
            if looks_crypto:
                out.append(
                    Position(
                        symbol=normalize_symbol(p.symbol),
                        qty=p.qty,
                        market_value=p.market_value,
                        avg_entry_price=p.avg_entry_price,
                        current_price=p.current_price,
                        unrealized_pl=p.unrealized_pl,
                    )
                )
        return out

    # ----------------------------------------------------------- options
    def get_option_chain(
        self,
        underlying: str,
        expiration_gte: str | date | None = None,
        expiration_lte: str | date | None = None,
        feed: str = "indicative",
    ) -> list[dict[str, Any]]:
        """Live option chain snapshot for an underlying.

        Returns one dict per contract with the fields the hedging engine
        needs: ``symbol``, ``type`` ("call"/"put"), ``strike``,
        ``expiration`` (ISO date), ``mid`` (indicative price from the
        latest quote), and ``iv`` (implied volatility, when present).

        Uses Alpaca's options market-data endpoint with pagination. The
        ``indicative`` feed is available without an options-data
        subscription; pass ``feed="opra"`` if the account has OPRA.
        """
        params: dict[str, Any] = {"feed": feed, "limit": 1000}
        if expiration_gte is not None:
            params["expiration_date_gte"] = _iso_date(expiration_gte)
        if expiration_lte is not None:
            params["expiration_date_lte"] = _iso_date(expiration_lte)

        contracts: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            if page_token:
                params["page_token"] = page_token
            data = self._request(
                "GET",
                self.data_url,
                f"/v1beta1/options/snapshots/{underlying}",
                params=params,
            )
            for sym, snap in (data.get("snapshots") or {}).items():
                parsed = _parse_option_symbol(sym)
                if parsed is None:
                    continue
                opt_type, strike, expiry = parsed
                quote = snap.get("latestQuote") or {}
                bid, ask = quote.get("bp"), quote.get("ap")
                mid = None
                if bid and ask:
                    mid = (float(bid) + float(ask)) / 2.0
                elif snap.get("latestTrade"):
                    mid = float(snap["latestTrade"].get("p") or 0) or None
                iv = snap.get("impliedVolatility")
                contracts.append(
                    {
                        "symbol": sym,
                        "type": opt_type,
                        "strike": strike,
                        "expiration": expiry,
                        "mid": mid,
                        "iv": float(iv) if iv is not None else None,
                    }
                )
            page_token = data.get("next_page_token")
            if not page_token:
                break
        return contracts


def _iso(value: str | date | datetime) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return value.isoformat()


def _iso_date(value: str | date) -> str:
    return value if isinstance(value, str) else value.isoformat()


def _parse_option_symbol(sym: str) -> tuple[str, float, str] | None:
    """Parse an OCC option symbol into (type, strike, expiration).

    OCC format: ROOT + YYMMDD + C/P + strike*1000 padded to 8 digits,
    e.g. ``SPY240920P00450000`` -> ("put", 450.0, "2024-09-20").
    """
    import re

    m = re.match(r"^[A-Z]+(\d{6})([CP])(\d{8})$", sym)
    if not m:
        return None
    yymmdd, cp, strike_raw = m.groups()
    expiry = f"20{yymmdd[:2]}-{yymmdd[2:4]}-{yymmdd[4:6]}"
    strike = int(strike_raw) / 1000.0
    return ("call" if cp == "C" else "put", strike, expiry)
