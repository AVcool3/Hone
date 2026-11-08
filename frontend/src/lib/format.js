/*
 * Number formatting. Rules:
 *  - Percentages default to whole numbers (weights) or one decimal (returns);
 *    precision is a display choice, not a claim about how sure the model is.
 *  - Signed formatters keep the sign (a loss must never print as a gain).
 *  - Nothing ever prints "-0".
 */

const isNum = x => typeof x === 'number' && Number.isFinite(x);

/** Unsigned percent: 0.354 -> "35%" (digits=0) or "35.4%" (digits=1). */
export const fmtPct = (x, digits = 0) => {
  if (!isNum(x)) return '—';
  const v = Number((x * 100).toFixed(digits));
  return `${Object.is(v, -0) ? 0 : v.toFixed(digits)}%`;
};

/**
 * Signed percent: +3.1% / −2.0% / 0.0%.
 * Guard: -0.0004 -> -0, prints as "0.0%" rather than "-0.0%".
 */
export const fmtSPct = (x, digits = 1) => {
  if (!isNum(x)) return '—';
  const v = Number((x * 100).toFixed(digits));
  if (v === 0) return `${(0).toFixed(digits)}%`;
  return `${v > 0 ? '+' : '−'}${Math.abs(v).toFixed(digits)}%`;
};

/** Percentage points, signed, for weight changes: +12 pts. */
export const fmtPts = (x, digits = 0) => {
  if (!isNum(x)) return '—';
  const v = Number((x * 100).toFixed(digits));
  if (v === 0) return '0 pts';
  return `${v > 0 ? '+' : '−'}${Math.abs(v).toFixed(digits)} pts`;
};

/** Money, unsigned: $12,345. Takes |x| — use fmtSMoney for anything signed. */
export const fmtMoney = (x, digits = 0) => {
  if (!isNum(x)) return '—';
  return Math.abs(x).toLocaleString('en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: digits, minimumFractionDigits: digits,
  });
};

/** Money, signed: +$1,200 / −$640. */
export const fmtSMoney = (x, digits = 0) => {
  if (!isNum(x)) return '—';
  const rounded = Number(x.toFixed(digits));
  if (rounded === 0) return fmtMoney(0, digits);
  return `${rounded > 0 ? '+' : '−'}${fmtMoney(rounded, digits)}`;
};

/** Price with sensible precision: $377.34, $0.42, $64,210. */
export const fmtPrice = x => {
  if (!isNum(x)) return '—';
  const digits = Math.abs(x) >= 1000 ? 0 : Math.abs(x) >= 1 ? 2 : 4;
  return fmtMoney(x, digits);
};

/** Contract price in cents: 0.31 -> "31¢". */
export const fmtCents = x => (isNum(x) ? `${Math.round(x * 100)}¢` : '—');

export const fmtNum = (x, digits = 0) =>
  isNum(x) ? x.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits }) : '—';

/** Risk-aversion coefficient: two significant decimals are plenty. */
export const fmtGamma = g => (isNum(g) ? g.toFixed(g >= 10 ? 0 : 1) : '—');

/** Horizon in days -> "1 year", "6 months", "45 days". */
export const fmtHorizon = days => {
  if (!isNum(days)) return '—';
  if (days >= 360) {
    const y = days / 365.25;
    return Math.abs(y - Math.round(y)) < 0.08 ? `${Math.round(y)} year${Math.round(y) === 1 ? '' : 's'}` : `${y.toFixed(1)} years`;
  }
  if (days >= 28) {
    const m = Math.round(days / 30.44);
    return `${m} month${m === 1 ? '' : 's'}`;
  }
  return `${Math.round(days)} days`;
};

/** "3 minutes ago" style relative time for "last saved" labels. */
export const fmtAgo = iso => {
  if (!iso) return '';
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 45) return 'just now';
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

export const fmtDate = iso =>
  iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—';

/** Implied change from a reference price to a target. */
export const impliedChange = (ref, target) => (isNum(ref) && isNum(target) && ref > 0 ? target / ref - 1 : null);

export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
