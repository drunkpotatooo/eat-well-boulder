"""HTTP routes.

Thin view layer: each handler validates its inputs, calls into
``products``/``images``, and returns a template or JSON. No SQL lives here.
"""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, render_template, request

from . import images, products

bp = Blueprint("main", __name__)


@bp.route("/")
def search_page() -> str:
    """Render the single-page search UI."""
    return render_template("search.html")


@bp.route("/api/search")
def api_search() -> Response:
    """Return search results as JSON for the given query/unit/order."""
    results = products.search_products(
        request.args.get("query", ""),
        request.args.get("unit", "none"),
        request.args.get("order", "price_per"),
    )
    return jsonify({"results": results})


@bp.route("/api/history")
def api_history() -> Response | tuple[str, int]:
    """Return a product's current state plus its price/details history.

    Responds 400 if ``product`` is missing or not an integer, and 404 if no
    such product exists.
    """
    product_id = request.args.get("product", type=int)
    if product_id is None:
        return "missing or invalid 'product' id", 400
    history = products.product_history(product_id)
    if history is None:
        return "", 404
    return jsonify(history)


@bp.route("/img/<int:product_id>.svg")
def product_image(product_id: int) -> Response:
    """Serve a generated SVG placeholder for a product.

    The image is derived from the product name, so it is stable and needs no
    stored files and no external CDN. Responds 404 for unknown products.
    """
    name = products.product_name(product_id)
    if name is None:
        return Response("not found", status=404)
    svg = images.placeholder_svg(name)
    resp = Response(svg, mimetype="image/svg+xml")
    # Placeholders are deterministic, so let browsers cache them for a day.
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@bp.route("/robots.txt")
def robots() -> Response:
    """Ask crawlers not to index the site.

    The site is public so people can look up prices, but the underlying
    scraped dataset should not be indexed or mirrored in bulk.
    """
    return Response("User-agent: *\nDisallow: /\n", mimetype="text/plain")


@bp.route("/healthz")
def healthz() -> Response:
    """Liveness probe for hosting platforms (Render, Koyeb, ...)."""
    return jsonify({"status": "ok"})
