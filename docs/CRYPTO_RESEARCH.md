# Hone Crypto — research basis and parameter choices

Hone Crypto applies the **same protocol** as the equities product to
digital assets: Holt-Laury multiple price list → CRRA maximum likelihood
with Fechner noise → 50 tiers → Ledoit-Wolf shrinkage covariance →
Black-Litterman with Idzorek confidence → γ-aware mean-variance
optimization → Merton risk budget → hedge sizing.

This document records the literature that supports reusing that protocol,
the places where crypto's statistical character strains it, and every
parameter that differs (and why).

---

## 1. Does mean-variance + Black-Litterman transfer to crypto?

The literature says yes — with the important caveat that estimation error
dominates, which is precisely the problem Black-Litterman and shrinkage
exist to solve.

- **Platanakis & Urquhart, "Portfolio management with cryptocurrencies:
  The role of estimation risk"** (*Economics Letters*, 2019) is the
  closest paper to what Hone does. It compares naïve 1/N diversification,
  plain Markowitz, and Black-Litterman with variance-based constraints on
  crypto portfolios, and finds **Black-Litterman with constraints
  delivers superior out-of-sample risk-adjusted returns and lower risk**.
  Their conclusion — that raw Markowitz on crypto is wrecked by
  estimation error, and that a Bayesian equilibrium anchor fixes it — is
  the core justification for keeping our exact pipeline rather than
  simplifying it for crypto.
  ([SSRN](https://www.ssrn.com/abstract=3287176) ·
  [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0165176519300254) ·
  [preprint PDF](https://centaur.reading.ac.uk/81734/1/ELs-Blind.Submission.R&R%5B1%5D.pdf))
- Black-Litterman-optimized crypto portfolios are reported to **bear less
  risk, hold more diversity across assets, and produce fewer extreme
  allocations** than unconstrained mean-variance — the same argument for
  the equilibrium prior we already use.
- Recent work extends MVO on crypto with additional signals (e.g.
  **sentiment-aware MVO**, arXiv 2025), confirming MVO as the standard
  backbone researchers build on rather than discard.
  ([arXiv:2508.16378](https://arxiv.org/pdf/2508.16378))
- **"Simple and Effective Portfolio Construction with Crypto Assets"**
  ([arXiv:2412.02654](https://arxiv.org/html/2412.02654v1)) and
  ([arXiv:2511.13239](https://arxiv.org/pdf/2511.13239)) treat
  risk-managed allocation — rather than directional speculation — as the
  serious approach to the asset class.

**Honest caveat, stated in the same literature:** the Gaussian-returns
and constant-covariance assumptions underpinning MVO "are often violated
in cryptocurrency markets, where returns have heavy tails and abrupt
regime shifts." We therefore keep the protocol but **do not** rely on
volatility alone to communicate risk — see §4.

## 2. Is CRRA risk elicitation valid for crypto investors?

The measurement instrument needs no change, and this is well supported:

- Switching points in a multiple price list are **a validated proxy for
  risk aversion under expected utility theory, mapping directly to CRRA
  parameters**; CRRA is "extensively used in experimental and applied
  economics due to its tractability, empirical plausibility, and
  alignment with expected utility theory when evaluating risky choices
  involving proportional or multiplicative changes in wealth."
  Proportional/multiplicative wealth changes describe crypto exactly.
- Crypto investor risk preferences are **heterogeneous and
  time-varying**, and Bitcoin is the dominant transmitter of risk-aversion
  spillovers across the asset class — supporting both (a) measuring each
  individual rather than assuming a "crypto investor" archetype, and
  (b) using BTC as the market/risk proxy.
  ([Annals of Operations Research, 2024](https://link.springer.com/article/10.1007/s10479-024-06001-9))
- Retail crypto risk perception clusters around "the possibility of
  losing money," "volatility and uncertainty," and "limiting investment
  to affordable amounts" — which is why the product expresses the risk
  budget in **dollars of drawdown** rather than in σ.
  ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214635024001096) ·
  [Journal of Asset Management](https://link.springer.com/article/10.1057/s41260-022-00302-z))

**Conclusion:** the questionnaire, the MLE, and the 50 tiers are
**byte-for-byte identical** across both products. A test asserts this
(`test_questionnaire_protocol_is_unchanged`).

## 3. Covariance estimation under heavy tails

- Shrinkage remains the right default. Work on **covariance estimation
  for minimum-variance portfolios under heavy tails** confirms shrinkage
  estimators are the practical choice, while cautioning that estimators
  tuned for *accuracy* are not always optimal for *portfolio variance*.
  ([arXiv:2606.27462](https://arxiv.org/html/2606.27462v1))
- Random-matrix-plus-shrinkage hybrids improve the bias-variance
  trade-off under heavy-tailed data
  ([arXiv:1912.03718](https://arxiv.org/pdf/1912.03718)) — a natural
  future upgrade, not a change needed for parity.
- Crypto **tail-risk is strongly interconnected**: tail dependence
  transmits across coins, and conditional tail risk (CoVaR) is large for
  BTC/ETH/XRP/LTC. This is the quantitative statement of "correlations go
  to 1 when it matters."
  ([LASSO quantile regression](https://sciencedirect.com/science/article/abs/pii/S0927539820300372?via=ihub%3D) ·
  [Conditional tail-risk in cryptocurrency markets](https://ideas.repec.org/a/eee/empfin/v50y2019icp1-19.html))
- Long-memory, asymmetric volatility models with heavy-tailed innovations
  outperform for crypto VaR
  ([Frontiers, 2025](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2025.1567626/full)).

**What we did about it:** kept Ledoit-Wolf shrinkage (same protocol), and
made the *communication* tail-aware — the stress table uses realized
crypto drawdowns (−84%, −77%) instead of model-implied losses, and the UI
states that betas rise and correlations converge in real crashes.

## 4. Hedging: stablecoins first, futures second

- **Stablecoins mitigate downside risk in crypto portfolios.** USDC acted
  as a hedge across a full sample (notably in the first five months of the
  pandemic) while USDT behaved only as a diversifier — i.e. the
  dollar-pegged leg is the reliable risk reducer.
  ([ScienceDirect, 2022](https://www.sciencedirect.com/science/article/pii/S1062940822001735))
- **Perpetual futures** neutralize downside for spot holders without
  selling, with hedge ratios typically 50–100% of exposure — but carry
  **liquidation risk from leverage and persistent funding costs that
  erode hedge effectiveness**.
- BTC futures **require only a minimal allocation** in diversified
  portfolios, and crypto "enhances diversification in normal periods and
  increases volatility during crises" — a caution against treating a
  crypto short as a benign hedge.
  ([Eurasian Economic Review, 2025](https://link.springer.com/article/10.1007/s40822-025-00353-8) ·
  [Bitcoin futures crash risk](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10825442/))
- Simulation frameworks integrating volatility, hedging, contagion and
  Monte Carlo support explicitly modeling contagion for crypto risk
  ([arXiv:2507.08915](https://arxiv.org/pdf/2507.08915)).

**What we did about it:** the hedge set is (1) a **stablecoin
allocation** — exact, no derivatives, no liquidation risk — and (2) a
short of the market proxy, which now emits an explicit **warning whenever
notional exceeds 50%** citing margin, funding and liquidation. Listed
options are omitted because they are not available via the brokerage
integration.

---

## 5. Parameter differences (and only these)

| Parameter | Equities | Crypto | Why |
|---|---|---|---|
| Periods per year | 252 | **365** | Crypto trades continuously; annualization only. |
| Market proxy | SPY | **BTC/USD** | BTC is the dominant risk factor and the documented transmitter of risk-aversion spillovers. |
| Stress scenarios | 2008 −55%, 2020 −34%, 2022 −25% | **2018 −84%, 2022 (Terra/FTX) −77%, May 2021 −53%, Mar 2020 −50%** | Realized peak-to-trough BTC drawdowns. |
| Cash leg | Cash / T-bills | **USDC or another dollar stablecoin** | Crypto-native risk-free-ish leg (see §4). |
| Options overlay | Available (live Alpaca chains) | **Disabled** | No listed crypto options through the integration. |
| Data endpoint | `/v2/stocks/bars` | `/v1beta3/crypto/us/bars` | Alpaca crypto data needs no market-data subscription. |
| Questionnaire, MLE, tiers, shrinkage, BL, MVO, Merton budget | — | **identical** | §1–§2. |

## 6. One protocol change that crypto forced — and it improved equities too

Applying the pipeline unchanged surfaced a genuine bug in the *original*
equities implementation. Reverse optimization used the **investor's own
γ** as the market's risk aversion δ:

```
Π = δ Σ w,  with δ = max(γ, 0.5)
```

Because Π scales with variance, crypto's ~15× larger variances produced
equilibrium returns near **+100%/yr**, so a genuinely bullish +50%/yr
view registered as *bearish* and the optimizer sold the asset the user
liked. Textbook Black-Litterman calibrates δ to the **market**, not the
individual. We now set

```
δ = S / σ_m,   S = 0.40 (target market Sharpe)
```

which yields δ ≈ 2.5 at σ_m ≈ 16% (the canonical equity value) and
δ ≈ 0.67 at σ_m ≈ 60%. This is applied identically in both products, so
protocol parity is preserved and the equities priors became more
principled as a side effect. See `calibrate_delta` in
`hone/optimization/black_litterman.py`.

## 7. Known limitations

1. **Volatility-based risk budgets understate crypto crash risk.** The
   Merton budget assumes σ summarizes risk; crypto's tails mean an 80%
   drawdown is not a 5σ event. The dollar stress table exists to
   compensate, but a CVaR/drawdown-based budget is the principled
   upgrade (tracked in `docs/ROADMAP.md`).
2. **Beta-approximated crash losses are optimistic** — betas rise and
   correlations converge exactly when it hurts. The UI now says so.
3. **A low-γ user can be told a 68%-volatility portfolio needs no hedge.**
   That is the identical protocol behaving correctly, and it is
   defensible for a measured risk-seeker — but it is the strongest
   argument for adding a fat-tail-aware floor.
4. **Demo mode is synthetic** (Student-t, df=4, ~55–110% vols, ρ≈0.75).
   Calibrated to look like crypto, but it is not history. Backtest
   conclusions require the live data path.
5. **No on-chain, staking, or self-custody risk** is modeled: no
   depegging, bridge failure, exchange insolvency, or smart-contract
   risk. These are real crypto risks that a covariance matrix cannot see.
