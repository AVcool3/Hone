# 03 — Who the income hedge helps, who it hurts, and where it breaks

**What was run.** `research/prediction/sweeps.py` pushes 78,480 personas through the shipped sizing (`hone.prediction.hedge.hedge_income`, with `hone.prediction.liquidity` caps). It uses the eight occupations, `exposure_for` logic and `realized()` reality check from `segments.py`. It then re-runs 8,000 of them under ±1% perturbations of each input (89,679 extra runs). The full run takes about 40 s on 4 cores. Before sweeping, the script checks that its generalized exposure builder matches `segments.exposure_for` contract for contract on all 576 default personas.

| sweep | personas | what varies |
|---|---|---|
| core | 12,960 | gamma 0.25–12 (15 steps) × savings 0/1/3/6/12/24 mo × income ×0.5/1/2 × loss share ×0.5/1/1.5 × {default cap, uncapped}, market beliefs |
| liquidity | 28,224 | OI share 5/10/25/50/100%/off × slippage 1/3/5/10¢ × {flat book, ladder book} + uncapped; 8 gammas, 3 savings, 3 incomes |
| beliefs | 26,112 | market + pessimist/optimist × shift 0.05–0.30 × confidence 0.2–1.0; 8 gammas × 4 savings × {cap, uncapped} |
| prices | 8,640 | protective-side price 5–90¢ × {market, ±0.10 at 60%} |
| edges | 2,544 | gamma −1…100, loss up to 99.9% of wealth, price 1–3¢ / 97–99¢, basis 0–1 |

"CE gain" is the certainty-equivalent gain at the person's own gamma. **Realized** means it was computed under `Truth()`, where the market price and the basis are both right. For personas who hold a view, we also report it with the person's own probability taken as true ("view right"). The "flat book" is what `segments.py` assumes: all quoted depth sits at the quote. The "ladder book" spreads `depth/4` contracts at every cent, up to 20¢ deep, so buying more costs more.

Caveats: the model is judging itself here, because `Truth()` uses the model's own assumptions. The occupations are illustrative, and the ladder book is synthetic. Read the numbers as relative effects across segments.

All tables are in `findings/sweeps/tables.md`. Raw rows are in `findings/sweeps/personas_*.csv.gz` and `perturbations.csv.gz`. The charts are `a1_ce_heatmap.png`, `a2_liquidity_retained.png`, `a3_speculation.png` and `a4_gamma_edge.png`.

---

## Key findings

1. **Under the shipped cap, almost nobody gets meaningful value.** Only **2.7%** of core personas gain more than 0.5% of income. **83.5%** gain less than 0.05%, and **24%** are told to buy nothing. Without the cap, 26.6% would clear 0.5%. The people who gain are those with **high risk aversion (gamma ≥ 6), little savings (0–3 months), a big loss share and decent basis**. Uncapped, ski instructors, realtors, recruiters and contractors reach a median of 1.1–1.6% of income at gamma 6–8. Under the cap, only rideshare drivers reach 0.55% (at gamma 12) and contractors 0.34%.
2. **Two groups get essentially nothing even without the cap.**
   - **Tech workers** have basis 0.15, so they get at most 0.05% of income, and 0% of them clear the bar.
   - **Retirees** lose only 6% of income in a bad year, so the median gain is 0.00% and 3% clear the bar.

   **Savings remove the need:** contractor value falls from 0.67% of income at 0 months of savings to 0.04% at 24 months.
