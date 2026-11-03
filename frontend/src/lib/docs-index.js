/*
 * Doc metadata only (titles, URL slugs, which product shows which doc).
 * Kept separate from docs.js — which bundles the full markdown text — so
 * the header and product switcher can know about docs without pulling
 * ~250 KB of text into every page. EDIT HERE to add or reorder a doc.
 */

/** Every document the site can show: slug -> { file, title, blurb }. */
export const DOC_INDEX = {
  'how-hone-works': { file: 'README.md', title: 'The full pipeline (README)', blurb: 'Every part of Hone from questionnaire to hedge, how to run it, and how to host it.' },
  vision: { file: 'VISION.md', title: 'Why Hone exists', blurb: 'The problem, the measurement-first approach and who it is for.' },
  'risk-elicitation': { file: 'ADAPTIVE_ELICITATION.md', title: 'Measuring risk aversion (DOSE)', blurb: 'How eight adaptive questions estimate γ, and why the classic 30-question menu tops out.' },
  calibration: { file: 'CALIBRATION.md', title: 'Confidence & the decision journal', blurb: 'What “confidence” means, how it is scored, and how your record rescales it.' },
  'flexible-views': { file: 'FLEXIBLE_VIEWS.md', title: 'Views that aren’t price targets', blurb: 'Entropy pooling: probability, ranking, volatility and conditional views.' },
  'tail-risk': { file: 'TAIL_RISK.md', title: 'Tail risk (CVaR)', blurb: 'Why variance is not enough, and the risk-first portfolio.' },
  'crypto-research': { file: 'CRYPTO_RESEARCH.md', title: 'Crypto: research basis & parameters', blurb: 'Where crypto strains the protocol, and every parameter that differs.' },
  'prediction-markets': { file: 'PREDICTION_MARKETS.md', title: 'Hedging income with event contracts', blurb: 'The theory, the sizing rule, basis risk, and the Kalshi catalog.' },
  qlora: { file: 'QLORA.md', title: 'Tuning a model on your convictions', blurb: 'Few-shot today, QLoRA later — and the arithmetic of why.' },
  roadmap: { file: 'ROADMAP.md', title: 'Roadmap', blurb: 'What comes next, ordered by leverage.' },
  'conviction-backtest': { file: 'BACKTEST_CONVICTION.md', title: 'Do convictions actually help?', blurb: 'Walk-forward simulation over a population of investors: skill, confidence, calibration.' },
  'behavior-gap': { file: 'BEHAVIOR_GAP.md', title: 'The behaviour gap', blurb: 'What returns look like once the investor is allowed to panic-sell.' },
  accounts: { file: 'SUPABASE.md', title: 'Accounts & saved portfolios', blurb: 'Optional sign-in with Supabase: setup in three steps.' },
};

/** Which docs appear under each destination, per product. Order matters. */
export const DOC_GROUPS = {
  stocks: {
    methodology: ['risk-elicitation', 'calibration', 'flexible-views', 'tail-risk', 'qlora', 'vision', 'roadmap'],
    backtests: ['conviction-backtest', 'behavior-gap'],
    setup: ['how-hone-works', 'accounts'],
  },
  crypto: {
    methodology: ['crypto-research', 'risk-elicitation', 'calibration', 'flexible-views', 'tail-risk', 'qlora'],
    backtests: ['conviction-backtest', 'behavior-gap'],
    setup: ['how-hone-works', 'accounts'],
  },
  'prediction-markets': {
    methodology: ['prediction-markets', 'risk-elicitation', 'calibration'],
    backtests: [],
    setup: ['how-hone-works', 'accounts'],
  },
};

/** Map a markdown link like "docs/CALIBRATION.md#scoring" to an in-app route. */
export function resolveDocLink(href, productSlug) {
  const m = href.match(/(?:^|\/)([A-Z_]+\.md)(#.*)?$/);
  if (!m) return null;
  const slug = Object.keys(DOC_INDEX).find(k => DOC_INDEX[k].file === m[1]);
  if (!slug) return null;
  const groups = DOC_GROUPS[productSlug] || DOC_GROUPS.stocks;
  const kind = Object.keys(groups).find(g => groups[g].includes(slug)) || 'methodology';
  return `/${productSlug}/${kind}/${slug}${m[2] || ''}`;
}

