import {pause, randInt} from '../utils.js';


export async function wholeFoodsScrape(zipcode, id, query, options) {
	// start blocking images
	browser.webRequest.onBeforeRequest.addListener(
		block,
		{ urls: ['*://m.media-amazon.com/images/*'] },
		['blocking']
	);
	// set location using cookie
	await browser.cookies.set({
		url: 'https://www.wholefoodsmarket.com',
		name: 'wfm_store_d8',
		value: btoa(`{"id":"${id}"}`),
		secure: true
	});
	// create tab
	const page = await browser.tabs.create({ url: `https://www.wholefoodsmarket.com/grocery/search?k=${query}` });
	// pause a bit
	await pause(randInt(options.minWait, options.maxWait));
	// inject content script
	await browser.scripting.executeScript({
		target: { tabId: page.id },
		files: ['wholefoods/cscript.js']
	});
	// tell content script to scroll
	await browser.tabs.sendMessage(page.id, { message: 'scroll', options: options });
	// close tab
	await browser.tabs.remove(page.id);
	// stop blocking images
	browser.webRequest.onBeforeRequest.removeListener(block);
}


function block() {return {cancel: true}}
