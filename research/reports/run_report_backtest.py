"""Replay a research archive through Hone at several risk tolerances.

    python research/reports/run_report_backtest.py \
        --notes notes.csv --prices prices.csv

Inputs
------
``--notes`` CSV, one row per published note:

    ticker,published,target_price,horizon_days,confidence,thesis
    NVDA,2023-02-14,300,365,,Datacentre demand inflecting
    INTC,2023-03-02,22,365,0.6,Foundry story not working

    horizon_days defaults to 365 (the usual 12-month target).
    confidence may be blank — most notes don't state one.
    thesis is optional and only used for the scorecard.

``--prices`` CSV, dates down the side, tickers across the top:

    date,NVDA,INTC,SPY
    2022-01-03,30.10,51.22,477.71
    ...

    Daily closes, adjusted for splits and dividends. It must start at least
    a year before the first note so the covariance estimate has a trailing
    window that never touches the future.

Read the caveats in ``hone/backtest/reports`` before believing the output.
The one that matters most: an archive covering fewer than fifteen or twenty
names cannot answer whether the research was any good, because the noise in
the covariance estimate is larger than the effect being measured.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hone.backtest.reports import (  # noqa: E402
    ResearchNote,
    analyst_scorecard,
    run_report_backtest,
    score_notes,
    summarize,
)


def load_notes(path: Path) -> list[ResearchNote]:
    df = pd.read_csv(path)
    required = {"ticker", "published", "target_price"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{path}: missing column(s) {', '.join(sorted(missing))}")

    notes, skipped = [], 0
    for i, row in df.iterrows():
        try:
            notes.append(
                ResearchNote(
                    ticker=str(row["ticker"]),
                    published=str(row["published"]),
                    target_price=float(row["target_price"]),
                    horizon_days=float(row.get("horizon_days") or 365.0),
                    confidence=(
                        float(row["confidence"])
                        if "confidence" in df.columns and pd.notna(row["confidence"])
                        else None
                    ),
                    thesis=str(row.get("thesis") or ""),
                )
            )
        except (ValueError, TypeError) as exc:
            print(f"  row {i + 2}: skipped ({exc})", file=sys.stderr)
            skipped += 1
    if skipped:
        print(f"  {skipped} row(s) skipped", file=sys.stderr)
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--notes", required=True, type=Path)
    ap.add_argument("--prices", required=True, type=Path)
    ap.add_argument("--gammas", default="0.5,1.2,2.5,5.0,8.0")
    ap.add_argument("--max-weight", type=float, default=0.35)
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--lookback", type=int, default=252)
    ap.add_argument("--confidence-default", type=float, default=0.5)
    ap.add_argument("--out", type=Path, default=None, help="write the table as CSV")
    args = ap.parse_args()

    notes = load_notes(args.notes)
    prices = pd.read_csv(args.prices, index_col=0, parse_dates=True).sort_index()
    gammas = tuple(float(g) for g in args.gammas.split(","))

    covered = sorted({n.ticker for n in notes})
    print(f"{len(notes)} notes covering {len(covered)} names, "
          f"{prices.index.min().date()} to {prices.index.max().date()}")
    absent = [t for t in covered if t not in prices.columns]
    if absent:
        print(f"  no price history for: {', '.join(absent)} — those notes "
              f"will be ignored", file=sys.stderr)
    if len(covered) < 15:
        print(f"\n  WARNING: {len(covered)} covered names. Below roughly fifteen,\n"
              f"  the covariance noise is larger than the effect being measured\n"
              f"  and the sign of research_alpha is not meaningful. Read the\n"
              f"  scorecard below; treat the return table as illustrative.\n",
              file=sys.stderr)

    outcomes = score_notes(notes, prices)
    card = analyst_scorecard(outcomes)
    print(f"\n--- the notes themselves ({card.get('n', 0)} scoreable) ---")
    if card.get("n"):
        print(f"  reached the target      : {card['target_hit_rate']:.0%}")
        print(f"  touched it at some point: {card['touched_rate']:.0%}")
        print(f"  right on direction      : {card['direction_hit_rate']:.0%}")
        print(f"  average predicted move  : {card['mean_implied_return']:+.1%}")
        print(f"  average realized move   : {card['mean_realized_return']:+.1%}")
        print(f"  median capture of move  : {card['median_capture']:.0%}")
        if "brier" in card:
            print(f"  Brier score             : {card['brier']:.3f}")
            print(f"  resolution              : {card['resolution']:.4f}"
                  f"   (0 = confident calls land no more often)")

    results = run_report_backtest(
        notes, prices, gammas=gammas, lookback=args.lookback,
        max_weight=args.max_weight, cost_bps=args.cost_bps,
        confidence_default=args.confidence_default,
    )
    table = summarize(results)
    print("\n--- net returns by risk aversion ---")
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(table.round(4).to_string())
    print("\n  research_alpha = CAGR minus the same machinery run with no notes.")
    print("  That is the only column that isolates the research from the risk")
    print("  allocation over names nobody wrote about.")

    if args.out:
        table.to_csv(args.out)
        print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
