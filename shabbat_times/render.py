# -*- coding: utf-8 -*-
"""Aleph Brick Shabbat / Yom Tov / Fast times graphics. PIL + RAQM, fonts and logo vendored in assets/.

v2 (Nov 9 2026, owner: "text and layout are great; the look is bland"): the text/table layout is unchanged; it now
sits on a rich procedural background (backgrounds.py) behind a translucent panel. Layers, bottom to top:
  scene (backgrounds.scene)  ->  translucent panel (+ gold rim, soft shadow)  ->  shapes (zebra rows, rules,
  candles, logo, brick band)  ->  text.
Every text run is recorded with its box and colour; after compositing, the WCAG contrast of each run against the
real pixels behind it is measured (worst of the 2nd/98th luminance percentiles) and must be >= 4.5:1.
House style = the ABC social series (cream / navy / brick red / gold, logo + series lockup, בס״ד, brick footer
band with studs). Motif: two brick candles (objects only, no people)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import backgrounds as BG

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, 'assets', 'fonts')
FONTS = {'pop_b': 'Poppins-Bold.ttf', 'pop_m': 'Poppins-Medium.ttf', 'pop_r': 'Poppins-Regular.ttf',
         'lora': 'Lora-Variable.ttf', 'heb': 'frank-ruhl-libre-he-lat-700.ttf', 'heb_m': 'frank-ruhl-libre-he-lat-500.ttf'}
LOGO = os.path.join(HERE, 'assets', 'logo_mark.png')

CREAM = (250, 242, 229); NAVY = (30, 56, 93); TRED = (196, 18, 30); NAVYBG = (13, 41, 73)
GOLD = (236, 190, 64); WHITE = (255, 255, 255)

# ---- palettes: text on the scene ("out") and inside the panel ("in")
OUT_DARK = dict(h1=WHITE, h2=GOLD, title=WHITE, heb=GOLD, date=GOLD, glow=(255, 200, 110), ga=150, motif=GOLD)
OUT_DARK_FAST = dict(h1=(236, 238, 244), h2=(222, 200, 150), title=(236, 238, 244), heb=(222, 200, 150),
                     date=(222, 200, 150), glow=(236, 190, 64), ga=0, motif=(222, 200, 150))
OUT_LIGHT = dict(h1=NAVY, h2=(110, 14, 22), title=NAVY, heb=(110, 14, 22), date=(110, 14, 22), glow=(255, 190, 90),
                 ga=120, motif=(110, 14, 22))
OUT_LIGHT_FAST = dict(OUT_LIGHT, h2=(60, 70, 88), heb=(60, 70, 88), date=(60, 70, 88), ga=0, motif=(60, 70, 88))
IN_CREAM = dict(panel=CREAM, pa=0.94, rim=(214, 170, 70), body=NAVY, muted=(78, 88, 108), zebra=(241, 229, 208),
                rule=(222, 206, 180), c1=TRED, c2=NAVY, note=(70, 84, 108), url=TRED)
IN_NAVY = dict(panel=(10, 28, 56), pa=0.86, rim=GOLD, body=WHITE, muted=(170, 184, 206), zebra=(24, 52, 88),
               rule=(52, 82, 120), c1=GOLD, c2=WHITE, note=(200, 210, 226), url=GOLD)
IN_SLATE = dict(panel=(18, 28, 44), pa=0.88, rim=(120, 130, 150), body=(236, 238, 244), muted=(160, 172, 194),
                zebra=(30, 44, 64), rule=(60, 76, 100), c1=(222, 200, 150), c2=(236, 238, 244), note=(196, 204, 220),
                url=(222, 200, 150))
BAND = {'shabbat': dict(band=TRED, bandtext=WHITE), 'yomtov': dict(band=GOLD, bandtext=NAVYBG),
        'fast': dict(band=NAVY, bandtext=(236, 238, 244))}


def theme(concept, tone, variant):
    """Merge the palette for one concept + occasion tone (shabbat | yomtov | fast)."""
    fast = tone == 'fast'
    light_scene = concept == 'stone'
    if fast:
        out = OUT_LIGHT_FAST if light_scene else OUT_DARK_FAST
        inn = IN_CREAM if light_scene else IN_SLATE
    elif tone == 'yomtov':
        out = OUT_LIGHT if light_scene else OUT_DARK
        inn = IN_CREAM if light_scene else IN_NAVY
    else:
        out = OUT_LIGHT if light_scene else OUT_DARK
        inn = IN_NAVY if concept == 'night' else IN_CREAM
    T = dict(out); T.update(inn); T.update(BAND[tone])
    if variant == 'yom_kippur' and not light_scene:
        T.update(h2=(226, 230, 240), heb=(226, 230, 240), date=(226, 230, 240), c1=(226, 230, 240), url=(226, 230, 240))
    return T


FMT = {'4x5': (1080, 1350), '1x1': (1080, 1080), '9x16': (1080, 1920)}
MIN_PX = 30          # house rule: nothing smaller than 30 px on a 1080 canvas
MIN_CONTRAST = 4.5
SIZES_USED = set()   # every font size drawn (checked against MIN_PX by generate.py)
DROPPED = []         # (post id, city) where a state abbreviation had to be dropped
CONTRAST = []        # (file, worst ratio, text)

_fc = {}


def font(key, size, var=None):
    SIZES_USED.add(size)
    k = (key, size, var)
    if k not in _fc:
        f = ImageFont.truetype(os.path.join(FD, FONTS[key]), size, layout_engine=ImageFont.Layout.RAQM)
        if var:
            f.set_variation_by_name(var)
        _fc[k] = f
    return _fc[k]


def tw(f, t, rtl=False, tr=0):
    if rtl:
        return f.getlength(t, direction='rtl', language='he')
    return f.getlength(t) + tr * max(0, len(t) - 1)


# ------------------------------------------------------------------ layered canvas
class Canvas:
    """Shapes go to `fx`, text to `tx`; text runs are recorded for the contrast check."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.fx = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.tx = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self._fd = ImageDraw.Draw(self.fx); self._td = ImageDraw.Draw(self.tx)
        self.recs = []
        self.geo = {}

    def draw(self):
        return _Draw(self)


