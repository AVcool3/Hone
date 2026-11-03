/*
 * HowItWorks — the complete user journey for one product.
 *
 * For each workspace tool: what you put in, what you get out, a link to the
 * tool itself and a link to its full methodology. Then a worked example,
 * the definition of "confidence", and how to read a proposed change.
 *
 * The tools are independent — the numbering is a suggested order, not a
 * required one. EDIT the STEPS arrays below to change the copy.
 */
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import { Button } from '../../components/ui.jsx';
import { appPath, docPath, publicPath } from '../../lib/products.js';
import { fmtHorizon, fmtPct } from '../../lib/format.js';
import './marketing.css';

/* -------------------------------------------------------- Stocks & Crypto */
function portfolioSteps(p) {
  const s = p.slug;
  const isCrypto = s === 'crypto';
  return [
    {
      title: 'Risk aversion',
      intro: 'How much uncertainty you are willing to carry for a higher expected return. Every other tool uses it.',
      input: 'Eight either/or choices between a sure amount and a gamble — or the classic 30-question menu, or set the number directly to explore.',
      output: 'An estimate of your risk-aversion coefficient with its uncertainty range, a plain-language description, and how the way you actually invest compares.',
      tool: appPath(s, 'risk'),
      docs: [{ to: docPath(s, 'methodology', 'risk-elicitation'), label: 'Measuring risk aversion' }],
    },
    {
      title: 'Investment theses',
      intro: `What you believe about the ${p.assetWord} you follow, written so a model can use it.`,
      input: 'An asset, a target price, a horizon and your confidence, plus your reasoning in words. Or type a sentence and let the compiler draft the fields. Other shapes of belief (“a 1-in-3 chance it falls 20%”, “A beats B”) live under More view types.',
      output: 'Editable thesis cards showing the reference price, when it was fetched, and the implied change. Conflicting views are flagged; any thesis can be switched off to compare.',
      tool: appPath(s, 'theses'),
      docs: [
        { to: docPath(s, 'methodology', 'calibration'), label: 'What confidence means' },
        { to: docPath(s, 'methodology', 'flexible-views'), label: 'More view types' },
      ],
    },
    {
      title: 'Portfolio',
      intro: 'Where your risk profile and your theses meet what you hold.',
      input: `Your holdings (sample, or your ${p.account}), your risk estimate, the theses you’ve included, and portfolio limits such as the maximum position size.`,
      output: 'Current versus model-proposed weights, the dollar change for each position, the reason for each change, and how your views moved each asset’s expected return.',
      tool: appPath(s, 'portfolio'),
      docs: [{ to: docPath(s, 'setup', 'how-hone-works', 'part-3--reweighting-and-hedging-honeoptimization-honehedging'), label: 'How weights are computed' }],
    },
    {
      title: 'Hedging',
      intro: 'What the portfolio could lose, and what it would take to bring that within what you said you could stomach.',
      input: 'Your risk estimate and the portfolio.',
      output: `Historical-style stress scenarios in dollars, the tail of the return distribution (average loss in the worst months), and hedges sized to the gap. ${isCrypto ? 'For crypto: a stablecoin allocation and a short of the market proxy.' : 'Hedges include more cash, an index short and option overlays.'}`,
      tool: appPath(s, 'hedging'),
      docs: [{ to: docPath(s, 'methodology', 'tail-risk'), label: 'Tail risk (CVaR)' }],
    },
    {
      title: 'Track record',
      intro: 'A decision journal that scores your confidence against what actually happened.',
      input: 'Theses you choose to log. Each is frozen at the price and time you committed — nothing is reconstructed afterwards.',
      output: 'Open and resolved predictions, a reliability check (“does 70% mean 70%?”), and — once enough have resolved — a map that can rescale your future confidence. You can also export your record as training data.',
      tool: appPath(s, 'record'),
      docs: [
        { to: docPath(s, 'methodology', 'calibration'), label: 'Scoring & calibration' },
        { to: docPath(s, 'methodology', 'qlora'), label: 'Tuning a model on your record' },
      ],
    },
    {
      title: 'Backtest',
      intro: 'How a risk-matched portfolio would have behaved over recent history.',
      input: 'Your risk estimate and the assets in the portfolio.',
      output: 'Equity curves against simple benchmarks, drawdowns, and the behaviour gap: the same strategies held by someone allowed to panic and sell.',
      tool: appPath(s, 'backtest'),
      docs: [
        { to: publicPath(s, 'backtests'), label: 'Research backtests' },
        { to: docPath(s, 'backtests', 'behavior-gap'), label: 'The behaviour gap' },
      ],
    },
    {
      title: 'Data & account',
      intro: 'Where the numbers come from, and where your work is saved.',
      input: `Nothing, to start: sample data is the default. Optionally, keys for your ${p.account}, and an email to sign in.`,
      output: 'A clear label on every screen saying whether you’re looking at sample data or your own account. Work saves in this browser; signing in keeps it across devices.',
      tool: appPath(s, 'settings'),
      docs: [{ to: publicPath(s, 'setup'), label: 'Setup' }],
    },
  ];
}

