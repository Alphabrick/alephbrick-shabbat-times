# Aleph Brick: Shabbat / Yom Tov / Fast-day times (DRAFT, files only)

Torah-only posts with candle lighting and Shabbat/Yom Tov end (or fast begins/ends) for **28 US cities**, plus a
separate **International card** for 13 cities in local time (Israel on the Israel calendar). Nothing is posted,
scheduled or emailed from here. Posting setup: `AUTOMATION.md`; ready-to-upload repository: `repo_ready/`.

## Run
```
pip install -r requirements.txt          # pyluach, pillow (needs RAQM / libraqm for Hebrew), numpy
python3 -B generate.py --start 2026-11-13 --end 2027-12-31     # whole range (~15 min)
python3 -B generate.py --upcoming 14 --jpeg                     # next 14 days (what the GitHub workflow runs)
python3 -B generate.py ... --bg night                           # another background (dusk | table | night | stone)
python3 -B generate.py ... --no-intl                            # US card only
python3 -B validate.py                                          # offline: times vs stored Hebcal reference + names
python3 -B contact.py                                           # contact sheets + _qa sheets
python3 -B board.py dusk                                        # background comparison boards -> _board/
sh automation/make_repo_ready.sh                                # rebuild repo_ready/
```
No network or API at runtime. Fonts (Poppins, Lora, Frank Ruhl Libre, all SIL OFL) and the logo are in `assets/`.

## Backgrounds (v2, Nov 9 2026: owner "text and layout are great; the look is bland")
The text and table layout are unchanged. They now sit on a rich, procedurally drawn background (`backgrounds.py`,
Pillow + numpy, no paid tools, no stock, deterministic) behind a translucent panel with a gold rim.
Comparison board: `_board/board_concepts.png`; seasonal board: `_board/board_seasonal_dusk.png`.

| Concept | Idea | Concept | Distinct | Brand fit | Legibility | 9:16 | Total |
|---|---|---|---|---|---|---|---|
| **(a) dusk (DEFAULT)** | warm dusk sky over a brick-built Jerusalem Old City skyline (walls, towers, flat-roofed houses, lit arched windows, cypresses), first stars | 5 | 5 | 5 | 5 | 5 | **25** |
| (c) night | deep navy star field, three bright stars (nightfall), gold studded-brick border | 4 | 4 | 4 | 5 | 4 | 21 |
| (d) stone | Jerusalem-stone ashlar wall with drafted margins, parchment noise, faint stud pattern | 4 | 3 | 4 | 4 | 3 | 18 |
| (b) table | soft-blurred Shabbat table: brick candlesticks, velvet challah cover, wine cup, bokeh | 4 | 3 | 4 | 4 | 3 | 18 |

**Why (a) won:** it is the only concept that says "Aleph Brick" without a word: Jerusalem, the home of the Beit
Hamikdash, literally built from studded bricks. It also gives the 9:16 story a strong bottom (the skyline stands on
the brick footer band), works in every season (the sky palette changes) and keeps the cream table panel the owner
already approved. (c) is a close second and the best fit if the owner prefers an all-dark look. (b) and (d) are
busier behind the header and less distinctive at phone size. Any concept: `--bg <name>`.

Seasonal variants (automatic, `generate.variant()`): Shabbat Chanukah (9-light brick chanukiah: 8 lights + raised
shamash), Sukkot (schach + hanging fruit), Shemini Atzeret/Simchat Torah (bunting), Pesach (full moon of 15 Nisan,
spring blossoms), Shavuot (greenery garland, flowers), Rosh Hashanah (pomegranates, apples, honey), Yom Kippur
(silver-white, no props), fasts (muted grey dusk, no lit windows), Tisha B'Av (darkest, broken wall). Shabbat Chol
HaMoed uses its festival's variant.

Rules kept in every scene: objects and places only; no people or faces; no domes, spires, minarets or crosses (windows
are plain arched slots; flowers have 5 petals); no 7-branch menorah. Every seasonal prop is checked against the text
boxes and is skipped if it would sit behind text.

**Contrast:** every text run is measured against the real pixels behind it (worst of the 2nd/98th luminance
percentile) and the build fails below 4.5:1. Worst value in the whole set: see `output/contrast_log.csv`.

## International card (new)
- Cities (`cities.py`): Toronto, Montreal, Mexico City, Buenos Aires, London, Paris, Antwerp, Johannesburg, Melbourne
  (Diaspora calendar) and Jerusalem, Tel Aviv, Bnei Brak, Haifa (Israel calendar). The list covers the largest
  communities by country; Manchester (large Haredi community) and Sydney are the natural next additions.
