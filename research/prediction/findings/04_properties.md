# 04 — Property-based tests of the income-hedging engine

Test file: `tests/test_hedge_properties.py`. It has 63 test items: 49 pass and 14 are strict xfails, each pinned to a documented bug. The whole file runs in about 13 s.

Run it with `python -m pytest -q tests/test_hedge_properties.py`.

- **Scope:** `hone/prediction/hedge.py`, `liquidity.py` and `contracts.py:kalshi_fee`.
- **Random inputs:** all random cases come from seeded `numpy.random.default_rng`. No new dependencies were added.
- **Shared sweep:** 1,500 random valid exposures, reused across the accounting tests. They cover:
  - wealth from $400 to $10M, loss/wealth from 0 to 0.97 (with a cushion of at least $250);
  - prices of 0.01, 0.99 and the cent grid between;
  - gamma at {0.05, 0.3, 1, 1.5, 2, 3.5, 5, 20} and continuous values in [0.05, 6];
  - basis correlation in [0, 1], with 20% of cases at exactly 1;
  - with and without a view, with market price differing from the ask, fees on or off, `allow_selling` on or off;
  - five liquidity shapes: none, open interest only, a flat book, a flat book plus open interest, and "known nothing".
- **xfails:** every one is `strict=True`. When a bug is fixed its test will XPASS and fail, which is the signal to remove the marker.

## Summary of bugs

| # | Severity | Bug | Where |
|---|---|---|---|
| B1 | **Medium-high** | With basis 1 (the default), zero-probability states still set the solvency bound. The hedge is capped at (W−L)/price even though the full hedge is solvent. | `hedge.py:304-311`, `:316` |
| B2 | **Medium** | `worst_hedged` is computed over impossible states. The "Worst season" stat is wrong for the default inputs. | `hedge.py:561` (rows are filtered at `:538`; this min is not) |
| B3 | **Medium** | When gamma ≤ 0 the code skips the solvency bounds. A large loss then makes `hedge_income` raise (HTTP 422). | `hedge.py:391-396` |
| B4 | **Medium** | The order-book average fill is applied after sizing and never re-optimized. The plan can propose a hedge with negative CE gain, or one that is insolvent (it raises). | `hedge.py:399-425` |
| B5 | Low | `int(round(n_star))` can round past the solvency bound. With a small cushion `hedge_income` raises. | `hedge.py:399` |
| B6 | Low (only for gamma above about 10) | `joint_states` leaves 2.8e-17 in the "impossible" states. At high gamma those phantom states move the optimum. | `hedge.py:152-155` |
| B7 | Low | `total_premium` uses the quoted price while `cost` uses the fill price. | `hedge.py:568` vs `:423-425` |
| B8 | Low | `w^(1-gamma)` underflows to 0, so `crra_inverse` raises ZeroDivisionError. That is not a ValueError, so the API returns HTTP 500. | `hedge.py:85-89` |
| B9 | Low | `blend_belief` clips to [0.01, 0.99] only when a view is given. "No view" and "a view at confidence 0" disagree at extreme prices. | `hedge.py:116-124` |

Design findings that are not marked xfail:

- **D1:** with basis risk, the speculative/hedge split is not zero at a fair price.
- **D2:** gamma = 0 is a cliff.
- **D3:** the number of contracts is not monotone in the loss at high loss/wealth. This is economically correct.
- **D4:** within 1e-9 of gamma = 1 the optimizer shows a little noise.

---

## Properties, cases and results

