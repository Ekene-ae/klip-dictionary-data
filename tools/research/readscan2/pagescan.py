"""readscan 2 — PAGE-LEVEL extraction. Does a reader view actually get text out?

OUTSIDE THE KLIP REPOSITORY. No repo code. Run under the scan venv's
`python3 -I` (which keeps the venv's site-packages and drops user site).

readability-lxml STANDS IN for whatever Dart extractor is chosen later. It is
not a proposal: it is the cheapest available instrument of the same CLASS, so
the share of pages that yield an article is measurable before anyone writes
one.

WHAT A REAL EXTRACTOR WOULD FACE, AND WHAT THIS REPRODUCES
----------------------------------------------------------
NO JAVASCRIPT. NO COOKIE JAR. NO CONSENT CLICKING. One plain GET with an
ordinary desktop browser UA, redirects followed. That is the situation an
on-device extractor is in, so it is the situation measured.

WHAT IS NOT PERSISTED, DELIBERATELY
-----------------------------------
THE EXTRACTED ARTICLE BODIES ARE NOT KEPT — only their measurements, the
short title, and which wall markers fired. readscan 1's rule, applied here:
counts and flags may be kept, bulk third-party article text may not. It also
keeps this directory small enough to re-read.
"""
import gzip, json, os, re, ssl, sys, time, urllib.error, urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from readability import Document

R1   = os.path.expanduser('~/dict-work/readscan')
BASE = os.path.expanduser('~/dict-work/readscan2')
PAGES = os.path.join(BASE, 'pages')

# A PLAIN desktop browser UA. Not rotated, not disguised as a crawler, and
# recorded here so the measurement can be repeated with the same one.
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
MAXBYTES = 3_000_000
TIMEOUT  = 25
READABLE_CHARS = 1200
READABLE_PARAS = 3
CTX = ssl.create_default_context()

# ── WALL MARKERS ─────────────────────────────────────────────────────────────
CONSENT = [r'cookiebot', r'onetrust', r'didomi', r'sourcepoint', r'quantcast',
           r'usercentrics', r'consentmanager', r'sp_message_container',
           r'cookie[- ]?consent', r'gdpr[- ]?consent', r'cmp[-_]?banner',
           r'tcfapi', r'samtykke', r'zustimmung', r'consentement',
           r'consentimiento', r'consenso\s+(?:ai\s+)?cookie']
PAYWALL = [r'abonnement', r'\babo\b', r'abonnenten', r'premium', r'paywall',
           r'suscr[ií]bete', r'suscripci[óo]n', r'subscribe to continue',
           r'subscribe to read', r'plus[- ]artikel', r'article r[ée]serv[ée]',
           r'solo per abbonati', r'kun for abonnenter', r'bli[v]? abonnent',
           r'registrati per continuare', r'contenido exclusivo']
LOGIN_URL = re.compile(r'/(?:login|signin|sign-in|auth|account[s]?)(?:[/?]|$)|'
                       r'^https?://(?:accounts|login|id)\.', re.I)
C_RE = [re.compile(p, re.I) for p in CONSENT]
P_RE = [re.compile(p, re.I) for p in PAYWALL]

TAGS = re.compile(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>|<[^>]+>')
import html as _html
def strip_html(s):
    if not s: return ''
    return ' '.join(_html.unescape(TAGS.sub(' ', s)).split())

def norm_title(s):
    s = _html.unescape(s or '').lower()
    s = re.sub(r'[^a-z0-9äöüåæøéèàìòùñçß ]+', ' ', s)
    return ' '.join(s.split())

def title_match(feed_t, extracted_t):
    a, b = norm_title(feed_t), norm_title(extracted_t)
    if not a or not b: return None, 0.0
    if a in b or b in a: return True, 1.0
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb: return False, 0.0
    j = len(ta & tb) / len(ta | tb)
    return (j >= 0.5), round(j, 2)

def local(t): return t.rsplit('}', 1)[-1] if '}' in t else t
def first_text(el, names):
    for ch in el:
        if local(ch.tag) in names:
            t = ''.join(ch.itertext())
            if t and t.strip(): return t.strip()
    return None
def parse_date(s):
    if not s: return None
    for f in ('%Y-%m-%dT%H:%M:%S%z','%Y-%m-%dT%H:%M:%S.%f%z','%Y-%m-%d'):
        try:
            d = datetime.strptime(s.strip().replace('Z','+0000'), f)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError: pass
    try:
        d = parsedate_to_datetime(s.strip()); return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: pass
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s or '')
    return datetime(int(m[1]),int(m[2]),int(m[3]),tzinfo=timezone.utc) if m else None

def feed_items(label):
    """(link, title, date) from the bytes readscan 1 measured — no re-fetch."""
    p = os.path.join(R1, 'raw', label + '.xml')
    if not os.path.exists(p): return []
    try: root = ET.fromstring(open(p,'rb').read())
    except ET.ParseError: return []
    rt = local(root.tag)
    if rt == 'feed':   parent, tag = root, 'entry'
    elif rt == 'rss':
        parent = root.find('channel')
        if parent is None: return []
        tag = 'item'
    elif rt == 'RDF':  parent, tag = root, 'item'
    else: return []
    out = []
    for it in ([e for e in parent if local(e.tag)==tag] or
               [e for e in root.iter() if local(e.tag)=='item']):
        link = None
        for ch in it:
            if local(ch.tag) == 'link':
                link = (ch.get('href') or ''.join(ch.itertext()) or '').strip()
                if link and (ch.get('rel') in (None,'alternate')): break
        if not link:
            g = first_text(it, {'guid','id'})
            if g and g.startswith('http'): link = g
        if not link: continue
        out.append((link, first_text(it,{'title'}),
                    parse_date(first_text(it,{'pubDate','updated','published','date'}))))
    dated = [o for o in out if o[2]]
    if dated: dated.sort(key=lambda o: o[2], reverse=True); return dated, True
    return out, False