/* -------------------------------------------------------- Prediction Markets */
function predictionSteps(p) {
  const s = p.slug;
  return [
    {
      title: 'Describe the income exposure',
      intro: 'Pick the kind of income that worries you: seasonal work, commissions, freelance bookings, business revenue, or something else.',
      input: 'The money you’ll have over the horizon — earnings plus the savings a bad season would eat.',
      output: 'A starting point, and a short list of market groups related to that kind of work.',
      tool: appPath(s, 'hedge'),
      docs: [{ to: docPath(s, 'methodology', 'prediction-markets', '1-the-problem-in-hones-own-terms'), label: 'The problem' }],
    },
    {
      title: 'Specify what could go wrong',
      intro: 'Name the bad outcome in your own terms and put a dollar figure on it.',
      input: 'What a bad season would cost you. Optionally, your own probability that it happens and how sure you are of it.',
      output: 'The risk Hone will size cover against. With no view of your own, it uses the market’s probability.',
      tool: appPath(s, 'hedge'),
      docs: [{ to: docPath(s, 'methodology', 'prediction-markets', '5-the-users-view-against-the-market'), label: 'Your view vs. the market' }],
    },
    {
      title: 'Review a related contract',
      intro: 'Choose an event contract whose bad side tends to happen when your bad season does.',
      input: 'A market from the catalog (or a price you enter for an illustrative contract).',
      output: 'The contract’s exact settlement rule, its price on the hedge side, its closing date, and whether the data is a dated snapshot or live.',
      tool: appPath(s, 'markets'),
      docs: [{ to: docPath(s, 'methodology', 'prediction-markets', '8-the-market-catalog-and-its-data'), label: 'The catalog and its data' }],
    },
    {
      title: 'Compare outcomes with and without the hedge',
      intro: 'The central picture: money at the end of a bad season and a normal one, after the contract’s cost and fees.',
      input: 'Your risk estimate and everything above.',
      output: 'How many contracts, the cost, the worst case with and without cover, and how much smoother the season gets.',
      tool: appPath(s, 'hedge'),
      docs: [{ to: docPath(s, 'methodology', 'prediction-markets', '3-the-answer-always-splits-into-insurance-and-a-bet'), label: 'Insurance vs. bet' }],
    },
    {
      title: 'Inspect cost, remaining exposure and assumptions',
      intro: 'Whether the cover is worth its price to someone with your risk tolerance — and what it leaves uncovered.',
      input: 'How closely the contract tracks your loss (the basis).',
      output: 'The most it is worth paying per contract, the value of the hedge in certain dollars, the insurance and bet parts of the position shown separately, and warnings where an assumption is doing a lot of work.',
      tool: appPath(s, 'hedge'),
      docs: [
        { to: docPath(s, 'methodology', 'prediction-markets', '6-what-the-hedge-is-worth-and-the-most-to-pay-for-it'), label: 'Pricing the cover' },
        { to: docPath(s, 'methodology', 'prediction-markets', '4-basis-risk'), label: 'Basis risk' },
      ],
    },
  ];
}