3. **The liquidity cap, not the model, decides the outcome for 6 of the 8 occupations.** At 10% of open interest (OI), contractors keep **24%** of their uncapped value, realtors 1.4%, recruiters 1.0%, ski 0.5%, ad freelancers 5.4% and tech 0%. Rideshare and retiree markets are deep enough that they keep 100%. Raising the cap to 25% roughly doubles the value kept (contractor 52%, realtor 3.4%). Beyond that, the thin markets still cannot help, because order-book depth becomes the binding limit.
4. **When a person holds a view, the position is mostly a bet.** The tilt from a view is a median **2.1× the pure hedge** for a gamma-2 pessimist and **7.9×** at gamma 0.5. The speculative share of the gross position is 43–87% by occupation; retirees are the highest at 87%. **37%** of personas with a view hold more than 2× the pure hedge. For **36%**, the worst-case outcome is more than 10% of income worse than not trading at all. If the market is right, the current advice costs **−2.4% of income on average and −37% at the 1st percentile**.
5. **Half of all optimists are told to sell the protection they need.** That is 6,368 of 26,112 belief personas (50% of optimists). Some sell at confidence as low as 0.2 or a shift as small as 0.05, and some sell even at gamma 12. The median sale is 0.73× the pure hedge. If the market is right, the 10th percentile loses **8.1% of income**. The liquidity cap does not prevent this: 24.9% of belief personas sell under both the capped and uncapped policy. Retirees under the default cap sell the full 5,738-contract OI limit.
6. **Gamma near zero produces a discontinuity, and very high gamma crashes.**
   - At gamma ≤ 0 the model shows the full pure hedge ρL, for example 10,500 contracts for a contractor, with a realized CE of −0.14% of income.
   - At gamma 0.001–0.25 with market beliefs it shows **0 contracts**.
   - With a modest pessimist view (+0.15 at 60%) it shows **124,061 contracts** (median), which is a bet sized at the solvency limit, and the gamma ≤ 0 warning does not fire.
   - At gamma ≳ 62–72, `hedge_income` raises `ZeroDivisionError` because `w^(1−γ)` underflows in `crra_utility`/`crra_inverse`.
7. **Low risk aversion buys nothing, and with weak basis high risk aversion buys less.** The taker fee adds 3.4–6.3% to the price of each contract, which is more than the insurance premium a low-gamma person will pay. So 92% of gamma-0.25 personas and 41% of gamma-1 personas get 0 contracts. Where basis is at most 0.6, the hedge ratio (contracts per contract of pure hedge) peaks at gamma 3–6 and then falls: contractor 1.20 → 0.69 at gamma 12, ski 0.78 → 0.45, tech 0.43 → 0.18. The reason is that the worst state is "lost the income and the contract did not pay", and every contract bought makes that state worse. The CRRA math is correct, but users will not expect it.
8. **About 1 in 18 personas (5.6%) changes its advice sharply when one input moves by 1%.** These cases sit at the point where hedging starts to beat the fee, and they are worth about $0: the median base CE is $0.00, and every no-view case is worth under $5. For example, an ad freelancer goes from 0 to 79 contracts as gamma moves from 0.744 to 0.760. This is a genuinely steep part of the curve, not a numerical bug. With a view, a 1% price move causes the jump 6.6% of the time (99th-percentile elasticity 88), because the tilt is proportional to (q − c). No case flipped between buying and selling.
9. **Many trades are worth nothing, and slippage is ignored.**
   - **12.5%** of personas get a non-zero trade worth under $1 of CE, with a median of 13 contracts, and 90% of these are capped.
   - The model sizes at the quoted price and then fills by walking the book. On the ladder book, **343** personas end up paying more than their reservation price at the average fill price, with a worst case of **−$531**. 993 liquidity-sweep personas end up with negative CE.
   - On the flat book, `max_slippage` has no effect at all: 1, 3, 5 and 10¢ all give the same contract counts.
10. **The model labels some positions as speculation when they are not, and some bets as hedges.**
    - For market-belief personas, `speculative_contracts` (n* − ρL) still comes out at −0.37× the pure hedge at the median, because of fees and CRRA skew; these people hold no view.
    - Basis 0 with a view yields a pure bet of ±13k contracts (realized CE down to −15% of income) with no "this is not a hedge" warning.
    - At extreme prices, views explode the position. A pessimist at 1¢ buys 177k contracts. An optimist at 97–99¢ sells 60k–138k contracts and loses about 2% of income if the market is right.
    - Every cost-over-25%-of-income case (2,604) comes from a view on an uncapped market.

---

## Key tables

### A1. Value by occupation (core sweep, market beliefs, realized under `Truth()`)

Medians are taken over gamma 0.25–12, savings 0–24 months, income ×0.5–2 and loss ×0.5–1.5. Percentages are % of income; the "> 0.5%" and "~0" columns are % of personas.

