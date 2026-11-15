"""Application configuration.

All settings are read from environment variables so the same image can run
unchanged in development, in Docker, and on a hosting service such as Render
or Koyeb. Nothing here holds secrets; the defaults are safe for local use.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repository root (one level above the ``app`` package).
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Runtime configuration resolved from the environment.

    Attributes:
        DATABASE: Absolute path to the SQLite file the app reads from. The app
            opens a fresh connection per request, so whatever this file
            contains at request time is what the user sees.
        SEARCH_LIMIT: Maximum number of rows returned by a single search.
        DEMO_PAGE: Path to the full Eat Well Boulder page. When this file
            exists it is served at ``/``; the plain price browser stays at
            ``/browse``. When it is missing, ``/`` falls back to the browser.
        JSON_SORT_KEYS: Kept ``False`` so JSON responses preserve insertion
            order, which keeps payloads stable and diff-friendly.
    """

    # Default to the database shipped inside the repository (``data/``). Override
    # with the DATABASE environment variable to point at another file.
    DATABASE: str = os.environ.get(
        "DATABASE", str(BASE_DIR / "data" / "store_bought.sqlite")
    )

    SEARCH_LIMIT: int = int(os.environ.get("SEARCH_LIMIT", "200"))

    DEMO_PAGE: str = os.environ.get(
        "DEMO_PAGE", str(BASE_DIR / "app" / "demo" / "index.html")
    )

    JSON_SORT_KEYS: bool = False
