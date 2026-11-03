/*
 * Compiler — "say it in plain English". Sends the text to the conviction
 * compiler (/api/compile-view), which returns structured, editable theses.
 * Fields the compiler guessed rather than read are flagged for review, and
 * nothing reaches the model until it's added to the list.
 *
 * The journal rides along: once enough predictions have resolved, they
 * personalise how the compiler reads your language ("tuned to your last N").
 */
import { useState } from 'react';
import { api } from '../../../lib/api.js';
import { makeThesis } from '../../../lib/store.jsx';
import { fmtHorizon, fmtPct, fmtPrice } from '../../../lib/format.js';
import { Badge, Button, ErrorNotice, Notice, SectionTitle } from '../../../components/ui.jsx';

export default function Compiler({ product, market, journal, onAdd }) {
  const [text, setText] = useState('');
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const compile = async () => {
    if (!text.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setRes(await api(product.assetClass, '/api/compile-view', { ...market, text, predictions: journal }));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  /** Compiled view -> a thesis in the list. */
  const toThesis = v =>
    makeThesis({
      ticker: v.ticker,
      target: v.target_price ?? null,
      confidence: v.confidence_pct != null ? v.confidence_pct / 100 : 0.5,
      horizonDays: v.horizon_days ?? 365,
      rationale: v.thesis || text,
      refPrice: v.live_price ?? v.entry_price ?? null,
      refAt: v.live_price ? new Date().toISOString() : null,
      tradeable: v.tradeable !== false,
    });

  return (
    <div className="card">
      <SectionTitle
        title="Write it in plain English"
        sub="Describe what you believe. Hone turns it into theses you can check and edit."
        right={res && <span className="tiny subtle">{res.engine === 'claude' ? 'compiled by Claude' : 'compiled locally'}{res.personalized_from ? ` · tuned to your last ${res.personalized_from} predictions` : ''}</span>}
      />
      <textarea
        aria-label="Your thesis in plain English"
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder={product.examplePhrase}
        onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) compile(); }}
      />
      <div className="row mt-3">
        <Button icon="SparklesIcon" onClick={compile} disabled={busy || !text.trim()}>{busy ? 'Reading your thesis…' : 'Turn into theses'}</Button>
        <span className="tiny subtle">Ctrl/⌘ + Enter</span>
      </div>
      <div className="mt-4"><ErrorNotice error={error} onRetry={compile} /></div>

      {res && (
        <div className="stack mt-4">
          {res.notes?.map(n => <Notice key={n}>{n}</Notice>)}
          {res.views.length === 0 && <Notice>Nothing to compile — name a {product.assetSingular} and where you think it goes.</Notice>}
          {res.views.map((v, i) => (
            <div key={i} className="card card--sunk" style={{ padding: 14 }}>
              <div className="row row--between">
                <div>
                  <b>{v.ticker}</b>{' '}
                  {v.target_price ? <>to {fmtPrice(v.target_price)}</> : <span className="subtle">no target found</span>}
                  {' · '}{fmtHorizon(v.horizon_days)}{' · '}{v.confidence_pct != null ? fmtPct(v.confidence_pct / 100) : '—'} confidence
                </div>
                <Button size="sm" variant="secondary" icon="Add01Icon" onClick={() => onAdd([toThesis(v)])}>Add</Button>
              </div>
              <div className="row mt-2" style={{ gap: 6 }}>
                {v.needs_review?.map(f => <Badge key={f} tone="stale">Check {f.replace('_pct', '').replace('_days', '').replace('_', ' ')}</Badge>)}
                {v.tradeable === false && <Badge tone="loss">No price history</Badge>}
              </div>
              {v.warnings?.map(w => <p key={w} className="tiny mt-2" style={{ color: 'var(--attention)' }}>{w}</p>)}
            </div>
          ))}
          {res.views.length > 1 && <Button variant="text" onClick={() => onAdd(res.views.map(toThesis))}>Add all {res.views.length}</Button>}
        </div>
      )}
    </div>
  );
}
