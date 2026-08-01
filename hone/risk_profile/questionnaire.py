"""Interactive Holt-Laury questionnaire.

Presents the 10-row menu at several stake scales, collects A/B choices,
runs the MLE engine, and returns a :class:`RiskProfile` containing the
gamma point estimate, the noise parameter, the switch-point interval,
and the 50-tier placement.

The I/O is injected (``input_fn`` / ``output_fn``) so the questionnaire
is scriptable and testable; the default wiring is the builtin
``input``/``print`` pair used by the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable, Sequence

from .holt_laury import (
    DEFAULT_SCALES,
    expected_value,
    gamma_interval,
    is_monotone,
    safe_choice_count,
    standard_menu,
)
from .estimation import EstimationResult, estimate
from .tiers import TierPlacement, gamma_to_tier


@dataclass
class RiskProfile:
    gamma: float
    mu: float
    se_gamma: float | None
    tier: TierPlacement
    interval: tuple[float, float]  # switch-point interval at scale 1
    estimation: EstimationResult
    choices: list[list[str]]
    scales: list[float]
    monotone: list[bool]  # per-scale: did the subject switch only once?

    def summary(self) -> str:
        lines = [
            "=== Risk Profile ===",
            f"Risk-aversion gamma : {self.gamma:+.4f}"
            + (f" (s.e. {self.se_gamma:.4f})" if self.se_gamma else ""),
            f"Decision noise mu   : {self.mu:.4f}",
            f"Switch-point bounds : ({self.interval[0]:+.3f}, {self.interval[1]:+.3f})",
            f"Placement           : {self.tier.describe()}",
        ]
        if not all(self.monotone):
            lines.append(
                "Note: some menus contained multiple switch points; the MLE "
                "noise parameter absorbs that inconsistency."
            )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["estimation"] = asdict(self.estimation)
        return d


def _format_lottery(high: float, low: float, p_high: float) -> str:
    return (
        f"{p_high * 100:3.0f}% chance of ${high:,.2f} / "
        f"{(1 - p_high) * 100:3.0f}% chance of ${low:,.2f}"
    )


def profile_from_choices(
    choices: Sequence[Sequence[str]],
    scales: Sequence[float] = DEFAULT_SCALES,
    error_spec: str = "fechner",
) -> RiskProfile:
    """Build a full risk profile from already-collected choice vectors."""
    result = estimate(choices, scales=scales, error_spec=error_spec)  # type: ignore[arg-type]
    n_safe = safe_choice_count(choices[0])
    interval = gamma_interval(n_safe)
    return RiskProfile(
        gamma=result.gamma,
        mu=result.mu,
        se_gamma=result.se_gamma,
        tier=gamma_to_tier(result.gamma),
        interval=interval,
        estimation=result,
        choices=[[str(c).strip().upper() for c in vec] for vec in choices],
        scales=list(scales),
        monotone=[is_monotone(vec) for vec in choices],
    )


def run_questionnaire(
    scales: Sequence[float] = DEFAULT_SCALES,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    show_expected_values: bool = False,
    error_spec: str = "fechner",
) -> RiskProfile:
    """Run the interactive questionnaire and return the risk profile.

    ``show_expected_values`` is off by default because displaying EVs
    anchors subjects toward risk neutrality and biases the elicitation.
    """
    output_fn(
        "\nHone risk questionnaire\n"
        "-----------------------\n"
        "For each row, imagine you must play one of the two lotteries and\n"
        "type A or B for the one you would rather play. There are no right\n"
        "answers; answer honestly, as if real money were on the line.\n"
    )
    all_choices: list[list[str]] = []
    for round_no, scale in enumerate(scales, start=1):
        menu = standard_menu(scale)
        output_fn(
            f"\n--- Round {round_no} of {len(scales)} "
            f"(stakes x{scale:g}: top prize ${menu[0].option_b.high:,.2f}) ---"
        )
        vec: list[str] = []
        for d in menu:
            prompt = (
                f"\n[{d.number:2d}] A: {_format_lottery(d.option_a.high, d.option_a.low, d.option_a.p_high)}\n"
                f"     B: {_format_lottery(d.option_b.high, d.option_b.low, d.option_b.p_high)}\n"
            )
            if show_expected_values:
                prompt += (
                    f"     (EV A ${expected_value(d.option_a):,.2f}, "
                    f"EV B ${expected_value(d.option_b):,.2f})\n"
                )
            output_fn(prompt.rstrip())
            while True:
                answer = input_fn("     Your choice [A/B]: ").strip().upper()
                if answer in ("A", "B"):
                    vec.append(answer)
                    break
                output_fn("     Please type A or B.")
        all_choices.append(vec)

    profile = profile_from_choices(all_choices, scales=scales, error_spec=error_spec)
    output_fn("\n" + profile.summary())
    return profile
