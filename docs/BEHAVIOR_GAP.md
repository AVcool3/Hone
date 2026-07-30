# The behaviour gap

## The assumption every backtest makes

Every backtest in this repository, and almost every backtest anywhere,
silently assumes the investor held the strategy through everything it
did. They did not. Real investors capitulate after drawdowns, sit in cash
while the recovery happens, and return once it feels safe — which is to
say, after the recovery.

The gap between what a strategy returned and what its investors returned
runs to whole percentage points a year. That is not a rounding error
against the differences most of finance argues about, and it is invisible
to every other number on Hone's evidence page.

It is also the strongest argument for the product existing, which is
exactly why it deserves to be measured rather than asserted. If a
portfolio matched to someone's measured risk tolerance is one they are
more likely to keep holding, the γ-matched book should lose less to
capitulation than an aggressive one — **even where the aggressive one
wins on paper**.

## The panic rule

The threshold is not a free parameter. The Merton rule puts
α* = (μ − r)/(γσ_m²) of wealth in the risky asset; pricing the market at
a Sharpe ratio S — so the premium is S·σ_m, the same assumption
`calibrate_delta` makes when building the equilibrium prior — collapses
it:

```
σ_target = α*·σ_m = S / γ
```

The market's volatility cancels, and so does its realized return. The
drawdown at which someone capitulates is then the 95% one-year VaR of
that budget, `1.645·σ_target`, bounded to [8%, 60%].

| γ | Tier | Sells after a drawdown of |
|---|---|---|
| 0.5 | risk-seeking | 60% (the cap) |
| 1.2 | mildly averse | 55% |
| 2.5 | risk-averse | 26% |
| 5.0 | very averse | 13% |
| 8.0 | extremely averse | 8% (the floor) |

**Two earlier versions of this used sample estimates and both broke.**
A per-strategy premium made tolerance a function of the *strategy's*
Sharpe ratio, so the same person tolerated a 60% drawdown in a bad fund
and 8% in a good one. A market-wide sample premium was negative over the
demo window, which pinned every γ to the same cap. A capitulation point
is a property of the person; it should not move because five years of
history happened to be poor.

## The two details that carry the model

**Drawdown is measured against the realized peak**, not the paper one.
Someone who sold and re-entered lower measures their pain from where
their own account peaked. Re-entering resets that peak — an investor who
capitulated and bought back has, in the only sense that matters here,
accepted the loss. Without the reset the simulation re-panics on the next
bar and parks the investor in cash permanently, an artifact of
bookkeeping rather than of anyone's psychology.

**Re-entry waits for confirmation.** The market must climb 10% off its
low since the sale before it feels safe again. This is what makes
capitulation cost anything, because it structurally buys back above the
trough.

A fixed cooldown does not have that property and can be accidentally
well-timed. The first version of this module used one, and produced a
panicking investor who *beat* the strategy by 21 points a year. That is a
stop-loss backtest wearing the wrong label, and it would have been a
flattering, useless result.

Costs are charged: 10bp per switch, and cash earns 4% rather than zero —
the two omissions `docs/BACKTEST_CONVICTION.md` flagged in every other
measurement here.

## What it shows

Median behaviour gap across 8 synthetic price panels, γ = 2.5 (sells past
a 26% drawdown). Positive means capitulating cost money:

| Strategy | Median gap | Mean panics |
|---|---|---|
| **Hone (tier-matched)** | **+0.39%** | 0.9 |
| Equal weight | +1.41% | 1.2 |
| 60/40 | +2.38% | 1.5 |
| Buy & hold | +0.05% | 1.8 |
| Performance-chasing | −2.98% | 3.4 |

At γ = 8.0 (sells past 8%) every gap widens to 2–6%, and the ranking of
who suffers least changes with the path.

The tier-matched portfolio has the smallest gap among the diversified
strategies. That is the thesis, and the size of the effect — a few tenths
of a percent at moderate risk aversion, several points at high — is the
credible version of it, not a headline.

## What it does not show

* **Capitulation is not always costly.** On a gentle, straight-line
  decline the trigger fires far above the bottom and selling is a good
  trade. There is a test asserting exactly that, because a simulation
  rigged so panicking always lost would be worthless as evidence. What
  hurts is the drop that overshoots the threshold in a session or two —
  you sell at the low — followed by a rebound that confirmation-waiting
  makes you miss.
* **The rule is a caricature.** Real investors sell partially, sell late,
  sell for reasons unrelated to drawdown, and sometimes never come back.
  One threshold and one re-entry rule is a model of a tendency, not of a
  person.
* **Single paths are noisy.** The endpoint runs one panel, and the
  ranking it reports can flip between paths. The page says so. The table
  above is a median over eight, and eight is not many either.
* **γ is doing double duty.** The same parameter sizes the portfolio and
  sets the panic threshold, so the two are not independent evidence. A
  properly convincing version would elicit loss tolerance separately —
  which is what DOSE could be extended to do.
* **Nothing here is validated against real investor behaviour.** Dalbar
  and Morningstar publish investor-return gaps from actual fund flows;
  this simulation has not been calibrated to them.

## References

* Barber, B. M., & Odean, T. (2000). "Trading is hazardous to your
  wealth." *Journal of Finance* 55(2), 773–806.
* Merton, R. C. (1969). "Lifetime portfolio selection under uncertainty."
  *Review of Economics and Statistics* 51(3), 247–257.
* Kahneman, D., & Tversky, A. (1979). "Prospect theory: an analysis of
  decision under risk." *Econometrica* 47(2), 263–291.
* Benartzi, S., & Thaler, R. H. (1995). "Myopic loss aversion and the
  equity premium puzzle." *QJE* 110(1), 73–92.
