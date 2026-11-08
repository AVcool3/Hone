# Job-loss odds and regional basis from BLS data

`research/prediction/labor_study.py` uses public Bureau of Labor Statistics
data to replace the page's generic labor-market guesses with measured
values. Each input comes from one source:
- `loss_prob` (your own chance of the bad outcome) comes from JOLTS layoffs and
  discharges by industry, Dec 2000 – Sep 2026.
- `basis_correlation` (how well a national contract tracks your loss) comes from
  three comparisons:
  - one worker's job loss against the national unemployment rate (JOLTS against CPS U3);
  - a state's or metro's unemployment against the national rate (LAUS, Jan 2001 – Oct 2026);
  - regional CPI against national CPI (CPI-U, Jan 2001 – Sep 2026).

The measured values are frozen as tables in `hone/prediction/labor.py`, so the
app works offline. The lookups are `job_loss_prob()`, `basis_to_national()`
and `hedge_defaults()`. The study's CSVs are in `data/bls/`.

## Headline

| Exposure | National contract | Measured basis | Use as `basis_correlation` |
|---|---|---|---|
| **Your own job** | U3 "rises" (monthly) | **0.000–0.003** | **0** (cap 0.02): no useful hedge |
| Your own job | U3 up over 12 months, or up ≥ 0.5 pt | 0.00–0.025 | 0 (cap 0.02) |
| **Income tied to your state's labor market** | U3 (monthly) | corr 0.49 median (0.13–0.60) | **0.34** median (0.09–0.41), by state |
| Income tied to your state's labor market | U3 over 12 months | corr 0.90 median (0.44–0.97) | 0.61 median (0.30–0.66) |
| **Retiree costs, by CPI region** | CPI (monthly) | corr 0.89–0.96 | **0.61–0.66** |
| Retiree costs, big metro (NY, LA, Chicago) | CPI (monthly) | corr 0.74–0.79 | 0.51–0.54 |

The second column of numbers already includes the single-strike discount.
`hedge.py` applies its own `BASIS_SHRINK` (×0.75) on top, so don't shrink these again.

**Today's labor default of 0.1 is wrong in both directions.** For a worker's
own job it is too high: the data allow about 0. For income that follows the
state economy it is too low: about 0.34 monthly and 0.6 over a year.

## What we could and couldn't fetch

- **BLS API (v1, no key):** one query got through. It returned 25 series for
  2021–2026 (national U3, employment, JOLTS, CPI national and two regions).
  The next query was refused with "daily threshold … reached". The keyless
  quota is counted per IP address, and this network had already used it.
  `fetch_series` stopped there, set `report.limit_hit` and didn't retry.
- **FRED mirror, 107 series:** the St. Louis Fed republishes the same BLS
  series unchanged, with no quota. `fetch_series` filled every remaining gap
  from FRED. `FRED_MIRROR` in `labor.py` maps each BLS ID to its FRED ID.
  The cache records the source of each window (`"source": "fred:UNRATE"`).
- **JOLTS by industry is the unadjusted series (JTU…).** FRED carries
  seasonally adjusted JOLTS only for the totals. Averages over whole years
  don't depend on seasonality, and the basis formula only picks up
  covariance with the contract.
- **Not fetched:**
  - the nine CPI divisions (published from Dec 2017, not on FRED);
  - Denver and Phoenix CPI.
  - States therefore use their CPI region.
- **Only 2001–2017:** Los Angeles and Washington CPI. Their FRED copies
  stop where BLS redrew the areas in 2018, so these use the old definitions
  (LA–Riverside–Orange County, Washington–Baltimore).
- **To complete the pull:** re-run tomorrow, or set `BLS_API_KEY` (a free v2
  key; the full pull is then 3 queries). Only missing windows are requested.
  `--offline` reruns everything from the cache, about 0.9 MB in `data/bls/`.

## Method

