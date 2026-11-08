"""Drive the full conviction-backtest sweep and dump the tables.

Usage:  python research/conviction/run_conviction_backtest.py [--investors 24] [--out DIR]

Writes, per asset class:
    panel_<asset>.csv      every investor x cell x strategy row
    summary_<asset>.csv    per-cell distribution summary + win rates
    diagnostics_<asset>.csv confidence / hit-rate diagnostics per cell
and prints the markdown tables that go into docs/BACKTEST_CONVICTION.md.
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from hone.backtest import conviction as cv

BASE_SEED = 1_000

GAMMAS = [0.5, 1.2, 2.5, 5.0, 8.0]
SKILLS = [0.0, 0.2, 0.4]
OVERCONFIDENCES = [1.0, 2.0]

STRATEGY_ORDER = [
    "equal_weight",
    "market_hold",
    "risk_only",
    "views_stated_conf",
    "views_calibrated_conf",
    "views_full_conf",
]

SHORT = {
    "equal_weight": "equal_weight",
    "market_hold": "market_hold",
    "risk_only": "risk_only",
    "views_stated_conf": "stated",
    "views_calibrated_conf": "calibrated",
    "views_full_conf": "face_value",
}


def one_investor(job: tuple[str, int]) -> pd.DataFrame:
    """Worker: the whole gamma x skill x overconfidence cross for one draw.

    Splitting on the investor index keeps every worker self-contained (its
    own price path, its own noise stream) and preserves the seeds exactly,
    so a parallel run reproduces a serial one row for row.
    """
    asset_name, i = job
    asset_class = cv.equities() if asset_name == "equities" else cv.crypto()
    panel = cv.run_panel(
        asset_class,
        gammas=GAMMAS,
        skills=SKILLS,
        overconfidences=OVERCONFIDENCES,
        n_investors=1,
        base_seed=BASE_SEED + i,
    )
    panel["investor"] = i
    return panel


def markdown_table(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    rule = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = []
    for _, r in df.iterrows():
        cells = []
        for v in r:
            cells.append(floatfmt.format(v) if isinstance(v, float) else str(v))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, rule, *rows])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--investors", type=int, default=24)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    for name in ("equities", "crypto"):
        t0 = time.time()
        jobs = [(name, i) for i in range(args.investors)]
        parts = []
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for done, part in enumerate(pool.map(one_investor, jobs), 1):
                parts.append(part)
                print(
                    f"  {name}: {done}/{args.investors}", file=sys.stderr, flush=True
                )
        panel = pd.concat(parts, ignore_index=True)
        panel.to_csv(args.out / f"panel_{name}.csv", index=False)
        summary = cv.summarize(panel)
        summary.to_csv(args.out / f"summary_{name}.csv", index=False)
        diag = cv.diagnostics_table(panel)
        diag.to_csv(args.out / f"diagnostics_{name}.csv", index=False)
        print(
            f"[{name}] {len(panel)} rows in {time.time() - t0:.0f}s",
            file=sys.stderr,
            flush=True,
        )

        summary["strategy"] = pd.Categorical(
            summary["strategy"], STRATEGY_ORDER, ordered=True
        )
        summary = summary.sort_values(
            ["skill", "overconfidence", "gamma", "strategy"]
        )

        print(f"\n\n=========== {name.upper()} ===========\n")

        # ---- headline: pooled across gamma, per skill x overconfidence
        pooled = (
            panel.assign(strategy=lambda d: d["strategy"].map(SHORT))
            .groupby(["skill", "overconfidence", "strategy"])
            .agg(
                sharpe=("sharpe", "median"),
                cagr=("cagr", "median"),
                vol=("volatility", "median"),
                sortino=("sortino", "median"),
                max_dd=("max_drawdown", "median"),
                eff_n=("effective_n", "median"),
                turnover=("turnover", "median"),
            )
            .reset_index()
        )
        wins = cv.summarize(panel)
        wins["strategy"] = wins["strategy"].map(SHORT)
        pooled_wins = (
            wins.groupby(["skill", "overconfidence", "strategy"])[
                ["beat_risk_only", "beat_market_hold"]
            ]
            .mean()
            .reset_index()
        )
        pooled = pooled.merge(pooled_wins, on=["skill", "overconfidence", "strategy"])
        pooled["strategy"] = pd.Categorical(
            pooled["strategy"], [SHORT[s] for s in STRATEGY_ORDER], ordered=True
        )
        pooled = pooled.sort_values(["skill", "overconfidence", "strategy"])
        print("### Pooled across gamma\n")
        print(markdown_table(pooled))

        # ---- by gamma, calibrated stater only (overconfidence = 1)
        print("\n\n### By gamma (calibrated stater)\n")
        by_gamma = (
            wins[wins["overconfidence"] == 1.0][
                [
                    "gamma",
                    "skill",
                    "strategy",
                    "sharpe",
                    "cagr",
                    "volatility",
                    "sortino",
                    "max_drawdown",
                    "effective_n",
                    "beat_risk_only",
                    "beat_market_hold",
                    "beat_risk_only_cagr",
                ]
            ]
            .copy()
        )
        by_gamma["strategy"] = pd.Categorical(
            by_gamma["strategy"], [SHORT[s] for s in STRATEGY_ORDER], ordered=True
        )
        print(markdown_table(by_gamma.sort_values(["skill", "gamma", "strategy"])))

        print("\n\n### Diagnostics\n")
        print(markdown_table(diag.drop(columns=["asset_class"])))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
