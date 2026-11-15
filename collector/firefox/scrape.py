import configparser
import json
import random
import sqlite3
import sys
from pathlib import Path

PARENT_DIR = Path(__file__).resolve().parent
DB_PATH = PARENT_DIR.parent / 'store_bought.sqlite'
QUERIES_PATH = PARENT_DIR / 'queries.txt'
STORES_PATH = PARENT_DIR / 'stores.txt'
SETTINGS_PATH = PARENT_DIR / 'settings.ini'


def read_lines(path):
	# nonempty, non-comment lines
	lines = Path(path).read_text().splitlines()
	return [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]


def load_queries(path=QUERIES_PATH):
	return [line.lower() for line in read_lines(path)]


def load_stores(path=STORES_PATH):
	stores = []
	for line in read_lines(path):
		cols = [col.strip() for col in line.split(',')]
		if len(cols) != 3:
			sys.exit(f'Bad store line (need brand, zipcode, store code): {line}')
		brand, zipcode, store_code = (col.lower() for col in cols)
		stores.append([brand, zipcode, store_code])
	return stores


def load_settings(path=SETTINGS_PATH):
	parser = configparser.ConfigParser()
	parser.read(path)
	return {
		'min_wait': parser.getint('scrape', 'min_wait', fallback=4000),
		'max_wait': parser.getint('scrape', 'max_wait', fallback=6000),
		'scroll_pages': parser.getint('scrape', 'scroll_pages', fallback=10),
	}


def fill_queue(conn, queries, stores, settings):
	# one run per query x store pair, random order
	pairs = [(query, store) for query in queries for store in stores]
	random.shuffle(pairs)
	for query, store in pairs:
		payload = {
			'query': query,
			'store': store,
			'minWait': settings['min_wait'],
			'maxWait': settings['max_wait'],
			'scrollPages': settings['scroll_pages'],
		}
		conn.execute('INSERT INTO runs (payload) VALUES (?)', (json.dumps(payload),))
	conn.commit()
	return len(pairs)


def main():
	if not DB_PATH.exists():
		sys.exit('store_bought.sqlite not found - run create_db.py first.')
	conn = sqlite3.connect(DB_PATH)

	# delete all runs
	conn.execute('DELETE FROM runs;')

	# create new runs
	queries = load_queries()
	stores = load_stores()
	queued = fill_queue(conn, queries, stores, load_settings())
	print(f'Queued {queued} runs: {len(queries)} queries x {len(stores)} stores, shuffled')


if __name__ == '__main__':
	main()
