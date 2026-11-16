"""readscan 2b — B6's REFINED WALL DETECTOR, measured.

WHY A RE-FETCH RATHER THAN A RE-READ OF DISK. readscan 2 deliberately did NOT
persist page bodies or raw HTML ("counts and flags may be kept, bulk
third-party article text may not"), so WHETHER A MARKER SAT INSIDE THE
EXTRACTED BODY CANNOT BE DERIVED FROM WHAT IS ON DISK. The refinement needs
the body, so the pages are fetched again — SAME SELECTION, from readscan 1's
persisted feed bytes, so the two figures are comparable.

AND THE BODIES ARE STILL NOT KEPT. Only positions, ratios and verdicts.

THE RULED DEFINITION
  A WALL is:
    (a) a paywall marker INSIDE the extracted article body; or
    (b) a TRUNCATION SIGNAL —
          (b1) the body ends on a subscribe cue, or
          (b2) extracted chars < 40% of what the feed's own
               description/summary length implies for a full article.
  Markers in site chrome (nav, footer, sidebars) are NOT walls.

ONE INTERPRETATION, STATED BECAUSE (b2) IS UNDERSPECIFIED. A feed description
is usually a 100-400 character teaser, which implies nothing about article
length. (b2) is therefore applied ONLY where the feed's own description is
itself substantial (>=1,200 chars — the readable bar), which is exactly the
case readscan 1 found at es-eldiario (5,744-char descriptions) and the EU
press corner. Where the description is a teaser the signal is recorded as
NOT APPLICABLE rather than silently passing.
"""
import gzip, json, os, re, ssl, sys, time, urllib.error, urllib.request, html as _html
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from readability import Document

R1   = os.path.expanduser('~/dict-work/readscan')
R2   = os.path.expanduser('~/dict-work/readscan2')
BASE = os.path.expanduser('~/dict-work/readscan2b')
PAGES= os.path.join(BASE,'pages')
UA=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
CTX=ssl.create_default_context()
MAXBYTES=3_000_000; TIMEOUT=25
READABLE_CHARS=1200; READABLE_PARAS=3
DESC_IMPLIES=1200          # the feed description must itself be this long for (b2)
TRUNC_RATIO=0.40
TAIL=260                   # how much of the body's end counts as "ends on"

PAYWALL=[r'abonnement', r'\babo\b', r'abonnenten', r'premium', r'paywall',
         r'suscr[ií]bete', r'suscripci[óo]n', r'subscribe to continue',
         r'subscribe to read', r'plus[- ]artikel', r'article r[ée]serv[ée]',
         r'solo per abbonati', r'kun for abonnenter', r'bli[v]? abonnent',
         r'registrati per continuare', r'contenido exclusivo']
# a SUBSCRIBE CUE is narrower than a paywall marker: it is an invitation, the
# kind of sentence a truncated body ends on.
CUE=[r'subscribe to (?:continue|read)', r'continue reading', r'sign in to',
     r'log in to (?:read|continue)', r'become a (?:member|subscriber)',
     r'abonn(?:er|ement|ez)', r'jetzt (?:abo|abonnieren|weiterlesen)',
     r'weiterlesen mit', r'suscr[ií]bete', r'hazte socio',
     r'abbonati', r'continua a leggere', r'lire la suite',
     r'article r[ée]serv[ée] aux abonn', r'bliv abonnent', r'f[åa] fuld adgang']
