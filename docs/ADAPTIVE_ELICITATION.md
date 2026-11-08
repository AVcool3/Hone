# Adaptive elicitation (DOSE)

## Why replace a working questionnaire

The Holt-Laury Multiple Price List is a good instrument. Hone's problem
with it was never validity — it was that thirty questions is a wall, and
it sits at the very front of the funnel, before the user has seen
anything the product does.

There is also a substantive problem, and it is the more interesting one.
The classic menu's indifference points top out around γ ≈ 1.4. Above
that, **every row is answered the same way**, so a genuinely risk-averse
user — tier 35 and up, a third of Hone's scale — produces a choice vector
that is consistent with any γ from 1.5 to 5. The MLE then reports a
number, and that number is mostly noise.

Chapman, Snowberg, Wang and Camerer (2018) set out the alternative:
maintain a Bayesian posterior over the preference parameters and, at each
step, ask whichever question the posterior expects to learn the most
from. They found a handful of adaptive questions recovers parameters
about as precisely as a full menu, with better test-retest reliability —
partly because subjects who are still paying attention give better data.

## Method

**Posterior** over a 121 × 13 grid in (γ, μ). μ is the same Fechner noise
parameter the MLE estimates: a user's inconsistency is information about
how much to trust their answers, not an error to discard.

**Likelihood** is `hone.risk_profile.estimation.choice_probability` under
the contextual-Fechner specification — the same function the MLE uses.
The grid version is vectorized for speed and held to agreement with it by
a test, because the two estimators drifting apart would mean two
different models of the same person.

**Selection** maximizes the mutual information between the parameters and
the answer:

```
I(θ; y) = H( E_θ[Pr(A|θ)] ) − E_θ[ H(Pr(A|θ)) ]
```

with H the binary entropy in bits. The first term rewards questions the
posterior is undecided about; the second penalizes questions that are
coin flips *for every individual θ* (those teach nothing about γ, only
about μ). A question everyone answers the same way scores zero and is
never asked.

**The question bank** is constructed rather than curated. For each target
γ on a grid and each of four coin flips, the sure amount offered is that
γ's certainty equivalent — which has a closed form, so the bank's
indifference points tile the range −1.2 to 4.8 with no gap wider than
0.5. A bank with holes cannot separate the tiers it fails to reach,
however cleverly questions are then selected. Pairs where one option
dominates are dropped: they cost a user's attention and buy nothing.

**A diversity rule** keeps consecutive questions from reusing the same
gamble. Pure information-maximization asks the same coin flip six times
with the sure amount nudged each round, which is tedious and reads like
the tool is haggling. Accepting a question within 80% of the best
expected gain fixes it at no measured cost in accuracy (mean RMSE 0.353
with and without, across γ from −0.5 to 3.6).

**Stopping** at eight questions, or earlier if the posterior s.d. on γ
drops below 0.05 — but never before four answers, because an early tight
posterior is the prior talking, not the user.

## Does it work

Synthetic CRRA subjects with Fechner noise (μ = 0.10), 20 runs per cell,
RMSE of the recovered γ:

| True γ | DOSE, 8 questions | DOSE, 12 questions | Full menu, 30 questions |
|---|---|---|---|
| −0.5 | 0.28 | 0.23 | 0.24 |
| +0.3 | 0.21 | 0.24 | 0.20 |
| +1.2 | 0.22 | 0.17 | 0.31 |
| +2.5 | **0.37** | 0.28 | **1.92** |
| +3.6 | **0.52** | 0.39 | **1.50** |

Eight adaptive questions match thirty fixed ones where the fixed menu can
see, and beat it by a factor of four to five where it cannot. The bottom
two rows are the substantive result: they are not a marginal efficiency
gain, they are the difference between measuring a risk-averse user and
guessing at them.

Reproduce with `tests/test_dose.py::TestPosterior::test_beats_the_full_menu_where_the_menu_is_blind`.

## What it does not fix

* **Eight binary answers carry at most eight bits.** The posterior s.d.
  after a full run is typically 0.3–0.7, which spans several of the 50
  tiers. The interval is shown on the profile page and carried through as
  a credible interval rather than being quietly rounded away — γ is
  inferred, not observed, and everything downstream inherits that width.
* **The estimate is Bayesian**, so it is pulled toward the prior. At the
  extremes this is visible: a true γ of 3.6 recovers at about 3.2 after
  eight questions. Widening the prior reduces the bias and costs a little
  precision in the middle, where most users are; the current setting
  (mean 0.65, s.d. 1.60) takes that trade deliberately.
* **Hypothetical stakes.** These are unincentivized questions about money
  the user will not receive, which is a known weakness of the whole
  elicitation literature and not something an adaptive design repairs.
  The revealed-γ diagnostic on the portfolio page — which infers risk
  aversion from what someone *actually holds* — is the counterweight, and
  the two disagreeing is a finding worth showing rather than hiding.
* **Preferences drift.** A measurement is of a moment. Hone suggests
  re-taking it quarterly.

## References

* Chapman, J., Snowberg, E., Wang, S., & Camerer, C. (2018). "Loss
  Attitudes in the U.S. Population: Evidence from Dynamically Optimized
  Sequential Experimentation (DOSE)." NBER Working Paper 25072.
* Holt, C. A., & Laury, S. K. (2002). "Risk aversion and incentive
  effects." *American Economic Review* 92(5), 1644–1655.
* Wilcox, N. T. (2011). "'Stochastically more risk averse': a contextual
  theory of stochastic discrete choice under risk." *Journal of
  Econometrics* 162(1), 89–104.
* Lindley, D. V. (1956). "On a measure of the information provided by an
  experiment." *Annals of Mathematical Statistics* 27(4), 986–1005.
