"""Claude backend for the Conviction Compiler.

Uses the Anthropic SDK's structured-output parsing so the model is
*constrained* to the :class:`~hone.llm.schemas.ThesisOut` schema rather than
asked politely for JSON — there is no parsing step that can fail on prose.

The system prompt is the interesting part.  It is written to stop the model
doing the thing that would make Hone dangerous: inventing price targets.  The
model translates what the user said; it does not have opinions about markets.
"""

from __future__ import annotations

import os

from .schemas import CompiledView, CompileResult, ThesisOut

#: Anthropic's most capable model — this runs once per thesis, not per token
#: of a chat, so the cost is a rounding error against getting the numbers right.
MODEL = "claude-opus-5"

MAX_TOKENS = 2048

SYSTEM_PROMPT = """\
You are the Conviction Compiler inside Hone, a portfolio risk tool. Your one \
job is to translate an investor's plain-English thesis into structured fields. \
You are a translator, not an analyst.

Hard rules:
1. NEVER invent a price target. If the user did not state or clearly imply a \
number, leave target_price null and add "target_price" to needs_review. A \
fabricated target flows straight into a Black-Litterman optimizer and moves \
real money.
2. NEVER invent an entry price. Leave entry_price null unless the user stated \
one; the server fills in the live market price.
3. Confidence comes from the user's language, not from your own view of the \
trade. Percentages they state ("70% sure") are used verbatim. Otherwise map \
their hedging: tentative ("might", "maybe") 30-45, plain assertion 50-65, \
emphatic ("very confident", "high conviction") 70-85. Never emit 100 and \
never emit above 90 — certainty does not exist and the optimizer treats it \
as a constraint.
4. Do not agree or disagree with the thesis. Do not add analysis they did not \
express. Do not warn them off the trade.
5. horizon_days is a day count. "by year end", "next quarter", "6 months" all \
resolve to a number. If no timeframe is stated, use 365 and flag \
"horizon_days" in needs_review.
6. direction is "bearish" whenever the user expects the price to fall — \
including when they describe shorting or buying puts.
7. Tickers uppercase. Crypto as PAIR/USD (BTC/USD, ETH/USD). If the user names \
a company, resolve it to its listed ticker.
8. risks: name 1-3 concrete things that would falsify THIS thesis, even when \
the user mentioned none. This is the one field where you add something they \
did not say, because naming the disconfirming case is the point of the tool. \
Keep each under 12 words. Do not turn them into advice.
9. One view per distinct ticker. If the text expresses no investable \
conviction, return an empty list.

Everything you emit is shown to the user in an editable form before it \
reaches the optimizer. Fields you guessed must appear in needs_review so they \
know what to check.\
"""


class ClaudeUnavailable(RuntimeError):
    """No API key, SDK not installed, or the API call failed."""


def available() -> bool:
    """True when a Claude compile could plausibly succeed."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def _user_prompt(
    text: str,
    universe: list[str] | None,
    asset_class: str,
    today: str | None,
) -> str:
    parts = [f"Asset class: {asset_class}."]
    if today:
        parts.append(f"Today's date: {today}. Resolve relative dates against it.")
    if universe:
        parts.append(
            "Symbols already in the user's investable universe (prefer these "
            "when the text is ambiguous): " + ", ".join(universe) + "."
        )
    parts.append("\nThe investor wrote:\n---\n" + text.strip() + "\n---")
    return "\n".join(parts)


def compile_with_claude(
    text: str,
    universe: list[str] | None = None,
    *,
    asset_class: str = "equities",
    today: str | None = None,
    timeout: float = 45.0,
) -> CompileResult:
    """Compile ``text`` with Claude.

    Raises :class:`ClaudeUnavailable` for every failure mode, so callers have
    exactly one exception to catch before falling back to the offline parser.
    """
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - depends on install extras
        raise ClaudeUnavailable(
            "the 'anthropic' package is not installed (pip install 'hone[llm]')"
        ) from exc

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ClaudeUnavailable("ANTHROPIC_API_KEY is not set")

    client = anthropic.Anthropic(timeout=timeout)

    try:
        message = client.messages.parse(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            output_format=ThesisOut,
            messages=[
                {
                    "role": "user",
                    "content": _user_prompt(text, universe, asset_class, today),
                }
            ],
        )
    except anthropic.APIStatusError as exc:
        raise ClaudeUnavailable(f"Claude API error ({exc.status_code})") from exc
    except anthropic.APIConnectionError as exc:
        raise ClaudeUnavailable("could not reach the Claude API") from exc

    # A refusal has no parsed output to read — check before touching content.
    if getattr(message, "stop_reason", None) == "refusal":
        raise ClaudeUnavailable("Claude declined to compile this text")

    parsed = getattr(message, "parsed_output", None)
    if parsed is None:
        raise ClaudeUnavailable("Claude returned no structured output")

    views: list[CompiledView] = list(parsed.views)
    notes: list[str] = []
    for view in views:
        view.ticker = view.ticker.upper().strip()
        if view.direction not in ("bullish", "bearish"):
            view.direction = "bullish"
        if view.confidence_pct is not None:
            # The prompt forbids certainty; enforce it rather than trust it.
            view.confidence_pct = max(1.0, min(90.0, view.confidence_pct))
        if view.target_price is None and "target_price" not in view.needs_review:
            view.needs_review.append("target_price")

    if not views:
        notes.append(
            "No investable conviction found in that text. Name a symbol and "
            "where you think it goes."
        )

    return CompileResult(views=views, engine="claude", notes=notes)
