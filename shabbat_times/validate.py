# -*- coding: utf-8 -*-
"""Compare generate.py's offline times with Hebcal reference times (fetched once, stored in
_validation/hebcal_reference.csv). Writes _validation/validation_table.csv and prints a summary.
Usage: python3 -B validate.py      (no network)"""
import csv, os, sys, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import calendar_rules as R, cities as CT

KIND = {'candles': 'candles', 'candles_after_tzeit': 'candles_after', 'havdalah': 'end',
        'fast_begins_alot': 'fast_begin_alot', 'fast_ends_minor': 'fast_end',
        'fast_begins_sunset': 'fast_begin_sunset', 'fast_ends_tisha_bav': 'fast_end_tb'}


def main():
    C = {c['name']: c for c in CT.cities()}
    ref = os.path.join(HERE, '_validation', 'hebcal_reference.csv')
    out = []
    worst = 0
    for r in csv.DictReader(open(ref, encoding='utf-8')):
        c = C[r['city']]
        d = dt.date.fromisoformat(r['date'])
        mine = R.time_for(KIND[r['kind']], d, c)
        h, m = map(int, r['hebcal_time'].split(':'))
        diff = (mine.hour * 60 + mine.minute) - (h * 60 + m)
        worst = max(worst, abs(diff))
        out.append(dict(city=r['city'], tz=c['tz'], date=r['date'], kind=r['kind'], hebcal=r['hebcal_time'],
                        ours=mine.strftime('%H:%M'), diff_min=diff, ok='PASS' if abs(diff) <= 1 else 'FAIL'))
    p = os.path.join(HERE, '_validation', 'validation_table.csv')
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    exact = sum(1 for o in out if o['diff_min'] == 0)
    # human-readable table
    md = ['# Validation: offline times vs Hebcal (fetched 2026-11-09)', '',
          'Hebcal REST API, `geo=pos` with the same coordinates, `b=18`, `M=on` (tzeit 8.5 deg), Diaspora. '
          'Pass = within 1 minute. Columns: Hebcal / ours.', '',
          '| City | Date | What | Hebcal | Ours | Diff (min) | Result |', '|---|---|---|---|---|---|---|']
    for o in out:
        md.append('| %s | %s | %s | %s | %s | %d | %s |' % (o['city'], o['date'], o['kind'], o['hebcal'], o['ours'], o['diff_min'], o['ok']))
    md += ['', 'Total %d checks, %d exact, worst difference %d min.' % (len(out), exact, worst)]
    open(os.path.join(HERE, '_validation', 'VALIDATION.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    cities = sorted({o['city'] for o in out}); kinds = sorted({o['kind'] for o in out})
    print('checks: %d  exact: %d  within 1 min: %d  worst diff: %d min' %
          (len(out), exact, sum(1 for o in out if abs(o['diff_min']) <= 1), worst))
    print('cities:', ', '.join(cities)); print('kinds:', ', '.join(kinds))
    for o in out:
        if o['diff_min']:
            print('  diff', o)
    return worst <= 1


def names_check():
    """Every Shabbat/Yom Tov/fast title vs the Hebcal list fetched for the same window. Parsha identity is checked
    with the Hebcal spelling kept in names.py; graphics use the brand (Shabbat Shalom series) spelling, also listed."""
    import re
    from pyluach import parshios
    import names
    ref = {}
    for line in open(os.path.join(HERE, '_validation', 'hebcal_names_2026-11-13_2027-12-31.txt'), encoding='utf-8'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) == 3 and re.match(r'\d{4}-', parts[0]):
            ref.setdefault(parts[0], []).append((parts[1], parts[2]))
    occ = R.occasions(dt.date(2026, 11, 13), dt.date(2027, 12, 31))
    bad = 0; n = 0; rows = []
    for o in occ:
        if o['kind'] == 'shabbat':
            sat = o['days'][-1]
            idx = parshios.getparsha(R.d2g(sat), israel=False)
            if idx:
                en_h, he_h = names.parsha_hebcal(idx)
            else:
                en_h, he_h = o['title_en'], o['title_he']
            he_ref = [h for t, h in ref.get(sat.isoformat(), []) if t.startswith('Parashat')]
            en_ref = [t.replace('Parashat ', '') for t, h in ref.get(sat.isoformat(), []) if t.startswith('Parashat')]
            ok = (he_ref == [he_h] and en_ref == [en_h]) if idx else (not he_ref)
            if not he_ref and sat.isoformat() > '2027-12-31':
                ok = True; en_ref = ['(after the fetched window)']
            rows.append((sat.isoformat(), o['title_en'], o['title_he'], en_h, he_h, en_ref, he_ref, ok))
        elif o['kind'] == 'fast':
            d = o['fast_date'].isoformat()
            he_ref = [h for t, h in ref.get(d, [])]
            ok = o['title_he'] in he_ref
            rows.append((d, o['title_en'], o['title_he'], '', '', [t for t, h in ref.get(d, [])], he_ref, ok))
        else:
            hes = []
            for day in o['days']:
                hes += [h for t, h in ref.get(day.isoformat(), [])]
            ok = all(any(h.startswith(part) for h in hes) for part in o['title_he'].split(' · '))
            rows.append((o['days'][0].isoformat(), o['title_en'], o['title_he'], '', '', '', hes, ok))
        n += 1; bad += 0 if ok else 1
    # Israel parsha where it differs from the Diaspora (Hebcal i=on)
    for line in open(os.path.join(HERE, '_validation', 'hebcal_intl_raw.txt'), encoding='utf-8'):
        if line.startswith('PARSHA_IL|'):
            _, d, en, he = line.strip().split('|')
            sat = dt.date.fromisoformat(d)
            idx = parshios.getparsha(R.d2g(sat), israel=True)
            en_h, he_h = names.parsha_hebcal(idx)
            ok = he_h == he and en_h.replace('’', "'") == en.replace('’', "'")
            br = names.parsha(idx)
            rows.append((d + ' (Israel)', br[0], br[1], en_h, he_h, [en], [he], ok))
            n += 1; bad += 0 if ok else 1
    for r in rows:
        if not r[-1]: print('  NAME MISMATCH', r)
    with open(os.path.join(HERE, '_validation', 'names_check.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['date', 'brand_title', 'brand_hebrew', 'hebcal_form_en', 'hebcal_form_he', 'hebcal_title',
                    'hebcal_hebrew', 'match'])
        for r in rows: w.writerow(r)
    print('titles checked: %d  mismatches: %d' % (n, bad))
    return bad == 0


IKIND = [("Candle lighting (after", 'candles_after'), ('Candle lighting', 'candles'), ('Havdalah', 'end'),
         ("Fast begins (Tisha", 'fast_begin_sunset'), ('Fast begins', 'fast_begin_alot'),
         ("Fast ends (Tisha", 'fast_end_tb'), ('Fast ends', 'fast_end')]


def intl_ref():
    out = []
    for line in open(os.path.join(HERE, '_validation', 'hebcal_intl_raw.txt'), encoding='utf-8'):
        if line.startswith('#') or line.startswith('LOC|') or line.startswith('PARSHA_IL|') or '|' not in line:
            continue
        city, when, title = line.strip().split('|', 2)
        kind = next(k for pre, k in IKIND if title.startswith(pre))
        out.append(dict(city=city, date=when[:10], hm=when[11:16], kind=kind, title=title))
    return out


def intl_check():
    """(1) Every Hebcal reference time for the 13 international cities vs time_for(); (2) the generator's actual
    international columns (World = Diaspora, Israel = Israel calendar) for the reference posts must contain exactly
    the Hebcal candle/havdalah events of that week, to the minute (+-1)."""
    C = {c['name']: c for c in CT.intl_cities()}
    ref = intl_ref()
    out = []; worst = 0
    for r in ref:
        c = C[r['city']]; d = dt.date.fromisoformat(r['date'])
        mine = R.time_for(r['kind'], d, c)
        h, m = map(int, r['hm'].split(':'))
        diff = (mine.hour * 60 + mine.minute) - (h * 60 + m)
        worst = max(worst, abs(diff))
        out.append(dict(city=r['city'], tz=c['tz'], calendar='Israel' if c['israel'] else 'Diaspora', date=r['date'],
                        kind=r['kind'], hebcal=r['hm'], ours=mine.strftime('%H:%M'), diff_min=diff,
                        ok='PASS' if abs(diff) <= 1 else 'FAIL'))
    with open(os.path.join(HERE, '_validation', 'validation_intl.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    # (2) event-level check of the generated columns
    occ = {o['id']: o for o in R.occasions(dt.date(2026, 12, 1), dt.date(2027, 10, 31))}
    refmap = {}
    for r in ref:
        if r['kind'] in ('candles', 'candles_after', 'end'):
            refmap.setdefault((r['city'], r['date']), []).append(r)
    ev_rows = []; ev_bad = 0
    for oid in ('2026-12-18_shabbat', '2027-04-21_yomtov', '2027-06-10_yomtov', '2027-10-15_yomtov'):
        o = occ[oid]
        for rr in o['rows_w'] + o['rows_il']:
            c = rr['city']; cols = o['il_cols'] if c['israel'] else o['cols']
            gen = sorted((d.isoformat(), kind, rr['times'][k].strftime('%H:%M')) for k, d, kind in cols)
            days = [o['erev']] + o['days']
            exp = sorted((r['date'], r['kind'], r['hm']) for d in days for r in refmap.get((c['name'], d.isoformat()), []))
            if not exp:
                continue
            ok = len(gen) == len(exp) and all(a[0] == b[0] and a[1] == b[1] and
                                              abs(int(a[2][:2]) * 60 + int(a[2][3:]) - int(b[2][:2]) * 60 - int(b[2][3:])) <= 1
                                              for a, b in zip(gen, exp))
            ev_bad += 0 if ok else 1
            ev_rows.append((oid, c['name'], 'Israel' if c['israel'] else 'Diaspora', ' ; '.join(' '.join(x) for x in gen),
                            ' ; '.join(' '.join(x) for x in exp), 'PASS' if ok else 'FAIL'))
    with open(os.path.join(HERE, '_validation', 'validation_intl_events.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['post', 'city', 'calendar', 'generated_columns', 'hebcal_events', 'result'])
        w.writerows(ev_rows)
    exact = sum(1 for o in out if o['diff_min'] == 0)
    md = ['', '## International cities (added Nov 9, 2026)', '',
          'Hebcal REST API with each city\'s GeoNames id (Hebcal default candle-lighting minutes: Jerusalem 40, '
          'Haifa 30, others 18; `i=on` for Israel), `M=on`, fetched via WebFetch 2026-11-09. Raw: '
          '`hebcal_intl_raw.txt`. Dates: Shabbat Dec 18-19 2026 + Asara B\'Tevet Dec 20; Pesach Apr 21-24 2027 '
          '(Israel: one day Yom Tov, then Shabbat Chol HaMoed); Shavuot Jun 10-12 2027 (Israel: 1 day, then Shabbat '
          'Parshat Nasso); Tisha B\'Av 2027 (Melbourne, London); Sukkot 2027 (Jerusalem).', '',
          '| City | Calendar | Date | What | Hebcal | Ours | Diff | Result |', '|---|---|---|---|---|---|---|---|']
    for o in out:
        md.append('| %s | %s | %s | %s | %s | %s | %d | %s |' % (o['city'], o['calendar'], o['date'], o['kind'], o['hebcal'],
                                                               o['ours'], o['diff_min'], o['ok']))
    md += ['', 'International: %d checks, %d exact, worst difference %d min.' % (len(out), exact, worst), '',
           '### Generated columns vs Hebcal events (Israel one-day Yom Tov logic)', '',
           '| Post | City | Calendar | Generated | Hebcal | Result |', '|---|---|---|---|---|---|']
    for r in ev_rows:
        md.append('| %s |' % ' | '.join(r))
    md += ['', 'Event checks: %d posts x cities, %d failures.' % (len(ev_rows), ev_bad)]
    with open(os.path.join(HERE, '_validation', 'VALIDATION.md'), 'a', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    print('intl checks: %d  exact: %d  worst diff: %d min  | event checks: %d  failures: %d' %
          (len(out), exact, worst, len(ev_rows), ev_bad))
    for o in out:
        if o['diff_min']:
            print('  diff', o)
    return worst <= 1 and ev_bad == 0


if __name__ == '__main__':
    a = main(); c = intl_check(); b = names_check()
    sys.exit(0 if (a and b and c) else 1)
