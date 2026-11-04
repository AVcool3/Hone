/*
 * DocsPage — Methodology and Setup.
 *
 * Renders the repository's own markdown files verbatim (lib/docs.js maps
 * which files belong to which product and page). Layout, left to right:
 *   [document list]  [the document]  [table of contents for this document]
 *
 * URLs:  /:product/methodology               -> first document
 *        /:product/methodology/calibration   -> that document
 *        /:product/methodology/calibration#scoring -> scrolled to a section
 *
 * <DocReader> is exported so the Backtests page can reuse the same reader.
 */
import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useParams } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import Markdown from '../../components/Markdown.jsx';
import { Notice } from '../../components/ui.jsx';
import { DOC_GROUPS, DOC_INDEX, getDoc } from '../../lib/docs.js';
import { appPath, docPath } from '../../lib/products.js';
import './marketing.css';

const PAGE_COPY = {
  methodology: {
    title: 'Methodology',
    lede: 'Every model, equation, assumption, parameter and limitation — the same documents the code is built from, unabridged.',
  },
  setup: {
    title: 'Setup',
    lede: 'Try the demo with no setup, connect a paper account, run Hone yourself, or turn on accounts.',
  },
};

export default function DocsPage({ kind = 'methodology' }) {
  const product = useProduct();
  const copy = PAGE_COPY[kind];
  return (
    <>
      <div className="container docs-head">
        <div className="eyebrow mb-2">{product.brand}</div>
        <h1>{copy.title}</h1>
        <p className="lede mt-3">{copy.lede}</p>
        {kind === 'setup' && <SetupQuickStart product={product} />}
      </div>
      <DocReader kind={kind} product={product} />
    </>
  );
}

/* -------------------------------------------------------------------------- */
/* The reader: doc list + document + table of contents                         */
/* -------------------------------------------------------------------------- */
export function DocReader({ kind, product }) {
  const { doc: docParam } = useParams();
  const slugs = DOC_GROUPS[product.slug]?.[kind] || [];
  // No :doc in the URL -> show the first document of this group.
  const current = docParam || slugs[0];
  const belongs = slugs.includes(current);
  const doc = belongs ? getDoc(current) : null;

  const bodyRef = useRef(null);
  const [toc, setToc] = useState([]);
  const [activeId, setActiveId] = useState(null);

  // Build the table of contents from the rendered headings (their ids come
  // from rehype-slug, so the links always match the anchors).
  useEffect(() => {
    const el = bodyRef.current;
    if (!el) return undefined;
    const hs = [...el.querySelectorAll('h2[id], h3[id]')];
    setToc(hs.map(h => ({ id: h.id, text: h.textContent, depth: h.tagName === 'H3' ? 3 : 2 })));

    // Highlight the section currently at the top of the viewport.
    const io = new IntersectionObserver(
      entries => {
        const visible = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActiveId(visible[0].target.id);
      },
      { rootMargin: '-80px 0px -70% 0px' },
    );
    hs.forEach(h => io.observe(h));
    return () => io.disconnect();
  }, [current]);

  if (!slugs.length) return null;

  return (
    <div className="container docs">
      <nav className="docs-list" aria-label={`${kind} documents`}>
        {slugs.map(s => (
          <NavLink key={s} to={docPath(product.slug, kind, s)} className={() => (s === current ? 'active' : '')}>
            {DOC_INDEX[s].title}
          </NavLink>
        ))}
      </nav>

      <article ref={bodyRef} style={{ minWidth: 0 }}>
        {doc ? (
          <>
            <div className="doc-meta">
              <span>{doc.blurb}</span>
              <a href={`https://github.com/avcool3/hone/blob/main/${doc.file === 'README.md' ? '' : 'docs/'}${doc.file}`} target="_blank" rel="noreferrer">
                Source: {doc.file}
              </a>
            </div>
            <Markdown productSlug={product.slug}>{doc.body}</Markdown>
          </>
        ) : (
          // A doc that exists for another product (or a typo): say so rather
          // than showing unrelated content.
          <Notice tone="attention" title="This document isn’t part of this product’s pages.">
            {DOC_INDEX[current] ? `“${DOC_INDEX[current].title}” belongs to a different product.` : 'No document has that name.'}{' '}
            Pick one from the list.
          </Notice>
        )}
      </article>

      <aside className="docs-toc" aria-label="On this page">
        {toc.length > 0 && <div className="eyebrow mb-3">On this page</div>}
        {toc.map(t => (
          <a key={t.id} href={`#${t.id}`} className={`depth-${t.depth} ${t.id === activeId ? 'is-active' : ''}`}>
            {t.text}
          </a>
        ))}
      </aside>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Setup: four short routes above the full documentation                       */
/* -------------------------------------------------------------------------- */
function SetupQuickStart({ product }) {
  const s = product.slug;
  const isPM = s === 'prediction-markets';
  const cards = [
    { title: 'Try the demo', body: 'Nothing to install or sign up for. Sample data is labelled everywhere.', to: appPath(s), cta: 'Open the workspace' },
    isPM
      ? { title: 'No brokerage needed', body: 'Hone reads public Kalshi prices and never holds exchange keys. It only sizes and explains.', to: appPath(s, 'markets'), cta: 'Browse markets' }
      : { title: 'Connect a paper account', body: `Use your own ${product.account} for real prices and holdings. Keys stay in your browser.`, to: appPath(s, 'settings'), cta: 'Data & account' },
    { title: 'Run it yourself', body: 'Install the Python package, start the web app, or host it with Docker, Render or Fly.', to: docPath(s, 'setup', 'how-hone-works', 'install'), cta: 'Install steps' },
    { title: 'Accounts (optional)', body: 'Turn on sign-in and saved portfolios with Supabase in about ten minutes.', to: docPath(s, 'setup', 'accounts'), cta: 'Set up accounts' },
  ];
  return (
    <div className="doc-cards">
      {cards.map(c => (
        <Link key={c.title} to={c.to} className="doc-card">
          <strong>{c.title}</strong>
          <span>{c.body}</span>
          <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{c.cta} →</span>
        </Link>
      ))}
    </div>
  );
}