- All times are **local** to each city; the lockup reads "INTERNATIONAL · LOCAL TIME" and the notes repeat it.
- Israel: one day of Yom Tov; Israel parsha. When Israel differs, the Israel section is labelled, e.g.
  "ISRAEL · SHAVUOT · PARSHAT NASSO", "ISRAEL · PARSHAT BEHA'ALOTECHA" (Jun 12 - Jul 17 2027), "ISRAEL · PESACH ·
  SHABBAT CHOL HAMOED PESACH", and the Israel columns are its own (e.g. Pesach: candles Wed, ends Thu, candles Fri,
  ends Sat).
- Candle lighting (as the live Hebcal API returns, verified): Jerusalem 40 min, Haifa 30, Tel Aviv and Bnei Brak 20,
  everywhere else 18. (The first pass assumed 18 for Tel Aviv/Bnei Brak and 7.083° for Israeli fast ends; Hebcal
  showed 20 min and 3.7°, so both were changed and re-validated.) Israel minor fasts end at 3.7°; elsewhere 7.083°.
  Tisha B'Av 6.45° everywhere.
- Layout: ordinary weeks and fasts: 4:5 and 9:16 one slide (world + Israel in two-column halves like the US card),
  1:1 two slides (world | Israel). Multi-day Yom Tov weeks (3-4 time columns): full-width rows with two-line heads
  ("CANDLES / WED 4/21", "AFTER / THU 4/22"); 4:5 and 9:16 become two slides (world | Israel) and 1:1 three
  (Americas | Europe · Africa · Australia | Israel). Text never below 30 px (asserted). Country codes are shown when
  they fit and dropped for the whole section when they do not (captions always name the country).
- Posting (default `--intl-mode carousel`): the International slide(s) ride in the **same Friday / erev Yom Tov
  8:00 AM ET post**, right after the US slide(s) (Facebook multi-photo, Instagram carousel, 1:1 and 9:16 files too). This
  keeps the owner-approved single 08:00 slot and gives 0 clashes in the cross-series check. Trade-off: 8:00 AM ET is
  already Friday night (Shabbat) in Melbourne and, in winter, about 1 h before candle lighting in Jerusalem.
  `--intl-mode separate` makes it its own post 12 h earlier (normally Thursday 8:00 PM ET); that collided with other
  series (Chanukah ads Thu 8:30 PM, Torah Trivia Tue 6:30 PM, feed cap) in the cross-series check, so it is off.

## One slot per morning (coordinator, Nov 9)
When a fast-day card is pulled in front of a pause onto the same morning as the Shabbat / Yom Tov post (Fri Dec 18 2026,
Asara B'Tevet; Fri Oct 1 2027, Tzom Gedaliah), it is merged into the 8:00 AM post as extra carousel slides; its text is
appended to the captions and to `whatsapp.txt`. The fast's 9:16 story re-share after the pause stays (Sat Dec 19
8:00 PM; Sun Oct 3 2027 9:00 PM). `generate.merge_same_slot()`; `post.json` records the merge in both folders.
Cross-series check (`social_52/_crosscheck/cross_series_check.py --actual`, Nov 9 2026): pause 0, erev-late 0, collisions 0, clashes inside this schedule 0, feed-cap 0, spelling 0 (exit 0).

## Output (`output/<post-date>_<kind>_<name>/`)
- `*_4x5_s1.png` (+ `s2` for multi-day Yom Tov), `*_9x16_s*.png`, `*_1x1_s1a/s1b.png`: US card, as before.
- `*_intl_4x5_s1.png`, `*_intl_9x16_s1.png`, `*_intl_1x1_s1a/s1b.png`: International card.
- Captions: `caption_facebook.txt` (US list **plus an International section**), `caption_instagram.txt`,
  `caption_x.txt`, `alt_text.txt`, `whatsapp.txt` (US tables **plus an International section**), and
  `caption_intl_facebook.txt`, `caption_intl_instagram.txt`, `caption_intl_x.txt` (≤270), `alt_text_intl.txt`.
- `times.csv`, `times_intl.csv`, `post.json` (incl. international post time, Israel label, background).
- `output/schedule.csv`: one row per post (`primary`, incl. the International slides; story re-shares after a pause).
  With `--intl-mode separate` there is also an `international` row.
  `output/fit_log.json` (sizes + contrast per image), `output/contrast_log.csv`.

