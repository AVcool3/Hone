/*
 * AdaptiveQuiz — eight either/or choices (DOSE, /api/dose).
 *
 * The server is stateless: we send every answer so far and it returns the
 * most informative next question plus its current belief about γ. That
 * makes "Back" trivial and honest: dropping the last answer recalculates
 * the questions that follow it. Answers are saved as you go, so leaving
 * the page and coming back resumes where you were.
 *
 * Keyboard: press A or B.
 */
import { useCallback, useEffect, useState } from 'react';
import { api } from '../../../lib/api.js';
import { useRisk } from '../../../lib/store.jsx';
import { fmtGamma } from '../../../lib/format.js';
import { DensityChart } from '../../../components/charts.jsx';
import { Button, ErrorNotice, Spinner } from '../../../components/ui.jsx';

export default function AdaptiveQuiz({ assetClass, onComplete, onCancel }) {
  const { profile, setProfile } = useRisk();
  const answers = profile.dose?.answers ?? [];
  const [res, setRes] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const setAnswers = useCallback(next => setProfile(p => ({ dose: { ...p.dose, answers: next } })), [setProfile]);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const r = await api(assetClass, '/api/dose', { answers });
      setRes(r);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetClass, JSON.stringify(answers)]);

  useEffect(() => { load(); }, [load]);

  const choose = useCallback(
    choice => {
      if (!res?.question || busy) return;
      setAnswers([...answers, { question_id: res.question.question_id, choice }]);
    },
    [res, busy, answers, setAnswers],
  );

  // A / B keyboard shortcuts while a question is showing.
  useEffect(() => {
    const onKey = e => {
      if (e.target.closest('input, textarea, select')) return;
      if (e.key === 'a' || e.key === 'A') choose('A');
      if (e.key === 'b' || e.key === 'B') choose('B');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [choose]);

  const q = res?.question;
  const st = res?.state;
  const total = q?.total ?? 8;
  const number = q?.number ?? answers.length + 1;

  return (
    <div className="card">
      <div className="row row--between mb-4">
        <div>
          <div className="eyebrow">Risk profile</div>
          <div className="quiz-progress mt-2">
            <span className="quiz-progress__dots" aria-hidden="true">
              {Array.from({ length: total }, (_, i) => <i key={i} className={i < answers.length ? 'done' : i === answers.length ? 'now' : ''} />)}
            </span>
            <span>{res?.finished ? 'All questions answered' : `Question ${Math.min(number, total)} of ${total}`}</span>
          </div>
        </div>
        <div className="row">
          {answers.length > 0 && !res?.finished && (
            <Button variant="secondary" size="sm" icon="ArrowTurnBackwardIcon" onClick={() => setAnswers(answers.slice(0, -1))} disabled={busy}>
              Change previous answer
            </Button>
          )}
          <Button variant="text" size="sm" onClick={onCancel}>Exit — progress is saved</Button>
        </div>
      </div>

      <ErrorNotice error={error} onRetry={load} />

      {!res && busy && <Spinner>Loading the first question…</Spinner>}

      {q && !res.finished && (
        <>
          <h2 style={{ fontSize: 24 }}>Which would you rather have?</h2>
          <p className="subtle mt-1 mb-4">There’s no right answer. Imagine the money is real. Press <kbd>A</kbd> or <kbd>B</kbd>.</p>
          <div className="choice-pair" style={{ opacity: busy ? 0.6 : 1 }}>
            {[['A', q.option_a], ['B', q.option_b]].map(([key, text]) => (
              <button key={key} type="button" className="choice" onClick={() => choose(key)} disabled={busy}>
                <span className="choice__tag">Option {key}</span>
                <span className="choice__main" style={{ display: 'block' }}>{text}</span>
              </button>
            ))}
          </div>
        </>
      )}

      {res?.finished && (
        <div className="stack">
          <p className="takeaway">That’s all eight. Your estimate is ready.</p>
          <div className="row">
            <Button icon="Tick02Icon" onClick={() => onComplete(st)}>Save my risk profile</Button>
            <Button variant="secondary" icon="ArrowTurnBackwardIcon" onClick={() => setAnswers(answers.slice(0, -1))}>Change last answer</Button>
          </div>
        </div>
      )}

      {/* What the engine believes so far — updates after every answer. */}
      {st && (
        <div className="mt-6">
          <div className="row row--between">
            <h3 style={{ fontSize: 16 }}>What we believe about you so far</h3>
            <span className="tiny subtle">Estimate {fmtGamma(st.gamma)} · 90% likely between {fmtGamma(st.gamma_ci90[0])} and {fmtGamma(st.gamma_ci90[1])}</span>
          </div>
          <DensityChart grid={st.gamma_grid} density={st.gamma_marginal} ci={st.gamma_ci90} mark={st.gamma} />
          <p className="chart-caption">
            Probability over risk-aversion values (higher = more cautious). The shaded band narrows as answers rule values out.
            It is an estimate from a handful of choices, not a fixed fact about you.
          </p>
        </div>
      )}
    </div>
  );
}
