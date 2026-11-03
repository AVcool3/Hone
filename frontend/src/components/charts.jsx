/*
 * Small hand-rolled SVG charts. No chart library: each chart answers one
 * question, labels its units, and works without hover (values are printed
 * or listed, never only in a tooltip).
 *
 *   LineChart      — equity curves (historical simulation)
 *   DensityChart   — the risk-aversion estimate as a probability curve
 *   OutcomeBars    — wealth in each scenario, with vs. without a hedge
 */
import { useId } from 'react';
import { fmtMoney, fmtPct } from '../lib/format.js';

/* Palette for multi-series charts. Index 0 is the user's / Hone's series. */
export const SERIES = ['#4f46e5', '#64748b', '#b45309', '#0f766e', '#9d174d', '#475569'];

/* ------------------------------------------------------------- LineChart */
/**
 * series: [{ label, values: number[], color?, dashed? }]
 * dates:  string[] (same length as values) — first/last are labelled.
 */
export function LineChart({ series, dates, height = 260, yFormat = v => fmtMoney(v), ariaLabel }) {
  const W = 720;
  const H = height;
  const pad = { l: 64, r: 16, t: 12, b: 28 };
  const all = series.flatMap(s => s.values).filter(Number.isFinite);
  if (!all.length) return null;
  let lo = Math.min(...all);
  let hi = Math.max(...all);
  const span = hi - lo || 1;
  lo -= span * 0.05;
  hi += span * 0.05;
  const n = Math.max(...series.map(s => s.values.length));
  const x = i => pad.l + (i / Math.max(1, n - 1)) * (W - pad.l - pad.r);
  const y = v => pad.t + (1 - (v - lo) / (hi - lo)) * (H - pad.t - pad.b);
  const ticks = Array.from({ length: 4 }, (_, i) => lo + ((hi - lo) * i) / 3);
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={ariaLabel}>
      {ticks.map(t => (
        <g key={t}>
          <line className="grid" x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} />
          <text x={pad.l - 8} y={y(t) + 4} textAnchor="end">{yFormat(t)}</text>
        </g>
      ))}
      {dates?.length > 1 && (
        <>
          <text x={pad.l} y={H - 6}>{dates[0]}</text>
          <text x={W - pad.r} y={H - 6} textAnchor="end">{dates[dates.length - 1]}</text>
        </>
      )}
      {series.map((s, si) => {
        const d = s.values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join('');
        return (
          <path
            key={s.label}
            d={d}
            fill="none"
            stroke={s.color || SERIES[si % SERIES.length]}
            strokeWidth={si === 0 ? 2.4 : 1.6}
            strokeDasharray={s.dashed ? '5 4' : undefined}
            strokeLinejoin="round"
          />
        );
      })}
    </svg>
  );
}

export function Legend({ items }) {
  return (
    <div className="row tiny muted" style={{ gap: 16 }}>
      {items.map((it, i) => (
        <span key={it.label} className="row" style={{ gap: 6 }}>
          <svg width="18" height="8" aria-hidden="true">
            <line x1="0" x2="18" y1="4" y2="4" stroke={it.color || SERIES[i % SERIES.length]} strokeWidth="2.4" strokeDasharray={it.dashed ? '4 3' : undefined} />
          </svg>
          {it.label}
        </span>
      ))}
    </div>
  );
}

/* ----------------------------------------------------------- DensityChart */
/**
 * The posterior over the risk-aversion coefficient: where the estimate sits
 * and how wide the uncertainty still is. `ci` shades the interval.
 */
