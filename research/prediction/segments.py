"""Who does the income hedge help, and by how much? A segment simulator.

Hone Markets sizes an event-contract hedge for one person. This module runs
that sizing for *many* people — every combination of occupation, savings,
risk aversion, belief and market depth — and then checks the advice
against simulated reality, so we can see which groups it serves well and
where it misleads.

Three layers:

1. **Personas** (:func:`personas`): one row per person. Each occupation
   (``OCCUPATIONS``) says what income is at risk, which Kalshi market is
   the closest proxy, how tightly that market tracks the person's own loss
   (basis correlation), and how deep the market is (from live Kalshi data,
   November 2026).
2. **Advice** (:func:`advise`): what Hone recommends for a persona —
   ``hone.prediction.hedge.hedge_income`` with the liquidity cap.
3. **Reality check** (:func:`realized`): simulate many seasons from a
   *true world* that can differ from the model's assumptions (the person's
   loss probability isn't the event's, the basis is weaker than believed,
   their view is miscalibrated...). Report the certainty-equivalent gain
   the advice actually delivers under the truth. Positive = the hedge
   helped this person, at their own risk aversion.

Run it:

    python research/prediction/segments.py            # summary by segment
    python research/prediction/segments.py --out x.csv

Everything is a model; numbers are illustrative of *relative* effects
across groups, not forecasts for any real person. To add a group, add an
entry to ``OCCUPATIONS``. To change what's swept, edit ``GRID``.
"""

from __future__ import annotations

import argparse
import itertools
import math
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from hone.prediction.hedge import IncomeExposure, crra_utility, crra_inverse, hedge_income, joint_states
from hone.prediction.liquidity import Liquidity


# ---------------------------------------------------------------- groups
@dataclass(frozen=True)
class Occupation:
    key: str
    label: str
    income: float          # yearly / seasonal income at stake, dollars
    loss_frac: float       # share of income lost in a bad season
    basis: float           # how tightly the proxy market tracks *their* loss (0-1)
    market: str            # closest Kalshi series
    price: float           # typical ask for the protective side
    open_interest: float   # typical open interest (contracts), live Nov 2026
    depth: float           # contracts on offer within 3¢ of best price, live Nov 2026


#: Occupations and their closest markets. Liquidity figures come from live
#: Kalshi data (Nov 2026: the biggest open market priced 5–60¢ in each
#: series). Income and loss figures are round, plausible values for the
#: group, not survey data — change them to test other assumptions.
OCCUPATIONS = [
    Occupation("rideshare", "Rideshare / delivery driver (fuel costs)", 45_000, 0.10, 0.85,
               "KXAAAGASM", 0.48, 30_861, 13_873),
    Occupation("retiree", "Retiree on fixed income (inflation)", 40_000, 0.06, 0.90,
               "KXCPIYOY", 0.35, 57_385, 6_866),
    Occupation("contractor", "Contract worker (unemployment risk)", 70_000, 0.50, 0.30,
               "KXU3MAX", 0.10, 10_668, 10_033),
    Occupation("realtor", "Real-estate agent / mortgage broker (rates)", 80_000, 0.40, 0.50,
               "KX30YMORTW", 0.42, 723, 1_044),
    Occupation("ad_freelancer", "Ad / media freelancer (ad budgets)", 60_000, 0.30, 0.40,
               "KXSTREAMINGADS", 0.18, 3_860, 161),
    Occupation("ski", "Ski instructor / mountain town (snowfall)", 35_000, 0.35, 0.60,
               "KXDENSNOWM", 0.49, 138, 25),
    Occupation("recruiter", "Recruiter (payroll growth)", 75_000, 0.35, 0.45,
               "KXPAYROLLS", 0.28, 408, 241),
    Occupation("tech", "Tech worker (layoffs)", 150_000, 0.50, 0.15,
               "KXTECHLAYOFF", 0.52, 19, 200),
]

#: What's swept for every occupation. Edit freely; the run time grows with
#: the product of the list lengths.
GRID = {
    "savings_months": [0, 3, 12],           # emergency fund, in months of income
    "gamma": [0.5, 2.0, 4.0, 8.0],          # risk aversion (Hone tiers span ~0-10)
    "belief": ["market", "pessimist", "optimist"],
    "liquidity": ["capped", "uncapped"],
}

#: How a belief maps to (own probability shift, confidence). "pessimist"
#: thinks the bad event is likelier than the market says.
BELIEFS = {
    "market": (0.0, 0.0),
    "pessimist": (+0.15, 0.6),
    "optimist": (-0.15, 0.6),
}


def personas(occupations=OCCUPATIONS, grid=GRID) -> list[dict]:
    rows = []
    for occ in occupations:
        for months, gamma, belief, liq in itertools.product(
            grid["savings_months"], grid["gamma"], grid["belief"], grid["liquidity"]
        ):
            rows.append({"occupation": occ, "savings_months": months, "gamma": gamma,
                         "belief": belief, "liquidity": liq})
    return rows


