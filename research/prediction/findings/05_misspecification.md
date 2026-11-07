# 05: Does the hedge still help when the model is wrong?

Script: `research/prediction/misspecification.py`. Full run: `python research/prediction/misspecification.py` (about 10 minutes; `--draws 5` is faster; `--out DIR` writes per-case CSVs).

**Model under test.** This tests `hone/prediction/hedge.py` **as committed at git HEAD**: the version that sized every plan in `segments.py` when this study began. It is unchanged since commit 5a157de. The script loads that file with `git show` so the results can be reproduced. While this study ran, the working tree gained an uncommitted rewrite of `hedge.py` ("v2"). It adds `loss_prob`, stops hedgers from selling, caps the view tilt with `MAX_VIEW_TILT`, and adds a minimum-worth gate. v2 is scored below as a candidate (`worktree_v2*`). It was the working-tree file at about 03:45 UTC on 2026-11-07, and it changed again later.

## Summary

- **The model's promise is thin.** When every assumption holds, the mean CE gain across the 96 no-view, uncapped personas is $277, on positions that cost thousands of dollars. Most of the potential errors cost money in proportion to position size: price bias, slippage, a basis that is too high, loss and event probabilities that differ. So small errors flip the sign. Each cent of price error costs about $55 of the $277. At 5¢ the hedge is worth roughly nothing on average, and it hurts 57–58% of personas.
- **Single assumptions, uncapped advice, no view.** In the bad half of each range, the share of personas the hedge hurts is:
  - 50–62% when the loss probability is 2–3× the event's;
  - 69–87% when a user guesses basis 0.6 and the true basis is ≤ 0.3;
  - 72–83% when settlement overlaps only 25–50% of the loss;
  - 41–58% at 3–5¢ of price bias or slippage.

  Without a view, the harm is small in dollars: usually below 0.5% of income and at worst 2.1%. The tech worker's basis is the worst case.
- **Views are the catastrophic case.** With a stated view, harm is large. A user with poor information and 90% confidence loses on average $5.6k of CE (8.5% of income) when hurt, and the worst case is 107% of income at gamma 0.5. In the severe joint world, the baseline hurts 63% of personas and its worst case is 91% of income.
- **The liquidity cap is already a strong safety device.** In the severe joint world, capped advice has an expected harm of $23, against $514 uncapped. Most of what remains comes from deep markets (rideshare, retiree).
- **Recommended package**, ranked below:
  1. Cap the view tilt and stop hedgers from selling.
  2. Shrink the basis by 0.75 when sizing.
  3. Size at the price plus 1¢.
  4. Keep the minimum-worth gate.
  5. Make `loss_prob` optional, asked only where the event clearly differs from the loss.

  On top of v2, items 2 and 3 reduce the share hurt under the six single-assumption stresses from **42.7% (HEAD) / 23.9% (v2) to 9.6%**, and expected harm from **$216 / $68 to $18**. In the severe joint world they reduce expected harm from **$514 / $195 to $74**, and the worst case from **91% / 6.6% to 4.6% of income**. The cost is **19% of the CE gain when the model is exactly right** (80.8% kept, compared with 97.6% for v2 alone).

## Method

**Personas.** These are the `segments.py` personas with `belief = "market"` (no view): 8 occupations × savings {0, 3, 12} months × gamma {0.5, 2, 4, 8} × liquidity {capped, uncapped}, which is 192 personas. Assumption 3 and the joint worlds give these personas random views. Tables show **uncapped** advice unless they say otherwise. Uncapped advice is what the model wants. The liquidity cap shrinks positions, and with them both gains and harms, in thin markets. "capped" columns use HEAD's 10% open-interest cap and a flat book at the quote.

**Scoring.** `segments.realized(p, plan, Truth(q_event, q_loss, rho))` gives the exact expectation over the four joint states. The **realized CE gain** is CE(hedged) − CE(unhedged) at the persona's own gamma under the true world. The **model CE gain** is `plan.ce_gain`, which is what the page would show. A persona is **hurt** when the realized gain is below −$0.005. "hurt >0.1% inc" counts only harms above 0.1% of income. "harm (if hurt)" is the mean over hurt personas. E[harm] is the mean of max(0, −gain) over all personas. There were no ruins (wealth ≤ 0 in some true state). As a check, when the truth equals the model, realized gain equals model gain to 0.00e+00 for all 192 personas.

**The six assumptions, each broken alone. Everything else stays right.**

| # | Model assumes | True world in the stress |
|---|---|---|
| 1 | loss probability = contract probability (`joint_states(belief, belief, ρ)`) | q_loss = m × q_event, m ∈ {0.25, 0.5, 1.5, 2, 3}, capped at 0.95. ρ is the occupation basis, clipped to the Fréchet bound. For m < 1 that bound usually binds: the loss then happens only in seasons when the event also happens. |
| 2 | basis is known | the user enters 0.6 for every occupation; the true basis is 0.5 / 0.4 / 0.3 / 0.2 / 0.1 |
| 3 | the view is worth its stated confidence | true q = sigmoid(logit(price) + N(0, 0.3)). The market is unbiased but noisy. The user's own_prob = true + logit noise with sd 0.3 / 0.6 / 1.2 (sharp / average / poor), plus an optional +0.4 logit pessimist bias. Stated confidence is 0.3 / 0.6 / 0.9. The Bayes-optimal confidence would be about 0.5 / 0.2 / 0.06. There are 30 users per persona per cell. |
| 4 | price = true probability | true = price − 1/2/3/5¢, or price + 3¢, or a favourite-longshot curve logit(q) = β·logit(price) with β = 1.15 or 1.30 |
| 5 | contract settles on the loss period | effective basis = default × overlap, with overlap 75 / 50 / 25% |
| 6 | fills at the quote | fills 1 / 2 / 3 / 5¢ worse; the fee is recomputed at the fill |

**Joint worlds.** Each world takes 30 random draws per persona.

| Parameter | Severe | Mild |
|---|---|---|
| q_loss/q_event | log-uniform on [0.25, 3] | log-uniform on [0.5, 2] |
| True basis | default × U[0.3, 1] | default × U[0.6, 1] |
| Favourite-longshot β | U[1, 1.3] | U[1, 1.15] |
| Market logit noise sd | 0.2 | 0.2 |
| Slippage | U[0, 3¢] | U[0, 1.5¢] |
| Users with a view | 50%, logit sd 0.6, confidence 0.3 / 0.6 / 0.9 | same as severe |

**Candidates.** Every candidate is a wrapper around HEAD's `hedge_income` or its helpers (`optimal_contracts`, `joint_states`, `_wealth`), and nothing under `hone/` is changed. Each is scored on the same cases. "kept %" is the realized CE gain summed over the model-right world as a percentage of the baseline's. "right+views" is a model-right world in which the `pessimist`/`optimist` personas' views are *correct*. That measures what a tilt cap gives up. Assumption 3 is subsampled to 6,400 cases for the candidates. When a user-supplied q_loss is used, it is the true q_loss × lognormal(0, 0.35): users misjudge their own loss rate by about ±35%.

## Results per assumption (baseline = HEAD `hedge_income`)

### A1. Loss probability equals the contract's probability

**Loss more common than the event (m > 1).** Coverage falls short. The true ρ is capped at √(q_e(1−q_l)/(q_l(1−q_e))), so some loss seasons pay nothing. The premium (fee plus any price error) buys less protection. At m = 2 the hedge delivers −7% of what the model promised, and at m = 3 it delivers −49%. It hurts 50–62% of personas, by up to 1.7% of income (realtor, ski).

**Loss rarer than the event (m < 1).** On average the hedge does *better* than promised. In this construction the loss then occurs only when the event also occurs. Even so, 16–34% of personas are hurt, in small amounts (at most $79). For them, the contract pays out in many seasons with no loss, which makes it a fair bet that adds variance and costs a fee.

**Who is hit.** Rideshare and retiree are hurt most often (55–67%) but by small amounts, because their promised gain is only $18–70. Realtor and ski take the largest harms.

By level (uncapped; the last two columns are with the liquidity cap):

| level | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc | hurt % (capped) | harm $ (capped, if hurt) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q_loss = 0.25 x q_event | 96 | 277 | 340 | 1.23 | 34.4 | 7.3 | 28 | 0.1 | 79 | 0.2 | 26.0 | 24 |
| q_loss = 0.5 x q_event | 96 | 277 | 397 | 1.43 | 15.6 | 0.0 | 4.53 | 0.0 | 8.85 | 0.0 | 13.5 | 4.52 |
| q_loss = 1 x q_event | 96 | 277 | 277 | 1.00 | 0.0 | 0.0 | 0.00 | 0.0 | 0.00 | 0.0 | 0.0 | 0.00 |
| q_loss = 1.5 x q_event | 96 | 277 | 144 | 0.52 | 22.9 | 0.0 | 11 | 0.0 | 26 | 0.1 | 13.5 | 5.17 |
| q_loss = 2 x q_event | 96 | 277 | -19 | -0.07 | 50.0 | 28.1 | 200 | 0.4 | 588 | 1.7 | 31.2 | 37 |
| q_loss = 3 x q_event | 96 | 277 | -136 | -0.49 | 61.5 | 42.7 | 285 | 0.5 | 1,070 | 1.7 | 38.5 | 36 |

By occupation, pooled over the misspecified levels (uncapped):

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 60 | 70 | -43 | -0.61 | 66.7 | 31.7 | 69 | 0.2 | 288 | 0.6 |
| retiree | 60 | 18 | -9.14 | -0.50 | 55.0 | 8.3 | 19 | 0.0 | 94 | 0.2 |
| contractor | 60 | 443 | 407 | 0.92 | 8.3 | 0.0 | 6.71 | 0.0 | 12 | 0.0 |
| realtor | 60 | 628 | 263 | 0.42 | 41.7 | 31.7 | 457 | 0.6 | 1,070 | 1.3 |
| ad_freelancer | 60 | 228 | 172 | 0.76 | 6.7 | 0.0 | 4.57 | 0.0 | 13 | 0.0 |
| ski | 60 | 305 | 45 | 0.15 | 43.3 | 38.3 | 303 | 0.9 | 580 | 1.7 |
| recruiter | 60 | 470 | 290 | 0.62 | 26.7 | 15.0 | 208 | 0.3 | 604 | 0.8 |
| tech | 60 | 51 | 36 | 0.72 | 46.7 | 0.0 | 56 | 0.0 | 116 | 0.1 |

By gamma, pooled over the misspecified levels (uncapped):

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 120 | 5.08 | -4.62 | -0.91 | 20.8 | 4.2 | 31 | 0.1 | 148 | 0.2 |
| 2.00 | 120 | 153 | 32 | 0.21 | 46.7 | 15.0 | 98 | 0.2 | 761 | 1.0 |
| 4.00 | 120 | 374 | 154 | 0.41 | 41.7 | 20.0 | 191 | 0.3 | 1,044 | 1.6 |
| 8.00 | 120 | 574 | 399 | 0.69 | 38.3 | 23.3 | 259 | 0.5 | 1,070 | 1.7 |

Share hurt (%) by occupation × gamma (uncapped, misspecified levels):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 13 | 13 | 0.00 | 0.00 |
| contractor | 27 | 6.67 | 0.00 | 0.00 |
| realtor | 40 | 47 | 40 | 40 |
| recruiter | 40 | 27 | 20 | 20 |
| retiree | 0.00 | 67 | 87 | 67 |
| rideshare | 0.00 | 100 | 87 | 80 |
| ski | 47 | 47 | 40 | 40 |
| tech | 0.00 | 67 | 60 | 60 |

### A2. Basis correlation overestimated (user enters 0.6)

