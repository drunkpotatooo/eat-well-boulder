"""SQLite access helpers.

The application keeps **no** data in memory between requests. Every request
opens a connection to the SQLite file named by ``app.config['DATABASE']``,
runs its queries, and the connection is closed when the request ends. This is
what guarantees that the page always reflects the current contents of the
database file (the requirement that the site "read from the main sqlite file
at every stage"). It also makes the app safe to run under multiple worker
processes, since no connection is shared across requests or threads.

Connections are opened read-only. The web app never writes to the database;
writes are the job of the data collector (see ``collector/``).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from flask import Flask, current_app, g


def get_db() -> sqlite3.Connection:
    """Return the SQLite connection for the current request.

    The connection is created lazily on first use and cached on Flask's
    request-scoped ``g`` object, so repeated calls within one request reuse it.
    Rows are returned as :class:`sqlite3.Row`, which behaves like both a tuple
    and a dict.
    """
    if "db" not in g:
        # ``uri=True`` lets us pass ?mode=ro to open the file read-only. If the
        # file is missing this raises immediately, which is the behaviour we
        # want (fail fast rather than silently create an empty database).
        db_path = current_app.config["DATABASE"]
        g.db = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception: BaseException | None = None) -> None:
    """Close the request's connection, if one was opened.

    Registered as a teardown handler, so it runs after every request whether or
    not it succeeded.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    """Run ``sql`` with ``params`` and return all rows.

    A thin convenience wrapper around :meth:`sqlite3.Connection.execute` that
    always uses parameter substitution, so callers never interpolate values
    into SQL strings.
    """
    return get_db().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    """Run ``sql`` with ``params`` and return the first row, or ``None``."""
    return get_db().execute(sql, params).fetchone()


def init_app(app: Flask) -> None:
    """Wire database teardown into the application's lifecycle."""
    app.teardown_appcontext(close_db)
