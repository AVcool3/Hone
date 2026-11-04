/*
 * Small, reusable UI pieces. Styling lives in styles/global.css — these
 * components only choose class names, so the look is changed in one place.
 */
import { useEffect, useId, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from './Icon.jsx';
import { fmtAgo } from '../lib/format.js';

/* ------------------------------------------------------------------ Button */
/**
 * <Button variant="primary|secondary|text" to="/route" | href | onClick>
 * Renders a router <Link> when `to` is given, an <a> for `href`, else <button>.
 */
export function Button({ variant = 'primary', size, to, href, icon, iconRight, children, className = '', ...rest }) {
  const cls = `btn btn--${variant}${size ? ` btn--${size}` : ''} ${className}`;
  const inner = (
    <>
      {icon && <Icon name={icon} size={18} className="btn__icon" />}
      {children}
      {iconRight && <Icon name={iconRight} size={18} className="btn__icon" />}
    </>
  );
  if (to) return <Link to={to} className={cls} {...rest}>{inner}</Link>;
  if (href) return <a href={href} className={cls} {...rest}>{inner}</a>;
  return <button type="button" className={cls} {...rest}>{inner}</button>;
}

/* ------------------------------------------------------------------ Notice */
const NOTICE_ICON = { info: 'InformationCircleIcon', attention: 'Alert02Icon', error: 'Alert02Icon', plain: 'InformationCircleIcon' };

export function Notice({ tone = 'plain', title, children, actions, className = '' }) {
  return (
    <div className={`notice notice--${tone} ${className}`} role={tone === 'error' ? 'alert' : undefined}>
      <Icon name={NOTICE_ICON[tone]} size={18} className="notice__icon" />
      <div className="notice__body">
        {title && <strong>{title} </strong>}
        {children}
        {actions && <div className="notice__actions">{actions}</div>}
      </div>
    </div>
  );
}

/**
 * Error notice that explains *which* kind of failure happened, keeps the
 * user's inputs intact, and always offers a retry.
 */
export function ErrorNotice({ error, onRetry, settingsTo }) {
  if (!error) return null;
  const kind = error.kind;
  const title =
    kind === 'brokerage' ? 'Your brokerage link needs attention.'
      : kind === 'credentials' ? 'Your Alpaca keys were not accepted.'
      : kind === 'data' ? 'Market data isn’t available for this request.'
        : kind === 'network' ? 'Can’t reach the server.'
          : kind === 'input' ? 'Something in the inputs needs fixing.'
            : 'That didn’t work.';
  return (
    <Notice
      tone="error"
      title={title}
      actions={
        <>
          {onRetry && <Button variant="secondary" size="sm" icon="RefreshIcon" onClick={onRetry}>Retry</Button>}
          {kind === 'credentials' && settingsTo && <Button variant="text" size="sm" to={settingsTo}>Check data source</Button>}
        </>
      }
    >
      <span>{error.message}</span> <span className="tiny">Your inputs are unchanged.</span>
    </Notice>
  );
}

/** "Needs recalculation" — shown when a result's inputs have changed since it ran. */
export function StaleBanner({ onRecalc, busy, what = 'this result' }) {
  return (
    <Notice
      tone="attention"
      title="Needs recalculation."
      actions={<Button size="sm" icon="RefreshIcon" onClick={onRecalc} disabled={busy}>{busy ? 'Recalculating…' : 'Recalculate'}</Button>}
    >
      Inputs changed since {what} was calculated. The figures below are from the previous inputs.
    </Notice>
  );
}

/* ------------------------------------------------------------------ Badges */
export const Badge = ({ tone = '', children, title }) => (
  <span className={`badge ${tone ? `badge--${tone}` : ''}`} title={title}>{children}</span>
);

/** Labels where numbers came from: sample data vs. the user's own account. */
export function SourceBadge({ dataSource }) {
  if (dataSource === 'brokers') return <Badge tone="live" title="Holdings from every brokerage you linked, combined">Your brokerages</Badge>;
  return dataSource === 'alpaca'
    ? <Badge tone="live" title="Prices and holdings from your Alpaca paper account">Your paper account</Badge>
    : <Badge tone="sample" title="Synthetic sample prices and holdings — nothing here is your data">Sample data</Badge>;
}

/** Short description of a data source, for "Calculated … · <source>" lines. */
export const sourceLabel = dataSource =>
  dataSource === 'brokers' ? 'Your linked brokerages' : dataSource === 'alpaca' ? 'Alpaca paper data' : 'Sample prices and holdings';

export function SavedLabel({ at }) {
  return <span className="tiny subtle" aria-live="polite">{at ? `Saved on this device · ${fmtAgo(at)}` : 'Not saved yet'}</span>;
}

/* ------------------------------------------------------------------ Stat */
export function Stat({ label, value, note, size }) {
  return (
    <div className="stat">
      <span className="stat__label">{label}</span>
      <span className={`stat__value ${size === 'sm' ? 'stat__value--sm' : ''}`}>{value}</span>
      {note && <span className="stat__note">{note}</span>}
    </div>
  );
}

/* ------------------------------------------------------------------ Spinner */
export const Spinner = ({ children = 'Loading…' }) => <span className="spinner" role="status">{children}</span>;

export function SkeletonRows({ rows = 4 }) {
  return (
    <div className="stack" aria-hidden="true">
      {Array.from({ length: rows }, (_, i) => <div key={i} className="skeleton" style={{ height: 18, width: `${90 - i * 12}%` }} />)}
    </div>
  );
}

/* ------------------------------------------------------------------ Field */
export function Field({ label, hint, error, children, htmlFor, link }) {
  return (
    <div className="field">
      {label && (
        <label className="field__label" htmlFor={htmlFor}>
          {label}
          {link && <> <Link to={link.to} className="tiny" style={{ fontWeight: 500 }}>{link.label}</Link></>}
        </label>
      )}
      {children}
      {error ? <span className="field__error">{error}</span> : hint ? <span className="field__hint">{hint}</span> : null}
    </div>
  );
}

/**
 * Number input with an optional slider beside it — sliders are never the
 * only way in. Values are kept as numbers; `scale` lets a 0–1 value be
 * typed as 0–100 (percent).
 */
export function NumberSlider({
  id, value, onChange, min, max, step = 1, scale = 1, prefix, suffix, slider = true, inputWidth = 120, ariaLabel,
}) {
  const autoId = useId();
  const inputId = id || autoId;
  const shown = value == null || Number.isNaN(value) ? '' : +(value * scale).toFixed(6);
  const [draft, setDraft] = useState(String(shown));
  const editing = useRef(false);
  useEffect(() => { if (!editing.current) setDraft(String(shown)); }, [shown]);

  const commit = raw => {
    const n = parseFloat(raw);
    if (Number.isFinite(n)) onChange(Math.min(max * scale, Math.max(min * scale, n)) / scale);
  };
  const padL = prefix ? 26 : 12;
  const padR = suffix ? 12 + suffix.length * 9 : 12;
  return (
    <div className="row" style={{ flexWrap: 'nowrap', gap: 12 }}>
      {slider && (
        <input
          type="range"
          aria-label={ariaLabel ? `${ariaLabel} slider` : undefined}
          aria-hidden={ariaLabel ? undefined : true}
          tabIndex={-1}
          min={min * scale}
          max={max * scale}
          step={step}
          value={shown === '' ? min * scale : shown}
          onChange={e => onChange(parseFloat(e.target.value) / scale)}
          style={{ flex: 1, minWidth: 80 }}
        />
      )}
      <div className="input-affix" style={{ width: inputWidth, flex: 'none', '--pad-l': `${padL}px`, '--pad-r': `${padR}px` }}>
        {prefix && <span className="input-affix__pre">{prefix}</span>}
        <input
          id={inputId}
          type="number"
          inputMode="decimal"
          aria-label={ariaLabel}
          min={min * scale}
          max={max * scale}
          step={step}
          value={draft}
          onFocus={() => { editing.current = true; }}
          onChange={e => { setDraft(e.target.value); commit(e.target.value); }}
          onBlur={() => { editing.current = false; setDraft(String(shown)); }}
        />
        {suffix && <span className="input-affix__post">{suffix}</span>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ Segmented */
export function Segmented({ options, value, onChange, label }) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map(o => (
        <button key={o.value} type="button" aria-pressed={o.value === value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ Modal */
export function Modal({ open, onClose, title, children }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const onKey = e => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    ref.current?.querySelector('input, button, [href]')?.focus();
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} ref={ref}>
        <div className="row row--between mb-4">
          <h2 style={{ fontSize: 22 }}>{title}</h2>
          <button type="button" className="btn btn--text" onClick={onClose} aria-label="Close"><Icon name="Cancel01Icon" /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ Expander */
export function Expander({ summary, children, defaultOpen = false }) {
  return (
    <details className="expander" open={defaultOpen || undefined}>
      <summary>
        <Icon name="ArrowRight01Icon" size={16} className="chev" />
        <div style={{ flex: 1, minWidth: 0 }}>{summary}</div>
      </summary>
      <div className="expander__body">{children}</div>
    </details>
  );
}

/* ------------------------------------------------------------------ Page header */
export function PageHeader({ eyebrow, title, lede, actions, meta }) {
  return (
    <header className="page-head">
      <div style={{ minWidth: 0 }}>
        {eyebrow && <div className="eyebrow mb-2">{eyebrow}</div>}
        <h1 className="page-head__title">{title}</h1>
        {lede && <p className="page-head__lede">{lede}</p>}
        {meta && <div className="row mt-3">{meta}</div>}
      </div>
      {actions && <div className="page-head__actions">{actions}</div>}
    </header>
  );
}

/** Section title inside a page, with an optional one-line takeaway. */
export function SectionTitle({ title, sub, right }) {
  return (
    <div className="row row--between mb-4" style={{ alignItems: 'flex-end' }}>
      <div>
        <h2 className="section-title">{title}</h2>
        {sub && <p className="subtle mt-1">{sub}</p>}
      </div>
      {right}
    </div>
  );
}
