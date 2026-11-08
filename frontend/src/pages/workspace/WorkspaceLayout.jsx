/*
 * WorkspaceLayout — the app shell for /:product/app/*.
 *
 *  ┌─────────────┬──────────────────────────────────────────────┐
 *  │  Sidebar    │  Top bar: portfolio name · sample/yours ·      │
 *  │  (tools)    │           data source · risk profile · saved   │
 *  │             ├──────────────────────────────────────────────┤
 *  │             │  <Outlet/> — the selected tool                 │
 *  └─────────────┴──────────────────────────────────────────────┘
 *
 * Every tool is reachable directly from the sidebar; none requires another
 * to be "completed" first. On phones the sidebar becomes a scrollable row.
 */
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import Icon from '../../components/Icon.jsx';
import { Logo } from '../../components/SiteHeader.jsx';
import ProductSwitcher from '../../components/ProductSwitcher.jsx';
import { Badge, SavedLabel, SourceBadge } from '../../components/ui.jsx';
import { appPath, docPath, publicPath, sectionsFor } from '../../lib/products.js';
import { portfolioSignature, useRisk, useWorkspace } from '../../lib/store.jsx';
import { useThesisQuotes } from '../../lib/hooks.js';
import { fmtGamma } from '../../lib/format.js';
import NotFound from '../NotFound.jsx';
import './workspace.css';

export default function WorkspaceLayout() {
  const product = useProduct();
  const { pathname } = useLocation();
  const { ws } = useWorkspace(product.slug);
  const risk = useRisk();
  useThesisQuotes(product.slug); // keep reference prices fresh for every page

  const sections = sectionsFor(product.slug);
  const current = pathname.split('/')[3] || '';
  if (!sections.some(s => s.key === current)) return <NotFound inApp />;

  // Small amber dots in the sidebar flag things worth a look.
  const optimizeStale = ws.results.optimize && ws.results.optimize.sig !== portfolioSignature(risk.gamma, ws);
  const flags = { risk: risk.isSample, portfolio: optimizeStale };
  const isPrediction = product.slug === 'prediction-markets';
  const hasYourData = !risk.isSample || ws.dataSource !== 'sample' || ws.theses.some(t => !t.sample);

  const nav = className => (
    <nav className={className} aria-label="Workspace tools">
      {sections.map(s => (
        <NavLink key={s.key} to={appPath(product.slug, s.key)} end={!s.key} className="ws-link">
          <Icon name={s.icon} size={18} />
          <span>{s.label}</span>
          {flags[s.key] && <span className="ws-link__flag" title="Needs attention" aria-label="needs attention" />}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="ws" data-product={product.slug}>
      <a href="#ws-main" className="skip-link">Skip to content</a>
      <aside className="ws-side">
        <div className="ws-side__brand">
          <Logo to={publicPath(product.slug)} />
          <ProductSwitcher current={product.slug} size="sm" compact className="product-switcher--full" />
        </div>
        <div className="ws-side__group">{product.kind}</div>
        {nav('ws-side__nav')}
        <div className="ws-side__foot">
          <Link to={docPath(product.slug, 'methodology')}><Icon name="Book02Icon" size={16} /> Methodology</Link>
          {!isPrediction && <Link to={docPath(product.slug, 'backtests')}><Icon name="ChartLineData02Icon" size={16} /> Research backtests</Link>}
          <Link to={docPath(product.slug, 'setup')}><Icon name="HelpCircleIcon" size={16} /> Setup & help</Link>
        </div>
      </aside>

      <div className="ws-main">
        {nav('ws-mobile-nav')}
        <div className="ws-top">
          <div className="ws-top__title">
            <span className="badge badge--product" data-product={product.slug}>{product.name}</span>
            <span>{hasYourData ? 'My portfolio' : 'Sample portfolio'}</span>
          </div>
          <div className="ws-top__meta">
            {!isPrediction && <SourceBadge dataSource={ws.dataSource} />}
            {risk.isSample
              ? <Badge tone="sample" title={`Using a sample risk aversion of ${fmtGamma(risk.gamma)} until you assess yours`}>Sample risk profile</Badge>
              : <Badge tone="yours" title="Your measured risk aversion">Risk: {risk.profile.tier?.category ?? `γ ${fmtGamma(risk.gamma)}`}</Badge>}
            <SavedLabel at={ws.savedAt} />
            <span className="show-sm"><ProductSwitcher current={product.slug} size="sm" compact /></span>
          </div>
        </div>
        <main id="ws-main" className="ws-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
