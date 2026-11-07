"""Does the income-hedge advice still help when the model's assumptions are wrong?

``hone.prediction.hedge.hedge_income`` sizes a binary contract against an
income loss under a model world: the person's loss probability equals the
contract's probability, the basis correlation is known, the user's view is
as good as their stated confidence, the price is the true probability (up
to their view), the contract settles on the same period as the loss, and
the order fills at the quote. This script breaks those assumptions one at
a time and jointly, scores the *unchanged* advice under the true world with
``segments.realized``, and then evaluates candidate model changes, each
implemented here as a wrapper around ``hedge_income`` (nothing under
``hone/`` is modified).

Run from the repo root:

    python research/prediction/misspecification.py             # full run, markdown tables
    python research/prediction/misspecification.py --draws 10  # faster
    python research/prediction/misspecification.py --out DIR   # also write per-case CSVs

All numbers are certainty-equivalent (CE) dollars at the persona's own
gamma, exact expectations over the four joint states (no sampling noise
except where a scenario draws random users or worlds; seeds are fixed).
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (str(ROOT), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import segments as S  # noqa: E402
from hone.prediction import hedge as H  # noqa: E402
from hone.prediction.contracts import kalshi_fee  # noqa: E402
from hone.prediction.liquidity import average_fill, limit_for  # noqa: E402

TOL = 0.005  # dollars; a realized CE gain below -TOL counts as "the hedge hurt"
Q_MAX = 0.95  # ceiling on any true probability we construct


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# ======================================================================
# Plans: re-pricing an arbitrary position exactly the way hedge_income does
# ======================================================================
def model_belief(exp: H.IncomeExposure) -> float:
    mp = exp.market_prob if exp.market_prob is not None else exp.price
    return H.blend_belief(mp, exp.own_prob, exp.confidence)


def finalize(exp: H.IncomeExposure, n_star: float, states) -> SimpleNamespace:
    """Whole-contract position, liquidity cap, fill price, fee and model CE gain
    for a continuous target ``n_star`` — the tail of ``hedge_income``, so a
    wrapper can change *how much* is bought without re-implementing the rest.
    ``states`` is the joint distribution the wrapper believes (for ce_gain)."""
    lo, hi = H._bounds(exp)  # a wrapper may target a size that is insolvent at the real price
    contracts = int(round(float(np.clip(n_star, lo, hi))))
    wanted = contracts
    lim = limit_for(exp.liquidity, buying=contracts >= 0)
    if lim.limit is not None and abs(contracts) > lim.limit:
        contracts = int(math.copysign(lim.limit, contracts)) if lim.limit > 0 else 0
    avg_fill = None
    if exp.liquidity is not None and contracts != 0:
        asks = exp.liquidity.asks_buy if contracts > 0 else exp.liquidity.asks_sell
        other = average_fill(asks or [], abs(contracts))
        if other is not None:
            avg_fill = other if contracts > 0 else 1.0 - other
    fill = replace(exp, price=avg_fill) if avg_fill is not None and 0 < avg_fill < 1 else exp
    w_un, probs = H._wealth(exp, states, 0.0, smooth_fee=False)
    w_hd, _ = H._wealth(fill, states, float(contracts), smooth_fee=False)
    fee = kalshi_fee(abs(contracts), fill.price, exp.fee_multiplier, exp.fee_rate)
    ce_un = H.crra_certainty_equivalent(w_un, probs, exp.gamma)
    ce_hd = H.crra_certainty_equivalent(w_hd, probs, exp.gamma)
    return SimpleNamespace(
        n_star=n_star, contracts=contracts, contracts_wanted=wanted,
        avg_fill_price=avg_fill, fee=float(fee if contracts else 0.0),
        ce_gain=ce_hd - ce_un, direction="buy" if contracts >= 0 else "sell",
    )


def executed(plan, exp: H.IncomeExposure, slip: float):
    """The plan as actually filled ``slip`` dollars worse than the price it was sized at."""
    if slip == 0 or plan.contracts == 0:
        return plan
    c = plan.avg_fill_price or exp.price
    c = c + slip if plan.contracts > 0 else c - slip  # a sell receives less
    c = float(np.clip(c, 0.005, 0.995))
    fee = kalshi_fee(abs(plan.contracts), c, exp.fee_multiplier, exp.fee_rate)
    return SimpleNamespace(contracts=plan.contracts, avg_fill_price=c, fee=fee)


# ======================================================================
# Candidate model changes (wrappers around hedge_income)
# ======================================================================
def baseline(exp, case):
    return H.hedge_income(exp)


def shrink_basis(lam):
    """Size with basis_correlation * lam (the model believes a weaker basis)."""
    def f(exp, case):
        return H.hedge_income(replace(exp, basis_correlation=exp.basis_correlation * lam))
    f.__name__ = f"shrink_basis({lam})"
    return f


def haircut(h):
    """Buy h * n_star (fractional-Kelly-style haircut on the whole position)."""
    def f(exp, case):
        plan = H.hedge_income(exp)
        b = model_belief(exp)
        states, _ = H.joint_states(b, b, exp.basis_correlation)
        return finalize(exp, h * plan.n_star, states)
    f.__name__ = f"haircut({h})"
    return f


def two_prob(oracle=False):
    """Separate q_loss input: size on joint_states(belief, q_loss, rho).
    The user supplies q_loss (``case['q_loss_est']``, a noisy estimate of the
    true loss probability); ``oracle`` uses the true value (upper bound)."""
    def f(exp, case):
        exp.validate()
        b = model_belief(exp)
        ql = case["truth"].q_loss if oracle else case["q_loss_est"]
        ql = float(np.clip(ql, 0.005, Q_MAX))
        states, _ = H.joint_states(b, ql, exp.basis_correlation)
        n = H.optimal_contracts(exp, states) if exp.loss > 0 else H.hedge_income(exp).n_star
        return finalize(exp, n, states)
    f.__name__ = "two_prob(oracle)" if oracle else "two_prob(user q_loss)"
    return f


def cap_tilt(tau):
    """No selling when there is exposure, and the speculative tilt capped at
    +tau * pure hedge: n in [0, (1 + tau) * rho * L]."""
    def f(exp, case):
        plan = H.hedge_income(replace(exp, allow_selling=exp.loss == 0))
        if exp.loss <= 0:
            return plan
        b = model_belief(exp)
        states, _ = H.joint_states(b, b, exp.basis_correlation)
        n = float(np.clip(plan.n_star, 0.0, (1 + tau) * plan.pure_hedge_contracts))
        return finalize(exp, n, states)
    f.__name__ = f"cap_tilt({tau})"
    return f


def min_gain(frac_wealth, floor=0.0):
    """Recommend nothing unless the model's CE gain >= max(floor, frac * wealth)."""
    def f(exp, case, inner=None):
        plan = (inner or baseline)(exp, case)
        if plan.ce_gain < max(floor, frac_wealth * exp.wealth):
            return SimpleNamespace(n_star=0.0, contracts=0, contracts_wanted=0,
                                   avg_fill_price=None, fee=0.0, ce_gain=0.0, direction="buy")
        return plan
    f.__name__ = f"min_gain({frac_wealth:.2%} of wealth)"
    return f


