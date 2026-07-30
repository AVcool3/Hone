"""Does routing a user's convictions through Hone actually beat the alternatives?

The Conviction Compiler turns a plain-English thesis into a structured
view, and the *stated confidence* on that view is what scales how far
Black-Litterman tilts the portfolio away from equilibrium.  That makes
confidence the single most dangerous number in the product: it is
self-reported, unverified, and multiplied straight into position sizes.

This module answers the question empirically instead of by assertion.  It
simulates a *population* of investors — differing in risk aversion
(gamma) and in genuine forecasting skill — walks each of them forward
over the same price history, and compares six ways of turning their
convictions into a portfolio:

``equal_weight``            1/N, the retail default.
``market_hold``             buy and hold the market proxy.
``risk_only``               Hone's MVO at the investor's gamma, no views.
``views_stated_conf``       the full pipeline at the investor's *self-reported*
                            confidence — what Hone ships today.
``views_calibrated_conf``   identical views, but confidence replaced by the
                            investor's own realized hit rate to date.  This is
                            the decision-journal / Brier-calibration proposal;
                            this backtest is the evidence for whether it earns
                            its build cost.
``views_full_conf``         views taken at face value (confidence pinned to
                            1.0) — what a naive "the LLM said so" wiring would
                            do, included to size the downside of *not* having a
                            confidence channel at all.

Strategies 4-6 see byte-identical views.  Only Omega differs, so any gap
between them is attributable to the confidence mapping and nothing else.

Modelling the investor
----------------------
*Skill* is defined the way the active-management literature defines it:
the correlation (information coefficient) between the forecast and the
realized forward return.  At the decision date the simulator — not the
investor — looks ahead ``view_horizon`` periods, standardizes that
realized return against the equilibrium prior, and hands the investor a
forecast that is ``skill`` parts signal and ``sqrt(1 - skill^2)`` parts
noise.  Centering the noise on the *equilibrium prior* rather than on
zero matters: a zero-skill forecaster then produces unbiased noise around
what the model already believed, so the skill=0 row is a clean null.  If
the noise were centered on zero, skill=0 views would systematically drag
mu toward the minimum-variance portfolio and would look like a risk
control rather than like noise.

*Stated confidence* is anchored the way real users actually talk.  The
compiler's own prompt maps hedged language to 30-45% and emphatic
language to 70-85%; nobody types "3% confident".  So stated confidence is
a floor of ``STATED_CONFIDENCE_ANCHOR`` plus the investor's true edge,
optionally multiplied by an overconfidence factor.  A no-skill investor
therefore still says ~30% (calibrated) or ~60% (2x overconfident), which
is the realistic and product-relevant case.

Experimental design
-------------------
Each investor draw resamples the *price path* as well as the forecast
noise, so a win rate is measured across markets and not conditioned on
one lucky history.  Within a draw all six strategies see the same path.
Across cells (gamma x skill x overconfidence) the path and the noise
draws for a given investor index are held fixed, which makes the
comparison paired and removes most of the Monte-Carlo variance from the
differences that matter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from ..crypto.universe import (
    CRYPTO_PERIODS_PER_YEAR,
    MARKET_PROXY as CRYPTO_MARKET_PROXY,
    synthetic_crypto_universe,
)
from ..market_data.covariance import returns_from_prices, shrinkage_covariance
from ..optimization.black_litterman import (
    black_litterman_posterior,
    calibrate_delta,
    implied_equilibrium_returns,
)
from ..optimization.mvo import mvo_weights
from ..optimization.views import DAYS_PER_YEAR, View
from ..pipeline import synthetic_universe
from .engine import TRADING_DAYS, performance_metrics

STRATEGIES = (
    "equal_weight",
    "market_hold",
    "risk_only",
    "views_stated_conf",
    "views_calibrated_conf",
    "views_full_conf",
)

STRATEGY_LABELS = {
    "equal_weight": "Equal weight (1/N)",
    "market_hold": "Buy & hold the market",
    "risk_only": "Hone MVO, no views",
    "views_stated_conf": "Hone + views, stated confidence",
    "views_calibrated_conf": "Hone + views, realized-hit-rate confidence",
    "views_full_conf": "Hone + views at face value (100%)",
}

#: View strategies are the ones whose weights depend on the investor's
#: forecasts; the rest are path-only and can be cached across cells.
VIEW_STRATEGIES = (
    "views_stated_conf",
    "views_calibrated_conf",
    "views_full_conf",
)

#: Idzorek's mapping sends confidence -> 0 to Omega -> infinity, so the
#: floor only has to be small enough that the view is effectively muted.
CONFIDENCE_FLOOR = 0.02

#: Nobody types "3% confident".  The Conviction Compiler's own prompt maps
#: even hedged language into the 30-45% band, so an investor with zero
#: measurable edge still states roughly this much.  Modelling stated
#: confidence without this floor would make the stated-vs-calibrated
#: comparison trivially favourable to calibration.
STATED_CONFIDENCE_ANCHOR = 0.30

#: Pseudo-observations of a coin flip mixed into the realized hit rate.
#: Calibration is a small-sample estimate — after three resolved views a
#: user can look like a 100% forecaster.  Shrinking toward chance is the
#: honest default and reproduces what a real decision journal would have
#: to do in a user's first months.
HIT_RATE_PRIOR_STRENGTH = 5.0


# ------------------------------------------------------------------ skill
def hit_rate_from_skill(skill: float) -> float:
    """Directional accuracy of a forecaster with information coefficient
    ``skill``.

    Under joint normality, P(sign(forecast) == sign(outcome)) =
    1 - arccos(rho)/pi.  The practical point is how *small* the effect is:
    an information coefficient of 0.2 — respectable for a professional —
    buys a 56% hit rate, not 80%.
    """
    rho = float(np.clip(skill, -0.999, 0.999))
    return float(0.5 + np.arcsin(rho) / np.pi)


def confidence_from_hit_rate(hit_rate: float) -> float:
    """Map a directional hit rate onto the (0, 1] confidence Idzorek wants.

    ``2 * (h - 0.5)``: a coin-flipper earns no tilt, a perfect forecaster
    earns a certain view, and the scale in between is linear in edge above
    chance.  This is the same quantity a Brier skill score rewards, in the
    units Black-Litterman consumes.
    """
    return float(np.clip(2.0 * (hit_rate - 0.5), CONFIDENCE_FLOOR, 1.0))


def stated_confidence(skill: float, overconfidence: float = 1.0) -> float:
    """What the investor *says*, which need not be what they can do.

    The anchor is the floor of human self-report; the remaining range is
    scaled by true edge, so a genuinely skilled user does state more.
    ``overconfidence`` > 1 is the miscalibrated case the product actually
    faces.
    """
    edge = confidence_from_hit_rate(hit_rate_from_skill(skill))
    anchored = STATED_CONFIDENCE_ANCHOR + (1.0 - STATED_CONFIDENCE_ANCHOR) * edge
    return float(np.clip(overconfidence * anchored, CONFIDENCE_FLOOR, 1.0))


# ------------------------------------------------------------ asset class
@dataclass(frozen=True)
class AssetClass:
    """Everything that differs between the equities and crypto runs.

    The *protocol* is identical in both; only the calendar, the market
    proxy, the estimation window and the price generator change.
    """

    name: str
    market: str
    periods_per_year: int
    lookback: int
    n_days: int
    factory: Callable[[int], tuple[pd.DataFrame, pd.Series]]

    def prices(self, seed: int) -> pd.DataFrame:
        prices, _ = self.factory(seed)
        return prices


def equities(n_days: int = 1260, lookback: int = TRADING_DAYS) -> AssetClass:
    """Five-year synthetic equity panel on a 252-day calendar (one year of
    it is consumed by the first estimation window)."""
    return AssetClass(
        name="equities",
        market="SPY",
        periods_per_year=TRADING_DAYS,
        lookback=lookback,
        n_days=n_days,
        factory=lambda seed: synthetic_universe(
            symbols=["AAPL", "MSFT", "SPY", "TSLA", "JNJ", "NVDA"],
            n_days=n_days,
            seed=seed,
        ),
    )


def crypto(n_days: int = 1460, lookback: int = CRYPTO_PERIODS_PER_YEAR) -> AssetClass:
    """Four-year synthetic crypto panel on a 365-day calendar."""
    return AssetClass(
        name="crypto",
        market=CRYPTO_MARKET_PROXY,
        periods_per_year=CRYPTO_PERIODS_PER_YEAR,
        lookback=lookback,
        n_days=n_days,
        factory=lambda seed: synthetic_crypto_universe(n_days=n_days, seed=seed),
    )


# --------------------------------------------------------- rebalance grid
@dataclass
class RebalancePoint:
    """Everything at one rebalance date that depends only on the path.

    Cached because the sweep re-runs the same investor's price history for
    every (gamma, skill, overconfidence) cell, and the Ledoit-Wolf
    estimate is by far the most expensive thing in the loop.
    """

    t: int
    sigma: pd.DataFrame
    mu_eq: pd.Series
    prior_weights: pd.Series
    _mvo_cache: dict = field(default_factory=dict, repr=False)

    def risk_only_weights(self, gamma: float, max_weight: float) -> pd.Series:
        key = (round(float(gamma), 6), round(float(max_weight), 6))
        if key not in self._mvo_cache:
            res = mvo_weights(
                self.mu_eq, self.sigma, gamma, long_only=True, max_weight=max_weight
            )
            self._mvo_cache[key] = res.weights
        return self._mvo_cache[key]


def build_grid(
    prices: pd.DataFrame,
    lookback: int,
    rebalance_every: int,
    periods_per_year: int,
) -> list[RebalancePoint]:
    """Precompute Sigma and the equilibrium prior at every rebalance date.

    The prior is 1/N rather than each strategy's own drifted weights: the
    six strategies would otherwise anchor on six different equilibria and
    the comparison would no longer isolate the confidence channel.
    """
    points: list[RebalancePoint] = []
    for t in range(lookback, len(prices), rebalance_every):
        window = prices.iloc[t - lookback : t]
        rets = returns_from_prices(window)
        if len(rets) < 20:
            continue
        sigma = shrinkage_covariance(rets, annualize=periods_per_year)
        n = sigma.shape[0]
        prior = pd.Series(np.full(n, 1.0 / n), index=sigma.index)
        mu_eq = implied_equilibrium_returns(
            sigma, prior, delta=calibrate_delta(sigma, prior)
        )
        points.append(
            RebalancePoint(t=t, sigma=sigma, mu_eq=mu_eq, prior_weights=prior)
        )
    return points


# ----------------------------------------------------------- the forecasts
@dataclass(frozen=True)
class Forecast:
    """One conviction: what the investor said, and what actually happened.

    ``realized_log_return`` is recorded at generation time but must not be
    consulted before ``resolves_at`` — the walk-forward loop enforces that,
    which is what keeps the calibrated-confidence strategy free of
    look-ahead.
    """

    ticker: str
    current_price: float
    target_price: float
    forecast_log_return: float
    realized_log_return: float
    prior_log_return: float
    resolves_at: int

    @property
    def said_up(self) -> bool:
        return self.target_price > self.current_price

    @property
    def went_up(self) -> bool:
        return self.realized_log_return > 0.0

    @property
    def beat_prior_call(self) -> bool:
        """Did the forecast get the sign of the *surprise* right?

        The directional call is contaminated by drift — in a rising market
        "up" is right most of the time regardless of skill.  This is the
        drift-free version, kept as a diagnostic.
        """
        return (self.forecast_log_return > self.prior_log_return) == (
            self.realized_log_return > self.prior_log_return
        )


def _make_forecasts(
    point: RebalancePoint,
    prices: pd.DataFrame,
    rng: np.random.Generator,
    skill: float,
    n_views: int,
    view_horizon: int,
    periods_per_year: int,
) -> list[Forecast]:
    """Draw this investor's convictions for one rebalance date."""
    t = point.t
    # The last price the investor can actually see is the one before the
    # bar on which the new weights start earning.
    last_known = t - 1
    resolve_at = last_known + view_horizon
    if resolve_at > len(prices) - 1:
        return []

    symbols = list(point.sigma.index)
    picked = rng.choice(len(symbols), size=min(n_views, len(symbols)), replace=False)
    horizon_years = view_horizon / periods_per_year

    forecasts: list[Forecast] = []
    for i in picked:
        sym = symbols[i]
        p0 = float(prices[sym].iloc[last_known])
        p1 = float(prices[sym].iloc[resolve_at])
        realized = float(np.log(p1 / p0))
        # Prior belief and dispersion for this asset over the view horizon,
        # both taken from in-sample quantities only.
        prior = float(point.mu_eq[sym]) * horizon_years
        vol_h = float(np.sqrt(point.sigma.loc[sym, sym] * horizon_years))
        z = (realized - prior) / vol_h if vol_h > 0 else 0.0
        noise = float(rng.standard_normal())
        signal = skill * z + np.sqrt(max(1.0 - skill**2, 0.0)) * noise
        forecast = prior + vol_h * signal
        forecasts.append(
            Forecast(
                ticker=sym,
                current_price=p0,
                target_price=p0 * float(np.exp(forecast)),
                forecast_log_return=forecast,
                realized_log_return=realized,
                prior_log_return=prior,
                resolves_at=resolve_at,
            )
        )
    return forecasts


