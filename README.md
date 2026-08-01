# Hone

Hedge-fund-grade risk tools for retail investors, in three parts:

1. **Quantify your risk aversion** — eight adaptive questions, each chosen
   to maximize what its answer reveals, place your risk-aversion
   parameter **γ** in one of **50 risk tiers** with a credible interval.
   The classic 30-question Holt-Laury menu with CRRA maximum-likelihood
   estimation is still available and estimates the same model.
2. **Measure your portfolio's risk** — an Alpaca paper-trading client
   pulls your holdings and price history, and a business-side
   covariance calculator (sample / EWMA / Ledoit-Wolf shrinkage) builds
   the covariance matrix Σ.
3. **Reweight and hedge** — name a stock you like with a target price
   and a confidence level; Black-Litterman blends that view with the
   equilibrium implied by your current holdings, γ-aware Mean-Variance
   Optimization reweights the portfolio, and the hedging engine
   proposes shorts and option overlays (protective puts, zero-cost
   collars) sized so the hedged portfolio matches your risk budget.

## Install

```bash
pip install -e ".[dev]"
python -m pytest            # full test suite, no network needed
```

## Web app

Everything below is also available in the browser:

```bash
python -m hone serve                 # http://127.0.0.1:8000
```

The single-page app walks through the same four steps: the 30-question
risk questionnaire (with the 50-tier gauge), your portfolio, the
optimize tab (views + Black-Litterman + MVO with a current-vs-target
weight chart and trade list), and the hedge tab. A **demo mode** toggle
runs the whole flow on synthetic data with no Alpaca account; switch it
off to use your paper account — keys can be typed into the page
(held in-page, sent per request, never stored server-side) or left
blank to use the server's `ALPACA_API_KEY` / `ALPACA_SECRET_KEY`
environment variables. The JSON API is documented at `/docs`
(OpenAPI) when the server is running.

## Quick start (CLI)

```bash
# Full pipeline on synthetic data (no API keys needed)
python -m hone demo

# Part 1: elicit your gamma interactively (3 rounds x 10 choices)
python -m hone questionnaire

# Part 3: reweight with a view — "TSLA to $400, 60% confident, 6 months"
export ALPACA_API_KEY=... ALPACA_SECRET_KEY=...     # paper keys
python -m hone optimize --gamma 1.2 --view TSLA:400:0.6:180

# Hedge suggestions for your risk tier
python -m hone hedge --gamma 2.4

# Everything also works without an Alpaca account:
python -m hone optimize --demo --gamma 1.2 --view TSLA:200:0.6
```

## How each part works

### Part 1 — the risk-aversion parameter (`hone/risk_profile/`)

* `holt_laury.py` — the 10-row menu (Option A safe: $2.00/$1.60;
  Option B risky: $3.85/$0.10) presented at three stake scales
  (×1, ×20, ×100 → top prize $2 to $385). The switch point brackets γ in
  the canonical intervals (switching after 5 safe choices ⇒
  γ ∈ (0.15, 0.41)).
* `estimation.py` — the precision engine. CRRA utility
  U(x) = x^(1−γ)/(1−γ), a noise parameter μ, and the log-likelihood
  ln L(γ, μ; y) = Σᵢ [yᵢ ln Pr(A) + (1−yᵢ) ln(1−Pr(A))] maximized with
  multi-start L-BFGS-B. Two error specifications:
  * `luce` — the latent choice ratio
    Pr(A) = U_A^(1/μ) / (U_A^(1/μ) + U_B^(1/μ)) exactly as in the design
    document (requires γ < 1, where expected utilities are positive);
  * `fechner` (default) — a logistic error on the contextually
    normalized EU difference, well-defined for every γ. Both agree
    closely in the empirically common region.
  Standard errors come from the inverse numerical Hessian.
* `tiers.py` — 50 tiers partitioning γ ∈ [−1, 4] into 0.10-wide bins;
  tier 1 = most risk-seeking, tier 50 = most risk-averse, with category
  labels and a representative γ per tier.
* `questionnaire.py` — the interactive flow (I/O injected, fully
  scriptable/testable).

### Part 2 — market data (`hone/market_data/`)

* `alpaca_client.py` — thin REST client for the **paper-trading**
  endpoints: account, positions, portfolio weights, daily bars (with
  pagination), latest prices, and order submission. Credentials from
  `ALPACA_API_KEY` / `ALPACA_SECRET_KEY`.
