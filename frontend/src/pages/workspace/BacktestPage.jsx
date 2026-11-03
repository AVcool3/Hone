/*
 * Backtest — "what happened historically?" for YOUR risk level.
 *
 * Runs /api/backtest: a walk-forward simulation of the tier-matched
 * portfolio against simple alternatives, then the same curves with the
 * investor allowed to panic-sell (the behaviour gap). Results are large, so
 * they're kept in memory only (re-run after a reload).
 *
 * The research backtests (population-level, many investors) live on the
 * public Backtests page; this one is a single historical path.
 */
import { Link } from 'react-router-dom';
import { useProduct } from '../../App.jsx';
import { LineChart, Legend, SERIES } from '../../components/charts.jsx';
import { Badge, Button, ErrorNotice, Notice, PageHeader, SectionTitle, SkeletonRows, StaleBanner } from '../../components/ui.jsx';
import { useEngineResult } from '../../lib/hooks.js';
import { appPath, docPath } from '../../lib/products.js';
import { fmtDate, fmtMoney, fmtPct, fmtSPct } from '../../lib/format.js';

const backtestRequest = (gamma, ws) => ({ gamma, max_weight: ws.maxWeight });

export default function BacktestPage() {
  const product = useProduct();
  const res = useEngineResult(product.slug, 'backtest', '/api/backtest', backtestRequest, { persist: false });
  const r = res.result;

  return (
    <>
      <PageHeader
        eyebrow="Historical simulation"
        title="Backtest"
        lede="How a portfolio matched to your risk level would have done over the last five years of prices — next to simple alternatives, and next to what a real person holding it might have got."
        actions={<Button icon={r ? 'RefreshIcon' : 'ChartLineData02Icon'} onClick={res.run} disabled={res.busy}>{res.busy ? 'Simulating…' : r ? 'Run again' : 'Run backtest'}</Button>}
        meta={<><Badge tone={product.slug === 'crypto' ? 'sample' : 'sample'}>Historical simulation · not a forecast</Badge><Link className="tiny" to={docPath(product.slug, 'backtests')}>Research backtests across many investors</Link></>}
      />
      {res.stale && <div className="mb-4"><StaleBanner onRecalc={res.run} busy={res.busy} what="this backtest" /></div>}
      <ErrorNotice error={res.error} onRetry={res.run} settingsTo={appPath(product.slug, 'settings')} />
      {!r && !res.busy && !res.error && (
        <Notice>Takes a few seconds. Uses {product.slug === 'crypto' ? 'daily crypto prices (365 days a year)' : 'daily stock prices'} from {product.slug === 'crypto' ? 'the sample coins' : 'the sample universe'} or your paper account, rebalanced monthly, with your current position limit.</Notice>
      )}
      {res.busy && !r && <div className="card"><SkeletonRows rows={6} /></div>}

      {r && (
        <div className="stack-lg">
          <div className="card">
            <p className="takeaway">{r.headline}</p>
            <Legend items={r.strategies.map((s, i) => ({ label: s.label, color: SERIES[i % SERIES.length], dashed: i > 0 && i % 2 === 0 }))} />
            <div className="mt-3">
              <LineChart
                series={r.strategies.map((s, i) => ({ label: s.label, values: s.equity_curve, color: SERIES[i % SERIES.length], dashed: i > 0 && i % 2 === 0 }))}
                dates={r.strategies[0]?.dates}
                ariaLabel={`Growth of $10,000 from ${r.start} to ${r.end}`}
              />
            </div>
            <p className="chart-caption">Growth of $10,000, {fmtDate(r.start)} – {fmtDate(r.end)}, {r.rebalances} rebalances. Historical simulation on {r.strategies[0] ? 'past prices' : ''}; no trading costs in these curves.</p>
          </div>

          <div className="card">
            <SectionTitle title="The numbers" />
            <div className="tscroll">
              <table>
                <thead><tr><th>Strategy</th><th className="r">Growth a year</th><th className="r">Volatility</th><th className="r">Sharpe</th><th className="r">Worst drawdown</th><th className="r">Worst month</th><th className="r">$10k became</th></tr></thead>
                <tbody>
                  {r.strategies.map(s => (
                    <tr key={s.name}>
                      <td>{s.name === 'tier_matched' ? <b>{s.label}</b> : s.label}</td>
                      <td className={`r ${s.metrics.cagr < 0 ? 'loss' : ''}`}>{fmtSPct(s.metrics.cagr)}</td>
                      <td className="r">{fmtPct(s.metrics.volatility)}</td>
                      <td className="r">{s.metrics.sharpe.toFixed(2)}</td>
                      <td className="r loss">{fmtPct(-s.metrics.max_drawdown)}</td>
                      <td className="r loss">{fmtPct(-s.metrics.worst_month)}</td>
                      <td className="r">{fmtMoney(10000 * s.metrics.final_multiple)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {r.behavior && <BehaviorGap b={r.behavior} />}
        </div>
      )}
    </>
  );
}

/* What you'd actually have got: the same strategies held by a person who sells when it hurts. */
function BehaviorGap({ b }) {
  return (
    <div className="card">
      <SectionTitle title="What you’d actually have got" sub="Every number above assumes you held through everything — including the worst of it. Almost nobody does." />
      <p className="takeaway">{b.summary}</p>
      <div className="tscroll">
        <table>
          <thead><tr><th>Strategy</th><th className="r">On paper</th><th className="r">As held</th><th className="r">Gap</th><th className="r">Panic sells</th><th className="r">Time in cash</th></tr></thead>
          <tbody>
            {b.rows.map(row => (
              <tr key={row.name}>
                <td>{row.label}</td>
                <td className="r">{fmtSPct(row.paper_cagr)}</td>
                <td className="r">{fmtSPct(row.realized_cagr)}</td>
                <td className={`r ${row.behavior_gap > 0 ? 'loss' : ''}`}>{fmtSPct(-row.behavior_gap)}</td>
                <td className="r">{row.panics}</td>
                <td className="r">{fmtPct(row.time_in_cash)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="tiny subtle mt-3">
        The sell rule isn’t invented: your risk level sets a tolerable loss ({fmtPct(b.panic_threshold)} here) through the same Merton budget the hedge plan uses, and
        the investor is modelled as capitulating past it. Buying back waits until the market has climbed 10% off its low — which is what makes it expensive.
        Trading costs are charged at 10bp a switch and cash earns 4%.
      </p>
      <Notice className="mt-3" tone={b.ranking_changed ? 'attention' : 'plain'}>
        {b.ranking_changed
          ? <><b>The ranking changed.</b> {b.best_on_paper} wins on paper; {b.best_as_held} wins once you’re allowed to be a person. That argues for sizing to what you can sit through — but this is one path, and single paths are noisy.</>
          : <>The ranking held: {b.best_on_paper} wins either way on this path. This is one path, and single paths are noisy.</>}
      </Notice>
    </div>
  );
}
