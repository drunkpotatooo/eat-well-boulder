"""Deterministic, offline product image placeholders.

The raw price data was collected with image URLs that pointed at the grocery
stores' own content-delivery networks (``images.albertsons-media.com`` and
``www.kroger.com``). We do not redistribute those images or call those CDNs at
run time. Instead, every product shows a generated placeholder:

* The product name is matched against a small keyword table to pick a food
  *category* (produce, dairy, meat, ...), which decides the emoji glyph and the
  base colour. This makes the placeholder "similar" to the product.
* A hash of the name nudges the hue and the gradient, so two products in the
  same category still look distinct, and the same product always looks the same.

The result is a self-contained SVG string. SVG is used (rather than PNG) so the
app needs no image libraries and the placeholders stay crisp at any size.
"""

from __future__ import annotations

import hashlib
from html import escape

# Keyword -> (emoji glyph, base hue in degrees). The first keyword found in a
# lowercased product name wins, so compound/specific terms are listed before the
# broad ones they contain (e.g. "ice cream" before "cream", "bread" before
# "milk", "chip" before "potato").
_CATEGORIES: list[tuple[tuple[str, ...], str, int]] = [
    (("ice cream", "frozen", "popsicle", "gelato"), "\U0001F366", 265),                            # ice cream
    (("bread", "bagel", "bun", "tortilla", "roll", "bakery", "muffin"), "\U0001F956", 35),         # bread
    (("chip", "cookie", "candy", "chocolate", "snack", "cracker", "popcorn", "pretzel"), "\U0001F36A", 25),  # cookie
    (("milk", "cream", "yogurt", "yoghurt", "cheese", "butter", "dairy"), "\U0001F9C0", 45),       # cheese
    (("egg",), "\U0001F95A", 45),                                                                  # egg
    (("chicken", "beef", "steak", "pork", "bacon", "sausage", "ham", "turkey", "meat"), "\U0001F356", 5),    # meat
    (("salmon", "tuna", "shrimp", "fish", "seafood", "crab", "lobster"), "\U0001F41F", 200),       # fish
    (("apple", "banana", "berry", "grape", "melon", "orange", "peach", "pear", "mango", "fruit"), "\U0001F34E", 355),  # fruit
    (("broccoli", "carrot", "lettuce", "potato", "onion", "pepper", "tomato", "spinach", "celery", "veg"), "\U0001F966", 130),  # vegetable
    (("water", "soda", "cola", "juice", "tea", "coffee", "drink", "beverage", "soft drink"), "\U0001F964", 210),       # cup
    (("rice", "pasta", "cereal", "oat", "grain", "flour", "noodle"), "\U0001F35A", 40),            # rice
]
_DEFAULT = ("\U0001F6D2", 215)  # shopping cart, cool blue


def _seed(text: str) -> int:
    """Stable 0..2^32 integer derived from ``text`` (not Python's salted hash)."""
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)


def categorize(name: str) -> tuple[str, int]:
    """Return ``(emoji, hue)`` for a product name."""
    low = name.lower()
    for keywords, emoji, hue in _CATEGORIES:
        if any(k in low for k in keywords):
            return emoji, hue
    return _DEFAULT


def placeholder_svg(name: str, size: int = 300) -> str:
    """Build a self-contained SVG placeholder for a product ``name``.

    Args:
        name: Product name; drives both the category glyph and the colour.
        size: Width/height of the square SVG in pixels.

    Returns:
        A complete ``<svg>...</svg>`` document as a string.
    """
    emoji, base_hue = categorize(name)
    seed = _seed(name)

    # Vary the hue a little within the category and pick two tones for a gentle
    # diagonal gradient. Keep saturation/lightness in a tasteful, muted range.
    hue = (base_hue + (seed % 24) - 12) % 360
    top = f"hsl({hue}, 48%, 86%)"
    bottom = f"hsl({(hue + 18) % 360}, 42%, 74%)"
    ink = f"hsl({hue}, 40%, 28%)"

    # A short, cleaned label from the first words of the name.
    label = escape(" ".join(name.split()[:3])[:22])
    grad_id = f"g{seed:x}"

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'role="img" aria-label="{escape(name)}">'
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{top}"/>'
        f'<stop offset="1" stop-color="{bottom}"/></linearGradient></defs>'
        f'<rect width="{size}" height="{size}" rx="{size // 12}" fill="url(#{grad_id})"/>'
        f'<text x="50%" y="46%" font-size="{int(size * 0.42)}" text-anchor="middle" '
        f'dominant-baseline="central">{emoji}</text>'
        f'<text x="50%" y="84%" font-size="{int(size * 0.072)}" text-anchor="middle" '
        f'font-family="Inter, system-ui, Arial, sans-serif" fill="{ink}" '
        f'font-weight="600">{label}</text>'
        f"</svg>"
    )
