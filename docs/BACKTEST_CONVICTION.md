# Do convictions actually help? A comparative backtest

The Conviction Compiler turns a plain-English thesis into a structured
view, and the confidence attached to that view is what scales how far
Black-Litterman tilts the portfolio away from equilibrium. That number is
self-reported, unverified, and multiplied straight into position sizes.
`hone/journal/` now scores that number against outcomes and rescales it
before it reaches Black-Litterman. This document asks whether any of that
machinery — the views, the confidence channel, the calibration — actually
earns its place, and for whom.

This document reports a walk-forward simulation over a *population* of
investors who differ in risk aversion (γ) and in genuine forecasting
skill. Code: `hone/backtest/conviction.py`; tests:
`tests/test_conviction_backtest.py`; sweep runner:
`research/conviction/run_conviction_backtest.py`.

---

## Headline

1. **Skill is the whole story. Confidence is a rounding error.** Whether a
   user's convictions help is determined almost entirely by whether their
   forecasts contain information. How that information is weighted —
   self-reported confidence, calibrated confidence, or no confidence
   channel at all — moves median Sharpe by ≤ 0.05 in the shipped
   configuration, against a 0.16 gap between "has skill" and "doesn't".
2. **Calibrated confidence did not beat stated confidence.** Replacing the
   user's self-report with their realized hit rate won on **27-54%** of
   investor draws in equities and **26-41%** in crypto — i.e. it lost
   more often than it won everywhere except the zero-skill equities cell.
   It helps the no-skill and the overconfident; it taxes anyone with real
   edge, because a Beta-smoothed hit rate is a slow, noisy estimator that
   caps confidence around 0.23 even for a genuinely good forecaster.
3. **A zero-skill user is made slightly worse off by using views at all.**
   In equities, views beat the view-free portfolio on only **33-48%** of
   draws at skill 0, at every γ. The product currently has no way to tell
   those users apart from the skilled ones.
4. **Taking views at face value is not catastrophic today — but only
   because the 35% position cap is hiding it.** Remove the cap and a
   no-skill user's face-value portfolio drops from Sharpe 0.394
   (view-free) to **0.184**, with an effective breadth of **1.28 names**.
   The cap, not Idzorek's Ω, is currently doing the safety work.
5. **Crypto is more favourable to views than equities**, but for an
   uncomfortable reason: the crypto baseline (`risk_only`) is weaker
   there, so there is more to beat.

---

## 1. What was compared

On the same price history, per investor draw:

| strategy | what it is |
|---|---|
| `equal_weight` | 1/N — the retail default |
| `market_hold` | buy and hold the market proxy (SPY / BTC/USD) |
| `risk_only` | Hone's γ-aware MVO on the equilibrium prior, no views |
| `views_stated_conf` | the full pipeline at the user's **self-reported** confidence — what Hone ships |
| `views_calibrated_conf` | identical views, confidence **replaced outright** by the user's realized hit rate to date |
| `views_full_conf` | views taken at **face value** (confidence = 1.0) — the naive "the LLM said so" wiring |

Strategies 4-6 receive byte-identical views. Only Ω differs, so any gap
between them is attributable to the confidence mapping and nothing else.
(`tests/test_conviction_backtest.py::test_only_omega_differs_between_view_strategies`
pins this: set stated confidence to 1.0 and the stated and face-value
equity curves coincide exactly.)

## 2. Method

**Walk-forward.** 252-day (365 for crypto) trailing estimation window,
rebalanced every 21 periods, Ledoit-Wolf shrinkage covariance,
Sharpe-calibrated δ, 1/N equilibrium prior, long-only, 35% per-name cap.
Every weight at date *t* is a function of data strictly before *t*.

**The investor's skill** is the information coefficient: the correlation
between their forecast and the realized forward return over the view
horizon (63 periods, re-issued every 21). At the decision date the
simulator — not the investor — standardizes the realized forward return
against the equilibrium prior and hands the investor
`skill × signal + √(1-skill²) × noise`. Centering the noise on the
*prior* rather than on zero makes skill = 0 a clean null: unbiased noise
around what the model already believed, rather than a systematic drag
toward minimum variance.