* `covariance.py` — **business-side only** (feeds the optimizer; never
  shown to end users): log-returns, sample covariance, RiskMetrics EWMA
  (λ = 0.94), and Ledoit-Wolf (2004) shrinkage — the default, because
  short retail price histories make raw sample covariances noisy and
  ill-conditioned.

### Part 3 — reweighting and hedging (`hone/optimization/`, `hone/hedging/`)

* `views.py` — a view is *(ticker, current price, target price,
  confidence, horizon)*; the target price is annualized into the
  Black-Litterman `Q` entry.
* `black_litterman.py` — equilibrium prior Π = δΣw from your **own**
  holdings (so "no views" ≈ hold what you have), Idzorek's mapping from
  confidence to view uncertainty Ω, and the standard posterior
  μ_BL = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹ [(τΣ)⁻¹Π + PᵀΩ⁻¹Q].
* `mvo.py` — maximizes w'μ − (γ/2)·w'Σw (full investment, optional
  long-only and per-name caps), with γ straight from the questionnaire.
* `hedging/` — the Merton rule α\* = (μₚ − r)/(γσₚ²) converts γ into a
  target volatility; the engine then sizes
  * a **short hedge** (e.g. short SPY) that brings hedged volatility to
    the target,
  * a **protective put** with a γ-dependent floor (more risk-averse ⇒
    tighter floor), and
  * a **zero-cost collar** (same put financed by selling an OTM call),
  with indicative Black-Scholes costs.
* `pipeline.py` — chains 1→2→3 and prints the posterior returns, the
  optimal weights, the buy/sell trade list, and the hedge plan.

## Layout

```
hone/
├── risk_profile/    # questionnaire, MLE, 50 tiers, DOSE adaptive elicitation
├── market_data/     # Alpaca client, covariance (internal)
├── optimization/    # MVO, views, Black-Litterman, CVaR, entropy pooling
├── hedging/         # shorts, puts, collars, Black-Scholes
├── journal/         # decision journal, Brier scoring, learned confidence
├── llm/             # Conviction Compiler (Claude + offline parser)
├── crypto/          # the crypto product's universe and parameters
├── backtest/        # walk-forward engine + conviction population study
├── web/             # FastAPI JSON API + single-page UI
├── pipeline.py      # end-to-end flow
└── cli.py           # `python -m hone ...` (incl. `serve`)
```

## Hosting it on a domain

The app ships with a `Dockerfile` and configs for the two easiest hosts.
Two environment variables control the deployment posture:

| Variable | Effect |
|---|---|
| `HONE_PUBLIC=1` | The server refuses to use its own `ALPACA_*` env keys — every visitor must enter their own keys in the page. **Set this on anything strangers can reach** (the Dockerfile sets it by default). |
| `HONE_ACCESS_PASSWORD` | When set, the whole site sits behind HTTP Basic auth with this password (any username). Use it for a private personal deployment. |

`/api/health` is always open for platform health checks.

> **Why not Vercel?** Tried and hit a hard wall: Vercel Python functions
> cap at 250 MB uncompressed, and this app's numpy+scipy+pandas+fastapi
> stack exceeds it once complete. The hosts below run the Docker image
> and have no such limit.

### Option A — Render (Docker, ~10 minutes)

