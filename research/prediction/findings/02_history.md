# 02 — The hedge model against settled Kalshi markets

**Script:** `research/prediction/backtest_history.py`. Run `--offline` to reuse the cache. Without the flag it downloads only what is missing, and `--refresh` downloads everything again.
**Data:** `research/prediction/data/kalshi_history/*.json.gz` holds 2,822 settled markets with daily candles, about 0.6 MB. The tables come from these files: `calibration_summary.csv`, `backtest_summary.csv` (one row per model, persona, horizon, variant, gamma and cap) and `backtest_periods.csv.gz` (one row per settled period).
**Models tested:**
- **v1** is `hone/prediction/hedge.py` at commit `5a157de`, the version described in the brief.
- **v2** is the uncommitted working tree as of this run (`worktree@70ca128177`), which another session was still editing. v2 forbids selling for anyone with exposure, adds `loss_prob`, uses a `MIN_WORTH` floor and caps at 25% of open interest. The v2 numbers describe a moving target, so re-run the script to update them.

## Headline

1. **The market price is good enough to use as the probability, but the protective side has been expensive.** Across all series combined, the mid price 7 and 28 days before close is calibrated. The recalibration slope is 1.01 [0.91, 1.15] at 7 days and 1.05 [0.88, 1.24] at 28 days, and the bias is +2.2pp [−1.7, +5.6] and +0.8pp [−3.1, +4.5]. In most series, though, the side a hedger buys lost money at the quoted price. Buying YES on unemployment above X at the ask returned −10c [−17, −5] per contract at 7 days and −16c [−24, −9] at 28 days. CPI returned −7c and −11c, and gas −19c at 7 days. NO on payrolls returned −16c at 28 days. The Fed series was the exception, priced fairly at about 0c.
2. **v1, as the Hedge page calls it, is dangerous.** The page passes `price` = the ask and `market_prob` = the mid. v1 reads the bid-ask spread as the protective side being overpriced. In 56–90% of gas and CPI months it told the person to **sell** the protection, booked at the ask, and sized the sale near the solvency limit. Filled at the real bid, the driver, fleet, retiree and contract-worker personas each had at least one month that wiped out their wealth: at gamma 2, and at gamma 4 for the 28-day driver, fleet and contract worker (the "ruin" cells in Table 3a). At the fill the model assumed, the same trades would have *made* money. The spread is the entire "edge" the model saw. The 10% open-interest cap was the only thing between these users and ruin.
3. **Positions that only buy protection barely matter, in either direction.**
   - **Driver and retiree:** a realistic driver (1,000 gallons a month, $15k cushion) loses $0–$1,036 in a month, and a retiree's CPI-surprise loss is $0–$200. Against these exposures the fees and spread cost about as much as the risk reduction is worth. v1 buys in 0–8 of 25 months for the driver, and the certainty-equivalent (CE) gain is between −$1.3 and +$5 over the whole history, including the thin-cushion driver.
   - **Fleet:** at ten times the driver's exposure, the 28-day hedge earns +$29 at gamma 4 and +$50 at gamma 8 for v1. That is under 0.1% of wealth.
   - **v2:** its $5 minimum-worth floor correctly drops almost all of these trades.
4. **The contract worker's hedge does not work.** "U3 above the last print" paid in 47% of the months a job loss would have happened and in 41% of the months it would not. The measured basis is **0.02**, against 0.30 assumed in `segments.py` and 0.5 as the page's default for a "proxy". Every variant that only buys protection lost certainty equivalent (−$20 to −$262). v2 with `loss_prob=3%` and the assumed 0.30 basis goes to ruin at gamma ≥ 4. The reason is that a 0.30 correlation between a 3% event and a 41% event sits at the Fréchet maximum, which the model reads as "the contract always pays when I lose my job".
5. **The measured basis is lower than `segments.py` assumes, even with no idiosyncratic noise.** Here the loss is defined purely from the realized index, so the measured basis is an *upper bound* on the real one. Gas comes out at 0.52–0.68 (assumed 0.85) and CPI at 0.79–0.82 (assumed 0.90). A single binary contract cannot track a loss that grows with the overrun. For an at-the-money strike and a normal surprise the theoretical ceiling is 0.68, and gas at 7 days hits exactly that.

## 1. Data and method

