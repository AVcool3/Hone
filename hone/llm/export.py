"""Turn a decision journal into fine-tuning data — and say when not to.

The ambition is real: a model tuned on *your* convictions and how they
actually turned out should compile your theses the way you mean them and
price your confidence the way your history earns.  Nobody else's data can
teach it your habits.

The arithmetic is less romantic.  A retail user with a year of active
investing has perhaps thirty resolved predictions.  Thirty examples is
not a fine-tuning dataset; it is a prompt.  LoRA on thirty rows memorizes
them, and a model that has memorized your last thirty calls is worse than
the base model at the thirty-first — confidently, in your own voice.

So this module does two things and is explicit about which is which:

* :func:`build_dataset` exports JSONL for QLoRA, with an honest
  readiness assessment attached.  At n < :data:`MIN_VIABLE_EXAMPLES` it
  exports anyway — it is the user's data — and tells them plainly that
  training on it will produce a worse model than they started with.
* :mod:`hone.llm.personalize` does what actually works at retail scale:
  puts the user's own resolved examples into the prompt.  No GPU, no
  training run, works at n = 5, and improves monotonically as the journal
  grows.

The second is the shipping feature.  The first is the on-ramp for the
user who eventually has the data — and the exported format is the same
one the few-shot path consumes, so nothing has to be rebuilt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..journal.records import Resolution
from .schemas import CompiledView

#: Below this, fine-tuning reliably produces a model worse than the base.
#: Not a hard floor in the literature — it depends on task and rank — but
#: the right order of magnitude for a narrow extraction task, and far
#: above what any retail journal will contain for a long time.
MIN_VIABLE_EXAMPLES = 200

#: Below this, few-shot prompting is not just easier but strictly better.
FEW_SHOT_CEILING = 500

SYSTEM_PROMPT = (
    "You are a conviction compiler. Translate an investor's plain-English "
    "thesis into structured fields: ticker, direction, target price, "
    "horizon in days, and confidence as a percentage. Never invent a price "
    "target the investor did not state."
)

CALIBRATION_SYSTEM_PROMPT = (
    "You estimate how likely this investor's price targets are to be "
    "reached, based on how their past predictions actually resolved. "
    "Answer with a probability between 0 and 1."
)


@dataclass
class TrainingExample:
    """One row of fine-tuning data, in chat form."""

    messages: list[dict]
    #: What this row teaches: "compile" (text -> fields) or "calibrate"
    #: (text -> realized probability).
    task: str
    #: True when the underlying prediction hit its target. Kept so a
    #: caller can filter, weight, or balance the set.
    hit: bool | None = None

    def to_jsonl(self) -> str:
        return json.dumps({"messages": self.messages}, ensure_ascii=False)


@dataclass
class DatasetReport:
    """The exported data, and whether it is worth training on."""

    examples: list[TrainingExample]
    n_compile: int
    n_calibrate: int
    n_resolved: int
    hit_rate: float | None
    #: "few_shot" | "marginal" | "ready"
    recommendation: str
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.examples)

    def to_jsonl(self, task: str | None = None) -> str:
        rows = [e for e in self.examples if task is None or e.task == task]
        return "\n".join(e.to_jsonl() for e in rows)

    def split(self, holdout: float = 0.2) -> tuple[list, list]:
        """Chronological split — the journal is a time series.

        A random split leaks the future into training: the same market
        regime appears on both sides and the validation loss flatters the
        model. The last slice is held out instead, which is also the only
        split that answers the question anyone cares about — does this
        help on the *next* prediction.
        """
        n_hold = max(1, int(len(self.examples) * holdout)) if self.examples else 0
        cut = len(self.examples) - n_hold
        return self.examples[:cut], self.examples[cut:]

    def summary(self) -> str:
        lines = [
            f"{self.n} training examples from {self.n_resolved} resolved "
            f"predictions ({self.n_compile} compile, {self.n_calibrate} "
            f"calibrate).",
        ]
        if self.hit_rate is not None:
            lines.append(f"Historical hit rate: {self.hit_rate:.0%}.")
        lines.extend(self.warnings)
        lines.extend(self.notes)
        return " ".join(lines)


def _view_json(view: CompiledView) -> str:
    return json.dumps(
        {
            "ticker": view.ticker,
            "direction": view.direction,
            "target_price": view.target_price,
            "horizon_days": view.horizon_days,
            "confidence_pct": view.confidence_pct,
        },
        ensure_ascii=False,
    )


def _compile_example(res: Resolution) -> TrainingExample | None:
    """thesis text -> the structured view the user actually committed to.

    The label is what the user *edited it into*, not what the compiler
    first proposed. That distinction is the entire value of the row: it
    teaches the model the corrections this person keeps making.
    """
    p = res.prediction
    thesis = (p.thesis or "").strip()
    if not thesis or len(thesis) < 12:
        return None
    view = CompiledView(
        ticker=p.ticker,
        direction=p.direction,
        entry_price=p.entry_price,
        target_price=p.target_price,
        horizon_days=p.horizon_days,
        confidence_pct=p.confidence * 100.0,
    )
    return TrainingExample(
        task="compile",
        hit=res.target_hit,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": thesis},
            {"role": "assistant", "content": _view_json(view)},
        ],
    )


def _calibration_example(res: Resolution) -> TrainingExample | None:
    """thesis -> whether it actually happened.

    The label is the realized outcome, not the stated confidence.  A model
    trained on stated confidence learns to imitate the user's
    overconfidence; trained on outcomes it learns what their language is
    actually worth, which is the only version worth having.
    """
    p = res.prediction
    thesis = (p.thesis or "").strip()
    if not thesis or len(thesis) < 12:
        return None
    move = (p.target_price / p.entry_price - 1.0) if p.entry_price else 0.0
    prompt = (
        f"{thesis}\n\n"
        f"[{p.ticker}: {move:+.1%} move to the target over "
        f"{p.horizon_days:.0f} days; the investor said "
        f"{p.confidence:.0%}]"
    )
    return TrainingExample(
        task="calibrate",
        hit=res.target_hit,
        messages=[
            {"role": "system", "content": CALIBRATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "1.0" if res.target_hit else "0.0"},
        ],
    )


def build_dataset(
    resolutions: list[Resolution],
    include_compile: bool = True,
    include_calibration: bool = True,
) -> DatasetReport:
    """Build fine-tuning data from resolved predictions, with a verdict.

    Only *resolved* predictions are used.  An open prediction has no
    label, and training on the stated confidence of an unresolved call
    teaches the model to reproduce the user's priors rather than their
    accuracy.
    """
    ordered = sorted(resolutions, key=lambda r: r.prediction.created_at)
    examples: list[TrainingExample] = []
    n_compile = n_calibrate = 0

    for res in ordered:
        if include_compile:
            ex = _compile_example(res)
            if ex:
                examples.append(ex)
                n_compile += 1
        if include_calibration:
            ex = _calibration_example(res)
            if ex:
                examples.append(ex)
                n_calibrate += 1

    n_resolved = len(ordered)
    hit_rate = (
        sum(1 for r in ordered if r.target_hit) / n_resolved if n_resolved else None
    )

    warnings: list[str] = []
    notes: list[str] = []
    if len(examples) < MIN_VIABLE_EXAMPLES:
        recommendation = "few_shot"
        warnings.append(
            f"{len(examples)} examples is far below the ~{MIN_VIABLE_EXAMPLES} "
            "where fine-tuning starts to help. A LoRA trained on this will "
            "memorize these rows and be worse than the base model on your "
            "next thesis — confidently, and in your own voice."
        )
        notes.append(
            "Use the few-shot path instead: your resolved predictions go "
            "into the prompt, which needs no GPU, works from about five "
            "examples, and improves every time one resolves."
        )
    elif len(examples) < FEW_SHOT_CEILING:
        recommendation = "marginal"
        warnings.append(
            f"{len(examples)} examples is enough to try, not enough to "
            "trust. Hold out the most recent fifth and compare against the "
            "base model before using the result — if it does not clearly "
            "win, it did not work."
        )
    else:
        recommendation = "ready"
        notes.append(
            "Enough data for a small-rank LoRA. Still hold out the recent "
            "slice chronologically; a random split leaks the regime."
        )

    if hit_rate is not None and n_resolved >= 10:
        if hit_rate < 0.1:
            warnings.append(
                f"Only {hit_rate:.0%} of these predictions hit. The "
                "calibration half of the set is almost all zeros, and a "
                "model trained on it will learn to answer 'no' to "
                "everything, which is accurate and useless."
            )
        elif hit_rate > 0.9:
            warnings.append(
                f"{hit_rate:.0%} of these hit — the calibration labels are "
                "nearly all ones, so there is little for a model to learn "
                "beyond saying yes."
            )

    return DatasetReport(
        examples=examples,
        n_compile=n_compile,
        n_calibrate=n_calibrate,
        n_resolved=n_resolved,
        hit_rate=hit_rate,
        recommendation=recommendation,
        warnings=warnings,
        notes=notes,
    )
