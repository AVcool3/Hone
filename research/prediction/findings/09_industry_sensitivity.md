# 09 — How much do industries lose when weather or the economy turns? (public company results, 2008–2026)

**Question.** `research/prediction/segments.py` (`OCCUPATIONS`: `income`, `loss_frac`, `basis`) and
`hone/prediction/quote.py` (`BUSINESSES`: elasticity, basis, margin, `max_loss_frac`) run on guessed sensitivities.
Study 06 replaced the ski-resort guesses with Vail's filings. This note does the same, more broadly and less deeply, for
the other groups Hone prices: hotels, airlines, rideshare drivers, realtors and mortgage brokers, recruiters and
contractors, and the weather-sensitive businesses being added to the quote engine (outdoor venues, landscaping and snow
removal, HVAC, construction, farms).

**Method.** For each industry I picked the episode where the driver moved most, and took 2–3 companies' reported
results from Quartr, plus SEC filings and company releases where Quartr's history is too short. Each figure is
compared with the driver's move over the same period. Driver series come from FRED: unemployment (UNRATE), payrolls
(PAYEMS), retail gasoline (GASREGW), the 30-year mortgage rate (MORTGAGE30US), temp-help and accommodation jobs.

**Data** (every row has its source URL):
* `research/prediction/data/industries/episodes.csv` — 67 raw before/after figures.
* `research/prediction/data/industries/sensitivity_summary.csv` — the derived sensitivities.
* `research/prediction/data/industries/management_quotes.csv` — 23 quotes from calls and filings.
* `research/prediction/data/industries/drivers.csv` — annual values of the driver series, 2006–2026.

---

## Bottom line

