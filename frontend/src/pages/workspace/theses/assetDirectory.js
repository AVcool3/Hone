/*
 * useAssetDirectory — every symbol the asset picker can offer.
 *
 *   Sample data   → the demo universe (only those symbols have demo prices),
 *                   plus the friendly names in assets.js.
 *   Alpaca paper  → every active, tradable asset Alpaca lists
 *                   (POST /api/assets): ~11k US stocks + ETFs, or Alpaca's
 *                   crypto pairs. The server caches it for 12 hours.
 *
 * The list is fetched once per visit and kept in the store's in-memory
 * `runtime` (never localStorage — it's ~500 KB). A module-level promise per
 * key makes sure several pickers on one page share one request.
 *
 * Returns { assets, source, loading, error, reload }
 *   assets  [{ symbol, name, exchange }]  (sorted by symbol)
 *   source  'alpaca' | 'demo' | 'fallback' (live list failed; demo list shown)
 *
 * searchAssets(assets, query, limit) ranks matches for the dropdown.
 */
import { useCallback, useEffect, useState } from 'react';
import { api } from '../../../lib/api.js';
import { useStore } from '../../../lib/store.jsx';
import { ASSET_NAMES, registerAssetNames } from './assets.js';

const pending = new Map(); // runtime key -> in-flight promise

/** Server rows [symbol, name, exchange] -> objects the picker uses. */
const toAssets = rows => rows.map(([symbol, name, exchange]) => ({ symbol, name: name || ASSET_NAMES[symbol] || '', exchange }));

/** The hand-written names in assets.js, for this product only. */
const builtInAssets = isCrypto =>
  Object.keys(ASSET_NAMES)
    .filter(sym => isCrypto === sym.includes('/'))
    .map(symbol => ({ symbol, name: ASSET_NAMES[symbol], exchange: '' }));

/** Merge lists, first one wins on duplicates, sorted by symbol. */
function mergeAssets(...lists) {
  const by = new Map();
  for (const list of lists) for (const a of list) if (!by.has(a.symbol)) by.set(a.symbol, a);
  return [...by.values()].sort((a, b) => a.symbol.localeCompare(b.symbol));
}

/**
 * @param product  the product object (useProduct()), for slug + assetClass
 * @param market   the market part of a request body (useWorkspace().market)
 */
export function useAssetDirectory(product, market) {
  const { runtime, setRuntimeKey } = useStore();
  const isCrypto = product.slug === 'crypto';
  // One list per product and data source. Keys don't change the list, so
  // switching Alpaca accounts doesn't refetch.
  const key = `${product.slug}:assets:${market.demo ? 'demo' : 'alpaca'}`;
  const cached = runtime[key] || null;
  const [loading, setLoading] = useState(!cached);
  const [error, setError] = useState(null);

  const load = useCallback(
    async (force = false) => {
      if (product.slug === 'prediction-markets') return; // no asset list there
      if (!force && runtime[key]) return;
      setLoading(true);
      setError(null);
      try {
        if (force || !pending.has(key)) pending.set(key, api(product.assetClass, '/api/assets', market));
        const data = await pending.get(key);
        const assets = mergeAssets(toAssets(data.assets), builtInAssets(isCrypto));
        registerAssetNames(assets);
        setRuntimeKey(key, { assets, source: data.source, asOf: data.as_of });
      } catch (e) {
        pending.delete(key); // let the next attempt retry
        setError(e);
        // Still give the picker something: the names we ship with.
        setRuntimeKey(key, { assets: builtInAssets(isCrypto), source: 'fallback', asOf: null });
      } finally {
        setLoading(false);
      }
    },
    // runtime is read only for the "already loaded" short-circuit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key, product.assetClass, product.slug, isCrypto, setRuntimeKey],
  );

  useEffect(() => { load(false); }, [load]);

  return {
    assets: cached?.assets || [],
    source: cached?.source || null,
    loading: loading && !cached,
    error,
    reload: () => load(true),
  };
}

/**
 * Rank assets against what the user typed. Lower score = better:
 *   0 exact symbol · 1 symbol starts with it · 2 name starts with it
 *   3 a word in the name starts with it · 4 symbol contains it · 5 name contains it
 * Ties go to the shorter symbol (SPY before SPYG), then alphabetical.
 * EDIT HERE to change how the dropdown orders matches.
 *
 * Returns { matches: [asset], total } — total counts every match, so the
 * dropdown can say "20 of 312".
 */
export function searchAssets(assets, query, limit = 20) {
  const q = query.trim().toUpperCase();
  if (!q) return { matches: [], total: 0 };
  const qLow = q.toLowerCase();
  const scored = [];
  for (const a of assets) {
    const name = a.name.toLowerCase();
    let score;
    if (a.symbol === q) score = 0;
    else if (a.symbol.startsWith(q)) score = 1;
    else if (name.startsWith(qLow)) score = 2;
    else if (name.includes(` ${qLow}`)) score = 3;
    else if (a.symbol.includes(q)) score = 4;
    else if (name.includes(qLow)) score = 5;
    else continue;
    scored.push([score, a]);
  }
  scored.sort((x, y) => x[0] - y[0] || x[1].symbol.length - y[1].symbol.length || x[1].symbol.localeCompare(y[1].symbol));
  return { matches: scored.slice(0, limit).map(s => s[1]), total: scored.length };
}
