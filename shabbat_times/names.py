# -*- coding: utf-8 -*-
"""Display names (English + Hebrew) for parshiyot, Yamim Tovim and fasts.

BRAND spellings (owner ruling, Nov 9 2026): every series uses the Shabbat Shalom series' spellings
(/home/claude/abc/social_52/shabbat_shalom/manifest.csv, e.g. בחוקותי, קדושים, מצורע), English and Hebrew.
Parshiyot that the Shabbat Shalom series does not (yet) cover use the same pattern (marked *).

HEBCAL spellings are kept next to each one only so validate.py can prove the parsha identity against the
Hebcal reference (_validation/hebcal_names_*.txt). They are never shown on a graphic or caption."""

# pyluach parsha index -> (English brand, Hebrew brand, English Hebcal, Hebrew Hebcal)
PARSHA = {
    0: ('Bereishit', 'בראשית', 'Bereshit', 'בראשית'),
    1: ('Noach', 'נח', 'Noach', 'נח'),
    2: ('Lech Lecha', 'לך לך', 'Lech-Lecha', 'לך־לך'),
    3: ('Vayera', 'וירא', 'Vayera', 'וירא'),
    4: ('Chayei Sarah', 'חיי שרה', 'Chayei Sara', 'חיי שרה'),
    5: ('Toldot', 'תולדות', 'Toldot', 'תולדות'),                       # *
    6: ('Vayetzei', 'ויצא', 'Vayetzei', 'ויצא'),
    7: ('Vayishlach', 'וישלח', 'Vayishlach', 'וישלח'),
    8: ('Vayeshev', 'וישב', 'Vayeshev', 'וישב'),
    9: ('Miketz', 'מקץ', 'Miketz', 'מקץ'),
    10: ('Vayigash', 'ויגש', 'Vayigash', 'ויגש'),
    11: ('Vayechi', 'ויחי', 'Vayechi', 'ויחי'),
    12: ('Shemot', 'שמות', 'Shemot', 'שמות'),
    13: ('Va’era', 'וארא', 'Vaera', 'וארא'),
    14: ('Bo', 'בא', 'Bo', 'בא'),
    15: ('Beshalach', 'בשלח', 'Beshalach', 'בשלח'),
    16: ('Yitro', 'יתרו', 'Yitro', 'יתרו'),
    17: ('Mishpatim', 'משפטים', 'Mishpatim', 'משפטים'),
    18: ('Terumah', 'תרומה', 'Terumah', 'תרומה'),
    19: ('Tetzaveh', 'תצוה', 'Tetzaveh', 'תצוה'),
    20: ('Ki Tisa', 'כי תשא', 'Ki Tisa', 'כי תשא'),
    21: ('Vayakhel', 'ויקהל', 'Vayakhel', 'ויקהל'),
    22: ('Pekudei', 'פקודי', 'Pekudei', 'פקודי'),
    23: ('Vayikra', 'ויקרא', 'Vayikra', 'ויקרא'),
    24: ('Tzav', 'צו', 'Tzav', 'צו'),
    25: ('Shemini', 'שמיני', 'Shmini', 'שמיני'),
    26: ('Tazria', 'תזריע', 'Tazria', 'תזריע'),
    27: ('Metzora', 'מצורע', 'Metzora', 'מצרע'),
    28: ('Acharei Mot', 'אחרי מות', 'Achrei Mot', 'אחרי מות'),
    29: ('Kedoshim', 'קדושים', 'Kedoshim', 'קדשים'),
    30: ('Emor', 'אמור', 'Emor', 'אמור'),
    31: ('Behar', 'בהר', 'Behar', 'בהר'),
    32: ('Bechukotai', 'בחוקותי', 'Bechukotai', 'בחקתי'),
    33: ('Bamidbar', 'במדבר', 'Bamidbar', 'במדבר'),
    34: ('Nasso', 'נשא', 'Nasso', 'נשא'),
    35: ('Beha’alotecha', 'בהעלותך', 'Beha’alotcha', 'בהעלתך'),
    36: ('Shelach', 'שלח', 'Sh’lach', 'שלח־לך'),
    37: ('Korach', 'קרח', 'Korach', 'קורח'),
    38: ('Chukat', 'חקת', 'Chukat', 'חוקת'),                           # * (series: חקת־בלק)
    39: ('Balak', 'בלק', 'Balak', 'בלק'),                              # * (series: חקת־בלק)
    40: ('Pinchas', 'פינחס', 'Pinchas', 'פינחס'),
    41: ('Matot', 'מטות', 'Matot', 'מטות'),                            # * (series: מטות־מסעי)
    42: ('Masei', 'מסעי', 'Masei', 'מסעי'),                            # * (series: מטות־מסעי)
    43: ('Devarim', 'דברים', 'Devarim', 'דברים'),
    44: ('Va’etchanan', 'ואתחנן', 'Vaetchanan', 'ואתחנן'),
    45: ('Eikev', 'עקב', 'Eikev', 'עקב'),
    46: ('Re’eh', 'ראה', 'Re’eh', 'ראה'),
    47: ('Shoftim', 'שופטים', 'Shoftim', 'שופטים'),
    48: ('Ki Teitzei', 'כי תצא', 'Ki Teitzei', 'כי־תצא'),
    49: ('Ki Tavo', 'כי תבוא', 'Ki Tavo', 'כי־תבוא'),
    50: ('Nitzavim', 'נצבים', 'Nitzavim', 'נצבים'),                     # * (series: נצבים־וילך)
    51: ('Vayelech', 'וילך', 'Vayeilech', 'וילך'),                     # * (series: נצבים־וילך)
    52: ('Ha’azinu', 'האזינו', 'Ha’azinu', 'האזינו'),
    53: ('Vezot Haberachah', 'וזאת הברכה', 'Vezot Haberakhah', 'וזאת הברכה'),   # *
}
MAQAF = '־'