P_RE=[re.compile(p, re.I) for p in PAYWALL]
C_RE=[re.compile(p, re.I) for p in CUE]
TAGS=re.compile(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>|<[^>]+>')
def strip_html(s):
    return ' '.join(_html.unescape(TAGS.sub(' ', s or '')).split())
def local(t): return t.rsplit('}',1)[-1] if '}' in t else t
def first_text(el, names):
    for ch in el:
        if local(ch.tag) in names:
            t=''.join(ch.itertext())
            if t and t.strip(): return t.strip()
    return None
def parse_date(s):
    if not s: return None
    for f in ('%Y-%m-%dT%H:%M:%S%z','%Y-%m-%dT%H:%M:%S.%f%z','%Y-%m-%d'):
        try:
            d=datetime.strptime(s.strip().replace('Z','+0000'), f)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError: pass
    try:
        d=parsedate_to_datetime(s.strip()); return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: pass
    m=re.search(r'(\d{4})-(\d{2})-(\d{2})', s or '')
    return datetime(int(m[1]),int(m[2]),int(m[3]),tzinfo=timezone.utc) if m else None

def feed_items(label):
    """SAME selection as readscan 2, plus each item's own description length."""
    p=os.path.join(R1,'raw',label+'.xml')
    if not os.path.exists(p): return []
    try: root=ET.fromstring(open(p,'rb').read())
    except ET.ParseError: return []
    rt=local(root.tag)
    if rt=='feed': parent,tag=root,'entry'
    elif rt=='rss':
        parent=root.find('channel')
        if parent is None: return []
        tag='item'
    elif rt=='RDF': parent,tag=root,'item'
    else: return []
    out=[]
    for it in ([e for e in parent if local(e.tag)==tag] or
               [e for e in root.iter() if local(e.tag)=='item']):
        link=None
        for ch in it:
            if local(ch.tag)=='link':
                link=(ch.get('href') or ''.join(ch.itertext()) or '').strip()
                if link and (ch.get('rel') in (None,'alternate')): break
        if not link:
            g=first_text(it,{'guid','id'})
            if g and g.startswith('http'): link=g
        if not link: continue
        # the feed's own description/summary, and content:encoded if present
        dtext=None
        for ch in it:
            if local(ch.tag) in ('description','summary'): dtext=''.join(ch.itertext()); break
        ctext=None
        for ch in it:
            if local(ch.tag)=='encoded': ctext=''.join(ch.itertext()); break
        feed_text_len=max(len(strip_html(dtext)), len(strip_html(ctext)))
        out.append((link, first_text(it,{'title'}),
                    parse_date(first_text(it,{'pubDate','updated','published','date'})),
                    feed_text_len))
    dated=[o for o in out if o[2]]
    if dated: dated.sort(key=lambda o:o[2], reverse=True); return dated
    return out

def fetch(url):
    r=urllib.request.Request(url, headers={'User-Agent':UA,
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding':'gzip','Accept-Language':'en,da,de,fr,es,it;q=0.8'})
    with urllib.request.urlopen(r, timeout=TIMEOUT, context=CTX) as resp:
        b=resp.read(MAXBYTES)
        if resp.headers.get('Content-Encoding')=='gzip':
            try: b=gzip.decompress(b)
            except Exception: pass
        return resp.status, b, resp.geturl()

def measure(url, feed_title, feed_text_len):
    rec={'url':url,'feed_text_len':feed_text_len}
    try:
        st,body,final=fetch(url)
    except urllib.error.HTTPError as e:
        rec.update(ok=False, http=e.code, error=f'HTTP {e.code}'); return rec
    except Exception as e:
        rec.update(ok=False, error=f'{type(e).__name__}'); return rec
    rec['http']=st; rec['final_url']=final
    s=body.decode('utf-8','replace')
    try:
        doc=Document(s); summary=doc.summary()
    except Exception as e:
        rec.update(ok=False, error=f'extract:{type(e).__name__}'); return rec
    btext=strip_html(summary)
    rec['chars']=len(btext)
    rec['paragraphs']=len(re.findall(r'<p[\s>]', summary, re.I))

    whole=strip_html(s)
    pw_page=sorted({m.pattern for m in P_RE if m.search(whole)})
    pw_body=sorted({m.pattern for m in P_RE if m.search(btext)})
    rec['paywall_in_page']=pw_page
    rec['paywall_in_body']=pw_body
    # chrome-only = in the page but NOT in the body
    rec['paywall_chrome_only']=sorted(set(pw_page)-set(pw_body))

    tail=btext[-TAIL:] if btext else ''
    cue=sorted({m.pattern for m in C_RE if m.search(tail)})
    rec['ends_on_subscribe_cue']=cue

    if feed_text_len >= DESC_IMPLIES:
        ratio=(rec['chars']/feed_text_len) if feed_text_len else None
        rec['trunc_ratio']=round(ratio,3) if ratio is not None else None
        rec['trunc_applicable']=True
        rec['truncated_vs_feed']=bool(ratio is not None and ratio < TRUNC_RATIO)
    else:
        rec['trunc_applicable']=False; rec['trunc_ratio']=None
        rec['truncated_vs_feed']=False

    rec['wall_refined']=bool(pw_body or cue or rec['truncated_vs_feed'])
    rec['readable_refined']=bool(rec['chars']>=READABLE_CHARS
                                 and rec['paragraphs']>=READABLE_PARAS
                                 and not rec['wall_refined'])
    rec['ok']=True
    return rec

def run():
    feeds=[]
    for p in sorted(os.listdir(os.path.join(R2,'pages'))):
        if not p.endswith('.json'): continue
        feeds.append(json.load(open(os.path.join(R2,'pages',p))))
    last=defaultdict(float)
    for i,f in enumerate(feeds,1):
        out=os.path.join(PAGES, f['label']+'.json')
        if os.path.exists(out):
            print(f'[{i}/{len(feeds)}] {f["label"]:<34} on disk', flush=True); continue
        items=feed_items(f['label'])[:10]
        recs=[]
        for (link,title,_d,ftl) in items:
            h=urlparse(link).netloc
            w=1.3-(time.time()-last[h])
            if w>0: time.sleep(w)
            recs.append(measure(link,title,ftl)); last[h]=time.time()
        ok=[r for r in recs if r.get('ok')]
        ch=sorted(r['chars'] for r in ok)
        res={'label':f['label'],'lang':f['lang'],'group':f['group'],
             'pages_attempted':len(recs),'pages_ok':len(ok),
             'readable_refined':sum(1 for r in ok if r['readable_refined']),
             'wall_refined':sum(1 for r in ok if r['wall_refined']),
             'readable_share_refined':round(100.0*sum(1 for r in ok if r['readable_refined'])/len(ok),1) if ok else None,
             'median_chars':ch[len(ch)//2] if ch else None,
             'readable_share_old':f.get('readable_share'),
             'walled_old':f.get('walled'),
             'measured_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
             'pages':recs}
        json.dump(res, open(out,'w'), ensure_ascii=False, indent=1)
        print(f'[{i}/{len(feeds)}] {f["label"]:<34} ok {len(ok)}/{len(recs)}  '
              f'readable OLD {res["readable_share_old"]}% -> NEW {res["readable_share_refined"]}%  '
              f'wall {res["wall_refined"]}', flush=True)

if __name__=='__main__':
    run()
