# 11. What weather has cost companies, from their earnings calls (November 2026)

**Question.** The quote engine (`hone/prediction/quote.py`, `BUSINESSES`)
needs one number per type of business: how much revenue falls for each 1%
that the season's weather is worse than normal. Some of those numbers were
measured (studies 06 and 09); others were guesses. Earnings calls are where
managers explain a bad quarter, often with figures ("snowfall was 55% below
last year and visits fell 13%"). How do the guesses hold up?

**Method.** Four researchers each covered one group of businesses (snow,
rain-stopped work, summer weather, farms) and searched Quartr's call
transcripts. They recorded every statement that ties weather to revenue,
with a link to the exact paragraph. Where a company compared revenue to
the prior year, they compared it with the prior year's weather too, so
both sides are measured the same way.

- Data: `research/prediction/data/calls/*.csv`. There are **195
  statements from 52 companies**, and each one links to its source.
- Each group's reasoning, with per-row workings, is in
  `research/prediction/data/calls/*_notes.md`.
- Cross-check and summary: `python research/prediction/call_sensitivity.py`.
  Its per-row ratios are rough, because it doesn't know which rows are
  measured against last year and which against normal. The matched
  figures in the notes are the ones used below.

## What changed in the quote engine

Effective sensitivity = % of revenue lost per 1% worse weather.

| Business | Before | Now | Confidence | Evidence |
|---|---|---|---|---|
| Ski resort | Vail-calibrated (study 06) | **unchanged** | medium-high | Vail's 2025/26 Rockies winter had 55% less snow than the year before. Visits fell 13% and revenue only about 5%, because passes cushion it. That is what the model already assumed. |
| Ski instructor | 1.3× the resort | **1.5×** | low | Vail's ski-school revenue fell 1.4–2.1× as much as resort revenue. There is no data on an individual instructor's pay. |
| Mountain shop / restaurant | 0.7× the resort | **1.3×** | low-medium | Vail's retail, dining and lodging fell 1.2–2.2× as much as resort revenue. Passes cushion the resort, not the shops. |
| Snow removal | 1.0, half of lost revenue offset by lower costs | **0.9**, with **60%** offset | high | BrightView, 8 matched seasons (median 0.92), and road-salt volumes (about 0.85). Only 20–30% of BrightView's snow-revenue swing reached its profit, because subcontractors are paid less. |
| Outdoor venue | 0.35 | **unchanged** | medium-low | Six Flags 2025 gives at most about 0.6 for attendance. Revenue falls less than attendance (SeaWorld: attendance −4.7%, revenue −1.1%). |
| Construction | 0.2 | **0.15** | medium-low | 9 companies. A wet quarter costs 4–10% of that quarter's volume, but 30–70% comes back within the season. Profit falls 1.5–2× as much as revenue. |
| Day-paid tradesperson | 0.9 | **0.25** | medium | See below. |
| Landscaping | 0.15 | **0.12** | low-medium | SiteOne and BrightView: contract mowing barely moves, and other work is put off rather than lost. |
| HVAC contractor | 0.9 | **0.6** | low-medium | In one region and quarter, revenue moves 0.4–1.1× with cooling degree days (Lennox, Frontdoor). Over a year it moves less, as replacements are put off, and the Sun Belt barely reacts. |
| Outdoor worker (heat) | 0.3 | **0.2** | low, still an assumption | Calls describe earlier shifts and heat breaks, but none put a number on lost pay. |
| Orchard (frost) | 0.3 | **unchanged** | low-medium | Alico lost 15% of revenue in its 2022 freeze year and Seeka 13% in its 2022 frost year. That is about the most the current setting allows (0.3 × the 50% cap on counted shortfall = 15%). |
| Crop farm (drought) | 0.6 | **unchanged** | low | Severe droughts cut yields 15–40% (US 2012, Argentina 2023, Brazil 2024). |

**The biggest correction is the tradesperson.** The old value (0.9) assumed
that each 1% more rain days costs nearly 1% of pay. But days with 5+ mm of
rain are only 12–20% of March–November days. If each rain day is a day's
pay lost and never made up, 1% more rain days costs about 0.15–0.25% of
pay. Wet ground stretches this a little: Vulcan said 30 rain days in
Nashville cost half its shipping days. The old figure overstated a
tradesperson's risk about 4×, so their quotes were too high. This one is
worked out rather than measured. Calls had no figures on day labourers' pay.

## Patterns across industries

1. **Lost vs. put off decides the loss.** Lost visits are gone for good
   (parks, ski tickets, plowing). Construction, landscaping and HVAC
   replacements mostly come back later in the season, or in the next one.
   That is why their sensitivities are low even though a single wet
   quarter looks bad.
2. **Profit moves more than revenue for asset-heavy businesses, and less
   for subcontract-heavy ones.**
   - Asset-heavy, profit falls more: idle plants and fleets (construction,
     1.5–2×), orchards (Seeka's orcharding profit went from +NZ$5.1m to
     −NZ$1.9m), farms (Adecoagro crop EBITDA −99%).
   - Subcontract-heavy, profit falls less: BrightView's snow business, where
     subcontractors are paid less in a dry winter.
3. **Pre-sold revenue isn't immune.** Bad weather in May–June 2025 cost
   Six Flags 300,000 season-pass sales. Vail gets about 70% of its lift
   revenue from passes, far above the 25% default. A resort that knows its
   own pass share should enter it.
4. **How far a drought reaches decides the price offset.** US farm receipts
   *rose* in 2012, because prices rose with a national drought. Regional
   droughts (Argentina 2023, Mato Grosso 2024) got almost no price offset,
   so a non-US or local grower's sensitivity is nearer 0.8–1.0.

## Limits and next steps

- Most statements compare with last year, not with normal. Each calendar
  quarter should be joined to observed weather (NOAA/ERA5 for the
  company's region) and fitted properly. The researchers recorded region
  and period for this.
- Calls cover big companies. A one-truck plowing business or a single
  orchard may be more exposed than BrightView or Alico, which spread risk
  across regions.
- No call gave usable figures for: outdoor workers' heat losses, frost in
  the northern-hemisphere April–May window (most quantified frosts were
  winter freezes or southern-hemisphere springs), Compagnie des Alpes,
  Toro, Columbia, Canada Goose or VF.