**Endpoints.** None of these need a key.
- `GET /historical/markets?series_ticker=…` returns markets settled before the exchange's historical cutoff, which is 2026-09-07 (`GET /historical/cutoff`).
- `GET /markets?series_ticker=…&status=settled` returns the newer ones.
- Daily candles: `GET /historical/markets/{ticker}/candlesticks` for old markets and `GET /series/{s}/markets/{ticker}/candlesticks` for new ones. Both take `start_ts`, `end_ts` and `period_interval=1440`.
- The event-level and batch candle endpoints return nothing for historical markets.

**API notes:**
- A candle carries the closing YES bid, YES ask, last trade, volume and **open interest** for the day. The historical market listings show open interest as 0, so the candle is the only place to read open interest.
- Field names differ between the two candle endpoints (`close` vs `close_dollars`, `open_interest` vs `open_interest_fp`).
- The public API served about 2–3 requests a second from this container and returned 429 with no Retry-After header beyond that. A steady 0.35 s pace with short retries worked, at 3,542 calls for the full pull. Exponential back-off made it about 10 times slower.

| series | markets | events | first close | last close | notes |
|---|---|---|---|---|---|
| KXAAAGASM (gas, monthly) | 493 | 35 | 2023-12 | 2026-10 | markets list about a month before close |
| KXCPIYOY | 671 | 47 | 2022-12 | 2026-10 | 4% of values inferred from strike results |
| KXU3 | 613 | 64 | 2021-08 | 2026-11 | 2021–22 events were single or range markets, so no ladder |
| KXPAYROLLS | 409 | 44 | 2023-04 | 2026-11 | calibration only |
| KXFED | 424 | 42 | 2021-07 | 2026-10 | ladders from 2023 on; 8% of values inferred |
| KX30YMORTW (weekly) | 211 | 11 | 2026-08 | 2026-11 | each market lives about a week, so only a 3-day horizon exists |
| KXU3MAX | 1 | 1 | 2023-01 | — | **one settled market ever; unusable** |

**Price at horizon h.** For a horizon h (1, 7, 14 or 28 days), the script takes the last daily candle ending at or before close − h. A candle more than 2 days stale, or one from before the market opened, is dropped. The probability is the bid/ask mid when the spread is 10c or less, otherwise the last trade. A hedger pays the **ask**. The "app" wiring takes `market_prob` from `hone.prediction.contracts.implied_probability`, the page's own rule.

**Realized value.** This is `expiration_value` when it agrees with every strike's result. When it does not, or when the field is missing (for example "Yes" or "Above 3.50%"), the value is inferred from the bracket the strike results imply. Strike floats such as 4.099999 are rounded.

**Personas.** One decision is made per settled period at horizon h.

| persona | contract (protective side) | wealth W | loss |
|---|---|---|---|
| rideshare (driver) | gas: YES on "above K" | $15,000: one month's income plus 3 months of savings | 1,000 gal × (realized − budget)⁺ |
| rideshare_thin | same | $6,000 | same |
| fleet (sensitivity) | same | $60,000 | 10,000 gal × (realized − budget)⁺ |
| retiree / retiree_thin | CPI YoY: YES on "above K" | $80,000 / $32,000 | $40k × (realized − budget)⁺ / 100, i.e. a year of spending at the surprise |
| contractor | U3: YES on "above K" | $23,333: a month's pay plus 3 months of savings | 3 months' pay ($17,500) with monthly probability 3% × exp(1 × Δu), where Δu = realized − last print, in pp |
| realtor / realtor_thin | Fed upper bound: YES on "above K" | $100,000 / $40,000 | $16,000 per +1pp above budget, i.e. 20% of commission per point |
| realtor_mortgage | weekly 30y mortgage rate | $100,000 | the same $16,000 per pp |

- **Budget:** the last value settled before the entry date. This uses no information from the period being hedged.
- **Strike:** K is the smallest listed strike at or above the budget that is quoted on the entry date.
- **Model loss L** for the index personas: dollars-per-unit × (K − budget + E[X − K | X > K]). The expectation is read from the ladder's survival curve on the entry date, cut off where strikes reach the 2c tick floor.

