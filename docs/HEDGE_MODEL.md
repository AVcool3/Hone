# The income-hedge model, in one page

This is the complete specification of how Hone sizes an income hedge. The
code is in `hone/prediction/hedge.py`; every rule below names the constant
that controls it and the study that justified it. The studies are in
`research/prediction/findings/`:

| File | What it did |
|---|---|
| 01_research.md | Kalshi rules, index-insurance literature, alternatives |
| 02_history.md | Backtest on 2,822 settled Kalshi markets |
| 03_segments.md | 78,480 simulated people across 8 occupations |
| 04_properties.md | Adversarial property tests (found 14 engine bugs) |
| 05_misspecification.md | What happens when the model's assumptions are wrong |

## What goes in

| Input | Meaning |
|---|---|
| `wealth` | Money available over the season: earnings plus savings. For a business, cash reserves plus a normal season's profit. |
| `loss` | Dollars lost in a bad season. |
| `price` | What the protective contract costs (the ask). |
| `market_prob` | The market's probability (the midpoint). Kalshi prices are well calibrated (02: Brier 0.109, slope 1.01), so this is trusted. |
| `own_prob`, `confidence` | Optional: your own view, and how sure you are. |
| `basis_correlation` | How closely the contract tracks *your* loss, from 0 to 1. |
| `loss_prob` | Optional: your own chance of a bad outcome, when it differs from the contract's event. For example, a layoff is rarer than "unemployment above 4.5%". |
| `gamma` | Your risk aversion, from Hone's questionnaire. |
| `liquidity` | Open interest and the order book (looked up by ticker). |

## How the size is chosen

1. **Insurance at the market's odds.** Hone finds the position that maximizes
   your expected CRRA utility if the market price is the true probability.
   That position is the hedge.
2. **Your view, capped.** If you gave a view, Hone also finds the position
   that is best at your own probability. The difference from step 1 is a bet
   on your view, so for anyone with income at risk it is limited to
   `MAX_VIEW_TILT` = **0.25×** the insurance part.
   - **Why:** views were 2 to 8 times the insurance part, and an overconfident
     user could lose up to 107% of income (03, 05).
   - **Cost:** at 0.25 you keep about 48% of the view's value when it is
     right, against 50% with no tighter limit.
3. **No selling for hedgers.** Someone with income at risk is never told to
   sell their protection (`allow_selling` = automatic).
   - **Why:** half of optimists were told to sell (03). At real prices, the old
     wiring told drivers and retirees to sell, and some were wiped out (02).
4. **What the market can supply.** The order book is walked contract by
   contract, at what each contract really costs. The position is capped at
   the smaller of two limits:
   - the depth within `max_slippage` (3¢) of the best price;
   - `DEFAULT_MAX_SHARE_OF_OI` (**25%**) of open interest.

   The sweep (03) found that 10% gave up most of the value in thin markets
   and left deep markets unaffected.
5. **Safety margins, for choosing the size only.** The size is chosen as if:
   - the contract tracked you `BASIS_SHRINK` = **0.75×** as closely as stated
     (people overestimate this);
   - every contract cost `PRICE_BUFFER` = **1¢** more (slippage, stale
     quotes, market bias).

   Every dollar figure shown still uses the real price and your stated
   inputs.
   - **Why:** the share of people hurt by a wrong model fell from 24% to 10%,
     and the average harm fell about 4×, for about 19% less value when the
     model is exactly right (05).
6. **Not worth it.** If the best position is worth less than
   `max(MIN_WORTH_DOLLARS, MIN_WORTH_FRAC × wealth)` ($5 or 0.05%), Hone
   proposes nothing and says why. 12.5% of the old positions were worth
   under $1 (03).
7. **Whole contracts.** The size is rounded to whichever neighbouring whole
   number is worth more (fees round to the cent), and it stays solvent in
   every outcome that can actually happen.

The optimum is found by solving the first-order condition, where one more
contract adds zero value, by bisection. This is exact. Searching the utility
itself was not exact, because it is flat to 16 digits on large portfolios
(04).

## What comes out

For each plan Hone reports:
- **The proposed position** (contracts, direction, cost, fee, and the average
  fill price).
- **The ideal size** before liquidity limits, and **coverage**, the share of
  the ideal that the market can supply.
- **Insurance part and view part**, plus a reference size: one contract per
  dollar at risk, scaled by basis.
- **Value to you:** the certainty-equivalent gain, the most worth paying per
  contract, and the worst outcome and typical swing with and without the
  hedge.
- **A plain-English warning for every rule that changed the answer.**

## What the evidence says about who it helps

- **Deep markets only.** Inflation and gas markets can supply a meaningful
  share of one person's hedge. Unemployment markets supply about 11%. Most
  others supply 0–2%.
- **Big exposure relative to savings.** For a typical driver ($4.5k at risk
  on $56k), insurance is worth about $26 a year. Kalshi's fee eats most of
  that, so Hone proposes nothing. A full-time driver with no savings and
  $9k at risk gains about $700.
- **Tracking matters more than anything.** Measured upper bounds (02):
  - gas vs. a driver's fuel costs: 0.52–0.68;
  - CPI vs. a retiree's purchasing power: about 0.8;
  - national unemployment vs. one person's job: **0.02**.

  The page's defaults now use these numbers. Labor-market contracts can't
  hedge an individual's job.
- **Basis risk makes demand hump-shaped.** The most risk-averse people buy
  *less* index insurance, because a bad season without a payout gets worse
  with every dollar of premium (Clarke 2016). The engine reproduces this and
  explains it to the user.
- **Protection has been expensive.** Buying the protective side at the ask
  lost 7–19¢ per contract historically (02). That is the insurance premium.

Across the 78,480 simulated people, the effect of these rules (03, rerun):

| | Before | Now |
|---|---|---|
| Crashes | 32 | 0 |
| Told to sell protection they need | 10.5% | 0% |
| Trades worth under $1 | 14.8% | 0% |
| With a view, hurt if the market was right | 46.4% | 4.7% |
| With a view, worst outcome | −133% of income | −0.05% of income |
| Gain more than 0.5% of income | 14.6% | 9.8% |
| Proposed nothing | 24% | 79% |

## Known limits

- **One period, one binary event.** Continuous losses would be better
  served by ladders of strikes (02).
- **Liquidity is a snapshot.** Open interest 28 days before close is 5–20×
  thinner than a week before (02).
- **The safety margins are a policy choice,** tuned on simulated people.
  Change the constants, then rerun `research/prediction/sweeps.py` and
  `research/prediction/misspecification.py` to see the trade-off.
- **Hone sizes and explains; it never trades.** Selling a payout to a
  customer is insurance or a swap, and both are regulated (01).

## The scenario suite

`tests/test_hedge_scenarios.py` writes each lesson above as a person
(a driver, a ski instructor, a contract worker, an optimist, someone
risk-seeking) together with what the model must do for them. Any change to
the engine has to keep passing it. To teach the model something new, add a
scenario that names the person, states the expected behaviour, and cites
the study it came from.
