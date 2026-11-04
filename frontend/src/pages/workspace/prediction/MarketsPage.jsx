/*
 * Markets — Prediction Markets workspace (/prediction-markets/app/markets)
 *
 * Browse the curated Kalshi catalog by industry. Each series says, in words,
 * how closely it tracks real income (direct / close / proxy), which side a
 * hedger buys, and lists its open markets. "Use this contract" copies the
 * market into the Income hedge inputs (ws.pm) and opens that tool.
 *
 * Desktop shows a table per series; phones get expandable rows instead,
 * so nothing ever scrolls the page sideways.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../../../lib/store.jsx';
import { appPath } from '../../../lib/products.js';
import { clamp, fmtCents, fmtDate, fmtNum, fmtPct } from '../../../lib/format.js';
import { Badge, Button, ErrorNotice, Expander, Notice, PageHeader, SkeletonRows } from '../../../components/ui.jsx';
import { askFor, badSideOf, BASIS_DEFAULT, BASIS_TEXT, isLive, probFor, sourceLabel, usePredictionCatalog } from './catalog.js';
import './prediction.css';

const SLUG = 'prediction-markets';

export default function MarketsPage() {
  const { ws, update } = useWorkspace(SLUG);
  const { catalog, loading, error, reload } = usePredictionCatalog();
  const nav = useNavigate();
  // Which industry tab is showing; starts on the one the hedge tool uses.
  const [tab, setTab] = useState(ws.pm.industry && ws.pm.industry !== 'manual' ? ws.pm.industry : 'snow');
  const [openOnly, setOpenOnly] = useState(false);

  const industry = catalog?.industries.find(i => i.key === tab) || catalog?.industries[0];

  /** Copy a market into the Income hedge inputs and go there. */
  const pickContract = (ind, series, market) => {
    const side = badSideOf(series);
    update(cur => ({
      ...cur,
      pm: {
        ...cur.pm,
        industry: ind.key,
        seriesTicker: series.ticker,
        marketTicker: market.ticker,
        side,
        price: clamp(askFor(market, side) ?? cur.pm.price, 0.01, 0.99),
        label: market.title,
        basis: BASIS_DEFAULT[series.basis] ?? cur.pm.basis,
      },
    }));
    nav(appPath(SLUG, 'hedge'));
  };

  return (
    <div className="pm">
      <PageHeader
        eyebrow="Income hedging"
        title="Markets that move with a paycheck"
        lede="Kalshi event contracts grouped by the kind of income they can offset. Pick one to size a hedge against your own season."
        meta={catalog && <Badge tone={isLive(catalog) ? 'live' : 'sample'}>{isLive(catalog) ? 'Live markets' : 'Market snapshot'}</Badge>}
      />

      {catalog && <Notice tone={isLive(catalog) ? 'info' : 'attention'} className="mb-5">{sourceLabel(catalog)}</Notice>}
      {error && <div className="mb-5"><ErrorNotice error={error} onRetry={reload} /></div>}
      {loading && <div className="card"><SkeletonRows rows={6} /></div>}

      {catalog && (
        <>
          {/* Industry tabs */}
          <div className="tabs mb-4" role="tablist" aria-label="Industry">
            {catalog.industries.map(ind => (
              <button key={ind.key} type="button" role="tab" className="tab" aria-selected={ind.key === industry?.key}
                onClick={() => setTab(ind.key)}>
                {ind.label}
              </button>
            ))}
          </div>

          {industry && (
            <div className="stack-lg">
              <div className="row row--between">
                <p className="muted" style={{ maxWidth: '70ch' }}>{industry.who}</p>
                <label className="row small" style={{ color: 'var(--ink)' }}>
                  <input type="checkbox" checked={openOnly} onChange={e => setOpenOnly(e.target.checked)} style={{ width: 20, height: 20 }} />
                  Only series with open markets
                </label>
              </div>

              {industry.series
                .filter(s => !openOnly || s.markets.length)
                .map(series => (
                  <SeriesCard key={series.ticker} series={series} onUse={m => pickContract(industry, series, m)}
                    selectedTicker={ws.pm.marketTicker} />
                ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------ SeriesCard */
function SeriesCard({ series, onUse, selectedTicker }) {
  const side = badSideOf(series);
  const SIDE = side.toUpperCase();
  return (
    <section className="card" aria-labelledby={`s-${series.ticker}`}>
      <div className="card__head">
        <div style={{ minWidth: 0 }}>
          <h2 id={`s-${series.ticker}`} className="card__title">{series.title}</h2>
          <p className="card__sub"><span className="tiny subtle">{series.ticker}</span></p>
        </div>
        <Badge>{series.markets.length ? `${series.markets.length} open` : 'None open'}</Badge>
      </div>

      <dl className="pm-facts">
        <div><dt>How closely it tracks income</dt><dd>{BASIS_TEXT[series.basis] || series.basis}</dd></div>
        <div><dt>Hedgers buy</dt><dd>{series.bad_side} — the side that pays in a bad season</dd></div>
        {series.note && <div><dt>Note</dt><dd>{series.note}</dd></div>}
      </dl>

      {!series.markets.length ? (
        <p className="small muted mt-3">No open markets in this series right now. They usually list as the season approaches.</p>
      ) : (
        <>
          {/* Desktop / tablet: a table */}
          <div className="tscroll pm-table mt-4">
            <table>
              <thead>
                <tr>
                  <th>Market</th>
                  <th className="r">{SIDE} ask</th>
                  <th className="r">Market odds</th>
                  <th className="r">Spread</th>
                  <th className="r">Volume</th>
                  <th>Closes</th>
                  <th><span className="sr-only">Action</span></th>
                </tr>
              </thead>
              <tbody>
                {series.markets.map(m => (
                  <tr key={m.ticker} className={m.ticker === selectedTicker ? 'pm-sens__current' : undefined}>
                    <td>
                      <div className="strong small">{m.label || m.title}</div>
                      <Expander summary={<span className="tiny">Settlement rule</span>}>
                        <span className="small">{m.rules || m.title}</span>
                      </Expander>
                    </td>
                    <td className="r">{fmtCents(askFor(m, side))}</td>
                    <td className="r">{fmtPct(probFor(m, side))}</td>
                    <td className="r">{m.spread == null ? '—' : fmtCents(m.spread)}</td>
                    <td className="r">{fmtNum(m.volume)}</td>
                    <td className="nowrap">{fmtDate(m.close_time)}</td>
                    <td className="r"><Button size="sm" variant="secondary" onClick={() => onUse(m)}>Use this contract</Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Phones: one expandable row per market */}
          <div className="pm-rows mt-3">
            {series.markets.map(m => (
              <Expander key={m.ticker}
                summary={
                  <div className="row row--between" style={{ flexWrap: 'nowrap' }}>
                    <span className="strong small">{m.label || m.title}</span>
                    <span className="small num">{SIDE} {fmtCents(askFor(m, side))}</span>
                  </div>
                }>
                <dl className="pm-facts">
                  <div><dt>Market odds</dt><dd>{fmtPct(probFor(m, side))} that {SIDE} pays</dd></div>
                  <div><dt>Spread · volume</dt><dd>{m.spread == null ? '—' : fmtCents(m.spread)} · {fmtNum(m.volume)}</dd></div>
                  <div><dt>Closes</dt><dd>{fmtDate(m.close_time)}</dd></div>
                  <div><dt>Settlement rule</dt><dd>{m.rules || m.title}</dd></div>
                </dl>
                <Button size="sm" className="mt-3" onClick={() => onUse(m)}>Use this contract</Button>
              </Expander>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