| Property | Cases | Result |
|---|---|---|
| `kalshi_fee`: never below the raw fee, never more than 1¢ above it, a whole number of cents | 20,000 | pass |
| `kalshi_fee`: symmetric fee(p) = fee(1−p) on the cent grid, monotone in contracts, 0 for no contracts, highest at 0.5 | 20,000 | pass |
| `blend_belief`: stays in [0.01, 0.99]; moves toward the view as confidence rises (confidence outside [0, 1] is clipped); equals the market at confidence 0 | 20,000 | pass |
| `blend_belief`: confidence 0 equals no view at market prices of 0.001, 0.005, 0.995 and 0.999 | 4 | **xfail B9** |
| `joint_states`: probabilities non-negative and summing to 1, marginals preserved to 1e-12, rho clipped to an independently computed Fréchet bound, output correlation equals the reported rho | 20,000 | pass |
| `joint_states(q, q, ·)` never clips, so `basis_clipped` can never be true from `hedge_income` | 99 | pass (observation) |
| Reservation price: at least the belief, and strictly above it when rho > 0; rises with gamma and with the loss; equals the belief at gamma = 0 or loss = 0; below the belief for gamma < 0 | 5,000 | pass |
| Reservation price is where the first contract stops paying: at price = c_max, \|n*\| < 1; at c_max − 2¢, n* > 0 | 300 | pass |
| Never buys above the reservation price when gamma > 0, with or without a view (c_max already includes the view) | 1,500 | pass, 0 cases |
| Solvency: wealth > 0 in every state in the table | 1,500 (sweep) | pass |
| Dollar fields match the states table: expected wealth, std, `ce_gain` = CE_h − CE_u, the CE recomputed from the rows, Jensen bounds, worst wealth when rho < 1 | 1,500 | pass |
| `worst_hedged` is a state that can happen (rho = 1) | 1 | **xfail B2** |
| CE recomputed from the rows matches when rho = 1 and gamma is high | — | fails in the sweep; **xfail B6** |
| Cost and fee: fee equals `kalshi_fee` at the fill price, cost = gross + fee, payout, direction, `needs_hedge`, `total_premium` = cost − c·belief, change in E[W] = edge − fee, pure + speculative = n* | 1,500 | pass (with a flat book) |
| `total_premium` when walking the book | 1 | **xfail B7** |
| Liquidity: \|c\| ≤ limit, never the opposite direction, \|c\| ≤ \|wanted\|, coverage in [0, 1] and equal to \|c\|/\|wanted\|, `capped` iff c ≠ wanted, `allow_selling=False` means c ≥ 0 | 1,500 | pass |
| loss = 0: c_max equals the belief, pure hedge is 0, `needs_hedge` is false, warning present | about 150 | pass |
| Deterministic: the same input gives an identical `to_dict()` | 200 | pass |
| Concavity at a fair, fee-free price: CE gain ≥ 0, including any open-interest cap | 1,200 | pass |
| With fees: CE gain ≥ −1¢ (integer rounding plus fee rounded up) | 1,200 | pass (worst found was above −1.1¢) |
| Walking the book never proposes a hedge worse than none | 1 | **xfail B4** |
| E[U] is concave in n across the whole solvency interval (second differences ≤ 0) | 300 × 41 points | pass |
| Pure hedge: rho = 1, fair price, no fee, gamma ≤ 8, bound slack: \|n* − L\| ≤ 0.51 | 800 | pass |
| With basis risk: \|n* − ρL\|/L ≤ 1.5·L/W (measured) | 800 | pass, see D1 |
| Fees shrink the hedge: n*(3× fee) ≤ n*(fee) ≤ n*(no fee) ≈ L | 400 | pass |
| More loss gives more contracts (L/W ≤ 0.3) | 150 × 8 | pass, see D3 |
| More basis gives more contracts | 150 × 8 | pass |
| A dearer price at a fixed belief gives fewer contracts | 150 × 9 | pass |
| More risk aversion moves the position closer to the pure hedge (rho = 1) | 120 × 6 | pass. It does **not** hold when rho < 1: in 111 of 300 cases n* crosses ρL. |
| CRRA scale invariance: n*(kW, kL) = k·n*(W, L) | about 250 | pass (relative 2e-3) |
| At gamma = 1 with no exposure and no fees, the stake fraction equals Kelly (±0.002); the sign of `kelly_fraction` is right | 500 / 5,000 | pass |
| `asks_from_orderbook`: sorted, unique prices in (0, 1), total quantity preserved, junk levels dropped | 3,000 books | pass |
| `depth_within` monotone in slippage; `average_fill` within [best, worst] and non-decreasing in n; None past the end of the book | 3,000 | pass |
| `limit_for` = floor(min(depth, floor(10% of OI))) | 3,000 | pass |
| Edge cases: price 0.01 and 0.99 (with and without an opposing view); gamma 0.05, 1.0 and 20; loss 0; L = W − 1 (rho = 0.5); W = 1e9 at gamma 20 and 0.05; W = $50; W = $1; rho = 0 with no view gives 0 contracts. All are finite and solvent. | 16 | pass |
| Solvency for gamma ≤ 0 with a large loss | 3 | **xfail B3** |
| Full basis: the full hedge is not capped by an impossible state | 1 | **xfail B1** |
| Rounding never goes past the bound (rho = 1 and rho < 1) | 2 + 1,000 | **xfail B5** |
| Walking the book keeps wealth positive | 1 | **xfail B4** |
| Large gamma does not underflow | 1 | **xfail B8** |
| Continuity: a 1e-7 nudge to wealth, loss or confidence | 400 × 3 | pass. Worst move is 5 contracts on 3.4M (1.5e-6 relative). Nothing beyond one rounding step exceeds 2e-6 relative, and the direction never flips. |
| Continuity in gamma near 1 (the log branch) | 9 | pass, see D4 |

