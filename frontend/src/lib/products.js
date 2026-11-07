/*
 * Product definitions — the single place that says how Stocks, Crypto and
 * Prediction Markets differ in the UI.
 *
 * The Python server picks its data/calendar/proxy from the `asset_class`
 * query parameter (equities | crypto | prediction); everything else here is
 * copy and navigation. EDIT HERE to change examples, labels, or which
 * workspace sections a product has.
 */

export const PRODUCTS = {
  stocks: {
    slug: 'stocks',
    assetClass: 'equities',
    name: 'Stocks',
    brand: 'Hone',
    kind: 'Portfolio sizing',
    assetWord: 'stocks',
    assetSingular: 'stock',
    cashWord: 'cash',
    marketName: 'the S&P 500',
    account: 'Alpaca paper account',
    // Sample-portfolio thesis used by the homepage demo and the sample workspace.
    example: { ticker: 'TSLA', target: 450, confidence: 0.6, horizonDays: 365 },
    examplePhrase: 'I think Tesla reaches $450 within a year — fairly confident.',
    hedgeNote: 'Hedges include holding more cash, shorting an index, and option overlays.',
    volatilityNote: '',
  },
  crypto: {
    slug: 'crypto',
    assetClass: 'crypto',
    name: 'Crypto',
    brand: 'Hone Crypto',
    kind: 'Portfolio sizing',
    assetWord: 'coins',
    assetSingular: 'coin',
    cashWord: 'stablecoins',
    marketName: 'Bitcoin',
    account: 'Alpaca crypto paper account',
    example: { ticker: 'SOL/USD', target: 380, confidence: 0.6, horizonDays: 180 },
    examplePhrase: 'I think Solana reaches $380 in six months — fairly confident.',
    hedgeNote:
      'Crypto hedges are a stablecoin allocation and a short of the market proxy (BTC). Listed crypto options are not available through the brokerage integration.',
    volatilityNote:
      'Crypto volatility runs 50–100%+ a year, several times equity levels, and 80% drawdowns have happened twice. Position sizes here will look small for a reason.',
  },
  'prediction-markets': {
    slug: 'prediction-markets',
    assetClass: 'prediction',
    name: 'Prediction Markets',
    brand: 'Hone Markets',
    kind: 'Income hedging',
    assetWord: 'contracts',
    assetSingular: 'contract',
    cashWord: 'cash',
    marketName: 'Kalshi',
    account: 'No brokerage — Hone only sizes the hedge',
    example: null,
    examplePhrase: '',
    hedgeNote:
      'Hone sizes event contracts against your income risk and explains the position. It never places orders, and it holds no Kalshi keys.',
    volatilityNote: '',
  },
};

export const PRODUCT_ORDER = ['stocks', 'crypto', 'prediction-markets'];

export const productFromSlug = slug => PRODUCTS[slug] ?? PRODUCTS.stocks;

/* Public (marketing) navigation, per product. */
export const PUBLIC_SECTIONS = [
  { key: '', label: 'Overview' },
  { key: 'how-it-works', label: 'How it works' },
  { key: 'methodology', label: 'Methodology' },
  { key: 'backtests', label: 'Backtests' },
  { key: 'setup', label: 'Setup' },
];

/*
 * Workspace sidebar sections. Each one is an independent tool with its own
 * URL: /:product/app/:section. `icon` names are Hugeicons exports.
 */
export const WORKSPACE_SECTIONS = {
  portfolio: [
    { key: '', label: 'Overview', icon: 'DashboardSquare01Icon' },
    { key: 'risk', label: 'Risk aversion', icon: 'Target02Icon' },
    { key: 'theses', label: 'Investment theses', icon: 'BulbIcon' },
    { key: 'portfolio', label: 'Portfolio', icon: 'PieChartIcon' },
    { key: 'hedging', label: 'Hedging', icon: 'Shield01Icon' },
    { key: 'record', label: 'Track record', icon: 'Notebook01Icon' },
    { key: 'backtest', label: 'Backtest', icon: 'ChartLineData02Icon' },
    { key: 'settings', label: 'Data & account', icon: 'Settings02Icon' },
  ],
  prediction: [
    { key: '', label: 'Overview', icon: 'DashboardSquare01Icon' },
    { key: 'risk', label: 'Risk aversion', icon: 'Target02Icon' },
    { key: 'quote', label: 'Price my risk', icon: 'Analytics01Icon' },
    { key: 'hedge', label: 'Income hedge', icon: 'Shield01Icon' },
    { key: 'markets', label: 'Markets', icon: 'Store01Icon' },
    { key: 'record', label: 'Track record', icon: 'Notebook01Icon' },
    { key: 'settings', label: 'Data & account', icon: 'Settings02Icon' },
  ],
};

export const sectionsFor = slug =>
  slug === 'prediction-markets' ? WORKSPACE_SECTIONS.prediction : WORKSPACE_SECTIONS.portfolio;

/* URL helpers so every link is built the same way. */
export const publicPath = (slug, section = '') => {
  if (slug === 'stocks' && !section) return '/';
  return `/${slug}${section ? `/${section}` : ''}`;
};
export const appPath = (slug, section = '') => `/${slug}/app${section ? `/${section}` : ''}`;
export const docPath = (slug, kind, doc, anchor) =>
  `/${slug}/${kind}${doc ? `/${doc}` : ''}${anchor ? `#${anchor}` : ''}`;
