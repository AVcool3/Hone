"""Large parameter sweeps of the income hedge: who it helps, who it hurts,
and where its advice breaks.

``segments.py`` runs a 576-persona grid. This script runs ~80,000 personas
through the same pieces (``segments.OCCUPATIONS``, ``hone.prediction.hedge.
hedge_income`` with the liquidity cap, and ``segments.realized`` for the
reality check), across far wider ranges:

* risk aversion 0.25-12 (and -1..100 at the edges), savings 0-24 months,
  income x0.5/x1/x2, loss share x0.5/x1/x1.5;
* beliefs: the market, or a pessimist/optimist shifted 5-30 points held
  with 20-100% confidence;
* liquidity policy: share of open interest 5-100% (or off), order-book
  slippage 1-10 cents, uncapped; on the flat book ``segments`` assumes and
  on a laddered book (``depth/4`` contracts at every cent, 20 cents deep)
  where slippage actually matters;
* the price of the protective side, 5-90 cents (1-99 at the edges);
* edge cases: gamma <= 0 and very high, wealth barely above the loss,
  basis 0 and 1.

Every persona records the advice (contracts wanted / proposed, coverage,
cost, direction, pure hedge vs speculative tilt, reservation price), the
model's CE gain, the realized CE gain when the market and basis are right
(``segments.Truth()``) and, for personas with a view, when *their* view is
right. A 1% perturbation pass looks for unstable advice, and a tilt-cap
pass asks what limiting the speculative part of the position would cost or
save.

Run it (about two minutes on four cores):

    python research/prediction/sweeps.py              # full sweep + analyses
    python research/prediction/sweeps.py --quick      # a thin slice, for testing
    python research/prediction/sweeps.py --analyze    # re-run analyses on saved CSVs

Outputs land in ``research/prediction/findings/sweeps/``; the write-up is
``research/prediction/findings/03_segments.md``.
"""

from __future__ import annotations

import argparse
import itertools
import math
import os
import sys
import time
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (str(ROOT), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import segments as seg  # noqa: E402
from hone.prediction.contracts import kalshi_fee  # noqa: E402
from hone.prediction.hedge import (  # noqa: E402
    IncomeExposure, hedge_income, joint_states, optimal_contracts,
)
from hone.prediction.liquidity import Liquidity  # noqa: E402

OUT = HERE / "findings" / "sweeps"
OCC = {o.key: o for o in seg.OCCUPATIONS}
OCC_ORDER = [o.key for o in seg.OCCUPATIONS]

# ------------------------------------------------------------------ grids
GAMMA_FINE = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0]
GAMMA_MID = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0]
SAVINGS = [0, 1, 3, 6, 12, 24]
INCOME_MULT = [0.5, 1.0, 2.0]
LOSS_MULT = [0.5, 1.0, 1.5]
OI_SHARES = [0.05, 0.10, 0.25, 0.50, 1.00, math.inf]  # inf = no open-interest cap
SLIPPAGES = [0.01, 0.03, 0.05, 0.10]
BOOKS = ["flat", "ladder"]
SHIFTS = [0.05, 0.10, 0.15, 0.20, 0.30]
CONFS = [0.2, 0.4, 0.6, 0.8, 1.0]
PRICES = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
TILT_CAPS = [0.0, 0.25, 0.5, 1.0]  # speculative tilt capped at X * pure hedge

# The shipped policy, read from the engine so this can never drift from it.
from hone.prediction.liquidity import DEFAULT_MAX_SHARE_OF_OI, DEFAULT_MAX_SLIPPAGE  # noqa: E402
DEFAULT_LIQ = dict(oi_share=DEFAULT_MAX_SHARE_OF_OI, slippage=DEFAULT_MAX_SLIPPAGE, book="flat")
UNCAPPED = dict(oi_share=None, slippage=None, book=None)


def persona(sweep, occ, gamma, savings, *, income_mult=1.0, loss_mult=1.0, loss_frac=None,
            shift=0.0, conf=0.0, price=None, basis=None, liq=DEFAULT_LIQ, tilt=False):
    o = OCC[occ]
    lf = loss_frac if loss_frac is not None else min(o.loss_frac * loss_mult, 0.9)
    belief = ("market" if conf == 0 else
              f"{'pess' if shift > 0 else 'opt'}{abs(shift):.2f}c{conf:.1f}")
    return dict(sweep=sweep, occupation=occ, gamma=gamma, savings_months=savings,
                income_mult=income_mult, loss_mult=loss_mult, loss_frac=lf,
                shift=shift, conf=conf, belief=belief,
                price=price if price is not None else o.price,
                basis=basis if basis is not None else o.basis,
                view_anchor=None, tilt=tilt, **liq)


def liq_label(p) -> str:
    if p["oi_share"] is None:
        return "uncapped"
    share = "off" if math.isinf(p["oi_share"]) else f"{p['oi_share']:.2f}"
    return f"oi{share}_slip{p['slippage']:.2f}_{p['book']}"


def build_personas(quick=False) -> list[dict]:
    occs = OCC_ORDER
    g_fine = GAMMA_FINE[::4] if quick else GAMMA_FINE
    g_mid = GAMMA_MID[::3] if quick else GAMMA_MID
    rows = []
    # A. core: who benefits, by occupation x savings x gamma x income x loss
    for occ, g, s, im, lm, liq in itertools.product(
            occs, g_fine, SAVINGS, INCOME_MULT, LOSS_MULT, [DEFAULT_LIQ, UNCAPPED]):
        rows.append(persona("core", occ, g, s, income_mult=im, loss_mult=lm, liq=liq))
    # B. liquidity policy
    policies = [dict(oi_share=sh, slippage=sl, book=b)
                for b, sh, sl in itertools.product(BOOKS, OI_SHARES, SLIPPAGES)] + [UNCAPPED]
    for occ, g, s, im, liq in itertools.product(occs, g_mid, [0, 3, 12], INCOME_MULT, policies):
        rows.append(persona("liquidity", occ, g, s, income_mult=im, liq=liq))
    # C. beliefs (with tilt-cap counterfactuals on the uncapped rows)
    beliefs = [(0.0, 0.0)] + [(d * sh, c) for d in (+1, -1) for sh in SHIFTS for c in CONFS]
    for occ, g, s, (sh, c), liq in itertools.product(
            occs, g_mid, [0, 3, 12, 24], beliefs, [DEFAULT_LIQ, UNCAPPED]):
        rows.append(persona("beliefs", occ, g, s, shift=sh, conf=c, liq=liq,
                            tilt=liq is UNCAPPED and c > 0))
    # D. price of the protective side
    for occ, g, s, pr, (sh, c), liq in itertools.product(
            occs, [0.5, 1, 2, 4, 8, 12], [0, 3, 12], PRICES,
            [(0.0, 0.0), (0.10, 0.6), (-0.10, 0.6)], [DEFAULT_LIQ, UNCAPPED]):
        rows.append(persona("prices", occ, g, s, price=pr, shift=sh, conf=c, liq=liq))
    # E. edges of the domain (uncapped, so the sizing itself is visible)
    three = [(0.0, 0.0), (0.15, 0.6), (-0.15, 0.6)]
    for occ, g, s, (sh, c) in itertools.product(
            occs, [-1, -0.5, 0, 0.001, 0.01, 0.05, 0.1, 0.25, 1, 4, 12, 20, 30, 50, 100],
            [0, 12], three[:2]):
        rows.append(persona("edge_gamma", occ, g, s, shift=sh, conf=c, liq=UNCAPPED))
    for occ, lf, g in itertools.product(occs, [0.5, 0.8, 0.9, 0.95, 0.99, 0.999], [0.5, 2, 4, 8]):
        rows.append(persona("edge_wealth", occ, g, 0, loss_frac=lf, liq=UNCAPPED))
    for occ, pr, g, s, (sh, c) in itertools.product(
            occs, [0.01, 0.02, 0.03, 0.97, 0.98, 0.99], [0.5, 2, 8], [0, 12], three):
        rows.append(persona("edge_price", occ, g, s, price=pr, shift=sh, conf=c, liq=UNCAPPED))
    for occ, b, g, s, (sh, c) in itertools.product(
            occs, [0.0, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0], [0.5, 2, 8], [0, 12], three):
        rows.append(persona("edge_basis", occ, g, s, basis=b, shift=sh, conf=c, liq=UNCAPPED))
    return rows


