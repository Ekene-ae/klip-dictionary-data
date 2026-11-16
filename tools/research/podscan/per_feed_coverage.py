#!/usr/bin/env python3
"""Per-FEED corrected coverage: episodes with SRT/VTT / episodes checked.

The earlier pass persisted only per-language totals, so this re-fetches and
PERSISTS PER FEED (per_feed_coverage.json) so it never needs repeating.
Normalisation mirrors podcast_feed.dart. Absolute per-feed deadline.
"""
import json, re, sys, time, urllib.request
USABLE={'srt','vtt'}
def fmt_mime(t):
    t=(t or '').strip().lower()
    if t.startswith('/'): t=t[1:]
    t=t.split(';')[0].strip()
    if not t: return None
    if 'subrip' in t or t.endswith('/srt') or t.endswith('x-srt'): return 'srt'
    for k in ('vtt','json','html'):
        if k in t: return k
    return 'text' if t=='text/plain' else None
def fmt_url(u):
    p=(u or '').strip().split('?')[0].split('#')[0]
    last=p.rsplit('/',1)[-1]
    if '.' not in last: return None
    return {'srt':'srt','vtt':'vtt','webvtt':'vtt','json':'json','html':'html',
            'htm':'html','txt':'text'}.get(last.rsplit('.',1)[1].lower())
def norm(m,u):
    a,b=fmt_mime(m),fmt_url(u)
    return b if b is not None else a
def grab(url,deadline=45.0,cap=30_000_000):
    t0=time.monotonic()
    req=urllib.request.Request(url,headers={'User-Agent':'klip-measure/1.0'})
    out,n=[],0
    with urllib.request.urlopen(req,timeout=12) as r:
        while time.monotonic()-t0<deadline and n<cap:
            b=r.read(262144)
            if not b: break
            out.append(b); n+=len(b)
    return b''.join(out)
ITEM=re.compile(rb'<item>.*?</item>',re.S)
TR=re.compile(rb'<podcast:transcript\b([^>]*)/?>',re.I)
ATTR=re.compile(rb'(\w+)\s*=\s*"([^"]*)"')
MONTHS={m:i+1 for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}
def pubdate(b):
    m=re.search(rb'<pubDate>([^<]+)</pubDate>',b)
    if not m: return None
    t=m.group(1).decode('utf-8','replace')
    g=re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})',t)
    if not g: return None
    mo=MONTHS.get(g.group(2).lower())
    return f'{g.group(3)}-{mo:02d}-{int(g.group(1)):02d}' if mo else None
def assess(url, cap_items=25):
    raw=grab(url)
    items=ITEM.findall(raw)
    checked=items[:cap_items]
    usable=0; dates=[]; fmts_seen=set()
    for it in checked:
        got=[]
        for m in TR.finditer(it):
            a=dict((k.decode().lower(),vv.decode('utf-8','replace')) for k,vv in ATTR.findall(m.group(1)))
            if a.get('url'): got.append(norm(a.get('type'),a['url']))
        fmts_seen.update(str(g) for g in got)
        if any(g in USABLE for g in got): usable+=1
        d=pubdate(it)
        if d: dates.append(d)
    return {'total_items':len(items),'checked':len(checked),'usable':usable,
            'coverage':round(100.0*usable/len(checked),1) if checked else 0.0,
            'latest':max(dates) if dates else None,'formats':sorted(fmts_seen)}
mode=sys.argv[1]
if mode=='starter':
    doc=json.load(open('/Users/idap.jorgensen/Projects/klip/tool/audio_ingest/starter_feeds.json'))
    out={}
    for lang,v in doc['languages'].items():
        out[lang]={}
        for f in v['feeds']:
            try: out[lang][f['name']]={**assess(f['feed']),'feed':f['feed']}
            except Exception as e: out[lang][f['name']]={'error':type(e).__name__,'feed':f['feed']}
            print('.',end='',flush=True)
    json.dump(out,open('per_feed_coverage.json','w'),ensure_ascii=False,indent=1)
else:
    cands=json.load(open('/tmp/da_candidates.json'))
    out={}
    for c in cands:
        try: out[c['name']]={**assess(c['feed']),'feed':c['feed'],'host':c['host']}
        except Exception as e: out[c['name']]={'error':type(e).__name__,'feed':c['feed'],'host':c['host']}
        print('.',end='',flush=True)
    json.dump(out,open('da_candidate_coverage.json','w'),ensure_ascii=False,indent=1)
print(' done')
