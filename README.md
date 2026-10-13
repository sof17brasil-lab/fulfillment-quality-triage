# Fulfillment Quality Triage

When a marketplace's on-time rate drops, find out fast **whose problem it is**, how big it is, and what fixing it is worth.

A portfolio case study by **Sofia Mota**, built on the public [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — 98,962 orders across 86 weeks, 2017–2018.

**Independent portfolio project. Not affiliated with Instacart.**

---

## The findings

1. **Most late deliveries weren't the seller's fault.** 72.3% of late orders had already left the seller on time. Only 12.4% would have been saved by a faster handoff alone.
2. **The monitor earns its keep.** A control chart on the weekly late rate flags 8 unusual weeks out of 86 — and those 8 weeks hold 41.5% of every late order in the window.
3. **Two episodes, two different causes.** Black Friday 2017 stretched both legs of the journey. February–March 2018 barely touched the seller leg (+0.3 days) and added 4.1 days to the carrier leg, concentrated in Rio de Janeiro — 402 late orders above Rio's own normal rate.
4. **A late handoff costs reviews even when the parcel still arrives on time** — 13.5% one-to-two-star against 8.9%, on 6,718 on-time deliveries. Probably because the order still arrives later: 15.1 days to the door against 9.3.
5. **New sellers really do have a rough first month.** 0.9% cancellations in their first 30 days against a month-matched 0.39% after day 90 — the gap survives controlling for the platform-wide downward trend.
6. **The seller programme is the smallest lever of the three.** Episode response avoids 782 late orders, the seller handoff programme 231, lane-level promise 142 — counting only what could realistically have been acted on in time.

## How to reproduce every number

```bash
pip install -r requirements.txt
python scripts/load.py            # CSVs -> build/olist.duckdb, checks row counts
python scripts/run.py             # runs sql/*.sql in order -> out/*.json
python scripts/verify_pandas.py   # independent recomputation -> out/pandas_recheck.json
python scripts/check.py           # must end with ALL CHECKS PASSED
```

The raw CSVs are **not** in this repository — see [`data/README.md`](data/README.md) for where to download them.

### Why you can trust the numbers

Every figure on the site has an id in [`reference/numbers_ledger.csv`](reference/numbers_ledger.csv), a claim in plain words, and the query it came from. `scripts/check.py` enforces three things on every build and exits non-zero if any fail:

| Check | Current |
|---|---|
| Validation checks pass | **16 / 16** |
| SQL agrees with an independent pandas recomputation | **122 / 122** |
| Nothing moved since the frozen reference | **135 / 135** |

`scripts/verify_pandas.py` recomputes the headline figures straight from the raw CSVs and **shares no logic with the SQL**, so a bug would have to exist twice, written two different ways, to survive. Nothing numeric is typed into the HTML by hand — `scripts/build_site.py` copies `out/` into `site/data/`, and the page reads only that.

## What it cannot claim

- This is **multi-day parcel shipping in Brazil, 2017–2018**, not same-day grocery. The methods transfer; the timescales and specific numbers do not.
- There are no reschedule events and no shopper-supply data, so two defect types a real fulfilment team tracks cannot be shown.
- Fault attribution uses timestamps, not pickup scans. A seller who hands off late because a carrier missed a pickup is blamed unfairly.
- The repeat-purchase result is observational and small — 35 and 41 repeat customers. It is shown with its counts and read as a direction, not a measured effect size.
- **No Instacart internal numbers, costs, defect rates or tools appear anywhere.** None are public. Savings are shown only through a calculator that takes the reader's own inputs.

## Layout

```
sql/        one file per question, DuckDB dialect kept portable to Snowflake
scripts/    load, run, independent re-check, ledger check, site build
reference/  the frozen numbers ledger
sources/    every outside fact, with the exact words and whether it was verified
docs/       project brief, summary, dashboard plan, talking points
site/       the static site (no server, deploys as-is to GitHub Pages)
```

## Credits

Data: Olist, via Kaggle, licensed **CC BY-NC-SA 4.0**.
Photography: six CC0 images from Wikimedia Commons, credited individually in [`design/image_credits.md`](design/image_credits.md); the halved produce is the author's own.
Type: Inter Tight and Fjalla One, both SIL Open Font License.

Built with AI assistance. Sofia Mota built this project with Claude, an AI assistant. Every headline number is computed twice, in SQL and again in separate Python code, and every quote is checked against its original source.
