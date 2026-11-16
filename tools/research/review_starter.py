#!/usr/bin/env python3
"""Fetch the 42 curated starter feeds and report what a reviewer needs.

THE zh TIMEOUT LESSON APPLIED: urlopen(timeout=) is PER-SOCKET-OPERATION,
not total. A feed that trickles bytes resets it on every read and the call
never returns. Each feed here carries an ABSOLUTE WALL-CLOCK DEADLINE.
"""
import json, re, socket, sys, time, urllib.request, urllib.error
import xml.etree.ElementTree as ET

NS = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
PODCAST_NS = 'podcastindex.org/namespace'
DEADLINE = 25.0          # seconds, TOTAL, per feed
CAP = 5_000_000          # bytes; a feed that hits this is flagged

def fetch(url):
    started = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent': 'klip-review/1.0'})
    chunks, n = [], 0
    with urllib.request.urlopen(req, timeout=10) as r:
        while True:
            if time.monotonic() - started > DEADLINE:
                return b''.join(chunks), True, n >= CAP
            b = r.read(65536)
            if not b: break
            chunks.append(b); n += len(b)
            if n >= CAP: return b''.join(chunks), False, True
    return b''.join(chunks), False, False

MONTHS = {m: i+1 for i, m in enumerate(
    ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}

def pubdate(s):
    if not s: return None
    m = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})', s)
    if not m: return None
    mo = MONTHS.get(m.group(2).lower())
    return f'{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}' if mo else None

def review(url):
    raw, timed_out, capped = fetch(url)
    root = ET.fromstring(raw)
    ch = root.find('channel')
    title = (ch.findtext('title') or '').strip()
    lang = (ch.findtext('language') or '').strip()
    items = ch.findall('item')
    dates, with_tr = [], 0
    for it in items:
        d = pubdate(it.findtext('pubDate'))
        if d: dates.append(d)
        for el in it:
            if PODCAST_NS in (el.tag or '') and el.tag.endswith('transcript'):
                with_tr += 1; break
    return {'title': title, 'lang': lang, 'items': len(items),
            'with_tr': with_tr, 'first': min(dates) if dates else None,
            'latest': max(dates) if dates else None,
            'timed_out': timed_out, 'capped': capped}

doc = json.load(open('/Users/idap.jorgensen/Projects/klip/tool/audio_ingest/starter_feeds.json'))
order = ['da','de','it','es','fr','nl','en']
out = {}
for lang in order:
    out[lang] = []
    for row in doc['languages'][lang]:
        rec = {'name': row['name'], 'feed': row['feed']}
        try:
            rec.update(review(row['feed']))
            rec['error'] = None
        except Exception as e:
            rec['error'] = f'{type(e).__name__}: {e}'[:70]
        out[lang].append(rec)
        print('.', end='', flush=True)
print()
json.dump(out, open('/tmp/starter_review.json','w'), ensure_ascii=False, indent=1)
print('done')