This is the most damaging assumption when there is no view. Most of the position becomes a near-fair bet once the true basis falls. At a true basis of 0.5 the hedge delivers 63% of the promise. At 0.3 it delivers −6% and 69% of personas are hurt. At 0.1 it delivers −69%: 87% are hurt, by $617 on average and up to $3,085 (2.1% of income, tech worker).

Big-loss occupations take the largest dollar harm: tech, realtor, recruiter, contractor. Rideshare and retiree are hurt as often but lose little. Hone's own defaults overstate the basis in the same way when settlement is misaligned; see A5.

By level (uncapped; the last two columns are with the liquidity cap):

| level | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc | hurt % (capped) | harm $ (capped, if hurt) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model 0.6, true 0.6 | 96 | 772 | 772 | 1.00 | 0.0 | 0.0 | 0.00 | 0.0 | 0.00 | 0.0 | 0.0 | 0.00 |
| model 0.6, true 0.5 | 96 | 772 | 488 | 0.63 | 8.3 | 0.0 | 2.44 | 0.0 | 13 | 0.0 | 3.1 | 0.26 |
| model 0.6, true 0.4 | 96 | 772 | 217 | 0.28 | 22.9 | 0.0 | 12 | 0.0 | 61 | 0.0 | 14.6 | 1.48 |
| model 0.6, true 0.3 | 96 | 772 | -43 | -0.06 | 68.8 | 31.2 | 122 | 0.1 | 626 | 0.4 | 25.0 | 6.53 |
| model 0.6, true 0.2 | 96 | 772 | -293 | -0.38 | 85.4 | 63.5 | 343 | 0.4 | 1,880 | 1.3 | 28.1 | 13 |
| model 0.6, true 0.1 | 96 | 772 | -534 | -0.69 | 86.5 | 69.8 | 617 | 0.7 | 3,085 | 2.1 | 38.5 | 15 |

By occupation, pooled over the misspecified levels (uncapped):

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 60 | 28 | -9.80 | -0.35 | 48.3 | 10.0 | 28 | 0.1 | 111 | 0.2 |
| retiree | 60 | 5.83 | -2.86 | -0.49 | 46.7 | 0.0 | 7.64 | 0.0 | 34 | 0.1 |
| contractor | 60 | 1,529 | 300 | 0.20 | 50.0 | 31.7 | 213 | 0.3 | 774 | 1.1 |
| realtor | 60 | 971 | -122 | -0.13 | 58.3 | 53.3 | 487 | 0.6 | 1,373 | 1.7 |
| ad_freelancer | 60 | 513 | 34 | 0.07 | 51.7 | 30.0 | 155 | 0.3 | 632 | 1.1 |
| ski | 60 | 305 | -55 | -0.18 | 60.0 | 50.0 | 173 | 0.5 | 513 | 1.5 |
| recruiter | 60 | 880 | -13 | -0.01 | 53.3 | 33.3 | 339 | 0.5 | 1,133 | 1.5 |
| tech | 60 | 1,946 | -393 | -0.20 | 66.7 | 55.0 | 1,033 | 0.7 | 3,085 | 2.1 |

By gamma, pooled over the misspecified levels (uncapped):

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 120 | 47 | -39 | -0.82 | 50.0 | 15.8 | 85 | 0.1 | 735 | 0.5 |
| 2.00 | 120 | 533 | -80 | -0.15 | 55.0 | 37.5 | 311 | 0.3 | 2,518 | 1.7 |
| 4.00 | 120 | 1,061 | -45 | -0.04 | 60.0 | 38.3 | 420 | 0.5 | 2,948 | 2.0 |
| 8.00 | 120 | 1,447 | 33 | 0.02 | 52.5 | 40.0 | 505 | 0.6 | 3,085 | 2.1 |

Share hurt (%) by occupation × gamma (uncapped, misspecified levels):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 60 | 60 | 47 | 40 |
| contractor | 80 | 47 | 40 | 33 |
| realtor | 53 | 60 | 60 | 60 |
| recruiter | 60 | 60 | 53 | 40 |
| retiree | 0.00 | 33 | 87 | 67 |
| rideshare | 0.00 | 60 | 73 | 60 |
| ski | 60 | 60 | 60 | 60 |
| tech | 87 | 60 | 60 | 60 |

### A3. Miscalibrated beliefs

**No view.** Market noise alone (sd 0.3 logit, unbiased) hurts 22% of no-view personas. On average they still get the promised gain (realized/model 1.01). That is the irreducible cost of a noisy price.

**With a view.** Confidence above what the user's information justifies is catastrophic:

- **Average information at confidence 0.6:** realized/model is 0.02, and 34% are hurt.
- **Average information at confidence 0.9:** realized/model is −0.28, 45% are hurt, and harm when hurt is $2,210 (3.3% of income).
- **Poor information at confidence 0.9:** realized/model is −0.54, 62% are hurt, harm when hurt is $5,569 (8.5% of income), and the worst case is 107% of income.
- **Habitual pessimists (+0.4 logit bias):** every confidence row is worse.
- **Sharp users at confidence 0.3** (about calibrated) are the only view-holders who gain more than promised (1.23×).

**Why.** The damage comes from the speculative tilt, which can run up to the solvency bound. Selling the protection is one form of it. The harm is largest at gamma 0.5 (54% hurt, 7.2% of income when hurt) and smallest at gamma 8 (20%, 0.8%). In the uncapped baseline the model promises a gain of $1–7k to exactly these users.

By level (uncapped; the last two columns are with the liquidity cap):

| level | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc | hurt % (capped) | harm $ (capped, if hurt) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sharp (sd 0.3), conf 0.3 | 2,880 | 338 | 416 | 1.23 | 17.9 | 10.3 | 163 | 0.2 | 2,715 | 2.7 | 13.2 | 26 |
| sharp (sd 0.3), conf 0.6 | 2,880 | 587 | 514 | 0.88 | 19.6 | 12.9 | 343 | 0.5 | 7,404 | 12.9 | 13.3 | 41 |
| sharp (sd 0.3), conf 0.9 | 2,880 | 929 | 354 | 0.38 | 28.0 | 21.2 | 696 | 1.1 | 13,576 | 20.7 | 16.4 | 48 |
| no view | 2,880 | 277 | 279 | 1.01 | 22.2 | 14.3 | 175 | 0.3 | 1,796 | 2.4 | 17.5 | 31 |
| average (sd 0.6), conf 0.3 | 2,880 | 472 | 344 | 0.73 | 24.0 | 17.0 | 486 | 0.8 | 8,106 | 8.7 | 17.5 | 48 |
| average (sd 0.6), conf 0.6 | 2,880 | 1,037 | 22 | 0.02 | 34.3 | 29.3 | 1,256 | 1.8 | 20,529 | 31.8 | 23.5 | 75 |
| average (sd 0.6), conf 0.9 | 2,880 | 1,997 | -560 | -0.28 | 44.9 | 40.5 | 2,210 | 3.3 | 45,807 | 65.4 | 28.0 | 77 |
| poor (sd 1.2), conf 0.3 | 2,880 | 811 | -85 | -0.10 | 35.4 | 29.8 | 1,421 | 2.2 | 31,632 | 41.5 | 23.3 | 75 |
| poor (sd 1.2), conf 0.6 | 2,880 | 2,420 | -1,137 | -0.47 | 50.9 | 46.7 | 2,914 | 4.4 | 44,801 | 63.1 | 31.4 | 102 |
| poor (sd 1.2), conf 0.9 | 2,880 | 5,912 | -3,201 | -0.54 | 62.4 | 59.7 | 5,569 | 8.5 | 94,073 | 106.6 | 38.0 | 117 |
| sharp (sd 0.3), conf 0.3, bias +0.4 | 2,880 | 562 | 421 | 0.75 | 32.1 | 25.3 | 366 | 0.6 | 7,542 | 6.0 | 20.7 | 48 |
| sharp (sd 0.3), conf 0.6, bias +0.4 | 2,880 | 1,248 | 169 | 0.14 | 38.5 | 33.0 | 956 | 1.4 | 22,759 | 19.5 | 22.3 | 70 |
| sharp (sd 0.3), conf 0.9, bias +0.4 | 2,880 | 2,239 | -378 | -0.17 | 46.8 | 41.6 | 1,726 | 2.7 | 30,562 | 48.7 | 22.1 | 76 |
| no view, bias +0.4 | 2,880 | 277 | 293 | 1.06 | 22.9 | 15.8 | 188 | 0.3 | 1,858 | 3.3 | 18.0 | 34 |
| average (sd 0.6), conf 0.3, bias +0.4 | 2,880 | 684 | 250 | 0.36 | 31.7 | 26.0 | 704 | 1.1 | 13,202 | 17.6 | 20.8 | 57 |
| average (sd 0.6), conf 0.6, bias +0.4 | 2,880 | 1,839 | -312 | -0.17 | 41.6 | 37.2 | 1,884 | 2.8 | 36,521 | 37.5 | 22.0 | 72 |
| average (sd 0.6), conf 0.9, bias +0.4 | 2,880 | 3,361 | -1,272 | -0.38 | 50.7 | 47.4 | 3,230 | 4.9 | 51,949 | 95.1 | 25.4 | 90 |
| poor (sd 1.2), conf 0.3, bias +0.4 | 2,880 | 1,039 | -77 | -0.07 | 38.6 | 33.0 | 1,395 | 2.1 | 36,328 | 31.3 | 23.6 | 83 |
| poor (sd 1.2), conf 0.6, bias +0.4 | 2,880 | 3,352 | -1,546 | -0.46 | 53.2 | 48.9 | 3,575 | 5.4 | 83,555 | 98.1 | 30.0 | 96 |
| poor (sd 1.2), conf 0.9, bias +0.4 | 2,880 | 7,335 | -3,600 | -0.49 | 65.2 | 62.2 | 5,907 | 9.0 | 120,379 | 99.5 | 34.3 | 120 |

By occupation, pooled over the misspecified levels (uncapped):

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 6,840 | 1,164 | -578 | -0.50 | 47.0 | 41.2 | 1,664 | 3.7 | 35,960 | 79.9 |
| retiree | 6,840 | 1,116 | -629 | -0.56 | 51.7 | 43.7 | 1,476 | 3.7 | 42,628 | 106.6 |
| contractor | 6,840 | 2,336 | -179 | -0.08 | 28.3 | 23.3 | 2,450 | 3.5 | 68,678 | 98.1 |
| realtor | 6,840 | 2,488 | -177 | -0.07 | 30.7 | 28.1 | 3,208 | 4.0 | 55,938 | 69.9 |
| ad_freelancer | 6,840 | 2,073 | -500 | -0.24 | 37.7 | 32.2 | 2,252 | 3.8 | 59,862 | 99.8 |
| ski | 6,840 | 1,139 | -114 | -0.10 | 30.8 | 28.9 | 1,603 | 4.6 | 32,945 | 94.1 |
| recruiter | 6,840 | 2,463 | -381 | -0.15 | 34.0 | 31.0 | 2,979 | 4.0 | 74,637 | 99.5 |
| tech | 6,840 | 2,564 | -1,395 | -0.54 | 50.7 | 40.0 | 3,577 | 2.4 | 120,379 | 80.3 |

By gamma, pooled over the misspecified levels (uncapped):

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 13,680 | 4,280 | -2,020 | -0.47 | 53.9 | 50.4 | 4,675 | 7.2 | 120,379 | 106.6 |
| 2.00 | 13,680 | 1,424 | -504 | -0.35 | 48.1 | 41.6 | 1,612 | 2.4 | 58,622 | 69.0 |
| 4.00 | 13,680 | 1,052 | 95 | 0.09 | 34.0 | 28.3 | 890 | 1.3 | 36,124 | 31.8 |
| 8.00 | 13,680 | 915 | 452 | 0.49 | 19.5 | 14.0 | 503 | 0.8 | 12,257 | 14.2 |

