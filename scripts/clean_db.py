#!/usr/bin/env python3
"""Clean the Store Bought SQLite database for publishing and deployment.

The raw database collected by the scraper carries sub-day timestamps and image
URLs that point at the grocery stores' content-delivery networks. For a public,
deployable copy we do not need minute/hour precision and we must not ship or
call those CDNs. This script produces a cleaned copy that:

1. **Rounds every timestamp to the nearest day.** ``products.time``,
   ``price_history.time`` and ``details_history.time`` are snapped to the
   closest UTC midnight (``round(time / 86400) * 86400``).

2. **Collapses same-day history to one row.** After rounding, a product can
   have several history rows on the same day. We keep exactly one per
   ``(product, day)`` -- the row with the largest ``id``. Because ids increase
   with insertion order, that is the last observation of the day, and it also
   provides the tie-breaker when prices differ within a day ("differing prices
   on the same day can be tiebroken by ID").

3. **Replaces store-CDN image links.** Every ``image`` value becomes a local,
   app-served placeholder reference (``/img/<product id>.svg``). No store CDN is
   contacted at any point; the placeholders are generated from product names.

The history tables are maintained by triggers on ``products``. Rewriting the
image column would otherwise fire those triggers and log spurious changes, so
the triggers are saved, dropped for the duration of the rewrite, and recreated
exactly as they were.

The source database is never modified: the script copies it to the output path
first and operates on the copy. Run it with Python's isolated mode because the
input may be an untrusted file::

    python -I scripts/clean_db.py --input raw.sqlite --output data/store_bought.sqlite
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

SECONDS_PER_DAY = 86_400
# Table and timestamp column pairs whose times get rounded to the day.
_TIME_TABLES = ("products", "price_history", "details_history")
# History tables de-duplicated to one row per (product, rounded day).
_HISTORY_TABLES = ("price_history", "details_history")


def _round_timestamps(conn: sqlite3.Connection) -> None:
    """Snap every timestamp column to the nearest whole day (UTC midnight)."""
    for table in _TIME_TABLES:
        conn.execute(
            f"UPDATE {table} "
            f"SET time = CAST(ROUND(time / {SECONDS_PER_DAY}.0) AS INTEGER) "
            f"* {SECONDS_PER_DAY}"
        )


def _dedupe_history(conn: sqlite3.Connection) -> int:
    """Keep one row per ``(product, time)`` in each history table.

    The surviving row is the one with the greatest ``id`` (the last observation
    of the day, and the id tie-break for prices that differ within a day).

    Returns the total number of rows deleted.
    """
    removed = 0
    for table in _HISTORY_TABLES:
        cur = conn.execute(
            f"DELETE FROM {table} WHERE id NOT IN ("
            f"  SELECT MAX(id) FROM {table} GROUP BY product, time"
            f")"
        )
        removed += cur.rowcount
    return removed


def _replace_images(conn: sqlite3.Connection) -> None:
    """Point every image at a local, app-generated placeholder (no CDN)."""
    conn.execute("UPDATE products SET image = '/img/' || id || '.svg'")
    conn.execute("UPDATE details_history SET image = '/img/' || product || '.svg'")


def _save_and_drop_triggers(conn: sqlite3.Connection) -> list[str]:
    """Return the triggers' ``CREATE`` statements and drop the triggers.

    Returning the exact ``sql`` lets us recreate them verbatim afterwards,
    without duplicating the schema in this script.
    """
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' AND sql IS NOT NULL"
    ).fetchall()
    for name, _sql in rows:
        conn.execute(f'DROP TRIGGER IF EXISTS "{name}"')
    return [sql for _name, sql in rows]


def _restore_triggers(conn: sqlite3.Connection, statements: list[str]) -> None:
    """Recreate triggers from their saved ``CREATE`` statements."""
    for sql in statements:
        conn.execute(sql)


def _report(conn: sqlite3.Connection, label: str) -> None:
    """Print row counts and a couple of sanity checks for the open database."""
    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("products", "price_history", "details_history")
    }
    not_daily = conn.execute(
        "SELECT COUNT(*) FROM price_history WHERE time % 86400 != 0"
    ).fetchone()[0]
    cdn_images = conn.execute(
        "SELECT COUNT(*) FROM products WHERE image LIKE 'http%'"
    ).fetchone()[0]
    print(f"[{label}] products={counts['products']:,} "
          f"price_history={counts['price_history']:,} "
          f"details_history={counts['details_history']:,} "
          f"| non-daily timestamps={not_daily:,} | cdn image urls={cdn_images:,}")


def clean(input_path: Path, output_path: Path) -> None:
    """Produce a cleaned copy of ``input_path`` at ``output_path``."""
    if not input_path.exists():
        sys.exit(f"input database not found: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Operate on a copy so the source is never touched.
    if input_path.resolve() != output_path.resolve():
        shutil.copyfile(input_path, output_path)

    conn = sqlite3.connect(output_path)
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        # Emit a single, self-contained file: rollback-journal mode means no
        # -wal/-shm sidecars, so the database opens cleanly read-only (e.g. on a
        # read-only deployment filesystem).
        conn.execute("PRAGMA journal_mode = DELETE")
        _report(conn, "before")

        triggers = _save_and_drop_triggers(conn)
        _round_timestamps(conn)
        removed = _dedupe_history(conn)
        _replace_images(conn)
        _restore_triggers(conn, triggers)
        conn.commit()

        print(f"       removed {removed:,} duplicate same-day history rows")
        # Reclaim space freed by the deletes and refresh the query planner stats.
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        conn.commit()
        _report(conn, "after ")
    finally:
        conn.close()
    size_mb = output_path.stat().st_size / 1_000_000
    print(f"       wrote {output_path} ({size_mb:.1f} MB)")


def main(argv: list[str] | None = None) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input", type=Path, default=repo_root / "data" / "store_bought.sqlite",
        help="raw database to clean (default: data/store_bought.sqlite)",
    )
    parser.add_argument(
        "--output", type=Path, default=repo_root / "data" / "store_bought.sqlite",
        help="where to write the cleaned database (default: in place)",
    )
    args = parser.parse_args(argv)
    clean(args.input, args.output)


if __name__ == "__main__":
    main()
