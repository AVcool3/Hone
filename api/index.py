"""Vercel serverless entrypoint.

Vercel's Python runtime detects the ASGI ``app`` variable and serves it;
``vercel.json`` rewrites every route here, and FastAPI handles the rest
(including serving the single-page UI at ``/``).

The hone package is normally importable because requirements.txt
installs it (the ``.`` line).  A repo-root sys.path entry covers local
checkouts, and if the import still fails the fallback app returns the
boot traceback instead of an opaque FUNCTION_INVOCATION_FAILED page.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from hone.web.app import app  # noqa: F401
except Exception:  # pragma: no cover - only reachable on broken deploys
    import traceback

    boot_error = traceback.format_exc()

    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    app = FastAPI(title="Hone (boot error)")

    @app.api_route("/{path:path}", methods=["GET", "POST"])
    def report(path: str) -> PlainTextResponse:
        return PlainTextResponse(
            "Hone failed to start. Boot error:\n\n" + boot_error,
            status_code=500,
        )
