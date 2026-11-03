/*
 * ProductSwitcher — Stocks / Crypto / Prediction Markets.
 *
 * Built on React Bits' RubberSegment. Switching keeps you in the same
 * place where that place exists for the new product (e.g. Methodology →
 * Crypto Methodology, or Workspace › Theses → Crypto › Theses). Where it
 * doesn't exist (Prediction Markets has no Theses), you land on the
 * product's overview of that area instead of on unrelated stock content.
 */
import { useLocation, useNavigate } from 'react-router-dom';
import RubberSegment from '../reactbits/RubberSegment/RubberSegment.jsx';
import { PRODUCT_ORDER, PRODUCTS, sectionsFor } from '../lib/products.js';
import { DOC_GROUPS } from '../lib/docs-index.js';

const LABELS = { stocks: 'Stocks', crypto: 'Crypto', 'prediction-markets': 'Prediction Markets' };
// Narrow spots (the workspace sidebar) use a shorter label for the third product.
const COMPACT = { ...LABELS, 'prediction-markets': 'Prediction' };

/** Where the same "place" lives for another product. */
export function equivalentPath(pathname, toSlug) {
  const parts = pathname.split('/').filter(Boolean);
  const onProduct = PRODUCTS[parts[0]];
  const rest = onProduct ? parts.slice(1) : [];
  if (!rest.length) return toSlug === 'stocks' ? '/' : `/${toSlug}`;
  const [area, sub] = rest;
  if (area === 'app') {
    const ok = sectionsFor(toSlug).some(s => s.key === (sub || ''));
    return `/${toSlug}/app${ok && sub ? `/${sub}` : ''}`;
  }
  if (['methodology', 'backtests', 'setup'].includes(area)) {
    const ok = sub && DOC_GROUPS[toSlug][area].includes(sub);
    return `/${toSlug}/${area}${ok ? `/${sub}` : ''}`;
  }
  return `/${toSlug}/${area}`;
}

export default function ProductSwitcher({ current, size = 'md', className = '', compact = false }) {
  const nav = useNavigate();
  const { pathname } = useLocation();
  return (
    <RubberSegment
      className={`product-switcher ${className}`}
      aria-label="Product"
      items={PRODUCT_ORDER.map(slug => ({ value: slug, label: (compact ? COMPACT : LABELS)[slug] }))}
      value={current}
      onChange={slug => nav(equivalentPath(pathname, slug))}
      size={size}
      equalSlots={false}
      trackColor="#ecebe2"
      thumbColor="#20251f"
      textColor="#20251f"
      activeTextColor="#ffffff"
      radius={999}
      inset={3}
      draggable
    />
  );
}
