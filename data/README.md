# Data

The raw data is not in this folder. Download it yourself from the official source, so anyone reviewing the project can do the same and get the same numbers.

## Download

1. Go to https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (a free Kaggle account is needed).
2. Read the **License** line on that page and write it in `sources/SOURCES.md` under S10c.
3. Click Download, unzip, and move these eight files into `data/raw/`:

| File | Rows expected |
|---|---|
| olist_orders_dataset.csv | 99,441 |
| olist_order_items_dataset.csv | 112,650 |
| olist_sellers_dataset.csv | 3,095 |
| olist_customers_dataset.csv | 99,441 |
| olist_order_reviews_dataset.csv | 99,224 |
| olist_products_dataset.csv | 32,951 |
| olist_order_payments_dataset.csv | 103,886 |
| product_category_name_translation.csv | 71 |

The download also contains `olist_geolocation_dataset.csv`. This project does not use it.

`python scripts/load.py` checks every row count and stops if one is off.

## What the data is

Real orders from Olist, a Brazilian marketplace that connects small sellers to large shopping sites. Orders run from late 2016 to 2018. Customers and sellers are anonymised. Each order has a status, a purchase time, the time the seller handed it to the carrier, the delivery time, the promised delivery date, the seller, the customer's state, and the customer's review.

## Fingerprints of the copies the reference numbers were built on

The numbers in `reference/numbers_ledger.csv` were computed on copies of these files that matched the published row counts above. If your Kaggle files have the same SHA-256 fingerprints, they are byte-for-byte identical. If the fingerprints differ but the row counts match and `scripts/check.py` passes, you are still fine (Kaggle sometimes re-saves files with different line endings).

```
983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2  olist_customers_dataset.csv
0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279  olist_order_items_dataset.csv
4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0  olist_order_payments_dataset.csv
012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7  olist_order_reviews_dataset.csv
8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf  olist_orders_dataset.csv
3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc  olist_products_dataset.csv
1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e  olist_sellers_dataset.csv
a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278  product_category_name_translation.csv
```

Honest note on where those copies came from: the cloud workspace that built the reference numbers could not reach Kaggle, so the files were taken from public GitHub copies of the dataset and accepted only because every row count matched the published dataset. Your own download from Kaggle is the copy of record.

## Rules

- Never edit the raw files.
- Never commit them to GitHub (`data/raw/` is in `.gitignore`). Link to Kaggle instead.
- Credit the source on the website: "Data: Brazilian E-Commerce Public Dataset by Olist, via Kaggle."