Skill translates to directional accuracy as
`hit_rate = 0.5 + arcsin(ρ)/π`, which is worth internalizing: an
information coefficient of **0.4 — better than most professionals ever
achieve — is a 63% hit rate**, not 80%.

**Stated confidence** is anchored where humans actually speak. The
compiler's own prompt maps hedged language to 30-45% and emphatic
language to 70-85%; nobody types "3% confident". So
`stated = clip(overconfidence × (0.30 + 0.70 × true_edge))`. A
calibrated no-skill investor still says 31%; a 2×-overconfident one says
63%.

**Calibrated confidence** is `2 × (hit_rate − 0.5)`, floored at 0.02,
where the hit rate is the investor's own resolved views to date,
Beta-smoothed with 5 pseudo-observations at chance. Views resolve only
after their horizon elapses, so there is no look-ahead.

This is deliberately the *aggressive* form of calibration: it throws the
user's number away and substitutes the measurement. What `hone/journal/`
actually ships is gentler — a logistic rescaling of the stated confidence
in log-odds space, shrunk toward the identity with 20 pseudo-counts,
inert below 5 resolutions and clipped to [0.05, 0.95]. The shipped
behaviour therefore sits *between* the `views_stated_conf` and
`views_calibrated_conf` arms measured here, and those two arms bracket
it. §9 reads the results back onto that design.

**Design.** 40 investor draws × 5 γ ∈ {0.5, 1.2, 2.5, 5.0, 8.0} × 3 skill
∈ {0, 0.2, 0.4} × 2 overconfidence ∈ {1×, 2×} × 2 asset classes = 14,400
investor-cell runs. The price path *and* the forecast-noise stream are
keyed to the investor index alone, so the design is paired: γ and skill
never change which market the investor lived through. Win rates are
computed per draw, not on pooled averages — a strategy that wins on
average but loses for 60% of users is a bad product.

**What is synthetic.** Prices come from `synthetic_universe` and
`synthetic_crypto_universe`. These are Gaussian (Student-t for crypto)
panels with constant covariance and drifts drawn *independently of
volatility*. §6 explains why that matters and re-runs the key result on a
DGP where risk is compensated.

---

## 3. Results — equities

40 draws, pooled across all five γ, calibrated stater (overconfidence
1×). Medians; `beat_*` is the fraction of the 200 draw-γ pairs in which
the strategy beat the benchmark on Sharpe.

| skill | strategy | CAGR | vol | Sharpe | Sortino | max DD | eff. N | turnover | beat risk_only | beat market_hold |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | equal_weight | 0.123 | 0.226 | 0.469 | 0.785 | −0.286 | 6.00 | 0.00 | 0.525 | 0.700 |
| 0.0 | market_hold | 0.123 | 0.337 | 0.429 | 0.718 | −0.428 | 1.00 | 0.00 | 0.360 | — |
| 0.0 | risk_only | 0.117 | 0.214 | 0.458 | 0.780 | −0.307 | 3.97 | 0.02 | — | 0.640 |
| 0.0 | stated | 0.119 | 0.231 | 0.448 | 0.748 | −0.310 | 3.66 | 0.38 | **0.430** | 0.610 |
| 0.0 | calibrated | 0.117 | 0.220 | 0.445 | 0.750 | −0.306 | 3.93 | 0.14 | 0.415 | 0.620 |
| 0.0 | face_value | 0.118 | 0.238 | 0.420 | 0.705 | −0.324 | 3.28 | 0.46 | 0.435 | 0.585 |
| 0.2 | stated | 0.138 | 0.233 | 0.522 | 0.881 | −0.298 | 3.61 | 0.40 | **0.650** | 0.720 |
| 0.2 | calibrated | 0.131 | 0.227 | 0.507 | 0.859 | −0.303 | 3.83 | 0.25 | 0.650 | 0.700 |
| 0.2 | face_value | 0.131 | 0.239 | 0.469 | 0.796 | −0.313 | 3.29 | 0.45 | 0.610 | 0.690 |
| 0.4 | stated | 0.165 | 0.234 | 0.621 | 1.059 | −0.289 | 3.53 | 0.40 | **0.830** | 0.830 |
| 0.4 | calibrated | 0.156 | 0.229 | 0.594 | 1.005 | −0.289 | 3.75 | 0.31 | 0.830 | 0.815 |
| 0.4 | face_value | 0.169 | 0.238 | 0.604 | 1.005 | −0.298 | 3.30 | 0.44 | 0.805 | 0.800 |

