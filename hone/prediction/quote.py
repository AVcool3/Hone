"""Price and size protection from a minimal description of a business.

"I own a ski resort in Aspen, about $4M in season revenue" is all the user
types. Everything else is worked out here:

1. **Where** — the place is geocoded (:mod:`hone.prediction.climate`).
2. **How often seasons go badly there** — every winter's snowfall since
   1980. A *bad season* is one below ``trigger_fraction`` of the place's
   normal (median) snowfall — default 80%. (A percentile trigger is also
   available, but "the worst 25%" happens 25% of the time by definition
   everywhere, so it can't tell a steady place from a volatile one.)
   Hone then estimates the chance of one *next* season:
     * if snowfall has a statistically meaningful trend, past seasons are
       re-centred on where the trend is now (a drying trend makes bad
       seasons likelier than their historical 25%);
     * the count is turned into a probability with a Beta posterior, so
       a short history gives a wide range instead of false precision.
3. **What a bad season costs** — the average snowfall shortfall in bad
   seasons (vs. the place's normal) times how sensitive the business's
   revenue is to snowfall (``BUSINESSES[...].elasticity``). For a
   business, what's at risk is *profit*: most costs are fixed, so lost
   revenue comes straight out of it. The cushion is therefore cash
   reserves plus a normal season's profit (``margin``), not revenue.
4. **Hone's price** — the fair price of a contract paying $1 in a bad
   season is the probability itself. A provider would add a margin
   (``DEFAULT_LOADING``); both are shown.
5. **How much to buy** — the same expected-utility sizing as the rest of
   Hone Markets (:func:`hone.prediction.hedge.hedge_income`), at the
   user's risk aversion. Buy-only: the customer can't sell protection
   back at Hone's price, so the "sell when overpriced" branch is off.

   Basis risk can make the right answer *smaller* for more vulnerable or
   more risk-averse owners: if there's a chance of a bad season in which
   the contract doesn't pay, every dollar spent on it makes that worst
   case worse. This is a known result for index insurance (Clarke 2016,
   "A Theory of Rational Demand for Index Insurance", AEJ: Micro). The
   quote compares against a contract that always paid, and explains the
   gap when it's large.
6. **Is there a market?** — the nearest Kalshi snow market, how far away,
   and how closely its location's snowfall has tracked this place's.

This module PRICES protection; it does not sell it. Selling a payout to a
customer is regulated (insurance / swaps) — see docs/PREDICTION_MARKETS.md.

To change an assumption, edit the constants below; each says what it does.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .climate import Place, geocode, snowfall_history
from .hedge import BASIS_SHRINK, IncomeExposure, hedge_income


# --------------------------------------------------------------- assumptions
#: Ski-resort revenue lost per 1% snowfall shortfall, by region. From the
#: published evidence collected in research/prediction/findings/01_research.md:
#: ~0.1-0.2 in high, snow-sure areas (Austria; Nevada 0.21), larger where
#: snow is marginal; US low-snow seasons cost ~5-16% of visits nationally
#: and 36% in the Pacific Northwest in 2014-15. Effects show up mainly below
#: ~70% of normal, which is why the default bad-season trigger is 70%.
REGION_ELASTICITY = {"pacific": 0.8, "rockies": 0.25, "east": 0.4, "other": 0.3}
#: In the East/Midwest temperature (rain vs snow, snowmaking days) matters
#: more than snowfall, so a snowfall contract tracks revenue less closely.
REGION_BASIS_SCALE = {"pacific": 1.0, "rockies": 1.0, "east": 0.8, "other": 0.9}


def region_of(lat: float, lon: float) -> str:
    """Rough North American ski regions by longitude; 'other' elsewhere."""
    if not (24 <= lat <= 60 and -170 <= lon <= -50):
        return "other"
    if lon < -116:
        return "pacific"
    if lon < -100:
        return "rockies"
    return "east"


@dataclass(frozen=True)
class Business:
    key: str
    label: str
    #: revenue sensitivity relative to a ski resort in the same region. No
    #: published figures exist for instructors or shops: these are flagged
    #: assumptions. Snow removal is set directly (fixed_elasticity).
    elasticity_scale: float
    #: how tightly a contract on THIS place's snowfall tracks the business's
    #: revenue (snowmaking, the wider economy and holidays also matter)
    basis: float
    #: a bad season can't cost more than this share of revenue
    max_loss_frac: float
    #: normal-season profit as a share of revenue (1.0 = it's personal
    #: income, all of which is the person's to lose)
    margin: float = 1.0
    #: default cash reserves as a share of revenue, if the user gives none
    reserves_frac: float = 0.25
    #: revenue that's proportional to snowfall itself, whatever the region
    fixed_elasticity: float | None = None
    season: tuple[int, int] = (11, 4)  # Nov-Apr

    def elasticity_for(self, region: str) -> float:
        if self.fixed_elasticity is not None:
            return self.fixed_elasticity
        return REGION_ELASTICITY.get(region, REGION_ELASTICITY["other"]) * self.elasticity_scale

    def basis_for(self, region: str) -> float:
        return min(1.0, self.basis * REGION_BASIS_SCALE.get(region, 1.0))

BUSINESSES = {
    b.key: b for b in [
        Business("ski_resort", "Ski resort", elasticity_scale=1.0, basis=0.7, max_loss_frac=0.6,
                 margin=0.15, reserves_frac=0.10),
        Business("ski_instructor", "Ski instructor (personal income)", elasticity_scale=1.3, basis=0.6,
                 max_loss_frac=0.7, margin=1.0, reserves_frac=0.25),
        Business("mountain_retail", "Mountain-town shop or restaurant", elasticity_scale=0.7, basis=0.5,
                 max_loss_frac=0.5, margin=0.10, reserves_frac=0.10),
        Business("snow_removal", "Snow removal / plowing", elasticity_scale=1.0, basis=0.8,
                 max_loss_frac=0.8, margin=0.20, reserves_frac=0.10, fixed_elasticity=1.0),
    ]
}

#: A "bad season" is below this fraction of the place's normal snowfall.
#: 70% because the evidence finds revenue effects mainly below about that.
DEFAULT_TRIGGER_FRACTION = 0.70
#: Margin a protection seller adds over the expected payout. Parametric
#: snow sellers (Arbol, Vortex/MSI, Demex) don't publish prices; catastrophe
#: bonds price at ~2.3-2.5x expected loss, but those are rare-event covers.
#: 30% is a moderate assumption for a 1-in-4-to-7 event; edit to test others.
DEFAULT_LOADING = 0.30
#: Use the trend-adjusted history only when the trend is this significant.
TREND_P_VALUE = 0.10
#: Default risk aversion when the user hasn't measured theirs.
DEFAULT_GAMMA = 3.0
#: Look for a Kalshi market within this distance.
MARKET_RADIUS_KM = 250.0

#: Kalshi snow-linked series with a location (see kalshi_client INDUSTRIES),
#: and what each settles on — which matters as much as where it is.
KALSHI_SNOW_MARKETS = [
    ("KXASPSNOWM", "Aspen monthly snowfall", 39.19, -106.82, "one month's snowfall"),
    ("KXDENSNOWM", "Denver monthly snowfall", 39.74, -104.99, "one month's snowfall"),
    ("KXKEYSTONEOPEN", "Keystone opening date", 39.60, -105.95, "the opening date"),
    ("KXBEAVEROPEN", "Beaver Creek opening date", 39.60, -106.52, "the opening date"),
    ("KXNORTHSTARSNOW", "Northstar (Tahoe) season snowfall", 39.27, -120.12, "season snowfall"),
    ("KXNORTHSTAROPEN", "Northstar opening date", 39.27, -120.12, "the opening date"),
    ("KXHEAVENLYOPEN", "Heavenly opening date", 38.94, -119.94, "the opening date"),
    ("KXSIERRAOPEN", "Sierra-at-Tahoe opening date", 38.80, -120.08, "the opening date"),
    ("KXSTOWEOPEN", "Stowe opening date", 44.53, -72.78, "the opening date"),
]


# ------------------------------------------------------------------- results
@dataclass
class SeasonRow:
    season: int     # year the season starts
    cm: float
    bad: bool


@dataclass
class Probability:
    estimate: float       # chance next season is "bad"
    low: float            # 90% range
    high: float
    historical: float     # plain share of past seasons that were bad
    trend_cm_per_decade: float
    trend_p_value: float
    trend_used: bool
    n_seasons: int


@dataclass
class NearbyMarket:
    ticker: str
    title: str
    distance_km: float
    #: correlation of season snowfall at the market's location with this place's
    correlation: float | None
    #: what the market pays on ("one month's snowfall", "the opening date"...)
    settles_on: str = ""


@dataclass
class Quote:
    place: dict
    business: str
    business_label: str
    revenue: float
    reserves: float
    wealth: float              # the cushion: reserves + a normal season's profit
    gamma: float
    history: list[SeasonRow]
    normal_cm: float
    trigger_cm: float
    trigger_rule: str          # "80% of normal" or "worst 25% of seasons"
    probability: Probability
    avg_shortfall: float       # average % below normal in bad seasons
    loss: float                # estimated revenue lost in a bad season
    elasticity: float
    basis: float
    fair_price: float          # per $1 of protection
    loaded_price: float
    loading: float
    protection: float          # $ paid out in a bad season (= contracts)
    cost_fair: float
    cost_loaded: float
    plan: dict                 # ContractHedgePlan.to_dict() at the loaded price
    nearby_market: NearbyMarket | None
    #: protection the user would want if the contract always paid in their
    #: bad seasons (basis 1.0) — the gap to `protection` is basis risk
    protection_if_perfect: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------------------------------------------- the math
def bad_season_probability(
    totals: pd.Series, trigger_cm: float, current_season: int
) -> tuple[Probability, np.ndarray]:
    """Chance next season falls below ``trigger_cm``, and the sample used.

    Returns the probability summary and the (possibly trend-adjusted)
    season totals it was computed from.
    """
    years = totals.index.to_numpy(dtype=float)
    x = totals.to_numpy(dtype=float)
    n = len(x)
    if n < 10:
        raise ValueError("need at least 10 seasons of history to price this")
    historical = float(np.mean(x < trigger_cm))
    fit = stats.linregress(years, x)
    trend_used = bool(fit.pvalue < TREND_P_VALUE)
    if trend_used:
        # Keep each season's deviation from the trend, but re-centre it on
        # where the trend line is for the coming season.
        sample = x + fit.slope * (current_season - years)
        sample = np.maximum(sample, 0.0)
    else:
        sample = x
    k = int(np.sum(sample < trigger_cm))
    # Jeffreys Beta(k + 1/2, n - k + 1/2) posterior: honest about small n.
    post = stats.beta(k + 0.5, n - k + 0.5)
    prob = Probability(
        estimate=float(post.mean()), low=float(post.ppf(0.05)), high=float(post.ppf(0.95)),
        historical=historical, trend_cm_per_decade=float(fit.slope * 10),
        trend_p_value=float(fit.pvalue), trend_used=trend_used, n_seasons=n,
    )
    return prob, sample


def estimated_loss(
    sample: np.ndarray, normal_cm: float, trigger_cm: float, revenue: float, biz: Business,
    elasticity: float,
) -> tuple[float, float]:
    """(revenue lost in a typical bad season, average % shortfall)."""
    bad = sample[sample < trigger_cm]
    if len(bad) == 0 or normal_cm <= 0:
        return 0.0, 0.0
    shortfall = float(np.mean(np.clip((normal_cm - bad) / normal_cm, 0.0, 1.0)))
    loss = min(revenue * elasticity * shortfall, revenue * biz.max_loss_frac)
    return float(loss), shortfall


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_market(place: Place, totals: pd.Series, biz: Business, today: date | None, session: Any) -> NearbyMarket | None:
    """The closest Kalshi snow market, and how well its location tracks this one."""
    best = min(KALSHI_SNOW_MARKETS, key=lambda m: _km(place.latitude, place.longitude, m[2], m[3]))
    dist = _km(place.latitude, place.longitude, best[2], best[3])
    if dist > MARKET_RADIUS_KM:
        return None
    corr = None
    try:
        there = snowfall_history(
            Place(best[1], "", "", best[2], best[3]), *biz.season, today=today, session=session
        )
        both = pd.concat([totals, there], axis=1, join="inner").dropna()
        if len(both) >= 10:
            corr = float(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1])
    except Exception:
        corr = None
    return NearbyMarket(best[0], best[1], round(dist, 1), corr, best[4])


# ------------------------------------------------------------------- quote
def quote(
    business: str,
    place: str | Place,
    revenue: float,
    reserves: float | None = None,
    gamma: float | None = None,
    trigger_fraction: float | None = DEFAULT_TRIGGER_FRACTION,
    trigger_percentile: float | None = None,
    margin: float | None = None,
    basis: float | None = None,
    loading: float = DEFAULT_LOADING,
    today: date | None = None,
    session: Any | None = None,
) -> Quote:
    """Everything a user needs to see, from three inputs."""
    if business not in BUSINESSES:
        raise ValueError(f"unknown business type {business!r}; choose from {sorted(BUSINESSES)}")
    if not revenue > 0:
        raise ValueError("revenue must be positive")
    if trigger_percentile is not None and not 0.05 <= trigger_percentile <= 0.5:
        raise ValueError("trigger percentile must be between 5% and 50%")
    if trigger_percentile is None and not 0.3 <= (trigger_fraction or 0) <= 0.95:
        raise ValueError("trigger fraction must be between 30% and 95% of normal")
    biz = BUSINESSES[business]
    if isinstance(place, str):
        found = geocode(place, count=1, session=session)
        if not found:
            raise ValueError(f"Couldn't find a place called '{place}'.")
        place = found[0]
    today = today or date.today()
    gamma = DEFAULT_GAMMA if gamma is None else float(gamma)
    reserves = revenue * biz.reserves_frac if reserves is None else float(reserves)
    margin = biz.margin if margin is None else float(margin)
    if not 0.0 < margin <= 1.0:
        raise ValueError("profit margin must be between 0% and 100%")
    if basis is not None and not 0.0 <= float(basis) <= 1.0:
        raise ValueError("basis correlation must be between 0 and 1")

    region = region_of(place.latitude, place.longitude)
    elasticity = biz.elasticity_for(region)
    basis = biz.basis_for(region) if basis is None else float(basis)
    totals = snowfall_history(place, *biz.season, today=today, session=session)
    if len(totals) < 10:
        raise ValueError("Not enough snowfall history at this location to price a season.")
    normal = float(totals.median())
    if trigger_percentile is not None:
        trigger = float(totals.quantile(trigger_percentile))
        rule = f"worst {trigger_percentile:.0%} of seasons"
    else:
        trigger = normal * float(trigger_fraction)
        rule = f"{trigger_fraction:.0%} of normal"
    # The season about to start (or under way) is labelled by its start year.
    current = today.year if today.month >= biz.season[0] else today.year - 1
    prob, sample = bad_season_probability(totals, trigger, current + (0 if today.month >= biz.season[0] else 1))
    loss, shortfall = estimated_loss(sample, normal, trigger, revenue, biz, elasticity)

    p = float(np.clip(prob.estimate, 0.02, 0.95))
    loaded = float(min(p * (1.0 + loading), 0.97))
    # What the owner actually has to absorb a bad season with.
    wealth = reserves + revenue * margin
    loss_used = min(loss, wealth * 0.95)

    def size(rho: float):
        return hedge_income(IncomeExposure(
            wealth=wealth, loss=loss_used, price=loaded, market_prob=p,
            gamma=gamma, basis_correlation=rho, fee_multiplier=0.0,
            allow_selling=False,  # a customer can only buy protection
            # Hone sets this price itself, so there's no slippage to allow for;
            # and "a contract that always paid" really does track perfectly.
            price_buffer=0.0, basis_shrink=1.0 if rho >= 1.0 else BASIS_SHRINK,
        ))

    plan = size(basis)
    perfect = size(1.0) if basis < 1.0 else plan
    contracts = max(plan.contracts, 0)

    warnings: list[str] = []
    if loss > wealth * 0.95:
        warnings.append(
            f"A typical bad season could cost about ${loss:,.0f} — more than your cushion of "
            f"${wealth:,.0f} (reserves plus a normal season's profit). Hone sized protection "
            "as if the loss stopped there; in reality you'd need outside funding."
        )
    if perfect.contracts > 0 and contracts < 0.6 * perfect.contracts:
        warnings.append(
            f"With a contract that always paid in your bad seasons you'd want about "
            f"${perfect.contracts:,.0f} of protection. This one tracks your revenue with "
            f"correlation {basis:.1f}, so a bad season could come without a payout — and then "
            "every dollar spent on it is a dollar less to get through. That's why Hone "
            f"suggests ${contracts:,.0f}. A contract settled closer to your own conditions "
            "(e.g. your resort's own snow station) would let you protect more."
        )
    # Liquidity is irrelevant when Hone sets the price itself.
    warnings += [w for w in plan.warnings if "couldn't check how many" not in w]
    market = nearest_market(place, totals, biz, today, session)

    assumptions = [
        f"A bad season is below {trigger:,.0f} cm here ({rule}); {prob.historical:.0%} of the {prob.n_seasons} seasons since {totals.index.min()} were that bad.",
        f"Revenue falls {elasticity:.2f}% for every 1% of snowfall below normal ({normal:,.0f} cm), capped at {biz.max_loss_frac:.0%} — "
        + (f"the published range for ski resorts in this region ({region})" if biz.fixed_elasticity is None and biz.elasticity_scale == 1.0
           else "set directly for this business" if biz.fixed_elasticity is not None
           else f"{biz.elasticity_scale:g}x the ski-resort figure for this region ({region}); no published data exists for this business type, so treat it as an estimate")
        + ".",
        f"A contract on this place's snowfall tracks your revenue with correlation {basis:.1f} (snowmaking and the economy matter too).",
        f"Cushion for a bad season: ${reserves:,.0f} cash reserves plus a normal season's profit of ${revenue * margin:,.0f} ({margin:.0%} of ${revenue:,.0f} revenue); risk aversion {gamma:g}.",
        "Snowfall data is ERA5 reanalysis (~25 km grid): it understates mountain snow, so only comparisons within this place's own history are used. A real contract would settle on a named weather station.",
    ]
    if prob.trend_used:
        assumptions.append(
            f"Snowfall here has a trend of {prob.trend_cm_per_decade:+,.0f} cm per decade, so past seasons were adjusted to today's level."
        )

    return Quote(
        place={"label": place.label, "latitude": place.latitude, "longitude": place.longitude, "elevation": place.elevation},
        business=business, business_label=biz.label, revenue=float(revenue), reserves=float(reserves), gamma=gamma,
        history=[SeasonRow(int(y), float(v), bool(v < trigger)) for y, v in totals.items()],
        normal_cm=normal, trigger_cm=trigger, trigger_rule=rule, wealth=float(wealth),
        probability=prob, avg_shortfall=shortfall, loss=loss, elasticity=elasticity, basis=basis,
        fair_price=p, loaded_price=loaded, loading=loading,
        protection=float(contracts), cost_fair=float(contracts * p), cost_loaded=float(contracts * loaded),
        plan=plan.to_dict(), nearby_market=market,
        protection_if_perfect=float(max(perfect.contracts, 0)),
        assumptions=assumptions, warnings=warnings,
    )
