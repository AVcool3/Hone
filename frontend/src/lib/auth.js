/*
 * Optional accounts + saved portfolios via Supabase (see docs/SUPABASE.md).
 *
 * Uses the Supabase REST and GoTrue HTTP APIs directly — no SDK. When
 * public/config.js has no Supabase URL/key, `Auth.enabled` is false and the
 * app simply never shows sign-in: everything stays on this device.
 */
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
};

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
  async savePortfolio(name, data) {
    if (!session) throw new Error('Sign in to save to your account.');
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
    const res = await fetch(`${base}/rest/v1/portfolios?select=id,name,created_at,data&order=created_at.desc`, { headers: headers() });
    if (!res.ok) throw new Error('Could not load saved portfolios.');
    return res.json();
  },
  async deletePortfolio(id) {
    if (!session) return;
    await fetch(`${base}/rest/v1/portfolios?id=eq.${encodeURIComponent(id)}`, { method: 'DELETE', headers: headers() });
  },
};
