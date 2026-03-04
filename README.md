# Amazon Product Price Tracker (Power BI Starter)

This project helps you collect **Amazon product pricing over time** for a Power BI portfolio project.

> ⚠️ Note: Direct scraping of Amazon pages can violate terms and frequently breaks due to anti-bot protections.
> This starter uses the **Rainforest API** (Amazon SERP/Product API) as a safer and more reliable path.

## What this gives you

- Pulls current product data (title, rating, list price, current price)
- Appends each run as a time snapshot
- Saves to `data/amazon_price_history.csv`
- Ready to load in Power BI

## 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in project root:

```bash
RAINFOREST_API_KEY=your_api_key_here
```

## 2) Track products

Run with Amazon ASINs:

```bash
python src/fetch_amazon_prices.py --asins B0CHX1W1XY B0C2XQY8KQ --country us
```

Or pass a file:

```bash
python src/fetch_amazon_prices.py --asin-file asins.txt
```

`asins.txt` example:

```text
B0CHX1W1XY
B0C2XQY8KQ
```

## 3) Schedule it (optional)

### Cron (Linux/macOS)

```bash
0 9 * * * cd /path/to/project && /path/to/project/.venv/bin/python src/fetch_amazon_prices.py --asin-file asins.txt
```

This tracks daily snapshots so you can build trend charts in Power BI.

## Power BI ideas

- Price trend per product (line chart)
- Discount % over time
- Current price vs list price
- Avg price by brand/category

## Dataset schema

Output CSV columns:

- `snapshot_ts_utc`
- `asin`
- `country`
- `title`
- `brand`
- `rating`
- `ratings_total`
- `list_price`
- `current_price`
- `currency`
- `in_stock`
- `product_url`

