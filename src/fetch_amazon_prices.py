import argparse
import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import requests
from dotenv import load_dotenv

API_BASE = "https://api.rainforestapi.com/request"
OUTPUT_FILE = Path("data/amazon_price_history.csv")

CSV_COLUMNS = [
    "snapshot_ts_utc",
    "asin",
    "country",
    "title",
    "brand",
    "rating",
    "ratings_total",
    "list_price",
    "current_price",
    "currency",
    "in_stock",
    "product_url",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Amazon product prices over time.")
    parser.add_argument("--asins", nargs="*", default=[], help="One or more ASIN values")
    parser.add_argument("--asin-file", help="Path to a text file containing ASINs (1 per line)")
    parser.add_argument("--country", default="us", help="Amazon marketplace country (default: us)")
    return parser.parse_args()


def load_asins(inline_asins: List[str], asin_file: str | None) -> List[str]:
    asins = [a.strip().upper() for a in inline_asins if a.strip()]

    if asin_file:
        with open(asin_file, "r", encoding="utf-8") as f:
            file_asins = [line.strip().upper() for line in f if line.strip()]
            asins.extend(file_asins)

    # de-duplicate while preserving order
    seen = set()
    result = []
    for asin in asins:
        if asin not in seen:
            seen.add(asin)
            result.append(asin)

    if not result:
        raise ValueError("No ASINs provided. Use --asins and/or --asin-file.")

    return result


def fetch_product_snapshot(api_key: str, asin: str, country: str) -> dict:
    params = {
        "api_key": api_key,
        "type": "product",
        "amazon_domain": f"amazon.{country}",
        "asin": asin,
    }
    response = requests.get(API_BASE, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    product = data.get("product", {})
    buybox = product.get("buybox_winner", {}) or {}

    current_price = buybox.get("price", {}) or {}
    list_price = buybox.get("rrp", {}) or product.get("list_price", {}) or {}

    return {
        "asin": asin,
        "country": country,
        "title": product.get("title"),
        "brand": product.get("brand"),
        "rating": product.get("rating"),
        "ratings_total": product.get("ratings_total"),
        "list_price": list_price.get("value"),
        "current_price": current_price.get("value"),
        "currency": current_price.get("currency") or list_price.get("currency"),
        "in_stock": buybox.get("in_stock"),
        "product_url": f"https://www.amazon.{country}/dp/{asin}",
    }


def append_rows(rows: Iterable[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output_path.exists()

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    load_dotenv()
    args = parse_args()

    api_key = os.getenv("RAINFOREST_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing RAINFOREST_API_KEY in environment/.env")

    asins = load_asins(args.asins, args.asin_file)
    snapshot_ts = datetime.now(timezone.utc).isoformat()

    rows = []
    for asin in asins:
        try:
            product = fetch_product_snapshot(api_key, asin, args.country)
            product["snapshot_ts_utc"] = snapshot_ts
            rows.append(product)
            print(f"Fetched {asin}")
        except requests.HTTPError as err:
            print(f"HTTP error for {asin}: {err}")
        except requests.RequestException as err:
            print(f"Request error for {asin}: {err}")

    if rows:
        append_rows(rows, OUTPUT_FILE)
        print(f"Saved {len(rows)} rows to {OUTPUT_FILE}")
    else:
        print("No rows saved (all requests failed).")


if __name__ == "__main__":
    main()
