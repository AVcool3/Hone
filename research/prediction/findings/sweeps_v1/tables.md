# Sweep tables (78,480 personas, 32 input errors)

## A1. Who gets value (core sweep: 12,960 personas, market beliefs)

Per occupation, medians over gamma 0.25-12, savings 0-24 mo, income x0.5-2, loss share x0.5-1.5. 'cap' = shipped default (10% of OI, 3c slippage, flat book). CE figures are realized under Truth() (market and basis right).

| occupation | loss/income | coverage (cap) | CE gain $ (cap) | CE % inc (cap) | CE % inc p90 (cap) | > 0.5% inc (cap) | CE % inc (uncap) | > 0.5% inc (uncap) | ~0 (<0.05%) (cap) | cost % inc (uncap) |
|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 0.10 | 1.00 | 10.77 | 0.03 | 0.52 | 10.37 | 0.03 | 12.59 | 56.91 | 1.46 |
| retiree | 0.06 | 1.00 | 0.40 | 0.00 | 0.20 | 2.96 | 0.00 | 2.96 | 74.44 | 0.23 |
| contractor | 0.50 | 0.17 | 29.15 | 0.04 | 0.44 | 7.90 | 0.18 | 36.30 | 52.72 | 1.01 |
| realtor | 0.40 | 0.01 | 5.07 | 0.01 | 0.03 | 0.00 | 0.46 | 48.52 | 96.42 | 4.04 |
| ad_freelancer | 0.30 | 0.04 | 3.73 | 0.01 | 0.06 | 0.00 | 0.09 | 25.18 | 87.41 | 1.20 |
| ski | 0.35 | 0.00 | 0.91 | 0.00 | 0.01 | 0.00 | 0.48 | 49.26 | 100.00 | 5.44 |
| recruiter | 0.35 | 0.01 | 1.84 | 0.00 | 0.02 | 0.00 | 0.24 | 38.15 | 100.00 | 2.44 |
| tech | 0.50 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 100.00 | 0.76 |

Median realized CE gain, % of income, by gamma (capped (default), income x1, all savings/loss levels):

| occupation | 0.25 | 0.5 | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 12.0 |
|---|---|---|---|---|---|---|---|---|---|
| rideshare | 0.000 | 0.000 | 0.000 | 0.013 | 0.056 | 0.110 | 0.223 | 0.334 | 0.551 |
| retiree | 0.000 | 0.000 | 0.000 | 0.000 | 0.006 | 0.020 | 0.059 | 0.104 | 0.201 |
| contractor | 0.000 | 0.000 | 0.006 | 0.027 | 0.053 | 0.086 | 0.165 | 0.248 | 0.335 |
| realtor | 0.000 | 0.000 | 0.001 | 0.004 | 0.008 | 0.010 | 0.015 | 0.019 | 0.023 |
| ad_freelancer | 0.000 | 0.000 | 0.000 | 0.004 | 0.008 | 0.013 | 0.022 | 0.033 | 0.054 |
| ski | 0.000 | 0.000 | 0.001 | 0.002 | 0.003 | 0.004 | 0.006 | 0.008 | 0.010 |
| recruiter | 0.000 | 0.000 | 0.000 | 0.002 | 0.003 | 0.004 | 0.007 | 0.010 | 0.014 |
| tech | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Median realized CE gain, % of income, by gamma (uncapped, income x1, all savings/loss levels):

| occupation | 0.25 | 0.5 | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 12.0 |
|---|---|---|---|---|---|---|---|---|---|
| rideshare | 0.000 | 0.000 | 0.000 | 0.013 | 0.056 | 0.111 | 0.230 | 0.353 | 0.596 |
| retiree | 0.000 | 0.000 | 0.000 | 0.000 | 0.006 | 0.020 | 0.059 | 0.104 | 0.201 |
| contractor | 0.000 | 0.000 | 0.018 | 0.139 | 0.322 | 0.552 | 1.090 | 1.084 | 0.953 |
| realtor | 0.000 | 0.001 | 0.088 | 0.425 | 0.778 | 1.099 | 1.344 | 1.172 | 0.908 |
| ad_freelancer | 0.000 | 0.000 | 0.003 | 0.067 | 0.170 | 0.291 | 0.567 | 0.855 | 1.216 |
| ski | 0.000 | 0.002 | 0.099 | 0.457 | 0.826 | 1.163 | 1.618 | 1.540 | 1.215 |
| recruiter | 0.000 | 0.000 | 0.025 | 0.203 | 0.429 | 0.667 | 1.124 | 1.392 | 1.097 |
| tech | 0.000 | 0.000 | 0.000 | 0.008 | 0.032 | 0.049 | 0.045 | 0.041 | 0.036 |

