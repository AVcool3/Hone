/*
 * Data & account.
 *
 *   Data source   Sample data (default) or your own Alpaca *paper* account.
 *                 Keys travel with each request and are never stored on the
 *                 server; on this device they're kept for the session only
 *                 unless you tick "remember".
 *   Account       Optional Supabase sign-in to save portfolios (only shown
 *                 when public/config.js has Supabase configured).
 *   Reset         Start this product's workspace over.
 *
 * "Missing credentials" and "missing market data" are reported differently
 * (see ErrorNotice), so a typo in a key never looks like an empty market.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import { api, marketBody } from '../../lib/api.js';
import { Auth } from '../../lib/auth.js';
import { useStore, useWorkspace } from '../../lib/store.jsx';
import { docPath } from '../../lib/products.js';
import { fmtDate, fmtPct } from '../../lib/format.js';
import { Badge, Button, ErrorNotice, Field, Notice, PageHeader, SectionTitle } from '../../components/ui.jsx';

export default function SettingsPage() {
  const product = useProduct();
  const isPrediction = product.slug === 'prediction-markets';
  return (
    <>
      <PageHeader eyebrow="Workspace" title="Data & account" lede="Where the numbers come from, and where your work is kept." />
      <div className="stack-lg" style={{ maxWidth: 820 }}>
        {isPrediction
          ? <Notice tone="info" title="No connection needed.">Hone Markets reads Kalshi’s public market data and never places orders, so there are no keys to enter. Everything you type stays on this device.</Notice>
          : <DataSource product={product} />}
        <AccountCard product={product} />
        <ResetCard product={product} />
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ data source */
function DataSource({ product }) {
  const { ws, update } = useWorkspace(product.slug);
  const { alpaca, setAlpaca } = useStore();
  const [test, setTest] = useState({ busy: false, error: null, ok: null });

  const choose = src => {
    // New data source = new prices: clear reference prices and results so nothing mixes sources.
    update(cur => ({ ...cur, dataSource: src, results: {}, theses: cur.theses.map(t => ({ ...t, refPrice: null, refAt: null })) }));
  };

  const runTest = async () => {
    setTest({ busy: true, error: null, ok: null });
    try {
      const r = await api(product.assetClass, '/api/portfolio', marketBody('alpaca', alpaca));
      setTest({ busy: false, error: null, ok: r });
    } catch (e) {
      setTest({ busy: false, error: e, ok: null });
    }
  };

  return (
    <div className="card">
      <SectionTitle title="Data source" sub="Every tool in this workspace uses the same source, labelled at the top of the page." />
      <div className="choice-pair">
        <button type="button" className="choice" aria-pressed={ws.dataSource !== 'alpaca'} onClick={() => choose('sample')}>
          <span className="choice__tag">Sample data</span>
          <span className="choice__main" style={{ display: 'block', fontSize: 17 }}>Synthetic prices and a $25,000 sample portfolio</span>
          <span className="small muted">Nothing to set up. Good for exploring.</span>
        </button>
        <button type="button" className="choice" aria-pressed={ws.dataSource === 'alpaca'} onClick={() => choose('alpaca')}>
          <span className="choice__tag">Your paper account</span>
          <span className="choice__main" style={{ display: 'block', fontSize: 17 }}>{product.account}</span>
          <span className="small muted">Real prices and your paper holdings. Free; no real money.</span>
        </button>
      </div>

      {ws.dataSource === 'alpaca' && (
        <div className="stack mt-5">
          <div className="grid-2" style={{ gap: 16 }}>
            <Field label="API key ID" htmlFor="ak">
              <input id="ak" type="text" autoComplete="off" spellCheck={false} value={alpaca.apiKey} onChange={e => setAlpaca({ apiKey: e.target.value.trim() })} placeholder="PK…" />
            </Field>
            <Field label="Secret key" htmlFor="sk">
              <input id="sk" type="password" autoComplete="off" value={alpaca.secretKey} onChange={e => setAlpaca({ secretKey: e.target.value.trim() })} />
            </Field>
          </div>
          <label className="row small">
            <input type="checkbox" checked={!!alpaca.remember} onChange={e => setAlpaca({ remember: e.target.checked })} style={{ width: 20, height: 20, accentColor: 'var(--primary)' }} />
            Remember keys on this device (otherwise they’re forgotten when you close the tab)
          </label>
          <div className="row">
            <Button variant="secondary" icon="Plug01Icon" onClick={runTest} disabled={test.busy || !alpaca.apiKey}>{test.busy ? 'Testing…' : 'Test connection'}</Button>
            <Link className="small" to={docPath(product.slug, 'setup', 'how-hone-works')}>How to get paper keys</Link>
          </div>
          <ErrorNotice error={test.error} onRetry={runTest} />
          {test.ok && (
            <Notice tone="info" title="Connected.">
              {test.ok.positions.length ? `${test.ok.positions.length} positions found: ${test.ok.positions.slice(0, 5).map(p => `${p.symbol} ${fmtPct(p.weight)}`).join(', ')}${test.ok.positions.length > 5 ? '…' : ''}` : 'The account has no open positions — the model will start from cash.'}
            </Notice>
          )}
          <p className="tiny subtle">Keys are sent with each request over HTTPS and never stored by the Hone server. Use paper-trading keys only.</p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ account */
function AccountCard({ product }) {
  const { update, ws } = useWorkspace(product.slug);
  const [user, setUser] = useState(Auth.user());
  const [form, setForm] = useState({ email: '', password: '' });
  const [msg, setMsg] = useState(null);
  const [list, setList] = useState(null);

  useEffect(() => {
    if (user) Auth.listPortfolios().then(setList).catch(e => setMsg({ ok: false, text: e.message }));
  }, [user]);

  if (!Auth.enabled) {
    return (
      <div className="card">
        <SectionTitle title="Account" />
        <p className="muted">Your work is saved in this browser only. Optional sign-in isn’t configured on this server — see <Link to={docPath(product.slug, 'setup', 'accounts')}>Accounts & saved portfolios</Link>.</p>
      </div>
    );
  }

  const go = async kind => {
    setMsg(null);
    try {
      const u = kind === 'up' ? await Auth.signUp(form.email, form.password) : await Auth.signIn(form.email, form.password);
      setUser(u);
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    }
  };

  if (!user) {
    return (
      <div className="card">
        <SectionTitle title="Account" sub="Optional. Sign in only if you want portfolios on more than one device." />
        <div className="grid-2" style={{ gap: 16 }}>
          <Field label="Email" htmlFor="em"><input id="em" type="email" autoComplete="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} /></Field>
          <Field label="Password" htmlFor="pw"><input id="pw" type="password" autoComplete="current-password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} /></Field>
        </div>
        <div className="row mt-4">
          <Button icon="Login01Icon" onClick={() => go('in')} disabled={!form.email || !form.password}>Sign in</Button>
          <Button variant="secondary" onClick={() => go('up')} disabled={!form.email || !form.password}>Create account</Button>
        </div>
        {msg && <p className="tiny loss mt-2">{msg.text}</p>}
      </div>
    );
  }

  const load = p => {
    const d = p.data || {};
    if (d.product && d.product !== product.slug) { setMsg({ ok: false, text: `That portfolio belongs to ${d.product}. Switch product to load it.` }); return; }
    update({ theses: d.theses || ws.theses, maxWeight: d.maxWeight ?? ws.maxWeight, results: {} });
    setMsg({ ok: true, text: `Loaded “${p.name}”.` });
  };

  return (
    <div className="card">
      <SectionTitle title="Account" sub={`Signed in as ${user.email}`} right={<Button variant="text" icon="Logout01Icon" onClick={() => { Auth.signOut(); setUser(null); }}>Sign out</Button>} />
      <h3 style={{ fontSize: 16 }} className="mb-2">Saved portfolios</h3>
      {list == null ? <p className="muted">Loading…</p> : list.length === 0 ? <p className="muted">None yet — save one from the Portfolio page.</p> : (
        <ul className="plain-list">
          {list.map(p => (
            <li key={p.id} className="row row--between">
              <span>{p.name} <span className="subtle tiny">· {fmtDate(p.created_at)} {p.data?.product && <Badge>{p.data.product}</Badge>}</span></span>
              <span className="row">
                <Button variant="text" size="sm" onClick={() => load(p)}>Load</Button>
                <Button variant="text" size="sm" className="btn--danger" onClick={async () => { await Auth.deletePortfolio(p.id); setList(l => l.filter(x => x.id !== p.id)); }}>Delete</Button>
              </span>
            </li>
          ))}
        </ul>
      )}
      {msg && <p className={`tiny mt-2 ${msg.ok ? '' : 'loss'}`}>{msg.text}</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ reset */
function ResetCard({ product }) {
  const { reset } = useWorkspace(product.slug);
  return (
    <div className="card">
      <SectionTitle title="Start over" sub={`Restores the ${product.name} workspace to its sample state. Your risk profile and journal are kept.`} />
      <Button variant="secondary" className="btn--danger" icon="Delete02Icon" onClick={() => { if (window.confirm(`Reset the ${product.name} workspace?`)) reset(); }}>
        Reset {product.name} workspace
      </Button>
    </div>
  );
}