def _to_views(
    forecasts: list[Forecast],
    confidence: float,
    view_horizon: int,
    periods_per_year: int,
) -> list[View]:
    """Wrap forecasts as Hone views at a given confidence.

    ``View`` annualizes with a 365.25-day year, so the horizon has to be
    expressed in calendar days — 63 trading days is ~91 calendar days for
    equities but ~63 for crypto, and getting that wrong would silently
    rescale every view return by 1.45x.
    """
    horizon_days = view_horizon * DAYS_PER_YEAR / periods_per_year
    return [
        View(
            ticker=f.ticker,
            current_price=f.current_price,
            target_price=f.target_price,
            confidence=confidence,
            horizon_days=horizon_days,
        )
        for f in forecasts
    ]


def _view_weights(
    point: RebalancePoint,
    views: list[View],
    gamma: float,
    max_weight: float,
    tau: float,
) -> pd.Series:
    bl = black_litterman_posterior(
        point.sigma,
        point.prior_weights,
        views,
        delta=calibrate_delta(point.sigma, point.prior_weights),
        tau=tau,
    )
    res = mvo_weights(
        bl.posterior_mu,
        bl.posterior_sigma,
        gamma,
        long_only=True,
        max_weight=max_weight,
    )
    return res.weights


# ------------------------------------------------------------------ engine
def _structure_metrics(history: list[np.ndarray]) -> dict[str, float]:
    """How concentrated and how twitchy the portfolio was.

    Two numbers, both needed to interpret a Sharpe difference honestly.
    ``effective_n`` is the inverse Herfindahl of the weights: a Sharpe gain
    that comes with a rise in effective_n is diversification, not
    forecasting.  ``turnover`` is the one-way fraction of the book traded
    per rebalance — the cost side that this frictionless backtest, like
    every frictionless backtest, does not charge for.
    """
    if not history:
        return {"effective_n": float("nan"), "turnover": float("nan")}
    w = np.vstack(history)
    hhi = np.sum(w**2, axis=1)
    eff_n = float(np.mean(1.0 / np.where(hhi > 0, hhi, np.nan)))
    turnover = (
        float(np.mean(0.5 * np.abs(np.diff(w, axis=0)).sum(axis=1)))
        if len(w) > 1
        else 0.0
    )
    return {"effective_n": eff_n, "turnover": turnover}