| occupation | loss/income | coverage (cap) | CE $ (cap) | CE % (cap) | > 0.5% (cap) | CE % (uncap) | > 0.5% (uncap) | ~0 (<0.05%) (cap) |
|---|---|---|---|---|---|---|---|---|
| rideshare | 0.10 | 1.00 | 10.77 | 0.03 | 10.4 | 0.03 | 12.6 | 56.9 |
| retiree | 0.06 | 1.00 | 0.40 | 0.00 | 3.0 | 0.00 | 3.0 | 74.4 |
| contractor | 0.50 | 0.17 | 29.15 | 0.04 | 7.9 | 0.18 | 36.3 | 52.7 |
| realtor | 0.40 | 0.01 | 5.07 | 0.01 | 0.0 | 0.46 | 48.5 | 96.4 |
| ad_freelancer | 0.30 | 0.04 | 3.73 | 0.01 | 0.0 | 0.09 | 25.2 | 87.4 |
| ski | 0.35 | 0.00 | 0.91 | 0.00 | 0.0 | 0.48 | 49.3 | 100.0 |
| recruiter | 0.35 | 0.01 | 1.84 | 0.00 | 0.0 | 0.24 | 38.2 | 100.0 |
| tech | 0.50 | 0.00 | 0.01 | 0.00 | 0.0 | 0.02 | 0.0 | 100.0 |

Median realized CE gain, % of income, by gamma. Each cell shows **capped / uncapped**, at income ×1.

| occupation | 1 | 2 | 4 | 6 | 8 | 12 |
|---|---|---|---|---|---|---|
| rideshare | 0.00 / 0.00 | 0.01 / 0.01 | 0.11 / 0.11 | 0.22 / 0.23 | 0.33 / 0.35 | 0.55 / 0.60 |
| retiree | 0.00 / 0.00 | 0.00 / 0.00 | 0.02 / 0.02 | 0.06 / 0.06 | 0.10 / 0.10 | 0.20 / 0.20 |
| contractor | 0.01 / 0.02 | 0.03 / 0.14 | 0.09 / 0.55 | 0.17 / 1.09 | 0.25 / 1.08 | 0.34 / 0.95 |
| realtor | 0.00 / 0.09 | 0.00 / 0.43 | 0.01 / 1.10 | 0.02 / 1.34 | 0.02 / 1.17 | 0.02 / 0.91 |
| ad_freelancer | 0.00 / 0.00 | 0.00 / 0.07 | 0.01 / 0.29 | 0.02 / 0.57 | 0.03 / 0.86 | 0.05 / 1.22 |
| ski | 0.00 / 0.10 | 0.00 / 0.46 | 0.00 / 1.16 | 0.01 / 1.62 | 0.01 / 1.54 | 0.01 / 1.22 |
| recruiter | 0.00 / 0.03 | 0.00 / 0.20 | 0.00 / 0.67 | 0.01 / 1.12 | 0.01 / 1.39 | 0.01 / 1.10 |
| tech | 0.00 / 0.00 | 0.00 / 0.01 | 0.00 / 0.05 | 0.00 / 0.05 | 0.00 / 0.04 | 0.00 / 0.04 |

% of personas with CE > 0.5% of income, by gamma band × savings months. Each cell shows **uncapped / capped**.

| gamma | 0 mo | 1–3 mo | 6 mo | 12–24 mo |
|---|---|---|---|---|
| ≤ 1 | 6.2 / 0.0 | 3.1 / 0.0 | 1.0 / 0.0 | 0.0 / 0.0 |
| 1–3 | 30.0 / 1.1 | 26.7 / 0.4 | 17.5 / 0.0 | 7.5 / 0.0 |
| 3–6 | 50.0 / 7.4 | 45.8 / 5.6 | 40.3 / 2.3 | 27.8 / 0.2 |
| 6–12 | 69.4 / 14.8 | 66.0 / 12.3 | 59.7 / 8.8 | 44.4 / 3.5 |

Hedge ratio by gamma (contracts ÷ pure hedge ρL), uncapped, savings 3 months. With weak basis the ratio peaks in the middle of the gamma range:

| occupation (ρ) | 0.5 | 1 | 2 | 4 | 6 | 8 | 12 |
|---|---|---|---|---|---|---|---|
| rideshare (0.85) | 0.00 | 0.01 | 0.51 | 0.75 | 0.83 | 0.86 | 0.89 |
| contractor (0.30) | 0.19 | 0.72 | 1.04 | 1.20 | 1.13 | 0.98 | 0.69 |
| ski (0.60) | 0.28 | 0.62 | 0.77 | 0.77 | 0.69 | 0.60 | 0.45 |
| tech (0.15) | 0.00 | 0.05 | 0.38 | 0.41 | 0.33 | 0.27 | 0.18 |

### A2. Liquidity policy (% of uncapped realized CE retained, median)

On the flat book, slippage has no effect; only the OI share matters.

| occupation | OI 5% | **10% (now)** | 25% | 50% | 100% | off |
|---|---|---|---|---|---|---|
| rideshare | 82.1 | 100 | 100 | 100 | 100 | 100 |
| retiree | 100 | 100 | 100 | 100 | 100 | 100 |
| contractor | 12.4 | **23.9** | 52.4 | 83.6 | 100 | 100 |
| realtor | 0.7 | **1.4** | 3.4 | 6.8 | 13.3 | 18.9 |
| ad_freelancer | 5.4 | 5.4 | 5.4 | 5.4 | 5.4 | 5.4 |
| ski | 0.2 | 0.5 | 1.0 | 1.0 | 1.0 | 1.0 |
| recruiter | 0.5 | 1.0 | 2.6 | 5.2 | 6.1 | 6.1 |
| tech | 0.0 | 0.0 | 0.3 | 0.5 | 1.1 | 12.3 |

On the ladder book, with 3¢ slippage, the median realized CE gain in dollars by OI share is:

| occupation | 5% | 10% | 25% | 50% | 100% | off |
|---|---|---|---|---|---|---|
| contractor | 39 | 76 | 167 | 253 | 255 | 255 |
| realtor | 4.9 | 9.8 | 24 | 47 | 88 | 119 |
| recruiter | 2.0 | 4.1 | 9.9 | 18 | 20 | 20 |
| rideshare | 37 | 49 | 47 | 47 | 47 | 47 |

On the ladder book, the slippage setting changes the result as follows:

- With slippage of 5¢ or more, the **mean** fraction of uncapped value retained goes negative: −0.06 at 100% OI and 5¢, and −1.15 with no OI cap and 10¢. The cause is that sizing still uses the quote while fills walk the book. A tech persona with no OI cap and 10¢ slippage keeps a median of −13% of its uncapped value.
- With no OI cap and 10¢ slippage, the p90 position is **28.9× open interest**.

**Is 10% too strict?** For the markets where the cap binds and the order book could supply more, yes. Contractors give up 76% of their value, and at 25% they would keep 52% on the flat book and 49% on the ladder, while holding at most a quarter of open interest. For the deep markets (rideshare, retiree) the cap does not bind at all. For the thin ones (ski, recruiter, ad, tech), no reasonable cap helps, because depth runs out first.

**Recommended default:** `max_share_of_open_interest = 0.25` with `max_slippage = 0.03`. Raise the slippage only after sizing becomes fill-aware (change 5 below). Going to 50% adds another 60–100% for contractors and realtors on the flat book. On the ladder book it adds little for contractors (62% vs 49% retained), it means holding half the market, and the cost of getting out of that position is not modeled.

### A3. Failure-mode counts (75,936 personas in core + liquidity + beliefs + prices)

| sweep | sells while exposed | cost > 25% income | quote > reservation & buy | fill > reservation & buy | model CE < 0 | realized CE < 0 | realized CE < 0, no view | trade worth < $1 | n |
|---|---|---|---|---|---|---|---|---|---|
| beliefs | 6,368 | 2,211 | 0 | 0 | 70 | 11,879 | 4 | 2,674 | 26,112 |
| core | 0 | 0 | 0 | 0 | 69 | 69 | 69 | 1,571 | 12,960 |
| liquidity | 0 | 0 | 0 | 343 | 993 | 993 | 993 | 4,139 | 28,224 |
| prices | 1,460 | 393 | 0 | 0 | 49 | 2,778 | 26 | 1,133 | 8,640 |