def price_buffer(delta):
    """Size as if the contract cost ``delta`` more than quoted (belief stays at
    the market price): a margin for price bias, slippage and the fee. The
    position is then bought at the real quote."""
    def f(exp, case):
        if exp.loss <= 0:
            return H.hedge_income(exp)
        mp = exp.market_prob if exp.market_prob is not None else exp.price
        padded = replace(exp, price=float(min(exp.price + delta, 0.99)), market_prob=mp)
        plan = H.hedge_income(padded)
        b = model_belief(exp)
        states, _ = H.joint_states(b, b, exp.basis_correlation)
        return finalize(exp, plan.n_star, states)
    f.__name__ = f"price_buffer({delta})"
    return f


def margin_gate(cents, inner=None):
    """Recommend nothing unless the model CE gain >= ``cents`` per contract:
    the hedge must survive the price being that many cents too high."""
    def f(exp, case):
        plan = (inner or baseline)(exp, case)
        if plan.contracts and plan.ce_gain < cents * abs(plan.contracts):
            return SimpleNamespace(n_star=0.0, contracts=0, contracts_wanted=0,
                                   avg_fill_price=None, fee=0.0, ce_gain=0.0, direction="buy")
        return plan
    f.__name__ = (f"{inner.__name__}+" if inner else "") + f"margin_gate({cents})"
    return f


def view_shrink(k_mult):
    """Multiply the user's stated confidence by k_mult before blending."""
    def f(exp, case):
        return H.hedge_income(replace(exp, confidence=exp.confidence * k_mult))
    f.__name__ = f"view_shrink({k_mult})"
    return f


