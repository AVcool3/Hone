"""How much does weather move revenue? What management said on earnings calls.

Four transcript-mining passes (snow, rain-stopped work, summer weather,
farms) each wrote one CSV to ``research/prediction/data/calls/``. Every row
is one statement from an earnings call, found and linked through Quartr,
pairing a weather event ("snowfall 38% below average") with its stated
effect ("lift-ticket revenue down 12%").

This script:

1. **checks** every row (columns, numbers, a Quartr link);
2. turns each row with both a weather deviation and an impact into an
   **elasticity**, in the quote engine's units: % of revenue lost per 1%
   the weather was worse than normal;
3. **summarizes** per Hone business type (median, range, how many rows
   are management's own weather estimate vs a raw year-on-year change);
4. **compares** that with what ``hone/prediction/quote.py`` assumes today.

Run it:

    python research/prediction/call_sensitivity.py
    python research/prediction/call_sensitivity.py --out summary.csv

The comparison is in revenue terms: Hone's "effective" elasticity is the
business's sensitivity after pre-sold revenue (passes, contracts) is taken
out but before cost savings, because that's what calls report.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from hone.prediction.perils import PERILS
from hone.prediction.quote import BUSINESSES

DATA = Path(__file__).parent / "data" / "calls"
COLUMNS = [
    "business_key", "company", "ticker", "event", "event_date", "period_affected", "region", "peril",
    "weather_stated", "weather_deviation_pct", "impact_metric", "impact_scope", "impact_pct",
    "impact_basis", "impact_usd", "deferred_or_lost", "quote", "source_url", "notes",
]
#: Rows whose impact is management's own estimate of the weather effect are
#: cleaner than a raw year-on-year change (which mixes in prices, openings,
#: acquisitions...). In the weighted median they count this much more.
ESTIMATE_WEIGHT = 2.0
#: Ignore deviations this small: dividing by ~0 makes nonsense elasticities.
MIN_DEVIATION_PCT = 3.0
#: Metrics that measure revenue (or a close stand-in for it). EBITDA and
#: profit rows are kept for the profit-vs-revenue story but not used for
#: the revenue elasticity.
REVENUE_LIKE = ("revenue", "sales", "visits", "attendance", "volume", "shipments", "units",
                "hours", "crop", "yield", "production", "comp", "traffic", "skier")


def load(data: Path = DATA) -> pd.DataFrame:
    frames = []
    for f in sorted(data.glob("*.csv")):
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        missing = [c for c in COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"{f.name}: missing columns {missing}")
        frames.append(df[COLUMNS].assign(file=f.stem))
    if not frames:
        raise FileNotFoundError(f"no CSVs in {data}")
    df = pd.concat(frames, ignore_index=True)
    for c in ("weather_deviation_pct", "impact_pct", "impact_usd"):
        df[c] = pd.to_numeric(df[c].str.replace(",", "").str.replace("%", "").str.strip(), errors="coerce")
    return df


def problems(df: pd.DataFrame) -> list[str]:
    """Rows that break the rules. The data tests fail if this isn't empty."""
    out = []
    for i, r in df.iterrows():
        where = f"{r.file}.csv row {i + 2}"
        if not r.source_url.startswith("https://web.quartr.com/"):
            out.append(f"{where}: source_url isn't a Quartr link")
        if r.business_key not in BUSINESSES:
            out.append(f"{where}: unknown business_key {r.business_key!r}")
        if r.peril and r.peril not in PERILS:
            out.append(f"{where}: unknown peril {r.peril!r}")
        if not r.quote.strip():
            out.append(f"{where}: no quote")
    return out


def is_bad_direction(peril: str) -> int:
    """+1 if MORE of the measure is bad (rain days, heat, frost), -1 if LESS
    is bad (snow, summer heat for HVAC, rainfall in a drought)."""
    return 1 if PERILS[peril].high_is_bad else -1


def elasticities(df: pd.DataFrame) -> pd.DataFrame:
    """One elasticity per usable row: % revenue lost per 1% worse weather.

    Positive = bad weather cost revenue (the expected sign). A row where bad
    weather *helped* comes out negative and is kept: it's evidence too.
    """
    rows = df[df.weather_deviation_pct.notna() & df.impact_pct.notna()].copy()
    rows = rows[rows.weather_deviation_pct.abs() >= MIN_DEVIATION_PCT]
    rows = rows[rows.impact_metric.str.lower().str.contains("|".join(REVENUE_LIKE))]
    rows = rows[rows.peril.isin(PERILS)]
    # "How much worse than normal", positive when the weather was bad:
    worse = rows.weather_deviation_pct * rows.peril.map(is_bad_direction)
    rows["worse_pct"] = worse
    rows["elasticity"] = -rows.impact_pct / worse
    rows["weight"] = np.where(rows.impact_basis.str.contains("estimate", case=False), ESTIMATE_WEIGHT, 1.0)
    return rows


def weighted_median(x: np.ndarray, w: np.ndarray) -> float:
    order = np.argsort(x)
    x, w = x[order], w[order]
    c = np.cumsum(w)
    return float(x[np.searchsorted(c, c[-1] / 2)])


def hone_effective(key: str, region: str = "rockies") -> float:
    """What the quote engine assumes, in revenue terms (see module doc)."""
    b = BUSINESSES[key]
    return b.elasticity_for(region) * (1.0 - b.pass_damping * b.pass_share)


def summary(df: pd.DataFrame) -> pd.DataFrame:
    el = elasticities(df)
    out = []
    for key in BUSINESSES:
        all_rows = df[df.business_key == key]
        e = el[el.business_key == key]
        row = {
            "business_key": key, "peril": BUSINESSES[key].peril, "rows": len(all_rows),
            "companies": all_rows.company.nunique(), "elasticity_rows": len(e),
            "hone_now": round(hone_effective(key), 3),
        }
        if len(e):
            row.update({
                "calls_median": round(weighted_median(e.elasticity.to_numpy(), e.weight.to_numpy()), 3),
                "calls_p25": round(float(e.elasticity.quantile(0.25)), 3),
                "calls_p75": round(float(e.elasticity.quantile(0.75)), 3),
                "from_estimates": int((e.weight > 1).sum()),
            })
        lost = all_rows.deferred_or_lost.str.lower()
        row["said_lost"] = int(lost.str.contains("lost").sum())
        row["said_deferred"] = int(lost.str.contains("defer").sum())
        out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the per-business summary to this CSV")
    args = ap.parse_args()
    df = load()
    bad = problems(df)
    print(f"{len(df)} statements from {df.company.nunique()} companies; {len(bad)} problems")
    for p in bad[:20]:
        print("  !", p)
    pd.set_option("display.width", 200)
    s = summary(df)
    print(s.to_string(index=False))
    el = elasticities(df)
    print("\nEvery usable row:")
    print(el[["business_key", "company", "period_affected", "weather_deviation_pct", "impact_metric",
              "impact_pct", "impact_basis", "elasticity"]].sort_values(["business_key", "elasticity"])
          .to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    if args.out:
        s.to_csv(args.out, index=False)
