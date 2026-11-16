"""readscan 3 (b) — THE ENDPOINT THE /detail/ SHELL CALLS, AND WHAT IT SERVES.

HOW IT WAS FOUND, so it can be found again when the bundle hash changes:
  1. GET /commission/presscorner/detail/da/ip_26_2334  -> a 22 KB Angular shell
  2. its <script src> / <link href> name main-*.js and five chunk-*.js
  3. grep the bundles for apiUrl:  L_={production:!0,apiUrl:"/commission/presscorner/api/"}
  4. grep for `${this.*Url}` template literals -> the endpoint list, including
     getDocumentlanguage():  documents?reference=${n.toUpperCase()}&language=${i}&ts=

THE REFERENCE FORM IS THE TRAP. The URL slug is `ip_26_2334`; the API wants
`IP/26/2334` WITH SLASHES. Every underscore form returns HTTP 200 WITH AN
EMPTY BODY — a success status for a request that found nothing, which is the
worst failure shape to debug. The slash form came from `refCode` in
latestnews, not from guessing.
"""
import json, os, re, ssl, sys, time, urllib.error, urllib.request, html as H
from datetime import datetime, timezone

UA=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
CTX=ssl.create_default_context()
API='https://ec.europa.eu/commission/presscorner/api/'
BASE=os.path.expanduser('~/dict-work/readscan3')
LANGS=['en','da','de','fr','es','it']
SPACING=1.6

def get(u):
    r=urllib.request.Request(u, headers={'User-Agent':UA,'Accept':'application/json, text/plain, */*'})
    with urllib.request.urlopen(r, timeout=25, context=CTX) as resp:
        return resp.status, resp.read(), dict(resp.headers)

def plain(h):
    s=re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>',' ', h or '')
    return ' '.join(H.unescape(re.sub(r'<[^>]+>',' ',s)).split())

def paras(h):
    return len(re.findall(r'<p[\s>]', h or '', re.I))

# ── collect recent ip_ / qanda_ references from latestnews, paged ──
def collect(n_want=10):
    refs=[]; page=1
    while len(refs) < n_want and page <= 12:
        ts=int(time.time()*1000)
        st,b,_=get(f'{API}latestnews?language=en&ts={ts}&pageNumber={page}&pageSize=50')
        d=json.loads(b)
        rows=d.get('docuLanguageListResources') or []
        if not rows: break
        for r in rows:
            code=(r.get('docutype') or {}).get('code','')
            ref=r.get('refCode','')
            if code in ('IP','QANDA','MEMO') and ref and ref not in [x[0] for x in refs]:
                if code in ('IP','QANDA'):
                    refs.append((ref, code, r.get('eventDate'), r.get('title')))
        page+=1
        time.sleep(SPACING)
    return refs[:n_want]

def doc(ref, lg):
    ts=int(time.time()*1000)
    u=f'{API}documents?reference={ref}&language={lg}&ts={ts}'
    try:
        st,b,h=get(u)
    except urllib.error.HTTPError as e:
        return {'http':e.code,'error':f'HTTP {e.code}'}
    if not b:
        return {'http':st,'error':'EMPTY BODY (200) — wrong reference form?'}
    d=json.loads(b)
    r=d.get('docuLanguageResource') or {}
    html=r.get('htmlContent') or ''
    t=plain(html)
    return {'http':st,'chars':len(t),'raw_chars':len(html),'paragraphs':paras(html),
            'title':(r.get('title') or '')[:200],
            'is_etranslated':r.get('isETranslated'),
            'languages_available':d.get('languages'),
            'etranslated_languages':d.get('eTranslatedlanguages'),
            'event_date':d.get('eventDate'),'publish_date':d.get('publishDate'),
            'head':t[:200]}

if __name__=='__main__':
    refs=collect(10)
    print(f'refs collected: {len(refs)}')
    for r in refs: print('  ', r[1], r[0], r[2], (r[3] or '')[:56])
    print()
    out={'measured_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
         'endpoint':API+'documents?reference=<REF WITH SLASHES>&language=<lg>&ts=<epoch ms>',
         'discovery':'bundle grep; see module docstring','rows':[]}
    hdr=f'{"REF":<16}{"TYPE":<7}' + ''.join(f'{l.upper():>8}' for l in LANGS) + '   AVAILABLE   DIFFER'
    print(hdr); print('-'*len(hdr))
    for ref,code,date,title in refs:
        row={'ref':ref,'type':code,'event_date':date,'title':title,'by_lang':{}}
        for lg in LANGS:
            time.sleep(SPACING)
            row['by_lang'][lg]=doc(ref,lg)
        en=row['by_lang']['en'].get('head')
        row['differs_from_en']=[lg for lg in LANGS[1:]
            if row['by_lang'][lg].get('head') and row['by_lang'][lg]['head']!=en]
        av=row['by_lang']['en'].get('languages_available') or []
        row['languages_available']=av
        out['rows'].append(row)
        cells=''.join(f'{row["by_lang"][l].get("chars","ERR"):>8}' for l in LANGS)
        print(f'{ref:<16}{code:<7}{cells}   {",".join(av) or "-":<11}{",".join(row["differs_from_en"]) or "none"}')
    json.dump(out, open(os.path.join(BASE,'eu','documents_api.json'),'w'), ensure_ascii=False, indent=1)
    n=len(out['rows'])
    print()
    print(f'refs measured                      {n}')
    print(f'per-language text served           {sum(1 for r in out["rows"] for l in LANGS if r["by_lang"][l].get("chars"))} of {6*n}')
    print(f'fully differing from EN (all five) {sum(1 for r in out["rows"] if len(r["differs_from_en"])==5)} of {n}')
    print(f'median EN chars                    '
          f'{sorted(r["by_lang"]["en"].get("chars",0) for r in out["rows"])[n//2] if n else "-"}')
