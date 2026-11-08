# Snow risk at 30 ski resorts

`research/prediction/resorts.py` covers 30 resorts in four groups: 11 in the
Rockies, 8 on the Pacific side, 7 in the East and Midwest, and Zermatt,
Chamonix, St. Anton and Niseko. For each resort it collects:
- every winter's snowfall since 1980 from ERA5 reanalysis (Open-Meteo),
  which is what the quote engine priced from until now;
- for 17 US resorts, peak snow water at the nearest long-record USDA SNOTEL
  station on the mountain (within 35 km, 20+ winters).

The data is in `data/resorts/resorts_summary.csv`. Rerun the script to
refresh it; raw downloads are cached and kept out of git.

A "bad season" is below 70% of the place's normal, the quote engine's
default trigger.

## 1. The grid and the mountain disagree about bad seasons

The two sources agree on how winters rank against each other (median rank
correlation 0.81 across 17 resorts). They disagree about which winters were
*bad*, and bad winters are what a contract pays on:

- **Missed:** the grid called only a median 55% of the winters that the
  station on the mountain called bad.
- **False alarms:** a median 25% of the grid's bad winters weren't bad on
  the mountain.
- **Different probabilities,** sometimes by a lot:

| Resort | Grid P(bad) | Mountain station P(bad) |
|---|---|---|
| Vail | 16% | **44%** (Vail Mountain, 3 km) |
| Palisades Tahoe | 22% | **46%** (Palisades Tahoe, 2.5 km) |
| Mt. Bachelor | 16% | **44%** |
| Taos | 39% | 44% |
| Steamboat | 29% | **7%** |
| Alta / Snowbird | 31% | **9%** |

**Change made:** the quote engine now prices from the nearest long-record
SNOTEL station whenever one exists, because a real contract would settle on
a named station. It falls back to the grid elsewhere, and every quote names
its source.

## 2. Snowfall is falling in Colorado and the Alps

| Region | Median P(bad) | Volatility (CV) | Median trend |
|---|---|---|---|
| Rockies | 22% | 0.26 | **−11.8 cm/decade** |
| Pacific | 20% | **0.37** (most volatile) | +1.9 cm/decade (none) |
| East / Midwest | 7% | 0.24 | +2.4 cm/decade (none) |
| Alps and Japan | 46% | 0.32 | **−28 cm/decade** (Alps) |

- **Significant declines (p < 0.1)** at 11 of 30 resorts:
  - Aspen, Vail, Breckenridge, Telluride, Steamboat, Alta/Snowbird, Taos;
  - Snowshoe;
  - Zermatt, Chamonix, St. Anton.
- **The Alps:** Chamonix (−35 cm/decade) and St. Anton (−37 cm/decade) now
  price at a 65% and 59% chance of falling below their own long-run 70%
  line. "Normal" there is shifting.
- **Steadiest:** Niseko (3%) and Big Sky (1%).
- **Recent bad winters:** 2025-26 was the worst winter on record for
  several Colorado resorts, which steepens their trend estimates.
- **The East looks steady** on snowfall. But Eastern revenue depends on
  temperature (rain vs. snow, snowmaking days) more than snowfall, so a
  snowfall contract tracks it less closely. The engine already lowers basis
  there.

## 3. What a frequent trigger means for the product

A live quote for a $4M resort at Vail, priced from the Vail Mountain station:
- 44% chance of a bad season (range 32–56%), and an estimated loss of $351k;
- recommended protection of only **$28k for $16k**, worth about $2k to the
  owner.

When the trigger is hit almost every other year, protection is an expensive
regular cost: 57¢ per $1 with a provider's margin. It doesn't behave like
insurance.

**Implication:** for snowy-but-volatile places, offer a deeper trigger
(e.g. below 50% of normal). That insures the rare disaster rather than the
usual dip; it's cheaper and worth more per dollar. The quote API already
accepts `trigger_fraction`. A useful next step is to recommend a trigger
per resort, choosing the one that maximizes value to the owner.

## Caveats

- **Peak snow water vs. snowfall.** SNOTEL measures peak snow water on the
  ground; ERA5 measures seasonal snowfall. They are related but different
  quantities, so part of the disagreement is definitional. A contract
  should settle on whichever one the resort's revenue actually tracks.
- **Some stations are far from the resort,** or at a different elevation
  (Aspen's is 22 km away). The quote shows the distance and elevation.
- **Short-term trends are fragile.** One bad recent winter moves them.
  Probabilities are reported with a range, and the trend is only used when
  it's statistically significant.
- **Open-Meteo's free tier is non-commercial** and rate-limited. A
  commercial launch needs the paid API.
