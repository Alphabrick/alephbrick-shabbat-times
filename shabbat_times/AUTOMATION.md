# Aleph Brick Shabbat / Yom Tov / Fast times: zero-cost automation

Business: Aleph Brick (abc). Social identity: the Facebook Page "Aleph Brick (Brooklyn)" and Instagram @aleph.brick,
both under alephbrickco@gmail.com. Nothing in this folder has been posted, scheduled, emailed or pushed.

**Status (Nov 9, 2026): route (a) is prepared for go-live** (owner: "Yes, don't ask, do"). The exact folder to upload is
`repo_ready/` (workflow, scripts, fonts, validation data, requirements; ~35 files). Its `README.md` has the
click-by-click steps for the GitHub account/repo, Actions settings, the never-expiring Meta Page token, the IDs and the
secrets. Rebuild it after any code change with `sh automation/make_repo_ready.sh`. The steps that need an owner login
(GitHub sign-up/sign-in with alephbrick@gmail.com; Facebook/Meta Business as the Page admin; Instagram if it must be
re-linked) are marked [LOGIN] there and are done in the ABC Chrome profile. The International slides ride in the same 8:00 AM post
as the US slides (one carousel); `--intl-mode separate` would make them a separate `international` row 12 h earlier.

## What has to happen every week

1. Work out the times. `generate.py` does this offline (pyluach calendar plus a NOAA solar port). It needs no API and no
   credits. The output is deterministic, so the year 2026-11-13 to 2027-12-31 is already generated in `output/`.
2. Host the images somewhere public. Instagram's API only accepts an image URL, not an upload.
3. Post at the scheduled time (`output/schedule.csv`):
   - Friday 8:00 AM ET, or the morning of erev Yom Tov.
   - Minor fasts at 8:00 PM ET the evening before. If that evening is inside a Shabbat/Yom Tov pause, the post moves
     to 8:30 AM before the pause, and a story re-share goes out after the pause ends.
   - Tisha B'Av at 8:00 AM ET on erev Tisha B'Av.
   - Nothing is posted inside candle lighting −60 min → sunset + 72 + 60 min (Brooklyn 11223, Yom Tov treated like
     Shabbat). The generator asserts this rule, and the poster checks it again.
4. WhatsApp. WhatsApp Channels and groups have no posting API, and the WhatsApp Business Cloud API charges per
   conversation for marketing messages. So WhatsApp is always a 30-second manual post: copy `whatsapp.txt` (it also
   works on kosher phones, which show no images) and attach the 1:1 or 4:5 PNG if you want.

## The four routes compared

| Route | Running cost | One-time setup | Ongoing effort | Fully automatic? | Main risks |
|---|---|---|---|---|---|
| **(a) GitHub Actions + Meta Graph API (recommended)** | $0 (public repo: unlimited Actions minutes; Graph API is free) | ~1.5–2 h, owner logins needed for Meta and GitHub | ~30 s/week for WhatsApp (GitHub emails you the text) | FB + IG yes; WhatsApp manual | The Page token can be invalidated (password change, role change), so the workflow fails visibly and you re-issue the token. GitHub cron can run 5–30 min late (the 45-min window absorbs this). |
| (b) Social Jobs Google Sheet → ABC Make (existing FB poster v11 / Publisher Gate v3 / IG adapter) | Make operations: about 5–10 ops per post × ~70 posts a year, plus the trigger's runs. Schedule it at 08:00 and 20:00 ET (~60 runs/month), **not** every 15 min (~2,900 ops/month). Small next to ABC's planned 20–30k ops/month. | ~1 h if the Sheet → Publisher Gate pipeline is live: add rows, upload PNG/JPEG to the ABC Drive with public links | Same WhatsApp step | Yes, through the existing approval gate | Uses Make credits. Drive links must be public for IG. Rows must be appended (manually once a year, or from (a) with a Google service account). |
| (c) Google Apps Script + Google Slides template | $0 (consumer quotas are ample) | High, 6–10 h: port the zmanim maths to JS (or read the pre-computed CSV), build a Slides template with 28×3 text boxes, export via the Slides thumbnail API (max 1600 px), then post with UrlFetchApp to the Graph API | Same WhatsApp step | Yes | Re-builds layout logic the Python generator already has. Slides typography is weaker (no RAQM Hebrew control). Uses the owner's Google account quotas. |
| (d) Canva: Connect API autofill, or Bulk Create | Autofill API requires **Canva Enterprise** (paid). Bulk Create needs Pro/Teams (manual). | Medium: brand template with ~60 data fields | Manual: upload the year's CSV in Bulk Create, download ~70 designs, schedule them. Still needs a poster. | No (Bulk Create), or paid (Enterprise) | Not zero-cost or not automatic. Canva is under the owner's personal login (an approved exception), and the data-field limits for a 28-city table are untested. |