Share hurt (%) by occupation × gamma (uncapped, misspecified levels):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 56 | 49 | 34 | 11 |
| contractor | 55 | 41 | 15 | 1.64 |
| realtor | 54 | 43 | 22 | 5.03 |
| recruiter | 56 | 47 | 26 | 6.90 |
| retiree | 53 | 56 | 54 | 45 |
| rideshare | 52 | 55 | 48 | 33 |
| ski | 54 | 41 | 23 | 5.15 |
| tech | 51 | 53 | 50 | 49 |

### A4. Market price is the true probability

The harm is linear in the bias. Each cent the price overstates the truth costs about $52 of the $277 mean gain, and 5¢ leaves about $15. A favourite-longshot curve with β = 1.3 removes 66% of the value. It hits the cheap contracts hardest: contractor at 10¢ (43% hurt) and the ad freelancer at 18¢ (39%). Rideshare and ski are priced near 50¢ and are barely affected. Low gamma is hurt most: gamma 2 is 51% hurt, gamma 8 only 10%, because high gamma values the insurance enough to absorb the overpricing. A price that *understates* the truth by 3¢ just makes the hedge better (1.54× the promise).

By level (uncapped; the last two columns are with the liquidity cap):

| level | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc | hurt % (capped) | harm $ (capped, if hurt) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| price 1c over true | 96 | 277 | 226 | 0.82 | 18.8 | 0.0 | 15 | 0.0 | 41 | 0.1 | 14.6 | 2.92 |
| price 2c over true | 96 | 277 | 174 | 0.63 | 33.3 | 6.2 | 38 | 0.1 | 130 | 0.2 | 24.0 | 7.83 |
| price 3c over true | 96 | 277 | 122 | 0.44 | 40.6 | 17.7 | 76 | 0.1 | 221 | 0.3 | 30.2 | 13 |
| price 5c over true | 96 | 277 | 15 | 0.05 | 58.3 | 39.6 | 147 | 0.2 | 479 | 0.7 | 43.8 | 25 |
| price 3c under true | 96 | 277 | 426 | 1.54 | 0.0 | 0.0 | 0.00 | 0.0 | 0.00 | 0.0 | 0.0 | 0.00 |
| FLB beta=1.15 | 96 | 277 | 181 | 0.65 | 25.0 | 11.5 | 66 | 0.1 | 185 | 0.3 | 19.8 | 7.81 |
| FLB beta=1.30 | 96 | 277 | 95 | 0.34 | 34.4 | 22.9 | 168 | 0.3 | 420 | 0.6 | 26.0 | 19 |

By occupation, pooled over the misspecified levels (uncapped):

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 84 | 70 | 46 | 0.65 | 23.8 | 6.0 | 34 | 0.1 | 85 | 0.2 |
| retiree | 84 | 18 | 0.74 | 0.04 | 42.9 | 3.6 | 21 | 0.1 | 52 | 0.1 |
| contractor | 84 | 443 | 211 | 0.48 | 42.9 | 34.5 | 192 | 0.3 | 479 | 0.7 |
| realtor | 84 | 628 | 487 | 0.78 | 21.4 | 11.9 | 111 | 0.1 | 346 | 0.4 |
| ad_freelancer | 84 | 228 | 97 | 0.42 | 39.3 | 26.2 | 116 | 0.2 | 285 | 0.5 |
| ski | 84 | 305 | 258 | 0.85 | 14.3 | 9.5 | 60 | 0.2 | 150 | 0.4 |
| recruiter | 84 | 470 | 294 | 0.63 | 29.8 | 16.7 | 134 | 0.2 | 338 | 0.5 |
| tech | 84 | 51 | 22 | 0.44 | 26.2 | 3.6 | 74 | 0.0 | 195 | 0.1 |

By gamma, pooled over the misspecified levels (uncapped):

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 168 | 5.08 | -17 | -3.41 | 29.8 | 13.7 | 79 | 0.1 | 309 | 0.4 |
| 2.00 | 168 | 153 | 33 | 0.21 | 51.2 | 26.8 | 118 | 0.2 | 479 | 0.7 |
| 4.00 | 168 | 374 | 230 | 0.62 | 29.2 | 11.9 | 97 | 0.1 | 475 | 0.7 |
| 8.00 | 168 | 574 | 462 | 0.80 | 10.1 | 3.6 | 57 | 0.1 | 160 | 0.3 |

Share hurt (%) by occupation × gamma (uncapped, misspecified levels):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 29 | 76 | 43 | 9.52 |
| contractor | 57 | 71 | 33 | 9.52 |
| realtor | 57 | 24 | 4.76 | 0.00 |
| recruiter | 57 | 52 | 9.52 | 0.00 |
| retiree | 0.00 | 57 | 76 | 38 |
| rideshare | 0.00 | 62 | 29 | 4.76 |
| ski | 38 | 14 | 4.76 | 0.00 |
| tech | 0.00 | 52 | 33 | 19 |

### A5. Contract settles on the same period as the loss

Modelled as effective basis = default × overlap. A 75% overlap keeps 45% of the promised value and hurts 16%. At 50% overlap the hedge is worth −7% of the promise and hurts 72%. At 25% it is worth −58% of the promise and hurts 83%, by up to 1.2% of income. The realtor and ski segments, with large losses and a moderate basis, take the largest harms.

By level (uncapped; the last two columns are with the liquidity cap):

| level | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc | hurt % (capped) | harm $ (capped, if hurt) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| overlap 100% | 96 | 277 | 277 | 1.00 | 0.0 | 0.0 | 0.00 | 0.0 | 0.00 | 0.0 | 0.0 | 0.00 |
| overlap 75% | 96 | 277 | 126 | 0.45 | 15.6 | 0.0 | 3.45 | 0.0 | 11 | 0.0 | 7.3 | 1.11 |
| overlap 50% | 96 | 277 | -20 | -0.07 | 71.9 | 18.8 | 42 | 0.1 | 122 | 0.3 | 28.1 | 9.55 |
| overlap 25% | 96 | 277 | -161 | -0.58 | 83.3 | 55.2 | 194 | 0.3 | 718 | 1.2 | 39.6 | 24 |

By occupation, pooled over the misspecified levels (uncapped):

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 36 | 70 | -18 | -0.26 | 52.8 | 16.7 | 50 | 0.1 | 186 | 0.4 |
| retiree | 36 | 18 | -6.07 | -0.33 | 52.8 | 5.6 | 16 | 0.0 | 58 | 0.1 |
| contractor | 36 | 443 | 60 | 0.14 | 50.0 | 22.2 | 87 | 0.1 | 227 | 0.3 |
| realtor | 36 | 628 | -86 | -0.14 | 66.7 | 52.8 | 260 | 0.3 | 718 | 0.9 |
| ad_freelancer | 36 | 228 | 3.78 | 0.02 | 50.0 | 22.2 | 76 | 0.1 | 245 | 0.4 |
| ski | 36 | 305 | -56 | -0.18 | 66.7 | 52.8 | 144 | 0.4 | 413 | 1.2 |
| recruiter | 36 | 470 | -21 | -0.04 | 61.1 | 25.0 | 155 | 0.2 | 503 | 0.7 |
| tech | 36 | 51 | -27 | -0.53 | 55.6 | 0.0 | 56 | 0.0 | 122 | 0.1 |

By gamma, pooled over the misspecified levels (uncapped):

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 72 | 5.08 | -8.33 | -1.64 | 37.5 | 2.8 | 22 | 0.0 | 116 | 0.2 |
| 2.00 | 72 | 153 | -36 | -0.23 | 69.4 | 27.8 | 80 | 0.1 | 499 | 0.7 |
| 4.00 | 72 | 374 | -28 | -0.08 | 63.9 | 31.9 | 138 | 0.2 | 718 | 1.1 |
| 8.00 | 72 | 574 | -2.24 | -0.00 | 56.9 | 36.1 | 182 | 0.3 | 711 | 1.2 |

Share hurt (%) by occupation × gamma (uncapped, misspecified levels):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 33 | 67 | 56 | 44 |
| contractor | 67 | 56 | 44 | 33 |
| realtor | 67 | 67 | 67 | 67 |
| recruiter | 67 | 67 | 67 | 44 |
| retiree | 0.00 | 67 | 78 | 67 |
| rideshare | 0.00 | 78 | 67 | 67 |
| ski | 67 | 67 | 67 | 67 |
| tech | 0.00 | 89 | 67 | 67 |

### A6. Fills at the quoted price

The pattern is almost identical to A4. Each cent of slippage costs about $54 of the $277 mean, and 5¢ leaves $7 (57% hurt). Tech, at a 52¢ price with basis 0.15, and retiree are hurt most often, because their promised gains are tiny. Gamma 2 is hurt most (66%) and gamma 8 least (14%).

By level (uncapped; the last two columns are with the liquidity cap):

| level | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc | hurt % (capped) | harm $ (capped, if hurt) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fill 0c worse | 96 | 277 | 277 | 1.00 | 0.0 | 0.0 | 0.00 | 0.0 | 0.00 | 0.0 | 0.0 | 0.00 |
| fill 1c worse | 96 | 277 | 222 | 0.80 | 18.8 | 0.0 | 15 | 0.0 | 40 | 0.1 | 13.5 | 3.10 |
| fill 2c worse | 96 | 277 | 168 | 0.61 | 35.4 | 4.2 | 34 | 0.1 | 121 | 0.2 | 24.0 | 7.59 |
| fill 3c worse | 96 | 277 | 115 | 0.41 | 42.7 | 17.7 | 69 | 0.1 | 208 | 0.3 | 29.2 | 13 |
| fill 5c worse | 96 | 277 | 6.89 | 0.02 | 57.3 | 38.5 | 137 | 0.2 | 411 | 0.6 | 42.7 | 23 |

By occupation, pooled over the misspecified levels (uncapped):

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 48 | 70 | 17 | 0.25 | 37.5 | 10.4 | 37 | 0.1 | 85 | 0.2 |
| retiree | 48 | 18 | -4.86 | -0.27 | 47.9 | 6.2 | 20 | 0.1 | 50 | 0.1 |
| contractor | 48 | 443 | 165 | 0.37 | 43.8 | 29.2 | 152 | 0.2 | 411 | 0.6 |
| realtor | 48 | 628 | 361 | 0.58 | 27.1 | 16.7 | 130 | 0.2 | 344 | 0.4 |
| ad_freelancer | 48 | 228 | 85 | 0.37 | 41.7 | 18.8 | 77 | 0.1 | 219 | 0.4 |
| ski | 48 | 305 | 182 | 0.60 | 27.1 | 16.7 | 57 | 0.2 | 151 | 0.4 |
| recruiter | 48 | 470 | 250 | 0.53 | 31.2 | 14.6 | 109 | 0.1 | 301 | 0.4 |
| tech | 48 | 51 | -32 | -0.63 | 52.1 | 8.3 | 74 | 0.0 | 203 | 0.1 |

By gamma, pooled over the misspecified levels (uncapped):

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 96 | 5.08 | -29 | -5.64 | 37.5 | 16.7 | 76 | 0.1 | 307 | 0.4 |
| 2.00 | 96 | 153 | -18 | -0.12 | 65.6 | 28.1 | 94 | 0.1 | 411 | 0.6 |
| 4.00 | 96 | 374 | 170 | 0.46 | 37.5 | 13.5 | 71 | 0.1 | 388 | 0.6 |
| 8.00 | 96 | 574 | 389 | 0.68 | 13.5 | 2.1 | 42 | 0.1 | 147 | 0.1 |

