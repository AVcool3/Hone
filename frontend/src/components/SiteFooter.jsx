/* Footer for public pages: product links, docs, and the not-advice disclaimer. */
import { Link } from 'react-router-dom';
import { Logo } from './SiteHeader.jsx';
import { appPath, PRODUCT_ORDER, PRODUCTS, publicPath } from '../lib/products.js';

export default function SiteFooter({ product }) {
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="site-footer__grid">
          <div>
            <Logo />
            <p className="subtle mt-3" style={{ maxWidth: 340 }}>
              Turn your investment views into a portfolio you can explain. An open research tool — not investment advice.
            </p>
          </div>
          <div>
            <div className="eyebrow mb-3">Products</div>
            <ul className="plain-list">
              {PRODUCT_ORDER.map(s => (
                <li key={s}><Link to={publicPath(s)}>{PRODUCTS[s].name}</Link> <span className="subtle">· {PRODUCTS[s].kind}</span></li>
              ))}
            </ul>
          </div>
          <div>
            <div className="eyebrow mb-3">{product.name}</div>
            <ul className="plain-list">
              <li><Link to={appPath(product.slug)}>Workspace</Link></li>
              <li><Link to={publicPath(product.slug, 'how-it-works')}>How it works</Link></li>
              <li><Link to={publicPath(product.slug, 'methodology')}>Methodology</Link></li>
              {product.slug !== 'prediction-markets' && <li><Link to={publicPath(product.slug, 'backtests')}>Backtests</Link></li>}
              <li><Link to={publicPath(product.slug, 'setup')}>Setup</Link></li>
            </ul>
          </div>
        </div>
        <p className="tiny subtle mt-6" style={{ maxWidth: 820 }}>
          Hone is educational software. It works on sample data or an Alpaca <em>paper</em> account, never places
          real trades, and holds no exchange keys for prediction markets. Model-proposed allocations depend on the
          model and on your inputs; they are not recommendations. Past and simulated results do not predict future returns.
        </p>
      </div>
    </footer>
  );
}
