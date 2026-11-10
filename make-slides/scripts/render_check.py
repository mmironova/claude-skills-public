"""Turn a Drive PDF export of a deck into page images and contact sheets.

Looking at the rendered slides is the only reliable way to catch text
overflowing a box, a figure colliding with bullets, or a line disappearing
under the footer band: the Slides API reports geometry, not what the
renderer actually does with it. LibreOffice and Keynote automation are
usually unavailable, so the export from Google is the rendering of record.

Workflow:

  1. Export:  Drive download_file_content, exportMimeType application/pdf.
     The result is too large for the context, so the host saves it to a
     JSON file and tells you the path.
  2. Render:  python render_check.py <that.json> <outdir> [--dpi 110]
              python render_check.py <deck.pdf> <outdir> --pages 3,5,11
  3. Read the contact sheets (4 slides each) and fix what you see.

Needs pymupdf and Pillow.
"""
import argparse
import base64
import json
import os
import sys

import pymupdf
from PIL import Image


def load_pdf(src, dest):
    """Accept either a .pdf or the JSON wrapper a connector export leaves."""
    if src.lower().endswith(".pdf"):
        return src
    with open(src) as f:
        payload = json.load(f)
    content = payload["content"] if isinstance(payload, dict) else payload
    out = os.path.join(dest, "deck.pdf")
    with open(out, "wb") as f:
        f.write(base64.b64decode(content))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help=".pdf, or the .json a Drive export was saved to")
    ap.add_argument("outdir")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--pages", default="", help="1-based, e.g. 3,5,11 or 4-9; default all")
    ap.add_argument("--per-sheet", type=int, default=4)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    doc = pymupdf.open(load_pdf(args.source, args.outdir))

    if args.pages:
        pages = []
        for part in args.pages.split(","):
            if "-" in part:
                a, b = part.split("-")
                pages += list(range(int(a), int(b) + 1))
            else:
                pages.append(int(part))
    else:
        pages = list(range(1, len(doc) + 1))

    files = []
    for p in pages:
        if not 1 <= p <= len(doc):
            print(f"skipping page {p}: deck has {len(doc)}", file=sys.stderr)
            continue
        path = os.path.join(args.outdir, f"p{p:02d}.png")
        doc[p - 1].get_pixmap(dpi=args.dpi).save(path)
        files.append(path)

    n = args.per_sheet
    cols = 2 if n > 1 else 1
    for k in range(0, len(files), n):
        ims = [Image.open(f) for f in files[k:k + n]]
        W, H = ims[0].size
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * W, rows * H), "white")
        for j, im in enumerate(ims):
            sheet.paste(im, ((j % cols) * W, (j // cols) * H))
        out = os.path.join(args.outdir, f"sheet{k // n + 1}.png")
        sheet.save(out)
        print("wrote", out, "pages", [os.path.basename(f) for f in files[k:k + n]])
    print(f"{len(files)} page images in {args.outdir}")


if __name__ == "__main__":
    main()
