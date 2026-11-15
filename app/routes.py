"""HTTP routes.

Thin view layer: each handler validates its inputs, calls into
``products``/``images``, and returns a template or JSON. No SQL lives here.
"""

from __future__ import annotations

import gzip
import os

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
)

from . import images, products

bp = Blueprint("main", __name__)


# Gzipped copy of the demo page, rebuilt whenever the file on disk changes.
_demo_gzip: dict[str, object] = {"key": None, "body": b""}


def _demo_gzipped(path: str) -> bytes:
    """Return the demo page gzipped, recompressing only when the file changes."""
    stat = os.stat(path)
    key = (path, stat.st_mtime_ns, stat.st_size)
    if _demo_gzip["key"] != key:
        with open(path, "rb") as fh:
            _demo_gzip["body"] = gzip.compress(fh.read(), compresslevel=6)
        _demo_gzip["key"] = key
    return _demo_gzip["body"]  # type: ignore[return-value]


@bp.route("/")
def home() -> Response | str:
    """Serve the full Eat Well Boulder page, or the price browser without it.

    The page is one self-contained HTML file (``DEMO_PAGE``). The file is
    checked on every request, so replacing it updates the site at once. It is
    several megabytes, so browsers that accept gzip get a compressed copy.
    """
    demo = current_app.config["DEMO_PAGE"]
    if not os.path.isfile(demo):
        return render_template("search.html")
    if "gzip" in request.headers.get("Accept-Encoding", ""):
        resp = Response(_demo_gzipped(demo), mimetype="text/html")
        resp.headers["Content-Encoding"] = "gzip"
    else:
        resp = send_file(demo, mimetype="text/html")
    resp.headers["Vary"] = "Accept-Encoding"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@bp.route("/browse")
def search_page() -> str:
    """Render the plain price browser backed by the live database."""
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
