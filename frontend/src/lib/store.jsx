/*
 * App state, shared across pages and persisted to this browser.
 *
 * Design rules (from the redesign brief):
 *  - Every workspace section is independent: you can open Theses before you
 *    have a risk profile. When an input is missing we fall back to a clearly
 *    labelled SAMPLE value instead of blocking the page.
 *  - Inputs are shared: the risk profile is one object used by all three
 *    products; theses/settings are per product.
 *  - Results remember the inputs that produced them (`sig`). If you edit an
 *    input afterwards, the result is kept but marked "Needs recalculation".
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { PRODUCTS, productFromSlug } from './products.js';
import { KEYS, migrateLegacyJournal, readJSON, writeJSON } from './storage.js';
import { marketBody } from './api.js';

/** Risk aversion used when you haven't measured yours. Labelled "sample" everywhere. */
export const SAMPLE_GAMMA = 2.0;

export const newId = () => Math.random().toString(36).slice(2, 10);

/* ----------------------------------------------------------------- defaults */

/*
 * Sample theses. Targets are stored as a relative change and turned into a
 * price the first time a reference price loads (sample prices move daily).
 */
const SAMPLE_THESES = {
  stocks: [
    { ticker: 'TSLA', targetChange: 0.2, confidence: 0.6, horizonDays: 365, rationale: 'Sample view: deliveries recover and margins stabilise.' },
    { ticker: 'MSFT', targetChange: -0.05, confidence: 0.4, horizonDays: 180, rationale: 'Sample view: a soft patch as AI capex weighs on margins.' },
  ],
  crypto: [
    { ticker: 'SOL/USD', targetChange: 0.25, confidence: 0.6, horizonDays: 180, rationale: 'Sample view: network usage keeps growing faster than issuance.' },
    { ticker: 'ETH/USD', targetChange: -0.1, confidence: 0.35, horizonDays: 120, rationale: 'Sample view: fees stay low while activity moves to layer 2s.' },
  ],
  'prediction-markets': [],
};

export function makeThesis(partial = {}) {
  return {
    id: newId(),
    ticker: '',
    target: null,          // absolute price target
    targetChange: null,    // used only to seed `target` once a reference price loads
    confidence: 0.5,       // 0–1, see the Confidence definition in docs/CALIBRATION.md
    horizonDays: 365,
    rationale: '',
    included: true,        // excluded theses are kept but not sent to the model
    sample: false,
    refPrice: null,        // reference price and when it was fetched
    refAt: null,
    tradeable: true,
    createdAt: new Date().toISOString(),
    ...partial,
  };
}

function defaultWorkspace(slug) {
  return {
    dataSource: 'sample',            // 'sample' | 'alpaca'
    theses: (SAMPLE_THESES[slug] || []).map(t => makeThesis({ ...t, sample: true })),
    maxWeight: 0.35,                 // largest single position the optimizer may propose
    useCalibration: true,            // apply your track-record confidence map when it's actionable
    calibration: null,               // last fitted map from the journal
    flexViews: [],                   // entropy-pooling views (Theses → More view types)
    pm: {                            // Prediction Markets income-hedge inputs
      industry: 'snow',
      seriesTicker: null,
      marketTicker: null,
      side: 'no',
      price: 0.3,
      label: '',
      wealth: 40000,
      loss: 12000,
      ownProb: null,
      confidence: 0,
      basis: 1,
    },
    results: {},                     // { optimize: {data, sig, at}, ... } — small results only
    savedAt: null,
  };
}

function defaultProfile() {
  return {
    gamma: null,          // CRRA risk-aversion coefficient (γ); null = not measured
    source: null,         // 'adaptive' | 'full' | 'manual'
    sd: null,             // posterior standard deviation (adaptive) or standard error (full)
    ci: null,             // [lo, hi] interval
    ciLevel: null,        // 0.9 or 0.95
    tier: null,           // TierInfo from the server
    summary: '',
    assessedAt: null,
    history: [],          // previous assessments, newest first
    dose: { answers: [] },        // adaptive questionnaire in progress
    full: { choices: null, round: 0 }, // 30-question menu in progress
  };
}

/* ----------------------------------------------------------------- signatures */

const r3 = x => (typeof x === 'number' ? Math.round(x * 1000) / 1000 : x);

export const validThesis = t =>
  t.ticker && typeof t.target === 'number' && t.target > 0 && t.confidence > 0 && t.horizonDays > 0;

/** Sent to the model: included, complete, and has price history here. */
export const usableThesis = t => t.included && validThesis(t) && t.tradeable !== false;

/** The inputs a portfolio result depends on, as a comparable string. */
export function portfolioSignature(gamma, ws) {
  return JSON.stringify({
    g: r3(gamma),
    d: ws.dataSource,
    mw: r3(ws.maxWeight),
    cal: ws.useCalibration && ws.calibration?.actionable ? [r3(ws.calibration.intercept), r3(ws.calibration.slope)] : null,
    t: ws.theses
      .filter(usableThesis)
      .map(t => [t.ticker, r3(t.target), r3(t.confidence), r3(t.horizonDays)]),
  });
}

/** Inputs for gamma-only results (hedge plan, CVaR, backtest). */
export const gammaSignature = (gamma, ws) => JSON.stringify({ g: r3(gamma), d: ws.dataSource, mw: r3(ws.maxWeight) });

/* ----------------------------------------------------------------- context */

const StoreCtx = createContext(null);

