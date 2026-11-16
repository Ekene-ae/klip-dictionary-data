#!/usr/bin/env python3
"""zh only, with an ABSOLUTE deadline. OUTSIDE THE REPO.

scan17.py hung for 20 minutes on zh. Cause: urlopen(timeout=) is a
PER-SOCKET-OPERATION timeout, not a total one, so a server trickling bytes
holds read() open forever and ThreadPoolExecutor.map waits for it.
**A WAIT THAT CANNOT GO UNSATISFIABLE** — §1.18's own lesson, in this script.

Fix: submit every probe, then wait on a GLOBAL deadline and take whatever
finished. Stragglers are recorded as timeouts, which is a number, not a hang.
"""
import json, re, sys, time, gzip, io, urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

UA = 'KlipAudioIngestSizing/1.0 (+sizing transcript availability for a language-learning app)'
TRANSCRIPT = re.compile(rb'<podcast:transcript\b[^>]*', re.I)
TYPE_ATTR  = re.compile(rb'type\s*=\s*["\']([^"\']+)["\']', re.I)
LANG_TAG   = re.compile(rb'<language>\s*([^<\s]+)', re.I)
ITEM       = re.compile(rb'<item[\s>]', re.I)
CAP = 300_000
TERMS = ['播客','新聞','歷史','社會','運動','文化','健康','科技','科學','商業','故事','兒童']

def get(url, cap=None, timeout=12):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(cap) if cap else r.read()
        if r.headers.get('Content-Encoding') == 'gzip':
            try: raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            except Exception: pass
        return raw

def probe(item):
    feed, name = item
    try: raw = get(feed, cap=CAP)
    except Exception as e: return {'feed': feed, 'name': name, 'error': type(e).__name__}
    lm = LANG_TAG.search(raw); tags = TRANSCRIPT.findall(raw)
    types = []
    for t in tags:
        m = TYPE_ATTR.search(t)
        types.append(m.group(1).decode('ascii','replace').lower() if m else '(none)')
    return {'feed': feed, 'name': name,
            'lang': lm.group(1).decode('ascii','replace').lower() if lm else '',
            'host': urllib.parse.urlparse(feed).netloc.lower(),
            'items_seen': len(ITEM.findall(raw)),
            'transcript_tags': len(tags), 'types': types}

feeds = {}
for t in TERMS:
    try:
        d = json.loads(get('https://itunes.apple.com/search?term=%s&country=tw&entity=podcast&limit=150'
                           % urllib.parse.quote(t)).decode('utf-8','replace'))
        for r in d.get('results', []):
            if r.get('feedUrl'): feeds[r['feedUrl']] = r.get('collectionName','')
    except Exception as e:
        print('  search %r failed: %s' % (t, e), file=sys.stderr)
    time.sleep(0.3)
print('candidates: %d' % len(feeds), flush=True)

rows, DEADLINE = [], 420          # 7 minutes, absolute
ex = ThreadPoolExecutor(max_workers=8)
futs = {ex.submit(probe, it): it for it in feeds.items()}
end = time.time() + DEADLINE
pending = set(futs)
while pending and time.time() < end:
    done, pending = wait(pending, timeout=min(15, max(1, end - time.time())),
                         return_when=FIRST_COMPLETED)
    for f in done:
        try: rows.append(f.result())
        except Exception as e: rows.append({'feed': futs[f][0], 'error': type(e).__name__})
    print('  done %d / %d' % (len(rows), len(futs)), flush=True)
abandoned = len(pending)
for f in pending:
    rows.append({'feed': futs[f][0], 'name': futs[f][1], 'error': 'DeadlineAbandoned'})
ex.shutdown(wait=False, cancel_futures=True)

json.dump(rows, open('zh.json','w'))
ok = [r for r in rows if 'error' not in r]
inl = [r for r in ok if r.get('lang','').startswith('zh')]
wt = [r for r in inl if r['transcript_tags'] > 0]
print('zh | candidates %4d | ok %4d | confirmed %4d | with transcripts %3d (%4.1f%%) | abandoned %d'
      % (len(feeds), len(ok), len(inl), len(wt), (100.0*len(wt)/len(inl)) if inl else 0.0, abandoned), flush=True)
