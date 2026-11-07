# Sweep tables (78,480 personas, 0 input errors)

## A1. Who gets value (core sweep: 12,960 personas, market beliefs)

Per occupation, medians over gamma 0.25-12, savings 0-24 mo, income x0.5-2, loss share x0.5-1.5. 'cap' = shipped default (10% of OI, 3c slippage, flat book). CE figures are realized under Truth() (market and basis right).

| occupation | loss/income | coverage (cap) | CE gain $ (cap) | CE % inc (cap) | CE % inc p90 (cap) | > 0.5% inc (cap) | CE % inc (uncap) | > 0.5% inc (uncap) | ~0 (<0.05%) (cap) | cost % inc (uncap) |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 0.10 | 1.00 | 0.00 | 0.00 | 0.61 | 12.59 | 0.00 | 12.59 | 60.37 | 0.00 |
| retiree | 0.06 | 1.00 | 0.00 | 0.00 | 0.20 | 2.96 | 0.00 | 2.96 | 78.52 | 0.00 |
| contractor | 0.50 | 0.21 | 39.68 | 0.08 | 0.88 | 21.48 | 0.18 | 36.30 | 48.02 | 0.93 |
| realtor | 0.40 | 0.00 | 0.00 | 0.00 | 0.07 | 0.00 | 0.46 | 48.52 | 86.17 | 3.71 |
| ad_freelancer | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.08 | 25.18 | 90.25 | 1.02 |
| ski | 0.35 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.48 | 49.26 | 100.00 | 5.16 |
| recruiter | 0.35 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.24 | 38.15 | 94.94 | 2.15 |
| tech | 0.50 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |

Median realized CE gain, % of income, by gamma (capped (default), income x1, all savings/loss levels):

| occupation | 0.25 | 0.5 | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 12.0 |
|---|---|---|---|---|---|---|---|---|---|
| rideshare | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.061 | 0.230 | 0.353 | 0.596 |
| retiree | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.055 | 0.201 |
| contractor | 0.000 | 0.000 | 0.000 | 0.039 | 0.114 | 0.195 | 0.381 | 0.570 | 0.665 |
| realtor | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| ad_freelancer | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| ski | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| recruiter | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| tech | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Median realized CE gain, % of income, by gamma (uncapped, income x1, all savings/loss levels):

| occupation | 0.25 | 0.5 | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 12.0 |
|---|---|---|---|---|---|---|---|---|---|
| rideshare | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.061 | 0.230 | 0.353 | 0.596 |
| retiree | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.055 | 0.201 |
| contractor | 0.000 | 0.000 | 0.000 | 0.082 | 0.322 | 0.552 | 1.090 | 1.084 | 0.953 |
| realtor | 0.000 | 0.000 | 0.059 | 0.425 | 0.778 | 1.099 | 1.344 | 1.172 | 0.908 |
| ad_freelancer | 0.000 | 0.000 | 0.000 | 0.041 | 0.170 | 0.291 | 0.567 | 0.855 | 1.216 |
| ski | 0.000 | 0.000 | 0.064 | 0.457 | 0.826 | 1.163 | 1.618 | 1.540 | 1.215 |
| recruiter | 0.000 | 0.000 | 0.000 | 0.203 | 0.429 | 0.667 | 1.124 | 1.392 | 1.097 |
| tech | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Median realized CE gain, % of income, by savings months (uncapped, income x1, loss x1, all gammas):

| occupation | 0 | 1 | 3 | 6 | 12 | 24 |
|---|---|---|---|---|---|---|
| rideshare | 0.112 | 0.095 | 0.069 | 0.000 | 0.000 | 0.000 |
| retiree | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| contractor | 0.665 | 0.553 | 0.396 | 0.257 | 0.127 | 0.000 |
| realtor | 0.866 | 0.971 | 0.811 | 0.624 | 0.388 | 0.168 |
| ad_freelancer | 0.311 | 0.266 | 0.198 | 0.133 | 0.000 | 0.000 |
| ski | 1.114 | 1.018 | 0.851 | 0.660 | 0.418 | 0.187 |
| recruiter | 0.687 | 0.604 | 0.474 | 0.341 | 0.190 | 0.000 |
| tech | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

