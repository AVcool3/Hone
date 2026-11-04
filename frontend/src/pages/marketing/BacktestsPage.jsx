/*
 * BacktestsPage — the evidence, inspectable rather than promotional.
 *
 *   1. Summary: the research's own headline findings (verbatim, unfavourable
 *      ones included), the setup, and the caveats.
 *   2. Explorer: every cell of the committed results CSVs
 *      (research/conviction/results/summary_*.csv). Pick a risk aversion,
 *      a skill level and an overconfidence level; see every strategy.
 *   3. The full write-ups, rendered verbatim (same reader as Methodology).
 *
 * Prediction Markets has no backtest; the page says so and explains why
 * instead of showing stock results.
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import Markdown from '../../components/Markdown.jsx';
import { Badge, Button, Notice, Segmented, Stat } from '../../components/ui.jsx';
import { getCsv, getDoc } from '../../lib/docs.js';
import { appPath, docPath } from '../../lib/products.js';
import { fmtNum, fmtPct, fmtSPct } from '../../lib/format.js';
import { DocReader } from './DocsPage.jsx';
import './marketing.css';

/* What each strategy in the CSV is (from docs/BACKTEST_CONVICTION.md §1). */
const STRATEGIES = [
  { key: 'market_hold', label: 'Hold the market', what: 'Buy and hold the market proxy' },
  { key: 'equal_weight', label: 'Equal weight', what: '1/N — the retail default' },
  { key: 'risk_only', label: 'Risk profile only', what: 'Hone’s risk-aware optimizer, no views (baseline)' },
  { key: 'views_stated_conf', label: 'Views · stated confidence', what: 'What Hone ships: views at the investor’s own confidence' },
  { key: 'views_calibrated_conf', label: 'Views · calibrated confidence', what: 'Confidence replaced by the realised hit rate' },
  { key: 'views_full_conf', label: 'Views · face value', what: 'Confidence forced to 100%' },
];

const GAMMAS = [0.5, 1.2, 2.5, 5, 8];
const SKILLS = [0, 0.2, 0.4];
const OVERCONF = [1, 2];