---

## Bugs

### B1 — Zero-probability states set the solvency bound when basis = 1 (medium-high)

**Reproduction:** `IncomeExposure(wealth=10_000, loss=9_500, price=0.5, gamma=2, fee_rate=0)`.

- **Observed:** 995 contracts. CE is $1,805, against $952 unhedged.
- **Expected:** about 9,500 contracts, the full hedge. It is solvent: wealth is a certain $5,250, so CE is $5,250.
- **Cause:** with rho = 1 the state "loss happens, contract does not pay" has probability 0. However:
  - `_bounds()` uses the cushion W − L as the worst-state wealth;
  - `_expected_utility` returns −inf if *any* state, including zero-probability ones, is ≤ 0.

  So the long position is capped at 0.995·(W−L)/(p·(1+fee)). This binds whenever L/W > 1/(1+p): above 0.67 at p = 0.5, and above 0.74 at p = 0.35.
- **Measured ratio n*/L** (fair price, no fee, gamma 2):

  | Price | L/W | n*/L |
  |---|---|---|
  | 0.35 | 0.8 | 0.71 |
  | 0.35 | 0.9 | 0.32 |
  | 0.8 | 0.6 | 0.83 |
  | 0.8 | 0.9 | 0.14 |

  `basis_correlation` defaults to 1.0 in both `IncomeExposure` and the API schema.
- **Suggested fix:** compute the bounds from states with `prob > eps`. The long bound is the minimum over non-paying states of the wealth there, divided by the per-contract cost; the short bound is analogous. Drop zero-probability states in `_wealth` and `_expected_utility`, or pass only positive-probability states.

### B2 — `worst_hedged` reports a state that cannot happen (medium)

**Reproduction:** the default page example, `IncomeExposure(38_000, 9_000, 0.35, gamma=1.5)`.

- **Observed:** `worst_hedged` is 26,289.59. The states table holds only 33,696.59 and 35,289.59.
  - Fee-free: `worst_hedged` is 25,850, while `std_hedged` is 0 and both real states are 34,850.
- **Expected:** `worst_hedged` equals `min(row.wealth_hedged)`.
- **Cause:** `hedge.py:561` takes `w_hd.min()` over all four joint states. The rows at `:538` drop states with prob ≤ 1e-9; the minimum does not. The wrong value is shown as "Worst season" on `IncomeHedgePage.jsx:532` and on the marketing `Home.jsx:418`. It understates the hedge by about $7–9k in the default example.
- **Suggested fix:** take the minimum over states with prob > 1e-9, the same filter the rows use. Apply the same filter to `worst_unhedged` for consistency.

### B3 — gamma ≤ 0 skips the solvency bounds and raises (medium)

**Reproductions:**

- `IncomeExposure(10_000, 9_500, 0.5, gamma=0)`
- `gamma=-0.5, basis_correlation=0.5` (the same wealth, loss and price)
- `gamma=-2`

**Observed:** each raises `ValueError: wealth must be positive in every state`, which the API turns into HTTP 422.

- **Expected:** a plan. The questionnaire produces gamma in [−3, 5] and the tiers cover [−1, 4], so negative gamma is a normal input.
- **Cause:** `hedge.py:391-396` sets `n_star = rho_eff * loss` without applying `_bounds(exp)`.
  - With rho = 0.5 the state that goes negative is real: W − L − n·p = 500 − 2,375.
  - With rho = 1 it is B1's phantom state, and `crra_certainty_equivalent` checks every state.
