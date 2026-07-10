# Hone

Hedge-fund-grade risk tools for retail investors, in three parts:

1. **Quantify your risk aversion** — a Holt-Laury Multiple Price List
   questionnaire run through a Maximum Likelihood engine (CRRA utility +
   Fechner noise) produces a rigorous point estimate of your
   risk-aversion parameter **γ** and places you in one of **50 risk
   tiers**.
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
├── risk_profile/    # Part 1: questionnaire, MLE, 50 tiers
├── market_data/     # Part 2: Alpaca client, covariance (internal)
├── optimization/    # Part 3: MVO, views, Black-Litterman
├── hedging/         # Part 3: shorts, puts, collars, Black-Scholes
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

### Option A — Render (easiest, free tier, ~10 minutes)

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

## Disclaimers

This is analytical tooling, not investment advice. Option costs are
indicative Black-Scholes values — always use live quotes for execution.
The Alpaca integration targets the **paper-trading** API.