Share hurt (%) by occupation × gamma (uncapped, misspecified levels):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 33 | 83 | 42 | 8.33 |
| contractor | 67 | 75 | 33 | 0.00 |
| realtor | 67 | 33 | 8.33 | 0.00 |
| recruiter | 67 | 50 | 8.33 | 0.00 |
| retiree | 0.00 | 67 | 83 | 42 |
| rideshare | 0.00 | 92 | 50 | 8.33 |
| ski | 67 | 33 | 8.33 | 0.00 |
| tech | 0.00 | 92 | 67 | 50 |

### Joint world, mild

Every assumption is somewhat wrong at once (ranges in the Method section).

Overall:

| liquidity | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| capped | 2,880 | 47 | 2.37 | 0.05 | 31.7 | 7.9 | 47 | 0.1 | 734 | 1.8 |
| uncapped | 2,880 | 646 | -290 | -0.45 | 47.7 | 36.0 | 884 | 1.3 | 40,241 | 31.1 |

Uncapped, by occupation:

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 360 | 389 | -287 | -0.74 | 51.1 | 38.3 | 628 | 1.4 | 12,700 | 28.2 |
| retiree | 360 | 220 | -284 | -1.29 | 53.6 | 37.5 | 557 | 1.4 | 11,173 | 27.9 |
| contractor | 360 | 666 | -146 | -0.22 | 46.1 | 32.8 | 671 | 1.0 | 21,764 | 31.1 |
| realtor | 360 | 957 | -134 | -0.14 | 44.4 | 38.6 | 1,032 | 1.3 | 18,104 | 22.6 |
| ad_freelancer | 360 | 393 | -155 | -0.39 | 48.3 | 35.6 | 501 | 0.8 | 10,266 | 17.1 |
| ski | 360 | 454 | -29 | -0.06 | 42.2 | 36.9 | 450 | 1.3 | 6,935 | 19.8 |
| recruiter | 360 | 1,014 | -277 | -0.27 | 46.9 | 36.4 | 1,017 | 1.4 | 19,311 | 25.7 |
| tech | 360 | 1,079 | -1,007 | -0.93 | 48.9 | 31.9 | 2,202 | 1.5 | 40,241 | 26.8 |

Capped (liquidity cap on), by occupation:

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 360 | 135 | -2.44 | -0.02 | 43.1 | 29.7 | 109 | 0.2 | 458 | 1.0 |
| retiree | 360 | 110 | -45 | -0.41 | 50.3 | 33.6 | 127 | 0.3 | 734 | 1.8 |
| contractor | 360 | 101 | 53 | 0.52 | 30.6 | 0.0 | 21 | 0.0 | 64 | 0.1 |
| realtor | 360 | 9.18 | 5.13 | 0.56 | 18.1 | 0.0 | 2.63 | 0.0 | 11 | 0.0 |
| ad_freelancer | 360 | 12 | 5.33 | 0.43 | 30.6 | 0.0 | 5.00 | 0.0 | 15 | 0.0 |
| ski | 360 | 1.69 | 0.97 | 0.57 | 21.7 | 0.0 | 0.53 | 0.0 | 1.66 | 0.0 |
| recruiter | 360 | 4.55 | 2.23 | 0.49 | 27.5 | 0.0 | 1.42 | 0.0 | 5.61 | 0.0 |
| tech | 360 | 0.04 | 0.00 | 0.11 | 31.9 | 0.0 | 0.05 | 0.0 | 0.13 | 0.0 |

Uncapped, by gamma:

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 720 | 1,008 | -1,010 | -1.00 | 47.4 | 38.1 | 2,237 | 3.1 | 40,241 | 31.1 |
| 2.00 | 720 | 481 | -296 | -0.62 | 56.5 | 41.9 | 656 | 0.9 | 27,755 | 18.5 |
| 4.00 | 720 | 485 | -27 | -0.05 | 49.9 | 37.5 | 347 | 0.5 | 9,694 | 6.5 |
| 8.00 | 720 | 612 | 173 | 0.28 | 37.1 | 26.5 | 226 | 0.4 | 2,090 | 4.6 |

Uncapped, by savings:

| savings_months | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.00 | 960 | 650 | -138 | -0.21 | 46.2 | 34.2 | 659 | 1.0 | 21,764 | 31.1 |
| 3.00 | 960 | 593 | -254 | -0.43 | 47.6 | 34.4 | 806 | 1.2 | 40,241 | 28.2 |
| 12 | 960 | 697 | -478 | -0.69 | 49.3 | 39.5 | 1,170 | 1.6 | 31,666 | 27.9 |

Share hurt (%), occupation × gamma (uncapped):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 44 | 63 | 53 | 32 |
| contractor | 59 | 66 | 44 | 16 |
| realtor | 56 | 49 | 37 | 37 |
| recruiter | 52 | 62 | 52 | 21 |
| retiree | 36 | 48 | 70 | 61 |
| rideshare | 40 | 61 | 57 | 47 |
| ski | 52 | 48 | 33 | 36 |
| tech | 40 | 56 | 52 | 48 |

View vs no view (uncapped):

| view | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| no view | 1,461 | 281 | 52 | 0.18 | 43.4 | 28.6 | 185 | 0.3 | 1,303 | 2.2 |
| view | 1,419 | 1,023 | -642 | -0.63 | 52.1 | 43.6 | 1,483 | 2.1 | 40,241 | 31.1 |

### Joint world, severe

Every assumption is wrong at once, over the full ranges.

Overall:

| liquidity | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| capped | 2,880 | 44 | -13 | -0.30 | 44.8 | 10.4 | 50 | 0.1 | 680 | 1.7 |
| uncapped | 2,880 | 577 | -428 | -0.74 | 62.6 | 52.6 | 821 | 1.2 | 54,682 | 91.1 |

Uncapped, by occupation:

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 360 | 250 | -213 | -0.85 | 57.2 | 46.1 | 434 | 1.0 | 11,337 | 25.2 |
| retiree | 360 | 222 | -233 | -1.05 | 64.2 | 45.8 | 398 | 1.0 | 8,537 | 21.3 |
| contractor | 360 | 527 | -270 | -0.51 | 68.3 | 61.9 | 528 | 0.8 | 8,938 | 12.8 |
| realtor | 360 | 1,012 | -598 | -0.59 | 61.4 | 57.5 | 1,328 | 1.7 | 15,069 | 18.8 |
| ad_freelancer | 360 | 687 | -584 | -0.85 | 70.0 | 61.4 | 879 | 1.5 | 54,682 | 91.1 |
| ski | 360 | 484 | -260 | -0.54 | 61.9 | 57.2 | 595 | 1.7 | 5,975 | 17.1 |
| recruiter | 360 | 772 | -506 | -0.66 | 68.1 | 60.0 | 893 | 1.2 | 12,666 | 16.9 |
| tech | 360 | 665 | -760 | -1.14 | 50.0 | 31.1 | 1,685 | 1.1 | 26,327 | 17.6 |

Capped (liquidity cap on), by occupation:

| occupation | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 360 | 125 | -59 | -0.47 | 54.7 | 39.7 | 143 | 0.3 | 449 | 1.0 |
| retiree | 360 | 104 | -71 | -0.69 | 59.7 | 41.4 | 134 | 0.3 | 680 | 1.7 |
| contractor | 360 | 97 | 20 | 0.21 | 49.2 | 1.9 | 34 | 0.0 | 90 | 0.1 |
| realtor | 360 | 9.52 | 3.48 | 0.37 | 35.3 | 0.0 | 3.03 | 0.0 | 11 | 0.0 |
| ad_freelancer | 360 | 12 | 0.33 | 0.03 | 47.5 | 0.0 | 6.74 | 0.0 | 19 | 0.0 |
| ski | 360 | 1.64 | 0.58 | 0.35 | 31.4 | 0.0 | 0.62 | 0.0 | 2.06 | 0.0 |
| recruiter | 360 | 4.43 | 0.87 | 0.20 | 41.7 | 0.0 | 1.75 | 0.0 | 5.64 | 0.0 |
| tech | 360 | 0.05 | -0.00 | -0.05 | 38.6 | 0.0 | 0.05 | 0.0 | 0.16 | 0.0 |

Uncapped, by gamma:

| gamma | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 720 | 811 | -984 | -1.21 | 47.9 | 41.0 | 2,149 | 3.1 | 54,682 | 91.1 |
| 2.00 | 720 | 424 | -442 | -1.04 | 72.1 | 60.8 | 666 | 1.0 | 26,327 | 17.6 |
| 4.00 | 720 | 480 | -252 | -0.53 | 68.1 | 58.6 | 499 | 0.8 | 8,879 | 8.0 |
| 8.00 | 720 | 594 | -33 | -0.06 | 62.5 | 50.1 | 332 | 0.6 | 2,014 | 4.0 |

Uncapped, by savings:

| savings_months | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.00 | 960 | 619 | -316 | -0.51 | 62.9 | 52.6 | 689 | 1.1 | 19,436 | 32.4 |
| 3.00 | 960 | 538 | -381 | -0.71 | 64.8 | 53.8 | 708 | 1.0 | 24,729 | 25.2 |
| 12 | 960 | 574 | -587 | -1.02 | 60.2 | 51.6 | 1,081 | 1.6 | 54,682 | 91.1 |

Share hurt (%), occupation × gamma (uncapped):

| occupation | gamma 0.5 | gamma 2 | gamma 4 | gamma 8 |
|---|---|---|---|---|
| ad_freelancer | 48 | 86 | 81 | 66 |
| contractor | 57 | 87 | 80 | 50 |
| realtor | 63 | 74 | 58 | 50 |
| recruiter | 54 | 80 | 69 | 69 |
| retiree | 38 | 61 | 78 | 80 |
| rideshare | 28 | 62 | 70 | 69 |
| ski | 56 | 72 | 58 | 62 |
| tech | 40 | 54 | 51 | 54 |

View vs no view (uncapped):

| view | n | model CE gain $ | realized CE gain $ | realized/model | hurt % | hurt >0.1% inc % | harm $ (if hurt) | harm % inc (if hurt) | worst $ | worst % inc |
|---|---|---|---|---|---|---|---|---|---|---|
| no view | 1,453 | 278 | -117 | -0.42 | 59.1 | 48.1 | 329 | 0.5 | 2,111 | 3.0 |
| view | 1,427 | 882 | -744 | -0.84 | 66.3 | 57.3 | 1,267 | 1.9 | 54,682 | 91.1 |

## Worst-affected segments

1. **View-holders at low gamma.** These segments do by far the most damage. Under A3, users who state a view at gamma 0.5 are hurt 54% of the time, by 7.2% of income when hurt. The worst single cases, across all gammas, are 107% of income (retiree), 100% (ad freelancer), 99.5% (recruiter) and 98% (contractor). In the severe joint world, users with a view lose 1.9% of income when hurt, against 0.5% for users without one, and the worst case is 91%. The cause is the unbounded speculative tilt, together with HEAD's `allow_selling=True` default.
2. **Large loss with a moderate or weak basis** (tech, realtor, ski, recruiter). Without a view, these take the largest harms: up to 1.5–2.1% of income. The tech worker under an overstated basis is the worst case. Realtor and ski are hit hardest under A1 (q_loss ≥ 2 q_event) and A5 (partial overlap).
3. **High basis but tiny promised gain** (rideshare, retiree). These are hurt most *often*: retiree at gamma 4 in 82% of stresses, rideshare at gamma 2 in 76%. The model promises them only $13–14, so any error flips the sign. The harm is small (at most $85, 0.2% of income).
4. **By gamma.** Gamma 2 is hurt most often (72% in the severe joint world). Gamma 0.5 takes the largest harms (3.1% of income when hurt). Gamma 8 is the most robust, because it values the insurance enough to absorb a few cents of mispricing.
5. **Twelve months of savings.** These personas take the largest dollar harms: $1,081 when hurt in the severe joint world, against $689 with no savings. More wealth lets the optimizer take larger speculative positions.
6. **With the liquidity cap on**, thin markets are protected almost entirely: realtor, ad freelancer, ski, recruiter and tech all lose under $20. The deep markets (rideshare, retiree) remain exposed: 55–60% hurt, about $140 (0.3% of income) when hurt, worst case 1.7%.


