# 06 — How much do resort revenue and visits fall in a low-snow season? (Vail Resorts filings, FY2005–FY2026)

**Question.** `hone/prediction/quote.py` prices bad-season protection as
`revenue × elasticity × snowfall_shortfall`, with `REGION_ELASTICITY = {pacific: 0.8, rockies: 0.25, east: 0.4}`.
Those values were picked from published studies. This note measures the number from one company's results:
Vail Resorts (NYSE: MTN), the largest ski operator. Its 10-Ks report lift revenue, skier visits and effective
ticket price (ETP) for every season, and management says in each one what the snow was like and where.

**Dataset:** `research/prediction/data/resorts/vail_seasons.csv` (22 seasons, FY2005–FY2026; every row lists its source URLs).
Vail's fiscal year ends on July 31, so FY2012 is the 2011/12 ski season.

---

## Bottom line

| | Large multi-resort operator, 40–70% of lift revenue from passes (Vail) | Single independent resort with few prepaid passes (estimated) |
|---|---|---|
| Visits in a bad season (core region at ~45–60% of normal snowpack) | **−10% to −13%** company-wide; −9% (Colorado) to −22% (Tahoe) for one region | **−10% to −15% (Rockies), −25% to −35% (Pacific)** |
| Lift revenue vs. its normal growth trend | **−4% to −8%** (in nominal terms, flat to −3.5%) | roughly tracks visits: **−10% to −30%** |
| Mountain (whole-resort) revenue vs. trend | **−5% to −8%** | **−10% to −30%** |
| Revenue elasticity (% revenue lost per 1% snowfall shortfall) | **0.15–0.20** | **0.25–0.35 Rockies, 0.4–0.65 Pacific** |
| Profit impact | Mountain EBITDA −6.7% (FY2012), −11.2% (FY2026); in-season revenue flow-through about 80% (an analyst's estimate the CFO confirmed) | larger: smaller cushion, no prepaid revenue |

The model's **Rockies value (0.25) is supported** for an independent resort. The **Pacific value (0.8) is too
high**: no season in the data, at Vail or across all of California and Nevada, implies more than about 0.67. The model also
**ignores season-pass prepayment**, which roughly halves a resort's revenue sensitivity compared with its visit sensitivity.
Recommendations are at the end.

---

## 1. Season-by-season table

Revenue is in $ millions and visits in millions; both are as reported in that year's 10-K. Pass share is the share of lift
revenue that came from season passes, as Vail reports it. Snow is my calculation (see §5): **peak snow water
equivalent (SWE) as a % of the 1991–2020 median**, from USDA SNOTEL stations: Colorado is the average of Vail
Mountain (#842) and Copper Mountain (#415), Park City is Thaynes Canyon (#814), and Tahoe is Truckee #2 (#834).

| FY | Season | Mountain rev | Lift rev | Visits (m) | ETP $ | Pass share | Visits YoY | Lift YoY | Snow % normal: CO / PC / Tahoe | Management's snow description (abridged) and structural notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2005 | 04-05 | 540.9 | 233.5 | 5.940 | 39.30 | n/r | – | – | 88 / 183 / 141 | base year |
| 2006 | 05-06 | 620.4 | 263.0 | 6.288 | 41.83 | n/r | +5.9% | +12.7% | 125 / 145 / 99 | CO visits +8.0% on "strong early season snowfall"; Heavenly −3.9% on "unfavorable weather conditions" [1] |
| 2007 | 06-07 | 665.4 | 287.0 | 6.219 | 46.15 | 25% | −1.1% | +9.1% | 96 / 70 / 82 | **Heavenly −12.0% vs Pacific West region −14.3%, with "a 40% reduction in snowfall for the region"**; CO +1.0% "in spite of a 23% reduction in snowfall" [1] |
| 2008 | 07-08 | 685.5 | 301.9 | 6.195 | 48.74 | 26% | −0.4% | +5.2% | 129 / 136 / 104 | "below average snow conditions" before Dec 24 cut non-pass visits 3.0% [2] |
| 2009 | 08-09 | 614.6 | 276.5 | 5.864 | 47.16 | 34% | −5.3% | −8.4% | 121 / 116 / 80 | **recession, not snow**: destination visits about −15%. Epic Pass launched [3] |
| 2010 | 09-10 | 638.5 | 289.3 | 6.010 | 48.13 | 35% | +2.5% | +4.6% | 86 / 101 / 120 | CO "significantly below average snowfall… up to mid-January"; CO +1.2%, Heavenly +10.7% [4] |
| 2011 | 10-11 | 752.2 | 342.5 | 6.991 | 48.99 | 35% | +16.3% | +18.4% | 151 / 167 / 217 | strong snow everywhere. **Northstar acquired** (same-store: visits +4.1%, lift +7.7%) [5] |
| **2012** | **11-12** | 766.6 | 342.5 | 6.144 | 55.75 | 40% | **−12.1%** | **0.0%** | **60 / 63 / 62** | **"historically low snowfall (with cumulative snowfall down more than 50%…)"; CO −8.9%, Tahoe −22.3%** [6] |
| 2013 | 12-13 | 867.5 | 390.8 | 6.977 | 56.02 | 38% | +13.6% | +14.1% | 87 / 94 / 64 | CO poor until Christmas (CO +4.0%); Tahoe +32.1% (including Kirkwood). **Canyons and urban ski areas added** [7] |
| 2014 | 13-14 | 963.6 | 447.3 | 7.688 | 58.18 | 40% | +10.2% | +14.4% | 120 / 85 / **19** | **"very poor conditions in the Tahoe region"; Tahoe visits −16.2%**; CO +8.4% [8] |
| 2015 | 14-15 | 1,104.0 | 536.5 | 8.466 | 63.37 | 40% | +10.1% | +19.9% | 80 / 51 / **19** | **Tahoe "very low snowfall levels", visits −16.4%**. **Park City and Perisher added** [9] |
| 2016 | 15-16 | 1,304.6 | 658.0 | 10.032 | 65.59 | 40% | +18.5% | +22.7% | 102 / 86 / 87 | "strong rebound at our Tahoe resorts" [10] |
| 2017 | 16-17 | 1,611.8 | 818.3 | 12.047 | 67.93 | 43% | +20.1% | +24.4% | 99 / 132 / 208 | "poor early season conditions" in CO. **Whistler Blackcomb acquired** (excluding it: lift +6.4%) [11] |
| **2018** | **17-18** | 1,722.9 | 880.3 | 12.345 | 71.31 | 47% | +2.5% | +7.6% | **78 / 68 / 76** | **"historically low snowfall for the first half"**; Vail, Beaver Creek and Park City lowest in 30+ years. **Same-store N. America season-to-date: visits −4.9%, lift +1.6%** [12][13] |
| 2019 | 18-19 | 1,956.2 | 1,033.2 | 14.998 | 68.89 | 47% | +21.5% | +17.4% | 112 / 133 / 188 | improved West. **Stevens Pass, Triple Peaks and Falls Creek/Hotham added** [14] |
| 2020 | 19-20 | 1,710.4 | 913.1 | 13.483 | 67.72 | 51% | −10.1% | −11.6% | 104 / 99 / 82 | **COVID closures from mid-March 2020**; $120.9M of pass revenue deferred to FY2021. **Peak Resorts (17 areas) added** [15] |
| 2021 | 20-21 | 1,689.9 | 1,076.6 | 14.852 | 72.49 | 61% | +10.2% | +17.9% | 71 / 67 / 81 | COVID limits, plus snowfall "well below average at our Colorado, Utah and Tahoe resorts through the holiday season" [16] |
| 2022 | 21-22 | 2,213.1 | 1,310.2 | 17.298 | 75.74 | 61% | +16.5% | +21.7% | 81 / 79 / 85 | "challenging early season conditions". Epic Pass price cut 20%. Seven Springs added [17] |
| 2023 | 22-23 | 2,540.9 | 1,420.9 | 19.410 | 73.20 | 61% | +12.2% | +8.4% | 97 / 164 / 213 | record visitation. Andermatt added [18] |
| **2024** | **23-24** | 2,544.4 | 1,442.8 | 17.564 | 82.14 | 65% | **−9.5%** | **+1.5%** | 95 / 113 / 116 | **western snowfall −42% YoY through Jan (−28% for the season)**; lift-ticket visits −17%; post-COVID normalization as well [19][20] |
| 2025 | 24-25 | 2,629.9 | 1,503.2 | 17.665 | 85.09 | 65% | +0.6% | +4.2% | 87 / 84 / 88 | better early season in the West and East [21] |
| **2026** | **25-26** | 2,503.2 | 1,451.1 | 15.299 | 94.85 | 70% | **−13.4%** | **−3.5%** | **47 / 58 / 75** | **"record low snowfall and historically warm temperatures across the western U.S."**; Rockies snowfall −43% YoY. No acquisitions [22][23] |

n/r = not reported. FY2020 and FY2021 Mountain revenue were later restated to $1,726.6M and $1,702.8M ([17]); lift
revenue and visits were not changed.

### Structural breaks to adjust for

* **Acquisitions:** Northstar (Oct 2010), Kirkwood (Apr 2012), Canyons (May 2013), Park City (Sep 2014), Perisher (Jun 2015),
  Whistler Blackcomb (Oct 2016), Stowe (Jun 2017), Stevens Pass and Triple Peaks (Aug–Sep 2018), Falls Creek/Hotham (Apr 2019),
  Peak Resorts (Sep 2019), Seven Springs (Dec 2021), Andermatt (Aug 2022), Crans-Montana (May 2024). Visits grew from 6.0m to 19.4m,
  mostly through acquisitions. **Raw year-on-year growth cannot be used**: each comparison below uses Vail's same-store figure or
  a season with no acquisition.
* **COVID:** FY2020 (closures from March 15, 2020, and the pass-revenue deferral) and FY2021 (capacity limits) are excluded.
* **Epic Pass growth:** passes were 25% of lift revenue in FY2007 and 70% in FY2026 [1][22]. In FY2026, passes were "approximately
  75% of our annual visitation" ([24]). Passes are sold before the season and recognized ratably, so the ~2008–2023 move into
  passes steadily lowered sensitivity to snow. It also mechanically shifted revenue from tickets to passes; in FY2009 that shift
  was mixed with the recession.
* **Recession:** FY2009 visits fell 5.3% and lift revenue 8.4% with near-normal Colorado snow. Economic shocks are about as large as
  snow shocks, so they need to be separated out.
* **Price trend:** ETP rose about 4–5% a year, from $39 to $95. A season with flat lift revenue is therefore a loss of roughly
  5–8% against trend.

---

## 2. Low-snow seasons named in the filings

"Trend" is the counterfactual growth rate: the same-store growth Vail reported in the nearest normal season. The elasticity is
the % change divided by the core-region snowpack shortfall from normal.

| Season (FY) | Snow in core region | Visits | Lift revenue | Mountain revenue | Visit elasticity | Revenue elasticity |
|---|---|---|---|---|---|---|
| **2011/12 (FY2012)**, company | CO 60%, Tahoe 62% of normal → ~40% short. "cumulative snowfall down more than 50%" YoY [6] | **−12.1%**; non-pass visits **−15.0%** [6] | 0.0% (pass +13.2%, non-pass −7.1%) vs trend +7.7% → **−7.1%** | +1.9% nominal; about +0.2% excluding an acquired online retailer (+$12.5M); vs +7.7% trend → **≈ −7%** | **0.30** | **0.18** |
| — Vail Colorado resorts | 60% | **−8.9%** [6] | | | 0.22 | |
| — Vail Tahoe resorts | 62% | **−22.3%** [6] | | | 0.59 | |
| — all Colorado ski areas (market) | 60% | 12.3m → 11.0m, **−10.6%** [5][6] | | | 0.27 | |
| — all California/Nevada areas (market) | 62% | 7.8m → 5.8m, **−25.6%** [5][6] | | | 0.67 | |
| — US industry | | about 51.0m vs a record 60.5m, **−15.7%** [25] | | | | |
| **2013/14 (FY2014)**, Vail Tahoe | Truckee 19% of normal → 81% short | **−16.2%** [8] (CA/NV market 6.8m → 4.9m, **−28%** [7][8]) | | Colorado growth hid it at company level | 0.20 (Vail), 0.35 (market) | |
| **2014/15 (FY2015)**, Vail Tahoe | 19% again | **−16.4%** further (about −30% over two years) [9] | non-pass lift revenue in Tahoe fell [9] | | 0.20 one year, 0.37 two years | |
| **2006/07 (FY2007)**, Heavenly | regional snowfall −40% YoY | **−12.0%** (Pacific West region −14.3%) [1] | | | 0.30 (vs YoY snow) | |
| **2017/18 (FY2018)**, North America same-store | CO 78%, PC 68%, Tahoe 76% → ~25% short (Whistler a record year) | **−4.9%** season-to-date to Mar 4 [13] | **+1.6%** vs trend +6.4% → **−4.5%** [13][11] | +6.9% reported (includes Stowe) | ~0.20 | ~0.18 |
| **2023/24 (FY2024)**, company | peak snowpack near normal (95% / 113% / 116%) but western snowfall −42% YoY through Jan and −28% for the season [19][20] | **−9.5%** (N. America −8% vs industry −9%); lift-ticket visits **−17%** [20][26] | +1.5% (pass +9.4%, non-pass −10.7%) vs trend +4–8% → **−3% to −6%** | +0.1% vs trend +3–4% → **≈ −3% to −4%** | 0.34 (vs −28% snowfall) | 0.1–0.2 |
| **2025/26 (FY2026)**, company, no acquisitions | **CO 47%, Park City 58%**, Tahoe 75%; Rockies snowfall −43% YoY [24]; East strong | **−13.4%** [22]; through Mar 1, pass-holder visits −14% and non-pass visits −6% [24] | **−3.5%** (pass +4%, **paid lift −17.5%**, paid ETP −8.8%) vs trend +4.2% → **−7.4%** [22][23] | **−4.8%** vs trend +3.4% → **−7.9%**; ski school −10.3%, dining −7.6%, retail/rental −6.5% [22] | 0.27 (vs ~50% Rockies shortfall) | 0.15–0.16 (paid lift revenue: ~0.42) |

### What the numbers show

1. **Visits in a bad season fall 10–13% for the diversified operator.** The two clean company-wide cases, FY2012 and FY2026, are
   −12.1% and −13.4%. A single region falls further: Tahoe −16% to −22%, Colorado about −9%. In both FY2012 and FY2026, total
   lift revenue fell by only **about 0.55–0.6× the visit decline** (relative to trend), because 40–70% of it was prepaid.
   - In FY2012, total lift revenue was flat and non-pass revenue fell 7.1%. Non-pass ETP rose 9.3%, which hid a 15% fall in
     non-pass visits.
   - In FY2026 the CFO said: "Total lift revenue decreased only 3.5%, despite a 13% decline in skier visitation, supported by 4%
     growth in pass revenue" [23].
2. **The revenue elasticity for a pass-heavy operator is 0.15–0.20.** Visits run at 0.2–0.35, and paid ticket revenue at 0.35–0.45.
   The paid-ticket figure is the best proxy for a resort with no prepaid passes.
3. **The response flattens as the shortfall deepens.** Tahoe in 2013/14 and 2014/15, at about 19% of normal snowpack, lost only
   16% of Vail's visits a year and 28% of the regional market. A linear model at elasticity 0.8 would predict a 65% loss.
   Snowmaking and the most committed skiers set a floor.
4. **Early-season timing matters as much as peak snowpack.** In FY2024, peak snowpack ended near normal, but snowfall was −42%
   through January. Visits still fell 9.5% (partly post-COVID normalization), and lift-ticket visits fell 17%. The pre-Christmas
   misses in FY2013 and FY2017 tell the same story.
5. **A bad season also costs the next one.** Pass units for the following season fell about 3% after 2023/24 and **about 12%**
   after 2025/26 ("pass units declined 12%, days sold declined 10%, and sales dollars… down 6%") [27][28]. After FY2012, pass
   revenue growth slowed from +13.2% to +8.8% [6][7]. Prepayment protects the bad season itself but passes part of the hit into
   the next year.
6. **Most of the lost revenue is lost profit.** FY2026 Mountain EBITDA fell 11.2% on revenue down 4.8% [22]. An analyst
   estimated the in-season flow-through at about 80%, and the CFO confirmed the "high flow through" [24].
7. **Snow is not the only shock.** The FY2009 recession (−5.3% visits, −8.4% lift revenue) was as large as the FY2018 snow
   drought, and it hit destination guests the most. Weather mostly moves local skiers: "Local guests tend to be more value-oriented
   and weather sensitive" [10].

---

## 3. A large operator compared with a single independent resort

* **What a large operator absorbs.**
  1. *Geographic spread.* In FY2018, Whistler's record year offset the western US. In FY2026, strong conditions in the East partly
     offset the Rockies. This roughly halves the company-wide visit hit compared with the worst region: FY2012 −12% company vs −22%
     Tahoe.
  2. *Prepayment.* 40–70% of lift revenue is locked in before the season.
  3. *Price.* Non-pass ETP rose 9% in FY2012 and 11% in FY2024 while those visits fell.
* **An independent resort without season-pass prepayment** behaves like Vail's *paid-ticket* segment, or like the *state market
  totals*:
  - Paid visits and revenue fell 15–20% in Vail's bad years: non-pass visits −15% in FY2012, lift-ticket visits −17% in FY2024,
    paid lift revenue −17.5% in FY2026.
  - In the regional markets, Colorado lost −10.6% and California/Nevada −25.6% in 2011/12, and California/Nevada −28% in 2013/14.
  - Expected revenue loss in a bad season: **about −10% to −20% in the Rockies and −25% to −35% in the Pacific**. That is an
    elasticity of about **0.25–0.35 (Rockies) and 0.4–0.65 (Pacific)**.
  - Lower-elevation resorts with less snowmaking sit at the top of each range. Resorts on the Ikon or Indy pass, or with strong
    local season-pass programs, sit between the two columns.

---

## 4. Recommendations for the model (`hone/prediction/quote.py`)

1. **Lower the Pacific elasticity from 0.8 to about 0.55, and keep the Rockies at 0.25** for an independent resort. The Pacific
   evidence spans 0.2–0.67:
   - Vail Tahoe: 0.59 in 2011/12, 0.20 in 2013/14 and 2014/15.
   - California/Nevada market: 0.67 in 2011/12, 0.35 in 2013/14.
   - Heavenly / Pacific West: 0.3–0.36 in 2006/07.

   The Rockies evidence spans 0.22–0.30 (Vail Colorado 0.22, Colorado market 0.27, FY2026 company 0.27). The East value (0.4)
   has no clean support in these filings; label it an assumption.
2. **Add a prepaid-pass share input, and scale the elasticity by `(1 − 0.7 × prepaid_share)`.** This fits Vail's results: at a
   40% pass share, lift revenue fell 0.59× as much as visits (FY2012); at 65–70%, it fell 0.53–0.56× as much (FY2024, FY2026).
   A pass-heavy Rockies resort at 60–70% would get 0.25 × 0.53 ≈ **0.13–0.15**, close to Vail's measured 0.15–0.18. Default the
   share to about 0.2 when the user doesn't know it.
3. **Make the loss saturate.** Use `elasticity × min(shortfall, 0.5)`, or lower `max_loss_frac` for `ski_resort` from 0.6 to
   about **0.35**. The worst cases observed are about −22% for a region inside Vail and −26% to −37% for a regional market (two
   years at 19% of normal). The current linear formula at 0.8 would predict about −65% for those seasons.
4. **Account for timing and the following year.**
   - *Timing:* a contract on full-season snowfall misses bad starts. In FY2024, peak snowpack was about normal but visits fell
     9.5%. Consider a Nov–Jan cumulative-snowfall trigger, or a blend of the two, for resorts. The current basis of 0.7 is about
     right for a full-season index.
   - *Following year:* for pass-heavy resorts, add a second-year revenue loss of **about 2–5%**, from next-season pass units of
     −3% and −12% after the last two bad seasons.
5. **Keep treating lost revenue as lost profit.** The data support it: about 80% in-season flow-through, and FY2026 Mountain EBITDA
   −11.2% on revenue −4.8%. The 15% margin cushion is consistent with Vail's Mountain EBITDA margin of about 29–37%, once the
   thinner margins of independent resorts are allowed for.

### Caveats

* **One operator.** Vail is snowier, higher, more destination-oriented and better equipped for snowmaking than most independent
  resorts. That makes its elasticities a lower bound for the typical resort.
* **Snow measures.** SNOTEL peak snowpack at one or two stations per region is a rough measure of what skiers experienced; early
  season and holiday timing matter (FY2024). Elasticities computed against year-on-year snowfall, as management quotes it, come
  out lower than those against normal when the prior year was big (FY2012 followed a record 2010/11).
* **Trend counterfactuals.** These are judgment calls (±2–3 percentage points). FY2024 is mixed with post-COVID normalization, and
  FY2009 with the recession.
* **No regional revenue disclosure.** Vail publishes regional visit changes only in some years. All revenue elasticities are
  company-level.

---

## 5. Sources

Quartr links point to the cited page or transcript paragraph. SEC links are the full 10-K or press release; search the text for
"Mountain Segment".

* [1] FY2007 10-K (FY2005–07 table, Kottke region comparison): https://www.sec.gov/Archives/edgar/data/812011/000081201107000054/form10k.htm
* [2] FY2008 10-K: https://www.sec.gov/Archives/edgar/data/812011/000081201108000026/form10k.htm
* [3] FY2009 10-K (pass share 34%/26%/25%): https://www.sec.gov/Archives/edgar/data/812011/000081201109000030/form10k.htm
* [4] FY2010 10-K: https://www.sec.gov/Archives/edgar/data/812011/000081201110000020/form10k.htm
* [5] FY2011 10-K (Northstar same-store; CA/NV 7.8m; Colorado 12.3m): https://www.sec.gov/Archives/edgar/data/812011/000119312511253811/d196554d10k.htm
* [6] FY2012 10-K (2011/12 low-snow narrative; CA/NV 5.8m; Colorado 11.0m; pass share 40%): https://www.sec.gov/Archives/edgar/data/812011/000081201112000017/mtn2012073110-k.htm (see also the Q3 FY2012 release: https://www.sec.gov/Archives/edgar/data/812011/000081201112000010/pressrelease.htm)
* [7] FY2013 10-K (CA/NV 6.8m): https://www.sec.gov/Archives/edgar/data/812011/000081201113000029/mtn2013073110-kforq4.htm
* [8] FY2014 10-K (CA/NV 4.9m): https://www.sec.gov/Archives/edgar/data/812011/000081201114000019/mtn2014073110-kforq4.htm ; Tahoe −16.2% on Quartr: https://web.quartr.com/m/sources/s47366016145
* [9] FY2015 10-K, Mountain table and Tahoe narrative: https://web.quartr.com/m/sources/s44773923797 , https://web.quartr.com/m/sources/s57767347833 ; pass share: https://web.quartr.com/m/sources/s80142766964
* [10] FY2016 10-K: https://web.quartr.com/m/sources/s63361248431 ; pass share and local weather sensitivity: https://web.quartr.com/m/sources/s69069390037
* [11] FY2017 10-K: https://web.quartr.com/m/sources/s56551784035
* [12] FY2018 10-K: https://web.quartr.com/m/sources/s71623772656 ; snowfall risk-factor wording: https://web.quartr.com/m/sources/s47997978256
* [13] Q2 FY2018 press release (season-to-date metrics to Mar 4, 2018): https://www.sec.gov/Archives/edgar/data/812011/000081201118000009/a20180131pressrelease.htm
* [14] FY2019 10-K: https://web.quartr.com/m/sources/s70515717431 , https://web.quartr.com/m/sources/s43607444717 ; pass share: https://web.quartr.com/m/sources/s60045206723
* [15] FY2020 10-K: https://web.quartr.com/m/sources/s43388643885 ; pass share: https://web.quartr.com/m/sources/s69828662383
* [16] FY2021 10-K: https://web.quartr.com/m/sources/s77270646466 , https://web.quartr.com/m/sources/s64258602174 ; pass share: https://web.quartr.com/m/sources/s60242272900
* [17] FY2022 10-K (restated FY2020/21): https://web.quartr.com/m/sources/s72667924003 ; pass share: https://web.quartr.com/m/sources/s56623225074
* [18] FY2023 10-K: https://web.quartr.com/m/sources/s76860565497 , https://web.quartr.com/m/sources/s60365258486 ; pass share: https://web.quartr.com/m/sources/s71669880717
* [19] FY2024 10-K: https://web.quartr.com/m/sources/s66496278614 ; pass share: https://web.quartr.com/m/sources/s74225993126 ; Q2 FY2024 call (−42% snowfall): https://web.quartr.com/m/sources/s68909303057759043928101
* [20] Q4 FY2024 call (western snowfall −28%; N. America −8% vs industry −9%): https://web.quartr.com/m/sources/s59815656355823094277081 , https://web.quartr.com/m/sources/s72187701810634008344783
* [21] FY2025 10-K: https://web.quartr.com/m/sources/s73582834605 ; pass share: https://web.quartr.com/m/sources/s64352749238
* [22] FY2026 10-K, Mountain segment: https://web.quartr.com/m/sources/s53343562989 , https://web.quartr.com/m/sources/s55358742775 ; pass share 70/65/65: https://web.quartr.com/m/sources/s48688088037
* [23] Q4 FY2026 call (lift −3.5% despite −13% visits): https://web.quartr.com/m/sources/s82256161273140269092395
* [24] Q2 FY2026 call (worst Rockies season; pass holders ~75% of visits; Rockies snowfall −43%; pass visits −14% / non-pass −6%; flow-through): https://web.quartr.com/m/sources/s73743674378663709449224 , https://web.quartr.com/m/sources/s72644737315278889851271 , https://web.quartr.com/m/sources/s93452225343564045304127 , https://web.quartr.com/m/sources/s54530303534014063050647 , https://web.quartr.com/m/sources/s51205168384865644215213
* [25] US 2011/12 industry visits (NSAA preliminary Kottke survey, 51.0m): https://prnewswire.com/news-releases/skisnowboard-industry-201112-season-wrap-up-bright-spots-emerge-but-skier-visits-plunge-151699545.html ; −15.7% from the record 60.54m (SAM): https://www.saminfo.com/archives/2010-2017/2013/july-2013/industry-reports-july-2013
* [26] Q4 FY2024 call (lift-ticket visitation −17%): https://web.quartr.com/m/sources/s91262331308128273024031
* [27] Q4 FY2024 call (2024/25 pass units −3%): https://web.quartr.com/m/sources/s76113185309336939388760
* [28] Q4 FY2026 call (2026/27 pass units −12%): https://web.quartr.com/m/sources/s77084848776804767653458
* Snowpack: USDA NRCS SNOTEL daily SWE (AWDB REST API, https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1) for stations
  842:CO, 415:CO, 814:UT and 834:CA. I read them from the cache that `research/prediction/resorts.py` keeps in
  `research/prediction/data/resorts/` and computed peak SWE as a % of the 1991–2020 median.