# ------------------------------------------------------------- the model
def book(price: float, depth: float, kind: str) -> list[tuple[float, float]]:
    """Asks for one side. 'flat': all depth at the quote (what segments.py
    assumes). 'ladder': depth/4 at every cent up to 20 cents above the
    quote, so ``depth`` sits within 3 cents and slippage matters."""
    if kind == "flat":
        return [(price, depth)]
    return [(round(price + 0.01 * k, 4), depth / 4) for k in range(21) if price + 0.01 * k < 0.995]


def occupation_for(p):
    o = OCC[p["occupation"]]
    return replace(o, income=o.income * p["income_mult"], loss_frac=p["loss_frac"],
                   price=p["price"], basis=p["basis"])


def exposure(p) -> tuple[seg.Occupation, IncomeExposure]:
    """Mirror of ``segments.exposure_for`` with every input free."""
    o = occupation_for(p)
    wealth = o.income * (1 + p["savings_months"] / 12)
    anchor = p["view_anchor"] if p["view_anchor"] is not None else o.price
    own = None if p["conf"] == 0 else float(np.clip(anchor + p["shift"], 0.02, 0.98))
    liq = None
    if p["oi_share"] is not None:
        liq = Liquidity(
            open_interest=None if math.isinf(p["oi_share"]) else o.open_interest,
            asks_buy=book(o.price, o.depth, p["book"]),
            asks_sell=book(1 - o.price, o.depth, p["book"]),
            max_share_of_open_interest=0.0 if math.isinf(p["oi_share"]) else p["oi_share"],
            max_slippage=p["slippage"],
        )
    return o, IncomeExposure(
        wealth=wealth, loss=o.income * o.loss_frac, price=o.price, gamma=p["gamma"],
        market_prob=o.price, own_prob=own, confidence=p["conf"],
        basis_correlation=o.basis, liquidity=liq,
    )


def _seg_persona(o, p) -> dict:
    # segments.realized rebuilds the exposure from these fields; belief and
    # liquidity do not enter the reality check.
    return {"occupation": o, "savings_months": p["savings_months"], "gamma": p["gamma"],
            "belief": "market", "liquidity": "uncapped"}


def _plan_of(n: int, price: float):
    return SimpleNamespace(contracts=n, avg_fill_price=None,
                           fee=kalshi_fee(abs(n), price) if n else 0.0)


def evaluate(p: dict) -> dict:
    row = {k: v for k, v in p.items() if k not in ("view_anchor", "tilt")}
    row["liquidity"] = liq_label(p)
    try:
        o, exp = exposure(p)
        plan = hedge_income(exp)
    except Exception as e:  # invalid inputs are a finding too
        row["error"] = f"{type(e).__name__}: {e}"[:200]
        return row
    sp = _seg_persona(o, p)
    real = seg.realized(sp, plan)
    inc = o.income
    row.update(
        error="", income=inc, wealth=exp.wealth, loss=exp.loss, own_prob=exp.own_prob,
        belief_blended=plan.belief, n_star=plan.n_star, contracts_wanted=plan.contracts_wanted,
        contracts=plan.contracts, coverage=plan.coverage, direction=plan.direction,
        cost=plan.cost, fee=plan.fee, avg_fill=plan.avg_fill_price,
        liq_limit=plan.liquidity_limit, capped=plan.liquidity_capped,
        pure_hedge=plan.pure_hedge_contracts, spec=plan.speculative_contracts,
        basis_used=plan.basis_correlation, basis_clipped=plan.basis_clipped,
        reservation=plan.reservation_price, ce_unhedged=plan.ce_unhedged,
        ce_gain_model=plan.ce_gain, worst_hedged=plan.worst_hedged,
        n_warnings=len(plan.warnings),
        ce_gain_true=real["ce_gain_true"], ruin_true=real["ruin"],
    )
    row["cost_pct_income"] = plan.cost / inc
    row["ce_model_pct"] = plan.ce_gain / inc
    row["ce_true_pct"] = real["ce_gain_true"] / inc
    if exp.own_prob is not None:
        rv = seg.realized(sp, plan, seg.Truth(q_event=exp.own_prob))
        row["ce_gain_view"] = rv["ce_gain_true"]
    # the market-belief optimum for the same person: the "insurance" part
    if exp.own_prob is not None or p["sweep"] in ("prices",):
        mk = replace(exp, own_prob=None, confidence=0.0, liquidity=None)
        st, _ = joint_states(exp.market_prob, exp.market_prob, exp.basis_correlation)
        n_mkt = optimal_contracts(mk, st) if exp.gamma > 0 else exp.basis_correlation * exp.loss
        row["n_mkt"] = n_mkt
    if p["tilt"]:
        pure = plan.pure_hedge_contracts
        n_mkt = row["n_mkt"]
        for x in TILT_CAPS:
            n = int(round(n_mkt + float(np.clip(plan.n_star - n_mkt, -x * pure, x * pure))))
            pl = _plan_of(n, exp.price)
            row[f"ce_true_tilt{x}"] = seg.realized(sp, pl)["ce_gain_true"]
            row[f"ce_view_tilt{x}"] = seg.realized(sp, pl, seg.Truth(q_event=exp.own_prob))["ce_gain_true"]
        n = max(plan.contracts, 0)
        pl = _plan_of(n, exp.price)
        row["ce_true_nosell"] = seg.realized(sp, pl)["ce_gain_true"]
        row["ce_view_nosell"] = seg.realized(sp, pl, seg.Truth(q_event=exp.own_prob))["ce_gain_true"]
    return row


