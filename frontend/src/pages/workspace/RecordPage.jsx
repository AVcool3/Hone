/*
 * Track record — the decision journal and confidence calibration.
 *
 * Every view you commit (Portfolio → "Slide to log") is stored on this
 * device with the server's price at that moment. /api/journal scores the
 * ones whose horizon has passed and fits a calibration map: does your 70%
 * actually come true 70% of the time? Once there are enough scored
 * predictions, that map rescales the confidence you type before the model
 * uses it (toggle on the Portfolio page).
 *
 * In sample mode with an empty journal, the server synthesises an example
 * history so the page shows what it is for. That history is labelled and
 * never used to adjust anything.
 */
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import { api } from '../../lib/api.js';
import { useWorkspace } from '../../lib/store.jsx';
import { appPath, docPath } from '../../lib/products.js';
import { fmtDate, fmtPct, fmtPrice, fmtSPct } from '../../lib/format.js';
import { Badge, Button, ErrorNotice, Notice, PageHeader, SectionTitle, SkeletonRows, Stat } from '../../components/ui.jsx';

/** Save a text file in the browser (used for the JSONL training export). */
function downloadText(filename, text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/x-ndjson' }));
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function RecordPage() {
  const product = useProduct();
  const slug = product.slug;
  const { ws, update, market, journal, setJournal } = useWorkspace(slug);
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      // Prediction markets has no price history of its own: score against the stocks universe.
      const assetClass = slug === 'prediction-markets' ? 'equities' : product.assetClass;
      const r = await api(assetClass, '/api/journal', {
        ...market,
        predictions: journal,
        seed_demo_history: journal.length === 0 && market.demo !== false,
      });
      setRes(r);
      // Only a real record may calibrate you — never the seeded example.
      if (!r.seeded) {
        const c = r.calibration;
        update({ calibration: { intercept: c.intercept, slope: c.slope, actionable: c.actionable, n: c.n } });
      }
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, JSON.stringify(journal), market]);

  useEffect(() => { load(); }, [load]);

  const c = res?.calibration;
  const removeEntry = id => setJournal(prev => prev.filter(p => p.id !== id));
  const clearAll = () => {
    if (!window.confirm('Delete every logged prediction? This cannot be undone.')) return;
    setJournal([]);
    update({ calibration: null });
  };

  return (
    <>
      <PageHeader
        eyebrow="Decision journal"
        title="Track record"
        lede="Your past views, scored against what actually happened. It’s the only honest check on the confidence numbers you type."
        actions={<Button variant="secondary" icon="Book02Icon" to={docPath(slug, 'methodology', 'calibration')}>How scoring works</Button>}
        meta={res?.seeded ? <Badge tone="sample">Example history — your journal is empty</Badge> : <Badge tone="yours">{journal.length} logged on this device</Badge>}
      />
      <ErrorNotice error={error} onRetry={load} settingsTo={appPath(slug, 'settings')} />
      {!res && busy && <div className="card"><SkeletonRows rows={6} /></div>}

      {res && (
        <div className="stack-lg">
          {res.seeded && (
            <Notice tone="attention" title="This is an example record, not yours.">
              Commit views from the <Link to={appPath(slug, 'portfolio')}>Portfolio</Link> page and they’ll appear here; they’re scored when their horizon ends. The example never adjusts your confidence.
            </Notice>
          )}

          <div className="card">
            {c?.n > 0 && <p className="takeaway">{c.summary}</p>}
            <div className="stat-row">
              <Stat label="Scored predictions" value={c?.n ?? 0} note={`${res.open.length} still open`} />
              <Stat label="Hit their target" value={c?.base_rate != null ? fmtPct(c.base_rate) : '—'} note={c?.mean_confidence != null ? `You averaged ${fmtPct(c.mean_confidence)} confidence` : ''} />
              <Stat label="Right direction" value={c?.direction_hit_rate != null ? fmtPct(c.direction_hit_rate) : '—'} note="Moved the way you said" />
              <Stat label="Brier score" value={c?.brier != null ? c.brier.toFixed(2) : '—'} note="0 is perfect, 0.25 is a coin flip" />
            </div>
          </div>

          {c?.bins?.some(b => b.n > 0) && (
            <div className="card">
              <SectionTitle title="Does 70% mean 70%?" sub="For each band of stated confidence: how often those predictions actually hit. The black tick is what you said." />
              <div className="calib-bins">
                {c.bins.filter(b => b.n > 0).map(b => (
                  <div key={b.lower} className="calib-bin">
                    <span className="small">{fmtPct(b.lower)}–{fmtPct(b.upper)}</span>
                    <div className="calib-bin__track" role="img" aria-label={`Stated about ${fmtPct(b.mean_confidence)}, hit ${fmtPct(b.hit_rate)}`}>
                      <div className="calib-bin__fill" style={{ width: `${b.hit_rate * 100}%` }} />
                      <div className="calib-bin__stated" style={{ left: `${b.mean_confidence * 100}%` }} />
                    </div>
                    <span className="small num">hit {fmtPct(b.hit_rate)} · n={b.n}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {c && (
            <div className="card">
              <SectionTitle title="What your confidence is worth" sub={c.actionable ? 'Your record is long enough to rescale what you type.' : 'Nothing is adjusted until enough predictions resolve — this is a record, not yet a correction.'} />
              <div className="row" style={{ gap: 10 }}>
                {c.examples?.map(e => <Badge key={e.stated} tone={Math.abs(e.used - e.stated) > 0.005 ? 'proposed' : ''}>You say {fmtPct(e.stated)} → model uses {fmtPct(e.used)}</Badge>)}
              </div>
              {c.actionable && !res.seeded && (
                <p className="small mt-3">Applied to new calculations: <b>{ws.useCalibration !== false ? 'on' : 'off'}</b> · <Link to={appPath(slug, 'portfolio')}>change on Portfolio</Link></p>
              )}
            </div>
          )}

          <div className="card">
            <SectionTitle title={`Open (${res.open.length})`} sub="Waiting for their horizon to end." />
            {res.open.length === 0 ? <p className="muted">Nothing open.</p> : (
              <div className="tscroll">
                <table>
                  <thead><tr><th>Asset</th><th>Logged</th><th className="r">Entry → target</th><th className="r">Confidence</th><th className="r">Now</th><th className="r">Days left</th><th /></tr></thead>
                  <tbody>
                    {res.open.map(o => (
                      <tr key={o.prediction.id || o.prediction.created_at + o.prediction.ticker}>
                        <td><b>{o.prediction.ticker}</b></td>
                        <td>{fmtDate(o.prediction.created_at)}</td>
                        <td className="r">{fmtPrice(o.prediction.entry_price)} → {fmtPrice(o.prediction.target_price)}</td>
                        <td className="r">{fmtPct(o.prediction.confidence)}</td>
                        <td className="r">{fmtPrice(o.current_price)}{o.progress != null && <span className="subtle"> · {fmtPct(o.progress)} of the way</span>}</td>
                        <td className="r">{Math.ceil(o.days_remaining)}</td>
                        <td>{!res.seeded && <Button variant="text" size="sm" onClick={() => removeEntry(o.prediction.id)}>Remove</Button>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="card">
            <SectionTitle title={`Scored (${res.resolved.length})`} />
            {res.resolved.length === 0 ? <p className="muted">None yet.</p> : (
              <div className="tscroll">
                <table>
                  <thead><tr><th>Asset</th><th>Logged → resolved</th><th className="r">Entry → target</th><th className="r">Final</th><th className="r">Return</th><th>Target hit?</th><th className="r">Confidence</th></tr></thead>
                  <tbody>
                    {res.resolved.map(x => (
                      <tr key={x.prediction.id || x.prediction.created_at + x.prediction.ticker}>
                        <td><b>{x.prediction.ticker}</b></td>
                        <td className="nowrap">{fmtDate(x.prediction.created_at)} → {fmtDate(x.resolved_at)}</td>
                        <td className="r">{fmtPrice(x.prediction.entry_price)} → {fmtPrice(x.prediction.target_price)}</td>
                        <td className="r">{fmtPrice(x.final_price)}</td>
                        <td className={`r ${x.realized_return < 0 ? 'loss' : ''}`}>{fmtSPct(x.realized_return)}</td>
                        <td>{x.target_hit ? <Badge tone="proposed">Hit</Badge> : x.direction_hit ? <Badge>Right way, short</Badge> : <Badge tone="loss">Missed</Badge>}</td>
                        <td className="r">{fmtPct(x.prediction.confidence)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <TrainingExport product={product} market={market} journal={journal} />

          {journal.length > 0 && (
            <div className="row"><Button variant="text" className="btn--danger" icon="Delete02Icon" onClick={clearAll}>Clear my journal</Button></div>
          )}
        </div>
      )}
    </>
  );
}

/* ------------------------------------------------------------------ export */
function TrainingExport({ product, market, journal }) {
  const [r, setR] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const assetClass = product.slug === 'prediction-markets' ? 'equities' : product.assetClass;
      setR(await api(assetClass, '/api/export/training', { ...market, predictions: journal }));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="card">
      <SectionTitle
        title="Teach a model your habits"
        sub="Your resolved predictions are the only data that could teach a model how you write and what your words turn out to be worth."
        right={<Button variant="secondary" size="sm" icon="Analytics01Icon" onClick={run} disabled={busy}>{busy ? 'Checking…' : 'Check my training data'}</Button>}
      />
      <ErrorNotice error={error} onRetry={run} />
      {r && (
        <div className="stack">
          <p className="takeaway">{r.summary}</p>
          <div className="stat-row">
            <Stat label="Training rows" value={r.n_examples} size="sm" note={`${r.n_compile} compile · ${r.n_calibrate} calibrate`} />
            <Stat label="Resolved predictions" value={r.n_resolved} size="sm" />
            <Stat label="Recommendation" value={{ few_shot: 'Few-shot', marginal: 'Marginal', ready: 'Ready' }[r.recommendation] ?? r.recommendation} size="sm" note="For fine-tuning, not the few-shot path" />
            <Stat label="In use now" value={r.few_shot_active} size="sm" note="Examples in the compiler’s prompt" />
          </div>
          {r.warnings?.map(w => <Notice key={w} tone="attention">{w}</Notice>)}
          {r.notes?.map(n => <Notice key={n}>{n}</Notice>)}
          <div className="row">
            <Button variant="secondary" icon="Download01Icon" disabled={!r.n_examples} onClick={() => downloadText('hone-training.jsonl', r.jsonl)}>Download JSONL ({r.n_examples} rows)</Button>
          </div>
          <p className="tiny subtle">
            The download trains a local open-weights model with <code>training/train_qlora.py</code>. Claude itself can’t be fine-tuned through the API — the
            personalization that reaches Claude is the {r.few_shot_active} examples put in the compiler’s prompt.{' '}
            <Link to={docPath(product.slug, 'methodology', 'qlora')}>Why</Link>
          </p>
        </div>
      )}
    </div>
  );
}