export function StoreProvider({ children }) {
  const [profile, setProfileState] = useState(() => ({ ...defaultProfile(), ...readJSON(KEYS.profile, {}) }));
  const [alpaca, setAlpacaState] = useState(
    () => readJSON(KEYS.alpaca, null) || readJSON(KEYS.alpaca, null, 'session') || { apiKey: '', secretKey: '', remember: false },
  );
  const [workspaces, setWorkspaces] = useState(() => {
    const out = {};
    for (const slug of Object.keys(PRODUCTS)) out[slug] = { ...defaultWorkspace(slug), ...readJSON(KEYS.ws(slug), {}) };
    return out;
  });
  const [journals, setJournals] = useState(() => {
    const out = {};
    for (const [slug, p] of Object.entries(PRODUCTS)) out[slug] = migrateLegacyJournal(slug, p.assetClass);
    return out;
  });
  // Large or short-lived results (backtests, market catalogs) live in memory only.
  const [runtime, setRuntime] = useState({});

  /* persist ------------------------------------------------------------- */
  useEffect(() => { writeJSON(KEYS.profile, profile); }, [profile]);
  useEffect(() => {
    // Keys go to localStorage only if the user ticked "remember on this device".
    if (alpaca.remember) { writeJSON(KEYS.alpaca, alpaca); writeJSON(KEYS.alpaca, null, 'session'); }
    else { writeJSON(KEYS.alpaca, null); writeJSON(KEYS.alpaca, alpaca, 'session'); }
  }, [alpaca]);
  useEffect(() => {
    for (const [slug, ws] of Object.entries(workspaces)) writeJSON(KEYS.ws(slug), ws);
  }, [workspaces]);
  useEffect(() => {
    for (const [slug, j] of Object.entries(journals)) writeJSON(KEYS.journal(slug), j);
  }, [journals]);

  /* updaters ------------------------------------------------------------ */
  const setProfile = useCallback(patch => {
    setProfileState(prev => ({ ...prev, ...(typeof patch === 'function' ? patch(prev) : patch) }));
  }, []);
  const setAlpaca = useCallback(patch => setAlpacaState(prev => ({ ...prev, ...patch })), []);
  const updateWs = useCallback((slug, patch) => {
    setWorkspaces(prev => {
      const cur = prev[slug];
      const next = typeof patch === 'function' ? patch(cur) : { ...cur, ...patch };
      return { ...prev, [slug]: { ...next, savedAt: new Date().toISOString() } };
    });
  }, []);
  const resetWs = useCallback(slug => {
    setWorkspaces(prev => ({ ...prev, [slug]: defaultWorkspace(slug) }));
  }, []);
  const setJournal = useCallback((slug, entries) => {
    setJournals(prev => ({ ...prev, [slug]: typeof entries === 'function' ? entries(prev[slug] || []) : entries }));
  }, []);
  const setRuntimeKey = useCallback((key, value) => setRuntime(prev => ({ ...prev, [key]: value })), []);

  const value = useMemo(
    () => ({ profile, setProfile, alpaca, setAlpaca, workspaces, updateWs, resetWs, journals, setJournal, runtime, setRuntimeKey }),
    [profile, setProfile, alpaca, setAlpaca, workspaces, updateWs, resetWs, journals, setJournal, runtime, setRuntimeKey],
  );
  return <StoreCtx.Provider value={value}>{children}</StoreCtx.Provider>;
}

export const useStore = () => useContext(StoreCtx);

/* ----------------------------------------------------------------- hooks */

/** The risk profile plus the gamma to actually use (yours, or the sample). */
export function useRisk() {
  const { profile, setProfile } = useStore();
  const measured = typeof profile.gamma === 'number';
  return {
    profile,
    setProfile,
    measured,
    gamma: measured ? profile.gamma : SAMPLE_GAMMA,
    isSample: !measured,
  };
}

/** Everything a workspace page needs for one product. */
export function useWorkspace(slug) {
  const store = useStore();
  const product = productFromSlug(slug);
  const ws = store.workspaces[product.slug];
  const update = useCallback(patch => store.updateWs(product.slug, patch), [store.updateWs, product.slug]);
  const market = useMemo(() => marketBody(ws.dataSource, store.alpaca), [ws.dataSource, store.alpaca]);

  /** Store a result alongside the signature of the inputs that produced it. */
  const saveResult = useCallback(
    (key, data, sig) => update(cur => ({ ...cur, results: { ...cur.results, [key]: { data, sig, at: new Date().toISOString() } } })),
    [update],
  );
  const updateThesis = useCallback(
    (id, patch) => update(cur => ({ ...cur, theses: cur.theses.map(t => (t.id === id ? { ...t, ...patch, sample: patch.sample ?? false } : t)) })),
    [update],
  );
  return {
    product,
    ws,
    update,
    market,
    saveResult,
    updateThesis,
    journal: store.journals[product.slug] || [],
    setJournal: entries => store.setJournal(product.slug, entries),
    runtime: store.runtime,
    setRuntime: store.setRuntimeKey,
    alpaca: store.alpaca,
    reset: () => store.resetWs(product.slug),
  };
}

/** Debounce a changing value (used for live recalculation while dragging). */
export function useDebounced(value, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

/** Keep the latest async request only; abort the ones it supersedes. */
export function useLatestRequest() {
  const ctrl = useRef(null);
  useEffect(() => () => ctrl.current?.abort(), []);
  return useCallback(fn => {
    ctrl.current?.abort();
    const c = new AbortController();
    ctrl.current = c;
    return fn(c.signal);
  }, []);
}
