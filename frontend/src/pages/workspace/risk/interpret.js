/*
 * Plain-English readings of a risk-aversion coefficient (γ, CRRA).
 * These are ILLUSTRATIONS with stated assumptions — the page says so.
 */

/**
 * Certainty equivalent of a 50/50 gamble between `a` and `b` for CRRA γ:
 * the sure amount that would feel as good as the gamble.
 */
export function certaintyEquivalent(gamma, a, b) {
  if (Math.abs(gamma - 1) < 1e-6) return Math.exp(0.5 * Math.log(a) + 0.5 * Math.log(b));
  const k = 1 - gamma;
  return (0.5 * a ** k + 0.5 * b ** k) ** (1 / k);
}

/**
 * Merton's rule of thumb: share of savings in a broad index
 *   = equity premium / (γ × market variance).
 * Assumptions are passed in so the page can print them.
 */
export function mertonShare(gamma, premium = 0.05, vol = 0.16) {
  if (gamma <= 0) return Infinity;
  return premium / (gamma * vol * vol);
}

/** A short sentence describing what the estimate does to position sizes. */
export function effectSentence(gamma) {
  if (gamma < 0.5) return 'Hone will accept large, concentrated positions when your views are strong — the position limit will often be what stops it.';
  if (gamma < 1.5) return 'Hone will lean into your views fairly readily, trimming only positions whose risk clearly outweighs their expected return.';
  if (gamma < 3.5) return 'Hone will want a view to earn its risk before sizing it up, and will spread money across holdings rather than concentrate it.';
  return 'Hone will hold mostly lower-volatility positions, size views cautiously, and often suggest a hedge to bring overall swings down.';
}