Worst occupation × gamma under assumptions 1, 2, 4, 5 and 6 (no views, uncapped), ranked by share hurt:

|---|---|---|---|---|---|---|---|---|---|---|---|
| retiree | 4.00 | 72 | 13 | -10 | -0.77 | 81.9 | 6.9 | 16 | 0.0 | 52 | 0.1 |
| rideshare | 2.00 | 72 | 14 | -14 | -1.01 | 76.4 | 9.7 | 24 | 0.1 | 85 | 0.2 |
| tech | 2.00 | 72 | 436 | -104 | -0.24 | 68.1 | 18.1 | 269 | 0.2 | 2,518 | 1.7 |
| ad_freelancer | 2.00 | 72 | 101 | -28 | -0.27 | 59.7 | 37.5 | 102 | 0.2 | 283 | 0.5 |
| rideshare | 4.00 | 72 | 63 | -6.85 | -0.11 | 58.3 | 20.8 | 45 | 0.1 | 142 | 0.3 |
| contractor | 0.50 | 72 | 14 | -30 | -2.05 | 58.3 | 19.4 | 61 | 0.1 | 247 | 0.4 |
| retiree | 2.00 | 72 | 1.34 | -5.14 | -3.84 | 56.9 | 0.0 | 10 | 0.0 | 38 | 0.1 |
| recruiter | 0.50 | 72 | 7.61 | -24 | -3.13 | 56.9 | 11.1 | 47 | 0.1 | 190 | 0.3 |
| realtor | 0.50 | 72 | 28 | -46 | -1.64 | 55.6 | 26.4 | 95 | 0.1 | 309 | 0.4 |
| tech | 4.00 | 72 | 673 | -99 | -0.15 | 54.2 | 16.7 | 434 | 0.3 | 2,948 | 2.0 |
| retiree | 8.00 | 72 | 48 | -0.01 | -0.00 | 54.2 | 11.1 | 26 | 0.1 | 94 | 0.2 |
| ski | 0.50 | 72 | 11 | -18 | -1.75 | 52.8 | 25.0 | 41 | 0.1 | 139 | 0.4 |

Ranked by worst harm as a share of income:

|---|---|---|---|---|---|---|---|---|---|---|---|
| tech | 8.00 | 72 | 624 | -65 | -0.10 | 47.2 | 12.5 | 424 | 0.3 | 3,085 | 2.1 |
| tech | 4.00 | 72 | 673 | -99 | -0.15 | 54.2 | 16.7 | 434 | 0.3 | 2,948 | 2.0 |
| realtor | 4.00 | 72 | 1,022 | 323 | 0.32 | 31.9 | 29.2 | 534 | 0.7 | 1,373 | 1.7 |
| realtor | 8.00 | 72 | 1,232 | 545 | 0.44 | 29.2 | 29.2 | 640 | 0.8 | 1,357 | 1.7 |
| tech | 2.00 | 72 | 436 | -104 | -0.24 | 68.1 | 18.1 | 269 | 0.2 | 2,518 | 1.7 |
| ski | 8.00 | 72 | 563 | 244 | 0.43 | 29.2 | 29.2 | 344 | 1.0 | 580 | 1.7 |
| ski | 4.00 | 72 | 433 | 134 | 0.31 | 31.9 | 29.2 | 263 | 0.8 | 551 | 1.6 |
| recruiter | 8.00 | 72 | 1,196 | 538 | 0.45 | 18.1 | 16.7 | 594 | 0.8 | 1,133 | 1.5 |

## Candidate model changes

Every candidate is a wrapper in `misspecification.py`.

| Candidate | What it does |
|---|---|
| `shrink_basis(λ)` | Sizes with basis × λ. |
| `haircut(h)` | Buys h × n*. |
| `two_prob` | Adds a separate q_loss input and sizes on `joint_states(belief, q_loss, ρ)`. The user supplies q_loss with ±35% error; `oracle` uses the true value. |
| `cap_tilt(τ)` | For hedgers: no selling, and n ∈ [0, (1+τ) ρL]. |
| `view_shrink(k)` | Multiplies the user's stated confidence by k. |
| `min_gain(f)` | Proposes nothing unless the model CE gain ≥ f × wealth. |
| `margin_gate(c)` | Proposes nothing unless the model CE gain ≥ c dollars per contract. |
| `price_buffer(δ)` | Sizes as if the ask were δ higher, keeping the belief at the market price, then buys at the real ask. |
| `robust_maxmin` | Maximizes the worst CE gain over 12 worlds: basis × {0.5, 1}, q_loss/q_event ∈ {0.5, 1, 2}, contract overpriced by {0, 2¢}. |
| Combinations | The names list the parts. |
| `worktree_v2*` | The uncommitted working-tree `hedge_income`, alone and with this study's additions. |


**Value kept when the model is right, and harm under the six single-assumption stresses.** Each stress column is the mean over the six assumptions, weighted equally:

| candidate | right: kept % | right+views: kept % | 1-6 hurt % | 1-6 hurt >0.1% inc % | 1-6 E[harm] $ | 1-6 CE gain $ |
|---|---|---|---|---|---|---|
| baseline | 100.0 | 100.0 | 42.7 | 22.6 | 216 | -19 |
| shrink_basis(0.75) | 92.6 | 98.3 | 30.4 | 14.1 | 172 | 29 |
| shrink_basis(0.5) | 70.7 | 93.3 | 19.1 | 8.1 | 152 | 25 |
| haircut(0.75) | 94.2 | 93.9 | 35.8 | 15.2 | 113 | 94 |
| haircut(0.5) | 76.1 | 75.5 | 30.5 | 8.6 | 51 | 135 |
| two_prob(user q_loss) | 93.1 | 98.2 | 36.8 | 20.0 | 245 | -60 |
| two_prob(oracle) | 100.0 | 100.0 | 36.9 | 20.3 | 226 | -27 |
| two_prob+cap_tilt(0) | 92.9 | 42.1 | 33.1 | 16.2 | 73 | 102 |
| cap_tilt(0.0) | 99.8 | 43.5 | 39.3 | 19.3 | 69 | 117 |
| cap_tilt(0.25) | 100.0 | 48.1 | 39.7 | 19.8 | 73 | 115 |
| min_gain(0.05% of wealth) | 97.6 | 99.8 | 26.3 | 20.0 | 208 | -15 |
| min_gain(0.10% of wealth) | 95.6 | 99.5 | 21.3 | 18.0 | 204 | -13 |
| price_buffer(0.01) | 98.1 | 98.5 | 29.1 | 15.8 | 185 | 14 |
| price_buffer(0.02) | 91.8 | 94.3 | 26.0 | 15.0 | 173 | 27 |
| margin_gate(0.01) | 99.0 | 99.9 | 28.2 | 19.6 | 208 | -14 |
| margin_gate(0.02) | 95.6 | 99.4 | 21.1 | 16.2 | 197 | -8.89 |
| view_shrink(0.5) | 100.0 | 76.5 | 41.0 | 20.8 | 108 | 94 |
| robust_maxmin | 22.9 | 61.1 | 2.8 | 2.0 | 66 | 22 |
| cap_tilt(0.0)+shrink(0.75) | 91.8 | 36.7 | 27.0 | 10.5 | 28 | 157 |
| cap_tilt(0.0)+shrink(0.75)+min_gain(0.05%) | 88.0 | 36.5 | 13.0 | 9.3 | 24 | 156 |
| cap_tilt(0.0)+shrink(0.75)+margin_gate(0.01) | 90.0 | 36.6 | 15.7 | 9.5 | 25 | 158 |
| price_buffer(0.01)+cap_tilt(0) | 98.0 | 43.5 | 25.8 | 12.7 | 50 | 137 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75) | 85.4 | 36.3 | 16.5 | 7.3 | 19 | 160 |
| price_buffer(0.02)+cap_tilt(0)+shrink(0.75) | 77.5 | 35.9 | 12.2 | 5.5 | 14 | 157 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.5) | 59.4 | 26.3 | 9.4 | 2.6 | 5.26 | 134 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) | 82.7 | 36.2 | 11.2 | 7.1 | 18 | 158 |
| two_prob+cap_tilt(0)+shrink(0.75)+margin_gate(0.01) | 83.1 | 36.0 | 13.0 | 7.3 | 25 | 153 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75) | 77.8 | 35.7 | 13.6 | 5.6 | 20 | 155 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) | 74.8 | 35.5 | 9.0 | 5.5 | 19 | 153 |
| worktree_v2 | 97.6 | 50.1 | 23.9 | 17.6 | 68 | 116 |
| worktree_v2+shrink(0.75) | 88.7 | 43.8 | 13.2 | 9.9 | 26 | 158 |
| worktree_v2+shrink(0.75)+price_buffer(0.01) | 80.8 | 41.1 | 9.6 | 6.8 | 18 | 158 |
| worktree_v2+loss_prob(user) | 91.5 | 48.4 | 20.5 | 15.0 | 82 | 89 |
| worktree_v2+shrink(0.75)+price_buffer(0.01)+loss_prob(user) | 72.3 | 40.4 | 8.0 | 5.3 | 20 | 151 |

**Joint world, mild (uncapped):**

