/*
 * Optional accounts + saved portfolios via Supabase (see docs/SUPABASE.md).
 *
 * Uses the Supabase REST and GoTrue HTTP APIs directly — no SDK. When
 * public/config.js has no Supabase URL/key, `Auth.enabled` is false and the
 * app simply never shows sign-in: everything stays on this device.
 */
import { useEffect, useState } from 'react';
import { KEYS, readJSON, writeJSON } from './storage.js';

const cfg = (typeof window !== 'undefined' && window.HONE_CONFIG) || {};
const base = (cfg.supabaseUrl || '').replace(/\/$/, '');
let session = readJSON(KEYS.session, null);

const headers = () => ({
  'Content-Type': 'application/json',
  apikey: cfg.supabaseAnonKey,
  ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}),
});
const persist = s => {
  session = s;
  writeJSON(KEYS.session, s);
  // Let any component showing sign-in state re-render (see useAuthUser).
  try { window.dispatchEvent(new Event('hone-auth-change')); } catch { /* no window */ }
};

/**
 * Supabase access tokens expire after about an hour. Swap in a fresh one
 * (using the refresh token) shortly before that, so a tab left open doesn't
 * start failing. Returns false if the session can't be renewed — the user is
 * then signed out and asked to sign in again.
 */
async function ensureFresh() {
  if (!session?.refresh_token) return !!session;
  const expiresAtMs = (session.expires_at || 0) * 1000;
  if (expiresAtMs - Date.now() > 60_000) return true;
  try {
    const d = await authCall('/token?grant_type=refresh_token', { refresh_token: session.refresh_token });
    persist(d);
    return true;
  } catch {
    persist(null);
    return false;
  }
}

async function authCall(path, payload) {
  const res = await fetch(`${base}/auth/v1${path}`, { method: 'POST', headers: headers(), body: JSON.stringify(payload) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error_description || data.msg || data.message || 'Sign-in failed');
  return data;
}

export const Auth = {
  enabled: !!(cfg.supabaseUrl && cfg.supabaseAnonKey),
  user: () => session?.user || null,
  async signUp(email, password) {
    await authCall('/signup', { email, password });
    return Auth.signIn(email, password);
  },
  async signIn(email, password) {
    const d = await authCall('/token?grant_type=password', { email, password });
    persist(d);
    return d.user;
  },
  signOut() {
    persist(null);
  },
  /** A current access token for the Hone server (X-Hone-Session), or null. */
  async accessToken() {
    if (!session) return null;
    return (await ensureFresh()) ? session.access_token : null;
  },

  /*
   * The brokerage link (SnapTrade user id + secret), kept in the user's own
   * row of `broker_links` so it follows them to other devices. Row-Level
   * Security means only they can read it (see docs/SUPABASE.md, step 2b).
   * All three fail soft: if the table doesn't exist yet, the link still
   * works on this device.
   */
  async getBrokerLink() {
    if (!session || !(await ensureFresh())) return null;
    const res = await fetch(`${base}/rest/v1/broker_links?select=snaptrade_user_id,snaptrade_user_secret`, { headers: headers() });
    if (!res.ok) return null;
    const row = (await res.json())[0];
    return row ? { userId: row.snaptrade_user_id, secret: row.snaptrade_user_secret } : null;
  },
  async saveBrokerLink(link) {
    if (!session || !(await ensureFresh())) return false;
    const res = await fetch(`${base}/rest/v1/broker_links`, {
      method: 'POST',
      // Upsert: one row per user, replaced if it already exists.
      headers: { ...headers(), Prefer: 'resolution=merge-duplicates' },
      body: JSON.stringify({
        user_id: session.user.id,
        snaptrade_user_id: link.userId,
        snaptrade_user_secret: link.secret,
        updated_at: new Date().toISOString(),
      }),
    });
    return res.ok;
  },
  async deleteBrokerLink() {
    if (!session || !(await ensureFresh())) return;
    await fetch(`${base}/rest/v1/broker_links?user_id=eq.${encodeURIComponent(session.user.id)}`, { method: 'DELETE', headers: headers() });
  },
  async savePortfolio(name, data) {
    if (!session) throw new Error('Sign in to save to your account.');
    await ensureFresh();
    const res = await fetch(`${base}/rest/v1/portfolios`, {
      method: 'POST',
      headers: { ...headers(), Prefer: 'return=representation' },
      body: JSON.stringify({ user_id: session.user.id, name, data }),
    });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).message || 'Save failed');
    return (await res.json())[0];
  },
  async listPortfolios() {
    if (!session) return [];
    await ensureFresh();
    const res = await fetch(`${base}/rest/v1/portfolios?select=id,name,created_at,data&order=created_at.desc`, { headers: headers() });
    if (!res.ok) throw new Error('Could not load saved portfolios.');
    return res.json();
  },
  async deletePortfolio(id) {
    if (!session) return;
    await fetch(`${base}/rest/v1/portfolios?id=eq.${encodeURIComponent(id)}`, { method: 'DELETE', headers: headers() });
  },
};

/** The signed-in user (or null), kept current when anyone signs in or out. */
export function useAuthUser() {
  const [user, setUser] = useState(() => Auth.user());
  useEffect(() => {
    const onChange = () => setUser(Auth.user());
    window.addEventListener('hone-auth-change', onChange);
    return () => window.removeEventListener('hone-auth-change', onChange);
  }, []);
  return user;
}