- **Suggested fix:** clip `n_star` into `_bounds(exp)` on the gamma ≤ 0 path. Also see D2.

### B4 — The order-book average fill is not fed back into sizing (medium)

**Reproduction 1 (negative CE):** `IncomeExposure(38_000, 9_000, 0.35, gamma=0.3, liquidity=Liquidity(asks_buy=[(0.35, 1), (0.38, 1e6)]))`.

- **Observed:** 1,257 contracts at an average fill of $0.380 and `ce_gain` of **−$36.74**, with `needs_hedge=True`. The only warning is the "walks up the order book" note.
- The reservation price is $0.369, so every contract after the first costs more than it is worth to this user. With the quoted price the same plan had a CE gain of +$1.72.

**Reproduction 2 (raises):** `IncomeExposure(10_000, 7_400, 0.21, gamma=1, basis_correlation=0.98, own_prob=0.72, confidence=1, liquidity=Liquidity(asks_buy=[(0.21, 10), (0.24, 1e7)]))` raises `ValueError`.

- In a random search, 326 of 4,000 exposures with a two-level book 3¢ deep raised.
- The `default_rng(5)` search used W = 10k, L/W from 0.3 to 0.95, rho from 0.3 to 0.99, and any view.

**Cause:**

- `hedge.py:398` sizes at `exp.price`.
- `:403-418` caps the size and then swaps in the average fill.
- `:421-425` evaluates at that fill. Nothing re-checks utility or solvency at the fill price.
- The "costs more than c_max" warning at `:451` also compares the quote, not the fill.

**Suggested fix:**

- Either optimize against the walked book, with a piecewise-linear cost per contract that is still concave, or re-optimize at the average fill price.
- At minimum, shrink the position until `ce_gain ≥ 0` and wealth stays above 0 at the fill price.
- Compare `avg_fill` with `c_max` for the warning.

### B5 — Rounding goes past the solvency bound (low)

**Reproductions:**

- `IncomeExposure(10_000, 9_999.6, 0.4, gamma=2)`: n* = 0.955, pinned at the bound by B1, rounds to 1, and the call raises.
- With rho < 1: about 4% of random exposures with W of $1–5 and loss/wealth of 0.5–0.99 raise. One example is W = 2.07, L = 1.72, p = 0.4, gamma = 0.5, rho = 0.87.

**Cause:** `int(round(n_star))` at `hedge.py:399` can add up to 0.5 contract. The 0.5% margin built into `_bounds` covers it only if the cushion exceeds about 100 contracts' cost. The fee rounded up to the cent adds up to 1¢ more.

**Suggested fix:** take `contracts = floor` toward zero whenever rounding would leave `[lo, hi]`, or check the exact wealth at the rounded size and step back one contract.

### B6 — Phantom probability left by `joint_states` (low; matters only for gamma above about 10)

**Reproduction:** `joint_states(0.515, 0.515, 1.0)` leaves 2.78e-17 in the pays≠loss states.

- About 8% of a 0.0001 grid of q values do this, for example 0.04, 0.06, 0.155, 0.415–0.465, 0.515 and 0.84.
- `IncomeExposure(100_000, 60_000, 0.515, gamma=20, fee_rate=0)` gives n* = **55,782** with `std_hedged` of 2,108. The expected result is 60,000 and 0.
- **Cause:** `p10 = q_event − p11` accumulates rounding. Multiplied by the marginal utility ratio (W_bad/W)^−gamma of about 10^15 at gamma = 20, the phantom state dominates. The plan's `ce_*` also includes those states, while the rows hide them; the sweep found a $834 CE mismatch.
- **Suggested fix:** snap \|p\| < 1e-12 to 0 in `joint_states`. The B1 fix (ignore zero-probability states) also covers this.

### B7 — `total_premium` uses the quote, not the fill (low)

**Reproduction:** `IncomeExposure(38_000, 9_000, 0.35, 1.5, liquidity=Liquidity(asks_buy=[(0.35, 100), (0.37, 1e6)]))`.

