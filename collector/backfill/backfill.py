import json
import sqlite3
from operator import itemgetter
import re

observations = []


def load_indexed_db(filename):
	indexed_db = json.load(open(filename))

	for p in indexed_db[0]['content']['products']:
		observations.append({
			'brand': p['storeBrand'],
			'store_code': p['storeId'],
			'pid': p['pid'],
			'name': p['name'],
			'image': p['image'],
			'time': round(p['date'] / 1000),
			'price': p['price'],
			'price_per': p['pricePer'],
			'unit': p['unit'],
			'coupons': json.dumps(p['coupons']),
		})

	print(f'{len(indexed_db[0]['content']['products'])} products loaded from {filename}')

	for p in indexed_db[0]['content']['prices']:
		details = next((product for product in indexed_db[0]['content']['products'] if product['storeBrand'] == p['storeBrand'] and product['storeId'] == p['storeId'] and product['pid'] == p['pid']), None)
		if details['date'] != p['date']:
			observations.append({
				'brand': p['storeBrand'],
				'store_code': p['storeId'],
				'pid': p['pid'],
				'name': details['name'],
				'image': details['image'],
				'time': round(p['date'] / 1000),
				'price': p['price'],
				'price_per': p['pricePer'],
				'unit': p['unit'],
				'coupons': json.dumps([]),
			})

	print(f'{len(indexed_db[0]['content']['prices'])} prices loaded from {filename}')


def load_sqlite(filename):
	db = sqlite3.connect(filename)
	db.row_factory = sqlite3.Row

	products = db.execute('SELECT brand, store_code, pid, products.name, image, time, price, price_per, unit, coupons FROM products JOIN stores ON products.store = stores.id').fetchall()
	for p in products:
		observations.append({
			'brand': p['brand'],
			'store_code': p['store_code'],
			'pid': p['pid'],
			'name': p['name'],
			'image': p['image'],
			'time': round(p['time'] / 1000),
			'price': p['price'],
			'price_per': p['price_per'],
			'unit': p['unit'],
			'coupons': p['coupons'],
		})

	print(f'{len(products)} products loaded from {filename}')

	prices = db.execute('SELECT product, time, price, price_per, unit, coupons FROM price_history').fetchall()
	for price in prices:
		detail = db.execute('SELECT name, image FROM details_history WHERE time <= ? AND product = ? ORDER BY time DESC LIMIT 1', (price['time'], price['product'])).fetchone()
		product = db.execute('SELECT brand, store_code, pid FROM products JOIN stores ON products.store = stores.id WHERE products.id = ?', (price['product'],)).fetchone()
		observations.append({
			'brand': product['brand'],
			'store_code': product['store_code'],
			'pid': product['pid'],
			'name': detail['name'],
			'image': detail['image'],
			'time': round(price['time'] / 1000),
			'price': price['price'],
			'price_per': price['price_per'],
			'unit': price['unit'],
			'coupons': price['coupons'],
		})

	print(f'{len(prices)} prices loaded from {filename}')

	details = db.execute('SELECT product, time, name, image FROM details_history').fetchall()
	for detail in details:
		price = db.execute('SELECT price, price_per, unit, coupons FROM price_history WHERE time <= ? AND product = ? ORDER BY time DESC LIMIT 1', (detail['time'], detail['product'])).fetchone()
		product = db.execute('SELECT brand, store_code, pid FROM products JOIN stores ON products.store = stores.id WHERE products.id = ?', (detail['product'],)).fetchone()
		observations.append({
			'brand': product['brand'],
			'store_code': product['store_code'],
			'pid': product['pid'],
			'name': detail['name'],
			'image': detail['image'],
			'time': round(detail['time'] / 1000),
			'price': price['price'],
			'price_per': price['price_per'],
			'unit': price['unit'],
			'coupons': price['coupons'],
		})

	print(f'{len(details)} details loaded from {filename}')


load_indexed_db('indexed_db.json')
load_sqlite('august.sqlite')
load_sqlite('september.sqlite')


print(f'All data loaded, {len(observations)} observations in total')

print('Normalizing...')

for product in observations:
	# make unit lowercase before removing special chars, nums, whitespace, 'per' from beginning, 's' from end
	unit = re.sub(r'[^a-z]', '', product['unit'].lower()).removeprefix('per').removesuffix('s')
	match (unit):
		case 'oz' | 'ounce' | 'reconstitutedounce':
			product['price_per'] *= 16
			product['unit'] = 'lb'
		case 'gram' | 'g':
			product['price_per'] *= 453.592
			product['unit'] = 'lb'
		case 'kilogram' | 'kg':
			product['price_per'] *= 0.453592
			product['unit'] = 'lb'
		case 'lb' | 'pound':
			product['unit'] = 'lb'
		case 'ea' | 'each' | 'count' | 'cnt' | 'ct' | 'per' | 'unit' | 'piece' | 'pc' | 'pack' | 'pk' | 'roll' | 'plate' | 'stem' | 'bunch' | 'x':
			product['unit'] = 'ea'
		case 'dozen':
			product['price_per'] *= 1 / 12
			product['unit'] = 'ea'
		case 'milliliter' | 'ml':
			product['price_per'] *= 3785.41
			product['unit'] = 'gal'
		case 'fluidounce' | 'flounce' | 'fluidoz' | 'floz' | 'fl':
			product['price_per'] *= 128
			product['unit'] = 'gal'
		case 'pint' | 'pt':
			product['price_per'] *= 8
			product['unit'] = 'gal'
		case 'drypint' | 'drypt' | 'drpt':
			product['price_per'] *= 6.87494
			product['unit'] = 'gal'
		case 'quart' | 'qt':
			product['price_per'] *= 4
			product['unit'] = 'gal'
		case 'liter' | 'litre' | 'litr' | 'ltr' | 'l':
			product['price_per'] *= 3.78541
			product['unit'] = 'gal'
		case 'gal' | 'gallon' | 'gl':
			product['unit'] = 'gal'
		case 'sqft' | 'squarefeet' | 'sf':
			product['unit'] = 'sqft'
		case 'sqyd' | 'squareyard' | 'sy':
			product['unit'] = 'sqyd'
		case _:
			product['unit'] = unit

print('Removing duplicates...')

observations = [dict(t) for t in {tuple(d.items()) for d in observations}]

print(f'Deduplicated, new length: {len(observations)}')

print('Sorting...')

observations.sort(key=itemgetter('time'))

# with open('store_bought.json', 'w', encoding='utf-8') as f:
# 	json.dump(observations, f, indent='\t')

def get_store_id(conn, brand, store_code):
	row = conn.execute('SELECT id FROM stores WHERE brand = ? AND store_code = ?', (brand, store_code)).fetchone()
	if row: return row[0]
	else: return conn.execute('INSERT INTO stores (brand, store_code) VALUES (?, ?)', (brand, store_code)).lastrowid # create new if nonexistent

def put_observation(conn, p):
	store = get_store_id(conn, p['brand'], p['store_code'])
	values = (p['name'], p['image'], p['time'], p['price'], p['price_per'], p['unit'], p['coupons'])
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
	
canon = sqlite3.connect('store_bought.sqlite')

print('Database connected, upserting...')

for observation in observations:
	put_observation(canon, observation)

canon.commit()
canon.execute('VACUUM')
canon.close()

print('All done!')
