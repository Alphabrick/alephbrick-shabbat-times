"""Zero-hit scan for the full Tetragrammaton. Letters built from code points; never typed.
Strips all Hebrew points/cantillation (U+0591-U+05C7), CGJ, ZW chars before matching; also decodes
\\uXXXX escapes, HTML entities and percent-encoding; scans binary files as UTF-8/UTF-16 too."""
import os, re, sys, html, urllib.parse
L = ''.join(map(chr, (0x5D9, 0x5D4, 0x5D5, 0x5D4)))
STRIP = re.compile('[\u0591-\u05C7\u034F\u200B-\u200F\u2060\uFEFF]')
ESC = re.compile(r'\\u05d9\W{0,40}?\\u05d4\W{0,40}?\\u05d5\W{0,40}?\\u05d4', re.I)
def variants(b):
    out = []
    for enc in ('utf-8', 'utf-16-le', 'utf-16-be'):
        try: out.append(b.decode(enc, errors='ignore'))
        except Exception: pass
    return out
hits = []; nfiles = 0
for root in sys.argv[1:]:
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f); nfiles += 1
            b = open(p, 'rb').read()
            for t in variants(b):
                cands = [t, html.unescape(t)]
                try: cands.append(urllib.parse.unquote(t))
                except Exception: pass
                found = any(L in STRIP.sub('', c) for c in cands) or ESC.search(t)
                if found: hits.append(p); break
print('files scanned:', nfiles); print('hits:', len(hits))
for h in hits: print('  HIT', h)
sys.exit(1 if hits else 0)
