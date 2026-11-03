/*
 * Thin client for the FastAPI backend (hone/web/app.py).
 *
 * Every call carries ?asset_class=… so the server uses the right market data
 * regardless of which URL the page is on. Errors throw an ApiError whose
 * `kind` lets the UI tell apart:
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

export async function api(assetClass, path, body, { signal } = {}) {
  const url = `${path}${path.includes('?') ? '&' : '?'}asset_class=${encodeURIComponent(assetClass)}`;
  let res;
  try {
    res = await fetch(url, {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
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
 * The market part of a request body: sample data, or the user's own Alpaca
 * paper account. Keys travel with the single request and are never stored
 * server-side.
 */
export function marketBody(dataSource, alpaca) {
  if (dataSource !== 'alpaca') return { demo: true };
  const body = { demo: false };
  if (alpaca?.apiKey || alpaca?.secretKey) {
    body.credentials = { api_key: alpaca.apiKey || null, secret_key: alpaca.secretKey || null };
  }
  return body;
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
