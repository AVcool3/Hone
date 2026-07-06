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

    @classmethod
    def from_api(cls, raw: Mapping[str, Any]) -> "Position":
        return cls(
            symbol=raw["symbol"],
            qty=float(raw["qty"]),
            market_value=float(raw["market_value"]),
            avg_entry_price=float(raw["avg_entry_price"]),
            current_price=float(raw["current_price"]),
            unrealized_pl=float(raw.get("unrealized_pl", 0.0)),
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


def _iso(value: str | date | datetime) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return value.isoformat()
