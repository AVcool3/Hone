"""Fetch the price panel the report backtest needs.

    pip install yfinance
    python research/reports/fetch_prices.py --notes notes.csv --out prices.csv

Reads the tickers out of your notes file, pulls split- and dividend-adjusted
daily closes covering every note's window plus a year of warm-up in front of
the earliest one, and writes the wide CSV that
``run_report_backtest.py --prices`` expects.

The warm-up year is not optional.  The covariance estimate at each rebalance
uses a trailing window, and if the panel starts on the first note's date
there is no window to use that does not reach forward into the test period.

Run this on a machine with network access.  It is deliberately a separate
script from the backtest so the fetch happens once and the replay stays
reproducible against a file you can inspect and keep.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

#: Trading days of history required before the first note, plus a margin for
#: holidays. `run_report_backtest` defaults to a 252-period lookback.
WARMUP_DAYS = 420


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--notes", type=Path, help="notes CSV; tickers are read from it")
    ap.add_argument("--tickers", help="comma-separated, instead of --notes")
    ap.add_argument("--out", type=Path, default=Path("prices.csv"))
    ap.add_argument("--benchmark", default="SPY",
                    help="always included, for the market comparison")
    ap.add_argument("--end", default=None, help="YYYY-MM-DD; defaults to today")
    args = ap.parse_args()

    try:
        import yfinance as yf
    except ImportError:
        print("pip install yfinance", file=sys.stderr)
        return 1

    if args.notes:
        notes = pd.read_csv(args.notes)
        tickers = sorted(set(notes["ticker"].astype(str).str.upper()))
        first = pd.to_datetime(notes["published"]).min()
        horizon = float(notes.get("horizon_days", pd.Series([365])).max() or 365)
        last = pd.to_datetime(notes["published"]).max() + pd.Timedelta(days=horizon)
    elif args.tickers:
        tickers = sorted({t.strip().upper() for t in args.tickers.split(",")})
        first, last = pd.Timestamp("2015-01-01"), pd.Timestamp.today()
    else:
        print("give --notes or --tickers", file=sys.stderr)
        return 1

    if args.benchmark and args.benchmark.upper() not in tickers:
        tickers.append(args.benchmark.upper())

    start = (first - pd.Timedelta(days=WARMUP_DAYS)).date()
    end = pd.Timestamp(args.end).date() if args.end else min(
        last, pd.Timestamp.today()
    ).date()
    print(f"{len(tickers)} tickers, {start} to {end} "
          f"({WARMUP_DAYS}d warm-up before the first note)")

    raw = yf.download(tickers, start=str(start), end=str(end),
                      auto_adjust=True, progress=False)
    px = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    px = pd.DataFrame(px).dropna(how="all")
    px.index.name = "date"

    empty = [t for t in tickers if t not in px.columns or px[t].isna().all()]
    if empty:
        print(f"  no data for: {', '.join(empty)} — delisted, renamed, or a "
              f"typo. Notes on these will be ignored.", file=sys.stderr)
        px = px.drop(columns=[c for c in empty if c in px.columns])

    gaps = px.isna().sum()
    for t, n in gaps[gaps > 0].items():
        print(f"  {t}: {n} missing days (forward-filled at replay time)",
              file=sys.stderr)

    px.round(6).to_csv(args.out)
    print(f"wrote {args.out}: {px.shape[0]} rows x {px.shape[1]} tickers")
    if px.shape[1] < 15:
        print(f"\n  NOTE: {px.shape[1]} names. Below roughly fifteen the "
              f"covariance noise\n  exceeds the effect being measured — the "
              f"scorecard will still be\n  meaningful, the return table will "
              f"not be.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