def fetch(url):
    r = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip',
        'Accept-Language': 'en,da,de,fr,es,it;q=0.8'})
    with urllib.request.urlopen(r, timeout=TIMEOUT, context=CTX) as resp:
        b = resp.read(MAXBYTES)
        if resp.headers.get('Content-Encoding') == 'gzip':
            try: b = gzip.decompress(b)
            except Exception: pass
        return resp.status, b, resp.geturl()

def measure_page(url, feed_title):
    rec = {'url': url, 'feed_title': feed_title}
    try:
        st, body, final = fetch(url)
    except urllib.error.HTTPError as e:
        rec.update(http=e.code, ok=False, error=f'HTTP {e.code}'); return rec
    except Exception as e:
        rec.update(ok=False, error=f'{type(e).__name__}: {str(e)[:90]}'); return rec
    rec['http'] = st; rec['final_url'] = final
    rec['redirected'] = (final != url)
    rec['page_bytes'] = len(body)
    s = body.decode('utf-8', 'replace')

    hits_c = sorted({m.pattern for m in C_RE if m.search(s)})
    hits_p = sorted({m.pattern for m in P_RE if m.search(s)})
    login  = bool(LOGIN_URL.search(final))
    rec['consent_markers'] = hits_c
    rec['paywall_markers'] = hits_p
    rec['login_redirect']  = login

    try:
        doc = Document(s)
        summary = doc.summary()
        short   = doc.short_title()
    except Exception as e:
        rec.update(ok=False, error=f'extract: {type(e).__name__}'); return rec
    text = strip_html(summary)
    rec['chars'] = len(text)
    rec['paragraphs'] = len(re.findall(r'<p[\s>]', summary, re.I))
    rec['extracted_title'] = (short or '')[:160]
    tm, score = title_match(feed_title, short)
    rec['title_match'] = tm; rec['title_jaccard'] = score

    # ── THE WALL VERDICT, stated so it can be re-derived ──
    # A cookie BANNER is on nearly every European news page and is not a wall.
    # A WALL is: a login redirect; or a paywall marker on a page that yielded
    # too little text; or consent markers on a page that yielded almost none.
    rec['wall'] = bool(login
                       or (hits_p and rec['chars'] < READABLE_CHARS)
                       or (hits_c and rec['chars'] < 300))
    rec['readable'] = bool(rec['chars'] >= READABLE_CHARS
                           and rec['paragraphs'] >= READABLE_PARAS
                           and not rec['wall'])
    rec['ok'] = True
    return rec

def run(limit_per_feed=10, only=None):
    feeds = []
    for p in sorted(os.listdir(os.path.join(R1,'feeds'))):
        if p.startswith('_') or not p.endswith('.json'): continue
        d = json.load(open(os.path.join(R1,'feeds',p)))
        if not d.get('ok'): continue
        if only and d['label'] not in only: continue
        feeds.append(d)
    last = defaultdict(float)
    for i, f in enumerate(feeds, 1):
        out = os.path.join(PAGES, f['label'] + '.json')
        if os.path.exists(out):
            print(f'[{i}/{len(feeds)}] {f["label"]:<34} on disk, skipped', flush=True); continue
        items, by_date = feed_items(f['label'])
        items = items[:limit_per_feed]
        recs = []
        for (link, title, _d) in items:
            h = urlparse(link).netloc
            wait = 1.3 - (time.time() - last[h])
            if wait > 0: time.sleep(wait)
            recs.append(measure_page(link, title))
            last[h] = time.time()
        okp = [r for r in recs if r.get('ok')]
        chars = sorted(r['chars'] for r in okp)
        res = {'label': f['label'], 'lang': f['lang'], 'group': f['group'],
               'feed_url': f['url'], 'ordered_by_date': by_date,
               'pages_attempted': len(recs), 'pages_ok': len(okp),
               'readable': sum(1 for r in okp if r['readable']),
               'walled': sum(1 for r in okp if r['wall']),
               'readable_share': round(100.0*sum(1 for r in okp if r['readable'])/len(okp),1) if okp else None,
               'median_chars': chars[len(chars)//2] if chars else None,
               'title_match_share': (round(100.0*sum(1 for r in okp if r.get('title_match'))/len(okp),1)
                                     if okp else None),
               'measured_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
               'pages': recs}
        json.dump(res, open(out,'w'), ensure_ascii=False, indent=1)
        print(f'[{i}/{len(feeds)}] {f["label"]:<34} pages {len(okp)}/{len(recs)}  '
              f'readable {res["readable_share"]}%  walled {res["walled"]}  '
              f'med {res["median_chars"]}', flush=True)

if __name__ == '__main__':
    run()
