"""Store Bought web application.

A small Flask app that serves a grocery price search over a read-only SQLite
database. It is built with the *application factory* pattern: :func:`create_app`
constructs and configures a fresh app instance. This keeps global state out of
import time and makes the app easy to run under a WSGI server (see ``wsgi.py``)
or in tests.
"""

from __future__ import annotations

from flask import Flask

from .config import Config


def create_app(config: type[Config] = Config) -> Flask:
    """Create and configure a Flask application instance.

    Args:
        config: Configuration class to load (defaults to :class:`Config`, which
            reads from the environment).

    Returns:
        A ready-to-serve :class:`flask.Flask` application.
    """
    app = Flask(__name__)
    app.config.from_object(config)

    # Register the per-request database teardown.
    from . import db

    db.init_app(app)

    # Register all HTTP routes.
    from .routes import bp

    app.register_blueprint(bp)

    return app
