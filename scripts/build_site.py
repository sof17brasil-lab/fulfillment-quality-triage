"""Step 5. Copy what the dashboard needs from out/ into site/data/.

    python scripts/build_site.py

Nothing in site/ is typed by hand -- every number and chart reads one of
these JSON files. Run after scripts/run.py and scripts/check.py pass.

It also builds site/data/public_facts.json, the handful of Instacart figures
quoted on the page. Those come from sources/SOURCES.md rather than from the
analysis, so they get their own gate: a fact is published only if its box in
SOURCES.md is ticked AND the number being shown still appears verbatim in the
quoted words. Either test failing stops the build.
"""
import csv
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
SITE_DATA = ROOT / "site" / "data"
SITE_SQL = ROOT / "site" / "sql"
SITE_DATA.mkdir(parents=True, exist_ok=True)
SITE_SQL.mkdir(parents=True, exist_ok=True)

FILES = [
    "02_baseline_scorecard.json",
    "03_customer_impact.json",
    "05_root_cause.json",
    "06_promise_accuracy.json",
    "07_seller_scorecard.json",
    "08_repeat_purchase.json",
    "09_validation_checks.json",
    "10_initiative_sizing.json",
    "11_launch_scorecard.json",
    "12_early_warning.json",
    "13_dashboard_cube.json",
    "14_customer_reviews.json",
    "15_cancellation_trend.json",
    "16_order_timeline.json",
    "17_escalation.json",
]

for name in FILES:
    shutil.copy(OUT / name, SITE_DATA / name)

# the ledger, as JSON, for the Method and SQL page
with open(ROOT / "out" / "numbers_ledger.csv", newline="") as f:
    ledger = list(csv.DictReader(f))
(SITE_DATA / "numbers_ledger.json").write_text(json.dumps(ledger, indent=1))

# the SQL files themselves, read-only copies, for the Method and SQL page
sql_files = sorted((ROOT / "sql").glob("*.sql"))
for path in sql_files:
    shutil.copy(path, SITE_SQL / path.name)
(SITE_DATA / "sql_manifest.json").write_text(json.dumps([p.name for p in sql_files], indent=1))

print(f"Copied {len(FILES)} files + numbers_ledger.json to {SITE_DATA}")
print(f"Copied {len(sql_files)} SQL files to {SITE_SQL}")


# ---------------------------------------------------------------- sources
def parse_sources(path):
    """Pull every row out of the SOURCES.md tables, keyed by source ID.

    The tables do not all carry the same columns -- some have a Speaker
    column, and the quoted-words column is variously headed "Exact words",
    "What I read" or "Evidence" -- so columns are located by name from each
    table's own header rather than by a fixed position.
    """
    QUOTE_COLS = ("exact words", "what i read", "evidence")
    rows, cols = {}, None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            cols = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):      # the |---|---| divider
            continue
        if cells and cells[0] == "ID":             # a header row
            cols = {name.lower(): i for i, name in enumerate(cells)}
            continue
        if cols and re.fullmatch(r"S\d+[a-z]?", cells[0]):
            get = lambda key: cells[cols[key]] if key in cols and cols[key] < len(cells) else ""
            quote = next((get(c) for c in QUOTE_COLS if c in cols), "")
            rows[cells[0]] = {
                "fact": get("fact"),
                "words": quote,
                "status": get("status"),
                "ticked": "[x]" in get("you checked").lower(),
            }
    return rows


sources = parse_sources(ROOT / "sources" / "SOURCES.md")
wanted = json.loads((ROOT / "reference" / "public_facts.json").read_text())

published, problems = [], []
for item in wanted:
    sid = item["id"]
    src = sources.get(sid)
    if src is None:
        problems.append(f"{sid}: not found in SOURCES.md")
        continue
    if not src["ticked"]:
        problems.append(f"{sid}: not ticked in SOURCES.md, so it cannot go on the site")
        continue
    missing = [s for s in item["must_contain"] if s not in src["words"]]
    if missing:
        problems.append(f"{sid}: {missing} no longer appear in the quoted words")
        continue
    published.append({
        "id": sid,
        "display": item["display"],
        "label": item["label"],
        "fact": src["fact"],
        "words": src["words"],
        "status": src["status"],
    })

if problems:
    print("\nFACT CHECK FAILED:", file=sys.stderr)
    for p in problems:
        print("  -", p, file=sys.stderr)
    raise SystemExit(1)

(SITE_DATA / "public_facts.json").write_text(json.dumps(published, indent=1))
skipped = sum(1 for s in sources.values() if not s["ticked"])
print(f"Fact check: {len(published)} of {len(wanted)} public facts ticked and verbatim "
      f"({skipped} unticked sources held back across SOURCES.md)")
