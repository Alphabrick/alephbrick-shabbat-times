# -*- coding: utf-8 -*-
"""Which posts exist, what times they show, and when they go out. Diaspora calendar via pyluach (offline).

Occasion kinds
  shabbat  : an ordinary Shabbat (Friday candles -> Saturday end)
  yomtov   : any run of consecutive Shabbat/Yom Tov days that contains a Yom Tov (incl. Yom Kippur)
  fast     : minor fasts (alot 16.1 deg -> tzeit 7.083 deg) and Tisha B'Av (sunset -> tzeit 6.45 deg)
Ta'anit Bechorot (firstborn only, usually a siyum) gets no graphic; it is mentioned in the erev Pesach caption.

Time rules for a run of restricted days D1..Dn (erev = D1 - 1):
  night before D1           : candle lighting = sunset - 18 (erev)
  night before Dk (k > 1)   : Shabbat after Yom Tov -> normal candle lighting (sunset - 18, from an existing flame)
                              otherwise ("second night")  -> candles AFTER tzeit 8.5 deg of D(k-1)
  end of Dn                 : tzeit 8.5 deg (Havdalah / Shabbat or Yom Tov ends)
"""
import datetime as dt
from zoneinfo import ZoneInfo
from pyluach import dates as hd, parshios
import zmanim as Z, names, cities as CT

ET = ZoneInfo('America/New_York')
SHABBAT_END_DEG = 8.5          # Hebcal default (M=on)
FAST_END_DEG = 7.083           # Hebcal minor fasts
FAST_END_DEG_IL = 3.7          # live Hebcal API, Israel cities, minor fasts (verified Jerusalem/Tel Aviv/Bnei Brak/Haifa, winter + summer)
TISHA_BAV_END_DEG = 6.45       # what the live Hebcal API returns for Tisha B'Av (verified Brooklyn/LA/Seattle 2027)
ALOT_DEG = 16.1
CANDLE_MIN = 18
BLACKOUT_HAVDALAH_MIN = 72     # brand rule: Havdalah per the 72-minute opinion for the posting pause
BLACKOUT_PAD_MIN = 60

POST_SHABBAT_ET = (8, 0)       # Friday / erev Yom Tov, 8:00 AM ET
POST_FALLBACK_ET = (8, 30)     # a fast post pulled in front of a Shabbat/Yom Tov pause
POST_FAST_EVE_ET = (20, 0)     # minor fast: the evening before, 8:00 PM ET
POST_TB_ET = (8, 0)            # Tisha B'Av: morning of erev Tisha B'Av


def g2d(g):
    return dt.date(g.year, g.month, g.day)


def d2g(d):
    return hd.GregorianDate(d.year, d.month, d.day)


def yomtov_name(d):
    return d2g(d).to_heb().festival(israel=False, include_working_days=False)


def festival_any(d):
    return d2g(d).to_heb().festival(israel=False, include_working_days=True)


def is_restricted(d):
    return d.weekday() == 5 or yomtov_name(d) is not None


def yomtov_name_il(d):
    return d2g(d).to_heb().festival(israel=True, include_working_days=False)


def is_restricted_il(d):
    return d.weekday() == 5 or yomtov_name_il(d) is not None


def fast_name(d):
    return d2g(d).to_heb().fast_day()


def heb_date_str(d):
    return d2g(d).to_heb().hebrew_date_string()


# ---------------------------------------------------------------- per-city times
def fmt(t):
    return t.strftime('%-I:%M')


def block_events(block, ytfn=None, prefix='c', endkey='end'):
    """Columns for a run of restricted days: list of (key, date, kind)."""
    ytfn = ytfn or yomtov_name
    ev = [('%s0' % prefix, block[0] - dt.timedelta(days=1), 'candles')]
    for k in range(1, len(block)):
        prev, day = block[k - 1], block[k]
        if day.weekday() == 5 and ytfn(prev):
            ev.append(('%s%d' % (prefix, k), prev, 'candles'))           # Friday Yom Tov into Shabbat
        else:
            ev.append(('%s%d' % (prefix, k), prev, 'candles_after'))     # second night: after nightfall
    ev.append((endkey, block[-1], 'end'))
    return ev


