# Snow businesses: what earnings calls and filings say

Source: Quartr transcripts, 10-K/10-Q text, S-1 and slides. 57 rows in `snow.csv`, every one with a Quartr source link.

**How to read the elasticity numbers.** Hone's definition is "% revenue lost per 1% that snowfall falls below normal". Most companies give snowfall against normal but give revenue against the prior year. A plain `impact_pct / weather_deviation_pct` is only correct when the prior year was close to normal. Where it was not, I also show a **matched** figure: the % change in revenue divided by the % change in snowfall from one year to the next. That is the better estimate.

Two companies have nothing usable for these keys. **Compagnie des Alpes**: its filings say a serious snow shortage "has not occurred for many years", and I found no quantified episode. **Toro**: it mentions low-snow seasons with no numbers. Three others are **not in Quartr at all**: Peak Resorts, Intrawest and Alamo Group (not checked). **Columbia, Canada Goose and VF** mention warm winters but give no numbers.

---

## ski_resort

**Episodes:** Vail FY2026 (2025/26, the worst Rockies snow season on record), Vail FY2024 (2023/24), Vail Australia 2023, 2024 and 2026, SkiStar spring 2025 (sudden warm spell over a late Easter).

| Row | impact | deviation | ratio |
|---|---|---|---|
| Vail NA pass-holder visits FY26 | -17 | -55 (Rockies) | 0.31 |
| Vail total lift revenue FY26 | -3.5 | -55 | 0.06 |
| Vail paid (non-pass) lift revenue FY26 | -17.5 | -55 | 0.32 |
| Vail Mountain EBITDA FY26 | -11.2 | -55 | 0.20 |
| Vail Mountain revenue FY26 (notes) | -4.8 | -55 | 0.09 |
| Industry Rockies visits FY26 | -24 | -55 | 0.44 |
| Rest-of-industry US lift-ticket visits FY26 | -20 | (~-55 West) | ~0.36 |
| Vail visits FY24 (snow -28% vs prior yr) | -8 | n/a | 0.29 matched |
| Vail Australia Q4 FY26 revenue | 0 | -50 | 0 (offset by pass growth) |

The -55% is the **Rockies** figure. Vail's whole network had a smaller shortfall, because the East had a good year. So the Vail ratios are lower bounds.

- **Recommended:** keep the current calibration, since FY2026 visits fell 13.4% and revenue fell 4.8%, right at the low edge of "5–8% of revenue".
  - As a snowfall elasticity: **0.12** for a pass-heavy operator (range 0.08–0.20).
  - For a resort that sells few passes: **0.35** (range 0.30–0.45). This is from industry Rockies visits (-24%) and walk-up ticket demand (-17% to -20%).
  - **Confidence: medium-high.**
- **Pre-sold share:** passes were 70% of Vail lift revenue in FY2026, up from 65% (FY24–25) and 40–47% (FY16–18). About 75% of visits are pre-committed, about $1.0B pre-sold. That is roughly 40% of all Mountain revenue. Hone's `pass_share=0.25` suits a typical independent resort. It is low for Vail.
- **Profit vs revenue:** profit falls much more than revenue.
  - Mountain EBITDA fell 11.2% on revenue down 4.8% (about 2.3×).
  - An analyst put the in-season flow-through at about 80% of the revenue shortfall, and the CFO agreed.
  - SkiStar's quarter operating profit fell 10% because staff schedules could not be cut.
- **Lost or deferred:** lost.
  - Pass buyers also cut back the next year: spring pass units fell 10% and September units fell 12%.
  - So a bad year also dents the following year's pre-sales.
- **Caveats:**
  - FY2026 also includes new ticket discounts and a mix shift (paid ticket price -8.8%).
  - FY2024 snowfall is only given against the prior year, which had heavy snow.
  - SkiStar's loss was melt at season end, mixed with the Easter calendar.

## ski_instructor

**Episodes:** Vail FY2026 (full year, Q2 and Q3) and Vail Australia 2023. SkiStar spring 2025 on staffing. There are no data on instructors' own pay. I used two proxies: ski school (lesson) revenue, and resort labor expense and hours.

| Row | impact | visits | ratio to visits | ratio to resort revenue |
|---|---|---|---|---|
| Ski school FY26 | -10.3 | -13.4 | 0.77 | 2.1× (rev -4.8) |
| Ski school Q3 FY26 (quarter) | -11.5 | -15 | 0.77 | 1.6× (rev -7) |
| Ski school season-to-date to 1 Mar 2026 | -8.2 | -12 | 0.68 | 1.6× (rev -5) |
| Ski school Australia Q1 FY24 | -19.6 | -33.7 | 0.58 | 1.35× |
| Mountain labor FY26 (hours) | -3.2 | -13.4 | 0.24 | 0.67× |
| Mountain labor Q2 FY26 | -4.1 | -13 | 0.32 | 0.8× |

Against snowfall (Rockies -55%), ski school's ratio is about 0.19–0.21.

- **Recommended `elasticity_scale`:** **1.5** (range 0.7–2.2). **Confidence: low.**
  - Lesson revenue falls 1.4–2.1× as much as resort revenue, because lessons are not pre-sold. That is the high end.
  - Total labor cost falls only 0.7–0.8× as much, because resorts keep full staff and trim hours. That is the low end.
  - Instructors paid by the lesson or with privates sit near the high end. Salaried or guaranteed-hours staff sit near the low end.