At 2× overconfidence the only row that moves is `stated`: Sharpe falls
from 0.448 → 0.424 (skill 0), 0.522 → 0.473 (skill 0.2), 0.621 → 0.605
(skill 0.4). Doubling a user's stated confidence costs at most ~0.05
Sharpe.

## 4. Results — crypto

Same design, 365-day annualization, BTC/USD proxy, 1,460-day panels.

| skill | strategy | CAGR | vol | Sharpe | Sortino | max DD | eff. N | turnover | beat risk_only | beat market_hold |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | equal_weight | 0.302 | 0.725 | 0.667 | 1.092 | −0.680 | 6.00 | 0.00 | 0.650 | 0.800 |
| 0.0 | market_hold | 0.155 | 0.541 | 0.465 | 0.657 | −0.632 | 1.00 | 0.00 | 0.240 | — |
| 0.0 | risk_only | 0.240 | 0.603 | 0.592 | 0.940 | −0.646 | 3.21 | 0.01 | — | 0.760 |
| 0.0 | stated | 0.294 | 0.716 | 0.658 | 1.026 | −0.681 | 3.24 | 0.39 | **0.565** | 0.745 |
| 0.0 | calibrated | 0.287 | 0.643 | 0.657 | 1.025 | −0.664 | 3.30 | 0.21 | 0.575 | 0.755 |
| 0.0 | face_value | 0.262 | 0.743 | 0.633 | 0.979 | −0.692 | 3.14 | 0.45 | 0.580 | 0.780 |
| 0.2 | stated | 0.378 | 0.724 | 0.744 | 1.174 | −0.661 | 3.22 | 0.40 | **0.790** | 0.820 |
| 0.2 | calibrated | 0.355 | 0.670 | 0.729 | 1.130 | −0.651 | 3.30 | 0.29 | 0.730 | 0.785 |
| 0.2 | face_value | 0.347 | 0.740 | 0.718 | 1.132 | −0.663 | 3.13 | 0.44 | 0.735 | 0.840 |
| 0.4 | stated | 0.446 | 0.728 | 0.820 | 1.305 | −0.642 | 3.21 | 0.39 | **0.915** | 0.855 |
| 0.4 | calibrated | 0.423 | 0.687 | 0.800 | 1.246 | −0.632 | 3.27 | 0.33 | 0.880 | 0.855 |
| 0.4 | face_value | 0.464 | 0.737 | 0.835 | 1.317 | −0.640 | 3.13 | 0.43 | 0.915 | 0.870 |

The crypto picture looks friendlier to views at every skill level, but
note *why*: `risk_only` there posts Sharpe 0.592 against 1/N's 0.667. The
equilibrium prior does worse in crypto, so views have a weaker baseline
to beat. This is a statement about the baseline, not about the views.

## 5. Does confidence calibration matter?

Paired per draw — the fraction of investor draws in which the left-hand
strategy beat the right-hand one on Sharpe. 0.500 means a coin flip.

**Equities**

| skill | overconf. | calibrated > stated | stated > face_value | calibrated > face_value | stated > risk_only |
|---|---|---|---|---|---|
| 0.0 | 1× | 0.540 | 0.555 | 0.570 | 0.430 |
| 0.0 | 2× | 0.555 | 0.500 | 0.570 | 0.420 |
| 0.2 | 1× | 0.370 | 0.555 | 0.455 | 0.650 |
| 0.2 | 2× | 0.425 | 0.525 | 0.455 | 0.640 |
| 0.4 | 1× | 0.270 | 0.575 | 0.380 | 0.830 |
| 0.4 | 2× | 0.380 | 0.555 | 0.380 | 0.815 |

