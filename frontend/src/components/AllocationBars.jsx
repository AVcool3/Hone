/*
 * AllocationBars — the core comparison in Hone: paired horizontal bars,
 * CURRENT (slate) over MODEL-PROPOSED (indigo), one row per asset.
 *
 * Colour is never the only signal: the legend names each bar, the values
 * column spells out "now → proposed", and screen readers get a sentence.
 *
 * Props
 *   rows       [{ symbol, current, target }] weights as fractions (0.35 = 35%)
 *   highlight  symbol to emphasise (e.g. the asset a thesis is about)
 *   compact    smaller rows for previews
 */
import { fmtPct } from '../lib/format.js';

export default function AllocationBars({ rows, highlight, compact = false, showLegend = true }) {
  if (!rows?.length) return null;
  const max = Math.max(0.05, ...rows.flatMap(r => [Math.abs(r.current ?? 0), Math.abs(r.target ?? 0)]));
  return (
    <div className="alloc">
      {showLegend && (
        <div className="alloc__legend" aria-hidden="true">
          <span><i className="alloc__swatch alloc__swatch--current" /> Current</span>
          <span><i className="alloc__swatch alloc__swatch--proposed" /> Model-proposed</span>
          <span className="subtle">Share of portfolio</span>
        </div>
      )}
      {rows.map(r => {
        const cur = r.current ?? 0;
        const tgt = r.target ?? 0;
        return (
          <div
            key={r.symbol}
            className="alloc__row"
            style={{
              padding: compact ? '4px 0' : undefined,
              background: highlight === r.symbol ? 'var(--proposed-wash)' : undefined,
              borderRadius: highlight === r.symbol ? 6 : undefined,
            }}
          >
            <div className="alloc__sym" title={r.symbol}>{r.symbol}</div>
            <div className="alloc__bars" role="img" aria-label={`${r.symbol}: current ${fmtPct(cur)}, proposed ${fmtPct(tgt)}`}>
              <div className="alloc__track"><div className="alloc__fill alloc__fill--current" style={{ width: `${(Math.abs(cur) / max) * 100}%` }} /></div>
              <div className="alloc__track"><div className="alloc__fill alloc__fill--proposed" style={{ width: `${(Math.abs(tgt) / max) * 100}%` }} /></div>
            </div>
            <div className="alloc__vals">
              {fmtPct(cur)} → <b>{fmtPct(tgt)}</b>
            </div>
          </div>
        );
      })}
    </div>
  );
}