| candidate | hurt % | hurt >0.1% inc % | harm $ if hurt | harm % inc if hurt | E[harm] $ | worst % inc | CE gain $ |
|---|---|---|---|---|---|---|---|
| baseline | 47.7 | 36.0 | 884 | 1.3 | 422 | 31.1 | -290 |
| shrink_basis(0.75) | 40.0 | 28.3 | 965 | 1.3 | 386 | 30.3 | -254 |
| shrink_basis(0.5) | 33.9 | 22.4 | 1,102 | 1.5 | 373 | 29.5 | -260 |
| haircut(0.75) | 41.5 | 28.7 | 579 | 0.8 | 241 | 20.7 | -101 |
| haircut(0.5) | 35.6 | 20.3 | 341 | 0.5 | 121 | 12.0 | 8.72 |
| two_prob(user q_loss) | 43.9 | 33.6 | 1,011 | 1.4 | 444 | 65.0 | -323 |
| two_prob(oracle) | 44.4 | 33.2 | 957 | 1.4 | 425 | 50.0 | -300 |
| two_prob+cap_tilt(0) | 31.7 | 21.9 | 206 | 0.3 | 65 | 3.4 | 61 |
| cap_tilt(0.0) | 36.6 | 26.1 | 206 | 0.3 | 75 | 2.6 | 59 |
| cap_tilt(0.25) | 37.5 | 26.8 | 225 | 0.4 | 84 | 3.1 | 49 |
| min_gain(0.05% of wealth) | 35.5 | 30.5 | 1,155 | 1.6 | 410 | 31.1 | -284 |
| min_gain(0.10% of wealth) | 30.9 | 27.2 | 1,287 | 1.8 | 398 | 31.1 | -276 |
| price_buffer(0.01) | 40.9 | 30.6 | 956 | 1.3 | 391 | 28.9 | -260 |
| price_buffer(0.02) | 39.4 | 28.0 | 984 | 1.4 | 388 | 31.3 | -258 |
| margin_gate(0.01) | 36.8 | 30.5 | 1,102 | 1.6 | 405 | 31.1 | -279 |
| margin_gate(0.02) | 29.4 | 24.7 | 1,281 | 1.8 | 376 | 31.1 | -257 |
| view_shrink(0.5) | 44.3 | 31.5 | 340 | 0.5 | 151 | 15.8 | -12 |
| robust_maxmin | 7.9 | 5.8 | 1,148 | 1.6 | 91 | 22.1 | -39 |
| cap_tilt(0.0)+shrink(0.75) | 27.6 | 16.6 | 137 | 0.2 | 38 | 1.8 | 93 |
| cap_tilt(0.0)+shrink(0.75)+min_gain(0.05%) | 17.2 | 12.5 | 171 | 0.3 | 29 | 1.8 | 95 |
| cap_tilt(0.0)+shrink(0.75)+margin_gate(0.01) | 19.7 | 13.5 | 161 | 0.2 | 32 | 1.8 | 96 |
| price_buffer(0.01)+cap_tilt(0) | 28.9 | 19.7 | 188 | 0.3 | 54 | 2.5 | 78 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75) | 20.9 | 10.9 | 124 | 0.2 | 26 | 1.7 | 98 |
| price_buffer(0.02)+cap_tilt(0)+shrink(0.75) | 16.6 | 8.0 | 108 | 0.2 | 18 | 1.7 | 99 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.5) | 14.0 | 5.1 | 75 | 0.1 | 11 | 1.1 | 85 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) | 15.1 | 9.9 | 149 | 0.2 | 23 | 1.7 | 97 |
| two_prob+cap_tilt(0)+shrink(0.75)+margin_gate(0.01) | 17.3 | 11.6 | 163 | 0.2 | 28 | 1.7 | 95 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75) | 18.8 | 9.7 | 124 | 0.2 | 23 | 1.7 | 97 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) | 13.2 | 8.6 | 152 | 0.2 | 20 | 1.7 | 96 |
| worktree_v2 | 28.2 | 23.0 | 290 | 0.5 | 82 | 4.1 | 42 |
| worktree_v2+shrink(0.75) | 18.2 | 14.0 | 205 | 0.3 | 37 | 2.6 | 85 |
| worktree_v2+shrink(0.75)+price_buffer(0.01) | 13.3 | 9.4 | 185 | 0.3 | 25 | 2.4 | 92 |
| worktree_v2+loss_prob(user) | 23.7 | 19.1 | 323 | 0.5 | 76 | 7.8 | 35 |
| worktree_v2+shrink(0.75)+price_buffer(0.01)+loss_prob(user) | 11.8 | 8.2 | 181 | 0.3 | 21 | 3.2 | 89 |

**Joint world, severe (uncapped):**

| candidate | hurt % | hurt >0.1% inc % | harm $ if hurt | harm % inc if hurt | E[harm] $ | worst % inc | CE gain $ |
|---|---|---|---|---|---|---|---|
| baseline | 62.6 | 52.6 | 821 | 1.2 | 514 | 91.1 | -428 |
| shrink_basis(0.75) | 55.1 | 43.4 | 791 | 1.2 | 436 | 89.6 | -351 |
| shrink_basis(0.5) | 47.2 | 33.4 | 828 | 1.2 | 391 | 88.1 | -315 |
| haircut(0.75) | 57.8 | 45.1 | 543 | 0.8 | 314 | 55.2 | -224 |
| haircut(0.5) | 52.0 | 35.0 | 322 | 0.5 | 168 | 28.9 | -86 |
| two_prob(user q_loss) | 56.7 | 45.7 | 907 | 1.3 | 515 | 104.8 | -439 |
| two_prob(oracle) | 57.2 | 45.7 | 898 | 1.3 | 514 | 104.9 | -438 |
| two_prob+cap_tilt(0) | 44.5 | 34.6 | 313 | 0.5 | 139 | 3.3 | -66 |
| cap_tilt(0.0) | 53.6 | 44.0 | 335 | 0.5 | 180 | 4.0 | -102 |
| cap_tilt(0.25) | 54.3 | 45.2 | 366 | 0.6 | 198 | 4.8 | -121 |
| min_gain(0.05% of wealth) | 48.1 | 44.4 | 1,030 | 1.5 | 495 | 91.1 | -414 |
| min_gain(0.10% of wealth) | 42.9 | 40.1 | 1,120 | 1.7 | 481 | 91.1 | -404 |
| price_buffer(0.01) | 55.2 | 45.1 | 824 | 1.2 | 455 | 80.1 | -367 |
| price_buffer(0.02) | 52.4 | 41.0 | 814 | 1.2 | 427 | 71.1 | -337 |
| margin_gate(0.01) | 50.1 | 45.2 | 982 | 1.5 | 492 | 91.1 | -410 |
| margin_gate(0.02) | 40.5 | 37.0 | 1,106 | 1.7 | 447 | 91.1 | -370 |
| view_shrink(0.5) | 60.2 | 49.5 | 443 | 0.7 | 266 | 37.2 | -181 |
| robust_maxmin | 13.8 | 8.5 | 778 | 1.2 | 107 | 73.4 | -75 |
| cap_tilt(0.0)+shrink(0.75) | 44.1 | 32.9 | 225 | 0.4 | 99 | 2.6 | -23 |
| cap_tilt(0.0)+shrink(0.75)+min_gain(0.05%) | 30.4 | 25.9 | 278 | 0.4 | 84 | 2.6 | -13 |
| cap_tilt(0.0)+shrink(0.75)+margin_gate(0.01) | 33.4 | 27.4 | 262 | 0.4 | 87 | 2.6 | -13 |
| price_buffer(0.01)+cap_tilt(0) | 45.1 | 35.7 | 310 | 0.5 | 140 | 3.7 | -63 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75) | 36.2 | 25.9 | 203 | 0.3 | 74 | 2.5 | -1.24 |
| price_buffer(0.02)+cap_tilt(0)+shrink(0.75) | 30.0 | 20.3 | 186 | 0.3 | 56 | 2.5 | 13 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.5) | 26.3 | 15.0 | 119 | 0.2 | 31 | 1.6 | 26 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) | 28.5 | 23.4 | 241 | 0.4 | 69 | 2.5 | 0.86 |
| two_prob+cap_tilt(0)+shrink(0.75)+margin_gate(0.01) | 27.9 | 21.9 | 244 | 0.4 | 68 | 2.5 | 6.96 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75) | 30.0 | 20.7 | 192 | 0.3 | 58 | 2.5 | 16 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) | 23.2 | 18.6 | 230 | 0.3 | 53 | 2.5 | 18 |
| worktree_v2 | 41.9 | 38.3 | 467 | 0.8 | 195 | 6.6 | -124 |
| worktree_v2+shrink(0.75) | 31.7 | 27.7 | 328 | 0.5 | 104 | 5.0 | -34 |
| worktree_v2+shrink(0.75)+price_buffer(0.01) | 25.6 | 21.6 | 290 | 0.5 | 74 | 4.6 | -6.29 |
| worktree_v2+loss_prob(user) | 33.9 | 30.0 | 481 | 0.7 | 163 | 7.7 | -101 |
| worktree_v2+shrink(0.75)+price_buffer(0.01)+loss_prob(user) | 21.1 | 17.2 | 273 | 0.4 | 57 | 4.8 | 8.17 |

**Joint world, severe, with the liquidity cap on:**

| candidate | hurt % | hurt >0.1% inc % | harm $ if hurt | harm % inc if hurt | E[harm] $ | worst % inc | CE gain $ |
|---|---|---|---|---|---|---|---|
| baseline | 44.8 | 10.4 | 50 | 0.1 | 23 | 1.7 | -13 |
| shrink_basis(0.75) | 41.4 | 8.7 | 45 | 0.1 | 18 | 1.6 | -9.15 |
| shrink_basis(0.5) | 37.5 | 6.9 | 42 | 0.1 | 16 | 1.8 | -6.91 |
| haircut(0.75) | 44.1 | 9.3 | 42 | 0.1 | 18 | 1.6 | -9.00 |
| haircut(0.5) | 43.5 | 7.3 | 33 | 0.1 | 14 | 1.6 | -5.07 |
| two_prob(user q_loss) | 39.0 | 7.4 | 44 | 0.1 | 17 | 1.7 | -8.14 |
| two_prob(oracle) | 38.1 | 7.3 | 44 | 0.1 | 17 | 1.6 | -7.56 |
| two_prob+cap_tilt(0) | 30.1 | 4.0 | 25 | 0.1 | 7.43 | 0.8 | 0.30 |
| cap_tilt(0.0) | 37.8 | 7.8 | 39 | 0.1 | 15 | 1.0 | -6.37 |
| cap_tilt(0.25) | 37.8 | 8.0 | 41 | 0.1 | 15 | 1.1 | -6.94 |
| min_gain(0.05% of wealth) | 11.2 | 7.7 | 153 | 0.4 | 17 | 1.7 | -9.62 |
| min_gain(0.10% of wealth) | 8.6 | 6.6 | 175 | 0.4 | 15 | 1.7 | -8.31 |
| price_buffer(0.01) | 39.0 | 9.0 | 49 | 0.1 | 19 | 1.6 | -9.73 |
| price_buffer(0.02) | 37.9 | 7.7 | 46 | 0.1 | 18 | 1.8 | -8.00 |
| margin_gate(0.01) | 36.3 | 9.0 | 56 | 0.1 | 20 | 1.7 | -11 |
| margin_gate(0.02) | 29.3 | 6.9 | 58 | 0.1 | 17 | 1.7 | -8.42 |
| view_shrink(0.5) | 43.3 | 9.8 | 44 | 0.1 | 19 | 1.6 | -9.82 |
| robust_maxmin | 10.8 | 1.9 | 42 | 0.1 | 4.56 | 1.4 | 1.32 |
| cap_tilt(0.0)+shrink(0.75) | 33.0 | 5.7 | 30 | 0.1 | 9.74 | 0.9 | -1.55 |
| cap_tilt(0.0)+shrink(0.75)+min_gain(0.05%) | 6.9 | 3.9 | 90 | 0.2 | 6.21 | 0.9 | 0.35 |
| cap_tilt(0.0)+shrink(0.75)+margin_gate(0.01) | 24.7 | 4.4 | 31 | 0.1 | 7.74 | 0.9 | 0.07 |
| price_buffer(0.01)+cap_tilt(0) | 30.9 | 6.2 | 36 | 0.1 | 11 | 1.0 | -3.11 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75) | 26.2 | 4.1 | 27 | 0.1 | 7.17 | 0.9 | 0.71 |
| price_buffer(0.02)+cap_tilt(0)+shrink(0.75) | 21.5 | 3.4 | 26 | 0.1 | 5.69 | 0.9 | 1.95 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.5) | 20.5 | 2.3 | 19 | 0.0 | 3.87 | 0.6 | 3.38 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) | 6.7 | 3.7 | 83 | 0.2 | 5.60 | 0.9 | 0.94 |
| two_prob+cap_tilt(0)+shrink(0.75)+margin_gate(0.01) | 20.3 | 3.0 | 24 | 0.1 | 4.89 | 0.7 | 2.47 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75) | 21.2 | 2.7 | 21 | 0.0 | 4.51 | 0.7 | 2.84 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) | 4.7 | 2.3 | 66 | 0.1 | 3.09 | 0.7 | 2.82 |
| worktree_v2 | 9.0 | 5.7 | 121 | 0.3 | 11 | 1.7 | -4.19 |
| worktree_v2+shrink(0.75) | 7.0 | 4.2 | 98 | 0.2 | 6.90 | 1.2 | -0.35 |
| worktree_v2+shrink(0.75)+price_buffer(0.01) | 4.8 | 2.9 | 96 | 0.2 | 4.62 | 1.0 | 1.49 |
| worktree_v2+loss_prob(user) | 5.8 | 2.9 | 79 | 0.2 | 4.61 | 1.7 | 1.41 |
| worktree_v2+shrink(0.75)+price_buffer(0.01)+loss_prob(user) | 3.5 | 1.8 | 70 | 0.2 | 2.41 | 1.0 | 3.01 |