/* ========================================================================== */
export default function HowItWorks() {
  const product = useProduct();
  const isPM = product.slug === 'prediction-markets';
  const steps = isPM ? predictionSteps(product) : portfolioSteps(product);

  return (
    <>
      <div className="container docs-head">
        <div className="eyebrow mb-2">{product.brand}</div>
        <h1>How it works</h1>
        <p className="lede mt-3">
          {isPM
            ? 'Five steps from “a bad season would hurt” to a sized, explained hedge. Each step lives in the workspace and can be revisited in any order.'
            : 'Seven independent tools. Open any of them directly — the numbers are a suggested order, not a required one. Missing inputs fall back to clearly labelled samples.'}
        </p>
      </div>

      <section className="container section--tight">
        <div className="journey">
          {steps.map((st, i) => (
            <div key={st.title} className="journey__step">
              <div className="journey__num">{i + 1}</div>
              <div>
                <h3>{st.title}</h3>
                <p className="muted mt-1">{st.intro}</p>
                <div className="journey__io">
                  <div><div className="eyebrow">You put in</div>{st.input}</div>
                  <div><div className="eyebrow">You get</div>{st.output}</div>
                </div>
                <div className="journey__links">
                  <Button size="sm" variant="secondary" to={st.tool} iconRight="ArrowRight01Icon">Open it</Button>
                  {st.docs.map(d => <Button key={d.label} size="sm" variant="text" to={d.to}>{d.label}</Button>)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {isPM ? <PredictionDetails product={product} /> : <PortfolioDetails product={product} />}

      <section className="container section--tight center">
        <div className="row" style={{ justifyContent: 'center' }}>
          <Button size="lg" to={isPM ? appPath(product.slug, 'hedge') : appPath(product.slug)} iconRight="ArrowRight01Icon">
            {isPM ? 'Size a sample hedge' : 'Explore a sample portfolio'}
          </Button>
          <Button size="lg" variant="secondary" to={publicPath(product.slug, 'methodology')}>Read the methodology</Button>
        </div>
      </section>
    </>
  );
}

/* -------------------------------------------------------------------------- */
function PortfolioDetails({ product }) {
  const s = product.slug;
  const ex = product.example;
  const sym = ex.ticker.replace('/USD', '');
  return (
    <>
      <section className="container section--tight">
        <h2 className="section-title mb-4">A worked example</h2>
        <p className="muted mb-4 prose">The sample workspace runs exactly this, on sample prices. Numbers depend on the day’s sample data, so they are described rather than quoted.</p>
        <div className="tscroll">
          <table className="example-table">
            <thead><tr><th>Tool</th><th>What you do</th><th>What you see</th></tr></thead>
            <tbody>
              <tr><td>Risk aversion</td><td>Answer eight choices.</td><td>An estimate and a range — say, “moderately risk-averse, probably between 1.5 and 3”.</td></tr>
              <tr><td>Theses</td><td>Write: {sym} reaches about 20% above today’s price within {fmtHorizon(ex.horizonDays)}, {fmtPct(ex.confidence)} confident.</td><td>The reference price and its timestamp, the target, and the implied change.</td></tr>
              <tr><td>Portfolio</td><td>Press Recalculate.</td><td>{sym}’s weight rises from its current share toward the cap; positions with weaker expected returns for their risk are trimmed — each with its reason and dollar change.</td></tr>
              <tr><td>Theses</td><td>Lower the confidence to 30%, or switch the thesis off.</td><td>The Portfolio result is marked “Needs recalculation”. Recalculate: the tilt toward {sym} shrinks or disappears.</td></tr>
              <tr><td>Hedging</td><td>Open it.</td><td>Losses in three historical-style crashes, the average loss in the worst months, and whether a hedge is needed for your risk estimate.</td></tr>
              <tr><td>Track record</td><td>Slide to log the thesis.</td><td>It’s frozen at today’s price; when the horizon ends, it is scored against what actually happened.</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="container section--tight">
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div className="definition" id="confidence">
            <h3>What “confidence” means</h3>
            <p>
              The chance you would give that the price is <b>at or beyond your target when the horizon ends</b>. That is
              exactly how Hone scores it in your track record.
            </p>
            <p>
              The optimizer uses the same number to decide how far to lean from its neutral starting point toward your view:
              near 100% treats the target as almost certain and concentrates into it; around 30% barely moves the portfolio.
              It is <em>not</em> a measure of how precise the model is — a result can be computed to many decimals and still
              rest on a 40% belief.
            </p>
            <p><Link to={docPath(s, 'methodology', 'calibration')}>Full definition and scoring →</Link></p>
          </div>
          <div className="definition" id="reading-an-explanation" style={{ borderLeftColor: 'var(--proposed)' }}>
            <h3>Reading a proposed change</h3>
            <ul className="muted mt-2" style={{ display: 'grid', gap: 6 }}>
              <li><b>Current → proposed weight:</b> what actually changes, as a share of the portfolio.</li>
              <li><b>Dollar change:</b> what that means for a portfolio of your size.</li>
              <li><b>Main driver:</b> the thesis, risk estimate or limit that caused it.</li>
              <li><b>Limit binding:</b> the maximum position size (or cash requirement) capped the result.</li>
              <li><b>Concentration:</b> a flag when one position dominates.</li>
              <li><b>Needs recalculation:</b> an input changed after this result was calculated.</li>
            </ul>
            <p className="small subtle mt-3">Every figure is labelled model-proposed. “Hold none” means none under this model and these inputs.</p>
          </div>
        </div>
      </section>
    </>
  );
}

/* -------------------------------------------------------------------------- */
function PredictionDetails({ product }) {
  const s = product.slug;
  return (
    <section className="container section--tight">
      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div className="definition" id="basis">
          <h3>Your loss event is not the contract’s settlement condition</h3>
          <p>
            <b>Your loss event</b> is what actually costs you money — fewer teaching days, fewer bookings, smaller
            commissions. <b>The contract’s settlement condition</b> is a precise public rule — snowfall measured at one
            station by one date, one official statistic.
          </p>
          <p>
            They usually move together, but not always: it can snow at the station and not on your mountain. Hone asks how
            closely the two track each other (the basis) and sizes the position down as the link weakens, then shows what is
            left uncovered.
          </p>
          <p><Link to={docPath(s, 'methodology', 'prediction-markets', '4-basis-risk')}>Basis risk in detail →</Link></p>
        </div>
        <div className="definition" style={{ borderLeftColor: 'var(--proposed)' }}>
          <h3>Insurance first, then any bet</h3>
          <p>
            Every position splits into two parts. The <b>insurance</b> part is sized to your loss and your risk tolerance. A
            <b> bet</b> part appears only if your own probability differs from the market’s. Hone shows both, so a hedge can
            never quietly become a wager.
          </p>
          <p>
            Your confidence in your own probability works like it does for stock views — and if you have a track record, it can
            be rescaled by it. <Link to={docPath(s, 'methodology', 'calibration')}>What confidence means →</Link>
          </p>
          <p className="small subtle">Examples on this site are illustrative unless marked live; the catalog shows the date its prices were taken.</p>
        </div>
      </div>
    </section>
  );
}
