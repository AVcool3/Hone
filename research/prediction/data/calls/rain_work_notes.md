# Rain-stopped work (`rain_work`): what earnings calls say

Source: Quartr earnings-call transcripts (plus three 10-Q figures for tonnage). 44 rows in `rain_work.csv`: 35 construction, 7 landscaping, 2 trades_worker. 23 rows have a % impact. Every row links to the Quartr paragraph it came from.

## First, how the units work (this matters more than any single episode)

In Hone, elasticity = % of revenue lost per 1% more days with 5+ mm of rain (Mar–Nov) than normal. Normal counts are small. ERA5 (pulled with `hone.prediction.perils.history`, 1991–2020 mean) gives:

| place | normal 5mm+ days, Mar–Nov | share of the 275 days |
|---|---|---|
| San Antonio | 34 | 12% |
| Dallas | 39 | 14% |
| Minneapolis | 45 | 16% |
| Houston, Charlotte | 47 | 17% |
| Birmingham | 53 | 19% |
| Nashville | 54 | 19% |

Say a worker loses a full day's pay on every rain day and never makes it up. Then each 1% more rain days costs about s/(1−s) of income, where s is the normal share. That works out to **0.14–0.24**. An elasticity near 1 would need about 4 lost days for every extra rain day. Wet ground can stretch one rain day into more than one lost day: Vulcan said Nashville had "30 rain days" in Q2 2024 and "we lost half of our shipping days" there. That only adds a factor of about 1–1.5, not 4.

Season deviations do happen. ERA5 shows Houston 2021 at 75 days vs 47 normal (+58%), Nashville 2018 at +38%, and Nashville 2025 at +29%.

## construction

**Episodes:** Vulcan (2018 Q3, 2019 Q2, 2020 Q3, 2024 Q2–Q3, 2025 Q2), Martin Marietta (2018 Q3, 2019, 2021 Q2, 2023 Q2), Summit (2023 Q1, 2024 Q2–Q3), Knife River (2024 Q2, 2025 Q2), Construction Partners (FY18 Q4, FY21 Q4 and its catch-up, FY23 Q1 and Q3), Eagle (FY20 Q1–Q2, FY25 Q3), Granite (2023), Arcosa (2021, 2024) and Sterling (2020).

**Quarter-level hits, using management's own weather estimates:**

