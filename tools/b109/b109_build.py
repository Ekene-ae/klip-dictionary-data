#!/usr/bin/env python3
"""B-109 — add the two frequency fields to the Danish pack. OUTSIDE THE REPO.

**IT WORKS ON A COPY. The published v6 asset is never touched by this script.**

WHY A POST-PASS ON THE BUILT PACK RATHER THAN A BUILDER RE-RUN
    `build_pack.dart` derives entries FROM a kaikki extract, and the extract
    behind the current 55,906 entries was not retained. kaikki serves a
    ROLLING dump, so a fresh fetch is a DIFFERENT extract — re-running the
    builder would change entry content, which is a far larger data change
    than a frequency field and would make the diff unreadable. This pass adds
    the two fields and leaves every existing row byte-identical, which is what
    "entries unchanged at 55,906" requires. The extract question goes to the
    owner with the diff.
"""
import hashlib, json, os, shutil, sqlite3, sys, datetime

S = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser('~/b107/downloads/pack-da/klip-dict-da.sqlite')
OUT = os.path.join(S, 'klip-dict-da.candidate.sqlite')
THRESHOLD = 20

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

before_sha, before_bytes = sha(SRC), os.path.getsize(SRC)
print('input pack  %s  %d bytes' % (before_sha[:16] + '…', before_bytes))
assert before_sha == 'aab33f71c0105df94598d51523e68d991b519cc8e575b7d3e979ae46577780bc', \
    'the input is not the published v6 Danish pack'

freq = {}
for line in open(S + '/b109_freq.tsv', encoding='utf-8'):
    f, n = line.rstrip('\n').split('\t')
    freq[f] = int(n)

shutil.copy2(SRC, OUT)
db = sqlite3.connect(OUT)

# ── BEFORE: the fingerprints every existing table must still have after ──
def fingerprint(c):
    out = {}
    for t in ('entry', 'sense', 'form', 'meta'):
        n = c.execute('select count(*) from %s' % t).fetchone()[0]
        out[t] = n
    # Content, not just counts: a stable digest over every existing row.
    rows = c.execute('select id, headword, fold, pos, gender, ipa, audio, class '
                     'from entry order by id').fetchall()
    out['entry_digest'] = hashlib.sha256(repr(rows).encode()).hexdigest()
    rows = c.execute('select entry_id, ord, gloss from sense order by entry_id, ord').fetchall()
    out['sense_digest'] = hashlib.sha256(repr(rows).encode()).hexdigest()
    rows = c.execute('select lemma_id, form, fold, tags, target, collapsed from form '
                     'order by lemma_id, form, fold').fetchall()
    out['form_digest'] = hashlib.sha256(repr(rows).encode()).hexdigest()
    return out
before = fingerprint(db)
print('before: entry %d · sense %d · form %d · meta %d'
      % (before['entry'], before['sense'], before['form'], before['meta']))

# ── 1. entry.lemma_freq, NULLABLE ────────────────────────────────────────
db.execute('ALTER TABLE entry ADD COLUMN lemma_freq INTEGER')
lemma_fold = {i: f for i, f in db.execute("select id, fold from entry where class='lemma'")}
forms_of = {}
for lid, fl in db.execute('select lemma_id, fold from form where lemma_id is not null'):
    forms_of.setdefault(lid, set()).add(fl)
upd = []
for lid, lf in lemma_fold.items():
    v = freq.get(lf, 0) + sum(freq.get(x, 0) for x in forms_of.get(lid, ()))
    # NULL, not 0: a lemma the corpora never contain has no count, and 0 would
    # be a claim rather than an absence.
    upd.append((v if v else None, lid))
db.executemany('UPDATE entry SET lemma_freq=? WHERE id=?', upd)
nz = db.execute('select count(*) from entry where lemma_freq is not null').fetchone()[0]
print('lemma_freq: %d lemmas written, %d non-null (%.1f%%)' % (len(upd), nz, 100.0*nz/len(upd)))

# ── 2. known_form, at the ruled threshold ────────────────────────────────
pack_folds = {f for (f,) in db.execute('select fold from entry')}
pack_folds |= {f for (f,) in db.execute('select fold from form')}
rows = [(f, n) for f, n in freq.items()
        if n >= THRESHOLD and len(f) > 2 and f not in pack_folds]
db.execute('CREATE TABLE known_form(fold TEXT PRIMARY KEY, freq INTEGER NOT NULL)')
db.executemany('INSERT INTO known_form VALUES (?,?)', rows)
print('known_form: %d rows at freq >= %d' % (len(rows), THRESHOLD))

