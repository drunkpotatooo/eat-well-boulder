import json
import sqlite3
import struct
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'store_bought.sqlite'


def get_store_id(conn, brand, store_code):
	row = conn.execute('SELECT id FROM stores WHERE brand = ? AND store_code = ?', (brand, store_code)).fetchone()
	if row: return row[0]
	else: return conn.execute('INSERT INTO stores (brand, store_code) VALUES (?, ?)', (brand, store_code)).lastrowid # create new if nonexistent


def put_observation(conn, payload):
	p = payload['product']
	store = get_store_id(conn, p['storeBrand'], p['storeCode'])
	values = (p['name'], p['image'], p['date'], p['price'], p['pricePer'], p['unit'], json.dumps(p.get('coupons', [])))
	row = conn.execute('SELECT id FROM products WHERE store = ? AND pid = ?', (store, p['pid'])).fetchone()
	if row:
		conn.execute(
			'UPDATE products SET name = ?, image = ?, time = ?, price = ?, price_per = ?, unit = ?, coupons = ? WHERE id = ?',
			values + (row[0],)
		)
	else:
		conn.execute(
			'INSERT INTO products (store, pid, name, image, time, price, price_per, unit, coupons) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
			(store, p['pid']) + values
		)
	conn.commit()


def claim_run(conn, payload):
	# gets run and deletes
	row = conn.execute('SELECT id, payload FROM runs ORDER BY id LIMIT 1').fetchone()
	if row is None:
		return None
	conn.execute('DELETE FROM runs WHERE id = ?', (row[0],))
	conn.commit()
	return {'id': row[0], 'payload': json.loads(row[1])}


ACTIONS = {
	'putObservation': put_observation,
	'claimRun': claim_run,
}


def read_message():
	raw_length = sys.stdin.buffer.read(4)
	if len(raw_length) == 0: return None # EOF
	message_length = struct.unpack('@I', raw_length)[0]
	message = sys.stdin.buffer.read(message_length).decode('utf-8')
	return json.loads(message)


def send_message(message):
	encoded = json.dumps(message, separators=(',', ':')).encode('utf-8')
	sys.stdout.buffer.write(struct.pack('@I', len(encoded)))
	sys.stdout.buffer.write(encoded)
	sys.stdout.buffer.flush()


def main():
	if not DB_PATH.exists():
		sys.exit('store_bought.sqlite not found - run create_db.py first.')
	conn = sqlite3.connect(DB_PATH)
	while True:
		msg = read_message()
		if msg is None: break # EOF
		try:
			handler = ACTIONS[msg['action']]
			result = handler(conn, msg.get('payload', {}))
			send_message({'id': msg.get('id'), 'result': result})
		except Exception as e: send_message({'id': msg.get('id'), 'error': f'{type(e).__name__}: {e}'})
	conn.close()


if __name__ == '__main__':
	main()
