# Linking brokerages

Hone can read your real holdings from every brokerage you use (Schwab,
Fidelity, Robinhood, Interactive Brokers, Webull, E*Trade, Vanguard,
Coinbase and others), combine them into one portfolio, and run every tool on
it. It does this through **[SnapTrade](https://snaptrade.com)**, a brokerage
aggregator: Hone integrates with SnapTrade once, and SnapTrade connects to
the brokers.

**It's off until you configure it.** Without SnapTrade keys, the Data &
account page offers sample data and an Alpaca paper account, exactly as
before.

## What users see

1. **Data & account → Your brokerages → Link a brokerage.**
2. SnapTrade's page opens. They pick a broker and sign in **there**. Hone
   never sees a brokerage password.
3. They come back to Hone. The linked brokerages and their accounts are
   listed, and **Check holdings** shows what was combined, plus every
   position that was left out and why.
4. Every tool (overview, portfolio, hedging, backtest) now uses those
   holdings. Each user can link as many brokerages as they like.

Connections are **read-only**. Hone asks SnapTrade for data access only and
has no code path that places an order.

## Set it up (about 15 minutes)

### 1. Get SnapTrade keys

Sign up at [dashboard.snaptrade.com](https://dashboard.snaptrade.com) and
create API keys. You get a **client ID** and a **consumer key**. The consumer
key signs every request, so treat it like a password.

SnapTrade charges per connected user per month (check their pricing page for
current rates). Users who never finish linking a broker cost nothing.

### 2. Give the server the keys

```bash
export SNAPTRADE_CLIENT_ID=...
export SNAPTRADE_CONSUMER_KEY=...
```

On Render/Fly, add them as environment variables or secrets. They never
reach the browser.

### 3. Give it a price source

SnapTrade answers "what does this person hold?". Price history, which Hone
needs for risk, still comes from Alpaca market data. Free Alpaca keys work:

```bash
export ALPACA_DATA_API_KEY=...       # used ONLY for price history
export ALPACA_DATA_SECRET_KEY=...
```

These keys are only ever used to fetch prices, never to read an account, so
they're safe on a public server (unlike `ALPACA_API_KEY`, which `HONE_PUBLIC`
refuses). On a private server, the regular `ALPACA_API_KEY` /
`ALPACA_SECRET_KEY` also work. A user who has entered their own Alpaca keys
uses those instead.

### 4. Public servers: turn on sign-in

With `HONE_PUBLIC=1` (the Dockerfile default), linking a brokerage requires
signing in with a Hone account. Each link is a paid SnapTrade user, and
tying links to accounts means one person gets one SnapTrade user, and a
stranger can't run up your bill.

Set up Supabase as described in [Accounts & saved portfolios](SUPABASE.md),
**including step 2b**, which creates the `broker_links` table. That table is
what lets a user's links follow them to another device.

The server verifies sign-ins against the same Supabase project the browser
uses. By default it reads the URL and key from `hone/web/static/config.js`.
Set `SUPABASE_URL` / `SUPABASE_ANON_KEY` to override.

On a private server (`HONE_PUBLIC` unset), sign-in is optional. Without it,
the link lives in that browser only.

## What gets modelled

| Position | Stocks product | Crypto product |
|---|---|---|
| Stocks, ETFs, ADRs, closed-end funds (USD) | ✅ combined across accounts | listed as skipped |
| Crypto | listed as skipped | ✅ (stablecoins count as cash) |
| Cash, money-market sweep | listed as skipped (cash) | listed as skipped |
| Options | listed as skipped (not modelled yet) | listed as skipped |
| Mutual funds | listed as skipped (no daily price feed) | listed as skipped |
| Non-USD listings (e.g. `VAB.TO`) | listed as skipped (no FX conversion) | listed as skipped |
| Anything with no price history | listed as skipped | listed as skipped |

The same ticker held at two brokers becomes one holding. Bank, credit and
annuity accounts are ignored. The portfolio value Hone uses for hedge sizing
is the value of what it models. Skipped positions and cash are shown but not
counted.

## How it works

- `hone/market_data/brokers/snaptrade.py`: a small signed REST client (no SDK
  dependency) plus `combine_positions`, which merges accounts and decides
  what is modelled. Holdings are cached for 60 seconds
  (`HOLDINGS_CACHE_SECONDS`), because Hone recalculates often and SnapTrade
  rate-limits some accounts to about 10 requests a minute.
- `hone/web/app.py`: `/api/broker/connect`, `/accounts`, `/disconnect` and
  `/unlink`, plus a branch in the market loader. When a request carries
  `credentials.broker`, holdings come from SnapTrade and prices from Alpaca.
- `frontend/src/pages/workspace/BrokeragesPanel.jsx`: the UI.
- A user's SnapTrade identity is a **link**, `{ user_id, user_secret }`. It
  is kept in the browser (and in the user's own `broker_links` row when
  signed in) and sent with each request, like Alpaca keys. The server stores
  nothing. A link is useless without the server's consumer key, which signs
  every SnapTrade request.

## Troubleshooting

| Message | Meaning |
|---|---|
| *Brokerage linking isn't configured on this server* | `SNAPTRADE_CLIENT_ID` / `SNAPTRADE_CONSUMER_KEY` aren't set. |
| *Sign in to link your brokerages* | Public server and not signed in. |
| *This server has no price-history source* | Set `ALPACA_DATA_*`, or enter Alpaca keys on the page. |
| *Your brokerage link is no longer valid* | The link's secret was rejected. Use **Remove all brokerage links**, then link again. |
| *Already linked from another device* | Sign in with the same account (the link comes with it), or **Reset and relink**. |
| A broker shows **Needs reconnecting** | The broker stopped sharing data, usually after a password change. Press **Reconnect**. |
