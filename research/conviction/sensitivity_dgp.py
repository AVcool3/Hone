"""Robustness check: does the answer change when risk *is* compensated?

`synthetic_universe` draws each asset's drift independently of its
volatility, so the CAPM-style equilibrium prior that Hone reverse-optimizes
(Pi = delta * Sigma * w, i.e. "more covariance with the market -> more
expected return") is misspecified by construction.  That is not a fair test
of `risk_only`.  This script rebuilds the same experiment on a panel where
every asset prices at the same Sharpe ratio, which is the world the prior
believes in, and re-runs the key cells.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from hone.backtest import conviction as cv

TRADING_DAYS = 252
N_DAYS = 1260
SYMBOLS = ["AAPL", "MSFT", "SPY", "TSLA", "JNJ", "NVDA"]
TARGET_SHARPE = 0.40
RISK_FREE = 0.04


def compensated_universe(seed: int) -> tuple[pd.DataFrame, pd.Series]:
    """Same shape as `synthetic_universe`, but mu = rf + S * vol."""
    rng = np.random.default_rng(seed)
    n = len(SYMBOLS)
    annual_vol = rng.uniform(0.15, 0.45, n)
    annual_mu = RISK_FREE + TARGET_SHARPE * annual_vol
    corr = np.full((n, n), 0.45)
    np.fill_diagonal(corr, 1.0)
    cov = corr * np.outer(annual_vol, annual_vol) / TRADING_DAYS
    rets = rng.multivariate_normal(annual_mu / TRADING_DAYS, cov, size=N_DAYS)
    rets = rets - rets.mean(axis=0, keepdims=True) + annual_mu / TRADING_DAYS
    prices = pd.DataFrame(
        100.0 * np.exp(np.cumsum(rets, axis=0)),
        columns=SYMBOLS,
        index=pd.bdate_range(end=pd.Timestamp("2025-01-01"), periods=N_DAYS),
    )
    return prices, pd.Series(np.full(n, 1.0 / n), index=SYMBOLS)


ASSET = cv.AssetClass(
    name="equities_compensated",
    market="SPY",
    periods_per_year=TRADING_DAYS,
    lookback=TRADING_DAYS,
    n_days=N_DAYS,
    factory=compensated_universe,
)

GAMMAS = [1.2, 2.5, 8.0]
SKILLS = [0.0, 0.2, 0.4]


def one(i: int) -> pd.DataFrame:
    p = cv.run_panel(
        ASSET, GAMMAS, SKILLS, [1.0], n_investors=1, base_seed=1_000 + i
    )
    p["investor"] = i
    return p


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as pool:
        panel = pd.concat(pool.map(one, range(24)), ignore_index=True)
    summ = cv.summarize(panel)
    pooled = (
        panel.groupby(["skill", "strategy"])
        .agg(sharpe=("sharpe", "median"), cagr=("cagr", "median"),
             vol=("volatility", "median"), eff_n=("effective_n", "median"))
        .reset_index()
        .merge(
            summ.groupby(["skill", "strategy"])[["beat_risk_only", "beat_market_hold"]]
            .mean().reset_index(),
            on=["skill", "strategy"],
        )
    )
    order = list(cv.STRATEGIES)
    pooled["strategy"] = pd.Categorical(pooled["strategy"], order, ordered=True)
    print(pooled.sort_values(["skill", "strategy"]).to_string(index=False))
