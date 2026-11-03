/*
 * Portfolio — designed around one decision:
 *   What do I hold now? What does the model propose? What caused each
 *   difference? Which assumption should I inspect next?
 *
 * Sections
 *   1. Preferences (position limit, track-record adjustment) + Recalculate
 *   2. Summary row — four clearly defined numbers
 *   3. Current vs. model-proposed bars
 *   4. Proposed changes — one expandable row per asset, plain English first,
 *      technical detail underneath
 *   5. Sensitivity — how much the result moves under nearby assumptions
 *   6. Commit — log these views to the decision journal (React Bits SlideCommit)
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import SlideCommit from '../../reactbits/SlideCommit/SlideCommit.jsx';
import AllocationBars from '../../components/AllocationBars.jsx';
import { Badge, Button, ErrorNotice, Expander, Field, Notice, NumberSlider, PageHeader, SectionTitle, SkeletonRows, StaleBanner, Stat } from '../../components/ui.jsx';
import { api } from '../../lib/api.js';
import { Auth } from '../../lib/auth.js';
import { buildOptimizeBody, useOptimize } from '../../lib/hooks.js';
import { appPath, docPath } from '../../lib/products.js';
import { newId, useRisk, useWorkspace } from '../../lib/store.jsx';
import { fmtAgo, fmtMoney, fmtPct, fmtPrice, fmtPts, fmtSMoney, fmtSPct } from '../../lib/format.js';

export default function PortfolioPage() {
  const product = useProduct();
  const slug = product.slug;
  const { ws, update, market, setJournal } = useWorkspace(slug);
  const risk = useRisk();
  const opt = useOptimize(slug, { auto: true });
  const r = opt.result;
  const value = r?.hedge_plan?.portfolio_value ?? null;
  const thesisFor = sym => ws.theses.find(t => t.included && t.ticker === sym);
  const returnsFor = sym => r?.returns?.find(x => x.symbol === sym);

  /*
   * Decision journal: the decision is made, so log each view at the
   * SERVER's price (not a browser guess) with the STATED confidence (not
   * the calibrated one — scoring the adjusted number would feed calibration
   * its own output). This is `journalRecord(optimize.views)` from v1.
   */
  const journalRecord = views => {
    const now = new Date().toISOString();
    const entries = views.map(v => ({
      id: newId(),
      ticker: v.ticker,
      direction: v.target_price >= v.current_price ? 'bullish' : 'bearish',
      entry_price: v.current_price,
      target_price: v.target_price,
      confidence: v.stated_confidence ?? v.confidence,
      horizon_days: v.horizon_days,
      thesis: ws.theses.find(t => t.ticker === v.ticker)?.rationale || v.description,
      created_at: now,
    }));
    setJournal(prev => [...prev, ...entries]);
    return entries.length;
  };

  return (
    <>
      <PageHeader
        eyebrow="Model-proposed allocation"
        title="Portfolio"
        lede="Your current holdings next to what the model proposes, with the reason for every change. A proposal depends on this model and these inputs — it is not a recommendation."
        actions={<Button icon="RefreshIcon" onClick={opt.run} disabled={opt.busy}>{opt.busy ? 'Calculating…' : 'Recalculate allocation'}</Button>}
        meta={<span className="tiny subtle">{opt.at ? `Calculated ${fmtAgo(opt.at)}` : 'Not calculated yet'} · {ws.dataSource === 'alpaca' ? 'Alpaca paper data' : 'Sample prices and holdings'}</span>}
      />

      {/* 1. Preferences */}
      <div className="card mb-5">
        <div className="grid-3" style={{ alignItems: 'start' }}>
          <Field label="Largest single position" hint="The model may not propose more than this in any one asset.">
            <NumberSlider value={ws.maxWeight} onChange={v => update({ maxWeight: v })} min={0.05} max={1} step={1} scale={100} suffix="%" ariaLabel="Maximum position size" />
          </Field>
          <Field label="Risk aversion used" hint={risk.isSample ? 'A sample value until you assess yours.' : 'From your risk profile.'}>
            <div className="row" style={{ minHeight: 44 }}>
              {risk.isSample ? <Badge tone="sample">Sample · {risk.gamma.toFixed(1)}</Badge> : <Badge tone="yours">{risk.profile.tier?.category ?? 'Yours'} · {risk.gamma.toFixed(1)}</Badge>}
              <Link className="small" to={appPath(slug, 'risk')}>{risk.isSample ? 'Assess mine' : 'Change'}</Link>
            </div>
          </Field>
          <Field label="Adjust confidence from my track record" hint={ws.calibration?.actionable ? `Your record has ${ws.calibration.n} scored predictions — enough to rescale stated confidence.` : 'Available once enough journal predictions have resolved.'}>
            <label className="row" style={{ minHeight: 44 }}>
              <input type="checkbox" checked={!!ws.calibration?.actionable && ws.useCalibration !== false} disabled={!ws.calibration?.actionable} onChange={e => update({ useCalibration: e.target.checked })} style={{ width: 20, height: 20, accentColor: 'var(--primary)' }} />
              <span className="small">{ws.calibration?.actionable ? (ws.useCalibration !== false ? 'On' : 'Off') : 'Not enough history yet'}</span>
            </label>
          </Field>
        </div>
        <p className="tiny subtle mt-3">Held fixed: nothing — every position may change. Minimum cash: none; to hold more cash, see <Link to={appPath(slug, 'hedging')}>Hedging</Link>.</p>
      </div>

      {opt.stale && <div className="mb-4"><StaleBanner onRecalc={opt.run} busy={opt.busy} what="this allocation" /></div>}
      <div className="mb-4"><ErrorNotice error={opt.error} onRetry={opt.run} settingsTo={appPath(slug, 'settings')} /></div>
      {!r && opt.busy && <div className="card"><SkeletonRows rows={6} /></div>}

      {r && (
        <div className="stack-lg">
          {/* Honest warnings first. */}
          {r.hedge_plan?.premium_is_negative && (
            <Notice tone="attention" title="This proposal has a negative expected return.">
              With these views, the best available mix is still expected to lose money — the model is choosing the least bad option, not a good one.
              Executing a plan you expect to lose rarely makes sense; revisit your views or hold cash instead.
            </Notice>
          )}
          {r.confidence_adjustments?.length > 0 && (
            <Notice tone="info" title="Confidence rescaled from your track record.">
              {r.confidence_adjustments.map(a => `${a.ticker}: you said ${fmtPct(a.stated)}, the model used ${fmtPct(a.used)}`).join(' · ')}.{' '}
              <Link to={appPath(slug, 'record')}>Why</Link>
            </Notice>
          )}

          {/* 2. Summary */}
          <div className="card">
            <div className="stat-row">
              <Stat label="Portfolio value" value={value ? fmtMoney(value) : '—'} note={r.demo ? 'Sample portfolio' : 'Paper account equity'} />
              <Stat label="Expected return (model)" value={fmtSPct(r.expected_return)} note={value ? `${fmtSMoney(r.expected_return * value)} a year` : 'per year'} />
              <Stat label="Volatility" value={fmtPct(r.volatility)} note="Typical yearly swing, one standard deviation" />
              <Stat label="Largest proposed position" value={(() => { const top = [...r.weights].sort((a, b) => b.target - a.target)[0]; return `${top.symbol} ${fmtPct(top.target)}`; })()} note={`Limit ${fmtPct(ws.maxWeight)}`} />
            </div>
          </div>

          {/* 3. Bars */}
          <div className="card">
            <SectionTitle title="Current vs. model-proposed" sub="Share of the portfolio in each asset." />
            <AllocationBars rows={r.weights} />
          </div>

          {/* 4. Changes */}
          <div className="card">
            <SectionTitle title="Proposed changes" sub="Open a row for the reason, the money involved, and the technical detail." />
            <div className="change-head tiny subtle" style={{ padding: '0 0 8px 28px' }} aria-hidden="true"><span>Asset</span><span>Main driver</span><span style={{ textAlign: 'right' }}>Change</span><span className="change-head__usd" style={{ textAlign: 'right' }}>Dollars</span></div>
            {r.weights.map(w => {
              const th = thesisFor(w.symbol);
              const ret = returnsFor(w.symbol);
              const atLimit = w.target >= ws.maxWeight - 0.0015;
              const zero = w.target < 0.0005;
              const driver = th ? `Your thesis: ${th.ticker} to ${fmtPrice(th.target)}` : atLimit ? 'Position limit' : zero ? 'Risk not paid for' : 'Risk balance';
              return (
                <Expander
                  key={w.symbol}
                  summary={
                    <div className="change-head">
                      <span className="change-head__sym">{w.symbol}</span>
                      <span className="driver">{driver}</span>
                      <span className="change-head__delta">{fmtPct(w.current)} → {fmtPct(w.target)}</span>
                      <span className="change-head__usd">{value ? fmtSMoney(w.trade * value) : fmtPts(w.trade)}</span>
                    </div>
                  }
                >
                  <p style={{ color: 'var(--ink)' }}>{w.reason || 'Weight set by the balance of expected return and risk at your risk level.'}</p>
                  <div className="row mt-3" style={{ gap: 8 }}>
                    {atLimit && <Badge tone="stale">At your {fmtPct(ws.maxWeight)} limit — the limit, not the model, set this size</Badge>}
                    {w.target >= 0.3 && <Badge tone="stale">Concentrated: {fmtPct(w.target)} in one asset</Badge>}
                    {zero && <Badge>No allocation — conditional on this model and these inputs</Badge>}
                    {th && <Badge tone="yours">Driven by your thesis</Badge>}
                  </div>
                  <dl className="kv mt-3">
                    <dt>Weight</dt><dd>{fmtPct(w.current, 1)} now → {fmtPct(w.target, 1)} proposed ({fmtPts(w.trade, 1)})</dd>
                    {value && <><dt>Dollars</dt><dd>{fmtMoney(w.current * value)} → {fmtMoney(w.target * value)} ({fmtSMoney(w.trade * value)})</dd></>}
                    {ret && <><dt>Expected return</dt><dd>{fmtSPct(ret.prior)} market-implied → {fmtSPct(ret.posterior)} after your views ({fmtSPct(ret.tilt)} tilt)</dd></>}
                    {th && <><dt>Thesis</dt><dd>{fmtPrice(th.target)} in {Math.round(th.horizonDays)} days at {fmtPct(th.confidence)} confidence · <Link to={appPath(slug, 'theses')}>edit</Link></dd></>}
                  </dl>
                </Expander>
              );
            })}
            <p className="tiny subtle mt-3">
              Expected returns blend market-implied returns with your views (Black–Litterman), then weights maximise return minus a risk penalty set by your risk aversion.{' '}
              <Link to={docPath(slug, 'methodology')}>Methodology</Link>
            </p>
          </div>

          {/* 5. Sensitivity */}
          <Sensitivity product={product} ws={ws} market={market} gamma={risk.gamma} base={r} />

          {/* 6. Commit to the journal */}
          {r.views?.length > 0 && (
            <div className="card">
              <SectionTitle title="Commit these views to your journal" sub="Logs each view at today’s price so it can be scored when its horizon ends. That score is what calibrates your confidence later." />
              <div className="row" style={{ gap: 20 }}>
                <SlideCommit
                  label={`Slide to log ${r.views.length} view${r.views.length === 1 ? '' : 's'}`}
                  doneLabel="Logged"
                  errorLabel="Couldn’t log"
                  onConfirm={() => journalRecord(r.views)}
                  trackColor="#20251f"
                  handleColor="#faf8ee"
                  successColor="#174e43"
                  dangerColor="#b42318"
                  width={300}
                  height={52}
                  radius={26}
                />
                <span className="tiny subtle">Paper only — nothing is traded. Keyboard: focus the handle and press End. <Link to={appPath(slug, 'record')}>Open track record</Link></span>
              </div>
            </div>
          )}

          {Auth.enabled && <SaveToAccount ws={ws} gamma={risk.gamma} result={r} product={product} />}
        </div>
      )}
    </>
  );
}

