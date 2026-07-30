"""Predictions and how they resolve against the market.

A journal entry is written at the moment a view is acted on, not afterwards.
That ordering is the entire point: a record assembled from memory is a record
of what the user now believes they believed.  Entry price, target, horizon and
confidence are all frozen at decision time, so the eventual score is
unarguable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

import pandas as pd


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_datetime(value: str | datetime | date) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass
class Prediction:
    """One dated, falsifiable claim.

    Parameters
    ----------
    ticker, direction
        What the claim is about and which way it points.
    entry_price, target_price
        The price when the claim was made and the price claimed.  Both are
        frozen at decision time.
    horizon_days
        When the claim becomes scoreable.
    confidence
        The user's stated probability, in (0, 1], that the target is reached
        within the horizon.  This is the number being scored.
    created_at
        Decision time.  Defaults to now, which is correct only when the
        record is written at the moment of the decision — the API refuses
        to accept a future date and the UI never sets it by hand.
    """

    ticker: str
    entry_price: float
    target_price: float
    confidence: float
    horizon_days: float = 365.0
    direction: str = "bullish"
    thesis: str = ""
    created_at: datetime = field(default_factory=_utcnow)
    id: str = ""
    asset_class: str = "equities"

    def __post_init__(self) -> None:
        self.created_at = _as_datetime(self.created_at)
        self.ticker = self.ticker.upper().strip()
        if self.entry_price <= 0 or self.target_price <= 0:
            raise ValueError("prices must be positive")
        if not 0.0 < self.confidence <= 1.0:
            raise ValueError("confidence must be in (0, 1]")
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        if self.direction not in ("bullish", "bearish"):
            raise ValueError("direction must be 'bullish' or 'bearish'")

    @property
    def resolves_at(self) -> datetime:
        return self.created_at + timedelta(days=float(self.horizon_days))

    def is_mature(self, now: datetime | None = None) -> bool:
        return (now or _utcnow()) >= self.resolves_at

    def implied_return(self) -> float:
        return self.target_price / self.entry_price - 1.0


@dataclass
class Resolution:
    """The verdict on one matured prediction.

    Two events are scored, because they answer different questions:

    ``target_hit``
        Did the price finish at or beyond the stated target?  This is
        literally what the confidence number claimed, so it is what the
        calibration mapping is fitted on.
    ``direction_hit``
        Did the price simply move the way the user said?  A much easier
        event, and a much less noisy signal of whether someone knows
        anything.  Reported alongside because a user who is directionally
        right and habitually too greedy about magnitude deserves different
        feedback from one who is simply wrong.

    ``touched`` records whether the target was reached *at any point* before
    expiry.  It is not scored — a target touched intraday and given back is
    not a forecast that paid — but it is shown, because "you were right and
    didn't take it" is the most useful thing a journal can tell someone.
    """

    prediction: Prediction
    final_price: float
    target_hit: bool
    direction_hit: bool
    touched: bool
    realized_return: float
    resolved_at: datetime

    @property
    def confidence(self) -> float:
        return self.prediction.confidence

    #: Squared error of the stated probability against the target event.
    @property
    def brier(self) -> float:
        return (self.confidence - float(self.target_hit)) ** 2


def resolve_prediction(
    prediction: Prediction,
    prices: pd.Series,
    now: datetime | None = None,
) -> Resolution | None:
    """Score one prediction against a price series, or None if not yet due.

    ``prices`` must be a datetime-indexed series for the prediction's ticker
    covering the horizon.  Returns None when the horizon has not elapsed or
    when there is no price data inside the window — an unresolvable
    prediction is left open rather than scored as a miss, since counting
    missing data as failure would quietly punish the user for our gaps.
    """
    now = now or _utcnow()
    if not prediction.is_mature(now):
        return None

    series = prices.dropna()
    if series.empty:
        return None
    index = pd.to_datetime(series.index)
    if index.tz is None:
        index = index.tz_localize(timezone.utc)
    series = pd.Series(series.to_numpy(), index=index)

    window = series[
        (series.index > prediction.created_at) & (series.index <= prediction.resolves_at)
    ]
    if window.empty:
        return None

    final = float(window.iloc[-1])
    bullish = prediction.direction == "bullish"
    target = prediction.target_price

    if bullish:
        target_hit = final >= target
        touched = bool(window.max() >= target)
        direction_hit = final > prediction.entry_price
    else:
        target_hit = final <= target
        touched = bool(window.min() <= target)
        direction_hit = final < prediction.entry_price

    return Resolution(
        prediction=prediction,
        final_price=final,
        target_hit=bool(target_hit),
        direction_hit=bool(direction_hit),
        touched=touched,
        realized_return=final / prediction.entry_price - 1.0,
        resolved_at=window.index[-1].to_pydatetime(),
    )


def resolve_all(
    predictions: list[Prediction],
    prices: pd.DataFrame,
    now: datetime | None = None,
) -> tuple[list[Resolution], list[Prediction]]:
    """Resolve everything that can be resolved.

    Returns ``(resolved, still_open)``.  Predictions whose ticker is absent
    from ``prices`` stay open.
    """
    resolved: list[Resolution] = []
    still_open: list[Prediction] = []
    for p in predictions:
        if p.ticker not in prices.columns:
            still_open.append(p)
            continue
        outcome = resolve_prediction(p, prices[p.ticker], now=now)
        if outcome is None:
            still_open.append(p)
        else:
            resolved.append(outcome)
    return resolved, still_open