**Sizing.** `hedge_income` is run at gamma 2, 4 and 8, with the basis that `segments.py` assigns to the occupation (0.85, 0.90, 0.30, 0.50). Each case is run without a cap and with `Liquidity(open_interest = the open interest on the entry day)`. Order-book depth cannot be reconstructed, so the cap uses open interest only. There are three wirings:
- `app`: price = ask, market_prob = mid, and the model's default `allow_selling`. This matches `IncomeHedgePage.jsx`.
- `buy_only`: the same with `allow_selling=False`, which is what `quote.py` does.
- `no_tilt`: market_prob = ask. This is the `segments.py` convention: zero speculative tilt and a pure insurance position.

**Accounting.**
- Wealth in each period is W − realized loss + contract P&L. A long position is filled at the ask. A sell recommendation buys NO at 1 − bid, which is the only price available. The model's own booking at 1 − ask is reported separately.
- The contract worker's loss is a lottery within each period, integrated exactly given the realized rate.
- The CE over the history treats each period as an equally likely draw. "Ruin" means at least one period ended at or below zero wealth.

**Look-ahead and other caveats:**
- The budget, strike, model loss, price and open interest use only data from the entry date or earlier.
- The *measured basis* is in-sample by definition.
- The contract worker's hazard parameters are a choice. Table 5b shows how the basis changes with them.
- Events overlap and are serially correlated, for example a run of disinflation months. The confidence intervals come from bootstraps that resample whole events. They handle the fact that all strikes in an event settle on one number, but not serial correlation, so read them as optimistic.
- 2021–2026 covers one disinflation and one re-inflation episode. That is too few cycles to call any series bias permanent.
- Fills assume the quoted ask for the full size. For uncapped positions of thousands of contracts that is optimistic.

## 2. Calibration (question 1)

### 2a. All series combined, and by series

Each row counts strikes (n) and events. "Skill" is 1 − Brier / Brier of the base rate. The slope b comes from logit P(yes) = a + b·logit(p): b > 1 means the prices were too timid and b < 1 means they were too extreme. Square brackets show 95% CIs from an event bootstrap.

| h | set | n / events | Brier [CI] | skill | bias p−y [CI] | slope b [CI] |
|---|---|---|---|---|---|---|
| 1 | all | 1713 / 238 | 0.090 [0.076, 0.104] | 0.64 | +0.003 [−0.026, +0.029] | 1.05 [0.96, 1.17] |
| 7 | all | 1416 / 227 | 0.109 [0.094, 0.127] | 0.56 | +0.022 [−0.017, +0.056] | 1.01 [0.91, 1.15] |
| 7 | 5–95c only | 872 / 204 | 0.172 [0.154, 0.192] | 0.31 | +0.031 [−0.029, +0.084] | 0.90 [0.76, 1.06] |
| 28 | all | 1214 / 185 | 0.117 [0.100, 0.136] | 0.53 | +0.008 [−0.031, +0.045] | 1.05 [0.88, 1.24] |
| 28 | 5–95c only | 859 / 175 | 0.160 [0.142, 0.180] | 0.36 | +0.010 [−0.045, +0.064] | 0.99 [0.81, 1.22] |
| 7 | KXAAAGASM | 294 / 33 | 0.071 | 0.71 | **+0.065 [+0.016, +0.112]** | 1.20 [1.00, 1.60] |
| 28 | KXAAAGASM | 290 / 27 | 0.120 | 0.51 | −0.002 [−0.085, +0.069] | 1.01 [0.75, 1.70] |
| 7 | KXCPIYOY | 295 / 45 | 0.081 | 0.67 | +0.033 [−0.014, +0.080] | 1.29 [0.95, 1.89] |
| 28 | KXCPIYOY | 308 / 41 | 0.099 | 0.59 | +0.053 [−0.001, +0.111] | 1.07 [0.86, 1.46] |
| 7 | KXU3 | 333 / 64 | 0.121 | 0.51 | **+0.064 [+0.025, +0.113]** | 1.15 [0.98, 1.38] |
| 28 | KXU3 | 199 / 41 | 0.125 | 0.49 | **+0.095 [+0.039, +0.154]** | 1.34 [1.07, 1.85] |
| 7 | KXPAYROLLS | 358 / 44 | 0.190 | 0.21 | −0.052 [−0.164, +0.058] | 0.70 [0.51, 1.00] |
| 28 | KXPAYROLLS | 260 / 35 | 0.182 | 0.23 | −0.091 [−0.208, +0.033] | 0.87 [0.53, 1.42] |
| 7 | KXFED | 136 / 41 | 0.014 | 0.94 | −0.002 [−0.024, +0.018] | n/a (nearly all strikes at the extremes) |
| 28 | KXFED | 156 / 40 | 0.027 | 0.89 | −0.009 [−0.032, +0.017] | n/a |
| 1 | KX30YMORTW | 171 / 11 | 0.050 | 0.80 | −0.056 [−0.110, −0.010] | 11 events; too few |

