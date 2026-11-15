"""Product queries and shaping.

This module turns rows from the ``products``, ``price_history`` and
``details_history`` tables into the plain dictionaries the frontend consumes.
It contains all of the SQL so the view layer (``routes.py``) stays thin.

The database schema is described in ``scripts/create_db.py``. In short:

* ``products`` holds one current row per product per store.
* ``price_history`` / ``details_history`` are append-only change logs kept by
  triggers, so a product's full timeline is the history rows plus its current
  row.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from flask import current_app

from .db import query, query_one

# Columns selected for a product "card". Joined with ``stores`` so each product
# carries a human-readable store name. Kept as one constant so the search and
# history queries cannot drift apart.
_PRODUCT_COLUMNS = (
    "p.id, p.pid, p.name, p.image, p.time, p.price, p.price_per, p.unit, "
    "p.coupons, s.brand AS store_brand, s.store_code, s.name AS store_name"
)
_PRODUCT_FROM = "FROM products p JOIN stores s ON s.id = p.store"

# Units offered in the UI's unit filter, plus the orderings we allow. Validating
# against these sets keeps untrusted query-string values out of the SQL.
_VALID_ORDERS = {"price_per", "time"}


def _product_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a product row into a JSON-ready dict.

    Parses the ``coupons`` JSON blob and collapses the store columns into a
    single display name (the manually-entered name if present, otherwise
    ``"<brand> #<code>"``).
    """
    product = dict(row)
    product["coupons"] = json.loads(product["coupons"])
    product["store"] = product.pop("store_name") or (
        f"{product['store_brand']} #{product['store_code']}"
    )
    return product


def search_products(query_text: str, unit: str, order: str) -> list[dict[str, Any]]:
    """Search products by name, optionally filtered by unit and ordered.

    Args:
        query_text: Substring matched against the product name (case-insensitive).
        unit: Exact unit to filter by, or ``"none"`` for no unit filter.
        order: ``"price_per"`` (cheapest per unit first) or ``"time"`` (newest
            first). Anything else falls back to ``"price_per"``.

    Returns:
        Up to ``SEARCH_LIMIT`` product dicts.
    """
    sql = [f"SELECT {_PRODUCT_COLUMNS}", _PRODUCT_FROM, "WHERE p.name LIKE ?"]
    params: list[Any] = [f"%{query_text}%"]

    if unit and unit != "none":
        sql.append("AND p.unit = ?")
        params.append(unit)

    if order not in _VALID_ORDERS:
        order = "price_per"
    if order == "time":
        sql.append("ORDER BY p.time DESC, p.id DESC")
    else:
        sql.append("ORDER BY p.price_per, p.time DESC")

    sql.append("LIMIT ?")
    params.append(current_app.config["SEARCH_LIMIT"])

    return [_product_dict(row) for row in query(" ".join(sql), tuple(params))]


def product_history(product_id: int) -> dict[str, Any] | None:
    """Return a product's current state plus its price and details timelines.

    The full history is the logged change rows *plus* the product's current row
    (the latest state is not duplicated into the history tables until it next
    changes). Rows are de-duplicated by timestamp so each day appears once,
    matching the day-level precision of the cleaned database.

    Returns ``None`` if no product has the given id.
    """
    row = query_one(
        f"SELECT {_PRODUCT_COLUMNS} {_PRODUCT_FROM} WHERE p.id = ?", (product_id,)
    )
    if row is None:
        return None
    product = _product_dict(row)

    prices = [
        dict(r) | {"coupons": json.loads(r["coupons"])}
        for r in query(
            "SELECT time, price, price_per, unit, coupons FROM price_history "
            "WHERE product = ? ORDER BY time, id",
            (product_id,),
        )
    ]
    details = [
        dict(r)
        for r in query(
            "SELECT time, name, image FROM details_history "
            "WHERE product = ? ORDER BY time, id",
            (product_id,),
        )
    ]

    # Fold the current state in as the most recent point of each timeline.
    prices.append({k: product[k] for k in ("time", "price", "price_per", "unit", "coupons")})
    details.append({k: product[k] for k in ("time", "name", "image")})

    # One entry per timestamp (last write for a given day wins).
    prices = list({d["time"]: d for d in prices}.values())
    details = list({d["time"]: d for d in details}.values())

    return {"product": product, "prices": prices, "details": details}


def product_name(product_id: int) -> str | None:
    """Return just the name of a product, or ``None`` if it does not exist.

    Used by the placeholder image route, which only needs the name to choose a
    category and colour.
    """
    row = query_one("SELECT name FROM products WHERE id = ?", (product_id,))
    return row["name"] if row else None
