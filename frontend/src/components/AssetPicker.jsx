/*
 * AssetPicker — search thousands of symbols by ticker or company name.
 *
 * Replaces a <datalist>, which can't rank results and gets sluggish with
 * ~11k options. Built as an ARIA combobox:
 *   - type to filter (ranking lives in searchAssets, assetDirectory.js)
 *   - ↑/↓ move through matches, Enter picks, Esc closes
 *   - with an empty box, `suggested` symbols (your holdings) are listed
 *
 * The value is *committed* (onChange) only when you pick a match, press
 * Enter, or leave the field — not on every keystroke — because each
 * committed ticker fetches a price from the server. Leaving the field
 * commits only an exact symbol, so a half-typed "app" never becomes the
 * ticker APP; Enter with no matches commits whatever was typed.
 *
 * Props
 *   id, placeholder   passed to the <input>
 *   value             the committed symbol
 *   onChange(sym)     called with the upper-cased symbol
 *   assets            [{ symbol, name, exchange }]
 *   suggested         symbols to show when the box is empty (the priced universe)
 *   loading           true while the full list is still loading
 *   limit             max matches shown (default 20)
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { searchAssets } from '../pages/workspace/theses/assetDirectory.js';

export default function AssetPicker({ id, value, onChange, assets, suggested = [], loading = false, placeholder, limit = 20 }) {
  const [text, setText] = useState(value || '');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0); // index of the highlighted option
  const listId = useId();
  const listRef = useRef(null);

  // Follow the committed value when it changes from outside (e.g. another thesis selected).
  useEffect(() => { setText(value || ''); }, [value]);

  const bySymbol = useMemo(() => new Map(assets.map(a => [a.symbol, a])), [assets]);

  const { matches, total } = useMemo(() => {
    if (text.trim() && text.trim().toUpperCase() !== (value || '')) return searchAssets(assets, text, limit);
    // Empty box, or showing the committed value: list the suggestions.
    const sug = suggested.map(sym => bySymbol.get(sym) || { symbol: sym, name: '', exchange: '' });
    return { matches: sug.slice(0, limit), total: sug.length };
  }, [assets, bySymbol, text, value, suggested, limit]);

  // Keep the highlighted option in range and scrolled into view.
  useEffect(() => { setActive(0); }, [text]);
  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [active]);

  /** Leaving the field: keep an exact symbol, otherwise go back to the committed value. */
  const onBlur = () => {
    const typed = text.toUpperCase().trim();
    if (!typed || bySymbol.has(typed)) commit(typed);
    else { setText(value || ''); setOpen(false); }
  };

  const commit = sym => {
    const next = (sym || '').toUpperCase().trim();
    setText(next);
    setOpen(false);
    if (next !== (value || '')) onChange(next);
  };

  const onKeyDown = e => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive(i => Math.min(i + 1, matches.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(i => Math.max(i - 1, 0)); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      // Pick the highlighted match if the list is open; otherwise take what was typed.
      commit(open && matches[active] ? matches[active].symbol : text);
    } else if (e.key === 'Escape') { setOpen(false); setText(value || ''); }
  };

  const showList = open && matches.length > 0;
  // One line under the matches: how many there are, or what the empty list means.
  const footer = [
    total > matches.length ? `${matches.length} of ${total.toLocaleString()} matches · keep typing to narrow` : '',
    !text.trim() || text.trim().toUpperCase() === (value || '') ? 'Your portfolio · type to search every symbol' : '',
    loading ? 'loading the full list…' : '',
  ].filter(Boolean).join(' · ');
  const optId = i => `${listId}-opt-${i}`;

  return (
    <div className="asset-picker">
      <input
        id={id}
        type="text"
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={showList && matches[active] ? optId(active) : undefined}
        autoCapitalize="characters"
        autoComplete="off"
        spellCheck={false}
        value={text}
        placeholder={placeholder}
        onChange={e => { setText(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
      />
      {showList && (
        <ul className="asset-picker__list" role="listbox" id={listId} ref={listRef}>
          {matches.map((a, i) => (
            <li
              key={a.symbol}
              id={optId(i)}
              data-index={i}
              role="option"
              aria-selected={i === active}
              className="asset-picker__opt"
              // mousedown, not click: click fires after the input's blur has already committed.
              onMouseDown={e => { e.preventDefault(); commit(a.symbol); }}
              onMouseEnter={() => setActive(i)}
            >
              <span className="asset-picker__sym">{a.symbol}</span>
              <span className="asset-picker__name">{a.name}</span>
              {a.exchange && <span className="asset-picker__ex">{a.exchange}</span>}
            </li>
          ))}
          {footer && <li className="asset-picker__foot" role="presentation">{footer}</li>}
        </ul>
      )}
    </div>
  );
}
