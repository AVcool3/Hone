"""Vercel serverless entrypoint.

Vercel's Python runtime detects the ASGI ``app`` variable and serves it;
``vercel.json`` rewrites every route here, and FastAPI handles the rest
(including serving the single-page UI at ``/``).
"""

import os
import sys

# Make the repo root importable when Vercel bundles the function.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hone.web.app import app  # noqa: E402,F401
