# Tail risk: CVaR as a second opinion

## Why variance is not enough

Mean-variance optimization is the backbone of Hone's main flow, and it
earns its place: it is the objective Black-Litterman blends views into,
and the quadratic utility it maximizes is the standard second-order
approximation of the CRRA preferences the questionnaire elicits. But it
carries two assumptions that do not survive contact with markets.

**Variance is symmetric.** It penalizes a 10% gain exactly as hard as a
10% loss. No investor feels that way, and the elicited γ is a statement
about losses.

**Σ assumes second moments tell the story.** Real returns are
left-skewed and fat-tailed, and correlations converge toward one exactly
when diversification is being counted on. A portfolio can look
well-behaved in the covariance matrix and still have a tail that takes
half of it. In crypto this is not a subtlety — the synthetic universe in
`hone/crypto/` uses Student-t innovations with 4 degrees of freedom
precisely because that is what the data looks like.

## What CVaR asks instead

Conditional Value-at-Risk at level β is the **average loss across the
worst 1 − β of outcomes**. Not the threshold you cross — the average of
everything past it.

| Measure | Question it answers |
|---|---|
| Volatility | How much does this bounce around? |
| VaR | How bad is the loss I only exceed 5% of the time? |
| **CVaR** | **When I do exceed it, how bad is it on average?** |

VaR is what most people mean by "worst case" and is the weakest of the
three: it says nothing whatsoever about the losses beyond it, and it is
not a coherent risk measure in the Artzner et al. (1999) sense — it can
penalize diversification, telling an investor that splitting a position
made them riskier. CVaR is coherent. Hone shows VaR anyway, next to
CVaR, because putting them side by side is the clearest way to make the
difference concrete.

## The method

Rockafellar & Uryasev (2000) is what makes this tractable. For a set of
scenarios, minimizing

```
F_β(w, ζ) = ζ + 1/((1−β)T) · Σ_t max(0, −r_t·w − ζ)
```

jointly over the weights and an auxiliary ζ minimizes CVaR, and the
optimal ζ turns out to be the VaR. The `max()` linearizes with one slack
variable per scenario, so the whole problem is a **linear program** — no
local optima, no convergence tuning, no covariance matrix at all. It
stays linear when an expected-return term is added, which is what makes
the mean-CVaR frontier cheap to trace.

Scenarios are overlapping 21-period simple returns from the user's own
price history — simple, not log, because portfolio return is a weighted
sum of simple returns and CVaR is a claim about wealth.

## Two portfolios, not one

**Minimum CVaR (risk-first)** minimizes the tail and *ignores expected
returns entirely*. That sounds like a limitation and is closer to a
feature: return forecasts are the least reliable input in the whole
pipeline, and a portfolio that never sees them cannot be wrecked by
getting them wrong.

**Mean-CVaR at your γ** trades tail against return at the rate the
user's elicited risk aversion implies. Hone's premise is that the risk
knob is measured rather than chosen, so a CVaR mode with a hand-picked
coefficient would be a different product wearing the same clothes.
`kappa_from_gamma` matches the marginal rate of substitution between
return and risk:

```
mean-variance :  dU/dσ = −γσ
mean-CVaR     :  dU/dσ = −κ·k        k = φ(z_β)/(1−β)
⇒  κ = γ·σ_ref / k
```

This is a **local** match at a reference volatility, and the claim is
deliberately narrow: it makes γ mean roughly the same thing in both
modes. It is not an equivalence — the entire point of CVaR is that the
distribution is not normal, and `k` is a normal-distribution factor.
Where the two modes disagree, the disagreement is the information.

The expected returns fed to the mean-CVaR arm are the **equilibrium
prior** Π = δΣw, not sample means. Two years of sample means are noise,
and feeding them to an optimizer is the classic error that gave
mean-variance its reputation.

## Where this sits in the product

It is a **second opinion, not a replacement**. The main flow stays
variance-based, because that is what Black-Litterman blends views into
and what the γ→volatility risk budget in the hedging engine is built on.
The tail page tells the user what that choice costs them in the tail,
in dollars.

## Known limitations

* **Overlapping windows share data.** 700 overlapping monthly windows are
  nothing like 700 independent observations. The effective sample in the
  tail is far smaller than the count suggests, and the page says so.
* **The tail is thin by construction.** At β = 0.95 over 500 scenarios the
  average is taken over 25 points. That is thin evidence, and it is why
  the 99% option carries a warning: at that level it is five points, and
  an average of five points is not an estimate.
* **History is not a forecast.** The worst month in the data is not the
  worst month there is. A user whose history happens to exclude a crash
  gets a CVaR that reflects that luck.
* **Pure risk minimizers concentrate.** Uncapped, the minimum-CVaR
  portfolio is often a *single name* — whatever happened to be quietest
  in-sample. This is the same pathology minimum-variance optimizers have,
  and it is why `max_weight` is not optional in the product. There is a
  test pinning the behaviour so nobody removes the cap thinking the
  objective will hold the line on its own.
* **No transaction costs.** Adopting these weights implies trades that are
  not priced anywhere in Hone yet.

## References

* Rockafellar, R. T., & Uryasev, S. (2000). "Optimization of Conditional
  Value-at-Risk." *Journal of Risk* 2(3), 21–41.
* Rockafellar, R. T., & Uryasev, S. (2002). "Conditional value-at-risk
  for general loss distributions." *Journal of Banking & Finance* 26(7).
* Artzner, P., Delbaen, F., Eber, J.-M., & Heath, D. (1999). "Coherent
  measures of risk." *Mathematical Finance* 9(3), 203–228.
* Krokhmal, P., Palmquist, J., & Uryasev, S. (2002). "Portfolio
  optimization with conditional value-at-risk objective and constraints."
  *Journal of Risk* 4(2).
