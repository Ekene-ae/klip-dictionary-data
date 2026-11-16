"""readscan 2 report — per-language page-level tables, then the summary bands."""
import json, os, glob
BASE=os.path.expanduser('~/dict-work/readscan2')
P=os.path.join(BASE,'pages')
LANGS=['da','de','fr','es','it','en']
GN={'a-broadcaster-press':'(a) broadcaster / press','b-easy-language':'(b) easy-language',
    'c-eu-institutions':'(c) EU institutions','d-wikinews':'(d) Wikinews'}
recs=[json.load(open(p)) for p in sorted(glob.glob(os.path.join(P,'*.json')))]
def band(r):
    s=r.get('readable_share')
    if s is None: return 'none'
    walled_share = 100.0*r['walled']/r['pages_ok'] if r['pages_ok'] else 0
    if walled_share >= 50: return 'walled'
    if s >= 80: return '>=80'
    if s >= 50: return '>=50'
    return '<50'
print('='*120)
print("readscan 2 — PAGE-LEVEL EXTRACTION.  readability-lxml, plain browser UA, NO JS, NO COOKIES.  2026-11-07")
print('READABLE = >=1,200 extracted chars AND >=3 paragraphs AND no wall')
print('WALL     = login redirect, OR paywall marker with <1,200 chars, OR consent marker with <300 chars')
print('='*120)
for lg in LANGS:
    rs=[r for r in recs if r['lang']==lg]
    if not rs: continue
    print(f'\n── {lg.upper()} ' + '─'*108)
    print(f"  {'FEED':<34}{'PAGES':>6}{'READ%':>7}{'WALL':>5}{'MEDCH':>7}{'TITLE%':>7}  BAND   TOP WALL MARKERS")
    for g in ['a-broadcaster-press','b-easy-language','c-eu-institutions','d-wikinews']:
        gr=[r for r in rs if r['group']==g]
        if not gr: continue
        print(f'  {GN[g]}')
        for r in sorted(gr, key=lambda x: -(x.get('readable_share') or 0)):
            mk={}
            for pg in r['pages']:
                for m in pg.get('paywall_markers',[]): mk[m]=mk.get(m,0)+1
                if pg.get('login_redirect'): mk['LOGIN']=mk.get('LOGIN',0)+1
            top=', '.join(f'{k}×{v}' for k,v in sorted(mk.items(), key=lambda x:-x[1])[:3])
            print(f"  {r['label']:<34}{r['pages_ok']:>3}/{r['pages_attempted']:<2}"
                  f"{str(r['readable_share'])+'%':>7}{r['walled']:>5}{str(r['median_chars']):>7}"
                  f"{str(r['title_match_share'])+'%':>7}  {band(r):<7}{top}")
print('\n'+'='*120)
print('SUMMARY — READABLE SHARE BANDS, PER LANGUAGE')
print('='*120)
print(f"  {'LANG':<6}{'FEEDS':>6}{'>=80%':>7}{'>=50%':>7}{'<50%':>7}{'WALLED':>8}{'no pages':>10}   median of medians")
tot={}
for lg in LANGS:
    rs=[r for r in recs if r['lang']==lg]
    if not rs: continue
    b=[band(r) for r in rs]
    meds=sorted(r['median_chars'] for r in rs if r['median_chars'] is not None)
    print(f"  {lg:<6}{len(rs):>6}{b.count('>=80'):>7}{b.count('>=50'):>7}{b.count('<50'):>7}"
          f"{b.count('walled'):>8}{b.count('none'):>10}   {meds[len(meds)//2] if meds else '-'}")
    for k in ['>=80','>=50','<50','walled','none']: tot[k]=tot.get(k,0)+b.count(k)
print(f"  {'ALL':<6}{len(recs):>6}{tot.get('>=80',0):>7}{tot.get('>=50',0):>7}{tot.get('<50',0):>7}"
      f"{tot.get('walled',0):>8}{tot.get('none',0):>10}")
print()
best=[r for r in recs if band(r)=='>=80']
print(f'  FEEDS AT >=80% READABLE  ({len(best)} of {len(recs)}):')
for r in sorted(best, key=lambda x:-x['readable_share']):
    print(f"      {r['lang']}  {r['label']:<34} {r['readable_share']}%  median {r['median_chars']} chars")
w=[r for r in recs if band(r)=='walled']
print(f'\n  FEEDS WALLED ON >=50% OF PAGES  ({len(w)}):')
for r in w: print(f"      {r['lang']}  {r['label']:<34} walled {r['walled']}/{r['pages_ok']}")
allp=[pg for r in recs for pg in r['pages']]
okp=[pg for pg in allp if pg.get('ok')]
print(f'\n  PAGES: {len(allp)} attempted, {len(okp)} fetched, {len(allp)-len(okp)} failed')
print(f'  pages readable      {sum(1 for p in okp if p["readable"]):>5}  ({100*sum(1 for p in okp if p["readable"])/len(okp):.0f}%)')
print(f'  pages walled        {sum(1 for p in okp if p["wall"]):>5}')
print(f'  login redirects     {sum(1 for p in okp if p.get("login_redirect")):>5}')
print(f'  paywall marker seen {sum(1 for p in okp if p.get("paywall_markers")):>5}')
print(f'  consent marker seen {sum(1 for p in okp if p.get("consent_markers")):>5}')
print(f'  title match         {sum(1 for p in okp if p.get("title_match")):>5}  ({100*sum(1 for p in okp if p.get("title_match"))/len(okp):.0f}%)')
