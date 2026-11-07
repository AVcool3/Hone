/*
 * Income hedge — Prediction Markets workspace (/prediction-markets/app/hedge)
 *
 * A task flow, not an essay. The left column walks through four inputs:
 *   1. Which kind of income exposure (an industry from the catalog, or "another")
 *   2. How big it is (money for the season, and what a bad season costs)
 *   3. Which contract could offset it (series → market → side), with YOUR
 *      loss event and the CONTRACT'S settlement condition shown side by side,
 *      plus how closely the two move together (basis correlation)
 *   4. Optionally, your own view of the odds
 * The right panel recalculates live (POST /api/predict/hedge, ~10 ms) and
 * leads with the outcome comparison: income after costs in each scenario,
 * with and without the hedge.
 *
 * All inputs live in ws.pm (lib/store.jsx) so they survive navigation and
 * reloads. Hone only sizes — it never places an order.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../../lib/api.js';
import { useDebounced, useLatestRequest, useRisk, useWorkspace } from '../../../lib/store.jsx';
import { appPath, docPath } from '../../../lib/products.js';
import { clamp, fmtCents, fmtDate, fmtGamma, fmtMoney, fmtNum, fmtPct, fmtSMoney } from '../../../lib/format.js';
import {
  Badge, ErrorNotice, Expander, Field, Notice, NumberSlider, PageHeader, Segmented,
  SkeletonRows, Spinner, Stat,
} from '../../../components/ui.jsx';
import { OutcomeBars } from '../../../components/charts.jsx';
import {
  askFor, badSideOf, BASIS_DEFAULT, BASIS_TEXT, isLive, probFor, sourceLabel, usePredictionCatalog,
} from './catalog.js';
import './prediction.css';

const SLUG = 'prediction-markets';

/* Risk-aversion values for the sensitivity table (same spread as the tiers). */
const GAMMA_GRID = [0.5, 1, 2, 3, 5, 8];
/* Basis correlations for the second sensitivity table. */
const BASIS_GRID = [1, 0.8, 0.6, 0.4];

/* A price of exactly 0¢ or 100¢ is a settled market; the engine needs (0, 1). */
const MIN_PRICE = 0.01;
const MAX_PRICE = 0.99;

/** Human label for one of the (contract pays?, income lost?) states. */
function stateLabel(st) {
  if (st.loss && st.pays) return 'Bad season, contract pays';
  if (st.loss && !st.pays) return 'Bad season, contract doesn’t pay';
  if (!st.loss && st.pays) return 'Good season, contract pays';
  return 'Good season';
}

