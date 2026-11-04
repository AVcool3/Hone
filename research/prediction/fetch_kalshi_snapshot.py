"""Refresh the bundled Kalshi snapshot the prediction-markets page falls back on.

    python research/prediction/fetch_kalshi_snapshot.py

Fetches the open markets of every series in ``hone.prediction.INDUSTRIES``
from Kalshi's public API (no account needed) and writes
``hone/prediction/kalshi_snapshot.json``.  Run it whenever a new season's
contracts have listed, or when you add a series to the catalog.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hone.prediction.kalshi_client import SNAPSHOT_PATH, fetch_live  # noqa: E402


def main() -> int:
    data = fetch_live(pause=0.6)
    data["source"] = "snapshot"
    n_series = len(data["series"])
    n_markets = sum(len(s["markets"]) for s in data["series"].values())
    SNAPSHOT_PATH.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
    print(f"wrote {SNAPSHOT_PATH}: {n_series} series, {n_markets} open markets, as of {data['as_of']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
