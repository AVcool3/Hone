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

The browser app is organised around **tools you can open in any order**,
each at its own URL, rather than a step-by-step flow:

| Workspace tool (`/:product/app/...`) | What it does |
|---|---|
| Overview | Summary, launch cards, current vs. model-proposed allocation |
| Risk aversion (`risk`) | Eight-question adaptive estimate (or the classic 30), with uncertainty; stated vs. revealed risk |
| Investment theses (`theses`) | Editable price-target views with a live allocation beside them; plain-English compiler; "More view types" (entropy pooling) |
| Portfolio (`portfolio`) | Current vs. proposed, one expandable explanation per change, sensitivity, commit views to the journal |
| Hedging (`hedging`) | Hedge plan, stress scenarios, tail risk (CVaR) |
| Track record (`record`) | Decision journal, calibration, training-data export |
| Backtest (`backtest`) | Walk-forward backtest at your risk level, with the behaviour gap |
| Data & account (`settings`) | Sample data vs. Alpaca paper account, optional sign-in |

Prediction Markets has its own tools: `hedge` (size an income hedge) and
`markets` (browse the curated Kalshi catalog, or search every open Kalshi
market). Public pages per product: overview,
`how-it-works`, `methodology`, `backtests`, `setup` — the last three render
the files in `docs/` verbatim. Everything runs on **sample data** with no
Alpaca account; switch to your paper account under *Data & account* (keys
are sent per request and never stored server-side), or leave them blank to
use the server's `ALPACA_API_KEY` / `ALPACA_SECRET_KEY`. With an Alpaca
account the thesis asset picker searches **every** active US stock and ETF
(or every crypto pair) Alpaca lists, by ticker or company name
(`POST /api/assets`, cached 12 hours in `hone/market_data/asset_directory.py`);
sample data covers only the demo symbols. The JSON API is
documented at `/docs` (OpenAPI) when the server is running.

### Working on the frontend

The UI is a React app (Vite) in `frontend/`. Its production build is
written to `hone/web/static/` and **committed**, so deploys need no Node
toolchain.

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173, proxies /api to python -m hone serve on :8000
npm run build   # rebuild hone/web/static/ — commit the result
```

Where things live: `src/lib/` (API client, persisted state, formatting,
product definitions), `src/components/` (shared UI), `src/pages/` (one
folder per area), `src/styles/global.css` (design tokens — edit colours
there), `src/reactbits/` (components from [React Bits](https://reactbits.dev):
AnimatedContent, SlideCommit, SpotlightCard, RubberSegment, SquishSwitch).

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
├── prediction/      # Hone Markets: event-contract hedging, Kalshi catalog
├── backtest/        # walk-forward engine + conviction population study
├── web/             # FastAPI JSON API; static/ holds the built React app
├── pipeline.py      # end-to-end flow
└── cli.py           # `python -m hone ...` (incl. `serve`)
frontend/            # React source for the web app (built into hone/web/static/)
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

**One deployment serves all three.** The site has product tabs: `/` is the
stocks product, `/crypto` is the crypto one and `/prediction-markets` is
Hone Markets (below) — so `studiohone.com/crypto`
works with no extra service, no second domain, and no DNS changes. The
asset class resolves per request (URL path, or `?asset_class=crypto` on
API calls), and each product keeps its own saved state in the browser.

Setting `HONE_ASSET_CLASS=crypto` still pins an entire deployment to one
product if you ever want them served separately.

The research basis, every parameter difference, and the known limitations
are documented in [docs/CRYPTO_RESEARCH.md](docs/CRYPTO_RESEARCH.md).

## Hone Markets (third product): hedging a paycheck

The third tab, `studiohone.com/prediction-markets`, turns the same
machinery around. The stocks product asks how much of a risky asset you
should hold given your γ; this one is for people whose *income* is the
risky asset — a ski instructor whose season depends on Aspen snowfall, an
ad freelancer whose bookings follow ad budgets, a recruiter whose fees
follow hiring. Kalshi lists event contracts on exactly those things, and a
contract that pays when the season goes badly is a hedge for a position
you never chose.

* **Same γ, same utility, same certainty equivalent** — the questionnaire
  is shared, and a number measured on the Stocks tab is offered here.
* **Insurance first, then the bet.** Maximizing expected CRRA utility of
  end-of-season wealth gives a position that always splits into a pure
  hedge (your loss × how tightly the market tracks it — the analogue of
  the beta-sized index short) and a speculative tilt on the gap between
  your odds and the price, shrunk by γ. The page labels both.
* **What it is worth, and the most to pay.** The certainty-equivalent
  gain prices the hedge in dollars at your γ; a closed-form reservation
  price `c_max = E[U′(W₀)·B] / E[U′(W₀)]` is the ceiling above which the
  tool shows no position — the Merton risk budget for a binary event.
* **Your odds against the market** are blended the Black-Litterman way,
  with the journal's calibration map applied to your confidence once it
  has scored enough of your predictions. Basis risk is a slider, and the
  hedge shrinks to ρ·L.
* **Live Kalshi data, no account.** 41 curated series in six groups —
  snow and ski-resort openings, ad-spend indices, labor, housing and
  rates, travel, fuel — read from the public API with a bundled snapshot
  as the fallback. Hone never places orders.
* **Every other Kalshi market, searchable.** *Markets → All Kalshi
  markets* searches every open event on the exchange (16,000+), not just
  the curated hedges. The server indexes them in the background
  (`hone/prediction/kalshi_browse.py`, rebuilt every 30 minutes) and
  fetches an event's live prices when you open it; *Hedge with YES/NO*
  copies that price into the income-hedge sizer.

```bash
python research/prediction/fetch_kalshi_snapshot.py   # refresh the bundled snapshot
HONE_KALSHI_LIVE=0 python -m hone serve                 # serve the snapshot only
```

Theory, derivations, the catalog and the limitations are in
[docs/PREDICTION_MARKETS.md](docs/PREDICTION_MARKETS.md).

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
- [docs/PREDICTION_MARKETS.md](docs/PREDICTION_MARKETS.md) — Hone Markets: hedging cyclical income with Kalshi event contracts.

## Disclaimers

This is analytical tooling, not investment advice. Option costs are
indicative Black-Scholes values — always use live quotes for execution.
The Alpaca integration targets the **paper-trading** API.
