#!/usr/bin/env python3
# Live-fetch the candidate feeds. ABSOLUTE PER-FEED DEADLINE, not a socket
# timeout — the zh lesson: urlopen(timeout=) is per-socket-operation and a
# trickling feed resets it on every read.
import json, re, time, urllib.request
import xml.etree.ElementTree as ET
PODCAST_NS='podcastindex.org/namespace'
DEADLINE=50.0; CAP=30_000_000
MONTHS={m:i+1 for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}
def pubdate(s):
    if not s: return None
    m=re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})',s)
    if not m: return None
    mo=MONTHS.get(m.group(2).lower())
    return f'{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}' if mo else None
def grab(url):
    started=time.monotonic()
    req=urllib.request.Request(url,headers={'User-Agent':'klip-review/1.0'})
    chunks=[];n=0
    with urllib.request.urlopen(req,timeout=12) as r:
        while True:
            if time.monotonic()-started>DEADLINE or n>=CAP: break
            b=r.read(262144)
            if not b: break
            chunks.append(b); n+=len(b)
    return b''.join(chunks)
pool=json.load(open('/tmp/pool3.json'))
out={}
for lang,v in pool.items():
    out[lang]=[]
    for c in v['cands']:
        rec=dict(c)
        try:
            ch=ET.fromstring(grab(c['feed'])).find('channel')
            items=ch.findall('item')
            dates=[d for d in (pubdate(i.findtext('pubDate')) for i in items) if d]
            tr=sum(1 for i in items if any(PODCAST_NS in (e.tag or '') and e.tag.endswith('transcript') for e in i))
            rec.update({'title':(ch.findtext('title') or '').strip(),
                        'lang':(ch.findtext('language') or '').strip(),
                        'items':len(items),'with_tr':tr,
                        'cov':(100.0*tr/len(items)) if items else 0.0,
                        'first':min(dates) if dates else None,
                        'latest':max(dates) if dates else None,'error':None})
        except Exception as e:
            rec.update({'error':f'{type(e).__name__}'})
        out[lang].append(rec)
        print('.',end='',flush=True)
    print(f' {lang} done')
json.dump(out,open('/tmp/cands3.json','w'),ensure_ascii=False,indent=1)
print('ALL DONE')