**Crypto**

| skill | overconf. | calibrated > stated | stated > face_value | calibrated > face_value | stated > risk_only |
|---|---|---|---|---|---|
| 0.0 | 1× | 0.410 | 0.470 | 0.440 | 0.565 |
| 0.0 | 2× | 0.395 | 0.500 | 0.440 | 0.605 |
| 0.2 | 1× | 0.290 | 0.520 | 0.415 | 0.790 |
| 0.2 | 2× | 0.390 | 0.540 | 0.415 | 0.770 |
| 0.4 | 1× | 0.265 | 0.470 | 0.355 | 0.915 |
| 0.4 | 2× | 0.345 | 0.510 | 0.355 | 0.915 |

Read plainly:

- **Calibration loses.** The only cell where calibrated confidence beats
  stated confidence more often than not is zero-skill equities (0.540 /
  0.555) — and there the entire strategy is under water versus
  `risk_only` anyway. At skill 0.4 calibration wins only 27% of draws.
- **Calibration does exactly what it is supposed to do; that is the
  problem.** Measured hit rates come out at 0.511 / 0.580 / 0.640 for
  skill 0 / 0.2 / 0.4, so calibrated confidence lands at 0.07 / 0.15 /
  0.23. A genuinely skilled user's views get 23% weight instead of the
  48% they asked for, and the portfolio stays too close to equilibrium to
  capture the edge they actually have.
- **The overconfidence case is where it earns something.** Every
  `calibrated > stated` figure rises when the user is 2× overconfident
  (0.270 → 0.380, 0.290 → 0.390). Calibration is insurance against
  miscalibration, not a performance improvement.
- **The confidence channel as a whole is weak.** `stated > face_value` sits
  at 0.47-0.58 across every cell in both asset classes — statistically
  indistinguishable from a coin flip on 40 draws. In the shipped
  configuration, the difference between a carefully elicited confidence
  and no confidence model at all is close to nothing.

## 6. Does the answer depend on γ?

Median Sharpe by γ, equities, calibrated stater:

| skill | γ | risk_only | stated | calibrated | face_value |
|---|---|---|---|---|---|
| 0.0 | 0.5 | 0.468 | 0.421 | 0.409 | 0.406 |
| 0.0 | 1.2 | 0.450 | 0.411 | 0.382 | 0.435 |
| 0.0 | 2.5 | 0.471 | 0.437 | 0.456 | 0.424 |
| 0.0 | 5.0 | 0.468 | 0.457 | 0.511 | 0.420 |
| 0.0 | 8.0 | 0.448 | 0.467 | 0.523 | 0.442 |
| 0.4 | 0.5 | 0.468 | 0.548 | 0.545 | 0.557 |
| 0.4 | 1.2 | 0.450 | 0.598 | 0.592 | 0.603 |
| 0.4 | 2.5 | 0.471 | 0.601 | 0.604 | 0.605 |
| 0.4 | 5.0 | 0.468 | 0.639 | 0.622 | 0.596 |
| 0.4 | 8.0 | 0.448 | 0.659 | 0.620 | 0.668 |

`beat_risk_only` for `stated` in equities rises monotonically with γ at
skill 0.4: 0.800, 0.775, 0.825, 0.850, **0.900**. At skill 0 it stays flat
and below chance at every γ: 0.475, 0.400, 0.400, 0.425, 0.450.

