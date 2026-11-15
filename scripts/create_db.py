"""Create the Store Bought SQLite schema.

Defines the five tables (``stores``, ``products``, ``price_history``,
``details_history``, ``runs``) and the triggers that maintain the two
append-only history logs whenever a product is inserted or updated. Running it
against an existing database is safe: every statement uses ``IF NOT EXISTS``.

    python scripts/create_db.py

The resulting file is written next to this script unless ``DB_PATH`` is changed.
The web app and the cleaner refer to the database in ``data/``; this script is
the authoritative definition of its shape.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'store_bought.sqlite'

SCHEMA = """
CREATE TABLE IF NOT EXISTS stores (
	id INTEGER PRIMARY KEY,
	brand TEXT NOT NULL,
	store_code TEXT NOT NULL,
	name TEXT NOT NULL DEFAULT '',
	UNIQUE (brand, store_code)
);

CREATE TABLE IF NOT EXISTS products (
	id INTEGER PRIMARY KEY,
	store INTEGER NOT NULL REFERENCES stores(id),
	pid TEXT NOT NULL,
	name TEXT NOT NULL,
	image TEXT NOT NULL,
	time INTEGER NOT NULL,
	price REAL NOT NULL,
	price_per REAL NOT NULL,
	unit TEXT NOT NULL,
	coupons TEXT NOT NULL DEFAULT '[]',
	embedding BLOB,
	UNIQUE (store, pid)
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products(name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS price_history (
	id INTEGER PRIMARY KEY,
	product INTEGER NOT NULL REFERENCES products(id),
	time INTEGER NOT NULL,
	price REAL NOT NULL,
	price_per REAL NOT NULL,
	unit TEXT NOT NULL,
	coupons TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product, time);

CREATE TABLE IF NOT EXISTS details_history (
	id INTEGER PRIMARY KEY,
	product INTEGER NOT NULL REFERENCES products(id),
	time INTEGER NOT NULL,
	name TEXT NOT NULL,
	image TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_details_history_product ON details_history(product, time);

CREATE TABLE IF NOT EXISTS runs (
	id INTEGER PRIMARY KEY,
	payload TEXT NOT NULL
);

-- if new row gets inserted into products, add info to price_history and details_history
CREATE TRIGGER IF NOT EXISTS products_insert AFTER INSERT ON products
BEGIN
	INSERT INTO price_history (product, time, price, price_per, unit, coupons)
	VALUES (new.id, new.time, new.price, new.price_per, new.unit, new.coupons);
	INSERT INTO details_history (product, time, name, image)
	VALUES (new.id, new.time, new.name, new.image);
END;

-- if a product's price, unit, or coupons changes, add two rows to price history recording most recent observation of old price and current new price
CREATE TRIGGER IF NOT EXISTS products_price_change AFTER UPDATE ON products
WHEN old.price != new.price OR old.price_per != new.price_per OR old.unit != new.unit OR old.coupons != new.coupons
BEGIN
	INSERT INTO price_history (product, time, price, price_per, unit, coupons)
	VALUES (old.id, old.time, old.price, old.price_per, old.unit, old.coupons);
	INSERT INTO price_history (product, time, price, price_per, unit, coupons)
	VALUES (new.id, new.time, new.price, new.price_per, new.unit, new.coupons);
END;

-- similar as above for product details
CREATE TRIGGER IF NOT EXISTS products_details_change AFTER UPDATE ON products
WHEN old.name != new.name OR old.image != new.image
BEGIN
	INSERT INTO details_history (product, time, name, image)
	VALUES (old.id, old.time, old.name, old.image);
	INSERT INTO details_history (product, time, name, image)
	VALUES (new.id, new.time, new.name, new.image);
END;

-- remove embedding if name changes
CREATE TRIGGER IF NOT EXISTS products_name_change AFTER UPDATE ON products
WHEN old.name != new.name
BEGIN
	UPDATE products SET embedding = NULL WHERE id = new.id;
END;
"""


def main():
	conn = sqlite3.connect(DB_PATH)
	conn.execute('PRAGMA journal_mode=WAL')
	conn.executescript(SCHEMA)
	conn.commit()
	print(f'Database ready at {DB_PATH}')


if __name__ == '__main__':
	main()
