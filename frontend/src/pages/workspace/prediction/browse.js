/*
 * Hooks for browsing every open Kalshi market (the "All Kalshi markets" view
 * on the Markets page). The curated income-hedge catalog lives in catalog.js;
 * this file covers the rest of the exchange.
 *
 *   useKalshiSearch({ q, category })  → pages of events from
 *       GET /api/predict/browse. The server keeps an index of every open
 *       event (tens of thousands) and searches it, so the browser only ever
 *       downloads PAGE_SIZE results at a time.
 *
 *   useEventMarkets(eventTicker)      → the live markets in one event, from
 *       GET /api/predict/event/{ticker}, fetched when the event is opened and
 *       kept in the store's in-memory runtime for EVENT_TTL_MS.
 *
 * EDIT HERE: PAGE_SIZE, EVENT_TTL_MS, INDEX_POLL_MS.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../../../lib/api.js';
import { useStore } from '../../../lib/store.jsx';

/** Events per "page" of search results. */
export const PAGE_SIZE = 30;
/** Re-fetch an opened event's prices after this long. */
const EVENT_TTL_MS = 60 * 1000;
/** While the server is still indexing Kalshi, refresh the first page this often. */
const INDEX_POLL_MS = 10 * 1000;

/**
 * Search every open Kalshi event.
 *
 * @param q         search text (debounce it before passing it in)
 * @param category  a Kalshi category name, or '' for all
 * @returns { data, events, loading, error, loadMore, hasMore, reload }
 *   data    the latest response: { source, complete, building, indexed,
 *           total, categories: [{ name, count }], ... }
 *   events  every result loaded so far (grows with loadMore)
 */
export function useKalshiSearch({ q, category }) {
  const [data, setData] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0); // bump to re-run the first-page fetch
  const ctrl = useRef(null);

  const fetchPage = useCallback(
    async offset => {
      ctrl.current?.abort(); // a newer search supersedes an older one
      const c = new AbortController();
      ctrl.current = c;
      const params = new URLSearchParams({ q, offset: String(offset), limit: String(PAGE_SIZE) });
      if (category) params.set('category', category);
      setLoading(true);
      setError(null);
      try {
        const res = await api('prediction', `/api/predict/browse?${params}`, undefined, { signal: c.signal });
        setData(res);
        setEvents(prev => (offset === 0 ? res.events : [...prev, ...res.events]));
      } catch (e) {
        if (e.name !== 'AbortError') setError(e);
      } finally {
        if (ctrl.current === c) setLoading(false);
      }
    },
    [q, category],
  );

  // New query or category: start again from the first page.
  useEffect(() => { fetchPage(0); }, [fetchPage, tick]);
  useEffect(() => () => ctrl.current?.abort(), []);

  // The first index build takes a few minutes. Until it finishes, refresh the
  // first page now and then so counts grow — but not once the user has
  // loaded more pages (that would yank the list out from under them).
  const building = data && !data.complete && data.live_enabled;
  useEffect(() => {
    if (!building || events.length > PAGE_SIZE) return undefined;
    const t = setTimeout(() => setTick(x => x + 1), INDEX_POLL_MS);
    return () => clearTimeout(t);
  }, [building, events.length, data]);

  return {
    data,
    events,
    loading,
    error,
    hasMore: !!data && events.length < data.total,
    loadMore: () => fetchPage(events.length),
    reload: () => setTick(x => x + 1),
  };
}

/**
 * Live markets for one event; fetched only while `eventTicker` is set.
 * @returns { detail, loading, error, reload }
 *   detail  { event, markets: [...normalized markets], source, as_of }
 */
export function useEventMarkets(eventTicker) {
  const { runtime, setRuntimeKey } = useStore();
  const key = `pm:event:${eventTicker}`;
  const cached = eventTicker ? runtime[key] : null;
  const fresh = cached && Date.now() - cached.at < EVENT_TTL_MS;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!eventTicker) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api('prediction', `/api/predict/event/${encodeURIComponent(eventTicker)}`);
      setRuntimeKey(key, { at: Date.now(), detail: res });
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [eventTicker, key, setRuntimeKey]);

  useEffect(() => {
    if (eventTicker && !fresh) load();
    // `fresh` is read once per open; re-opening an event after a minute refetches.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventTicker]);

  return { detail: cached?.detail || null, loading: loading && !cached, error, reload: load };
}