## Rules implemented
| Item | Rule (matches Hebcal) |
|---|---|
| Candle lighting | sunset − 18 min (Israel: Jerusalem 40, Haifa 30, Tel Aviv/Bnei Brak 20); sunset seconds dropped first |
| Shabbat / Yom Tov end | tzeit, sun 8.5° below the horizon |
| 2nd night Yom Tov / Yom Tov after Shabbat | "after" = tzeit 8.5° of the previous day; Friday Yom Tov into Shabbat = normal candle lighting |
| Minor fasts | begin at alot 16.1°; end at tzeit 7.083° (Israel: 3.7°) |
| Tisha B'Av | begins at sunset, ends at 6.45° (what the live Hebcal API returns, Diaspora and Israel) |
| Calendar | pyluach: Diaspora for the US and world cities, Israel for the Israel section |
| Names | brand spellings = the Shabbat Shalom series (owner ruling Nov 9): e.g. בחוקותי, קדושים, מצורע, Bereishit, Shemini, Acharei Mot |
| Posting | Fri / erev Yom Tov 8:00 AM ET (US + International slides in one post); minor fast 8:00 PM ET the evening before (if that is in a pause: merged into the 8:00 AM post of that morning, + 9:16 re-share after the pause); Tisha B'Av 8:00 AM erev. Never inside candle lighting −60 → sunset + 72 + 60 (Brooklyn 11223), asserted. |
| Rabbeinu Tam | not shown (owner ruling Nov 9) |
| Greetings (captions, WhatsApp text and alt text only; graphics unchanged) | Owner ruling Nov 9, 2026 (20:10 ET): Shabbat posts rotate **Shabbat Shalom / Gut Shabbos / Git Shabbos** by week (`GREET_ROTATION`, counted from Fri 2026-11-13); in a Gut/Git Shabbos week the caption text says "Shabbos" throughout (`shabbos_spelling`, hashtags untouched). A Yom Tov run that includes Shabbat gets one combined greeting: Pesach I (Apr 21), Shavuot (Jun 10), Sukkot (Oct 15) and Shemini Atzeret (Oct 22) **Shabbat Shalom & Chag Sameach**; Rosh Hashanah (Oct 1) **Shana Tova & Shabbat Shalom**. Regenerated Nov 9 PM (ABC-SOC-RULES-004): all 577 PNGs byte-identical to the previous run (md5), 67 schedule rows with the same times and files; only text changed. |

## Validation
- US: 145 checks vs Hebcal, all exact (unchanged).
- International: **165 checks**, 13 cities, 3+ dates each (Shabbat Dec 18-19 2026 + Asara B'Tevet; Pesach Apr 21-24
  2027 where Israel differs; Shavuot Jun 10-12 2027 where Israel differs), plus Tisha B'Av (Melbourne, London,
  Jerusalem), Tzom Tammuz and Sukkot (Jerusalem). **All 165 match to the minute.** Plus 40 event-level checks that the
  generated World/Israel columns of four posts contain exactly Hebcal's candle/havdalah events: 0 failures.
  `_validation/VALIDATION.md`, `validation_intl.csv`, `validation_intl_events.csv`, raw data `hebcal_intl_raw.txt`.
- Names: 73 titles (67 posts + 6 Israel parshiyot) checked against Hebcal's parsha identity: 0 mismatches
  (`_validation/names_check.csv` lists the brand spelling next to Hebcal's).

## Checks run
- Divine-Name scan: 0 hits. Fonts ≥ 30 px (asserted). Contrast ≥ 4.5:1 for every text run (asserted).
- Visual QA at full size, 390 px and 150 px (`_qa/`), contact sheets `contact_sheet.png`,
  `contact_sheet_international.png`.
- Rabbinic screen (abc-rabbinic-review v2.0, internal AI screen, not a rabbi): PASS for content and imagery (Torah
  only; objects and places; Jerusalem shown as Old City walls without any house of worship; chanukiah has 9 lights).
  New visuals still need owner visual approval.

## Owner decisions (open)
1. Approve the new default background (a) dusk + seasonal variants, and the International card (visual approval).
2. International timing: keep it inside the Friday 8:00 AM post (default; Melbourne sees it after Shabbat has begun), or
   give it its own Thursday-evening slot in the master posting plan (`--intl-mode separate`, needs a free 2-hour slot).
3. Hebrew spellings now follow the Shabbat Shalom series exactly, which for two parshiyot is the shorter spelling
   (קרח, חקת־בלק). Keep, or use the fuller קורח / חוקת everywhere (both series)?