@dataclass
class InvestorRun:
    gamma: float
    skill: float
    overconfidence: float
    seed: int
    metrics: dict[str, dict[str, float]]
    diagnostics: dict[str, float]
    rebalances: int


def run_investor_backtest(
    prices: pd.DataFrame,
    gamma: float,
    skill: float,
    overconfidence: float = 1.0,
    seed: int = 0,
    grid: list[RebalancePoint] | None = None,
    lookback: int = TRADING_DAYS,
    rebalance_every: int = 21,
    view_horizon: int = 63,
    n_views: int = 2,
    max_weight: float = 0.35,
    tau: float = 0.05,
    market: str = "SPY",
    periods_per_year: int = TRADING_DAYS,
    initial_value: float = 10_000.0,
) -> InvestorRun:
    """Walk one synthetic investor forward across all six strategies.

    Every strategy trades the same path with the same rebalance schedule;
    the three view strategies receive identical forecasts and differ only
    in the confidence handed to Idzorek's Omega.
    """
    prices = prices.sort_index().dropna(how="any")
    if grid is None:
        grid = build_grid(prices, lookback, rebalance_every, periods_per_year)
    if len(grid) < 3:
        raise ValueError(
            f"need at least 3 rebalance dates; got {len(grid)} — lengthen the "
            "price history or shorten the lookback"
        )

    stated = stated_confidence(skill, overconfidence)
    rng = np.random.default_rng(seed)

    columns = list(prices.columns)
    # The accumulation loop runs once per bar per strategy; keeping it in
    # numpy rather than pandas is worth roughly a quarter of the sweep's
    # total runtime.
    ret_mat = prices.pct_change().fillna(0.0).to_numpy()

    def align(w: pd.Series) -> np.ndarray:
        return w.reindex(columns).fillna(0.0).to_numpy(dtype=float)

    equal = np.full(len(columns), 1.0 / len(columns))
    if market in columns:
        hold = np.zeros(len(columns))
        hold[columns.index(market)] = 1.0
    else:  # no proxy in the universe: fall back to 1/N rather than crash
        hold = equal.copy()

    weights: dict[str, np.ndarray | None] = {s: None for s in STRATEGIES}
    values = {s: initial_value for s in STRATEGIES}
    curves: dict[str, list[float]] = {s: [] for s in STRATEGIES}
    # Weight history is kept so the report can separate "the views carried
    # information" from "the views happened to de-concentrate the
    # portfolio" — two very different reasons for a Sharpe gain.
    history: dict[str, list[np.ndarray]] = {s: [] for s in STRATEGIES}
    curve_dates: list = []

    pending: list[Forecast] = []
    wins = losses = 0
    prior_wins = prior_losses = 0
    calibrated_seen: list[float] = []

    points = {p.t: p for p in grid}
    start = grid[0].t

    for t in range(start, len(prices)):
        point = points.get(t)
        if point is not None:
            # Resolve every conviction whose horizon has now elapsed. This
            # happens before the new views are priced, so the calibrated
            # confidence uses exactly the information a real decision
            # journal would hold at this date and no more.
            still_open = []
            for f in pending:
                if f.resolves_at <= t - 1:
                    if f.said_up == f.went_up:
                        wins += 1
                    else:
                        losses += 1
                    if f.beat_prior_call:
                        prior_wins += 1
                    else:
                        prior_losses += 1
                else:
                    still_open.append(f)
            pending = still_open

            n_resolved = wins + losses
            smoothed = (wins + 0.5 * HIT_RATE_PRIOR_STRENGTH) / (
                n_resolved + HIT_RATE_PRIOR_STRENGTH
            )
            calibrated = confidence_from_hit_rate(smoothed)
            calibrated_seen.append(calibrated)

            weights["equal_weight"] = equal
            weights["market_hold"] = hold
            risk_only = align(point.risk_only_weights(gamma, max_weight))
            weights["risk_only"] = risk_only

            forecasts = _make_forecasts(
                point, prices, rng, skill, n_views, view_horizon, periods_per_year
            )
            if forecasts:
                pending.extend(forecasts)
                for name, conf in (
                    ("views_stated_conf", stated),
                    ("views_calibrated_conf", calibrated),
                    ("views_full_conf", 1.0),
                ):
                    views = _to_views(forecasts, conf, view_horizon, periods_per_year)
                    try:
                        weights[name] = align(
                            _view_weights(point, views, gamma, max_weight, tau)
                        )
                    except (ValueError, np.linalg.LinAlgError):
                        # A degenerate Omega is not a reason to abandon the
                        # investor; fall back to the view-free portfolio.
                        weights[name] = risk_only
            else:
                # Past the last date at which a view could resolve inside
                # the sample: stop issuing new convictions and hold.
                for name in VIEW_STRATEGIES:
                    if weights[name] is None:
                        weights[name] = risk_only

            for name in STRATEGIES:
                if weights[name] is not None:
                    history[name].append(weights[name])

        r = ret_mat[t]
        for name in STRATEGIES:
            w = weights[name]
            if w is not None:
                values[name] *= 1.0 + float(w @ r)
            curves[name].append(values[name])
        curve_dates.append(prices.index[t])

    idx = pd.DatetimeIndex(curve_dates)
    metrics = {}
    for name in STRATEGIES:
        m = performance_metrics(pd.Series(curves[name], index=idx), periods_per_year)
        m.update(_structure_metrics(history[name]))
        metrics[name] = m

    n_resolved = wins + losses
    n_prior = prior_wins + prior_losses
    diagnostics = {
        "stated_confidence": stated,
        "mean_calibrated_confidence": float(np.mean(calibrated_seen))
        if calibrated_seen
        else float("nan"),
        "final_calibrated_confidence": calibrated_seen[-1]
        if calibrated_seen
        else float("nan"),
        "directional_hit_rate": wins / n_resolved if n_resolved else float("nan"),
        "surprise_hit_rate": prior_wins / n_prior if n_prior else float("nan"),
        "views_resolved": float(n_resolved),
    }
    return InvestorRun(
        gamma=gamma,
        skill=skill,
        overconfidence=overconfidence,
        seed=seed,
        metrics=metrics,
        diagnostics=diagnostics,
        rebalances=len(grid),
    )


