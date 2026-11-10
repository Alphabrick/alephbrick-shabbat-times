# Aleph Brick: Shabbat / Yom Tov / Fast times (automatic posting)

Business: **Aleph Brick (abc)** only. This repository builds and posts the weekly times graphics to the Facebook Page
**"Aleph Brick (Brooklyn)"** and Instagram **@aleph.brick**. It costs $0 to run (public repo = free GitHub Actions; the
Meta Graph API is free). Nothing posts until the repository variable `LIVE` is `1`.

What runs:
- Sunday 06:03 UTC: `generate.py --upcoming 14 --jpeg` makes the next 14 days of graphics, then `validate.py`
  (times vs stored Hebcal reference, 0 min tolerance today) and the Divine-Name scan must pass.
- Every 15 minutes: `automation/post_meta.py` posts any row of `shabbat_times/output/schedule.csv` that is due:
  - **primary**: Friday / erev Yom Tov 8:00 AM ET, one carousel = 28 US cities + the International slide(s)
    (13 cities, local time, Israel on the Israel calendar). Fasts: see README in `shabbat_times/`; a fast card that
    falls on the same morning is merged into that post.
  - It refuses to post inside the Shabbat / Yom Tov pause (Brooklyn 11223: candle lighting -60 min until
    sunset + 72 + 60 min). The generator asserts the same rule.
- After each primary post, a GitHub issue with the WhatsApp text and image links is opened; GitHub emails it to you.
  Paste it into the ABC WhatsApp Channel / groups (WhatsApp has no free posting API).

Secrets live only in GitHub Secrets. Never put a token in a file, email, chat or commit.

---

## Setup, click by click (about 1.5 to 2 hours, once)

Do every step in the **ABC Chrome profile**. Steps marked **[LOGIN]** need an existing login that only the owner
has (or a sign-in code sent to an ABC inbox). Everything else is clicking inside an already signed-in session.

### A. GitHub account and repository (about 20 min)

1. **[LOGIN]** Open `https://github.com/signup` (or `https://github.com/login` if ABC already has a GitHub account).
   - Email: **alephbrick@gmail.com** (the ABC Google identity in the Brand Bible). Username: `alephbrick`
     (or `alephbrick-co` if taken). Use a new password and save it in the ABC password manager.
   - Enter the verification code GitHub emails to alephbrick@gmail.com (open Gmail in the same ABC profile).
   - Turn on two-factor authentication when GitHub asks (Settings > Password and authentication). Save the recovery
     codes in the ABC Google Drive, not in this repo.
2. Top right **+** > **New repository**.
   - Owner: the ABC account. Repository name: `alephbrick-shabbat-times`.
   - Description: `Aleph Brick Shabbat / Yom Tov times (automatic posting)`.
   - Visibility: **Public** (free unlimited Actions minutes, and Instagram must be able to fetch the images).
   - Leave "Add a README", ".gitignore" and "license" **unticked**. Click **Create repository**.
3. On the empty repository page click **uploading an existing file**.
   - On your computer, open the `repo_ready` folder. Show hidden files first so `.github` and `.gitignore` are
     visible (Mac Finder: **Cmd+Shift+.**; Windows Explorer: **View > Show > Hidden items**).
   - Select **everything inside** `repo_ready` (`.github`, `.gitignore`, `README.md`, `shabbat_times`, `tools`) and drag
     it onto the browser page. Wait until every file is listed (about 35 files; the web limit is 100 per upload).
   - Commit message: `Initial upload`. Choose **Commit directly to the main branch**. Click **Commit changes**.
   - Check that `.github/workflows/shabbat-times.yml` is visible in the repository. If the `.github` folder is missing,
     click **Add file > Create new file**, type the name `.github/workflows/shabbat-times.yml`, paste the file's
     contents from `repo_ready/.github/workflows/shabbat-times.yml`, and click **Commit changes**.
4. **Settings > Actions > General**
   - Actions permissions: **Allow all actions and reusable workflows**.
   - Workflow permissions: **Read and write permissions**. Click **Save**.
5. **Settings > Secrets and variables > Actions > Variables tab > New repository variable**, three times:
   - `LIVE` = `0` (dry run: logs what it would post, posts nothing)
   - `IG_STORY` = `0` (set `1` later to also post the 9:16 as an Instagram story)
   - `META_GRAPH_VERSION` = the current version shown at `https://developers.facebook.com/docs/graph-api/changelog`
     (for example `v21.0`)
6. **Watch** (top of the repository) > **All Activity**, so GitHub emails you the WhatsApp issues. (To receive them at
   another address, add a Gmail forwarding filter in alephbrick@gmail.com for mail from notifications@github.com.)
7. **Actions** tab. If asked, click **I understand my workflows, go ahead and enable them**. Click
   **ABC Shabbat times** > **Run workflow** > branch `main` > **Run workflow**. Wait 3 to 5 minutes for the green tick.
   - Open the run: "Generate next 14 days + checks" must show `checks: ... worst diff: 0 min`, `intl checks: ...`,
     `titles checked: ... mismatches: 0` and `hits: 0`.
   - "Post due rows" shows `live: False` and `DRY RUN POST` lines, or `due: 0`.
   - A new commit "Shabbat times: generate/post log" adds `shabbat_times/output/`.