| Industry (who it's for) | Driver | Bad-episode move | Measured sensitivity | Profit hit | Pre-sales / contracts buffer | Sources |
|---|---|---|---|---|---|---|
| **Hotels** (hospitality workers) | unemployment | 2009: U3 5.8% → 9.3% (+3.5pp) | RevPAR −17% to −20% → **−5 to −6% per pp of unemployment**. Hotel jobs −6% to −8%, about 0.3× the RevPAR fall | Host EBITDA −42% on revenue −19% (2.2× leverage); Marriott incentive fees −$157m | none: bookings are weeks to months ahead | [H1][H2][H3] |
| Hotels, tail case | travel shutdown | 2020 | revenue −50% (Marriott), −54% (Hilton), −70% (Host); hotel jobs −43% from Feb to Apr | losses | none | [H4][H5][H6] |
| **Airlines** | demand (recession) | 2009 | revenue −18% to −19% → about −5% per pp of unemployment | losses | 1–3 months of advance sales | [A1][A2] |
| Airlines | jet fuel | 2022 vs 2019: fuel expense +35% on 15% less capacity | **revenue up**: fares recaptured more than all of the fuel increase (+$3.6bn revenue vs about +$3.0bn fuel at Delta) | operating margin 14.1% → 7.2% | none (fuel is a cost) | [A3][A4] |
| **Rideshare / delivery drivers** | gas price | Q1 2026: +42%. 2022: +31% (annual average), +66% at the June peak | fuel rose from 13.2% to **17.4% of gross pay**. A driver loses about **0.10–0.13 × the % gas rise** of gross pay: ≈ −4% in a bad gas year, −8.6% in peak weeks | the driver pays all of it | 2022 surcharges of $0.45–0.55 per trip offset much of it for about six months. 2026 relief was token | [R1][R2][R3][R4] |
| **Realtors** | mortgage rate | 2021 → 2023: rate 2.96% → 6.81% (+3.85pp) | existing-home sales −33%. Compass revenue per agent **−39%**, transactions per agent −36% (−8 to −10% per pp). Commissions paid per agent −22% in 2023 alone. NAR median income only −1%, but survivor-biased | Anywhere operating income $435m → −$122m | none: the pending-sale pipeline is 1–2 months | [E1][E2][E3][E4][E5] |
| **Mortgage brokers** | mortgage rate | same | Rocket revenue **−71%** (2021 → 2023) | profits erased | none | [E6] |
| **Recruiters** | unemployment / payrolls | 2009 (+3.5pp; payrolls −4.3%) | permanent-placement fees **−57%** (−16% per pp). Total staffing revenue −21% to −34% | Robert Half pre-tax income −84% | none for permanent placement | [S1][S2][S3] |
| Recruiters | **hiring slump with payrolls still growing** | 2023–25: U3 +0.6pp, payrolls +2.2%/+1.2%/+0.5% | permanent-placement fees **−22%, −14%, −10%** (−39% cumulative) | Robert Half operating income $891m → $76m | none | [S4][S5] |
| **Contract / temp workers** | unemployment | 2009 | temp-help jobs **−22.5%** (−34% peak to trough). That is 5× the fall in all payrolls | — | assignments last weeks | [S6] |
| **Outdoor venues / amusement parks** | rainy, stormy or hot days | Q2 2025: 18.6% of operating days hit by weather, 49 full closures | attendance −9% for the quarter, **−12% in the six bad weeks** → **about 0.5% of attendance per 1% of operating days hit** | legacy Cedar Fair revenue −5%, EBITDA −12%. Lost visits carry 55–80% margin | season passes move visits later in the year, but pass sales were lost (−300k units) | [P1][P2][P3] |
| Outdoor venues, typical bad stretch | weather (management estimates) | 2023–26 | 3–10% of a quarter's attendance; ~4.5% of a year's (Six Flags 2023) | about $15m EBITDA in one quarter | as above | [P4]–[P8] |
| **Snow removal** | snowfall | FY2017, FY2020: 58–62% of the 10-year average | revenue **−30% to −34%** year on year; **elasticity 0.7–1.2** | smaller than the revenue hit: subcontractor costs fall with it | some fixed-fee seasonal contracts | [L1][L2][L3] |
| **Lawn and garden** | late or cold spring | 2018: season started 4–6 weeks late | point-of-sale −15% by mid-April, **flat for the full year** | small | demand is deferred, not lost | [L4] |
| **HVAC** | cooling degree days (CDD) | Q3 2019: US CDD −5%, Northeast and upper Midwest −10%, Texas +9% | residential revenue in Texas +10% → **about 1:1 by region**. Northern states +15–20% in hot 2018 | — | replacements can be put off for a while | [V1][V2] |
| **Construction** | rain days | record-rain quarters 2018–20 | aggregates shipments −1% to −7% in the quarter; caught up the next quarter | under-absorbed fixed costs | backlog: work is deferred | [C1][C2][C3] |
| **Farms** | drought | 2012 | corn yield −16% year on year (about −25% vs. expectations) | about $17bn of crop-insurance claims; prices rose | federal crop insurance and higher prices offset it | [F1][F2] |

**Three patterns cut across industries.**

1. **Whether lost demand is gone or only delayed decides how big the loss is.**
   - *Lost for good:* sales that happen on a given day. Park visits, hotel nights, rides and plowing are perishable.
   - *Mostly delayed:* sales that wait for better conditions. Lawn and garden, homebuilders and aggregates catch up
     within the season.
   - This is the main thing the quote engine should encode per business, as study 06's pass share did for resorts.
2. **Profit falls 1.5–2.5× as much as revenue for asset-heavy companies,** and lost visits are high-margin.
   - Host: EBITDA −42% on revenue −19%.
   - Six Flags: 55–80% of the revenue from a lost visit was profit.
   - Asset-light and commission businesses pass most of the hit to their workers.
3. **For commission workers, the person's loss is larger than the company's.**
   - Compass's revenue fell 24% while revenue per agent fell 39%, because the company kept adding agents.
   - Permanent-placement fees fall about twice as fast as staffing revenue.
   - Company totals understate a single realtor's or recruiter's loss.

---

## 1. Hotels: RevPAR vs. unemployment (2009; 2020 as the tail case)

| | 2008 | 2009 | Change |
|---|---|---|---|
| Host comparable RevPAR | | | **−19.9%** (occupancy −5.4pp, rate −13.5%) [H1] |
| Host revenue | $5,140m (implied) | $4,158m | −19.1% [H1] |
| Host Adjusted EBITDA | $1,365m | $798m | **−41.5%**; comparable margins −520bp [H1] |
| Marriott worldwide systemwide RevPAR (constant $) | | | **−17.3%** [H2] |
| Marriott segment revenues | $12,817m | $10,831m | −15%; incentive fees −$157m, base and franchise fees −$156m [H2] |
| US accommodation jobs (annual average) | 1,868k | 1,762k | −5.7% (−7.6% peak to trough) [H3] |
| US unemployment (annual average) | 5.8% | 9.3% | +3.5pp [D] |

* **Sensitivity.** RevPAR fell 5.0–5.7% per percentage point of unemployment.
  - Owners (Host) lost about twice that share of profit.
  - Asset-light franchisors (Marriott) lost revenue in proportion to RevPAR. Their profit-linked incentive fees fell
    $157m, as much as base and franchise fees combined, on a much smaller base.
* **Workers.** Hotel employment fell about 0.3× as much as RevPAR. The rest of a worker's loss comes through hours,
  overtime and tips, which track occupancy and food-and-beverage revenue (Host F&B −20.4%).
* **COVID, 2020.**
  - Marriott RevPAR was −84% in Q2 and −64% in Q4 [H4].
  - Revenue fell 50–70% [H4][H5][H6], and hotel jobs fell 43% from February to April [H3].
  - This is a tail scenario, not a recession, and an unemployment contract would have paid in it.
* **Buffer:** none worth modeling.

## 2. Airlines: demand shocks and fuel

* **Demand (2009).**
  - United's revenue fell 19.1% ($20.2bn → $16.3bn) [A1]. Its first-half passenger unit revenue was −16.1%.
  - Delta reported $28bn vs. $34bn (−18%); that comparison is distorted by the Northwest merger [A2].
  - The sensitivity is about −5% of revenue per point of unemployment, like hotels.
* **Fuel is passed through, not absorbed, when demand is strong.**
  - In 2022, Delta's adjusted fuel price was $3.36/gal and its fuel expense was +35% vs. 2019 on 15% less capacity.
    Revenue still rose to $50.6bn vs. $47.0bn [A3].
  - Management called it "the recapture of higher fuel prices" [A4].
  - The operating margin still halved, from 14.1% to 7.2%.
  - In 2008, by contrast, fuel rose 42% ($2.24 → $3.18/gal) into weak demand, and Delta lost $8.3bn at the operating
    line, most of it a goodwill impairment [A5].
* **For Hone:** airline workers (pilots, flight attendants) are protected by seniority and contracts. The relevant
  driver is a demand shock, not fuel. No occupation needs this today.

## 3. Rideshare and delivery drivers: gas prices

This is the clearest natural experiment, and it has happened twice.

* **Q1 2026** (oil shock from the Middle East war):
  - Regular gasoline rose from $2.81 (January average) to $3.99 (week of Mar 30), +42% [D].
  - Gridwise's driver panel shows fuel's share of rideshare gross hourly pay rising **from 13.2% to 17.4%**, and for
    delivery from 11.2% to 15.6% [R1]. A full-time driver faced "$20 to $30 in extra weekly fuel costs" [R1].
  - So: −4.2% of gross pay (−4.8% of pay net of fuel) for a 42% gas rise.
  - The fuel share rose 32% for a 42% price rise, so it scales almost one-for-one with gas.
* **2022:**
  - Gasoline averaged $3.95 vs. $3.01 in 2021 (+31%) and peaked at $5.01 in June (+66%) [D].
  - At a 13% base fuel share, a driver lost about **4% of gross for the year and 8.6% in the peak weeks**.
  - From Mar 16, 2022, Uber added a **$0.45–0.55 surcharge per trip ($0.35–0.45 per Eats order), 100% to drivers** [R2].
    Lyft ran a per-ride surcharge from March and removed it in Q3 "with gas prices moderating" [R3].
  - My estimate, assuming ~2 trips an hour and $25–30 an hour of gross pay: $0.50 a trip is about $1 an hour, or
    **3–4% of gross**. That offset most of the annual-average rise while it lasted, but not the June peak.
* **2026 relief was token.**
  - Lyft's whole 2026 fuel program was "about $20 million... largely co-funded... by partners" [R4]. The CEO said:
    "We did not actually see a huge issue, unlike maybe prior fuel shocks" [R4].
  - Gridwise reports DoorDash relief reaching ~40% of workers with a $15/week maximum [R1].
  - Uber says fuel hit driver supply in Brazil and India [R5]. When gas prices hurt, drivers drive less.
* **The platforms' own revenue barely notices.** The driver absorbs the cost.

**Implication:** a bad gas year costs a driver **4–5% of gross pay** (5–9% in the peak months), not 10%. The link
to the pump price is mechanical. Basis is limited only by local vs. national prices and by surcharges or relief.

## 4. Real-estate agents and mortgage brokers: rates and home sales (2022–23)

| | 2021 | 2022 | 2023 | 2021→23 |
|---|---|---|---|---|
| 30-year mortgage rate (annual average) | 2.96% | 5.34% | 6.81% | +3.85pp [D] |
| US existing-home sales | 6.12m | 5.03m | 4.09m | **−33%** [E1] |
| Compass revenue | $6,421m | $6,018m | $4,885m | −24% [E2] |
| Compass average principal agents | 11,180 | 13,296 | 13,973 | +25% [E2] |
| Compass revenue per agent | $574k | $453k | $350k | **−39%** [E2] |
| Compass transactions per agent | 20.1 | 15.9 | 12.8 | −36% [E2] |
| Compass commissions paid per agent (excluding stock comp) | | $367k | $286k | −22% in one year [E3] |
| Anywhere revenue / cost of revenue (mostly commissions) | $7,983m / $4,753m | $6,908m / $4,415m | $5,636m / $3,664m | −29% / −23% [E4] |
| Anywhere operating income | $435m | −$323m | −$122m | [E4] |
| eXp revenue | | ~$4.6bn | $4.28bn | −7%; agents +2% [E5] |
| NAR median REALTOR gross income | | $56,400 | $55,800 | −1%; median transactions 12 → 10, brokerage sales volume −26% [E7] |
| Rocket Companies revenue (originations) | $12,914m | $5,838m | $3,799m | **−71%** [E6] |

* **Sensitivity.** A typical producing agent lost about 20–25% of commissions in the worst year and 35–40% over the
  two-year episode: −8 to −10% per point of mortgage rate. Mortgage originators lost about 70%.
* **The NAR median barely moved.** That is survivorship: agents who quit drop out of the survey. The median member's
  transactions still fell 17% and her sales volume 26%.
* **The hit lags the rate.** Sales fell 18% in 2022 and another 19% in 2023, and stayed near 4.0m a month through
  2025–26 (Sep 2026: 3.99m SAAR [D]) with rates around 6.5%. A rate contract that pays when rates are high lines up with
  the multi-year slump. One that pays only on a *change* in rates would miss 2024–26.
* **Buffer:** none beyond a 1–2 month pipeline of pending sales.

## 5. Staffing: recruiters and contractors

| | 2008 | 2009 | Change |
|---|---|---|---|
| Robert Half revenue | $4.6bn | $3.0bn | −34% [S1] |
| — temporary staffing | $3.6bn | $2.5bn | −32% [S1] |
| — **permanent placement** | $427m | $182m | **−57%** [S1] |
| Robert Half pre-tax income | $419m | $67m | −84% [S1] |
| ManpowerGroup revenue | | $16.0bn | −26% (−21% in constant currency) [S2] |
| Kelly revenue, first nine months | | $3.12bn | −26.4% [S3] |
| US temp-help jobs (annual average) | 2.35m | 1.82m | **−22.5%** (−34% peak to trough) [S6] |
| US payrolls / unemployment | | | −4.3% / +3.5pp [D] |

* **Recessions.**
  - Total staffing revenue fell 6–10% per point of unemployment.
  - Permanent-placement fees fell about 16% per point. Recruiters are paid on these fees.
  - Robert Half's 10-K: permanent placement is "even more sensitive to economic and labor market conditions" [S1].
  - In 2020, permanent placement fell 30.6% and total revenue 15.9% [S7].
* **2023–25: the slump that payrolls missed.**
  - Permanent-placement revenue fell 21.7% in 2023, 14.1% in 2024 and 9.8% in 2025: $725m → $440m, −39% [S4][S5].
  - Over the same years, payrolls grew 2.2%, 1.2% and 0.5%, and unemployment rose only 0.6pp [D].
  - Temp-help jobs fell 19% (3.09m → 2.50m) [S6].
  - Robert Half's operating income fell from $891m to $76m [S5].
  - A contract on negative payrolls or on high unemployment would not have paid at any point. For a recruiter, the
    driver that matters is hiring volume (job openings, quits), not employment levels.
* **Contract workers.**
  - Temp jobs move about 5× as much as total payrolls, so a contractor's job-loss risk is much more cyclical than a
    typical worker's.
  - My calculation: if a contractor's yearly chance of losing work is ~25–30% in a recession year vs. ~10–12% otherwise,
    and recessions come one year in seven, then the correlation between a "U3 spikes" event and "this person loses
    income" is **about 0.13–0.21**.
  - That is well above the 0.02 measured for a generic worker (study 02).

## 6. Weather-sensitive businesses

### Outdoor venues and amusement parks (rain, storms, heat)

* **Q2 2025 at Six Flags is the cleanest episode in the data.**
  - "Close to 20% of our operating days in the second quarter were impacted by weather, including 49 days in which parks
    were forced to close entirely" (12 closure days in Q2 2024) [P1]. Weather hit 379 of 2,042 days, 60% of them on
    Fridays to Sundays [P2].
  - Attendance in the six bad weeks was **−12%**, while the first seven weeks were flat [P2]. The quarter was −9%
    (−1.4m visits).
  - At the legacy Cedar Fair parks, attendance fell 8%, but revenue fell only 5.2% ($572m → $542m) because ticket prices
    and in-park spending rose. EBITDA fell 12.2% ($205m → $180m), "entirely due to" lower attendance and revenue [P3].
  - This was partly fewer scheduled operating days, so it is an upper bound on the weather effect.
* **Rule:** attendance lost ≈ **0.5 × the share of operating days hit by weather**, revenue about 0.6× attendance
  (per-capita spending rises when the visitors who do come are committed).
* **Profit.**
  - The CFO: lost visits carry "55%–70% margin" [P1].
  - Guidance rule: "a 100-basis-point decline in second half attendance, or approximately 300,000 visits, could result in
    a $10–15 million decline in Adjusted EBITDA" [P2]. That is $33–50 of EBITDA per lost visit vs. ~$62 of per-capita
    spending.
* **Typical bad stretches**, all management estimates:
  - Six Flags (legacy), 2023: weather took "over 1 million guests" of 22.2m (≈4.5% of the year) [P4]; 5–6 points of Q2
    attendance [P5]; 180k of 1.6m visits in Q1 (≈10%) [P6].
  - Six Flags, April 2025: 175k visits [P7].
  - United Parks: 140k visits in Q1 2026 (revenue −3.0%) [P8]; 167k in Q4 2024 (Hurricane Milton) [P9].
* **Pre-sales buffer: weaker than for ski passes.** Pass holders shift their visits later in the season. But weather
  also cuts *sales of next season's passes*: "more than 300,000 season pass sales down in the months of May and June"
  [P1], and an active pass base −8% [P2]. Visitors on one-day tickets disappear almost entirely: "you lose almost all
  your demand tickets" [P1].

### Snow removal and landscaping

* **BrightView snow removal** (snowfall as % of BrightView's 10-year average, its own footprint):

  | Period | Snowfall | Snow revenue | YoY elasticity |
  |---|---|---|---|
  | 2016 vs 2015 | 94% vs 112% (−16%) | $315m → $257m (**−18.6%**) | 1.16 [L1] |
  | 9M 2017 vs 9M 2016 | 58% vs 100% (−42%) | $209m → $146m (**−30.4%**) | 0.72 [L2] |
  | 6M 2018 vs 6M 2017 | 84% vs 63% (+33%) | $189m → $244m (+29.3%) | 0.88 [L3] |
  | FY2020 vs FY2019 | 61.6% vs 86.3% (−29%) | $245m → $163m (**−33.5%**) | 1.17 [L4] |

  - Revenue moves about one-for-one with snowfall, and the response flattens at the low end (−30% at 58% of normal).
  - Profit falls less than revenue, because subcontractor, salt and fuel costs fall with the storms. In 2016, the cost
    of services fell $81.7m "due to a decrease in labor costs from the reduced use of subcontractors for snow removal"
    [L1].
  - Landscape maintenance revenue, which is contracted, barely moved in those years.
* **Lawn and garden (Scotts).** In 2018, consumer purchases "were down 15... midway through April... by far the latest
  start to a season I have ever witnessed... [and] have come all the way back to flat" [L5]. A late spring moves demand
  to later in the season instead of destroying it. The exposed party is a business paid by the visit during the delay
  (crews, nurseries with perishable stock).

### HVAC (cool summers, mild winters)

* Lennox, Q3 2019: "degree cooling days in July and August... down about 10% [in the Northeast/upper Midwest]... had an
  impact on our revenue... Texas, cooling degree days were up 9% in Q3, and our revenue was up 10%" [V1]. Nationally,
  cooling degree days were about −5% [V1].
* Watsco, hot northern summer 2018: "the weather sensitive states... were up materially... mid-teens, low twenties" vs.
  Sun Belt states "fairly flat" [V2].
* **Sensitivity:** regional replacement and service revenue moves about 1:1 with the cooling-degree-day anomaly.
  Company-wide it is diluted to about 0.3–0.5. A contractor's bad season is a *mild* summer or winter.

### Construction (rain days)

* Martin Marietta: aggregates shipments **−7.2%** (Mid-America, Q2 2020, "near-record rainfall"), −3.2% (Southeast,
  Q1 2020), −1.2% (West, Q4 2018, Texas's record October rain) [C1].
* Vulcan: "17, 18, 19, 20-plus more rain days in the third quarter... you're seeing some of that work catch up in
  October" [C2].
* Homebuilders: weather pushes closings into the next quarter (Green Brick, 40 homes in Q1 2021) [C3].
* **For a firm,** a wet quarter costs a few percent and mostly comes back, though fixed costs go unabsorbed (Martin
  Marietta took an $11m inventory charge after a wet 2018 [C1]). **For an hourly crew member,** a lost day is lost pay:
  the loss is about excess rain days ÷ scheduled days.

### Farms (drought)

* 2012: US corn yield 123.4 bu/acre vs. 147.2 in 2011 (−16%; "about one-fourth" below expectations), the lowest since
  1995 [F1].
* Corn crop-insurance claims were $11.7bn, 68% of all claims, so roughly $17bn in total [F2]. Prices spiked, so many
  farms' revenue fell far less than yield. This is the only industry here with a large existing insurance program, and
  Hone's quote must net it out, as it does pass revenue for resorts.

---

## 7. Caveats: companies are not workers

* **Survivorship and composition.** Company totals mix the drop in activity with changes in headcount. Compass kept
  adding agents, so revenue per agent fell faster than revenue. NAR's survey loses the agents who quit. The worker
  figures here are per-agent, per-job or per-hour proxies, not individual earnings records.
* **Companies diversify; people don't.** Six Flags' roughly 40 parks and BrightView's national footprint average out local
  weather, as Vail's regions did in study 06. One park, one landscaper or one HVAC contractor will see swings about 1.5–2×
  larger.
* **Management weather estimates are self-serving.** "Weather cost us X visits" is measured against the company's own
  normal, usually a five-year average [P6], and management has a reason to blame weather [P1]. The Q2 2025 six-weeks vs.
  seven-weeks split is the most credible test in this set.
* **Confounders.** 2009 mixes recession with credit stress; 2020 is a shutdown; 2022 gas mixes with strong post-COVID
  demand (higher fares, higher surge pricing for drivers); 2023 real estate mixes rates with low inventory; Q2 2025 parks
  mixes weather with fewer scheduled days and a "value-conscious" consumer.
* **Breadth over depth.** Most industries have 1–3 episodes and 2–3 companies. Treat the ranges as order-of-magnitude
  calibration, not estimates with standard errors. Some 2008–09 bases are implied from the reported percentage change
  (marked "implied" in `episodes.csv`).

---

## 8. Parameter recommendations (ranked by how much they change results × how strong the evidence is)

**`segments.OCCUPATIONS`**

1. **`recruiter`: lower `basis` from 0.45 to about 0.30, and raise `loss_frac` from 0.35 to 0.40.**
   - In 2023–25, permanent-placement fees fell 39% while payrolls kept growing; a payrolls market would never have paid.
   - In recessions the loss is 0.55 (2009: −57%); in a slump, 0.2–0.4 a year.
   - Consider a job-openings or quits proxy if Kalshi lists one.
2. **`rideshare`: lower `loss_frac` from 0.10 to 0.05, and keep `basis` at 0.6.**
   - Fuel is 11–17% of gross pay. A bad gas year (+30–40%) costs 4–5% of gross; the peak months cost 8–9%.
   - Measured twice (2022 by calculation, Q1 2026 in Gridwise's panel). Surcharges in 2022 offset much of it; 2026
     relief was token.
   - The 0.10 value assumed roughly a doubling of gas prices.
3. **`realtor`: split into two occupations.**
   - `realtor`: `loss_frac` **0.30** per bad-rate year (0.20–0.25 in the worst single year; 0.35–0.40 cumulative over two
     years).
   - `mortgage_broker`: `loss_frac` about **0.55–0.60** (Rocket −71%).
   - Keep `basis` around 0.5 for a rate-*level* contract; it should be lower for one that pays on a rate *change*,
     because sales stayed near 30-year lows for years after rates stopped rising.
4. **`contractor`: raise `basis` from 0.05 to about 0.12; keep `loss_frac` at 0.5** (it is conditional on losing work).
   - Temp-help jobs fall about 5× as much as total payrolls (−22.5% in 2009), so a contractor's income is far more tied
     to unemployment than the generic worker behind the 0.02 measured in study 02.
   - 0.12 comes from the calculation in §5; label it derived, not measured.
5. **Add `hospitality`** (hotel or restaurant worker, unemployment market): `income` about $35k, `loss_frac` about
   **0.15**, `basis` about 0.10–0.15 (an estimate by analogy with the contractor calculation, not measured).
   - Hotel jobs fell 6–8% in 2009 against RevPAR −17% to −20%; for those who keep their jobs, hours and tips fall roughly
     with occupancy.
   - Use 0.4–0.5 for a COVID-style tail.

**`quote.BUSINESSES`** (the weather businesses being added)

6. **`snow_removal`: keep `fixed_elasticity` 1.0** (measured 0.7–1.2) **and lower `max_loss_frac` from 0.8 to about
   0.5.**
   - The worst observed years, at 58–62% of normal snowfall, were −30% to −34%. Losses flatten, as they did for ski.
   - Because subcontracting makes costs variable, the profit at risk is about half the revenue lost. Add a
     `variable_cost_share` of about 0.5, or lower the effective elasticity used against the margin cushion to about 0.5.
   - Ask for a contracted (fixed-fee) share, damped like `pass_share`.
7. **`outdoor_venue` (park, attraction, recurring-season venue):**
   - driver: the share of in-season operating days with rain or storms (or heat-index closures);
   - `elasticity` about **0.5** (attendance), revenue about 0.3–0.4 after per-capita gains;
   - `max_loss_frac` about **0.15** per season (the worst 6 weeks were −12%, a full year about −4.5% at a diversified
     operator; double it for a single site);
   - `margin` about 0.25–0.35; treat 0.6–0.8 of lost revenue as lost profit;
   - `pass_share` default about 0.3, with weaker damping than ski (0.4 instead of 0.7), because bad weather also cuts pass
     sales;
   - `basis` about 0.5.
   - **One-off outdoor events** (a festival or wedding on a fixed date) are a different product: cancellation can lose
     100% of that day's revenue. Price them as a binary rain-on-the-day contract, not a seasonal elasticity.
8. **`hvac`:** driver: the seasonal cooling- or heating-degree-day shortfall at the place; `elasticity` about **0.8–1.0**
   for a local contractor (0.3–0.5 for a multi-region firm); `max_loss_frac` about 0.25; `margin` about 0.10–0.15;
   `basis` about 0.6 (degree days from one station are a good local index).
9. **`landscaping`:** `elasticity` about **0.1–0.2** to a late or wet spring over the full season, because demand is
   mostly deferred. `max_loss_frac` about 0.15 for maintenance crews paid by the visit, less for contracted maintenance.
   A spring-start (timing) trigger fits this better than season totals. Label this an estimate (one company, one
   episode).
10. **`construction`:** firm `elasticity` to the excess-rain-day share about **0.1–0.3** (deferral; backlog cushions it).
    For personal income (an hourly tradesperson), lost days are lost pay: elasticity about 0.8–1.0 to excess rain days
    ÷ scheduled days, with `max_loss_frac` about 0.15–0.2. No filing quantifies this in dollars; the aggregates figures
    support only the "deferred" part.
11. **`farm`:** revenue elasticity to the yield shortfall about **1.0 × (1 − price offset ≈ 0.3–0.5)**; subtract the
    insured share (most row-crop acres carry federal crop insurance) the same way `pass_share` is subtracted; `basis`
    about 0.5–0.7 for a county rainfall or heat index. This is calibrated on 2012 only; label it an assumption.

**Not recommended:** an airline-fuel occupation. Fuel is passed through to fares, and airline workers' pay is
contractual.

---

## 9. Sources

Quartr links point to the cited page or transcript paragraph. [D] = FRED series (values in `drivers.csv`).

* [D] FRED: UNRATE https://fred.stlouisfed.org/series/UNRATE · PAYEMS https://fred.stlouisfed.org/series/PAYEMS · GASREGW https://fred.stlouisfed.org/series/GASREGW · MORTGAGE30US https://fred.stlouisfed.org/series/MORTGAGE30US · TEMPHELPS https://fred.stlouisfed.org/series/TEMPHELPS · CES7072100001 https://fred.stlouisfed.org/series/CES7072100001 · EXHOSLUSM495S https://fred.stlouisfed.org/series/EXHOSLUSM495S
* [H1] Host Hotels Q4/FY2009 release (RevPAR −19.9%, revenue −19.1%, Adj. EBITDA $798m vs $1,365m): https://www.sec.gov/Archives/edgar/data/0001070750/000119312510032891/dex991.htm ; FY2009 10-K (F&B −20.4%): https://www.sec.gov/Archives/edgar/data/0001070750/000119312510044002/d10k.htm
* [H2] Marriott 2009 Annual Report, MD&A (RevPAR −17.3%; segment revenues; fees): https://media.corporate-ir.net/media_files/IROL/10/108017/MarriottAR09/financials/mda_06.html
* [H3] BLS accommodation employment: https://fred.stlouisfed.org/series/CES7072100001
* [H4] Marriott FY2020 10-K (revenue; quarterly RevPAR −23/−84/−66/−64%): https://web.quartr.com/m/documents/239719 , https://web.quartr.com/m/sources/s57506364912
* [H5] Hilton FY2020 10-K: https://web.quartr.com/m/documents/219866
* [H6] Host FY2020 10-K: https://web.quartr.com/m/documents/217054
* [A1] United 2009 revenue −19.1% (CAPA): https://centreforaviation.com/news/united-airlines-revenue-down-78-remains-in-the-red-in-4q2009-35055 ; first-half 2009 PRASM −16.1%: https://www.sec.gov/Archives/edgar/data/0000100517/000095012309043466/c90252exv99w1.htm ; 2008 revenue: https://www.sec.gov/Archives/edgar/data/0000100517/000095013709001460/c49215e10vk.htm
* [A2] Delta 2009 results (AJC): https://www.ajc.com/business/delta-reports-billion-loss-for-2009/c65CMe6lmCNXFmwSyHvEdO
* [A3] Delta Q4 2022 release (adj. fuel $3.36/gal; fuel +35% vs 2019; 15% less capacity): https://web.quartr.com/m/sources/s64469433319 ; FY2022 10-K: https://web.quartr.com/m/documents/216002 ; FY2019: https://web.quartr.com/m/documents/216005 ; United FY2022/FY2019: https://web.quartr.com/m/documents/220525 , https://web.quartr.com/m/documents/220530
* [A4] Delta Q2 2022 call ("recapture of higher fuel prices"): https://web.quartr.com/m/sources/s366005975432304829579
* [A5] Delta FY2008 10-K ($3.18 vs $2.24/gal; operating loss $8.3bn): https://www.sec.gov/Archives/edgar/data/0000027904/000119312509042726/d10k.htm
* [R1] Gridwise 2026 Gas Report (fuel share 13.2% → 17.4%; delivery 11.2% → 15.6%; $20–30/week; DoorDash relief): https://gridwise.io/analytics/how-rising-fuel-prices-are-impacting-the-gig-mobility-industry
* [R2] Uber newsroom, fuel surcharge (Mar 2022): https://www.uber.com/us/en/newsroom/new-fuel-surcharge
* [R3] Lyft Q1 2022 10-Q risk factor (surcharge): https://web.quartr.com/m/sources/s69494437013 ; Lyft Q3 2022 call (surcharge removed): https://web.quartr.com/m/sources/s280181730432417902651
* [R4] Lyft Q3 2026 call (~$20m relief; "not seen a huge impact"): https://web.quartr.com/m/sources/s209384253106078159483 , https://web.quartr.com/m/sources/s202879654760110340921
* [R5] Uber Q3 2026 call (fuel hit supply in Brazil and India): https://web.quartr.com/m/sources/s302262047313151557952 ; Uber 2026 AGM (fuel incentives): https://web.quartr.com/m/sources/s367346738466393074901
* [E1] Existing-home sales 2023 (4.09m): https://eyeonhousing.org/2024/01/existing-home-sales-end-2023-at-the-lowest-level-since-1995/ ; 2022 (5.03m, −17.8%): https://eyeonhousing.org/2023/01/existing-home-sales-end-2022-with-weakest-year-since-2014/
* [E2] Compass FY2023 10-K, key metrics (transactions, agents, GTV): https://web.quartr.com/m/sources/s50071845305 ; revenue: https://web.quartr.com/m/documents/329391 , https://web.quartr.com/m/documents/221609 , https://web.quartr.com/m/documents/221610
* [E3] Compass FY2023 10-K, commissions expense: https://web.quartr.com/m/sources/s53115955959
* [E4] Anywhere FY2023 10-K: https://web.quartr.com/m/documents/323524 ; commission costs −$751m: https://web.quartr.com/m/sources/s69875636726 ; 2022 volume −14%: https://web.quartr.com/m/sources/s74352214033 ; FY2022/FY2021: https://web.quartr.com/m/documents/216837 , https://web.quartr.com/m/documents/216838
* [E5] eXp Q4/FY2023 release: https://www.sec.gov/Archives/edgar/data/1495932/000155837024001523/expi-20240222xex99d1.htm
* [E6] Rocket Companies FY2023 / FY2021: https://web.quartr.com/m/documents/328997 , https://web.quartr.com/m/documents/230809
* [E7] NAR 2024 Member Profile highlights: https://cdn.nar.realtor/sites/default/files/documents/2024-nar-member-profile-highlights-07-10-2024.pdf
* [S1] Robert Half FY2009 10-K: https://www.sec.gov/Archives/edgar/data/0000315213/000119312510034421/d10k.htm
* [S2] ManpowerGroup Q4/FY2009 release: https://manpowergroup.gcs-web.com/node/51221
* [S3] Kelly Services Q3 2009 10-Q: https://www.sec.gov/Archives/edgar/data/0000055135/000095012309058841/c91820e10vq.htm
* [S4] Robert Half permanent placement: 2023 −21.7% https://web.quartr.com/m/sources/s79318438823 ; 2024 −14.1% https://web.quartr.com/m/sources/s43798406165 ; 2025 −9.8% https://web.quartr.com/m/sources/s44893563659
* [S5] Robert Half revenue and operating income FY2022/FY2025: https://web.quartr.com/m/documents/221932 , https://web.quartr.com/m/documents/2821976
* [S6] BLS temp-help employment: https://fred.stlouisfed.org/series/TEMPHELPS
* [S7] Robert Half FY2020 10-K (permanent placement −30.6%): https://web.quartr.com/m/sources/s85611128602 ; revenue: https://web.quartr.com/m/documents/221934
* [P1] Six Flags Q2 2025 call: weather days https://web.quartr.com/m/sources/s71133977201580576625289 ; margin of lost visits https://web.quartr.com/m/sources/s64648537347110682632913 ; pass sales https://web.quartr.com/m/sources/s77054943121388296118345 ; demand tickets https://web.quartr.com/m/sources/s53916336362468630968461 ; "prefer not to use weather as an excuse" https://web.quartr.com/m/sources/s76982641572766970583354
* [P2] Six Flags Q2 2025 release (379 of 2,042 days; −12% vs flat; pass base; EBITDA rule): https://web.quartr.com/m/sources/s82441862551 , https://web.quartr.com/m/sources/s80020542959 , https://web.quartr.com/m/sources/s66160624027
* [P3] Same release, legacy Cedar Fair revenue and EBITDA: https://web.quartr.com/m/sources/s62919718197 , https://web.quartr.com/m/sources/s71757955621
* [P4] Six Flags (legacy) Q4 2023 call: https://web.quartr.com/m/sources/s316066453486923780538
* [P5] Six Flags (legacy) Q2 2023 call: https://web.quartr.com/m/sources/s366619033691555678229
* [P6] Six Flags (legacy) Q1 2023 call: https://web.quartr.com/m/sources/s344861312932491712391 , https://web.quartr.com/m/sources/s335535929906128921460
* [P7] Six Flags Q1 2025 call: https://web.quartr.com/m/sources/s302131801985626665773 ; Q3 2024 call ($15m EBITDA): https://web.quartr.com/m/sources/s354864722581615366414
* [P8] United Parks Q1 2026 call: https://web.quartr.com/m/sources/s204463706047744426307 , https://web.quartr.com/m/sources/s197902519919117623623 ; Q3 2026: https://web.quartr.com/m/sources/s361088401402964846192
* [P9] United Parks Q4 2024 call: https://web.quartr.com/m/sources/s299729494236931922677
* [L1] BrightView S-1, 2016 vs 2015 snow and segment results: https://web.quartr.com/m/sources/s72491901170
* [L2] BrightView S-1, 9M 2017: https://web.quartr.com/m/sources/s51049493446
* [L3] BrightView S-1, 6M 2018: https://web.quartr.com/m/sources/s74415557286
* [L4] BrightView FY2020 10-K: https://web.quartr.com/m/sources/s59071565445
* [L5] Scotts Q3 2018 call: https://web.quartr.com/m/sources/s194420514005245874161 ; Q4 2018 call: https://web.quartr.com/m/sources/s336430727050871538013
* [V1] Lennox Q3 2019 call: https://web.quartr.com/m/sources/s62992569968706466155280 , https://web.quartr.com/m/sources/s73977100345529237209075
* [V2] Watsco Q3 2018 call: https://web.quartr.com/m/sources/s328066723394439443393
* [C1] Martin Marietta releases and calls: https://web.quartr.com/m/sources/s80865048449 , https://web.quartr.com/m/sources/s70881422489 , https://web.quartr.com/m/sources/s81916601142 , https://web.quartr.com/m/sources/s303962236267163627270
* [C2] Vulcan Q3 2020 call: https://web.quartr.com/m/sources/s222706263137347665520
* [C3] Green Brick Q1 2021 call: https://web.quartr.com/m/sources/s186386616378166147197
* [F1] USDA NASS Crop Production 2012 Summary release: https://www.nass.usda.gov/Newsroom/printable/2013/01_11_13.pdf
* [F2] Crop insurance in 2012 (corn $11.7bn = 68% of claims): https://cropinsuranceinamerica.org/?p=615
