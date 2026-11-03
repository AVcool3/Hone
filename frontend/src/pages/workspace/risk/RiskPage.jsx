/*
 * Risk aversion — a permanent profile page, not a one-off quiz.
 *
 * Leads with the current estimate and what it means in plain English, then
 * its uncertainty. The questionnaire lives *inside* this page (mode state),
 * and finishing it leaves you on your result rather than pushing you on.
 *
 * Modes: 'result' (default) · 'adaptive' (8 questions) · 'full' (30) · 'manual'
 */
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useProduct } from '../../../App.jsx';
import { useRisk, SAMPLE_GAMMA } from '../../../lib/store.jsx';
import { useEngineResult } from '../../../lib/hooks.js';
import { appPath, docPath } from '../../../lib/products.js';
import { fmtDate, fmtGamma, fmtMoney, fmtPct } from '../../../lib/format.js';
import { Badge, Button, ErrorNotice, Field, Notice, NumberSlider, PageHeader, SectionTitle, Stat } from '../../../components/ui.jsx';
import { DensityChart } from '../../../components/charts.jsx';
import AdaptiveQuiz from './AdaptiveQuiz.jsx';
import FullMenuQuiz from './FullMenuQuiz.jsx';
import { certaintyEquivalent, effectSentence, mertonShare } from './interpret.js';

