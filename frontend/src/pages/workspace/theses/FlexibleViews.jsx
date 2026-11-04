/*
 * FlexibleViews — "More view types": beliefs that aren't price targets,
 * handled by entropy pooling (/api/pooling, docs/FLEXIBLE_VIEWS.md).
 *
 *   probability  "There's a 30% chance TSLA falls more than 10%"
 *   ranking      "AAPL will do better than MSFT"
 *   volatility   "SOL will swing about 20% in a typical month"
 *   mean         "JNJ returns about 2% a month"
 *   conditional  "If SPY falls 10%, TSLA falls about 20%"
 *
 * Views only ever cost history: the engine reweights past scenarios to make
 * your views true, and the page shows how many scenarios that discards.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../../lib/api.js';
import { newId } from '../../../lib/store.jsx';
import { docPath } from '../../../lib/products.js';
import { fmtPct, fmtSPct } from '../../../lib/format.js';
import AllocationBars from '../../../components/AllocationBars.jsx';
import { Badge, Button, ErrorNotice, Field, Notice, SectionTitle, Stat } from '../../../components/ui.jsx';

const KINDS = [
  { value: 'probability', label: 'Chance of a move', help: 'The chance this asset’s one-month return is at or below a level.' },
  { value: 'ranking', label: 'Ranking', help: 'This asset will return at least as much as another.' },
  { value: 'volatility', label: 'Volatility', help: 'How much this asset will swing in a typical month (standard deviation of monthly returns).' },
  { value: 'mean', label: 'Expected return', help: 'The average one-month return you expect.' },
  { value: 'conditional', label: 'If … then …', help: 'If this asset falls to a level, what the other one does on average.' },
];

/** Readable sentence for one view. */
function describe(v) {
  const pct = x => fmtSPct(x, 0);
  switch (v.kind) {
    case 'probability': return `${fmtPct(v.value)} chance ${v.ticker} returns ${pct(v.threshold)} or worse in a month`;
    case 'ranking': return `${v.ticker} does at least as well as ${v.versus}`;
    case 'volatility': return `${v.ticker} swings about ${fmtPct(v.value)} in a typical month`;
    case 'mean': return `${v.ticker} returns about ${pct(v.value)} a month`;
    case 'conditional': return `If ${v.ticker} returns ${pct(v.threshold)} or worse, ${v.versus} returns about ${pct(v.value)}`;
    default: return '';
  }
}

/** Pick a second symbol different from the first, so "if BTC falls, BTC falls" can't happen by default. */
const otherThan = (list, sym) => list.find(s => s !== sym) ?? '';

