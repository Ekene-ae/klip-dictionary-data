"""The DR table, plus the SAMPLE-VARIANCE check that the threshold needs."""
import json, glob, os, statistics
BASE=os.path.expanduser('~/dict-work/readscan2b-dr')
OLD =os.path.expanduser('~/dict-work/readscan2b')
ORDER=['da-dr-indland','da-dr-udland','da-dr-penge','da-dr-politik','da-dr-viden',
 'da-dr-kultur','da-dr-musik','da-dr-vejret','da-dr-regionale','da-dr-reg-kbh',
 'da-dr-reg-bornholm','da-dr-reg-syd','da-dr-reg-fyn','da-dr-reg-vest',
 'da-dr-reg-nord','da-dr-reg-trekanten','da-dr-reg-sjaelland',
 'da-dr-reg-oestjylland','da-dr-sporten']
recs={}
for p in glob.glob(os.path.join(BASE,'pages','*.json')):
    r=json.load(open(p)); recs[r['label']]=r
L=[];a=L.append
a('%-24s %5s %5s %8s %9s %6s %6s' % ('FEED','FTCH','OK','READ%','MED CHARS','BODY','WALL'))
a('-'*70)
for lb in ORDER:
    r=recs.get(lb)
    if not r: a('%-24s  (no record)'%lb); continue
    a('%-24s %5d %5d %7.0f%% %9.0f %6d %6d' % (lb,r['pages_attempted'],r['pages_ok'],
        r['readable_share_refined'] or 0, r['median_chars'] or 0,
        r['paywall_in_body'], r['wall_refined']))
a('-'*70)
ok=[g for lb in ORDER if lb in recs for g in recs[lb]['pages'] if g.get('ok')]
rd=sum(1 for g in ok if g['readable_refined'])
a('%-24s %5s %5d %7.0f%% %9.0f %6d %6d' % ('ALL 19 POOLED','',len(ok),
   100.0*rd/len(ok), statistics.median([g['chars'] for g in ok]),
   sum(1 for g in ok if g.get('paywall_in_body')), sum(1 for g in ok if g['wall_refined'])))
a('')
a('THRESHOLD AT >=50%% READABLE')
a('-'*70)
q=[lb for lb in ORDER if lb in recs and (recs[lb]['readable_share_refined'] or 0)>=50]
f=[lb for lb in ORDER if lb in recs and (recs[lb]['readable_share_refined'] or 0)<50]
a('QUALIFY (%d): %s' % (len(q), ', '.join(q)))
a('BELOW   (%d): %s' % (len(f), ', '.join(f)))
a('')
a('SAMPLE VARIANCE — indland measured TWICE, same pipeline, different 10 items')
a('-'*70)
old=os.path.join(OLD,'pages','da-dr-indland.json')
if os.path.exists(old) and 'da-dr-indland' in recs:
    o=json.load(open(old)); n=recs['da-dr-indland']
    oo=[g for g in o['pages'] if g.get('ok')]; nn=[g for g in n['pages'] if g.get('ok')]
    orr=sum(1 for g in oo if g['readable_refined']); nr=sum(1 for g in nn if g['readable_refined'])
    a('readscan2b  %s  %d/%d = %.0f%%  median %.0f' % (o['measured_at'][:10],orr,len(oo),100.0*orr/len(oo),statistics.median([g['chars'] for g in oo])))
    a('this run    %s  %d/%d = %.0f%%  median %.0f' % (n['measured_at'][:10],nr,len(nn),100.0*nr/len(nn),statistics.median([g['chars'] for g in nn])))
    urls={g['url'] for g in oo} & {g['url'] for g in nn}
    a('items shared between the two runs: %d' % len(urls))
    pool={}
    for g in oo+nn: pool.setdefault(g['url'],g)
    pr=sum(1 for g in pool.values() if g['readable_refined'])
    a('POOLED DISTINCT  %d/%d = %.0f%%  median %.0f' % (pr,len(pool),100.0*pr/len(pool),
        statistics.median([g['chars'] for g in pool.values()])))
print('\n'.join(L))
open(os.path.join(BASE,'reports','dr_refined.txt'),'w').write('\n'.join(L)+'\n')