Median realized CE gain, % of income, by savings months (uncapped, income x1, loss x1, all gammas):

| occupation | 0 | 1 | 3 | 6 | 12 | 24 |
|---|---|---|---|---|---|---|
| rideshare | 0.112 | 0.095 | 0.069 | 0.043 | 0.015 | 0.000 |
| retiree | 0.022 | 0.017 | 0.010 | 0.003 | 0.000 | 0.000 |
| contractor | 0.665 | 0.553 | 0.396 | 0.257 | 0.127 | 0.040 |
| realtor | 0.866 | 0.971 | 0.811 | 0.624 | 0.388 | 0.168 |
| ad_freelancer | 0.311 | 0.266 | 0.198 | 0.133 | 0.065 | 0.016 |
| ski | 1.114 | 1.018 | 0.851 | 0.660 | 0.418 | 0.187 |
| recruiter | 0.687 | 0.604 | 0.474 | 0.341 | 0.190 | 0.067 |
| tech | 0.033 | 0.037 | 0.040 | 0.026 | 0.009 | 0.000 |

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
| 1-3 | 1.1 | 0.4 | 0.0 | 0.0 |
| 3-6 | 7.4 | 5.6 | 2.3 | 0.2 |
| 6-12 | 14.8 | 12.3 | 8.8 | 3.5 |

Contracts / pure hedge (rho*L) by gamma (uncapped, market belief, savings 3 mo, income x1, loss x1). Basis (rho): rideshare 0.85, retiree 0.9, contractor 0.3, realtor 0.5, ad_freelancer 0.4, ski 0.6, recruiter 0.45, tech 0.15:

| occupation | 0.25 | 0.5 | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 12.0 |
|---|---|---|---|---|---|---|---|---|---|
| rideshare | 0.00 | 0.00 | 0.01 | 0.51 | 0.67 | 0.75 | 0.83 | 0.86 | 0.89 |
| retiree | 0.00 | 0.00 | 0.00 | 0.22 | 0.48 | 0.61 | 0.74 | 0.81 | 0.87 |
| contractor | 0.00 | 0.19 | 0.72 | 1.04 | 1.16 | 1.20 | 1.13 | 0.98 | 0.69 |
| realtor | 0.00 | 0.28 | 0.62 | 0.77 | 0.78 | 0.75 | 0.65 | 0.55 | 0.40 |
| ad_freelancer | 0.00 | 0.00 | 0.43 | 0.78 | 0.91 | 0.98 | 1.02 | 1.00 | 0.87 |
| ski | 0.00 | 0.28 | 0.62 | 0.77 | 0.78 | 0.77 | 0.69 | 0.60 | 0.45 |
| recruiter | 0.00 | 0.08 | 0.56 | 0.80 | 0.87 | 0.89 | 0.85 | 0.77 | 0.59 |
| tech | 0.00 | 0.00 | 0.05 | 0.38 | 0.43 | 0.41 | 0.33 | 0.27 | 0.18 |

Capped default: 24.0% of core personas are advised 0 contracts; 2.7% get > 0.5% of income; 83.5% get < 0.05%. Uncapped: 24.0% zero, 26.6% > 0.5%.

## A2. Liquidity policy (28,224 personas)