def robust(rho_f=(0.5, 1.0), q_loss_m=(0.5, 1.0, 2.0), dq=(0.0, 0.02)):
    """Max-min sizing: choose n >= 0 maximizing the *worst* CE gain over a
    small set of worlds (basis x rho_f, q_loss = m * q_event, the contract
    overpriced by dq). Never buys unless every world in the set gains."""
    def f(exp, case):
        exp.validate()
        if exp.loss <= 0:
            return H.hedge_income(exp)
        b = model_belief(exp)
        worlds = []
        for fr in rho_f:
            for m in q_loss_m:
                for d in dq:
                    qe = float(np.clip(b - d, 0.01, 0.99))
                    ql = float(np.clip(m * qe, 0.005, Q_MAX))
                    worlds.append(H.joint_states(qe, ql, fr * exp.basis_correlation)[0])
        g = exp.gamma
        ce0 = [H.crra_inverse(H._expected_utility(exp, st, 0.0), g) for st in worlds]

        def worst(n):
            return min(H.crra_inverse(H._expected_utility(exp, st, n), g) - c0
                       for st, c0 in zip(worlds, ce0))

        _, hi = H._bounds(exp)
        res = minimize_scalar(lambda n: -worst(n), bounds=(0.0, hi), method="bounded",
                              options={"xatol": 1e-3})
        n = float(res.x) if worst(float(res.x)) > 0 else 0.0
        states, _ = H.joint_states(b, b, exp.basis_correlation)
        return finalize(exp, n, states)
    f.__name__ = "robust_maxmin"
    return f


def shrink_then(lam, inner):
    """Run ``inner`` with the basis shrunk by lam."""
    def f(exp, case):
        return inner(replace(exp, basis_correlation=exp.basis_correlation * lam), case)
    f.__name__ = f"{inner.__name__}+shrink({lam})"
    return f


def gated(inner, frac_wealth):
    g = min_gain(frac_wealth)

    def f(exp, case):
        return g(exp, case, inner=inner)
    f.__name__ = f"{inner.__name__}+min_gain({frac_wealth:.2%})"
    return f


# ======================================================================
# Scenarios: (model exposure, true world, slippage, user's q_loss estimate)
# ======================================================================
def base_personas(belief="market"):
    return [p for p in S.personas() if p["belief"] == belief]


def _case(p, assumption, level, truth, exp=None, slip=0.0, q_loss_est=None, rng=None, **extra):
    occ = p["occupation"]
    exp = exp or S.exposure_for(p)
    if q_loss_est is None:
        # what a user would type for "how likely is a bad season for YOU":
        # the true value, mis-estimated by ~35% (lognormal)
        q_loss_est = float(np.clip(truth.q_loss * math.exp(rng.normal(0, 0.35)), 0.005, Q_MAX))
    return dict(
        p=p, exp=exp, truth=truth, slip=slip, q_loss_est=q_loss_est,
        assumption=assumption, level=level, occupation=occ.key, gamma=p["gamma"],
        savings_months=p["savings_months"], liquidity=p["liquidity"],
        income=occ.income, loss=occ.income * occ.loss_frac,
        wealth=occ.income * (1 + p["savings_months"] / 12), **extra,
    )


def scen_right(rng):
    return [_case(p, "0 model right", "right",
                  S.Truth(p["occupation"].price, p["occupation"].price, p["occupation"].basis), rng=rng)
            for p in base_personas()]


A1_LEVELS = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0]


def scen_qloss(rng, levels=A1_LEVELS):
    out = []
    for m in levels:
        for p in base_personas():
            o = p["occupation"]
            out.append(_case(p, "1 q_loss != q_event", f"q_loss = {m:g} x q_event",
                             S.Truth(o.price, min(m * o.price, Q_MAX), o.basis), rng=rng, x=m))
    return out


A2_LEVELS = [0.6, 0.5, 0.4, 0.3, 0.2, 0.1]


def scen_basis_guess(rng, levels=A2_LEVELS, guess=0.6):
    out = []
    for r in levels:
        for p in base_personas():
            o = p["occupation"]
            p2 = dict(p, occupation=replace(o, basis=guess))
            out.append(_case(p2, "2 basis overestimated", f"model {guess}, true {r:g}",
                             S.Truth(o.price, o.price, r), rng=rng, x=r))
    return out


A3_SIGMA = {"sharp (sd 0.3)": 0.3, "average (sd 0.6)": 0.6, "poor (sd 1.2)": 1.2}
A3_CONF = [0.0, 0.3, 0.6, 0.9]
SIGMA_MARKET = 0.3  # logit sd of the market's error around the true probability


