"""Personalizing the compiler from a journal, without training anything.

Fine-tuning is the answer to "make the model learn my habits" that people
reach for first, and at retail data volumes it is the wrong one — see
:mod:`hone.llm.export` for why thirty examples produce a worse model than
the one you started with.

In-context learning is the answer that works today.  The user's own
resolved predictions go into the prompt: here is how this person writes,
here is what they meant by it, and here is whether it happened.  No GPU,
no training run, useful from about five examples, and better every time a
prediction resolves.  It also degrades gracefully — a bad example set
makes the model slightly worse, where a bad fine-tune makes it
confidently, permanently worse.

Two things go into the prompt, and the second is the interesting one:

* **Style examples** — theses and the structured views the user edited
  them into.  These teach the model the corrections this person keeps
  making: that they always mean 6 months when they say "medium term",
  that "I like it here" is 55% and not 75%.
* **A calibration note** — the user's realized hit rate against their
  average stated confidence.  It is one sentence, and it is the sentence
  that stops the model repeating the user's overconfidence back at them.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..journal.calibration import CalibrationReport
from ..journal.records import Resolution

#: How many examples to put in the prompt. Beyond about a dozen the
#: marginal example teaches little and the cost is linear, and a long
#: example block starts to crowd out the thesis being compiled.
MAX_EXAMPLES = 10

#: Minimum resolved predictions before personalizing at all. Below this
#: the "examples" are anecdotes, and anchoring the model on three of them
#: is worse than leaving it alone.
MIN_EXAMPLES = 5


@dataclass
class Personalization:
    """The prompt fragments derived from one user's history."""

    examples: list[dict]
    calibration_note: str
    n_used: int
    active: bool

    def as_prompt_block(self) -> str:
        """The block appended to the compiler's system prompt."""
        if not self.active:
            return ""
        lines = [
            "",
            "This investor has a track record with you. Use it.",
            "",
            "How they write, and what they turned out to mean:",
        ]
        for ex in self.examples:
            lines.append(f'  "{ex["thesis"]}"')
            lines.append(
                f"    -> {ex['ticker']} {ex['direction']}, target "
                f"{ex['target']}, {ex['horizon']:.0f} days, "
                f"they said {ex['confidence']:.0%} — {ex['outcome']}"
            )
        if self.calibration_note:
            lines += ["", self.calibration_note]
        return "\n".join(lines)


def _select(resolutions: list[Resolution], limit: int) -> list[Resolution]:
    """Choose which resolved predictions to show the model.

    Recency-weighted but outcome-balanced: the most recent hits and the
    most recent misses, interleaved.  Showing only recent predictions
    would hand the model whatever streak the user is on, and showing only
    hits would teach it that this person is always right.
    """
    ordered = sorted(resolutions, key=lambda r: r.prediction.created_at, reverse=True)
    hits = [r for r in ordered if r.target_hit]
    misses = [r for r in ordered if not r.target_hit]
    picked: list[Resolution] = []
    while len(picked) < limit and (hits or misses):
        if hits:
            picked.append(hits.pop(0))
        if len(picked) < limit and misses:
            picked.append(misses.pop(0))
    # Present oldest-first so the model reads them as a progression.
    return sorted(picked, key=lambda r: r.prediction.created_at)


def _outcome_phrase(res: Resolution) -> str:
    if res.target_hit:
        return "it hit"
    if res.touched:
        return "it touched the target and gave it back"
    if res.direction_hit:
        return "right direction, short of the target"
    return "it went the other way"


def build_personalization(
    resolutions: list[Resolution],
    calibration: CalibrationReport | None = None,
    limit: int = MAX_EXAMPLES,
) -> Personalization:
    """Assemble the in-context personalization for one user."""
    usable = [
        r for r in resolutions
        if (r.prediction.thesis or "").strip()
        and len((r.prediction.thesis or "").strip()) >= 12
    ]
    if len(usable) < MIN_EXAMPLES:
        return Personalization(
            examples=[], calibration_note="", n_used=0, active=False
        )

    chosen = _select(usable, limit)
    examples = [
        {
            "thesis": (r.prediction.thesis or "").strip()[:200],
            "ticker": r.prediction.ticker,
            "direction": r.prediction.direction,
            "target": f"${r.prediction.target_price:,.2f}",
            "horizon": r.prediction.horizon_days,
            "confidence": r.prediction.confidence,
            "outcome": _outcome_phrase(r),
        }
        for r in chosen
    ]

    note = ""
    if calibration is not None and calibration.n >= MIN_EXAMPLES:
        gap = calibration.mean_confidence - calibration.base_rate
        if gap > 0.08:
            note = (
                f"Across {calibration.n} resolved predictions this investor "
                f"averaged {calibration.mean_confidence:.0%} confidence and "
                f"hit {calibration.base_rate:.0%} of the time. Read their "
                f"confidence language accordingly — do not simply echo the "
                f"number they use."
            )
        elif gap < -0.08:
            note = (
                f"Across {calibration.n} resolved predictions this investor "
                f"averaged {calibration.mean_confidence:.0%} confidence and "
                f"hit {calibration.base_rate:.0%} of the time. They "
                f"understate. Take their hedged language more seriously "
                f"than the words alone suggest."
            )
        else:
            note = (
                f"Across {calibration.n} resolved predictions this "
                f"investor's stated confidence has matched their hit rate "
                f"closely. Take the number they give you at face value."
            )

    return Personalization(
        examples=examples,
        calibration_note=note,
        n_used=len(chosen),
        active=True,
    )