- **Pre-sold share:** small. Lessons are mostly bought close to the day.
- **Profit vs revenue:** for a person, income is the revenue line. Vail's 10-K says the cut came through "reduced labor hours", not layoffs. Vail reported "full staffing". SkiStar said scheduled staff could not be cut mid-season.
- **Lost or deferred:** lost.
- **Caveats:** this is all one operator (Vail). Ski school revenue also reflects lesson price rises. No source gives instructors' pay directly.

## mountain_retail

**Episodes:** Vail FY2026 (retail/rental, dining, retail sales, resort-town condo lodging), Vail Australia 2023 (dining), SkiStar spring 2025 (unquantified: "did not sell any ... cold products"), Dick's warm winters 2012/13 and 2015/16 (national cold-weather goods, unquantified: "down double digits").

| Row | impact | ratio to visits | ratio to resort revenue |
|---|---|---|---|
| Retail/rental FY26 | -6.5 | 0.49 | 1.35× |
| Dining FY26 | -7.6 | 0.57 | 1.6× |
| Retail merchandise FY26 | -9.6 | 0.72 | 2.0× |
| Retail merchandise Q2 FY26 | -11.2 | 0.86 | 2.2× |
| Dining Q3 FY26 | -10.7 | 0.71 | 1.5× |
| Managed condo rooms FY26 | -9.6 | 0.72 | 2.0× |
| Dining Australia Q1 FY24 | -7.0 | 0.21 | 0.5× (diluted by summer) |

Against snowfall (-55% Rockies), these ratios are about 0.12–0.19.

- **Recommended `elasticity_scale`:** **1.3** (range 0.5–2.0). **Confidence: low-medium.**
- **Surprise:** the current 0.7× guess looks too low. Resort revenue is cushioned by pre-sold passes. Shops, restaurants and lodging are not, so they fall with visits (0.5–0.85× visits), which works out to 1.2–2.0× the resort's revenue loss.
- **Pre-sold share:** near zero for shops and restaurants. Lodging is partly booked ahead, but both price and occupancy fell.
- **Profit vs revenue:** Vail's retail cost of goods fell in line with sales (-9.7% vs -9.6%), so gross margin held. Fixed rent and staff mean operating profit falls faster than revenue (not measured).
- **Lost or deferred:**
  - Lost. Dick's CEO: people buy cold-weather gear "very close to need".
  - Unsold stock is carried into next season. That ties up cash, but the sale itself is lost.
- **Caveats:**
  - These are resort-owned outlets. Independent town shops may differ.
  - Vail's retail line includes some city stores.
  - Dick's is temperature-driven and national, with no snowfall measure.

## snow_removal

**Episodes:**
- BrightView in 9 seasons or periods: CY2016, 9M2017, 6M2018, FY2019, FY2020, Q1 FY22, Q2 FY22, Q1 FY23, Q2 FY23, plus FY2026 upside.
- Compass Minerals deicing salt, 2023 and 2024.
- Douglas Dynamics plow equipment, 2023 and 2024.

Matched BrightView elasticities (% revenue change ÷ % snowfall change vs prior year):

| Period | snowfall (% of normal) | revenue | matched elasticity |
|---|---|---|---|
| 9M 2017 | 100→58 (-42%) | -30.4% | 0.72 |
| CY2016 | 112→94 (-16%) | -18.6% | 1.16 |
| 6M 2018 (upside) | 63→84 (+33%) | +29.3% | 0.88 |
| FY2020 | 86.3→61.6 (-29%) | -33.5% | 1.17 |
| Q1 FY22 | -59% YoY (56% of 30-yr) | -43% organic | 0.73 |
| Q2 FY22 | -11% YoY | -13% organic | 1.18 |
| Q1 FY23 (upside) | ~56→~85 (+52%) | +50% organic (+44% volume) | 0.85–0.96 |
| Q2 FY23 | 91→50 (-45%) | -33.3% total / -37.2% organic | 0.74–0.83 |
| FY2019 | 87.1→86.3 (flat) | -2.9% | n/a (fewer events) |

Compass Minerals salt volumes: -21% on snow events about 25% lower than the year before, so about **0.85**.

- **Recommended:** **0.9** (range 0.7–1.2). **Confidence: high.**
  - The median of 8 matched points is 0.92.
  - The single clean vs-normal point (9M2017, prior year exactly 100% of normal) gives 0.72.
  - Lower values come from periods with more fixed contracts. The current 1.0 is fine, or 0.9.
- **Pre-sold share:**
  - BrightView snow revenue is 60% variable and 40% fixed (FY2026), with a target of about 67% fixed.
  - A business with more fixed or seasonal contracts should scale elasticity down by roughly its variable share.
- **Profit vs revenue:**
  - BrightView says 20–30% of a change in snow revenue reaches EBITDA. In Q2 FY23, $19M of EBITDA was lost on $77M of revenue.
  - So 70–80% of lost snow revenue is offset by lower subcontractor, labor and materials cost.
  - Hone's `variable_cost_share=0.5` is low for a subcontract-heavy firm. It may be right for an owner-operator.
  - Douglas Dynamics (a manufacturer) is the opposite case: Attachments EBITDA fell 35% on sales down 24%.
- **Lost or deferred:**
  - For service providers and salt, lost.
  - For equipment makers, deferred. Douglas expected half of 2023's lost volume back in 2024, but a second bad winter pushed it out again. Its in-season quarter fell 58% in a season only 14% below normal nationally, with the East Coast at record lows.
  - Douglas measures equipment demand. Do not use it for operator revenue.
- **Caveats:**
  - BrightView's measure is its own footprint-weighted NOAA snowfall.
  - Event frequency matters as well as total inches. FY2019 revenue fell with flat inches.
  - Acquisitions are excluded where "organic" figures were given.