### B. Meta: app, never-expiring Page token and IDs (about 45 to 60 min)

1. **[LOGIN]** Sign in to Facebook in the ABC profile as the person who administers **Aleph Brick (Brooklyn)**
   (the alephbrickco@gmail.com identity). Open `https://business.facebook.com/settings`.
   - Top left: pick the **Aleph Brick** business portfolio.
   - **Accounts > Pages**: "Aleph Brick (Brooklyn)" must be listed.
   - **Accounts > Instagram accounts**: @aleph.brick must be listed. If not: **Add** > **[LOGIN]** sign in to
     @aleph.brick (it must be a Professional account linked to the Page).
2. Open `https://developers.facebook.com/apps` > **Create app**.
   - Use case: **Other** > Next. App type: **Business** > Next.
   - App name `ABC Shabbat Times`; app contact email `alephbrickco@gmail.com`; Business portfolio: **Aleph Brick**.
     Click **Create app** and **[LOGIN]** re-enter the Facebook password if asked.
3. In the app: **App settings > Basic**: Privacy Policy URL `https://www.alephbrick.com/policies/privacy-policy`,
   category **Education**, app icon = the ABC logo. **Save changes**.
   Then **Add product** > **Instagram** > **API setup with Facebook login** > Set up.
4. Back in **Business settings > Users > System users > Add**: name `abc-shabbat-times-bot`, role **Admin** >
   **Create system user**. (No "System users" item? You need to be a full admin of the portfolio; otherwise use the
   alternative token in step 8.)
5. Select `abc-shabbat-times-bot` > **Assign assets**:
   - **Apps**: ABC Shabbat Times > **Manage app** (full control).
   - **Pages**: Aleph Brick (Brooklyn) > **Content** (create, edit and delete content) only.
   - **Instagram accounts**: @aleph.brick > **Content** only. Click **Save changes**.
6. With the system user still selected: **Generate new token**.
   - App: **ABC Shabbat Times**. Token expiration: **Never**.
   - Permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`,
     `instagram_content_publish`, `business_management`. Click **Generate token**. Copy it (shown once). Do not save it
     anywhere except the next two steps.
7. Open `https://developers.facebook.com/tools/explorer`.
   - Paste the token into **Access Token**. In the query box type `me/accounts` and click **Submit**.
   - In the answer, find `"name": "Aleph Brick (Brooklyn)"`. Copy its `"id"` (= **META_PAGE_ID**) and its
     `"access_token"` (= **META_PAGE_TOKEN**; a Page token made from a never-expiring system-user token does not expire).
   - Query `<META_PAGE_ID>?fields=instagram_business_account` > **Submit**. Copy `instagram_business_account.id`
     (= **META_IG_USER_ID**).
   - Optional check: `https://developers.facebook.com/tools/debug/accesstoken` > paste the Page token > **Debug**:
     "Expires: Never" and the permissions above.
8. *Alternative token (only if step 4 is not possible):* in the Graph API Explorer pick the app, **User Token**, add the
   six permissions, **Generate Access Token** **[LOGIN]**, then open the Access Token Debugger and click **Extend Access
   Token** (60-day user token). Paste the extended token back into the Explorer and run `me/accounts`; the Page
   `access_token` it returns does not expire on its own (it stops working if the admin's password or Page role
   changes; the workflow then fails visibly and you repeat this step).
9. **App mode**: at the top of the app dashboard switch **Development** to **Live**. Posts made by an app in
   Development mode are visible only to people with a role on the app. If Meta asks for App Review or business
   verification before going Live, complete it; if that is refused, use the Make route (b) in `shabbat_times/AUTOMATION.md`.

### C. Put the three secrets into GitHub (5 min)

**Settings > Secrets and variables > Actions > Secrets tab > New repository secret**, three times:
`META_PAGE_TOKEN`, `META_PAGE_ID`, `META_IG_USER_ID`. Paste each value, **Add secret**. Then clear your clipboard.

### D. Dry run, approval, go live (10 min)

1. **Actions > ABC Shabbat times > Run workflow** again. Still `live: False`. Check the log for errors.
2. Owner visual approval of the new backgrounds and the International card (contact sheets in the ABC Drive).
3. Set the variable `LIVE` = `1`. From the next due row on, the workflow posts by itself:
   - Facebook: the 4:5 slides as one multi-photo post with the row's Facebook caption.
   - Instagram: the 4:5 slides as a carousel (JPEG) with the Instagram caption (+ 9:16 story if `IG_STORY` = `1`).
   - Each post is written to `shabbat_times/output/posted.log`, so nothing posts twice.
4. Pause: set `LIVE` = `0`. Stop everything: **Actions > ABC Shabbat times > ... > Disable workflow**.

### Upkeep
- GitHub disables scheduled workflows after 60 days without commits; the workflow's own weekly commit prevents that.
- If a run fails with an OAuth error, re-do B.7 (or B.8) and update `META_PAGE_TOKEN`.
- Each December, add fresh Hebcal reference times for the new year to `shabbat_times/_validation/` (see `AUTOMATION.md`).
