/*
 * Investment theses — a working collection of editable beliefs.
 *
 * Left (main):  the list of theses · live allocation · plain-English compiler
 * Right (panel): the selected thesis, edited as a sentence, plus its effect
 *               on the portfolio (with vs. without this one thesis).
 *
 * This is Hone's signature interaction: change a belief and watch the
 * model-proposed allocation respond. Every edit re-runs the optimizer
 * (debounced; it takes ~30 ms on the server) and the result is saved, so
 * the Portfolio page always reflects the latest inputs.
 *
 * Tabs: "Price targets" (default) and "More view types" (?tab=more).
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useProduct } from '../../../App.jsx';
import { api, quote } from '../../../lib/api.js';
import { makeThesis, portfolioSignature, usableThesis, useDebounced, useLatestRequest, useRisk, useWorkspace, validThesis } from '../../../lib/store.jsx';
import { buildOptimizeBody } from '../../../lib/hooks.js';
import { appPath } from '../../../lib/products.js';
import { fmtHorizon, fmtPct, fmtPrice, fmtPts, fmtSPct, impliedChange } from '../../../lib/format.js';
import AllocationBars from '../../../components/AllocationBars.jsx';
import { Badge, Button, ErrorNotice, Notice, PageHeader, SectionTitle, Segmented, Spinner } from '../../../components/ui.jsx';
import ThesisEditor from './ThesisEditor.jsx';
import Compiler from './Compiler.jsx';
import FlexibleViews from './FlexibleViews.jsx';
import { findConflicts } from './assets.js';

export default function ThesesPage() {
  const product = useProduct();
  const slug = product.slug;
  const { ws, update, updateThesis, market, saveResult, journal, runtime, setRuntime } = useWorkspace(slug);
  const { gamma, isSample } = useRisk();
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') === 'more' ? 'more' : 'targets';
  const [filter, setFilter] = useState('all');
  const [selectedId, setSelectedId] = useState(() => ws.theses[0]?.id ?? null);
  const selected = ws.theses.find(t => t.id === selectedId) ?? ws.theses[0] ?? null;
  const panelRef = useRef(null);
  /** Select a thesis; on narrow screens the editor sits below the list, so bring it into view. */
  const select = id => {
    setSelectedId(id);
    if (window.matchMedia('(max-width: 1040px)').matches) {
      requestAnimationFrame(() => panelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
    }
  };

  /* Tradeable universe for the asset picker (fetched once if no quote has run yet). */
  const universe = runtime[`${slug}:universe`] || [];
  useEffect(() => {
    if (universe.length || !product.example) return;
    quote(product.assetClass, product.example.ticker, market).then(q => setRuntime(`${slug}:universe`, q.universe)).catch(() => {});
  }, [universe.length, product, market, slug, setRuntime]);

  /* ---------------------------------------------------------------- live allocation */
  const sig = portfolioSignature(gamma, ws);
  const debouncedSig = useDebounced(sig, 280);
  const latest = useLatestRequest();
  const [live, setLive] = useState({ busy: false, error: null });
  const [retry, setRetry] = useState(0); // bumped by the Retry button
  const saved = ws.results.optimize;

  useEffect(() => {
    if (saved?.sig === debouncedSig && !retry) return; // already up to date
    setLive({ busy: true, error: null });
    latest(signal =>
      api(product.assetClass, '/api/optimize', buildOptimizeBody(gamma, ws, market), { signal })
        .then(data => { saveResult('optimize', data, debouncedSig); setLive({ busy: false, error: null }); })
        .catch(e => { if (e.name !== 'AbortError') setLive({ busy: false, error: e }); }),
    );
    // Only the debounced signature (or an explicit retry) should trigger a run.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSig, retry]);

  /* ---------------------------------------------------------------- with vs without */
  // Re-run the optimizer leaving the selected thesis out, to show its own effect.
  const [without, setWithout] = useState(null);
  const latestWithout = useLatestRequest();
  const selKey = selected && usableThesis(selected) ? `${debouncedSig}|${selected.id}` : null;
  useEffect(() => {
    if (!selKey) { setWithout(null); return; }
    const wsWithout = { ...ws, theses: ws.theses.filter(t => t.id !== selected.id) };
    latestWithout(signal =>
      api(product.assetClass, '/api/optimize', buildOptimizeBody(gamma, wsWithout, market), { signal })
        .then(setWithout)
        .catch(() => {}),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selKey]);

  /* ---------------------------------------------------------------- list ops */
  const add = (list = [makeThesis({ ticker: '', horizonDays: 365 })]) => {
    update(cur => ({ ...cur, theses: [...cur.theses, ...list] }));
    select(list[list.length - 1].id);
    if (tab !== 'targets') setParams({});
  };
  const duplicate = t => add([makeThesis({ ...t, id: undefined, sample: false, createdAt: new Date().toISOString() })]);
  const remove = id => {
    update(cur => ({ ...cur, theses: cur.theses.filter(t => t.id !== id) }));
    setSelectedId(ws.theses.find(t => t.id !== id)?.id ?? null);
  };

  const conflicts = useMemo(() => findConflicts(ws.theses), [ws.theses]);
  const shown = ws.theses.filter(t => (filter === 'all' ? true : filter === 'included' ? t.included : !t.included));
  const result = saved?.data;
  const selWeight = (r, sym) => r?.weights?.find(w => w.symbol === sym);

  return (
    <>
      <PageHeader
        eyebrow="Your views"
        title="Investment theses"
        lede={`Where you think a ${product.assetSingular} is going, by when, and how sure you are. The allocation updates as you edit.`}
        actions={<Button icon="Add01Icon" onClick={() => add()}>Add thesis</Button>}
      />

      <div className="tabs mb-5" role="tablist">
        <button type="button" role="tab" className="tab" aria-selected={tab === 'targets'} onClick={() => setParams({})}>Price targets</button>
        <button type="button" role="tab" className="tab" aria-selected={tab === 'more'} onClick={() => setParams({ tab: 'more' })}>More view types</button>
      </div>

      {tab === 'more' && (
        <FlexibleViews product={product} market={market} gamma={gamma} ws={ws} update={update} universe={universe} />
      )}

      {tab === 'targets' && (
        <div className="ws-cols">
          {/* ------------------------------------------------ main column */}
          <div className="stack-lg">
            <div className="card">
              <SectionTitle
                title={`${ws.theses.length} ${ws.theses.length === 1 ? 'thesis' : 'theses'}`}
                right={<Segmented label="Filter" value={filter} onChange={setFilter} options={[{ value: 'all', label: 'All' }, { value: 'included', label: 'Included' }, { value: 'excluded', label: 'Excluded' }]} />}
              />
              {Object.entries(conflicts).map(([tk, kind]) => (
                <Notice key={tk} tone="attention" className="mb-3" title={kind === 'conflict' ? `Conflicting views on ${tk}.` : `Overlapping views on ${tk}.`}>
                  {kind === 'conflict' ? 'One says up, another says down. The model blends them, which is rarely what you mean — exclude one.' : 'Two views on the same asset count it twice. Consider keeping one.'}
                </Notice>
              ))}
              {shown.length === 0 && (
                <div className="center" style={{ padding: '24px 0' }}>
                  <p className="muted">No theses {filter !== 'all' ? `marked ${filter}` : 'yet'}.</p>
                  <Button className="mt-3" variant="secondary" icon="Add01Icon" onClick={() => add()}>Add a thesis</Button>
                </div>
              )}
              {shown.length > 0 && (
                <div className="thesis-list" role="list">
                  <div className="thesis-row__head" aria-hidden="true"><span>Asset</span><span>Thesis</span><span>Horizon</span><span>Confidence</span><span>Status</span></div>
                  {shown.map(t => {
                    const chg = impliedChange(t.refPrice, t.target);
                    const status = !t.included ? 'Excluded' : !t.target ? 'Needs target' : t.tradeable === false ? 'No data' : 'Included';
                    return (
                      <button key={t.id} type="button" role="listitem" className="thesis-row" aria-current={selected?.id === t.id} data-excluded={!t.included} onClick={() => select(t.id)}>
                        <span className="thesis-row__sym">{t.ticker || '—'}</span>
                        <span>
                          {t.target ? <>to {fmtPrice(t.target)} {chg != null && <span className="subtle">({fmtSPct(chg)})</span>}</> : <span className="subtle">Set a target</span>}
                          {t.sample && <> <Badge tone="sample">Sample</Badge></>}
                          {conflicts[t.ticker] && t.included && <> <Badge tone="stale">{conflicts[t.ticker]}</Badge></>}
                        </span>
                        <span className="small">{fmtHorizon(t.horizonDays)}</span>
                        <span className="small">{fmtPct(t.confidence)}</span>
                        <span>{status === 'Included' ? <Badge tone="proposed">Included</Badge> : status === 'Excluded' ? <Badge>Excluded</Badge> : <Badge tone="stale">{status}</Badge>}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="card">
              <SectionTitle
                title="Live allocation"
                sub={`Current vs. model-proposed, at ${isSample ? 'a sample' : 'your'} risk level. Updates as you edit.`}
                right={live.busy ? <Spinner>Updating…</Spinner> : <Button variant="text" to={appPath(slug, 'portfolio')} iconRight="ArrowRight01Icon">Why each change</Button>}
              />
              <ErrorNotice error={live.error} onRetry={() => setRetry(n => n + 1)} settingsTo={appPath(slug, 'settings')} />
              {result && <div style={{ opacity: live.busy ? 0.6 : 1, transition: 'opacity 150ms' }}><AllocationBars rows={result.weights} highlight={selected?.ticker} /></div>}
              {result?.confidence_adjustments?.length > 0 && (
                <p className="tiny subtle mt-3">Confidence rescaled from your track record: {result.confidence_adjustments.map(a => `${a.ticker} ${fmtPct(a.stated)} → ${fmtPct(a.used)}`).join(' · ')}</p>
              )}
            </div>

            <Compiler product={product} market={market} journal={journal} onAdd={list => add(list)} />
          </div>

          {/* ------------------------------------------------ right panel */}
          <div className="ws-panel" ref={panelRef} style={{ scrollMarginTop: 16 }}>
            {selected ? (
              <ThesisEditor
                key={selected.id}
                thesis={selected}
                product={product}
                universe={universe}
                onChange={patch => updateThesis(selected.id, patch)}
                onDuplicate={() => duplicate(selected)}
                onDelete={() => remove(selected.id)}
              >
                <EffectOnPortfolio thesis={selected} withRes={result} withoutRes={without} weightOf={selWeight} />
              </ThesisEditor>
            ) : (
              <div className="card center muted">Select a thesis to edit it, or add one.</div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

/* The selected thesis's own effect: its asset's proposed weight with and without it. */
function EffectOnPortfolio({ thesis, withRes, withoutRes, weightOf }) {
  if (!thesis.included) return <Notice>Excluded theses are kept but not sent to the model. Switch it on to see its effect.</Notice>;
  if (!validThesis(thesis)) return <Notice tone="attention">Add a price target to see this thesis’s effect.</Notice>;
  const w = weightOf(withRes, thesis.ticker);
  const wo = weightOf(withoutRes, thesis.ticker);
  if (!w || !wo) return <Spinner>Measuring this thesis’s effect…</Spinner>;
  const others = withRes.weights
    .map(x => ({ sym: x.symbol, d: x.target - (weightOf(withoutRes, x.symbol)?.target ?? 0) }))
    .filter(x => x.sym !== thesis.ticker && Math.abs(x.d) >= 0.005)
    .sort((a, b) => Math.abs(b.d) - Math.abs(a.d))
    .slice(0, 3);
  return (
    <div className="card card--sunk" style={{ padding: 14 }}>
      <div className="eyebrow mb-2">Effect on the portfolio</div>
      <p className="small">
        Proposed {thesis.ticker}: <b>{fmtPct(wo.target)}</b> without this thesis → <b>{fmtPct(w.target)}</b> with it ({fmtPts(w.target - wo.target)}).
      </p>
      {others.length > 0 && <p className="tiny subtle mt-1">Knock-on: {others.map(o => `${o.sym} ${fmtPts(o.d)}`).join(' · ')}</p>}
      {w.reason && <p className="tiny mt-2" style={{ color: 'var(--ink-2)' }}>{w.reason}</p>}
      <Link className="tiny" to="../portfolio" relative="path">See the full explanation</Link>
    </div>
  );
}
