"""readscan 2b-dr — THE 18 DR CANDIDATES PLUS sporten, 2026-11-08.

WHY A SEPARATE DIRECTORY AND NOT readscan2b/pages. `report_b6.py` GLOBS
readscan2b/pages/*.json, and its figures (63 feeds, 409 pages, 56% refined)
are quoted in LEARN_LOOP_DESIGN.md §3.11/§4b. Writing 19 DR feeds into that
directory would SILENTLY RESTATE A PUBLISHED MEASUREMENT. Same pipeline, same
detector, separate ledger.

THE DETECTOR IS NOT REIMPLEMENTED — b6scan is IMPORTED and its `measure` and
`feed_items` are called directly, with b6scan.R1 repointed at this run's own
raw/ so the ITEM SELECTION is the same code too (10 most recent by date).

AND THE BODIES ARE STILL NOT KEPT. Only positions, ratios and verdicts.
"""
import importlib.util, json, os, ssl, statistics, sys, time, urllib.request
from datetime import datetime, timezone

BASE = os.path.expanduser('~/dict-work/readscan2b-dr')
B6   = os.path.expanduser('~/dict-work/readscan2b/b6scan.py')
spec = importlib.util.spec_from_file_location('b6scan', B6)
b6   = importlib.util.module_from_spec(spec); spec.loader.exec_module(b6)
b6.R1 = BASE                      # feed_items reads R1/raw/<label>.xml

FEEDS = [  # (label, feed path) — the 18 candidates of §3.13, plus sporten
    ('da-dr-indland','indland'), ('da-dr-udland','udland'),
    ('da-dr-penge','penge'), ('da-dr-politik','politik'),
    ('da-dr-viden','viden'), ('da-dr-kultur','kultur'),
    ('da-dr-musik','musik'), ('da-dr-vejret','vejret'),
    ('da-dr-regionale','regionale'),
    ('da-dr-reg-kbh','regionale/kbh'), ('da-dr-reg-bornholm','regionale/bornholm'),
    ('da-dr-reg-syd','regionale/syd'), ('da-dr-reg-fyn','regionale/fyn'),
    ('da-dr-reg-vest','regionale/vest'), ('da-dr-reg-nord','regionale/nord'),
    ('da-dr-reg-trekanten','regionale/trekanten'),
    ('da-dr-reg-sjaelland','regionale/sjaelland'),
    ('da-dr-reg-oestjylland','regionale/oestjylland'),
    ('da-dr-sporten','sporten'),          # NOT a candidate: measured to settle it
]
FEEDBASE='https://www.dr.dk/nyheder/service/feeds/'
CTX=ssl.create_default_context()

def get_feed(label, path):
    out=os.path.join(BASE,'raw',label+'.xml')
    if os.path.exists(out): return out
    rq=urllib.request.Request(FEEDBASE+path, headers={'User-Agent':b6.UA})
    with urllib.request.urlopen(rq, timeout=b6.TIMEOUT, context=CTX) as r:
        open(out,'wb').write(r.read())
    return out

def main():
    last=0.0
    for i,(label,path) in enumerate(FEEDS,1):
        rec_path=os.path.join(BASE,'pages',label+'.json')
        if os.path.exists(rec_path):
            print(f'[{i}/{len(FEEDS)}] {label:<26} on disk', flush=True); continue
        get_feed(label,path)
        items=b6.feed_items(label)[:10]
        recs=[]
        for (link,title,_d,ftl) in items:
            w=1.3-(time.time()-last)
            if w>0: time.sleep(w)
            last=time.time()
            recs.append(b6.measure(link,title,ftl))
        ok=[r for r in recs if r.get('ok')]
        rd=[r for r in ok if r['readable_refined']]
        rec={'label':label,'lang':'da','group':'dr-topical',
             'feed_url':FEEDBASE+path,
             'pages_attempted':len(recs),'pages_ok':len(ok),
             'readable_refined':len(rd),
             'wall_refined':sum(1 for r in ok if r['wall_refined']),
             'paywall_in_body':sum(1 for r in ok if r.get('paywall_in_body')),
             'readable_share_refined':(100.0*len(rd)/len(ok)) if ok else None,
             'median_chars':(statistics.median([r['chars'] for r in ok])) if ok else None,
             'readable_share_old':None,   # no readscan 2 record exists for these feeds
             'walled_old':None,
             'measured_at':datetime.now(timezone.utc).isoformat(),
             'pages':recs}
        json.dump(rec, open(rec_path,'w'), indent=1)
        print('[%d/%d] %-26s ok %2d  read %3.0f%%  med %6s  body %d  wall %d' % (
            i,len(FEEDS),label,len(ok),rec['readable_share_refined'] or 0,
            rec['median_chars'],rec['paywall_in_body'],rec['wall_refined']), flush=True)

main()
