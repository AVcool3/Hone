/*
 * Price my risk — "I own a ski resort in X" -> a priced, sized hedge.
 *
 * The user gives three things: what they do, where, and their season
 * revenue. The server (hone/prediction/quote.py) does the rest:
 *   1. finds the place and pulls every season's weather since 1980 — snow,
 *      rain, heat or frost depending on the business (perils.py) — from the
 *      best source: a mountain snow station, a NOAA station, or the grid,
 *   2. works out how often a season there is "bad" (below 80% of normal),
 *      adjusting for any long-term trend, with an honest range,
 *   3. estimates what a bad season costs this business,
 *   4. prices protection itself (fair = the probability; provider = + margin),
 *   5. sizes it at the user's risk aversion (same engine as Income hedge),
 *   6. points to the nearest Kalshi market, if any, and how well it fits.
 *
 * Optional inputs (reserves, margin, basis, trigger, provider margin) sit
 * in "More options" with sensible per-business defaults from the server.
 *
 * Layout: <QuoteForm> on top, <QuoteResult> below. The season chart is
 * <SeasonBars>, a small SVG at the bottom of this file.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../../lib/api.js';
import { useRisk, useWorkspace } from '../../../lib/store.jsx';
import { appPath } from '../../../lib/products.js';
import { fmtGamma, fmtMoney, fmtPct } from '../../../lib/format.js';
import { Badge, Button, ErrorNotice, Expander, Field, Notice, PageHeader, Spinner, Stat } from '../../../components/ui.jsx';
import './prediction.css';

const SLUG = 'prediction-markets';

/** Parse "4,000,000" / "4m" / "$250k" into a number (or NaN). */
function parseMoney(text) {
  const t = String(text || '').trim().toLowerCase().replace(/[$,\s]/g, '');
  const m = t.match(/^(\d+(?:\.\d+)?)([km]?)$/);
  if (!m) return NaN;
  return Number(m[1]) * (m[2] === 'm' ? 1e6 : m[2] === 'k' ? 1e3 : 1);
}