def parsha(idx_list):
    """Brand spelling: 'Parshat Chukat-Balak' / 'פרשת חקת־בלק' (combined readings: hyphen / maqaf)."""
    en = '-'.join(PARSHA[i][0] for i in idx_list)
    he = MAQAF.join(PARSHA[i][1] for i in idx_list)
    return 'Parshat ' + en, 'פרשת ' + he


def parsha_hebcal(idx_list):
    """Hebcal spelling, for validation only."""
    return '-'.join(PARSHA[i][2] for i in idx_list), 'פרשת ' + MAQAF.join(PARSHA[i][3] for i in idx_list)


# Yom Tov / fast names. English = house style (Shabbat Shalom series); Hebrew = full spelling.
HOLIDAY = {
    'Rosh Hashana': ('Rosh Hashanah', 'ראש השנה'),
    'Yom Kippur': ('Yom Kippur', 'יום כיפור'),
    'Succos': ('Sukkot', 'סוכות'),
    'Shmini Atzeres': ('Shemini Atzeret', 'שמיני עצרת'),
    'Simchas Torah': ('Simchat Torah', 'שמחת תורה'),
    'Pesach': ('Pesach', 'פסח'),
    'Shavuos': ('Shavuot', 'שבועות'),
}
FAST = {
    '10 of Teves': ('Asara B’Tevet', 'עשרה בטבת', 'Fast of the 10th of Tevet'),
    'Taanis Esther': ('Ta’anit Esther', 'תענית אסתר', 'Fast of Esther'),
    '17 of Tamuz': ('Tzom Tammuz', 'צום י״ז בתמוז', 'Fast of the 17th of Tammuz'),
    '9 of Av': ('Tisha B’Av', 'תשעה באב', 'Fast of the 9th of Av'),
    'Tzom Gedalia': ('Tzom Gedaliah', 'צום גדליה', 'Fast of Gedaliah'),
}
CHOL_HAMOED_SHABBAT = {'Pesach': ('Shabbat Chol HaMoed Pesach', 'שבת חול המועד פסח'),
                       'Succos': ('Shabbat Chol HaMoed Sukkot', 'שבת חול המועד סוכות')}
