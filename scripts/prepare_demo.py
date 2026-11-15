"""Install the Eat Well Boulder page into the Flask app.

Copies the page's single HTML file, unchanged, to ``app/demo/index.html``,
which the app serves at ``/`` (the plain price browser stays at ``/browse``).

    python -I scripts/prepare_demo.py path/to/eat-well-boulder.html
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "app" / "demo" / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="the page's HTML file")
    args = parser.parse_args()

    head = args.source.read_bytes()[:4096].decode("utf-8", errors="replace")
    if "<title>Eat Well Boulder" not in head:
        print("error: this does not look like the Eat Well Boulder page", file=sys.stderr)
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.source, TARGET)
    print(f"wrote {TARGET} ({TARGET.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