def scen_beliefs(rng, draws=30, biases=(0.0, 0.4)):
    """Users with private views. True probability = market price + logit noise
    (sd 0.3, unbiased). The user's own_prob = true + logit noise (sd sigma_u)
    + a systematic bias (0, or +0.4 logit = habitual pessimist). Hone blends
    it at the user's stated confidence. A Bayes-optimal weight on the view
    would be w* = 0.3^2/(0.3^2+sigma_u^2): 0.50 / 0.20 / 0.06."""
    out = []
    for bias in biases:
        for sname, su in A3_SIGMA.items():
            for k in A3_CONF:
                if k == 0.0 and (sname != "average (sd 0.6)"):
                    continue  # no view: sigma_u irrelevant, one reference row
                for p in base_personas():
                    o = p["occupation"]
                    for _ in range(draws):
                        lt = logit(o.price) + rng.normal(0, SIGMA_MARKET)
                        qt = float(np.clip(sigmoid(lt), 0.01, Q_MAX))
                        own = float(np.clip(sigmoid(lt + bias + rng.normal(0, su)), 0.02, 0.98))
                        exp = S.exposure_for(p)
                        if k > 0:
                            exp = replace(exp, own_prob=own, confidence=k)
                        lvl = (f"no view" if k == 0 else f"{sname}, conf {k}")
                        if bias:
                            lvl += f", bias +{bias}"
                        out.append(_case(p, "3 miscalibrated beliefs", lvl,
                                         S.Truth(qt, qt, o.basis), exp=exp, rng=rng,
                                         x=k, sigma_u=su if k else 0.0, bias=bias))
    return out


A4_LEVELS = [("price 1c over true", -0.01), ("price 2c over true", -0.02),
             ("price 3c over true", -0.03), ("price 5c over true", -0.05),
             ("price 3c under true", +0.03),
             ("FLB beta=1.15", ("flb", 1.15)), ("FLB beta=1.30", ("flb", 1.30))]


def scen_price_bias(rng, levels=A4_LEVELS):
    out = []
    for name, spec in levels:
        for p in base_personas():
            o = p["occupation"]
            if isinstance(spec, tuple):
                qt = float(sigmoid(spec[1] * logit(o.price)))
            else:
                qt = o.price + spec
            qt = float(np.clip(qt, 0.005, Q_MAX))
            out.append(_case(p, "4 market-price bias", name, S.Truth(qt, qt, o.basis),
                             rng=rng, x=qt - o.price))
    return out


A5_LEVELS = [1.0, 0.75, 0.5, 0.25]


def scen_timing(rng, levels=A5_LEVELS):
    out = []
    for f in levels:
        for p in base_personas():
            o = p["occupation"]
            out.append(_case(p, "5 settlement/timing mismatch", f"overlap {f:.0%}",
                             S.Truth(o.price, o.price, o.basis * f), rng=rng, x=f))
    return out


A6_LEVELS = [0.0, 0.01, 0.02, 0.03, 0.05]


def scen_slippage(rng, levels=A6_LEVELS):
    out = []
    for s in levels:
        for p in base_personas():
            o = p["occupation"]
            out.append(_case(p, "6 execution slippage", f"fill {s * 100:.0f}c worse",
                             S.Truth(o.price, o.price, o.basis), slip=s, rng=rng, x=s))
    return out


JOINT = {
    # name: (q_loss/q_event log-uniform range, basis factor range, FLB beta range,
    #        slippage range, share of users with a view)
    "severe": ((0.25, 3.0), (0.3, 1.0), (1.0, 1.3), (0.0, 0.03), 0.5),
    "mild": ((0.5, 2.0), (0.6, 1.0), (1.0, 1.15), (0.0, 0.015), 0.5),
}


def scen_joint(rng, draws=40, severity="severe"):
    """Every assumption wrong at once, each drawn from a range (see JOINT).
    Severe: q_loss/q_event log-uniform on [0.25, 3]; true basis = default x
    U[0.3, 1] (overestimate and/or settlement mismatch); true q_event from a
    favourite-longshot curve with beta ~ U[1, 1.3] plus unbiased market noise
    (logit sd 0.2); fill 0-3c worse; half of users state a view (logit sd
    0.6 around the truth, conf 0.3/0.6/0.9). Mild halves most ranges."""
    (m_lo, m_hi), (f_lo, f_hi), (b_lo, b_hi), (s_lo, s_hi), view_share = JOINT[severity]
    out = []
    for p in base_personas():
        o = p["occupation"]
        for _ in range(draws):
            m = math.exp(rng.uniform(math.log(m_lo), math.log(m_hi)))
            fr = rng.uniform(f_lo, f_hi)
            beta = rng.uniform(b_lo, b_hi)
            lt = beta * logit(o.price) + rng.normal(0, 0.2)
            qe = float(np.clip(sigmoid(lt), 0.005, Q_MAX))
            ql = float(np.clip(m * qe, 0.005, Q_MAX))
            slip = rng.uniform(s_lo, s_hi)
            exp = S.exposure_for(p)
            k = 0.0
            if rng.random() < view_share:
                k = float(rng.choice([0.3, 0.6, 0.9]))
                own = float(np.clip(sigmoid(lt + rng.normal(0, 0.6)), 0.02, 0.98))
                exp = replace(exp, own_prob=own, confidence=k)
            out.append(_case(p, f"J joint {severity}", f"joint {severity}",
                             S.Truth(qe, ql, o.basis * fr), exp=exp, slip=slip, rng=rng, x=k))
    return out


