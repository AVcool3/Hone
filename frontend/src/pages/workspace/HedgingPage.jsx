/*
 * Hedging (stocks & crypto) — three views of the same question,
 * "how bad could this get, and what would bring it back within my limit?"
 *
 *   ?tab=plan       Hedge plan: risk budget vs. current risk, and the hedges
 *                   that would close the gap (cash, index short, options).
 *   ?tab=stress     Stress scenarios: historical crashes replayed on the
 *                   proposed portfolio.
 *   ?tab=tail       Tail risk (CVaR): "when it goes badly, how badly" — and
 *                   the risk-first portfolio that minimises it.
 *
 * The hedge plan and stress scenarios come from the same /api/optimize result
 * as the Portfolio page, so they always describe the same proposal.
 */
import { Link, useSearchParams } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import AllocationBars from '../../components/AllocationBars.jsx';
import { Badge, Button, ErrorNotice, Notice, PageHeader, SectionTitle, SkeletonRows, StaleBanner, Stat } from '../../components/ui.jsx';
import { useEngineResult, useOptimize } from '../../lib/hooks.js';
import { appPath, docPath } from '../../lib/products.js';
import { fmtMoney, fmtPct, fmtSMoney, fmtSPct } from '../../lib/format.js';

const KIND_LABEL = { cash: 'Hold more cash', short: 'Short the index', protective_put: 'Protective puts', collar: 'Collar' };

export default function HedgingPage() {
  const product = useProduct();
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') || 'plan';
  const tabs = [
    { key: 'plan', label: 'Hedge plan' },
    { key: 'stress', label: 'Stress scenarios' },
    { key: 'tail', label: 'Tail risk' },
  ];
  return (
    <>
      <PageHeader
        eyebrow="Downside"
        title="Hedging"
        lede="How much you could lose, how much your risk level says you should be able to stomach, and what would close the gap."
        actions={<Button variant="secondary" icon="Book02Icon" to={docPath(product.slug, 'methodology', 'tail-risk')}>Methodology</Button>}
      />
      <div className="tabs mb-5" role="tablist">
        {tabs.map(t => (
          <button key={t.key} type="button" role="tab" className="tab" aria-selected={tab === t.key} onClick={() => setParams(t.key === 'plan' ? {} : { tab: t.key })}>{t.label}</button>
        ))}
      </div>
      {tab === 'plan' && <HedgePlan product={product} />}
      {tab === 'stress' && <Stress product={product} />}
      {tab === 'tail' && <TailRisk product={product} />}
    </>
  );
}

