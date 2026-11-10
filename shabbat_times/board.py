# -*- coding: utf-8 -*-
"""Background comparison boards (files only).
  python3 -B board.py            -> _board/board_concepts.png  (4 concepts x 4:5 / 9:16 / international, same post)
                                    _board/board_seasonal_<concept>.png (every seasonal variant in one concept)
Renders straight from generate.py's specs, so the boards show exactly what the generator would publish."""
import os, sys, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import calendar_rules as R, generate as G, render, backgrounds as BG

OUT = os.path.join(HERE, '_board'); os.makedirs(OUT, exist_ok=True)
F = ImageFont.truetype(os.path.join(HERE, 'assets/fonts/Poppins-Medium.ttf'), 22)
FB = ImageFont.truetype(os.path.join(HERE, 'assets/fonts/Poppins-Bold.ttf'), 30)
LABEL = {'dusk': '(a) Jerusalem dusk - brick skyline', 'table': '(b) Shabbat table - soft blur',
         'night': '(c) Night sky - gold brick border', 'stone': '(d) Jerusalem stone - ashlar'}
SEASONAL = ['2026-12-04_shabbat', '2027-04-21_yomtov', '2027-06-10_yomtov', '2027-10-01_yomtov', '2027-10-10_yomtov',
            '2027-10-15_yomtov', '2027-10-22_yomtov', '2026-12-20_fast', '2027-08-12_fast', '2026-11-13_shabbat']


def occ_by_id():
    return {o['id']: o for o in R.occasions(dt.date(2026, 11, 13), dt.date(2027, 12, 31))}


def render_one(o, fmt, concept, intl=False):
    D = G.describe(o)
    specs = G.intl_slide_specs(o, D, fmt) if intl else G.slide_specs(o, D, fmt)
    suf, spec = specs[0]
    p = os.path.join(OUT, '%s_%s_%s%s.png' % (o['id'], concept, fmt, '_intl' if intl else ''))
    try:
        (render.render_intl if intl else render.render)(spec, fmt, p, concept)
    except render.Overflow:
        spec = G.intl_split(spec)[0][1]
        render.render_intl(spec, fmt, p, concept)
    return p


def sheet(cells, cols, tw_, th, title, path, lab_h=34):
    """Rows are as tall as their tallest image (scaled to width tw_)."""
    pad = 18
    ims = []
    for p, label in cells:
        im = Image.open(p).convert('RGB'); im = im.resize((tw_, int(im.height * tw_ / im.width)), Image.LANCZOS)
        ims.append((im, label))
    rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
    hs = [max(im.height for im, _ in r) for r in rows]
    sh = Image.new('RGB', (cols * (tw_ + pad) + pad, sum(h + pad + lab_h for h in hs) + pad + 60), (18, 24, 38))
    d = ImageDraw.Draw(sh); d.text((pad, 14), title, font=FB, fill=(255, 255, 255))
    y = 60 + pad
    for r, h in zip(rows, hs):
        for i, (im, label) in enumerate(r):
            x = pad + i * (tw_ + pad)
            sh.paste(im, (x, y)); d.text((x, y + im.height + 4), label, font=F, fill=(220, 226, 236))
        y += h + pad + lab_h
    sh.save(path, optimize=True)
    return path


def main():
    O = occ_by_id()
    o = O['2026-11-13_shabbat']
    cells = []
    for c in BG.CONCEPTS:
        cells.append((render_one(o, '4x5', c), LABEL[c] + ' · 4:5'))
    for c in BG.CONCEPTS:
        cells.append((render_one(o, '9x16', c), LABEL[c].split(' - ')[0] + ' · 9:16'))
    for c in BG.CONCEPTS:
        cells.append((render_one(o, '4x5', c, intl=True), LABEL[c].split(' - ')[0] + ' · International 4:5'))
    sheet(cells, 4, 420, 746, 'Background concepts - same post (Parshat Toldot), US 4:5 / story 9:16 / International',
          os.path.join(OUT, 'board_concepts.png'))
    for c in (sys.argv[1:] or [BG.DEFAULT]):
        cells = []
        for oid in SEASONAL:
            oo = O[oid]
            cells.append((render_one(oo, '4x5', c), '%s · %s' % (G.variant(oo), oo['id'][:10])))
        sheet(cells, 5, 380, 476, 'Seasonal variants - concept %s' % LABEL[c], os.path.join(OUT, 'board_seasonal_%s.png' % c))
    for c in render.CONTRAST:
        print('contrast', c)
    print('boards ->', OUT)


if __name__ == '__main__':
    main()