**Recommendation: (a).** It is the only route that is both free and fully automatic for Facebook and Instagram, and
it runs the exact generator and checks used here. If the owner wants every automated post to pass through the
existing ABC Make Publisher Gate (the Brand Bible says template-approved automated posts publish through the
approval-gated pipeline), use **(a) for generating and hosting plus (b) for posting**: Actions appends the week's rows
to the Social Jobs sheet, and Make posts the approved ones. This costs a few hundred Make ops a year. *Owner decision.*

## Step-by-step setup for (a)

The authoritative, click-by-click version is `repo_ready/README.md`. Summary:

All steps use Aleph Brick identities only (alephbrickco@gmail.com for Meta). Secrets go in GitHub Secrets and never
in a file.

### 1. GitHub (about 15 min)
1. Create a GitHub account for ABC, or use an existing one. Create a **public** repository, for example
   `alephbrick-shabbat-times`. It must be public for two reasons: Actions minutes are unlimited only on public repos
   (a private repo on GitHub Free gets 2,000 min/month, and a 15-minute cron uses about 2,900), and Instagram must be
   able to fetch the images from a public URL. The repo holds only public post images and code, never secrets.
2. Copy this folder into the repo as `shabbat_times/`. Copy `automation/shabbat-times.yml` to
   `.github/workflows/shabbat-times.yml`.
3. Under Settings → Actions → General → Workflow permissions, choose "Read and write".
4. Under Settings → Secrets and variables → Actions → **Variables**, add `LIVE` = `0`. The workflow then runs in dry
   run: it logs what it would post and posts nothing.

### 2. Meta app and Page token (about 45–60 min, owner login required)
1. Sign in to developers.facebook.com as the alephbrickco@gmail.com identity that administers the Page. Create an
   app of type **Business** named "ABC Shabbat Times" and attach it to the ABC business portfolio.
2. Add the products "Facebook Login for Business" and "Instagram Graph API".
3. Permissions needed: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`,
   `instagram_content_publish`, `business_management`. Apps in Development mode can use these for people who have a
   role on the app. If Meta asks for App Review or business verification, complete it or fall back to route (b).
4. Preferred token: Business Settings → Users → **System users** → add one (Admin) → assign the Page and the
   Instagram account → Generate token for the app, with the permissions above and expiry "Never".
   Alternative token: Graph API Explorer → user token → exchange it for a long-lived token (60 days) → call
   `/me/accounts` → take the Page `access_token`. A Page token from a long-lived user token does not expire on its
   own.
5. Get the IDs: `GET /me/accounts` gives the Page id. `GET /{page-id}?fields=instagram_business_account` gives the
   IG user id.
6. In GitHub → Secrets, add `META_PAGE_TOKEN`, `META_PAGE_ID` and `META_IG_USER_ID`.

### 3. Dry run and go-live (about 15 min)
1. Actions → "ABC Shabbat times" → Run workflow (manual). It generates the next 14 days with JPEG copies, re-runs
   `validate.py` and dry-runs the poster. Check the log.
2. Owner approval: approve the template once (standing approval), or keep per-post approval through route (b).
3. Set the variable `LIVE` = `1`. From then on, every 15 minutes the workflow posts any row that is due:
   - Facebook: the 4:5 slides as one multi-photo post with the Facebook caption.
   - Instagram: the 4:5 slides as a carousel (JPEG) with the Instagram caption. Add `IG_STORY=1` to also post the
     9:16 as a story.
   - Every post is appended to `output/posted.log`, so nothing posts twice.
   - A GitHub **issue** opens with the WhatsApp text and image links. GitHub emails it to you, and you paste it into
     the ABC WhatsApp Channel and groups (about 30 s).
4. To pause posting, set `LIVE` = `0`. To stop everything, disable the workflow.

### 4. Yearly upkeep
- The weekly Sunday run generates 14 days ahead, so the year rolls forward on its own. Once a year (December), run
  `python3 -B generate.py --start <Jan 1> --end <Dec 31>` locally if you want the full year to preview.
- `validate.py` needs no network. To re-check against Hebcal for a new year, fetch fresh reference times and add them
  to `_validation/hebcal_reference.csv`.
- GitHub turns off scheduled workflows in public repos after 60 days with no repository activity. The workflow's own
  commits (posted.log, generated files) count as activity.

## Notes
- Graph API version: `automation/post_meta.py` pins `v21.0`. Bump it to the current version during setup.
- Instagram publishing accepts JPEG only, so the workflow passes `--jpeg`. Carousels take up to 10 items. Meta caps
  API-published posts per 24 h; this uses at most 3.
- The 1:1 set is two slides per table (Northeast & Mid-Atlantic; Midwest/South/West), sized for X, WhatsApp and other square feeds.