export default function FlexibleViews({ product, market, gamma, ws, update, universe }) {
  const syms = universe.length ? universe : product.slug === 'crypto' ? ['BTC/USD', 'ETH/USD', 'SOL/USD'] : ['AAPL', 'MSFT', 'SPY', 'TSLA', 'JNJ'];
  const views = ws.flexViews || [];
  const [draft, setDraft] = useState(() => ({ kind: 'probability', ticker: syms[0], versus: otherThan(syms, syms[0]), threshold: -0.1, value: 0.3 }));
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const kind = KINDS.find(k => k.value === draft.kind);
  const needsVersus = draft.kind === 'ranking' || draft.kind === 'conditional';
  const needsThreshold = draft.kind === 'probability' || draft.kind === 'conditional';
  const needsValue = draft.kind !== 'ranking';
  const setD = patch => setDraft(d => {
    const n = { ...d, ...patch };
    if (n.versus === n.ticker) n.versus = otherThan(syms, n.ticker);
    return n;
  });

  const add = () => {
    update(cur => ({ ...cur, flexViews: [...(cur.flexViews || []), { ...draft, id: newId() }] }));
  };
  const remove = id => update(cur => ({ ...cur, flexViews: cur.flexViews.filter(v => v.id !== id) }));

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const body = {
        ...market,
        gamma,
        max_weight: ws.maxWeight,
        views: views.map(({ kind: k, ticker, versus, threshold, value }) => ({
          kind: k, ticker,
          versus: k === 'ranking' || k === 'conditional' ? versus : null,
          threshold: k === 'probability' || k === 'conditional' ? threshold : null,
          value: k === 'ranking' ? null : value,
        })),
      };
      setRes(await api(product.assetClass, '/api/pooling', body));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  // Value field: probability in %, volatility in %, returns in % (signed).
  const valueField = {
    probability: { label: 'Chance', suffix: '%', min: 1, max: 99 },
    volatility: { label: 'Monthly volatility', suffix: '%', min: 1, max: 100 },
    mean: { label: 'Monthly return', suffix: '%', min: -50, max: 50 },
    conditional: { label: `${draft.versus || 'Other'} returns`, suffix: '%', min: -80, max: 80 },
  }[draft.kind];

  return (
    <div className="stack-lg">
      <Notice tone="info">
        Price targets can’t express every belief. These views reweight history instead: Hone keeps the past scenarios and makes
        the ones consistent with your view more likely. Views only ever cost history — the more a view disagrees with the past,
        the fewer scenarios still count. Treat the result as a stress test rather than a forecast.{' '}
        <Link to={docPath(product.slug, 'methodology', 'flexible-views')}>Full method</Link>
      </Notice>

      <div className="card">
        <SectionTitle title="Add a view" sub={kind.help} />
        <div className="grid-2" style={{ gap: 16 }}>
          <Field label="Kind of view">
            <select value={draft.kind} onChange={e => setD({ kind: e.target.value })}>
              {KINDS.map(k => <option key={k.value} value={k.value}>{k.label}</option>)}
            </select>
          </Field>
          <Field label={needsVersus && draft.kind === 'conditional' ? 'If this asset…' : 'Asset'}>
            <select value={draft.ticker} onChange={e => setD({ ticker: e.target.value })}>
              {syms.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
          {needsThreshold && (
            <Field label={draft.kind === 'conditional' ? '…falls to (monthly return)' : 'Monthly return at or below'}>
              <input type="number" step="1" value={Math.round(draft.threshold * 100)} onChange={e => setD({ threshold: +e.target.value / 100 })} aria-label="Threshold, percent" />
            </Field>
          )}
          {needsVersus && (
            <Field label={draft.kind === 'ranking' ? '…does at least as well as' : '…then this asset'}>
              <select value={draft.versus} onChange={e => setD({ versus: e.target.value })}>
                {syms.filter(s => s !== draft.ticker).map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
          )}
          {needsValue && valueField && (
            <Field label={`${valueField.label} (${valueField.suffix})`}>
              <input type="number" step="1" min={valueField.min} max={valueField.max} value={Math.round(draft.value * 100)} onChange={e => setD({ value: +e.target.value / 100 })} />
            </Field>
          )}
        </div>
        <p className="muted mt-3">“{describe(draft)}”</p>
        <Button className="mt-3" variant="secondary" icon="Add01Icon" onClick={add}>Add this view</Button>
      </div>

      {views.length > 0 && (
        <div className="card">
          <SectionTitle title="Your views" right={<Button icon="Analytics01Icon" onClick={run} disabled={busy}>{busy ? 'Reweighting…' : 'Run the stress test'}</Button>} />
          <ul className="plain-list">
            {views.map(v => (
              <li key={v.id} className="row row--between"><span>{describe(v)}</span><Button variant="text" size="sm" onClick={() => remove(v.id)}>Remove</Button></li>
            ))}
          </ul>
          <div className="mt-4"><ErrorNotice error={error} onRetry={run} /></div>
        </div>
      )}

      {res && (
        <div className="card stack">
          <p className="takeaway">{res.summary}</p>
          {res.collapsed && <Notice tone="attention" title="Too few scenarios left to trust.">Your views disagree with history so strongly that the result rests on a handful of past months.</Notice>}
          <div className="stat-row">
            <Stat label="Scenarios still counting" value={`${Math.round(res.effective_scenarios)} of ${res.n_scenarios}`} note="Effective number after reweighting" />
            <Stat label="History given up" value={fmtPct(res.confidence_cost)} note="The cost of your views" />
            <Stat label="Tail loss before" value={fmtPct(res.cvar_before, 1)} note="Average of the worst 5% of months" />
            <Stat label="Tail loss after" value={fmtPct(res.cvar_after, 1)} note="With your views applied" />
          </div>
          <div className="tscroll">
            <table>
              <thead><tr><th>View</th><th className="r">Asked</th><th className="r">Delivered</th><th>Status</th></tr></thead>
              <tbody>
                {res.views.map(v => (
                  <tr key={v.label}>
                    <td>{v.label}</td>
                    <td className="r">{v.target.toFixed(3)}</td>
                    <td className="r">{v.achieved.toFixed(3)}</td>
                    <td>{!v.satisfied ? <Badge tone="loss">Not met</Badge> : v.binding ? <Badge tone="proposed">Changed the weights</Badge> : <Badge>Already true in history</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3 style={{ fontSize: 16 }}>Allocation with these views</h3>
          <AllocationBars rows={res.weights} />
          <p className="tiny subtle">Expected monthly return, before → after your views: {res.prior_mu.map(m => `${m.symbol} ${fmtSPct(m.prior)} → ${fmtSPct(m.posterior)}`).join(' · ')}</p>
        </div>
      )}
    </div>
  );
}
