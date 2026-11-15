// importing this module sets up event listeners to open history modal upon click/enter on elements with data-product tag

import { el, img, table, money, age, fullDate, getJSON } from './common.js';
import { Chart, LinearScale, LineController, LineElement, PointElement, Tooltip, TimeScale } from 'https://cdn.jsdelivr.net/npm/chart.js@4.0.1/+esm';
import 'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/+esm';

Chart.register(LinearScale, LineController, LineElement, PointElement, Tooltip, TimeScale);
Chart.defaults.font.family = 'Carlito,Calibri,"Segoe UI",system-ui,-apple-system,Arial,sans-serif';
Chart.defaults.font.size = 14;


const overlay = document.getElementById('overlay');
overlay.addEventListener('click', e => { if (e.target === overlay) closeHistory(); });
document.addEventListener('click', e => openHistory(e.target.closest('[data-product]')));
document.addEventListener('keydown', e => {
	if (e.key === 'Escape' && !overlay.hidden) closeHistory();
	if (e.key === 'Enter') openHistory(e.target.closest?.('[data-product]'));
});

async function openHistory(node) {
	if (!node) return;
	let data;
	try {
		data = await getJSON('/api/history', { product: node.dataset.product });
	} catch {
		return;
	}
	document.getElementById('overlay-panel').replaceChildren(...render(data));
	overlay.hidden = false;
}

function closeHistory() {
	overlay.hidden = true;
}


const cssVar = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function render(data) {
	// current details header
	const p = data.product;
	const head = el('div', 'history-head');
	head.append(img(p.image));
	const title = el('div');
	title.append(el('h3', null, p.name), el('div', 'meta', p.store + ' - last checked ' + age(p.time)));
	head.append(title);
	const now = el('div', 'now');
	now.append(el('span', 'price', money(p.price)), el('span', 'per', money(p.price_per) + '/' + p.unit));
	head.append(now);
	
	// price chart
	const chart = el('canvas', 'history-section');
	new Chart(chart, {
		type: 'line',
		data: {
			datasets: [{
				data: data.prices.map(r => ({x: r.time * 1000, y: r.price_per})),
				borderColor: cssVar('--muted'),
				pointBackgroundColor: cssVar('--muted'),
				tension: 0.001
			}]
		},
		options: {
			scales: {
				x: {
					type: 'time',
					time: {
						minUnit: 'day'
					},
					ticks: {
						maxTicksLimit: 20,
						maxRotation: 0,
						autoSkipPadding: 20
					},
					grid: {
						display: false
					}
				},
				y: {
					beginAtZero: true,
					ticks: {
						callback: function(value, index, ticks) {
							if (index === ticks.length - 1) return '$' + value; // check if tick is highest
							else return value;
						}
					}
				}
			},
			interaction: {
				mode: 'nearest',
				axis: 'x',
				intersect: false
			},
			plugins: {
				tooltip: {
					displayColors: false,
					callbacks: {
						label: function(context) {
							let label = context.dataset.label || '';
							if (label) label += ': ';
							if (context.parsed.y !== null) label += '$' + context.parsed.y;
							return label;
						}
					}
				}
			}
		}
	});

	// price history table
	const prices = el('section', 'history-section');
	prices.append(el('h3', null, 'Prices'));
	prices.append(table(
		['When', 'Price', 'Per unit', 'Coupons'],
		data.prices.map(r => [fullDate(r.time), money(r.price), money(r.price_per) + '/' + r.unit, r.coupons.join(', ')])
	));

	// details history table
	const details = el('section', 'history-section');
	details.append(el('h3', null, 'Details'));
	details.append(table(
		['When', 'Name', 'Image'],
		data.details.map(r => [fullDate(r.time), r.name, r.image])
	));

	return [head, chart, prices, details];
}
