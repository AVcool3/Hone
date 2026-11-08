/*
 * Waitlist sign-ups, saved to the `waitlist` table in Supabase.
 *
 * The browser writes straight to Supabase's REST API with the public
 * (publishable) key from public/config.js. That's safe because the table's
 * row-level security only allows INSERT: nobody can read the list from the
 * site, only from the Supabase dashboard. The SQL that creates the table is
 * in docs/SUPABASE.md, step 2c.
 *
 * To change what's collected: edit ROLES (the dropdown) and the `row` in
 * joinWaitlist, and add the matching column to the table.
 */
import { readJSON, writeJSON } from './storage.js';

const cfg = (typeof window !== 'undefined' && window.HONE_CONFIG) || {};
const base = (cfg.supabaseUrl || '').replace(/\/$/, '');

/** True when the site has a Supabase project to save sign-ups to. */
export const waitlistEnabled = !!(base && cfg.supabaseAnonKey);

/** The "what describes you best" options: value saved -> label shown. */
export const ROLES = [
  { value: 'business', label: 'I run a business that depends on the weather' },
  { value: 'worker', label: 'My pay depends on the weather' },
  { value: 'risk_pro', label: 'I work in insurance or risk' },
  { value: 'curious', label: 'Just interested' },
];

// Remembered in this browser so a returning visitor sees "you're on the list".
const JOINED_KEY = 'hone.waitlist.joined';
export const joinedEmail = () => readJSON(JOINED_KEY, null);

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export const validEmail = email => EMAIL_RE.test(String(email).trim()) && String(email).trim().length <= 254;

/**
 * Add someone to the waitlist. Resolves to 'joined' or 'already' (the email
 * was on the list before); throws an Error with a readable message otherwise.
 */
export async function joinWaitlist({ email, role, business, source = 'home' }) {
  if (!waitlistEnabled) throw new Error('The waitlist isn’t set up on this copy of the site yet.');
  const clean = String(email).trim().toLowerCase();
  if (!validEmail(clean)) throw new Error('That email address doesn’t look right.');
  const row = {
    email: clean,
    role: role || null,
    business: (business || '').trim().slice(0, 200) || null,
    source,
  };
  let res;
  try {
    res = await fetch(`${base}/rest/v1/waitlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: cfg.supabaseAnonKey,
        // "minimal": don't send the row back. The table can't be read with
        // this key, so asking for it back would fail.
        Prefer: 'return=minimal',
      },
      body: JSON.stringify(row),
    });
  } catch {
    throw new Error('Couldn’t reach the server. Check your connection and try again.');
  }
  // 409 = the unique index on the email fired: they're already signed up.
  const result = res.ok ? 'joined' : res.status === 409 ? 'already' : null;
  if (!result) throw new Error('Something went wrong saving your spot. Please try again in a minute.');
  writeJSON(JOINED_KEY, clean);
  return result;
}
