"""readscan report — one table per language, then the summary. Reads feeds/*.json."""
import json, glob, os, re
BASE=os.path.expanduser('~/dict-work/readscan')
recs=[]
for p in sorted(glob.glob(os.path.join(BASE,'feeds','*.json'))):
    if os.path.basename(p).startswith('_'): continue
    recs.append(json.load(open(p)))
LANGS=['da','de','fr','es','it','en']
GNAME={'a-broadcaster-press':'(a) broadcaster / press',
       'b-easy-language':'(b) easy-language',
       'c-eu-institutions':'(c) EU institutions',
       'd-wikinews':'(d) Wikinews'}
def row(r):
    if not r.get('ok'):
        return (f"  {r['label']:<34} {'—':<5} {'—':>5} {'—':>7} {'—':>7} {'—':<11} "
                f"FAILED: {r.get('error','')[:34]}")
    lang = r.get('declared_lang_base') or '—'
    conf = '✓' if r.get('lang_confirmed') else ('✗' if r.get('declared_lang') else '—')
    return (f"  {r['label']:<34} {r['dialect']:<5} {r['items']:>5} "
            f"{str(r['full_text_pct'])+'%':>7} {str(r['desc_full_pct'])+'%':>7} "
            f"{str(r['latest_item'] or '—'):<11} {lang}{conf}  "
            f"med c/d {r['median_chars']}/{r['median_desc_chars']}")
print('='*118)
print('readscan — the Read starter list\'s INPUT MEASUREMENT.  2026-11-07')
print('FULL% = items whose content:encoded / Atom <content>, HTML-STRIPPED, exceeds 1,500 chars  (the ruled definition)')
print('DESC% = the same test on <description>/<summary>        med c/d = median stripped chars, content / description')
print('='*118)
for lg in LANGS:
    rs=[r for r in recs if r.get('lang')==lg]
    if not rs: continue
    print(f'\n── {lg.upper()} ' + '─'*106)
    print(f"  {'FEED':<34} {'DIAL':<5} {'ITEMS':>5} {'FULL%':>7} {'DESC%':>7} {'LATEST':<11} LANG")
    for g in ['a-broadcaster-press','b-easy-language','c-eu-institutions','d-wikinews']:
        gr=[r for r in rs if r['group']==g]
        if not gr: continue
        print(f'  {GNAME[g]}')
        for r in sorted(gr, key=lambda x: -(x.get('full_text_pct') or 0)): print(row(r))
other=[r for r in recs if r.get('lang') not in LANGS]
if other:
    print(f'\n── REFERENCE (outside the six) ' + '─'*86)
    for r in other: print(row(r))
# ── SUMMARY ──
ok=[r for r in recs if r.get('ok')]
fail=[r for r in recs if not r.get('ok')]
f80=[r for r in ok if (r.get('full_text_pct') or 0)>=80]
d80=[r for r in ok if (r.get('desc_full_pct') or 0)>=80]
atom=[r for r in ok if r['dialect']=='Atom']
rss1=[r for r in ok if r['dialect']=='RSS1']
nolang=[r for r in ok if not r.get('declared_lang')]
badlang=[r for r in ok if r.get('declared_lang') and not r.get('lang_confirmed')]
print('\n'+'='*118)
print('SUMMARY')
print('='*118)
print(f'  candidates probed                      {len(recs)}')
print(f'  parsed as a feed                       {len(ok)}')
print(f'  failed (404 / 403 / HTML / malformed)  {len(fail)}')
print()
print(f'  FEEDS WITH >=80% FULL TEXT (ruled definition, content:encoded/Atom content)')
print(f'      {len(f80)} of {len(ok)}  ({100*len(f80)/len(ok):.0f}%)' + (':' if f80 else ''))
for r in f80: print(f'        {r["label"]:<34} {r["full_text_pct"]}%  median {r["median_chars"]} chars')
print()
print(f'  FEEDS WITH >=80% FULL TEXT IN <description> INSTEAD')
print(f'      {len(d80)} of {len(ok)}' + (':' if d80 else ''))
for r in d80: print(f'        {r["label"]:<34} {r["desc_full_pct"]}%  median {r["median_desc_chars"]} chars')
print()
print(f'  ATOM SHARE                             {len(atom)} of {len(ok)} ({100*len(atom)/len(ok):.0f}%)'
      f'   [RSS {len(ok)-len(atom)-len(rss1)}, RSS1/RDF {len(rss1)}, Atom {len(atom)}]')
print(f'      every Atom feed is a Wikinews RecentChanges stream: '
      f'{sorted(set(r["label"].split("-")[1] for r in atom))}')
print(f'  DECLARED LANGUAGE absent               {len(nolang)} of {len(ok)}: '
      f'{", ".join(r["label"] for r in nolang)}')
print(f'  DECLARED LANGUAGE present but ≠ expected {len(badlang)}'
      + (': '+", ".join(f'{r["label"]}={r["declared_lang"]}' for r in badlang) if badlang else ''))