def scen_right_views(rng):
    """Model exactly right *including* the user's view: Hone's pessimist and
    optimist personas, with the truth equal to their blended belief. This is
    what a cap on the speculative tilt gives up."""
    out = []
    for b in ("pessimist", "optimist"):
        for p in base_personas(b):
            exp = S.exposure_for(p)
            q = model_belief(exp)
            out.append(_case(p, "0 model right (views)", "right", S.Truth(q, q, p["occupation"].basis),
                             exp=exp, rng=rng))
    return out


# ======================================================================
# Evaluation
# ======================================================================
def evaluate(cases, sizer) -> pd.DataFrame:
    rows = []
    for c in cases:
        plan = sizer(c["exp"], c)
        r = S.realized(c["p"], executed(plan, c["exp"], c["slip"]), c["truth"])
        ce_true = r["ce_gain_true"]
        rows.append({
            k: c[k] for k in ("assumption", "level", "occupation", "gamma", "savings_months",
                              "liquidity", "income", "loss", "wealth")
        } | {"x": c.get("x"), "contracts": plan.contracts, "ce_model": plan.ce_gain,
             "ce_true": ce_true, "ruin": r["ruin"]})
    df = pd.DataFrame(rows)
    df["ruin"] = df["ruin"].astype(bool)
    # a ruin (wealth <= 0 in some state) is scored as losing the whole cushion
    df.loc[df.ruin, "ce_true"] = -(df.loc[df.ruin, "wealth"] - df.loc[df.ruin, "loss"])
    df["hurt"] = df.ce_true < -TOL
    df["harm"] = (-df.ce_true).clip(lower=0)
    df["harm_pct"] = df.harm / df.income
    df["material"] = df.harm_pct > 0.001  # hurt by more than 0.1% of income
    return df


def agg(df: pd.DataFrame, by) -> pd.DataFrame:
    def f(g):
        h = g[g.hurt]
        return pd.Series({
            "n": len(g),
            "model CE gain $": g.ce_model.mean(),
            "realized CE gain $": g.ce_true.mean(),
            "realized/model": g.ce_true.sum() / g.ce_model.sum() if g.ce_model.sum() > 0 else np.nan,
            "hurt %": 100 * g.hurt.mean(),
            "hurt >0.1% inc %": 100 * g.material.mean(),
            "harm $ (if hurt)": h.harm.mean() if len(h) else 0.0,
            "harm % inc (if hurt)": 100 * h.harm_pct.mean() if len(h) else 0.0,
            "worst $": g.harm.max(),
            "worst % inc": 100 * g.harm_pct.max(),
        })
    return df.groupby(by, sort=False).apply(f, include_groups=False)


def md(df: pd.DataFrame, fmt=None) -> str:
    """Markdown table (no tabulate dependency)."""
    df = df.reset_index()
    fmt = fmt or {}

    def cell(col, v):
        if isinstance(v, (float, np.floating)):
            if np.isnan(v):
                return "–"
            f = fmt.get(col)
            if f:
                return f.format(v)
            if "%" in col or "/" in col:
                return f"{v:,.1f}" if "/" not in col else f"{v:.2f}"
            return f"{v:,.0f}" if abs(v) >= 10 else f"{v:,.2f}"
        return str(v)
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(cell(c, r[c]) for c in cols) + " |")
    return "\n".join(out)


def section(title, df, by_level=True):
    print(f"\n### {title}\n")
    unc = df[df.liquidity == "uncapped"]
    cap = df[df.liquidity == "capped"]
    if by_level:
        t = agg(unc, "level")
        t["hurt % (capped)"] = agg(cap, "level")["hurt %"]
        t["harm $ (capped, if hurt)"] = agg(cap, "level")["harm $ (if hurt)"]
        print("By level (uncapped advice; last two columns: with the liquidity cap):\n")
        print(md(t))
    mis = unc[~unc.level.isin(RIGHT_LEVELS)]
    print("\nBy occupation, pooled over the misspecified levels (uncapped):\n")
    print(md(agg(mis, "occupation")))
    print("\nBy gamma, pooled over the misspecified levels (uncapped):\n")
    print(md(agg(mis, "gamma")))
    piv = mis.pivot_table(index="occupation", columns="gamma", values="hurt", aggfunc="mean") * 100
    print("\nHurt % by occupation x gamma (uncapped, misspecified levels):\n")
    print(md(piv.rename(columns=lambda g: f"gamma {g:g}"), fmt={c: "{:.0f}" for c in piv.columns}))


