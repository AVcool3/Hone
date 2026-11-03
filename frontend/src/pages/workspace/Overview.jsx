/*
 * Workspace Overview — "where am I, and what should I look at next?"
 *
 *   1. Summary row: four numbers, each clearly defined.
 *   2. Launch cards (React Bits SpotlightCard) into the three core tools.
 *   3. Current vs. model-proposed allocation (computed on first visit).
 *   4. Active theses and suggested next steps.
 *
 * The Prediction Markets product has its own, simpler overview below.
 */
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import SpotlightCard from '../../reactbits/SpotlightCard/SpotlightCard.jsx';
import AllocationBars from '../../components/AllocationBars.jsx';
import Icon from '../../components/Icon.jsx';
import { Badge, Button, ErrorNotice, Notice, PageHeader, SectionTitle, SkeletonRows, StaleBanner, Stat } from '../../components/ui.jsx';
import { appPath, docPath } from '../../lib/products.js';
import { useOptimize } from '../../lib/hooks.js';
import { useRisk, useWorkspace, validThesis } from '../../lib/store.jsx';
import { fmtGamma, fmtHorizon, fmtMoney, fmtPct, fmtPrice, fmtSPct, impliedChange } from '../../lib/format.js';

/** One launch card. The whole card is a link (keyboard focusable). */
export function LaunchCard({ to, icon, title, body, cta }) {
  return (
    <Link to={to}>
      <SpotlightCard theme="light" spotlightColor="#7c5cc4" intensity={0.12} spotlightSize={280} borderGlow={0.45} proximity={60}>
        <div className="ws-launch__icon"><Icon name={icon} size={20} /></div>
        <div className="ws-launch__title">{title}</div>
        <p className="ws-launch__body">{body}</p>
        <span className="ws-launch__go">{cta} <Icon name="ArrowRight01Icon" size={16} /></span>
      </SpotlightCard>
    </Link>
  );
}

export default function Overview() {
  const product = useProduct();
  if (product.slug === 'prediction-markets') return <PredictionOverview />;
  return <PortfolioOverview product={product} />;
}

