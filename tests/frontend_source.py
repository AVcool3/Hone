"""Read the React frontend's source and build output for UI invariant tests.

The UI used to be one hand-written index.html, so tests grepped the served
page. It is now a React app in frontend/src, built by Vite into
hone/web/static. The invariants are the same product promises (honest
caveats, disclosures, no iOS zoom trap, ...) checked against the source that
produces them. If one of these fails after a UI edit, the promise was
probably dropped along with the copy — put it back, don't just edit the test.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"
STATIC = ROOT / "hone" / "web" / "static"


@lru_cache(maxsize=None)
def source(*names: str) -> str:
    """Concatenated text of frontend source files.

    With no arguments: every .js/.jsx file. With arguments: only files whose
    path ends with one of the given names (e.g. "HedgingPage.jsx").
    """
    files = sorted(p for p in SRC.rglob("*") if p.suffix in (".js", ".jsx"))
    if names:
        files = [p for p in files if any(str(p).endswith(n) for n in names)]
        assert files, f"no frontend source matching {names}"
    return "\n".join(p.read_text(encoding="utf-8") for p in files)


@lru_cache(maxsize=None)
def css() -> str:
    """Every stylesheet in the frontend (design system, pages, React Bits)."""
    return "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(SRC.rglob("*.css"))
    )


def built_index() -> str:
    """The built index.html the server actually serves."""
    return (STATIC / "index.html").read_text(encoding="utf-8")
