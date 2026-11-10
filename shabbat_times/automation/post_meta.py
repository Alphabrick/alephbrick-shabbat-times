# -*- coding: utf-8 -*-
"""Post due Shabbat-times rows to the Aleph Brick Facebook Page and Instagram via the Meta Graph API.
Standard library only. DRY RUN unless the environment variable LIVE=1 is set.

Meant to run inside GitHub Actions (see shabbat-times.yml) every 15 minutes:
  - reads output/schedule.csv, picks rows whose time is in [now - WINDOW, now] and not yet in posted.log
  - refuses anything inside the Shabbat / Yom Tov pause (Brooklyn 11223, candle lighting -60 .. sunset+72+60)
  - rows: post_role = primary (28 US cities), international (13 world/Israel cities, local time, goes out 12 h
    earlier so it is still before Shabbat in Israel and Melbourne), story re-share (9:16 only)
  - FB: 4:5 slides as one multi-photo post (the row's Facebook caption)
  - IG: 4:5 slides as a carousel (or single image), JPEG copies served from the public repo (raw URL)
  - optional: 9:16 as an Instagram story (IG_STORY=1)
  - WhatsApp has no posting API: the workflow opens a GitHub issue with whatsapp.txt so the owner gets an email

Secrets (GitHub > Settings > Secrets and variables > Actions), never in the repo:
  META_PAGE_TOKEN  long-lived Page access token (or System User token) for "Aleph Brick (Brooklyn)"
  META_PAGE_ID     the Page id
  META_IG_USER_ID  the Instagram professional account id linked to the Page (@aleph.brick)
  RAW_BASE         e.g. https://raw.githubusercontent.com/<owner>/<repo>/main/shabbat_times/output
"""
import csv, datetime as dt, json, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import calendar_rules as R

GRAPH = 'https://graph.facebook.com/' + os.environ.get('META_GRAPH_VERSION', 'v21.0')   # set the repo variable to the current version
WINDOW_MIN = int(os.environ.get('WINDOW_MIN', '45'))
LIVE = os.environ.get('LIVE') == '1'
LOG = os.path.join(ROOT, 'output', 'posted.log')


def api(path, params):
    data = urllib.parse.urlencode(params).encode()
    if not LIVE:
        print('  DRY RUN POST', path, {k: (v[:60] + '...' if isinstance(v, str) and len(v) > 60 else v)
                                       for k, v in params.items() if k != 'access_token'})
        return {'id': 'dry_run'}
    with urllib.request.urlopen(urllib.request.Request(GRAPH + path, data=data), timeout=60) as r:
        return json.loads(r.read().decode())


def get(path, params):
    if not LIVE:
        return {'status_code': 'FINISHED'}
    q = urllib.parse.urlencode(params)
    with urllib.request.urlopen(GRAPH + path + '?' + q, timeout=60) as r:
        return json.loads(r.read().decode())


def wait_ready(container, tok):
    for _ in range(20):
        st = get('/%s' % container, {'fields': 'status_code', 'access_token': tok}).get('status_code')
        if st == 'FINISHED':
            return
        time.sleep(6)
    raise RuntimeError('IG container not ready: %s' % container)


def post_row(row, env):
    tok, page, ig, raw = env['META_PAGE_TOKEN'], env['META_PAGE_ID'], env.get('META_IG_USER_ID'), env['RAW_BASE']
    folder = os.path.join(ROOT, 'output', row['folder'])
    files = [f for f in row['files'].split(' | ') if '_4x5_' in f]
    story = [f for f in row['files'].split(' | ') if '_9x16_' in f]
    cap_ig = (row.get('caption_instagram') or '').strip()
    if row['post_role'] in ('primary', 'international'):
        # Facebook: multi-photo post
        ids = []
        for f in files:
            r = api('/%s/photos' % page, {'url': raw + '/' + f, 'published': 'false', 'access_token': tok})
            ids.append(r['id'])
        params = {'message': row['caption'], 'access_token': tok}
        for i, mid in enumerate(ids):
            params['attached_media[%d]' % i] = json.dumps({'media_fbid': mid})
        api('/%s/feed' % page, params)
        # Instagram: carousel of JPEGs (single image if only one slide)
        if ig:
            jpgs = [raw + '/' + f[:-4] + '.jpg' for f in files]
            if len(jpgs) == 1:
                c = api('/%s/media' % ig, {'image_url': jpgs[0], 'caption': cap_ig, 'access_token': tok})['id']
            else:
                kids = [api('/%s/media' % ig, {'image_url': u, 'is_carousel_item': 'true', 'access_token': tok})['id']
                        for u in jpgs]
                c = api('/%s/media' % ig, {'media_type': 'CAROUSEL', 'children': ','.join(kids), 'caption': cap_ig,
                                          'access_token': tok})['id']
            wait_ready(c, tok)
            api('/%s/media_publish' % ig, {'creation_id': c, 'access_token': tok})
    if ig and story and (os.environ.get('IG_STORY') == '1' or row['post_role'].startswith('story')):
        c = api('/%s/media' % ig, {'image_url': raw + '/' + story[0][:-4] + '.jpg', 'media_type': 'STORIES',
                                   'access_token': tok})['id']
        wait_ready(c, tok)
        api('/%s/media_publish' % ig, {'creation_id': c, 'access_token': tok})


def main():
    env = dict(os.environ)
    now = dt.datetime.fromisoformat(os.environ['NOW']) if os.environ.get('NOW') else dt.datetime.now(R.ET)  # NOW: test override
    done = set(open(LOG).read().split()) if os.path.exists(LOG) else set()
    wins = R.blackout_windows(now.date() - dt.timedelta(days=3), now.date() + dt.timedelta(days=3))
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'output', 'schedule.csv'), encoding='utf-8')))
    due = []
    for r in rows:
        t = dt.datetime.fromisoformat(r['post_datetime_iso'])
        key = '%s|%s' % (r['folder'], r['post_role'][:7])
        if key in done or not (now - dt.timedelta(minutes=WINDOW_MIN) <= t <= now):
            continue
        if R.in_blackout(now, wins):
            print('SKIP (inside Shabbat/Yom Tov pause):', key); continue
        due.append((key, r))
    print('%s  due: %d  live: %s' % (now.isoformat(timespec='minutes'), len(due), LIVE))
    for key, r in due:
        if not env.get('META_PAGE_TOKEN') and LIVE:
            sys.exit('missing secrets')
        post_row(r, env if LIVE else dict(env, META_PAGE_TOKEN='x', META_PAGE_ID='PAGE', META_IG_USER_ID='IG',
                                          RAW_BASE=env.get('RAW_BASE', 'https://example.invalid')))
        if LIVE:
            with open(LOG, 'a') as f:
                f.write(key + '\n')
        # hand-off for WhatsApp (no API): print the folder so the workflow can open an issue
        if r['post_role'] == 'primary':
            print('WHATSAPP_READY', r['folder'])


if __name__ == '__main__':
    main()
