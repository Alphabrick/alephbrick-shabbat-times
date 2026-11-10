# -*- coding: utf-8 -*-
"""Aleph Brick (abc) Shabbat / Yom Tov / Fast-day times post generator.

Files only: nothing is posted, emailed or uploaded. No network and no API keys at runtime
(pyluach for the Diaspora calendar, a NOAA solar port for the times, fonts and logo vendored in assets/).

Usage
  python3 -B generate.py --start 2026-11-13 --end 2027-12-31        # every post whose post date is in range
  python3 -B generate.py --upcoming 8                                # posts due in the next 8 days (for cron)
  options: --out output  --sizes 4x5,1x1,9x16  --no-images  --jpeg (adds .jpg copies for Instagram)
           --bg dusk|table|night|stone   background concept (default: dusk, see README "Backgrounds")
           --no-intl                      skip the International card

For each post it writes output/<post-date>_<slug>/ with the PNG slides, captions (Facebook, Instagram, X),
whatsapp.txt, alt_text.txt, times.csv and post.json, plus output/schedule.csv for the whole run.
"""
import argparse, csv, datetime as dt, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import calendar_rules as R, render, guard, backgrounds as BG

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
STANDARD = 'Times calculated for each city; local calendars may differ — follow your community’s custom.'
GREET_ROTATION = ['Shabbat Shalom', 'Gut Shabbos', 'Git Shabbos']   # owner ruling Nov 9, 2026 (20:10 ET)


def shabbos_spelling(t):
    """In a 'Gut/Git Shabbos' week the caption text says 'Shabbos' throughout (one spelling per post; owner ruling
    Nov 9, 2026). Hashtags such as #ShabbatShalom are fixed tags and are left alone (no word boundary inside them)."""
    return re.sub(r'(?<!#)\bShabbat\b', 'Shabbos', t)
NCITY = 28
INTL_STANDARD = STANDARD
COUNTRY = {'CA': 'Canada', 'MX': 'Mexico', 'AR': 'Argentina', 'UK': 'UK', 'FR': 'France', 'BE': 'Belgium',
           'ZA': 'South Africa', 'AU': 'Australia', 'IL': 'Israel'}
SCREEN = ('Content PASS (internal AI screen, abc-rabbinic-review v2.0, not a rabbi); OWNER POLICY DECISION on the '
          'zmanim opinions shown (end = tzeit 8.5 deg; Tisha B\'Av end 6.45 deg as on Hebcal); owner visual approval required')


def tfmt(t):
    return t.strftime('%-I:%M')


def ampm(t):
    return t.strftime('%-I:%M %p')


def dshort(d):
    return d.strftime('%a, %b %-d')


def dlong(d):
    return '%s, %s' % (DAYS[d.weekday()], d.strftime('%B %-d, %Y'))


def slug(o):
    s = re.sub(r'[^a-z0-9]+', '-', o['title_en'].lower().replace('’', '').replace('parshat ', '')).strip('-')
    return '%s_%s' % (o['kind'], s)


