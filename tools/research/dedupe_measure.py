#!/usr/bin/env python3
"""PD3: folded-key dedupe measurement. SAFETY FIRST, SIZE SECOND. Outside the repo.

THE SIZE QUESTION IS THE EASY ONE. The question that decides whether the
dedupe is ADOPTABLE is whether rows sharing a folded key share a TARGET:

  if they do      -> the row is redundant and dropping it loses no lookup
  if they do NOT  -> dedupe must pick one target and LOSES A LEMMA POINTER

So this reports CONFLICTS before it reports bytes, and the bytes are measured
on a real deduped copy rather than projected from a row ratio (indices and
page overhead do not scale linearly with rows).

Precedent this is testing against: the Danish verb-form dedupe on NORMALISED
TEXT removed 17,729 of 38,097 rows and shrank that pack 3.2 MiB.
"""
import os, shutil, sqlite3, sys, tempfile

def measure(path):
    db = sqlite3.connect(path)
    q = db.execute
    before = q('SELECT COUNT(*) FROM form').fetchone()[0]
    distinct_fold = q('SELECT COUNT(*) FROM (SELECT DISTINCT fold FROM form)').fetchone()[0]
    # the candidate row set: one row per (fold, target) pair
    after = q("SELECT COUNT(*) FROM (SELECT DISTINCT fold, IFNULL(target,'') FROM form)").fetchone()[0]
    # SAFETY: folded keys that map to MORE THAN ONE target
    conflicts = q("""SELECT COUNT(*) FROM (
                       SELECT fold FROM form GROUP BY fold
                       HAVING COUNT(DISTINCT IFNULL(target,'')) > 1)""").fetchone()[0]
    conflict_rows = q("""SELECT IFNULL(SUM(n),0) FROM (
                           SELECT COUNT(*) AS n FROM form GROUP BY fold
                           HAVING COUNT(DISTINCT IFNULL(target,'')) > 1)""").fetchone()[0]
    sample = q("""SELECT fold, GROUP_CONCAT(DISTINCT IFNULL(target,'(null)')) FROM form
                  GROUP BY fold HAVING COUNT(DISTINCT IFNULL(target,'')) > 1 LIMIT 3""").fetchall()
    db.close()
    return before, distinct_fold, after, conflicts, conflict_rows, sample

def bytes_after(path):
    """Real bytes, from a deduped copy, vacuumed. Not a projection."""
    tmp = tempfile.mkdtemp(prefix='dd_')
    cp = os.path.join(tmp, 'c.sqlite')
    try:
        shutil.copyfile(path, cp)
        db = sqlite3.connect(cp)
        db.execute('PRAGMA journal_mode=OFF')
        db.execute("""CREATE TABLE form_dd AS
                      SELECT MIN(rowid) AS r FROM form GROUP BY fold, IFNULL(target,'')""")
        db.execute('DELETE FROM form WHERE rowid NOT IN (SELECT r FROM form_dd)')
        db.execute('DROP TABLE form_dd')
        db.commit(); db.execute('VACUUM'); db.close()
        return os.path.getsize(cp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    p = sys.argv[1]; code = sys.argv[2]
    b, df, a, cf, cr, sample = measure(p)
    bb = os.path.getsize(p)
    ba = bytes_after(p)
    print('PD3 %-3s rows %9d -> %9d (-%5.1f%%)  distinct_fold %9d'
          % (code, b, a, 100.0*(b-a)/b if b else 0, df))
    print('PD3 %-3s bytes %9d -> %9d (-%5.1f%%)' % (code, bb, ba, 100.0*(bb-ba)/bb if bb else 0))
    print('PD3 %-3s CONFLICTING folds %d  (rows involved %d)' % (code, cf, cr))
    for f, t in sample:
        print('PD3 %-3s   conflict e.g. fold=%r targets=%s' % (code, f[:24], t[:60]))
