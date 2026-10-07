"""The behaviour gap: what the investor got, not what the strategy did.

Every backtest in this repository, and almost every backtest anywhere,
silently assumes the investor holds the strategy through whatever it does.
They do not.  Real investors capitulate after drawdowns, sit in cash while
the recovery happens, and return once it feels safe — which is to say
after the recovery.  The gap between fund returns and investor returns
runs to whole percentage points a year, which is not a rounding error
against the differences most of finance argues about.

That gap is the strongest argument for Hone existing, and it is testable
rather than assertable: if a portfolio matched to someone's measured risk
tolerance is one they are more likely to actually hold, the γ-matched book
should lose less to capitulation than an aggressive one — even where the
aggressive one wins on paper.

This module also charges the two costs the conviction backtest
(docs/BACKTEST_CONVICTION.md) flagged as missing everywhere else in the
codebase: trading costs on every switch, and the cash rate — not zero —
while out of the market.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..optimization.black_litterman import TARGET_MARKET_SHARPE
from .engine import TRADING_DAYS, performance_metrics

#: One-sided 95% normal quantile — the same rule of thumb the hedge page
#: uses to turn a volatility budget into a dollar loss.
VAR_Z = 1.645

#: Minimum periods out of the market after capitulating, before the
#: re-entry rule is consulted at all. A month: nobody sells in a panic and
#: buys back the same week.
DEFAULT_MIN_WAIT = 21

#: Re-entry rule: how far the market must climb off its low *after* the
#: sale before it feels safe again. This is the mechanism that makes
#: capitulation expensive, and it is the part a fixed cooldown gets wrong
#: — see :func:`simulate_holding`.
DEFAULT_REENTRY_RECOVERY = 0.10

#: Round-trip cost in basis points per switch. Retail commissions are near
#: zero; this is spread and slippage, which are not.
DEFAULT_COST_BPS = 10.0

#: Cash rate earned while out of the market.
DEFAULT_CASH_RATE = 0.04


def panic_threshold(
    gamma: float,
    market_sharpe: float = TARGET_MARKET_SHARPE,
    floor: float = 0.08,
    cap: float = 0.60,
) -> float:
    """Drawdown at which this investor is modelled as capitulating.

    The Merton rule puts α* = (μ − r) / (γ σ_m²) of wealth in the risky
    asset.  Pricing the market at a Sharpe ratio S — so the premium is
    S·σ_m, the same assumption
    :func:`~hone.optimization.black_litterman.calibrate_delta` makes when
    it builds the equilibrium prior — collapses the whole expression:

        σ_target = α*·σ_m = S / γ

    The market's volatility cancels, and so does its realized return.
    That is the point.  Two earlier versions of this used sample
    estimates and both broke.  A per-strategy premium made tolerance a
    function of the *strategy's* Sharpe ratio, so the same person
    tolerated a 60% drawdown in a bad fund and 8% in a good one.  A
    market-wide sample premium was negative over the demo window, which
    pinned every γ to the same cap.  A capitulation point is a property
    of the person; it should not move because five years of history
    happened to be poor.

    Bounded at both ends, where the formula degenerates: a nearly
    risk-neutral investor would tolerate an unbounded drawdown, which no
    human does, and a very risk-averse one would panic at a twitch.
    """
    g = max(float(gamma), 1e-6)
    return float(np.clip(VAR_Z * float(market_sharpe) / g, floor, cap))


@dataclass
class BehaviorResult:
    """One strategy, held perfectly vs. held by a person."""

    name: str
    paper_equity: pd.Series
    realized_equity: pd.Series
    panic_threshold: float
    panics: list = field(default_factory=list)
    periods_in_cash: int = 0
    cost_drag: float = 0.0
    periods_per_year: int = TRADING_DAYS

    @property
    def paper_metrics(self) -> dict[str, float]:
        return performance_metrics(self.paper_equity, self.periods_per_year)

    @property
    def realized_metrics(self) -> dict[str, float]:
        return performance_metrics(self.realized_equity, self.periods_per_year)

    @property
    def behavior_gap(self) -> float:
        """Paper CAGR minus realized CAGR — what the panicking cost."""
        p = self.paper_metrics.get("cagr")
        r = self.realized_metrics.get("cagr")
        if p is None or r is None:
            return float("nan")
        return float(p - r)

    @property
    def time_in_cash(self) -> float:
        return self.periods_in_cash / max(len(self.paper_equity), 1)

    def summary(self) -> str:
        pm, rm = self.paper_metrics, self.realized_metrics
        n = len(self.panics)
        lines = [
            f"{self.name}",
            f"  panic threshold : {self.panic_threshold:.0%} drawdown",
            f"  on paper        : {pm.get('cagr', 0):+.2%}/yr, "
            f"max drawdown {pm.get('max_drawdown', 0):.0%}",
            f"  as actually held: {rm.get('cagr', 0):+.2%}/yr "
            f"({n} capitulation{'s' if n != 1 else ''}, "
            f"{self.time_in_cash:.0%} of the time in cash)",
            f"  behaviour gap   : {self.behavior_gap:+.2%}/yr",
        ]
        if self.cost_drag:
            lines.append(f"  trading costs   : {self.cost_drag:.2%}/yr")
        return "\n".join(lines)


def simulate_holding(
    returns: pd.Series,
    threshold: float,
    min_wait: int = DEFAULT_MIN_WAIT,
    reentry_recovery: float = DEFAULT_REENTRY_RECOVERY,
    cash_rate: float = DEFAULT_CASH_RATE,
    periods_per_year: int = TRADING_DAYS,
    cost_bps: float = DEFAULT_COST_BPS,
) -> tuple[pd.Series, list, int, float]:
    """Apply a capitulation rule to a return series.

    Returns ``(realized equity, panic dates, periods in cash, cost drag)``.

    Two details carry the whole model.

    **Drawdown is measured against the realized peak**, not the paper one.
    Someone who sold and re-entered lower measures their pain from where
    their own account peaked, not from where the strategy would have been.
    Re-entering resets that peak: an investor who capitulated and bought
    back has, in the only sense that matters here, accepted the loss.
    Without the reset the simulation re-panics on the next bar and parks
    the investor in cash permanently — an artifact of the bookkeeping
    rather than of anyone's psychology.

    **Re-entry waits for confirmation** — the market must climb
    ``reentry_recovery`` off its low since the sale before it feels safe
    again.  This is what makes capitulation cost anything, because it
    structurally buys back above the trough.  A fixed cooldown does not,
    and can be accidentally well-timed: that version of this function
    produced a panicking investor who *beat* the strategy by 21 points a
    year, which is a stop-loss backtest wearing the wrong label.
    """
    rets = returns.dropna()
    cash_per_period = cash_rate / periods_per_year
    cost_per_switch = cost_bps / 10_000.0

    equity = [1.0]
    peak = 1.0
    out_of_market = False
    waited = 0
    shadow = 1.0  # what the strategy does while the investor is out
    trough = 1.0
    panics: list = []
    cash_periods = 0
    switches = 0

    for date, r in rets.items():
        r = float(r)
        if out_of_market:
            shadow *= 1.0 + r
            trough = min(trough, shadow)
            waited += 1
            cash_periods += 1
            value = equity[-1] * (1.0 + cash_per_period)
            recovered = trough > 0 and (shadow / trough - 1.0) >= reentry_recovery
            if waited >= min_wait and recovered:
                value *= 1.0 - cost_per_switch  # buying back in
                switches += 1
                out_of_market = False
                peak = value  # the old high is no longer the reference
        else:
            value = equity[-1] * (1.0 + r)
            if value / peak - 1.0 < -threshold:
                value *= 1.0 - cost_per_switch  # sell at today's close
                switches += 1
                out_of_market = True
                waited = 0
                shadow = 1.0
                trough = 1.0
                panics.append(date)
        peak = max(peak, value)
        equity.append(value)

    realized = pd.Series(equity[1:], index=rets.index)
    years = max(len(rets) / periods_per_year, 1e-9)
    drag = switches * cost_per_switch / years
    return realized, panics, cash_periods, float(drag)


def behavior_gap(
    equity_curves: dict[str, pd.Series],
    gamma: float,
    min_wait: int = DEFAULT_MIN_WAIT,
    reentry_recovery: float = DEFAULT_REENTRY_RECOVERY,
    cash_rate: float = DEFAULT_CASH_RATE,
    periods_per_year: int = TRADING_DAYS,
    cost_bps: float = DEFAULT_COST_BPS,
) -> dict[str, BehaviorResult]:
    """Run the capitulation simulation across several strategies.

    One threshold, from γ alone, applied to every strategy — because it
    is the same person holding each of them.  What differs between
    strategies is how often their drawdowns cross it.
    """
    threshold = panic_threshold(gamma)
    out: dict[str, BehaviorResult] = {}
    for name, curve in equity_curves.items():
        equity = pd.Series(curve).dropna()
        if len(equity) < 3:
            continue
        rets = equity.pct_change().dropna()
        realized, panics, cash_periods, drag = simulate_holding(
            rets, threshold, min_wait, reentry_recovery,
            cash_rate, periods_per_year, cost_bps,
        )
        out[name] = BehaviorResult(
            name=name,
            paper_equity=equity / equity.iloc[0],
            realized_equity=realized,
            panic_threshold=threshold,
            panics=panics,
            periods_in_cash=cash_periods,
            cost_drag=drag,
            periods_per_year=periods_per_year,
        )
    return out


def matching_advantage(results: dict[str, BehaviorResult]) -> dict:
    """Does matching the portfolio to the investor actually pay?

    The claim under test is not "the tier-matched portfolio wins on
    paper" — often it does not, and it is not supposed to.  It is that a
    portfolio sized to what someone can tolerate is one they keep
    holding, so it loses less to capitulation.  This returns the pieces
    needed to check that, including when it fails.
    """
    if not results:
        return {}
    paper = {k: v.paper_metrics.get("cagr", 0.0) for k, v in results.items()}
    realized = {k: v.realized_metrics.get("cagr", 0.0) for k, v in results.items()}
    return {
        "best_on_paper": max(paper, key=paper.get),
        "best_as_held": max(realized, key=realized.get),
        "ranking_changed": max(paper, key=paper.get) != max(realized, key=realized.get),
        "paper_spread": float(max(paper.values()) - min(paper.values())),
        "realized_spread": float(max(realized.values()) - min(realized.values())),
        "worst_gap": float(max(v.behavior_gap for v in results.values())),
        "best_gap": float(min(v.behavior_gap for v in results.values())),
        "total_panics": int(sum(len(v.panics) for v in results.values())),
    }
