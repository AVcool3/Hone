/*
 * usePredictionCatalog — the Kalshi market catalog Hone curates for income
 * hedging (GET /api/predict/markets).
 *
 * The catalog is ~180 KB and changes slowly, so it is fetched once per visit
 * and kept in the store's in-memory `runtime` under 'pm:catalog' (never in
 * localStorage). Both the Income hedge and Markets pages call this hook; a
 * module-level promise makes sure they share one request.
 *
 * Returns { catalog, loading, error, reload }
 *   catalog.source  'live' | 'live-partial' | 'snapshot'
 *   catalog.as_of   ISO timestamp the prices were taken
 *   catalog.industries[].series[].markets[]
 */
import { useCallback, useEffect, useState } from 'react';
import { api } from '../../../lib/api.js';
import { useStore } from '../../../lib/store.jsx';

const KEY = 'pm:catalog';
let pending = null; // shared in-flight request

export function usePredictionCatalog() {
  const { runtime, setRuntimeKey } = useStore();
  const catalog = runtime[KEY] || null;
  const [loading, setLoading] = useState(!catalog);
  const [error, setError] = useState(null);

  const load = useCallback(
    async (force = false) => {
      if (!force && runtime[KEY]) return;
      setLoading(true);
      setError(null);
      try {
        if (force || !pending) pending = api('prediction', '/api/predict/markets');
        const data = await pending;
        setRuntimeKey(KEY, data);
      } catch (e) {
        pending = null; // let the next attempt retry
        setError(e);
      } finally {
        setLoading(false);
      }
    },
    // runtime is read only for the "already loaded" short-circuit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [setRuntimeKey],
  );

  useEffect(() => {
    load(false);
  }, [load]);

  return { catalog, loading: loading && !catalog, error, reload: () => load(true) };
}

/* ------------------------------------------------------------ helpers */

/** "YES on 'above X%'" -> 'yes';  "NO" -> 'no'. The side that pays in a bad season. */
export const badSideOf = series => (/^\s*yes/i.test(series?.bad_side || '') ? 'yes' : 'no');

/** The ask price for one side of a market (what buying that side costs). */
export const askFor = (market, side) => (side === 'yes' ? market?.yes_ask : market?.no_ask);

/** The market's probability that `side` pays (midpoint-based `implied` is for YES). */
export const probFor = (market, side) => {
  const yes = market?.implied ?? market?.last;
  if (typeof yes !== 'number') return null;
  return side === 'yes' ? yes : 1 - yes;
};

/** Plain-English meaning of the catalog's basis verdicts. */
export const BASIS_TEXT = {
  direct: 'Direct — the contract settles on the very thing that drives your income (e.g. snowfall at your mountain).',
  close: 'Close — settles on something that usually moves with your income, but not always.',
  proxy: 'Proxy — a broad indicator; it captures the general climate, not your specific season.',
};

/** Suggested starting correlation for each basis verdict (the user can change it). */
/*
 * Default "how closely does this market track your income" by tier. Lowered
 * after the backtest on 2,822 settled Kalshi markets
 * (research/prediction/findings/02_history.md) measured upper bounds of
 * 0.52-0.68 for gas vs. a driver's fuel costs and ~0.8 for CPI vs. a
 * retiree's purchasing power. Labor-market series carry their own lower
 * default (basis_default in kalshi_client.py): one person's job loss barely
 * moves with the national unemployment rate (measured 0.02).
 */
export const BASIS_DEFAULT = { direct: 0.7, close: 0.5, proxy: 0.25 };

/** "Snapshot of Kalshi markets as of Nov 3, 2026 — prices may have moved" */
export function sourceLabel(catalog) {
  if (!catalog) return '';
  const when = catalog.as_of
    ? new Date(catalog.as_of).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
    : 'an unknown date';
  if (catalog.source === 'live') return `Live Kalshi prices · ${when}`;
  if (catalog.source === 'live-partial') return `Mostly live Kalshi prices · ${when} — some series fell back to a snapshot`;
  return `Snapshot of Kalshi markets as of ${when} — prices may have moved`;
}

export const isLive = catalog => catalog?.source === 'live' || catalog?.source === 'live-partial';

/** Find a market (and its series/industry) by ticker anywhere in the catalog. */
export function findMarket(catalog, ticker) {
  if (!catalog || !ticker) return null;
  for (const industry of catalog.industries) {
    for (const series of industry.series) {
      const market = series.markets.find(m => m.ticker === ticker);
      if (market) return { industry, series, market };
    }
  }
  return null;
}
