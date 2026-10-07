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
from .option_chain import select_contract

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
    warning: str | None = None  # shown prominently when the hedge is aggressive
    details: dict = field(default_factory=dict)

    def describe(self) -> str:
        lines = [f"[{self.kind}] {self.description}"]
        if self.hedged_volatility is not None:
            lines.append(f"    hedged volatility ~ {self.hedged_volatility:.2%}")
        lines.append(
            f"    est. cost ~ {self.est_annual_cost_fraction:.2%} of portfolio/yr"
        )
        return "\n".join(lines)


#: (label, peak-to-trough market shock) used for dollar stress tests.
STRESS_SCENARIOS = [
    ("2008-style financial crisis", -0.55),
    ("2020-style pandemic crash", -0.34),
    ("2022-style rate shock", -0.25),
]


@dataclass
class StressResult:
    name: str
    market_shock: float
    loss_fraction: float  # unhedged portfolio loss (fraction of value)
    loss_usd: float
    hedged_loss_fraction: float | None = None  # with the short hedge on
    hedged_loss_usd: float | None = None


def portfolio_beta(
    weights: pd.Series,
    sigma: pd.DataFrame,
    hedge_instrument: str = "SPY",
    fallback_hedge_vol: float = 0.18,
    fallback_correlation: float = 0.85,
) -> float:
    """Beta of the portfolio to the hedge instrument (market proxy).

    Uses the covariance matrix exactly when the instrument is in it;
    otherwise approximates via an assumed correlation and market vol.
    """
    port_vol = portfolio_volatility(weights, sigma)
    if hedge_instrument in sigma.index:
        w = weights.reindex(sigma.index).fillna(0.0).to_numpy()
        cov_ph = float(w @ sigma[hedge_instrument].to_numpy())
        var_h = float(sigma.loc[hedge_instrument, hedge_instrument])
        return cov_ph / var_h if var_h > 0 else 0.0
    return fallback_correlation * port_vol / fallback_hedge_vol


def stress_scenarios(
    weights: pd.Series,
    sigma: pd.DataFrame,
    portfolio_value: float,
    hedge_instrument: str = "SPY",
    hedge_fraction: float = 0.0,
    scenarios: list[tuple[str, float]] | None = None,
) -> list[StressResult]:
    """Dollar losses under historical-style market shocks.

    First-order (beta) approximation: portfolio loss = beta x shock.
    With a short hedge of notional fraction h on the market proxy, the
    hedged beta is (beta - h).
    """
    beta = portfolio_beta(weights, sigma, hedge_instrument)
    results = []
    for name, shock in (scenarios or STRESS_SCENARIOS):
        loss = max(beta, 0.0) * shock
        hedged = None
        if hedge_fraction > 0:
            hedged = max(beta - hedge_fraction, 0.0) * shock
        results.append(
            StressResult(
                name=name,
                market_shock=shock,
                loss_fraction=loss,
                loss_usd=loss * portfolio_value,
                hedged_loss_fraction=hedged,
                hedged_loss_usd=None if hedged is None else hedged * portfolio_value,
            )
        )
    return results


def revealed_gamma(
    portfolio_vol: float,
    market_premium: float = 0.05,
) -> float:
    """Risk aversion implied by *holding* this portfolio fully invested.

    Inverts the Merton rule at alpha = 1: an investor for whom this
    portfolio is optimal has gamma = premium / sigma_p^2. The market
    premium is an assumption (default 5%/yr excess return); the output
    is a positioning diagnostic, not a preference measurement — compare
    it against the questionnaire's elicited gamma to reveal the gap
    between stated and revealed risk appetite.
    """
    if portfolio_vol <= 0:
        raise ValueError("portfolio volatility must be positive")
    return market_premium / (portfolio_vol**2)


