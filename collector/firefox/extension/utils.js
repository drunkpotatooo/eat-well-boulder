// final check to ensure that data is clean and proper. returns false if data should be rejected and true if everything fine.
export function standardize(product) {
	// check all values to ensure that they exist and are typed correctly
	if (!(
		typeof product?.storeBrand === 'string' && product.storeBrand.length > 0 &&
		typeof product.storeCode === 'string' && product.storeCode.length > 0 &&
		typeof product.pid === 'string' && product.pid.length > 0 &&
		typeof product.name === 'string' && product.name.length > 0 &&
		typeof product.image === 'string' && product.image.length > 0 &&
		Array.isArray(product.coupons) &&
		typeof product.date === 'number' && product.date >= 0 &&
		typeof product.price === 'number' && product.price >= 0 &&
		typeof product.pricePer === 'number' && product.pricePer >= 0 &&
		typeof product.unit === 'string' && product.unit.length > 0
	)) {
		console.log(`Rejected ${JSON.stringify(product)} due to improper data`);
		return false;
	}
	// sort coupons for consistent order
	product.coupons.sort();
	// make unit lowercase before removing special chars, nums, whitespace, 'per ' from beginning
	const unit = product.unit.toLowerCase().replace(/[^a-z]/g, '').replace(/^per/, '');
	// strip s (couldn't think of any base unit ending with s) and convert unit
	switch (unit.replace(/s$/, '')) {
		case 'oz':
		case 'ounce':
		case 'reconstitutedounce':
			product.pricePer *= 16;
			product.unit = 'lb';
			break;
		case 'gram':
		case 'g':
			product.pricePer *= 453.592;
			product.unit = 'lb';
			break;
		case 'kilogram':
		case 'kg':
			product.pricePer *= 0.453592;
			product.unit = 'lb';
			break;
		case 'lb':
		case 'pound':
			product.unit = 'lb';
			break;
		case 'ea':
		case 'each':
		case 'count':
		case 'cnt':
		case 'ct':
		case 'per':
		case 'unit':
		case 'piece':
		case 'pc':
		case 'pack':
		case 'pk':
		case 'roll':
		case 'plate':
		case 'stem':
		case 'bunch':
		case 'x':
			product.unit = 'ea';
			break;
		case 'dozen':
			product.pricePer *= 1 / 12;
			product.unit = 'ea';
			break;
		case 'milliliter':
		case 'ml':
			product.pricePer *= 3785.41;
			product.unit = 'gal';
			break;
		case 'fluidounce':
		case 'flounce':
		case 'fluidoz':
		case 'floz':
		case 'fl':
			product.pricePer *= 128;
			product.unit = 'gal';
			break;
		case 'pint':
		case 'pt':
			product.pricePer *= 8;
			product.unit = 'gal';
			break;
		case 'drypint':
		case 'drypt':
		case 'drpt':
			product.pricePer *= 6.87494;
			product.unit = 'gal';
			break;
		case 'quart':
		case 'qt':
			product.pricePer *= 4;
			product.unit = 'gal';
			break;
		case 'liter':
		case 'litre':
		case 'litr':
		case 'ltr':
		case 'l':
			product.pricePer *= 3.78541;
			product.unit = 'gal';
			break;
		case 'gal':
		case 'gallon':
		case 'gl':
			product.unit = 'gal';
			break;
		case 'sqft':
		case 'squarefeet':
		case 'sf':
			product.unit = 'sqft';
			break;
		case 'sqyd':
		case 'squareyard':
		case 'sy':
			product.unit = 'sqyd';
			break;
		default:
			product.unit = unit;
			break;
	}
	// round to 4 places
	product.pricePer = roundPlace(product.pricePer, 10000);
	product.price = roundPlace(product.price, 10000);
	// everything's good!
	return true;
}


export function roundPlace(num, place) {
	return Math.round(num * place) / place;
}


export function randInt(min, max) {
	return Math.floor(Math.random() * (max - min + 1)) + min;
}


export function pause(ms) {
	return new Promise(resolve => setTimeout(resolve, ms));
}
