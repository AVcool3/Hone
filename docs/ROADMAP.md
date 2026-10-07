# Roadmap — taking Hone to the next level

Ideas ordered roughly by leverage: how much each moves the product per
unit of effort. Items marked ★ are the highest-conviction bets.

## Measurement (Part 1)

- ★ **Stated vs. revealed risk aversion.** Reverse-optimize the user's
  actual holdings to extract the γ their portfolio implies, and show it
  next to their questionnaire γ: "You answer like Tier 31 but invest
  like Tier 8." The gap is the single most shareable, most actionable
  insight the data can produce. (All the math already exists in
  `black_litterman.implied_equilibrium_returns` — this is a UI feature.)
- ★ **Loss aversion (prospect theory λ).** Add a short gain/loss-framed
  lottery block (Tanaka-Camerer-Nguyen style) and estimate λ alongside
  γ. Hedging then keys the put floor to λ (fear of losses) and the vol
  budget to γ (dislike of variance) — two-parameter personalization no
  mainstream tool has.
- **γ history and retest cadence.** Preferences drift with age, markets,
  and life events. Store every elicitation, chart the trajectory, prompt
  a quarterly retest. (Requires accounts — already scoped.)
- **Consistency diagnostics.** Surface the noise parameter μ to users as
  a "decision consistency" score; flag scale-sensitivity (different
  switch points at $2 vs $200 stakes) as its own insight.

## Risk expression (Part 2)

- ★ **Dollars and drawdowns, not volatility.** Translate every risk
  number into dollar terms on the user's actual balance, and add
  historical scenario replays (2008, 2020, 2022): "In a 2008, this
  portfolio loses ~$23,000; your tier tolerates ~$9,000."
- **CVaR / max-drawdown risk budget.** Offer expected-shortfall or
  drawdown as the budget the hedging engine targets instead of vol —
  closer to how people actually experience risk.
- **Risk drift alerts.** Recompute portfolio vol vs. tier budget on a
  schedule; email/push when the portfolio drifts more than N tiers hot.
  Turns a one-shot tool into a recurring relationship.
- **Regime awareness.** Flag when EWMA correlations spike vs. the
  long-run estimate ("diversification is currently weaker than normal").

## Portfolio & hedging (Part 3)

- ★ **One-click paper execution.** `submit_order` exists; wire an
  "Execute rebalance + hedge" button against the Alpaca paper account,
  then track realized before/after performance. Learning by doing is
  what converts trust into habit.
- **Live options chains.** Alpaca's options paper trading gives real
  strikes/premiums; replace indicative Black-Scholes hedge costs with
  executable quotes, and place the collar as a real paper order.
- **Transaction-cost & turnover penalty in MVO.** Stops the optimizer
  suggesting 1% dust trades; add a "minimum trade size" and a
  cost-adjusted certainty-equivalent comparison ("this rebalance is
  worth +0.8%/yr after costs").
- **Robust optimization.** Michaud-style resampling or worst-case
  (box-uncertainty) MVO so weights stop being twitchy to estimation
  error in μ.
- **Multiple simultaneous views with consistency check.** Warn when a
  user's views are internally contradictory given correlations.

## Product & trust

- **Accounts + persistence** (scoped: SQLite storage, session auth,
  encrypted key storage, saved profiles/views).
- **Plain-English explanations everywhere.** Every recommendation gets a
  "why": "Sell MSFT: it's 45% of your portfolio and contributes more
  variance than expected return at your tier."
- **Evidence page.** Backtest tier-matched portfolios vs. naive
  alternatives on risk-adjusted return and drawdown-behavior metrics;
  publish the methodology. The credibility asset for a math-forward
  product.
- **Education layer.** Every concept (γ, covariance, collar) gets a
  two-sentence tooltip; the product doubles as a financial-literacy
  course the user takes by accident.
- **Peer context.** "Your tier vs. the distribution of Hone users" —
  `percentile_hint` already computes the raw material.
- **Compliance posture.** Keep positioning as decision-support /
  education, not advice; revisit registered-advisor requirements before
  any real-money execution feature.

## Business

- ★ **B2B risk-profiling API.** Advisors are legally required to assess
  client risk tolerance, and incumbent tools are unfalsifiable
  three-bucket quizzes. White-label the Holt-Laury + MLE engine
  (questionnaire in, γ + tier + confidence interval out) for RIAs and
  fintechs. The retail app is the demo; the API is the revenue.
- **Freemium split.** Free: questionnaire, tier, demo pipeline. Paid:
  live account link, hedge plans, drift alerts, γ history.
