/*
 * Thin client for the FastAPI backend (hone/web/app.py).
 *
 * Every call carries ?asset_class=… so the server uses the right market data
 * regardless of which URL the page is on. Errors throw an ApiError whose
 * `kind` lets the UI tell apart:
 *   'brokerage'   — a linked-brokerage problem (link expired, needs sign-in…)
 *   'credentials' — Alpaca rejected or is missing keys
 *   'data'        — the market data needed isn't available (502/422)
 *   'network'     — the request never reached the server
 *   'input'       — the request was invalid (422 validation)
 */

export class ApiError extends Error {
  constructor(message, { status = 0, kind = 'unknown' } = {}) {
    super(message);
    this.status = status;
    this.kind = kind;
  }
}

function classify(status, message) {
  const m = (message || '').toLowerCase();
  // Checked first: these messages also mention keys/sign-in, but the fix is
  // on the brokerage side, not the Alpaca keys.
  if (m.includes('brokerage') || m.includes('sign in') || m.includes('snaptrade')) return 'brokerage';
  if (m.includes('key') || m.includes('credential') || m.includes('unauthorized') || m.includes('forbidden') || status === 401 || status === 403) {
    return 'credentials';
  }
  if (status === 502 || m.includes('history') || m.includes('price')) return 'data';
  if (status === 422) return 'input';
  return 'unknown';
}

/** Turn FastAPI's `detail` (string or validation array) into one sentence. */
function detailText(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map(d => `${(d.loc || []).filter(x => x !== 'body').join(' → ')}: ${d.msg}`)
      .join('; ');
  }
  return fallback;
}

export async function api(assetClass, path, body, { signal, headers } = {}) {
  const url = `${path}${path.includes('?') ? '&' : '?'}asset_class=${encodeURIComponent(assetClass)}`;
  let res;
  try {
    res = await fetch(url, {
      method: body === undefined ? 'GET' : 'POST',
      headers: { ...(body === undefined ? {} : { 'Content-Type': 'application/json' }), ...headers },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError('Could not reach the Hone server. Check your connection and retry.', { kind: 'network' });
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = detailText(data.detail, res.statusText || 'Request failed');
    throw new ApiError(message, { status: res.status, kind: classify(res.status, message) });
  }
  return data;
}

/**
 * The market part of a request body. Three data sources:
 *   'sample'  — synthetic prices and holdings ({ demo: true })
 *   'alpaca'  — the user's Alpaca paper account (their keys)
 *   'brokers' — every brokerage linked through SnapTrade, combined. Any
 *               Alpaca keys the user entered are sent too, but only to fetch
 *               price history.
 * Everything travels with the single request and is never stored server-side.
 */
export function marketBody(dataSource, alpaca, broker) {
  if (dataSource !== 'alpaca' && dataSource !== 'brokers') return { demo: true };
  const body = { demo: false };
  const creds = {};
  if (alpaca?.apiKey || alpaca?.secretKey) {
    creds.api_key = alpaca.apiKey || null;
    creds.secret_key = alpaca.secretKey || null;
  }
  if (dataSource === 'brokers') {
    creds.source = 'brokers'; // so the server can say "nothing linked yet"
    if (broker?.userId) creds.broker = { user_id: broker.userId, user_secret: broker.secret };
  }
  if (Object.keys(creds).length) body.credentials = creds;
  return body;
}

/** The server's switches (is brokerage linking on? does it need sign-in?). */
let configPromise = null;
export function serverConfig(assetClass = 'stocks') {
  configPromise ??= api(assetClass, '/api/config').catch(() => ({}));
  return configPromise;
}

/**
 * Look up a reference price for one symbol.
 *
 * There is no dedicated quote endpoint, so this asks the conviction compiler
 * to parse just the ticker (offline parser, no LLM) and reads back the live
 * price it attaches. It also returns whether the symbol is tradeable in the
 * current universe, and the universe itself (for the asset picker).
 */
export async function quote(assetClass, ticker, market) {
  const res = await api(assetClass, '/api/compile-view', {
    ...market,
    text: ticker,
    offline: true,
    with_prices: true,
  });
  const v = res.views?.[0];
  return {
    ticker: v?.ticker ?? ticker,
    price: v?.live_price ?? v?.entry_price ?? null,
    tradeable: v ? v.tradeable !== false : false,
    universe: res.universe ?? [],
    at: new Date().toISOString(),
  };
}
