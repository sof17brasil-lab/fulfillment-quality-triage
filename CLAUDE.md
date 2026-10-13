# Fulfillment Quality Triage

Portfolio case study by Sofia Mota for a fulfillment-quality analyst role (Instacart, Data Analyst, Platform Excellence Ops Analytics). It runs on public marketplace data from Olist. Read `docs/project_brief.md` before doing anything.

## Commands

```
pip install -r requirements.txt
python scripts/load.py            # CSVs in data/raw -> build/olist.duckdb, checks row counts
python scripts/run.py             # runs sql/*.sql in order -> out/*.json
python scripts/verify_pandas.py   # independent recomputation -> out/pandas_recheck.json
python scripts/check.py           # must end with ALL CHECKS PASSED
```

## Rules that are not negotiable

1. **No hand-typed numbers.** Every number on the website, in the README, and in the deck is read from `out/*.json` or `out/numbers_ledger.csv`. If a number is not in the ledger, add it to `scripts/check.py` first.
2. **Run the full check after any SQL change.** If a number that is frozen in `reference/numbers_ledger.csv` changes, stop and tell Sofia which number moved and why. Only run `python scripts/check.py --freeze` after she says yes.
3. **Every headline number gets an independent re-check.** New analysis means a new numbered file in `sql/` plus a matching recomputation in `scripts/verify_pandas.py` that shares no logic with the SQL.
4. **Outside facts come only from `sources/SOURCES.md`.** To use a new fact, add it there with the link, the exact words, and the date, and mark it unticked. It goes on the website only after Sofia has opened the link and ticked it.
5. **Never state or estimate Instacart's internal numbers**, costs, defect rates, or tools. None are public. Savings are shown through a calculator that takes the reader's own inputs.
6. **Word claims to match the evidence.** Say "in this marketplace data". Show counts beside small-sample results (the repeat-purchase test rests on 35 and 41 repeat customers). Use "is associated with", not "causes", unless the design supports it.
7. **Instacart-inspired, never Instacart's.** An Instacart-like palette and a similar free font are fine. Instacart's logo, exact brand colour codes, brand font, artwork, or wording that implies affiliation are not. The footer says "Independent portfolio project. Not affiliated with Instacart."
8. **Raw data is never committed.** `data/raw/` and `build/` are gitignored.

## How to work with Sofia

- Do the work yourself, including all SQL. She does not want lessons, quizzes, or walkthroughs of how a query works.
- Report in short plain-English summaries: what you found and what it means for the business. No SQL in summaries unless she asks.
- Work on your own between the four checkpoints in the build plan. Stop at each checkpoint and wait.
- Ask before anything that leaves her computer: creating a GitHub repo, pushing, deploying, publishing.
- When she pushes for a bigger claim than the data supports, say so and offer the strongest wording that is still true.

## The website

- A dark, scroll-driven data story with Instacart-inspired colours, as described in `design/inspiration/notes.md` and `design/design_brief.md`. Where those two files and `CLAUDE_CODE_PROMPT.md` differ on design, the two design files win.
- Very little text. The main page never explains how numbers were calculated. Definitions, checks, SQL, limits, sources, and the AI note live on a separate Method and SQL page behind one quiet link.
- Small-sample results still show their counts on the chart, and the footer still names the data, its licence, its main limit, and that the project is not affiliated with Instacart. Compact, never omitted.
- Smooth: animate only transform and opacity, honour reduced-motion settings, Lighthouse performance 90 or more on desktop.

## SQL conventions

- DuckDB dialect, kept portable to Snowflake (date_trunc, datediff, count_if, qualify).
- One file per question. Each file opens with a comment stating the question in plain words.
- Base tables are `fct_orders` (one row per order) and `fct_order_seller` (one row per order and seller). Never sum the seller table to get platform totals.
- Rates state their denominator in the column name or a comment.