Notes on the table:

- "Quote > reservation & buy" never happens: buying above the reservation price only appears once the order book is walked.
- The 69 negative-CE personas in the core sweep come from the fee being rounded up to the cent; each loses at most $0.009.
- Every case of cost above 25% of income involves a view on an uncapped market; the default cap prevented all of them in this grid.

**Instability** (8,000 personas, ±1% perturbations of each input; "unstable" means a change of at least max(3 contracts, 10%), or switching between zero and non-zero):

| input | no view | with view |
|---|---|---|
| gamma | 1.3% | 1.7% |
| wealth | 1.4% | 1.8% |
| loss | 1.4% | 1.8% |
| basis | 1.4% | 1.8% |
| confidence | — | 2.1% |
| price | 0.04% | **6.6%** (p99 elasticity 88) |

**Speculation.** The tilt is n*(view) − n*(market). The table gives its median as a multiple of the pure hedge ρL:

| gamma | 0.5 | 1 | 2 | 4 | 8 | 12 |
|---|---|---|---|---|---|---|
| pessimist | +7.94 | +4.16 | +2.08 | +0.98 | +0.41 | +0.25 |
| optimist | −5.01 | −2.58 | −1.21 | −0.75 | −0.41 | −0.23 |

**Counterfactual: capping the tilt.** These are the 12,800 uncapped personas who hold a view. Each variant keeps n_mkt and allows at most X·ρL of tilt on top. Figures are realized CE as % of income.

| variant | mkt right: median | mkt right: p5 | mkt right: p1 | mkt right: mean | view right: median | view right: mean | break-even P(view right) |
|---|---|---|---|---|---|---|---|
| current advice | −0.12 | −14.0 | −37.4 | −2.41 | +1.80 | +5.03 | — |
| cap 0× (no tilt) | +0.13 | 0.00 | 0.00 | +0.43 | 0.00 | +0.44 | 38% |
| cap 0.5× ρL | +0.08 | −0.12 | −0.27 | +0.33 | +0.56 | +1.17 | 42% |
| **cap 1× ρL** | −0.04 | −0.46 | −0.76 | +0.18 | +0.94 | +1.64 | 43% |
| no-sell only | 0.00 | −6.50 | −24.4 | −0.98 | +0.53 | +3.50 | 48% |

"Break-even" is how often the person's view must be right for the current advice to beat the variant on average. Retail forecasters rarely beat a liquid market price that often.

### A4. Edges of the domain

| edge | behaviour |
|---|---|
| gamma ≤ 0 | Pure hedge ρL (rideshare 3,825, contractor 10,500, tech 11,250), realized CE −0.14% of income, warning fires |
| gamma 0.001–0.25 | Market belief: 0 contracts. Pessimist +0.15 @ 60%: **124,061 contracts** (median); the gamma ≤ 0 warning does not fire |
| gamma 20–50 | Smooth; hedge ratio shrinks (contractor 0.27× → 0.11×) |
| gamma ≥ ~62–72 | `ZeroDivisionError` (32 of 32 gamma-100 personas); the threshold depends on wealth |
| loss 99.9% of wealth | No errors; position shrinks smoothly (median 12–126 contracts), CE ≤ 0.24% of income |
| price 1¢ | Market: fine (cost 0.1% of income). Pessimist: 177k contracts, −2.4% of income if the market is right |
| price 97–99¢ | Market: fine. Optimist: sells 60k–138k contracts, about −2% of income if the market is right. Pessimist at 99¢ ends up selling, because `segments.py` clips the view to 0.98 (artifact of the research script) |
| basis 0 | Market: 0 contracts (correct). With a view: ±13k contracts of pure bet, realized CE down to −15% of income, labelled as a hedge |
| basis 1 | Fine; no clipping (ρ_max = 1 when q_event = q_loss) |

---

## Recommended model changes (ranked)