export default function IncomeHedgePage() {
  const { ws, update } = useWorkspace(SLUG);
  const { gamma, isSample, profile } = useRisk();
  const { catalog, loading: catLoading, error: catError, reload } = usePredictionCatalog();
  const pm = ws.pm;

  /** Patch the prediction-markets inputs (merged into ws.pm). */
  const setPm = patch => update(cur => ({ ...cur, pm: { ...cur.pm, ...patch } }));

  /* ---------------------------------------------------------- selection */
  const manual = pm.industry === 'manual';
  const industry = catalog?.industries.find(i => i.key === pm.industry) || null;

  // Series: the one the user picked, else the first one with open markets.
  const series = useMemo(() => {
    if (!industry) return null;
    return (
      industry.series.find(s => s.ticker === pm.seriesTicker) ||
      industry.series.find(s => s.markets.length) ||
      industry.series[0]
    );
  }, [industry, pm.seriesTicker]);

  const market = series?.markets.find(m => m.ticker === pm.marketTicker) || null;
  // The user's chosen market disappeared from a refreshed catalog.
  const marketMissing = !!pm.marketTicker && !!series && !market && pm.seriesTicker === series.ticker;

  // Side that pays in a bad season. Defaults from the catalog; user can override.
  const side = pm.side || badSideOf(series);

  // Price: a chosen market's ask for that side; otherwise the typed illustrative price.
  const rawAsk = market ? askFor(market, side) : null;
  const price = clamp(rawAsk ?? pm.price ?? 0.3, MIN_PRICE, MAX_PRICE);
  const priceIsIllustrative = !market;
  const askOutOfRange = market && (rawAsk == null || rawAsk <= MIN_PRICE || rawAsk >= MAX_PRICE);
  const marketProb = market ? probFor(market, side) : null;

  const hasView = typeof pm.ownProb === 'number';
  const calibration = ws.useCalibration !== false && ws.calibration?.actionable ? ws.calibration : null;

  /* ---------------------------------------------------------- the request */
  const body = useMemo(() => {
    const b = {
      gamma,
      wealth: pm.wealth,
      loss: pm.loss,
      price,
      basis_correlation: clamp(pm.basis ?? 1, 0, 1),
      market_ticker: market?.ticker ?? null,
      side,
    };
    if (marketProb != null) b.market_prob = clamp(marketProb, MIN_PRICE, MAX_PRICE);
    if (hasView) {
      b.own_prob = clamp(pm.ownProb, 0, 1);
      b.confidence = clamp(pm.confidence ?? 0, 0, 1);
      if (calibration) b.calibration = calibration;
    }
    return b;
  }, [gamma, pm.wealth, pm.loss, price, pm.basis, market, side, marketProb, hasView, pm.ownProb, pm.confidence, calibration]);

  const inputError =
    !(pm.wealth > 0) ? 'Enter how much money you have for the season.'
      : !(pm.loss >= 0) ? 'Enter what a bad season would cost you (0 or more).'
        : pm.loss > pm.wealth ? 'A bad season can’t cost more than the money you have for it — check the two amounts.'
          : null;

  // Recalculate ~300 ms after the inputs stop changing; keep the last good result meanwhile.
  const debounced = useDebounced(JSON.stringify(body), 300);
  const latest = useLatestRequest();
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0); // bump to retry

  useEffect(() => {
    if (inputError) return;
    setBusy(true);
    latest(signal =>
      api('prediction', '/api/predict/hedge', JSON.parse(debounced), { signal })
        .then(data => { setResult(data); setError(null); setBusy(false); })
        .catch(e => { if (e.name !== 'AbortError') { setError(e); setBusy(false); } }),
    );
  }, [debounced, tick, inputError, latest]);

  /* ---------------------------------------------------------- sensitivity */
  // Same request at other risk-aversion levels and other basis correlations.
  const [sens, setSens] = useState(null);
  const sensLatest = useLatestRequest();
  useEffect(() => {
    if (inputError || !result) return;
    const base = JSON.parse(debounced);
    sensLatest(signal =>
      Promise.all([
        Promise.all(GAMMA_GRID.map(g => api('prediction', '/api/predict/hedge', { ...base, gamma: g }, { signal }))),
        Promise.all(BASIS_GRID.map(b => api('prediction', '/api/predict/hedge', { ...base, basis_correlation: b }, { signal }))),
      ])
        .then(([byGamma, byBasis]) => setSens({ byGamma, byBasis }))
        .catch(() => {}), // sensitivity is secondary; the main result shows any error
    );
    // only after a main result for these inputs exists
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  /* ---------------------------------------------------------- handlers */
  const chooseIndustry = key => setPm({ industry: key, seriesTicker: null, marketTicker: null, side: null });
  const chooseSeries = ticker => {
    const s = industry?.series.find(x => x.ticker === ticker);
    setPm({ seriesTicker: ticker, marketTicker: null, side: null, basis: BASIS_DEFAULT[s?.basis] ?? pm.basis });
  };
  const chooseMarket = m => {
    const sd = side;
    setPm({
      seriesTicker: series.ticker,
      marketTicker: m.ticker,
      side: sd,
      price: clamp(askFor(m, sd) ?? pm.price, MIN_PRICE, MAX_PRICE),
      label: m.title,
    });
  };

  /* ---------------------------------------------------------- render */
  return (
    <div className="pm">
      <PageHeader
        eyebrow="Income hedging"
        title="Hedge the income risk you already carry"
        lede="Describe what a bad season would cost you, pick an event contract that pays when that happens, and see your season with and without it. Hone only sizes the hedge — it never places orders."
        meta={
          <>
            {isSample ? (
              <>
                <Badge tone="sample">Sample risk profile</Badge>
                <Link className="tiny" to={appPath(SLUG, 'risk')}>Measure yours</Link>
              </>
            ) : (
              <Badge tone="yours" title="Your measured risk aversion">
                Your risk aversion {fmtGamma(gamma)}{profile.tier ? ` · ${profile.tier.category}` : ''}
              </Badge>
            )}
            {catalog && <Badge tone={isLive(catalog) ? 'live' : 'sample'}>{isLive(catalog) ? 'Live markets' : 'Market snapshot'}</Badge>}
          </>
        }
      />

      <div className="ws-cols">
        {/* ============================================ inputs (main column) */}
        <div className="pm-steps">
          {/* ---- 1. Scenario ---------------------------------------- */}
          <section className="card pm-step" aria-labelledby="pm-s1">
            <div className="pm-step__head">
              <span className="pm-step__num" aria-hidden="true">1</span>
              <div>
                <h2 id="pm-s1" className="card__title">What kind of income is at risk?</h2>
                <p className="card__sub">Pick the closest match. It decides which contracts are worth looking at.</p>
              </div>
            </div>
            {catLoading && <SkeletonRows rows={3} />}
            {catError && <ErrorNotice error={catError} onRetry={reload} />}
            <div className="pm-industries">
              {catalog?.industries.map(ind => (
                <button key={ind.key} type="button" className="choice pm-industry" aria-pressed={pm.industry === ind.key}
                  onClick={() => chooseIndustry(ind.key)}>
                  <div className="pm-industry__label">{ind.label}</div>
                  <div className="pm-industry__who">{ind.who}</div>
                </button>
              ))}
              <button type="button" className="choice pm-industry" aria-pressed={manual} onClick={() => chooseIndustry('manual')}>
                <div className="pm-industry__label">Another exposure</div>
                <div className="pm-industry__who">Commissions, business revenue or anything else — you supply the contract price.</div>
              </button>
            </div>
          </section>

          {/* ---- 2. Exposure ---------------------------------------- */}
          <section className="card pm-step" aria-labelledby="pm-s2">
            <div className="pm-step__head">
              <span className="pm-step__num" aria-hidden="true">2</span>
              <div>
                <h2 id="pm-s2" className="card__title">How big is the exposure?</h2>
                <p className="card__sub">Rough numbers are fine — the result shows how much they matter.</p>
              </div>
            </div>
            <div className="stack">
              <Field label="Money you have for the season" htmlFor="pm-wealth"
                hint="Expected earnings plus the savings a bad season would eat into.">
                <NumberSlider id="pm-wealth" ariaLabel="Money for the season" value={pm.wealth} onChange={v => setPm({ wealth: v })}
                  min={1000} max={250000} step={500} prefix="$" inputWidth={140} />
              </Field>
              <Field label="What a bad season would cost you" htmlFor="pm-loss"
                hint="The income you’d lose if things go wrong — fewer bookings, smaller commissions, a short season.">
                <NumberSlider id="pm-loss" ariaLabel="Cost of a bad season" value={pm.loss} onChange={v => setPm({ loss: v })}
                  min={0} max={Math.max(1000, pm.wealth || 0)} step={250} prefix="$" inputWidth={140} />
              </Field>
              {inputError && <Notice tone="attention">{inputError}</Notice>}
            </div>
          </section>

          {/* ---- 3. Contract ---------------------------------------- */}
          <section className="card pm-step" aria-labelledby="pm-s3">
            <div className="pm-step__head">
              <span className="pm-step__num" aria-hidden="true">3</span>
              <div>
                <h2 id="pm-s3" className="card__title">Which contract pays when it goes wrong?</h2>
                <p className="card__sub">An event contract pays $1 if its event happens. You want the side that pays in your bad season.</p>
              </div>
            </div>

            {/* Where the prices came from — right next to the picker, not in a footnote. */}
            {catalog && !manual && (
              <Notice tone={isLive(catalog) ? 'info' : 'attention'} className="mb-4">
                {sourceLabel(catalog)}
              </Notice>
            )}

            {catLoading && !manual ? (
              <SkeletonRows rows={3} />
            ) : manual || !industry ? (
              <ManualPrice pm={pm} setPm={setPm} />
            ) : (
              <div className="stack">
                <Field label="Contract series" htmlFor="pm-series">
                  <select id="pm-series" value={series?.ticker || ''} onChange={e => chooseSeries(e.target.value)}>
                    {industry.series.map(s => (
                      <option key={s.ticker} value={s.ticker}>
                        {s.title} — {s.markets.length ? `${s.markets.length} open` : 'none open'}
                      </option>
                    ))}
                  </select>
                </Field>

                {series && (
                  <div className="pm-series-info">
                    <Badge>{series.basis}</Badge>
                    <span className="small muted">{BASIS_TEXT[series.basis] || series.basis}</span>
                    {series.note && <p className="tiny subtle" style={{ flexBasis: '100%' }}>{series.note}</p>}
                  </div>
                )}

                {series && !series.markets.length ? (
                  <>
                    <Notice tone="attention" title="No open markets in this series right now.">
                      Contracts in this series list closer to the season. You can still size a hedge with an illustrative price.
                    </Notice>
                    <ManualPrice pm={pm} setPm={setPm} />
                  </>
                ) : (
                  series && (
                    <>
                      <Field label="Side that pays in your bad season"
                        hint={`Catalog default: ${series.bad_side}. Change it only if your bad outcome is the other way round.`}>
                        <Segmented label="Contract side" value={side}
                          options={[{ value: 'yes', label: 'YES' }, { value: 'no', label: 'NO' }]}
                          onChange={v => setPm({ side: v, price: clamp(askFor(market, v) ?? pm.price, MIN_PRICE, MAX_PRICE) })} />
                      </Field>

                      <div role="radiogroup" aria-label="Open markets" className="pm-markets">
                        {series.markets.map(m => {
                          const ask = askFor(m, side);
                          const selected = m.ticker === pm.marketTicker;
                          return (
                            <button key={m.ticker} type="button" role="radio" aria-checked={selected}
                              className={`pm-market ${selected ? 'is-selected' : ''}`} onClick={() => chooseMarket(m)}>
                              <span className="pm-market__label">{m.label || m.title}</span>
                              <span className="pm-market__meta">
                                <span>{side.toUpperCase()} ask <b>{fmtCents(ask)}</b></span>
                                <span>Market odds {fmtPct(probFor(m, side))}</span>
                                <span>Closes {fmtDate(m.close_time)}</span>
                                <span>Spread {m.spread == null ? '—' : fmtCents(m.spread)}</span>
                                <span>Volume {fmtNum(m.volume)}</span>
                              </span>
                            </button>
                          );
                        })}
                      </div>
                      {!market && (
                        <Notice>
                          {marketMissing
                            ? 'The market you picked is no longer listed. Pick another — the result is using an illustrative price meanwhile.'
                            : `Pick a market to use its price. Until then the result uses an illustrative ${fmtCents(price)}.`}
                        </Notice>
                      )}
                      {askOutOfRange && (
                        <Notice tone="attention">
                          This side is quoted at {fmtCents(rawAsk)} — the market is close to settled. Hone uses {fmtCents(price)}; a
                          strike further from today’s value will tell you more.
                        </Notice>
                      )}
                    </>
                  )
                )}
              </div>
            )}

            {/* Your loss vs. the contract's settlement: the core basis-risk point. */}
            <div className="pm-compare mt-5">
              <div className="pm-compare__col">
                <div className="eyebrow">Your loss happens when</div>
                <p>Your season goes badly and you lose about <b>{fmtMoney(pm.loss)}</b> of income. You define this — no exchange measures it.</p>
              </div>
              <div className="pm-compare__col">
                <div className="eyebrow">This contract pays when</div>
                {market ? (
                  <p>
                    It resolves <b>{side.toUpperCase()}</b>.{' '}
                    <span className="muted">Settlement rule: “{market.rules || market.title}”</span>
                    {side === 'no' && <span className="muted"> — the NO side pays when that does not happen.</span>}
                  </p>
                ) : (
                  <p className="muted">Its official settlement condition — a weather station, a government statistic, a company report.</p>
                )}
              </div>
            </div>
            <Field label="How closely do they move together?" htmlFor="pm-basis"
              hint="1 means the contract pays in exactly your bad seasons. Count past bad seasons in which the contract’s number also came in bad — every miss is a year the hedge paid nothing while your income fell anyway.">
              <NumberSlider id="pm-basis" ariaLabel="Basis correlation" value={pm.basis ?? 1} onChange={v => setPm({ basis: v })}
                min={0} max={1} step={0.05} inputWidth={100} />
            </Field>
          </section>

          {/* ---- 4. Your view (optional) ------------------------------ */}
          <section className="card pm-step" aria-labelledby="pm-s4">
            <div className="pm-step__head">
              <span className="pm-step__num" aria-hidden="true">4</span>
              <div>
                <h2 id="pm-s4" className="card__title">Your view <span className="subtle" style={{ fontWeight: 500 }}>(optional)</span></h2>
                <p className="card__sub">Skip this to take the market’s odds as given — that’s the pure-insurance answer.</p>
              </div>
            </div>
            <Expander summary={<span className="strong">{hasView ? 'Using your own odds' : 'I think the odds are different'}</span>} defaultOpen={hasView}>
              <div className="stack">
                <label className="row small" style={{ color: 'var(--ink)' }}>
                  <input type="checkbox" checked={hasView}
                    onChange={e => setPm(e.target.checked ? { ownProb: marketProb ?? price, confidence: 0.5 } : { ownProb: null, confidence: 0 })}
                    style={{ width: 20, height: 20 }} />
                  Use my own probability
                </label>
                {hasView && (
                  <>
                    <Field label="Your probability that this side pays" htmlFor="pm-own"
                      hint={`The market says ${fmtPct(marketProb ?? price)}.`}>
                      <NumberSlider id="pm-own" ariaLabel="Your probability" value={pm.ownProb} onChange={v => setPm({ ownProb: v })}
                        min={0.01} max={0.99} step={1} scale={100} suffix="%" inputWidth={110} />
                    </Field>
                    <Field label="How much weight to give your view" htmlFor="pm-conf"
                      link={{ to: docPath(SLUG, 'methodology', 'calibration'), label: 'What this means' }}
                      hint="0% ignores your view; 100% replaces the market’s odds with yours. Your track record can rescale this.">
                      <NumberSlider id="pm-conf" ariaLabel="Confidence" value={pm.confidence ?? 0} onChange={v => setPm({ confidence: v })}
                        min={0} max={1} step={5} scale={100} suffix="%" inputWidth={110} />
                    </Field>
                  </>
                )}
              </div>
            </Expander>
          </section>
        </div>

        {/* ============================================ result (right panel) */}
        <aside className="ws-panel" aria-label="Hedge result" aria-busy={busy}>
          <ResultPanel
            result={result}
            busy={busy}
            error={error}
            onRetry={() => setTick(t => t + 1)}
            inputError={inputError}
            price={price}
            priceIsIllustrative={priceIsIllustrative}
            side={side}
            label={market?.label || market?.title || pm.label}
            sens={sens}
            gamma={gamma}
            basis={pm.basis ?? 1}
          />
        </aside>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------ ManualPrice */
/** Typed price for "Another exposure" or a series with nothing open. Always labelled illustrative. */
function ManualPrice({ pm, setPm }) {
  return (
    <div className="stack">
      <Field label="Contract price" htmlFor="pm-price" hint="Illustrative price — not a live market. Use the ask of the side that pays in your bad season.">
        <NumberSlider id="pm-price" ariaLabel="Contract price in cents" value={pm.price ?? 0.3}
          onChange={v => setPm({ price: v, marketTicker: null })} min={0.01} max={0.99} step={1} scale={100} suffix="¢" inputWidth={110} />
      </Field>
      <Field label="What the contract is (optional)" htmlFor="pm-label">
        <input id="pm-label" type="text" value={pm.label || ''} placeholder="e.g. Aspen snowfall below 30 in. in January"
          onChange={e => setPm({ label: e.target.value })} />
      </Field>
    </div>
  );
}

/* ------------------------------------------------------------ ResultPanel */
function ResultPanel({ result: r, busy, error, onRetry, inputError, price, priceIsIllustrative, side, label, sens, gamma, basis }) {
  if (inputError) return <div className="card"><p className="muted">{inputError}</p></div>;
  if (!r && error) return <div className="card"><ErrorNotice error={error} onRetry={onRetry} /></div>;
  if (!r) return <div className="card"><Spinner>Sizing the hedge…</Spinner></div>;

  // Drop impossible states (probability ~0) so the chart only shows real scenarios.
  const states = r.states.filter(st => st.prob > 0.0005);
  const rows = states.map(st => ({ label: stateLabel(st), prob: st.prob, unhedged: st.wealth_unhedged, hedged: st.wealth_hedged }));
  const none = !r.needs_hedge || r.contracts === 0;
  // The market itself is the limit (see hone/prediction/liquidity.py):
  // `tooThin` = the model wants a hedge but nothing can be bought;
  // `capped`  = some can, but fewer than the model wants.
  const tooThin = r.liquidity_capped && r.contracts === 0 && r.contracts_wanted !== 0;
  const capped = r.liquidity_capped && r.contracts !== 0;
  const sideWord = (r.side || side || '').toUpperCase();
  const adjusted = Math.abs((r.confidence_used ?? 0) - (r.confidence_stated ?? 0)) > 0.005;

  return (
    <div className="stack">
      <div className="card">
        {error && <div className="mb-4"><ErrorNotice error={error} onRetry={onRetry} /></div>}
        <div className="row row--between">
          <div className="eyebrow">Model-sized hedge</div>
          {busy && <Spinner>Updating</Spinner>}
        </div>

        {/* Headline: what to buy, or why nothing. */}
        {tooThin ? (
          <h2 className="pm-headline">This market is too small to hedge you</h2>
        ) : none ? (
          <h2 className="pm-headline">No hedge at this price</h2>
        ) : (
          <h2 className="pm-headline">
            {r.direction === 'sell' ? 'Sell' : 'Buy'} {fmtNum(r.contracts)} {sideWord} contracts
          </h2>
        )}
        <p className="small muted mt-1">
          {label ? <>{label} · </> : null}
          {fmtCents(price)} each{priceIsIllustrative && <> · <Badge tone="sample">Illustrative price</Badge></>}
        </p>
        {capped && (
          <div className="pm-coverage mt-3">
            <div className="row row--between small">
              <span>Capped by what the market can supply</span>
              <span className="num strong">{fmtPct(r.coverage)} of the protection you want</span>
            </div>
            <div className="pm-coverage__bar" aria-hidden="true"><i style={{ width: `${Math.min(100, r.coverage * 100)}%` }} /></div>
            <p className="tiny muted mt-1">
              Your risk profile wants {fmtNum(Math.abs(r.contracts_wanted))} contracts; {fmtNum(Math.abs(r.contracts))} can be bought
              {r.liquidity_basis.includes('order book') ? ' near the current price' : ` (10% of the ${fmtNum(r.open_interest ?? 0)} open)`}.
              {r.avg_fill_price ? <> Average price about {fmtCents(r.avg_fill_price)}.</> : null}
            </p>
          </div>
        )}
        {tooThin && (
          <p className="small mt-3">
            Your risk profile wants {fmtNum(Math.abs(r.contracts_wanted))} contracts, but this market has none on offer near this price.
            Try a more heavily traded market that tracks the same risk — economy-wide markets (jobs, inflation, gas, rates) are usually deepest.
          </p>
        )}
        {none && !tooThin && (
          <p className="small mt-3">
            At your risk aversion and this price, the cover costs more than the protection is worth to you — or your loss is
            too small relative to your savings to need it. A cheaper strike, a bigger loss, or a closer contract can change that.
          </p>
        )}

        <div className="mt-5">
          <div className="takeaway">Your season after costs, with and without the hedge</div>
          <div className="pm-legend tiny muted" aria-hidden="true">
            <span><i style={{ background: 'var(--current)' }} /> Without hedge</span>
            <span><i style={{ background: 'var(--proposed)' }} /> With hedge</span>
          </div>
          <OutcomeBars rows={rows} height={240} />
          <p className="chart-caption">Projection for one season, in dollars, at the probabilities shown. Not a forecast of which one happens.</p>
        </div>
      </div>

      {!none && (
        <div className="card">
          <div className="pm-stats">
            <Stat size="sm" label="Cost of contracts" value={fmtMoney(r.cost)} note={`plus ${fmtMoney(r.fee)} exchange fees`} />
            <Stat size="sm" label="Pays if it settles your way" value={fmtMoney(r.payout_if_pays)} />
            <Stat size="sm" label="Worst season" value={fmtMoney(r.worst_hedged)} note={`${fmtMoney(r.worst_unhedged)} without`} />
            <Stat size="sm" label="Typical swing" value={fmtMoney(r.std_hedged)} note={`${fmtMoney(r.std_unhedged)} without`} />
          </div>
        </div>
      )}

      <div className="card stack">
        <div>
          <div className="strong">Worth {fmtSMoney(r.ce_gain)} to you</div>
          <p className="small muted">
            The certainty-equivalent gain: how much guaranteed money the hedged season is worth to you over the unhedged one,
            at your risk aversion ({fmtGamma(gamma)}). Expected income {r.expected_wealth_hedged < r.expected_wealth_unhedged ? 'falls' : 'changes'} from{' '}
            {fmtMoney(r.expected_wealth_unhedged)} to {fmtMoney(r.expected_wealth_hedged)} — that difference is the price of the insurance.
          </p>
        </div>
        <div>
          <div className="strong">You’d pay up to {fmtCents(r.reservation_price)} a contract</div>
          <p className="small muted">
            It costs {fmtCents(r.price)}; its fair value at {r.belief === r.market_prob ? 'the market’s' : 'your blended'} odds is {fmtCents(r.fair_price)}.
          </p>
        </div>
        {!none && (
          <div>
            <div className="strong">Why this size</div>
            <div className="pm-split">
              <div><span className="num">{fmtNum(r.pure_hedge_contracts)}</span> <span className="small muted">pure insurance — offsets your loss</span></div>
              <div>
                <span className="num">{r.speculative_contracts >= 0 ? '+' : '−'}{fmtNum(Math.abs(r.speculative_contracts))}</span>{' '}
                <span className="small muted">
                  {r.speculative_contracts >= 0 ? 'added by your view of the odds' : 'trimmed because the cover is priced above fair or your view disagrees'}
                </span>
              </div>
            </div>
          </div>
        )}
        {r.basis_clipped && (
          <Notice tone="attention">
            A correlation of {basis.toFixed(2)} isn’t possible with these probabilities; Hone used {r.basis_correlation.toFixed(2)}.
          </Notice>
        )}
        {adjusted && (
          <Notice tone="info">
            Your weight on your own view was rescaled from your track record: you said {fmtPct(r.confidence_stated)}, Hone
            used {fmtPct(r.confidence_used)}.
          </Notice>
        )}
        {r.warnings?.map(w => <Notice key={w} tone="attention">{w}</Notice>)}
      </div>

      {/* How fragile is this size? */}
      <div className="card">
        <div className="takeaway">How much the size depends on the inputs</div>
        {!sens ? (
          <Spinner>Checking nearby assumptions…</Spinner>
        ) : (
          <div className="pm-sens">
            <SensTable caption="If your risk aversion were…" head="Risk aversion" rows={sens.byGamma}
              keyOf={x => fmtGamma(x.gamma)} isCurrent={x => Math.abs(x.gamma - gamma) < 1e-6} />
            <SensTable caption="If the contract tracked your income…" head="Correlation" rows={sens.byBasis}
              keyOf={(x, i) => BASIS_GRID[i].toFixed(1)} isCurrent={(x, i) => Math.abs(BASIS_GRID[i] - basis) < 1e-6} />
          </div>
        )}
      </div>

      <p className="tiny subtle">
        Hone sizes event contracts against your income risk and explains the position. It never places orders, and it holds no Kalshi keys.
      </p>
    </div>
  );
}

/** One small "contracts / cost" table for the sensitivity check. */
function SensTable({ caption, head, rows, keyOf, isCurrent }) {
  return (
    <div className="tscroll">
      <table>
        <caption className="tiny subtle" style={{ textAlign: 'left', paddingBottom: 6 }}>{caption}</caption>
        <thead><tr><th>{head}</th><th className="r">Contracts</th><th className="r">Cost</th></tr></thead>
        <tbody>
          {rows.map((x, i) => (
            <tr key={keyOf(x, i)} className={isCurrent(x, i) ? 'pm-sens__current' : undefined}>
              <td>{keyOf(x, i)}{isCurrent(x, i) && <span className="tiny subtle"> (now)</span>}</td>
              <td className="r">{x.needs_hedge ? fmtNum(x.contracts) : '0'}</td>
              <td className="r">{x.needs_hedge ? fmtMoney(x.cost + x.fee) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

