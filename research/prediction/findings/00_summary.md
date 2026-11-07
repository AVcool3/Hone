# Income hedge: what the studies found and what changed

Five studies ran in parallel (November 2026), each in its own file here.
The resulting model is specified in [docs/HEDGE_MODEL.md](../../../docs/HEDGE_MODEL.md),
and its lessons are pinned in `tests/test_hedge_scenarios.py`.

| # | Study | Headline |
|---|---|---|
| 01 | Research (rules, literature, alternatives) | Kalshi's limits don't bind a retail hedger; liquidity does. Index insurance fails on basis risk; demand is hump-shaped in risk aversion. Selling a payout yourself is insurance or a swap, and both are regulated. |
| 02 | Backtest, 2,822 settled Kalshi markets | Prices are well calibrated, but buying the protective side lost 7–19¢ a contract. The old page wiring told hedgers to sell their protection, which wiped out several personas. Measured basis: gas 0.52–0.68, CPI about 0.8, unemployment vs. one person's job 0.02. |
| 03 | Segment sweep, 78,480 personas | At a 10% open-interest cap almost nobody benefited. Half of optimists were told to sell. Views were 2–8× the insurance part. 12.5% of trades were worth under $1. |
| 04 | Property tests | 14 engine bugs, the worst shrinking full-basis hedges about 10×. All are fixed and kept as regression tests. |
| 05 | Model-wrong stress test | Tested a capped view, no selling, basis × 0.75 and a 1¢ buffer together. People hurt fell from 43% to 10%; average harm fell from $216 to $18. |
| 06 | Vail Resorts' filings, 22 seasons | A bad snow year costs ~10–13% of visits but only 5–8% of revenue, because 40–70% is pre-sold passes. The quote engine's sensitivities, pass discount and loss caps are now calibrated on this. |
| 07 | Snow risk at 30 resorts | The weather grid and the mountain station agree on how winters rank (0.81) but catch only 55% of each other's bad winters; quotes now price from the station. Colorado and the Alps are losing snow significantly. |

## Effect on the same 78,480 personas

| | Before (v1) | Now (v2) |
|---|---|---|
| Crashes | 32 | 0 |
| Told to sell protection they need | 10.5% | 0% |
| Trades worth under $1 | 14.8% | 0% |
| With a view: hurt if the market was right | 46.4% | 4.7% |
| With a view: worst outcome | −133% of income | −0.05% |
| Gain more than 0.5% of income | 14.6% | 9.8% |
| Proposed nothing | 24% | 79% |

v1's summary tables are in `sweeps_v1/`; its raw persona data is in git
history. Rerun the current tables with `python research/prediction/sweeps.py`.
One table of that report still assumes every occupation trades, so it
errors under v2 after saving the data. The headline table above was
computed from the saved CSVs.

## The honest bottom line

The model now protects people from bad advice. It says "don't trade" to
most of them because fees, thin markets and realistic basis leave little
value on Kalshi for a typical worker. The value concentrates in large
exposures relative to savings, deep markets (inflation, gas), and
businesses. That is the case for Hone pricing protection itself (the quote
engine) rather than depending on Kalshi's depth.
