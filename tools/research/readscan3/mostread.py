"""readscan 3 (a) ADDENDUM — THE MOST-READ ARTICLES, NOT RANDOM ONES.

(a) sampled `list=random&rnnamespace=0` and that stays THE BASELINE: it is
what the encyclopaedia contains. THIS IS THE END-OF-PIPELINE FIGURE — what a
reader actually opens — taken from the featured feed's `mostread` list for a
FIXED DATE so the measurement is repeatable.

Same measures as (a): plain-text characters via Action API extracts, paragraph
count, share >=1,200 chars, and the same READABLE bar (>=1,200 chars AND >=3
paragraphs).
"""
import json, os, re, ssl, time, urllib.error, urllib.request
from datetime import datetime, timezone

UA='readscan/3 (Klip Read starter-list measurement; stdlib urllib)'
CTX=ssl.create_default_context()
BASE=os.path.expanduser('~/dict-work/readscan3')
import sys
WIKIS=(sys.argv[1].split(',') if len(sys.argv)>1 else ['da','de','fr','es','it','en'])
DATE='2026/11/06'
N=50
FULL=1200
SPACING=1.5

def api(host, params):
    u=f'https://{host}/w/api.php?format=json&formatversion=2&'+'&'.join(
        f'{k}={urllib.request.quote(str(v), safe="|")}' for k,v in params.items())
    for t in range(3):
        try:
            r=urllib.request.Request(u, headers={'User-Agent':UA})
            with urllib.request.urlopen(r, timeout=30, context=CTX) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code==429 and t<2: time.sleep(8*(t+1)); continue
            raise
        except Exception:
            if t<2: time.sleep(4*(t+1)); continue
            raise

def featured(host, date):
    u=f'https://{host}/api/rest_v1/feed/featured/{date}'
    for t in range(4):
        try:
            r=urllib.request.Request(u, headers={'User-Agent':UA,'Accept':'application/json'})
            with urllib.request.urlopen(r, timeout=30, context=CTX) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code==429 and t<3: time.sleep(20*(t+1)); continue
            raise

def plain_paras(t):
    blocks=[b.strip() for b in re.split(r'\n\s*\n', t or '') if b.strip()]
    return [b for b in blocks if not re.match(r'^=+\s.*\s=+$', b)]

out={}
print(f'{"WIKI":<6}{"n":>4}{">=1200ch":>10}{"READABLE":>10}{"MEDIAN":>8}{"p25":>7}{"p75":>7}'
      f'{"MED ¶":>7}{"VIEWS/med":>11}', flush=True)
print('-'*72)
for w in WIKIS:
    host=f'{w}.wikipedia.org'
    rec={'wiki':w,'host':host,'date':DATE,'sample':'mostread',
         'measured_at':datetime.now(timezone.utc).isoformat(timespec='seconds')}
    try:
        st,feed=featured(host, DATE)
        arts=(feed.get('mostread') or {}).get('articles',[])
        rec['feed_http']=st; rec['mostread_available']=len(arts)
        titles=[(a['title'], a.get('views')) for a in arts[:N]]
    except Exception as e:
        rec['error']=f'featured: {type(e).__name__}: {str(e)[:70]}'
        out[w]=rec; print(f'{w:<6} ERR {rec["error"]}'); continue
    time.sleep(SPACING)
    res=[]
    for t,views in titles:
        time.sleep(SPACING)
        try:
            q=api(host, dict(action='query', prop='extracts', explaintext=1,
                             exlimit=1, redirects=1, titles=t))
            pg=(q.get('query',{}).get('pages') or [{}])[0]
            txt=pg.get('extract') or ''
            ps=plain_paras(txt)
            res.append({'title':pg.get('title',t),'views':views,
                        'chars':len(txt),'paragraphs':len(ps)})
        except Exception as e:
            res.append({'title':t,'views':views,'error':type(e).__name__})
    ok=[a for a in res if 'chars' in a]
    ch=sorted(a['chars'] for a in ok); pr=sorted(a['paragraphs'] for a in ok)
    vw=sorted(a['views'] for a in ok if a.get('views'))
    rec.update(articles=res, measured_n=len(ok),
        full_text_items=sum(1 for a in ok if a['chars']>=FULL),
        full_text_pct=round(100.0*sum(1 for a in ok if a['chars']>=FULL)/len(ok),1) if ok else None,
        readable_pct=round(100.0*sum(1 for a in ok if a['chars']>=FULL and a['paragraphs']>=3)/len(ok),1) if ok else None,
        median_chars=ch[len(ch)//2] if ch else None,
        p25_chars=ch[len(ch)//4] if ch else None,
        p75_chars=ch[3*len(ch)//4] if ch else None,
        max_chars=ch[-1] if ch else None,
        median_paragraphs=pr[len(pr)//2] if pr else None,
        pct_3plus_paras=round(100.0*sum(1 for a in ok if a['paragraphs']>=3)/len(ok),1) if ok else None,
        median_views=vw[len(vw)//2] if vw else None)
    json.dump(rec, open(os.path.join(BASE,'wiki',f'{w}_mostread.json'),'w'),
              ensure_ascii=False, indent=1)
    out[w]=rec
    print(f'{w:<6}{rec["measured_n"]:>4}{str(rec["full_text_pct"])+"%":>10}'
          f'{str(rec["readable_pct"])+"%":>10}{rec["median_chars"]:>8}'
          f'{rec["p25_chars"]:>7}{rec["p75_chars"]:>7}{rec["median_paragraphs"]:>7}'
          f'{rec["median_views"] or "-":>11}', flush=True)