@dataclass
class HedgePlan:
    gamma: float
    current_volatility: float
    target_volatility: float
    suggestions: list[HedgeSuggestion]
    needs_hedge: bool
    portfolio_value: float | None = None
    tolerable_annual_loss_usd: float | None = None  # ~95% VaR at target vol
    current_annual_loss_usd: float | None = None  # same measure, unhedged
    scenarios: list[StressResult] = field(default_factory=list)
    #: The portfolio's expected excess return, and whether it is positive.
    #: The Merton budget alpha* = (mu - r) / (gamma * sigma^2) is only
    #: meaningful when there is a premium to be paid for bearing risk. With
    #: a non-positive premium the rule degenerates to "hold no risk at all",
    #: which arrives at the user as the cheerful and quite wrong message
    #: that no hedge is needed. Flagged so the page can say what is
    #: actually going on.
    expected_excess_return: float = 0.0
    premium_is_negative: bool = False

    def summary(self) -> str:
        lines = [
            "Hedge Plan",
            "----------",
            f"risk aversion gamma : {self.gamma:.3f}",
            f"current volatility  : {self.current_volatility:.2%}",
            f"target volatility   : {self.target_volatility:.2%}",
        ]
        if self.premium_is_negative:
            lines.append(
                f"Expected excess return is {self.expected_excess_return:+.2%} "
                "— the risk budget does not apply to a portfolio you expect "
                "to lose money on. Revisit the views driving it before "
                "hedging anything."
            )
            return "\n".join(lines)
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
    # A short this large is a leveraged position, not a tweak: it needs
    # margin, pays funding, and can be liquidated in a squeeze. Say so.
    warning = None
    if h > 0.50:
        warning = (
            f"This is a large short ({h:.0%} of portfolio value). It requires margin, "
            "accrues funding costs, and can be liquidated if the market rallies "
            "sharply. Reducing exposure directly is usually the safer way to reach "
            "the same risk level."
        )
    return HedgeSuggestion(
        kind="short",
        warning=warning,
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


def cash_hedge(
    portfolio_vol: float,
    target_vol: float,
    instrument_label: str = "cash or short-term Treasuries",
    yield_rate: float = DEFAULT_RISK_FREE,
    portfolio_expected_return: float = 0.07,
) -> HedgeSuggestion:
    """Reduce exposure by holding a zero-volatility asset.

    The plainest hedge there is, and the only one that needs no
    derivatives approval: hold a fraction ``c`` of the portfolio in cash
    (equities) or stablecoins (crypto). Because that leg has ~zero
    volatility, hedged volatility is simply ``(1 - c) * sigma_p``, so
    hitting the target requires

        c = 1 - sigma_target / sigma_p.

    The cost is the give-up between the portfolio's expected return and
    what the cash leg yields.
    """
    if portfolio_vol <= 0:
        raise ValueError("portfolio volatility must be positive")
    c = max(0.0, min(1.0, 1.0 - target_vol / portfolio_vol))
    give_up = max(portfolio_expected_return - yield_rate, 0.0) * c
    return HedgeSuggestion(
        kind="cash",
        instrument=instrument_label,
        description=(
            f"Move {c:.0%} of the portfolio into {instrument_label}. "
            f"Brings volatility from {portfolio_vol:.0%} to {target_vol:.0%} with no "
            f"derivatives, no margin, and no liquidation risk — the simplest way to "
            f"hold exactly the risk your number allows."
        ),
        hedge_notional_fraction=float(c),
        hedged_volatility=float(target_vol),
        est_annual_cost_fraction=float(give_up),
        details={"cash_fraction": float(c), "yield": yield_rate, "pricing_source": "exact"},
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
    chain: list[dict] | None = None,
) -> HedgeSuggestion:
    """Protective puts on an index proxy with a gamma-dependent floor.

    When a live option ``chain`` is supplied, the nearest listed put to
    the target strike/horizon is used for a real market premium (and its
    implied vol); otherwise the Black-Scholes model price is used.
    """
    floor = _protection_floor(gamma)
    strike = spot * (1.0 - floor)
    pricing_source = "black_scholes"
    quoted_symbol = None
    quote = None
    if chain is not None:
        quote = select_contract(chain, "put", strike, t_years * 365.0)
    if quote is not None:
        strike = quote.strike
        floor = max(0.0, 1.0 - strike / spot)
        premium = quote.price
        eff_t = max(quote.days_to_expiry / 365.0, 1e-6)
        pricing_source = "alpaca_chain"
        quoted_symbol = quote.symbol
    else:
        eff_t = t_years
        premium = bs_price("put", spot, strike, implied_vol, t_years, risk_free)
    annual_cost = coverage * (premium / spot) * (1.0 / eff_t)
    src_note = " (live quote)" if pricing_source == "alpaca_chain" else ""
    return HedgeSuggestion(
        kind="protective_put",
        instrument=instrument,
        description=(
            f"Buy {eff_t * 12:.0f}-month {instrument} puts struck {floor:.0%} "
            f"below spot (strike ~ {strike:,.2f}) covering {coverage:.0%} of the "
            f"portfolio{src_note}. Caps downside at ~{floor:.0%} beyond the premium."
        ),
        hedge_notional_fraction=float(coverage),
        est_annual_cost_fraction=float(annual_cost),
        details={
            "strike": float(strike),
            "floor": floor,
            "premium_per_share": float(premium),
            "t_years": eff_t,
            "pricing_source": pricing_source,
            "contract": quoted_symbol,
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
    chain: list[dict] | None = None,
) -> HedgeSuggestion:
    """Same put floor, financed by selling an out-of-the-money call.

    With a live ``chain``, the put premium comes from the nearest listed
    put, and the financing call is the nearest listed call whose premium
    covers it — so the collar is genuinely zero-cost at market prices,
    not just under a flat-vol model.
    """
    floor = _protection_floor(gamma)
    put_strike = spot * (1.0 - floor)
    pricing_source = "black_scholes"
    if chain is not None:
        put_q = select_contract(chain, "put", put_strike, t_years * 365.0)
        if put_q is not None:
            put_strike = put_q.strike
            floor = max(0.0, 1.0 - put_strike / spot)
            calls = [
                c
                for c in chain
                if c.get("type") == "call"
                and c.get("mid")
                and c["expiration"] == put_q.expiration
                and c["strike"] > spot
            ]
            # cheapest call whose premium still covers the put => tightest
            # upside cap that keeps the collar at (or below) zero cost
            covering = sorted(
                (c for c in calls if c["mid"] >= put_q.price),
                key=lambda c: c["strike"],
            )
            call_strike = (
                covering[0]["strike"]
                if covering
                else (max(calls, key=lambda c: c["mid"])["strike"] if calls else spot * 1.1)
            )
            upside_cap = call_strike / spot - 1.0
            pricing_source = "alpaca_chain"
            return HedgeSuggestion(
                kind="collar",
                instrument=instrument,
                description=(
                    f"Zero-cost collar on {instrument} (live quotes): buy the "
                    f"{floor:.0%}-OTM put (strike ~ {put_strike:,.2f}) and sell a "
                    f"call struck ~ {call_strike:,.2f} ({upside_cap:+.0%}). Downside "
                    f"capped at ~{floor:.0%}, upside capped at ~{upside_cap:.0%}."
                ),
                hedge_notional_fraction=float(coverage),
                est_annual_cost_fraction=0.0,
                details={
                    "put_strike": float(put_strike),
                    "call_strike": float(call_strike),
                    "floor": floor,
                    "upside_cap": float(upside_cap),
                    "t_years": max(put_q.days_to_expiry / 365.0, 1e-6),
                    "pricing_source": pricing_source,
                },
            )
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
            "pricing_source": "black_scholes",
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
    portfolio_value: float | None = None,
    option_chain: list[dict] | None = None,
    scenarios: list[tuple[str, float]] | None = None,
    cash_hedge_label: str | None = None,
    allow_options: bool = True,
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
    premium = port_mu - risk_free
    premium_is_negative = premium <= 0

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
        # Simplest first: the cash/stablecoin leg needs no derivatives
        # approval and carries no liquidation risk.
        suggestions.append(
            cash_hedge(
                port_vol,
                target_vol,
                instrument_label=cash_hedge_label or "cash or short-term Treasuries",
                yield_rate=risk_free,
                portfolio_expected_return=port_mu,
            )
        )
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
        if option_chain is not None or allow_options:
            suggestions.append(
                protective_put(
                    gamma, hedge_spot, iv, instrument=hedge_instrument,
                    risk_free=risk_free, chain=option_chain,
                )
            )
            suggestions.append(
                zero_cost_collar(
                    gamma, hedge_spot, iv, instrument=hedge_instrument,
                    risk_free=risk_free, chain=option_chain,
                )
            )

    tolerable_loss = current_loss = None
    stress: list[StressResult] = []
    if portfolio_value is not None and portfolio_value > 0:
        # ~95% one-year VaR at the target and current volatility levels.
        tolerable_loss = 1.65 * target_vol * portfolio_value
        current_loss = 1.65 * port_vol * portfolio_value
        short_fraction = next(
            (s.hedge_notional_fraction for s in suggestions if s.kind == "short"),
            0.0,
        )
        stress = stress_scenarios(
            weights,
            sigma,
            portfolio_value,
            hedge_instrument=hedge_instrument,
            hedge_fraction=short_fraction,
            scenarios=scenarios,
        )

    return HedgePlan(
        gamma=gamma,
        current_volatility=port_vol,
        target_volatility=target_vol,
        suggestions=suggestions,
        needs_hedge=needs_hedge,
        portfolio_value=portfolio_value,
        tolerable_annual_loss_usd=tolerable_loss,
        current_annual_loss_usd=current_loss,
        scenarios=stress,
        expected_excess_return=premium,
        premium_is_negative=premium_is_negative,
    )
