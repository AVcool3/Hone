"""Hone — hedge-fund-grade risk tooling for retail investors.

The toolkit has three parts, designed to be usable independently and
chained together into a single pipeline:

1. ``hone.risk_profile``  — Holt-Laury Multiple Price List questionnaire and
   a Maximum Likelihood (CRRA + Fechner noise) engine that produces a
   point estimate of the risk-aversion parameter gamma and places the
   user in one of 50 risk tiers.
2. ``hone.market_data``   — Alpaca paper-trading API client and the
   (business-side only) covariance matrix calculator.
3. ``hone.optimization`` / ``hone.hedging`` — Mean-Variance Optimization,
   Black-Litterman view blending, and hedge suggestions (shorts / options)
   sized to the user's risk-aversion parameter.
"""

__version__ = "0.1.0"
