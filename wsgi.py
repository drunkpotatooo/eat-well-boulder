"""WSGI entry point.

Production servers (gunicorn, and therefore the Docker image used on Render or
Koyeb) import the module-level ``app`` object from here::

    gunicorn wsgi:app

Running this file directly starts Flask's built-in server, which is convenient
for local development but should not be used in production.
"""

from __future__ import annotations

import os

from app import create_app

app = create_app()


if __name__ == "__main__":
    # Local development server. ``PORT`` matches the convention hosting
    # platforms use, so `python wsgi.py` behaves like the deployed app.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=True)
