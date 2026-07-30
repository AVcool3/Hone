"""The compiler front door: text in, editable structured views out.

Backend selection is automatic and never fatal.  Claude compiles the thesis
when a key is configured; otherwise — or when the API call fails for any
reason — the deterministic parser runs instead and the result says so.  The
user always gets a form to edit; they never get an error page because a model
was unreachable.
"""

from __future__ import annotations

from datetime import date

from .fallback import compile_offline
from .schemas import CompiledView, CompileResult


class ConvictionCompiler:
    """Compiles plain-English theses into structured views.

    Parameters
    ----------
    prefer_llm
        Use Claude when it is available.  Set False to force the offline
        parser (tests, air-gapped deployments, cost control).
    """

    def __init__(self, prefer_llm: bool = True) -> None:
        self.prefer_llm = prefer_llm

    def compile(
        self,
        text: str,
        universe: list[str] | None = None,
        *,
        asset_class: str = "equities",
        prices: dict[str, float] | None = None,
    ) -> CompileResult:
        text = (text or "").strip()
        if not text:
            return CompileResult(
                views=[], engine="none", notes=["Nothing to compile."]
            )

        today = date.today()
        result: CompileResult | None = None

        if self.prefer_llm:
            from .claude import ClaudeUnavailable, available, compile_with_claude

            if available():
                try:
                    result = compile_with_claude(
                        text,
                        universe,
                        asset_class=asset_class,
                        today=today.isoformat(),
                    )
                except ClaudeUnavailable as exc:
                    result = None
                    fallback_note = f"Used the offline parser ({exc})."
                else:
                    fallback_note = None
            else:
                fallback_note = None
        else:
            fallback_note = None

        if result is None:
            result = compile_offline(text, universe, today_month=today.month)
            if fallback_note:
                result.notes.insert(0, fallback_note)

        _fill_live_prices(result, prices)
        return result


def _fill_live_prices(
    result: CompileResult, prices: dict[str, float] | None
) -> None:
    """Stamp the live price onto each view as the entry, unless the user
    stated their own basis.

    The server owns this number.  The model is explicitly told not to guess
    prices, so this is where entry_price actually comes from.
    """
    if not prices:
        return
    upper = {k.upper(): v for k, v in prices.items()}
    for view in result.views:
        live = upper.get(view.ticker.upper())
        if live is None or live <= 0:
            continue
        if view.entry_price is None:
            view.entry_price = float(live)
            if "entry_price" in view.needs_review:
                view.needs_review.remove("entry_price")


def compile_convictions(
    text: str,
    universe: list[str] | None = None,
    *,
    asset_class: str = "equities",
    prices: dict[str, float] | None = None,
    prefer_llm: bool = True,
) -> CompileResult:
    """One-shot convenience wrapper around :class:`ConvictionCompiler`."""
    return ConvictionCompiler(prefer_llm=prefer_llm).compile(
        text, universe, asset_class=asset_class, prices=prices
    )


def sanity_check(view: CompiledView) -> list[str]:
    """Warnings about an *edited* view, shown before it reaches the optimizer.

    These are not blockers.  The user is allowed to hold an extreme view —
    they just should not hold one by accident, and an unnoticed typo in a
    price target is the single most damaging input error in the whole tool.
    """
    warnings: list[str] = []
    implied = view.implied_return()

    if implied is not None:
        years = max((view.horizon_days or 365.0) / 365.0, 1e-6)
        annualized = (1.0 + implied) ** (1.0 / years) - 1.0
        if annualized > 3.0:
            warnings.append(
                f"That implies {annualized:.0%}/yr. Check the target and the "
                f"timeframe — a decimal-point slip looks exactly like this."
            )
        elif annualized > 1.0:
            warnings.append(
                f"That implies {annualized:.0%}/yr, well above what any asset "
                f"sustains. The optimizer will take it seriously."
            )
        if annualized < -0.9:
            warnings.append(
                "That target implies near-total loss. Check the direction."
            )

    if view.direction == "bullish" and implied is not None and implied < 0:
        warnings.append(
            "Marked bullish but the target is below the entry price."
        )
    if view.direction == "bearish" and implied is not None and implied > 0:
        warnings.append(
            "Marked bearish but the target is above the entry price."
        )

    if (view.confidence_pct or 0) >= 85:
        warnings.append(
            "Above 85% confidence the optimizer treats your view as near-fact "
            "and will concentrate the portfolio into it."
        )
    if view.horizon_days is not None and view.horizon_days < 14:
        warnings.append(
            "Horizons under two weeks are noise, not signal, at this "
            "estimator's resolution."
        )
    return warnings
