"""The structured shape a conviction compiles into.

These models are the contract in three places at once: the JSON schema the
LLM is constrained to emit, the API response body, and the editable form in
the browser.  Keeping one definition means a field can never be present in
the model and missing from the form.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompiledView(BaseModel):
    """One conviction, structured.

    Every field is a *proposal* the user can overwrite.  ``confidence_pct``
    is the user's self-reported confidence as a percentage (the UI speaks
    percent; the optimizer takes the 0-1 fraction via
    :meth:`confidence_fraction`).
    """

    ticker: str = Field(description="Ticker symbol, uppercase, e.g. NVDA or BTC/USD")
    direction: str = Field(
        default="bullish",
        description='"bullish" if the thesis expects a rise, "bearish" if a fall',
    )
    entry_price: float | None = Field(
        default=None,
        description=(
            "Price the thesis starts from. Null when the user did not state "
            "one — the server fills in the live price."
        ),
    )
    target_price: float | None = Field(
        default=None, description="Where the user expects the price to end up"
    )
    horizon_days: float | None = Field(
        default=None,
        description=(
            'Days until the target is reached. "by year end", "6 months", '
            '"a couple of quarters" all resolve to a day count.'
        ),
    )
    confidence_pct: float | None = Field(
        default=None,
        description=(
            "Confidence 0-100. Map hedged language low (30-45), plain "
            "statements mid (50-65), emphatic language high (70-85). Never "
            "emit 100."
        ),
    )
    thesis: str = Field(
        default="",
        description="One sentence, in the user's own framing, of what they believe",
    )
    catalysts: list[str] = Field(
        default_factory=list,
        description="Concrete events the user cited that would prove them right",
    )
    risks: list[str] = Field(
        default_factory=list,
        description=(
            "What would prove them wrong. Populate this even when the user "
            "did not mention any — naming the disconfirming case is the point."
        ),
    )
    needs_review: list[str] = Field(
        default_factory=list,
        description="Field names that were guessed rather than stated by the user",
    )

    # ---------------------------------------------------------------- helpers
    def confidence_fraction(self, default: float = 0.5) -> float:
        """Confidence as the 0-1 fraction the optimizer wants."""
        if self.confidence_pct is None:
            return default
        return max(0.01, min(1.0, self.confidence_pct / 100.0))

    def implied_return(self) -> float | None:
        """Simple (not annualized) return from entry to target."""
        if not self.entry_price or not self.target_price:
            return None
        return self.target_price / self.entry_price - 1.0


class CompileResult(BaseModel):
    """Everything the compiler produced for one block of user text."""

    views: list[CompiledView] = Field(default_factory=list)
    #: "claude" when the LLM compiled it, "fallback" when the deterministic
    #: parser did.  Surfaced in the UI so the user knows what they are editing.
    engine: str = "fallback"
    #: Non-fatal notes: unrecognized tickers, defaults that were applied,
    #: an LLM error that triggered the fallback.
    notes: list[str] = Field(default_factory=list)


class ThesisOut(BaseModel):
    """LLM-facing schema: exactly what the model is constrained to return.

    Deliberately narrower than :class:`CompileResult` — the model returns
    views and nothing else, and the server owns provenance and notes.
    """

    views: list[CompiledView] = Field(
        description=(
            "One entry per distinct ticker the user expressed a view on. "
            "Empty list if the text contains no investable conviction."
        )
    )