/** Pull "## Headline" out of the write-up so the summary quotes it verbatim. */
function headlineSection(md) {
  const m = md.match(/\n## Headline\n([\s\S]*?)\n## /);
  return m ? m[1].replace(/\n---\s*$/, '').trim() : '';
}

export default function BacktestsPage() {
  const product = useProduct();
  if (product.slug === 'prediction-markets') return <NoBacktest product={product} />;
  return <PortfolioBacktests key={product.slug} product={product} />;
}

/* -------------------------------------------------------------------------- */
function PortfolioBacktests({ product }) {
  const isCrypto = product.slug === 'crypto';
  const summary = useMemo(() => getCsv(isCrypto ? 'summary_crypto' : 'summary_equities'), [isCrypto]);
  const diagnostics = useMemo(() => getCsv(isCrypto ? 'diagnostics_crypto' : 'diagnostics_equities'), [isCrypto]);
  const headline = useMemo(() => headlineSection(getDoc('conviction-backtest')?.body || ''), []);

  // Explorer selection. Defaults: a middling investor (γ 2.5) with some skill.
  const [gamma, setGamma] = useState(2.5);
  const [skill, setSkill] = useState(0.2);
  const [over, setOver] = useState(1);

  const near = (a, b) => Math.abs(a - b) < 1e-9;
  const cell = summary.filter(r => near(r.gamma, gamma) && near(r.skill, skill) && near(r.overconfidence, over));
  const diag = diagnostics.find(r => near(r.gamma, gamma) && near(r.skill, skill) && near(r.overconfidence, over));
  const rows = STRATEGIES.map(s => ({ ...s, r: cell.find(c => c.strategy === s.key) })).filter(x => x.r);
  const draws = rows[0]?.r?.n;

  return (
    <>
      <div className="container docs-head">
        <div className="eyebrow mb-2">{product.brand}</div>
        <h1>Backtests</h1>
        <p className="lede mt-3">
          Do views actually help, and for whom? A walk-forward simulation over a population of investors — favourable and
          unfavourable results kept side by side.
        </p>
        <div className="row mt-4">
          <Badge tone="sample">Simulated · synthetic price paths</Badge>
          <Badge>Historical simulation, not forward performance</Badge>
          <Button variant="text" to={appPath(product.slug, 'backtest')} iconRight="ArrowRight01Icon">Run a backtest on your own inputs</Button>
        </div>
      </div>

      {/* ---------------- summary ---------------- */}
      <section className="container section--tight">
        <h2 className="section-title mb-4">Summary — what the research found</h2>
        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div className="md" style={{ fontSize: 15.5 }}>
            <Markdown productSlug={product.slug}>{headline}</Markdown>
          </div>
          <div className="stack">
            <div className="card">
              <div className="card__title mb-3">How it was run</div>
              <div className="grid-2" style={{ gap: 14 }}>
                <Stat size="sm" label="Investor draws per cell" value="40" />
                <Stat size="sm" label="Investor-cell runs" value="14,400" note="both asset classes" />
                <Stat size="sm" label="Estimation window" value={isCrypto ? '365 days' : '252 days'} note="trailing, walk-forward" />
                <Stat size="sm" label="Rebalance" value="Every 21 periods" note="long-only, 35% cap per name" />
              </div>
            </div>
            <div className="card card--sunk">
              <div className="card__title mb-2">Caveats that matter</div>
              <ul className="small muted" style={{ display: 'grid', gap: 6 }}>
                <li><b>Synthetic prices.</b> Constant covariance, drifts drawn independently of volatility (§7.1 re-runs the key result where risk is paid).</li>
                <li><b>No trading costs.</b> View strategies turn over far more; §7.4 estimates the fee drag.</li>
                <li><b>The 35% cap does safety work.</b> Remove it and face-value views get much worse (§7.2).</li>
                <li><b>Calibration arm is the aggressive form.</b> What ships sits between the stated and calibrated arms (§2).</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- explorer ---------------- */}
      <section className="container section--tight">
        <h2 className="section-title">Explore every result</h2>
        <p className="subtle mt-1 mb-4">
          Source: <code>research/conviction/results/{isCrypto ? 'summary_crypto' : 'summary_equities'}.csv</code>. Medians across{' '}
          {draws ?? 40} investor draws; returns and volatility are annualised.
        </p>
        <div className="explorer">
          <div className="explorer__controls">
            <div className="field">
              <span className="field__label">Risk aversion (γ)</span>
              <Segmented label="Risk aversion" value={gamma} onChange={setGamma} options={GAMMAS.map(g => ({ value: g, label: String(g) }))} />
            </div>
            <div className="field">
              <span className="field__label">Forecasting skill</span>
              <Segmented label="Skill" value={skill} onChange={setSkill}
                options={SKILLS.map(k => ({ value: k, label: k === 0 ? 'None' : `IC ${k}` }))} />
            </div>
            <div className="field">
              <span className="field__label">Overconfidence</span>
              <Segmented label="Overconfidence" value={over} onChange={setOver}
                options={OVERCONF.map(o => ({ value: o, label: o === 1 ? 'Calibrated' : `${o}× over` }))} />
            </div>
          </div>
          <p className="takeaway">
            {takeaway(rows)}
          </p>
          <div className="tscroll">
            <table>
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th className="r">CAGR</th>
                  <th className="r">Sharpe (p25–p75)</th>
                  <th className="r">Max drawdown</th>
                  <th className="r">Volatility</th>
                  <th className="r">Effective names</th>
                  <th className="r">Turnover / rebalance</th>
                  <th className="r">Beats risk-only</th>
                  <th className="r">Beats market</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ key, label, what, r }) => (
                  <tr key={key} className={key === 'risk_only' ? 'is-base' : ''}>
                    <td><div className="strong">{label}</div><div className="tiny subtle">{what}</div></td>
                    <td className="r">{fmtSPct(r.cagr)}</td>
                    <td className="r">{r.sharpe.toFixed(2)} <span className="subtle">({r.sharpe_p25.toFixed(2)}–{r.sharpe_p75.toFixed(2)})</span></td>
                    <td className="r loss">{fmtSPct(r.max_drawdown, 0)}</td>
                    <td className="r">{fmtPct(r.volatility, 0)}</td>
                    <td className="r">{fmtNum(r.effective_n, 1)}</td>
                    <td className="r">{fmtPct(r.turnover, 0)}</td>
                    <td className="r">{key === 'risk_only' ? '—' : fmtPct(r.beat_risk_only, 0)}</td>
                    <td className="r">{key === 'market_hold' ? '—' : fmtPct(r.beat_market_hold, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="chart-caption">
            “Beats” = share of investor draws on which the strategy’s Sharpe ratio was higher (per draw, not on averages).
            Shaded row: the no-views baseline. Effective names = how diversified the book is (1 = everything in one asset).
          </p>

          {diag && (
            <div className="mt-5">
              <div className="small strong mb-3">The investor in this cell</div>
              <div className="grid-4">
                <Stat size="sm" label="Stated confidence" value={fmtPct(diag.diag_stated_confidence, 0)} />
                <Stat size="sm" label="Calibrated confidence (final)" value={fmtPct(diag.diag_final_calibrated_confidence, 0)}
                  note={`mean ${fmtPct(diag.diag_mean_calibrated_confidence, 0)}`} />
                <Stat size="sm" label="Direction right" value={fmtPct(diag.diag_directional_hit_rate, 0)}
                  note={`vs. prior: ${fmtPct(diag.diag_surprise_hit_rate, 0)}`} />
                <Stat size="sm" label="Views resolved" value={fmtNum(diag.diag_views_resolved)} note="per investor" />
              </div>
              <p className="chart-caption">
                “Direction right” is flattered by market drift; “vs. prior” grades the same calls against what the model already
                expected — the honest measure of skill. See{' '}
                <Link to={docPath(product.slug, 'methodology', 'calibration')}>Confidence &amp; the decision journal</Link>.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* ---------------- full write-ups ---------------- */}
      <section style={{ borderTop: '1px solid var(--line)', marginTop: 32 }}>
        <div className="container" style={{ paddingTop: 40 }}>
          <h2 className="section-title">The full write-ups</h2>
          <p className="subtle mt-1">Method, every result table, robustness checks and how to reproduce them — unabridged.</p>
        </div>
        <DocReader kind="backtests" product={product} />
      </section>
    </>
  );
}

/** One sentence that says what the selected cell shows. */
function takeaway(rows) {
  const base = rows.find(x => x.key === 'risk_only')?.r;
  const stated = rows.find(x => x.key === 'views_stated_conf')?.r;
  if (!base || !stated) return '';
  const diff = stated.sharpe - base.sharpe;
  const verb = Math.abs(diff) < 0.02 ? 'performed about the same as' : diff > 0 ? 'beat' : 'trailed';
  return `In this cell, views at stated confidence ${verb} the no-views baseline (median Sharpe ${stated.sharpe.toFixed(2)} vs ${base.sharpe.toFixed(2)}), winning on ${fmtPct(stated.beat_risk_only, 0)} of investor draws.`;
}

/* -------------------------------------------------------------------------- */
function NoBacktest({ product }) {
  const s = product.slug;
  return (
    <div className="container docs-head" style={{ paddingBottom: 64 }}>
      <div className="eyebrow mb-2">{product.brand}</div>
      <h1>Backtests</h1>
      <p className="lede mt-3">There is no backtest for income hedging yet — on purpose.</p>
      <div className="stack mt-6" style={{ maxWidth: 760 }}>
        <Notice tone="info" title="Why not.">
          A hedge is judged by how it changes the spread of your season’s outcomes, not by a return series. Each contract
          settles once, the related markets have only a short listing history, and the link between a market and any one
          person’s income can’t be observed historically. A backtest built on those gaps would look precise and mean little.
        </Notice>
        <p className="muted">
          What Hone shows instead is the full outcome comparison for your own inputs — income in each scenario with and
          without the hedge, the cost, and how the answer changes as the contract’s link to your income weakens.
        </p>
        <div className="row">
          <Button to={appPath(s, 'hedge')} iconRight="ArrowRight01Icon">Compare outcomes for your season</Button>
          <Button variant="secondary" to={docPath(s, 'methodology', 'prediction-markets', '9-what-this-cannot-do')}>What this cannot do</Button>
        </div>
      </div>
    </div>
  );
}
