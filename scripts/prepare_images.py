"""Turn the CC0 source photos into cut-out WebP files for the website.

    python scripts/prepare_images.py

Reads reference/image_sources.json (the Commons file names, licences and
credits, captured when the photos were chosen), downloads each photo once
into build/img_cache/, lifts the subject off its white studio background,
trims, resizes and writes site/img/<slug>.webp.

The cutout works by flood-filling inward from the border: anything that is
background-coloured AND connected to the edge of the frame is removed, so
white highlights inside the subject survive while the backdrop and its
drop shadow do not.

Re-running is cheap -- downloads are cached, so it only redoes the cutting.
"""
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "reference" / "image_sources.json"
CACHE = ROOT / "build" / "img_cache"
OUT = ROOT / "site" / "img"

# A studio backdrop is bright and almost colourless, which separates it from
# the fruit cleanly: even a pale lemon is far more saturated than grey card.
# Per-image overrides live in reference/image_sources.json.
LUMA_MIN = 145      # backdrop is at least this bright
SAT_MAX = 55        # ...and no more colourful than this
# Discard leftover specks smaller than this share of the main subject.
SPECK_SHARE = 0.05
# longest edge of the written file; the page shows these at ~240 CSS px, so
# this leaves enough for a 2x display without shipping a huge file
MAX_EDGE = 520
WEBP_QUALITY = 82


def fetch(url: str, dest: pathlib.Path) -> None:
    """Download with curl (the system Python has no usable CA bundle)."""
    if dest.exists() and dest.stat().st_size > 10_000:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    ua = "SofiaMotaPortfolio/1.0 (portfolio case study; sof17.brasil@gmail.com)"
    subprocess.run(["curl", "-sfL", "-A", ua, "-o", str(dest), url], check=True)


def cut_out(im: Image.Image, luma_min=LUMA_MIN, sat_max=SAT_MAX) -> Image.Image:
    """Remove the studio backdrop and its drop shadow, returning RGBA."""
    im = im.convert("RGB")
    a = np.asarray(im).astype(np.int16)
    hi = a.max(axis=2)
    lo = a.min(axis=2)
    backdrop_like = (hi >= luma_min) & ((hi - lo) <= sat_max)

    # Keep only backdrop that is connected to the edge of the frame. This is
    # what protects white highlights sitting inside the subject -- they are
    # backdrop-coloured but have no path out to the border.
    labels, n = ndimage.label(backdrop_like)
    if n:
        border = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
        border.discard(0)
        outside = np.isin(labels, list(border))
    else:
        outside = np.zeros_like(backdrop_like)

    solid = ~outside

    # Drop stray survivors (a lit patch of backdrop the flood could not reach,
    # a crumb on the sweep) by keeping only blobs close to the subject's size.
    blobs, m = ndimage.label(solid)
    if m > 1:
        sizes = ndimage.sum(solid, blobs, range(1, m + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s >= SPECK_SHARE * sizes.max()]
        solid = np.isin(blobs, keep)

    mask = Image.fromarray(np.where(solid, 255, 0).astype(np.uint8), "L")
    # pull the edge in by a hair, then soften it, so no white fringe survives
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))

    rgba = im.convert("RGBA")
    rgba.putalpha(mask)
    return rgba


def trim(im: Image.Image, trim_bottom: int = 0) -> Image.Image:
    """Crop to the visible subject. trim_bottom shaves a fixed number of rows
    off the base first, for the one photo whose contact shadow picks up so
    much colour bounced off the subject that no threshold separates it."""
    def bbox(img):
        return img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()

    box = bbox(im)
    if box:
        im = im.crop(box)
    if trim_bottom:
        im = im.crop((0, 0, im.width, max(1, im.height - trim_bottom)))
        box = bbox(im)
        if box:
            im = im.crop(box)
    return im


def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 1
    sources = json.loads(SRC.read_text())
    OUT.mkdir(parents=True, exist_ok=True)

    for item in sources:
        slug = item["slug"]
        raw = CACHE / f"{slug}.jpg"
        fetch(item["download_url"], raw)

        im = cut_out(Image.open(raw),
                     luma_min=item.get("luma_min", LUMA_MIN),
                     sat_max=item.get("sat_max", SAT_MAX))
        im = trim(im, trim_bottom=item.get("trim_bottom", 0))
        im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)

        dest = OUT / f"{slug}.webp"
        im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
        kb = dest.stat().st_size / 1024
        print(f"{slug:14s} {im.width:>4}x{im.height:<4} {kb:6.1f} KB  <- {item['title']}")

    # Sofia's own halved fruit and vegetable cut-outs. These arrive already
    # masked, so they skip the background lift entirely -- they only need
    # trimming to the subject, resizing and converting to WebP. They are
    # padded to a square first so that the slow rotation in the hero turns
    # about the centre of the subject and never clips a corner.
    local = sorted((ROOT / "design").glob("*.png"))
    for path in local:
        im = Image.open(path).convert("RGBA")
        im = im.crop(im.getchannel("A").getbbox())      # trim to the subject

        side = max(im.size)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
        # The hero shows these at 8-13rem (128-208 CSS px). 440px covers a 2x
        # display with headroom; 520 was shipping pixels no screen could use,
        # which is what Lighthouse's "improve image delivery" was pointing at.
        square.thumbnail((440, 440), Image.LANCZOS)

        dest = OUT / f"half-{path.stem}.webp"
        square.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
        kb = dest.stat().st_size / 1024
        print(f"half-{path.stem:9s} {square.width:>4}x{square.height:<4} {kb:6.1f} KB  <- design/{path.name}")

    total = sum(f.stat().st_size for f in OUT.glob("*.webp")) / 1024
    print(f"\n{len(sources) + len(local)} images, {total:.1f} KB total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
