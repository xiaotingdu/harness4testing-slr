"""Draw the study-selection flow diagram for the 154-paper corpus.

Fonts, font sizes, line colours and box geometry follow the previous PowerPoint figure; the database, venue and
final-corpus icons are copied as vector graphics from that figure.
Usage: python prisma_fitz.py prisma_ppt_20260930.pdf prisma   (run in figures/)
"""
import sys

import fitz

OLD, STEM = sys.argv[1], sys.argv[2]
FONTS = {'reg': 'C:/Windows/Fonts/gadugi.ttf', 'bold': 'C:/Windows/Fonts/gadugib.ttf',
         'num': 'C:/Windows/Fonts/calibrib.ttf'}
GREY, BLUE, RED, GREEN = (0.455, 0.455, 0.455), (0.306, 0.580, 0.851), (0.753, 0.310, 0.082), (0.275, 0.827, 0.353)
W, H = 960, 618

doc = fitz.open()
page = doc.new_page(width=W, height=H)
old = fitz.open(OLD)
for name, path in FONTS.items():
    page.insert_font(fontname=name, fontfile=path)
measure = {name: fitz.Font(fontfile=path) for name, path in FONTS.items()}


def rbox(x0, y0, x1, y1, color, radius=0.18):
    page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=color, fill=(1, 1, 1), width=1.5, radius=radius)


def text(x, y_top, s, size, font='reg', align='left'):
    """Place text so that its top edge is at y_top (matching the old figure's span boxes)."""
    if align == 'center':
        x -= measure[font].text_length(s, fontsize=size) / 2
    page.insert_text((x, y_top + size * 1.02), s, fontname=font, fontsize=size, color=(0, 0, 0))


def arrow(x0, y0, x1, y1):
    page.draw_line((x0, y0), (x1, y1), color=(0, 0, 0), width=1.5)
    if x0 == x1:  # downward arrow
        tri = [(x1 - 4.5, y1 - 9), (x1 + 4.5, y1 - 9), (x1, y1)]
    else:  # rightward arrow
        tri = [(x1 - 9, y1 - 4.5), (x1 - 9, y1 + 4.5), (x1, y1)]
    page.draw_polyline(tri + [tri[0]], color=(0, 0, 0), fill=(0, 0, 0), width=0.5, closePath=True)


def pill(cx, y_top, s, color, bold=False, size=14):
    font = 'bold' if bold else 'reg'
    w = measure[font].text_length(s, fontsize=size) + 22
    rbox(cx - w / 2, y_top, cx + w / 2, y_top + 22.5, color, radius=0.5)
    text(cx, y_top + 2.2, s, size, font, align='center')


# Search routes: the two kept boxes reuse the old boxes' size and their vector icons.
ROUTES = [((110, 25.3), (2.5, 26.1, 217.9, 86.6), (9.5, 40.3, 35.1, 75.1), 'Database search',
           'arXiv \u00b7 ACM DL \u00b7 IEEE Xplore'),
          ((380, 25.3), (246.4, 25.3, 464.4, 85.8), (254.1, 36.2, 285.3, 71.9), 'Manual venue search',
           'Main tracks of selected venues')]
for (bx, by), obox, icon, title, sub in ROUTES:
    w, h = obox[2] - obox[0], obox[3] - obox[1]
    rbox(bx, by, bx + w, by + h, GREY, radius=0.15)
    ix, iy = bx + (icon[0] - obox[0]), by + (icon[1] - obox[1])
    page.show_pdf_page(fitz.Rect(ix, iy, ix + icon[2] - icon[0], iy + icon[3] - icon[1]), old, 0,
                       clip=fitz.Rect(*icon))
    tx = ix + (icon[2] - icon[0]) + 8
    text(tx, by + 11.5, title, 14, 'bold')
    text(tx, by + 38, sub, 12)
