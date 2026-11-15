import {pause, randInt} from './utils.js';
import {sendToHost} from './native.js';
import {setupSafewayListeners} from './safeway/listeners.js'
import {setupKingSoopersListeners} from './kingsoopers/listeners.js'
import {setupWholeFoodsListeners} from './wholefoods/listeners.js'
import {safewayScrape} from './safeway/scraper.js'
import {kingSoopersScrape} from './kingsoopers/scraper.js'
import {wholeFoodsScrape} from './wholefoods/scraper.js'


// set up passive network listeners
setupSafewayListeners();
setupKingSoopersListeners();
setupWholeFoodsListeners();


// extension icon button clears and sets interval
let pollInterval;
browser.browserAction.onClicked.addListener(() => {
	if (pollInterval) pollInterval = clearInterval(pollInterval);
	else pollInterval = setInterval(pollForRun, 5000);
});


let scraping = false;
async function pollForRun() {
	if (scraping) return;
	const run = await sendToHost('claimRun');
	if (!run) return;
	scraping = true;
	try {
		await runScrape(run.payload);
	} finally {
		scraping = false;
	}
}


async function runScrape({query, store, minWait, maxWait, scrollPages}) {
	const options = { minWait, maxWait, scrollPages };
	const [brand, zipcode, id] = store;
	switch (brand) {
		case 'safeway':
			await safewayScrape(zipcode, id, query, options);
			break;
		case 'kingsoopers':
			await kingSoopersScrape(zipcode, id, query, options);
			break;
		case 'wholefoods':
			await wholeFoodsScrape(zipcode, id, query, options);
			break;
		default:
			return;
	}
	await pause(randInt(options.minWait, options.maxWait));
}
