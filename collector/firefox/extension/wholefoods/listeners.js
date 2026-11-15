import {standardize} from '../utils.js'
import {sendToHost} from '../native.js'


export function setupWholeFoodsListeners() {
	// wholefoods has two APIs for products, one gives you the products when you first search and the other handles the load more button
	browser.webRequest.onBeforeRequest.addListener(
		readAPIResponse,
		{ urls: ['https://www.wholefoodsmarket.com/grocery/search?*', 'https://www.wholefoodsmarket.com/api/wwos/products?*'] },
		['blocking']
	);
	// get cookie for store ID from request, sadly not really a better way to do this
	browser.webRequest.onBeforeSendHeaders.addListener(
		captureRequestCookie,
		{ urls: ['https://www.wholefoodsmarket.com/grocery/search?*', 'https://www.wholefoodsmarket.com/api/wwos/products?*'] },
		['blocking', 'requestHeaders']
	);
}


// callback for capturing cookies, store in map for later eating
const requestStoreCodes = new Map();
function captureRequestCookie(details) {
	const cookieObj = details.requestHeaders.find(h => h.name.toLowerCase() === 'cookie');
	if (!cookieObj) return; // no cookies found

	const targetKey = 'wfm_store_d8=';
	const startIdx = cookieObj.value.indexOf(targetKey);
	if (startIdx === -1) return; // store cookie is missing

	const valueStart = startIdx + targetKey.length;
	let endIdx = cookieObj.value.indexOf(';', valueStart);
	if (endIdx === -1) endIdx = cookieObj.value.length;

	try {
		const base64Cookie = decodeURIComponent(cookieObj.value.substring(valueStart, endIdx).trim());
		const decodedJson = JSON.parse(atob(base64Cookie));
		requestStoreCodes.set(details.requestId, decodedJson?.id);
	} catch (e) {
		console.error('Failed to parse wfm_store_d8:', e);
	}
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
		processAPIResponse(body, details.requestId);
	};
}


async function processAPIResponse(body, requestId) {

	// eat cookie for request
	const storeCode = requestStoreCodes.get(requestId);
	requestStoreCodes.delete(requestId); // don't forget to free

	// the products endpoint returns just a json array of the products, the search endpoint returns html with the products data in it
	const parsed =
		body[0] === '[' ?
		JSON.parse(body) :
		JSON.parse((new DOMParser()).parseFromString(body, 'text/html').getElementById('__NEXT_DATA__').textContent).props.pageProps.productsInfo;
	
	for (const rawProduct of parsed) {

		if (rawProduct.availability) {

			const cleanProduct = {
				storeBrand: 'wholefoods',
				storeCode: storeCode,
				pid: rawProduct.asin,
				name: rawProduct.veryShortName || rawProduct.shortName || rawProduct.name,
				image: rawProduct.productImages[0],
				coupons: [],
				date: Math.round(Date.now() / 1000),
				price: rawProduct.variableUnitOfMeasure.selectorItemList[0].selectorPrice.priceAmount
			};

			// wholefoods puts unit price in different places based on whether it sells by unit or count (or combo of both)
			if (rawProduct.variableUnitOfMeasure.pricingUom.dimension === 'COUNT') {
				cleanProduct.pricePer = rawProduct.offerDetails.unitPrice?.priceAmount;
				cleanProduct.unit = rawProduct.offerDetails.unitPrice?.baseUnit;
			}
			else {
				cleanProduct.pricePer = rawProduct.offerDetails.price.priceAmount;
				cleanProduct.unit = rawProduct.variableUnitOfMeasure.pricingUom.unit;
			}

			// standardize data
			if (!standardize(cleanProduct)) continue;

			// add to DB
			sendToHost('putObservation', { product: cleanProduct }).catch(e => console.warn('Failed to save observation:', e));
			
		}
	}
}
