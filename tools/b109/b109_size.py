#!/usr/bin/env python3
"""B-109 step 2 — size the two fields and test the filter's headline case."""
import collections, json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wordscreen import dict_fold

S = os.path.dirname(os.path.abspath(__file__))
P = os.path.expanduser('~/b107/downloads/pack-da/klip-dict-da.sqlite')

freq = {}
for line in open(S + '/b109_freq.tsv', encoding='utf-8'):
    f, n = line.rstrip('\n').split('\t')
    freq[f] = int(n)
print('frequency table: %d folds (count >= 2)' % len(freq))

db = sqlite3.connect('file:%s?mode=ro' % P, uri=True)
entries = db.execute('select id, headword, fold, class from entry').fetchall()
lemma_fold = {i: f for i, h, f, c in entries if c == 'lemma'}
lemma_head = {i: h for i, h, f, c in entries if c == 'lemma'}
forms_of = collections.defaultdict(set)
for lid, fm, fl in db.execute('select lemma_id, form, fold from form'):
    if lid is not None:
        forms_of[lid].add(fl)
pack_folds = {f for _, _, f, _ in entries} | {fl for _, _, fl in
              db.execute('select lemma_id, form, fold from form')}
print('pack folds (entry + form): %d' % len(pack_folds))

# ── USE 1: LEMMA FREQUENCY ───────────────────────────────────────────────
lemfreq = {}
for lid, lf in lemma_fold.items():
    lemfreq[lid] = freq.get(lf, 0) + sum(freq.get(x, 0) for x in forms_of.get(lid, ()))
nz = sum(1 for v in lemfreq.values() if v)
print('\nUSE 1 — lemma frequency over %d lemmas; %d have a non-zero count (%.1f%%)'
      % (len(lemfreq), nz, 100.0*nz/len(lemfreq)))

# Does it reproduce B-106's ten? Their margins are the published check.
B106 = [('hele','hel',2.0),('taler','tale',2.9),('kigger','kigge',2.8),
        ('var','være',3.2),('får','få',2.7),('går','gå',1.9),('lad','lade',1.2),
        ('skal','skulle',1.1),('tænker','tænke',1.03),('gange','gang',1.02)]
head_by_fold = collections.defaultdict(list)
for lid, h in lemma_head.items():
    head_by_fold[lemma_fold[lid]].append(lid)
print('\n  surface      own lemma     competing     mine    B-106   agrees?')
agree = 0
for surf, comp, b_margin in B106:
    sf, cf = dict_fold(surf), dict_fold(comp)
    own = max((lemfreq[l] for l in head_by_fold.get(sf, [])), default=0)
    other = max((lemfreq[l] for l in head_by_fold.get(cf, [])), default=0)
    m = (other / own) if own else float('inf')
    ok = (other > own)
    agree += ok
    print('  %-12s %9d %13d  %6.2fx %6.2fx   %s'
          % (surf, own, other, m, b_margin, 'picks the competing lemma' if ok else 'DISAGREES'))
print('  agreement with B-106\'s direction: %d of 10' % agree)

# ── USE 2: THE KNOWN-FORMS SET ───────────────────────────────────────────
SHORT = lambda f: len(f) <= 2
LOANSTEMS = ('podcast','episode','reality','summit','quote','approach','burger',
             'online','weekend','job','test','fitness','update','blog','app',
             'stream','playlist','sms','mail')
def keep(f):
    return not SHORT(f) and f not in pack_folds
print('\nUSE 2 — known Danish forms the pack does NOT already carry')
print('  threshold   folds     bytes (fold+count, utf-8)')
rows = []
for T in (2, 3, 5, 10, 20, 50, 100):
    ks = [f for f, n in freq.items() if n >= T and keep(f)]
    b = sum(len(f.encode()) + 4 for f in ks)
    rows.append((T, len(ks), b))
    print('  >= %-6d %8d   %8.1f MiB' % (T, len(ks), b/1048576))

# THE HEADLINE CASE, and it is not circular: altså's corpus frequency has
# nothing to do with B-110's labels.
print('\n  the case the filter exists for:')
for w in ('altså', 'kirkegård', 'quickfix', 'produktchef', 'ultraforarbejdet'):
    f = dict_fold(w)
    print('    %-18s corpus %7d   in pack: %-5s   admitted at >=5: %s'
          % (w, freq.get(f, 0), f in pack_folds, 'yes' if freq.get(f,0) >= 5 and keep(f) else 'no'))
print('\n  and the mishearings it must hide:')
for w in ('kirkår', 'grafsten', 'trovmand', 'ogog', 'mytte', 'bukt', 'unavngivende'):
    f = dict_fold(w)
    print('    %-18s corpus %7d   hidden at >=5: %s'
          % (w, freq.get(f, 0), 'yes' if not (freq.get(f,0) >= 5 and keep(f)) and f not in pack_folds else 'NO'))
json.dump({'thresholds': rows}, open(S + '/b109_sizing.json', 'w'))