% of personas with CE gain > 0.5% of income, by gamma band x savings (uncapped | capped):

| gamma_band | 0 | 1-3 | 6 | 12-24 |
|---|---|---|---|---|
| <=1 | 6.2 | 3.1 | 1.0 | 0.0 |
| 1-3 | 30.0 | 26.7 | 17.5 | 7.5 |
| 3-6 | 50.0 | 45.8 | 40.3 | 27.8 |
| 6-12 | 69.4 | 66.0 | 59.7 | 44.4 |

| gamma_band | 0 | 1-3 | 6 | 12-24 |
|---|---|---|---|---|
| <=1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 1-3 | 3.1 | 1.8 | 0.6 | 0.0 |
| 3-6 | 11.6 | 10.2 | 5.6 | 1.2 |
| 6-12 | 20.4 | 19.0 | 13.9 | 7.4 |

Contracts / pure hedge (rho*L) by gamma (uncapped, market belief, savings 3 mo, income x1, loss x1). Basis (rho): rideshare 0.85, retiree 0.9, contractor 0.3, realtor 0.5, ad_freelancer 0.4, ski 0.6, recruiter 0.45, tech 0.15:

| occupation | 0.5 | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 12.0 |
|---|---|---|---|---|---|---|---|---|
| rideshare |  | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| retiree |  |  | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 |
| contractor | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| realtor | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| ad_freelancer |  | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| ski | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| recruiter | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| tech |  | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 0.00 | 0.00 |

Capped default: 82.3% of core personas are advised 0 contracts; 4.6% get > 0.5% of income; 82.3% get < 0.05%. Uncapped: 50.5% zero, 26.6% > 0.5%.

## A2. Liquidity policy (28,224 personas)