def israel_runs(block):
    """Israel-calendar restricted runs inside a Diaspora run (Israel days are a subset of Diaspora days)."""
    runs, cur = [], []
    for d in block:
        if is_restricted_il(d):
            cur.append(d)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return runs


def israel_events(block):
    """Israel columns for the same post: one set of candles/end per Israel run (keys i0.., ie0..)."""
    ev = []
    for n, run in enumerate(israel_runs(block)):
        ev += block_events(run, ytfn=yomtov_name_il, prefix='i%d_' % n, endkey='ie%d' % n)
    return ev


def israel_label(block):
    """(label_en, label_he, differs) describing what Israel keeps in this run, e.g. 'Pesach · Shabbat Chol HaMoed'."""
    parts_en, parts_he = [], []
    for run in israel_runs(block):
        yts = []
        for d in run:
            y = yomtov_name_il(d)
            if y and y not in yts:
                yts.append(y)
        if yts:
            for y in yts:
                en, he = names.HOLIDAY[y]
                if y == 'Shmini Atzeres':
                    en, he = 'Shemini Atzeret & Simchat Torah', 'שמיני עצרת · שמחת תורה'
                parts_en.append(en); parts_he.append(he)
        sat = [d for d in run if d.weekday() == 5]
        if sat and not yomtov_name_il(sat[0]):
            idx = parshios.getparsha(d2g(sat[0]), israel=True)
            if idx:
                en, he = names.parsha(idx)
            else:
                fest = festival_any_il(sat[0])
                en, he = names.CHOL_HAMOED_SHABBAT.get(fest, ('Shabbat', 'שבת'))
            parts_en.append(en); parts_he.append(he)
    dias_days = [yomtov_name(d) for d in block]
    il_days = [yomtov_name_il(d) for d in block]
    differs = dias_days != il_days
    for d in block:
        if d.weekday() == 5 and not yomtov_name(d) and not yomtov_name_il(d):
            if parshios.getparsha(d2g(d), israel=True) != parshios.getparsha(d2g(d), israel=False):
                differs = True
    return ' · '.join(parts_en), ' · '.join(parts_he), differs


def festival_any_il(d):
    return d2g(d).to_heb().festival(israel=True, include_working_days=True)


def time_for(kind, date, c):
    t = _time_for(kind, date, c)
    return t


def _time_for(kind, date, c):
    if kind == 'candles':
        return Z.candle_lighting(date, c, c.get('candle_min', CANDLE_MIN))
    if kind in ('candles_after', 'end'):
        return Z.tzeit(date, c, SHABBAT_END_DEG)
    if kind == 'fast_begin_alot':
        return Z.alot(date, c, ALOT_DEG)
    if kind == 'fast_begin_sunset':
        return Z.sunset_rounded(date, c)
    if kind == 'fast_end':
        return Z.tzeit(date, c, FAST_END_DEG_IL if c.get('israel') else FAST_END_DEG)
    if kind == 'fast_end_tb':
        return Z.tzeit(date, c, TISHA_BAV_END_DEG)
    raise ValueError(kind)


# ---------------------------------------------------------------- blackout (Brooklyn 11223)
def blackout_windows(start, end):
    """[(from, to)] in ET: candle lighting - 60 min .. sunset + 72 + 60 min, for every restricted run."""
    loc = CT.BLACKOUT_LOC
    out = []
    for blk in restricted_runs(start - dt.timedelta(days=3), end + dt.timedelta(days=3)):
        a = Z.candle_lighting(blk[0] - dt.timedelta(days=1), loc, CANDLE_MIN) - dt.timedelta(minutes=BLACKOUT_PAD_MIN)
        b = Z.sunset_plus(blk[-1], loc, BLACKOUT_HAVDALAH_MIN) + dt.timedelta(minutes=BLACKOUT_PAD_MIN)
        out.append((a.astimezone(ET), b.astimezone(ET)))
    return out


def in_blackout(t, windows):
    return any(a <= t <= b for a, b in windows)


