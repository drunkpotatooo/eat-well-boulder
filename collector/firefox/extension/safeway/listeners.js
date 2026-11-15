import {standardize} from '../utils.js'
import {sendToHost} from '../native.js'


// safeway's API responses can be directly accessed for data, so we'll use that
export function setupSafewayListeners() {
	browser.webRequest.onBeforeRequest.addListener(
		readAPIResponse,
		{ urls: ['https://www.safeway.com/abs/pub/xapi/pgmsearch/v1/search/products?*'] },
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
	for (const rawProduct of parsed.primaryProducts.response.docs) {

		// get data from docs
		const cleanProduct = {
			storeBrand: 'safeway',
			storeCode: rawProduct.storeId,
			pid: rawProduct.pid,
			name: rawProduct.name,
			image: `${rawProduct.imageUrl}?$grid-product-card-mobile$&defaultImage=Not_Available`,
			coupons: getCoupons(parsed.offersData, rawProduct.upc),
			date: Math.round(Date.now() / 1000),
			price: rawProduct.price,
			pricePer: rawProduct.pricePer,
			unit: rawProduct.unitQuantity
		};

		// standardize data
		if (!standardize(cleanProduct)) continue;

		// add to DB
		sendToHost('putObservation', { product: cleanProduct }).catch(e => console.warn('Failed to save observation:', e));

	}
}


function getCoupons(offersData, upc) {
	// offers without an ecomDescription can't be interpreted, skip them
	return Object.values(offersData?.upcs?.[upc]?.offers || {})
		.map(offer => offer?.ecomDescription)
		.filter(coupon => typeof coupon === 'string');
}
