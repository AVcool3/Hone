"""Turn the sweep CSVs into the tables that go into the doc."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from hone.backtest import conviction as cv

OUT = Path(__file__).parent / "results"

SHORT = {
    "equal_weight": "equal_weight",
    "market_hold": "market_hold",
    "risk_only": "risk_only",
    "views_stated_conf": "stated",
    "views_calibrated_conf": "calibrated",
    "views_full_conf": "face_value",
}
ORDER = [SHORT[s] for s in cv.STRATEGIES]


def md(df, fmt="{:.3f}"):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(
            fmt.format(v) if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def pairwise(panel, a, b, metric="sharpe"):
    """Fraction of investor draws where strategy a beat strategy b."""
    wide = panel.pivot_table(
        index=["skill", "overconfidence", "gamma", "investor"],
        columns="strategy", values=metric)
    return (wide[a] > wide[b]).groupby(level=["skill", "overconfidence"]).mean()


for asset in ("equities", "crypto"):
    panel = pd.read_csv(OUT / f"panel_{asset}.csv")
    summ = cv.summarize(panel)
    summ["strategy"] = summ["strategy"].map(SHORT)
    panel_s = panel.assign(strategy=panel["strategy"].map(SHORT))

    print(f"\n\n############ {asset.upper()} ############\n")

    pooled = (panel_s.groupby(["skill", "overconfidence", "strategy"])
              .agg(cagr=("cagr", "median"), vol=("volatility", "median"),
                   sharpe=("sharpe", "median"), sortino=("sortino", "median"),
                   max_dd=("max_drawdown", "median"),
                   eff_n=("effective_n", "median"),
                   turnover=("turnover", "median"))
              .reset_index())
    w = (summ.groupby(["skill", "overconfidence", "strategy"])
         [["beat_risk_only", "beat_market_hold"]].mean().reset_index())
    pooled = pooled.merge(w, on=["skill", "overconfidence", "strategy"])
    pooled["strategy"] = pd.Categorical(pooled["strategy"], ORDER, ordered=True)
    pooled = pooled.sort_values(["skill", "overconfidence", "strategy"])
    print("## pooled across gamma\n")
    print(md(pooled))

    print("\n\n## calibrated vs stated, paired (fraction of draws calibrated wins on Sharpe)\n")
    p = pairwise(panel_s, "calibrated", "stated").rename("calibrated_beats_stated")
    p2 = pairwise(panel_s, "stated", "face_value").rename("stated_beats_face_value")
    p3 = pairwise(panel_s, "calibrated", "face_value").rename("calibrated_beats_face_value")
    p4 = pairwise(panel_s, "stated", "risk_only").rename("stated_beats_risk_only")
    print(md(pd.concat([p, p2, p3, p4], axis=1).reset_index()))

    print("\n\n## by gamma (calibrated stater, overconfidence=1)\n")
    g = summ[summ["overconfidence"] == 1.0][
        ["gamma", "skill", "strategy", "sharpe", "cagr", "volatility",
         "max_drawdown", "effective_n", "beat_risk_only", "beat_market_hold"]].copy()
    g["strategy"] = pd.Categorical(g["strategy"], ORDER, ordered=True)
    print(md(g.sort_values(["skill", "gamma", "strategy"])))

    print("\n\n## by gamma (2x overconfident)\n")
    g2 = summ[summ["overconfidence"] == 2.0][
        ["gamma", "skill", "strategy", "sharpe", "cagr", "volatility",
         "max_drawdown", "beat_risk_only", "beat_market_hold"]].copy()
    g2 = g2[g2["strategy"].isin(["stated", "calibrated", "face_value", "risk_only"])]
    g2["strategy"] = pd.Categorical(g2["strategy"], ORDER, ordered=True)
    print(md(g2.sort_values(["skill", "gamma", "strategy"])))

    print("\n\n## diagnostics\n")
    diag = pd.read_csv(OUT / f"diagnostics_{asset}.csv")
    diag = diag[diag["gamma"] == 2.5].drop(columns=["asset_class", "gamma"])
    print(md(diag))