def restricted_runs(start, end):
    runs, cur = [], []
    d = start
    while d <= end:
        if is_restricted(d):
            cur.append(d)
        elif cur:
            runs.append(cur); cur = []
        d += dt.timedelta(days=1)
    if cur:
        # finish a run that crosses `end`
        d = cur[-1] + dt.timedelta(days=1)
        while is_restricted(d):
            cur.append(d); d += dt.timedelta(days=1)
        runs.append(cur)
    return runs


def at_et(d, hm):
    return dt.datetime(d.year, d.month, d.day, hm[0], hm[1], tzinfo=ET)


# ---------------------------------------------------------------- titles
def block_title(block):
    yts = [yomtov_name(d) for d in block if yomtov_name(d)]
    has_shabbat = any(d.weekday() == 5 for d in block)
    if not yts:
        sat = block[0]
        idx = parshios.getparsha(d2g(sat), israel=False)
        if idx:
            en, he = names.parsha(idx)
            sub = 'Shabbat'
        else:
            fest = festival_any(sat)
            en, he = names.CHOL_HAMOED_SHABBAT.get(fest, ('Shabbat', 'שבת'))
            sub = 'Shabbat'
        return dict(title_en=en, title_he=he, kind='shabbat', sub=sub, yt=[], fast=False)
    uniq = []
    for y in yts:
        if y not in uniq:
            uniq.append(y)
    en = ' & '.join(names.HOLIDAY[y][0] for y in uniq)
    he = ' · '.join(names.HOLIDAY[y][1] for y in uniq)
    part = ''
    if uniq == ['Pesach']:
        part = 'First days' if d2g(block[0]).to_heb().day in (15, 16) else 'Last days'
    if uniq == ['Succos']:
        part = 'First days'
    sub = 'Yom Tov & Shabbat' if has_shabbat else 'Yom Tov'
    return dict(title_en=en, title_he=he, kind='yomtov', sub=sub, part=part, yt=uniq,
                fast=('Yom Kippur' in uniq))


def specials(block):
    """Short extra line for the graphic (Chanukah only; other Shabbatot stay clean)."""
    out = []
    fri = block[0] - dt.timedelta(days=1)
    for d in (fri, block[0]):
        f = festival_any(d)
        if f and f.startswith('Chanuk') and 'Shabbat Chanukah' not in out and block[0].weekday() == 5:
            out.append('Shabbat Chanukah')
    return out


# ---------------------------------------------------------------- occasions
POST_INTL_OFFSET_H = 12        # international card: 12 h before the US post (Thu 8 PM ET for a Fri 8 AM post)


def intl_post_time(primary, windows, taken=()):
    """International card goes out 12 h before the US post, so it is still before candle lighting in Israel and
    Melbourne (Fri 8 AM ET is already Fri night / Shabbat in Melbourne). If that moment is inside a pause, use 8:30 AM
    ET on the latest earlier day that is clear. Never at the same minute as another post (then +15 min)."""
    t = primary - dt.timedelta(hours=POST_INTL_OFFSET_H)
    if in_blackout(t, windows):
        k = t.date()
        while in_blackout(at_et(k, POST_FALLBACK_ET), windows) or at_et(k, POST_FALLBACK_ET) >= primary:
            k -= dt.timedelta(days=1)
        t = at_et(k, POST_FALLBACK_ET)
    while t in taken:
        t += dt.timedelta(minutes=15)
    assert not in_blackout(t, windows), ('intl post inside blackout', primary)
    return t


def intl_rows(cols, il_cols):
    rows_w, rows_il = [], []
    for c in CT.intl_cities():
        cc = il_cols if c['israel'] else cols
        r = dict(city=c, times={k: time_for(kind, d, c) for (k, d, kind) in cc})
        (rows_il if c['israel'] else rows_w).append(r)
    return rows_w, rows_il


