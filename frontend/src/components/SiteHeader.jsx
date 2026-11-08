/*
 * SiteHeader — public pages.
 *   Left:   Hone logo + product switcher (selects the product)
 *   Middle: sections for the selected product (explain the product)
 *   Right:  "Join the waitlist" (the landing page form) and "Try the demo"
 * On phones the product switcher stays visible; the sections fold into a menu.
 */
import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import Icon from './Icon.jsx';
import ProductSwitcher from './ProductSwitcher.jsx';
import { appPath, PUBLIC_SECTIONS, publicPath } from '../lib/products.js';

export function Logo({ to = '/' }) {
  return (
    <Link to={to} className="logo" aria-label="Hone home">
      <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#174e43" />
        <path d="M9 23V9m0 7h14m0-7v14" stroke="#faf8ee" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <span>Hone</span>
    </Link>
  );
}

export default function SiteHeader({ product }) {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => setOpen(false), [pathname]);

  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <div className="site-header__brand">
          <Logo to="/" />
          <ProductSwitcher current={product.slug} size="md" className="hide-sm" />
        </div>
        <nav className={`site-nav ${open ? 'is-open' : ''}`} aria-label={`${product.name} sections`}>
          {PUBLIC_SECTIONS.map(s => (
            <NavLink key={s.key} to={publicPath(product.slug, s.key)} end={!s.key} className="site-nav__link">
              {s.label}
            </NavLink>
          ))}
          <Link to={appPath(product.slug)} className="site-nav__link site-nav__cta-mobile">Try the demo</Link>
          <Link to="/#waitlist" className="btn btn--primary btn--sm site-nav__cta-mobile">Join the waitlist</Link>
        </nav>
        <div className="site-header__actions">
          {/* New visitors go to the waitlist; the demo stays one click away. */}
          <Link to={appPath(product.slug)} className="btn btn--secondary btn--sm hide-sm">Try the demo</Link>
          <Link to="/#waitlist" className="btn btn--primary btn--sm hide-sm">Join the waitlist</Link>
          <button
            type="button"
            className="btn btn--secondary btn--sm show-sm"
            aria-expanded={open}
            aria-label="Sections"
            onClick={() => setOpen(o => !o)}
          >
            <Icon name={open ? 'Cancel01Icon' : 'Menu01Icon'} />
          </button>
        </div>
      </div>
      <div className="container show-sm" style={{ paddingBottom: 10 }}>
        <ProductSwitcher current={product.slug} size="sm" className="product-switcher--full" />
      </div>
    </header>
  );
}