class _Draw:
    def __init__(self, cv):
        self.cv = cv

    def text(self, xy, text, font=None, fill=None, direction=None, language=None):
        kw = dict(direction=direction, language=language) if direction else {}
        bb = self.cv._td.textbbox(xy, text, font=font, **kw)
        self.cv.recs.append((bb, tuple(fill[:3]), text))
        self.cv._td.text(xy, text, font=font, fill=fill, **kw)

    def __getattr__(self, name):
        return getattr(self.cv._fd, name)


def tracked(d, x, y, text, f, fill, tr, align='l'):
    w = tw(f, text, tr=tr)
    if align == 'c': x -= w / 2
    elif align == 'r': x -= w
    x0 = x
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch) + tr
    return x0, x


def heb(d, cx, y, text, f, fill):
    w = tw(f, text, True)
    d.text((cx - w / 2, y), text, font=f, fill=fill, direction='rtl', language='he')
    return cx - w / 2, cx + w / 2


# ------------------------------------------------------------------ brand pieces
_logo = None


def logo(h):
    global _logo
    if _logo is None:
        _logo = Image.open(LOGO).convert('RGBA')
    return _logo.resize((int(_logo.width * h / _logo.height), h), Image.LANCZOS)


def glow(cv, cx, cy, rx, ry, color, alpha):
    if alpha <= 0:
        return
    W, H = cv.fx.size
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=min(255, alpha))
    m = m.filter(ImageFilter.GaussianBlur(max(rx, ry) * 0.45))
    g = Image.new('RGBA', (W, H), tuple(color) + (0,)); g.putalpha(m)
    cv.fx.alpha_composite(g)


