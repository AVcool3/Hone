# Summer weather: what earnings calls say (Quartr)

Data: `summer.csv`, 49 rows (outdoor_venue 20, hvac 20, outdoor_worker 9). Every row has a Quartr paragraph link.
"Elasticity" below means % of revenue lost per 1% the weather measure is worse than normal, as Hone defines it.

Few calls give both a weather size and a revenue size. So most rows are context: which way the effect goes, whether demand is lost or delayed, and how profit moves. Only a handful support a number.

---

## outdoor_venue (peril `rain_summer`)

**Episodes**
- Six Flags (merged), Q2 2025: about 20% of operating days were hit by weather, with 49 full closures vs 12 the year before. Over the last 6 weeks attendance fell 12%, while the first 7 weeks, which had normal weather, were flat. That puts the effect at roughly 0.6 or less per 1% of days hit. Days inside the 6-week window were hit at a higher rate than 20%, so the true figure is lower. This matches the current 0.5 attendance figure taken from the whole quarter.
- Six Flags, July 2024: attendance fell 3% overall but only 1% at parks that stayed open. Closures caused most of the drop.
- Legacy Six Flags: Q2 2023 lost 5–6 points of attendance (about 400k visits). FY2023 lost about 4.3% (over 1m visits). Q1 2023 lost about 10% from cold and rain, but that is outside the season and a low-volume quarter. None of these state a day count.
- United Parks (SeaWorld): bad-weather quarters cost 2–4% of attendance (Q2/Q3 2023 vs prior year; Q3 2024 and Q4 2024 hurricanes, by management estimate). Revenue falls much less than attendance because spending per guest holds up or rises:
  - Q3 2026: attendance −4.7%, revenue −1.1%.
  - Q3 2024: attendance −1.4%, revenue −0.4%.
  - Q2 2023: attendance −2.0%, revenue −1.7%.
- Lucky Strike water parks, June 2026: a cool, wet June cost about $3–5m on roughly $56m of trailing water-park revenue.
- Inverse case: indoor bowling in Chicago had sales up about 90% on a day when rain closed the water park. Indoor venues gain when it rains.
- Heat: French festivals were shut down for extreme heat in late June 2026. They were fully insured, so the net effect was 0.

**Per-row elasticity** can only be computed for Six Flags Q2 2025: at most 0.6 for attendance, measured against share of days hit. No other venue gives a day count.

**Recommended elasticity: 0.35 (range 0.2–0.6), medium-low confidence. Keep the current value.**
Attendance responds at about 0.5–0.6 per 1% of days hit. Revenue moves only 25–100% as much as attendance, which gives 0.15–0.6 for revenue, centred near 0.35.
Caveat: "days impacted" (closures, storms, heat) is not the same as Hone's count of rainy days (≥2.5 mm). Many rainy days are light or fall overnight, so the per-rainy-day figure is probably at or below the per-impacted-day figure.

**Lost vs deferred:** lost.
- Legacy Six Flags: "We do not expect to make up weather-related losses."
- In 2025 Six Flags management said guests "delayed" visits, but July was only +1% and full-year EBITDA guidance was cut by about $215m.

**Pre-sold share:** passes soften the hit. Pass holders move their visits to another day, while walk-up single-day tickets are "almost all" lost. But weather also hits pass sales: 300k fewer season passes were sold in May–June 2025. Keep pass_share at 0.3. Note that bad weather early in the season also shrinks the pass base for the rest of the season.

**Profit vs revenue:** profit falls more than revenue. Six Flags said lost visits carried a 55–70% margin, so only 30–45% of the lost revenue is offset by lower costs. The current 30% cost offset sits at the low end of that range. 0.3–0.4 is reasonable.

**Coverage:** not in Quartr or no transcripts: Compagnie des Alpes, Merlin, Parques Reunidos, Drive Shack, old pre-merger Cedar Fair calls. Topgolf (Callaway), Live Nation and Vail's summer business had nothing quantified. Vail's ski data does show how strongly passes damp losses: visitation −13%, lift revenue −3.5%. That is winter data, so it is not in the CSV.

---

## hvac (peril `cool_summer`)