/* ------------------------------------------------------------------ plan */
function HedgePlan({ product }) {
  const opt = useOptimize(product.slug, { auto: true });
  const plan = opt.result?.hedge_plan;
  const value = plan?.portfolio_value;
  // No risk budget is shown when it can't be computed: with a negative
  // expected return the Merton budget is undefined, and printing a number
  // there would contradict the sentence above it.
  const budget = (value && !plan?.premium_is_negative) ? plan.tolerable_annual_loss_usd : null;

  return (
    <div className="stack-lg">
      {opt.stale && <StaleBanner onRecalc={opt.run} busy={opt.busy} what="this hedge plan" />}
      <ErrorNotice error={opt.error} onRetry={opt.run} settingsTo={appPath(product.slug, 'settings')} />
      {!plan && opt.busy && <div className="card"><SkeletonRows /></div>}
      {plan && (
        <>
          <div className="card">
            <p className="takeaway">
              {plan.premium_is_negative
                ? 'This proposal has a negative expected return, so there is no risk budget to hedge to — revisit your views first.'
                : plan.needs_hedge
                  ? `The proposed portfolio swings more than your risk level allows: ${fmtPct(plan.current_volatility)} a year against a target of ${fmtPct(plan.target_volatility)}.`
                  : `The proposed portfolio is within your risk level: ${fmtPct(plan.current_volatility)} a year, at or below the ${fmtPct(plan.target_volatility)} target. No hedge needed.`}
            </p>
            <div className="stat-row">
              <Stat label="Volatility now" value={fmtPct(plan.current_volatility)} note="Proposed portfolio, typical yearly swing" />
              <Stat label="Your target" value={plan.premium_is_negative ? '—' : fmtPct(plan.target_volatility)} note="Merton risk budget at your risk level" />
              <Stat label="A bad year could cost" value={plan.current_annual_loss_usd != null ? fmtMoney(plan.current_annual_loss_usd) : '—'} note="One-standard-deviation loss, in dollars" />
              <Stat label="What you can stomach" value={budget != null ? fmtMoney(budget) : '—'} note={budget != null ? 'Same measure at your target' : 'Not defined for a losing plan'} />
            </div>
          </div>
          {plan.premium_is_negative && (
            <Notice tone="attention" title="Negative expected return.">
              The risk budget assumes you’re being paid to take risk. Here you aren’t ({fmtSPct(plan.expected_excess_return)} a year over cash), so a hedge would only make
              a plan you expect to lose cheaper to hold. <Link to={appPath(product.slug, 'theses')}>Revisit your theses</Link>.
            </Notice>
          )}
          {plan.needs_hedge && plan.suggestions.length > 0 && (
            <div className="card">
              <SectionTitle title="Ways to close the gap" sub={product.hedgeNote} />
              <div className="grid-2">
                {plan.suggestions.map(s => (
                  <div key={s.kind + s.instrument} className="hedge-card">
                    <div className="hedge-card__kind">{KIND_LABEL[s.kind] ?? s.kind}</div>
                    <p className="mt-2">{s.description}</p>
                    <dl className="kv mt-3">
                      <dt>Covers</dt><dd>{fmtPct(s.hedge_notional_fraction)} of the portfolio{value ? ` (${fmtMoney(s.hedge_notional_fraction * value)})` : ''}</dd>
                      <dt>Volatility after</dt><dd>{s.hedged_volatility != null ? fmtPct(s.hedged_volatility) : 'Caps the loss instead'}</dd>
                      <dt>Estimated cost</dt><dd>{fmtPct(s.est_annual_cost_fraction, 1)} a year{value ? ` (${fmtMoney(s.est_annual_cost_fraction * value)})` : ''}</dd>
                      {s.details?.pricing_source && <><dt>Pricing</dt><dd>{s.details.pricing_source === 'black_scholes' ? 'Model estimate (Black–Scholes)' : s.details.pricing_source}</dd></>}
                    </dl>
                    {s.warning && <Notice tone="attention" className="mt-3">{s.warning}</Notice>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ stress */
function Stress({ product }) {
  const opt = useOptimize(product.slug, { auto: true });
  const plan = opt.result?.hedge_plan;
  const rows = plan?.scenarios ?? [];
  const worst = rows.length ? Math.min(...rows.map(s => s.loss_fraction)) : 0;
  return (
    <div className="stack-lg">
      {opt.stale && <StaleBanner onRecalc={opt.run} busy={opt.busy} what="these scenarios" />}
      <ErrorNotice error={opt.error} onRetry={opt.run} />
      {plan && (
        <div className="card">
          <p className="takeaway">If one of these crashes happened again, the proposed portfolio could lose up to {fmtPct(-worst)}{plan.portfolio_value ? ` (${fmtMoney(-worst * plan.portfolio_value)})` : ''}.</p>
          <div className="stack">
            {rows.map(s => (
              <div key={s.name}>
                <div className="row row--between small"><b>{s.name}</b><span className="subtle">Market fell {fmtPct(-s.market_shock)}</span></div>
                <div className="alloc__bars mt-1" role="img" aria-label={`${s.name}: lose ${fmtPct(-s.loss_fraction)}${s.hedged_loss_fraction != null ? `, hedged ${fmtPct(-s.hedged_loss_fraction)}` : ''}`}>
                  <div className="alloc__track"><div className="alloc__fill" style={{ width: `${(s.loss_fraction / worst) * 100}%`, background: 'var(--loss)' }} /></div>
                  {s.hedged_loss_fraction != null && <div className="alloc__track"><div className="alloc__fill alloc__fill--proposed" style={{ width: `${(s.hedged_loss_fraction / worst) * 100}%` }} /></div>}
                </div>
                <div className="tiny muted mt-1">
                  Loss {fmtPct(-s.loss_fraction)} ({fmtSMoney(s.loss_usd)})
                  {s.hedged_loss_fraction != null && <> · with the first hedge {fmtPct(-s.hedged_loss_fraction)} ({fmtSMoney(s.hedged_loss_usd)})</>}
                </div>
              </div>
            ))}
          </div>
          <p className="chart-caption mt-4">
            Scenario, not forecast: each historical market drop is applied to today’s proposed portfolio through its sensitivity to {product.marketName}.
            Real crashes also change correlations, so treat these as a floor on how bad it could feel.
          </p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ tail risk */
const cvarRequest = (gamma, ws) => ({ gamma, max_weight: ws.maxWeight });

function TailRisk({ product }) {
  const res = useEngineResult(product.slug, 'cvar', '/api/cvar', cvarRequest);
  const r = res.result;
  return (
    <div className="stack-lg">
      <Notice tone="info">
        Volatility treats a 10% gain and a 10% loss the same. Tail risk asks only about the bad side: when it goes badly, how badly?
        Here that is the average loss across the worst 5% of one-month periods in history (CVaR).
      </Notice>
      <div className="card">
        <SectionTitle
          title="The risk-first portfolio"
          sub="The mix with the smallest average loss in bad months, next to one balanced for your risk level."
          right={<Button icon={r ? 'RefreshIcon' : 'Analytics01Icon'} onClick={res.run} disabled={res.busy}>{res.busy ? 'Measuring…' : r ? 'Recalculate' : 'Measure tail risk'}</Button>}
        />
        {res.stale && <div className="mb-4"><StaleBanner onRecalc={res.run} busy={res.busy} what="this tail-risk result" /></div>}
        <ErrorNotice error={res.error} onRetry={res.run} settingsTo={appPath(product.slug, 'settings')} />
        {r && (
          <div className="stack">
            <p className="takeaway">{r.summary}</p>
            {r.cvar_saved_usd != null && <Badge tone="proposed">Risk-first mix avoids about {fmtMoney(r.cvar_saved_usd)} of loss in a bad month</Badge>}
            <div className="tscroll">
              <table>
                <thead><tr><th>Portfolio</th><th className="r">Avg month</th><th className="r">Volatility</th><th className="r">Bad month (VaR {Math.round(r.beta * 100)}%)</th><th className="r">Worst 5% avg (CVaR)</th><th className="r">Worst seen</th></tr></thead>
                <tbody>
                  {r.comparison.map(c => (
                    <tr key={c.portfolio}>
                      <td>{c.label}</td>
                      <td className="r">{fmtSPct(c.mean)}</td>
                      <td className="r">{fmtPct(c.volatility, 1)}</td>
                      <td className="r loss">{fmtPct(c.var, 1)}</td>
                      <td className="r loss">{fmtPct(c.cvar, 1)}</td>
                      <td className="r loss">{fmtPct(-c.worst, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h3 style={{ fontSize: 16 }}>Current vs. risk-first allocation</h3>
            <AllocationBars rows={r.min_cvar_weights} />
            <p className="chart-caption">
              Based on {r.n_scenarios} overlapping {r.horizon}-day windows, of which {r.tail_scenarios} form the worst 5%. Overlapping windows share data, so the
              evidence is thinner than the count suggests. This is history, not a forecast.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