**Per assumption** (misspecified levels only, uncapped; share hurt and E[harm] over all personas):

| candidate | A1 hurt % | A1 E[harm] $ | A2 hurt % | A2 E[harm] $ | A3 hurt % | A3 E[harm] $ | A4 hurt % | A4 E[harm] $ | A5 hurt % | A5 E[harm] $ | A6 hurt % | A6 E[harm] $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 36.9 | 58 | 54.4 | 183 | 39.1 | 931 | 30.1 | 30 | 56.9 | 64 | 38.5 | 31 |
| shrink_basis(0.75) | 26.5 | 25 | 37.3 | 66 | 36.9 | 896 | 21.1 | 13 | 35.1 | 23 | 25.5 | 12 |
| shrink_basis(0.5) | 16.9 | 7.49 | 18.3 | 15 | 35.7 | 882 | 11.2 | 3.99 | 20.8 | 3.47 | 11.5 | 2.76 |
| haircut(0.75) | 32.5 | 31 | 44.0 | 80 | 33.7 | 501 | 27.1 | 18 | 44.4 | 27 | 33.1 | 18 |
| haircut(0.5) | 28.7 | 12 | 35.2 | 24 | 28.8 | 241 | 24.3 | 10 | 36.5 | 8.16 | 29.7 | 10 |
| two_prob(user q_loss) | 9.6 | 7.57 | 52.9 | 288 | 40.9 | 1,044 | 27.8 | 28 | 53.8 | 71 | 35.9 | 32 |
| two_prob(oracle) | 0.2 | 0.00 | 54.4 | 183 | 41.3 | 1,050 | 30.1 | 26 | 56.9 | 64 | 38.5 | 31 |
| two_prob+cap_tilt(0) | 9.6 | 7.57 | 52.9 | 252 | 19.8 | 55 | 27.2 | 25 | 53.5 | 70 | 35.4 | 31 |
| cap_tilt(0.0) | 36.9 | 58 | 54.4 | 182 | 20.1 | 55 | 29.9 | 28 | 56.2 | 63 | 38.0 | 30 |
| cap_tilt(0.25) | 36.9 | 58 | 54.4 | 183 | 21.4 | 71 | 30.1 | 30 | 56.9 | 64 | 38.5 | 31 |
| min_gain(0.05% of wealth) | 20.0 | 53 | 39.0 | 179 | 32.9 | 923 | 13.5 | 19 | 35.8 | 59 | 16.4 | 17 |
| min_gain(0.10% of wealth) | 15.2 | 51 | 33.8 | 177 | 30.8 | 917 | 8.8 | 14 | 29.5 | 55 | 9.9 | 11 |
| price_buffer(0.01) | 22.7 | 45 | 39.2 | 143 | 36.6 | 858 | 17.0 | 11 | 38.9 | 44 | 20.1 | 10 |
| price_buffer(0.02) | 25.4 | 42 | 32.7 | 117 | 35.7 | 818 | 12.4 | 7.57 | 31.6 | 36 | 18.5 | 19 |
| margin_gate(0.01) | 24.6 | 55 | 37.1 | 178 | 33.0 | 919 | 15.5 | 19 | 39.2 | 60 | 19.8 | 18 |
| margin_gate(0.02) | 17.5 | 52 | 31.9 | 169 | 28.0 | 887 | 7.9 | 11 | 30.9 | 56 | 10.4 | 9.20 |
| view_shrink(0.5) | 36.9 | 58 | 54.4 | 183 | 29.0 | 281 | 30.1 | 30 | 56.9 | 64 | 38.5 | 31 |
| robust_maxmin | 1.2 | 0.04 | 1.5 | 0.05 | 13.9 | 393 | 0.1 | 0.00 | 0.0 | 0.00 | 0.0 | 0.00 |
| cap_tilt(0.0)+shrink(0.75) | 26.5 | 25 | 37.3 | 65 | 17.1 | 34 | 20.8 | 12 | 35.1 | 22 | 25.5 | 11 |
| cap_tilt(0.0)+shrink(0.75)+min_gain(0.05%) | 13.8 | 23 | 23.3 | 62 | 13.0 | 30 | 5.5 | 5.66 | 17.0 | 19 | 5.2 | 3.88 |
| cap_tilt(0.0)+shrink(0.75)+margin_gate(0.01) | 17.1 | 24 | 25.0 | 62 | 13.6 | 31 | 7.9 | 6.72 | 21.9 | 20 | 8.6 | 5.14 |
| price_buffer(0.01)+cap_tilt(0) | 22.7 | 45 | 39.2 | 143 | 17.5 | 48 | 16.8 | 11 | 38.9 | 43 | 19.8 | 10 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75) | 18.3 | 18 | 24.6 | 47 | 14.7 | 29 | 9.7 | 3.93 | 21.5 | 14 | 9.9 | 2.63 |
| price_buffer(0.02)+cap_tilt(0)+shrink(0.75) | 14.8 | 14 | 20.6 | 35 | 12.5 | 25 | 5.1 | 1.10 | 16.3 | 8.54 | 4.2 | 0.52 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.5) | 11.7 | 4.83 | 12.3 | 8.80 | 11.5 | 16 | 4.2 | 0.72 | 12.8 | 0.73 | 3.6 | 0.29 |
| price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) | 12.1 | 18 | 19.8 | 47 | 12.3 | 28 | 4.3 | 2.78 | 15.6 | 13 | 2.9 | 1.30 |
| two_prob+cap_tilt(0)+shrink(0.75)+margin_gate(0.01) | 3.5 | 2.60 | 24.2 | 84 | 13.5 | 31 | 6.8 | 5.84 | 21.2 | 21 | 8.6 | 5.78 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75) | 2.9 | 1.84 | 24.0 | 68 | 14.4 | 29 | 9.1 | 3.02 | 20.8 | 15 | 10.7 | 3.20 |
| price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) | 1.7 | 1.78 | 19.4 | 68 | 12.0 | 28 | 3.4 | 2.01 | 13.9 | 14 | 3.4 | 1.66 |
| worktree_v2 | 20.0 | 53 | 39.0 | 179 | 19.0 | 78 | 13.5 | 19 | 35.8 | 59 | 16.4 | 17 |
| worktree_v2+shrink(0.75) | 13.8 | 23 | 23.3 | 63 | 14.3 | 42 | 5.8 | 6.28 | 17.0 | 20 | 5.2 | 4.15 |
| worktree_v2+shrink(0.75)+price_buffer(0.01) | 10.4 | 17 | 18.8 | 46 | 11.8 | 32 | 2.2 | 1.35 | 13.5 | 13 | 1.0 | 0.46 |
| worktree_v2+loss_prob(user) | 3.3 | 6.61 | 37.3 | 285 | 19.1 | 95 | 12.9 | 19 | 33.7 | 67 | 16.4 | 20 |
| worktree_v2+shrink(0.75)+price_buffer(0.01)+loss_prob(user) | 1.7 | 1.78 | 18.1 | 68 | 11.9 | 35 | 1.8 | 0.90 | 13.2 | 14 | 1.6 | 0.82 |

**Assumption 3 by level, leading candidates.** Share hurt and mean realized CE gain, uncapped, no systematic bias, subsample:

| level | baseline hurt % | baseline CE $ | cap_tilt(0.0) hurt % | cap_tilt(0.0) CE $ | price_buffer(0.01)+cap_tilt(0)+shrink(0.75) hurt % | price_buffer(0.01)+cap_tilt(0)+shrink(0.75) CE $ | price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) hurt % | price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) CE $ | price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) hurt % | price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) CE $ | robust_maxmin hurt % | robust_maxmin CE $ | worktree_v2 hurt % | worktree_v2 CE $ | worktree_v2+shrink(0.75)+price_buffer(0.01) hurt % | worktree_v2+shrink(0.75)+price_buffer(0.01) CE $ | view_shrink(0.5) hurt % | view_shrink(0.5) CE $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sharp (sd 0.3), conf 0.3 | 22 | 415 | 21 | 329 | 8 | 287 | 5 | 282 | 5 | 260 | 1 | 121 | 12 | 351 | 3 | 284 | 23 | 342 |
| sharp (sd 0.3), conf 0.6 | 19 | 553 | 9 | 368 | 6 | 312 | 2 | 307 | 2 | 291 | 1 | 275 | 7 | 387 | 2 | 317 | 15 | 478 |
| sharp (sd 0.3), conf 0.9 | 25 | 350 | 11 | 327 | 8 | 279 | 5 | 276 | 5 | 264 | 5 | 267 | 9 | 346 | 5 | 294 | 17 | 431 |
| no view | 24 | 279 | 24 | 277 | 11 | 233 | 5 | 228 | 4 | 206 | 0 | 65 | 11 | 275 | 4 | 220 | 24 | 279 |
| average (sd 0.6), conf 0.3 | 22 | 290 | 19 | 298 | 12 | 263 | 8 | 260 | 7 | 242 | 4 | 113 | 13 | 311 | 7 | 267 | 22 | 310 |
| average (sd 0.6), conf 0.6 | 33 | 2 | 13 | 335 | 11 | 281 | 10 | 277 | 10 | 261 | 11 | 149 | 14 | 326 | 9 | 284 | 21 | 347 |
| average (sd 0.6), conf 0.9 | 43 | -513 | 13 | 295 | 10 | 258 | 9 | 254 | 9 | 230 | 12 | 44 | 15 | 281 | 9 | 259 | 29 | 276 |
| poor (sd 1.2), conf 0.3 | 34 | 9 | 17 | 281 | 13 | 248 | 10 | 246 | 10 | 227 | 10 | 85 | 16 | 260 | 9 | 247 | 25 | 261 |
| poor (sd 1.2), conf 0.6 | 56 | -1,219 | 17 | 232 | 12 | 203 | 10 | 203 | 11 | 186 | 18 | -200 | 17 | 179 | 11 | 194 | 36 | 35 |
| poor (sd 1.2), conf 0.9 | 60 | -3,178 | 17 | 204 | 15 | 188 | 14 | 186 | 14 | 172 | 27 | -1,491 | 22 | 152 | 15 | 176 | 40 | -622 |

**Severe joint world by occupation, leading candidates** (share hurt and mean realized CE gain):

| occupation | baseline hurt % | baseline CE $ | cap_tilt(0.0) hurt % | cap_tilt(0.0) CE $ | price_buffer(0.01)+cap_tilt(0)+shrink(0.75) hurt % | price_buffer(0.01)+cap_tilt(0)+shrink(0.75) CE $ | price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) hurt % | price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) CE $ | price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) hurt % | price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) CE $ | robust_maxmin hurt % | robust_maxmin CE $ | worktree_v2 hurt % | worktree_v2 CE $ | worktree_v2+shrink(0.75)+price_buffer(0.01) hurt % | worktree_v2+shrink(0.75)+price_buffer(0.01) CE $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 57 | -213 | 46 | -45 | 31 | -8 | 24 | -6 | 14 | 1 | 9 | -28 | 36 | -57 | 18 | -10 |
| retiree | 64 | -233 | 49 | -32 | 29 | -10 | 15 | -7 | 11 | -4 | 13 | -67 | 26 | -27 | 12 | -6 |
| contractor | 68 | -270 | 62 | -103 | 39 | 27 | 35 | 29 | 29 | 44 | 12 | 23 | 48 | -123 | 27 | 28 |
| realtor | 61 | -598 | 54 | -165 | 39 | 37 | 34 | 44 | 28 | 75 | 16 | -57 | 50 | -220 | 35 | 23 |
| ad_freelancer | 70 | -584 | 63 | -147 | 46 | -42 | 36 | -35 | 32 | -24 | 23 | -243 | 53 | -165 | 29 | -38 |
| ski | 62 | -260 | 57 | -87 | 38 | 15 | 37 | 16 | 26 | 55 | 9 | -30 | 52 | -118 | 37 | 3 |
| recruiter | 68 | -506 | 60 | -195 | 44 | -21 | 38 | -16 | 33 | 6 | 18 | -43 | 53 | -235 | 38 | -35 |
| tech | 50 | -760 | 37 | -38 | 24 | -10 | 10 | -18 | 12 | -11 | 9 | -157 | 17 | -49 | 9 | -16 |

