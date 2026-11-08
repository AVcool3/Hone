"""Conviction Compiler — plain-English theses into structured, editable views.

The user types what they actually believe ("I think Nvidia runs to $250 by
the summer, I'm fairly confident"), and this package compiles it into a
:class:`~hone.llm.schemas.CompiledView`: ticker, entry price, target price,
horizon, confidence and the rationale that produced them.

Nothing here reaches the optimizer directly.  The compiled view is a
*proposal* — the UI shows every field and the user edits it before the
Black-Litterman engine ever sees it.  That is deliberate: an LLM is a good
translator of intent and a bad source of price targets.

Two backends, same output shape:

* :mod:`hone.llm.claude` — Claude (``claude-opus-5``) with structured
  outputs, used when ``ANTHROPIC_API_KEY`` is configured.
* :mod:`hone.llm.fallback` — a deterministic parser with no network and no
  dependencies, so the feature works offline, in tests, and on a
  deployment with no API key.
"""

from .compiler import ConvictionCompiler, compile_convictions
from .schemas import CompiledView, CompileResult

__all__ = [
    "CompiledView",
    "CompileResult",
    "ConvictionCompiler",
    "compile_convictions",
]
