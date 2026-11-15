import {standardize} from '../utils.js'
import {sendToHost} from '../native.js'


// king sooper's API responses can be directly accessed for data, so we'll use that
export function setupKingSoopersListeners() {
	browser.webRequest.onBeforeRequest.addListener(
		readAPIResponse,
		{ urls: ['https://www.kingsoopers.com/atlas/v1/product/v2/products?*'] },
		['blocking']
	);
}


// callback for API listener, copy data as it comes in and send to processAPIResponse at the end
function readAPIResponse(details) {
	const filter = browser.webRequest.filterResponseData(details.requestId);
	let decoder = new TextDecoder('utf-8');
	let body = '';
	filter.ondata = event => {
		filter.write(event.data);
		body += decoder.decode(event.data, { stream: true });
	};
	filter.onstop = event => {
		filter.close();
		processAPIResponse(body);
	};
}


async function processAPIResponse(body) {

	// parse API response docs
	const parsed = JSON.parse(body);
	for (const rawProduct of parsed.data.products) {

		// these values are rather muddled to get
		const {price, pricePer, unit} = getPrices(rawProduct);

		const cleanProduct = {
			storeBrand: 'kingsoopers',
			storeCode: rawProduct?.price?.storePrices?.sourceLocationId || rawProduct?.inventory?.locations?.[0]?.locationId || rawProduct?.sourceLocations?.[0]?.id,
			pid: rawProduct?.id,
			name: rawProduct?.item?.description,
			image: `https://www.kroger.com/product/images/medium/front/${rawProduct?.id}`,
			coupons: rawProduct?.offers?.map(offer => offer?.defaultDescription) || [],
			date: Math.round(Date.now() / 1000),
			price: price,
			pricePer: pricePer,
			unit: unit
		};

		// standardize data
		if (!standardize(cleanProduct)) continue;

		// add to DB
		sendToHost('putObservation', { product: cleanProduct }).catch(e => console.warn('Failed to save observation:', e));

	}
}


// several methods to try and get unit price because there doesn't seem to be any one way they store it
function getPrices(rawProduct) {

	// account for promos
	const storePrice = rawProduct?.price?.storePrices?.promo || rawProduct?.price?.storePrices?.regular;

	// price should be straightforward
	const price = Number(storePrice?.price?.slice(4));

	// these two are not
	let pricePer;
	let unit;

	// try interpreting from secondaryDescription
	const secDescSplit = storePrice?.secondaryDescription?.split('/');
	pricePer = Number(secDescSplit?.[0]?.slice(1));
	unit = secDescSplit?.[1];
	if (pricePer && unit) return {price, pricePer, unit};

	// try obtaining from equivalizedUnitPrice
	// second in priority because equivalizedUnitPrice seems to lie ocassionally???
	const eqUnitPrice = storePrice?.equivalizedUnitPrice;
	pricePer = Number(eqUnitPrice?.amount);
	if (eqUnitPrice?.denomination === 'CENT') pricePer /= 100;
	unit = eqUnitPrice?.unit;
	if (pricePer && unit) return {price, pricePer, unit};

	// finally, calculate it from the weight. some items don't include weight, and for items sold by count this will take a default value of 1 lb.
	const weightSplit = rawProduct?.item?.customerFacingSize?.split(' ');
	const weight = Number(weightSplit?.[0]);
	pricePer = price / weight;
	unit = weightSplit?.[1];
	return {price, pricePer, unit};

}