**Episodes and per-row elasticity**
| Episode | Weather | Outcome | Elasticity |
|---|---|---|---|
| Lennox Texas, Q3 2019 | CDD +9% | revenue +10% (vs prior year) | ~1.1 |
| Lennox central US, Q2 2019 | CDD −30% (regions with 40% of revenue) | weather loss > $28m, at least 3.9% of the segment, so ≥10% in those regions | ≥0.33, likely 0.4–0.6 |
| Lennox, June 2020 | CDD +12% | residential +7% | ~0.6 (COVID reopening muddies it) |
| Frontdoor, Q2 2023 (HVAC repair calls) | CDD −23% | "similar decline" in HVAC claims | ~1.0 |
| Frontdoor, Q2 2024 | CDD +20% | only a "moderate" rise in HVAC calls | ~0.2–0.5 |
| Frontdoor, Q3 2024 | CDD −16% | $14m less claims cost | no base given |

Equipment makers and distributors now mostly refuse to put a number on weather: Lennox, Carrier, Watsco and Trane say things like "we don't like to talk about weather".

**Recommended elasticity: 0.6 (range 0.3–1.0), low-medium confidence. Lower it from 0.9.**
- Measured against cooling degree days, single-region revenue moves at 0.4–1.1 within a quarter. But part of it comes back later (see below), so the effect over a full season is smaller.
- Hone's measure is days over 30°C, not degree days. That count probably swings more in % terms than degree days do; this is my judgement, not from the calls. If so, the per-hot-day elasticity should be lower still.
- Revenue in the hot Sun Belt is barely weather-sensitive. Watsco: "in Florida it's either hot or hotter". The effect is concentrated in northern and temperate markets.

**Lost vs deferred:** mixed.
- Repair calls on a cool summer are lost, because the unit never fails (Frontdoor).
- Replacements are partly deferred. Lennox (2023): a cold June "washes out for the full year". Lennox (2025): weak May, strong June/July. Watsco (2023): repair parts picked up once heat arrived. Hudson: volumes strong from mid-June.
- If Hone's loss is per season, I'd treat about half of the replacement loss as recovered later in the season or the next year.

**Pre-sold share:** none. Service agreements exist but no call quantified them.

**Profit vs revenue:** profit falls more than revenue.
- Lennox (2019) cut factory-productivity guidance because lower output meant fixed costs were spread over fewer units.
- Repair work and parts carry higher margins for distributors (Watsco), so losing repair volume hurts margin.
- I found no contractor-level margin data.

**Coverage:** Daikin has no transcripts in Quartr. Rheem is private. AAON and Comfort Systems had nothing relevant: they are commercial and backlog-driven, and their weather comments were about construction disruption.

---

## outdoor_worker (peril `heat`)

**I found nothing that quantifies lost hours, pay or revenue from heat.** Nine rows are qualitative:
- US firms report little impact.
  - BrightView: "very little"; heat is a smaller disruption than rain.
  - MYR Group: "getting full days in" by starting crews earlier.
  - Badger: hydration breaks and job rotation, with double-digit revenue growth in the same quarter.
- Some loss is visible.
  - TrueBlue/PeopleReady: solar-site staffing volume fell on Southwest heat, but not sized and mixed with project delays.
  - Larsen & Toubro (India): extreme heat plus election-related labour shortages slowed Q1 FY25 work; early and late shifts don't restore full productivity.
  - Mahindra Logistics (India): "much higher absenteeism".
  - Heijmans (Netherlands): a long heat protocol in late June 2026; the CEO floated a formal heat-leave scheme.

**Recommended elasticity: 0.2 (range 0.05–0.4), low confidence, still an assumption.**
- The calls suggest employers mostly shift hours rather than lose them in the US, which points below 0.3.
- Daily-paid workers in extreme heat (India, EU heat protocols) do lose days, which points higher.
- Calibrate from labour-economics studies of hours lost on hot days, not from calls.

**Lost vs deferred:** for an hourly worker, a heat stoppage or absence is lost pay. Shifting to early starts keeps hours. For contractors the work is deferred: Larsen & Toubro kept its full-year guidance.

**Profit vs revenue:** no data.

**Coverage:** UPS, FedEx and waste haulers mention heat only as a safety or labour-contract topic, with no numbers. Searches covering Quanta, MasTec and Primoris found nothing quantified. I did not search Beacon (roofing), pool service or farm labour.
