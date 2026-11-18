#!/usr/bin/env python3
"""B-109 step 1 — a FULL Danish surface-form frequency table. OUTSIDE THE REPO.

B-110 only needed counts for 2,880 known candidates. B-109 needs the whole
table twice over:
  LEMMA FREQUENCY   for the homograph rule — lemma plus every form the pack
                    lists for it, so a surface form can be attributed to the
                    commoner reading.
  KNOWN FORMS       corpus-frequent SURFACE forms, which is what lets the app
                    tell a real Danish word the pack lacks from a mishearing.

ONE CORPUS AT A TIME, DELETED BEFORE THE NEXT (the B6 sweep's method). The
counter is shared across all three, so the table is their union.
"""
import io, json, os, shutil, sys, urllib.request, zipfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wordscreen import dict_fold, TOKEN   # the replicated fold, asserted elsewhere

S = os.path.dirname(os.path.abspath(__file__))
DL = os.path.expanduser('~/b107/downloads')
UA = 'klip-research/1.0 (+B-109 Danish lemma frequency)'
corpora = json.load(open(S + '/b110_corpora.json', encoding='utf-8'))

freq = Counter()
per_corpus = {}
for name in ('Tatoeba', 'Europarl', 'DGT'):
    url = corpora[name]['url']
    d = os.path.join(DL, 'b109-' + name.lower())
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    zp = os.path.join(d, 'c.zip')
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(zp, 'wb') as f:
        shutil.copyfileobj(r, f, 1024 * 1024)
    print('%-9s zip %d bytes' % (name, os.path.getsize(zp)), flush=True)
    with zipfile.ZipFile(zp) as z:
        da = [n for n in z.namelist() if n.endswith('.da')]
        assert len(da) == 1, da
        z.extract(da[0], d)
        path = os.path.join(d, da[0])
    os.remove(zp)
    n_tok = 0
    before = len(freq)
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            for m in TOKEN.finditer(line):
                n_tok += 1
                freq[dict_fold(m.group(0))] += 1
    per_corpus[name] = {'tokens': n_tok, 'new_types': len(freq) - before,
                        'version': corpora[name]['version']}
    print('%-9s %12d tokens · table now %d distinct folds (+%d new)'
          % (name, n_tok, len(freq), len(freq) - before), flush=True)
    shutil.rmtree(d, ignore_errors=True)
    print('%-9s deleted' % name, flush=True)

print('\nTOTAL %d tokens across three corpora · %d distinct folds'
      % (sum(c['tokens'] for c in per_corpus.values()), len(freq)), flush=True)

# The table is kept at count >= 2. A fold seen ONCE in 131.7M tokens is as
# likely to be the corpus's own typo as a word, and keeping singletons would
# double the file for the least trustworthy half of it.
kept = {f: n for f, n in freq.items() if n >= 2}
print('folds with count >= 2: %d (%.1f%% of types)' % (len(kept), 100.0*len(kept)/len(freq)))
with open(S + '/b109_freq.tsv', 'w', encoding='utf-8') as out:
    for f, n in sorted(kept.items(), key=lambda kv: (-kv[1], kv[0])):
        out.write('%s\t%d\n' % (f, n))
json.dump(per_corpus, open(S + '/b109_corpus_meta.json', 'w'), indent=1)
print('wrote b109_freq.tsv (%d bytes)' % os.path.getsize(S + '/b109_freq.tsv'))
