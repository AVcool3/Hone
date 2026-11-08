/*
 * Home — the product overview for Stocks, Crypto or Prediction Markets.
 *
 * Page order (top to bottom):
 *   1. Hero: headline, one sentence, two actions, and a LIVE product preview
 *      that calls the real engine (no screenshots, no invented numbers).
 *   2. Feature tabs: five lavender pills; each panel shows one tool working
 *      on the same sample portfolio as the hero, plus a link to the full docs.
 *   3. Launch cards: jump straight into a tool.
 *   4. The problem, then the FAQ ("Is this real money?").
 *   5. A closing call to action.
 *
 * The hero's latest engine result is lifted into <HomeInner> state so the
 * feature tabs can reuse it ("the same sample portfolio across the story").
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import AllocationBars from '../../components/AllocationBars.jsx';
import Icon from '../../components/Icon.jsx';
import { DensityChart, OutcomeBars } from '../../components/charts.jsx';
import { Badge, Button, ErrorNotice, NumberSlider, SkeletonRows, Stat } from '../../components/ui.jsx';
import { api, quote } from '../../lib/api.js';
import { SAMPLE_GAMMA, useDebounced, useLatestRequest } from '../../lib/store.jsx';
import { appPath, docPath, publicPath } from '../../lib/products.js';
import {
  fmtCents, fmtDate, fmtGamma, fmtHorizon, fmtMoney, fmtNum, fmtPct, fmtPrice, fmtSMoney, fmtSPct, impliedChange,
} from '../../lib/format.js';
import './marketing.css';

/** Value of the server's demo portfolio (hone/web/app.py DEMO_PORTFOLIO_VALUE). */
const DEMO_VALUE = 25000;
/** Largest single position the sample optimizer may propose. */
const SAMPLE_MAX_WEIGHT = 0.35;
/** Sample income-hedge inputs for Prediction Markets. */
const PM_SAMPLE = { wealth: 40000, loss: 12000, priceCents: 30 };

/** Short label for a symbol ("SOL/USD" -> "SOL"). */
const short = sym => (sym || '').replace('/USD', '');

/*
 * Reveal used to fade sections in on scroll. The site no longer animates
 * content in (it read as gimmicky), so it's now a plain wrapper. Kept as a
 * component so the page structure stays readable; `delay` is ignored.
 */
// eslint-disable-next-line no-unused-vars
function Reveal({ children, delay, className }) {
  return <div className={className}>{children}</div>;
}

/* ========================================================================== */
/* Page                                                                       */
/* ========================================================================== */
export default function Home() {
  const product = useProduct();
  // `key` remounts everything when the product changes, so no stale preview
  // from Stocks ever shows on the Crypto page.
  return <HomeInner key={product.slug} product={product} />;
}