# ---------------------------------------------------------- perturbation
PERTURB = ["gamma", "wealth", "loss", "price", "basis", "conf"]


def perturbed(p: dict, what: str, eps: float) -> dict | None:
    q = dict(p, tilt=False)
    if what == "gamma":
        q["gamma"] = p["gamma"] * (1 + eps)
    elif what == "wealth":
        q["savings_months"] = 12 * ((1 + p["savings_months"] / 12) * (1 + eps) - 1)
    elif what == "loss":
        q["loss_frac"] = p["loss_frac"] * (1 + eps)
    elif what == "price":
        q["price"] = p["price"] * (1 + eps)
        q["view_anchor"] = p["price"]  # the market moves; the person's view does not
    elif what == "basis":
        if p["basis"] * (1 + eps) > 1:
            return None
        q["basis"] = p["basis"] * (1 + eps)
    elif what == "conf":
        if p["conf"] == 0 or p["conf"] * (1 + eps) > 1:
            return None
        q["conf"] = p["conf"] * (1 + eps)
    return q


def perturb_one(args) -> list[dict]:
    idx, p = args
    out = []
    try:
        base = hedge_income(exposure(p)[1]).contracts
    except Exception:
        return out
    for what in PERTURB:
        for eps in (-0.01, 0.01):
            q = perturbed(p, what, eps)
            if q is None:
                continue
            try:
                k = hedge_income(exposure(q)[1]).contracts
            except Exception:
                continue
            out.append({"idx": idx, "input": what, "eps": eps, "k0": base, "k1": k})
    return out


# ------------------------------------------------------------- running
def check_against_segments() -> None:
    """The generalized exposure must reproduce segments.exposure_for exactly."""
    for sp in seg.personas():
        shift, conf = seg.BELIEFS[sp["belief"]]
        p = persona("check", sp["occupation"].key, sp["gamma"], sp["savings_months"], shift=shift, conf=conf,
                    liq=DEFAULT_LIQ if sp["liquidity"] == "capped" else UNCAPPED)
        a, b = seg.exposure_for(sp), exposure(p)[1]
        assert (a.wealth, a.loss, a.price, a.own_prob, a.confidence, a.basis_correlation) == \
               (b.wealth, b.loss, b.price, b.own_prob, b.confidence, b.basis_correlation), sp
        assert hedge_income(a).contracts == hedge_income(b).contracts, sp


def run_all(quick=False, procs=None) -> dict[str, pd.DataFrame]:
    check_against_segments()
    ps = build_personas(quick)
    print(f"{len(ps):,} personas", flush=True)
    t = time.time()
    with Pool(procs or os.cpu_count()) as pool:
        rows = pool.map(evaluate, ps, chunksize=200)
    df = pd.DataFrame(rows)
    df.insert(0, "pid", range(len(df)))
    print(f"  evaluated in {time.time() - t:.0f}s", flush=True)
    # 1% perturbation pass on a random sample of the main sweeps
    rng = np.random.default_rng(7)
    pool_idx = df.index[df.sweep.isin(["core", "beliefs", "prices"]) & (df.error == "")]
    sample = rng.choice(pool_idx, size=min(len(pool_idx), 400 if quick else 8000), replace=False)
    t = time.time()
    with Pool(procs or os.cpu_count()) as pool:
        pert = pool.map(perturb_one, [(int(i), ps[i]) for i in sample], chunksize=50)
    pert = pd.DataFrame([r for rs in pert for r in rs])
    print(f"  {len(pert):,} perturbations in {time.time() - t:.0f}s", flush=True)
    return {"personas": df, "perturb": pert}