| row | weather | revenue/volume hit | elasticity |
|---|---|---|---|
| ROAD Jul–Sep 2021 | rainfall +30% vs normal; 7–9 extra lost workdays (~+80% lost days if ~10 are normal) | −10.4% revenue | 0.35 on rainfall; ~0.13 on lost days |
| MLM Q3 2018 | record Sep rain in TX, Florence in the Carolinas | −7.1% volume (+4% actual vs +12% ex-weather) | n/a (deviation not stated) |
| VMC Q3 2018 | record rain days in Dallas/San Antonio, Florence | −4.3% volume (2.5 Mt of 58.5) | n/a |
| VMC Q3 2024 | 17 of 20 top markets wetter YoY, plus hurricanes | about −5 pts (−10% actual vs underlying mid-single-digit decline) | n/a |
| VMC Q2 2025 | 10-year rainfall records in the Southeast | −4.0% (2–3 Mt of ~62) | n/a |
| SUM Q2 2024 | Houston precipitation days +30% YoY | −2.8% of company aggregates volume | local elasticity maybe ~0.9 (Houston's volume share not stated; rough) |
| KNF Q2 2025 | rain on ~40% of workdays (normal is maybe 15–20%) | contracting revenue −8.5% (mixed with Oregon) | ≤0.05–0.09 |
| EXP Oct–Dec 2024 | rainfall 250% of normal in key markets | −7% cement volume | ~0.05 on rainfall |
| MLM Q2 2021 | >1/3 of Texas shipping days disrupted (~+70–120% vs a ~15–20% norm) | Texas cement −<2% | ~0.02–0.03 |

In a single wet quarter (+30% to +100% rain days), firms lose **4–10% of that quarter's volume**. Per 1% more rain days, that is about **0.1–0.35 within the quarter**, and lower when demand is strong or plants are sold out.

**Deferred vs lost (the key question): mostly deferred.**
- ROAD's $30–35M Jul–Sep 2021 shortfall was fully recovered in Oct–Dec. Revenue that quarter was a record and, for the first time in company history, above Q4's.
- VMC's 2018 shortfall shipped in January 2019.
- MLM's wet-2018 Texas cement work made 2019 a record year.
- Granite's wet Q1 2023 was followed by California revenue +21% in Q3.
- Sterling and Eagle say the same: "projects don't get canceled, they just get delayed."

There are limits:
- VMC said 2024 "never got out of the weather problem", and the delayed volume pushed into 2025, a different season.
- Arcosa: roads can't be built faster to catch up.
- Knife River and Summit say "partly recover".

My read: **30–70% of a wet quarter's volume comes back the same season**, and most of the rest comes back the next year. For a backlog firm, the revenue lost over a whole Mar–Nov season is about half the in-quarter hit or less.

**Profit vs revenue: profit falls more.**
- VMC 2018: −7.1% of EBITDA vs −4.3% volume.
- MLM 2018: about −13% of gross profit vs −7% volume.
- ROAD and Arcosa: lost fixed-cost recovery at plants and fleet is not recovered even when the revenue is ("While the revenue moves forward and is not lost, margins are impacted").
- Eagle: earnings fell while revenue rose.

Profit hits run about **1.5–2× the revenue hit**.

**Recommendation:** elasticity **0.15** (range 0.05–0.30), medium-low confidence. Keep max loss at 15%: the largest single-quarter hit found was about 10%, and season-level hits are smaller. Lost fixed-cost recovery means a small firm's profit hit is about twice its revenue hit. For a small contractor without backlog or pricing power, use the upper half of the range.

## trades_worker

**Episodes:** no direct data. TrueBlue/PeopleReady transcripts in Quartr start in 2021 and only mention "holiday and weather" in Q4 outlooks. Labor Ready-era calls are not in Quartr. Primoris, MYR and Dycom mention rain only qualitatively.

**Indirect evidence:**
- ROAD lost 7–9 extra workdays (~12.5% of the quarter's days) and revenue fell ~10%: about 0.8% of revenue per 1% of workdays lost, before catch-up.
- Make-up is common: ROAD crews "might make up for it on the weekend", and BrightView runs 4×10 schedules with a Friday make-up day ("The employees still get their 40 hours") and gives PTO for rain days.
- SiteOne says labor-constrained customers cannot make up lost days in the short term.

**Recommendation:** elasticity **0.25** (range 0.15–0.40), medium confidence. This rests on the arithmetic above, not on a measured episode. **The current 0.9 is about 4× too high under Hone's definition.** With 1:1 pay loss on rain-stopped days, normal rain-day shares of 12–20% give 0.14–0.24, and wet ground pushes it up to ~0.35. Weekend or Friday make-up and PTO push it down: an employee crew member loses little, while an independent day laborer loses the full day. Deferral does not help a day laborer unless the extra work comes back as extra paid days. Max loss of 20% is fine: at +58% rain days (Houston 2021) × 0.25, the loss is ~15%.

## landscaping

**Episodes:** SiteOne (2016 Q1/Q2, 2018 Q3, 2019 Q2–Q3, 2022 Q2) and BrightView (FY22 Q4, plus scheduling and PTO practice). SiteOne is a supplier to landscapers, so its sales stand in for their activity.

- **SiteOne, wet May–June 2019 (8 of 11 regions wetter):** organic sales came in about 4 pts below plan (wet regions flat or negative vs mid-single-digit growth elsewhere). EBITDA missed by ~$4–5M (~4%), about in line with sales. Part of it came back in Q3: landscaping products +8%, helped by "the backlog of work resulting from the challenging weather".
- **SiteOne, September 2018:** Texas had +11 and the Carolinas +12 rain days YoY, yet company-wide growth was only ~2 pts lower that month. Work "to carry into 2019".
- **BrightView, one week of hurricane rain (Sep 2022):** about −0.8 pt of maintenance organic growth and ~$3M of EBITDA (~3%). Profit took about 4× the revenue hit because high-margin ancillary installs were the part lost.

**Deferred vs lost:** contract mowing revenue barely moves. Installs and enhancements are mostly deferred ("a shell game between quarters", SiteOne 2016). Lost work: skipped fertilizer rounds (2022) and short-term catch-up limited by labor (2019).

**Recommendation:** elasticity **0.12** (range 0.05–0.25), low-medium confidence. A contract-maintenance firm is near the bottom of the range. A per-visit owner-operator who skips wet days is near the trades_worker arithmetic (~0.2). Profit falls more than revenue when ancillary or install work is what's lost.

## Caveats

- Most weather figures are vs the prior year, not vs normal. The few vs-normal figures are rainfall totals (ROAD +30%, Eagle +150%), not 5mm-day counts. Rain-day deviations are usually much smaller than rainfall deviations, so per-rain-day elasticities are higher than the rainfall-based ones shown. Look up rain_work counts for the listed regions and quarters before fitting.
- Hurricanes (Florence, Helene, Ian) are mixed into several rows. They cause flooding and power loss, not just rain days.
- Weather is often mixed with demand (housing slowdown, Oregon, imports). Prefer the rows marked "management weather estimate".
- Several rows are Q1 or Dec (Summit SLC, ROAD Oct–Dec), outside Mar–Nov, and are flagged.
- These are large, diversified firms. A single-site small business sees larger swings, but also has fewer projects to shuffle.
- Not found or not useful: TrueBlue (no quantified weather, no pre-2021 calls), CRH (qualitative only), US Lime (no hits), IBP (winter only), Pool Corp (Q1 rain and cold mixed with demand), Primoris, MYR and Dycom (qualitative). Scotts and Central Garden were not searched: their weather risk is consumer demand, a different peril.