# ---------------------------------------------------------------- advice
def exposure_for(p: dict) -> IncomeExposure:
    occ: Occupation = p["occupation"]
    wealth = occ.income * (1 + p["savings_months"] / 12)
    shift, conf = BELIEFS[p["belief"]]
    own = None if conf == 0 else float(np.clip(occ.price + shift, 0.02, 0.98))
    liquidity = None
    if p["liquidity"] == "capped":
        asks = [(occ.price, occ.depth)]  # flat book at the quoted price
        liquidity = Liquidity(open_interest=occ.open_interest, asks_buy=asks,
                              asks_sell=[(1 - occ.price, occ.depth)])
    return IncomeExposure(
        wealth=wealth, loss=occ.income * occ.loss_frac, price=occ.price, gamma=p["gamma"],
        market_prob=occ.price, own_prob=own, confidence=conf,
        basis_correlation=occ.basis, liquidity=liquidity,
    )


def advise(p: dict):
    return hedge_income(exposure_for(p))


# --------------------------------------------------------- reality check
@dataclass(frozen=True)
class Truth:
    """How the world actually works, which may differ from the model.

    ``q_event``/``q_loss`` default to the market price (market is right);
    ``rho`` defaults to the occupation's basis (basis is right).
    """

    q_event: float | None = None
    q_loss: float | None = None
    rho: float | None = None


def realized(p: dict, plan, truth: Truth = Truth(), n: int = 0) -> dict:
    """Certainty-equivalent gain the advice delivers *under the truth*.

    Exact expectation over the four joint states (n=0), or a Monte Carlo
    with ``n`` seasons when you want sampling noise in the picture.
    """
    exp = exposure_for(p)
    q_e = truth.q_event if truth.q_event is not None else exp.market_prob
    q_l = truth.q_loss if truth.q_loss is not None else q_e
    rho = truth.rho if truth.rho is not None else exp.basis_correlation
    states, _ = joint_states(q_e, q_l, rho)
    k = plan.contracts
    # Realized cost per contract: the fill price if known, else the quote.
    c = plan.avg_fill_price or exp.price
    cost_each = c if k >= 0 else -(1 - c)  # a sell receives c up front
    fee = plan.fee
    w_un = np.array([exp.wealth - (exp.loss if s.loss else 0) for s in states])
    w_hd = np.array([exp.wealth - (exp.loss if s.loss else 0) + k * ((1 if s.pays else 0) - c) - fee for s in states])
    probs = np.array([s.prob for s in states])
    if n:
        rng = np.random.default_rng(0)
        idx = rng.choice(len(states), size=n, p=probs)
        probs = np.bincount(idx, minlength=len(states)) / n
    if (w_hd <= 0).any() or (w_un <= 0).any():
        return {"ce_gain_true": -math.inf, "ruin": True}
    g = p["gamma"]
    ce = lambda w: crra_inverse(float(np.sum(probs * crra_utility(w, g))), g)
    return {
        "ce_gain_true": ce(w_hd) - ce(w_un),
        "ruin": False,
        "worst_unhedged": float(w_un.min()),
        "worst_hedged": float(w_hd.min()),
        "p_lose_money_on_hedge": float(np.sum(probs[[i for i, s in enumerate(states) if not s.pays]])) if k > 0 else 0.0,
    }


# ------------------------------------------------------------------ run
def run(personas_list=None, truth_fn=None) -> pd.DataFrame:
    """One row per persona: the advice and what it's worth under the truth.

    ``truth_fn(persona) -> Truth`` sets the true world per persona; default
    is "the model's assumptions are right".
    """
    rows = []
    for p in personas_list or personas():
        occ: Occupation = p["occupation"]
        plan = advise(p)
        truth = truth_fn(p) if truth_fn else Truth()
        real = realized(p, plan, truth)
        rows.append({
            "occupation": occ.key, "market": occ.market, "savings_months": p["savings_months"],
            "gamma": p["gamma"], "belief": p["belief"], "liquidity": p["liquidity"],
            "income": occ.income, "loss": occ.income * occ.loss_frac,
            "contracts_wanted": plan.contracts_wanted, "contracts": plan.contracts,
            "coverage": plan.coverage, "direction": plan.direction,
            "cost": plan.cost, "cost_pct_income": plan.cost / occ.income,
            "ce_gain_model": plan.ce_gain, "ce_gain_model_pct": plan.ce_gain / occ.income,
            "ce_gain_true": real["ce_gain_true"], "ce_gain_true_pct": real["ce_gain_true"] / occ.income,
            "worst_unhedged": plan.worst_unhedged, "worst_hedged": plan.worst_hedged,
            "n_warnings": len(plan.warnings),
            "sell": plan.direction == "sell" and plan.contracts != 0,
            "over_reservation": plan.price > plan.reservation_price and plan.contracts > 0,
        })
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame) -> pd.DataFrame:
    """The headline table: per occupation, with the cap on and beliefs = market."""
    base = df[(df.liquidity == "capped") & (df.belief == "market")]
    return base.groupby("occupation").agg(
        loss=("loss", "first"), market=("market", "first"),
        coverage=("coverage", "median"),
        contracts=("contracts", "median"),
        ce_gain_median=("ce_gain_true", "median"),
        ce_gain_pct_income=("ce_gain_true_pct", "median"),
        uncapped_would_be=("contracts_wanted", "median"),
    ).sort_values("coverage", ascending=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write every persona row to this CSV")
    args = ap.parse_args()
    df = run()
    pd.set_option("display.width", 160)
    print(f"{len(df)} personas\n")
    print(summary(df).to_string(float_format=lambda x: f"{x:,.3f}"))
    if args.out:
        df.to_csv(args.out, index=False)
        print(f"\nwrote {args.out}")
