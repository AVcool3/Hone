/*
 * Browser storage helpers. Every read/write is wrapped: storage can be
 * blocked (private windows, strict settings) and the app must still work —
 * it just won't remember anything between visits.
 *
 * Key scheme (v2 redesign):
 *   hone:v2:profile            risk profile, shared by all three products
 *   hone:v2:ws:<product>       one product's workspace (theses, settings, results)
 *   hone:v2:journal:<product>  decision journal entries
 *   hone:v2:alpaca             Alpaca paper keys (only if "remember" is ticked)
 */

export const KEYS = {
  profile: 'hone:v2:profile',
  ws: slug => `hone:v2:ws:${slug}`,
  journal: slug => `hone:v2:journal:${slug}`,
  alpaca: 'hone:v2:alpaca',
  session: 'hone-session', // Supabase session (unchanged so existing sign-ins survive)
};

export function readJSON(key, fallback, store = 'local') {
  try {
    const s = store === 'session' ? window.sessionStorage : window.localStorage;
    const raw = s.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function writeJSON(key, value, store = 'local') {
  try {
    const s = store === 'session' ? window.sessionStorage : window.localStorage;
    if (value === undefined || value === null) s.removeItem(key);
    else s.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

/*
 * One-time import of the pre-redesign journal (key "hone-journal:<asset_class>").
 * A journal is a record of past decisions at past prices — it cannot be
 * recreated, so it is worth carrying across. Nothing else is migrated.
 */
export function migrateLegacyJournal(slug, assetClass) {
  const next = readJSON(KEYS.journal(slug), null);
  if (next) return next;
  const old = readJSON(`hone-journal:${assetClass}`, null);
  if (Array.isArray(old) && old.length) {
    writeJSON(KEYS.journal(slug), old);
    return old;
  }
  return [];
}