Reliability across all series at 7 days (28 days is similar; both tables are in the script output):

| price bucket | 0–5c | 5–10 | 10–20 | 20–30 | 30–40 | 40–50 | 50–60 | 60–70 | 70–80 | 80–90 | 90–95 | 95–100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| strikes | 262 | 103 | 110 | 76 | 76 | 66 | 73 | 84 | 69 | 122 | 81 | 294 |
| mean price | 2.1 | 6.9 | 14.5 | 25.1 | 34.5 | 44.1 | 55.1 | 65.5 | 75.4 | 85.2 | 92.3 | 97.7 |
| % YES | 0.0 | 5.8 | 18.2 | 21.1 | 26.3 | 53.0 | 49.3 | 54.8 | 68.1 | 81.1 | 87.7 | 98.3 |

There is no strong favourite–longshot bias. The 0–5c bucket is about 2c rich, which is the tick floor, and 5–20c is fair. The 60–95c range is 4–11pp rich at 7 days, but every bucket's CI there includes zero.

### 2b. What buying at the quote returned (per $1 contract, before fees)

Only quotes with a 3c ≤ bid and an ask ≤ 97c are included. A YES bought at the ask pays y − ask, and a NO bought at 1 − bid pays bid − y.

| h | series | n / events | mean spread | **YES at ask** [CI] | NO at 1−bid [CI] |
|---|---|---|---|---|---|
| 7 | all | 884 / 206 | 5.3c | −5.7c [−11.0, +0.3] | +0.3c [−5.7, +6.1] |
| 7 | gas | 116 / 30 | 5.8c | **−19.3c [−31.2, −7.6]** | +13.5c |
| 7 | CPI | 166 / 45 | 5.7c | **−7.1c [−13.1, −1.0]** | +1.4c |
| 7 | U3 | 251 / 64 | 5.3c | **−10.4c [−17.4, −5.0]** | +5.1c |
| 7 | payrolls | 320 / 44 | 5.3c | +3.3c | −8.6c [−21.1, +3.7] |
| 7 | Fed | 31 / 23 | 1.6c | −0.6c | −1.0c |
| 28 | gas | 191 / 24 | 8.7c | −4.2c [−14.8, +9.8] | −4.5c |
| 28 | CPI | 181 / 37 | 7.0c | **−11.3c [−19.0, −3.4]** | +4.3c |
| 28 | U3 | 148 / 39 | 10.0c | **−15.9c [−23.8, −8.8]** | +6.0c |
| 28 | payrolls | 230 / 35 | 9.6c | +6.3c | **−15.9c [−27.2, −2.5]** |
| 28 | Fed | 52 / 36 | 2.3c | +0.8c | −3.1c |

The bold sides are the ones a hedger buys: high gas, high CPI, high unemployment, low payrolls. All of them had **negative realized returns**, from 4 to 19c per contract. This is consistent with an insurance or pessimism premium. In this sample it is several times the half-spread. The Fed ladder is the one fairly priced, liquid exception.

**Answer to question 1.** Across series, the market's mid price is calibrated at both horizons. The model can keep using it as the probability, and there is no evidence for a general longshot correction. The **protective side** of the macro ladders has carried a premium of roughly 5–15c over and above the spread. The model treats that premium as zero, so it overstates what a hedge is worth for these series. With only 30–64 serially correlated events per series, a correction factor is not yet justified. The result is grounds for showing users the record and for leaning towards smaller hedges.

## 3. Hedge performance by segment (question 2)

### 3a. v1 as the page wires it (`app`: price = ask, market_prob = mid, selling allowed)

Each period is one decision. P&L is summed over the history. "Ruin" means wealth went to zero or below in at least one period.

