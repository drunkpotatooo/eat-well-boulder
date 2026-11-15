# Store Bought

A small web app for finding the true, discount-aware price of groceries and
comparing it across local stores. It serves a search UI and price-history
charts over a SQLite database of prices collected from Safeway, King Soopers,
and Whole Foods.

This repository is the **web application and the published dataset**. The
browser extension and tools that *collect* the prices live under
[`collector/`](collector/) and are not part of the deployed site.

---

## How it works

- **Flask app, read-only SQLite.** The site is a [Flask](https://flask.palletsprojects.com/)
  application (the [application factory](https://flask.palletsprojects.com/en/latest/patterns/appfactories/)
  pattern). Every request opens a fresh connection to the SQLite file, runs its
  queries, and closes it. Nothing is cached in memory, so the page always
  reflects the **current contents of the database file** — drop in a newer
  database and the next request serves it.
- **Two JSON endpoints** back a single-page UI: `/api/search` (search by name,
  filter by unit, order by price-per-unit or recency) and `/api/history`
  (a product's full price and detail timeline).
- **Offline images.** Products are shown with generated SVG placeholders served
  from `/img/<id>.svg`. The original data referenced the stores' image CDNs; we
  neither redistribute those images nor call those CDNs. Placeholders are
  derived from the product name (a food-category glyph plus a colour), so they
  are stable and "similar" to the product without any network calls.

## Project layout

```
store-bought/
├── app/                     # the Flask application package
│   ├── __init__.py          #   create_app() factory
│   ├── config.py            #   configuration from environment variables
│   ├── db.py                #   per-request read-only SQLite connections
│   ├── products.py          #   search / history queries (all the SQL)
│   ├── images.py            #   deterministic SVG placeholder generator
│   ├── routes.py            #   HTTP routes (thin view layer)
│   ├── templates/           #   Jinja templates
│   └── static/              #   CSS + JS (vanilla, ES modules)
├── data/
│   └── store_bought.sqlite  # the cleaned, deploy-ready database
├── scripts/
│   ├── create_db.py         # creates the schema + history triggers
│   └── clean_db.py          # produces the cleaned database (see below)
├── collector/               # the price scraper (Firefox extension + host)
├── wsgi.py                  # WSGI entry point (gunicorn wsgi:app)
├── Dockerfile               # container image for Render / Koyeb / Fly
├── render.yaml              # Render Blueprint
└── requirements.txt
```

## Run it locally

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Development server (auto-reload) on http://127.0.0.1:8000
python wsgi.py

# Or exactly as it runs in production:
gunicorn wsgi:app
```

By default the app reads `data/store_bought.sqlite`. Point it elsewhere with the
`DATABASE` environment variable:

```bash
DATABASE=/path/to/other.sqlite python wsgi.py
```

## The database

The schema (five tables plus history-maintaining triggers) is defined in
[`scripts/create_db.py`](scripts/create_db.py) and described in
[`collector/ORIGINAL_README.md`](collector/ORIGINAL_README.md). In brief:

| table | purpose |
| --- | --- |
| `stores` | one row per store (brand, code, name) |
| `products` | current state of each product (name, image, price, unit, coupons, time) |
| `price_history` / `details_history` | append-only change logs kept by triggers |
| `runs` | queue for the scraper's auto-browse feature |

### Cleaning (`scripts/clean_db.py`)

The database shipped in `data/` has been cleaned for publishing. From a raw
scraper database, the cleaner produces a copy that is:

1. **Day-precise** — every timestamp is rounded to the nearest day. Minute/hour
   precision is not needed for price trends.
2. **De-duplicated** — after rounding, only one history row is kept per product
   per day: the one with the largest `id` (the last observation of the day, and
   the tie-break when prices differ within a day).
3. **CDN-free** — every image URL is replaced with a local `/img/<id>.svg`
   reference. No store CDN is contacted.

The history triggers are saved, dropped during the rewrite, and recreated
verbatim so rewriting the image column does not log spurious changes. The source
file is never modified.

```bash
python -I scripts/clean_db.py --input raw.sqlite --output data/store_bought.sqlite
```

On the shipped data this rounds 114k timestamps, removes ~17.8k duplicate
same-day rows, and shrinks the file from 27 MB to ~18 MB.

## Deploy

The app is a standard Docker web service that listens on `$PORT`.

**Docker (local):**

```bash
docker build -t store-bought .
docker run -p 8000:8000 store-bought   # http://localhost:8000
```

**Render:** New → Blueprint, point it at this repo. `render.yaml` configures a
free Docker web service with a `/healthz` health check. Render supplies `$PORT`.

**Koyeb:** New Service → Docker/GitHub, select this repo. Koyeb detects the
`Dockerfile` and injects `$PORT`; set the health check path to `/healthz`.

The cleaned database is committed to the repo and copied into the image, so the
service is self-contained — no external database to provision. To publish newer
prices, replace `data/store_bought.sqlite` and redeploy.

## Collector

[`collector/`](collector/) holds the Firefox extension and Python host that
gather the price data by native messaging. It is kept for completeness and is
**not** required to run or deploy the website. See
[`collector/ORIGINAL_README.md`](collector/ORIGINAL_README.md) for setup.
