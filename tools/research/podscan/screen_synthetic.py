#!/usr/bin/env python3
"""Screen starter-feed descriptions for STATED synthetic production.

Patterns are the owner's (2026-11-06). Deliberately narrow: they match a
publisher SAYING the show is machine-made, not a show ABOUT AI. "AI" alone is
never a hit — it must sit beside a host word, a generation verb, or a voice
noun.
"""
import json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET

HOSTWORD = r'(?:host|hosts|vært|værter|värd|moderator|moderatoren|' \
           r'conduttore|conduttori|presentador|presentadora|presentadores|' \
           r'animateur|animatrice|speaker)'
PATTERNS = [
    ('AI + host word',      rf'\b(?:a\.?i\.?|ki|ia)[\s\-–]*{HOSTWORD}'),
    ('AI + host word (rev)', rf'\b{HOSTWORD}[\s\-–]*(?:a\.?i\.?|ki|ia)\b'),
    ('AI-generated',        r'\b(?:a\.?i\.?|ki|ia)[\s\-–]*(?:generated|genereret|'
                            r'generiert|generato|generata|generado|generada|'
                            r'généré|générée|gener[ae]ted)'),
    ('synthetic voice',     r'(?:synthetic\s+voice|syntetisk[e]?\s+stemme[r]?|'
                            r'synthetische[nrs]?\s+stimme[n]?|voce\s+sintetic[ah]e?|'
                            r'voces?\s+sintética[s]?|voix\s+synthétique[s]?)'),
    ('text-to-speech',      r'text[\s\-]?to[\s\-]?speech|\btts\b'),
    ('Emma & Alex pair',    r'emma[^.]{0,40}\balex\b|alex[^.]{0,40}\bemma\b'),
]

def grab(url, deadline=30.0):
    t0 = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent': 'klip-screen/1.0'})
    out = []
    with urllib.request.urlopen(req, timeout=12) as r:
        while time.monotonic() - t0 < deadline:
            b = r.read(131072)
            if not b: break
            out.append(b)
    return b''.join(out)

def clean(t):
    t = re.sub(r'<[^>]+>', ' ', t or '')
    return re.sub(r'\s+', ' ', t).strip()

doc = json.load(open('/Users/idap.jorgensen/Projects/klip/tool/audio_ingest/starter_feeds.json'))
ITUNES = '{http://www.itunes.com/dtds/podcast-1.0.dtd}summary'
hits, checked, failed = [], 0, []
texts = {}
for lang, v in doc['languages'].items():
    for f in v['feeds']:
        try:
            ch = ET.fromstring(grab(f['feed'])).find('channel')
            desc = clean(ch.findtext('description'))
            summ = clean(ch.findtext(ITUNES))
            blob = f'{desc} {summ}'.strip()
            texts[f"{lang}/{f['name']}"] = blob
            checked += 1
            for label, pat in PATTERNS:
                m = re.search(pat, blob, re.I)
                if m:
                    i = max(0, m.start() - 70)
                    hits.append((lang, f['name'], label, blob[i:m.end() + 70]))
                    break
        except Exception as e:
            failed.append((lang, f['name'], type(e).__name__))
        print('.', end='', flush=True)
print()
json.dump(texts, open('starter_descriptions.json', 'w'), ensure_ascii=False, indent=1)
print(f'screened {checked} of 33 feeds; fetch failures: {len(failed)}')
for l, n, e in failed: print(f'   FAILED {l}/{n}: {e}')
print()
if not hits:
    print('NO HITS — no starter feed states synthetic production.')
for l, n, label, quote in hits:
    print(f'** HIT [{label}]  {l}/{n}')
    print(f'   "...{quote}..."')
