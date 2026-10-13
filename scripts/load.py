"""Step 1. Load the raw CSV files into a local DuckDB database.

    python scripts/load.py                 # reads data/raw, writes build/olist.duckdb
    python scripts/load.py path/to/csvs    # read the CSVs from somewhere else
"""
import pathlib
import sys

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
data_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw"
db_path = ROOT / "build" / "olist.duckdb"
db_path.parent.mkdir(exist_ok=True)

TABLES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}
# Row counts of the dataset as published. A mismatch means a different
# version or a damaged download: stop and find out why before going on.
EXPECTED_ROWS = {
    "orders": 99441, "order_items": 112650, "sellers": 3095, "customers": 99441,
    "order_reviews": 99224, "products": 32951, "order_payments": 103886,
    "category_translation": 71,
}

missing = [f for f in TABLES.values() if not (data_dir / f).exists()]
if missing:
    sys.exit(f"Missing files in {data_dir}:\n  " + "\n  ".join(missing)
             + "\nSee data/README.md for where to download them.")

con = duckdb.connect(str(db_path))
ok = True
for table, filename in TABLES.items():
    con.execute(
        f"create or replace table {table} as "
        f"select * from read_csv_auto('{(data_dir / filename).as_posix()}', header=true, sample_size=-1)"
    )
    rows = con.execute(f"select count(*) from {table}").fetchone()[0]
    status = "ok" if rows == EXPECTED_ROWS[table] else f"MISMATCH (expected {EXPECTED_ROWS[table]})"
    ok = ok and rows == EXPECTED_ROWS[table]
    print(f"{table:22s} {rows:>9,d} rows  {status}")
print(f"\nDatabase written to {db_path}")
if not ok:
    sys.exit("Row counts do not match the published dataset. Do not continue until this is explained.")