There is one genuine γ effect, and it is the sensible one: **the more
risk-averse the investor, the more the confidence discount is worth.** At
zero skill, calibrated confidence goes from the *worst* view strategy at
γ = 0.5 (0.409 vs `risk_only`'s 0.468) to the best at γ = 5 and γ = 8
(0.511 vs 0.468, and 0.523 vs 0.448 — the only view strategy clearly
above the baseline at both). A high-γ investor is the one most damaged by
having noise injected into μ, so muting the noise is worth most to them.
Crypto shows the same tendency more weakly and noisily.

## 7. Robustness checks

### 7.1 The synthetic DGP is unfair to `risk_only`

`synthetic_universe` draws each asset's drift independently of its
volatility. Hone's equilibrium prior is `Π = δ Σ w`, which asserts the
opposite: more covariance with the market means more expected return. The
prior is therefore *misspecified by construction* in the default panels,
and `risk_only`'s mediocre showing versus 1/N (it wins 47.5% of draws) is
partly an artefact.

Re-running the key slice on a panel where every asset prices at the same
0.40 Sharpe (`research/conviction/sensitivity_dgp.py`, 24 draws, γ ∈ {1.2, 2.5,
8.0}):

| skill | strategy | Sharpe | CAGR | eff. N | beat risk_only |
|---|---|---|---|---|---|
| 0.0 | equal_weight | 0.680 | 0.174 | 6.00 | 0.583 |
| 0.0 | risk_only | 0.681 | 0.168 | 4.43 | — |
| 0.0 | stated | 0.674 | 0.170 | 3.65 | 0.389 |
| 0.0 | calibrated | 0.665 | 0.161 | 4.10 | 0.292 |
| 0.0 | face_value | 0.654 | 0.170 | 3.27 | 0.417 |
| 0.2 | stated | 0.776 | 0.207 | 3.60 | 0.569 |
| 0.2 | calibrated | 0.714 | 0.195 | 3.82 | 0.583 |
| 0.2 | face_value | 0.744 | 0.208 | 3.26 | 0.639 |
| 0.4 | stated | 0.868 | 0.235 | 3.53 | 0.778 |
| 0.4 | calibrated | 0.834 | 0.214 | 3.72 | 0.736 |
| 0.4 | face_value | 0.846 | 0.235 | 3.28 | 0.764 |

`risk_only` now ties 1/N exactly (0.681 vs 0.680), confirming the
artefact. Every qualitative conclusion survives: zero-skill views are
mildly harmful (29-42% win rate), calibration still trails stated
confidence at positive skill, and the spread across confidence treatments
stays small relative to the spread across skill. The crypto cell where
zero-skill views appeared to *help* does not survive — treat that as a
baseline artefact, not a finding.

### 7.2 The 35% position cap is doing the safety work

One slice (equities, γ = 2.5, 24 draws) at the shipped cap and with the
cap removed (`research/conviction/sensitivity_cap.py`):

| cap | skill | strategy | Sharpe | CAGR | eff. N | turnover |
|---|---|---|---|---|---|---|
| 0.35 | 0.0 | risk_only | 0.390 | 0.101 | 5.38 | 0.01 |
| 0.35 | 0.0 | stated | 0.358 | 0.102 | 3.75 | 0.42 |
| 0.35 | 0.0 | calibrated | 0.407 | 0.110 | 4.80 | 0.18 |
| 0.35 | 0.0 | face_value | 0.367 | 0.106 | 3.27 | 0.48 |
| **1.00** | 0.0 | risk_only | 0.394 | 0.102 | 5.38 | 0.01 |
| **1.00** | 0.0 | stated | **0.231** | 0.069 | 2.07 | 0.69 |
| **1.00** | 0.0 | calibrated | **0.351** | 0.095 | 4.45 | 0.23 |
| **1.00** | 0.0 | face_value | **0.184** | 0.055 | 1.28 | 0.77 |
| 1.00 | 0.4 | stated | 0.665 | 0.190 | 1.70 | 0.72 |
| 1.00 | 0.4 | calibrated | 0.607 | 0.167 | 2.69 | 0.58 |
| 1.00 | 0.4 | face_value | 0.597 | 0.180 | 1.29 | 0.77 |

Uncapped, a no-skill user's face-value portfolio is a **1.28-name bet**
that loses **53% of the view-free Sharpe** (0.184 vs 0.394) and 4.7
percentage points of annual return. Calibrated confidence is the only
treatment that keeps such a user near the view-free baseline (0.351,
effective breadth 4.45). Two things follow: the cap is currently
substituting for a confidence model, and **the value of calibration is
conditional on how tightly the portfolio is otherwise constrained** — it
is worth far more for a concentrated book than for a capped six-name one.

### 7.3 `View.expected_return` explodes on short horizons

A view is a target price plus a horizon; `View.expected_return`
annualizes it as a CAGR. Over 10 seeds of zero-skill quarterly targets:

| asset class | mean implied return | median | > +100%/yr | > +1000%/yr | max |
|---|---|---|---|---|---|
| equities | +27%/yr | +4%/yr | 13% | 0.0% | +900%/yr |
| crypto | +962%/yr | +19%/yr | 40% | 12% | +130,300%/yr |

The median is sane; the tail is not. Exponentiating a noisy quarterly
return to an annual rate is explosive in high-volatility assets, and 12%
of crypto convictions produce a Q entry above +1000%/yr. At full
confidence these go straight into μ and pin the optimizer against its
bound. This is a live product hazard independent of everything else in
this document: a user who types a plausible three-month BTC target can
generate an expected-return input that no risk model should be asked to
digest.

### 7.4 Costs are not charged

The backtest is frictionless. One-way turnover per rebalance is 0.02 for
`risk_only` versus 0.38-0.46 for the view strategies — roughly **4.8×
book turnover per year** against 0.2×. At 10bp per side that is ~0.48%/yr
for stated confidence and ~0.02%/yr for `risk_only`. That fee is
comfortably covered at skill 0.4 (+4.8pp CAGR), roughly half-eaten at
skill 0.2 (+2.1pp), and pure loss at skill 0. Calibrated confidence cuts
turnover by 45-63% for low-skill users, which is a real advantage the
frictionless Sharpe comparison above does not credit it for.

---

## 8. Honest reading

**Where Hone's machinery clearly helps.** A user with a genuine
information coefficient of 0.2-0.4 is better off running their views
through Black-Litterman + MVO than not: +2.1 to +4.8 percentage points of
CAGR in equities, +0.06 to +0.16 Sharpe, winning on 65-83% of draws in
equities and 79-92% in crypto, with no increase in drawdown. That is a
real and reasonably robust result, and it holds at every γ tested.

**Where it does not help.** For a user with no edge — which, given that
an IC of 0.2 is professional-grade, is most users — views are a small
negative in equities (win rate 0.33-0.48 versus the view-free portfolio at
every γ) and a wash after costs. The product cannot presently distinguish
these users from skilled ones, and the confidence they self-report does
not distinguish them either: a no-skill investor and a skilled one both
say something in the 30-50% band.

**Where the specific claim about confidence fails.** The Idzorek
confidence channel is close to inert as shipped. Stated confidence beats
face value on 47-58% of draws — a coin flip. Doubling every user's stated
confidence costs at most 0.05 Sharpe. The 35% cap and the long-only
constraint are absorbing what Ω was supposed to absorb. If this project's
pitch is "your confidence sizes the tilt", the honest version is "your
confidence sizes the tilt within bounds that already do most of the
work".

**Where calibration fails.** Replacing self-reported confidence with a
realized hit rate is not a free improvement. It loses to self-report on
63-74% of draws for skilled users, because a Beta-smoothed directional hit
rate is a low-power estimator: after ~90 resolved views, a true IC of 0.4
still only reads as 0.64 accuracy, mapping to 0.23 confidence. The
correction is right in direction and far too blunt in magnitude.

**A trap the journal walks into.** The naive scoring metric — "you said
up, it went up" — is contaminated by drift, and `resolve_prediction`'s
`direction_hit` is exactly that metric. See §9.

**Limits of this evidence.** Synthetic Gaussian/Student-t prices with
constant covariance and no regime shifts; no transaction costs, taxes, or
slippage; one view horizon (63 periods) and two views per rebalance; skill
modelled as a stationary information coefficient with independent
per-asset noise, whereas real conviction errors are correlated across
names and clustered in time (everyone is wrong about the same thing at the
same moment, which is when it hurts most); 40 draws, so win rates carry a
standard error of roughly ±8pp and differences under ~15pp should not be
over-read. Nothing here has been validated on real price history.

---

## 9. Reading this back onto `hone/journal/`

The journal and its Brier calibration landed alongside this backtest, and
`apply_calibration` is already wired into the rebalance endpoint. The
results say the shipped design got the important call right and leave
three concrete corrections.

**The gentle design is the correct one.** Full replacement of stated
confidence by a measured hit rate — the `views_calibrated_conf` arm — is a
*net negative* for anyone with real edge, losing on 63-74% of draws at
skill 0.2-0.4. What ships instead is a logistic rescale shrunk toward the
identity with 20 pseudo-counts, which moves a user only part of the way
toward the measurement. That is the right place to sit: the evidence
supports damping a self-report, not overriding it. Had the blunt version
shipped, this backtest would be an argument to revert it.

**`MIN_FOR_ADJUSTMENT = 5` is too low to act on, even with shrinkage.**
Directional accuracy in these runs reads 0.511 / 0.580 / 0.640 for true
IC of 0 / 0.2 / 0.4. Separating those requires on the order of 100
resolved predictions; at n = 5 the standard error on a hit rate is ±22
percentage points, which spans the entire range the parameter is trying to
distinguish. The K = 20 pseudo-count means a 5-observation user is moved
only 20% of the way, which limits the damage — but the threshold governs
what the *user is told*, and telling someone they are overconfident on
five coin flips is the failure mode `describe()` should not have. Raise
the actionable threshold, or state the interval alongside the number.

**`direction_hit` is drift-contaminated; do not promote it.**
`resolve_prediction` defines it as "final > entry", which in a rising
market is right most of the time regardless of skill. In these runs a
*zero-skill* investor measured 0.511-0.513 directional accuracy against a
0.491-0.506 surprise accuracy (forecast versus the equilibrium prior); the
gap is small only because the synthetic drifts are modest. Real bull-market
drift will hand coin-flippers a 60%+ "hit rate". The Brier score already
uses the harder `target_hit` event, which is better, but a bullish target
in a rising market is still easier than a bearish one — the drift-free
version scores the forecast against `Π` for that asset and horizon, which
the journal has everything it needs to compute.

**Two changes look higher-leverage than any calibration tuning**, and both
fall out of §7:

- Cap or transform the annualized view return before it reaches
  Black-Litterman (§7.3). Convictions implying +1000%/yr are an input
  error, not a signal, and no confidence weighting rescues them. This is
  the single most likely source of a genuinely bad allocation today.
- Treat the 35% position cap as a first-class, documented risk control
  rather than an incidental default (§7.2). It is currently the main thing
  standing between a face-value view and a one-name portfolio, and the
  value of the entire confidence channel is conditional on it. Keying it to
  γ would make that explicit.

**Do not claim calibration improves returns.** On this evidence it does
not: it is a guardrail against a known failure mode (overconfidence,
concentration), worth most to high-γ users, to the demonstrably
overconfident, and to anyone whose book is not otherwise capped. Every
`calibrated > stated` figure in §5 rises when the user is 2× overconfident
(0.270 → 0.380, 0.290 → 0.390), and §7.2 shows the effect becomes large
once the position cap stops binding. It also cuts turnover by 45-63% for
low-skill users (§7.4), which is a real saving the frictionless Sharpe
comparison does not credit. Those are the honest claims. "It makes your
portfolio perform better" is not one of them.

---

## Reproducing

```bash
python -m pytest tests/test_conviction_backtest.py -q     # ~8s, offline
python research/conviction/run_conviction_backtest.py --investors 40 --workers 4
python research/conviction/analyze.py            # the §3-§6 tables
python research/conviction/sensitivity_dgp.py    # §7.1
python research/conviction/sensitivity_cap.py    # §7.2
```

Everything is seeded and runs offline; the parallel runner reproduces a
serial run row for row. `research/conviction/results/summary_*.csv` and
`diagnostics_*.csv` are the outputs behind every table above (the ~4 MB
per-investor panels are regenerated rather than stored).