| persona | h | periods | months told to SELL (γ2/4/8) | P&L filled at bid, γ4 | P&L at model's fill, γ4 | CE gain γ2 | CE gain γ4 | CE gain γ8 | CE γ4, OI-capped |
|---|---|---|---|---|---|---|---|---|---|
| rideshare | 7 | 25 | 21/20/20 | −$2,908 | +$7,305 | −$303 | −$136 | −$64 | −$8 |
| rideshare | 28 | 25 | 18/17/14 | −$37,913 | +$30,497 | ruin | ruin | −$8,660 | −$1 |
| fleet | 28 | 25 | 17/12/8 | −$142,036 | +$121,777 | ruin | ruin | −$32,169 | −$6 |
| retiree | 7 | 30 | 22/22/22 | −$65,412 | +$1,963 | ruin | −$17,357 | −$3,950 | −$24 |
| retiree | 28 | 29 | 26/26/26 | −$76,092 | +$135,015 | ruin | −$55,922 | −$5,772 | −$0 |
| contractor | 7 | 46 | 5/5/5 (bought 41) | −$2,166 | −$1,760 | −$111 | −$117 | −$46 | −$62 |
| contractor | 28 | 30 | 5/5/5 (bought 25) | −$19,112 | +$2,156 | ruin | ruin | −$3,777 | −$69 |
| realtor (Fed) | 28 | 24 | 10/8/7 | −$1,899 | +$186 | −$193 | −$94 | −$66 | −$3 |
| realtor_mortgage | 3 | 10 | 8/8/8 | −$1,645 | +$1,286 | −$412 | −$191 | −$91 | +$1 |

The thin-cushion personas look the same. All rows are in `backtest_summary.csv`, filter `variant == "app"`.

**Mechanism.** With `market_prob` = mid and `price` = ask, `price − belief` equals half the spread, and v1 treats that as the protective side being overpriced. The speculative tilt, at ±(spread / variance) × wealth / gamma, swamps a small pure hedge of ρ × L. So the model sells the protection, sizing the sale against `1 − price`, and the market charges `1 − bid`. When the spread is wide (an ask of 0.49 against a last trade of 0.01, for example), the position runs to the solvency bound.

### 3b. Buying protection only: v1 `no_tilt` (as in segments.py), v1 `buy_only` and v2

Coverage tracks how often the bought contract paid. "Pays if loss" is the share of loss periods in which the contract paid, and "pays if no loss" is the share of other periods in which it paid. The premium is the expected cost of the hedge above the market's mid: spread plus fees.

| persona | h | loss periods | pays if loss / no loss | v1 months hedged γ2/4/8 | v1 premium γ4 | v1 net P&L γ4 | v1 CE γ2 / γ4 / γ8 | v1 CE γ4 capped | v1 buy_only CE γ4 | v2 months hedged γ2/4/8 | v2 CE γ4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 7 | 10/25 | 0.80 / 0.00 | 0/0/5 | $0 | $0 | 0 / 0 / −0.3 | 0 | 0 | 0/0/0 | 0 |
| rideshare | 28 | 9/25 | 1.00 / 0.00 | 1/4/8 | $195 | +$32 | +0.7 / +1.3 / +1.7 | −1.1 | 0 | 0/0/0 | 0 |
| rideshare_thin | 28 | 9/25 | 1.00 / 0.00 | 6/11/21 | $291 | +$41 | +0.7 / +2.8 / +5.0 | −1.3 | +0.9 | 0/0/0 | 0 |
| fleet | 7 | 10/25 | 0.80 / 0.00 | 0/7/16 | $160 | −$124 | 0 / −4.2 / −0.5 | −5.9 | −0.3 | 0/0/0 | 0 |
| fleet | 28 | 9/25 | 1.00 / 0.00 | 6/11/21 | $2,909 | +$412 | +6.5 / +29 / +50 | −1.4 | +8.4 | 0/0/0 | 0 |
| retiree (and thin) | 7, 28 | 15–16/30 | 0.94–1.00 / 0.00 | 0/0/0 | — | — | 0 / 0 / 0 | 0 | 0 | 0/0/0 | 0 |
| contractor | 7 | 1.4 expected | 0.47 / 0.41 | 46/46/46 | $1,802 | −$4,515 | −243 / −232 / −91 | −85 | −133 | 38/36/27 | −68 |
| contractor | 28 | 0.9 expected | 0.53 / 0.46 | 30/30/30 | $1,611 | −$3,390 | −262 / −243 / −94 | −28 | −198 | 21/20/16 | −113 |
| realtor (Fed) | 7 | 5/23 | 0.80 / 0.00 | 0/15/23 | $27 | −$171 | 0 / −7.8 / −18 | −7.8 | −2.6 | 0/0/0 | 0 |
| realtor (Fed) | 28 | 5/24 | 0.80 / 0.00 | 2/14/24 | $167 | −$769 | −7.1 / −33 / −59 | −30 | −6.7 | 0/0/0 | 0 |
| realtor_mortgage | 3 | 6/10 | 1.00 / 0.00 | 0/0/1 | $0 | $0 | 0 / 0 / +0.1 | 0 | 0 | 0/0/0 | 0 |