# ------------------------------------------------------------------- panel
def run_panel(
    asset_class: AssetClass,
    gammas: list[float],
    skills: list[float],
    overconfidences: list[float],
    n_investors: int = 20,
    base_seed: int = 1_000,
    rebalance_every: int = 21,
    view_horizon: int = 63,
    n_views: int = 2,
    max_weight: float = 0.35,
    tau: float = 0.05,
    progress: Callable[[str], None] | None = None,
) -> pd.DataFrame:
    """Run the full cross of investors x gamma x skill x overconfidence.

    The price path and the forecast-noise stream are keyed to the investor
    index alone, so every cell sees the same markets and the same
    "personality" — the design is paired, and differences between cells
    are not Monte-Carlo noise about which histories got drawn.
    """
    rows: list[dict] = []
    for i in range(n_investors):
        seed = base_seed + i
        prices = asset_class.prices(seed)
        grid = build_grid(
            prices,
            asset_class.lookback,
            rebalance_every,
            asset_class.periods_per_year,
        )
        if progress is not None:
            progress(f"{asset_class.name}: investor {i + 1}/{n_investors}")
        for gamma in gammas:
            for skill in skills:
                for over in overconfidences:
                    run = run_investor_backtest(
                        prices,
                        gamma=gamma,
                        skill=skill,
                        overconfidence=over,
                        seed=seed,
                        grid=grid,
                        lookback=asset_class.lookback,
                        rebalance_every=rebalance_every,
                        view_horizon=view_horizon,
                        n_views=n_views,
                        max_weight=max_weight,
                        tau=tau,
                        market=asset_class.market,
                        periods_per_year=asset_class.periods_per_year,
                    )
                    for name, m in run.metrics.items():
                        rows.append(
                            {
                                "asset_class": asset_class.name,
                                "investor": i,
                                "gamma": gamma,
                                "skill": skill,
                                "overconfidence": over,
                                "strategy": name,
                                **m,
                                **{
                                    f"diag_{k}": v
                                    for k, v in run.diagnostics.items()
                                },
                            }
                        )
    return pd.DataFrame(rows)