def save(res: dict[str, pd.DataFrame]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = res["personas"]
    for sw, d in df.groupby("sweep"):
        d = d.dropna(axis=1, how="all")
        d.to_csv(OUT / f"personas_{sw}.csv.gz", index=False, float_format="%.6g")
    res["perturb"].to_csv(OUT / "perturbations.csv.gz", index=False)


def load() -> dict[str, pd.DataFrame]:
    parts = [pd.read_csv(f, keep_default_na=True) for f in sorted(OUT.glob("personas_*.csv.gz"))]
    df = pd.concat(parts, ignore_index=True)
    df["error"] = df["error"].fillna("")
    return {"personas": df, "perturb": pd.read_csv(OUT / "perturbations.csv.gz")}


# ------------------------------------------------------------- analyses
def md(df: pd.DataFrame, floatfmt="{:,.2f}") -> str:
    """Markdown table without the tabulate dependency."""
    n_idx = 0
    if not isinstance(df.index, pd.RangeIndex):
        n_idx = df.index.nlevels
        df = df.reset_index()
    cols = [str(c) for c in df.columns]
    def cell(v, i):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else (f"{v:g}" if i < n_idx else floatfmt.format(v))
        return str(v)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(cell(v, i) for i, v in enumerate(r)) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def pct(x):
    return f"{100 * x:.1f}%"


def analyze_core(df: pd.DataFrame, rep: list[str]) -> None:
    c = df[(df.sweep == "core") & (df.error == "")].copy()
    c["meaningful"] = c.ce_true_pct > 0.005
    c["nothing"] = c.ce_true_pct < 0.0005
    g = c.groupby(["liquidity", "occupation", "savings_months", "gamma"]).agg(
        n=("contracts", "size"), coverage=("coverage", "median"), contracts=("contracts", "median"),
        contracts_wanted=("contracts_wanted", "median"),
        cost_pct_income=("cost_pct_income", "median"), ce_gain_usd=("ce_gain_true", "median"),
        ce_gain_pct_income=("ce_true_pct", "median"), share_meaningful=("meaningful", "mean"),
    ).reset_index()
    g.to_csv(OUT / "a1_core_by_occ_savings_gamma.csv", index=False, float_format="%.6g")

    cap = c[c.liquidity == liq_label(dict(DEFAULT_LIQ))]
    unc = c[c.liquidity == "uncapped"]
    occ_tbl = pd.DataFrame({
        "loss/income": cap.groupby("occupation").loss_frac.median(),
        "coverage (cap)": cap.groupby("occupation").coverage.median(),
        "CE gain $ (cap)": cap.groupby("occupation").ce_gain_true.median(),
        "CE % inc (cap)": 100 * cap.groupby("occupation").ce_true_pct.median(),
        "CE % inc p90 (cap)": 100 * cap.groupby("occupation").ce_true_pct.quantile(0.9),
        "> 0.5% inc (cap)": 100 * cap.groupby("occupation").meaningful.mean(),
        "CE % inc (uncap)": 100 * unc.groupby("occupation").ce_true_pct.median(),
        "> 0.5% inc (uncap)": 100 * unc.groupby("occupation").meaningful.mean(),
        "~0 (<0.05%) (cap)": 100 * cap.groupby("occupation").nothing.mean(),
        "cost % inc (uncap)": 100 * unc.groupby("occupation").cost_pct_income.median(),
    }).loc[OCC_ORDER]
    occ_tbl.to_csv(OUT / "a1_by_occupation.csv", float_format="%.6g")
    rep += ["## A1. Who gets value (core sweep: 12,960 personas, market beliefs)", "",
            "Per occupation, medians over gamma 0.25-12, savings 0-24 mo, income x0.5-2, loss share x0.5-1.5. "
            "'cap' = shipped default (10% of OI, 3c slippage, flat book). CE figures are realized under Truth() "
            "(market and basis right).", "", md(occ_tbl.round(3), "{:,.2f}"), ""]

    for lab, d in (("capped (default)", cap), ("uncapped", unc)):
        pv = d[d.income_mult == 1].pivot_table(index="occupation", columns="gamma", values="ce_true_pct",
                                                aggfunc="median").loc[OCC_ORDER] * 100
        pv.to_csv(OUT / f"a1_ce_pct_occ_x_gamma_{lab.split()[0]}.csv", float_format="%.5g")
        rep += [f"Median realized CE gain, % of income, by gamma ({lab}, income x1, all savings/loss levels):", "",
                md(pv[[g for g in (0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0) if g in pv.columns]].round(3), "{:.3f}"), ""]
    pv = unc[(unc.income_mult == 1) & (unc.loss_mult == 1)].pivot_table(
        index="occupation", columns="savings_months", values="ce_true_pct", aggfunc="median").loc[OCC_ORDER] * 100
    rep += ["Median realized CE gain, % of income, by savings months (uncapped, income x1, loss x1, all gammas):", "",
            md(pv.round(3), "{:.3f}"), ""]
    # who gets value: logistic-free decomposition
    seg_tbl = unc.assign(gamma_band=pd.cut(unc.gamma, [0, 1, 3, 6, 12.1], labels=["<=1", "1-3", "3-6", "6-12"]),
                         sav_band=pd.cut(unc.savings_months, [-1, 0, 3, 6, 24], labels=["0", "1-3", "6", "12-24"]))
    t2 = seg_tbl.groupby(["gamma_band", "sav_band"], observed=True).meaningful.mean().unstack() * 100
    t3 = cap.assign(gamma_band=pd.cut(cap.gamma, [0, 1, 3, 6, 12.1], labels=["<=1", "1-3", "3-6", "6-12"]),
                    sav_band=pd.cut(cap.savings_months, [-1, 0, 3, 6, 24], labels=["0", "1-3", "6", "12-24"])
                    ).groupby(["gamma_band", "sav_band"], observed=True).meaningful.mean().unstack() * 100
    rep += ["% of personas with CE gain > 0.5% of income, by gamma band x savings (uncapped | capped):", "",
            md(t2.round(1), "{:.1f}"), "", md(t3.round(1), "{:.1f}"), ""]
    cp = unc[(unc.income_mult == 1) & (unc.loss_mult == 1) & (unc.savings_months == 3)]
    cp = cp.assign(x=cp.contracts / cp.pure_hedge).pivot_table(index="occupation", columns="gamma", values="x").loc[OCC_ORDER]
    cp.to_csv(OUT / "a1_contracts_over_pure_by_gamma.csv", float_format="%.5g")
    rep += ["Contracts / pure hedge (rho*L) by gamma (uncapped, market belief, savings 3 mo, income x1, loss x1). "
            "Basis (rho): " + ", ".join(f"{k} {OCC[k].basis}" for k in OCC_ORDER) + ":", "",
            md(cp[[g for g in (0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0) if g in cp.columns]], "{:.2f}"), ""]
    zero = (cap.contracts == 0).mean()
    rep += [f"Capped default: {pct(zero)} of core personas are advised 0 contracts; "
            f"{pct((cap.ce_true_pct > 0.005).mean())} get > 0.5% of income; "
            f"{pct((cap.ce_true_pct < 0.0005).mean())} get < 0.05%. Uncapped: "
            f"{pct((unc.contracts == 0).mean())} zero, {pct((unc.ce_true_pct > 0.005).mean())} > 0.5%.", ""]


def analyze_liquidity(df: pd.DataFrame, rep: list[str]) -> None:
    L = df[(df.sweep == "liquidity") & (df.error == "")].copy()
    key = ["occupation", "gamma", "savings_months", "income_mult"]
    base = L[L.liquidity == "uncapped"].set_index(key)[["ce_gain_true", "contracts"]]
    base.columns = ["ce_unc", "k_unc"]
    L = L[L.liquidity != "uncapped"].join(base, on=key)
    L["retained"] = np.where(L.ce_unc > 1e-9, L.ce_gain_true / L.ce_unc, np.nan)
    L["share_of_oi"] = L.contracts / L.occupation.map(lambda k: OCC[k].open_interest)
    L["slip_paid"] = (L.avg_fill - L.price).where(L.contracts > 0)
    L["oi"] = L.oi_share.map(lambda x: "off" if math.isinf(x) else f"{x:.2f}")
    t = L.groupby(["book", "oi", "slippage"]).agg(
        retained_median=("retained", "median"), retained_mean=("retained", "mean"),
        ce_usd_mean=("ce_gain_true", "mean"), coverage=("coverage", "median"),
        pos_share_oi_p90=("share_of_oi", lambda s: s.quantile(0.9)),
    ).reset_index()
    t.to_csv(OUT / "a2_policy_overall.csv", index=False, float_format="%.6g")
    by = L.groupby(["book", "oi", "slippage", "occupation"]).agg(
        retained=("retained", "median"), ce_usd=("ce_gain_true", "median"),
        coverage=("coverage", "median"), contracts=("contracts", "median"),
        share_of_oi=("share_of_oi", "median"), slip_paid=("slip_paid", "median")).reset_index()
    by.to_csv(OUT / "a2_policy_by_occupation.csv", index=False, float_format="%.6g")
    # flat book: slippage is inert
    flat = L[L.book == "flat"]
    inert = flat.groupby(["occupation", "gamma", "savings_months", "income_mult", "oi"]).contracts.nunique().max()
    pv = by[(by.book == "ladder")].pivot_table(index="occupation", columns=["oi", "slippage"], values="retained").loc[OCC_ORDER]
    pv_flat = by[(by.book == "flat") & (by.slippage == 0.03)].pivot_table(
        index="occupation", columns="oi", values="retained").loc[OCC_ORDER]
    rep += ["## A2. Liquidity policy (28,224 personas)", "",
            f"Flat book (segments.py's assumption): contracts never depend on max_slippage "
            f"(max distinct sizes across slippage settings = {inert}); the OI share is the only lever.", "",
            "Median share of uncapped CE gain retained, flat book, by OI share (slippage irrelevant):", "",
            md((pv_flat * 100).round(1), "{:.1f}"), ""]
    sel = [(o, s) for o in ["0.05", "0.10", "0.25", "0.50", "1.00", "off"] for s in [0.01, 0.03, 0.10]]
    pv2 = pv[[c for c in sel if c in pv.columns]] * 100
    pv2.columns = [f"{o}/{int(s*100)}c" for o, s in pv2.columns]
    rep += ["Ladder book (depth/4 per cent, 20c deep; fills walk the book): median % of uncapped CE retained, "
            "columns = OI share / slippage. Values > 100% mean the cap *beats* the uncapped advice, "
            "because uncapped advice ignores slippage:", "", md(pv2.round(1), "{:.1f}"), ""]
    # value in dollars by occupation for selected policies, ladder
    sel2 = by[(by.book == "ladder") & (by.slippage == 0.03)].pivot_table(
        index="occupation", columns="oi", values="ce_usd").loc[OCC_ORDER]
    rep += ["Ladder book, 3c slippage: median realized CE gain ($) by OI share:", "", md(sel2.round(1), "{:,.1f}"), ""]
    # best policy per occupation on ladder book
    best = (L[L.book == "ladder"].groupby(["occupation", "oi", "slippage"]).ce_gain_true.mean()
            .reset_index().sort_values("ce_gain_true").groupby("occupation").tail(1).set_index("occupation").loc[OCC_ORDER])
    rep += ["Ladder book: the policy with the highest mean realized CE gain per occupation:", "",
            md(best.round(2), "{:,.2f}"), ""]
    unc_l = L[(L.book == "ladder") & (L.oi == "off") & (L.slippage == 0.10)]
    rep += [f"Ladder book, no OI cap, 10c slippage: median position = "
            f"{unc_l.share_of_oi.median():.1f}x open interest (p90 {unc_l.share_of_oi.quantile(0.9):.1f}x).", ""]


def analyze_failures(df: pd.DataFrame, pert: pd.DataFrame, rep: list[str]) -> None:
    d = df[(df.error == "") & df.sweep.isin(["core", "liquidity", "beliefs", "prices"])].copy()
    d["f_sell"] = (d.direction == "sell") & (d.contracts != 0) & (d.loss > 0)
    d["f_cost25"] = d.cost_pct_income > 0.25
    d["f_over_res"] = (d.price > d.reservation) & (d.contracts > 0)
    d["f_fill_over_res"] = (d.avg_fill > d.reservation) & (d.contracts > 0)
    d["f_ce_model_neg"] = d.ce_gain_model < -1e-6
    d["f_ce_true_neg"] = d.ce_gain_true < -1e-6
    d["f_ce_true_neg_mkt"] = d.f_ce_true_neg & (d.conf == 0)
    d["f_tiny"] = (d.contracts != 0) & (d.ce_gain_true.abs() < 1.0)
    flags = ["f_sell", "f_cost25", "f_over_res", "f_fill_over_res", "f_ce_model_neg", "f_ce_true_neg", "f_ce_true_neg_mkt", "f_tiny"]
    tbl = d.groupby("sweep")[flags].agg(["sum"]).droplevel(1, axis=1)
    tbl.loc["all"] = tbl.sum()
    tbl["n"] = d.groupby("sweep").size().reindex(tbl.index).fillna(len(d)).astype(int)
    tbl.loc["all", "n"] = len(d)
    tbl.to_csv(OUT / "a3_failure_counts.csv")
    rep += ["## A3. Failure modes", "",
            "Counts over the core, liquidity, beliefs and prices sweeps. f_sell = sells the protective side while "
            "exposed; f_cost25 = cost > 25% of income; f_over_res = buys with the quoted price above the reservation "
            "price; f_fill_over_res = buys with the average *fill* price above it; "
            "f_ce_model_neg / f_ce_true_neg = negative CE gain by the model's own numbers / under Truth(); "
            "f_ce_true_neg_mkt = same, among personas with no view; f_tiny = a non-zero trade worth < $1.", "",
            md(tbl.astype(int)), ""]
    # where do the failures sit?
    b = d[d.sweep == "beliefs"]
    s = b[b.f_sell]
    if len(s):
        st = s.groupby(["occupation"]).size().reindex(OCC_ORDER).fillna(0).astype(int)
        rep += [f"Sells while exposed (beliefs sweep): {len(s):,} of {len(b):,}; all are optimists "
                f"({(s["shift"] < 0).mean():.0%}); median confidence {s.conf.median():.1f}, median shift "
                f"{s["shift"].abs().median():.2f}, median gamma {s.gamma.median():.1f}. "
                f"Median sold position = {(-s.contracts / s.pure_hedge.replace(0, np.nan)).median():.2f}x the pure hedge; "
                f"realized CE when the market is right: median {s.ce_true_pct.median() * 100:.2f}% of income "
                f"(p10 {s.ce_true_pct.quantile(0.1) * 100:.2f}%). By occupation: "
                + ", ".join(f"{k} {v}" for k, v in st.items()), ""]
    c25 = d[d.f_cost25]
    if len(c25):
        rep += [f"Cost > 25% of income: {len(c25):,} personas, "
                f"{(c25.sweep == 'prices').mean():.0%} in the price sweep; median price {c25.price.median():.2f}, "
                f"median cost {c25.cost_pct_income.median() * 100:.0f}% of income; "
                f"{(c25.conf > 0).mean():.0%} hold a view. Occupations: "
                + ", ".join(f"{k} {v}" for k, v in c25.occupation.value_counts().items()), ""]
    neg = d[d.f_ce_true_neg_mkt]
    if len(neg):
        rep += [f"Negative realized CE with market beliefs: {len(neg):,}; median {neg.ce_gain_true.median():.2f} $, "
                f"min {neg.ce_gain_true.min():.2f} $. Liquidity: "
                + ", ".join(f"{k} {v}" for k, v in neg.liquidity.value_counts().head(4).items()), ""]
    negm = d[d.f_ce_model_neg]
    if len(negm):
        rep += [f"Negative CE by the model's own accounting: {len(negm):,}; "
                f"{(negm.direction == 'sell').mean():.0%} sells, {(negm.book == 'ladder').mean():.0%} on the ladder book, "
                f"median {negm.ce_gain_model.median():.2f} $, worst {negm.ce_gain_model.min():,.0f} $.", ""]
    rep += [f"Buying above the reservation price at the quote: {int(d.f_over_res.sum())} personas; at the "
            f"average fill: {int(d.f_fill_over_res.sum())} (all on the ladder book: "
            f"{int((d.f_fill_over_res & (d.book == 'ladder')).sum())}); their median realized CE "
            f"{d[d.f_fill_over_res].ce_gain_true.median():.2f} $, worst {d[d.f_fill_over_res].ce_gain_true.min():,.0f} $.", ""]
    tiny = d[d.f_tiny]
    rep += [f"Non-zero trades worth < $1 of CE: {len(tiny):,} ({pct(len(tiny) / len(d))}); median size "
            f"{tiny.contracts.abs().median():.0f} contracts; {pct(tiny.capped.astype(bool).mean())} of them are capped. "
            f"Negative model CE among market-belief, flat-book personas is fee rounding: worst "
            f"{d[(d.conf == 0) & (d.book != 'ladder') & d.f_ce_model_neg].ce_gain_model.min():.3f} $.", ""]

    # instability
    if len(pert):
        pert = pert.copy()
        big = np.maximum(pert.k0.abs(), pert.k1.abs())
        dk = (pert.k1 - pert.k0).abs()
        pert["flip"] = (np.sign(pert.k0) * np.sign(pert.k1) < 0)
        pert["onoff"] = ((pert.k0 == 0) != (pert.k1 == 0)) & (big >= 3)
        pert["jump"] = (dk >= np.maximum(3, 0.10 * big))  # >10x elasticity
        pert["unstable"] = pert.flip | pert.onoff | pert.jump
        pert["elasticity"] = np.where(pert.k0 != 0, (pert.k1 - pert.k0) / pert.k0.abs() / 0.01, np.nan)
        meta = df.set_index("pid").loc[pert.idx, ["sweep", "occupation", "gamma", "conf", "liquidity", "price"]
                                       ].reset_index(drop=True)
        pert = pd.concat([pert.reset_index(drop=True), meta], axis=1)
        pert["has_view"] = pert.conf > 0
        pert.to_csv(OUT / "a3_perturbations_flagged.csv.gz", index=False, float_format="%.6g")
        it = pert.groupby(["input", "has_view"]).agg(
            n=("unstable", "size"), unstable_pct=("unstable", "mean"), jump_pct=("jump", "mean"),
            onoff_pct=("onoff", "mean"), flip_pct=("flip", "mean"),
            median_abs_elasticity=("elasticity", lambda s: s.abs().median()),
            p99_abs_elasticity=("elasticity", lambda s: s.abs().quantile(0.99)),
        )
        for col in ["unstable_pct", "jump_pct", "onoff_pct", "flip_pct"]:
            it[col] *= 100
        it.to_csv(OUT / "a3_instability.csv", float_format="%.6g")
        base_ce = df.set_index("pid").ce_gain_true
        pert["base_ce_usd"] = pert.idx.map(base_ce).values
        per_persona = pert.groupby("idx").unstable.any()
        uu = pert[pert.unstable]
        stake = (f"Value at stake where it happens: median base CE gain {uu.base_ce_usd.median():.2f} $ "
                 f"(p90 {uu.base_ce_usd.quantile(0.9):.2f} $) vs {pert.base_ce_usd.median():.2f} $ for all sampled; "
                 f"{pct(((uu.k0 == 0) | (uu.k1 == 0)).mean())} of unstable "
                 f"re-runs straddle the 0-contract entry threshold. Without a view, "
                 f"{pct((uu[~uu.has_view].base_ce_usd < 5).mean())} of unstable cases are worth < $5.")
        rep += ["### Instability (1% input perturbations)", "",
                f"{pert.idx.nunique():,} sampled personas x up to 12 perturbations = {len(pert):,} re-runs. "
                f"Unstable = direction flip, on/off switch (>= 3 contracts), or a change >= max(3, 10%) of the "
                f"position from a 1% input move (elasticity > 10). "
                f"{pct(per_persona.mean())} of personas are unstable to at least one 1% perturbation.", "",
                md(it.round(2)), "", stake, ""]
        u = pert[pert.unstable]
        ut = u.groupby(["occupation"]).size().reindex(OCC_ORDER).fillna(0).astype(int)
        rep += ["Unstable re-runs by occupation: " + ", ".join(f"{k} {v}" for k, v in ut.items()) +
                f". By liquidity: capped {int((u.liquidity != 'uncapped').sum())}, uncapped "
                f"{int((u.liquidity == 'uncapped').sum())}.", ""]

    # speculation share
    b = df[(df.sweep == "beliefs") & (df.error == "") & (df.liquidity == "uncapped")].copy()
    b["tilt"] = b.n_star - b.n_mkt
    b["tilt_x_pure"] = b.tilt / b.pure_hedge.replace(0, np.nan)
    b["dir"] = np.where(b["shift"] > 0, "pessimist", np.where(b["shift"] < 0, "optimist", "market"))
    v = b[b.conf > 0]
    sp = v.groupby(["dir", "gamma"]).tilt_x_pure.median().unstack(0)
    sp.to_csv(OUT / "a3_speculation_by_gamma.csv", float_format="%.5g")
    sp2 = v.assign(strength=(v["shift"].abs() * v.conf).round(2)).groupby(["dir", "strength"]).tilt_x_pure.median().unstack(0)
    sp3 = v.groupby(["occupation", "dir"]).tilt_x_pure.median().unstack(1).loc[OCC_ORDER]
    mk = b[b.conf == 0]
    rep += ["### How much of the position is speculation? (beliefs sweep, uncapped)", "",
            "Tilt = n*(with view) - n*(market belief), in units of the pure hedge rho*L. "
            f"For market-belief personas the model's own 'speculative_contracts' (n* - rho*L) is still "
            f"{mk.spec.div(mk.pure_hedge).median():.2f}x the pure hedge at the median "
            f"(p10 {mk.spec.div(mk.pure_hedge).quantile(0.1):.2f}, p90 {mk.spec.div(mk.pure_hedge).quantile(0.9):.2f}) "
            "— fees and CRRA skew, not a view.", "",
            "Median tilt / pure hedge, by gamma:", "", md(sp.round(2)), "",
            "Median tilt / pure hedge, by view strength = |shift| x confidence (blended move in probability):", "",
            md(sp2.round(2)), "", "Median tilt / pure hedge, by occupation:", "", md(sp3.round(2)), ""]
    # share of |position| that is speculative
    v = v.assign(spec_share=(v.tilt.abs() / (v.n_mkt.abs() + v.tilt.abs())))
    ss = v.groupby(["occupation"]).spec_share.median().loc[OCC_ORDER]
    rep += ["Median share of the gross position that is speculative, |tilt| / (|n_mkt| + |tilt|): "
            + ", ".join(f"{k} {100 * x:.0f}%" for k, x in ss.items()) + ".", ""]

    drop = (b.worst_hedged - (b.wealth - b.loss)) / b.income
    rep += [f"Worst-state wealth falls by more than 10% of income vs. not trading: "
            f"{pct((drop[b.conf > 0] < -0.10).mean())} of personas with a view, "
            f"{pct((drop[b.conf == 0] < -0.10).mean())} without. Positions > 2x the pure hedge: "
            f"{pct((b[b.conf > 0].contracts.abs() > 2 * b[b.conf > 0].pure_hedge).mean())} with a view "
            "(by gamma: " + ", ".join(f"{g:g}: {100 * x:.0f}%" for g, x in b[b.conf > 0].groupby("gamma").apply(
                lambda g: (g.contracts.abs() > 2 * g.pure_hedge).mean()).items()) + ").", ""]

    # tilt cap counterfactuals
    tc = [f"ce_true_tilt{x}" for x in TILT_CAPS] + ["ce_true_nosell"]
    tv = [f"ce_view_tilt{x}" for x in TILT_CAPS] + ["ce_view_nosell"]
    w = b[b.conf > 0].copy()
    rows = []
    names = ["current advice"] + [f"cap {x:g}x pure" for x in TILT_CAPS] + ["no-sell"]
    for x, a, bb in zip(names, ["ce_gain_true"] + tc, ["ce_gain_view"] + tv):
        m = w[a] / w.income * 100   # realized CE % of income, market right
        v = w[bb] / w.income * 100  # ... the person's own view right
        dm = m.mean() - (w.ce_gain_true / w.income * 100).mean()
        dv = v.mean() - (w.ce_gain_view / w.income * 100).mean()
        rows.append({"variant": x,
                     "mkt right: median": m.median(), "mkt right: p5": m.quantile(0.05),
                     "mkt right: p1": m.quantile(0.01), "mkt right: mean": m.mean(),
                     "view right: median": v.median(), "view right: mean": v.mean(),
                     # P(view right) above which the current advice beats this variant
                     "break-even P(view right)": dm / (dm - dv) if dm > 0 and dv < 0 else np.nan})
    tct = pd.DataFrame(rows).set_index("variant")
    tct.to_csv(OUT / "a3_tilt_cap.csv", float_format="%.6g")
    # by confidence
    rows = []
    for c_, g_ in w.groupby("conf"):
        r = {"conf": c_}
        for x in TILT_CAPS:
            dm = ((g_[f"ce_true_tilt{x}"] - g_.ce_gain_true) / g_.income * 100).mean()
            dv = ((g_[f"ce_view_tilt{x}"] - g_.ce_gain_view) / g_.income * 100).mean()
            r[f"cap{x:g}: mkt/view"] = f"{dm:+.3f} / {dv:+.3f}"
        rows.append(r)
    byc = pd.DataFrame(rows).set_index("conf")
    rep += ["### What capping the speculative tilt would do (3,968... personas with a view, uncapped)".replace(
                "3,968...", f"{len(w):,}"), "",
            "Realized CE gain, % of income, when the market is right vs. when the person's own (unblended) view is "
            "right. Variants keep the market-belief position n_mkt and allow at most X * pure hedge of tilt on top; "
            "'no-sell' floors the current advice at zero. Break-even = the probability the view must be right "
            "for the current advice to beat the variant on average.", "",
            md(tct.round(3), "{:+.3f}"), "", "By confidence (mean delta % of income, market right / view right):", "",
            md(byc), ""]
    # asymmetry: market-right loss vs view-right gain from the tilt, by occupation
    asym = w.assign(loss_mr=(w.ce_gain_true - w["ce_true_tilt0.0"]) / w.income * 100,
                    gain_vr=(w.ce_gain_view - w["ce_view_tilt0.0"]) / w.income * 100)
    at = asym.groupby("occupation")[["loss_mr", "gain_vr"]].mean().loc[OCC_ORDER]
    at.columns = ["tilt value if market right (% inc)", "tilt value if view right (% inc)"]
    rep += ["Value of the whole tilt (current advice minus market-belief advice), mean % of income:", "",
            md(at.round(3), "{:+.3f}"), ""]


def analyze_edges(df: pd.DataFrame, rep: list[str]) -> None:
    rep += ["## A4. Edges of the domain", ""]
    e = df[df.sweep == "edge_gamma"]
    t = e[(e.savings_months == 0)].pivot_table(index="gamma", columns=["belief"], values="contracts",
                                               aggfunc="median")
    t2 = e[(e.savings_months == 0) & (e.belief == "market")].pivot_table(
        index="gamma", columns="occupation", values="contracts", aggfunc="first")[["rideshare", "contractor", "tech"]]
    t3 = e[(e.savings_months == 0) & (e.belief == "market")].groupby("gamma").agg(
        ce_true_pct=("ce_true_pct", "median"), pure_hedge=("pure_hedge", "median"), n_warnings=("n_warnings", "median"))
    pd.concat([t2, t3], axis=1).to_csv(OUT / "a4_edge_gamma.csv", float_format="%.6g")
    rep += ["Gamma (savings 0, market belief, uncapped): contracts for three occupations, plus median CE % and "
            "pure hedge.", "", md(pd.concat([t2, t3 * [100, 1, 1]], axis=1).round(3), "{:,.3f}"), ""]
    rep += ["Gamma with a pessimist view (+0.15 at 60%), median contracts across occupations:", "",
            md(t.round(0), "{:,.0f}"), ""]
    w = df[df.sweep == "edge_wealth"]
    tw = w.pivot_table(index="loss_frac", columns="gamma", values="ce_true_pct", aggfunc="median") * 100
    tw2 = w.pivot_table(index="loss_frac", columns="gamma", values="contracts", aggfunc="median")
    errs = (w.error != "").sum()
    tw.to_csv(OUT / "a4_edge_wealth.csv", float_format="%.6g")
    rep += [f"Wealth barely above the loss (savings 0, loss = 50-99.9% of income; {errs} errors): median CE gain "
            "% of income:", "", md(tw.round(2), "{:,.2f}"), "", "median contracts:", "", md(tw2.round(0), "{:,.0f}"), ""]
    p = df[df.sweep == "edge_price"]
    tp = p.groupby(["price", "belief"]).agg(contracts=("contracts", "median"), cost_pct=("cost_pct_income", "median"),
                                            ce_true_pct=("ce_true_pct", "median"),
                                            spec_x_pure=("spec", lambda s: np.nan),
                                            errors=("error", lambda s: (s != "").sum())).drop(columns="spec_x_pure")
    tp["cost_pct"] *= 100
    tp["ce_true_pct"] *= 100
    tp.to_csv(OUT / "a4_edge_price.csv", float_format="%.6g")
    rep += ["Price of the protective side at the edges (uncapped; medians over occupations, gamma, savings):", "",
            md(tp.round(3), "{:,.3f}"), ""]
    bsis = df[df.sweep == "edge_basis"]
    tb = bsis.groupby(["basis", "belief"]).agg(contracts=("contracts", "median"), pure=("pure_hedge", "median"),
                                               basis_used=("basis_used", "median"),
                                               clipped=("basis_clipped", "mean"),
                                               ce_true_pct=("ce_true_pct", "median"),
                                               ce_true_min_pct=("ce_true_pct", "min"))
    tb[["ce_true_pct", "ce_true_min_pct"]] *= 100
    tb.to_csv(OUT / "a4_edge_basis.csv", float_format="%.6g")
    rep += ["Basis correlation at the edges (uncapped):", "", md(tb.round(3), "{:,.3f}"), ""]
    # prices sweep: value vs price
    pr = df[(df.sweep == "prices") & (df.liquidity == "uncapped") & (df.belief == "market")]
    tpr = pr.pivot_table(index="price", columns="occupation", values="ce_true_pct", aggfunc="median")[OCC_ORDER] * 100
    tpr.to_csv(OUT / "a4_ce_by_price.csv", float_format="%.6g")
    tpc = pr.pivot_table(index="price", columns="occupation", values="cost_pct_income", aggfunc="median")[OCC_ORDER] * 100
    rep += ["Price sweep (uncapped, market belief): median realized CE gain % of income by price:", "",
            md(tpr.round(3), "{:.3f}"), "", "... and median cost % of income:", "", md(tpc.round(2), "{:.2f}"), ""]


# ---------------------------------------------------------------- charts
INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def charts(df: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    plt.rcParams.update({"font.family": "sans-serif", "text.color": INK, "axes.labelcolor": "#52514e",
                         "axes.titlesize": 10, "axes.titleweight": "bold", "figure.facecolor": "#fcfcfb",
                         "axes.facecolor": "#fcfcfb"})
    blues = LinearSegmentedColormap.from_list("b", ["#f0efec", "#86b6ef", "#2a78d6", "#0d366b"])

    # 1. heatmap: CE % income, occupation x gamma, capped vs uncapped
    c = df[(df.sweep == "core") & (df.error == "") & (df.income_mult == 1)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, lab in zip(axes, [liq_label(dict(DEFAULT_LIQ)), "uncapped"]):
        pv = c[c.liquidity == lab].pivot_table(index="occupation", columns="gamma", values="ce_true_pct",
                                              aggfunc="median").loc[OCC_ORDER] * 100
        im = ax.imshow(pv.values, aspect="auto", cmap=blues, vmin=0, vmax=max(1.0, np.nanmax(pv.values)))
        ax.set_xticks(range(len(pv.columns)), [f"{g:g}" for g in pv.columns], fontsize=8)
        ax.set_yticks(range(len(pv.index)), pv.index, fontsize=8)
        for (i, j), v in np.ndenumerate(pv.values):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                    color="#ffffff" if v > 0.6 * max(1.0, np.nanmax(pv.values)) else INK)
        ax.set_title("Default cap (10% OI, 3c)" if lab != "uncapped" else "Uncapped")
        ax.set_xlabel("risk aversion gamma")
    fig.colorbar(im, ax=axes, shrink=0.8, label="median realized CE gain, % of income")
    fig.suptitle("Who the hedge helps: CE gain as % of income (core sweep, market beliefs)", fontsize=11)
    fig.savefig(OUT / "a1_ce_heatmap.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # 2. liquidity: % of uncapped value retained vs OI share, ladder 3c, one line per occupation
    L = df[(df.sweep == "liquidity") & (df.error == "")]
    key = ["occupation", "gamma", "savings_months", "income_mult"]
    base = L[L.liquidity == "uncapped"].set_index(key).ce_gain_true.rename("ce_unc")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, bk in zip(axes, ["flat", "ladder"]):
        d = L[(L.book == bk) & (L.slippage == 0.03)].join(base, on=key)
        d = d.assign(ret=np.where(d.ce_unc > 1e-9, d.ce_gain_true / d.ce_unc * 100, np.nan),
                     oi=d.oi_share.replace(np.inf, 2.0))
        for i, occ in enumerate(OCC_ORDER):
            s = d[d.occupation == occ].groupby("oi").ret.median()
            ax.plot(s.index, s.values, color=SERIES[i], linewidth=2, marker="o", markersize=4, label=occ)
        ax.set_xscale("log")
        ax.set_xticks([0.05, 0.1, 0.25, 0.5, 1.0, 2.0], ["5%", "10%", "25%", "50%", "100%", "off"])
        ax.axvline(0.10, color=MUTED, linestyle="--", linewidth=1)
        ax.set_title(f"{bk} book, 3c slippage")
        ax.set_xlabel("max share of open interest")
        _style(ax)
    axes[0].set_ylabel("median % of uncapped CE gain retained")
    axes[1].legend(fontsize=7, frameon=False, loc="center right")
    fig.suptitle("Liquidity cap: value kept vs the share-of-OI limit (dashed = shipped default)", fontsize=11)
    fig.savefig(OUT / "a2_liquidity_retained.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # 3. speculation: tilt / pure hedge vs confidence, by gamma, for shift 0.15
    b = df[(df.sweep == "beliefs") & (df.liquidity == "uncapped") & (df.conf > 0) & (df.error == "")]
    b = b.assign(tx=(b.n_star - b.n_mkt) / b.pure_hedge)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, (lab, sgn) in zip(axes, [("pessimist (+0.15)", 0.15), ("optimist (-0.15)", -0.15)]):
        d = b[np.isclose(b["shift"], sgn)]
        for i, g in enumerate([0.5, 1, 2, 4, 8, 12]):
            s = d[d.gamma == g].groupby("conf").tx.median()
            ax.plot(s.index, s.values, color=SERIES[i], linewidth=2, marker="o", markersize=4, label=f"gamma {g:g}")
        ax.axhline(0, color="#c3c2b7", linewidth=1)
        ax.axhline(-1, color="#d03b3b", linewidth=1, linestyle=":", label="tilt = -1x pure hedge (advice sells at or above here)")
        ax.set_title(lab)
        ax.set_xlabel("confidence in own view")
        _style(ax)
    axes[0].set_ylabel("speculative tilt / pure hedge (median over occupations)")
    axes[1].legend(fontsize=7, frameon=False, loc="lower left")
    fig.suptitle("Speculation dwarfs insurance once a view is held: tilt relative to the pure hedge", fontsize=11)
    fig.savefig(OUT / "a3_speculation.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # 4. edge: contracts vs gamma near 0
    e = df[(df.sweep == "edge_gamma") & (df.savings_months == 0) & (df.belief == "market")]
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, occ in enumerate(["rideshare", "contractor", "ski"]):
        s = e[e.occupation == occ].set_index("gamma").contracts.sort_index()
        s = s[s.index <= 12]
        ax.plot(s.index, s.values / OCC[occ].basis / (OCC[occ].income * OCC[occ].loss_frac), color=SERIES[i],
                linewidth=2, marker="o", markersize=4, label=occ)
    ax.set_xscale("symlog", linthresh=0.01)
    ax.axvline(0, color=MUTED, linestyle="--", linewidth=1)
    ax.set_xlabel("gamma (symlog)")
    ax.set_ylabel("contracts / pure hedge")
    ax.set_title("Gamma = 0 jumps to the full pure hedge; gamma = 0.01 buys nothing")
    ax.legend(fontsize=8, frameon=False)
    _style(ax)
    fig.savefig(OUT / "a4_gamma_edge.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--quick", action="store_true", help="thin grid, for testing")
    ap.add_argument("--analyze", action="store_true", help="re-run analyses on saved CSVs")
    ap.add_argument("--procs", type=int, default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.analyze:
        res = load()
    else:
        res = run_all(args.quick, args.procs)
        save(res)
        res = load()  # analyze exactly what was saved
    df = res["personas"]
    rep: list[str] = [f"# Sweep tables ({len(df):,} personas, {df.error.ne('').sum()} input errors)", ""]
    analyze_core(df, rep)
    analyze_liquidity(df, rep)
    analyze_failures(df, res["perturb"], rep)
    analyze_edges(df, rep)
    (OUT / "tables.md").write_text("\n".join(rep))
    charts(df)
    print("\n".join(rep))
    total = sum(f.stat().st_size for f in OUT.iterdir())
    print(f"\nwrote {OUT} ({total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
