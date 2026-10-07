"""Replaying real research notes through the pipeline.

Everything else in `hone/backtest/` measures Hone against synthetic prices or
simulated investors.  This module does the only test that really counts:
take research notes somebody actually published, with the price targets and
dates they actually committed to, run them through the same compiler,
Black-Litterman and MVO the product uses, and see what an investor would
have ended up with — after costs, at each level of risk aversion.

Two outputs, and the second is the more interesting one:

* **Net returns by γ.**  The same notes produce different portfolios at
  different risk tolerances, so the question "did this research make money"
  has no single answer.  It has one answer per investor.
* **The analyst's calibration.**  Every note is a dated, falsifiable
  prediction.  Feeding them through :mod:`hone.journal` scores the
  publication itself: how often the targets were reached, and whether the
  confident calls landed more often than the tentative ones.  No research
  shop publishes that about itself.

Three ways this can lie to you
------------------------------
**Survivorship in the note set.**  If notes were ever deleted, edited after
publication, or selected for inclusion here, the result is a measure of the
selection and not of the research.  Use every note in the archive, in the
form it was published, or state plainly that you did not.

**The compiler has read the future.**  A language model pretrained after the
notes were written knows what happened to those tickers.  For *extraction*
— pulling out a number the analyst wrote down — that is mostly harmless.
For *inferring confidence from tone* it is not, because the model's sense of
how confident the note "sounds" is contaminated by knowing the outcome.
:func:`compile_notes` therefore defaults to the offline parser, which has
read nothing.  Passing ``use_llm=True`` is available and is a decision to
document, not a default to accept.

**Too few covered names.**  With a handful of tickers and a position cap, a
single covered name is at most ``max_weight`` of the book, and
Black-Litterman's covariance spillover reshuffles everything else by an
amount of the same order.  On a four-name universe, one entirely correct
call produced a research contribution of −3.6pp at γ=1.2 and +1.6pp at γ=5
— it disagreed with itself, because the answer was noise.  The same harness
on notes covering every name with perfect foresight returned +3.8pp and
+6.9pp.  Both are pinned by tests.  An archive covering fewer than roughly
fifteen or twenty names cannot answer "was this research any good", and no
amount of care in the rest of the method fixes that.

**Costs.**  A note-driven strategy rebalances on every publication, which is
far more turnover than a periodic rebalance.  Costs are charged here on
every trade, because the conviction backtest showed they are the difference
between a strategy that works on paper and one that works.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

import numpy as np
import pandas as pd

from ..market_data.covariance import portfolio_covariance
from ..optimization.black_litterman import (
    black_litterman_posterior,
    calibrate_delta,
    implied_equilibrium_returns,
)
from ..optimization.mvo import mvo_weights
from ..optimization.views import View
from .engine import TRADING_DAYS, performance_metrics

#: Round-trip cost in basis points of traded notional. Spread and slippage,
#: not commission — commissions are near zero and the other two are not.
DEFAULT_COST_BPS = 10.0

#: Trailing window for the covariance estimate, in periods.
DEFAULT_LOOKBACK = TRADING_DAYS

#: Per-name cap. Not optional: with a handful of names and strong views the
#: optimizer concentrates into one, which the CVaR work showed is a property
#: of the objective rather than of these particular numbers.
DEFAULT_MAX_WEIGHT = 0.35


@dataclass
class ResearchNote:
    """One published note, reduced to the claim it can be scored on."""

    ticker: str
    published: date
    target_price: float
    #: Days from publication to the target date the note gave. Most notes
    #: say "12-month price target"; that is the default rather than a guess.
    horizon_days: float = 365.0
    #: The analyst's stated conviction, 0-1. Left None when the note does
    #: not say, which is most of the time — see `confidence_default`.
    confidence: float | None = None
    #: Price at publication. Filled from the panel when absent, which is
    #: preferable: the note's own quoted price may be stale by a day.
    entry_price: float | None = None
    thesis: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        self.ticker = self.ticker.upper().strip()
        if isinstance(self.published, str):
            self.published = datetime.fromisoformat(self.published).date()
        if isinstance(self.published, datetime):
            self.published = self.published.date()
        if self.target_price <= 0:
            raise ValueError(f"{self.ticker}: target price must be positive")
        if self.horizon_days <= 0:
            raise ValueError(f"{self.ticker}: horizon must be positive")
        if self.confidence is not None and not 0 < self.confidence <= 1:
            raise ValueError(f"{self.ticker}: confidence must be in (0, 1]")

    @property
    def expires(self) -> date:
        return self.published + pd.Timedelta(days=self.horizon_days).to_pytimedelta()


@dataclass
class NoteOutcome:
    """What actually happened to one note."""

    note: ResearchNote
    entry_price: float
    final_price: float
    peak_price: float
    trough_price: float
    target_hit: bool
    touched: bool
    direction_hit: bool
    realized_return: float
    implied_return: float

    @property
    def capture(self) -> float:
        """Fraction of the predicted move that actually happened.

        More informative than a hit/miss flag on its own: an analyst who
        consistently captures 60% of their predicted move is useful and
        systematically too optimistic, which is a different problem from
        being wrong.
        """
        if abs(self.implied_return) < 1e-9:
            return 0.0
        return self.realized_return / self.implied_return


@dataclass
class GammaResult:
    """One risk tolerance, replayed over the whole note archive."""

    gamma: float
    equity: pd.Series
    turnover: float
    cost_drag: float
    n_rebalances: int
    metrics: dict = field(default_factory=dict)

    @property
    def net_return(self) -> float:
        return float(self.equity.iloc[-1] / self.equity.iloc[0] - 1.0)


def compile_notes(
    text: str,
    universe: list[str] | None = None,
    published: date | None = None,
    use_llm: bool = False,
) -> list[ResearchNote]:
    """Turn raw report text into scoreable notes.

    Defaults to the deterministic parser rather than Claude, and the reason
    is not cost.  A model pretrained after these notes were written knows
    how the trades turned out, and asking it to read confidence off the
    prose invites that knowledge into the number.  The offline parser has
    read nothing and cannot leak.
    """
    from ..llm.compiler import ConvictionCompiler

    result = ConvictionCompiler(prefer_llm=use_llm).compile(text, universe)
    notes: list[ResearchNote] = []
    for view in result.views:
        if not view.target_price:
            continue
        notes.append(
            ResearchNote(
                ticker=view.ticker,
                published=published or date.today(),
                target_price=float(view.target_price),
                horizon_days=float(view.horizon_days or 365.0),
                confidence=(
                    view.confidence_fraction()
                    if view.confidence_pct is not None
                    else None
                ),
                entry_price=view.entry_price,
                thesis=view.thesis,
            )
        )
    return notes


def score_notes(
    notes: list[ResearchNote], prices: pd.DataFrame
) -> list[NoteOutcome]:
    """Score every note against what the price actually did.

    A note whose window extends past the end of the price data is dropped
    rather than scored on a truncated window — a half-elapsed target is not
    a miss, and counting it as one flatters nobody.
    """
    px = prices.sort_index()
    idx = pd.to_datetime(px.index)
    out: list[NoteOutcome] = []

    for note in notes:
        if note.ticker not in px.columns:
            continue
        start = pd.Timestamp(note.published)
        end = start + pd.Timedelta(days=note.horizon_days)
        if end > idx.max():
            continue
        series = px[note.ticker].loc[idx >= start].dropna()
        window = series.loc[pd.to_datetime(series.index) <= end]
        if len(window) < 2:
            continue

        entry = float(note.entry_price or window.iloc[0])
        if entry <= 0:
            continue
        final = float(window.iloc[-1])
        peak, trough = float(window.max()), float(window.min())
        bullish = note.target_price >= entry

        out.append(
            NoteOutcome(
                note=note,
                entry_price=entry,
                final_price=final,
                peak_price=peak,
                trough_price=trough,
                target_hit=(final >= note.target_price) if bullish
                else (final <= note.target_price),
                touched=(peak >= note.target_price) if bullish
                else (trough <= note.target_price),
                direction_hit=(final > entry) if bullish else (final < entry),
                realized_return=final / entry - 1.0,
                implied_return=note.target_price / entry - 1.0,
            )
        )
    return out


def _active_views(
    notes: list[ResearchNote],
    as_of: pd.Timestamp,
    prices_now: pd.Series,
    confidence_default: float,
) -> list[View]:
    """Views live at a point in time — published, not yet expired.

    Only the most recent note per ticker survives: a house that publishes
    twice on one name has changed its mind, and stacking both would let a
    superseded target keep voting.
    """
    latest: dict[str, ResearchNote] = {}
    for n in notes:
        pub = pd.Timestamp(n.published)
        if pub > as_of or pub + pd.Timedelta(days=n.horizon_days) <= as_of:
            continue
        prior = latest.get(n.ticker)
        if prior is None or pd.Timestamp(n.published) > pd.Timestamp(prior.published):
            latest[n.ticker] = n

    views: list[View] = []
    for ticker, n in latest.items():
        price = prices_now.get(ticker)
        if price is None or not np.isfinite(price) or price <= 0:
            continue
        elapsed = (as_of - pd.Timestamp(n.published)).days
        remaining = max(n.horizon_days - elapsed, 21.0)
        views.append(
            View(
                ticker=ticker,
                current_price=float(price),
                target_price=n.target_price,
                confidence=n.confidence or confidence_default,
                horizon_days=float(remaining),
            )
        )
    return views


def run_report_backtest(
    notes: list[ResearchNote],
    prices: pd.DataFrame,
    gammas: tuple[float, ...] = (0.5, 1.2, 2.5, 5.0, 8.0),
    start_weights: pd.Series | None = None,
    include_no_views: bool = True,
    lookback: int = DEFAULT_LOOKBACK,
    max_weight: float = DEFAULT_MAX_WEIGHT,
    cost_bps: float = DEFAULT_COST_BPS,
    confidence_default: float = 0.5,
    periods_per_year: int = TRADING_DAYS,
) -> dict[str, GammaResult]:
    """Replay the archive at each risk tolerance and report net returns.

    The portfolio starts as ``start_weights`` (equal weight across the
    covered universe by default) and is edited whenever a note publishes or
    expires: covariance from the trailing window, equilibrium prior from the
    weights currently held, Black-Litterman for the live views, MVO at γ.
    Every weight at date *t* uses only data from before *t*.
    """
    px = prices.sort_index().ffill().dropna(how="all")
    px.index = pd.to_datetime(px.index)
    if len(px) <= lookback + 2:
        raise ValueError(
            f"need more than {lookback + 2} price rows to leave a trailing "
            f"window; got {len(px)}"
        )

    rets = px.pct_change().fillna(0.0)
    assets = list(px.columns)
    cost = cost_bps / 10_000.0

    # Rebalance whenever the live view set could have changed, plus the
    # first tradeable date. Nothing else moves the answer.
    events = set()
    for n in notes:
        for stamp in (
            pd.Timestamp(n.published),
            pd.Timestamp(n.published) + pd.Timedelta(days=n.horizon_days),
        ):
            future = px.index[px.index >= stamp]
            if len(future):
                events.add(future[0])
    start_date = px.index[lookback]
    events = sorted(e for e in events if e >= start_date)
    events = [start_date] + [e for e in events if e != start_date]

    if start_weights is None:
        base = pd.Series(1.0 / len(assets), index=assets)
    else:
        base = start_weights.reindex(assets).fillna(0.0)
        base = base / base.sum()

    results: dict[str, GammaResult] = {}

    # Each gamma is run twice: with the notes, and with the identical risk
    # machinery and no notes at all. That second run is the comparator that
    # matters. Beating equal-weight conflates two things — whether the
    # research was right, and whether the risk allocation over the names
    # nobody wrote about happened to help. With a position cap, a single
    # covered name is at most `max_weight` of the book and the uncovered
    # remainder can swamp it, so a correct call can lose to 1/N while the
    # research was worth every basis point it was given room to earn.
    runs: list[tuple[str, float, list[ResearchNote]]] = []
    for gamma in gammas:
        runs.append((f"gamma_{gamma:g}", gamma, notes))
        if include_no_views and notes:
            runs.append((f"no_views_{gamma:g}", gamma, []))

    for label, gamma, active_notes in runs:
        value, weights = 1.0, base.copy()
        curve, dates = [], []
        turnover_total, n_rebal = 0.0, 0

        for i in range(lookback, len(px)):
            today = px.index[i]

            if today in events:
                window = px.iloc[i - lookback : i]
                try:
                    sigma = portfolio_covariance(
                        window, annualize=periods_per_year
                    ).covariance
                    delta = calibrate_delta(sigma, weights)
                    pi = implied_equilibrium_returns(sigma, weights, delta)
                    views = _active_views(
                        active_notes, today, px.iloc[i - 1], confidence_default
                    )
                    if views:
                        bl = black_litterman_posterior(
                            sigma, weights, views, delta
                        )
                        mu, cov = bl.posterior_mu, bl.posterior_sigma
                    else:
                        mu, cov = pi, sigma
                    target = mvo_weights(
                        mu, cov, gamma=gamma, max_weight=max_weight,
                        current_weights=weights,
                    ).weights
                except (ValueError, np.linalg.LinAlgError):
                    target = weights  # a failed solve holds, it does not guess

                traded = float((target - weights).abs().sum())
                if traded > 1e-6:
                    value *= 1.0 - traded * cost / 2.0  # cost on one side
                    turnover_total += traded / 2.0
                    n_rebal += 1
                weights = target

            value *= 1.0 + float(weights @ rets.iloc[i].reindex(assets).fillna(0.0))
            # Let positions drift between rebalances, as a real book does.
            grown = weights * (1.0 + rets.iloc[i].reindex(assets).fillna(0.0))
            total = grown.sum()
            if total > 0:
                weights = grown / total
            curve.append(value)
            dates.append(today)

        equity = pd.Series(curve, index=pd.DatetimeIndex(dates))
        years = max(len(equity) / periods_per_year, 1e-9)
        results[label] = GammaResult(
            gamma=gamma,
            equity=equity,
            turnover=turnover_total / years,
            cost_drag=turnover_total * cost / years,
            n_rebalances=n_rebal,
            metrics=performance_metrics(equity, periods_per_year),
        )

    # Benchmarks on the identical window, so the comparison is like for like.
    for name, w in (
        ("equal_weight", pd.Series(1.0 / len(assets), index=assets)),
        ("start_hold", base),
    ):
        held = (1.0 + rets.iloc[lookback:] @ w).cumprod()
        results[name] = GammaResult(
            gamma=float("nan"),
            equity=held,
            turnover=0.0,
            cost_drag=0.0,
            n_rebalances=0,
            metrics=performance_metrics(held, periods_per_year),
        )
    return results


def analyst_scorecard(outcomes: list[NoteOutcome]) -> dict:
    """Score the publication itself, not the portfolio.

    The one thing here that no research shop publishes about its own work.
    """
    from ..journal.calibration import brier_decomposition

    if not outcomes:
        return {"n": 0}

    hits = np.array([float(o.target_hit) for o in outcomes])
    conf = np.array(
        [o.note.confidence if o.note.confidence is not None else np.nan
         for o in outcomes]
    )
    captures = np.array([o.capture for o in outcomes])

    card = {
        "n": len(outcomes),
        "target_hit_rate": float(hits.mean()),
        "touched_rate": float(np.mean([o.touched for o in outcomes])),
        "direction_hit_rate": float(np.mean([o.direction_hit for o in outcomes])),
        "mean_implied_return": float(
            np.mean([o.implied_return for o in outcomes])
        ),
        "mean_realized_return": float(
            np.mean([o.realized_return for o in outcomes])
        ),
        "median_capture": float(np.median(captures)),
    }
    if np.isfinite(conf).sum() >= 5:
        stated = conf[np.isfinite(conf)]
        card |= {
            "mean_stated_confidence": float(stated.mean()),
            **brier_decomposition(stated, hits[np.isfinite(conf)]),
        }
    return card


def summarize(results: dict[str, GammaResult]) -> pd.DataFrame:
    """One row per strategy, ordered so the benchmarks sit at the bottom."""
    rows = []
    for name, r in results.items():
        m = r.metrics
        rows.append(
            {
                "strategy": name,
                "net_return": r.net_return,
                "cagr": m.get("cagr", float("nan")),
                "volatility": m.get("volatility", float("nan")),
                "sharpe": m.get("sharpe", float("nan")),
                "max_drawdown": m.get("max_drawdown", float("nan")),
                "turnover_pa": r.turnover,
                "cost_drag_pa": r.cost_drag,
                "rebalances": r.n_rebalances,
            }
        )
    df = pd.DataFrame(rows).set_index("strategy")
    bench = [i for i in df.index if not i.startswith("gamma_")]
    out = pd.concat([df.drop(index=bench), df.loc[bench]])

    # The number the whole exercise exists to produce: what the notes added
    # over running the same risk machinery without them.
    out["research_alpha"] = [
        (
            out.loc[i, "cagr"] - out.loc[f"no_views_{i.split('_', 1)[1]}", "cagr"]
            if i.startswith("gamma_")
            and f"no_views_{i.split('_', 1)[1]}" in out.index
            else float("nan")
        )
        for i in out.index
    ]
    return out