export default function RiskPage() {
  const product = useProduct();
  const { profile, setProfile, measured, gamma } = useRisk();
  // ?mode=adaptive lets other pages (and the homepage) deep-link straight in.
  const [params, setParams] = useSearchParams();
  const mode = params.get('mode') || 'result';
  const setMode = m => setParams(m === 'result' ? {} : { mode: m }, { replace: false });

  /** Save a finished assessment; the previous one moves into history. */
  const saveProfile = (next, source) => {
    setProfile(p => ({
      ...next,
      source,
      assessedAt: new Date().toISOString(),
      history: p.gamma != null
        ? [{ gamma: p.gamma, source: p.source, assessedAt: p.assessedAt, category: p.tier?.category }, ...(p.history || [])].slice(0, 12)
        : p.history || [],
      dose: { answers: [] },
      full: { choices: null, round: 0 },
    }));
    setMode('result');
  };

  const onAdaptiveDone = st =>
    saveProfile({ gamma: st.gamma, sd: st.gamma_sd, ci: st.gamma_ci90, ciLevel: 0.9, tier: st.tier, summary: st.summary }, 'adaptive');
  const onFullDone = p =>
    saveProfile({ gamma: p.gamma, sd: p.se_gamma, ci: p.gamma_ci95 ?? p.interval, ciLevel: p.gamma_ci95 ? 0.95 : null, tier: p.tier, summary: p.summary }, 'full');

  const inProgress = (profile.dose?.answers?.length ?? 0) > 0;

  return (
    <>
      <PageHeader
        eyebrow="Risk profile"
        title="Risk aversion"
        lede="How much certainty is worth to you. Hone measures it with choices between a sure amount and a gamble, then sizes every position against it."
        actions={mode === 'result' && (
          <>
            <Button icon="RefreshIcon" onClick={() => setMode('adaptive')}>{measured ? 'Retake assessment' : inProgress ? 'Resume assessment' : 'Assess my risk'}</Button>
            <Button variant="secondary" to={docPath(product.slug, 'methodology', 'risk-elicitation')} icon="Book02Icon">How it’s estimated</Button>
          </>
        )}
      />

      {mode === 'adaptive' && <AdaptiveQuiz assetClass={product.assetClass} onComplete={onAdaptiveDone} onCancel={() => setMode('result')} />}
      {mode === 'full' && <FullMenuQuiz assetClass={product.assetClass} onComplete={onFullDone} onCancel={() => setMode('result')} />}
      {mode === 'manual' && <ManualEntry onCancel={() => setMode('result')} onSave={g => saveProfile({ gamma: g, sd: null, ci: null, ciLevel: null, tier: null, summary: '' }, 'manual')} />}

      {mode === 'result' && (
        <div className="stack-lg">
          <ResultCard profile={profile} measured={measured} gamma={gamma} onStart={() => setMode('adaptive')} inProgress={inProgress} />

          <div className="card">
            <SectionTitle title="Other ways to set it" />
            <div className="grid-3">
              <div>
                <h3 style={{ fontSize: 16 }}>Adaptive · 8 questions</h3>
                <p className="small muted mt-1">Eight either/or choices. Each question is picked to be the most informative given your earlier answers, and it reaches higher risk aversion than the classic menu can.</p>
                <Button variant="text" onClick={() => setMode('adaptive')}>{inProgress ? 'Resume' : 'Start'}</Button>
              </div>
              <div>
                <h3 style={{ fontSize: 16 }}>Classic · 30 choices</h3>
                <p className="small muted mt-1">The Holt–Laury multiple price list: three rounds of ten lottery pairs at rising stakes. Slower, and fully transparent.</p>
                <Button variant="text" onClick={() => setMode('full')}>Use the full version</Button>
              </div>
              <div>
                <h3 style={{ fontSize: 16 }}>Set it directly</h3>
                <p className="small muted mt-1">Type a value to explore how sizes change. It won’t carry an uncertainty estimate, and it’s labelled as set by hand.</p>
                <div className="row">
                  <Button variant="text" onClick={() => setMode('manual')}>Enter a value</Button>
                  {measured && <Button variant="text" onClick={() => setProfile({ gamma: null, source: null, tier: null, ci: null, sd: null })}>Use the sample profile</Button>}
                </div>
              </div>
            </div>
          </div>

          {product.slug !== 'prediction-markets' && <RevealedRisk slug={product.slug} />}

          {profile.history?.length > 0 && (
            <div className="card">
              <SectionTitle title="Previous assessments" />
              <div className="tscroll">
                <table>
                  <thead><tr><th>Date</th><th>Method</th><th className="r">Estimate</th><th>Category</th></tr></thead>
                  <tbody>
                    {profile.history.map((h, i) => (
                      <tr key={i}><td>{fmtDate(h.assessedAt)}</td><td>{h.source}</td><td className="r">{fmtGamma(h.gamma)}</td><td>{h.category ?? '—'}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}

/* ---------------------------------------------------------------- result */
function ResultCard({ profile, measured, gamma, onStart, inProgress }) {
  const product = useProduct();
  // Illustration 1: a coin flip on $100,000 of savings.
  const ce = certaintyEquivalent(gamma, 80000, 130000);
  // Illustration 2: Merton's share in a broad index.
  const share = mertonShare(gamma);
  const ciText = profile.ci ? `${fmtGamma(profile.ci[0])} – ${fmtGamma(profile.ci[1])}` : null;

  return (
    <div className="risk-hero">
      <div className="card">
        <div className="row mb-3">
          {measured
            ? <Badge tone="yours">Your estimate · {profile.source === 'manual' ? 'set by hand' : profile.source === 'full' ? '30-question version' : 'adaptive questionnaire'}</Badge>
            : <Badge tone="sample">Sample profile — not yours yet</Badge>}
          {measured && profile.assessedAt && <span className="tiny subtle">Assessed {fmtDate(profile.assessedAt)}</span>}
        </div>
        <div className="risk-hero__big">{measured ? profile.tier?.category ?? 'Set by hand' : 'Moderately risk-averse (sample)'}</div>
        <p className="muted mt-3" style={{ fontSize: 17 }}>
          A coin flip that leaves $100,000 of savings at either <b>$80,000</b> or <b>$130,000</b> feels about as good to {measured ? 'you' : 'this sample investor'} as
          a sure <b>{fmtMoney(Math.round(ce / 100) * 100)}</b>.
        </p>
        <p className="mt-3">{effectSentence(gamma)}</p>
        {!measured && (
          <div className="row mt-4">
            <Button onClick={onStart} icon="Target02Icon">{inProgress ? 'Resume — you’re partway through' : 'Assess my risk · about 2 minutes'}</Button>
          </div>
        )}
      </div>

      <div className="card">
        <div className="grid-2" style={{ gap: 16 }}>
          <Stat label="Risk-aversion estimate (γ)" value={fmtGamma(gamma)} note="Higher = more cautious. Typical people: 1–4." />
          <Stat
            label={profile.ciLevel ? `${Math.round(profile.ciLevel * 100)}% likely range` : 'Uncertainty'}
            value={ciText ?? '—'}
            size="sm"
            note={ciText ? 'From the spread of your answers' : measured ? 'Not available for a hand-set value' : 'Measure yours to see it'}
          />
          <Stat label="Tier" value={profile.tier ? `${profile.tier.tier} of 50` : '—'} size="sm" note="A coarse grouping used in reports — secondary to the estimate." />
          <Stat
            label="Rule-of-thumb stock share"
            value={Number.isFinite(share) ? (share > 1 ? 'Over 100%' : fmtPct(share)) : '—'}
            size="sm"
            note="Merton’s rule with a 5% premium and 16% index volatility."
          />
        </div>
        {profile.source === 'adaptive' && profile.ci && <MiniBelief gamma={gamma} ci={profile.ci} />}
        <p className="tiny subtle mt-3">
          What this changes: every tool reads this one number. <Link to={appPath(product.slug, product.slug === 'prediction-markets' ? 'hedge' : 'portfolio')}>See its effect</Link>.
        </p>
      </div>
    </div>
  );
}

/** A compact normal approximation of the saved estimate, for the result card. */
function MiniBelief({ gamma, ci }) {
  const sd = (ci[1] - ci[0]) / (2 * 1.645);
  const grid = Array.from({ length: 121 }, (_, i) => -1 + i * 0.1);
  const dens = grid.map(g => Math.exp(-0.5 * ((g - gamma) / sd) ** 2));
  return <div className="mt-4"><DensityChart grid={grid} density={dens} ci={ci} mark={gamma} height={110} /></div>;
}

/* ---------------------------------------------------------------- manual */
function ManualEntry({ onSave, onCancel }) {
  const { gamma } = useRisk();
  const [g, setG] = useState(gamma ?? SAMPLE_GAMMA);
  return (
    <div className="card">
      <SectionTitle title="Set your risk aversion directly" sub="Useful for exploring. A measured estimate is more reliable." />
      <Field label="Risk-aversion coefficient" hint="0.5 = adventurous · 2 = moderate · 5+ = very cautious">
        <NumberSlider value={g} onChange={setG} min={0} max={12} step={0.1} ariaLabel="Risk aversion" />
      </Field>
      <p className="muted mt-3">{effectSentence(g)}</p>
      <div className="row mt-5">
        <Button icon="Tick02Icon" onClick={() => onSave(g)}>Use this value</Button>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- revealed */
/*
 * Stated vs. revealed: what the holdings themselves imply. Uses
 * /api/portfolio with analyze=true. `request` is module-level so the hook's
 * callback stays stable.
 */
const portfolioRequest = gamma => ({ analyze: true, stated_gamma: gamma });

function RevealedRisk({ slug }) {
  const { measured } = useRisk();
  const res = useEngineResult(slug, 'portfolio', '/api/portfolio', portfolioRequest);
  const a = res.result?.analysis;
  return (
    <div className="card">
      <SectionTitle
        title="How you answer vs. how you invest"
        sub="Your holdings imply a risk aversion of their own. A big gap is worth knowing about."
        right={<Button variant="secondary" size="sm" icon={a ? 'RefreshIcon' : 'Analytics01Icon'} onClick={res.run} disabled={res.busy}>{res.busy ? 'Measuring…' : a ? 'Recalculate' : 'Compare with my holdings'}</Button>}
      />
      <ErrorNotice error={res.error} onRetry={res.run} settingsTo={appPath(slug, 'settings')} />
      {a && (
        <>
          <div className="stat-row">
            <Stat label={measured ? 'You answer like' : 'Sample profile'} value={a.stated_tier?.category ?? '—'} size="sm" note={a.stated_gamma != null ? `Estimate ${fmtGamma(a.stated_gamma)}` : ''} />
            <Stat label="Your holdings behave like" value={a.revealed_tier.category} size="sm" note={`Implied estimate ${fmtGamma(a.revealed_gamma)}`} />
            <Stat label="Portfolio volatility" value={fmtPct(a.volatility)} size="sm" note="Typical yearly swing" />
            <Stat label="Market beta" value={a.beta.toFixed(2)} size="sm" note="1.0 moves with the index" />
          </div>
          <p className="tiny subtle mt-3">
            The implied value assumes the market pays a {fmtPct(a.market_premium_assumption)} yearly premium for risk. It describes your holdings, not your intentions.
            {res.result.demo && ' Holdings shown are the sample portfolio.'}
          </p>
        </>
      )}
      {!a && !res.busy && !res.error && <Notice>Uses your current holdings ({res.result?.demo === false ? 'paper account' : 'sample portfolio by default'}) and two years of prices.</Notice>}
    </div>
  );
}
