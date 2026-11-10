# -*- coding: utf-8 -*-
"""Divine-name guard for the Shabbat-times generator. Every pattern is assembled from code points; none is typed."""
import re
def _s(*cps): return ''.join(map(chr, cps))
HEB = [_s(0x5D9, 0x5D4, 0x5D5, 0x5D4), _s(0x5D0, 0x5DC, 0x5D4, 0x5D9, 0x5DD), _s(0x5D0, 0x5D3, 0x5E0, 0x5D9)]
LAT = [_s(0x67, 0x6F, 0x64), _s(0x6A, 0x65, 0x68, 0x6F, 0x76, 0x61, 0x68), _s(0x79, 0x61, 0x68, 0x77, 0x65, 0x68)]
STRIP = re.compile('[֑-ׇ͏​-‏⁠﻿]')
LAT_RE = re.compile(r'(?<![a-z])(' + '|'.join(LAT) + r')(?![a-z])', re.I)
def hits(text):
    t = STRIP.sub('', text)
    out = [h for h in HEB if h in t]
    out += [m.group(0) for m in LAT_RE.finditer(text)]
    return out
