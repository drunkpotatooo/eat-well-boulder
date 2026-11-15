import { getJSON, productCard } from './common.js';
import './history.js';

const controls = document.getElementById('controls');
controls.addEventListener('change', search);

async function search() {
	const query = controls.querySelector('#q').value;
	const unit = controls.querySelector('#q-unit').value;
	const order = controls.querySelector('#q-order').value;
	const data = await getJSON('/api/search', { query: query, unit: unit, order: order });
	document.getElementById('results').replaceChildren(...data.results.map(productCard));
}

search();
let intervalId = undefined;
document.getElementById('q-refresher').addEventListener('click', e => {
	if (intervalId === undefined) intervalId = setInterval(search, 2000);
	else intervalId = clearInterval(intervalId);
});