Realized losses over the whole history, with no hedge, give the scale of what is at stake:
- driver: $1,085 at 7 days and $2,128 at 28 days;
- fleet: $10,850 and $21,276;
- retiree: $1,320 and $1,840;
- realtor: $20,000;
- contract worker: an expected $24,760 over 46 months (1.4 job losses).

The standard deviation of wealth per period is $76–217 for the driver, $54–67 for the retiree, about $1,650 for the realtor and about $3,020 for the contract worker.

**What the table says:**

- **Driver and retiree.** The exposure is too small for the hedge to pay for itself. The whole risk premium is roughly γσ²/2W. For the retiree that is about $0.2 per period at gamma 8, less than the fee on 15 contracts. v1 rarely buys, and when it does the CE gain is a few dollars over the whole history. The `segments.py` loss sizes ($4,500 for the driver and $2,400 for the retiree) are far larger than anything one settled monthly contract implies:
  - The largest driver loss was $1,036 (March 2026). The average month with a loss was $108 at 7 days and $236 at 28 days, so the assumption is 4 times the worst month and 20–40 times the typical one.
  - The largest retiree loss was $200, and the average month with a loss $88–115: 12 times and about 25 times.
- **Fleet.** This is the one case with a clearly positive result, and only at 28 days: +$29 at gamma 4 and +$50 at gamma 8 on $60k. The contract paid in all 9 overrun months and in none of the other 16. The fleet paid $2.9k of spread and fees on $11.5k of contracts and still came out +$412. In that sample gas overruns were priced correctly at the 28-day horizon (Table 2b). By 7 days the outcome is mostly known: 32% of the chosen strikes were already at 5c or below, or 95c or above, so there was nothing left to hedge.
- **Contract worker.** It buys every month at gamma 2–8 (714 contracts at gamma 4, about $400 a month). The hedge pays almost as often when nothing happens as when the job is lost, so it adds variance (σ goes from 3,022 to 3,038) and loses $3.4–4.5k. This is a hedge that should not exist.
- **Realtor (Fed).** At gamma 4 and 8, v1 bought cheap tail strikes ("hike above budget" at 2–3c) that never paid. Of the 5 hikes, 3–4 were already priced at 30–97c by the entry date, and the model, sizing at fair odds, held none of them. The other 1–2 were missed because the nearest quoted strike sat one step above the budget. The net effect is small and negative.
- **v2** suppresses nearly all of these trades through its minimum-worth floor and no-sell default. That is the right answer for the driver and retiree. It also drops the fleet's small positive hedge. Its contract-worker hedge is about 60% of v1's size and still loses (−$68 to −$113 at gamma 4).

### 3c. v2 with `loss_prob` (contract worker, loss_prob = 3%, basis = 0.30)

| h | γ | months hedged | median contracts | cost | net P&L | CE gain | CE gain, OI-capped |
|---|---|---|---|---|---|---|---|
| 7 | 2 | 41 | 3,222 | $68k | −$9.7k | −$459 | −$232 |
| 7 | 4 | 46 | 7,908 | $185k | −$39.6k | ruin | −$2,342 |
| 7 | 8 | 46 | 12,320 | $281k | −$64.5k | ruin | −$7,937 |
| 28 | 4 | 27 | 7,857 | $108k | −$24.5k | −$11,802 | −$24 |

