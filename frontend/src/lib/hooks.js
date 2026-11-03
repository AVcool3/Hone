/*
 * Hooks that talk to the engine. Pages call these instead of fetch() so
 * request shapes, staleness and error handling are identical everywhere.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { api, quote } from './api.js';
import { gammaSignature, portfolioSignature, usableThesis, useRisk, useWorkspace } from './store.jsx';

/* ------------------------------------------------------------ optimize */

/** Theses -> the `views` array /api/optimize expects. Excluded theses are left out. */
export const thesesToViews = theses =>
  theses
    .filter(usableThesis)
    .map(t => ({ ticker: t.ticker, target_price: t.target, confidence: t.confidence, horizon_days: t.horizonDays }));

/** The full /api/optimize request body for a workspace. */
export function buildOptimizeBody(gamma, ws, market, overrides = {}) {
  const body = {
    ...market,
    gamma,
    views: thesesToViews(ws.theses),
    max_weight: ws.maxWeight,
    portfolio_value: null,
    ...overrides,
  };
  // If the user has a scored track record, send the fitted map so the server
  // rescales their stated confidence before Black-Litterman sees it.
  if (ws.useCalibration !== false && ws.calibration?.actionable) body.calibration = ws.calibration;
  return body;
}

/**
 * The workspace's model-proposed allocation.
 * Returns the last saved result (even if stale), whether it is stale, and
 * `run()` to recalculate. Pass { auto: true } to calculate once on first
 * visit when there is no result yet.
 */
export function useOptimize(slug, { auto = false } = {}) {
  const { ws, market, saveResult, product } = useWorkspace(slug);
  const { gamma } = useRisk();
  const sig = portfolioSignature(gamma, ws);
  const saved = ws.results.optimize;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api(product.assetClass, '/api/optimize', buildOptimizeBody(gamma, ws, market));
      saveResult('optimize', data, sig);
      return data;
    } catch (e) {
      setError(e);
      return null;
    } finally {
      setBusy(false);
    }
  }, [gamma, ws, market, product.assetClass, saveResult, sig]);

  // Sample theses are stored as a relative change ("+20%") and only get a
  // dollar target once useThesisQuotes has fetched a reference price. If the
  // first auto-calculation ran before that, it would be built with no theses
  // at all, and then immediately flagged "Needs recalculation" when the
  // targets arrived — the first thing a new visitor saw. So wait for them.
  const pendingTargets = ws.theses.some(
    t => t.included && t.target == null && typeof t.targetChange === 'number',
  );

  const started = useRef(false);
  useEffect(() => {
    if (!auto || saved || started.current) return;
    const go = () => {
      started.current = true;
      run();
    };
    if (!pendingTargets) {
      go();
      return;
    }
    // Fallback: if a price lookup is slow or fails, calculate anyway after a
    // few seconds rather than leaving the page empty. (If the targets arrive
    // first, this effect re-runs, clears the timer, and calculates at once.)
    const timer = setTimeout(go, 5000);
    return () => clearTimeout(timer);
  }, [auto, saved, run, pendingTargets]);

  return { result: saved?.data ?? null, at: saved?.at, stale: !!saved && saved.sig !== sig, run, busy, error, sig };
}

/**
 * A gamma-only result (hedge plan, CVaR, backtest, portfolio analysis).
 * `request(gamma)` builds the body; the result is kept per `key`.
 * Large results can be kept in memory only with { persist: false }.
 */
export function useEngineResult(slug, key, path, request, { persist = true } = {}) {
  const { ws, market, saveResult, product, runtime, setRuntime } = useWorkspace(slug);
  const { gamma } = useRisk();
  const sig = gammaSignature(gamma, ws);
  const memKey = `${product.slug}:${key}`;
  const saved = persist ? ws.results[key] : runtime[memKey];
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api(product.assetClass, path, { ...market, ...request(gamma, ws) });
      if (persist) saveResult(key, data, sig);
      else setRuntime(memKey, { data, sig, at: new Date().toISOString() });
      return data;
    } catch (e) {
      setError(e);
      return null;
    } finally {
      setBusy(false);
    }
    // `request` is expected to be stable (defined at module level).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gamma, ws, market, product.assetClass, path, persist, key, memKey, saveResult, setRuntime, sig]);

  return { result: saved?.data ?? null, at: saved?.at, stale: !!saved && saved.sig !== sig, run, busy, error };
}

/* ------------------------------------------------------------ quotes */

const QUOTE_TTL_MS = 6 * 3600 * 1000;

/**
 * Keeps a reference price on every thesis (and fills in sample targets that
 * were stored as a relative change). Mounted once by the workspace layout.
 * Also returns the tradeable universe for the asset picker.
 */
export function useThesisQuotes(slug) {
  const { ws, market, product, update, runtime, setRuntime } = useWorkspace(slug);
  const inflight = useRef(new Set());
  const uniKey = `${product.slug}:universe`;

  useEffect(() => {
    if (product.slug === 'prediction-markets') return;
    const due = ws.theses.filter(
      t => t.ticker && !inflight.current.has(t.ticker) && (!t.refPrice || !t.refAt || Date.now() - new Date(t.refAt).getTime() > QUOTE_TTL_MS),
    );
    // One request per distinct ticker.
    const tickers = [...new Set(due.map(t => t.ticker))];
    tickers.forEach(ticker => {
      inflight.current.add(ticker);
      quote(product.assetClass, ticker, market)
        .then(q => {
          if (q.universe?.length) setRuntime(uniKey, q.universe);
          update(cur => ({
            ...cur,
            theses: cur.theses.map(t => {
              if (t.ticker !== ticker) return t;
              const next = { ...t, refPrice: q.price, refAt: q.at, tradeable: q.tradeable };
              if (next.target == null && typeof t.targetChange === 'number' && q.price) {
                next.target = Math.round(q.price * (1 + t.targetChange) * 100) / 100;
              }
              return next;
            }),
          }));
        })
        .catch(() => {})
        .finally(() => inflight.current.delete(ticker));
    });
  }, [ws.theses, market, product.assetClass, product.slug, update, setRuntime, uniKey]);

  return runtime[uniKey] || [];
}
