import {pause, randInt} from '../utils.js';


export async function kingSoopersScrape(zipcode, id, query, options) {
	// start blocking images
	browser.webRequest.onBeforeRequest.addListener(
		block,
		{ urls: ['*://www.kroger.com/product/images/*'] },
		['blocking']
	);
	// set location using cookie
	await browser.cookies.set({
		url: 'https://www.kingsoopers.com',
		name: 'x-active-modality',
		value: `{"type":"IN_STORE","locationId":"${id}","source":"FALLBACK_ACTIVE_MODALITY_COOKIE","createdDate":${Date.now() - randInt(1 * 60 * 1000, 60 * 60 * 1000)}}`,
		secure: true
	});
	// create king soopers query tab
	const homepage = await browser.tabs.create({ url: `https://www.kingsoopers.com/search?query=${query}&searchType=default_search` });
	// pause a bit
	await pause(randInt(options.minWait, options.maxWait));
	// inject content script
	await browser.scripting.executeScript({
		target: { tabId: homepage.id },
		files: ['kingsoopers/cscript.js']
	});
	// tell content script to scroll
	await browser.tabs.sendMessage(homepage.id, { message: 'scroll', options: options });
	// close tab
	await browser.tabs.remove(homepage.id);
	// stop blocking images
	browser.webRequest.onBeforeRequest.removeListener(block);
}


function block() {return {cancel: true}}