export function DensityChart({ grid, density, ci, mark, height = 150 }) {
  const gid = useId();
  if (!grid?.length) return null;
  const W = 640;
  const H = height;
  const pad = { l: 8, r: 8, t: 10, b: 26 };
  const lo = grid[0];
  const hi = grid[grid.length - 1];
  const top = Math.max(...density) || 1;
  const x = v => pad.l + ((v - lo) / (hi - lo)) * (W - pad.l - pad.r);
  const y = v => pad.t + (1 - v / top) * (H - pad.t - pad.b);
  const line = grid.map((g, i) => `${i ? 'L' : 'M'}${x(g).toFixed(1)},${y(density[i]).toFixed(1)}`).join('');
  const area = `${line}L${x(hi)},${y(0)}L${x(lo)},${y(0)}Z`;
  const ticks = [0, 1, 2, 3, 5, 8, 12].filter(t => t >= lo && t <= hi);
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`Estimate ${mark?.toFixed(1)}${ci ? `, likely between ${ci[0].toFixed(1)} and ${ci[1].toFixed(1)}` : ''}`}>
      <defs>
        <clipPath id={`ci-${gid}`}>
          {ci && <rect x={x(ci[0])} y={0} width={Math.max(0, x(ci[1]) - x(ci[0]))} height={H} />}
        </clipPath>
      </defs>
      <path d={area} fill="var(--surface-sunk)" />
      {ci && <path d={area} fill="var(--lavender)" clipPath={`url(#ci-${gid})`} />}
      <path d={line} fill="none" stroke="var(--lavender-ink)" strokeWidth="2" />
      <line className="axis" x1={pad.l} x2={W - pad.r} y1={y(0)} y2={y(0)} />
      {ticks.map(t => <text key={t} x={x(t)} y={H - 6} textAnchor="middle">{t}</text>)}
      {Number.isFinite(mark) && (
        <g>
          <line x1={x(mark)} x2={x(mark)} y1={pad.t} y2={y(0)} stroke="var(--ink)" strokeWidth="1.5" strokeDasharray="3 3" />
        </g>
      )}
    </svg>
  );
}

/* ------------------------------------------------------------ OutcomeBars */
/**
 * Vertical comparison of money in each scenario, unhedged vs hedged.
 * rows: [{ label, prob, unhedged, hedged }]
 */
export function OutcomeBars({ rows, height = 220 }) {
  if (!rows?.length) return null;
  const W = 640;
  const H = height;
  const pad = { l: 8, r: 8, t: 26, b: 44 };
  const max = Math.max(...rows.flatMap(r => [r.unhedged, r.hedged])) * 1.08 || 1;
  const groupW = (W - pad.l - pad.r) / rows.length;
  const barW = Math.min(64, groupW / 3);
  const y = v => pad.t + (1 - v / max) * (H - pad.t - pad.b);
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={rows.map(r => `${r.label}: ${fmtMoney(r.unhedged)} without, ${fmtMoney(r.hedged)} with the hedge`).join('. ')}>
      <line className="axis" x1={pad.l} x2={W - pad.r} y1={y(0)} y2={y(0)} />
      {rows.map((r, i) => {
        const cx = pad.l + groupW * i + groupW / 2;
        const bars = [
          { v: r.unhedged, fill: 'var(--current)', dx: -barW - 3, tag: 'Without' },
          { v: r.hedged, fill: 'var(--proposed)', dx: 3, tag: 'With hedge' },
        ];
        return (
          <g key={r.label}>
            {bars.map(b => (
              <g key={b.tag}>
                <rect x={cx + b.dx} y={y(b.v)} width={barW} height={Math.max(0, y(0) - y(b.v))} rx="3" fill={b.fill} />
                <text x={cx + b.dx + barW / 2} y={y(b.v) - 6} textAnchor="middle" style={{ fill: 'var(--ink)', fontWeight: 600 }}>
                  {fmtMoney(b.v)}
                </text>
              </g>
            ))}
            <text x={cx} y={H - 24} textAnchor="middle" style={{ fill: 'var(--ink)', fontWeight: 600 }}>{r.label}</text>
            <text x={cx} y={H - 8} textAnchor="middle">{fmtPct(r.prob)} likely</text>
          </g>
        );
      })}
    </svg>
  );
}