**1. Monthly → annual job-loss odds.** JOLTS reports layoffs and discharges
(L&D) in a month as a percent of employment. We read it as a monthly hazard
`m` and convert to the chance of at least one job loss in a year:
`P = 1 − (1 − m)^12`. For example, 1.2% a month gives 13.5% a year, not
14.4%, because a job can only be lost once.

- **"Typical"** averages every month except the Mar–May 2020 shock.
- **"Recession"** averages the 2001 and 2008–09 NBER recession months.

**2. From layoffs to a settled worker.** JOLTS counts separations, not
people. That includes firing for cause, seasonal and temporary jobs ending,
and the same person twice.
- The CPS Displaced Worker Survey counts people who lost a job to a closure,
  an abolished position or slack work: **6.3 M over 2021–23**
  ([BLS, Aug 2024](https://www.bls.gov/news.release/disp.nr0.htm)), or
  2.10 M a year.
- JOLTS L&D over the same years was 18.2 M a year.
- Their ratio, **0.115** (`DISPLACEMENT_SCALE`), turns an industry's JOLTS
  rate into a settled-worker rate.

**3. Job-loss basis.** We use the same measure as 02_history §4.
- For each month t, the contract pays `B_t = 1` if U3 rises over the window:
  next month for the 1-month contract, 12 months later for the 12-month one.
  This is an at-the-money "above the last print" contract.
- The worker's chance of losing their job in the window is `p_t`, built from
  their industry's L&D rate × 0.115.
- `corr = (mean(B·p) − p̄q) / √(p̄(1−p̄)q(1−q))`. This is the correlation of
  two 0/1 events, which `hedge.joint_states` consumes.
- We also report `P(pays | job lost) = mean(B·p)/p̄`.
- Mar 2020 – Dec 2021 is excluded.

**4. Place basis.** We correlate changes in the local series with changes in
the national one.
- Unemployment: monthly and 12-month changes in percentage points. States use
  seasonally adjusted series against U3. Metros use unadjusted series against
  unadjusted U3, 12-month changes only. Mar 2020 – Dec 2021 is excluded,
  because one simultaneous national shock makes every place look alike.
- CPI: monthly and 12-month log changes. All series are unadjusted, so for
  the monthly changes each calendar month's mean is removed. Otherwise the
  shared seasonal rhythm alone would inflate the correlation.
- `beta` is the slope of the local change on the national change.

**5. Single-strike discount.** One binary contract says only "it happened".
A loss grows with the overshoot. Take a national surprise N and a local
overrun L as standard normals with correlation r. Then
`corr(1{N>0}, max(L,0)) = 0.683·r` (Stein's lemma; checked by Monte Carlo
in the tests). This is the same 0.68 ceiling 02_history found for gas.
`basis_to_national()` returns both `corr` and `basis = 0.683·corr`. A ladder
of strikes, or variance-minimizing sizing, can get closer to `corr`.

## 1. Chance of losing your job, by industry

"Any layoff" counts every layoff and discharge. Use it for seasonal, temp,
gig and new hires. "Settled worker" multiplies the rate by 0.115 (DWS). Use
it for someone in a job they've held a while.

| Industry | Monthly L&D (typical) | Any layoff, 1 yr | …in a recession | Settled worker, 1 yr | …in a recession  | Worst 2020 month |
|---|---|---|---|---|---|---|
| Construction | 3.18% | 32.1% | 40.3% | 4.3% | 5.7% | 10.6% |
| Professional and business services | 2.16% | 23.0% | 26.8% | 2.9% | 3.5% | 6.3% |
| Leisure and hospitality | 1.98% | 21.3% | 24.3% | 2.7% | 3.1% | 32.4% |
| Accommodation and food services | 1.66% | 18.2% | 21.2% | 2.3% | 2.7% | 33.4% |
| All private-sector jobs | 1.47% | 16.3% | 19.9% | 2.0% | 2.5% | 9.9% |
| Retail trade | 1.43% | 15.8% | 19.2% | 2.0% | 2.4% | 8.9% |
| Mining and logging | 1.42% | 15.7% | 19.4% | 1.9% | 2.4% | 10.1% |
| Transportation, warehousing and utilities | 1.39% | 15.4% | 15.6% | 1.9% | 1.9% | 6.6% |
| Trade, transportation and utilities | 1.32% | 14.8% | 17.7% | 1.8% | 2.2% | 7.3% |
| All jobs (total nonfarm) | 1.32% | 14.7% | 17.7% | 1.8% | 2.2% | 8.5% |
| Other services | 1.26% | 14.1% | 14.8% | 1.7% | 1.8% | 18.2% |
| Information (media, publishing, telecom, software publishing) | 1.16% | 13.0% | 13.9% | 1.6% | 1.7% | 6.5% |
| Manufacturing | 1.08% | 12.2% | 19.1% | 1.5% | 2.4% | 6.4% |
| Wholesale trade | 0.96% | 10.9% | 15.4% | 1.3% | 1.9% | 4.6% |
| Private education and health services | 0.78% | 9.0% | 10.3% | 1.1% | 1.2% | 6.2% |
| Financial activities | 0.77% | 8.9% | 12.5% | 1.1% | 1.5% | 2.8% |
| Health care and social assistance | 0.75% | 8.6% | 9.7% | 1.0% | 1.2% | 5.9% |
| Government | 0.48% | 5.6% | 5.8% | 0.7% | 0.7% | 1.0% |

- **Construction is highest on both measures:** 3.2% a month, with seasonal
  churn. That is 32% a year for any layoff and 4.3% a year for a settled
  worker. Next come professional & business services (staffing agencies sit
  here) and leisure & hospitality.
- **Government is lowest:** 0.7% a year for a settled worker. Health care
  and finance are about 1%.
- **The pandemic was a different kind of risk.** Leisure & hospitality lost
  32% of its workforce in a single month (Apr 2020), against a 2% typical month.
  No other recession comes close. That tail is real, but no national
  unemployment contract priced it in advance.
- **Recessions raise the odds less than you'd think.** In 2001 and 2008–09
  they raised them by at most 60%, about 20% for private jobs overall. Manufacturing (+57%), wholesale and
  finance rise most. Health, government and transport barely move.

## 2. A national unemployment contract barely tracks one person's job

| Industry | 1-mo basis (settled) | 12-mo basis (settled) | 1-mo basis (any layoff) | 12-mo basis (any layoff) | P(pays | loss), 1 mo | P(pays), 1 mo | P(pays | loss), 12 mo | P(pays), 12 mo |
|---|---|---|---|---|---|---|---|---|
| Construction | 0.002 | 0.005 | 0.006 | 0.010 | 33.9% | 32.5% | 34.2% | 33.2% |
| Professional and business services | 0.001 | -0.000 | 0.002 | -0.000 | 33.0% | 32.5% | 33.2% | 33.2% |
| Leisure and hospitality | 0.001 | -0.003 | 0.003 | -0.010 | 33.5% | 32.5% | 32.2% | 33.2% |
| Accommodation and food services | 0.001 | -0.003 | 0.003 | -0.010 | 33.6% | 32.5% | 32.2% | 33.2% |
| All private-sector jobs | 0.001 | 0.004 | 0.003 | 0.011 | 33.7% | 32.5% | 34.4% | 33.2% |
| Retail trade | 0.001 | 0.004 | 0.003 | 0.011 | 33.5% | 32.5% | 34.5% | 33.2% |
| Mining and logging | 0.002 | 0.000 | 0.006 | 0.001 | 34.9% | 32.5% | 33.3% | 33.2% |
| Transportation, warehousing and utilities | -0.001 | 0.004 | -0.003 | 0.010 | 31.2% | 32.5% | 34.5% | 33.2% |
| Trade, transportation and utilities | 0.001 | 0.005 | 0.002 | 0.014 | 33.1% | 32.5% | 34.9% | 33.2% |
| All jobs (total nonfarm) | 0.001 | 0.003 | 0.003 | 0.008 | 33.5% | 32.5% | 34.2% | 33.2% |
| Other services | -0.001 | -0.006 | -0.002 | -0.017 | 31.9% | 32.5% | 31.2% | 33.2% |
| Information (media, publishing, telecom, software publishing) | 0.001 | 0.005 | 0.002 | 0.015 | 33.3% | 32.5% | 35.2% | 33.2% |
| Manufacturing | 0.003 | 0.018 | 0.009 | 0.052 | 36.5% | 32.5% | 40.2% | 33.2% |
| Wholesale trade | 0.002 | 0.010 | 0.005 | 0.028 | 34.7% | 32.5% | 37.2% | 33.2% |
| Private education and health services | 0.000 | 0.002 | 0.001 | 0.005 | 32.8% | 32.5% | 34.0% | 33.2% |
| Financial activities | 0.001 | 0.009 | 0.003 | 0.027 | 34.3% | 32.5% | 37.4% | 33.2% |
| Health care and social assistance | 0.000 | 0.003 | 0.000 | 0.008 | 32.7% | 32.5% | 34.4% | 33.2% |
| Government | 0.000 | -0.005 | 0.001 | -0.013 | 33.0% | 32.5% | 30.6% | 33.2% |

- **The monthly basis is 0.000–0.003 in every industry.** In the months
  people in an industry were laid off, "U3 rises" paid 31–37% of the time,
  against 32.5% overall.
- **That is lower than 02_history's 0.02.** That figure assumed a hazard
  elasticity. This one uses the actual timing of industry layoffs.
- **Over 12 months the basis peaks at 0.018 (manufacturing).** Even a
  worker exposed to every layoff reaches only 0.05.
- **The reason:** layoffs are a steady churn of 1–3% a month that barely
  moves with the business cycle. A 0.1-point move in U3 says almost nothing
  about one job.

**A deeper strike doesn't rescue it.** Take a contract that pays if U3 rises
at least 0.5 points within 12 months (Sahm-rule territory, like `KXU3MAX`):

| Industry | Basis | P(pays | loss) | P(pays) | Basis incl. 2020-21 (12-mo, ATM) |
|---|---|---|---|---|
| Construction | 0.025 | 17.8% | 13.7% | 0.010 |
| Professional and business services | 0.009 | 15.4% | 13.7% | 0.004 |
| Leisure and hospitality | 0.007 | 15.1% | 13.7% | 0.020 |
| Accommodation and food services | 0.008 | 15.5% | 13.7% | 0.022 |
| All private-sector jobs | 0.011 | 16.4% | 13.7% | 0.012 |
| Retail trade | 0.012 | 16.6% | 13.7% | 0.012 |
| Mining and logging | 0.012 | 16.7% | 13.7% | 0.010 |
| Transportation, warehousing and utilities | 0.002 | 14.2% | 13.7% | 0.010 |
| Trade, transportation and utilities | 0.010 | 16.3% | 13.7% | 0.012 |
| All jobs (total nonfarm) | 0.010 | 16.2% | 13.7% | 0.010 |
| Other services | 0.003 | 14.6% | 13.7% | 0.011 |
| Information (media, publishing, telecom, software publishing) | 0.003 | 14.6% | 13.7% | 0.011 |
| Manufacturing | 0.024 | 20.5% | 13.7% | 0.022 |
| Wholesale trade | 0.017 | 18.6% | 13.7% | 0.014 |
| Private education and health services | 0.005 | 15.4% | 13.7% | 0.008 |
| Financial activities | 0.016 | 19.1% | 13.7% | 0.012 |
| Health care and social assistance | 0.005 | 15.3% | 13.7% | 0.009 |
| Government | 0.001 | 14.1% | 13.7% | -0.002 |

- **Even then the basis stays at or below 0.025.**
- **Manufacturing is the best case:** P(pays | job lost) is 20.5% against
  13.7% unconditionally.

## 3. State and metro unemployment vs national

| State | Region | Monthly | 12-month | Beta (12-mo) | Monthly incl. 2020-21 | 12-mo incl. 2020-21 | Single-strike basis (monthly) |
|---|---|---|---|---|---|---|---|
| CA | west | 0.60 | 0.97 | 1.25 | 0.97 | 0.98 | 0.41 |
| VA | south | 0.55 | 0.95 | 0.74 | 0.97 | 0.98 | 0.38 |
| PA | northeast | 0.52 | 0.94 | 0.71 | 0.97 | 0.98 | 0.36 |
| AZ | west | 0.49 | 0.94 | 1.12 | 0.96 | 0.95 | 0.34 |
| FL | south | 0.55 | 0.94 | 1.20 | 0.94 | 0.97 | 0.37 |
| ME | northeast | 0.49 | 0.93 | 0.79 | 0.91 | 0.90 | 0.34 |
| OR | west | 0.50 | 0.93 | 1.18 | 0.97 | 0.96 | 0.34 |
| MA | northeast | 0.58 | 0.93 | 0.83 | 0.95 | 0.96 | 0.40 |
| KS | midwest | 0.52 | 0.93 | 0.67 | 0.96 | 0.96 | 0.36 |
| AL | south | 0.48 | 0.93 | 1.09 | 0.96 | 0.94 | 0.33 |
| IN | midwest | 0.52 | 0.93 | 1.11 | 0.96 | 0.95 | 0.35 |
| GA | south | 0.53 | 0.93 | 0.99 | 0.96 | 0.95 | 0.36 |
| DE | south | 0.51 | 0.92 | 0.88 | 0.82 | 0.95 | 0.35 |
| ID | west | 0.52 | 0.92 | 1.16 | 0.96 | 0.91 | 0.35 |
| WI | midwest | 0.50 | 0.92 | 0.96 | 0.96 | 0.95 | 0.34 |
| MO | midwest | 0.47 | 0.92 | 0.86 | 0.97 | 0.96 | 0.32 |
| OH | midwest | 0.52 | 0.92 | 1.02 | 0.96 | 0.96 | 0.35 |
| KY | south | 0.54 | 0.92 | 1.07 | 0.91 | 0.85 | 0.37 |
| NY | northeast | 0.49 | 0.91 | 0.88 | 0.95 | 0.96 | 0.34 |
| NC | south | 0.43 | 0.91 | 1.25 | 0.95 | 0.93 | 0.30 |
| TN | south | 0.53 | 0.91 | 1.04 | 0.96 | 0.96 | 0.36 |
| TX | south | 0.43 | 0.90 | 0.83 | 0.96 | 0.97 | 0.30 |
| IL | midwest | 0.51 | 0.90 | 1.05 | 0.97 | 0.97 | 0.35 |
| SC | south | 0.50 | 0.90 | 1.14 | 0.96 | 0.92 | 0.34 |
| IA | midwest | 0.46 | 0.90 | 0.60 | 0.96 | 0.95 | 0.32 |
| MI | midwest | 0.53 | 0.90 | 1.39 | 0.97 | 0.96 | 0.36 |
| WA | west | 0.53 | 0.90 | 1.03 | 0.96 | 0.96 | 0.36 |
| NV | west | 0.48 | 0.89 | 1.23 | 0.97 | 0.95 | 0.33 |
| MT | west | 0.49 | 0.89 | 0.65 | 0.96 | 0.94 | 0.33 |
| CO | west | 0.50 | 0.89 | 1.02 | 0.83 | 0.92 | 0.34 |
| NE | midwest | 0.43 | 0.88 | 0.39 | 0.91 | 0.88 | 0.29 |
| NH | northeast | 0.47 | 0.88 | 0.63 | 0.96 | 0.95 | 0.32 |
| MD | south | 0.50 | 0.88 | 0.76 | 0.95 | 0.91 | 0.34 |
| VT | northeast | 0.44 | 0.88 | 0.57 | 0.95 | 0.95 | 0.30 |
| NJ | northeast | 0.48 | 0.88 | 1.01 | 0.86 | 0.94 | 0.33 |
| RI | northeast | 0.48 | 0.88 | 1.09 | 0.97 | 0.96 | 0.33 |
| UT | west | 0.44 | 0.88 | 1.10 | 0.94 | 0.87 | 0.30 |
| MN | midwest | 0.50 | 0.88 | 0.66 | 0.83 | 0.94 | 0.34 |
| AR | south | 0.47 | 0.86 | 0.62 | 0.96 | 0.95 | 0.32 |
| CT | northeast | 0.47 | 0.86 | 0.84 | 0.66 | 0.89 | 0.32 |
| SD | midwest | 0.36 | 0.86 | 0.39 | 0.95 | 0.92 | 0.24 |
| WV | south | 0.52 | 0.85 | 0.77 | 0.96 | 0.94 | 0.35 |
| DC | south | 0.40 | 0.84 | 0.81 | 0.89 | 0.85 | 0.27 |
| HI | west | 0.40 | 0.82 | 0.66 | 0.97 | 0.91 | 0.28 |
| OK | south | 0.46 | 0.82 | 0.71 | 0.96 | 0.93 | 0.31 |
| NM | west | 0.41 | 0.81 | 0.70 | 0.85 | 0.81 | 0.28 |
| WY | west | 0.39 | 0.80 | 0.75 | 0.10 | 0.79 | 0.27 |
| AK | west | 0.41 | 0.80 | 0.41 | 0.93 | 0.92 | 0.28 |
| MS | south | 0.27 | 0.73 | 0.73 | 0.90 | 0.86 | 0.18 |
| ND | midwest | 0.23 | 0.72 | 0.23 | 0.96 | 0.91 | 0.16 |
| LA | south | 0.13 | 0.44 | 0.56 | 0.65 | 0.78 | 0.09 |

Median across states: monthly 0.49, 12-month 0.90.

- **Monthly correlations are moderate (about 0.5).** National U3's monthly
  change is mostly CPS sampling noise (±0.1 pt). The LAUS state models smooth
  theirs.
- **Over 12 months the cycle dominates (about 0.9).** California, Virginia,
  Pennsylvania, Arizona and Florida move most closely with the nation.
- **Oil and hurricane states are the outliers:**
  - Louisiana (0.13 monthly / 0.44 over 12 months): Katrina in 2005 and oil.
  - North Dakota (0.23 / 0.72): the shale boom ran against the national cycle.
  - Mississippi (0.27 / 0.73).
  - Wyoming and Alaska (0.80 over 12 months).
- **Beta varies a lot.** A national contract over- or under-hedges a state
  whose unemployment moves more or less than the nation's:
  - Michigan moves 1.39 points per national point.
  - California 1.25, Florida 1.20.
  - North Dakota 0.23, Nebraska and South Dakota 0.39.
  - Size with beta: contracts ≈ beta × the exposure per national point.
- **Including 2020–21 pushes nearly everything to 0.9 or higher.** Don't use
  those numbers. One giant common shock is not a guide to ordinary years.

**Metros**, unadjusted, 12-month changes:

| Metro | 12-month | Beta | 12-mo incl. 2020-21 |
|---|---|---|---|
| san_francisco | 0.97 | 1.20 | 0.98 |
| philadelphia | 0.95 | 0.82 | 0.98 |
| los_angeles | 0.95 | 1.25 | 0.96 |
| phoenix | 0.94 | 1.14 | 0.95 |
| atlanta | 0.94 | 1.04 | 0.96 |
| washington_dc | 0.93 | 0.65 | 0.96 |
| new_york | 0.92 | 1.00 | 0.95 |
| miami | 0.92 | 1.25 | 0.96 |
| dallas | 0.92 | 0.90 | 0.97 |
| chicago | 0.91 | 1.11 | 0.97 |
| las_vegas | 0.91 | 1.30 | 0.95 |
| detroit | 0.89 | 1.60 | 0.96 |
| denver | 0.89 | 1.07 | 0.93 |
| houston | 0.86 | 0.86 | 0.95 |
| seattle | 0.85 | 1.23 | 0.94 |

- **Metros track the nation about as closely as their states over 12
  months.** San Francisco is highest (0.97) and Seattle and Houston lowest
  (0.85–0.86).
- **Detroit (beta 1.60) and Las Vegas (1.30) swing hardest.**

## 4. Regional CPI vs national CPI

| Area | Kind | Since | Monthly | Monthly ex 2020-21 | 12-month | Beta (monthly) | Single-strike basis (monthly) | n (monthly) |
|---|---|---|---|---|---|---|---|---|
| northeast | region | 2001-01 | 0.89 | 0.89 | 0.96 | 0.89 | 0.61 | 306 |
| midwest | region | 2001-01 | 0.92 | 0.91 | 0.98 | 1.14 | 0.63 | 306 |
| south | region | 2001-01 | 0.96 | 0.96 | 0.99 | 1.10 | 0.66 | 306 |
| west | region | 2001-01 | 0.89 | 0.88 | 0.96 | 0.86 | 0.61 | 306 |
| new_york | metro | 2001-01 | 0.74 | 0.75 | 0.90 | 0.77 | 0.51 | 306 |
| los_angeles | metro | 2001-01 | 0.79 | 0.79 | 0.88 | 1.00 | 0.54 | 203 |
| chicago | metro | 2001-01 | 0.76 | 0.75 | 0.95 | 1.01 | 0.52 | 306 |
| dallas | metro | 2001-01 | — | — | 0.92 | — | — | 0 |
| houston | metro | 2001-02 | — | — | 0.89 | — | — | 0 |
| washington_dc | metro | 2001-01 | — | — | 0.93 | — | — | 0 |
| miami | metro | 2001-02 | — | — | 0.92 | — | — | 0 |
| atlanta | metro | 2001-02 | — | — | 0.93 | — | — | 0 |
| san_francisco | metro | 2001-02 | — | — | 0.71 | — | — | 0 |
| seattle | metro | 2001-02 | — | — | 0.88 | — | — | 0 |
| boston | metro | 2001-01 | — | — | 0.90 | — | — | 0 |
| philadelphia | metro | 2001-02 | — | — | 0.93 | — | — | 0 |
| detroit | metro | 2001-02 | — | — | 0.92 | — | — | 0 |

- **The four CPI regions track national CPI closely.** The monthly
  correlation is 0.89–0.96, highest in the South (the largest region by
  weight) and lowest in the Northeast and West.
- **Big metros track less closely.** New York, Los Angeles and Chicago are
  0.74–0.79 monthly, because metro samples are smaller and noisier.
- **Most metros are priced every other month,** so only 12-month figures exist:
  - most are 0.88–0.95;
  - San Francisco is 0.71, its housing cycle running against the national one.
- **The pandemic changes little.** The ex-2020–21 monthly figures match the
  full-sample ones to ±0.01.
- **It compounds with the backtest's ceiling.** 02_history measured a ceiling
  of about 0.8 for national CPI against a loss defined from national CPI.
  A retiree's loss follows their region, so the basis falls further:
  0.683 × 0.9 ≈ 0.61 for a single monthly strike.

## Recommended defaults for hedge inputs

`hedge_defaults(industry, place, contract, horizon_months, exposure)`
returns these numbers with an evidence string the page can show.

| Who / exposure | Contract | `loss_prob` | `basis_correlation` | Evidence |
|---|---|---|---|---|
| Employee, own job (settled) | U3 monthly | `job_loss_prob(industry, 1)`: 0.17%/mo private (0.06% gov – 0.37% construction) | **0.0** (table value ≤ 0.003; never above 0.02) | §2: P(pays \| loss) 33.5% vs 32.5% |
| Employee, own job | U3 12-month / peak-unemployment | `job_loss_prob(industry, 12)`: 2.0%/yr private (0.7% gov – 4.3% construction; ×1.0–1.6 in a recession) | 0.0–0.02 (manufacturing 0.018, deep strike 0.024) | §1, §2 deep strike |
| Seasonal, temp or gig worker | U3 | `kind="any"`: 16%/yr private, 21% leisure, 32% construction | ≤ 0.05 | §1, §2 "any layoff" columns |
| Shop, agent or commission income that follows the state economy | U3 monthly | None (same event) | 0.683 × state monthly corr: **0.34** median; 0.41 CA, 0.30 TX, 0.09 LA | §3 |
| The same | U3 12-month | None | 0.683 × state 12-month corr: 0.61 median; 0.66 CA, 0.30 LA | §3 |
| Retiree, cost of living | CPI monthly | None | 0.61 Northeast, West; 0.63 Midwest; 0.66 South; 0.51–0.54 NY, LA, Chicago | §4 |
| Retiree | CPI 12-month | None | 0.65–0.68 regions; 0.48–0.65 metros | §4 |

What this means for the page:

1. **Split the labor default by exposure, not by market.** Today every labor
   series defaults to 0.1 (`basis_default` in `kalshi_client.py`). For "my
   job", use the industry's measured basis, about 0. The engine then proposes
   nothing, and the page should say plainly that a national unemployment
   contract doesn't insure one job. For "my business follows the local
   economy", use `basis_to_national(state)`: 0.3–0.4 monthly.
2. **Always pass `loss_prob` for job hedges.** Use the industry's
   settled-worker value at the contract's horizon. A monthly contract needs
   the monthly chance, e.g. 0.17% for private jobs, not 2%.
   - Without a separate `loss_prob`, the model treats the job loss as the
     contract's own 32% event. That overstates the risk about 200 times.
   - With it, the small basis makes the hedge correctly worthless.
3. **For CPI, use the region (or metro) basis, about 0.6.** Use it instead of
   the "direct" 0.7. It is already lower than the 0.8 national ceiling
   because of the single-strike discount.

## Caveats

- **Basis is an upper bound for a real person.** Industry-average hazards
  carry no firm- or person-specific shocks. Those add noise that never pays
  on a national contract, which pushes the true job basis even closer to 0.
  Likewise a retiree's own basket (housing, medical) differs from their
  region's CPI.
- **The settled-worker scale is one national ratio.** We apply it to every
  industry, though seasonal churn varies (construction's is surely larger).
  The DWS also undercounts: it relies on recall and counts one loss per
  person in three years. Treat the settled-worker odds as ±50%.
- **Some correlation is built into the data.** LAUS state estimates are
  forced to add up to the national CPS totals. U3 is the revised series, not
  the first print a Kalshi contract settles on. The ATM "rises" contract
  ignores the market's own forecast, so a real strike near the expected print
  pays more like a surprise.
- **The windows overlap.** 12-month windows are serially correlated, so the
  effective sample is about 25 years, not 300 months. There are two
  recessions plus the pandemic. Everything is in-sample.
- **Some months are missing.** October 2025 is absent (the shutdown cancelled
  collection) and is skipped rather than bridged.
- **These are labor and price data, not Kalshi data.** Contract pricing,
  premia and liquidity are covered in 02 and 03.

## Using it

```python
from hone.prediction import labor
labor.job_loss_prob("restaurant server", horizon_months=1)    # 0.0019
labor.basis_to_national("Austin, TX")                          # corr 0.43, basis 0.30
labor.basis_to_national("Ohio", measure="cpi")                 # Midwest: corr 0.92, basis 0.63
labor.hedge_defaults("construction", "CO")                     # loss_prob 0.0037, basis 0.002
```

Re-run with `python research/prediction/labor_study.py` (add `--offline` to
skip the network). Paste the printed tables at the end of `labor.py`.
