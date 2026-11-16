#!/usr/bin/env python3
"""Size podcast transcript availability for da and en. OUTSIDE THE REPO.

NO PODCAST INDEX KEY: api.podcastindex.org returns 401 without one, and I
cannot register an account on the owner's behalf. So feeds come from Apple's
keyless search endpoint, and LANGUAGE IS CONFIRMED FROM THE FEED'S OWN
<language> TAG, never from the storefront country — a Danish storefront
carries plenty of English podcasts.

WHAT THIS CAN AND CANNOT ANSWER
  CAN: transcript presence per feed, transcript TYPE distribution, hosting
       platform, all read from the live RSS.
  CANNOT: "podcasts in the index" — that is a Podcast Index total and needs
       either the key or the 1.71 GiB feeds dump. Reported as unavailable
       rather than estimated.
"""
import json, re, sys, time, gzip, io
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = 'KlipAudioIngestSizing/1.0 (+sizing transcript availability for a language-learning app)'
TRANSCRIPT = re.compile(rb'<podcast:transcript\b[^>]*', re.I)
TYPE_ATTR  = re.compile(rb'type\s*=\s*["\']([^"\']+)["\']', re.I)
URL_ATTR   = re.compile(rb'url\s*=\s*["\']([^"\']+)["\']', re.I)
LANG_TAG   = re.compile(rb'<language>\s*([^<\s]+)', re.I)
GENERATOR  = re.compile(rb'<generator>\s*([^<]{0,80})', re.I)
ITEM       = re.compile(rb'<item[\s>]', re.I)
CAP = 2_000_000          # bytes per feed: newest items come first in RSS

def get(url, cap=None, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(cap) if cap else r.read()
        if r.headers.get('Content-Encoding') == 'gzip':
            try: raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            except Exception: pass
        return raw

def apple_feeds(country, terms, limit=200):
    """Candidate feed URLs from Apple's keyless search."""
    out = {}
    for t in terms:
        u = ('https://itunes.apple.com/search?term=%s&country=%s&entity=podcast&limit=%d'
             % (urllib.parse.quote(t), country, limit))
        try:
            d = json.loads(get(u).decode('utf-8', 'replace'))
        except Exception as e:
            print('  search failed %r: %s' % (t, e), file=sys.stderr); continue
        for r in d.get('results', []):
            f = r.get('feedUrl')
            if f: out[f] = r.get('collectionName', '')
        time.sleep(0.3)                      # polite
    return out

def probe(item):
    feed, name = item
    try:
        raw = get(feed, cap=CAP)
    except Exception as e:
        return {'feed': feed, 'name': name, 'error': type(e).__name__}
    lang = (LANG_TAG.search(raw) or [None, b''])[1] if LANG_TAG.search(raw) else b''
    lang = (LANG_TAG.search(raw).group(1).decode('ascii','replace').lower()
            if LANG_TAG.search(raw) else '')
    gen = (GENERATOR.search(raw).group(1).decode('utf-8','replace').strip()
           if GENERATOR.search(raw) else '')
    tags = TRANSCRIPT.findall(raw)
    types, urls = [], []
    for t in tags:
        m = TYPE_ATTR.search(t); types.append(m.group(1).decode('ascii','replace').lower() if m else '(none)')
        u = URL_ATTR.search(t)
        if u: urls.append(u.group(1).decode('utf-8','replace'))
    host = urllib.parse.urlparse(feed).netloc.lower()
    return {'feed': feed, 'name': name, 'lang': lang, 'generator': gen,
            'host': host, 'items_seen': len(ITEM.findall(raw)),
            'transcript_tags': len(tags), 'types': types,
            'transcript_urls': urls[:3], 'bytes': len(raw)}

if __name__ == '__main__':
    import urllib.parse
    which = sys.argv[1]
    country, prefix, terms = {
      'da': ('dk', 'da', ['podcast','nyheder','historie','samfund','sport','kultur',
                          'politik','sundhed','penge','teknologi','krimi','børn',
                          'mad','musik','videnskab','erhverv','humor','natur',
                          'dansk','radio','interview','livet','familie','bog']),
      'en': ('us', 'en', ['podcast','news','history','society','sport','culture',
                          'politics','health','money','technology','crime','kids',
                          'food','music','science','business','comedy','nature',
                          'english','radio','interview','life','family','book']),
    }[which]
    feeds = apple_feeds(country, terms)
    print('candidate feeds from Apple (%s storefront): %d' % (country, len(feeds)), flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(probe, list(feeds.items())), 1):
            rows.append(r)
            if i % 50 == 0: print('  probed %d/%d' % (i, len(feeds)), flush=True)
    json.dump(rows, open('/tmp/podscan/%s.json' % which, 'w'))
    ok = [r for r in rows if 'error' not in r]
    inlang = [r for r in ok if r.get('lang','').startswith(prefix)]
    print('fetched OK: %d   errors: %d' % (len(ok), len(rows)-len(ok)))
    print('confirmed <language> starts with %r: %d' % (prefix, len(inlang)))