Flat book (segments.py's assumption): contracts never depend on max_slippage (max distinct sizes across slippage settings = 1); the OI share is the only lever.

Median share of uncapped CE gain retained, flat book, by OI share (slippage irrelevant):

| occupation | 0.05 | 0.10 | 0.25 | 0.50 | 1.00 | off |
|---|---|---|---|---|---|---|
| rideshare | 82.1 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| retiree | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| contractor | 12.4 | 23.9 | 52.4 | 83.6 | 100.0 | 100.0 |
| realtor | 0.7 | 1.4 | 3.4 | 6.8 | 13.3 | 18.9 |
| ad_freelancer | 5.4 | 5.4 | 5.4 | 5.4 | 5.4 | 5.4 |
| ski | 0.2 | 0.5 | 1.0 | 1.0 | 1.0 | 1.0 |
| recruiter | 0.5 | 1.0 | 2.6 | 5.2 | 6.1 | 6.1 |
| tech | 0.0 | 0.0 | 0.3 | 0.5 | 1.1 | 12.3 |

Ladder book (depth/4 per cent, 20c deep; fills walk the book): median % of uncapped CE retained, columns = OI share / slippage. Values > 100% mean the cap *beats* the uncapped advice, because uncapped advice ignores slippage:

| occupation | 0.05/1c | 0.05/3c | 0.05/10c | 0.10/1c | 0.10/3c | 0.10/10c | 0.25/1c | 0.25/3c | 0.25/10c | 0.50/1c | 0.50/3c | 0.50/10c | 1.00/1c | 1.00/3c | 1.00/10c | off/1c | off/3c | off/10c |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rideshare | 82.1 | 82.1 | 82.1 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| retiree | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| contractor | 12.4 | 12.4 | 12.4 | 23.9 | 23.9 | 23.9 | 49.2 | 49.2 | 49.2 | 60.9 | 62.0 | 62.0 | 60.9 | 62.8 | 64.1 | 60.9 | 62.8 | 55.2 |
| realtor | 0.7 | 0.7 | 0.7 | 1.4 | 1.4 | 1.4 | 3.4 | 3.4 | 3.4 | 6.7 | 6.7 | 6.7 | 8.3 | 10.5 | 10.5 | 8.3 | 14.1 | 19.6 |
| ad_freelancer | 2.3 | 3.3 | 3.1 | 2.3 | 3.3 | 3.2 | 2.3 | 3.3 | 2.8 | 2.3 | 3.3 | 2.8 | 2.3 | 3.3 | 2.8 | 2.3 | 3.3 | 2.8 |
| ski | 0.2 | 0.2 | 0.2 | 0.4 | 0.5 | 0.5 | 0.4 | 0.7 | 0.9 | 0.4 | 0.7 | 1.2 | 0.4 | 0.7 | 1.2 | 0.4 | 0.7 | 1.2 |
| recruiter | 0.5 | 0.5 | 0.5 | 1.0 | 1.0 | 1.0 | 2.0 | 2.0 | 2.0 | 2.3 | 3.3 | 3.3 | 2.3 | 3.7 | 4.4 | 2.3 | 3.7 | 4.7 |
| tech | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.3 | 0.3 | 0.3 | 0.5 | 0.5 | 0.5 | 1.1 | 1.1 | 1.1 | 3.9 | 4.3 | -12.9 |

Ladder book, 3c slippage: median realized CE gain ($) by OI share:

| occupation | 0.05 | 0.10 | 0.25 | 0.50 | 1.00 | off |
|---|---|---|---|---|---|---|
| rideshare | 36.7 | 49.2 | 47.1 | 47.1 | 47.1 | 47.1 |
| retiree | 7.9 | 7.9 | 7.9 | 7.9 | 7.9 | 7.9 |
| contractor | 39.2 | 75.6 | 167.2 | 253.4 | 255.1 | 255.1 |
| realtor | 4.9 | 9.8 | 24.4 | 47.3 | 88.1 | 118.5 |
| ad_freelancer | 6.8 | 6.8 | 6.8 | 6.8 | 6.8 | 6.8 |
| ski | 0.8 | 1.7 | 3.0 | 3.0 | 3.0 | 3.0 |
| recruiter | 2.0 | 4.1 | 9.9 | 17.9 | 20.4 | 20.4 |
| tech | 0.0 | 0.0 | 0.1 | 0.3 | 0.6 | 3.3 |

Ladder book: the policy with the highest mean realized CE gain per occupation:

| occupation | oi | slippage | ce_gain_true |
|---|---|---|---|
| rideshare | off | 0.10 | 105.21 |
| retiree | 0.10 | 0.01 | 28.84 |
| contractor | 1.00 | 0.03 | 403.07 |
| realtor | off | 0.10 | 186.90 |
| ad_freelancer | 0.10 | 0.10 | 18.61 |
| ski | 1.00 | 0.10 | 6.15 |
| recruiter | off | 0.10 | 46.31 |
| tech | off | 0.03 | 3.24 |

Ladder book, no OI cap, 10c slippage: median position = 0.5x open interest (p90 28.9x).

## A3. Failure modes

Counts over the core, liquidity, beliefs and prices sweeps. f_sell = sells the protective side while exposed; f_cost25 = cost > 25% of income; f_over_res = buys with the quoted price above the reservation price; f_fill_over_res = buys with the average *fill* price above it; f_ce_model_neg / f_ce_true_neg = negative CE gain by the model's own numbers / under Truth(); f_ce_true_neg_mkt = same, among personas with no view; f_tiny = a non-zero trade worth < $1.

| sweep | f_sell | f_cost25 | f_over_res | f_fill_over_res | f_ce_model_neg | f_ce_true_neg | f_ce_true_neg_mkt | f_tiny | n |
|---|---|---|---|---|---|---|---|---|---|
| beliefs | 6368 | 2211 | 0 | 0 | 70 | 11879 | 4 | 2674 | 26112 |
| core | 0 | 0 | 0 | 0 | 69 | 69 | 69 | 1571 | 12960 |
| liquidity | 0 | 0 | 0 | 343 | 993 | 993 | 993 | 4139 | 28224 |
| prices | 1460 | 393 | 0 | 0 | 49 | 2778 | 26 | 1133 | 8640 |
| all | 7828 | 2604 | 0 | 343 | 1181 | 15719 | 1092 | 9517 | 75936 |

Sells while exposed (beliefs sweep): 6,368 of 26,112; all are optimists (100%); median confidence 0.8, median shift 0.20, median gamma 2.0. Median sold position = 0.73x the pure hedge; realized CE when the market is right: median -0.34% of income (p10 -8.06%). By occupation: rideshare 872, retiree 1104, contractor 772, realtor 518, ad_freelancer 936, ski 492, recruiter 714, tech 960

Cost > 25% of income: 2,604 personas, 15% in the price sweep; median price 0.35, median cost 47% of income; 100% hold a view. Occupations: ad_freelancer 378, retiree 355, contractor 338, rideshare 325, ski 323, recruiter 323, realtor 299, tech 263

Negative realized CE with market beliefs: 1,092; median -2.25 $, min -555.08 $. Liquidity: oioff_slip0.10_ladder 165, oioff_slip0.05_ladder 84, oi1.00_slip0.10_ladder 82, oi0.10_slip0.03_flat 81

Negative CE by the model's own accounting: 1,181; 4% sells, 79% on the ladder book, median -1.42 $, worst -555 $.

Buying above the reservation price at the quote: 0 personas; at the average fill: 343 (all on the ladder book: 343); their median realized CE -8.05 $, worst -531 $.

Non-zero trades worth < $1 of CE: 9,517 (12.5%); median size 13 contracts; 90.4% of them are capped. Negative model CE among market-belief, flat-book personas is fee rounding: worst -0.009 $.

### Instability (1% input perturbations)

8,000 sampled personas x up to 12 perturbations = 89,679 re-runs. Unstable = direction flip, on/off switch (>= 3 contracts), or a change >= max(3, 10%) of the position from a 1% input move (elasticity > 10). 5.6% of personas are unstable to at least one 1% perturbation.

| input | has_view | n | unstable_pct | jump_pct | onoff_pct | flip_pct | median_abs_elasticity | p99_abs_elasticity |
|---|---|---|---|---|---|---|---|---|
| basis | False | 5488 | 1.35 | 1.35 | 0.24 | 0.00 | 1.08 | 20.15 |
| basis | True | 10512 | 1.75 | 1.75 | 0.41 | 0.00 | 0.10 | 18.32 |
| conf | True | 9679 | 2.05 | 2.05 | 0.49 | 0.00 | 0.17 | 24.77 |
| gamma | False | 5488 | 1.31 | 1.31 | 0.24 | 0.00 | 0.17 | 19.23 |
| gamma | True | 10512 | 1.65 | 1.65 | 0.41 | 0.00 | 0.25 | 18.41 |
| loss | False | 5488 | 1.44 | 1.44 | 0.24 | 0.00 | 0.65 | 21.15 |
| loss | True | 10512 | 1.82 | 1.82 | 0.44 | 0.00 | 0.05 | 20.57 |
| price | False | 5488 | 0.04 | 0.04 | 0.00 | 0.00 | 0.05 | 1.85 |
| price | True | 10512 | 6.57 | 6.57 | 0.99 | 0.00 | 0.70 | 87.94 |
| wealth | False | 5488 | 1.40 | 1.40 | 0.24 | 0.00 | 0.20 | 20.17 |
| wealth | True | 10512 | 1.78 | 1.78 | 0.44 | 0.00 | 0.30 | 21.10 |

Value at stake where it happens: median base CE gain 0.00 $ (p90 27.37 $) vs 0.59 $ for all sampled; 19.8% of unstable re-runs straddle the 0-contract entry threshold. Without a view, 100.0% of unstable cases are worth < $5.

Unstable re-runs by occupation: rideshare 328, retiree 386, contractor 272, realtor 188, ad_freelancer 206, ski 161, recruiter 199, tech 188. By liquidity: capped 604, uncapped 1324.

### How much of the position is speculation? (beliefs sweep, uncapped)

Tilt = n*(with view) - n*(market belief), in units of the pure hedge rho*L. For market-belief personas the model's own 'speculative_contracts' (n* - rho*L) is still -0.37x the pure hedge at the median (p10 -1.00, p90 -0.06) — fees and CRRA skew, not a view.

Median tilt / pure hedge, by gamma:

| gamma | optimist | pessimist |
|---|---|---|
| 0.5 | -5.01 | 7.94 |
| 1 | -2.58 | 4.16 |
| 2 | -1.21 | 2.08 |
| 3 | -0.85 | 1.33 |
| 4 | -0.75 | 0.98 |
| 6 | -0.55 | 0.59 |
| 8 | -0.41 | 0.41 |
| 12 | -0.23 | 0.25 |

Median tilt / pure hedge, by view strength = |shift| x confidence (blended move in probability):

| strength | optimist | pessimist |
|---|---|---|
| 0.01 | -0.09 | 0.15 |
| 0.02 | -0.20 | 0.35 |
| 0.03 | -0.35 | 0.53 |
| 0.04 | -0.47 | 0.70 |
| 0.05 | -0.65 | 0.88 |
| 0.06 | -0.70 | 1.06 |
| 0.08 | -0.96 | 1.40 |
| 0.09 | -1.16 | 1.57 |
| 0.1 | -1.47 | 1.74 |
| 0.12 | -1.55 | 2.02 |
| 0.15 | -2.59 | 2.54 |
| 0.16 | -2.51 | 2.71 |
| 0.18 | -2.34 | 3.03 |
| 0.2 | -3.60 | 3.33 |
| 0.24 | -3.62 | 3.96 |
| 0.3 | -5.29 | 4.98 |

Median tilt / pure hedge, by occupation:

| occupation | optimist | pessimist |
|---|---|---|
| rideshare | -0.87 | 1.69 |
| retiree | -1.86 | 2.67 |
| contractor | -1.08 | 1.59 |
| realtor | -0.48 | 0.55 |
| ad_freelancer | -1.23 | 1.54 |
| ski | -0.45 | 0.53 |
| recruiter | -0.74 | 0.86 |
| tech | -0.58 | 1.30 |

Median share of the gross position that is speculative, |tilt| / (|n_mkt| + |tilt|): rideshare 69%, retiree 87%, contractor 53%, realtor 44%, ad_freelancer 64%, ski 43%, recruiter 50%, tech 75%.

Worst-state wealth falls by more than 10% of income vs. not trading: 36.0% of personas with a view, 0.0% without. Positions > 2x the pure hedge: 37.1% with a view (by gamma: 0.5: 79%, 1: 66%, 2: 48%, 3: 38%, 4: 28%, 6: 18%, 8: 13%, 12: 7%).

### What capping the speculative tilt would do (12,800 personas with a view, uncapped)

Realized CE gain, % of income, when the market is right vs. when the person's own (unblended) view is right. Variants keep the market-belief position n_mkt and allow at most X * pure hedge of tilt on top; 'no-sell' floors the current advice at zero. Break-even = the probability the view must be right for the current advice to beat the variant on average.

| variant | mkt right: median | mkt right: p5 | mkt right: p1 | mkt right: mean | view right: median | view right: mean | break-even P(view right) |
|---|---|---|---|---|---|---|---|
| current advice | -0.123 | -14.023 | -37.398 | -2.405 | +1.795 | +5.029 |  |
| cap 0x pure | +0.134 | +0.000 | +0.000 | +0.433 | +0.000 | +0.442 | +0.382 |
| cap 0.25x pure | +0.122 | -0.047 | -0.107 | +0.394 | +0.358 | +0.849 | +0.401 |
| cap 0.5x pure | +0.080 | -0.115 | -0.268 | +0.329 | +0.558 | +1.167 | +0.415 |
| cap 1x pure | -0.035 | -0.462 | -0.759 | +0.179 | +0.941 | +1.635 | +0.432 |
| no-sell | +0.000 | -6.504 | -24.381 | -0.983 | +0.534 | +3.497 | +0.481 |

By confidence (mean delta % of income, market right / view right):

| conf | cap0: mkt/view | cap0.25: mkt/view | cap0.5: mkt/view | cap1: mkt/view |
|---|---|---|---|---|
| 0.2 | +0.217 / -1.804 | +0.195 / -1.430 | +0.170 / -1.183 | +0.136 / -0.903 |
| 0.4 | +0.958 / -3.658 | +0.925 / -3.251 | +0.874 / -2.935 | +0.775 / -2.484 |
| 0.6 | +2.211 / -5.074 | +2.171 / -4.659 | +2.102 / -4.321 | +1.945 / -3.805 |
| 0.8 | +4.024 / -6.004 | +3.978 / -5.586 | +3.894 / -5.241 | +3.687 / -4.698 |
| 1 | +6.779 / -6.393 | +6.729 / -5.975 | +6.633 / -5.628 | +6.380 / -5.078 |

Value of the whole tilt (current advice minus market-belief advice), mean % of income:

| occupation | tilt value if market right (% inc) | tilt value if view right (% inc) |
|---|---|---|
| rideshare | -2.728 | +4.266 |
| retiree | -3.340 | +4.972 |
| contractor | -2.835 | +5.849 |
| realtor | -2.373 | +3.913 |
| ad_freelancer | -3.646 | +5.524 |
| ski | -2.312 | +3.857 |
| recruiter | -3.278 | +4.904 |
| tech | -2.190 | +3.409 |

## A4. Edges of the domain

Gamma (savings 0, market belief, uncapped): contracts for three occupations, plus median CE % and pure hedge.

| gamma | rideshare | contractor | tech | ce_true_pct | pure_hedge | n_warnings |
|---|---|---|---|---|---|---|
| -1 | 3,825.000 | 10,500.000 | 11,250.000 | -0.239 | 8,925.000 | 3.000 |
| -0.5 | 3,825.000 | 10,500.000 | 11,250.000 | -0.190 | 8,925.000 | 3.000 |
| 0 | 3,825.000 | 10,500.000 | 11,250.000 | -0.140 | 8,925.000 | 2.000 |
| 0.001 | 0.000 | 0.000 | 0.000 | 0.000 | 8,925.000 | 0.000 |
| 0.01 | 0.000 | 0.000 | 0.000 | 0.000 | 8,925.000 | 0.000 |
| 0.05 | 0.000 | 0.000 | 0.000 | 0.000 | 8,925.000 | 0.000 |
| 0.1 | 0.000 | 0.000 | 0.000 | 0.000 | 8,925.000 | 0.000 |
| 0.25 | 0.000 | 0.000 | 0.000 | 0.000 | 8,925.000 | 0.000 |
| 1 | 837.000 | 9,160.000 | 2,582.000 | 0.081 | 8,925.000 | 1.000 |
| 4 | 3,057.000 | 11,634.000 | 3,629.000 | 0.902 | 8,925.000 | 1.000 |
| 12 | 3,410.000 | 4,901.000 | 1,386.000 | 0.922 | 8,925.000 | 1.000 |
| 20 | 3,235.000 | 2,884.000 | 832.000 | 0.663 | 8,925.000 | 1.000 |
| 30 | 2,814.000 | 1,902.000 | 555.000 | 0.452 | 8,925.000 | 1.000 |
| 50 | 1,963.000 | 1,132.000 | 333.000 | 0.267 | 8,925.000 | 1.000 |
| 100 |  |  |  |  |  |  |

Gamma with a pessimist view (+0.15 at 60%), median contracts across occupations:

| gamma | market | pess0.15c0.6 |
|---|---|---|
| -1 | 8,925 | 8,925 |
| -0.5 | 8,925 | 8,925 |
| 0 | 8,925 | 8,925 |
| 0.001 | 0 | 124,061 |
| 0.01 | 0 | 124,061 |
| 0.05 | 0 | 124,061 |
| 0.1 | 0 | 123,034 |
| 0.25 | 0 | 89,278 |
| 1 | 4,629 | 32,263 |
| 4 | 6,155 | 11,552 |
| 12 | 4,003 | 5,071 |
| 20 | 2,824 | 3,348 |
| 30 | 1,952 | 2,320 |
| 50 | 1,193 | 1,384 |

Wealth barely above the loss (savings 0, loss = 50-99.9% of income; 0 errors): median CE gain % of income:

| loss_frac | 0.5 | 2.0 | 4.0 | 8.0 |
|---|---|---|---|---|
| 0.5 | 0.15 | 1.33 | 2.07 | 1.47 |
| 0.8 | 0.85 | 2.67 | 1.73 | 0.63 |
| 0.9 | 1.09 | 2.55 | 0.91 | 0.32 |
| 0.95 | 1.05 | 1.87 | 0.46 | 0.16 |
| 0.99 | 0.66 | 0.49 | 0.09 | 0.03 |
| 0.999 | 0.24 | 0.05 | 0.01 | 0.00 |

median contracts:

| loss_frac | 0.5 | 2.0 | 4.0 | 8.0 |
|---|---|---|---|---|
| 0.5 | 8,074 | 12,681 | 10,559 | 5,997 |
| 0.8 | 14,742 | 9,590 | 5,038 | 2,430 |
| 0.9 | 10,678 | 5,114 | 2,529 | 1,215 |
| 0.95 | 5,761 | 2,585 | 1,264 | 608 |
| 0.99 | 1,230 | 518 | 253 | 122 |
| 0.999 | 126 | 52 | 26 | 12 |

Price of the protective side at the edges (uncapped; medians over occupations, gamma, savings):

| price | belief | contracts | cost_pct | ce_true_pct | errors |
|---|---|---|---|---|---|
| 0.01 | market | 5,512.500 | 0.100 | 0.009 | 0 |
| 0.01 | opt0.15c0.6 | 33,108.500 | 0.520 | -0.078 | 0 |
| 0.01 | pess0.15c0.6 | 177,463.500 | 3.497 | -2.363 | 0 |
| 0.02 | market | 5,474.500 | 0.200 | 0.017 | 0 |
| 0.02 | opt0.15c0.6 | 5,474.500 | 0.200 | 0.017 | 0 |
| 0.02 | pess0.15c0.6 | 113,478.500 | 4.445 | -2.484 | 0 |
| 0.03 | market | 5,393.500 | 0.298 | 0.025 | 0 |
| 0.03 | opt0.15c0.6 | 0.000 | 0.633 | 0.000 | 0 |
| 0.03 | pess0.15c0.6 | 87,301.000 | 5.060 | -2.429 | 0 |
| 0.97 | market | 2,138.000 | 3.701 | 0.005 | 0 |
| 0.97 | opt0.15c0.6 | -60,357.000 | 3.648 | -2.055 | 0 |
| 0.97 | pess0.15c0.6 | 10,859.000 | 16.603 | -0.036 | 0 |
| 0.98 | market | 2,111.000 | 3.724 | 0.004 | 0 |
| 0.98 | opt0.15c0.6 | -83,148.000 | 3.330 | -2.096 | 0 |
| 0.98 | pess0.15c0.6 | 2,111.000 | 3.724 | 0.004 | 0 |
| 0.99 | market | 2,092.000 | 3.742 | 0.002 | 0 |
| 0.99 | opt0.15c0.6 | -137,661.500 | 2.736 | -1.989 | 0 |
| 0.99 | pess0.15c0.6 | -9,698.500 | 0.276 | -0.055 | 0 |

Basis correlation at the edges (uncapped):

| basis | belief | contracts | pure | basis_used | clipped | ce_true_pct | ce_true_min_pct |
|---|---|---|---|---|---|---|---|
| 0 | market | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 0 | opt0.15c0.6 | -13,338.000 | 0.000 | 0.000 | 0.000 | -1.420 | -10.853 |
| 0 | pess0.15c0.6 | 12,381.500 | 0.000 | 0.000 | 0.000 | -1.099 | -14.599 |
| 0.01 | market | 0.000 | 221.250 | 0.010 | 0.000 | 0.000 | 0.000 |
| 0.01 | opt0.15c0.6 | -13,302.500 | 221.250 | 0.010 | 0.000 | -1.409 | -10.831 |
| 0.01 | pess0.15c0.6 | 12,498.000 | 221.250 | 0.010 | 0.000 | -1.100 | -14.608 |
| 0.1 | market | 0.000 | 2,212.500 | 0.100 | 0.000 | 0.000 | 0.000 |
| 0.1 | opt0.15c0.6 | -11,040.000 | 2,212.500 | 0.100 | 0.000 | -1.299 | -10.667 |
| 0.1 | pess0.15c0.6 | 14,413.000 | 2,212.500 | 0.100 | 0.000 | -1.086 | -14.683 |
| 0.5 | market | 4,717.500 | 11,062.500 | 0.500 | 0.000 | 0.163 | 0.000 |
| 0.5 | opt0.15c0.6 | -4,792.000 | 11,062.500 | 0.500 | 0.000 | -0.673 | -10.298 |
| 0.5 | pess0.15c0.6 | 24,798.500 | 11,062.500 | 0.500 | 0.000 | -0.813 | -14.999 |
| 0.9 | market | 14,440.500 | 19,912.500 | 0.900 | 0.000 | 0.716 | 0.000 |
| 0.9 | opt0.15c0.6 | -663.500 | 19,912.500 | 0.900 | 0.000 | -0.139 | -10.121 |
| 0.9 | pess0.15c0.6 | 33,209.000 | 19,912.500 | 0.900 | 0.000 | -0.468 | -15.297 |
| 0.99 | market | 16,389.000 | 21,903.750 | 0.990 | 0.000 | 0.896 | 0.000 |
| 0.99 | opt0.15c0.6 | -197.500 | 21,903.750 | 0.990 | 0.000 | -0.047 | -10.089 |
| 0.99 | pess0.15c0.6 | 39,475.000 | 21,903.750 | 0.990 | 0.000 | -0.352 | -15.363 |
| 1 | market | 16,544.000 | 22,125.000 | 1.000 | 0.000 | 0.918 | 0.000 |
| 1 | opt0.15c0.6 | -136.000 | 22,125.000 | 1.000 | 0.000 | -0.033 | -10.086 |
| 1 | pess0.15c0.6 | 41,282.500 | 22,125.000 | 1.000 | 0.000 | -0.338 | -15.370 |

Price sweep (uncapped, market belief): median realized CE gain % of income by price:

| price | rideshare | retiree | contractor | realtor | ad_freelancer | ski | recruiter | tech |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.015 | 0.002 | 0.246 | 0.305 | 0.078 | 0.287 | 0.164 | 0.059 |
| 0.1 | 0.028 | 0.004 | 0.390 | 0.526 | 0.136 | 0.508 | 0.284 | 0.087 |
| 0.2 | 0.049 | 0.007 | 0.494 | 0.776 | 0.205 | 0.789 | 0.425 | 0.096 |
| 0.3 | 0.062 | 0.009 | 0.398 | 0.851 | 0.230 | 0.906 | 0.472 | 0.075 |
| 0.4 | 0.068 | 0.010 | 0.337 | 0.817 | 0.224 | 0.909 | 0.457 | 0.051 |
| 0.5 | 0.068 | 0.010 | 0.246 | 0.672 | 0.200 | 0.832 | 0.406 | 0.034 |
| 0.6 | 0.063 | 0.009 | 0.162 | 0.516 | 0.165 | 0.704 | 0.333 | 0.022 |
| 0.7 | 0.053 | 0.008 | 0.101 | 0.386 | 0.125 | 0.530 | 0.244 | 0.013 |
| 0.8 | 0.039 | 0.006 | 0.057 | 0.241 | 0.082 | 0.340 | 0.152 | 0.007 |
| 0.9 | 0.021 | 0.003 | 0.024 | 0.113 | 0.040 | 0.166 | 0.071 | 0.002 |

... and median cost % of income:

| price | rideshare | retiree | contractor | realtor | ad_freelancer | ski | recruiter | tech |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.28 | 0.11 | 0.78 | 1.08 | 0.61 | 1.07 | 0.84 | 0.44 |
| 0.1 | 0.56 | 0.22 | 1.32 | 1.81 | 1.16 | 2.04 | 1.56 | 0.64 |
| 0.2 | 1.11 | 0.43 | 2.17 | 3.23 | 2.02 | 3.36 | 2.43 | 0.76 |
| 0.3 | 1.64 | 0.64 | 2.80 | 4.36 | 2.56 | 4.82 | 3.21 | 0.84 |
| 0.4 | 2.15 | 0.83 | 3.12 | 5.39 | 2.84 | 5.98 | 4.03 | 0.86 |
| 0.5 | 2.65 | 1.02 | 3.24 | 6.10 | 3.05 | 7.05 | 4.59 | 0.84 |
| 0.6 | 3.13 | 1.20 | 3.30 | 6.50 | 3.29 | 7.89 | 5.03 | 0.79 |
| 0.7 | 3.59 | 1.37 | 3.32 | 6.80 | 3.52 | 8.62 | 5.38 | 0.72 |
| 0.8 | 4.04 | 1.54 | 3.32 | 7.03 | 3.75 | 9.06 | 5.67 | 0.64 |
| 0.9 | 4.48 | 1.69 | 3.30 | 7.20 | 3.93 | 9.41 | 5.90 | 0.60 |
