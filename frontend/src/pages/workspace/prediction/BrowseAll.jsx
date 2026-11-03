/*
 * BrowseAll — every open Kalshi market, searchable (Markets page → "All
 * Kalshi markets").
 *
 *   search box + category chips → a list of events (30 at a time, "Show more")
 *   open an event               → its live markets, with YES and NO prices
 *   "Hedge with YES/NO"         → copies that price into the Income hedge
 *                                 (as "Another exposure") and opens it
 *
 * Data comes from browse.js; the server does the searching. Desktop shows a
 * table per event; phones get expandable rows (same pattern as the curated
 * view), so nothing scrolls the page sideways.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDebounced, useWorkspace } from '../../../lib/store.jsx';
import { appPath } from '../../../lib/products.js';
import { clamp, fmtCents, fmtDate, fmtNum, fmtPct } from '../../../lib/format.js';
import { Badge, Button, ErrorNotice, Expander, Notice, SkeletonRows, Spinner } from '../../../components/ui.jsx';
import { BASIS_DEFAULT } from './catalog.js';
import { PAGE_SIZE, useEventMarkets, useKalshiSearch } from './browse.js';

const SLUG = 'prediction-markets';
/** Categories shown before "More categories". */
const TOP_CATEGORIES = 8;

export default function BrowseAll() {
  const { update } = useWorkspace(SLUG);
  const nav = useNavigate();
  const [text, setText] = useState('');
  const [category, setCategory] = useState('');
  const [allCats, setAllCats] = useState(false);
  const [openTicker, setOpenTicker] = useState(null);
  const q = useDebounced(text.trim(), 250);
  const { data, events, loading, error, hasMore, loadMore, reload } = useKalshiSearch({ q, category });

  /**
   * Use one side of a market in the Income hedge. Browsed markets aren't in
   * the curated picker, so they go in as "Another exposure" with the ask
   * price filled in (marketTicker is kept so the hedge page can say where the
   * price came from).
   */
  const pickContract = (event, market, side) => {
    const ask = side === 'yes' ? market.yes_ask : market.no_ask;
    update(cur => ({
      ...cur,
      pm: {
        ...cur.pm,
        industry: 'manual',
        seriesTicker: event.series_ticker || null,
        marketTicker: market.ticker,
        side,
        price: clamp(ask ?? cur.pm.price, 0.01, 0.99),
        label: `${side.toUpperCase()} · ${market.title}`,
        // A curated series knows how closely it tracks income; otherwise keep the user's setting.
        basis: BASIS_DEFAULT[event.curated?.basis] ?? cur.pm.basis,
      },
    }));
    nav(appPath(SLUG, 'hedge'));
  };

  const cats = data?.categories || [];
  const shownCats = allCats ? cats : cats.slice(0, TOP_CATEGORIES);

  return (
    <div className="stack-lg">
      <IndexStatus data={data} />

      <div className="stack">
        <label className="sr-only" htmlFor="pm-search">Search Kalshi markets</label>
        <input
          id="pm-search"
          type="search"
          value={text}
          onChange={e => { setText(e.target.value); setOpenTicker(null); }}
          placeholder="Search every market — e.g. Fed, bitcoin, unemployment, Lakers, snowfall"
          autoComplete="off"
        />

        {/* Category chips. Counts are for the current search. */}
        {cats.length > 0 && (
          <div className="pm-cats" role="group" aria-label="Category">
            <button type="button" className="pilltab" aria-pressed={!category} onClick={() => setCategory('')}>
              All <span className="pm-cats__n">{fmtNum(cats.reduce((n, c) => n + c.count, 0))}</span>
            </button>
            {shownCats.map(c => (
              <button key={c.name} type="button" className="pilltab" aria-pressed={category === c.name}
                onClick={() => setCategory(category === c.name ? '' : c.name)}>
                {c.name} <span className="pm-cats__n">{fmtNum(c.count)}</span>
              </button>
            ))}
            {cats.length > TOP_CATEGORIES && (
              <button type="button" className="pilltab" onClick={() => setAllCats(v => !v)}>
                {allCats ? 'Fewer' : `+${cats.length - TOP_CATEGORIES} more`}
              </button>
            )}
          </div>
        )}
      </div>

      {error && <ErrorNotice error={error} onRetry={reload} />}
      {loading && !events.length && <div className="card"><SkeletonRows rows={6} /></div>}
      {!loading && data && !events.length && (
        <div className="card"><p className="muted">No open markets match “{q}”{category ? ` in ${category}` : ''}.</p></div>
      )}

      {events.length > 0 && (
        <div className="stack">
          <p className="small muted" aria-live="polite">
            {fmtNum(data.total)} event{data.total === 1 ? '' : 's'}{q ? ` matching “${q}”` : ''}{category ? ` in ${category}` : ''}
          </p>
          {events.map(ev => (
            <EventCard
              key={ev.event_ticker}
              event={ev}
              open={openTicker === ev.event_ticker}
              onToggle={() => setOpenTicker(t => (t === ev.event_ticker ? null : ev.event_ticker))}
              onUse={(m, side) => pickContract(ev, m, side)}
            />
          ))}
          {hasMore && (
            <div className="row" style={{ justifyContent: 'center' }}>
              <Button variant="secondary" onClick={loadMore} disabled={loading}>
                {loading ? 'Loading…' : `Show ${Math.min(PAGE_SIZE, data.total - events.length)} more`}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------ IndexStatus */
/** Where the list comes from, said plainly (live, still indexing, or offline). */
function IndexStatus({ data }) {
  if (!data) return null;
  if (data.source === 'live') {
    return (
      <Notice tone="info">
        Every open Kalshi event — {fmtNum(data.indexed)} of them, indexed {fmtDate(data.as_of)}. Prices load live when you open one.
      </Notice>
    );
  }
  if (data.source === 'live-partial') {
    return (
      <Notice tone="attention" title="Still indexing Kalshi…">
        {fmtNum(data.indexed)} events so far; the full list takes a few minutes the first time. Results update on their own.
      </Notice>
    );
  }
  return (
    <Notice tone="attention" title={data.live_enabled ? 'Connecting to Kalshi…' : 'Offline snapshot'}>
      {data.live_enabled
        ? 'Showing the curated markets until the first page of the full list arrives.'
        : 'This server is set to offline mode (HONE_KALSHI_LIVE=0), so only the curated markets from the bundled snapshot are listed.'}
    </Notice>
  );
}

/* ------------------------------------------------------------ EventCard */
function EventCard({ event: ev, open, onToggle, onUse }) {
  const bodyId = `ev-${ev.event_ticker}`;
  return (
    <section className="card pm-event">
      <button type="button" className="pm-event__head" aria-expanded={open} aria-controls={bodyId} onClick={onToggle}>
        <span style={{ minWidth: 0 }}>
          <span className="pm-event__title">{ev.title}</span>
          {ev.sub_title && <span className="pm-event__sub">{ev.sub_title}</span>}
          <span className="tiny subtle">{ev.event_ticker}</span>
        </span>
        <span className="pm-event__badges">
          {ev.curated && <Badge tone="live" title={`In the curated catalog under ${ev.curated.industry_label}`}>Income hedge</Badge>}
          <Badge>{ev.category}</Badge>
          <span aria-hidden="true" className="pm-event__chev">{open ? '▾' : '▸'}</span>
        </span>
      </button>
      {open && <div id={bodyId} className="mt-4"><EventMarkets event={ev} onUse={onUse} /></div>}
    </section>
  );
}

/* ------------------------------------------------------------ EventMarkets */
function EventMarkets({ event: ev, onUse }) {
  const { detail, loading, error, reload } = useEventMarkets(ev.event_ticker);
  if (error && !detail) return <ErrorNotice error={error} onRetry={reload} />;
  if (loading || !detail) return <Spinner>Loading live prices…</Spinner>;
  const markets = detail.markets;
  if (!markets.length) return <p className="small muted">No open markets in this event right now.</p>;

  return (
    <>
      {ev.curated && (
        <p className="small muted mb-3">
          Part of the curated <b>{ev.curated.industry_label}</b> catalog — hedgers usually buy {ev.curated.bad_side}.
        </p>
      )}
      <p className="tiny subtle mb-3">
        {detail.source === 'live' ? `Live prices · ${fmtDate(detail.as_of)}` : `Snapshot prices · ${fmtDate(detail.as_of)}`}
        {' · '}Buy the side that pays when your income takes the hit.
      </p>

      {/* Desktop / tablet: a table */}
      <div className="tscroll pm-table">
        <table>
          <thead>
            <tr>
              <th>Market</th>
              <th className="r">YES ask</th>
              <th className="r">NO ask</th>
              <th className="r">Odds of YES</th>
              <th className="r">Volume</th>
              <th>Closes</th>
              <th><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {markets.map(m => (
              <tr key={m.ticker}>
                <td>
                  <div className="strong small">{m.label || m.title}</div>
                  <Expander summary={<span className="tiny">Settlement rule</span>}>
                    <span className="small">{m.rules || m.title}</span>
                  </Expander>
                </td>
                <td className="r">{fmtCents(m.yes_ask)}</td>
                <td className="r">{fmtCents(m.no_ask)}</td>
                <td className="r">{fmtPct(m.implied ?? m.last)}</td>
                <td className="r">{fmtNum(m.volume)}</td>
                <td className="nowrap">{fmtDate(m.close_time)}</td>
                <td className="r nowrap">
                  <SideButtons market={m} onUse={side => onUse(m, side)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Phones: one expandable row per market */}
      <div className="pm-rows">
        {markets.map(m => (
          <Expander key={m.ticker}
            summary={
              <div className="row row--between" style={{ flexWrap: 'nowrap' }}>
                <span className="strong small">{m.label || m.title}</span>
                <span className="small num nowrap">Y {fmtCents(m.yes_ask)} · N {fmtCents(m.no_ask)}</span>
              </div>
            }>
            <dl className="pm-facts">
              <div><dt>Odds of YES</dt><dd>{fmtPct(m.implied ?? m.last)}</dd></div>
              <div><dt>Volume</dt><dd>{fmtNum(m.volume)}</dd></div>
              <div><dt>Closes</dt><dd>{fmtDate(m.close_time)}</dd></div>
              <div><dt>Settlement rule</dt><dd>{m.rules || m.title}</dd></div>
            </dl>
            <div className="row mt-3"><SideButtons market={m} onUse={side => onUse(m, side)} /></div>
          </Expander>
        ))}
      </div>
    </>
  );
}

/** "Hedge with YES" / "Hedge with NO" — disabled when that side has no usable ask. */
function SideButtons({ market: m, onUse }) {
  const usable = ask => typeof ask === 'number' && ask > 0 && ask < 1;
  return (
    <span className="row" style={{ gap: 6, justifyContent: 'flex-end', flexWrap: 'nowrap' }}>
      <Button size="sm" variant="secondary" disabled={!usable(m.yes_ask)} onClick={() => onUse('yes')}>Hedge with YES</Button>
      <Button size="sm" variant="secondary" disabled={!usable(m.no_ask)} onClick={() => onUse('no')}>Hedge with NO</Button>
    </span>
  );
}