Flat book (segments.py's assumption): contracts never depend on max_slippage (max distinct sizes across slippage settings = 1); the OI share is the only lever.

Median share of uncapped CE gain retained, flat book, by OI share (slippage irrelevant):

| occupation | 0.05 | 0.10 | 0.25 | 0.50 | 1.00 | off |
|---|---|---|---|---|---|---|
| rideshare | 74.5 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| retiree | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| contractor | 7.6 | 18.7 | 44.7 | 75.4 | 99.0 | 99.0 |
| realtor | 0.0 | 0.0 | 0.0 | 0.0 | 11.5 | 16.7 |
| ad_freelancer | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ski | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| recruiter | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| tech | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Ladder book (depth/4 per cent, 20c deep; fills walk the book): median % of uncapped CE retained, columns = OI share / slippage. Values > 100% mean the cap *beats* the uncapped advice, because uncapped advice ignores slippage:

| occupation | 0.05/1c | 0.05/3c | 0.05/10c | 0.10/1c | 0.10/3c | 0.10/10c | 0.25/1c | 0.25/3c | 0.25/10c | 0.50/1c | 0.50/3c | 0.50/10c | 1.00/1c | 1.00/3c | 1.00/10c | off/1c | off/3c | off/10c |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 74.5 | 74.5 | 74.5 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| retiree | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| contractor | 7.6 | 7.6 | 7.6 | 18.7 | 18.7 | 18.7 | 44.2 | 44.2 | 44.2 | 66.4 | 68.3 | 68.3 | 66.4 | 76.9 | 76.9 | 66.4 | 76.9 | 77.1 |
| realtor | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 7.7 | 10.4 | 10.4 | 7.7 | 14.3 | 24.0 |
| ad_freelancer | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ski | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| recruiter | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| tech | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Ladder book, 3c slippage: median realized CE gain ($) by OI share:

| occupation | 0.05 | 0.10 | 0.25 | 0.50 | 1.00 | off |
|---|---|---|---|---|---|---|
| rideshare | 30.8 | 41.9 | 41.9 | 41.9 | 41.9 | 41.9 |
| retiree | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| contractor | 0.0 | 63.2 | 167.2 | 254.8 | 273.7 | 273.7 |
| realtor | 0.0 | 0.0 | 0.0 | 0.0 | 76.4 | 112.9 |
| ad_freelancer | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ski | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| recruiter | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| tech | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Ladder book: the policy with the highest mean realized CE gain per occupation:

| occupation | oi | slippage | ce_gain_true |
|---|---|---|---|
| rideshare | off | 0.10 | 103.11 |
| retiree | 0.10 | 0.10 | 25.39 |
| contractor | off | 0.05 | 430.73 |
| realtor | off | 0.10 | 209.46 |
| ad_freelancer | 0.50 | 0.10 | 16.65 |
| ski | 1.00 | 0.10 | 1.37 |
| recruiter | off | 0.10 | 44.99 |
| tech | 0.10 | 0.10 | 0.00 |

Ladder book, no OI cap, 10c slippage: median position = 0.0x open interest (p90 1.6x).

## A3. Failure modes

Counts over the core, liquidity, beliefs and prices sweeps. f_sell = sells the protective side while exposed; f_cost25 = cost > 25% of income; f_over_res = buys with the quoted price above the reservation price; f_fill_over_res = buys with the average *fill* price above it; f_ce_model_neg / f_ce_true_neg = negative CE gain by the model's own numbers / under Truth(); f_ce_true_neg_mkt = same, among personas with no view; f_tiny = a non-zero trade worth < $1.

| sweep | f_sell | f_cost25 | f_over_res | f_fill_over_res | f_ce_model_neg | f_ce_true_neg | f_ce_true_neg_mkt | f_tiny | n |
|---|---|---|---|---|---|---|---|---|---|
| beliefs | 0 | 0 | 0 | 0 | 0 | 4801 | 0 | 20 | 26112 |
| core | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12960 |
| liquidity | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28224 |
| prices | 0 | 20 | 0 | 0 | 0 | 1180 | 0 | 12 | 8640 |
| all | 0 | 20 | 0 | 0 | 0 | 5981 | 0 | 32 | 75936 |

Cost > 25% of income: 20 personas, 100% in the price sweep; median price 0.90, median cost 28% of income; 100% hold a view. Occupations: ski 13, realtor 7

Buying above the reservation price at the quote: 0 personas; at the average fill: 0 (all on the ladder book: 0); their median realized CE nan $, worst nan $.

Non-zero trades worth < $1 of CE: 32 (0.0%); median size 5307 contracts; 34.4% of them are capped. Negative model CE among market-belief, flat-book personas is fee rounding: worst nan $.

### Instability (1% input perturbations)

8,000 sampled personas x up to 12 perturbations = 89,679 re-runs. Unstable = direction flip, on/off switch (>= 3 contracts), or a change >= max(3, 10%) of the position from a 1% input move (elasticity > 10). 0.8% of personas are unstable to at least one 1% perturbation.

| input | has_view | n | unstable_pct | jump_pct | onoff_pct | flip_pct | median_abs_elasticity | p99_abs_elasticity |
|---|---|---|---|---|---|---|---|---|
| basis | False | 5488 | 0.29 | 0.29 | 0.29 | 0.00 | 1.20 | 1.92 |
| basis | True | 10512 | 0.14 | 0.14 | 0.14 | 0.00 | 1.00 | 2.95 |
| conf | True | 9679 | 0.11 | 0.11 | 0.11 | 0.00 | 0.00 | 2.07 |
| gamma | False | 5488 | 0.27 | 0.27 | 0.27 | 0.00 | 0.25 | 1.08 |
| gamma | True | 10512 | 0.14 | 0.14 | 0.14 | 0.00 | 0.26 | 2.11 |
| loss | False | 5488 | 0.29 | 0.29 | 0.29 | 0.00 | 1.03 | 2.68 |
| loss | True | 10512 | 0.16 | 0.16 | 0.16 | 0.00 | 0.98 | 3.40 |
| price | False | 5488 | 0.09 | 0.09 | 0.09 | 0.00 | 0.19 | 1.14 |
| price | True | 10512 | 0.34 | 0.34 | 0.32 | 0.00 | 0.15 | 6.82 |
| wealth | False | 5488 | 0.29 | 0.29 | 0.29 | 0.00 | 0.29 | 3.32 |
| wealth | True | 10512 | 0.19 | 0.19 | 0.19 | 0.00 | 0.29 | 2.42 |

Value at stake where it happens: median base CE gain 20.30 $ (p90 309.52 $) vs 0.00 $ for all sampled; 98.9% of unstable re-runs straddle the 0-contract entry threshold. Without a view, 35.3% of unstable cases are worth < $5.

Unstable re-runs by occupation: rideshare 17, retiree 14, contractor 43, realtor 15, ad_freelancer 44, ski 20, recruiter 26, tech 3. By liquidity: capped 64, uncapped 118.

### How much of the position is speculation? (beliefs sweep, uncapped)

Tilt = n*(with view) - n*(market belief), in units of the pure hedge rho*L. For market-belief personas the model's own 'speculative_contracts' (n* - rho*L) is still 0.00x the pure hedge at the median (p10 0.00, p90 0.00) — fees and CRRA skew, not a view.

Median tilt / pure hedge, by gamma:

| gamma | optimist | pessimist |
|---|---|---|
| 0.5 | -1.00 | 3.53 |
| 1 | -1.00 | 2.34 |
| 2 | -1.00 | 1.47 |
| 3 | -1.00 | 1.29 |
| 4 | -1.00 | 1.11 |
| 6 | -0.84 | 0.77 |
| 8 | -0.60 | 0.56 |
| 12 | -0.38 | 0.37 |

Median tilt / pure hedge, by view strength = |shift| x confidence (blended move in probability):

| strength | optimist | pessimist |
|---|---|---|
| 0.01 | -0.18 | 0.18 |
| 0.02 | -0.36 | 0.37 |
| 0.03 | -0.54 | 0.53 |
| 0.04 | -0.71 | 0.70 |
| 0.05 | -0.95 | 0.88 |
| 0.06 | -1.00 | 1.00 |
| 0.08 | -1.00 | 1.18 |
| 0.09 | -1.00 | 1.25 |
| 0.1 | -1.00 | 1.25 |
| 0.12 | -1.00 | 1.26 |
| 0.15 | -1.00 | 1.26 |
| 0.16 | -1.00 | 1.26 |
| 0.18 | -1.00 | 1.28 |
| 0.2 | -1.00 | 1.28 |
| 0.24 | -1.00 | 1.29 |
| 0.3 | -1.00 | 1.31 |

Median tilt / pure hedge, by occupation:

| occupation | optimist | pessimist |
|---|---|---|
| rideshare | -1.00 | 1.26 |
| retiree | -1.00 | 1.46 |
| contractor | -1.00 | 1.00 |
| realtor | -0.70 | 0.65 |
| ad_freelancer | -1.00 | 1.02 |
| ski | -0.67 | 0.66 |
| recruiter | -1.00 | 0.89 |
| tech | -1.00 | 2.16 |

Median share of the gross position that is speculative, |tilt| / (|n_mkt| + |tilt|): rideshare 50%, retiree 53%, contractor 50%, realtor 42%, ad_freelancer 50%, ski 42%, recruiter 50%, tech 50%.

Worst-state wealth falls by more than 10% of income vs. not trading: 7.4% of personas with a view, 0.0% without. Positions > 2x the pure hedge: 29.4% with a view (by gamma: 0.5: 46%, 1: 45%, 2: 39%, 3: 33%, 4: 28%, 6: 19%, 8: 16%, 12: 9%).

### What capping the speculative tilt would do (12,800 personas with a view, uncapped)

Realized CE gain, % of income, when the market is right vs. when the person's own (unblended) view is right. Variants keep the market-belief position n_mkt and allow at most X * pure hedge of tilt on top; 'no-sell' floors the current advice at zero. Break-even = the probability the view must be right for the current advice to beat the variant on average.

| variant | mkt right: median | mkt right: p5 | mkt right: p1 | mkt right: mean | view right: median | view right: mean | break-even P(view right) |
|---|---|---|---|---|---|---|---|
| current advice | +0.000 | -0.222 | -0.395 | +0.236 | +0.425 | +1.441 |  |
| cap 0x pure | +0.134 | +0.000 | +0.000 | +0.433 | +0.000 | +0.442 | +0.164 |
| cap 0.25x pure | +0.127 | +0.000 | +0.000 | +0.413 | +0.000 | +0.686 | +0.190 |
| cap 0.5x pure | +0.102 | +0.000 | +0.000 | +0.374 | +0.000 | +0.878 | +0.196 |
| cap 1x pure | +0.000 | -0.000 | -0.001 | +0.284 | +0.000 | +1.160 | +0.144 |
| no-sell | +0.000 | -0.222 | -0.395 | +0.236 | +0.425 | +1.441 |  |

By confidence (mean delta % of income, market right / view right):

| conf | cap0: mkt/view | cap0.25: mkt/view | cap0.5: mkt/view | cap1: mkt/view |
|---|---|---|---|---|
| 0.2 | +0.070 / -0.790 | +0.058 / -0.562 | +0.044 / -0.418 | +0.026 / -0.245 |
| 0.4 | +0.141 / -0.982 | +0.123 / -0.737 | +0.093 / -0.548 | +0.039 / -0.282 |
| 0.6 | +0.205 / -1.054 | +0.184 / -0.805 | +0.142 / -0.601 | +0.050 / -0.292 |
| 0.8 | +0.258 / -1.081 | +0.236 / -0.831 | +0.184 / -0.623 | +0.057 / -0.294 |
| 1 | +0.306 / -1.087 | +0.283 / -0.837 | +0.225 / -0.627 | +0.066 / -0.293 |

Value of the whole tilt (current advice minus market-belief advice), mean % of income:

| occupation | tilt value if market right (% inc) | tilt value if view right (% inc) |
|---|---|---|
| rideshare | -0.133 | +0.762 |
| retiree | -0.062 | +0.495 |
| contractor | -0.183 | +1.076 |
| realtor | -0.319 | +1.362 |
| ad_freelancer | -0.176 | +1.053 |
| ski | -0.350 | +1.426 |
| recruiter | -0.254 | +1.272 |
| tech | -0.092 | +0.544 |

## A4. Edges of the domain

Gamma (savings 0, market belief, uncapped): contracts for three occupations, plus median CE % and pure hedge.

| gamma | rideshare | contractor | tech | ce_true_pct | pure_hedge | n_warnings |
|---|---|---|---|---|---|---|
| -1 | 0 | 0 | 0 | 0.000 | 0.000 | 1.000 |
| -0.5 | 0 | 0 | 0 | 0.000 | 0.000 | 1.000 |
| 0 | 0 | 0 | 0 | 0.000 | 0.000 | 1.000 |
| 0.001 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| 0.01 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| 0.05 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| 0.1 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| 0.25 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| 1 | 0 | 9160 | 0 | 0.058 | 4,629.345 | 1.000 |
| 4 | 3056 | 11633 | 3629 | 0.902 | 6,155.250 | 1.000 |
| 12 | 3410 | 4900 | 0 | 0.922 | 4,003.185 | 2.000 |
| 20 | 3234 | 2884 | 0 | 0.663 | 2,824.555 | 2.000 |
| 30 | 2813 | 1902 | 0 | 0.452 | 1,952.635 | 2.000 |
| 50 | 1963 | 1131 | 0 | 0.267 | 1,193.225 | 2.000 |
| 100 | 1004 | 562 | 0 | 0.132 | 593.412 | 2.000 |

Gamma with a pessimist view (+0.15 at 60%), median contracts across occupations:

| gamma | market | pess0.15c0.6 |
|---|---|---|
| -1 | 0 | 0 |
| -0.5 | 0 | 0 |
| 0 | 0 | 0 |
| 0.001 | 0 | 8,925 |
| 0.01 | 0 | 8,925 |
| 0.05 | 0 | 8,925 |
| 0.1 | 0 | 8,925 |
| 0.25 | 0 | 8,925 |
| 1 | 2,520 | 13,111 |
| 4 | 6,155 | 11,552 |
| 12 | 4,003 | 5,071 |
| 20 | 2,824 | 3,348 |
| 30 | 1,952 | 2,320 |
| 50 | 1,192 | 1,383 |
| 100 | 593 | 690 |

Wealth barely above the loss (savings 0, loss = 50-99.9% of income; 0 errors): median CE gain % of income:

| loss_frac | 0.5 | 2.0 | 4.0 | 8.0 |
|---|---|---|---|---|
| 0.5 | 0.15 | 1.33 | 2.07 | 1.47 |
| 0.8 | 0.85 | 2.67 | 1.73 | 0.63 |
| 0.9 | 1.09 | 2.55 | 0.91 | 0.32 |
| 0.95 | 1.05 | 1.87 | 0.46 | 0.16 |
| 0.99 | 0.66 | 0.49 | 0.09 | 0.00 |
| 0.999 | 0.24 | 0.03 | 0.00 | 0.00 |

median contracts:

| loss_frac | 0.5 | 2.0 | 4.0 | 8.0 |
|---|---|---|---|---|
| 0.5 | 8,074 | 12,680 | 10,558 | 5,996 |
| 0.8 | 14,742 | 9,590 | 5,038 | 2,430 |
| 0.9 | 10,655 | 5,114 | 2,528 | 1,215 |
| 0.95 | 5,718 | 2,584 | 1,264 | 607 |
| 0.99 | 1,218 | 518 | 253 | 0 |
| 0.999 | 124 | 25 | 0 | 0 |

Price of the protective side at the edges (uncapped; medians over occupations, gamma, savings):

| price | belief | contracts | cost_pct | ce_true_pct | errors |
|---|---|---|---|---|---|
| 0.01 | market | 0.000 | 0.000 | 0.000 | 0 |
| 0.01 | opt0.15c0.6 | 12,897.000 | 0.235 | 0.000 | 0 |
| 0.01 | pess0.15c0.6 | 15,409.000 | 0.243 | -0.002 | 0 |
| 0.02 | market | 0.000 | 0.000 | 0.000 | 0 |
| 0.02 | opt0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |
| 0.02 | pess0.15c0.6 | 14,667.500 | 0.465 | -0.005 | 0 |
| 0.03 | market | 0.000 | 0.000 | 0.000 | 0 |
| 0.03 | opt0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |
| 0.03 | pess0.15c0.6 | 14,583.500 | 0.683 | -0.007 | 0 |
| 0.97 | market | 0.000 | 0.000 | 0.000 | 0 |
| 0.97 | opt0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |
| 0.97 | pess0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |
| 0.98 | market | 0.000 | 0.000 | 0.000 | 0 |
| 0.98 | opt0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |
| 0.98 | pess0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |
| 0.99 | market | 0.000 | 0.000 | 0.000 | 0 |
| 0.99 | opt0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |
| 0.99 | pess0.15c0.6 | 0.000 | 0.000 | 0.000 | 0 |

Basis correlation at the edges (uncapped):

| basis | belief | contracts | pure | basis_used | clipped | ce_true_pct | ce_true_min_pct |
|---|---|---|---|---|---|---|---|
| 0 | market | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0 | opt0.15c0.6 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0 | pess0.15c0.6 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0.01 | market | 0.000 | 0.000 | 0.010 | 0.000 | 0.000 | 0.000 |
| 0.01 | opt0.15c0.6 | 0.000 | 0.000 | 0.010 | 0.000 | 0.000 | 0.000 |
| 0.01 | pess0.15c0.6 | 0.000 | 0.000 | 0.010 | 0.000 | 0.000 | -0.002 |
| 0.1 | market | 0.000 | 0.000 | 0.100 | 0.000 | 0.000 | 0.000 |
| 0.1 | opt0.15c0.6 | 0.000 | 0.000 | 0.100 | 0.000 | 0.000 | 0.000 |
| 0.1 | pess0.15c0.6 | 2,625.000 | 0.000 | 0.100 | 0.000 | -0.029 | -0.152 |
| 0.5 | market | 4,120.500 | 4,717.560 | 0.500 | 0.000 | 0.163 | 0.000 |
| 0.5 | opt0.15c0.6 | 0.000 | 4,717.560 | 0.500 | 0.000 | 0.000 | 0.000 |
| 0.5 | pess0.15c0.6 | 12,022.000 | 4,717.560 | 0.500 | 0.000 | -0.040 | -0.501 |
| 0.9 | market | 13,481.000 | 14,440.700 | 0.900 | 0.000 | 0.716 | 0.000 |
| 0.9 | opt0.15c0.6 | 0.000 | 14,440.700 | 0.900 | 0.000 | 0.000 | 0.000 |
| 0.9 | pess0.15c0.6 | 24,566.000 | 14,440.700 | 0.900 | 0.000 | -0.064 | -0.873 |
| 0.99 | market | 14,909.000 | 16,388.900 | 0.990 | 0.000 | 0.896 | 0.000 |
| 0.99 | opt0.15c0.6 | 0.000 | 16,388.900 | 0.990 | 0.000 | 0.000 | 0.000 |
| 0.99 | pess0.15c0.6 | 30,334.500 | 16,388.900 | 0.990 | 0.000 | -0.053 | -0.852 |
| 1 | market | 15,066.500 | 16,543.850 | 1.000 | 0.000 | 0.918 | 0.000 |
| 1 | opt0.15c0.6 | 0.000 | 16,543.850 | 1.000 | 0.000 | 0.000 | 0.000 |
| 1 | pess0.15c0.6 | 31,887.500 | 16,543.850 | 1.000 | 0.000 | -0.049 | -0.827 |

Price sweep (uncapped, market belief): median realized CE gain % of income by price:

| price | rideshare | retiree | contractor | realtor | ad_freelancer | ski | recruiter | tech |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.000 | 0.000 | 0.246 | 0.305 | 0.043 | 0.287 | 0.164 | 0.037 |
| 0.1 | 0.000 | 0.000 | 0.390 | 0.526 | 0.136 | 0.508 | 0.284 | 0.053 |
| 0.2 | 0.025 | 0.000 | 0.494 | 0.776 | 0.205 | 0.789 | 0.425 | 0.056 |
| 0.3 | 0.032 | 0.000 | 0.398 | 0.851 | 0.230 | 0.906 | 0.472 | 0.041 |
| 0.4 | 0.035 | 0.000 | 0.337 | 0.817 | 0.224 | 0.909 | 0.457 | 0.000 |
| 0.5 | 0.035 | 0.000 | 0.246 | 0.672 | 0.200 | 0.832 | 0.406 | 0.000 |
| 0.6 | 0.032 | 0.000 | 0.162 | 0.516 | 0.165 | 0.704 | 0.333 | 0.000 |
| 0.7 | 0.027 | 0.000 | 0.101 | 0.386 | 0.125 | 0.530 | 0.244 | 0.000 |
| 0.8 | 0.000 | 0.000 | 0.029 | 0.241 | 0.042 | 0.340 | 0.152 | 0.000 |
| 0.9 | 0.000 | 0.000 | 0.000 | 0.113 | 0.000 | 0.166 | 0.064 | 0.000 |

... and median cost % of income:

| price | rideshare | retiree | contractor | realtor | ad_freelancer | ski | recruiter | tech |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.00 | 0.00 | 0.78 | 1.08 | 0.31 | 1.07 | 0.84 | 0.17 |
| 0.1 | 0.00 | 0.00 | 1.26 | 1.81 | 1.16 | 2.04 | 1.56 | 0.22 |
| 0.2 | 0.56 | 0.00 | 2.17 | 3.23 | 2.02 | 3.36 | 2.43 | 0.25 |
| 0.3 | 0.82 | 0.00 | 2.80 | 4.36 | 2.56 | 4.82 | 3.21 | 0.26 |
| 0.4 | 1.08 | 0.00 | 3.12 | 5.39 | 2.84 | 5.98 | 4.03 | 0.00 |
| 0.5 | 1.33 | 0.00 | 3.24 | 6.10 | 3.05 | 7.04 | 4.58 | 0.00 |
| 0.6 | 1.58 | 0.00 | 2.20 | 6.50 | 3.16 | 7.89 | 4.67 | 0.00 |
| 0.7 | 1.81 | 0.00 | 2.21 | 6.80 | 3.24 | 8.62 | 4.36 | 0.00 |
| 0.8 | 0.00 | 0.00 | 0.89 | 7.03 | 1.22 | 9.06 | 4.46 | 0.00 |
| 0.9 | 0.00 | 0.00 | 0.00 | 5.12 | 0.00 | 7.04 | 3.24 | 0.00 |
