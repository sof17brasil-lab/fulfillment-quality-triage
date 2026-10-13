# Reference numbers

This folder is the proof that the project is built on real numbers.

## numbers_ledger.csv

Open it in Excel or Google Sheets. One row per number used in the write-up.

| Column | Meaning |
|---|---|
| id | N01, N02 and so on. The brief and the website cite these. |
| claim | What the number says, in plain words. |
| value | The number, from the SQL. |
| unit | Orders, %, days, and so on. |
| sql_source | Which file in `sql/` produced it. "05b" means the second query in file 05. |
| pandas_value | The same number recomputed from the raw CSV files by separate pandas code. |
| agreement | MATCH: both methods agree. SQL only: no second computation exists for this one. |

When this file was frozen (11 Oct 2026): 61 numbers, 48 computed two ways and all 48 matched, 13 SQL only.

## expected_results/

The full output of every SQL file from the run that produced the ledger. If your run on your own Kaggle download produces the same files, your data and your code are the same as the reference.

## How to prove it yourself

```
python scripts/load.py
python scripts/run.py
python scripts/verify_pandas.py
python scripts/check.py
```

The last command must print these lines (it also lists the flagged weeks):

```
1. validation checks: 16 of 16 PASS
2. SQL vs independent pandas: 48 of 48 MATCH (13 numbers are SQL only)
3. this run vs frozen reference: 61 of 61 identical
ALL CHECKS PASSED
```

## What "checked" does and does not mean

It means the arithmetic is right: two different programs, written differently, got the same answer from the same raw files.

It does not mean the definitions are the only reasonable ones. "Late" here means delivered after the end of the promised day. "Flagged seller" uses a 50-order minimum and a 95% bound. Different choices give different numbers. The choices are written at the top of each SQL file so a reader can disagree with them knowingly.

## Do not edit by hand

`numbers_ledger.csv` is written by `python scripts/check.py --freeze`. Change the SQL, review the difference, then freeze.