1. **Do not let hedgers sell protection by default.** For `loss > 0`, set `allow_selling=False` (or require an explicit opt-in). When the optimum is negative, return 0 contracts with the message "your view says this insurance is overpriced — skip it."
   - *Evidence:* 50% of optimists are told to sell, at a 10th-percentile cost of −8.1% of income if the market is right. The liquidity cap does not stop it; retirees sell 5,738 contracts under the default cap.
   - *Cost:* flooring at zero costs only 1.5% of income in the view-right case, and needs P(view right) > 48% to be worth giving up.
2. **Limit the speculative tilt to 1× the pure hedge for hedgers:** |n − n_mkt| ≤ ρL, where n_mkt is the market-belief optimum, which costs one extra `optimal_contracts` call. Offer anything beyond that as a separately labelled, opt-in "bet" with its own Kelly/CRRA sizing.
   - *Evidence:* under market truth, the 1st-percentile outcome improves from −37.4% to −0.76% of income, and the mean from −2.41% to +0.18%. The cap keeps about half the view-right median upside (+0.94% vs +1.80%) and about a third of the mean.
   - *Break-even:* 43%.
   - Use 0.5× for gamma < 2, where tilts are 2–8× ρL.
3. **Make gamma handling continuous and safe.**
   - Replace the gamma ≤ 0 branch, which shows a full ρL hedge at negative CE, with a floor such as gamma < 0.5 → 0 contracts and the message "insurance isn't worth its fee at your risk tolerance." This matches what gamma 0.001–0.25 already returns.
   - Apply the low-gamma warning to any 0 < gamma < 0.5 with a view: that is where the 124k-contract bets come from.
   - Work with W/W₀ (normalized wealth) or log-space CE so that gamma ≳ 60 does not raise `ZeroDivisionError`, or clamp gamma at 30.
4. **Raise `DEFAULT_MAX_SHARE_OF_OI` from 0.10 to 0.25.** Contractors would keep 52% of their uncapped value instead of 24%, about $167 instead of $76 median on the ladder book. Realtors and recruiters would gain about 2.5×. Positions would stay at no more than a quarter of OI, and deep markets would be unaffected.
5. **Size against the book, not the quote.**
   - When an order book is available, maximize EU with n·avg_fill(n) as the cost. A simple fixed-point loop also works: re-solve at the average fill until it stops changing.
   - Never propose a size whose average fill exceeds the reservation price.
   - *Evidence:* 343 ladder-book personas pay above their reservation price (worst −$531), and the mean value retained turns negative at slippage ≥ 5¢.
   - The flat-book assumption also hides the `max_slippage` parameter entirely. Until this is fixed, keep slippage at 3¢.
6. **Add a materiality threshold, with hysteresis.** Show "not worth trading" when the CE gain is below max($5, 0.05% of income).
   - *Evidence:* 12.5% of personas get trades worth under $1, a median of 13 contracts.
   - The same threshold removes almost all of the 1% instability, since every no-view unstable case is worth under $5. Hysteresis stops the advice flickering between 0 and 70 contracts as answers move slightly.
7. **Warn when the market cannot hedge this person, whatever the cap.** If ρ < 0.2 or the uncapped CE is below 0.05% of income, say "this market tracks too little of your risk." Tech workers at ρ = 0.15 never exceed 0.05% of income. When basis = 0 and loss > 0, label the position as a bet, not a hedge.
8. **Report the speculative part relative to n_mkt, not ρL.** Today a user with no view sees `speculative_contracts` = −0.37× the hedge (median), which is really fee drag and CRRA skew.
9. **Explain basis-driven shrinkage in the UI.** For ρ ≤ 0.6 the most risk-averse users are told to hedge less: contractor 1.20× ρL at gamma 4 versus 0.69× at gamma 12. Add one sentence: "your worst case is losing income *and* the contract not paying; more contracts make that case worse."
10. **Fix in research (not the model):** the clip in `segments.exposure_for`, `own = clip(price + shift, 0.02, 0.98)`, turns a pessimist into an optimist at prices ≥ 0.98. Clip the shift instead.

## Reproduce

```
pip install matplotlib   # charts only
python research/prediction/sweeps.py            # ~40 s, writes findings/sweeps/
python research/prediction/sweeps.py --analyze  # re-run analyses/charts on saved CSVs
```