# ---------------------------------------------------------------- text per occasion
def describe(o):
    """Labels for columns, legend, notes, date lines and greeting."""
    k = o['kind']
    cols = o['cols']
    D = {}
    if k == 'shabbat':
        fri, sat = o['erev'], o['days'][-1]
        D['lock1'] = 'SHABBAT TIMES'
        D['date_lines'] = [dlong(fri).upper()]
        if o['specials']:
            D['date_lines'].append(' · '.join(o['specials']).upper())
        D['main'] = [('c0', 'CANDLES', 'c1', 'Candle lighting · Fri'), ('end', 'ENDS', 'c2', 'Shabbat ends · Sat')]
        D['extra'] = []
        D['notes'] = ['Candle lighting 18 min before sunset. Shabbat ends at nightfall (sun 8.5° below the horizon).', STANDARD]
        # Owner ruling Nov 9, 2026 (20:10 ET): vary the Shabbat greeting week by week (captions only; graphics unchanged)
        g = GREET_ROTATION[((fri - dt.date(2026, 11, 13)).days // 7) % 3]
        D['greet'] = g + ' from our family to yours!'
        D['shabbos'] = 'Shabbos' in g
        D['what'] = 'Shabbat candle-lighting and Shabbat-end times for %s' % o['title_en']
    elif k == 'yomtov':
        first, last = o['erev'], o['days'][-1]
        yk = o['fast']
        D['lock1'] = 'YOM KIPPUR TIMES' if yk else 'YOM TOV TIMES'
        rng = '%s – %s' % (dshort(first), dshort(last)) + last.strftime(', %Y')
        D['date_lines'] = [((o.get('part') + ' · ') if o.get('part') else '').upper() + rng.upper()]
        last_is_yt = R.yomtov_name(last) is not None
        end_lbl = 'Fast ends' if yk else ('Yom Tov ends' if last_is_yt else 'Shabbat ends')
        D['main'] = [('c0', 'CANDLES', 'c1', 'Candle lighting · %s' % first.strftime('%a %-m/%-d')),
                     ('end', 'ENDS', 'c2', '%s · %s' % (end_lbl, last.strftime('%a %-m/%-d')))]
        extra = []
        for key, d, kind in cols[1:-1]:
            nxt = d + dt.timedelta(days=1)
            if kind == 'candles_after':
                extra.append((key, 'AFTER', 'c1', 'Light after · %s night' % d.strftime('%a %-m/%-d')))
            else:
                extra.append((key, d.strftime('%a').upper(), 'c2', 'Candle lighting · %s' % d.strftime('%a %-m/%-d')))
        D['extra'] = extra
        if yk:
            D['notes'] = ['Candle lighting 18 min before sunset; the fast begins before sunset. Fast ends at nightfall (sun 8.5° below the horizon).', STANDARD]
        else:
            D['notes'] = ['Candle lighting 18 min before sunset. Ends at nightfall (sun 8.5° below the horizon).', STANDARD]
        D['notes_extra'] = ['“After” = light only after nightfall. On Yom Tov, light from an existing flame.', STANDARD] \
            if any(kd == 'candles_after' for _, _, kd in cols[1:-1]) else \
            ['Candle lighting 18 min before sunset. On Yom Tov, light from an existing flame.', STANDARD]
        names = o['yt']
        # Owner ruling Nov 9, 2026 (20:10 ET): when the Yom Tov run includes Shabbat, one combined greeting
        with_shabbat = any(d.weekday() == 5 for d in o['days'])
        if 'Rosh Hashana' in names:
            D['greet'] = ('Shana Tova & Shabbat Shalom' if with_shabbat else 'Shana Tova') + ' from our family to yours!'
        elif yk:
            D['greet'] = 'G’mar Chatimah Tovah' + (' & Shabbat Shalom' if with_shabbat else '') + ', and wishing everyone an easy and meaningful fast.'
        else:
            D['greet'] = ('Shabbat Shalom & Chag Sameach' if with_shabbat else 'Chag Sameach') + ' from our family to yours!'
        D['what'] = '%s candle-lighting and end times' % o['title_en']
    else:  # fast
        tb = o.get('tisha_bav')
        fd = o['fast_date']
        D['lock1'] = 'FAST DAY TIMES'
        if tb:
            D['date_lines'] = [('%s evening – %s' % (o['erev'].strftime('%a, %b %-d'), fd.strftime('%a, %b %-d, %Y'))).upper()]
            D['main'] = [('b', 'BEGINS', 'c1', 'Fast begins · %s sunset' % o['erev'].strftime('%a')),
                         ('e', 'ENDS', 'c2', 'Fast ends · %s night' % fd.strftime('%a'))]
            D['notes'] = ['Fast begins at sunset and ends at nightfall.', STANDARD]
        else:
            D['date_lines'] = [dlong(fd).upper()]
            D['main'] = [('b', 'BEGINS', 'c1', 'Fast begins · a.m. (dawn)'),
                         ('e', 'ENDS', 'c2', 'Fast ends · p.m. (nightfall)')]
            D['notes'] = ['Fast begins at dawn (alot hashachar) and ends at nightfall (tzeit).', STANDARD]
        D['extra'] = []
        D['greet'] = 'Wishing everyone an easy and meaningful fast.'
        D['what'] = '%s (%s) fast times' % (o['title_en'], o['sub'])
    return D


def city_rows(o, keys):
    out = []
    for r in o['rows']:
        c = r['city']
        out.append(dict(name=c['name'], st=c['st'], region=c['region'], t=[tfmt(r['times'][k]) for k in keys]))
    return out


def variant(o):
    """Background variant (backgrounds.py) for an occasion."""
    if o['kind'] == 'fast':
        return 'tisha_bav' if o.get('tisha_bav') else 'fast'
    if o['kind'] == 'yomtov':
        y = o['yt']
        if 'Yom Kippur' in y: return 'yom_kippur'
        if 'Rosh Hashana' in y: return 'rosh_hashanah'
        if 'Shmini Atzeres' in y or 'Simchas Torah' in y: return 'simchat_torah'
        if 'Succos' in y: return 'sukkot'
        if 'Pesach' in y: return 'pesach'
        if 'Shavuos' in y: return 'shavuot'
        return 'shabbat'
    if 'Shabbat Chanukah' in o.get('specials', []): return 'chanukah'
    if 'Chol HaMoed Pesach' in o['title_en']: return 'pesach'
    if 'Chol HaMoed Sukkot' in o['title_en']: return 'sukkot'
    return 'shabbat'


def slide_specs(o, D, fmt):
    """List of (suffix, spec) for one format."""
    tone = {'shabbat': 'shabbat', 'yomtov': 'yomtov', 'fast': 'fast'}[o['kind']]
    motif = 'bricks' if o['kind'] == 'fast' else 'candles'
    sets = [('1', D['main'], D['notes'])]
    if D['extra']:
        sets.append(('2', D['extra'], D['notes_extra']))
    out = []
    for sn, cols, nts in sets:
        rows = city_rows(o, [c[0] for c in cols])
        A = [r for r in rows if r['region'] == 'A']; B = [r for r in rows if r['region'] == 'B']
        base = dict(id=o['id'], tone=tone, variant=variant(o), motif=motif, title_en=o['title_en'], title_he=o['title_he'],
                    date_lines=D['date_lines'], lock1=D['lock1'],
                    cols=[dict(key=c[0], head=c[1], color=c[2]) for c in cols],
                    legend=[(c[2], c[3]) for c in cols], notes=nts, city_head=['CITY', 'CITY'])
        npart = len(sets)
        if fmt == '1x1':
            for part, grp, lbl in (('a', A, 'NORTHEAST · MID-ATLANTIC'), ('b', B, 'MIDWEST · SOUTH · WEST')):
                h = (len(grp) + 1) // 2
                sp = dict(base, halves=[grp[:h], grp[h:]], lock2=lbl)
                out.append(('s%s%s' % (sn, part), sp))
        else:
            h = (len(rows) + 1) // 2
            sp = dict(base, halves=[rows[:h], rows[h:]], lock2=('MORE TIMES · 2 OF 2' if sn == '2' else
                                                  ('%d US CITIES' % len(rows) + (' · 1 OF 2' if npart > 1 else ''))))
            out.append(('s%s' % sn, sp))
    return out


def captions(o, D):
    rows = o['rows']
    cols = [c[0] for c in D['main']]
    lines = []
    for r in rows:
        c = r['city']
        lines.append('%s, %s: %s' % (c['name'], c['st'], ' / '.join(ampm(r['times'][k]) for k in cols)))
    head = D['what']
    if o['kind'] == 'shabbat':
        intro = '%s (%s). Candle lighting Friday, %s; Shabbat ends Saturday night. Times for %d US cities:' % (
            head, o['title_he'], o['erev'].strftime('%B %-d'), len(rows), )
        key = 'Candle lighting / Shabbat ends'
    elif o['kind'] == 'yomtov':
        intro = '%s (%s), %s. Times for %d US cities:' % (head, o['title_he'], D['date_lines'][0].title(), len(rows))
        key = '%s / %s' % (D['main'][0][3], D['main'][1][3])
    else:
        intro = '%s (%s), %s. Times for %d US cities:' % (o['title_en'], o['title_he'], D['date_lines'][0].title(), len(rows))
        key = 'Fast begins / Fast ends'
    extra_txt = ''
    if D['extra']:
        ex = []
        for key2, head2, col2, leg in D['extra']:
            ex.append(leg + ': ' + ', '.join('%s %s' % (r['city']['name'], tfmt(r['times'][key2])) for r in rows[:6]) +
                      ' (all cities on slide 2)')
        extra_txt = '\n'.join(ex)
    notes = ' '.join(D['notes'][:1]) + ' ' + STANDARD
    tags = hashtags(o)
    special = special_line(o)
    body = [intro, '(' + key + ')', '\n'.join(lines)]
    if extra_txt: body.append(extra_txt)
    if o.get('rows_w'): body.append(intl_text_section(o, D))
    body.append(notes)
    if special: body.append(special)
    body.append(D['greet'])
    fb = '\n\n'.join(body) + '\n\n' + ' '.join(tags)
    ig_body = [intro.replace('Times for %d US cities:' % len(rows), 'Find your city in the graphic (%d US cities).' % len(rows)), notes]
    if special: ig_body.append(special)
    ig_body.append(D['greet'])
    ig = '\n\n'.join(ig_body) + '\n\n' + ' '.join(tags)
    # X: <= 270 chars, 4 sample cities
    pick = [r for r in rows if r['city']['name'] in ('Brooklyn', 'Chicago', 'Miami', 'Los Angeles')]
    sample = ' · '.join('%s %s' % (r['city']['name'].replace('Los Angeles', 'LA'), '/'.join(tfmt(r['times'][k]) for k in cols)) for r in pick)
    if o['kind'] == 'shabbat':
        x = '%s: %s (%s). 28 cities in the image. %s' % (o['title_en'], sample, 'candles/ends', tags[0])
    elif o['kind'] == 'yomtov':
        x = '%s times: %s (%s). 28 cities in the image. %s' % (o['title_en'], sample, 'candles/ends', tags[0])
    else:
        x = '%s fast times: %s (begins/ends). 28 cities in the image. %s' % (o['title_en'], sample, tags[0])
    assert len(x) <= 270, (len(x), x)
    alt = '%s. %s. Times for %d US cities (%s): %s.' % (head, D['date_lines'][0].title(), len(rows), key.lower(), '; '.join(lines))
    return fb, ig, x, alt


def special_line(o):
    if 'Shabbat Chanukah' in o.get('specials', []):
        return 'On Friday, the Chanukah lights are lit before the Shabbat candles.'
    if o['kind'] == 'yomtov' and o['yt'] == ['Pesach'] and o.get('part') == 'First days':
        return ('Today is also Ta’anit Bechorot, the Fast of the Firstborn; many firstborns take part in a siyum. '
                'Ask your rav.')
    if o['kind'] == 'fast' and o.get('tisha_bav') and o['erev'].weekday() == 5:
        return 'This year the fast is pushed off to Sunday; it begins at sunset on Shabbat.'
    return ''


def hashtags(o):
    if o['kind'] == 'shabbat':
        t = ['#ShabbatShalom', '#CandleLighting', '#ShabbatTimes']
        if o['title_en'].startswith('Parshat '):
            t.append('#Parshat' + re.sub(r'[^A-Za-z]', '', o['title_en'][8:]))
        t += ['#JewishFamily', '#AlephBrick']
    elif o['kind'] == 'yomtov':
        t = ['#ChagSameach' if not o['fast'] else '#YomKippur'] + ['#' + re.sub(r'[^A-Za-z]', '', n) for n in o['title_en'].split(' & ')]
        t += ['#CandleLighting', '#JewishHolidays', '#AlephBrick']
    else:
        t = ['#' + re.sub(r'[^A-Za-z]', '', o['title_en']), '#FastDay', '#JewishCalendar', '#AlephBrick']
    out = []
    for x in t:
        if x not in out: out.append(x)
    return out


def whatsapp(o, D):
    cols = [c[0] for c in D['main']]
    w = max(len('%s %s' % (r['city']['name'], r['city']['st'])) for r in o['rows'])
    L = ['*%s*' % (D['lock1'].title().replace('Yom Tov', 'Yom Tov') + ' · ' + o['title_en']), o['title_he'],
         ', '.join(x.title() for x in D['date_lines']), '']
    L.append('_%s_' % ' / '.join(c[3] for c in D['main']))
    L.append('```')
    for r in o['rows']:
        nm = '%s %s' % (r['city']['name'], r['city']['st'])
        L.append('%s  %s' % (nm.ljust(w), ' / '.join(tfmt(r['times'][k]).rjust(5) for k in cols)))
    L.append('```')
    for key2, head2, col2, leg in D['extra']:
        L.append('')
        L.append('_%s_' % leg)
        L.append('```')
        for r in o['rows']:
            nm = '%s %s' % (r['city']['name'], r['city']['st'])
            L.append('%s  %s' % (nm.ljust(w), tfmt(r['times'][key2]).rjust(5)))
        L.append('```')
    if o.get('rows_w'):
        L += whatsapp_intl(o, D)
    L.append('')
    L.append(D['notes'][0])
    if D['extra']:
        L.append(D['notes_extra'][0])
    L.append(STANDARD)
    sp = special_line(o)
    if sp: L.append(sp)
    L.append('')
    L.append(D['greet'] + ' — Aleph Brick')
    return '\n'.join(L)


# ---------------------------------------------------------------- international card
def tfmt_or_dash(t):
    return tfmt(t) if t is not None else '—'


def col_spec(key, d, kind):
    if kind == 'candles':
        return dict(key=key, head='CANDLES', sub=d.strftime('%a %-m/%-d').upper(), color='c1',
                    legend='Candle lighting · %s' % d.strftime('%a %-m/%-d'))
    if kind == 'candles_after':
        return dict(key=key, head='AFTER', sub=d.strftime('%a %-m/%-d').upper(), color='c1',
                    legend='Light after · %s night' % d.strftime('%a %-m/%-d'))
    if kind == 'end':
        return dict(key=key, head='ENDS', sub=d.strftime('%a %-m/%-d').upper(), color='c2',
                    legend='Ends · %s' % d.strftime('%a %-m/%-d'))
    if kind == 'fast_begin_alot':
        return dict(key=key, head='BEGINS', sub='DAWN', color='c1', legend='Fast begins · dawn')
    if kind == 'fast_begin_sunset':
        return dict(key=key, head='BEGINS', sub='%s SUNSET' % d.strftime('%a').upper(), color='c1',
                    legend='Fast begins · %s sunset' % d.strftime('%a'))
    return dict(key=key, head='ENDS', sub='NIGHTFALL', color='c2', legend='Fast ends · nightfall')


def intl_rows_disp(rows, cols, show_cc=True):
    return [dict(name=r['city']['name'], st=(r['city']['st'] if show_cc else ''),
                 t=[tfmt_or_dash(r['times'][c['key']]) for c in cols]) for r in rows]


def israel_section_label(o, fmt):
    cands = []
    if o['il_differs'] and o['il_label']:
        cands.append('ISRAEL · ' + o['il_label'].upper())
        if o['kind'] == 'yomtov':
            cands.append('ISRAEL · ONE DAY OF YOM TOV')
        cands.append('ISRAEL · ISRAEL CALENDAR')
    cands.append('ISRAEL')
    for c in cands:
        if render.label_fits(c, fmt):
            return c
    return 'ISRAEL'


def intl_sections(o, fmt):
    wcols = [col_spec(*c) for c in o['cols']]
    icols = [col_spec(*c) for c in o['il_cols']]
    layout = 'halves' if len(wcols) <= 2 and len(icols) <= 2 else 'full'
    if layout == 'halves':   # heads like the US card; the legend line explains the days
        for c in wcols + icols:
            c['head'] = {'c1': 'BEGINS' if o['kind'] == 'fast' else 'CANDLES', 'c2': 'ENDS'}[c['color']]
    w = dict(label='AROUND THE WORLD · LOCAL TIME', cols=wcols, rows=intl_rows_disp(o['rows_w'], wcols),
             layout=layout, city_head='CITY')
    i = dict(label=israel_section_label(o, fmt), cols=icols, rows=intl_rows_disp(o['rows_il'], icols, False),
             layout=layout, city_head='CITY')
    if not render.label_fits(w['label'], fmt):
        w['label'] = 'AROUND THE WORLD'
    return [w, i], layout


def intl_notes(o, layout):
    if o['kind'] == 'fast':
        n = ['All times are local. ' + ('Fast begins at sunset and ends at nightfall.' if o.get('tisha_bav') else
                                         'Fast begins at dawn and ends at nightfall.')]
    else:
        n = ['All times are local. Candles 18 min before sunset (Israel: Jerusalem 40, Haifa 30, others 20); '
             'ends at nightfall (sun 8.5° below the horizon).']
        if any(k == 'candles_after' for _, _, k in o['cols'] + o['il_cols']):
            n.append('“After” = light only after nightfall, from an existing flame.')
    n.append(INTL_STANDARD)
    return n


def intl_slide_specs(o, D, fmt):
    secs, layout = intl_sections(o, fmt)
    tone = {'shabbat': 'shabbat', 'yomtov': 'yomtov', 'fast': 'fast'}[o['kind']]
    base = dict(id=o['id'] + '_intl', tone=tone, variant=variant(o), motif='bricks' if o['kind'] == 'fast' else 'candles',
                title_en=o['title_en'], title_he=o['title_he'], date_lines=D['date_lines'], lock1=D['lock1'],
                lock2='INTERNATIONAL · LOCAL TIME', notes=intl_notes(o, layout))
    if layout == 'halves':
        base['legend'] = [(c['color'], leg) for c, leg in zip(secs[0]['cols'], [x[3] for x in D['main']])]
    if fmt == '1x1':
        return intl_split(dict(base, sections=secs))
    return [('s1', dict(base, sections=secs))]


def notes_for(spec, secs):
    """Notes for a slide that shows only some sections: drop lines that do not apply to it."""
    after = any(c['head'] == 'AFTER' for sc in secs for c in sc['cols'])
    israel = any(sc['label'].startswith('ISRAEL') for sc in secs)
    out = []
    for n in spec['notes']:
        if n.startswith('“After”') and not after:
            continue
        if not israel:
            n = n.replace(' (Israel: Jerusalem 40, Haifa 30, others 20)', '')
        out.append(n)
    return out


def intl_split(spec, suf='s1'):
    """Too tall for one slide: world | Israel; a world section that is still too tall: Americas | rest of the world."""
    secs = spec['sections']
    if len(secs) == 2:
        return [(suf + 'a', dict(spec, sections=[secs[0]], notes=notes_for(spec, [secs[0]]))),
                (suf + 'b', dict(spec, sections=[secs[1]], notes=notes_for(spec, [secs[1]])))]
    sec = secs[0]
    if sec['label'].startswith('AROUND') and len(sec['rows']) > 5:
        am = [r for r in sec['rows'] if r['name'] in ('Toronto', 'Montreal', 'Mexico City', 'Buenos Aires')]
        rest = [r for r in sec['rows'] if r not in am]
        return [(suf + '1', dict(spec, sections=[dict(sec, label='THE AMERICAS · LOCAL TIME', rows=am)])),
                (suf + '2', dict(spec, sections=[dict(sec, label='EUROPE · AFRICA · AUSTRALIA', rows=rest)]))]
    raise render.Overflow((spec['id'], 'cannot split'))


def intl_city_line(r, cols, show_cc=True):
    c = r['city']
    nm = c['name'] + (', ' + COUNTRY[c['st']] if show_cc else '')
    if len(cols) <= 2:
        return '%s: %s' % (nm, ' / '.join(ampm(r['times'][k]) if r['times'][k] else '—' for k, _, _ in cols))
    return '%s: %s' % (nm, ' · '.join('%s %s' % (col_spec(k, d, kd)['legend'].split(' · ')[0] + ' ' +
                                                  col_spec(k, d, kd)['sub'].title(), ampm(r['times'][k]))
                                      for k, d, kd in cols))


def intl_text_section(o, D):
    """Plain-text international block (Facebook caption + alt text)."""
    wl = [intl_city_line(r, o['cols']) for r in o['rows_w']]
    il = [intl_city_line(r, o['il_cols'], False) for r in o['rows_il']]
    key = ' / '.join(col_spec(*c)['legend'] for c in o['cols']) if len(o['cols']) <= 2 else ''
    il_key = ' / '.join(col_spec(*c)['legend'] for c in o['il_cols']) if len(o['il_cols']) <= 2 else ''
    il_head = 'Israel (Israel calendar%s)' % ((': ' + o['il_label']) if o['il_differs'] and o['il_label'] else '')
    out = ['International, local time in each city' + (' (' + key + ')' if key else '') + ':', '\n'.join(wl), '',
           il_head + (' (' + il_key + ')' if il_key else '') + ':', '\n'.join(il)]
    if o['kind'] != 'fast':
        out.append('In Israel, candle lighting is 40 min before sunset in Jerusalem, 30 in Haifa and 20 in Tel Aviv and Bnei Brak.')
    return '\n'.join(out)


def intl_captions(o, D):
    head = {'shabbat': 'International Shabbat times', 'yomtov': 'International %s times' % o['title_en'],
            'fast': 'International %s fast times' % o['title_en']}[o['kind']]
    if o['kind'] == 'shabbat':
        intro = '%s for %s (%s), %s. All times are LOCAL time in each city.' % (head, o['title_en'], o['title_he'],
                                                                               dlong(o['erev']))
    else:
        intro = '%s (%s), %s. All times are LOCAL time in each city.' % (head, o['title_he'],
                                                                      D['date_lines'][0].title())
    il_note = ''
    if o['il_differs'] and o['il_label']:
        il_note = 'Israel keeps the Israel calendar this week: %s (%s).' % (o['il_label'], o['il_label_he'])
    notes_ = ' '.join(intl_notes(o, ''))
    tags = hashtags(o) 
    tags = tags[:-1] + ['#JewishWorld', '#AlephBrick']
    fb = '\n\n'.join(x for x in [intro, intl_text_section(o, D), il_note, notes_, D['greet']] if x) + '\n\n' + ' '.join(tags)
    ig = '\n\n'.join(x for x in [intro.replace('All times are LOCAL time in each city.',
                                               'Find your city in the graphic (13 cities, local time).'),
                                  il_note, notes_, D['greet']] if x) + '\n\n' + ' '.join(tags)
    cols = [c[0] for c in o['cols']][:1] + [o['cols'][-1][0]]
    picks = [r for r in o['rows_w'] + o['rows_il'] if r['city']['name'] in ('Jerusalem', 'London', 'Toronto', 'Melbourne')]
    def two(r):
        cc = o['il_cols'] if r['city']['israel'] else o['cols']
        ks = [cc[0][0], cc[-1][0]]
        return '/'.join(tfmt_or_dash(r['times'][k]) for k in ks)
    sample = ' · '.join('%s %s' % (r['city']['name'], two(r)) for r in picks)
    what = 'begins/ends' if o['kind'] == 'fast' else 'candles/ends'
    x = '%s, %s (local time): %s (%s). 13 cities in the image. %s' % (head, o['title_en'] if o['kind'] == 'shabbat' else
                                                                       D['date_lines'][0].title(), sample, what, tags[0])
    if len(x) > 270:
        x = '%s (local time): %s (%s). 13 cities in the image. %s' % (head, sample, what, tags[0])
    assert len(x) <= 270, (len(x), x)
    alt = '%s. %s. %s' % (head, D['date_lines'][0].title(), intl_text_section(o, D).replace('\n\n', ' ').replace('\n', '; '))
    return fb, ig, x, alt


def whatsapp_intl(o, D):
    L = ['', '*International · local time in each city*']
    for rows, cols, title, cc in ((o['rows_w'], o['cols'], 'Around the world', True),
                                  (o['rows_il'], o['il_cols'], 'Israel (Israel calendar)' +
                                   ((' · ' + o['il_label']) if o['il_differs'] and o['il_label'] else ''), False)):
        w = max(len(r['city']['name'] + (' ' + r['city']['st'] if cc else '')) for r in rows)
        L.append('_%s: %s_' % (title, ' / '.join(col_spec(*c)['legend'] for c in cols)))
        L.append('```')
        for r in rows:
            nm = r['city']['name'] + (' ' + r['city']['st'] if cc else '')
            L.append('%s  %s' % (nm.ljust(w), ' / '.join(tfmt_or_dash(r['times'][k]).rjust(5) for k, _, _ in cols)))
        L.append('```')
    if o['kind'] != 'fast':
        L.append('Candle lighting: Jerusalem 40 min, Haifa 30, Tel Aviv and Bnei Brak 20 min before sunset; all other cities 18 min.')
    return L


# ---------------------------------------------------------------- one slot per morning
MERGE_GAP_H = 2     # cross-series rule: no two posts on the same channel less than 2 h apart


def _split_tags(cap):
    body, _, tags = cap.rpartition('\n\n')
    if tags.startswith('#'):
        return body, tags.split()
    return cap, []


def _join_caps(a, b, sep):
    ba, ta = _split_tags(a); bb, tb = _split_tags(b)
    tags = []
    for t in ta + tb:
        if t not in tags: tags.append(t)
    return ba + '\n\n' + sep + '\n\n' + bb + ('\n\n' + ' '.join(tags) if tags else '')


def merge_same_slot(sched, out_root):
    """A fast-day card that would go out less than 2 h after/before the Shabbat / Yom Tov post of the same morning
    (fast pulled in front of a pause: Fri Dec 18 2026, Fri Oct 1 2027) is merged into that post as extra carousel
    slides, with its text appended to the captions and to whatsapp.txt. The same for the International rows.
    The fast's 9:16 story re-share after the pause stays as its own row."""
    out, merged = [], []
    for role in ('primary', 'international'):
        rows = sorted([r for r in sched if r['post_role'] == role], key=lambda r: r['post_datetime_iso'])
        for f in [r for r in rows if r['type'] == 'fast']:
            t = dt.datetime.fromisoformat(f['post_datetime_iso'])
            host = [r for r in rows if r['type'] != 'fast' and r not in merged and
                    abs((dt.datetime.fromisoformat(r['post_datetime_iso']) - t).total_seconds()) < MERGE_GAP_H * 3600]
            if not host:
                continue
            h = host[0]
            sep = '— Also this week: %s —' % f['title']
            h['files'] = h['files'] + ' | ' + f['files']
            h['caption'] = _join_caps(h['caption'], f['caption'], sep)
            h['caption_instagram'] = _join_caps(h['caption_instagram'], f['caption_instagram'], sep)
            x2 = h['caption_x'] + ' + %s fast times in the images.' % f['title']
            if len(x2) <= 270:
                h['caption_x'] = x2
            h['alt_text'] = h['alt_text'] + ' Fast slides: ' + f['alt_text']
            h['type'] = h['type'] + ' + fast'
            h['title'] = h['title'] + ' + ' + f['title']
            h['title_he'] = h['title_he'] + ' · ' + f['title_he']
            if role == 'primary':
                h['whatsapp_text'] = h['whatsapp_text'] + '\n\n' + f['whatsapp_text']
            merged.append(f)
            hd = os.path.join(out_root, h['folder']); fd = os.path.join(out_root, f['folder'])
            names = (('caption_facebook.txt', 'caption'), ('caption_instagram.txt', 'caption_instagram'),
                     ('caption_x.txt', 'caption_x'), ('alt_text.txt', 'alt_text'), ('whatsapp.txt', 'whatsapp_text')) \
                if role == 'primary' else (('caption_intl_facebook.txt', 'caption'), ('caption_intl_instagram.txt', 'caption_instagram'),
                                           ('caption_intl_x.txt', 'caption_x'), ('alt_text_intl.txt', 'alt_text'))
            for fn, key in names:
                with open(os.path.join(hd, fn), 'w', encoding='utf-8') as fh:
                    fh.write(h[key] + '\n')
            for folder_, note in ((hd, 'includes %s (%s) as extra slides' % (f['folder'], role)),
                                  (fd, '%s post merged into %s %s (same morning)' % (role, h['folder'], h['date_time_ET']))):
                pj = os.path.join(folder_, 'post.json')
                m = json.load(open(pj, encoding='utf-8'))
                m.setdefault('merged', []).append(note)
                json.dump(m, open(pj, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return [r for r in sched if r not in merged]


# ---------------------------------------------------------------- main
def save_img(spec, fmt, p, concept, jpeg, intl=False):
    r = (render.render_intl if intl else render.render)(spec, fmt, p, concept)
    if jpeg:   # Instagram's publishing API accepts JPEG only
        from PIL import Image
        Image.open(p).convert('RGB').save(p[:-4] + '.jpg', quality=92, optimize=True)
    return r


def build(start, end, out_root, sizes, images=True, jpeg=False, concept=BG.DEFAULT, intl=True, intl_mode='carousel'):
    """intl_mode 'carousel' (default): the International slides ride in the same 08:00 post as the US slides (one post,
    no extra slot in the cross-series calendar). 'separate': its own post 12 h earlier (Thu 8 PM ET), better for
    Melbourne/Israel but it needs a free slot in the cross-series calendar (owner decision)."""
    occ = R.occasions(start, end)
    os.makedirs(out_root, exist_ok=True)
    sched = []
    fitlog = {}
    for o in occ:
        D = describe(o)
        folder = '%s_%s' % (o['post'].date().isoformat(), slug(o))
        od = os.path.join(out_root, folder); os.makedirs(od, exist_ok=True)
        files = {}
        for fmt in sizes:
            files[fmt] = []
            for suf, spec in slide_specs(o, D, fmt):
                fn = 'ABC_TIMES_%s_%s_%s_%s.png' % (o['post'].date().isoformat(), slug(o).split('_')[0], fmt, suf)
                p = os.path.join(od, fn)
                if images:
                    fitlog[fn] = save_img(spec, fmt, p, concept, jpeg)
                files[fmt].append(os.path.join(folder, fn))
        ifiles = {}
        if intl:
            for fmt in sizes:
                ifiles[fmt] = []
                todo = list(intl_slide_specs(o, D, fmt))
                while todo:
                    suf, spec = todo.pop(0)
                    fn = 'ABC_TIMES_%s_%s_intl_%s_%s.png' % (o['post'].date().isoformat(), slug(o).split('_')[0], fmt, suf)
                    p = os.path.join(od, fn)
                    if images:
                        try:
                            fitlog[fn] = save_img(spec, fmt, p, concept, jpeg, intl=True)
                        except render.Overflow:
                            todo = intl_split(spec, suf) + todo   # too tall for one slide: split it
                            continue
                    ifiles[fmt].append(os.path.join(folder, fn))
        fb, ig, x, alt = captions(o, D)
        wa = whatsapp(o, D)
        ifb, iig, ix, ialt = intl_captions(o, D)
        if D.get('shabbos'):
            fb, ig, x, alt, wa, ifb, iig, ix, ialt = [shabbos_spelling(s) for s in (fb, ig, x, alt, wa, ifb, iig, ix, ialt)]
        outs = [('caption_facebook.txt', fb), ('caption_instagram.txt', ig), ('caption_x.txt', x),
                ('whatsapp.txt', wa), ('alt_text.txt', alt)]
        if intl:
            outs += [('caption_intl_facebook.txt', ifb), ('caption_intl_instagram.txt', iig),
                     ('caption_intl_x.txt', ix), ('alt_text_intl.txt', ialt)]
        for name, txt in outs:
            with open(os.path.join(od, name), 'w', encoding='utf-8') as f:
                f.write(txt + '\n')
        with open(os.path.join(od, 'times.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['city', 'state', 'tz'] + ['%s (%s %s)' % (k, d.isoformat(), kind) for k, d, kind in o['cols']])
            for r in o['rows']:
                c = r['city']
                w.writerow([c['name'], c['st'], c['tz']] + [r['times'][k].strftime('%Y-%m-%d %H:%M') for k, _, _ in o['cols']])
        with open(os.path.join(od, 'times_intl.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['city', 'country', 'tz', 'calendar', 'column', 'date', 'what', 'local_time'])
            for rows, cols, cal in ((o['rows_w'], o['cols'], 'Diaspora'), (o['rows_il'], o['il_cols'], 'Israel')):
                for r in rows:
                    c = r['city']
                    for k, d, kind in cols:
                        t = r['times'][k]
                        w.writerow([c['name'], COUNTRY[c['st']], c['tz'], cal, k, d.isoformat(), kind,
                                    t.strftime('%Y-%m-%d %H:%M') if t else ''])
        hits = guard.hits('\n'.join([fb, ig, x, wa, alt, ifb, iig, ix, ialt, o['title_en'], o['title_he']]))
        assert not hits, ('guard', o['id'], hits)
        meta = dict(id=o['id'], kind=o['kind'], title_en=o['title_en'], title_he=o['title_he'],
                    hebrew_dates=o['heb_dates'], post_time_et=o['post'].isoformat(),
                    story_reshare_et=o['post2'].isoformat() if o['post2'] else '',
                    files=files, feed_carousel=files.get('4x5', []), story=files.get('9x16', []),
                    square=files.get('1x1', []), torah_only=True, status='DRAFT',
                    international=dict(mode=intl_mode, post_time_et=(o['post_intl'] if intl_mode == 'separate'
                                                                      else o['post']).isoformat(), files=ifiles,
                                       israel_label=o['il_label'], israel_label_he=o['il_label_he'],
                                       israel_differs=o['il_differs']) if intl else None,
                    background=dict(concept=concept, variant=variant(o)),
                    rabbinic_screen=SCREEN)
        with open(os.path.join(od, 'post.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        carousel = intl and intl_mode == 'carousel'
        allf = [p for fmt in sizes for p in files[fmt] + (ifiles[fmt] if carousel else [])]
        if carousel:   # one post: US slide(s), then the International slide(s)
            ig = ig.replace('\n\n', '\n\nSwipe for 13 international cities (local time, Israel on the Israel calendar).\n\n', 1)
            alt = alt + ' Next slide: ' + ialt
            with open(os.path.join(od, 'caption_instagram.txt'), 'w', encoding='utf-8') as f:
                f.write(ig + '\n')
            with open(os.path.join(od, 'alt_text.txt'), 'w', encoding='utf-8') as f:
                f.write(alt + '\n')
        sched.append(dict(date_time_ET=o['post'].strftime('%Y-%m-%d %H:%M'), post_datetime_iso=o['post'].isoformat(),
                          type=o['kind'] if not (o['kind'] == 'yomtov' and o['fast']) else 'yomtov (Yom Kippur)',
                          post_role='primary', title=o['title_en'], title_he=o['title_he'], folder=folder,
                          files=' | '.join(allf), caption=fb, caption_instagram=ig, caption_x=x,
                          whatsapp_text=wa, alt_text=alt, rabbinic_screen=SCREEN, status='DRAFT'))
        if intl and intl_mode == 'separate':
            sched.append(dict(date_time_ET=o['post_intl'].strftime('%Y-%m-%d %H:%M'),
                              post_datetime_iso=o['post_intl'].isoformat(), type=sched[-1]['type'],
                              post_role='international', title=o['title_en'], title_he=o['title_he'], folder=folder,
                              files=' | '.join(p for fmt in sizes for p in ifiles[fmt]), caption=ifb,
                              caption_instagram=iig, caption_x=ix, whatsapp_text='', alt_text=ialt,
                              rabbinic_screen=SCREEN, status='DRAFT'))
        if o['post2']:
            sched.append(dict(date_time_ET=o['post2'].strftime('%Y-%m-%d %H:%M'), post_datetime_iso=o['post2'].isoformat(),
                              type=o['kind'], post_role='story re-share (after Shabbat/Yom Tov pause)',
                              title=o['title_en'], title_he=o['title_he'], folder=folder,
                              files=' | '.join(files.get('9x16', [])), caption='', caption_instagram='', caption_x='',
                              whatsapp_text=wa, alt_text=alt, rabbinic_screen=SCREEN, status='DRAFT'))
    mine = {(r['folder'], r['post_role']) for r in sched}     # incl. rows merged away below
    sched = merge_same_slot(sched, out_root)
    # merge with an existing schedule (a weekly --upcoming run must not drop the rest of the year)
    sp = os.path.join(out_root, 'schedule.csv')
    if os.path.exists(sp):
        for r in csv.DictReader(open(sp, encoding='utf-8')):
            if (r['folder'], r['post_role']) not in mine:
                sched.append(r)
    sched.sort(key=lambda r: (r['post_datetime_iso'], r['folder']))
    fields = ['date_time_ET', 'post_datetime_iso', 'type', 'post_role', 'title', 'title_he', 'folder', 'files',
              'caption', 'caption_instagram', 'caption_x', 'whatsapp_text', 'alt_text', 'rabbinic_screen', 'status']
    with open(sp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', restval=''); w.writeheader(); w.writerows(sched)
    if images:
        with open(os.path.join(out_root, 'fit_log.json'), 'w') as f:
            json.dump(fitlog, f, indent=0, sort_keys=True)
        small = sorted(s for s in render.SIZES_USED if s < render.MIN_PX)
        assert not small, ('font sizes below 30 px', small)
        low = [c for c in render.CONTRAST if c[1] < render.MIN_CONTRAST]
        with open(os.path.join(out_root, 'contrast_log.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['file', 'worst_text_contrast', 'text_run', 'box'])
            w.writerows(sorted(render.CONTRAST))
        assert not low, ('text contrast below 4.5:1', low[:10])
    return occ, sched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start'); ap.add_argument('--end'); ap.add_argument('--upcoming', type=int)
    ap.add_argument('--today', help='override today (YYYY-MM-DD) for --upcoming')
    ap.add_argument('--out', default=os.path.join(HERE, 'output'))
    ap.add_argument('--sizes', default='4x5,1x1,9x16'); ap.add_argument('--no-images', action='store_true')
    ap.add_argument('--jpeg', action='store_true', help='also write .jpg copies (needed for Instagram API)')
    ap.add_argument('--bg', default=BG.DEFAULT, choices=BG.CONCEPTS, help='background concept')
    ap.add_argument('--no-intl', action='store_true', help='skip the International card')
    ap.add_argument('--intl-mode', default='carousel', choices=['carousel', 'separate'],
                    help='carousel: extra slides in the 08:00 post (default); separate: own post 12 h earlier')
    a = ap.parse_args()
    if a.upcoming:
        today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(R.ET).date()
        start, end = today, today + dt.timedelta(days=a.upcoming)
    else:
        start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    occ, sched = build(start, end, a.out, a.sizes.split(','), not a.no_images, a.jpeg, a.bg, not a.no_intl, a.intl_mode)
    print('posts: %d  schedule rows: %d  -> %s' % (len(occ), len(sched), a.out))
    if render.DROPPED:
        print('WARNING state abbreviation dropped to fit:', sorted(set(render.DROPPED)))


if __name__ == '__main__':
    main()
