import {pause, randInt} from '../utils.js';


export async function safewayScrape(zipcode, id, query, options) {
	// start blocking images
	browser.webRequest.onBeforeRequest.addListener(
		block,
		{ urls: ['*://images.albertsons-media.com/*'] },
		['blocking']
	);
	// create safeway tab
	const homepage = await browser.tabs.create({ url: `https://www.safeway.com/` });
	// pause a bit
	await pause(randInt(options.minWait, options.maxWait));
	// inject content script
	await browser.scripting.executeScript({
		target: { tabId: homepage.id },
		files: ['safeway/cscript.js']
	});
	// tell content script to set store
	await browser.tabs.sendMessage(homepage.id, { message: 'setstore', zipcode: zipcode, id: id, options: options });
	// pause a bit
	await pause(randInt(options.minWait, options.maxWait));
	// update tab to search query
	await browser.tabs.update(homepage.id, { url: `https://www.safeway.com/shop/search-results.html?q=${query}&tab=products&sort=salesRank` });
	// pause a bit
	await pause(randInt(options.minWait, options.maxWait));
	// inject content script again
	await browser.scripting.executeScript({
		target: { tabId: homepage.id },
		files: ['safeway/cscript.js']
	});
	// tell content script to scroll
	await browser.tabs.sendMessage(homepage.id, { message: 'scroll', options: options });
	// close tab
	await browser.tabs.remove(homepage.id);
	// stop blocking images
	browser.webRequest.onBeforeRequest.removeListener(block);
}


function block() {return {cancel: true}}
