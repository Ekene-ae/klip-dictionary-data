#!/usr/bin/env python3
# Re-fetch the final set to confirm nothing moved. ABSOLUTE per-feed deadline.
import json, re, time, urllib.request
import xml.etree.ElementTree as ET
PODCAST_NS='podcastindex.org/namespace'
MONTHS={m:i+1 for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}
def pubdate(s):
    if not s: return None
    m=re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})',s)
    if not m: return None
    mo=MONTHS.get(m.group(2).lower())
    return f'{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}' if mo else None
def grab(url, deadline=60.0, cap=40_000_000):
    t0=time.monotonic()
    req=urllib.request.Request(url, headers={'User-Agent':'klip-review/1.0'})
    out=[]; n=0
    with urllib.request.urlopen(req, timeout=15) as r:
        while time.monotonic()-t0 < deadline and n < cap:
            b=r.read(262144)
            if not b: break
            out.append(b); n+=len(b)
    return b''.join(out)
final=json.load(open('/tmp/final_set.json'))
res={}
for lang, rows in final.items():
    res[lang]=[]
    for row in rows:
        rec=dict(row)
        try:
            ch=ET.fromstring(grab(row['feed'])).find('channel')
            items=ch.findall('item')
            dates=[d for d in (pubdate(i.findtext('pubDate')) for i in items) if d]
            tr=sum(1 for i in items if any(PODCAST_NS in (e.tag or '') and e.tag.endswith('transcript') for e in i))
            rec.update({'title':(ch.findtext('title') or '').strip(),
                        'declared_language':(ch.findtext('language') or '').strip(),
                        'episodes':len(items),'episodes_with_transcript':tr,
                        'coverage_pct':round(100.0*tr/len(items),1) if items else 0.0,
                        'first_episode':min(dates) if dates else None,
                        'latest_episode':max(dates) if dates else None,'error':None})
        except Exception as e:
            rec['error']=type(e).__name__
        res[lang].append(rec); print('.',end='',flush=True)
    print(f' {lang}')
json.dump(res, open('/tmp/confirmed.json','w'), ensure_ascii=False, indent=1)
errs=[(l,r['name']) for l,v in res.items() for r in v if r.get('error')]
print('ERRORS:', errs or 'none')
