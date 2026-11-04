/*
 * Technical documentation, bundled at build time from the repository's own
 * markdown files. The website renders these files verbatim — nothing is
 * paraphrased or dropped — so the methodology and backtest pages can never
 * drift from the research they describe. Edit the .md files, rebuild, done.
 *
 * Each product maps doc "slugs" (used in URLs) to files and groups them into
 * the Methodology / Backtests / Setup destinations. EDIT HERE to add a doc.
 */

const DOCS = import.meta.glob('../../../docs/*.md', { query: '?raw', import: 'default', eager: true });
const README = import.meta.glob('../../../README.md', { query: '?raw', import: 'default', eager: true });
const CSVS = import.meta.glob('../../../research/conviction/results/{summary,diagnostics}_*.csv', {
  query: '?raw',
  import: 'default',
  eager: true,
});

import { DOC_GROUPS, DOC_INDEX, resolveDocLink } from './docs-index.js';

export { DOC_GROUPS, DOC_INDEX, resolveDocLink };

const byFile = name => {
  const key = Object.keys(DOCS).find(k => k.endsWith(`/${name}`));
  return key ? DOCS[key] : '';
};
const readme = () => Object.values(README)[0] || '';

export function getDoc(slug) {
  const meta = DOC_INDEX[slug];
  if (!meta) return null;
  const body = meta.file === 'README.md' ? readme() : byFile(meta.file);
  return { slug, ...meta, body };
}

/** Parse one of the committed backtest CSVs into an array of objects. */
export function getCsv(name) {
  const key = Object.keys(CSVS).find(k => k.endsWith(`/${name}.csv`));
  if (!key) return [];
  const [head, ...lines] = CSVS[key].trim().split('\n');
  const cols = head.split(',');
  return lines.map(line => {
    const cells = line.split(',');
    const row = {};
    cols.forEach((c, i) => {
      const n = Number(cells[i]);
      row[c] = cells[i] !== '' && Number.isFinite(n) ? n : cells[i];
    });
    return row;
  });
}

/** Pull "## Heading" sections out of a markdown string (for a sticky TOC). */
export function headings(md) {
  const out = [];
  let inFence = false;
  for (const line of md.split('\n')) {
    if (line.startsWith('```')) inFence = !inFence;
    if (inFence) continue;
    const m = line.match(/^(#{2,3})\s+(.*)$/);
    if (m) out.push({ depth: m[1].length, text: m[2].replace(/[`*_]/g, '').trim() });
  }
  return out;
}
