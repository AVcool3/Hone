/*
 * Linked brokerages — every account at every broker, combined.
 *
 * Shown on Data & account when the data source is "Your brokerages".
 * Linking goes through SnapTrade (hone/market_data/brokers/snaptrade.py):
 *
 *   1. "Connect a brokerage" asks the server for a SnapTrade Connection
 *      Portal URL. The first time, the server also creates this person's
 *      SnapTrade user and returns a link { userId, secret } — kept in the
 *      store (this browser) and, when signed in, in their own Supabase row.
 *   2. The browser goes to SnapTrade's page. The user picks Schwab, Fidelity,
 *      Robinhood, ... and signs in *there*; Hone never sees that password.
 *   3. SnapTrade sends them back here with ?broker=connected. We refresh the
 *      list of connections and accounts, and clear old results so every tool
 *      recalculates from the real holdings.
 *
 * Everything is read-only: Hone asks SnapTrade for data access only.
 */
import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api } from '../../lib/api.js';
import { Auth, useAuthUser } from '../../lib/auth.js';
import { KEYS, readJSON, writeJSON } from '../../lib/storage.js';
import { useStore, useWorkspace } from '../../lib/store.jsx';
import { fmtMoney, fmtPct } from '../../lib/format.js';
import { Badge, Button, ErrorNotice, Notice } from '../../components/ui.jsx';

/** A random id for linking without sign-in (private servers only). */
function localId() {
  let id = readJSON(KEYS.brokerLocalId, null);
  if (!id) {
    id = window.crypto?.randomUUID?.()
      // randomUUID needs https or localhost; fall back to random hex.
      ?? Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
    writeJSON(KEYS.brokerLocalId, id);
  }
  return id;
}

/** { userId, secret } (browser shape) -> { user_id, user_secret } (API shape). */
const toApi = link => (link ? { user_id: link.userId, user_secret: link.secret } : null);

