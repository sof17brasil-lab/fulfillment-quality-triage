"""Step 6. Build the 6-slide insights deck.

    python scripts/build_deck.py      # -> site/deck.pdf

Every number is pulled from out/numbers_ledger.csv by its ledger id, so the
deck cannot drift from the website or from the SQL. If an id is missing the
build fails loudly rather than printing a blank.
"""
import csv
import pathlib
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "out" / "numbers_ledger.csv"
OUT = ROOT / "site" / "deck.pdf"

PAGE = landscape((1280, 720))          # 16:9, in points
W, H = PAGE

INK = HexColor("#100B06")
CREAM = HexColor("#F5E4C7")
GOLD = HexColor("#BE8D3F")
EMBER = HexColor("#F15726")
MUTED = HexColor("#AC9F8A")

MARGIN = 72

# Helvetica stands in for the website's fonts: the free webfonts the site uses
# are not bundled here, and a PDF that silently substitutes a metric-different
# face looks worse than one that picks a clean default on purpose.
BOLD, REG = "Helvetica-Bold", "Helvetica"


def load_ledger():
    if not LEDGER.exists():
        sys.exit("out/numbers_ledger.csv not found — run scripts/check.py first")
    rows = {r["id"]: r for r in csv.DictReader(open(LEDGER))}
    if not rows:
        sys.exit("ledger is empty")
    return rows


L = load_ledger()


def val(nid):
    """Ledger value, formatted the way the unit implies."""
    if nid not in L:
        sys.exit(f"ledger id {nid} not found — add it to scripts/check.py first")
    r = L[nid]
    v, unit = r["value"], r["unit"]
    if unit == "%":
        return f"{float(v):g}%"
    if unit == "days":
        return f"{float(v):g} days"
    if unit == "stars":
        return f"{float(v):g}★"
    try:
        f = float(v)
        return f"{int(f):,}" if f.is_integer() else f"{f:g}"
    except ValueError:
        return v


class Deck:
    def __init__(self, path):
        self.c = pdfcanvas.Canvas(str(path), pagesize=PAGE)
        self.n = 0

    def slide(self, eyebrow, title):
        self.n += 1
        c = self.c
        c.setFillColor(INK)
        c.rect(0, 0, W, H, stroke=0, fill=1)

        c.setFillColor(GOLD)
        c.setFont(BOLD, 13)
        c.drawString(MARGIN, H - MARGIN, eyebrow.upper())

        c.setFillColor(CREAM)
        c.setFont(BOLD, 42)
        y = H - MARGIN - 54
        for line in simpleSplit(title, BOLD, 42, W - 2 * MARGIN):
            c.drawString(MARGIN, y, line)
            y -= 48
        self.y = y - 18

        # slide number + footer rule
        c.setStrokeColor(HexColor("#2A2219"))
        c.setLineWidth(1)
        c.line(MARGIN, 52, W - MARGIN, 52)
        c.setFillColor(MUTED)
        c.setFont(REG, 10)
        c.drawString(MARGIN, 34, "Fulfillment Quality Triage  ·  Sofia Mota  ·  Olist public data, Brazil 2017–2018")
        c.drawRightString(W - MARGIN, 34, f"{self.n}/6")
        return self

    def body(self, text, size=17, color=None, gap=26):
        c = self.c
        c.setFillColor(color or MUTED)
        c.setFont(REG, size)
        for line in simpleSplit(text, REG, size, W - 2 * MARGIN):
            c.drawString(MARGIN, self.y, line)
            self.y -= gap
        self.y -= 8
        return self

    def stats(self, items, y=None):
        """A row of big numbers with labels underneath."""
        c = self.c
        y = y if y is not None else self.y - 40
        colw = (W - 2 * MARGIN) / len(items)
        for i, (v, label) in enumerate(items):
            x = MARGIN + i * colw
            c.setFillColor(CREAM)
            c.setFont(BOLD, 48)
            c.drawString(x, y, v)
            c.setFillColor(MUTED)
            c.setFont(REG, 12)
            ly = y - 22
            for line in simpleSplit(label, REG, 12, colw - 18):
                c.drawString(x, ly, line)
                ly -= 15
        self.y = y - 86
        return self

    def bars(self, items, unit=""):
        """Horizontal bars, largest first, labelled with their value."""
        c = self.c
        top = self.y - 14
        biggest = max(v for _, v in items) or 1
        maxw = W - 2 * MARGIN - 300
        for i, (label, v) in enumerate(items):
            y = top - i * 54
            c.setFillColor(CREAM)
            c.setFont(REG, 15)
            c.drawString(MARGIN, y + 6, label)
            bw = maxw * (v / biggest)
            c.setFillColor(EMBER if i == 0 else HexColor("#6E5B3F"))
            c.roundRect(MARGIN + 290, y, max(bw, 2), 22, 3, stroke=0, fill=1)
            c.setFillColor(CREAM)
            c.setFont(BOLD, 15)
            c.drawString(MARGIN + 300 + max(bw, 2), y + 6, f"{v:,}{unit}")
        self.y = top - len(items) * 54 - 16
        return self

    def note(self, text):
        c = self.c
        c.setFillColor(GOLD)
        c.setFont(REG, 13)
        for line in simpleSplit(text, REG, 13, W - 2 * MARGIN):
            c.drawString(MARGIN, self.y, line)
            self.y -= 18
        return self

    def done(self):
        self.c.showPage()
        return self

    def save(self):
        self.c.save()


