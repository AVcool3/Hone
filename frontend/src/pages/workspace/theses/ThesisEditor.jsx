/*
 * ThesisEditor — the right-hand panel for the selected thesis.
 *
 * Reads like a sentence: Asset → belief (price target) → horizon → confidence.
 * The user speaks in investment terms; this panel translates them into the
 * model's inputs and shows the reference price (with its timestamp) and the
 * implied % change as you type. Every slider has a number box beside it.
 */
import { Link } from 'react-router-dom';
import SquishSwitch from '../../../reactbits/SquishSwitch/SquishSwitch.jsx';
import { Badge, Button, Field, Notice, NumberSlider, Segmented } from '../../../components/ui.jsx';
import { docPath } from '../../../lib/products.js';
import { fmtAgo, fmtHorizon, fmtPct, fmtPrice, fmtSPct, impliedChange } from '../../../lib/format.js';
import AssetPicker from '../../../components/AssetPicker.jsx';
import { assetName } from './assets.js';

const HORIZONS = [
  { value: 91, label: '3 mo' },
  { value: 182, label: '6 mo' },
  { value: 365, label: '1 yr' },
  { value: 730, label: '2 yrs' },
];

/*
 * `directory` is useAssetDirectory()'s result: { assets, source, loading }.
 * With an Alpaca account it holds every symbol Alpaca lists; with sample
 * data, just the demo universe.
 */
export default function ThesisEditor({ thesis: t, product, universe, directory, onChange, onDuplicate, onDelete, children }) {
  const chg = impliedChange(t.refPrice, t.target);
  const everySymbol = directory?.source === 'alpaca';
  // Slider range for the target: 30% to 300% of the reference price.
  const lo = t.refPrice ? Math.max(0.01, +(t.refPrice * 0.3).toFixed(2)) : 1;
  const hi = t.refPrice ? +(t.refPrice * 3).toFixed(2) : 1000;
  const step = t.refPrice && t.refPrice < 5 ? 0.01 : 1;

  return (
    <div className="card stack">
      <div className="row row--between">
        <div className="row" style={{ gap: 8 }}>
          <h2 style={{ fontSize: 19 }}>{t.ticker || 'New thesis'}</h2>
          {t.sample && <Badge tone="sample">Sample</Badge>}
          {!t.included && <Badge>Excluded</Badge>}
        </div>
        <SquishSwitch
          checked={t.included}
          onChange={v => onChange({ included: v })}
          label={t.included ? 'Included' : 'Excluded'}
          ariaLabel="Include this thesis in calculations"
          width={52}
          height={28}
          radius={14}
          trackColor="#d9d8cf"
          trackOnColor="#174e43"
          thumbColor="#ffffff"
          thumbOnColor="#ffffff"
        />
      </div>

      {/* The sentence, assembled from the fields below. */}
      <p className="thesis-sentence">
        I think <b>{t.ticker ? `${assetName(t.ticker) || t.ticker}` : '…'}</b> will be around{' '}
        <b>{t.target ? fmtPrice(t.target) : '…'}</b> in <b>{fmtHorizon(t.horizonDays)}</b>, and I’m <b>{fmtPct(t.confidence)}</b> confident.
      </p>

      <Field
        label="Asset"
        hint={[
          'Search by ticker or name.',
          everySymbol
            ? `All ${directory.assets.length.toLocaleString()} ${product.slug === 'crypto' ? 'crypto pairs' : 'US stocks and ETFs'} on Alpaca.`
            : 'Sample data covers only the symbols listed — connect Alpaca under Data & account to search every market.',
          product.slug === 'crypto' ? 'Crypto pairs look like SOL/USD.' : '',
        ].filter(Boolean).join(' ')}
        htmlFor={`tk-${t.id}`}
      >
        <AssetPicker
          id={`tk-${t.id}`}
          value={t.ticker}
          assets={directory?.assets || []}
          suggested={universe}
          loading={directory?.loading}
          placeholder={product.example?.ticker}
          // A new ticker needs a new reference price: clear the old one so the quote hook fetches it.
          onChange={sym => onChange({ ticker: sym, refPrice: null, refAt: null, tradeable: true })}
        />
      </Field>
      {t.ticker && t.tradeable === false && (
        <Notice tone="attention" title="No price history here for this symbol.">
          It can’t be used in a calculation{universe.length ? ` — available: ${universe.join(', ')}` : ''}. It stays saved, excluded from results.
        </Notice>
      )}

      <Field label="Price target" htmlFor={`tg-${t.id}`}>
        <NumberSlider id={`tg-${t.id}`} value={t.target} onChange={v => onChange({ target: v })} min={lo} max={hi} step={step} prefix="$" inputWidth={140} ariaLabel="Price target" />
        <div className="ref-line mt-1">
          {t.refPrice
            ? <>
                <span>Reference {fmtPrice(t.refPrice)}</span>
                <span className="tiny subtle">({product.slug === 'crypto' ? 'latest' : 'last close'} · fetched {fmtAgo(t.refAt)}{t.refAt ? '' : ''})</span>
                {chg != null && <span>→ implies <span className="implied">{fmtSPct(chg)}</span></span>}
              </>
            : t.ticker ? <span className="tiny subtle">Loading reference price…</span> : <span className="tiny subtle">Pick an asset to see its price.</span>}
        </div>
      </Field>

      <Field label="Horizon" hint="By when you expect the price to get there.">
        <div className="row" style={{ gap: 10 }}>
          <Segmented label="Horizon" options={HORIZONS} value={HORIZONS.some(h => h.value === t.horizonDays) ? t.horizonDays : null} onChange={v => onChange({ horizonDays: v })} />
          <div className="input-affix" style={{ width: 120, '--pad-r': '48px' }}>
            <input type="number" aria-label="Horizon in days" min={7} max={1825} value={Math.round(t.horizonDays)} onChange={e => e.target.value && onChange({ horizonDays: Math.max(7, +e.target.value) })} />
            <span className="input-affix__post">days</span>
          </div>
        </div>
      </Field>

      <Field
        label="Confidence"
        link={{ to: docPath(product.slug, 'methodology', 'calibration', 'the-problem-this-solves'), label: 'What this means' }}
        hint="How far the model moves from a neutral portfolio toward your view: 60% moves it 60% of the way. It is not the probability of hitting the target exactly."
      >
        <NumberSlider value={t.confidence} onChange={v => onChange({ confidence: Math.min(0.99, Math.max(0.01, v)) })} min={0.01} max={0.99} step={1} scale={100} suffix="%" ariaLabel="Confidence" />
      </Field>

      <Field label="Why you believe it" hint="Your reasoning, kept with the numbers. Hone doesn’t read it into the model — it’s for you, later.">
        <textarea value={t.rationale} onChange={e => onChange({ rationale: e.target.value })} placeholder="e.g. Margins recover as the new factory ramps…" />
      </Field>

      {children}

      <div className="row" style={{ borderTop: '1px solid var(--line-soft)', paddingTop: 14 }}>
        <Button variant="secondary" size="sm" icon="Copy01Icon" onClick={onDuplicate}>Duplicate</Button>
        <Button variant="text" size="sm" icon="Delete02Icon" className="btn--danger" onClick={onDelete}>Delete</Button>
        <span className="tiny subtle" style={{ marginLeft: 'auto' }}>
          <Link to={docPath(product.slug, 'methodology', 'flexible-views')}>Other kinds of view</Link>
        </span>
      </div>
    </div>
  );
}
