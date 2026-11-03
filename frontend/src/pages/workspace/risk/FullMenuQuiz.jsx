/*
 * FullMenuQuiz — the classic Holt–Laury multiple price list: 3 rounds × 10
 * rows, each a choice between a safer and a riskier lottery (/api/menu),
 * scored by maximum likelihood (/api/questionnaire).
 *
 * Probabilities and payoffs sit in aligned columns so rows can be compared
 * at a glance. Progress is saved after every click.
 */
import { useEffect, useState } from 'react';
import { api } from '../../../lib/api.js';
import { useRisk } from '../../../lib/store.jsx';
import { fmtMoney, fmtPct } from '../../../lib/format.js';
import { Button, ErrorNotice, Spinner } from '../../../components/ui.jsx';

const lottery = l => (
  <span className="lot">
    {fmtPct(l.p_high)} chance of <b>{fmtMoney(l.high, 2)}</b>
    <br />
    <span className="subtle">otherwise {fmtMoney(l.low, 2)}</span>
  </span>
);

export default function FullMenuQuiz({ assetClass, onComplete, onCancel }) {
  const { profile, setProfile } = useRisk();
  const [menu, setMenu] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const choices = profile.full?.choices ?? [Array(10).fill(null), Array(10).fill(null), Array(10).fill(null)];
  const round = profile.full?.round ?? 0;
  const save = (nextChoices, nextRound = round) => setProfile({ full: { choices: nextChoices, round: nextRound } });

  const loadMenu = () => {
    setError(null);
    api(assetClass, '/api/menu').then(setMenu).catch(setError);
  };
  useEffect(loadMenu, [assetClass]);

  if (error && !menu) return <div className="card"><ErrorNotice error={error} onRetry={loadMenu} /></div>;
  if (!menu) return <div className="card"><Spinner>Loading the questions…</Spinner></div>;

  const rows = menu[round].rows;
  const roundDone = choices[round].every(Boolean);
  const set = (i, v) => save(choices.map((r, ri) => (ri === round ? r.map((c, ci) => (ci === i ? v : c)) : r)));

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const p = await api(assetClass, '/api/questionnaire', { choices });
      onComplete(p);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <div className="row row--between mb-4">
        <div>
          <div className="eyebrow">Risk profile · full version</div>
          <div className="quiz-progress mt-2">
            <span>Round {round + 1} of 3 · stakes ×{menu[round].scale}</span>
            <span className="subtle">({choices[round].filter(Boolean).length} of 10 answered)</span>
          </div>
        </div>
        <Button variant="text" size="sm" onClick={onCancel}>Exit — progress is saved</Button>
      </div>
      <p className="muted mb-4">For each row, pick the lottery you’d rather play. Most people start with A and switch to B somewhere down the list.</p>

      <div className="tscroll">
        <table className="menu-table">
          <thead><tr><th>#</th><th>Option A</th><th>Option B</th></tr></thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={row.number}>
                <td className="subtle">{row.number}</td>
                {['A', 'B'].map(k => (
                  <td key={k}>
                    <label className="opt">
                      <input type="radio" name={`r${round}-${i}`} checked={choices[round][i] === k} onChange={() => set(i, k)} />
                      {lottery(k === 'A' ? row.option_a : row.option_b)}
                    </label>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ErrorNotice error={error} onRetry={submit} />
      <div className="row row--between mt-5">
        <Button variant="secondary" icon="ArrowLeft01Icon" disabled={round === 0} onClick={() => save(choices, round - 1)}>Previous round</Button>
        {round < 2
          ? <Button iconRight="ArrowRight01Icon" disabled={!roundDone} onClick={() => save(choices, round + 1)}>Next round</Button>
          : <Button icon="Tick02Icon" disabled={!choices.every(r => r.every(Boolean)) || busy} onClick={submit}>{busy ? 'Scoring…' : 'Score my answers'}</Button>}
      </div>
    </div>
  );
}
