/*
 * Friendly names for symbols, so the asset picker can be searched by name
 * as well as ticker. Unknown symbols simply show their ticker.
 * EDIT HERE to add names for symbols in your own universe.
 */
export const ASSET_NAMES = {
  AAPL: 'Apple', MSFT: 'Microsoft', SPY: 'S&P 500 ETF', TSLA: 'Tesla', JNJ: 'Johnson & Johnson',
  NVDA: 'Nvidia', AMZN: 'Amazon', GOOGL: 'Alphabet', META: 'Meta', QQQ: 'Nasdaq-100 ETF',
  'BTC/USD': 'Bitcoin', 'ETH/USD': 'Ethereum', 'SOL/USD': 'Solana', 'LINK/USD': 'Chainlink',
  'AVAX/USD': 'Avalanche', 'DOT/USD': 'Polkadot',
};

/*
 * Names learned from the full asset directory (every Alpaca symbol — see
 * assetDirectory.js). Filled in once the directory loads, so `assetName`
 * knows "COST" is Costco even though it isn't in ASSET_NAMES above.
 * ASSET_NAMES wins when both have a name (it's shorter and friendlier).
 */
const DIRECTORY_NAMES = new Map();

/** Remember names from a loaded directory: [{ symbol, name }, ...]. */
export function registerAssetNames(assets) {
  for (const a of assets) if (a.name) DIRECTORY_NAMES.set(a.symbol, a.name);
}

export const assetName = sym => ASSET_NAMES[sym] || DIRECTORY_NAMES.get(sym) || '';

/**
 * Overlapping or conflicting theses: more than one thesis on the same asset.
 * Returns { [ticker]: 'conflict' | 'overlap' } for included theses only.
 * Opposite directions = conflict; same direction = overlap (they'd double-count).
 */
export function findConflicts(theses) {
  const by = {};
  theses.filter(t => t.included && t.ticker && t.target && t.refPrice).forEach(t => {
    (by[t.ticker] ||= []).push(Math.sign(t.target - t.refPrice));
  });
  const out = {};
  for (const [tk, dirs] of Object.entries(by)) {
    if (dirs.length < 2) continue;
    out[tk] = new Set(dirs).size > 1 ? 'conflict' : 'overlap';
  }
  return out;
}
