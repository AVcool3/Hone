# Hone — know your number

## The one-liner

Hedge funds quantify risk tolerance before they invest a dollar. Retail
investors get a three-question quiz and a "moderate" sticker. Hone gives
individual investors the same measurement science the professionals use —
and then makes every portfolio decision answer to it.

## The problem

Every brokerage onboarding asks some version of "How would you feel if
your portfolio dropped 20%?" and sorts you into Conservative, Moderate,
or Aggressive. That label then quietly governs the most consequential
financial decisions of your life — while being unfalsifiable, unstable,
and untethered to any model of behavior.

Meanwhile, the quantitative machinery that institutions run on — utility
theory, covariance estimation, portfolio optimization, systematic
hedging — has been fully described in public academic literature for
decades. It never reached individuals, not because it's secret, but
because it was never packaged for them.

The result is a familiar failure mode: investors take on more risk than
they can psychologically carry, discover this only inside a drawdown,
and sell at the bottom. The damage isn't caused by markets. It's caused
by the mismatch between a portfolio and the person holding it.

## What Hone does

Hone is built on a simple conviction: **your risk tolerance is a
measurable number, and your portfolio should be built around it.**

**1. Measure.** Instead of asking how you'd feel about losses, Hone
observes what you choose. A Holt-Laury lottery experiment — the standard
instrument in experimental economics since 2002 — presents thirty
structured choices between safer and riskier gambles at escalating
stakes. A maximum-likelihood engine fits a constant-relative-risk-
aversion utility model to your choices, separating your true preference
from decision noise, and produces a point estimate of your risk-aversion
parameter γ with a confidence interval. You're placed in one of fifty
tiers, from aggressively risk-seeking to highly risk-averse. Not a
vibe — a coefficient.

**2. Diagnose.** Hone connects to your brokerage account, reads your
actual holdings, and builds the statistical fingerprint of your
portfolio: how your assets move together, and how much risk you're
really carrying. Because the same math runs in reverse, Hone can also
infer the risk tolerance your portfolio *implies* — and show you the gap
between who you say you are and how your money is invested.

**3. Reweight.** When you have conviction — "I think this stock reaches
$400 within a year, and I'm 60% confident" — Hone doesn't ignore it or
blindly obey it. Black-Litterman, the model built at Goldman Sachs for
exactly this purpose, blends your view against market equilibrium in
proportion to your stated confidence. Mean-variance optimization then
rebuilds your weights with your measured γ setting the risk appetite.
Your conviction, disciplined by your own number.

**4. Hedge.** If your portfolio runs hotter than your tier can tolerate,
Hone sizes the professional's toolkit to close the gap: an index short
that brings volatility exactly to your budget, protective puts with a
floor set by your risk aversion, or a zero-cost collar that trades
upside you don't need for protection you do. Costed, explained, and
sized to *you*.

## What Hone is not

Hone is not investment advice, not a robo-advisor that hides the
machinery, and not a signal service. It doesn't predict markets. It
makes one promise only: the risk you carry will be the risk you chose,
measured honestly. Every recommendation shows its work — the model, the
inputs, and the assumptions are on the table.

## The goal

Financial self-knowledge, quantified. In the long run, Hone wants
"What's your risk number?" to be as answerable as "What's your credit
score?" — and wants every retail portfolio to be able to justify itself
against the number of the person who owns it.

The gap between institutional and individual investing was never about
intelligence. It was about tooling. That gap is now closeable.

---

*Hone runs on the Holt-Laury multiple price list (2002), CRRA expected
utility with Fechner-noise maximum likelihood estimation, Ledoit-Wolf
covariance shrinkage, Black-Litterman equilibrium blending with Idzorek
confidence mapping, Markowitz mean-variance optimization, and
Merton-rule risk budgeting — the standard quantitative canon, applied to
one person at a time.*