# ── 3. meta — provenance and the credits ─────────────────────────────────
# The CURRENT JRC page (owner ruling 2026-11-18), VERIFIED LIVE 2026-11-18:
# title "DGT-Translation Memory - Joint Research Centre - European Commission",
# carrying the same ownership and attribution language as the archive's LICENSE.
# The archive's own README still names the OLD ec.europa.eu/jrc path; the
# licence requires "the website address", and a live one serves the reader.
DGT_PAGE = ('https://joint-research-centre.ec.europa.eu/'
            'language-technology-resources/dgt-translation-memory_en')
SOURCE = ('English Wiktionary, extracted by wiktextract and published at kaikki.org. '
          'Word-frequency data from three parallel corpora, Danish side: '
          'DGT-TM, release 2021, distributed via OPUS (package 2026-07-18), '
          + DGT_PAGE + ' — The European Commission retains ownership of the data; '
          'Europarl v8, extracted from the European Parliament web site by '
          'Philipp Koehn (University of Edinburgh); and Tatoeba v2026-07-08, '
          'from tatoeba.org.')
LICENCE = (
    'Dictionary entries: CC BY-SA and GFDL — the same licences as Wiktionary. '
    'This pack is a derived database and carries the same share-alike terms. '
    'Word-frequency data: Tatoeba under CC BY 2.0 FR; DGT under the Commission '
    'Decision of 12 December 2011 on the re-use of Commission documents '
    '(OJ L330, 14 December 2011, pp. 39-42), which requires the website '
    'address, the date of the latest update and the fact that the European '
    'Commission retains ownership of the data — all three are stated in the '
    'source line; Europarl under the same licence as its original sources, the '
    'European Parliament. OPUS asks that its packages be cited as '
    'J. Tiedemann, 2012, Parallel Data, Tools and Interfaces in OPUS, '
    'LREC 2012.')
new_meta = {
  'source': SOURCE,
  'licence': LICENCE,
  'freq_corpora': 'DGT v2021; Europarl v8; Tatoeba v2026-07-08',
  'freq_tokens': '131679525',
  'freq_threshold': str(THRESHOLD),
  'freq_archive_sha256': ('dgt=6e654992791140f5fc60ac4a2eef7980cb539b2574f9e0b19b4778cf0e5fedfb; '
                          'europarl=83eddbf2c016c39a5b0b6d3468dd65417f7a65acfd0e31cbdb5217ae6361a2dd; '
                          'tatoeba=a8662857fdc0bbb10d93726cb239db440e94f98469e954c07ca29ba477cc7514'),
  'freq_built_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'freq_input_pack_sha256': before_sha,
  'kaikki_extract_sha256': 'UNRECOVERABLE — see kaikki_extract_note',
  'kaikki_extract_note': ('The extract these entries were built from (2026-11-06) was not '
                          'retained, and kaikki.org serves a rolling dump with no versioned '
                          'archive, so it cannot be re-fetched or digested. A digest taken '
                          'today would describe a DIFFERENT extract and would be a false '
                          'provenance claim for these entries. Owed at the next pack REBUILD, '
                          'where the extract is in hand.'),
}
changed = []
for k, v in new_meta.items():
    old = db.execute('select value from meta where key=?', (k,)).fetchone()
    changed.append((k, 'changed' if old else 'new'))
    db.execute('INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)', (k, v))
db.commit()
print('meta: %s' % ', '.join('%s (%s)' % kv for kv in changed))

# pack_format is NOT touched — exact-equality check in the service.
fmt = db.execute("select value from meta where key='pack_format'").fetchone()[0]
assert fmt == '2', fmt
print('pack_format: %s — unchanged, as ruled' % fmt)

db.execute('VACUUM')
after = fingerprint(db)
db.close()

# ── THE GUARANTEE: every pre-existing row is byte-identical ──────────────
ok = True
for k in ('entry', 'sense', 'form', 'entry_digest', 'sense_digest', 'form_digest'):
    same = before[k] == after[k]
    ok &= same
    print('%-14s %s' % (k, 'IDENTICAL' if same else 'CHANGED — STOP'))
assert ok, 'a pre-existing row changed; refusing to call this a field addition'
print('meta rows: %d -> %d (+%d)' % (before['meta'], after['meta'], after['meta']-before['meta']))

out_sha, out_bytes = sha(OUT), os.path.getsize(OUT)
print('\ncandidate pack %s  %d bytes (%.2f MiB, %+.1f%%)'
      % (out_sha[:16] + '…', out_bytes, out_bytes/1048576,
         100.0*(out_bytes-before_bytes)/before_bytes))
json.dump({'before_sha': before_sha, 'before_bytes': before_bytes,
           'after_sha': out_sha, 'after_bytes': out_bytes,
           'known_form_rows': len(rows), 'lemma_freq_nonnull': nz,
           'meta_added': after['meta']-before['meta'], 'threshold': THRESHOLD},
          open(S + '/b109_diff.json', 'w'), indent=1)
