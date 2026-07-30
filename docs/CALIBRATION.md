# The decision journal and confidence calibration

## The problem this solves

Hone measures almost everything it uses. γ comes from an incentivized
Holt-Laury experiment. Σ comes from price history. Π comes from the
user's own holdings. One number is different: **confidence**, which the
user simply types in.

That number is not decorative. In Black-Litterman it drives Ω, the
view-uncertainty matrix, through the Idzorek mapping — it is the single
lever deciding how far the posterior moves from equilibrium. Type 90%
and the optimizer treats your price target as near-fact and concentrates
into it. Type 30% and it barely registers.

And self-reported confidence is, in the literature, the least reliable
number a forecaster produces. Lichtenstein, Fischhoff & Phillips (1982)
established the base finding across domains: people asked for events they
are 90% sure of are right roughly 70–75% of the time, and the gap widens
with difficulty. Barber & Odean (2000, 2001) traced the same
overconfidence directly into retail trading accounts — the most active
traders underperformed the market by ~6.5 percentage points a year, and
the effect was strongest where overconfidence was strongest.

So Hone was, until this module, doing careful measurement everywhere
except at the one input that most determines the answer.

## What it does instead

Every view a user acts on is logged at the moment they commit — the
optimize request that produced their trade list is the same event that
writes the journal entry. The entry freezes the ticker, **the server's
price**, the target, the horizon and the stated confidence. Nothing is
reconstructed afterwards, because a record assembled from memory is a
record of what someone now believes they believed.

When the horizon elapses the prediction resolves against the market:

| Event | Definition | Used for |
|---|---|---|
| `target_hit` | Final price at or beyond the target | The Brier score and the calibration fit — it is literally what the confidence claimed |
| `direction_hit` | Price simply moved the way the user said | Reported, **never scored** — see below |
| `touched` | Target reached at any point before expiry | Shown only. A target touched and given back is not a forecast that paid, but "you were right and didn't take it" is the most useful thing a journal can say |

`direction_hit` is shown because "right on direction, too greedy on
magnitude" is a different and fixable problem from "simply wrong". It is
kept out of the score because it is **contaminated by drift**: in a
rising market a coin-flipper who is long by habit clears 60% on it while
knowing nothing. The conviction backtest measured the effect directly — a
zero-skill investor scored 0.511 directional against 0.491 when the same
calls were graded against the equilibrium prior instead of against zero.
Feeding it into the calibration map would hand users a flattering number
manufactured by the market going up.

A prediction whose price data is missing stays **open** rather than being
scored a miss. Counting our data gaps as the user's failures would
quietly manufacture overconfidence.

## Scoring

The Brier score (Brier 1950) is the mean squared error of the stated
probability against the binary outcome. Murphy's (1973) decomposition
splits it into three parts that answer different questions:

```
BS = reliability − resolution + uncertainty
```

* **Reliability** — does 70% mean 70%? Lower is better; zero is perfect
  calibration.
* **Resolution** — do the calls you're confident about land more often
  than the ones you're not? Higher is better. This is the part that
  cannot be faked by predicting the base rate.
* **Uncertainty** — the variance of the outcomes themselves. A property
  of the questions, not the forecaster.

The distinction drives what Hone does with the score. Poor reliability
with good resolution means the user knows something and states it badly:
rescale their confidence, don't discard it. Zero resolution means the
number carries no information at all, and no rescaling helps.

## The calibration map

A one-parameter-pair logistic regression in log-odds space:

```
logit(p_used) = a + b · logit(p_stated)
```

fitted by maximum likelihood, with `a ∈ [−4, 4]` and `b ∈ [0, 3]`. The
bounds matter: under perfect separation — a user whose every call so far
has hit — the unconstrained MLE diverges to infinity.

The fit is then **shrunk toward the identity map** (a = 0, b = 1) by a
pseudo-count of 20 calibrated observations:

```
a_used = w · â          b_used = w · b̂ + (1 − w)          w = n / (n + 20)
```

