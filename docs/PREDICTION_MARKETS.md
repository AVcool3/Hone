# Hone Markets — hedging cyclical income with event contracts
> **The current model, every rule and the evidence for it: [HEDGE_MODEL.md](HEDGE_MODEL.md).**


The stocks and crypto products answer one question: *given how much risk you
can carry, how much of this risky asset should you hold?* This product
answers the mirror image for people whose **paycheck is the risky asset**.
A ski instructor's season depends on snowfall; an ad-agency freelancer's
bookings on ad budgets; a recruiter's fees on hiring; a realtor's
commissions on mortgage rates. Each of them holds a position they never
chose, and [Kalshi](https://kalshi.com) — a CFTC-regulated exchange for
event contracts — lists contracts on exactly those events.

This document records the theory the tab runs on, how each piece maps onto
machinery Hone already had, the market catalog and where its data comes
from, and the honest list of what the tool cannot do.

Everything lives in `hone/prediction/`; the page is the third product tab
at `/prediction-markets`; the API is `GET /api/predict/markets` and
`POST /api/predict/hedge`.

---

## 1. The problem, in Hone's own terms

Hone measures a person's constant-relative-risk-aversion parameter γ with
an adaptive questionnaire and uses it everywhere downstream through the
utility function

    U(w) = w^(1−γ) / (1−γ)            (γ = 1: U(w) = ln w)

and the **certainty equivalent** CE = U⁻¹(E[U(w)]) — the sure amount worth
the same to this person as an uncertain prospect. The "Certainty equivalent"
tile on the rebalance page is this number for a stock portfolio.

A season of income is a prospect of the same kind. Over the horizon a person
expects wealth W (earnings plus the savings a bad season would eat). If the
bad outcome D happens they lose L. An event contract B pays $1 when the
market's event resolves the way that accompanies the bad outcome; it costs
c per contract plus fees. Buying n contracts leaves

    wealth = W − L·D + n·(B − c) − fee(n, c)

and the person chooses n to maximize E[U(wealth)]. That is the mean-variance
problem of the optimize page with a binary asset in place of stocks. The
code is `hone/prediction/hedge.py::hedge_income`; the maximization is exact
(bounded scalar optimization over n, with n kept inside the solvency bounds
that keep wealth positive in every state).

## 2. A price is a probability

A Kalshi contract pays $1.00 on YES and $0 on NO; YES and NO prices sum to
$1. A YES at 35¢ is the market saying 35%. Two frictions are modelled:

* **The spread.** Buyers pay the ask. In thin weather markets the ask can sit
  20–50¢ above the bid (the Northstar snowfall ladder had a 44¢ bid / $1.00
  ask on the day the snapshot was taken). The catalog reports the spread and
  the tool prices at the ask of the side being bought, never the midpoint.
* **The fee.** Kalshi's taker fee is `ceil_to_cent(0.07 × C × P × (1 − P))`
  times a per-series multiplier the API reports as `fee_multiplier`;
  largest on coin flips, near zero at the extremes. Resting orders are
  generally free. The optimizer uses the smooth (unrounded) fee so the
  objective stays concave, then reports the rounded one. Schedules change;
  the page says the figure is indicative.

`hone/prediction/contracts.py` holds `kalshi_fee`, `implied_probability` (the
midpoint when both sides are quoted, the last trade when the book is empty —
a $0.00 bid / $1.00 ask is not a 50% opinion) and the `Contract` type.

## 3. The answer always splits into insurance and a bet

For a small position the CRRA problem is approximately mean-variance.
Writing q for the probability of the bad outcome (after blending, §5) and ρ
for the correlation between the market's event and the person's own loss
(§4), the first-order condition gives

    n* ≈ ρ·L  +  W·(q − c) / (γ·q·(1 − q))

* **ρ·L is the pure hedge** — the position minimizing the variance of
  wealth. It does not depend on price or on γ. It is the exact analogue of
  the beta-sized index short in `hone/hedging/short_hedge`: the hedge is
  scaled by how much of the risk the instrument can see, and capped at the
  minimum-variance size.
* **The second term is a bet** on the gap between the person's probability
  and the price, shrunk by γ and by the event's own uncertainty. At a fair
  price with no fees it is zero and *any* risk-averse person hedges the whole
  loss — a result the test suite asserts exactly (`contracts == L`,
  `std_hedged == 0`). Fees act like a higher price and shrink the hedge; a
  contract the person believes is cheap adds to it.

The page reports the exact optimum and this decomposition side by side, so
a "hedge" that has quietly become a bet is labelled as one. With no exposure
(L = 0) the whole position is the bet, and the result reduces to CRRA bet
sizing: the Kelly fraction (q − c)/(1 − c) at γ = 1, and roughly Kelly/γ
above it — which is where "half Kelly" comes from.

## 4. Basis risk

The contract resolves on a weather station or a government statistic; the
income depends on visitors and bookings. The tool asks for the correlation
ρ ∈ [0, 1] between the two and builds the joint distribution of (contract
pays, income lost) from the shared marginal q and ρ:

    P(both) = q² + ρ·q(1 − q)

ρ is clipped into the Fréchet-feasible range and the value used is reported.
Negative ρ is excluded on purpose: the user picks the contract side so that it
pays when they lose, and a side that paid when they won is not a hedge. The
residual variance (1 − ρ²) of the original stays with the person whatever they
buy, which is why the catalog labels every market **direct**, **close** or
**proxy**, and why the worked example on the concepts page shows the same
exposure at ρ = 0.9 and ρ = 0.6.

How to estimate ρ honestly: count past bad seasons in which the market's number
also came in bad. Every year it did not is a year the hedge would have paid
nothing while income fell anyway.

## 5. The user's view against the market

The market price aggregates everyone else's information. A user who thinks
the odds differ is not taken at their word: the belief is blended the
Black-Litterman way,

    q* = (1 − κ)·p_market + κ·q_user

with the market price as the equilibrium prior, the user's probability as the
view and their confidence κ ∈ [0, 1] as the weight — Idzorek's reading, in
which 100% confidence adopts the view outright. The result is clipped to
[0.01, 0.99] so no certainty can let the optimizer bet everything. A blended
probability more than 15 points from the price triggers a warning.

Prediction markets are the one place a stated confidence can be *scored*: a
probability that resolves YES or NO is exactly what a Brier score measures,
which is the currency of Hone's decision journal (`docs/CALIBRATION.md`).
When the journal's calibration map is actionable the `/api/predict/hedge`
endpoint applies it to κ before blending, using the same `apply_calibration`
as the views page, and the result discloses both the stated and the used
confidence.

## 6. What the hedge is worth, and the most to pay for it

Two numbers turn the position into a decision:

* **Certainty-equivalent gain** CE(n*) − CE(0): the dollar value of the
  insurance to this person. Higher γ values it more; a risk-neutral person
  values it at zero.
* **The reservation price** — the most the person should pay per contract —
  has a closed form. At the price where the first contract is exactly worth
  buying, the marginal condition E[U′(W₀)(B − c)] = 0 gives

      c_max = E[U′(W₀)·B] / E[U′(W₀)]        with U′(w) = w^(−γ)

  the person's probability of the event re-weighted by how much a dollar is
  worth in each state. For the worked example (W = $38,000, L = $9,000,
  q = 35%, γ = 1.5) it is 45¢ against a fair 35¢: the 10¢ gap is the
  insurance premium this person's risk aversion will rationally pay. Above
  c_max the tool shows no position. At γ = 0 it collapses to q.

This is the Merton risk budget of the hedge page written for a binary event:
how much expected return the person's γ gives up to remove risk.

## 7. Where each piece already lived in Hone

| Here | Elsewhere in Hone |
|---|---|
| Risk number γ, 50 tiers | `hone/risk_profile` — the same questionnaire, shared across tabs; a γ measured on the Stocks tab is offered on this one |
| Certainty-equivalent gain | The "Certainty equivalent" tile on the rebalance page (`hone/optimization/mvo.py`) |
| Pure hedge ρ·L | The beta-sized index short (`hone/hedging/hedge.py::short_hedge`, `portfolio_beta`) |
| Reservation price c_max | The Merton risk budget (`gamma_target_volatility`) |
| Blending odds with the price | Black-Litterman + Idzorek (`hone/optimization/black_litterman.py`) |
| Confidence corrected by the record | The journal's Brier scoring and calibration map (`hone/journal/calibration.py`) |
| Season with/without the hedge | The stress table on the hedge page |

## 8. The market catalog and its data

`hone/prediction/kalshi_client.py::INDUSTRIES` is the curated list: 41 series
in six groups — snow and the ski season (Aspen monthly snowfall, Vail Resorts
skier visits, Colorado and Tahoe resort opening dates, Northstar season
snowfall, New Hampshire and Utah skier visits), advertising and media
(monthly ad-spend indices by category, Super Bowl advertisers), hiring and
layoffs (unemployment, payrolls, weekly claims, holiday retail hiring, tech
layoffs), housing and rates, travel and hospitality (Orlando room nights,
Florida visitors, cruise and hotel KPIs), and fuel and the cost of living.
Each entry carries a basis verdict and the side a hedger buys.

Data comes from Kalshi's public REST API (`/trade-api/v2/markets?series_ticker=…`,
no account needed). The server returns at once with the bundled
`kalshi_snapshot.json` and refreshes from the live API in a background thread,
caching for ten minutes; `source` in the response says which you got.
`HONE_KALSHI_LIVE=0` disables live fetching. The snapshot was generated with
`research/prediction/fetch_kalshi_snapshot.py` on 3 November 2026 and should
be refreshed when a new season's contracts list (Aspen's December 2026 series
existed but had no open contracts that day).

