"""Brokerage connections beyond Alpaca.

Alpaca does two jobs in Hone: it holds a paper account (what you own) and it
supplies market data (price history). Linking a real brokerage only replaces
the first job — prices still come from the market-data source — so a broker
integration only has to answer "what does this user hold?".

:mod:`.snaptrade` answers that for every brokerage SnapTrade supports.
"""

from .snaptrade import (
    BrokerHoldings,
    Holding,
    Skipped,
    SnapTradeClient,
    SnapTradeError,
    combine_positions,
    configured,
    fetch_holdings,
)

__all__ = [
    "BrokerHoldings",
    "Holding",
    "Skipped",
    "SnapTradeClient",
    "SnapTradeError",
    "combine_positions",
    "configured",
    "fetch_holdings",
]
