"""Web layer: FastAPI app serving the JSON API and the single-page UI.

Run with ``python -m hone serve`` (or ``uvicorn hone.web.app:app``).
"""

from .app import app, create_app

__all__ = ["app", "create_app"]
