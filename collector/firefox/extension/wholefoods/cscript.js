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
	if (msg.message === 'scroll') {
		return scroll(msg.options);
	}
});


async function scroll(options) {
	for (let i = 0; i < options.scrollPages; i++) {
		// find the right button
		const btn = await waitQuerySelector('main [class="m-auto flex w-max p-8"] button');
		// check for honeypot?
		if (!btn) break;
		if (btn.checkVisibility({ contentVisibilityAuto: true, opacityProperty: true, visibilityProperty: true }) === false) break;
		if (btn.innerText !== 'Load More') break;
		// focus the button
		btn.scrollIntoView();
		// click it
		btn.click()
		await pause(randInt(options.minWait, options.maxWait));
	}
}
