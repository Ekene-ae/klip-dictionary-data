"""(c) EU PRESS CORNER — is the per-language PAGE actually in that language?

readscan 1 found the parallel KEY confirmed 10/10 across six language feeds,
but every feed served IDENTICAL ENGLISH titles and linked to /detail/en/.
This fetches /detail/<lang>/<ref> directly and asks the only question that
matters for parallel reading: IS THE TEXT DIFFERENT, OR IS ENGLISH BEING
SERVED UNDER A DANISH PATH?
"""
import gzip, json, os, re, ssl, time, urllib.error, urllib.request, html as H
from datetime import datetime, timezone
from readability import Document

UA=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
CTX=ssl.create_default_context()
R1=os.path.expanduser('~/dict-work/readscan')
OUT=os.path.expanduser('~/dict-work/readscan2/reports')
LANGS=['en','da','de','fr','es','it']
SPACING=3.0

# Crude, independent language check: function words that are common in one of
# the six and rare in the others. NOT a classifier — a sanity check that the
# page is not English wearing another path.
STOP={'en':['the','and','that','with','will'],
      'da':['og','ikke','til','som','af'],
      'de':['und','nicht','der','die','auch'],
      'fr':['et','pas','les','des','pour'],
      'es':['y','no','los','las','para'],
      'it':['e','non','gli','delle','per']}
TAGS=re.compile(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>|<[^>]+>')
def strip(s): return ' '.join(H.unescape(TAGS.sub(' ', s or '')).split())
def guess_lang(txt):
    w=re.findall(r"[a-zà-öø-ÿ']+", txt.lower())
    if not w: return None, {}
    n=len(w); sc={}
    for lg,ws in STOP.items():
        sc[lg]=round(1000.0*sum(w.count(x) for x in ws)/n,1)
    return max(sc,key=sc.get), sc
def fetch(u):
    r=urllib.request.Request(u, headers={'User-Agent':UA,'Accept':'text/html,*/*','Accept-Encoding':'gzip'})
    with urllib.request.urlopen(r, timeout=25, context=CTX) as resp:
        b=resp.read(3_000_000)
        if resp.headers.get('Content-Encoding')=='gzip':
            try: b=gzip.decompress(b)
            except Exception: pass
        return resp.status, b, resp.geturl()

d=json.load(open(os.path.join(R1,'feeds','c-ec-presscorner-en.json')))
refs=[]
for i in d['item_ids']:
    m=re.search(r'/detail/[a-z]{2}/([a-z]+_\d+_\d+)', i)
    if m and m.group(1) not in refs: refs.append(m.group(1))
refs=refs[:10]
SPACING_NOTE='3s per request'
print(f'refs ({len(refs)}): {refs}\n')

res={'measured_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
     'refs':refs,'rows':[]}
hdr=f'{"REF":<14}' + ''.join(f'{lg.upper():>9}' for lg in LANGS) + '   VERDICT'
print('cells = META DESCRIPTION chars (readability gets 0 — the page is a JS shell)')
print(hdr); print('-'*(len(hdr)+8))
for ref in refs:
    row={'ref':ref,'by_lang':{}}
    for lg in LANGS:
        u=f'https://ec.europa.eu/commission/presscorner/detail/{lg}/{ref}'
        time.sleep(SPACING)
        try:
            st,b,fin=fetch(u)
            raw=b.decode('utf-8','replace')
            txt=strip(Document(raw).summary())
            # THE PAGE IS A JS SHELL (22 KB, 38 chars of text), so readability
            # gets nothing. The only text served without JS is the meta
            # description — so THAT is what the per-language comparison uses,
            # and the fact that it is the only option IS the finding.
            nos=re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>',' ', raw)
            whole=strip(nos)
            m=re.search(r'<meta[^>]+(?:property="og:description"|name="description")'
                        r'[^>]*content="([^"]{20,})"', raw)
            meta=H.unescape(m.group(1)) if m else ''
            g,sc=guess_lang(meta or txt)
            row['by_lang'][lg]={'http':st,'final_url':fin,
                                'readability_chars':len(txt),
                                'whole_page_chars':len(whole),
                                'meta_desc_chars':len(meta),
                                'guessed_lang':g,'stop_scores':sc,
                                'head':(meta or txt)[:160]}
        except urllib.error.HTTPError as e:
            row['by_lang'][lg]={'http':e.code,'error':f'HTTP {e.code}'}
        except Exception as e:
            row['by_lang'][lg]={'error':f'{type(e).__name__}: {str(e)[:60]}'}
    en=row['by_lang'].get('en',{}).get('head')
    diff=[lg for lg in LANGS[1:]
          if row['by_lang'].get(lg,{}).get('head') and row['by_lang'][lg]['head']!=en]
    same=[lg for lg in LANGS[1:]
          if row['by_lang'].get(lg,{}).get('head')==en and en]
    guessed_right=[lg for lg in LANGS[1:]
                   if row['by_lang'].get(lg,{}).get('guessed_lang')==lg]
    row['differs_from_en']=diff; row['identical_to_en']=same
    row['lang_guess_matches_path']=guessed_right
    res['rows'].append(row)
    cells=''.join(f'{row["by_lang"].get(lg,{}).get("meta_desc_chars","ERR"):>9}' for lg in LANGS)
    verdict=('TRANSLATED' if len(diff)==5 else
             f'{len(same)} IDENTICAL TO EN' if same else f'{len(diff)}/5 differ')
    print(f'{ref:<14}{cells}   {verdict}  guess-ok={len(guessed_right)}/5')
json.dump(res, open(os.path.join(OUT,'eu_parallel_pages.json'),'w'), ensure_ascii=False, indent=1)
tr=sum(1 for r in res['rows'] if len(r['differs_from_en'])==5)
print(f'\nFULLY TRANSLATED (all five differ from EN): {tr} of {len(res["rows"])} refs')
lg_ok=sum(len(r['lang_guess_matches_path']) for r in res['rows'])
print(f'LANGUAGE GUESS MATCHES PATH: {lg_ok} of {5*len(res["rows"])} language-pages')