/* ------------------------------------------------------------------ sensitivity */
/*
 * Re-runs the optimizer with each thesis nudged (confidence ±20 points,
 * target ±10%) and reports the proposed weight of that asset each time.
 * A result that swings wildly under small nudges deserves less trust.
 */
function Sensitivity({ product, ws, market, gamma, base }) {
  const [rows, setRows] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const theses = ws.theses.filter(t => base.views?.some(v => v.ticker === t.ticker) && t.included);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const weightOf = (res, sym) => res.weights.find(w => w.symbol === sym)?.target ?? 0;
      const nudge = async (id, patch) => {
        const w2 = { ...ws, theses: ws.theses.map(t => (t.id === id ? { ...t, ...patch } : t)) };
        return api(product.assetClass, '/api/optimize', buildOptimizeBody(gamma, w2, market));
      };
      const out = [];
      for (const t of theses) {
        const [cLo, cHi, tLo, tHi] = await Promise.all([
          nudge(t.id, { confidence: Math.max(0.01, t.confidence - 0.2) }),
          nudge(t.id, { confidence: Math.min(0.99, t.confidence + 0.2) }),
          nudge(t.id, { target: t.target * 0.9 }),
          nudge(t.id, { target: t.target * 1.1 }),
        ]);
        out.push({ t, base: weightOf(base, t.ticker), cLo: weightOf(cLo, t.ticker), cHi: weightOf(cHi, t.ticker), tLo: weightOf(tLo, t.ticker), tHi: weightOf(tHi, t.ticker) });
      }
      setRows(out);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  if (!theses.length) return null;
  return (
    <div className="card">
      <SectionTitle
        title="How fragile is this?"
        sub="The proposed weight of each thesis’s asset under nearby assumptions."
        right={<Button variant="secondary" size="sm" icon="Analytics01Icon" onClick={run} disabled={busy}>{busy ? 'Testing…' : rows ? 'Re-test' : 'Test nearby assumptions'}</Button>}
      />
      <ErrorNotice error={error} onRetry={run} />
      {rows && (
        <>
          <div className="tscroll">
            <table>
              <thead><tr><th>Asset</th><th className="r">Confidence −20 pts</th><th className="r">As entered</th><th className="r">Confidence +20 pts</th><th className="r">Target −10%</th><th className="r">Target +10%</th></tr></thead>
              <tbody>
                {rows.map(x => (
                  <tr key={x.t.id}>
                    <td><b>{x.t.ticker}</b></td>
                    <td className="r">{fmtPct(x.cLo)}</td>
                    <td className="r"><b>{fmtPct(x.base)}</b></td>
                    <td className="r">{fmtPct(x.cHi)}</td>
                    <td className="r">{fmtPct(x.tLo)}</td>
                    <td className="r">{fmtPct(x.tHi)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="tiny subtle mt-3">The model’s arithmetic is precise; your inputs are not. If a small change to a guess moves the weight a lot, treat that weight as a rough range.</p>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ account save */
function SaveToAccount({ ws, gamma, result, product }) {
  const [name, setName] = useState('');
  const [msg, setMsg] = useState(null);
  if (!Auth.user()) {
    return <Notice>Want this on another device? <Link to={appPath(product.slug, 'settings')}>Sign in</Link> to save portfolios to your account.</Notice>;
  }
  const save = async () => {
    try {
      await Auth.savePortfolio(name || `${product.name} · ${new Date().toLocaleDateString()}`, {
        product: product.slug, gamma, theses: ws.theses, maxWeight: ws.maxWeight, weights: result.weights,
      });
      setMsg({ ok: true, text: 'Saved to your account.' });
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    }
  };
  return (
    <div className="card">
      <SectionTitle title="Save to my account" sub="Stores your risk level, theses and this proposal so you can reload them anywhere." />
      <div className="row" style={{ flexWrap: 'nowrap' }}>
        <input type="text" aria-label="Name" placeholder="Name this portfolio" value={name} onChange={e => setName(e.target.value)} />
        <Button onClick={save}>Save</Button>
      </div>
      {msg && <p className={`tiny mt-2 ${msg.ok ? '' : 'loss'}`}>{msg.text}</p>}
    </div>
  );
}