A correlation of 0.30 between a 3% loss and a 41% event is at the top of the feasible range: `joint_states` clips it to about 0.27. In that state every job loss coincides with the contract paying, so the model buys about L/(1 − p) contracts to insure the loss "fully". The data say the contract paid in 47% of job-loss months. With `loss_prob` available, the basis has to be elicited on a different scale. See change #3.

### 3d. Liquidity

The open interest (OI) on the entry day, 28 days before close, is thin. For gas the median is 542 contracts (25th percentile: 25). For U3 it is 666 (25th percentile: 43). By 7 days before close, these grow to 11,633 and 3,487. CPI and the Fed are deeper.

At 28 days the 10% cap therefore left the fleet a median of 3–12% of its wanted hedge, depending on gamma, and the contract worker 6–20%. That turned the fleet's only positive result into a slightly negative one: −$1.4 at gamma 4 with the cap. The cap does its job against the v1 sell bug. For genuine buy-side hedges it binds hardest exactly when the hedge is most useful, which is early, before the outcome is known.

## 4. Basis: measured vs assumed (question 3)

The measured basis is corr(contract payoff, realized loss) across periods. For the contract worker it is corr(payoff, job-loss indicator), computed exactly as cov(B, p_t) / √(var B · p̄(1 − p̄)).

| persona | h | periods | assumed (segments.py) | measured ρ(payoff, $ loss) | measured ρ(payoff, any loss) | variance-minimizing contracts | model's ρ·L |
|---|---|---|---|---|---|---|---|
| rideshare / fleet | 7 | 25 | 0.85 | **0.68** | 0.84 | 111 per 1,000 gal | 77 |
| rideshare / fleet | 28 | 25 | 0.85 | **0.52** | 1.00 | 236 | 156 |
| retiree | 7 | 30 | 0.90 | **0.82** | 1.00 | 88 | 51 |
| retiree | 28 | 29 | 0.90 | **0.79** | 0.93 | 106 | 71 |
| contractor | 7 | 46 | 0.30 | **0.019** | — | 116 | 5,250 |
| contractor | 28 | 30 | 0.30 | **0.022** | — | 131 | 5,250 |
| realtor (Fed) | 7 / 28 | 23 / 24 | 0.50 | 0.87 (upper bound) | 0.87 | 3,790 | 1,700–1,900 |
| realtor_mortgage | 3 | 10 | 0.50 | 0.72 (10 weeks) | 1.00 | 1,973 | 463 |

**Reading the table.** For the gas, CPI and Fed personas the loss is *defined* from the realized index, so these numbers measure only the mismatch between a single binary strike and a loss that grows with the overrun. They are **upper bounds**. A real driver's fuel bill or an agent's commissions add idiosyncratic noise on top, which this data cannot see.

Even this ceiling is below what `segments.py` assumes for the driver (0.85) and the retiree (0.90). The ceiling has a theoretical value: for an at-the-money strike and a normal surprise X, corr(1{X > 0}, max(X, 0)) = 0.68, and gas at 7 days measures 0.677. At 28 days the strike sits further from the realized value, so the ceiling is lower (0.52).

The variance-minimizing size is 1.4–2.2 times the model's ρ·L. The model's single-strike L understates how far the loss keeps growing past the strike. For the contract worker the model's pure hedge (5,250 contracts) is 40 times the variance-minimizing one (116–131).

### 4b. Contract worker: the basis is small under any plausible hazard

The table shows the measured basis for different monthly job-loss probabilities p0 and hazard elasticities κ, where hazard = p0 × e^(κΔu) at 7 days. Over the 46 months, Δu had a standard deviation of 0.12pp (range −0.20 to +0.30pp). The contract paid in 41% of months.

| p0 | κ = 1 | κ = 3 | κ = 10 | κ = 30 |
|---|---|---|---|---|
| 1% | 0.011 | 0.035 | 0.152 | 0.564 |
| 3% | 0.019 | 0.061 | 0.271 | 0.764 |
| 10% | 0.036 | 0.116 | 0.462 | 0.953 |

Reaching the assumed 0.30 needs κ ≈ 10: each 0.1pp unemployment surprise would multiply a person's monthly layoff risk by 2.7. That is not plausible for an individual. The month-to-month surprise in U3 is mostly noise relative to one person's job risk.

## 5. Model changes the data supports, ranked