function PortfolioOverview({ product }) {
  const slug = product.slug;
  const { ws } = useWorkspace(slug);
  const risk = useRisk();
  const opt = useOptimize(slug, { auto: true });
  const r = opt.result;
  const value = r?.hedge_plan?.portfolio_value;
  const largest = r ? [...r.weights].sort((a, b) => b.target - a.target)[0] : null;
  const active = ws.theses.filter(t => t.included && validThesis(t));

  return (
    <>
      <PageHeader
        eyebrow={`${product.brand} · Workspace`}
        title="Overview"
        lede="Your risk profile, your investment theses and the allocation they imply — each tool opens on its own, in any order."
      />

      {/* 1. Summary row — four numbers, no more. */}
      <div className="card mb-5">
        <div className="stat-row">
          <Stat label="Portfolio value" value={value ? fmtMoney(value) : '—'} note={ws.dataSource === 'alpaca' ? 'Alpaca paper account' : 'Sample portfolio'} />
          <Stat
            label="Risk aversion"
            value={risk.isSample ? 'Sample' : risk.profile.tier?.category ?? fmtGamma(risk.gamma)}
            note={risk.isSample ? <Link to={appPath(slug, 'risk')}>Measure yours (8 questions)</Link> : `Tier ${risk.profile.tier?.tier} of 50`}
          />
          <Stat label="Active theses" value={active.length} note={`${ws.theses.length - active.length} excluded or incomplete`} />
          <Stat
            label="Largest proposed position"
            value={largest ? `${largest.symbol} ${fmtPct(largest.target)}` : '—'}
            note={largest && largest.target >= ws.maxWeight - 0.001 ? `At your ${fmtPct(ws.maxWeight)} position limit` : 'Model-proposed'}
          />
        </div>
      </div>

      {/* 2. Launch cards */}
      <div className="ws-launch mb-6">
        <LaunchCard to={appPath(slug, 'risk')} icon="Target02Icon" title="Understand my risk"
          body={risk.isSample ? 'Eight either/or choices estimate how much risk you can carry — with its uncertainty.' : 'See your estimate, what it changes, and retake it any time.'}
          cta={risk.isSample ? 'Assess my risk' : 'View my profile'} />
        <LaunchCard to={appPath(slug, 'theses')} icon="BulbIcon" title="Add an investment thesis"
          body={`Say where you think a ${product.assetSingular} is going, by when, and how sure you are. Watch the allocation respond.`}
          cta="Open theses" />
        <LaunchCard to={appPath(slug, 'hedging')} icon="Shield01Icon" title="Explore hedging"
          body="Stress scenarios, tail risk, and the hedges that would bring risk back within your limit."
          cta="Open hedging" />
      </div>

      {/* 3. Current vs proposed */}
      <div className="card mb-5">
        <SectionTitle
          title="Current vs. model-proposed allocation"
          sub={active.length ? `Built from ${active.length} active ${active.length === 1 ? 'thesis' : 'theses'} at ${risk.isSample ? 'a sample' : 'your'} risk level.` : 'No active theses — the model sizes positions on risk alone.'}
          right={<Button variant="secondary" size="sm" to={appPath(slug, 'portfolio')} iconRight="ArrowRight01Icon">Explain each change</Button>}
        />
        {opt.stale && <div className="mb-4"><StaleBanner onRecalc={opt.run} busy={opt.busy} what="this allocation" /></div>}
        <ErrorNotice error={opt.error} onRetry={opt.run} settingsTo={appPath(slug, 'settings')} />
        {!r && opt.busy && <SkeletonRows rows={5} />}
        {r && (
          <>
            <AllocationBars rows={r.weights} />
            <p className="tiny subtle mt-3">
              Model-proposed allocation: what this model suggests given these inputs — not a recommendation.
              Expected return {fmtSPct(r.expected_return)} a year, volatility {fmtPct(r.volatility)} (typical yearly swing).
            </p>
          </>
        )}
      </div>

      {/* 4. Theses and next steps */}
      <div className="grid-2">
        <div className="card">
          <SectionTitle title="Active theses" right={<Button variant="text" to={appPath(slug, 'theses')}>Edit</Button>} />
          {ws.theses.length === 0 && <p className="muted">No theses yet. <Link to={appPath(slug, 'theses')}>Add one</Link> — the allocation updates as you type.</p>}
          <ul className="plain-list">
            {ws.theses.map(t => {
              const chg = impliedChange(t.refPrice, t.target);
              return (
                <li key={t.id} className="row" style={{ justifyContent: 'space-between', opacity: t.included ? 1 : 0.55 }}>
                  <span><b>{t.ticker || 'New thesis'}</b> {t.target ? <>to {fmtPrice(t.target)} {chg != null && <span className="subtle">({fmtSPct(chg)})</span>}</> : <span className="subtle">no target yet</span>}</span>
                  <span className="subtle tiny">{fmtHorizon(t.horizonDays)} · {fmtPct(t.confidence)} confidence {t.sample && <Badge tone="sample">Sample</Badge>}</span>
                </li>
              );
            })}
          </ul>
        </div>
        <div className="card">
          <SectionTitle title="Suggested next steps" />
          <div className="stack">
            {risk.isSample && <Notice tone="attention" title="You’re using a sample risk profile.">Position sizes depend heavily on it. <Link to={appPath(slug, 'risk')}>Assess yours</Link> in about two minutes.</Notice>}
            {ws.theses.some(t => t.sample) && <Notice>The theses marked <b>Sample</b> are illustrations. <Link to={appPath(slug, 'theses')}>Replace them with your own views</Link>.</Notice>}
            {ws.dataSource !== 'alpaca' && <Notice>Prices and holdings are synthetic sample data. <Link to={appPath(slug, 'settings')}>Connect an Alpaca paper account</Link> to use your own.</Notice>}
            {product.volatilityNote && <Notice tone="attention">{product.volatilityNote}</Notice>}
            <p className="tiny subtle">How the numbers are made: <Link to={docPath(slug, 'methodology')}>Methodology</Link> · <Link to={docPath(slug, 'backtests')}>Backtests</Link></p>
          </div>
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ prediction */
function PredictionOverview() {
  const slug = 'prediction-markets';
  const { ws } = useWorkspace(slug);
  const risk = useRisk();
  const pm = ws.pm;
  return (
    <>
      <PageHeader
        eyebrow="Hone Markets · Workspace"
        title="Overview"
        lede="Your paycheck is already a position. Size an event contract that pays when your income takes a hit — and see exactly what it costs."
      />
      <div className="card mb-5">
        <div className="stat-row">
          <Stat label="Money over the season" value={fmtMoney(pm.wealth)} note="Earnings plus savings a bad season would draw on" />
          <Stat label="Loss in a bad season" value={fmtMoney(pm.loss)} note={`${fmtPct(pm.loss / pm.wealth)} of the total`} />
          <Stat label="Contract" value={pm.label || pm.marketTicker || 'Not chosen'} size="sm" note={pm.price ? `${Math.round(pm.price * 100)}¢ per contract` : ''} />
          <Stat label="Risk aversion" value={risk.isSample ? 'Sample' : risk.profile.tier?.category ?? fmtGamma(risk.gamma)} note={risk.isSample ? <Link to={appPath(slug, 'risk')}>Measure yours</Link> : `Tier ${risk.profile.tier?.tier} of 50`} />
        </div>
      </div>
      <div className="ws-launch mb-6">
        <LaunchCard to={appPath(slug, 'risk')} icon="Target02Icon" title="Understand my risk" body="How much certainty is worth to you sets how much cover to buy." cta={risk.isSample ? 'Assess my risk' : 'View my profile'} />
        <LaunchCard to={appPath(slug, 'hedge')} icon="Shield01Icon" title="Size an income hedge" body="Describe the exposure, pick a related contract, compare income with and without the hedge." cta="Open income hedge" />
        <LaunchCard to={appPath(slug, 'markets')} icon="Store01Icon" title="Browse markets" body="Kalshi contracts grouped by the kinds of income they move with." cta="Open markets" />
      </div>
      <Notice tone="info" title="Hone only sizes.">It never places orders and holds no Kalshi keys. Contracts are a partial hedge at best — a weather contract and your actual income may not move together exactly. <Link to={docPath(slug, 'methodology')}>Read the method</Link>.</Notice>
    </>
  );
}
