let port = null;
let nextId = 0;
const pending = new Map();


function connect() {
	port = browser.runtime.connectNative('store_bought_host');
	port.onMessage.addListener(msg => {
		const p = pending.get(msg.id);
		if (!p) return;
		pending.delete(msg.id);
		if (msg.error) p.reject(new Error(msg.error));
		else p.resolve(msg.result);
	});
	port.onDisconnect.addListener(() => {
		const err = port.error ? new Error(port.error.message) : new Error('Native host disconnected');
		for (const p of pending.values()) p.reject(err);
		pending.clear();
		port = null;
	});
}


export function sendToHost(action, payload = {}) {
	if (!port) connect();
	const id = nextId++;
	return new Promise((resolve, reject) => {
		pending.set(id, { resolve, reject });
		port.postMessage({ id, action, payload });
	});
}
