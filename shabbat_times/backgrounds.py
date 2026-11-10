# -*- coding: utf-8 -*-
"""Procedural backgrounds for the Aleph Brick Shabbat / Yom Tov / Fast times graphics (Pillow + numpy, no paid
tools, no stock). Four concepts, each with seasonal variants:

  dusk   (a) warm dusk sky over a brick-built Jerusalem Old City skyline (walls, towers, flat-roofed houses,
             cypresses; no domes, spires or minarets), lit windows, first stars
  table  (b) Shabbat table, soft-blurred: brick candlesticks with glowing candles, velvet challah cover, wine cup
  night  (c) deep navy night sky, star field, three bright stars (nightfall) and a gold studded-brick border
  stone  (d) Jerusalem-stone ashlar wall with drafted margins, parchment noise and a faint stud pattern

Variants: shabbat, chanukah, sukkot, simchat_torah, pesach, shavuot, rosh_hashanah, yom_kippur, fast, tisha_bav.
Rules kept: objects and places only. No people, no faces, no crosses or plus-shaped windows (windows are plain
arched slots), no domes/spires/minarets, no seven-branch menorah (the Chanukah variant draws a 9-light chanukiah:
8 lights in a row + raised shamash). Every scene is deterministic (fixed seeds), so re-runs are byte-stable.

API: scene(concept, variant, W, H, geo) -> RGB image.  geo = dict(fmt, panel=(x0,y0,x1,y1), band_y, avoid=[boxes])
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CONCEPTS = ['dusk', 'table', 'night', 'stone']
DEFAULT = 'dusk'
GOLD = (236, 190, 64)


# ------------------------------------------------------------------ numpy helpers
def vgrad(W, H, stops, y0=0, y1=None):
    """Vertical gradient. stops: [(t, (r,g,b))], t in 0..1 between y0 and y1."""
    y1 = H if y1 is None else y1
    t = (np.arange(H, dtype=np.float32) - y0) / max(1, (y1 - y0))
    t = np.clip(t, 0, 1)
    ts = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    col = np.stack([np.interp(t, ts, cs[:, k]) for k in range(3)], -1)
    return np.repeat(col[:, None, :], W, axis=1)


def radial(arr, cx, cy, rx, ry, color, strength):
    H, W, _ = arr.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    arr += (np.array(color, np.float32) - arr) * a[..., None]
    return arr


def noise(W, H, cell, seed, octaves=3):
    rng = np.random.default_rng(seed)
    out = np.zeros((H, W), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        c = max(2, int(cell / (2 ** o)))
        small = rng.random((H // c + 3, W // c + 3)).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize(((W // c + 3) * c, (H // c + 3) * c), Image.BICUBIC)
        out += np.asarray(im, np.float32)[:H, :W] / 255.0 * amp
        tot += amp; amp *= 0.5
    return out / tot


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')


def overlaps(box, avoid, pad=6):
    x0, y0, x1, y1 = box
    for a in avoid:
        if x0 < a[2] + pad and x1 > a[0] - pad and y0 < a[3] + pad and y1 > a[1] - pad:
            return True
    return False


def add_layer(img, layer):
    base = img.convert('RGBA'); base.alpha_composite(layer); return base.convert('RGB')


def glow_spot(layer, cx, cy, r, color, alpha):
    W, H = layer.size
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.55))
    g = Image.new('RGBA', (W, H), color + (0,)); g.putalpha(m)
    layer.alpha_composite(g)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ------------------------------------------------------------------ palettes per variant (sky / city / accents)
SKY = {
    'shabbat':       [(0, (14, 22, 52)), (.42, (40, 36, 88)), (.78, (104, 52, 96)), (1, (178, 86, 84))],
    'chanukah':      [(0, (10, 18, 46)), (.5, (28, 34, 82)), (.85, (74, 50, 100)), (1, (130, 70, 92))],
    'sukkot':        [(0, (16, 28, 56)), (.45, (40, 46, 86)), (.8, (90, 56, 72)), (1, (150, 92, 62))],
    'simchat_torah': [(0, (16, 26, 60)), (.45, (44, 44, 100)), (.8, (102, 58, 104)), (1, (164, 86, 92))],
    'pesach':        [(0, (12, 24, 58)), (.45, (34, 50, 104)), (.8, (82, 72, 128)), (1, (150, 104, 132))],
    'shavuot':       [(0, (8, 28, 48)), (.45, (16, 50, 66)), (.8, (36, 72, 72)), (1, (118, 118, 84))],
    'rosh_hashanah': [(0, (22, 14, 38)), (.5, (54, 22, 52)), (.85, (100, 38, 54)), (1, (160, 88, 52))],
    'yom_kippur':    [(0, (14, 22, 42)), (.5, (36, 48, 76)), (.85, (74, 88, 116)), (1, (112, 124, 148))],
    'fast':          [(0, (20, 26, 38)), (.5, (38, 46, 60)), (.85, (62, 70, 84)), (1, (88, 94, 106))],
    'tisha_bav':     [(0, (14, 18, 26)), (.5, (28, 32, 42)), (.85, (46, 50, 60)), (1, (64, 68, 78))],
}
CITY = {  # far houses, near wall, mortar/highlight
    'warm': ((44, 34, 70), (24, 22, 46)), 'cool': ((40, 46, 72), (22, 28, 48)),
    'fast': ((40, 46, 58), (26, 30, 40)), 'dark': ((30, 34, 42), (18, 20, 26)),
}
LIT = (255, 196, 110)


def city_tone(v):
    return {'fast': 'fast', 'tisha_bav': 'dark', 'yom_kippur': 'cool', 'pesach': 'cool', 'shavuot': 'cool'}.get(v, 'warm')


def festive(v):
    return v not in ('fast', 'tisha_bav', 'yom_kippur')


# ------------------------------------------------------------------ brick primitives
def brick_rect(d, x0, y0, x1, y1, col, hl=True):
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=mix(col, (0, 0, 0), .38))          # mortar
    d.rectangle((x0 + 1, y0, x1 - 2, y1 - 2), fill=col)
    if hl:
        d.line((x0 + 2, y0, x1 - 4, y0), fill=mix(col, (255, 255, 255), .12))


def brick_course(d, x0, x1, y, bh, bw, col, offset=0, hl=True):
    x = x0 - (offset % bw)
    while x < x1:
        a, b = max(x0, x), min(x1, x + bw)
        if b - a > 3:
            brick_rect(d, a, y, b, y + bh, col, hl)
        x += bw


def brick_block(d, x0, y0, x1, y1, col, bw=30, bh=15, studs=True, hl=True):
    """A solid block built from staggered bricks, optional studs on top."""
    y = y1 - bh; k = 0
    while y >= y0 - 1:
        brick_course(d, x0, x1, y, bh, bw, col, offset=(bw // 2) * (k % 2), hl=hl)
        y -= bh; k += 1
    if studs:
        stud_row(d, x0, x1, y + bh, col, bw)


def stud_row(d, x0, x1, ytop, col, bw=30):
    sw, sh = max(6, bw * 0.42), max(3, bw * 0.16)
    x = x0 + (bw - sw) / 2
    while x + sw <= x1 + 1:
        d.rounded_rectangle((x, ytop - sh, x + sw, ytop + 1), 2, fill=col)
        d.line((x + 2, ytop - sh + 1, x + sw * .4, ytop - sh + 1), fill=mix(col, (255, 255, 255), .16))
        x += bw


def arched_window(d, x, y, w, h, col):
    """Plain arched slot window (no mullions, never cross-shaped)."""
    d.rectangle((x, y + w / 2, x + w, y + h), fill=col)
    d.pieslice((x, y, x + w, y + w), 180, 360, fill=col)


# ------------------------------------------------------------------ (a) dusk skyline
def skyline(img, x0, x1, ground, scale, variant, avoid, seed=7, far=True, gate=True):
    """Brick-built Old City skyline standing on y=ground: hills, dusk-lit far houses (flat roofs, studs, arched lit
    windows), cypresses, and a dark crenellated city wall with four towers. No domes, spires or minarets."""
    d = ImageDraw.Draw(img)
    tone = CITY[city_tone(variant)]
    horizon_col = SKY[variant][-1][1]
    far_col = mix(tone[0], horizon_col, .22)
    rim = mix(horizon_col, (255, 214, 160), .35)
    bw, bh = int(30 * scale), int(15 * scale)
    rng = np.random.default_rng(seed)
    lit = festive(variant) or variant == 'yom_kippur'
    win = LIT if variant != 'yom_kippur' else (226, 230, 242)
    ruins = variant == 'tisha_bav'
    # distant hills
    pts = [(x0, ground)]
    for i in range(0, 41):
        x = x0 + (x1 - x0) * i / 40
        y = ground - bh * (6.2 + 1.8 * math.sin(i * .45 + 1.3) + .9 * math.sin(i * 1.3))
        pts.append((x, y))
    pts.append((x1, ground))
    d.polygon(pts, fill=mix(far_col, horizon_col, .30))
    if far:
        x = x0 - int(rng.integers(0, bw))
        while x < x1:
            w = bw * int(rng.integers(2, 5)); h = bh * int(rng.integers(5, 9))
            if ruins:
                h = int(h * .75)
            brick_block(d, x, ground - h, x + w, ground, far_col, bw, bh, studs=True)
            if not overlaps((x, ground - h - 3, x + w, ground - h + 3), avoid, 4):
                d.line((x, ground - h, x + w - 2, ground - h), fill=rim, width=2)      # warm rim light on the roof
            if lit:
                for wx in range(int(x + bw * .45), int(x + w - bw * .6), int(bw * 1.1)):
                    for wy in range(int(ground - h + bh * 1.2), int(ground - bh * 4.6), int(bh * 2.2)):
                        box = (wx, wy, wx + bw * .38, wy + bh * 1.1)
                        if rng.random() < .5 and not overlaps(box, avoid, 10):
                            arched_window(d, box[0], box[1], bw * .38, bh * 1.1, win)
            x += w + bw * int(rng.integers(0, 2))
        for cx in rng.integers(x0 + 40, x1 - 40, 8):          # cypress trees
            th = bh * rng.uniform(6.5, 9.5); tw_ = bw * .6
            d.ellipse((cx - tw_ / 2, ground - th, cx + tw_ / 2, ground - bh * 3), fill=mix(tone[1], (16, 52, 40), .55))
    # near wall with crenellations
    near = tone[1]
    wall_h = bh * 4
    brick_block(d, x0, ground - wall_h, x1, ground, near, bw, bh, studs=False)
    x = x0
    while x < x1:
        if not (ruins and rng.random() < .45):
            brick_block(d, x, ground - wall_h - bh, x + bw, ground - wall_h, near, bw, bh, studs=True)
        x += bw * 2
    W = x1 - x0
    for fx_, n_w, n_h in ((0.04, 4, 9), (0.22, 3, 7), (0.78, 3, 7), (0.96, 4, 10)):
        tx = int(x0 + W * fx_ - n_w * bw / 2); tw_ = n_w * bw; th = n_h * bh
        if ruins:
            th = int(th * .7)
        brick_block(d, tx, ground - th, tx + tw_, ground, near, bw, bh, studs=False)
        for m in range(n_w):
            if m % 2 == 0 and not (ruins and m == 2):
                brick_block(d, tx + m * bw, ground - th - bh, tx + (m + 1) * bw, ground - th, near, bw, bh, studs=True)
        if lit:
            box = (tx + tw_ / 2 - bw * .25, ground - th + bh * 1.5, tx + tw_ / 2 + bw * .25, ground - th + bh * 3.2)
            if not overlaps(box, avoid, 10):
                arched_window(d, box[0], box[1], bw * .5, bh * 1.7, win)
    if gate:   # arched gate in the middle of the wall
        gx = x0 + W * .5 - bw
        dark = mix(near, (0, 0, 0), .5)
        d.rectangle((gx, ground - bh * 2.2, gx + 2 * bw, ground), fill=dark)
        d.pieslice((gx, ground - bh * 2.2 - bw, gx + 2 * bw, ground - bh * 2.2 + bw), 180, 360, fill=dark)
    if ruins:  # missing bricks in the wall face
        for _ in range(9):
            mx_ = int(rng.integers(x0, x1 - bw)); my_ = int(ground - bh * rng.integers(1, 4))
            d.rectangle((mx_, my_, mx_ + bw - 2, my_ + bh - 2), fill=mix(near, (0, 0, 0), .45))


def stars(img, x0, y0, x1, y1, n, seed, avoid, bright=1.0, big=0):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.choice([0.9, 1.2, 1.5, 2.0], p=[.45, .3, .17, .08])
        a = int(rng.uniform(90, 230) * bright)
        if overlaps((x - 3, y - 3, x + 3, y + 3), avoid, 4):
            continue
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 250, 235, a))
    for i in range(big):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if overlaps((x - 14, y - 14, x + 14, y + 14), avoid, 8):
            continue
        glow_spot(layer, x, y, 12, (255, 236, 190), int(150 * bright))
        ImageDraw.Draw(layer).ellipse((x - 2.6, y - 2.6, x + 2.6, y + 2.6), fill=(255, 252, 240, int(255 * bright)))
    return add_layer(img, layer)


def scene_dusk(W, H, geo, v):
    p = geo['panel']; fmt = geo['fmt']
    story = fmt == '9x16'
    horizon = (geo['band_y'] if story else p[1] + 6)
    arr = vgrad(W, H, SKY[v], 0, horizon)
    n = noise(W, H, 180, 11, 3)
    arr += (n[..., None] - .5) * 10                       # soft cloud texture
    if festive(v):
        radial(arr, W * .5, horizon, W * .75, (horizon) * .55, SKY[v][-1][1], .55)
    img = to_img(arr)
    avoid = geo['avoid']
    img = stars(img, 0, 0, W, horizon * .55, 130 if v != 'tisha_bav' else 50, 3, avoid,
                bright=1.0 if festive(v) else .55, big=3 if festive(v) else 1)
    if v == 'pesach':
        mx, my = geo.get('moon_xy', (W * .72, horizon * .3))
        img = moon(img, mx, my, 34 if not story else 60, avoid)
    skyline(img, -10, W + 10, horizon, 1.0 if not story else 1.25, v, avoid, seed=7, gate=story)
    if not story:
        # the panel hides the ground: a dark gradient continues under the translucent panel
        tone = CITY[city_tone(v)]
        g = vgrad(W, H - horizon, [(0, tone[1]), (1, mix(tone[1], (0, 0, 0), .5))])
        img.paste(to_img(g), (0, horizon))
    return img


def moon(img, cx, cy, r, avoid):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    glow_spot(layer, cx, cy, r * 2.2, (255, 240, 200), 120)
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 244, 222, 255))
    for (dx, dy, rr) in ((-.3, -.2, .22), (.25, .15, .16), (-.05, .35, .12)):
        d.ellipse((cx + dx * r - rr * r, cy + dy * r - rr * r, cx + dx * r + rr * r, cy + dy * r + rr * r), fill=(236, 228, 204, 255))
    return add_layer(img, layer)


# ------------------------------------------------------------------ (b) Shabbat table
def candlestick(d, layer, cx, base, h, s, flame_on=True, glow_r=120):
    """Gold brick candlestick (stacked studded bricks) holding a white candle."""
    g1, g2, g3 = (196, 146, 40), (232, 186, 70), (150, 108, 30)
    bw = 26 * s
    # foot
    d.rounded_rectangle((cx - 60 * s, base - 22 * s, cx + 60 * s, base), 6, fill=g1)
    d.rectangle((cx - 56 * s, base - 20 * s, cx + 56 * s, base - 15 * s), fill=g2)
    # stem of stacked bricks
    y = base - 22 * s; k = 0
    while y > base - h * .62:
        w = (34 if k % 2 else 28) * s
        d.rectangle((cx - w, y - 18 * s, cx + w, y - 1), fill=g1 if k % 2 else g3)
        d.line((cx - w + 2, y - 17 * s, cx + w * .2, y - 17 * s), fill=g2, width=max(1, int(2 * s)))
        y -= 18 * s; k += 1
    # cup
    d.rounded_rectangle((cx - 44 * s, y - 22 * s, cx + 44 * s, y), 6, fill=g2)
    for sx in (-24, 0, 24):
        d.rounded_rectangle((cx + (sx - 8) * s, y - 30 * s, cx + (sx + 8) * s, y - 20 * s), 3, fill=g2)
    # candle
    top = base - h
    d.rectangle((cx - bw / 2, top, cx + bw / 2, y - 22 * s), fill=(250, 247, 238))
    d.rectangle((cx + bw / 2 - 6 * s, top, cx + bw / 2, y - 22 * s), fill=(222, 216, 204))
    d.line((cx, top - 12 * s, cx, top), fill=(50, 40, 30), width=max(2, int(3 * s)))
    if flame_on:
        glow_spot(layer, cx, top - 34 * s, glow_r, (255, 190, 90), 150)
        fd = ImageDraw.Draw(layer)
        for k, col in ((1.0, (246, 150, 40, 255)), (.66, (255, 206, 80, 255)), (.34, (255, 246, 214, 255))):
            r = 13 * s * k; fy = top - 14 * s - r
            fd.ellipse((cx - r, fy - r, cx + r, fy + r), fill=col)
            fd.polygon([(cx - r * .95, fy - r * .2), (cx, fy - r - 34 * s * k), (cx + r * .95, fy - r * .2)], fill=col)


def scene_table(W, H, geo, v):
    p = geo['panel']; story = geo['fmt'] == '9x16'
    edge = p[1] + 40 if not story else int(H * .52)
    wall = {'shabbat': ((70, 22, 30), (34, 12, 18)), 'yom_kippur': ((44, 48, 66), (22, 24, 34)),
            'fast': ((46, 46, 54), (24, 24, 30)), 'tisha_bav': ((32, 32, 38), (16, 16, 20))}.get(
        v, ((60, 24, 40), (28, 12, 22)))
    arr = vgrad(W, H, [(0, wall[1]), (.7, wall[0]), (1, mix(wall[0], (0, 0, 0), .2))], 0, edge)
    n = noise(W, H, 90, 5, 2); arr += (n[..., None] - .5) * 12
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # faint damask of studs on the wall
    for y in range(20, edge, 56):
        for x in range(20 + (28 if (y // 56) % 2 else 0), W, 56):
            d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=mix(wall[0], (255, 220, 160), .10), width=2)
    # table: white cloth with a lace edge
    d.rectangle((0, edge, W, H), fill=(236, 230, 218))
    for x in range(0, W, 28):
        d.ellipse((x, edge - 8, x + 28, edge + 14), fill=(244, 240, 230))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    s = 1.0 if not story else 1.35
    on = v not in ('fast', 'tisha_bav')
    if story:
        xs, base, h = (W * .16, W * .84), edge + 60 * s, int(330 * s)
    else:   # stand the candlesticks in the free zones beside the title, flames below the header
        fz = geo['free'] or [(30, 0, 250, 0), (W - 250, 0, W - 30, 0)]
        xs = ((fz[0][0] + fz[0][2]) / 2, (fz[1][0] + fz[1][2]) / 2)
        base = edge + 60; h = int(base - (geo.get('hdr_bottom', 130) + 115))
    for x in xs:
        candlestick(d, layer, int(x), base, h, s, on, glow_r=(56 if not story else 110) * s)
    if on:
        # challah under a velvet cover (deep blue, gold border at the edges only)
        cx = W * .5; cw, ch = 300 * s, 120 * s; cy0 = edge - ch * .55
        d.rounded_rectangle((cx - cw / 2, cy0, cx + cw / 2, cy0 + ch), 28, fill=(28, 40, 96))
        d.rounded_rectangle((cx - cw / 2, cy0, cx + cw / 2, cy0 + ch), 28, outline=(214, 170, 70), width=int(5 * s))
        for k in range(-5, 6):  # fringe
            d.line((cx + k * cw / 11, cy0 + ch, cx + k * cw / 11, cy0 + ch + 14 * s), fill=(214, 170, 70), width=3)
        # wine cup (silver, studded rim), only where no text sits above it
        wx = W * .68; wy = edge + 20 * s
    if on and not overlaps((wx - 40 * s, wy - 130 * s, wx + 40 * s, wy), geo['avoid'], 30):
        d.polygon([(wx - 34 * s, wy - 120 * s), (wx + 34 * s, wy - 120 * s), (wx + 22 * s, wy - 64 * s), (wx - 22 * s, wy - 64 * s)], fill=(196, 200, 210))
        d.rectangle((wx - 6 * s, wy - 64 * s, wx + 6 * s, wy - 18 * s), fill=(176, 180, 190))
        d.rounded_rectangle((wx - 30 * s, wy - 20 * s, wx + 30 * s, wy), 6, fill=(186, 190, 200))
        d.rectangle((wx - 30 * s, wy - 112 * s, wx + 30 * s, wy - 96 * s), fill=(120, 20, 40))
    img = add_layer(img, layer)
    img = img.filter(ImageFilter.GaussianBlur(6 if not story else 7))
    # bokeh
    bl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rng = np.random.default_rng(21)
    if on:
        for _ in range(16):
            x, y = rng.uniform(0, W), rng.uniform(0, edge * .9)
            if overlaps((x - 30, y - 30, x + 30, y + 30), geo['avoid'], 6):
                continue
            glow_spot(bl, x, y, rng.uniform(14, 34), (255, 206, 130), int(rng.uniform(40, 90)))
    return add_layer(img, bl)


# ------------------------------------------------------------------ (c) night sky + gold brick border
def gold_border(img, geo, col=(214, 170, 60)):
    d = ImageDraw.Draw(img); W, H = img.size
    t = 16; bw = 44
    bottom = geo['band_y']
    for y in (0,):
        brick_course(d, 0, W, y, t, bw, col, 0)
    x = 0
    yy = t
    while yy < bottom:
        h = min(bw, bottom - yy)
        brick_rect(d, 0, yy, t, yy + h, col); brick_rect(d, W - t, yy, W, yy + h, col)
        yy += bw
    stud_row(d, t, W - t, t + 7, col, bw)


def scene_night(W, H, geo, v):
    p = geo['panel']
    arr = vgrad(W, H, [(0, (8, 16, 40)), (.6, (14, 30, 66)), (1, (20, 40, 84))])
    if v in ('fast', 'tisha_bav'):
        arr = vgrad(W, H, [(0, (14, 18, 28)), (1, (34, 40, 54))])
    radial(arr, W * .5, H * .12, W * .8, H * .35, (40, 64, 120) if festive(v) else (50, 56, 70), .35)
    n = noise(W, H, 260, 9, 3)
    band = np.exp(-((np.arange(W)[None, :] - W * .3 - np.arange(H)[:, None] * .35) / 260.0) ** 2)
    arr += (n * band)[..., None] * np.array([30, 34, 50], np.float32) * (1 if festive(v) else .4)
    img = to_img(arr)
    img = stars(img, 18, 18, W - 18, H - 18, 520, 4, geo['avoid'], bright=1.0 if festive(v) else .5, big=0)
    # three bright stars (nightfall) in a free top area
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    for (x, y) in geo.get('three_stars', []):
        glow_spot(lay, x, y, 16, (255, 236, 190), 170 if festive(v) else 90)
        ImageDraw.Draw(lay).ellipse((x - 3.2, y - 3.2, x + 3.2, y + 3.2), fill=(255, 252, 240, 255))
    img = add_layer(img, lay)
    gold_border(img, geo, (214, 170, 60) if festive(v) else (128, 120, 100))
    return img


# ------------------------------------------------------------------ (d) Jerusalem stone
def scene_stone(W, H, geo, v):
    base = {'fast': (198, 196, 190), 'tisha_bav': (170, 168, 164), 'yom_kippur': (226, 224, 218)}.get(v, (228, 212, 182))
    arr = np.ones((H, W, 3), np.float32) * np.array(base, np.float32)
    n1 = noise(W, H, 40, 31, 4); n2 = noise(W, H, 6, 32, 1)
    arr += (n1[..., None] - .5) * 26 + (n2[..., None] - .5) * 10
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(17)
    ch = 92; y = -20; row = 0
    joint = mix(base, (60, 50, 40), .24); draft = mix(base, (255, 255, 255), .22); shade = mix(base, (0, 0, 0), .10)
    while y < H:
        x = -int(rng.integers(0, 160))
        while x < W:
            w = int(rng.integers(150, 290))
            d.rectangle((x, y, x + w, y + ch), outline=joint, width=3)
            d.rectangle((x + 10, y + 10, x + w - 10, y + ch - 10), outline=draft, width=3)    # drafted margin
            d.rectangle((x + 13, y + ch - 14, x + w - 10, y + ch - 10), fill=shade)
            x += w
        y += ch; row += 1
    # faint stud pattern (brand texture)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for yy in range(30, H, 60):
        for xx in range(30, W, 60):
            ld.ellipse((xx - 12, yy - 12, xx + 12, yy + 12), outline=(255, 255, 255, 34), width=2)
    img = add_layer(img, lay)
    arr = np.asarray(img, np.float32)
    radial(arr, W * .5, 0, W * .9, H * .45, (255, 236, 200) if festive(v) else base, .25)
    # warm vignette edges
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = np.clip(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2, 0, 1)
    arr *= (1 - .18 * vig * np.clip((yy / H - .35) * 2, 0, 1))[..., None]   # vignette on the lower part only
    return to_img(arr)


# ------------------------------------------------------------------ seasonal props (drawn in free zones)
def leaf(d, x, y, ang, L, col):
    a = math.radians(ang); dx, dy = math.cos(a) * L, math.sin(a) * L
    nx, ny = -dy * .28, dx * .28
    d.polygon([(x, y), (x + dx * .5 + nx, y + dy * .5 + ny), (x + dx, y + dy), (x + dx * .5 - nx, y + dy * .5 - ny)], fill=col)


def flower5(d, x, y, r, petal, centre):
    for k in range(5):
        a = math.radians(k * 72 - 90)
        px, py = x + math.cos(a) * r * .62, y + math.sin(a) * r * .62
        d.ellipse((px - r * .5, py - r * .5, px + r * .5, py + r * .5), fill=petal)
    d.ellipse((x - r * .3, y - r * .3, x + r * .3, y + r * .3), fill=centre)


def pomegranate(d, x, y, r):
    d.ellipse((x - r, y - r, x + r, y + r), fill=(176, 28, 44))
    d.ellipse((x - r * .55, y - r * .7, x - r * .05, y - r * .25), fill=(214, 70, 80))
    for k in (-1, 0, 1):   # crown
        d.polygon([(x + k * r * .28 - r * .14, y - r * .86), (x + k * r * .28, y - r * 1.25), (x + k * r * .28 + r * .14, y - r * .86)], fill=(150, 22, 36))


def apple(d, x, y, r):
    d.ellipse((x - r, y - r * .9, x + r, y + r), fill=(200, 36, 40))
    d.ellipse((x - r * .55, y - r * .55, x - r * .1, y - r * .15), fill=(236, 96, 90))
    d.line((x, y - r * .9, x + r * .15, y - r * 1.35), fill=(80, 50, 20), width=max(2, int(r * .12)))
    leaf(d, x + r * .12, y - r * 1.1, -20, r * .8, (70, 140, 60))


def chanukiah(img, cx, base, s):
    """Nine-light chanukiah built from bricks: 8 lights in a row and a raised shamash. Never 7 branches."""
    d = ImageDraw.Draw(img); lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    g1, g2 = (214, 164, 44), (246, 206, 96)
    bw = 16 * s; gap = 6 * s
    total = 9 * bw + 8 * gap
    x0 = cx - total / 2
    d.rectangle((cx - total / 2 - 6 * s, base - 14 * s, cx + total / 2 + 6 * s, base), fill=g1)
    d.rectangle((cx - total / 2 - 6 * s, base - 14 * s, cx + total / 2 + 6 * s, base - 10 * s), fill=g2)
    d.rectangle((cx - 10 * s, base, cx + 10 * s, base + 40 * s), fill=g1)
    d.rectangle((cx - 40 * s, base + 40 * s, cx + 40 * s, base + 52 * s), fill=g1)
    for i in range(9):
        x = x0 + i * (bw + gap)
        h = 46 * s if i == 4 else 28 * s           # middle light raised = shamash
        d.rectangle((x, base - 14 * s - h, x + bw, base - 14 * s), fill=g1)
        d.rectangle((x + 2, base - 14 * s - h, x + 5 * s, base - 14 * s - 2), fill=g2)
        fx, fy = x + bw / 2, base - 14 * s - h - 12 * s
        glow_spot(lay, fx, fy, 22 * s, (255, 190, 90), 140)
        fd = ImageDraw.Draw(lay)
        for k, col in ((1.0, (246, 150, 40, 255)), (.55, (255, 236, 170, 255))):
            r = 6 * s * k
            fd.ellipse((fx - r, fy - r + 4 * s, fx + r, fy + r + 4 * s), fill=col)
            fd.polygon([(fx - r, fy + 4 * s), (fx, fy - 12 * s * k), (fx + r, fy + 4 * s)], fill=col)
    return add_layer(img, lay)


class _Guard:
    """ImageDraw wrapper that silently skips any shape whose box touches a text box."""
    def __init__(self, d, avoid, pad=10):
        self.d, self.avoid, self.pad = d, avoid, pad

    def _ok(self, xy):
        if len(xy) == 4 and not isinstance(xy[0], (tuple, list)):
            box = xy
        else:
            pts = list(xy); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; box = (min(xs), min(ys), max(xs), max(ys))
        return not overlaps(box, self.avoid, self.pad)

    def __getattr__(self, name):
        fn = getattr(self.d, name)
        def wrapped(xy, *a, **k):
            if self._ok(xy):
                fn(xy, *a, **k)
        return wrapped


def props(img, v, geo):
    """Seasonal decoration in the free zones left/right of the title (zones from geo['free']).
    Every shape is checked against the text boxes, so a prop can never sit behind text."""
    W, H = img.size
    zones = geo['free']          # [(x0,y0,x1,y1) left, right]
    if not zones:
        return img
    d = _Guard(ImageDraw.Draw(img), geo['avoid'])
    s = geo.get('prop_s', 1.0)
    L, R = zones
    if v == 'chanukah':
        cs = min(1.0 * s, (R[2] - R[0] - 20) / 200.0)
        if cs >= .6:
            cx_, base_ = (R[0] + R[2]) / 2, R[3] - 56 * cs
            box = (cx_ - 115 * cs, base_ - 80 * cs, cx_ + 115 * cs, base_ + 52 * cs)
            if not overlaps(box, geo['avoid'], 8):
                img = chanukiah(img, cx_, base_, cs)
    elif v in ('sukkot', 'simchat_torah'):
        # schach (green branches) along the very top edge + hanging fruit in the free zones
        for x in range(-10, W + 10, 18):
            leaf(d, x, 4, 70 + (x * 37) % 40, 34, (52, 110, 54) if (x // 18) % 2 else (74, 136, 64))
        d.rectangle((0, 0, W, 6), fill=(110, 80, 46))
        for z, seed in ((L, 1), (R, 2)):
            xs = np.linspace(z[0] + 30 * s, z[2] - 30 * s, 3)
            for i, x in enumerate(xs):
                y = z[1] + 40 * s + (i % 2) * 34 * s
                d.line((x, z[1], x, y - 16 * s), fill=(200, 180, 140), width=2)
                if v == 'simchat_torah':
                    col = [(196, 18, 30), GOLD, (40, 90, 170)][i % 3]
                    d.polygon([(x - 18 * s, y - 16 * s), (x + 18 * s, y - 16 * s), (x, y + 22 * s)], fill=col)
                else:
                    [pomegranate, apple, pomegranate][i % 3](d, x, y, 15 * s)
    elif v == 'pesach':      # a straight spring (almond) branch with blossoms along it
        for z, sgn in ((L, 1), (R, -1)):
            x0, y0 = (z[0] + 16 * s, z[3] - 14 * s) if sgn > 0 else (z[2] - 16 * s, z[3] - 14 * s)
            x1, y1 = (z[2] - 24 * s, z[3] - 70 * s) if sgn > 0 else (z[0] + 24 * s, z[3] - 70 * s)
            d.line((x0, y0, x1, y1), fill=(96, 64, 52), width=int(4 * s))
            for k in range(1, 7):
                t = k / 7.0; off = (9 if k % 2 else -9) * s
                flower5(d, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + off, 12 * s, (250, 224, 232), (220, 120, 140))
    elif v == 'shavuot':
        for x in range(-10, W + 10, 22):     # leafy garland along the top
            leaf(d, x, 2, 60 + (x * 13) % 60, 30, (60, 132, 70) if (x // 22) % 2 else (90, 160, 80))
        for z in (L, R):
            rng = np.random.default_rng(int(z[0]))
            for k in range(6):
                x = rng.uniform(z[0] + 20 * s, z[2] - 20 * s); y = rng.uniform(z[1] + 30 * s, z[3] - 20 * s)
                leaf(d, x, y + 10 * s, 120, 26 * s, (70, 140, 70))
                flower5(d, x, y, 12 * s, [(250, 250, 250), (250, 214, 90), (238, 160, 190)][k % 3], (240, 190, 60))
    elif v == 'rosh_hashanah':
        for z in (L, R):
            cx = (z[0] + z[2]) / 2; by = z[3] - 26 * s
            pomegranate(d, cx - 34 * s, by - 6 * s, 24 * s)
            apple(d, cx + 30 * s, by, 22 * s)
            # honey drops
            for k, dx in enumerate((-60, 64)):
                d.ellipse((cx + dx * s - 7 * s, by - 40 * s, cx + dx * s + 7 * s, by - 26 * s), fill=(240, 176, 40))
    return img


# ------------------------------------------------------------------ entry point
SCENES = {'dusk': scene_dusk, 'table': scene_table, 'night': scene_night, 'stone': scene_stone}


def scene(concept, variant, W, H, geo):
    img = SCENES[concept](W, H, geo, variant)
    if concept != 'table' or variant in ('chanukah', 'sukkot', 'simchat_torah', 'pesach', 'shavuot', 'rosh_hashanah'):
        img = props(img, variant, geo)
    return img