**Mean CE gain when the model is right, by occupation:**

| occupation | baseline | cap_tilt(0.0) | price_buffer(0.01)+cap_tilt(0)+shrink(0.75) | price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%) | price_buffer(0.01)+cap_tilt(0)+two_prob+shrink(0.75)+min_gain(0.05%) | robust_maxmin | worktree_v2 | worktree_v2+shrink(0.75)+price_buffer(0.01) |
|---|---|---|---|---|---|---|---|---|
| rideshare | 70 | 70 | 55 | 53 | 48 | 0 | 66 | 41 |
| retiree | 18 | 18 | 13 | 10 | 10 | 1 | 14 | 6 |
| contractor | 443 | 439 | 390 | 390 | 382 | 212 | 438 | 370 |
| realtor | 628 | 628 | 539 | 528 | 460 | 61 | 626 | 528 |
| ad_freelancer | 228 | 228 | 196 | 188 | 181 | 86 | 226 | 180 |
| ski | 305 | 305 | 259 | 254 | 190 | 0 | 304 | 254 |
| recruiter | 470 | 470 | 410 | 408 | 382 | 146 | 469 | 408 |
| tech | 51 | 51 | 28 | 0 | 0 | 0 | 16 | 0 |

## Trade-off summary

The stacked package, step by step. All columns except "HEAD + cap/shrink/buffer/gate" build on the uncommitted v2. That column applies the same ideas to HEAD as wrappers, so the conclusion does not depend on v2.

| metric (uncapped unless noted) | HEAD | v2 (working tree) | v2 + shrink 0.75 | **v2 + shrink 0.75 + buffer 1¢** | + loss_prob (user, ±35%) | HEAD + cap/shrink/buffer/gate |
|---|---|---|---|---|---|---|
| CE gain kept, model right (no view) | 100% ($277) | 97.6% | 88.7% | **80.8% ($224)** | 72.3% | 82.7% |
| CE gain kept, model right (views right) | 100% | 50.1% | 43.8% | **41.1%** | 40.4% | 36.2% |
| A1–A6: share hurt | 42.7% | 23.9% | 13.2% | **9.6%** | 8.0% | 11.2% |
| A1–A6: E[harm] | $216 | $68 | $26 | **$18** | $20 | $18 |
| Joint mild: share hurt / E[harm] / mean CE gain | 47.7% / $422 / −$290 | 28.2% / $82 / +$42 | 18.2% / $37 / +$85 | **13.3% / $25 / +$92** | 11.8% / $21 / +$89 | 15.1% / $23 / +$97 |
| Joint severe: share hurt / E[harm] / mean CE gain | 62.6% / $514 / −$428 | 41.9% / $195 / −$124 | 31.7% / $104 / −$34 | **25.6% / $74 / −$6** | 21.1% / $57 / +$8 | 28.5% / $69 / +$1 |
| Joint severe: worst harm, % of income | 91.1% | 6.6% | 5.0% | **4.6%** | 4.8% | 2.5% |
| Joint severe, capped: share hurt / E[harm] | 44.8% / $23 | 9.0% / $11 | 7.0% / $6.9 | **4.8% / $4.6** | 3.5% / $2.4 | 6.7% / $5.6 |

The "HEAD + cap/shrink/buffer/gate" column is `price_buffer(0.01)+cap_tilt(0)+shrink(0.75)+min_gain(0.05%)`.

**Rejected candidates and why:**

- **`robust_maxmin`** has the lowest share hurt: 2.8% under A1–A6 and 13.8% in the severe joint world. But it keeps only 22.9% of the value when the model is right, and it gives rideshare, ski and tech nothing at all.
- **Haircuts** are blunt. `haircut(0.5)` keeps 76%, yet 30.5% of personas are still hurt.
- **`view_shrink(0.5)`** leaves poor-information users at confidence 0.9 at −$622. The tilt cap leaves them at +$204.
- **`margin_gate` and `min_gain` alone** cut the share hurt mostly by dropping positions that were harmless anyway. E[harm] barely moves: $216 → $208. So neither works as a robustness device on its own.
- **`shrink_basis(0.5)`** gives up 29–41% of the value.

## Recommendations, ranked

Each item gives the exact change and the evidence for it. Line references are to HEAD's `hone/prediction/hedge.py`. Where v2 already contains a change, the item says so.

### 1. Cap the view-driven tilt and stop hedgers from selling (done in v2; keep it)

Evidence, HEAD → `cap_tilt(0)`:
- A3 expected harm falls from $931 to $55 and the share hurt from 39% to 20%.
- The worst case in the severe joint world falls from **91% to 4.0% of income**.
- The mild joint world goes from −$290 to +$59 mean realized gain.
- It costs 0.2% of the value when there is no view.
- It costs 56% of the speculative value when the view is exactly right: 43.5% kept with τ = 0, and 48.1% with τ = 0.25.

For poor-information users at confidence 0.9, the mean realized gain goes from −$3,178 to +$204.

- **HEAD form:** change `IncomeExposure.allow_selling: bool = True` to `allow_selling: bool | None = None`, where None means selling is allowed only when `loss == 0`. In `_bounds`, change `if exp.allow_selling` to `if (exp.allow_selling if exp.allow_selling is not None else exp.loss == 0)`. Add `MAX_VIEW_TILT = 0.25`. In `hedge_income`, directly after `n_star = optimal_contracts(exp, states)`:
  ```python
  if exp.loss > 0:
      n_star = min(max(n_star, 0.0), (1.0 + MAX_VIEW_TILT) * rho_eff * exp.loss)
  ```
- **v2 form:** this is already implemented (`MAX_VIEW_TILT = 1.0`, `allow_selling: bool | None = None`). v2's tail is 6.6% of income, against 4.0% for `cap_tilt(0)` on HEAD. Lowering `MAX_VIEW_TILT` from 1.0 to **0.25** would likely tighten that tail, at a cost of only about 2 points of view value (48.1% kept at τ = 0.25 vs 50.1% for v2). Only τ ∈ {0, 0.25} on HEAD and 1.0 in v2 were tested.

### 2. Size with a shrunk basis: `BASIS_SHRINK = 0.75` (new)

A basis that is too high is the costliest error when there is no view: A2 and A5 hurt 54–57% of personas.

Evidence on top of v2:
- A1–A6 share hurt falls from 23.9% to 13.2%, and E[harm] from $68 to $26.
- A2 E[harm] falls from $179 to $63, and A5 from $59 to $20.
- Severe joint E[harm] falls from $195 to $104.
- Cost: 8.9 points of model-right value (97.6% → 88.7%).

`0.5` gives up too much: 70.7% kept on HEAD.

Code: add `BASIS_SHRINK = 0.75` beside the other constants.
- **v2:** `states, rho_eff = joint_states(belief, q_loss, BASIS_SHRINK * exp.basis_correlation)`, and the same for `states_mkt`.
- **HEAD (line 379):** `states, rho_eff = joint_states(belief, belief, BASIS_SHRINK * exp.basis_correlation)`.

Report the stated basis next to the basis used. The flag `clipped` should compare against the shrunk value. If Hone later estimates the basis from data, for example `research/prediction/backtest_history.py`, replace the fixed 0.75 with the estimate's lower confidence bound.

### 3. Size at the ask plus 1¢: `PRICE_BUFFER = 0.01` (new)

This protects against price bias, slippage and the favourite-longshot bias, all of which cost in proportion to the position.

Evidence on top of v2 + shrink:
- A4 share hurt falls from 5.8% to 2.2%, and A6 from 5.2% to 1.0%.
- A1–A6 share hurt falls from 13.2% to 9.6%.
- Severe joint E[harm] falls from $104 to $74.
- Cost: 7.9 points of value (88.7% → 80.8%).

2¢ buys little more: 12.2% vs 16.5% hurt on the HEAD combo, for 8 more points of value.

Code: add `PRICE_BUFFER = 0.01`. The buffer applies only to *choosing n*. Belief, market_prob, cost, fee, CE and the states table stay at the real price.
- **HEAD:** `n_star = optimal_contracts(replace(exp, price=min(exp.price + PRICE_BUFFER, 0.99)), states)`.
- **v2:** build the sizing pricers from `replace(exp, price=exp.price + PRICE_BUFFER)`, with every `asks_buy` level shifted by `+PRICE_BUFFER`, for the `_bounds`/`_argmax` calls in steps 1–3. Keep `book_pricer` unshifted for the accounting block and for `_round_solvent`.

### 4. Keep the minimum-worth gate (done in v2: `MIN_WORTH_DOLLARS = 5.0`, `MIN_WORTH_FRAC = 0.0005`)

On its own the gate barely reduces E[harm]: $216 → $208. Its job is to stop advising trades whose gain is a few dollars, which are a coin flip under any misspecification. Combined with items 1–3 on HEAD, the share hurt falls from 16.5% to 11.2% (A1–A6), and with the liquidity cap from 26.2% to **6.7%** (severe joint, capped). It costs 2.7 points of value. Expect "harm if hurt" to *rise* with the gate, because only real positions remain. Judge it on E[harm], not on the share hurt. For HEAD, after `ce_un`/`ce_hd`: `if contracts and ce_hd - ce_un < max(5.0, 0.0005 * exp.wealth): contracts = 0`, with the dependent fields recomputed.

### 5. `loss_prob` as an optional input, asked only when the event clearly differs (done in v2; restrict its use)

With the true value, it removes A1 harm completely: share hurt 36.9% → 0.2%. With the user's own estimate (±35%):
- On top of v2, A1 share hurt falls from 20.0% to 3.3%.
- But A2 E[harm] rises from $179 to $285. An overstated q_loss enlarges the position just when the basis is also too high.
- It costs 6 points of model-right value.

Keep `loss_prob: float | None = None` with None meaning the same event. In the UI, ask for it only when the contract's event is plainly a different event from the person's loss: contractor on U-3, tech on layoffs. Phrase it as a frequency ("in how many of the last 10 years…"), and never pre-fill it from a guess. With items 2 and 3 in place it still pays off overall: severe joint E[harm] falls from $74 to $57 and mean CE gain moves from −$6 to +$8.

### Not recommended
- `robust_maxmin`
- haircuts
- `view_shrink`
- `shrink_basis(0.5)`
- `PRICE_BUFFER = 0.02`

The reasons are in the trade-off summary above.

## Caveats

- The world is one period with four states. The "true worlds" are stylised ranges, not estimates; the occupation figures are the same round numbers as in `segments.py`.
- The fixed share of 50% of users holding views drives the size of the joint-world numbers.
- Under m < 1 in A1, the Fréchet clip makes the loss a subset of the event. That is a favourable case for the hedge, so A1's low side is optimistic.
- The liquidity "capped" columns use HEAD's 10% open-interest cap and a flat book. The working tree has raised the cap to 25%, which makes capped positions larger in deep markets, so the deep-market harms here are a lower bound for v2.
- The v2 numbers are a snapshot of an uncommitted file that was still changing. Re-run with `--model worktree` to stress-test whatever is in the working tree; the `worktree_v2*` rows then compare the working tree with itself plus this study's additions.