export default function QuotePage() {
  const { product, ws, update } = useWorkspace(SLUG);
  const { gamma, isSample } = useRisk();
  // The last quote is kept in the workspace so it survives navigation.
  const saved = ws.quote || {};
  const [form, setForm] = useState({
    business: saved.business || 'ski_resort',
    placeText: saved.placeText || '',
    place: saved.place || null,              // {label, latitude, longitude} once picked
    revenue: saved.revenue || '',
    reserves: saved.reserves || '',
    margin: saved.margin || '',
    basis: saved.basis || '',
    // How far from normal counts as bad, in %: 30 means below 70% of normal
    // for "too little" risks (snow) or above 130% for "too much" ones (rain).
    triggerGap: saved.triggerGap || '30',
    loading: saved.loading || '30',
    passShare: saved.passShare || '',
  });
  const [businesses, setBusinesses] = useState([]);
  const [matches, setMatches] = useState(null);   // place search results
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const result = saved.result || null;

  const set = patch => setForm(f => ({ ...f, ...patch }));

  // Business types and their defaults come from the server, so the page
  // never disagrees with the model about what "ski resort" assumes.
  useEffect(() => {
    api(product.assetClass, '/api/predict/businesses').then(setBusinesses).catch(() => {});
  }, [product.assetClass]);
  const biz = businesses.find(b => b.key === form.business);

  const findPlace = async () => {
    setError(null);
    setMatches(null);
    try {
      const found = await api(product.assetClass, `/api/predict/places?q=${encodeURIComponent(form.placeText)}`);
      setMatches(found);
      if (found.length === 1) set({ place: found[0] });
    } catch (e) {
      setError(e);
    }
  };

  const revenue = parseMoney(form.revenue);
  const canQuote = form.place && revenue > 0 && !busy;

  const getQuote = async () => {
    setBusy(true);
    setError(null);
    // Blank optional fields are left out, so the server's defaults apply.
    const opt = (text, scale = 1) => (String(text).trim() === '' ? undefined : Number(text) * scale);
    const body = {
      business: form.business,
      latitude: form.place.latitude,
      longitude: form.place.longitude,
      place_label: form.place.label,
      revenue,
      reserves: form.reserves ? parseMoney(form.reserves) : undefined,
      margin: opt(form.margin, 0.01),
      basis: opt(form.basis),
      trigger_fraction: opt(form.triggerGap) === undefined ? undefined : 1 - Number(form.triggerGap) / 100,
      loading: opt(form.loading, 0.01),
      pass_share: opt(form.passShare, 0.01),
      gamma,
    };
    try {
      const r = await api(product.assetClass, '/api/predict/quote', body);
      update(cur => ({ ...cur, quote: { ...form, result: r } }));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="Price my risk"
        title="What would protecting a bad season cost?"
        lede="Tell Hone what you do, where, and your season revenue. It looks up decades of local weather — snow, rain, heat or frost, whatever drives your business — works out how often seasons go badly there, and prices the protection itself."
      />
      <div className="stack-lg" style={{ maxWidth: 900 }}>
        {/* ------------------------------------------------ the three inputs */}
        <div className="card stack">
          <Field label="What do you do?" htmlFor="q-biz">
            <select id="q-biz" value={form.business} onChange={e => set({ business: e.target.value })}>
              {(businesses.length ? businesses : [{ key: 'ski_resort', label: 'Ski resort' }]).map(b => (
                <option key={b.key} value={b.key}>{b.label}</option>
              ))}
            </select>
          </Field>

          <Field label="Where?" htmlFor="q-place" hint={form.place ? `Using ${form.place.label}` : 'A town or resort name, then Find.'}>
            <div className="row" style={{ flexWrap: 'nowrap' }}>
              <input id="q-place" type="text" value={form.placeText} placeholder="e.g. Aspen"
                onChange={e => set({ placeText: e.target.value, place: null })}
                onKeyDown={e => { if (e.key === 'Enter') findPlace(); }} />
              <Button variant="secondary" icon="Search01Icon" onClick={findPlace} disabled={!form.placeText.trim()}>Find</Button>
            </div>
          </Field>
          {/* Several matches: let the user pick the right one. */}
          {matches && matches.length > 1 && !form.place && (
            <div className="row">
              {matches.map(m => (
                <Button key={`${m.latitude},${m.longitude}`} variant="secondary" size="sm" onClick={() => set({ place: m })}>{m.label}</Button>
              ))}
            </div>
          )}
          {matches && matches.length === 0 && <p className="tiny loss">No place by that name — try the nearest town.</p>}

          <Field label={biz?.margin === 1 ? 'Your season income' : 'Season revenue'} htmlFor="q-rev" hint="e.g. 4m, 250k or 60,000">
            <input id="q-rev" type="text" inputMode="decimal" value={form.revenue} onChange={e => set({ revenue: e.target.value })} />
          </Field>

          {/* ------------------------------------------ optional overrides */}
          <Expander summary={<span className="small">More options <span className="muted">— defaults are typical for this business</span></span>}>
            <div className="grid-2 mt-3" style={{ gap: 16 }}>
              <Field label="Cash reserves" htmlFor="q-res" hint={biz ? `Default: ${fmtPct(biz.reserves_frac)} of revenue` : ''}>
                <input id="q-res" type="text" inputMode="decimal" value={form.reserves} onChange={e => set({ reserves: e.target.value })} />
              </Field>
              <Field label="Profit margin (%)" htmlFor="q-mar" hint={biz ? `Default: ${fmtPct(biz.margin)}` : ''}>
                <input id="q-mar" type="number" min="1" max="100" value={form.margin} onChange={e => set({ margin: e.target.value })} />
              </Field>
              <Field label="How closely the weather drives revenue (0–1)" htmlFor="q-basis"
                hint={biz ? `Default: ${biz.basis}. Lower if other things matter a lot (snowmaking, indoor space, contracts).` : ''}>
                <input id="q-basis" type="number" min="0" max="1" step="0.05" value={form.basis} onChange={e => set({ basis: e.target.value })} />
              </Field>
              <Field label={`Bad season = ${biz?.high_is_bad ? 'more' : 'less'} than normal by (%)`} htmlFor="q-trig"
                hint={`Default: 30 — ${biz?.high_is_bad ? 'above 130%' : 'below 70%'} of normal${biz ? ` ${biz.peril_label.toLowerCase()} (${biz.season})` : ''}. Bigger = rarer, cheaper cover for a worse season.`}>
                <input id="q-trig" type="number" min="5" max="70" value={form.triggerGap} onChange={e => set({ triggerGap: e.target.value })} />
              </Field>
              {/* Revenue locked in before the season (passes, contracts, crop
                  insurance) doesn't fall in a bad one, so it softens the loss
                  (Vail's filings: sensitivity x (1 - 0.7 x share)). */}
              {biz && (
                <Field label="Revenue already locked in before the season (%)" htmlFor="q-pass"
                  hint={`Season passes, fixed contracts or crop insurance. Default: ${fmtPct(biz.pass_share)}.`}>
                  <input id="q-pass" type="number" min="0" max="100" value={form.passShare} onChange={e => set({ passShare: e.target.value })} />
                </Field>
              )}
              <Field label="Provider's margin over fair price (%)" htmlFor="q-load" hint="Default: 30%. 0 shows the pure fair price.">
                <input id="q-load" type="number" min="0" max="200" value={form.loading} onChange={e => set({ loading: e.target.value })} />
              </Field>
            </div>
          </Expander>

          <div className="row">
            <Button icon="ArrowRight01Icon" onClick={getQuote} disabled={!canQuote}>{busy ? 'Pricing…' : 'Price my risk'}</Button>
            <span className="tiny muted">
              At {isSample ? 'a sample' : 'your'} risk aversion ({fmtGamma(gamma)}).{' '}
              {isSample && <Link to={appPath(SLUG, 'risk')}>Measure yours</Link>}
            </span>
          </div>
          {busy && <Spinner>Reading decades of local weather…</Spinner>}
          <ErrorNotice error={error} onRetry={canQuote ? getQuote : undefined} />
        </div>

        {result && <QuoteResult q={result} />}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ result */
function QuoteResult({ q }) {
  const p = q.probability;
  // Units come from the server: "cm of snowfall", "in. of snow water (season
  // peak)", "rainy days", "days over 32°C"… Short form for labels, and one
  // decimal only for small amounts like inches of snow water.
  const u = q.unit.startsWith('in.') ? 'in.' : q.unit.startsWith('cm') ? 'cm' : q.unit.startsWith('mm') ? 'mm' : q.unit;
  const amount = v => (Math.abs(v) < 100 && !/days|nights/.test(q.unit) ? v.toFixed(1) : Math.round(v));
  const where = q.place.label.split(',')[0];
  const none = q.protection <= 0;
  const oneIn = p.estimate > 0 ? Math.round(1 / p.estimate) : null;
  const m = q.nearby_market;

  return (
    <div className="stack">
      {/* Headline: what to buy and what it costs. */}
      <div className="card">
        <div className="eyebrow">{q.business_label} · {q.place.label}</div>
        {none ? (
          <h2 className="pm-headline">Protection isn't worth it here at this price</h2>
        ) : (
          <h2 className="pm-headline">Protect {fmtMoney(q.protection)} for about {fmtMoney(q.cost_loaded)}</h2>
        )}
        <p className="small mt-1">
          Pays {none ? 'out' : fmtMoney(q.protection)} if {where} <strong>{q.condition}</strong> — {q.trigger_rule}.
          {q.loading > 0 && !none && <> At the fair price it would cost {fmtMoney(q.cost_fair)}; the rest is a typical provider's margin.</>}
        </p>
        <div className="pm-stats mt-4">
          <Stat size="sm" label="Chance of a bad season"
            value={fmtPct(p.estimate)} note={`about 1 in ${oneIn} · likely ${fmtPct(p.low)}–${fmtPct(p.high)}`} />
          <Stat size="sm" label="A bad season costs you" value={fmtMoney(q.loss)} note={`${fmtPct(q.avg_shortfall)} ${q.worse_word} than normal, on average`} />
          <Stat size="sm" label="Hone's price per $1 of cover" value={`${Math.round(q.loaded_price * 100)}¢`} note={`fair ${Math.round(q.fair_price * 100)}¢`} />
          <Stat size="sm" label="Worth to you" value={fmtMoney(q.plan.ce_gain)} note="certainty-equivalent gain at your risk aversion" />
        </div>
      </div>

      {/* The history the price comes from. */}
      <div className="card">
        <div className="takeaway">{q.peril_label}: every season since {q.history[0]?.season}</div>
        <p className="tiny muted mb-2">
          {q.unit.charAt(0).toUpperCase() + q.unit.slice(1)}, {q.season_label} each year. Highlighted bars were bad seasons ({fmtPct(p.historical)} of them).
          {p.trend_used
            ? ` There's a trend of ${p.trend_cm_per_decade > 0 ? '+' : ''}${p.trend_cm_per_decade.toFixed(1)} ${u} per decade, so the price uses today's level.`
            : ' No meaningful long-term trend, so the price uses the history as is.'}
        </p>
        <p className="tiny muted mb-2">Source: {q.index_source}.</p>
        <SeasonBars history={q.history} trigger={q.trigger_cm} normal={q.normal_cm} unit={u} />
        {/* Legend under the chart: the two lines are often too close to label inside it. */}
        <div className="pm-legend tiny muted mt-2">
          <span><i style={{ background: 'var(--loss, #b45309)' }} /> Bad season ({q.history.some(h => h.bad && h.cm > q.normal_cm) ? 'above' : 'below'} {amount(q.trigger_cm)} {u}, dashed line)</span>
          <span><i style={{ background: 'var(--current)' }} /> Other seasons · normal {amount(q.normal_cm)} {u} (dotted line)</span>
        </div>
      </div>

      {q.warnings.map(w => <Notice key={w} tone="attention">{w}</Notice>)}

      {/* Is there a market that could do this today? */}
      <div className="card">
        <div className="strong">Can you buy this today?</div>
        {m ? (
          <p className="small mt-1">
            The nearest tradeable market is <strong>{m.title}</strong> on Kalshi ({Math.round(m.distance_km)} km away). It pays on{' '}
            {m.settles_on}{m.settles_on !== 'season snowfall' ? ', which covers only part of your season' : ''}.
            {m.correlation != null && <> Season snowfall there has tracked yours with correlation {m.correlation.toFixed(2)}.</>}{' '}
            <Link to={appPath(SLUG, 'hedge')}>Size a hedge with it</Link> — the Income hedge page checks how many contracts are actually for sale.
          </p>
        ) : (
          <p className="small mt-1">
            No Kalshi market tracks this risk near you. Protection like this is sold privately as parametric weather
            cover; the price above is what a fair contract on your own local weather would cost.
          </p>
        )}
      </div>

      <Expander summary={<span className="small">How this was worked out</span>}>
        <ul className="plain-list small mt-2">
          {q.assumptions.map(a => <li key={a}>{a}</li>)}
        </ul>
      </Expander>
      <p className="tiny subtle">Hone prices and sizes protection to help you decide. It doesn't sell insurance or place trades.</p>
    </div>
  );
}

/* ------------------------------------------------------------- chart */
/**
 * One bar per season; bad seasons in the warning colour; dashed lines for
 * the bad-season threshold and normal. Plain SVG, scales to the card.
 */
function SeasonBars({ history, trigger, normal, unit = 'cm' }) {
  const W = 760, H = 200, pad = { l: 36, r: 8, t: 8, b: 22 };
  const max = Math.max(...history.map(h => h.cm), normal) * 1.05 || 1;
  const bw = (W - pad.l - pad.r) / history.length;
  const y = v => pad.t + (H - pad.t - pad.b) * (1 - v / max);
  const ticks = [0, Math.round(max / 2), Math.round(max)];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Weather each season, with the bad-season threshold">
      {ticks.map(t => (
        <g key={t}>
          <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="var(--line)" />
          <text x={pad.l - 6} y={y(t) + 4} textAnchor="end" fontSize="11" fill="var(--ink-3)">{t}</text>
        </g>
      ))}
      {history.map((h, i) => (
        <rect key={h.season} x={pad.l + i * bw + 1} y={y(h.cm)} width={Math.max(bw - 2, 1)} height={Math.max(H - pad.b - y(h.cm), 0)}
          fill={h.bad ? 'var(--loss, #b45309)' : 'var(--current)'} rx="1.5">
          <title>{`${h.season}–${String(h.season + 1).slice(2)}: ${unit === 'in.' ? h.cm.toFixed(1) : Math.round(h.cm)} ${unit}${h.bad ? ' (bad season)' : ''}`}</title>
        </rect>
      ))}
      <line x1={pad.l} x2={W - pad.r} y1={y(trigger)} y2={y(trigger)} stroke="var(--loss, #b45309)" strokeDasharray="5 4" strokeWidth="1.5" />
      <line x1={pad.l} x2={W - pad.r} y1={y(normal)} y2={y(normal)} stroke="var(--ink-3)" strokeDasharray="2 4" />
      {[0, Math.floor(history.length / 2), history.length - 1].map(i => history[i] && (
        <text key={i} x={pad.l + i * bw + bw / 2} y={H - 6} textAnchor="middle" fontSize="11" fill="var(--ink-3)">{history[i].season}</text>
      ))}
    </svg>
  );
}