def brick_band(cv, y, h, color, stud_w=64, stud_h=18, pitch=120):
    d = cv.draw(); W = cv.W
    d.rectangle((0, y, W, y + h), fill=color)
    hl = tuple(min(255, int(c * 1.12 + 10)) for c in color)
    off = (W - (W // pitch) * pitch) // 2 + (pitch - stud_w) // 2
    for x in range(off, W, pitch):
        d.rounded_rectangle((x, y - stud_h, x + stud_w, y + 4), 6, fill=color)
        d.rectangle((x + 8, y - stud_h + 4, x + 16, y - 2), fill=hl)


def flame(cv, cx, bottom, h, w):
    S = 4; Wd, Hd = w * S, h * S
    f = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0)); d = ImageDraw.Draw(f)

    def drop(k, col):
        r = Wd * k / 2; cy = Hd - r - 1; cxx = Wd / 2
        d.ellipse((cxx - r, cy - r, cxx + r, cy + r), fill=col)
        d.polygon([(cxx - r * 0.97, cy - r * 0.25), (cxx, Hd - Hd * k), (cxx + r * 0.97, cy - r * 0.25)], fill=col)
    drop(1.0, (246, 150, 40, 255)); drop(0.68, (255, 206, 80, 255)); drop(0.36, (255, 246, 214, 255))
    f = f.resize((w, h), Image.LANCZOS)
    cv.fx.alpha_composite(f, (int(cx - w / 2), int(bottom - h)))