function HomeInner({ product }) {
  const isPM = product.slug === 'prediction-markets';
  // The hero's latest engine result, shared with the feature tabs.
  const [sample, setSample] = useState(null);

  return (
    <>
      {isPM ? <HeroHedge product={product} onResult={setSample} /> : <HeroPortfolio product={product} onResult={setSample} />}

      <section className="mk-section mk-section--alt" aria-labelledby="features-title">
        <div className="container">
          <Reveal>
            <div className="mk-head">
              <div className="eyebrow mb-3">{isPM ? 'How Hone sizes a hedge' : 'What you can do'}</div>
              <h2 id="features-title">
                {isPM ? 'From a worry about next season to a sized, explained hedge.' : 'Every tool works on its own. Together they explain a portfolio.'}
              </h2>
              <p className="lede">
                {isPM
                  ? 'Each step below runs on the same illustrative sample as the preview above. Pick any step — there is no fixed order.'
                  : 'Each panel below uses the same sample portfolio as the preview above. Open any of them directly in the workspace.'}
              </p>
            </div>
          </Reveal>
          {isPM ? <PMFeatureTabs product={product} sample={sample} /> : <PortfolioFeatureTabs product={product} sample={sample} />}
        </div>
      </section>

      <section className="mk-section" aria-labelledby="launch-title">
        <div className="container">
          <Reveal>
            <div className="mk-head">
              <h2 id="launch-title">Start with whichever question you have.</h2>
            </div>
          </Reveal>
          <LaunchCards product={product} />
        </div>
      </section>

      <section className="mk-section mk-section--alt" aria-labelledby="problem-title">
        <div className="container">
          <Reveal>
            <div className="mk-head">
              <h2 id="problem-title">{isPM ? 'Your paycheck carries risk nobody sizes.' : 'Most tools stop at a risk label.'}</h2>
            </div>
          </Reveal>
          <Problem product={product} />
        </div>
      </section>

      <section className="mk-section" aria-labelledby="faq-title">
        <div className="container">
          <Reveal>
            <div className="mk-head">
              <h2 id="faq-title">Common questions</h2>
            </div>
          </Reveal>
          <Faq product={product} />
        </div>
      </section>

      <section className="closing">
        <div className="container">
          <Reveal>
            <h2>{isPM ? 'See what a bad season would cost — and what cover would cost.' : 'Change one belief. Watch the portfolio answer.'}</h2>
            <div className="row">
              <Button size="lg" to={isPM ? appPath(product.slug, 'hedge') : appPath(product.slug)} iconRight="ArrowRight01Icon">
                {isPM ? 'Size a sample hedge' : 'Explore a sample portfolio'}
              </Button>
              <Button size="lg" variant="secondary" to="/#waitlist">Join the waitlist</Button>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}

/* ========================================================================== */
/* Hero — Stocks & Crypto: an editable thesis beside a live allocation        */
/* ========================================================================== */
function HeroPortfolio({ product, onResult }) {
  const ex = product.example; // { ticker, target, confidence, horizonDays }

  // Reference price for the example asset (sample prices move daily).
  const [ref, setRef] = useState(null);
  const [quoteError, setQuoteError] = useState(null);
  // The two inputs a visitor can change.
  const [target, setTarget] = useState(null);
  const [confidence, setConfidence] = useState(ex.confidence);
  // Engine output.
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  const latest = useLatestRequest();

  // 1) Load the reference price, then seed the target ~20% above it.
  useEffect(() => {
    let alive = true;
    setQuoteError(null);
    quote(product.assetClass, ex.ticker, { demo: true })
      .then(q => {
        if (!alive) return;
        if (!q.price) throw new Error(`No sample price for ${ex.ticker}.`);
        setRef(q);
        setTarget(t => t ?? Math.round(q.price * 1.2));
      })
      .catch(e => alive && setQuoteError(e));
    return () => { alive = false; };
  }, [product.assetClass, ex.ticker, retry]);

  // 2) Recalculate the allocation whenever the (debounced) inputs change.
  const dTarget = useDebounced(target, 250);
  const dConfidence = useDebounced(confidence, 250);
  useEffect(() => {
    if (!ref || !dTarget) return;
    setLoading(true);
    latest(signal =>
      api(
        product.assetClass,
        '/api/optimize',
        {
          demo: true,
          gamma: SAMPLE_GAMMA,
          max_weight: SAMPLE_MAX_WEIGHT,
          views: [{ ticker: ex.ticker, target_price: dTarget, confidence: dConfidence, horizon_days: ex.horizonDays }],
        },
        { signal },
      ),
    )
      .then(data => {
        setResult(data);
        setError(null);
        setLoading(false);
        onResult?.(data);
      })
      .catch(e => {
        if (e.name === 'AbortError') return; // superseded by a newer request
        setError(e);
        setLoading(false);
      });
  }, [ref, dTarget, dConfidence, retry, product.assetClass, ex.ticker, ex.horizonDays, latest, onResult]);

  // Rows sorted by current weight, so bars don't jump around while dragging.
  const rows = (result?.weights || [])
    .map(w => ({ symbol: short(w.symbol), current: w.current, target: w.target, raw: w }))
    .sort((a, b) => b.current - a.current);
  const exRow = result?.weights?.find(w => w.symbol === ex.ticker);
  const change = impliedChange(ref?.price, target);

  return (
    <section className="hero">
      <div className="container hero__grid">
        <div>
          <div className="hero__product">
            <span className="badge badge--product" data-product={product.slug}>{product.name}</span>
            <span className="subtle">{product.kind}</span>
          </div>
          <h1 className="display hero__title">
            Turn your investment views into a portfolio you can explain.
          </h1>
          <p className="lede hero__lede">
            Compare a model-proposed allocation with what you hold, understand the risk behind every change,
            and test it with paper money — {product.slug === 'crypto' ? 'for the coins you actually follow.' : 'before a single real dollar moves.'}
          </p>
          <div className="hero__ctas">
            <Button size="lg" to={appPath(product.slug)} iconRight="ArrowRight01Icon">Explore a sample portfolio</Button>
            <Button size="lg" variant="secondary" to={appPath(product.slug, 'risk')}>Build my portfolio</Button>
          </div>
          <p className="hero__note">No account needed. Sample data first; connect an Alpaca paper account when you want your own.</p>
          {product.volatilityNote && <p className="hero__note">{product.volatilityNote}</p>}
        </div>

        {/* ---------------- live preview ---------------- */}
        <div className="preview" aria-label="Live preview: change a belief and see the proposed allocation">
          <div className="preview__head">
            <span className="preview__title">Try it: change one belief</span>
            <Badge tone="sample">Sample portfolio · sample prices</Badge>
          </div>

          {quoteError ? (
            <ErrorNotice error={quoteError} onRetry={() => setRetry(n => n + 1)} />
          ) : (
            <div className="preview__thesis">
              <p className="preview__sentence">
                I think <b>{short(ex.ticker)}</b> reaches <b>{target ? fmtPrice(target) : '…'}</b> within{' '}
                <b>{fmtHorizon(ex.horizonDays)}</b>, and I’m <b>{fmtPct(confidence)}</b> confident.
              </p>
              <div className="preview__ctl">
                <label htmlFor="hero-target">Target price</label>
                {ref ? (
                  <NumberSlider
                    id="hero-target"
                    ariaLabel="Target price"
                    value={target}
                    onChange={v => setTarget(Math.round(v * 100) / 100)}
                    min={Math.round(ref.price * 0.5)}
                    max={Math.round(ref.price * 2)}
                    step={1}
                    prefix="$"
                    inputWidth={112}
                  />
                ) : <div className="skeleton" style={{ height: 44 }} />}
              </div>
              <div className="preview__ctl">
                <label htmlFor="hero-conf">Confidence</label>
                <NumberSlider
                  id="hero-conf"
                  ariaLabel="Confidence"
                  value={confidence}
                  onChange={v => setConfidence(v)}
                  min={0.05}
                  max={0.95}
                  step={5}
                  scale={100}
                  suffix="%"
                  inputWidth={112}
                />
              </div>
              <div className="preview__meta">
                <span>Reference price <b>{ref ? fmtPrice(ref.price) : '…'}</b></span>
                <span>Implied change <b>{change == null ? '…' : fmtSPct(change)}</b></span>
                <span>Risk profile <b>sample ({fmtGamma(SAMPLE_GAMMA)})</b></span>
              </div>
            </div>
          )}

          <div className="preview__result" aria-live="polite" aria-busy={loading}>
            {error ? (
              <ErrorNotice error={error} onRetry={() => setRetry(n => n + 1)} />
            ) : rows.length ? (
              <>
                <AllocationBars rows={rows} highlight={short(ex.ticker)} compact />
                {exRow && (
                  <p className="preview__why">
                    <b>Why {short(ex.ticker)} moved {fmtPct(exRow.current)} → {fmtPct(exRow.target)}:</b> {exRow.reason}
                  </p>
                )}
              </>
            ) : (
              <SkeletonRows rows={5} />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ========================================================================== */
/* Hero — Prediction Markets: income with and without a hedge                 */
/* ========================================================================== */
function HeroHedge({ product, onResult }) {
  const [loss, setLoss] = useState(PM_SAMPLE.loss);
  const [priceCents, setPriceCents] = useState(PM_SAMPLE.priceCents);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [retry, setRetry] = useState(0);
  const latest = useLatestRequest();
  const dLoss = useDebounced(loss, 250);
  const dPrice = useDebounced(priceCents, 250);

  useEffect(() => {
    const inputs = { gamma: SAMPLE_GAMMA, wealth: PM_SAMPLE.wealth, loss: dLoss, price: dPrice / 100 };
    latest(signal => api(product.assetClass, '/api/predict/hedge', inputs, { signal }))
      .then(data => {
        setResult(data);
        setError(null);
        onResult?.({ data, inputs });
      })
      .catch(e => e.name !== 'AbortError' && setError(e));
  }, [dLoss, dPrice, retry, product.assetClass, latest, onResult]);

  const bars = outcomeRows(result);

  return (
    <section className="hero">
      <div className="container hero__grid">
        <div>
          <div className="hero__product">
            <span className="badge badge--product" data-product={product.slug}>{product.name}</span>
            <span className="subtle">{product.kind}</span>
          </div>
          <h1 className="display hero__title">Your paycheck is already a position.</h1>
          <p className="lede hero__lede">
            If your income rises and falls with snowfall, ad budgets, hiring or mortgage rates, an event contract can
            pay out in the bad season. Hone sizes that contract to your risk tolerance and shows the cost.
          </p>
          <div className="hero__ctas">
            <Button size="lg" to={appPath(product.slug, 'hedge')} iconRight="ArrowRight01Icon">Size a sample hedge</Button>
            <Button size="lg" variant="secondary" to={appPath(product.slug, 'markets')}>Browse markets</Button>
          </div>
          <p className="hero__note">{product.hedgeNote}</p>
        </div>

        <div className="preview" aria-label="Live preview: income with and without a hedge">
          <div className="preview__head">
            <span className="preview__title">A ski instructor’s season</span>
            <Badge tone="sample">Illustrative example · not a live market</Badge>
          </div>
          <div className="preview__thesis">
            <p className="preview__sentence">
              I expect to earn <b>{fmtMoney(PM_SAMPLE.wealth)}</b> this season. A low-snow winter would cost me{' '}
              <b>{fmtMoney(loss)}</b>. A contract that pays $1 if snowfall is low costs <b>{priceCents}¢</b>.
            </p>
            <div className="preview__ctl">
              <label htmlFor="pm-loss">Bad-season loss</label>
              <NumberSlider id="pm-loss" ariaLabel="Bad-season loss" value={loss} onChange={v => setLoss(Math.round(v))}
                min={1000} max={30000} step={500} prefix="$" inputWidth={118} />
            </div>
            <div className="preview__ctl">
              <label htmlFor="pm-price">Contract price</label>
              <NumberSlider id="pm-price" ariaLabel="Contract price in cents" value={priceCents} onChange={v => setPriceCents(Math.round(v))}
                min={5} max={80} step={1} suffix="¢" inputWidth={118} />
            </div>
          </div>
          <div className="preview__result" aria-live="polite">
            {error ? (
              <ErrorNotice error={error} onRetry={() => setRetry(n => n + 1)} />
            ) : result ? (
              <>
                <div className="alloc__legend" aria-hidden="true">
                  <span><i className="alloc__swatch alloc__swatch--current" /> Without hedge</span>
                  <span><i className="alloc__swatch alloc__swatch--proposed" /> With hedge</span>
                  <span className="subtle">Money at season’s end, after costs</span>
                </div>
                <OutcomeBars rows={bars} height={200} />
                <div className="preview__meta mt-2">
                  <span>Buy <b>{fmtNum(result.contracts)}</b> contracts</span>
                  <span>Cost <b>{fmtMoney(result.cost + result.fee)}</b> incl. fees</span>
                  <span>Worst case <b>{fmtMoney(result.worst_unhedged)} → {fmtMoney(result.worst_hedged)}</b></span>
                </div>
              </>
            ) : (
              <SkeletonRows rows={5} />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

/** /api/predict/hedge `states` -> rows for <OutcomeBars>, bad season first. */
function outcomeRows(result) {
  if (!result?.states) return [];
  return [...result.states]
    .sort((a, b) => Number(b.loss) - Number(a.loss))
    .map(s => ({ label: s.loss ? 'Bad season' : 'Normal season', prob: s.prob, unhedged: s.wealth_unhedged, hedged: s.wealth_hedged }));
}

/* ========================================================================== */
/* Feature tabs — manual control only, no autoplay                            */
/* ========================================================================== */
function FeatureTabs({ tabs }) {
  const [active, setActive] = useState(tabs[0].key);
  const tab = tabs.find(t => t.key === active) || tabs[0];

  // Arrow keys move between tabs (WAI-ARIA tabs pattern).
  const onKeyDown = e => {
    const i = tabs.findIndex(t => t.key === active);
    if (e.key === 'ArrowRight') setActive(tabs[(i + 1) % tabs.length].key);
    if (e.key === 'ArrowLeft') setActive(tabs[(i - 1 + tabs.length) % tabs.length].key);
  };

  return (
    <div>
      <div className="pilltabs" role="tablist" aria-label="Features" onKeyDown={onKeyDown}>
        {tabs.map(t => (
          <button
            key={t.key}
            type="button"
            role="tab"
            id={`ft-${t.key}`}
            aria-selected={t.key === active}
            aria-controls={`fp-${t.key}`}
            tabIndex={t.key === active ? 0 : -1}
            className="pilltab"
            onClick={() => setActive(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="feature" role="tabpanel" id={`fp-${tab.key}`} aria-labelledby={`ft-${tab.key}`}>
        <div className="feature__copy">
          <h3>{tab.title}</h3>
          <p>{tab.body}</p>
          <div className="row" style={{ marginTop: 20 }}>
            <Button variant="secondary" to={tab.tool.to} iconRight="ArrowRight01Icon" style={{ marginTop: 0 }}>{tab.tool.label}</Button>
            <Button variant="text" to={tab.doc.to} style={{ marginTop: 0 }}>{tab.doc.label}</Button>
          </div>
        </div>
        <div className="feature__demo">{tab.demo}</div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------- Stocks & Crypto tabs */
function PortfolioFeatureTabs({ product, sample }) {
  const s = product.slug;
  const tabs = [
    {
      key: 'risk',
      label: 'Understand your risk',
      title: 'Eight choices, one honest estimate.',
      body: 'Choose between a sure amount and a gamble. Each answer picks the most informative next question, and the estimate shows how uncertain it still is — not just a label.',
      demo: <RiskDemo product={product} />,
      tool: { to: appPath(s, 'risk'), label: 'Open Risk aversion' },
      doc: { to: docPath(s, 'methodology', 'risk-elicitation'), label: 'How the estimate works' },
    },
    {
      key: 'views',
      label: 'Express your views',
      title: 'Say it the way an investor would.',
      body: 'Pick an asset, a target, a horizon and how confident you are. Hone translates that sentence into model inputs, and every thesis stays an editable card you can switch off to compare.',
      demo: <ViewsDemo product={product} />,
      tool: { to: appPath(s, 'theses'), label: 'Open Investment theses' },
      doc: { to: docPath(s, 'methodology', 'calibration'), label: 'What confidence means' },
    },
    {
      key: 'allocation',
      label: 'See your allocation',
      title: 'Current and proposed, side by side.',
      body: 'Every chart says which portfolio it shows. Slate is what you hold; indigo is what the model proposes for your risk profile and your views.',
      demo: <AllocationDemo product={product} sample={sample} />,
      tool: { to: appPath(s, 'portfolio'), label: 'Open Portfolio' },
      doc: { to: docPath(s, 'setup', 'how-hone-works', 'part-3--reweighting-and-hedging-honeoptimization-honehedging'), label: 'How weights are computed' },
    },
    {
      key: 'change',
      label: 'Understand each change',
      title: 'Every change comes with its reason.',
      body: 'For each position: what changes, what it means in dollars, which belief or limit drove it, and whether a position cap was binding.',
      demo: <ChangeDemo product={product} sample={sample} />,
      tool: { to: appPath(s, 'portfolio'), label: 'See every change' },
      doc: { to: publicPath(s, 'how-it-works'), label: 'Reading an explanation' },
    },
    {
      key: 'test',
      label: 'Test the result',
      title: 'Stress it before you trust it.',
      body: 'See the portfolio in historical-style crashes, its tail risk, and a backtest that includes what happens when a real person panics and sells.',
      demo: <TestDemo product={product} sample={sample} />,
      tool: { to: appPath(s, 'hedging'), label: 'Open Hedging' },
      doc: { to: publicPath(s, 'backtests'), label: 'All backtests' },
    },
  ];
  return <FeatureTabs tabs={tabs} />;
}

/** A real, unsaved run of the adaptive questionnaire (first three questions). */
function RiskDemo({ product }) {
  const DEMO_QUESTIONS = 3;
  const [answers, setAnswers] = useState([]);
  const [res, setRes] = useState(null);
  const [error, setError] = useState(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let alive = true;
    api(product.assetClass, '/api/dose', { answers })
      .then(r => { if (alive) { setRes(r); setError(null); } })
      .catch(e => alive && setError(e));
    return () => { alive = false; };
  }, [answers, retry, product.assetClass]);

  if (error) return <ErrorNotice error={error} onRetry={() => setRetry(n => n + 1)} />;
  if (!res) return <SkeletonRows rows={6} />;
  const st = res.state;
  const done = answers.length >= DEMO_QUESTIONS || res.finished;
  return (
    <div className="stack">
      <div className="row row--between">
        <span className="small strong">Risk profile · Question {Math.min(answers.length + 1, res.question?.total ?? 8)} of {res.question?.total ?? 8}</span>
        <Badge>Try it — nothing is saved</Badge>
      </div>
      {!done && res.question ? (
        <div className="grid-2" style={{ gap: 12 }}>
          {['A', 'B'].map(k => (
            <button
              key={k}
              type="button"
              className="choice"
              style={{ padding: 16 }}
              onClick={() => setAnswers(a => [...a, { question_id: res.question.question_id, choice: k }])}
            >
              <span className="choice__tag">Option {k}</span>
              <span className="choice__main" style={{ display: 'block', fontSize: 17 }}>
                {k === 'A' ? res.question.option_a : res.question.option_b}
              </span>
            </button>
          ))}
        </div>
      ) : (
        <p className="small muted">
          That’s the idea. The full assessment takes eight questions.{' '}
          <Link to={appPath(product.slug, 'risk')}>Continue in the workspace →</Link>
        </p>
      )}
      <div>
        <div className="small">
          Estimate so far: <b className="num">{fmtGamma(st.gamma)}</b>{' '}
          <span className="muted">({st.tier.category.toLowerCase()}), likely between {fmtGamma(st.gamma_ci90[0])} and {fmtGamma(st.gamma_ci90[1])}</span>
        </div>
        <DensityChart grid={st.gamma_grid} density={st.gamma_marginal} ci={st.gamma_ci90} mark={st.gamma} height={120} />
        <p className="chart-caption">Shaded: the 90% range for your risk-aversion coefficient. It narrows with each answer.</p>
      </div>
    </div>
  );
}

/** The structured sentence a thesis is built from. Illustration only. */
function ViewsDemo({ product }) {
  const ex = product.example;
  return (
    <div className="stack">
      <div className="flow-labels" aria-hidden="true">
        <span>Asset</span><Icon name="ArrowRight01Icon" size={12} />
        <span>Belief</span><Icon name="ArrowRight01Icon" size={12} />
        <span>Horizon</span><Icon name="ArrowRight01Icon" size={12} />
        <span>Confidence</span>
      </div>
      <div className="sentence-chips">
        <span className="chip">{short(ex.ticker)}</span> reaches
        <span className="chip">a price target</span> within
        <span className="chip">{fmtHorizon(ex.horizonDays)}</span>, and I’m
        <span className="chip">{fmtPct(ex.confidence)} confident</span>
      </div>
      <table className="mt-3">
        <tbody>
          <tr><td className="strong">Reference price</td><td className="muted">Shown beside your target, with when it was fetched.</td></tr>
          <tr><td className="strong">Implied change</td><td className="muted">Calculated for you from the reference price.</td></tr>
          <tr><td className="strong">Confidence</td><td className="muted">The chance you’d give that the price is at or beyond your target when the horizon ends — and how far the model leans toward your view.</td></tr>
          <tr><td className="strong">More view types</td><td className="muted">“A 1-in-3 chance it falls 20%”, “A beats B”, volatility and conditional views.</td></tr>
        </tbody>
      </table>
    </div>
  );
}

/** The hero's allocation, reused. */
function AllocationDemo({ product, sample }) {
  if (!sample?.weights) return <SkeletonRows rows={6} />;
  const rows = sample.weights.map(w => ({ symbol: short(w.symbol), current: w.current, target: w.target })).sort((a, b) => b.current - a.current);
  return (
    <div className="stack">
      <div className="row row--between">
        <span className="small strong">Sample portfolio</span>
        <Badge tone="sample">Sample data</Badge>
      </div>
      <AllocationBars rows={rows} highlight={short(product.example.ticker)} />
      <div className="grid-2" style={{ gap: 12 }}>
        <Stat size="sm" label="Expected return (model, per year)" value={fmtSPct(sample.expected_return)} />
        <Stat size="sm" label="Volatility (per year)" value={fmtPct(sample.volatility)} />
      </div>
      <p className="tiny subtle">Model-proposed allocation for a sample risk profile and one sample thesis. Not a recommendation.</p>
    </div>
  );
}

/** One proposed change, expanded into its explanation. */
function ChangeDemo({ product, sample }) {
  const ex = product.example;
  const row = sample?.weights?.find(w => w.symbol === ex.ticker);
  if (!row) return <SkeletonRows rows={6} />;
  const view = sample.views?.find(v => v.ticker === ex.ticker);
  const capped = row.target >= SAMPLE_MAX_WEIGHT - 1e-4;
  return (
    <div className="stack">
      <div className="row row--between">
        <span className="strong">{short(ex.ticker)}</span>
        <span className="row" style={{ gap: 6 }}>
          <Badge tone="current">Now {fmtPct(row.current)}</Badge>
          <Badge tone="proposed">Proposed {fmtPct(row.target)}</Badge>
        </span>
      </div>
      <div className="grid-2" style={{ gap: 12 }}>
        <Stat size="sm" label="Dollar change" value={fmtSMoney(row.trade * DEMO_VALUE)} note={`On the ${fmtMoney(DEMO_VALUE)} sample portfolio`} />
        <Stat size="sm" label="Main driver" value={view ? 'Your thesis' : 'Risk profile'} note={view ? `${fmtPrice(view.current_price)} → ${fmtPrice(view.target_price)}` : 'No view on this asset'} />
      </div>
      <p className="small muted" style={{ borderLeft: '3px solid var(--proposed)', paddingLeft: 12 }}>{row.reason}</p>
      {capped ? (
        <p className="small"><Badge tone="stale">Limit binding</Badge> The {fmtPct(SAMPLE_MAX_WEIGHT)} maximum position size capped this position.</p>
      ) : (
        <p className="small subtle">No position limit was binding for this asset.</p>
      )}
    </div>
  );
}

/** Stress scenarios from the same sample run. */
function TestDemo({ product, sample }) {
  const scen = sample?.hedge_plan?.scenarios;
  if (!scen) return <SkeletonRows rows={5} />;
  return (
    <div className="stack">
      <p className="takeaway">How the sample portfolio would fare in three historical-style market shocks.</p>
      <div className="tscroll">
        <table>
          <thead><tr><th>Scenario</th><th className="r">Market move</th><th className="r">Portfolio loss</th></tr></thead>
          <tbody>
            {scen.map(sc => (
              <tr key={sc.name}>
                <td>{sc.name}</td>
                <td className="r">{fmtSPct(sc.market_shock, 0)}</td>
                <td className="r loss">{fmtSMoney(sc.loss_usd)} <span className="subtle">({fmtSPct(sc.loss_fraction, 0)})</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="chart-caption">Stress test on a {fmtMoney(DEMO_VALUE)} sample portfolio, using each asset’s sensitivity to {product.marketName}. A scenario, not a forecast.</p>
      <Link to={appPath(product.slug, 'backtest')} className="small">Run a historical backtest on your own inputs →</Link>
    </div>
  );
}

/* ------------------------------------------------------ Prediction Markets */
function PMFeatureTabs({ product, sample }) {
  const s = product.slug;
  const tabs = [
    {
      key: 'exposure',
      label: 'Describe the exposure',
      title: 'Start with the income you already carry.',
      body: 'How much you expect to have over the season, and how much a bad one would cost. Seasonal income, commissions, freelance bookings or business revenue all work the same way.',
      demo: <PMExposureDemo sample={sample} />,
      tool: { to: appPath(s, 'hedge'), label: 'Describe yours' },
      doc: { to: docPath(s, 'methodology', 'prediction-markets', '1-the-problem-in-hones-own-terms'), label: 'The idea in detail' },
    },
    {
      key: 'contract',
      label: 'Pick a related contract',
      title: 'Find an event that moves with your income.',
      body: 'Browse event contracts grouped by the kind of work they relate to. The side that pays in your bad season is the hedge.',
      demo: <PMContractDemo product={product} />,
      tool: { to: appPath(s, 'markets'), label: 'Browse markets' },
      doc: { to: docPath(s, 'methodology', 'prediction-markets', '8-the-market-catalog-and-its-data'), label: 'About the catalog' },
    },
    {
      key: 'compare',
      label: 'Compare outcomes',
      title: 'Your season, with and without cover.',
      body: 'The central picture: money at the end of a bad season and a normal one, after the contract’s cost and fees.',
      demo: sample?.data ? (
        <div className="stack">
          <div className="alloc__legend" aria-hidden="true">
            <span><i className="alloc__swatch alloc__swatch--current" /> Without hedge</span>
            <span><i className="alloc__swatch alloc__swatch--proposed" /> With hedge</span>
          </div>
          <OutcomeBars rows={outcomeRows(sample.data)} />
          <p className="chart-caption">Illustrative sample. Money at season’s end, in dollars, after costs and fees.</p>
        </div>
      ) : <SkeletonRows rows={5} />,
      tool: { to: appPath(s, 'hedge'), label: 'Open Income hedge' },
      doc: { to: docPath(s, 'methodology', 'prediction-markets', '3-the-answer-always-splits-into-insurance-and-a-bet'), label: 'Insurance vs. bet' },
    },
    {
      key: 'basis',
      label: 'Mind the basis',
      title: 'Your loss and the contract are not the same event.',
      body: 'A contract settles on its own rule — inches of snow at one station, one official number. Your income depends on more than that. The weaker the link, the less cover the contract really buys.',
      demo: <PMBasisDemo product={product} sample={sample} />,
      tool: { to: appPath(s, 'hedge'), label: 'Set the basis' },
      doc: { to: docPath(s, 'methodology', 'prediction-markets', '4-basis-risk'), label: 'Basis risk' },
    },
    {
      key: 'cost',
      label: 'Check the cost',
      title: 'What the cover costs, and what it’s worth to you.',
      body: 'Hone separates the price you pay from the most someone with your risk tolerance should pay, so you can see when cover is good value and when it isn’t.',
      demo: <PMCostDemo sample={sample} />,
      tool: { to: appPath(s, 'hedge'), label: 'Open Income hedge' },
      doc: { to: docPath(s, 'methodology', 'prediction-markets', '6-what-the-hedge-is-worth-and-the-most-to-pay-for-it'), label: 'Pricing the cover' },
    },
  ];
  return <FeatureTabs tabs={tabs} />;
}

function PMExposureDemo({ sample }) {
  const inp = sample?.inputs || { wealth: PM_SAMPLE.wealth, loss: PM_SAMPLE.loss };
  return (
    <div className="stack">
      <div className="row row--between">
        <span className="small strong">Your exposure</span>
        <Badge tone="sample">Illustrative</Badge>
      </div>
      <table>
        <tbody>
          <tr><td className="strong">Kind of income</td><td>Seasonal — ski instruction</td></tr>
          <tr><td className="strong">Money over the season</td><td className="num">{fmtMoney(inp.wealth)} <span className="subtle">(earnings plus savings a bad season would eat)</span></td></tr>
          <tr><td className="strong">What could go wrong</td><td>Low snowfall cuts teaching days</td></tr>
          <tr><td className="strong">Cost of a bad season</td><td className="num loss">{fmtSMoney(-inp.loss)}</td></tr>
        </tbody>
      </table>
    </div>
  );
}

/** Shows one real contract from the catalog (snapshot or live), clearly dated. */
function PMContractDemo({ product }) {
  const [cat, setCat] = useState(null);
  const [error, setError] = useState(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let alive = true;
    api(product.assetClass, '/api/predict/markets').then(d => alive && setCat(d)).catch(e => alive && setError(e));
    return () => { alive = false; };
  }, [retry, product.assetClass]);
  if (error) return <ErrorNotice error={error} onRetry={() => setRetry(n => n + 1)} />;
  if (!cat) return <SkeletonRows rows={6} />;
  // First series in the catalog that has a listed market.
  let pick = null;
  for (const ind of cat.industries) {
    for (const se of ind.series) {
      if (se.markets?.length) { pick = { ind, se, m: se.markets[0] }; break; }
    }
    if (pick) break;
  }
  if (!pick) return <p className="muted">No markets are listed in the catalog right now.</p>;
  const { ind, se, m } = pick;
  return (
    <div className="stack">
      <div className="row row--between">
        <span className="small strong">{ind.label}</span>
        <Badge tone={cat.source === 'snapshot' ? 'sample' : 'live'}>
          {cat.source === 'snapshot' ? `Snapshot · ${fmtDate(cat.as_of)}` : `Live · ${fmtDate(cat.as_of)}`}
        </Badge>
      </div>
      <div>
        <div className="strong">{m.title}</div>
        <div className="tiny subtle mt-1">{se.title} · closes {fmtDate(m.close_time)}</div>
      </div>
      <div className="grid-2" style={{ gap: 12 }}>
        <Stat size="sm" label="YES ask" value={fmtCents(m.yes_ask)} />
        <Stat size="sm" label="NO ask" value={fmtCents(m.no_ask)} />
      </div>
      <p className="small muted"><b>Hedge side:</b> {se.bad_side}. {se.note}</p>
      {m.rules && <p className="tiny subtle">Settlement rule: {m.rules}</p>}
    </div>
  );
}

/** Same sample, sized at a perfect link (1.0) vs a looser one (0.6). */
function PMBasisDemo({ product, sample }) {
  const [loose, setLoose] = useState(null);
  const [error, setError] = useState(null);
  const inputs = sample?.inputs;
  useEffect(() => {
    if (!inputs) return undefined;
    let alive = true;
    api(product.assetClass, '/api/predict/hedge', { ...inputs, basis_correlation: 0.6 })
      .then(d => alive && setLoose(d))
      .catch(e => alive && setError(e));
    return () => { alive = false; };
  }, [inputs, product.assetClass]);
  if (error) return <ErrorNotice error={error} />;
  if (!sample?.data || !loose) return <SkeletonRows rows={5} />;
  return (
    <div className="stack">
      <div className="grid-2" style={{ gap: 12 }}>
        <div className="card card--sunk">
          <Stat size="sm" label="Contract tracks your loss exactly" value={`${fmtNum(sample.data.contracts)} contracts`} note={`Cost ${fmtMoney(sample.data.cost + sample.data.fee)}`} />
        </div>
        <div className="card card--sunk">
          <Stat size="sm" label="Loosely related (correlation 0.6)" value={`${fmtNum(loose.contracts)} contracts`} note={`Cost ${fmtMoney(loose.cost + loose.fee)}`} />
        </div>
      </div>
      <p className="small muted">
        <b>Your loss event:</b> fewer teaching days. <b>The contract’s settlement condition:</b> measured snowfall at one place
        by one date. They usually move together — not always.
      </p>
    </div>
  );
}

function PMCostDemo({ sample }) {
  const r = sample?.data;
  if (!r) return <SkeletonRows rows={5} />;
  return (
    <div className="stack">
      <div className="grid-2" style={{ gap: 12 }}>
        <Stat size="sm" label="You pay per contract" value={fmtCents(r.price)} />
        <Stat size="sm" label="Most worth paying, for you" value={fmtCents(r.reservation_price)} />
        <Stat size="sm" label="Total cost incl. fees" value={fmtMoney(r.cost + r.fee)} />
        <Stat size="sm" label="Worth to you (certain dollars)" value={fmtSMoney(r.ce_gain)} />
      </div>
      <p className="small muted">
        “Worth to you” is the certainty-equivalent gain: how many guaranteed dollars the smoother season is worth at your
        risk tolerance, after paying for it. Expected money goes {r.expected_wealth_hedged < r.expected_wealth_unhedged ? 'down' : 'up'} by{' '}
        {fmtMoney(Math.abs(r.expected_wealth_hedged - r.expected_wealth_unhedged))} — that is the price of cover.
      </p>
    </div>
  );
}

/* ========================================================================== */
/* Launch cards — React Bits SpotlightCard                                    */
/* ========================================================================== */
function LaunchCards({ product }) {
  const s = product.slug;
  const cards = s === 'prediction-markets'
    ? [
      { icon: 'Target02Icon', title: 'Understand my risk', body: 'Eight choices estimate how much uncertainty you’re willing to carry. It sets how much cover is worth buying.', to: appPath(s, 'risk') },
      { icon: 'Shield01Icon', title: 'Size a hedge', body: 'Describe a bad season, pick a contract, and compare your income with and without it.', to: appPath(s, 'hedge') },
      { icon: 'Store01Icon', title: 'Browse markets', body: 'Event contracts grouped by the work they relate to — snow, ads, hiring, housing, travel, prices.', to: appPath(s, 'markets') },
    ]
    : [
      { icon: 'Target02Icon', title: 'Understand my risk', body: 'Measure your risk aversion with an adaptive questionnaire, and see what the estimate changes in a portfolio.', to: appPath(s, 'risk') },
      { icon: 'BulbIcon', title: 'Add an investment thesis', body: `Write down what you believe about the ${product.assetWord} you follow, and see how far the model leans toward it.`, to: appPath(s, 'theses') },
      { icon: 'Shield01Icon', title: 'Explore hedging', body: 'Stress scenarios, tail risk and hedges sized to the losses you said you could stomach.', to: appPath(s, 'hedging') },
    ];
  return (
    <div className="launch-grid">
      {cards.map((c, i) => (
        <Reveal key={c.title} delay={i * 0.06}>
          <div className="launch">
            <div className="launch__icon"><Icon name={c.icon} size={20} /></div>
            <h3><Link to={c.to} className="stretched">{c.title}</Link></h3>
            <p>{c.body}</p>
            <span className="launch__go" aria-hidden="true">Open <Icon name="ArrowRight01Icon" size={16} /></span>
          </div>
        </Reveal>
      ))}
    </div>
  );
}

/* ========================================================================== */
/* The problem & FAQ                                                          */
/* ========================================================================== */
function Problem({ product }) {
  const items = product.slug === 'prediction-markets'
    ? [
      { t: 'Your income is a position you never chose.', b: 'A ski instructor is long snowfall; a recruiter is long hiring. Nobody sizes that exposure — it just happens to you.' },
      { t: 'Insurance doesn’t cover a bad season.', b: 'Policies pay for accidents and damage, not for a dry winter or a slow quarter for ad budgets.' },
      { t: 'The contracts exist; sizing them is hard.', b: 'Too few and the cover is cosmetic. Too many and the hedge turns into a bet. Hone shows exactly where that line is for you.' },
    ]
    : [
      { t: 'Risk quizzes end in a label.', b: 'Three questions, a “moderate” sticker, and nothing downstream actually uses it. Hone measures a number and every result answers to it.' },
      { t: 'Beliefs and position sizes never meet.', b: `What you think about a ${product.assetSingular} lives in your head; how much you hold lives in a brokerage. Nothing links how sure you are to how much you own.` },
      { t: 'Spreadsheets can’t explain themselves.', b: 'When a number moves you can’t see which assumption moved it. In Hone, every proposed change names its driver.' },
    ];
  return (
    <div className="problem">
      {items.map((it, i) => (
        <Reveal key={it.t} delay={i * 0.06}>
          <h3>{it.t}</h3>
          <p>{it.b}</p>
        </Reveal>
      ))}
    </div>
  );
}

function Faq({ product }) {
  const s = product.slug;
  const isPM = s === 'prediction-markets';
  const items = [
    {
      q: 'Is this real money?',
      a: (
        <>
          No. Hone runs on sample data or an Alpaca <em>paper-trading</em> account, and it never places trades for you
          {isPM ? ' — for prediction markets it holds no exchange keys at all and only sizes the position' : ''}. It is an
          educational research tool, not investment advice.
        </>
      ),
    },
    ...(isPM
      ? [{
        q: 'Isn’t this just gambling?',
        a: (
          <>
            A bet adds a risk you didn’t have. A hedge offsets one you already carry. Hone splits every position into the
            insurance part (sized to your loss) and any bet part (from your own view versus the market’s), and shows both
            separately. With no view of your own, it sizes cover only.{' '}
            <Link to={docPath(s, 'methodology', 'prediction-markets', '3-the-answer-always-splits-into-insurance-and-a-bet')}>Read the reasoning</Link>.
          </>
        ),
      }]
      : []),
    {
      q: 'Is the proposed allocation a recommendation?',
      a: (
        <>
          No. It is what one model proposes given your risk estimate and your stated views. A different model — or the same
          one with nearby inputs — can propose something different, and Hone shows when a result is sensitive or limited by a
          position cap. “Hold none of this” means none <em>under this model and these inputs</em>.
        </>
      ),
    },
    {
      q: 'Where do the numbers come from?',
      a: (
        <>
          Sample mode uses synthetic prices so you can explore safely; it is labelled everywhere. With your own Alpaca paper
          account, prices and holdings come from Alpaca. Every method is documented in full on the{' '}
          <Link to={publicPath(s, 'methodology')}>Methodology</Link> page{isPM ? '' : <>, and every experiment on <Link to={publicPath(s, 'backtests')}>Backtests</Link></>}.
        </>
      ),
    },
    {
      q: 'Do I need an account?',
      a: 'No. Everything saves in this browser. Sign in only if you want to keep portfolios across devices.',
    },
  ];
  return (
    <div className="faq">
      {items.map(it => (
        <details key={it.q}>
          <summary>{it.q} <Icon name="ArrowRight01Icon" size={18} className="chev" /></summary>
          <div className="faq__a">{it.a}</div>
        </details>
      ))}
    </div>
  );
}
