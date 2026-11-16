"""readscan 3 (a) — WIKIPEDIA. 50 random mainspace articles per wiki.

MEASURED AT THE END OF THE PIPELINE, which is the rule readscan keeps
re-learning: plain-text characters a reader would actually see, not the
presence of a carrier. The Action API's `prop=extracts&explaintext=1` returns
exactly that — the article as text, no wrapper to inflate the count.

Random sampling is `list=random&rnnamespace=0`, so the sample is mainspace
articles including stubs. THAT IS THE POINT: a learner's Read surface would
meet the same distribution.
"""
import json, os, re, ssl, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone

UA='readscan/3 (Klip Read starter-list measurement; stdlib urllib)'
CTX=ssl.create_default_context()
BASE=os.path.expanduser('~/dict-work/readscan3')
WIKIS=['da','de','fr','es','it','en','simple']
N=50
FULL=1200
SPACING=0.9

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

def rest(host, path):
    u=f'https://{host}/api/rest_v1/{path}'
    r=urllib.request.Request(u, headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(r, timeout=30, context=CTX) as resp:
        return resp.status, resp.read(), dict(resp.headers)

def plain_paras(t):
    # the Action API's explaintext output separates paragraphs by \n\n and
    # section headings by == .. ==
    blocks=[b.strip() for b in re.split(r'\n\s*\n', t or '') if b.strip()]
    return [b for b in blocks if not re.match(r'^=+\s.*\s=+$', b)]

def run():
    out={}
    for w in WIKIS:
        host=f'{w}.wikipedia.org'
        rec={'wiki':w,'host':host,
             'measured_at':datetime.now(timezone.utc).isoformat(timespec='seconds')}
        # ── licence, from the API itself ──
        try:
            si=api(host, dict(action='query', meta='siteinfo', siprop='rightsinfo|statistics'))
            ri=si['query']['rightsinfo']
            rec['licence_text']=ri.get('text'); rec['licence_url']=ri.get('url')
            rec['articles_total']=si['query']['statistics']['articles']
        except Exception as e:
            rec['licence_error']=f'{type(e).__name__}: {str(e)[:60]}'
        time.sleep(SPACING)
        # ── featured / "today" feed availability ──
        d=datetime.now(timezone.utc)
        try:
            st,b,h=rest(host, f'feed/featured/{d:%Y/%m/%d}')
            j=json.loads(b)
            rec['featured_feed']={'http':st,'bytes':len(b),
                                  'sections':sorted(j.keys()) if isinstance(j,dict) else None,
                                  'has_tfa':'tfa' in j if isinstance(j,dict) else None,
                                  'mostread_n':len((j.get('mostread') or {}).get('articles',[])) if isinstance(j,dict) else None}
        except urllib.error.HTTPError as e:
            body=b''
            try: body=e.read()[:200]
            except Exception: pass
            rec['featured_feed']={'http':e.code,'error':f'HTTP {e.code}',
                                  'body':body.decode('utf-8','replace')[:200]}
        except Exception as e:
            rec['featured_feed']={'error':f'{type(e).__name__}: {str(e)[:70]}'}
        time.sleep(SPACING)
        # ── 50 random mainspace articles ──
        try:
            rnd=api(host, dict(action='query', list='random', rnnamespace=0, rnlimit=N))
            titles=[p['title'] for p in rnd['query']['random']]
        except Exception as e:
            rec['error']=f'random: {type(e).__name__}'; out[w]=rec; continue
        rec['sample_n']=len(titles)
        arts=[]
        for t in titles:
            time.sleep(SPACING)
            try:
                q=api(host, dict(action='query', prop='extracts', explaintext=1,
                                 exlimit=1, redirects=1, titles=t))
                pg=(q.get('query',{}).get('pages') or [{}])[0]
                txt=pg.get('extract') or ''
                ps=plain_paras(txt)
                arts.append({'title':pg.get('title',t),'chars':len(txt),
                             'paragraphs':len(ps),
                             'first_para_chars':len(ps[0]) if ps else 0})
            except Exception as e:
                arts.append({'title':t,'error':f'{type(e).__name__}'})
        ok=[a for a in arts if 'chars' in a]
        ch=sorted(a['chars'] for a in ok)
        rec['articles']=arts
        rec['measured_n']=len(ok)
        rec['full_text_items']=sum(1 for a in ok if a['chars']>=FULL)
        rec['full_text_pct']=round(100.0*rec['full_text_items']/len(ok),1) if ok else None
        rec['median_chars']=ch[len(ch)//2] if ch else None
        rec['p25_chars']=ch[len(ch)//4] if ch else None
        rec['p75_chars']=ch[3*len(ch)//4] if ch else None
        rec['max_chars']=ch[-1] if ch else None
        pr=sorted(a['paragraphs'] for a in ok)
        rec['median_paragraphs']=pr[len(pr)//2] if pr else None
        rec['pct_3plus_paras']=round(100.0*sum(1 for a in ok if a['paragraphs']>=3)/len(ok),1) if ok else None
        rec['readable_pct']=round(100.0*sum(1 for a in ok if a['chars']>=FULL and a['paragraphs']>=3)/len(ok),1) if ok else None
        json.dump(rec, open(os.path.join(BASE,'wiki',f'{w}.json'),'w'), ensure_ascii=False, indent=1)
        print(f"{w:<8} n={rec['measured_n']:<3} >={FULL}ch {rec['full_text_pct']}%  "
              f"readable {rec['readable_pct']}%  median {rec['median_chars']}  "
              f"p25/p75 {rec['p25_chars']}/{rec['p75_chars']}  "
              f"featured {rec['featured_feed'].get('http','ERR')}", flush=True)
        out[w]=rec
    return out

if __name__=='__main__':
    run()