def occasions(start, end):
    """All posts whose (primary) post date falls in [start, end]."""
    city_list = CT.cities()
    windows = blackout_windows(start - dt.timedelta(days=10), end + dt.timedelta(days=10))
    occ = []
    # Shabbat / Yom Tov runs
    for blk in restricted_runs(start, end + dt.timedelta(days=1)):
        erev = blk[0] - dt.timedelta(days=1)
        if not (start <= erev <= end):
            continue
        meta = block_title(blk)
        cols = block_events(blk)
        rows = []
        for c in city_list:
            rows.append(dict(city=c, times={k: time_for(kind, d, c) for (k, d, kind) in cols}))
        post = at_et(erev, POST_SHABBAT_ET)
        assert not in_blackout(post, windows), ('post inside blackout', erev)
        il_cols = israel_events(blk)
        rw, ril = intl_rows(cols, il_cols)
        il_en, il_he, il_diff = israel_label(blk)
        occ.append(dict(meta, id='%s_%s' % (erev.isoformat(), 'yomtov' if meta['kind'] == 'yomtov' else 'shabbat'),
                        erev=erev, days=blk, cols=cols, rows=rows, post=post, post2=None,
                        specials=specials(blk), heb_dates=[heb_date_str(d) for d in blk],
                        il_cols=il_cols, rows_w=rw, rows_il=ril, il_label=il_en, il_label_he=il_he, il_differs=il_diff))
    # fasts (Yom Kippur is covered by its Yom Tov post)
    d = start - dt.timedelta(days=1)
    while d <= end + dt.timedelta(days=2):
        fn = fast_name(d)
        if fn:
            en, he, plain = names.FAST[fn]
            tb = fn == '9 of Av'
            eve = d - dt.timedelta(days=1)
            if tb:
                cols = [('b', eve, 'fast_begin_sunset'), ('e', d, 'fast_end_tb')]
                pref = at_et(eve, POST_TB_ET)
            else:
                cols = [('b', d, 'fast_begin_alot'), ('e', d, 'fast_end')]
                pref = at_et(eve, POST_FAST_EVE_ET)
            loc = CT.BLACKOUT_LOC
            fast_start_ny = time_for(cols[0][2], cols[0][1], loc)
            post, post2 = pref, None
            if in_blackout(pref, windows) or is_restricted(pref.date()):
                # pull the post in front of the pause: 8:30 AM on the last ordinary day before it
                k = pref.date()
                while is_restricted(k) or in_blackout(at_et(k, POST_FALLBACK_ET), windows):
                    k -= dt.timedelta(days=1)
                post = at_et(k, POST_FALLBACK_ET)
                # optional 9:16 story re-share once the pause is over (pause end rounded up to :00/:15/:30/:45),
                # only if that is still the evening before and well before the fast starts
                t2 = pref
                for w0, w1 in windows:
                    if w0 <= t2 <= w1 or (w0.date() <= t2.date() <= w1.date() and t2 < w1):
                        t2 = (w1 + dt.timedelta(minutes=(15 - w1.minute % 15) % 15)).replace(second=0, microsecond=0)
                if (not in_blackout(t2, windows) and t2.date() == pref.date() and t2.hour < 23
                        and t2 < fast_start_ny - dt.timedelta(minutes=30)):
                    post2 = t2
            if start <= post.date() <= end:
                rows = [dict(city=c, times={k: time_for(kind, dd, c) for (k, dd, kind) in cols}) for c in city_list]
                assert not in_blackout(post, windows), ('fast post in blackout', d)
                rw, ril = intl_rows(cols, cols)
                occ.append(dict(id='%s_fast' % d.isoformat(), kind='fast', title_en=en, title_he=he, sub=plain,
                                fast_date=d, erev=eve, days=[d], cols=cols, rows=rows, post=post, post2=post2,
                                tisha_bav=tb, specials=[], heb_dates=[heb_date_str(d)], yt=[], fast=True,
                                il_cols=cols, rows_w=rw, rows_il=ril, il_label='', il_label_he='', il_differs=False))
        d += dt.timedelta(days=1)
    occ.sort(key=lambda o: o['post'])
    taken = set()
    for o in occ:
        taken.add(o['post'])
        if o['post2']:
            taken.add(o['post2'])
    for o in occ:
        o['post_intl'] = intl_post_time(o['post'], windows, taken)
        taken.add(o['post_intl'])
    return occ
