# Farms and orchards: weather sensitivity from earnings calls

Source: Quartr transcripts. There are 45 rows in `farm.csv` (20 orchard, 25 farm_crops), and every row links to the paragraph it came from.

**Main limit:** no transcript gives the size of the weather deviation as a number (no "rainfall X% below normal", no "N frost nights"). Managers describe the weather in words ("worst drought in 100 years", "freeze not seen in 20 years"). So `weather_deviation_pct` is blank in every row. A true per-1% elasticity cannot be computed from the calls alone. It needs to be joined to station or reanalysis weather for each episode. What the calls do give is the yield or crop loss in a named bad year, how much of it reached revenue, the price and insurance offsets, and what happened to profit.

## orchard (peril `spring_frost`)

### Episodes found
| Episode | Crop / volume loss | Revenue / profit effect | Basis |
|---|---|---|---|
| Alico, Florida citrus, Jan 2022 freeze (worst in ~20 yrs) | Valencia -12 to -15%; full-year boxes -12.9%; Apr-Jun quarter boxes -19.9%; state oranges -22.5%, state Valencia -33.9% | Citrus revenue -15.2% ($105.8M to $89.7M); price per pound solid +7.3%; net-income guidance cut about 14% | vs prior year |
| Seeka, NZ kiwifruit, Oct 2022 spring frost (plus hail and cyclones) | SunGold yield -22%; lowest Hayward yields in 10 years | Orcharding revenue -13%; orcharding EBITDA NZD 5.1M to -1.9M | vs prior year |
| Vintage Wine Estates, Oregon, April 2022 frost | Crop at 50-60% of a normal year (-40 to -50%) | not given | vs normal |
| Remy Cointreau, Cognac, April 2021 frost | Own estate -15% | "not so material" because of aged stocks | management estimate |
| Select Harvests, Australian almonds, spring 2024 frost | about 500 t, around -1.7% of crop | small | management estimate |
| Constellation, NZ (Kim Crawford), 2020/21 frost | lower production, amount not stated | hit margin through fixed-cost absorption | qualitative |
| LVMH and Verallia, France, April 2021 | France's harvest was the lowest in many years | LVMH: no unit-cost rise, fewer bottles in 2-3 years | qualitative, deferred |
| Limoneira (it gained), Spain/Turkey freeze 2025 | competitors 20-30% short | lifted Limoneira lemon prices from about $17 to the low $20s | management estimate |

### Recommended values
- **Revenue loss in a bad frost year for one grower: about 15%** (range 5-45%). Confidence: low to medium.
  - Two clean company revenue figures agree on -13% to -15%: Alico FY2022 and Seeka orcharding.
  - The single-region crop loss in Oregon (-45%) shows the upper end for a grower without frost protection or regional spread.
  - Mild events take 2% or less (Select Harvests).
- **Severe year: 40-50% crop loss.** The current `max_loss_frac` of 0.6 is a reasonable cap.
- **How often:**
  - Severe events happen about 1 year in 10 to 20 ("not occurred in Florida for almost 20 years", "lowest Hayward yields in 10 years").
  - Minor frost damage is common: Select Harvests had it in 2024 but not in 2025. Cobram Estate also cites a damaging frost in 2018 and has since spent about AUD 10M on frost fans.
- The current elasticity of 0.3 per % has no basis in these calls. As the brief expected, the per-% framing does not fit. Better: a direct loss fraction applied in a bad year, set by how severe the frost is.

### Offsets
- **Price:** Alico got +7.3% price on -12.9% volume, but revenue still fell slightly more than volume because fruit quality (solids per box) also fell. For a single grower, the price offset is small when the frost is regional. Growers outside the frost region gain (Limoneira).
- **Insurance:** Alico carries catastrophic-only cover. It says past claims (2018 freeze, Irma) were paid within the same crop year. No amount is given.
- **Inventory:** wine, Cognac and Champagne makers use reserves and aged stock to defer and spread the loss over 2-3 years. Do not use these as orchard revenue cases.

### Profit vs revenue
Profit falls much more than revenue. Seeka's orcharding EBITDA went from positive to negative on a 13% revenue drop. Constellation's frost cost showed up as unabsorbed fixed cost. Alico's net income is distorted by land-sale gains, so it is a poor guide to profit.

### Caveats
- **Timing:** most of the quantified cases are not Hone's Apr-May northern-hemisphere window. Alico was a January freeze. Seeka, Select Harvests and Constellation NZ were southern-hemisphere spring frosts (Sep-Oct). Only Oregon 2022 and France 2021 fit the window, and they are the least quantified.
- **Mixed causes:** Seeka mixes frost with hail and cyclones, and Alico mixes freeze with greening disease.
- **No coverage:** Quartr had no Fresh Del Monte or Crimson Wine, and no frost material for Calavo, Mission Produce, Duckhorn, Treasury Wine (only adaptation talk), Smucker, Seneca or Lamb Weston.

