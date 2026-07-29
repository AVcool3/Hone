"""Crypto universe, calendar, and stress scenarios.

Everything in this module encodes a factual difference between crypto and
equities, not a change of method.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: Crypto markets trade continuously, so a "year" is 365 daily periods
#: rather than the ~252 trading days of an equity calendar. This affects
#: annualization only (volatility, mean returns, Sharpe), not the models.
CRYPTO_PERIODS_PER_YEAR = 365

#: Market proxy used for beta, the short hedge, and equilibrium anchoring.
#: BTC plays the role SPY plays for equities: the dominant risk factor
#: whose moves the rest of the market largely follows.
MARKET_PROXY = "BTC/USD"

#: Dollar-pegged assets. These are the crypto-native "cash" leg: the
#: hedging engine allocates to them to reduce exposure, exactly as an
#: equity investor would move to cash or T-bills.
STABLECOINS = ("USDC/USD", "USDT/USD", "DAI/USD")

#: A liquid default universe available on Alpaca's crypto venue.
DEFAULT_CRYPTO_UNIVERSE = (
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
    "LINK/USD",
    "AVAX/USD",
    "DOT/USD",
)

#: Realized crypto drawdowns, used for the dollar stress table. These are
#: peak-to-trough BTC declines from actual history — far deeper than the
#: equity scenarios, which is the single most important thing a crypto
#: investor should internalize before sizing a position.
CRYPTO_STRESS_SCENARIOS = [
    ("2018 crypto winter (BTC -84%)", -0.84),
    ("2022 Terra/FTX collapse (BTC -77%)", -0.77),
    ("May 2021 deleveraging (BTC -53%)", -0.53),
    ("March 2020 liquidity shock (BTC -50%)", -0.50),
]


def is_stablecoin(symbol: str) -> bool:
    """True for dollar-pegged assets (accepts BTC/USD or BTCUSD forms)."""
    base = symbol.upper().replace("/", "").removesuffix("USD")
    return any(base == s.upper().replace("/", "").removesuffix("USD") for s in STABLECOINS)


def normalize_symbol(symbol: str) -> str:
    """Alpaca crypto market data uses ``BTC/USD``; positions report
    ``BTCUSD``. Normalize to the slash form the data API expects."""
    s = symbol.upper().strip()
    if "/" in s:
        return s
    for quote in ("USDT", "USDC", "USD", "BTC", "ETH"):
        if s.endswith(quote) and len(s) > len(quote):
            return f"{s[:-len(quote)]}/{quote}"
    return s


def synthetic_crypto_universe(
    symbols: list[str] | None = None,
    n_days: int = 730,
    seed: int = 11,
) -> tuple[pd.DataFrame, pd.Series]:
    """Synthetic crypto price history + weights for demo mode.

    Calibrated to crypto's empirical character rather than equities':
    annualized volatilities of roughly 55-110%, high pairwise
    correlation (~0.75, since altcoins mostly trade as levered BTC), and
    a fat-tailed return process (Student-t innovations, 4 degrees of
    freedom) so the demo's drawdowns look like crypto drawdowns.
    """
    symbols = list(symbols or DEFAULT_CRYPTO_UNIVERSE)
    rng = np.random.default_rng(seed)
    n = len(symbols)

    # BTC least volatile, altcoins progressively more so.
    annual_vol = np.linspace(0.55, 1.10, n)
    annual_mu = rng.uniform(-0.10, 0.45, n)
    corr = np.full((n, n), 0.75)
    np.fill_diagonal(corr, 1.0)

    cov_daily = corr * np.outer(annual_vol, annual_vol) / CRYPTO_PERIODS_PER_YEAR
    chol = np.linalg.cholesky(cov_daily)

    # Student-t shocks (df=4) scaled to unit variance -> fat tails.
    df = 4
    z = rng.standard_t(df, size=(n_days, n)) / np.sqrt(df / (df - 2))
    rets = z @ chol.T + annual_mu / CRYPTO_PERIODS_PER_YEAR
    # Pin the sample mean to the intended drift so demo output is stable.
    rets = rets - rets.mean(axis=0, keepdims=True) + annual_mu / CRYPTO_PERIODS_PER_YEAR

    prices = pd.DataFrame(
        1000.0 * np.exp(np.cumsum(rets, axis=0)),
        columns=symbols,
        index=pd.date_range(end=pd.Timestamp.today().normalize(), periods=n_days, freq="D"),
    )
    # A typical retail crypto book: BTC/ETH heavy, a few speculative tails.
    raw = rng.dirichlet(np.linspace(3.0, 0.6, n))
    weights = pd.Series(raw, index=symbols)
    return prices, weights