- **Observed:** `total_premium` is 120.83.
- **Expected:** cost − c·belief = 266.97.
- **Cause:** `hedge.py:567-568` uses `exp.price`, while cost and fee use `fill.price`.
- **Suggested fix:** use `fill.price`. Consider defining the premium for sells too; it is currently fee-only.

### B8 — Underflow becomes ZeroDivisionError and HTTP 500 (low)

**Reproduction:** `IncomeExposure(1e6, 1e5, 0.35, gamma=60)`. The same happens with gamma = 20 and W of about 1e17.

- **Cause:** `w**(1−gamma)` underflows to 0, and `crra_inverse` then evaluates `(-0.0) ** (negative)`.
- The API catches only `ValueError` (`app.py:2152`), and `ContractHedgeRequest.gamma` has no bound.
- **Suggested fix:**
  - Normalize wealth by W before computing utilities. CRRA CE is homogeneous, so CE(w) = W·CE(w/W).
  - Bound gamma in the schema.

### B9 — `blend_belief` clips inconsistently (low)

**Reproduction:** `blend_belief(0.995, None, 0)` returns 0.995, while `blend_belief(0.995, 0.5, 0)` returns 0.99.

- **Cause:** with no view the function returns before the clip (`hedge.py:116-117`).
- **Suggested fix:** clip in both branches, or clip neither. It matters only once sub-cent prices appear.

---

## Design findings (tests pass; not marked xfail)

### D1 — With basis risk, the "speculative" share is not zero at a fair price

With rho < 1, the CRRA optimum is not the variance-minimizing ρL. The gap \|n* − ρL\|/L reaches about 1.2·(L/W):

| L/W | Worst \|n* − ρL\|/L | Mean |
|---|---|---|
| 0.02 | 0.011 | 0.003 |
| 0.1 | 0.069 | 0.016 |
| 0.4 | 0.37 | 0.10 |

`IncomeHedgePage.jsx:559-561` labels a positive gap "added by your view of the odds", even for a user with **no** view at a fair price. The docstring claim that the "speculative tilt [is] zero when the contract is fairly priced" holds only at rho = 1.

Suggestion: label the gap "CRRA adjustment for basis risk", or define the pure hedge as the CRRA optimum at q = c.

### D2 — gamma = 0 is a cliff

| gamma | Contracts | CE gain | `needs_hedge` |
|---|---|---|---|
| 0 | 9,000 | −$143 | true |
| 0.01 | 0 | $0 | false |

At gamma = 0 the proposed position is worse than nothing *by the user's own preferences*, because they pay fees for a variance cut they do not value. It is documented with a warning.

The "costs more than … your risk aversion makes it worth" warning is reachable only on this path, because for gamma > 0 buying above c_max is mathematically impossible (verified on 1,500 cases). Its text, "exists only because you believe the market is underpricing", is wrong there.

### D3 — Contracts are not monotone in the loss at high L/W

With basis risk and a dear contract, n* rises and then falls with L. For example, at p = 0.76, rho = 0.72, gamma = 3, n* is 17,720 at L/W = 0.45 and 15,125 at 0.6. Each contract drains the "loss, no payout" state. This is correct CRRA behaviour; the test checks monotonicity only for L/W ≤ 0.3.

### D4 — Optimizer noise near gamma = 1

Inside 1e-9 of 1 the code uses log utility. Just outside, w^(1−γ)/(1−γ) loses precision through cancellation. n* wanders by about 20 contracts on 6,618 (0.3%); the CE changes by less than 1¢. This is the worst discontinuity found apart from the bugs above. Using `np.expm1((1−γ)·log w)/(1−γ)` would remove it.

### Fees vs the pure hedge

At rho = 1 and a fair price, with W = 100k and L = 30k:

| gamma | n*/L |
|---|---|
| 0.5 | about 0.60 |
| 1.5 | about 0.86 |
| 3 | about 0.93 |
| 5 | about 0.96 |

The ratio is almost flat across price (0.58–0.62 at gamma 0.5 for p from 0.05 to 0.8), because the fee per dollar of cover, 0.07·(1−p), and the value of cover scale together. Without fees, n* = L to within 0.51 contract in 800/800 cases.