## farm_crops (peril `drought`)

### Episodes found
| Episode | Yield / volume loss | Revenue / profit effect | Basis |
|---|---|---|---|
| US 2012 (Deere) | corn production -13%, yield -16% YoY (about -24% vs trend); soybean production -12% (about -11% vs trend) | Sector cash receipts rose; crop insurance $15-16B, about 4% of gross income; about 85% of acres insured | vs prior year / vs trend |
| Argentina 2022/23 (Adecoagro, Cresud) | Adecoagro yields -30 to -40%, farming output -27%; Cresud soy -30 to -50% and corn -18 to -35% vs budget; national soy -50% | Adecoagro crop EBITDA $18M to about $0 (-99%); only a partial offset from a preferential FX rate; Cresud says prices and FX offset "the majority" | management estimate / vs plan |
| Same drought, irrigated rice (Adecoagro) | -6% | margins rose | vs prior year |
| Brazil 2021/22 (SLC) | second-crop cotton and corn -20% vs plan; South American soy -20% | record revenue on high prices; margins held | vs plan |
| Brazil 2023/24 El Nino (SLC) | soybeans -17% vs budget | Q1 net income -60%; prices also lower | vs plan |
| BrasilAgro 2022/23 (one farm in drought) | soybeans -6% vs plan | n/a | vs plan |
| Lithuania May-June 2023 (Akola) | harvest -4% | n/a | vs prior year |
| EU 2022 (Sudzucker beet) | sugar output about -16% vs the next year | segment revenue up on price | vs prior year |
| California 2021-22, irrigated (Gladstone Land, Farmland Partners) | low yields | participation rents -23% (with lower almond prices); loss carried into 2023 | vs prior year |
| CIS 2012 heat (Deere) | yield projections -20% | n/a | vs plan |
| Paraguay 2023/24 (Cresud) | -90 to -100% yield on the affected farms | n/a | vs prior year |

### Per-row elasticity
None can be computed, because no rainfall deviation was stated. What the calls do support:

- **Severe drought:** yield loss is 15-40%, and 50-100% on the worst-hit local farms.
- **Mild dry spell:** 4-6%.
- **Pass-through to revenue (1 minus price offset):**
  - about 0.8-1.0 for a local or regional drought that does not move world prices: Argentina 2023 (only offset was a government FX rate) and Mato Grosso 2024 (prices fell too).
  - about 0 or negative for the sector in a breadbasket drought that moves world prices: US 2012 and South America 2022, where receipts rose.

### Recommended value
**Keep `fixed_elasticity` at 0.6, range 0.3-1.0. Confidence: low.**
- 0.6 is the yield loss times (1 - 40% offset) that the US 2012 case supports for an insured US farm.
- For rain-fed farms outside the US, in regions too small to move world prices (Argentina, Brazil, Baltics), the evidence points to the top of the range (0.8-1.0 of yield loss reaching revenue). They usually have little or no revenue insurance.
- For irrigated farms it should be far lower: rice -6% in the same Argentine drought.
- To turn this into a per-1% rainfall elasticity, join the episodes to observed May-Aug rainfall. Candidates: US Midwest 2012, Pampas Nov 2022-Mar 2023, western Mato Grosso Oct-Dec 2023, Lithuania May-Jun 2023, EU Jun-Aug 2022.

### Offsets
- **Price:** depends on scale. It is fully offset or better in aggregate when the drought hits a major exporter (US 2012, South America 2022, EU sugar 2022). It is small when the drought is local.
- **Crop insurance (US):** pays about 4% of sector gross income in 2012. Revenue-protection policies pay at harvest price.
- **Government policy:** Argentina's preferential FX rate in 2023.
- **Lower variable costs:** SLC used less chemical on a dry crop.

### Profit vs revenue
Profit falls 3-10 times more than revenue or yield, because costs per hectare are fixed:
- Adecoagro crop EBITDA -99% on -30 to -40% yields.
- SLC net income -60% on a -17% soybean shortfall.

### Caveats
- Several cases are southern-hemisphere seasons (Oct-Mar), not May-Aug.
- California cases are about irrigation-water allocations, not rainfall.
- Deere and Sudzucker figures are sector-wide or processor numbers, not single-farm revenue.
- Quartr had no 2012 transcripts for Andersons or ADM, no 2018-19 transcripts for Australian ag (GrainCorp and Elders coverage starts about 2021), and nothing useful from Bonduelle.
- Lindsay talks about drought helping irrigation demand, but gives no grower figure, so it is not used.
