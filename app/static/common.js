// hits up endpoint, expects json
export async function getJSON(path, params = {}) {
	const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null));
	const resp = await fetch(query.size ? `${path}?${query}` : path);
	if (!resp.ok) throw new Error(`${path} responded ${resp.status}`);
	return resp.json();
}


// element factories
export function el(tag, cls, text) {
	const node = document.createElement(tag);
	if (cls) node.className = cls;
	if (text !== undefined) node.textContent = text;
	return node;
}

export function img(src) {
	const node = el('img');
	node.loading = 'lazy';
	node.src = src;
	return node;
}

export function table(headers, data) {
	const table = el('table');
	const headRow = el('tr');
	headers.forEach(h => headRow.append(el('th', null, h)));
	table.append(headRow);
	for (const row of data.toReversed()) {
		const tr = document.createElement('tr');
		row.forEach(col => tr.append(el('td', null, col)));
		table.append(tr);
	}
	return table;
}


// formatting utils
export function money(n) {
	return '$' + n.toFixed(2);
}

export function age(time) {
	const s = Math.max(0, Math.floor(Date.now() / 1000) - time);
	if (s < 60) return 'just now'; 
	if (s < 3600) return Math.floor(s / 60) + 'm ago';
	if (s < 86400) return Math.floor(s / 3600) + 'h ago';
	if (s < 86400 * 30) return Math.floor(s / 86400) + 'd ago';
	if (s < 86400 * 365) return Math.floor(s / (86400 * 30)) + 'mo ago';
	return Math.floor(s / (86400 * 365)) + 'y ago';
}

export function shortDate(t, spanDays = 0) {
	const opts = spanDays > 330 ? { month: 'short', year: 'numeric' } : { month: 'short', day: 'numeric' };
	return new Date(t * 1000).toLocaleDateString(undefined, opts);
}

export function fullDate(t) {
	return new Date(t * 1000).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}


export function productCard(p) {
	const card = el('div', 'card');

	// image, price, price per, coupons, name, store, time of last scan
	card.append(img(p.image));
	const line = el('div', 'price-line');
	line.append(el('span', 'price', money(p.price)), el('span', 'per', money(p.price_per) + '/' + p.unit));
	card.append(line);
	for (const c of p.coupons) card.append(el('span', 'coupon', c));
	card.append(el('div', 'name', p.name));
	card.append(el('div', 'meta', p.store + ' - ' + age(p.time)));

	// make clickable for history graph
	card.dataset.product = p.id;
	card.tabIndex = 0;
	card.setAttribute('role', 'button');

	return card;
}