Shrinkage is not a nicety, and the threshold below which nothing happens
at all is not either. Both were tested rather than assumed — see
[docs/BACKTEST_CONVICTION.md](BACKTEST_CONVICTION.md), which simulated a
population of investors and compared this design against the two obvious
alternatives:

* Replacing stated confidence **outright** with the realized hit rate —
  the blunt version of this feature — *lost* on the majority of investor
  draws (it won 27-54% in equities, 26-41% in crypto). It helps the
  overconfident and taxes anyone with genuine edge, because a hit rate is
  a slow, noisy estimator that caps confidence near 0.23 even for a good
  forecaster. Shrinking toward the user's own number is what makes the
  feature safe.
* Acting at **five** resolutions, the original threshold, was acting on
  noise: the standard error on a hit rate at n=5 is about ±22 percentage
  points, and separating a forecaster with a real information coefficient
  of 0.2 from one with none takes on the order of a hundred resolutions.
  The threshold is now **25**, which is still optimistic and is the least
  defensible number in this module.

Below the threshold nothing is adjusted at all — the page is a record,
not yet a correction.

Two more guards:

* The adjusted confidence is clipped to [0.05, 0.95]. Black-Litterman
  needs a positive confidence, and a bad run should never erase a user's
  voice entirely.
* The journal records the **stated** confidence, never the adjusted one.
  Scoring our own output would feed the calibration its own tail and
  discount the user a little further on every pass.

## Where it lives

Nothing is stored server-side. The journal lives in the browser under
`hone-journal:<asset class>`; `POST /api/journal` receives it, resolves
what it can against market data, and returns the verdict plus the fitted
map. The map is cached in page state and sent back with the next
`POST /api/optimize`, which applies it server-side so the arithmetic has
exactly one implementation. When a view's confidence is rescaled the
optimize page says so explicitly — the correction is disclosed, never
silent, and can be switched off on the record page.

## Known limitations

* **Selection.** Users journal the views they act on, not the views they
  consider. A user who only acts on their strongest ideas is scored on a
  truncated sample, and the fit is conditional on that.
* **Small n.** Retail users will have tens of resolved predictions, not
  thousands. The reliability curve uses five buckets rather than ten for
  this reason, and it is still noisy. Read the shape, not the wiggles.
* **The evidence for this feature is mixed, and honestly so.** The
  simulation says the confidence channel moves median Sharpe by less than
  0.05 in the shipped configuration, against a 0.16 gap between having
  forecasting skill and not. Confidence handling is a guardrail, not an
  edge — it earns its place by limiting the damage a badly-calibrated user
  does to themselves, not by making anyone money.
* **Horizon clustering.** Predictions made in the same week resolve in
  the same market. Twelve calls made into one drawdown are closer to one
  observation than twelve, and the score does not currently correct for
  this — it will overstate how much evidence a burst of activity provides.
* **The target event is demanding.** Reaching a specific price by a
  specific date is much harder than being directionally right, so hit
  rates look low and almost everyone reads as overconfident. That is why
  the direction-only rate is shown beside it. Users who are consistently
  right on direction and short on magnitude have a fixable problem, and
  the page should tell them which one they have.

## References

* Brier, G. W. (1950). "Verification of forecasts expressed in terms of
  probability." *Monthly Weather Review* 78(1), 1–3.
* Murphy, A. H. (1973). "A new vector partition of the probability
  score." *Journal of Applied Meteorology* 12(4), 595–600.
* Lichtenstein, S., Fischhoff, B., & Phillips, L. D. (1982). "Calibration
  of probabilities: the state of the art to 1980." In *Judgment Under
  Uncertainty: Heuristics and Biases*.
* Barber, B. M., & Odean, T. (2000). "Trading is hazardous to your
  wealth." *Journal of Finance* 55(2), 773–806.
* Barber, B. M., & Odean, T. (2001). "Boys will be boys: gender,
  overconfidence, and common stock investment." *QJE* 116(1), 261–292.
* Idzorek, T. (2007). "A step-by-step guide to the Black-Litterman
  model." In *Forecasting Expected Returns in the Financial Markets*.
