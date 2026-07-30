# Flexible views: entropy pooling

## The throat in Black-Litterman

Black-Litterman is a good engine with a narrow throat. A view has to be a
**linear statement about expected returns** under a **joint normal**
distribution: *NVDA returns 18%*. That is one shape of belief, and it is
not the shape most beliefs have.

Things a user can hold and the main flow cannot accept:

* "There's a one-in-three chance Tesla drops more than 20% this year."
* "I don't know where Nvidia lands, but I'm confident it beats Intel."
* "If Bitcoin falls 20%, Ethereum falls at least as far."
* "Volatility is going to be higher than the last two years suggest."

The first and fourth are statements about the *shape* of the
distribution, not its centre. The second has no number in it at all. The
third is a conditional relationship that a full-sample covariance matrix
averages away — it is precisely the correlation everyone discovers during
the crash and not before.

Forcing these through a price-target box means asking the user to invent
numbers they do not have, which is the single worst thing a tool like
this can do: an invented number is indistinguishable from a real one by
the time it reaches the optimizer.

## Meucci's answer

*Fully Flexible Views: Theory and Practice* (Meucci, 2008): stop
parameterizing the distribution. Represent the market as **scenarios with
probabilities**, treat each view as a **constraint on those
probabilities**, and find the posterior that satisfies the constraints
while staying as close to the prior as possible:

```
minimize   Σ p̃ᵢ ln(p̃ᵢ / pᵢ)              (relative entropy, Kullback-Leibler)
subject to Ã p̃ = b   (or ≤ b)
           Σ p̃ = 1,  p̃ ≥ 0
```

Minimum relative entropy is the right notion of "least distortion": it is
the update that adds **no information beyond what the views assert**.
That is exactly the discipline you want when the views come from a human
who is confident about one thing and silent about everything else.

Every view type reduces to one row: a vector `g` over scenarios and a
target for `E[g]`.

| View | `g` | Says |
|---|---|---|
| Mean | the asset's returns | `E[r] = q` |
| Probability | a 0/1 indicator | `P(r ≤ t) = q` |
| Ranking | `r_loser − r_winner` | `E[·] ≤ 0` |
| Volatility | `r²` | second moment pinned |
| Conditional | `1{cond}·(r − q)` | `E[r \| cond] = q`, kept linear |

## The dual

The primal has one variable per scenario — hundreds or thousands. The
dual has one per view:

```
D(λ) = ln( Σᵢ pᵢ exp(−(Ãᵀλ)ᵢ) ) + λᵀb
```

minimized over λ, free for equalities and non-negative for inequalities.
The posterior is `p̃ᵢ ∝ pᵢ exp(−(Ãᵀλ)ᵢ)` — an exponential tilt of the
prior, the same object that appears in importance sampling and
large-deviations theory, for the same reason. Solved with L-BFGS-B and an
analytic gradient; the log-sum-exp form is not cosmetic, since the tilt
exponent is unbounded in λ and overflows long before convergence.

## What it costs, and saying so

Views are not free. Insisting that a 6%-likely event is 33% likely means
reweighting the scenarios that contain it, and there are only so many.
`effective_number_of_scenarios` is `exp(entropy)` — Meucci's diagnostic
and the honest answer to *were my views too strong?*

A uniform prior over 700 scenarios has an effective size of 700. If three
views drop that to 90, the posterior is carried by ~90 paths and every
statistic computed from it — the tail above all — is that thin. The page
shows the fraction kept, and flags a collapse rather than quietly
returning a confident-looking number built on nothing.

Measured behaviour on the demo universe:

| View | Effective scenarios kept |
|---|---|
| `E[TSLA] = +3%` (prior +0.8%) | 98% |
| `P(BTC ≤ −15%) = 30%` | 79% |
| `E[ETH \| BTC ≤ −20%] = −30%` | 95% |
| `P(TSLA ≤ −25%) = 60%` | collapses — flagged |

## Why this fits the rest of Hone

The posterior is a **reweighted set of the same scenarios**, and
`hone/optimization/cvar.py` already optimizes over scenarios. Chaining
them gives a path from belief to portfolio that assumes normality
*nowhere*:

```
empirical scenarios → entropy-pooled posterior → CVaR optimization
```

Black-Litterman remains the default route: it is what the confidence
calibration in `hone/journal/` is fitted against, and what the hedging
engine's γ→volatility budget is built on. This is the route for views the
default cannot represent.

## Known limitations

* **Nothing here is calibrated.** The decision journal scores price-target
  views because they resolve unambiguously. "I think A beats B" also
  resolves, but is not yet logged; probability views are far harder,
  since a single outcome barely tests a stated probability.
* **Views can be mutually impossible.** Two constraints the scenario set
  cannot satisfy together drive the effective sample toward zero rather
  than failing loudly. The collapse warning is the signal; there is no
  infeasibility certificate.
* **Resampling to feed the CVaR optimizer adds noise.** The optimizer
  treats rows as equally likely, so a weighted posterior is resampled
  before use — sampling error on top of an already-thin tail. Passing
  probabilities through directly would be better and is not done yet.
* **History bounds imagination.** A view about an event with no instance
  in the price history cannot be expressed at all: there are no scenarios
  to reweight. This is a real ceiling, and the reason the conditional
  view refuses to condition on fewer than five scenarios rather than
  returning an average of two.

## References

* Meucci, A. (2008). "Fully Flexible Views: Theory and Practice."
  *Risk* 21(10), 97–102.
* Meucci, A. (2010). "Historical Scenarios with Fully Flexible
  Probabilities." *GARP Risk Professional*.
* Kullback, S., & Leibler, R. A. (1951). "On information and
  sufficiency." *Annals of Mathematical Statistics* 22(1), 79–86.
* Cover, T. M., & Thomas, J. A. (2006). *Elements of Information
  Theory*, ch. 11 (information geometry and exponential tilting).
