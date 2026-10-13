"""Render the 1200x630 social preview card.

    python scripts/make_social_card.py

Uses the site's own fonts and palette, and reads its headline number from
out/numbers_ledger.csv so the card can never quote a figure the page does not.
"""
import csv
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "out" / "numbers_ledger.csv"
FONTS = ROOT / "site" / "fonts"
OUT = ROOT / "site" / "img" / "social-card.png"

INK, CREAM, EMBER, GOLD = "#100B06", "#F5E4C7", "#F15726", "#BE8D3F"


def ledger():
    return {r["id"]: r for r in csv.DictReader(open(LEDGER))}


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def main() -> int:
    L = ledger()
    im = Image.new("RGB", (1200, 630), INK)
    d = ImageDraw.Draw(im)

    body = lambda s: font("inter-tight-var-latin.woff2", s)
    disp = lambda s: font("fjalla-one-400-latin.woff2", s)

    d.text((72, 64), "FULFILLMENT QUALITY TRIAGE", font=disp(26), fill=GOLD)

    # headline, hand-broken so the accent lands on its own line
    d.text((72, 140), "Most late deliveries", font=body(76), fill=CREAM)
    d.text((72, 224), "weren't the seller's fault.", font=body(76), fill=EMBER)

    d.text((72, 356), f"{L['N18']['value']}%", font=disp(96), fill=CREAM)
    d.text((72, 470), "of late orders had already left the seller on time",
           font=body(30), fill=CREAM)
    d.text((72, 512), f"across {int(float(L['N01']['value'])):,} real marketplace orders",
           font=body(30), fill="#B0A591")

    d.line([(72, 580), (1128, 580)], fill="#3A322A", width=1)
    d.text((72, 596), "A portfolio case study by Sofia Mota", font=body(22), fill="#B0A591")
    d.text((836, 596), "Not affiliated with Instacart", font=body(22), fill="#8C8373")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, "PNG", optimize=True)
    print(f"{OUT.relative_to(ROOT)}  {im.width}x{im.height}  {OUT.stat().st_size/1024:.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