1. **Never propose selling the protective side to someone with exposure, and price any short at the bid.**
   - The evidence is Table 3a: v1 as wired led to ruin for 4 of 5 personas at gamma 2–4.
   - v2's `allow_selling=None` closes this for hedgers. `_Pricer` still books shorts at `1 − price`, which is the ask's complement. If selling is ever re-enabled (speculation with `loss == 0`), it needs the bid.
   - The page should pass the bid as well as the ask.
2. **Treat the spread as a cost, not as mispricing.**
   - The belief is the mid and the fill is the ask, and the half-spread plus fee is the premium. This is what v2's "insurance at market odds" step does. Keep it, and add a regression test: with no view, the result should never be smaller than the `no_tilt` result at a zero spread.
3. **With a separate `loss_prob`, change what "basis" means.**
   - A Pearson correlation between Bernoullis with very different marginals is not something users can supply. A 0.30 sounds modest, but against a 3% loss it implies "always pays when I lose", and the model went to ruin (Table 3c).
   - Elicit **P(contract pays | I suffer the loss)** instead. The data give 0.47 against an unconditional 0.41 for U3. Derive ρ from that, or cap ρ at a share of the Fréchet maximum and warn.
4. **Lower the default basis to what the data allow.**
   - Unemployment-proxy hedges for individual job loss: about 0.02 (at most 0.1 under any plausible hazard). The model should say "no useful hedge" instead of defaulting to 0.5, the frontend's `BASIS_DEFAULT.proxy`.
   - A single binary strike against a loss that grows with the overrun: at most about 0.68 at the money (0.52–0.82 measured). The "direct" default of 0.9 is above what a single strike can reach.
   - **Offer a ladder of strikes, or a variance-minimizing size of about cov(B, L)/var(B), when the loss is continuous.** The single-strike ρ·L under-sizes by 1.4–2.2 times (Table 4).
5. **Do not assume the protective side is fair.**
   - Combining all series, the market price is calibrated, so keep using it as the probability.
   - But buyers of the protective macro sides lost 4–16c per contract, with CIs that exclude zero for CPI, U3 and payrolls. Show each series' record ("buyers of this side lost about X c per $1 over N events") next to the reservation price.
   - Consider adding the measured premium to the price before sizing. Treat that as a soft adjustment until more events accumulate: the serial correlation and the 2022–26 regime make it fragile.
6. **Keep a minimum-worth floor (v2's `MIN_WORTH`) and say so up front.**
   - For realistic monthly cost exposures (drivers, retirees), the best hedge is worth a few dollars at most, and it is negative after the cap.
   - Re-base `segments.py`'s loss sizes on per-contract, per-period losses. For monthly contracts they are 4–12 times the worst month and 20–40 times the typical one, which inflates every segment result built on them.
   - Point hedging at larger, lumpier exposures (fleets, agents' pipelines). The contract-worker segment is not hedgeable with U3 at all.
7. **Make the liquidity cap aware of timing.** Open interest 28 days out is 5–20 times smaller than a week out, so a 10% cap leaves 3–20% of the hedge exactly when it is useful. The options are to:
   - cap against expected open interest near close (for example, the median final OI of the series' recent events);
   - propose building the position in stages;
   - report "enter now, add later" instead of a single capped number.

   v2's move to 25% of OI helps only at the margin.
8. **Tie horizon guidance to information.** Seven days before close, the strike nearest the budget was already at 5c or below, or 95c or above, in 32% of gas periods, 20% of CPI periods and 74% of Fed periods (U3: 0%). The page should warn when the market has already resolved most of the uncertainty: such a hedge is either pointless or expensive.

## 6. What this does not show

- **The links between index and income.** Gas against a real driver's fuel bill, Fed rates against commissions, and U3 against a specific job are not observable here. The losses are modelling choices, stated in §1, and the basis for index-defined losses is an upper bound.
- **Order-book depth.** It is not available historically, so the depth half of `limit_for` was not tested.
- **Large sample sizes.** There are 23–64 events per series, overlapping and serially correlated. The weekly mortgage series has 11 weeks, and KXU3MAX one market. Treat the series-level bias numbers as indicative.
- **A stable v2.** v2 was changing during the run. The numbers are tagged `worktree@70ca128177`, and `--models <rev> worktree` re-runs them against any revision.
