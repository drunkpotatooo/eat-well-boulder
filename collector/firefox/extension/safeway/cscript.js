// util functions (cannot be imported because import not possible in content scripts)
function pause(ms) {
	return new Promise(resolve => setTimeout(resolve, ms));
}
function randInt(min, max) {
	return Math.floor(Math.random() * (max - min + 1)) + min;
}
async function waitQuerySelector(query, retries=10) {
	for (let i = 0; i < retries; i++) {
		let out = document.querySelector(query);
		if (out !== null) return out;
		else await pause(1000);
	}
	return null;
}


browser.runtime.onMessage.addListener((msg) => {
	if (msg.message === 'setstore') {
		return setStore(msg.zipcode, msg.id, msg.options);
	}
	else if (msg.message === 'scroll') {
		return scroll(msg.options);
	}
});


async function setStore(zipcode, id, options) {
	// open store picker dialog
	(await waitQuerySelector('#openFulfillmentModalButton')).click();
	await pause(randInt(options.minWait, options.maxWait));
	// don't do anything if it's already set
	if (document.getElementById(`addressOf_${id}`)) return;
	// set zipcode bar
	const zipbar = await waitQuerySelector('input[placeholder="Enter ZIP Code to get started."]');
	zipbar.value = zipcode;
	zipbar.dispatchEvent(new Event('input'));
	await pause(randInt(options.minWait, options.maxWait));
	// click zipcode search
	(await waitQuerySelector('span[aria-label="search Zipcode"]')).click();
	await pause(randInt(options.minWait, options.maxWait));
	// click appropriate button
	(await waitQuerySelector(`a[aria-describedby*="address_${id}"]`)).click();
}


async function scroll(options) {
	for (let i = 0; i < options.scrollPages; i++) {
		// find the right button
		const btn = await waitQuerySelector('button[class="btn btn-secondary bloom-load-button btn-xl mt-3"]');
		// check for honeypot?
		if (!btn) break;
		if (btn.checkVisibility({ contentVisibilityAuto: true, opacityProperty: true, visibilityProperty: true }) === false) break;
		if (btn.innerText !== 'Load more') break;
		// focus the button
		btn.scrollIntoView();
		// click it
		btn.click()
		await pause(randInt(options.minWait, options.maxWait));
	}
}