CELL_KEYS = ["asset_class", "gamma", "skill", "overconfidence"]

#: Metric the win rates are scored on.  Sharpe rather than CAGR because
#: the product's claim is about risk-adjusted outcomes, not about beating
#: the market on return — but ``summarize`` reports the CAGR-based win
#: rate too, since that is the one users will feel.
PRIMARY_METRIC = "sharpe"


def _win_rate(panel: pd.DataFrame, metric: str, benchmark: str) -> pd.Series:
    """Fraction of investor draws in which each strategy beat ``benchmark``.

    Paired within (cell, investor): the point of the exercise is "does
    this help *me*", not "does it help the average of a population that
    never existed".
    """
    wide = panel.pivot_table(
        index=CELL_KEYS + ["investor"], columns="strategy", values=metric
    )
    beat = wide.gt(wide[benchmark], axis=0)
    return beat.groupby(level=CELL_KEYS).mean().stack()


def summarize(panel: pd.DataFrame) -> pd.DataFrame:
    """Per-cell, per-strategy distribution summary plus win rates."""
    grouped = panel.groupby(CELL_KEYS + ["strategy"])
    out = grouped.agg(
        cagr=("cagr", "median"),
        cagr_mean=("cagr", "mean"),
        volatility=("volatility", "median"),
        sharpe=("sharpe", "median"),
        sharpe_p25=("sharpe", lambda s: s.quantile(0.25)),
        sharpe_p75=("sharpe", lambda s: s.quantile(0.75)),
        sortino=("sortino", "median"),
        max_drawdown=("max_drawdown", "median"),
        final_multiple=("final_multiple", "median"),
        effective_n=("effective_n", "median"),
        turnover=("turnover", "median"),
        n=("sharpe", "size"),
    )
    for metric, suffix in ((PRIMARY_METRIC, ""), ("cagr", "_cagr")):
        for bench in ("risk_only", "market_hold"):
            rate = _win_rate(panel, metric, bench)
            rate.index.names = CELL_KEYS + ["strategy"]
            out[f"beat_{bench}{suffix}"] = rate
    return out.reset_index()


def diagnostics_table(panel: pd.DataFrame) -> pd.DataFrame:
    """Confidence and hit-rate diagnostics per cell (path-independent of
    strategy, so one row per cell)."""
    cols = [c for c in panel.columns if c.startswith("diag_")]
    return (
        panel[panel["strategy"] == "views_stated_conf"]
        .groupby(CELL_KEYS)[cols]
        .mean()
        .reset_index()
    )