export default function BrokeragesPanel({ product, config, onLinksChanged }) {
  const { broker, setBroker } = useStore();
  const { market } = useWorkspace(product.slug);
  const user = useAuthUser();
  const location = useLocation();
  const navigate = useNavigate();

  const [list, setList] = useState(null);       // { connections, accounts } from the server
  const [busy, setBusy] = useState(null);       // which action is running, for button labels
  const [error, setError] = useState(null);
  const [canReset, setCanReset] = useState(false);
  const [returned, setReturned] = useState(false);
  const [check, setCheck] = useState({ busy: false, ok: null, error: null });

  const needsSignIn = config.requires_sign_in && !user;

  /** Call a /api/broker/* endpoint, with the sign-in token when there is one. */
  const call = useCallback(async (path, body) => {
    const token = await Auth.accessToken();
    return api(product.assetClass, path, body, { headers: token ? { 'X-Hone-Session': token } : undefined });
  }, [product.assetClass]);

  /* Signed in on a new device: fetch the link saved with the account. */
  useEffect(() => {
    if (user && !broker) Auth.getBrokerLink().then(l => l && setBroker(l)).catch(() => {});
    // Signed out: forget an account-owned link on this device (shared computers).
    if (!user && broker?.userId && !broker.userId.startsWith('hone-local-') && config.requires_sign_in) setBroker(null);
  }, [user, broker, setBroker, config.requires_sign_in]);

  /* Load what's linked whenever the link changes. */
  const refresh = useCallback(async () => {
    if (!broker) { setList(null); return; }
    setError(null);
    try {
      setList(await call('/api/broker/accounts', { link: toApi(broker) }));
    } catch (e) {
      setError(e);
    }
  }, [broker, call]);
  useEffect(() => { refresh(); }, [refresh]);

  /* Back from SnapTrade's page: say so, drop the query param, and make every
     tool recalculate from the newly linked holdings. */
  useEffect(() => {
    if (new URLSearchParams(location.search).has('broker')) {
      setReturned(true);
      onLinksChanged();
      navigate(location.pathname, { replace: true });
    }
    // Run once on arrival only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Go to SnapTrade's Connection Portal (new link, another broker, or a repair). */
  const connect = async ({ reconnect = null, reset = false } = {}) => {
    setBusy(reconnect ? `reconnect:${reconnect}` : 'connect');
    setError(null);
    setCanReset(false);
    try {
      const r = await call('/api/broker/connect', {
        link: reset ? null : toApi(broker),
        local_id: localId(),
        redirect_url: `${window.location.origin}${location.pathname}?broker=connected`,
        reconnect,
        reset,
      });
      const link = { userId: r.link.user_id, secret: r.link.user_secret };
      if (!broker || broker.userId !== link.userId || broker.secret !== link.secret) {
        setBroker(link);
        // Best effort: keep it with the account so other devices can use it.
        if (user) await Auth.saveBrokerLink(link).catch(() => false);
      }
      window.location.assign(r.redirect_url);
    } catch (e) {
      setError(e);
      setCanReset(e.status === 409); // linked elsewhere, but we lost the key
      setBusy(null);
    }
  };

  const disconnect = async conn => {
    if (!window.confirm(`Unlink ${conn.brokerage}? Its accounts leave your portfolio here (nothing changes at ${conn.brokerage}).`)) return;
    setBusy(`disconnect:${conn.id}`);
    try {
      await call('/api/broker/disconnect', { link: toApi(broker), connection_id: conn.id });
      onLinksChanged();
      await refresh();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  };

  const unlinkAll = async () => {
    if (!window.confirm('Remove every brokerage link? Hone forgets them on this device and in your account.')) return;
    setBusy('unlink');
    try {
      await call('/api/broker/unlink', { link: toApi(broker) });
    } catch {
      // Even if the server can't confirm (link already invalid), forget it here.
    }
    await Auth.deleteBrokerLink().catch(() => {});
    setBroker(null);
    setList(null);
    setCheck({ busy: false, ok: null, error: null });
    onLinksChanged();
    setBusy(null);
  };

  /** Pull holdings through the same path every tool uses, and show the result. */
  const runCheck = async () => {
    setCheck({ busy: true, ok: null, error: null });
    try {
      setCheck({ busy: false, ok: await api(product.assetClass, '/api/portfolio', market), error: null });
    } catch (e) {
      setCheck({ busy: false, ok: null, error: e });
    }
  };

  /* ---------------------------------------------------------------- render */
  if (needsSignIn) {
    return (
      <Notice tone="info" title="Sign in to link your brokerages.">
        Links are kept with your Hone account, so they work on any device. Use the Account section below.
      </Notice>
    );
  }

  const conns = list?.connections ?? [];
  const accounts = list?.accounts ?? [];

  return (
    <div className="stack">
      <p className="muted">
        Link as many brokerages as you like — Schwab, Fidelity, Robinhood, Interactive Brokers, Webull, Coinbase and more.
        Every account is combined into one portfolio. You sign in on SnapTrade’s secure page, Hone asks for <strong>read-only</strong> access,
        and it never places trades.
      </p>

      {returned && !error && <Notice tone="info" title="Back from your brokerage.">If you finished linking, it’s listed below. New accounts can take a minute to appear — press Refresh.</Notice>}

      {conns.length > 0 && (
        <ul className="plain-list">
          {conns.map(c => (
            <li key={c.id} className="row row--between">
              <span className="row">
                {c.logo_url && <img src={c.logo_url} alt="" width={24} height={24} style={{ borderRadius: 6 }} />}
                <strong>{c.brokerage}</strong>
                {c.disabled && <Badge tone="stale" title="The brokerage stopped sharing data — usually after a password change.">Needs reconnecting</Badge>}
              </span>
              <span className="row">
                {c.disabled && <Button variant="secondary" size="sm" onClick={() => connect({ reconnect: c.id })} disabled={!!busy}>{busy === `reconnect:${c.id}` ? 'Opening…' : 'Reconnect'}</Button>}
                <Button variant="text" size="sm" className="btn--danger" onClick={() => disconnect(c)} disabled={!!busy}>{busy === `disconnect:${c.id}` ? 'Unlinking…' : 'Unlink'}</Button>
              </span>
            </li>
          ))}
        </ul>
      )}

      {accounts.length > 0 && (
        <div>
          <h3 style={{ fontSize: 16 }} className="mb-2">Accounts</h3>
          <ul className="plain-list">
            {accounts.map(a => (
              <li key={a.id} className="row row--between">
                <span>
                  {a.label}{' '}
                  {a.is_paper && <Badge>Paper</Badge>}{' '}
                  {!a.investment && <Badge title="Bank, credit and annuity accounts aren’t part of the portfolio">Not modelled</Badge>}
                </span>
                <span className="tiny subtle">{a.value != null ? (a.currency && a.currency !== 'USD' ? `${a.value.toLocaleString()} ${a.currency}` : fmtMoney(a.value)) : '—'}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {broker && list && conns.length === 0 && <p className="muted">Nothing linked yet.</p>}

      <div className="row">
        <Button icon="Add01Icon" onClick={() => connect()} disabled={!!busy}>
          {busy === 'connect' ? 'Opening SnapTrade…' : conns.length ? 'Link another brokerage' : 'Link a brokerage'}
        </Button>
        {conns.length > 0 && <Button variant="secondary" icon="Plug01Icon" onClick={runCheck} disabled={check.busy || !!busy}>{check.busy ? 'Checking…' : 'Check holdings'}</Button>}
        {broker && <Button variant="text" icon="RefreshIcon" onClick={refresh} disabled={!!busy}>Refresh</Button>}
      </div>

      <ErrorNotice error={error} />
      {canReset && (
        <Notice tone="info" title="Start the link over?" actions={<Button variant="secondary" size="sm" onClick={() => connect({ reset: true })}>Reset and relink</Button>}>
          You’ll sign in to each brokerage again. Nothing changes at the brokerages themselves.
        </Notice>
      )}

      <ErrorNotice error={check.error} onRetry={runCheck} />
      {check.ok && <HoldingsSummary result={check.ok} />}

      <div className="row row--between">
        <p className="tiny subtle">Holdings come from your brokerages through SnapTrade; prices come from Alpaca market data.</p>
        {broker && <Button variant="text" size="sm" className="btn--danger" onClick={unlinkAll} disabled={!!busy}>{busy === 'unlink' ? 'Removing…' : 'Remove all brokerage links'}</Button>}
      </div>
    </div>
  );
}

/** What "Check holdings" found: what's modelled, and what was left out and why. */
function HoldingsSummary({ result }) {
  const { positions = [], skipped = [], accounts = [], portfolio_value: value } = result;
  return (
    <Notice tone="info" title={`${positions.length} holdings across ${accounts.length} account${accounts.length === 1 ? '' : 's'}${value ? ` · ${fmtMoney(value)} modelled` : ''}.`}>
      {positions.slice(0, 6).map(p => `${p.symbol} ${fmtPct(p.weight)}`).join(', ')}
      {positions.length > 6 ? '…' : ''}
      {skipped.length > 0 && (
        <details className="mt-2">
          <summary className="small">{skipped.length} position{skipped.length === 1 ? '' : 's'} not included — why</summary>
          <ul className="plain-list tiny mt-2">
            {skipped.map((k, i) => (
              <li key={`${k.symbol}-${i}`}>
                <strong>{k.symbol}</strong>{k.market_value != null ? ` (${fmtMoney(k.market_value)})` : ''} — {k.reason}
                {k.account ? <span className="subtle"> · {k.account}</span> : null}
              </li>
            ))}
          </ul>
        </details>
      )}
    </Notice>
  );
}
