# 10. Can El Niño forecast a bad snow season? (November 2026)

**Question.** Hone prices a bad winter from the place's own history ("11
of 45 winters were bad, so about 25%"). Before a winter starts we also know
the state of the Pacific: El Niño / La Niña (the ONI index) and the PDO.
If we had used them in past winters, would our odds have been closer to
what happened?

**Short answer.** Only in a few places. Across the whole West the gain is
close to zero, so Hone uses the forecast only in the **Southwest** (New
Mexico and Arizona), the one region where it passed both tests. There it
improves the odds by about 12%. Everywhere else, quotes stay on history
alone and say why.

Code: `research/prediction/forecast_data.py` (download),
`research/prediction/forecast_study.py` (tests and `--save`),
`hone/prediction/forecast.py` (the model used in quotes),
`tests/test_forecast.py`.

## Data

- **Snow:** 568 USDA SNOTEL stations with records back to 1990 or earlier,
  for winters 1980–81 to 2025–26. That is 25,180 station-winters. We use
  the season's peak snow water from monthly values. That matches the daily
  peak Hone's quotes use: correlation 0.97–0.99, and the two agree on which
  winters were bad 93–100% of the time.
- **Bad winter:** peak below 70% of the station's normal (its median). This
  is Hone's default trigger. On average 17.5% of winters were bad.
- **Signals, all known before the winter starts:** ONI for Aug–Oct
  (published early November) and the PDO averaged over Sep–Oct.

## What the raw numbers say

Share of station-winters that were bad, by phase of the Pacific:

| Region | El Niño | La Niña | Neutral |
|---|---|---|---|
| Pacific Northwest | 29% | **6%** | 27% |
| Northern Rockies | 16% | **4%** | 12% |
| Sierra / Great Basin | 27% | 16% | 30% |
| Utah | 15% | 13% | 20% |
| Colorado | 5% | 9% | 20% |
| Southwest | **6%** | **41%** | 38% |
| Alaska | 27% | 13% | 17% |

The textbook pattern shows up. La Niña protects the north, and El Niño
protects the Southwest while La Niña hurts it. But in most regions El Niño
is no worse than a neutral year, and neutral years (24 of the 46) are
where most bad winters happen. Neutral years carry no signal to use.

## The tests

Each model predicts the chance of a bad winter for every station, and it
is scored against the baseline (Hone's current method: the station's own
bad-winter rate). The score is the **Brier skill score (BSS)**. Above 0
means the model's odds were closer to what happened.

1. **Leave one winter out.** Hold out a whole winter, every station at
   once, because they all share that winter's El Niño. Fit on the other
   45 winters and predict it. Repeat for each of the 46 winters.
2. **Forward in time.** For each winter from 2006 to 2025, fit only on
   earlier winters, which is exactly what Hone would have known.

The 90% ranges come from resampling whole winters. However many stations
there are, there are only about 46 independent Pacific outcomes.

| Model | BSS, leave one winter out | 90% range | BSS, forward |
|---|---|---|---|
| History alone (the baseline) | 0 | — | 0 |
| West-wide El Niño/PDO shift | −0.4% | −2.9% to +2.5% | +1.0% |
| **Regional shift (shipped)** | **+0.6%** | −2.2% to +3.8% | **+2.2%** |
| Gradient-boosted trees (location + signals) | −6.4% | −14.7% to +1.5% | −4.1% |

The shipped model, region by region:

| Region | Stations | BSS | 90% range | Forward | Used? |
|---|---|---|---|---|---|
| **Southwest** | 25 | **+11.6%** | +0.7% to +21.4% | **+11.9%** | **yes** |
| Colorado | 70 | +3.6% | −0.1% to +7.0% | +4.4% | no (just missed) |
| Pacific Northwest | 105 | +0.6% | −5.1% to +6.5% | +2.5% | no |
| Northern Rockies | 221 | −0.2% | −2.7% to +2.8% | +0.7% | no |
| Utah | 75 | −1.7% | −4.7% to +1.9% | +2.0% | no |
| Sierra / Great Basin | 52 | −2.4% | −9.1% to +4.4% | −1.5% | no |
| Alaska | 20 | −2.8% | −7.9% to +2.0% | +1.3% | no |

By phase (leave one winter out, shipped model): La Niña winters **+12.3%**,
El Niño +3.8%, neutral **−3.8%**. The model helps when the Pacific gives a
clear signal and costs a little when it doesn't.

**Rule for using it:** a region is adjusted only if the lower end of its
90% range is above 0 *and* the forward test is above 0. That is saved in
the model file, and a test checks the file against this rule.

### Robustness

- Other trigger levels: below 60% of normal +0.7%, below 80% +1.5%. That
  is the same small, positive picture.
- Reading El Niño earlier (Jun–Aug instead of Aug–Oct): +0.8%. Before
  late summer the quote engine doesn't use the forecast at all.
- Model forms tried. This choice was made on the same tests, so its
  numbers are slightly optimistic:

  | Form | Leave one out | Forward |
  |---|---|---|
  | **El Niño and La Niña slopes separately, plus PDO (shipped)** | **+0.6%** | **+2.2%** |
  | Single straight line in ONI, plus PDO | −2.0% | −3.3% |
  | El Niño / La Niña / neutral categories, plus PDO | −0.9% | −2.7% |
  | Categories, no PDO | +0.6% | −0.4% |
  | Straight line in ONI, no PDO | −0.5% | −2.4% |

  The common "one line in ONI" model is *worse* than history. It forces El
  Niño to be the mirror image of La Niña, and in the north it isn't.

- Calibration: the shipped model is too confident at the top end
  (predicted 46%, observed 35% in its highest band). That is one more
  reason it caps any shift at 3× the odds.

## How quotes use it

`quote()` calls `forecast.shift_probability()` for snow quotes:

    log-odds(bad) = log-odds(history) + shift(region, El Niño, La Niña, PDO)

- The price is unchanged, with the reason shown to the user, when: the
  place is more than 150 km from any training station (for example
  Vermont); the region didn't pass the tests; it's too early in the year;
  or the readings can't be fetched.
- Readings are clipped to the range seen since 1980, and the shift is
  capped at 3× the odds either way.
- The user sees the explanation, the test evidence for their region and
  the three most similar past winters.

**This winter (2026–27):** ONI for Aug–Oct is **+2.46**, the strongest
since at least 1980, with a strongly negative PDO (−1.9). For Taos the live
quote moves from 44% (history alone) to **20%**, at the 3× cap. The most
similar past winters in the Southwest were 2023–24 (24% of stations bad),
2015–16 (12%) and 1982–83 (0%). The closest analogue, 2023–24, also had a
negative PDO and was the worst of the three, so the forecast is not a
guarantee.

## Limits and next steps

- **Small sample.** The skill rests on about 46 winters, of which only 12
  were El Niño and 10 La Niña. More stations cannot fix that.
- **Regions by state are coarse.** Southern Colorado (the San Juans) likely
  behaves like the Southwest. A smarter regional split could let
  Colorado pass, but it has to be justified by physics, not by searching
  until a test passes.
- **East, Europe, Canada:** not covered (no SNOTEL). NOAA snowfall
  stations would extend it.
- **Summer rain and drought:** El Niño's summer signal over the US is much
  weaker than its winter one. If winter barely beats history, summer
  probably won't, but that is a guess. The same harness could test it on
  NOAA station data.
- **Retrain every year** after the season ends: `python
  research/prediction/forecast_data.py && python
  research/prediction/forecast_study.py --save`.