CX = 353.1  # centre of the stage column, as in the old figure
db_cx, ve_cx = 110 + 215.4 / 2, 380 + 218 / 2
page.draw_line((db_cx, 86), (db_cx, 106), color=(0, 0, 0), width=1.5)
page.draw_line((ve_cx, 86), (ve_cx, 106), color=(0, 0, 0), width=1.5)
page.draw_line((db_cx, 106), (ve_cx, 106), color=(0, 0, 0), width=1.5)
for x in (db_cx, ve_cx):
    page.draw_circle((x, 86), 2.6, color=(0, 0, 0), fill=(0, 0, 0))
arrow(CX, 106, CX, 128)


def stage(y, num, title, sub):
    rbox(171.7, y, 534.6, y + 59, BLUE)
    page.draw_circle((196.85, y + 29.5), 16.5, color=BLUE, fill=(1, 1, 1), width=1.5)
    text(196.85, y + 16.8, str(num), 18, 'num', align='center')
    text(225, y + 7, title, 16, 'bold')
    text(225, y + 31, sub, 14)


def excluded(y, n, lines):
    rbox(582.1, y, 894.0, y + 59, RED)
    text(596, y + 2, 'Excluded', 16, 'bold')
    w = measure['bold'].text_length(n, fontsize=14) + 22
    rbox(869.7 - w, y + 4.4, 869.7, y + 21.4, RED, radius=0.5)
    text(869.7 - w / 2, y + 3.6, n, 14, 'bold', align='center')
    for i, line in enumerate(lines):
        text(595, y + 21 + 17 * i, line, 14)
    arrow(534.6, y + 29.5, 582.1, y + 29.5)


Y = [128, 234, 340, 446]
stage(Y[0], 1, 'Literature search and deduplication', 'Out-of-period records removed; routes merged')
arrow(CX, Y[0] + 59, CX, Y[1])
pill(440.3, Y[0] + 71.5, '3,942 unique records', BLUE)

stage(Y[1], 2, 'Title-and-abstract screening', 'Records checked against the screening criteria')
excluded(Y[1], 'n = 2,623', ['Did not meet the screening criteria (2,609)', 'Duplicates (14)'])
arrow(CX, Y[1] + 59, CX, Y[2])
pill(440.3, Y[1] + 71.5, '1,319 reports', BLUE)

stage(Y[2], 3, 'Venue filtering', 'Reports checked against the venue condition')
excluded(Y[2], 'n = 984', ['Venue not eligible (972)', 'Withdrawn (5); duplicates (7)'])
arrow(CX, Y[2] + 59, CX, Y[3])
pill(440.3, Y[2] + 71.5, '335 full-text reports', BLUE)

stage(Y[3], 4, 'Final study selection', 'Reports assessed against five conditions')
excluded(Y[3], 'n = 181', ['Did not meet one or more of the five', 'selection conditions'])
FY = 559
arrow(CX, Y[3] + 59, CX, FY)

# Final corpus box, with the old check-mark icon.
rbox(217.9, FY, 482.2, FY + 50.4, GREEN)
page.draw_circle((242.65, FY + 24.3), 16.5, color=GREEN, fill=(1, 1, 1), width=1.5)
page.show_pdf_page(fitz.Rect(231.2, FY + 16.2, 254.2, FY + 32.4), old, 0, clip=fitz.Rect(231.2, 501.8, 254.2, 518.0))
text(271, FY + 2.4, 'Final corpus', 16, 'bold')
text(271, FY + 26.4, 'Studies included', 14)
w = measure['bold'].text_length('n = 154', fontsize=14) + 22
rbox(419.7 - w / 2, FY + 13.5, 419.7 + w / 2, FY + 37.8, GREEN, radius=0.5)
text(419.7, FY + 15.5, 'n = 154', 14, 'bold', align='center')

doc.subset_fonts()
doc.save(STEM + '.pdf', garbage=3, deflate=True)
page.get_pixmap(dpi=110).save(STEM + '.png')
print('written', STEM + '.pdf')