Hone holds no Kalshi credentials and places no orders. It reads prices, sizes
a position and explains it.

## 9. What this cannot do

* **Remove basis risk.** A proxy hedge leaves the uncorrelated part of the
  season untouched, and even a direct hedge resolves on a measurement rather
  than on a bank balance.
* **See the order book you will trade in.** Thin markets may not fill at the
  ask; Kalshi imposes per-market position limits; fee schedules change.
  Volume and spread are shown so the user can judge.
* **Model more than one period and one binary event.** A real season has many
  months and many thresholds, and the contract settles on its own date, not
  when the income arrives. Laddering several strikes is a natural extension;
  the tool sizes one at a time.
* **Beat the market.** Prediction-market prices are hard to beat. The blend
  and the warnings exist to keep a hedge from turning into an unexamined bet,
  not to encourage one. A gamma at or below zero (risk-neutral or
  risk-seeking) has no interior optimum; the tool then shows the pure hedge
  and says plainly that those preferences do not want insurance.
* **Give advice.** Tax treatment of event contracts, state-by-state
  availability and the legal status of some contract types are the user's to
  check.

## 10. Next steps

* Log sized hedges in the decision journal as probability predictions, so the
  journal's Brier score covers them and the calibration map learns from them
  — the journal's record type is price-target-shaped today.
* Ladder several strikes of one series and size them jointly.
* Multi-period exposures (a whole season of monthly contracts) with the
  horizon-weighted wealth the stocks product already uses.
