# -*- coding: utf-8 -*-
"""Contact sheets + QA sheets, built from the FINAL images in output/.
Usage: python3 -B contact.py
  contact_sheet.png              US 4:5 feed slides, representative posts (every background variant)
  contact_sheet_international.png International 4:5 slides (incl. weeks where Israel differs)
  _qa/qa_150px.png  _qa/qa_phone_390px.png  _qa/qa_9x16.png  _qa/qa_1x1.png  _qa/qa_intl_9x16_1x1.png"""
import os, glob
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'output'); QA = os.path.join(HERE, '_qa'); os.makedirs(QA, exist_ok=True)
F = ImageFont.truetype(os.path.join(HERE, 'assets/fonts/Poppins-Medium.ttf'), 20)
FB = ImageFont.truetype(os.path.join(HERE, 'assets/fonts/Poppins-Bold.ttf'), 26)
BG = (20, 30, 50)
PICK = ['2026-11-13_shabbat', '2026-12-04_shabbat', '2026-12-18_fast', '2027-03-21_fast', '2027-04-21_yomtov',
        '2027-04-27_yomtov', '2027-06-10_yomtov', '2027-06-25_shabbat', '2027-08-11_fast', '2027-10-01_yomtov',
        '2027-10-10_yomtov', '2027-10-15_yomtov', '2027-10-22_yomtov']
PICK_INTL = ['2026-11-13_shabbat', '2026-12-18_fast', '2027-04-21_yomtov', '2027-06-10_yomtov', '2027-06-18_shabbat',
             '2027-07-16_shabbat', '2027-08-11_fast', '2027-10-15_yomtov']


def folder(prefix):
    m = sorted(glob.glob(os.path.join(OUT, prefix + '_*')))
    return os.path.basename(m[0]) if m else None


def files(fo, fmt, intl=False):
    fs = sorted(glob.glob(os.path.join(OUT, fo, '*_%s_*.png' % fmt)))
    return [f for f in fs if ('_intl_' in f) == intl]


def sheet(items, tw_, cols, title, path):
    pad = 16; lab = 30
    ims = []
    for p, label in items:
        im = Image.open(p).convert('RGB'); ims.append((im.resize((tw_, int(im.height * tw_ / im.width)), Image.LANCZOS), label))
    rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
    hs = [max(i.height for i, _ in r) for r in rows]
    sh = Image.new('RGB', (cols * (tw_ + pad) + pad, sum(h + pad + lab for h in hs) + pad + 56), BG)
    d = ImageDraw.Draw(sh); d.text((pad, 14), title, font=FB, fill=(255, 255, 255))
    y = 56 + pad
    for r, h in zip(rows, hs):
        for i, (im, label) in enumerate(r):
            x = pad + i * (tw_ + pad)
            sh.paste(im, (x, y)); d.text((x, y + im.height + 3), label[:34], font=F, fill=(220, 226, 236))
        y += h + pad + lab
    sh.save(path, optimize=True)


def lab(p):
    b = os.path.basename(p)
    return b[10:20] + ' ' + b.split('_', 4)[-1][:-4].replace('_', ' ')


def main():
    pick = [f for f in (folder(p) for p in PICK) if f]
    items = [(p, f[:10] + ' ' + f.split('_', 2)[2][:16] + (' s2' if p.endswith('_s2.png') else ''))
             for f in pick for p in files(f, '4x5')]
    sheet(items[:16], 270, 4, 'Aleph Brick - Shabbat / Yom Tov / Fast times (DRAFT, US 4:5 feed slides)',
          os.path.join(HERE, 'contact_sheet.png'))
    ip = [f for f in (folder(p) for p in PICK_INTL) if f]
    sheet([(p, f[:10] + ' intl ' + f.split('_', 2)[2][:12] + ' ' + p.rsplit('_', 1)[-1][:-4]) for f in ip for p in files(f, '4x5', True)],
          270, 4, 'International card (DRAFT, 4:5, local time; Israel = Israel calendar)',
          os.path.join(HERE, 'contact_sheet_international.png'))
    sheet([(files(f, '4x5')[0], f[:10]) for f in pick], 150, 7, '150 px check', os.path.join(QA, 'qa_150px.png'))
    sheet([(files(f, '4x5')[0], f[:10]) for f in pick[:4]] + [(files(f, '4x5', True)[0], f[:10] + ' intl') for f in ip[2:4]],
          390, 3, '390 px (phone feed width)', os.path.join(QA, 'qa_phone_390px.png'))
    sheet([(p, lab(p)) for f in pick[:6] for p in files(f, '9x16')], 216, 6, '9:16 stories (US)', os.path.join(QA, 'qa_9x16.png'))
    sheet([(p, lab(p)) for f in pick[4:8] for p in files(f, '1x1')], 270, 4, '1:1 slides (US)', os.path.join(QA, 'qa_1x1.png'))
    sheet([(p, lab(p)) for f in ip[:5] for p in files(f, '9x16', True) + files(f, '1x1', True)], 216, 6,
          'International 9:16 + 1:1', os.path.join(QA, 'qa_intl_9x16_1x1.png'))


if __name__ == '__main__':
    main()
