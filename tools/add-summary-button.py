#!/usr/bin/env python3
"""
Add the "Return to IRG's Center for Investigative Oversight" button to page 1
of the two-page summary PDF, in the navy band directly above the IRG logo.

WHY THIS EXISTS
    The summary is produced from Word, and a Word export cannot carry this
    button. Re-run this after every re-export or the button is lost.

USAGE — always run it on a FRESH Word export:

    python3 tools/add-summary-button.py <fresh-export.pdf> Agency_Sunshine_Summary.pdf

    It reads the input and writes a new output file, so it never stacks
    buttons. Do NOT run it with the same file as input and output twice: the
    button is drawn page content, not an annotation, so a second pass would
    paint a second bar on top of the first.

PLACEMENT
    Anchored to the IRG wordmark found on page 1, so it stays correct if the
    header shifts. Sits above the logo and clear of the sun graphic to its
    right. Falls back to fixed coordinates if the logo cannot be located.

NOTE ON THE LABEL
    The PDF base fonts use WinAnsi encoding, which has no left-arrow glyph —
    a "←" renders as "?". The guillemet "«" is in WinAnsi and is used instead.
"""
import os
import sys

import fitz

URL = "https://reforminggovernment.org/center-for-investigative-oversight/"
LABEL = "«  RETURN TO IRG'S CENTER FOR INVESTIGATIVE OVERSIGHT"

GOLD = (0.749, 0.565, 0.000)   # #BF9000
NAVY = (0.122, 0.220, 0.392)   # #1F3864

MAX_WIDTH = 232.0
BAR_HEIGHT = 20.0
GAP_ABOVE_LOGO = 9.0


def find_logo(page):
    """The IRG wordmark: widest image in the top quarter of the page."""
    best = None
    for img in page.get_images(full=True):
        for rect in page.get_image_rects(img[0]):
            if rect.y0 < page.rect.height * 0.25 and rect.width > 100:
                if best is None or rect.width > best.width:
                    best = rect
    return best


def already_has_button(page):
    for link in page.get_links():
        if link.get("uri") == URL and link["from"].y1 < page.rect.height * 0.2:
            return True
    return False


def add_button(src, dst):
    doc = fitz.open(src)
    page = doc[0]

    if already_has_button(page):
        raise SystemExit(
            "refusing to run: page 1 already carries this button.\n"
            "Run this on a fresh Word export instead, or the bar will double up."
        )

    logo = find_logo(page)
    if logo:
        centre_x = (logo.x0 + logo.x1) / 2
        bottom = logo.y0 - GAP_ABOVE_LOGO
    else:
        centre_x, bottom = 270.0, 69.0

    # Shrink the type until the label fits the available width.
    size = 8.0
    while size > 5.0 and fitz.get_text_length(LABEL, fontname="hebo", fontsize=size) > MAX_WIDTH - 18:
        size -= 0.2

    text_w = fitz.get_text_length(LABEL, fontname="hebo", fontsize=size)
    width = text_w + 18
    rect = fitz.Rect(centre_x - width / 2, bottom - BAR_HEIGHT, centre_x + width / 2, bottom)

    page.draw_rect(rect, color=GOLD, fill=GOLD, width=0.6)
    # Baseline placed so the caps sit optically centred in the bar.
    baseline = fitz.Point(rect.x0 + 9, rect.y0 + BAR_HEIGHT / 2 + size * 0.35)
    page.insert_text(baseline, LABEL, fontname="hebo", fontsize=size, color=NAVY)
    page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": URL})

    tmp = dst + ".tmp"
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    os.replace(tmp, dst)
    print("button added -> %s" % dst)
    print("  rect      : %s" % (tuple(round(v, 1) for v in rect),))
    print("  font size : %.1f pt" % size)
    print("  links to  : %s" % URL)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__.strip().split("USAGE")[1].split("PLACEMENT")[0].strip())
    add_button(sys.argv[1], sys.argv[2])
