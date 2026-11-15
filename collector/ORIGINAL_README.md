# Store Bought

The purpose of this project is to clarify shopping. I want to be able to find the true price of groceries ("member price" and other discounts/coupons applied), search/sort through those prices, and compare them across different stores. Doing so is a tedious process by hand. This project currently consists of:
- A Firefox extension that
	- Passively collects price data whenever you use a grocery store's website (currently Safeway and King Soopers only). Data is sent through Native Messaging to a Python host that adds to an sqlite3 table.
	- Can automatically browse through grocery sites for a search term.
- A set of Python tools for visualizing that data.

## Installation

Setup
1. Run `create_db.py` to set up the database if it doesn't exist.
2. Run `firefox/install.py`. Currently only Windows is supported.

Extension
1. You will need to download Firefox ESR or Developer Edition to install an unsigned extension.
2. Once you have that installed, go to `about:config` and set `xpinstall.signatures.required` to `false`.
3. Compress the items in `firefox/extension/` (not the folder, the items directly) to a `.zip` file.
4. Go to `about:addons` and click the gear icon next to "Manage Your Extensions". Click "Install Add-on From File..." and select the `.zip` file. Agree to the permissions.

## Database Structure

Data is stored in five SQLite tables (see `create_db.py`).

- `stores`: gives an ID to stores by brand, brand-internal code, and a name. I'm currently just adding name manually.

- `products`: one row per product per store holding current state in terms of details (name, image, etc.), price (price, price per, unit, coupons), and time of last observation. Add an observation by upserting. There are triggers on the table that add to `price_history` and `details_history` whenever detail/price changes.

- `price_history` and `details_history`: append-only change logs maintained by schema triggers. A product's initial values are added on first sight. Whenever an upsert changes a value, old row is logged at its last-seen time alongside the new row at the new time. It's recorded this way because I want history, and I expect details/prices to change a lot but at their own paces. This structure saves a lot of space compared to re-recording the entire row. Using triggers because I don't want to have to worry about checking/updating history in every future component that upserts.

- `runs`: for instructing the extension to autobrowse.
