"""Step 2. Run every SQL file in sql/ in order and save each result as JSON in out/.

    python scripts/run.py          # run everything
    python scripts/run.py 04 05    # run only files starting with 04 or 05

Nothing on the website is typed by hand. The site reads these JSON files.
"""
import datetime
import decimal
import json
import pathlib
import sys

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
out_dir = ROOT / "out"
out_dir.mkdir(exist_ok=True)
con = duckdb.connect(str(ROOT / "build" / "olist.duckdb"))


def clean(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value


only = sys.argv[1:]
for path in sorted((ROOT / "sql").glob("*.sql")):
    if only and not any(path.name.startswith(prefix) for prefix in only):
        continue
    # DuckDB's own parser splits the file into statements, so comments and
    # semicolons inside comments are handled correctly.
    results = []
    for statement in con.extract_statements(path.read_text()):
        cursor = con.execute(statement)
        if statement.type == duckdb.StatementType.SELECT and cursor.description:
            columns = [d[0] for d in cursor.description]
            results.append([dict(zip(columns, map(clean, row))) for row in cursor.fetchall()])
    (out_dir / f"{path.stem}.json").write_text(json.dumps(results, indent=1))
    print(f"{path.name:32s} {len(results)} result set(s), rows: {[len(r) for r in results]}")