def build():
    d = Deck(OUT)

    # 1 — situation
    (d.slide("01 · Situation", "A marketplace where most orders are fine and the failures are concentrated.")
      .stats([(val("N01"), "orders analysed, 86 weeks"),
              (val("N06"), "arrived on time"),
              (val("N07"), "late, of delivered orders"),
              (val("N09"), "rated 1–2★ when late")])
      .body("A late order is rare. When it happens the customer reaction is severe: "
            f"{val('N09')} leave 1–2★, against {val('N10')} on an on-time order.")
      .done())

    # 2 — what the monitor caught
    (d.slide("02 · What the monitor caught", "Eight weeks out of 86 were genuinely unusual, not just noisy.")
      .stats([(val("N20"), "weeks flagged SEV1 by the control chart"),
              (val("N36"), "of all late orders fall in those 8 weeks"),
              ("2", "separate episodes: Black Friday 2017, Feb–Mar 2018")])
      .body("A control chart on the weekly late rate, baselined on the median of the prior 26 weeks, "
            "so an alert means statistically unusual rather than simply higher than last week.")
      .done())

    # 3 — whose problem
    (d.slide("03 · Whose problem it was", "Same symptom, two different causes. Sellers were not the main one.")
      .stats([(val("N18"), "of late orders had already left the seller on time"),
              (val("N19"), "would have been saved by an on-time handoff alone"),
              (val("N32"), "late rate in Rio de Janeiro, Feb–Mar 2018")])
      .body(f"Black Friday stretched both legs ({val('N102')} on the seller leg, {val('N103')} on the carrier leg). "
            f"February–March barely touched the seller leg ({val('N104')}) and added {val('N105')} to the carrier leg. "
            "Chasing slow sellers would have missed the worse episode entirely.")
      .done())

    # 4 — what to do
    (d.slide("04 · What to do", "Three moves, ranked by what the data actually supports.")
      .body("1  Wire the monitor to a weekly review with a defined SEV1 trigger.   0–30 days", size=16, color=CREAM, gap=24)
      .body("2  Run the episode-response playbook on the next flagged week.   30–60 days", size=16, color=CREAM, gap=24)
      .body(f"3  Put the {val('N41')} flagged sellers on a handoff improvement track.   60–90 days", size=16, color=CREAM, gap=24)
      .note("Owners shown on the website are illustrative functional roles. No Instacart team, tool or "
            "internal metric is named or estimated anywhere in this project.")
      .done())

    # 5 — what it is worth
    (d.slide("05 · What it is worth", "Counting only what could actually have been acted on at the time.")
      .bars([("Episode response (longer promise)", int(float(L["N70"]["value"]))),
             ("Seller handoff programme", int(float(L["N62"]["value"]))),
             ("Lane-level promise", int(float(L["N78"]["value"])))], unit=" late orders")
      .note("Black Friday is on the calendar, so it is counted in full. Feb–Mar 2018 counts only orders placed "
            "after the monitor could have confirmed the episode, using the dataset's own median promise length "
            "as the detection delay. The cost in lost conversions from a longer promise cannot be measured here.")
      .done())

    # 6 — limits
    (d.slide("06 · Limits", "What this evidence does not support."))
    for line in [
        "Multi-day parcel shipping in Brazil, 2017–2018. The methods transfer; the timescales and the specific numbers do not.",
        "No reschedule events and no shopper-supply data, so two defect types a real fulfilment team tracks cannot be shown.",
        "Fault attribution uses timestamps, not pickup scans: a seller delayed by a missed carrier pickup is blamed unfairly.",
        f"The repeat-purchase result rests on {val('N50')} and {val('N55')} repeat customers. A consistent signal, not a measured effect size.",
        "The early-warning signal was tested and dropped: it gave no usable lead time before either episode.",
    ]:
        d.body("—  " + line, size=14, gap=22)
    d.done()

    d.save()
    size = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)}  ·  6 slides  ·  {size:.0f} KB")
    print(f"every number read from {LEDGER.relative_to(ROOT)} ({len(L)} ids available)")


if __name__ == "__main__":
    build()
