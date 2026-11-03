/*
 * Route table. Every page and every workspace tool has its own URL, so
 * back/forward, refresh and shared links all work.
 *
 *   /                                   Stocks overview (marketing)
 *   /:product                           product overview  (stocks | crypto | prediction-markets)
 *   /:product/how-it-works
 *   /:product/methodology[/:doc]        repository docs, verbatim
 *   /:product/backtests[/:doc]
 *   /:product/setup[/:doc]
 *   /:product/app[/:section]            the workspace (see lib/products.js for sections)
 *
 * The Python server returns index.html for all of these (hone/web/app.py).
 */
import { lazy, Suspense, useEffect } from 'react';
import { Navigate, Outlet, Route, Routes, useLocation, useParams } from 'react-router-dom';
import { PRODUCTS, productFromSlug } from './lib/products.js';
import SiteHeader from './components/SiteHeader.jsx';
import SiteFooter from './components/SiteFooter.jsx';

import Home from './pages/marketing/Home.jsx';
// Docs-heavy pages load on demand: they bundle the repository's markdown,
// the backtest CSVs and the markdown renderer, which most visits never need.
const HowItWorks = lazy(() => import('./pages/marketing/HowItWorks.jsx'));
const DocsPage = lazy(() => import('./pages/marketing/DocsPage.jsx'));
const BacktestsPage = lazy(() => import('./pages/marketing/BacktestsPage.jsx'));
import NotFound from './pages/NotFound.jsx';

import WorkspaceLayout from './pages/workspace/WorkspaceLayout.jsx';
import Overview from './pages/workspace/Overview.jsx';
import RiskPage from './pages/workspace/risk/RiskPage.jsx';
import ThesesPage from './pages/workspace/theses/ThesesPage.jsx';
import PortfolioPage from './pages/workspace/PortfolioPage.jsx';
import HedgingPage from './pages/workspace/HedgingPage.jsx';
import RecordPage from './pages/workspace/RecordPage.jsx';
import BacktestPage from './pages/workspace/BacktestPage.jsx';
import SettingsPage from './pages/workspace/SettingsPage.jsx';
import IncomeHedgePage from './pages/workspace/prediction/IncomeHedgePage.jsx';
import MarketsPage from './pages/workspace/prediction/MarketsPage.jsx';

/** The product for the current URL ("/" means Stocks). */
export function useProduct() {
  const { product } = useParams();
  return productFromSlug(product || 'stocks');
}

/** Scroll to top on navigation, or to #anchor when the URL has one. */
function ScrollManager() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) {
      const id = decodeURIComponent(hash.slice(1));
      // Wait a frame so the page (e.g. a markdown doc) has rendered its headings.
      requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ block: 'start' }));
    } else {
      window.scrollTo(0, 0);
    }
  }, [pathname, hash]);
  return null;
}

/** Rejects unknown product slugs instead of silently showing Stocks. */
function ProductGuard({ children }) {
  const { product } = useParams();
  if (product && !PRODUCTS[product]) return <NotFound />;
  return children;
}

function PublicLayout() {
  const product = useProduct();
  return (
    <div className="public" data-product={product.slug}>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteHeader product={product} />
      <main id="main">
        <Suspense fallback={<div className="container section"><span className="spinner" role="status">Loading…</span></div>}>
          <Outlet />
        </Suspense>
      </main>
      <SiteFooter product={product} />
    </div>
  );
}

export default function App() {
  return (
    <>
      <ScrollManager />
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/stocks" element={<Navigate to="/" replace />} />
          <Route path="/:product" element={<ProductGuard><Home /></ProductGuard>} />
          <Route path="/:product/how-it-works" element={<ProductGuard><HowItWorks /></ProductGuard>} />
          <Route path="/:product/methodology/:doc?" element={<ProductGuard><DocsPage kind="methodology" /></ProductGuard>} />
          <Route path="/:product/backtests/:doc?" element={<ProductGuard><BacktestsPage /></ProductGuard>} />
          <Route path="/:product/setup/:doc?" element={<ProductGuard><DocsPage kind="setup" /></ProductGuard>} />
        </Route>
        <Route path="/:product/app" element={<ProductGuard><WorkspaceLayout /></ProductGuard>}>
          <Route index element={<Overview />} />
          <Route path="risk" element={<RiskPage />} />
          <Route path="theses" element={<ThesesPage />} />
          <Route path="portfolio" element={<PortfolioPage />} />
          <Route path="hedging" element={<HedgingPage />} />
          <Route path="record" element={<RecordPage />} />
          <Route path="backtest" element={<BacktestPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="hedge" element={<IncomeHedgePage />} />
          <Route path="markets" element={<MarketsPage />} />
          <Route path="*" element={<NotFound inApp />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