def brick_candle(cv, cx, base_y, body_h, s, T):
    """Shabbat candle built from bricks: gold studded holder, white brick body, smooth teardrop flame."""
    bw = int(34 * s)
    fy = base_y - int(22 * s) - body_h
    glow(cv, cx, fy - int(24 * s), int(60 * s), int(62 * s), T['glow'], T['ga'] if T['ga'] else 0)
    d = cv.draw()
    hw, hh = int(70 * s), int(22 * s)
    d.rounded_rectangle((cx - hw // 2, base_y - hh, cx + hw // 2, base_y), int(5 * s), fill=(214, 164, 44))
    d.rectangle((cx - hw // 2 + 3, base_y - hh + 3, cx + hw // 2 - 3, base_y - hh + int(7 * s)), fill=(246, 206, 96))
    for k in (-1, 1):
        sx = cx + k * int(22 * s)
        d.rounded_rectangle((sx - int(9 * s), base_y - hh - int(6 * s), sx + int(9 * s), base_y - hh + 2), 3,
                            fill=(214, 164, 44))
    top = base_y - hh - body_h; nb = max(2, round(body_h / (26 * s))); bh = body_h / nb
    for i in range(nb):
        y0 = top + i * bh; y1 = top + (i + 1) * bh - 2
        d.rectangle((cx - bw // 2, y0, cx + bw // 2, y1), fill=(252, 250, 243))
        d.rectangle((cx + bw // 2 - int(7 * s), y0, cx + bw // 2, y1), fill=(226, 221, 210))
        d.rectangle((cx - bw // 2, y1 - int(3 * s), cx + bw // 2, y1), fill=(214, 208, 196))
    d.rounded_rectangle((cx - int(9 * s), top - int(6 * s), cx + int(9 * s), top + 2), 3, fill=(252, 250, 243))
    d.rectangle((cx - int(2 * s), top - int(12 * s), cx + int(2 * s), top - int(6 * s)), fill=(60, 50, 40))
    flame(cv, cx, top - int(9 * s), int(46 * s), int(24 * s))


def brick_wall(cv, cx, y, color, bw=46, bh=17, cols=5):
    """Fast-day motif: a short, low wall of studded bricks (two staggered courses). No flame."""
    d = cv.draw()
    hl = tuple(min(255, int(c * 1.12 + 10)) for c in color)
    sh = tuple(int(c * 0.78) for c in color)
    W = cols * bw; x0 = cx - W / 2
    for i in range(cols):
        for k in (0.3, 0.7):
            sx = x0 + i * bw + k * bw
            d.rounded_rectangle((sx - 6, y - 6, sx + 6, y + 2), 2, fill=color)
            d.rectangle((sx - 4, y - 5, sx - 1, y - 1), fill=hl)
    for row in range(2):
        yy = y + row * (bh + 3)
        off = 0 if row == 0 else -bw / 2
        for i in range(cols + (1 if row else 0)):
            bx0 = max(x0, x0 + off + i * bw); bx1 = min(x0 + W, x0 + off + (i + 1) * bw)
            if bx1 - bx0 < 6: continue
            d.rectangle((bx0 + 1.5, yy, bx1 - 1.5, yy + bh), fill=color)
            d.rectangle((bx0 + 1.5, yy + bh - 3, bx1 - 1.5, yy + bh), fill=sh)
    return y + 2 * bh + 3


# ------------------------------------------------------------------ layout (unchanged geometry)
L = {  # per format: geometry and type sizes (px)
    '4x5': dict(M=40, hdr_y=44, logo=80, lock=30, title=54, heb=46, date=30, legend=30, th=30, city=30, time=35,
                note=30, top_gap=14, row=47, band_y=1252, band_h=98, url_in_band=True, cand_s=0.62),
    '1x1': dict(M=44, hdr_y=36, logo=72, lock=30, title=48, heb=42, date=30, legend=30, th=30, city=34, time=38,
                note=30, top_gap=10, row=58, band_y=992, band_h=88, url_in_band=True, cand_s=0.56),
    '9x16': dict(M=44, hdr_y=262, logo=92, lock=32, title=62, heb=52, date=32, legend=32, th=30, city=34, time=40,
                 note=30, top_gap=18, row=53, band_y=1800, band_h=120, url_in_band=False, cand_s=0.72),
}
PANEL_PAD = 18


def header(cv, T, g, line1, line2):
    d = cv.draw()
    M = g['M']; y = g['hdr_y']; lh = g['logo']
    lg = logo(lh); cv.fx.alpha_composite(lg, (M, y))
    tx = M + lg.width + 20; cy = y + lh / 2; fs = g['lock']
    _, r1 = tracked(d, tx, cy - fs - 6, line1, font('pop_b', fs), T['h1'], 3.2)
    _, r2 = tracked(d, tx, cy + 4, line2, font('pop_m', fs), T['h2'], 2.6)
    f = font('heb_m', 34); t = 'בס״ד'
    bx = cv.W - M - tw(f, t, True)
    d.text((bx, y - 4), t, font=f, fill=T['h2'], direction='rtl', language='he')
    cv.geo['lock_right'] = max(r1, r2); cv.geo['bsd_left'] = bx; cv.geo['hdr_bottom'] = y + lh
    return y + lh


def title_block(cv, T, g, y, spec):
    W = cv.W; cx = W / 2
    d = cv.draw()
    ft = font('lora', g['title'], 'SemiBold')
    title = spec['title_en']
    while tw(ft, title) > W - 2 * g['M'] - 220 and ft.size > 36:
        ft = font('lora', ft.size - 2, 'SemiBold')
    wt = tw(ft, title)
    fh = font('heb', g['heb'])
    half = max(wt, tw(fh, spec['title_he'], True)) / 2
    left, right = cx - half, cx + half
    if spec['motif'] == 'candles':
        s = g['cand_s']; body_h = int(ft.size * 0.95)
        base = int(y + ft.size * 1.05 + g['heb'] * 1.05)
        gap = int(70 * s)
        for k in (-1, 1):
            brick_candle(cv, int(cx + k * (half + gap)), base, body_h, s, T)
        left, right = cx - half - gap - 40 * s, cx + half + gap + 40 * s
    d.text((cx - wt / 2, y), title, font=ft, fill=T['title'])
    y += int(ft.size * 1.22)
    heb(d, cx, y - 4, spec['title_he'], fh, T['heb'])
    y += int(g['heb'] * 1.18)
    if spec['motif'] == 'bricks':
        y = brick_wall(cv, cx, y + 10, T['motif']) + 12
    fd = font('pop_b', g['date'])
    cv.geo['date_top'] = y
    for line in spec['date_lines']:
        tr = 2.4
        while tw(fd, line, tr=tr) > W - 2 * g['M'] and tr > 0.5:
            tr -= 0.4
        x0, x1 = tracked(d, cx, y, line, fd, T['date'], tr, align='c'); y += int(g['date'] * 1.3)
    cv.geo['title_lr'] = (left, right)
    return y


def legend(cv, T, g, y, items):
    """items: [(colour_key, text)] drawn centred on one line (two lines if it does not fit)."""
    d = cv.draw(); W = cv.W
    f = font('pop_m', g['legend']); r = g['legend'] * 0.26; gap = 36
    parts = [(T[k], t) for k, t in items]
    def width(ps):
        return sum(2 * r + 10 + tw(f, t) for _, t in ps) + gap * (len(ps) - 1)
    lines = [parts] if width(parts) <= W - 2 * g['M'] else [[p] for p in parts]
    for ps in lines:
        x = W / 2 - width(ps) / 2
        for col, t in ps:
            cy = y + g['legend'] * 0.72
            d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=col)
            x += 2 * r + 10
            d.text((x, y), t, font=f, fill=T['body']); x += tw(f, t) + gap
        y += int(g['legend'] * 1.4)
    return y


def table(cv, T, g, y, spec, final=False):
    """Two halves side by side; each row: City  ST   time1  time2 (right-aligned time columns)."""
    d = cv.draw(); W = cv.W; M = g['M']
    gutter = 26
    half = (W - 2 * M - gutter) / 2
    ncol = len(spec['cols'])
    fc = font('pop_m', g['city']); fst = font('pop_r', g['city']); ftm = font('pop_b', g['time'])
    fh = font('pop_b', g['th'])
    halves = spec['halves']; nrows = max(len(h) for h in halves)
    cw = [max(tw(ftm, r['t'][ci]) for h in halves for r in h) + 18 for ci in range(ncol)]
    cw[-1] = max(cw[-1], tw(fh, spec['cols'][-1]['head'], tr=1.2) + 12)
    def right_of(x1, ci):
        return x1 - 12 - sum(cw[ci + 1:])
    dropped = 0
    hy = y
    for hi in range(2):
        x0 = M + hi * (half + gutter); x1 = x0 + half
        tracked(d, x0 + 12, hy, spec['city_head'][hi], fh, T['muted'], 1.6)
        for ci, c in enumerate(spec['cols']):
            tracked(d, right_of(x1, ci), hy, c['head'], fh, T[c['color']], 1.2, align='r')
    y = hy + int(g['th'] * 1.45)
    d.line((M, y - 6, W - M, y - 6), fill=T['rule'], width=2)
    rh = g['row']
    for ri in range(nrows):
        ry = y + ri * rh
        if ri % 2 == 0:
            d.rounded_rectangle((M, ry, W - M, ry + rh - 2), 10, fill=T['zebra'])
        for hi in range(2):
            if ri >= len(halves[hi]):
                continue
            row = halves[hi][ri]
            x0 = M + hi * (half + gutter); x1 = x0 + half
            ty = ry + (rh - g['city'] * 1.32) / 2
            name, st = row['name'], row['st']
            maxname = half - 24 - sum(cw) - 2
            if tw(fc, name) > maxname:
                spec['too_long'] = True
            if st and tw(fc, name + ' ' + st) > maxname:
                dropped += 1
                if final: DROPPED.append((spec['id'], name))
                st = ''
            d.text((x0 + 12, ty), name, font=fc, fill=T['body'])
            if st:
                d.text((x0 + 12 + tw(fc, name + ' '), ty), st, font=fst, fill=T['muted'])
            for ci, c in enumerate(spec['cols']):
                right = right_of(x1, ci)
                t = row['t'][ci]
                tyy = ry + (rh - g['time'] * 1.32) / 2
                d.text((right - tw(ftm, t), tyy), t, font=ftm, fill=T[c['color']])
    d.line((W / 2, y, W / 2, y + nrows * rh - 2), fill=T['rule'], width=2)
    return y + nrows * rh, dropped


def table_full(cv, T, g, y, sec):
    """Full-width rows (international card when a section has 3-4 columns): City CC | t1 t2 t3 t4.
    Column heads are two lines: what (CANDLES / AFTER / ENDS) and when (FRI 10/15, SAT NIGHT)."""
    d = cv.draw(); W = cv.W; M = g['M']
    fc = font('pop_m', g['city']); fst = font('pop_r', g['city']); ftm = font('pop_b', g['time'])
    fh = font('pop_b', g['th'])
    ncol = len(sec['cols'])
    colw = min(205, (W - 2 * M - 330) / max(1, ncol))
    rights = [W - M - 14 - (ncol - 1 - ci) * colw for ci in range(ncol)]
    tracked(d, M + 12, y + int(g['th'] * 0.6), sec['city_head'], fh, T['muted'], 1.6)
    for ci, c in enumerate(sec['cols']):
        tr = 1.2
        for li, txt in enumerate((c['head'], c['sub'])):
            while tw(fh, txt, tr=tr) > colw - 8 and tr > 0:
                tr -= 0.4
            tracked(d, rights[ci], y + li * int(g['th'] * 1.12), txt, fh, T[c['color']] if li == 0 else T['muted'], tr, align='r')
    y += int(g['th'] * 2.6)
    d.line((M, y - 6, W - M, y - 6), fill=T['rule'], width=2)
    rh = g['row']
    for ri, row in enumerate(sec['rows']):
        ry = y + ri * rh
        if ri % 2 == 0:
            d.rounded_rectangle((M, ry, W - M, ry + rh - 2), 10, fill=T['zebra'])
        ty = ry + (rh - g['city'] * 1.32) / 2
        d.text((M + 12, ty), row['name'], font=fc, fill=T['body'])
        if row['st']:
            d.text((M + 12 + tw(fc, row['name'] + ' '), ty), row['st'], font=fst, fill=T['muted'])
        for ci, c in enumerate(sec['cols']):
            t = row['t'][ci]
            tyy = ry + (rh - g['time'] * 1.32) / 2
            d.text((rights[ci] - tw(ftm, t), tyy), t, font=ftm, fill=T[c['color']])
    return y + len(sec['rows']) * rh


def label_fits(text, fmt):
    g = L[fmt]
    return tw(font('pop_b', g['th']), text, tr=0) <= 1080 - 2 * g['M'] - 24


def section_label(cv, T, g, y, text):
    d = cv.draw(); W = cv.W; M = g['M']
    f = font('pop_b', g['th']); tr = 2.0
    while tw(f, text, tr=tr) > W - 2 * M - 24 and tr > 0:
        tr -= 0.4
    if tw(f, text, tr=tr) > W - 2 * M - 24:
        raise Overflow(('label', text))
    tracked(d, W / 2, y, text, f, T['c1'], tr, align='c')
    return y + int(g['th'] * 1.5)


def wrap(f, text, maxw):
    out, cur = [], ''
    for w in text.split(' '):
        t = (cur + ' ' + w).strip()
        if tw(f, t) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    out.append(cur)
    return out


def notes(cv, T, g, y, lines, maxw=None):
    d = cv.draw(); W = cv.W
    f = font('pop_r', g['note']); maxw = maxw or W - 2 * g['M']
    out = []
    for text in lines:
        out += wrap(f, text, maxw)
    for l in out:
        d.text((W / 2 - tw(f, l) / 2, y), l, font=f, fill=T['note']); y += int(g['note'] * 1.28)
    return y


def notes_height(g, lines, W=1080):
    f = font('pop_r', g['note']); maxw = W - 2 * g['M']
    return sum(len(wrap(f, t, maxw)) for t in lines) * int(g['note'] * 1.28)


class Overflow(Exception):
    pass


# ------------------------------------------------------------------ compositing + contrast
def lum(a):
    a = a / 255.0
    a = np.where(a <= 0.03928, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def ratio(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def panel_layer(W, H, rect, T):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('L', (W, H), 0)
    x0, y0, x1, y1 = rect
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 8, x1, y1 + 10), 28, fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); shadow.putalpha(sh)
    lay.alpha_composite(shadow)
    p = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(p)
    d.rounded_rectangle(rect, 26, fill=tuple(T['panel']) + (int(255 * T['pa']),))
    d.rounded_rectangle(rect, 26, outline=tuple(T['rim']) + (230,), width=3)
    lay.alpha_composite(p)
    return lay


def compose(cv, concept, variant, T, fmt, out, spec_id):
    W, H = cv.W, cv.H
    g = cv.geo
    avoid = [r[0] for r in cv.recs]
    lr = g.get('title_lr', (W / 2 - 200, W / 2 + 200))
    y_top = g['hdr_bottom'] + 6; y_bot = min(g['panel'][1], g.get('date_top', 9999)) - 6
    free = []
    if fmt == '9x16':
        free = [(36, 40, 330, 236), (W - 330, 40, W - 36, 236)]
    elif lr[0] - 44 > 150 and y_bot - y_top > 90:
        free = [(30, y_top, lr[0] - 14, y_bot), (lr[1] + 14, y_top, W - 30, y_bot)]
    cx3 = (g['lock_right'] + g['bsd_left']) / 2
    geo = dict(fmt=fmt, panel=g['panel'], band_y=g['band_y'], avoid=avoid, free=free, hdr_bottom=g['hdr_bottom'],
               prop_s=1.0 if fmt != '9x16' else 1.3,
               three_stars=[(cx3 - 64, g['hdr_y'] + 34), (cx3, g['hdr_y'] + 6), (cx3 + 64, g['hdr_y'] + 40)]
               if fmt != '9x16' else [(W * .40, 120), (W * .5, 84), (W * .60, 128)],
               moon_xy=(cx3, g['hdr_y'] + 34) if fmt != '9x16' else (W * .74, 130))
    sc = BG.scene(concept, variant, W, H, geo).convert('RGBA')
    sc.alpha_composite(panel_layer(W, H, g['panel'], T))
    sc.alpha_composite(cv.fx)
    under = np.asarray(sc.convert('RGB'), np.float32)
    worst = (99.0, '', None)
    for (x0, y0, x1, y1), fill, text in cv.recs:
        x0, y0 = max(0, int(x0)), max(0, int(y0)); x1, y1 = min(W, int(x1) + 1), min(H, int(y1) + 1)
        if x1 - x0 < 2 or y1 - y0 < 2 or not text.strip():
            continue
        L_ = lum(under[y0:y1, x0:x1].reshape(-1, 3))
        lt = float(lum(np.array([fill], np.float32))[0])
        r = min(ratio(lt, float(np.percentile(L_, 2))), ratio(lt, float(np.percentile(L_, 98))))
        if r < worst[0]:
            worst = (r, text, (x0, y0, x1, y1))
    sc.alpha_composite(cv.tx)
    sc.convert('RGB').save(out, optimize=True)
    CONTRAST.append((os.path.basename(out), round(worst[0], 2), worst[1], worst[2]))
    return worst[0]


def bottom_and_url(cv, T, g):
    W = cv.W
    d = cv.draw()
    if g['url_in_band']:
        brick_band(cv, g['band_y'], g['band_h'], T['band'])
        tracked(d, W / 2, g['band_y'] + (g['band_h'] - 30) / 2 - 6, 'ALEPHBRICK.COM', font('pop_b', 30),
                T['bandtext'], 4, align='c')
    else:
        tracked(d, W / 2, 1572, 'ALEPHBRICK.COM', font('pop_b', 30), T['url'], 4, align='c')
        brick_band(cv, g['band_y'], g['band_h'], T['band'])


def panel_rect(g, y_top, W):
    bottom = (g['band_y'] - 26) if g['url_in_band'] else 1622
    return (22, int(y_top), W - 22, int(bottom))


# ------------------------------------------------------------------ US card (unchanged layout)
def render(spec, fmt, out, concept=BG.DEFAULT):
    W, H = FMT[fmt]; g = dict(L[fmt]); T = theme(concept, spec['tone'], spec['variant'])
    nrows = max(len(h) for h in spec['halves'])
    for attempt in range(60):
        cv = Canvas(W, H)
        y = header(cv, T, g, spec['lock1'], spec['lock2'])
        y = title_block(cv, T, g, y + g['top_gap'] + 8, spec)
        y_panel = y + 2
        y_leg = y_panel + (6 if fmt == '1x1' else PANEL_PAD - 4)
        y = legend(cv, T, g, y_leg, spec['legend'])
        y_tab = y + 6
        nh = notes_height(g, spec['notes'])
        limit = (g['band_y'] - 34) if g['url_in_band'] else 1620 - 50
        need = y_tab + int(g['th'] * 1.45) + nrows * g['row'] + 14 + nh
        if need > limit:
            g['row'] -= 2
            if g['row'] < max(g['city'], g['time']) * 1.18:
                if g['city'] > MIN_PX: g['city'] -= 1      # city names give way first; then only the times shrink
                g['time'] -= 1; g['row'] = int(g['time'] * 1.3)
            if min(g['city'], g['time']) < MIN_PX:
                raise Overflow((spec['id'], fmt))
            continue
        spare = limit - need
        last = g['time'] <= 32 and g['city'] <= 30
        y, dropped = table(cv, T, g, y_tab + min(spare // 3, 24), spec, final=last)
        if dropped and not last:
            if g['city'] > 30: g['city'] -= 1
            else: g['time'] -= 1
            continue
        notes(cv, T, g, y + 14 + min(spare // 3, 24), spec['notes'])
        bottom_and_url(cv, T, g)
        cv.geo.update(panel=panel_rect(g, y_panel, W), band_y=g['band_y'], hdr_y=g['hdr_y'])
        c = compose(cv, concept, spec['variant'], T, fmt, out, spec['id'])
        return dict(row=g['row'], city=g['city'], time=g['time'], contrast=round(c, 2))
    raise Overflow((spec['id'], fmt))


# ------------------------------------------------------------------ international card
LI = {  # starting sizes; they shrink until everything fits (never below 30 px)
    '4x5': dict(city=34, time=40, row=58), '1x1': dict(city=36, time=42, row=62), '9x16': dict(city=36, time=42, row=60),
}


def render_intl(spec, fmt, out, concept=BG.DEFAULT):
    """spec['sections'] = [dict(label, cols=[dict(key, head, sub, color)], rows=[dict(name, st, t)], layout)]
    layout 'halves' (2 columns, shown like the US card) or 'full' (3-4 columns, two-line heads).
    Sizes start large and shrink until it fits (never below 30 px); spare height then grows the rows (max +12 px)
    and the rest becomes air between the sections (max +22 px when a slide has 5 rows or fewer)."""
    W, H = FMT[fmt]; g = dict(L[fmt]); g.update(LI[fmt]); T = theme(concept, spec['tone'], spec['variant'])
    limit = (g['band_y'] - 34) if g['url_in_band'] else 1620 - 50
    gap, phase = 0, 'fit'
    nrows = sum(((len(sc['rows']) + 1) // 2) if sc['layout'] == 'halves' else len(sc['rows']) for sc in spec['sections'])
    for attempt in range(80):
        cv = Canvas(W, H)
        y = header(cv, T, g, spec['lock1'], spec['lock2'])
        y = title_block(cv, T, g, y + g['top_gap'] + 8, spec)
        y_panel = y + 2
        y = y_panel + (6 if fmt == '1x1' else PANEL_PAD - 4)
        if spec.get('legend'):
            y = legend(cv, T, g, y, spec['legend'])
        y += 6
        try:
            for si, sec in enumerate(spec['sections']):
                y = section_label(cv, T, g, y + (gap if si else gap // 2), sec['label'])
                if sec['layout'] == 'halves':
                    rows = [dict(r, st='') for r in sec['rows']] if sec.get('no_cc') else sec['rows']
                    h = (len(rows) + 1) // 2
                    sub = dict(id=spec['id'], cols=sec['cols'], halves=[rows[:h], rows[h:]],
                               city_head=['CITY', 'CITY'])
                    y, dropped = table(cv, T, g, y, sub, final=False)
                    if sub.get('too_long'):
                        raise Overflow('dropped')
                    if dropped:       # country codes do not fit: drop them for the whole section (consistent)
                        sec['no_cc'] = True
                        raise Overflow('retry')
                else:
                    y = table_full(cv, T, g, y, sec)
            y = notes(cv, T, g, y + 14 + gap // 2, spec['notes'])
        except Overflow as e:
            if e.args and e.args[0] == 'retry':
                continue
            if e.args and e.args[0] != 'dropped':
                raise
            y = limit + 1
        if y > limit:
            if phase == 'grow':           # grew too far: step back and stop growing
                g['row'] -= 3; phase = 'gap'; continue
            g['row'] -= 2
            if g['row'] < max(g['city'], g['time']) * 1.16:
                g['city'] -= 1; g['time'] -= 1; g['row'] = int(g['time'] * 1.3)
            if min(g['city'], g['time']) < MIN_PX:
                raise Overflow((spec['id'], fmt, 'intl'))
            gap = 0
            continue
        spare = limit - y
        if phase == 'fit':
            add = min(12 if nrows > 5 else 22, int(spare * 0.5 / max(1, nrows)))
            phase = 'grow'
            if add >= 2:
                g['row'] += add; continue
        if phase == 'grow':
            phase = 'gap'
        if phase == 'gap':
            phase = 'done'
            gap = min(48, int(spare / (len(spec['sections']) + 1)))
            if gap > 4:
                continue
        bottom_and_url(cv, T, g)
        cv.geo.update(panel=panel_rect(g, y_panel, W), band_y=g['band_y'], hdr_y=g['hdr_y'])
        c = compose(cv, concept, spec['variant'], T, fmt, out, spec['id'])
        return dict(row=g['row'], city=g['city'], time=g['time'], contrast=round(c, 2))
    raise Overflow((spec['id'], fmt, 'intl'))