RIGHT_LEVELS = {"right", "q_loss = 1 x q_event", "model 0.6, true 0.6", "overlap 100%",
                "fill 0c worse", "no view"}


CANDIDATES = None  # filled in main()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--draws", type=int, default=30, help="random users/worlds per persona (A3, joint)")
    ap.add_argument("--out", help="directory for per-case CSVs")
    ap.add_argument("--skip-candidates", action="store_true")
    args = ap.parse_args()
    pd.set_option("display.width", 200)
    t0 = time.time()
    rng = np.random.default_rng(20261107)

    # sanity: finalize() reproduces hedge_income on every persona
    for p in S.personas():
        exp = S.exposure_for(p)
        plan = H.hedge_income(exp)
        b = model_belief(exp)
        st, _ = H.joint_states(b, b, exp.basis_correlation)
        fz = finalize(exp, plan.n_star, st)
        assert fz.contracts == plan.contracts and abs(fz.ce_gain - plan.ce_gain) < 1e-6, p

    scen = {
        "right": scen_right(rng),
        "right_views": scen_right_views(rng),
        "A1": scen_qloss(rng),
        "A2": scen_basis_guess(rng),
        "A3": scen_beliefs(rng, draws=args.draws),
        "A4": scen_price_bias(rng),
        "A5": scen_timing(rng),
        "A6": scen_slippage(rng),
        "Jm": scen_joint(rng, draws=args.draws, severity="mild"),
        "Js": scen_joint(rng, draws=args.draws, severity="severe"),
    }
    titles = {
        "A1": "Assumption 1 — loss probability equals the contract's probability",
        "A2": "Assumption 2 — basis correlation overestimated (user guesses 0.6)",
        "A3": "Assumption 3 — miscalibrated beliefs",
        "A4": "Assumption 4 — market price is the true probability",
        "A5": "Assumption 5 — contract settles on the same period as the loss",
        "A6": "Assumption 6 — fills at the quoted price",
        "Jm": "Joint (mild) — all assumptions somewhat wrong at once",
        "Js": "Joint (severe) — all assumptions wrong at once",
    }
    base = {k: evaluate(v, baseline) for k, v in scen.items()}
    print("# Misspecification stress test (baseline hedge_income)\n")
    r = base["right"]
    print(f"Model-right check: {len(r)} personas, max |realized - model| = "
          f"{(r.ce_true - r.ce_model).abs().max():.2e}, hurt = {r.hurt.sum()}")
    print(f"Ruins (wealth <= 0 in some state) across all scenarios: "
          f"{sum(int(d.ruin.sum()) for d in base.values())}")
    for k in ("A1", "A2", "A3", "A4", "A5", "A6"):
        section(titles[k], base[k])
    for key in ("Jm", "Js"):
        print(f"\n### {titles[key]}\n")
        j = base[key]
        ju = j[j.liquidity == "uncapped"]
        print("Overall:\n")
        print(md(agg(j, "liquidity")))
        print("\nuncapped: by occupation\n")
        print(md(agg(ju, "occupation")))
        print("\ncapped (liquidity cap on): by occupation\n")
        print(md(agg(j[j.liquidity == "capped"], "occupation")))
        print("\nuncapped: by gamma\n")
        print(md(agg(ju, "gamma")))
        print("\nuncapped: by savings months\n")
        print(md(agg(ju, "savings_months")))
        piv = ju.pivot_table(index="occupation", columns="gamma", values="hurt", aggfunc="mean") * 100
        print("\nHurt % by occupation x gamma (uncapped):\n")
        print(md(piv.rename(columns=lambda g: f"gamma {g:g}"), fmt={c: "{:.0f}" for c in piv.columns}))
        ju2 = ju.assign(view=np.where(ju.x > 0, "view", "no view"))
        print("\nBy view / no view (uncapped):\n")
        print(md(agg(ju2, "view")))

    # worst segments overall: uncapped, all misspecified single-assumption levels
    allmis = pd.concat([base[k] for k in ("A1", "A2", "A4", "A5", "A6")])
    allmis = allmis[(allmis.liquidity == "uncapped") & ~allmis.level.isin(RIGHT_LEVELS)]
    seg = agg(allmis, ["occupation", "gamma"]).sort_values("hurt %", ascending=False)
    print("\nWorst occupation x gamma under assumptions 1,2,4,5,6 (no views, uncapped), by hurt %:\n")
    print(md(seg.head(12)))
    seg = agg(allmis, ["occupation", "gamma"]).sort_values("worst % inc", ascending=False)
    print("\n... by worst harm % income:\n")
    print(md(seg.head(8)))

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for k, d in base.items():
            d.to_csv(out / f"baseline_{k}.csv", index=False)

    if args.skip_candidates:
        return

    # ------------------------------------------------------- candidates
    cands = candidates()
    stress_keys = ["A1", "A2", "A3", "A4", "A5", "A6"]
    uncapped = {k: [c for c in v if c["liquidity"] == "uncapped"] for k, v in scen.items()}
    # A3 is large; candidates use a deterministic subsample
    uncapped["A3"] = uncapped["A3"][:: max(1, len(uncapped["A3"]) // 6000)]
    capped_js = [c for c in scen["Js"] if c["liquidity"] == "capped"]
    rows, per = [], {}
    for cand in cands:
        res = {k: evaluate(uncapped[k], cand) for k in ["right", "right_views", "Jm", "Js", *stress_keys]}
        res["Js_capped"] = evaluate(capped_js, cand)
        per[cand.__name__] = res
        b0 = per["baseline"]
        row = {
            "candidate": cand.__name__,
            "right: kept %": 100 * res["right"].ce_true.sum() / b0["right"].ce_true.sum(),
            "right+views: kept %": 100 * res["right_views"].ce_true.sum() / b0["right_views"].ce_true.sum(),
        }
        # equal weight per assumption (A3 has many more cases than the others)
        stress = [res[k][~res[k].level.isin(RIGHT_LEVELS)] for k in stress_keys]
        row |= {
            "1-6 hurt %": 100 * np.mean([d.hurt.mean() for d in stress]),
            "1-6 hurt >0.1% inc %": 100 * np.mean([d.material.mean() for d in stress]),
            "1-6 E[harm] $": np.mean([d.harm.mean() for d in stress]),
            "1-6 CE gain $": np.mean([d.ce_true.mean() for d in stress]),
        }
        for key, lab in (("Jm", "mild"), ("Js", "severe"), ("Js_capped", "severe capped")):
            jj = res[key]
            row |= {
                f"{lab} hurt %": 100 * jj.hurt.mean(),
                f"{lab} hurt >0.1% inc %": 100 * jj.material.mean(),
                f"{lab} harm $ if hurt": jj[jj.hurt].harm.mean() if jj.hurt.any() else 0.0,
                f"{lab} harm % inc if hurt": 100 * jj[jj.hurt].harm_pct.mean() if jj.hurt.any() else 0.0,
                f"{lab} E[harm] $": jj.harm.mean(),
                f"{lab} worst % inc": 100 * jj.harm_pct.max(),
                f"{lab} CE gain $": jj.ce_true.mean(),
            }
        for k in stress_keys:
            s_ = res[k][~res[k].level.isin(RIGHT_LEVELS)]
            row[f"A{k[1]} hurt %"] = 100 * s_.hurt.mean()
            row[f"A{k[1]} E[harm] $"] = s_.harm.mean()
        rows.append(row)
        print(f"  [{time.time() - t0:5.0f}s] {cand.__name__}", file=sys.stderr)
    comp = pd.DataFrame(rows).set_index("candidate")
    pct = lambda cols: {c: "{:.1f}" for c in cols if "%" in c}
    print("\n## Candidate model changes\n")
    print("Value kept when the model is right (uncapped, % of baseline CE gain), and harm under the "
          "single-assumption stresses 1-6 pooled:\n")
    a = comp[["right: kept %", "right+views: kept %", "1-6 hurt %", "1-6 hurt >0.1% inc %",
              "1-6 E[harm] $", "1-6 CE gain $"]]
    print(md(a, fmt=pct(a.columns)))
    for lab in ("mild", "severe", "severe capped"):
        print(f"\nJoint world ({lab}):\n")
        cols = [c for c in comp.columns if c.startswith(lab + " ") and
                not (lab == "severe" and c.startswith("severe capped"))]
        a = comp[cols].rename(columns=lambda c: c[len(lab) + 1:])
        print(md(a, fmt=pct(a.columns)))
    print("\nPer assumption (misspecified levels only, uncapped): hurt % / E[harm] $ over all personas\n")
    cols = [c for c in comp.columns if c[:1] == "A" and c[1].isdigit()]
    a = comp[cols]
    print(md(a, fmt=pct(a.columns)))

    for key, lab in (("Js", "severe joint"), ("Jm", "mild joint")):
        for by in ("occupation", "gamma"):
            tbl = {}
            for name in LEAD:
                if name in per:
                    g = per[name][key].groupby(by, sort=False)
                    tbl[(name, "hurt %")] = g.hurt.mean() * 100
                    tbl[(name, "CE $")] = g.ce_true.mean()
            t = pd.DataFrame(tbl)
            t.columns = [f"{n} {m}" for n, m in t.columns]
            print(f"\n{lab}, uncapped, by {by}: leading candidates (hurt % and mean realized CE gain $)\n")
            print(md(t, fmt={c: ("{:.0f}" if "hurt" in c else "{:,.0f}") for c in t.columns}))
    tbl = {}
    for name in LEAD + ["view_shrink(0.5)"]:
        if name in per:
            d = per[name]["A3"]
            d = d[d.level.isin([l for l in d.level.unique() if "bias" not in l])]
            g = d.groupby("level", sort=False)
            tbl[(name, "hurt %")] = g.hurt.mean() * 100
            tbl[(name, "CE $")] = g.ce_true.mean()
    t = pd.DataFrame(tbl)
    t.columns = [f"{n} {m}" for n, m in t.columns]
    print("\nAssumption 3 by level (no systematic bias, uncapped, subsample): leading candidates\n")
    print(md(t, fmt={c: ("{:.0f}" if "hurt" in c else "{:,.0f}") for c in t.columns}))
    tbl = {}
    for name in LEAD:
        if name in per:
            g = per[name]["right"].groupby("occupation", sort=False)
            tbl[name] = g.ce_true.mean()
    t = pd.DataFrame(tbl)
    print("\nModel-right world, mean CE gain $ by occupation (uncapped):\n")
    print(md(t, fmt={c: "{:,.0f}" for c in t.columns}))
    print(f"\n(run time {time.time() - t0:.0f}s)")
    if args.out:
        comp.to_csv(Path(args.out) / "candidates.csv")


def two_prob_capped(exp, case):
    """two_prob sizing, then clipped to [0, pure hedge] on the two-prob states."""
    plan = two_prob()(exp, case)
    if exp.loss <= 0:
        return plan
    b = model_belief(exp)
    ql = float(np.clip(case["q_loss_est"], 0.005, Q_MAX))
    states, rho_eff = H.joint_states(b, ql, exp.basis_correlation)
    n = float(np.clip(plan.n_star, 0.0, rho_eff * exp.loss))
    return finalize(exp, n, states)


two_prob_capped.__name__ = "two_prob+cap_tilt(0)"


def candidates():
    ct0 = cap_tilt(0.0)
    return [
        baseline,
        shrink_basis(0.75), shrink_basis(0.5),
        haircut(0.75), haircut(0.5),
        two_prob(), two_prob(oracle=True), two_prob_capped,
        cap_tilt(0.0), cap_tilt(0.25),
        min_gain(0.0005), min_gain(0.001),
        price_buffer(0.01), price_buffer(0.02),
        margin_gate(0.01), margin_gate(0.02),
        view_shrink(0.5),
        robust(),
        shrink_then(0.75, ct0),
        gated(shrink_then(0.75, ct0), 0.0005),
        margin_gate(0.01, inner=shrink_then(0.75, ct0)),
        price_buffer_capped(0.01),
        shrink_then(0.75, price_buffer_capped(0.01)),
        shrink_then(0.75, price_buffer_capped(0.02)),
        shrink_then(0.5, price_buffer_capped(0.01)),
        gated(shrink_then(0.75, price_buffer_capped(0.01)), 0.0005),
        margin_gate(0.01, inner=shrink_then(0.75, two_prob_capped)),
        shrink_then(0.75, price_buffer_capped(0.01, two_prob_states=True)),
        gated(shrink_then(0.75, price_buffer_capped(0.01, two_prob_states=True)), 0.0005),
    ]


def price_buffer_capped(delta, two_prob_states=False):
    """price_buffer(delta) and cap_tilt(0) together (optionally on two-prob states)."""
    def f(exp, case):
        if exp.loss <= 0:
            return H.hedge_income(exp)
        exp.validate()
        b = model_belief(exp)
        ql = float(np.clip(case["q_loss_est"], 0.005, Q_MAX)) if two_prob_states else b
        states, rho_eff = H.joint_states(b, ql, exp.basis_correlation)
        padded = replace(exp, price=float(min(exp.price + delta, 0.99)), allow_selling=False)
        n = H.optimal_contracts(padded, states)
        n = float(np.clip(n, 0.0, rho_eff * exp.loss))
        return finalize(exp, n, states)
    f.__name__ = f"price_buffer({delta})+cap_tilt(0)" + ("+two_prob" if two_prob_states else "")
    return f


LEAD = ["baseline", "cap_tilt(0.0)", "price_buffer(0.01)+cap_tilt(0)+shrink(0.75)",
        "price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%)",
        "price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%)", "robust_maxmin"]


if __name__ == "__main__":
    main()
