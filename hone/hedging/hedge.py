"""Hedge sizing keyed to the elicited risk-aversion parameter.

The risk budget
---------------
For a CRRA investor the Merton rule gives the optimal fraction of
wealth in a risky portfolio:  alpha* = (mu_p - rf) / (gamma * sigma_p^2).
If alpha* >= 1 the investor can tolerate the portfolio as is; if
alpha* < 1 their preferences call for less exposure, and the tolerable
volatility of total wealth is

    sigma_target = alpha* x sigma_p = (mu_p - rf) / (gamma * sigma_p).

Rather than telling the user to sell down to cash, the hedging engine
offers ways to *synthetically* reduce exposure to that target:

* ``short_hedge``     — short an index proxy (e.g. SPY) sized so hedged
  volatility hits sigma_target;
* ``protective_put``  — buy puts on the proxy with a gamma-dependent
  floor (more risk-averse -> tighter floor);
* ``zero_cost_collar``— finance the same put by selling an OTM call.

All costs are indicative Black-Scholes values; live quotes should be
used for execution.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .black_scholes import bs_price, implied_zero_cost_call_strike

DEFAULT_RISK_FREE = 0.04


def portfolio_volatility(weights: pd.Series, sigma: pd.DataFrame) -> float:
    w = weights.reindex(sigma.index).fillna(0.0).to_numpy()
    return float(np.sqrt(max(w @ sigma.to_numpy() @ w, 0.0)))


def gamma_target_volatility(
    gamma: float,
    portfolio_mu: float,
    portfolio_vol: float,
    risk_free: float = DEFAULT_RISK_FREE,
) -> float:
    """Merton risk budget: tolerable wealth volatility for this gamma.

    Returns the current volatility unchanged when preferences already
    tolerate full exposure (alpha* >= 1) or when the premium is not
    positive (no meaningful budget can be computed).
    """
    if portfolio_vol <= 0:
        return 0.0
    premium = portfolio_mu - risk_free
    if gamma <= 0 or premium <= 0:
        return portfolio_vol
    alpha_star = premium / (gamma * portfolio_vol**2)
    return portfolio_vol * min(alpha_star, 1.0)


@dataclass
class HedgeSuggestion:
    kind: str  # "short", "protective_put", "collar"
    instrument: str
    description: str
    hedge_notional_fraction: float  # fraction of portfolio value
    hedged_volatility: float | None = None
    est_annual_cost_fraction: float = 0.0  # indicative cost, fraction of NAV
    details: dict = field(default_factory=dict)

    def describe(self) -> str:
        lines = [f"[{self.kind}] {self.description}"]
        if self.hedged_volatility is not None:
            lines.append(f"    hedged volatility ~ {self.hedged_volatility:.2%}")
        lines.append(
            f"    est. cost ~ {self.est_annual_cost_fraction:.2%} of portfolio/yr"
        )
        return "\n".join(lines)


@dataclass
class HedgePlan:
    gamma: float
    current_volatility: float
    target_volatility: float
    suggestions: list[HedgeSuggestion]
    needs_hedge: bool

    def summary(self) -> str:
        lines = [
            "Hedge Plan",
            "----------",
            f"risk aversion gamma : {self.gamma:.3f}",
            f"current volatility  : {self.current_volatility:.2%}",
            f"target volatility   : {self.target_volatility:.2%}",
        ]
        if not self.needs_hedge:
            lines.append(
                "Portfolio volatility is already within your risk budget — "
                "no hedge required."
            )
            return "\n".join(lines)
        lines.append("")
        for s in self.suggestions:
            lines.append(s.describe())
            lines.append("")
        return "\n".join(lines).rstrip()


def short_hedge(
    portfolio_vol: float,
    target_vol: float,
    hedge_vol: float,
    correlation: float,
    instrument: str = "SPY",
    hedge_expected_return: float = 0.07,
    risk_free: float = DEFAULT_RISK_FREE,
) -> HedgeSuggestion:
    """Size a short position in a hedge instrument to reach target vol.

    With short notional fraction h, hedged variance is
    sigma_p^2 - 2 h c + h^2 sigma_h^2 where c = corr * sigma_p * sigma_h.
    Solve for the smallest h reaching target; if the target is below the
    minimum achievable variance, cap at the minimum-variance hedge
    h* = c / sigma_h^2.
    """
    c = correlation * portfolio_vol * hedge_vol
    if c <= 0:
        raise ValueError(
            "hedge instrument must be positively correlated with the portfolio"
        )
    h_minvar = c / hedge_vol**2
    var_min = max(portfolio_vol**2 - c**2 / hedge_vol**2, 0.0)

    if target_vol**2 <= var_min:
        h = h_minvar
        hedged_vol = math.sqrt(var_min)
        capped = True
    else:
        disc = c**2 - hedge_vol**2 * (portfolio_vol**2 - target_vol**2)
        h = (c - math.sqrt(max(disc, 0.0))) / hedge_vol**2
        hedged_vol = target_vol
        capped = False

    # Carrying a short forgoes the instrument's expected return above
    # cash — that drag is the economic cost of the hedge.
    cost = h * max(hedge_expected_return - risk_free, 0.0)
    note = " (capped at the minimum-variance hedge)" if capped else ""
    return HedgeSuggestion(
        kind="short",
        instrument=instrument,
        description=(
            f"Short {instrument} for {h:.1%} of portfolio value{note}. "
            f"Reduces volatility from {portfolio_vol:.1%} to {hedged_vol:.1%}."
        ),
        hedge_notional_fraction=float(h),
        hedged_volatility=float(hedged_vol),
        est_annual_cost_fraction=float(cost),
        details={"correlation": correlation, "capped": capped},
    )


def _protection_floor(gamma: float) -> float:
    """How far below spot the put floor sits, as a fraction.

    More risk-averse users get a tighter floor: gamma 4 -> ~5% OTM,
    gamma 1 -> ~12.5% OTM, gamma near 0 -> ~25% OTM (clipped to
    [4%, 25%])."""
    return float(np.clip(0.25 / (1.0 + max(gamma, 0.0)), 0.04, 0.25))


def protective_put(
    gamma: float,
    spot: float,
    implied_vol: float,
    instrument: str = "SPY",
    t_years: float = 0.5,
    coverage: float = 1.0,
    risk_free: float = DEFAULT_RISK_FREE,
) -> HedgeSuggestion:
    """Protective puts on an index proxy with a gamma-dependent floor."""
    floor = _protection_floor(gamma)
    strike = spot * (1.0 - floor)
    premium = bs_price("put", spot, strike, implied_vol, t_years, risk_free)
    annual_cost = coverage * (premium / spot) * (1.0 / t_years)
    return HedgeSuggestion(
        kind="protective_put",
        instrument=instrument,
        description=(
            f"Buy {t_years * 12:.0f}-month {instrument} puts struck {floor:.0%} "
            f"below spot (strike ~ {strike:,.2f}) covering {coverage:.0%} of the "
            f"portfolio. Caps downside at ~{floor:.0%} beyond the premium."
        ),
        hedge_notional_fraction=float(coverage),
        est_annual_cost_fraction=float(annual_cost),
        details={
            "strike": float(strike),
            "floor": floor,
            "premium_per_share": float(premium),
            "t_years": t_years,
        },
    )


def zero_cost_collar(
    gamma: float,
    spot: float,
    implied_vol: float,
    instrument: str = "SPY",
    t_years: float = 0.5,
    coverage: float = 1.0,
    risk_free: float = DEFAULT_RISK_FREE,
) -> HedgeSuggestion:
    """Same put floor, financed by selling an out-of-the-money call."""
    floor = _protection_floor(gamma)
    put_strike = spot * (1.0 - floor)
    call_strike = implied_zero_cost_call_strike(
        spot, put_strike, implied_vol, t_years, risk_free
    )
    upside_cap = call_strike / spot - 1.0
    return HedgeSuggestion(
        kind="collar",
        instrument=instrument,
        description=(
            f"Zero-cost collar on {instrument}: buy the {floor:.0%}-OTM put "
            f"(strike ~ {put_strike:,.2f}) and sell a call struck ~ "
            f"{call_strike:,.2f} ({upside_cap:+.0%}). Downside capped at "
            f"~{floor:.0%}, upside capped at ~{upside_cap:.0%}, near-zero premium."
        ),
        hedge_notional_fraction=float(coverage),
        est_annual_cost_fraction=0.0,
        details={
            "put_strike": float(put_strike),
            "call_strike": float(call_strike),
            "floor": floor,
            "upside_cap": float(upside_cap),
            "t_years": t_years,
        },
    )


def suggest_hedges(
    weights: pd.Series,
    sigma: pd.DataFrame,
    mu: pd.Series,
    gamma: float,
    hedge_instrument: str = "SPY",
    hedge_vol: float = 0.18,
    hedge_correlation: float | None = None,
    hedge_spot: float = 100.0,
    implied_vol: float | None = None,
    risk_free: float = DEFAULT_RISK_FREE,
) -> HedgePlan:
    """Full hedge plan for a portfolio and a risk-aversion parameter.

    ``hedge_correlation`` defaults to 0.85 (typical diversified equity
    portfolio vs. SPY) when the hedge instrument is not in the
    covariance matrix; if it is, the correlation is computed exactly.
    """
    port_vol = portfolio_volatility(weights, sigma)
    port_mu = float(weights.reindex(mu.index).fillna(0.0) @ mu)
    target_vol = gamma_target_volatility(gamma, port_mu, port_vol, risk_free)
    needs_hedge = target_vol < port_vol * 0.999

    if hedge_instrument in sigma.index:
        w = weights.reindex(sigma.index).fillna(0.0).to_numpy()
        cov_ph = float(w @ sigma[hedge_instrument].to_numpy())
        hedge_vol = float(np.sqrt(sigma.loc[hedge_instrument, hedge_instrument]))
        corr = cov_ph / (port_vol * hedge_vol) if port_vol > 0 else 0.0
    else:
        corr = hedge_correlation if hedge_correlation is not None else 0.85

    iv = implied_vol if implied_vol is not None else hedge_vol

    suggestions: list[HedgeSuggestion] = []
    if needs_hedge:
        suggestions.append(
            short_hedge(
                port_vol,
                target_vol,
                hedge_vol,
                corr,
                instrument=hedge_instrument,
                risk_free=risk_free,
            )
        )
        suggestions.append(
            protective_put(
                gamma, hedge_spot, iv, instrument=hedge_instrument, risk_free=risk_free
            )
        )
        suggestions.append(
            zero_cost_collar(
                gamma, hedge_spot, iv, instrument=hedge_instrument, risk_free=risk_free
            )
        )

    return HedgePlan(
        gamma=gamma,
        current_volatility=port_vol,
        target_volatility=target_vol,
        suggestions=suggestions,
        needs_hedge=needs_hedge,
    )