1. Push this repo to GitHub (already done if you're reading this there).
2. At [render.com](https://render.com): **New + → Blueprint**, pick this
   repo — it reads `render.yaml` and builds the Docker image.
3. You immediately get `https://hone-XXXX.onrender.com` with TLS.
4. Custom domain: service **Settings → Custom Domains → Add**, enter
   `studiohone.com`. Render shows you the DNS records to create at your
   registrar: a `CNAME` from `www` to your onrender hostname (and an
   `A`/`ALIAS` record for the apex). Certificates are provisioned
   automatically once DNS propagates.

### Option B — Fly.io

```bash
fly launch --copy-config --no-deploy    # uses fly.toml
fly deploy
fly certs add studiohone.com            # prints the DNS records to add
```

### Option C — your own VPS (full control)

```bash
docker build -t hone . && docker run -d -p 127.0.0.1:8000:8000 hone
```

Then put [Caddy](https://caddyserver.com) in front for automatic HTTPS —
a 2-line `Caddyfile`:

```
studiohone.com {
    reverse_proxy 127.0.0.1:8000
}
```

and point your domain's `A` record at the server's IP.

### Deployment posture

- **Public site** (default in the Dockerfile): keep `HONE_PUBLIC=1`, do
  NOT set `ALPACA_*` on the server. Visitors bring their own paper keys,
  which are sent per request and never stored.
- **Personal site**: set `HONE_ACCESS_PASSWORD`, optionally set your
  `ALPACA_*` keys as server env vars, and `HONE_PUBLIC=0` so the page
  works without typing keys.
- There are no user accounts and no server-side storage — every request
  is stateless. If you want saved profiles/portfolios per user, that's
  the next build step.

## Hone Crypto (side product, same protocol)

The same engine runs a crypto variant — identical elicitation, covariance,
Black-Litterman and MVO protocol, with crypto parameters (365-day year,
BTC as market proxy, real crypto drawdowns for stress tests, stablecoins
instead of options as the hedge leg):

```bash
python -m hone crypto-demo                  # full crypto pipeline, synthetic data
python -m hone serve --asset-class crypto   # the crypto site
HONE_ASSET_CLASS=crypto python -m hone serve   # same thing via env
```

**One deployment serves both.** The site has product tabs: `/` is the
stocks product and `/crypto` is the crypto one — so `studiohone.com/crypto`
works with no extra service, no second domain, and no DNS changes. The
asset class resolves per request (URL path, or `?asset_class=crypto` on
API calls), and each product keeps its own saved state in the browser.

Setting `HONE_ASSET_CLASS=crypto` still pins an entire deployment to one
product if you ever want them served separately.

The research basis, every parameter difference, and the known limitations
are documented in [docs/CRYPTO_RESEARCH.md](docs/CRYPTO_RESEARCH.md).

## Accounts & saved portfolios (optional)

Hone has an optional Supabase-powered auth layer: users sign in and save
named portfolio snapshots (γ, tier, views) to reload later. It's **off
until configured** — with no keys, Hone runs fully in-browser as
described above. To turn it on, follow [docs/SUPABASE.md](docs/SUPABASE.md)
(create a project, run the provided SQL with Row-Level Security, and fill
in `hone/web/static/config.js`).

## Measuring risk aversion in eight questions

The 30-question Holt-Laury menu is still there, but the default is now
adaptive (`hone/risk_profile/dose.py`): a Bayesian posterior over (γ, μ) is
updated after every answer, and each question is chosen to maximize the
information its answer is expected to carry. Eight questions match thirty
fixed ones — and beat them by a factor of four to five for risk-averse
users, because the classic menu's indifference points top out around γ ≈ 1.4
and it simply cannot see above that. The page shows the posterior narrowing
as you answer, and the credible interval is carried forward rather than
rounded away. Method, the simulation results, and the limitations are in
[docs/ADAPTIVE_ELICITATION.md](docs/ADAPTIVE_ELICITATION.md).

## Teaching a model your habits

Your resolved predictions are the only data that could teach a model how *you*
write and what your language turns out to be worth. Hone ships two paths and
is blunt about which one works at your scale. **In-context personalization**
(`hone/llm/personalize.py`) puts your own resolved examples — outcome-balanced,
plus your realized hit rate — into the compiler's prompt. No GPU, active from
five predictions, better every time one resolves. **QLoRA export**
(`hone/llm/export.py`, `training/train_qlora.py`) builds a fine-tuning dataset
whose calibration labels are *realized outcomes* rather than stated confidence
— so a model learns what your language predicts, not how sure you claim to be.
It refuses to train below 200 examples, because thirty rows produce a model
that has memorized them and is worse than the base on the thirty-first.
See [docs/QLORA.md](docs/QLORA.md).

## The behaviour gap

Every backtest here assumed you held the strategy through everything it did.
Almost nobody does. `hone/backtest/behavior.py` drops that assumption: your γ
sets a tolerable drawdown through the same Merton budget the hedge page uses,
you're modelled as capitulating past it, and you buy back only once the market
has climbed 10% off its low — which is what makes it expensive, because it
means buying above the bottom. Trading costs and the cash rate are both
charged. The evidence page now shows what the same strategies returned *as
you'd have held them*. The tier-matched portfolio has the smallest gap of the
diversified strategies, which is the whole argument for sizing a portfolio to
what you can sit through. See [docs/BEHAVIOR_GAP.md](docs/BEHAVIOR_GAP.md),
including the case where capitulating is the right call.

## Views that aren't price targets

Black-Litterman needs a linear statement about an expected return under a
normal distribution. Most convictions aren't that shape: *a one-in-three
chance of a bad drawdown*, *I'm sure A beats B but couldn't price either*,
*if Bitcoin breaks, Ethereum breaks harder*. Forcing those through a
price-target box makes users invent numbers, and an invented number is
indistinguishable from a real one by the time it reaches the optimizer.
`hone/optimization/entropy_pooling.py` takes them as constraints on scenario
probabilities instead, and returns the minimum-relative-entropy posterior —
the update that adds nothing beyond what you actually asserted (Meucci 2008).
It reports what your views cost in effective scenarios, and says so when
they've collapsed the sample. Chained with CVaR, it gives a path from belief
to portfolio that assumes normality nowhere.
See [docs/FLEXIBLE_VIEWS.md](docs/FLEXIBLE_VIEWS.md).

## Tail risk, as a second opinion

Variance treats a good month and a bad month identically and assumes the
covariance matrix captures the joint distribution. `hone/optimization/cvar.py`
adds the blunter question — *when it goes badly, how badly?* — via
Conditional Value-at-Risk, the average loss across the worst 5% of months,
read straight off price history rather than assumed from Σ. Rockafellar and
Uryasev's formulation makes it a linear program, so it solves exactly. Two
portfolios come back: the **risk-first** one that minimizes the tail and
never looks at expected returns, and the **γ-matched** one that trades tail
for return at the rate your elicited risk aversion implies. The main flow
stays variance-based; this page prices what that choice costs you.
See [docs/TAIL_RISK.md](docs/TAIL_RISK.md).

## The conviction loop

Two features turn the pipeline above into something that improves with use.

**The Conviction Compiler** (`hone/llm/`) takes a thesis in plain English —
"I think Nvidia runs to $250 by the summer, fairly confident" — and compiles
it into the structured view the optimizer needs: ticker, entry price, target,
horizon, confidence. Claude does this when `ANTHROPIC_API_KEY` is set;
otherwise a deterministic parser handles it with no network and no key. The
result is a **proposal**: every field lands in an editable form with the
guessed ones marked, and nothing reaches Black-Litterman until the user
confirms it. The model is explicitly forbidden from inventing price targets —
it translates intent, and the server supplies live prices.

**The decision journal** (`hone/journal/`) logs every view at the moment it is
acted on, at the server's price, and scores it when its horizon elapses. The
accumulated record yields a Brier score, a reliability curve and a fitted map
from what the user *says* to what their history justifies — which is then
applied to future views, disclosed on screen, and switchable off. Confidence
is the one number in Hone the user supplies rather than the system measures,
and it is the lever controlling how far the portfolio tilts; this is how it
stops being taken on trust. The correction is deliberately gentle, and that
is an empirical result rather than caution: a simulated population of
investors showed that replacing stated confidence *outright* with a realized
hit rate loses more often than it wins, because it taxes anyone with genuine
edge. Confidence handling is a guardrail, not an edge. The method, the guards
against over-correcting on thin evidence, and the honest limitations are in
[docs/CALIBRATION.md](docs/CALIBRATION.md); the evidence is in
[docs/BACKTEST_CONVICTION.md](docs/BACKTEST_CONVICTION.md).

```bash
pip install -e ".[llm]"        # optional: enables the Claude compiler
export ANTHROPIC_API_KEY=...   # without it, the offline parser is used
```

## More docs

- [docs/VISION.md](docs/VISION.md) — what Hone is and why.
- [docs/ADAPTIVE_ELICITATION.md](docs/ADAPTIVE_ELICITATION.md) — DOSE: eight adaptive questions instead of thirty.
- [docs/BACKTEST_CONVICTION.md](docs/BACKTEST_CONVICTION.md) — does any of the conviction machinery actually help, and for whom.
- [docs/TAIL_RISK.md](docs/TAIL_RISK.md) — CVaR, why variance isn't enough, and what the tail page does not know.
- [docs/FLEXIBLE_VIEWS.md](docs/FLEXIBLE_VIEWS.md) — entropy pooling: probability, ranking and conditional views.
- [docs/BEHAVIOR_GAP.md](docs/BEHAVIOR_GAP.md) — what you'd actually have got, once you're allowed to panic.
- [docs/QLORA.md](docs/QLORA.md) — personalizing the compiler: few-shot now, fine-tuning when the data justifies it.
- [docs/CALIBRATION.md](docs/CALIBRATION.md) — the decision journal, Brier scoring, and learned confidence.
- [docs/ROADMAP.md](docs/ROADMAP.md) — where it's going.
- [docs/SUPABASE.md](docs/SUPABASE.md) — enabling accounts & saved portfolios.
- [docs/CRYPTO_RESEARCH.md](docs/CRYPTO_RESEARCH.md) — Hone Crypto: literature, parameters, limitations.

## Disclaimers

This is analytical tooling, not investment advice. Option costs are
indicative Black-Scholes values — always use live quotes for execution.
The Alpaca integration targets the **paper-trading** API.
