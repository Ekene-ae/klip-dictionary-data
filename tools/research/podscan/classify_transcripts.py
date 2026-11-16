#!/usr/bin/env python3
"""Classify starter-feed episodes by transcript availability.

**THE NORMALISATION MIRRORS lib/services/podcast_feed.dart EXACTLY**, or the
figures would not inform a decision about that file: the URL extension wins a
disagreement, the declared type carries it when the URL has no extension.
Absolute per-feed deadline (the zh lesson), not a socket timeout.
"""
import json, re, time, urllib.request
from urllib.parse import urlparse

USABLE = {'srt', 'vtt'}

def fmt_from_mime(t):
    t = (t or '').strip().lower()
    if t.startswith('/'): t = t[1:]
    t = t.split(';')[0].strip()
    if not t: return None
    if 'subrip' in t or t.endswith('/srt') or t.endswith('x-srt'): return 'srt'
    if 'vtt' in t: return 'vtt'
    if 'json' in t: return 'json'
    if 'html' in t: return 'html'
    if t == 'text/plain': return 'text'
    return None

def fmt_from_url(u):
    p = (u or '').strip().split('?')[0].split('#')[0]
    last = p.rsplit('/', 1)[-1]
    if '.' not in last: return None
    ext = last.rsplit('.', 1)[1].lower()
    return {'srt':'srt','vtt':'vtt','webvtt':'vtt','json':'json',
            'html':'html','htm':'html','txt':'text'}.get(ext)

def normalise(mime, url):
    a, b = fmt_from_mime(mime), fmt_from_url(url)
    if b is None: return a
    if a is None: return b
    return b          # the URL names the resource being served

def grab(url, deadline=45.0, cap=30_000_000):
    t0 = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent': 'klip-measure/1.0'})
    out, n = [], 0
    with urllib.request.urlopen(req, timeout=12) as r:
        while time.monotonic() - t0 < deadline and n < cap:
            b = r.read(262144)
            if not b: break
            out.append(b); n += len(b)
    return b''.join(out)

doc = json.load(open('/Users/idap.jorgensen/Projects/klip/tool/audio_ingest/starter_feeds.json'))
ITEM = re.compile(rb'<item>.*?</item>', re.S)
TR = re.compile(rb'<podcast:transcript\b([^>]*)/?>', re.I)
ATTR = re.compile(rb'(\w+)\s*=\s*"([^"]*)"')
rows = {}
for lang, v in doc['languages'].items():
    rows[lang] = {'usable': 0, 'json_only': 0, 'html_only': 0,
                  'other_only': 0, 'none': 0, 'items': 0}
    for f in v['feeds']:
        try:
            raw = grab(f['feed'])
        except Exception:
            continue
        for it in ITEM.findall(raw)[:25]:
            rows[lang]['items'] += 1
            fmts = []
            for m in TR.finditer(it):
                a = dict((k.decode().lower(), vv.decode('utf-8', 'replace'))
                         for k, vv in ATTR.findall(m.group(1)))
                if not a.get('url'): continue
                fmts.append(normalise(a.get('type'), a['url']))
            if not fmts:
                rows[lang]['none'] += 1
            elif any(x in USABLE for x in fmts):
                rows[lang]['usable'] += 1
            elif 'json' in fmts:
                rows[lang]['json_only'] += 1
            elif 'html' in fmts:
                rows[lang]['html_only'] += 1
            else:
                rows[lang]['other_only'] += 1
        print('.', end='', flush=True)
print()
json.dump(rows, open('/tmp/transcript_classes.json', 'w'), indent=1)
hdr = f"{'lang':5} {'items':>6} {'SRT/VTT':>8} {'JSON only':>10} {'html only':>10} {'other':>6} {'none':>6}"
print(hdr); print('-' * len(hdr))
tot = {k: 0 for k in ('items','usable','json_only','html_only','other_only','none')}
for lang, r in rows.items():
    for k in tot: tot[k] += r[k]
    print(f"{lang:5} {r['items']:>6} {r['usable']:>8} {r['json_only']:>10} "
          f"{r['html_only']:>10} {r['other_only']:>6} {r['none']:>6}")
print('-' * len(hdr))
print(f"{'ALL':5} {tot['items']:>6} {tot['usable']:>8} {tot['json_only']:>10} "
      f"{tot['html_only']:>10} {tot['other_only']:>6} {tot['none']:>6}")
with_any = tot['usable'] + tot['json_only'] + tot['html_only'] + tot['other_only']
print()
print(f"episodes with ANY transcript: {with_any}")
if with_any:
    pj = 100.0 * tot['json_only'] / with_any
    print(f"JSON-ONLY as a share of episodes with any transcript: {pj:.2f}%")
    print(f"THRESHOLD ~10% -> {'PROPOSE P1c' if pj > 10 else 'RECORD THE FIGURE, LEAVE THE EXTENSION LIST'}")
