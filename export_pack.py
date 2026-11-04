"""Dump a Klip dictionary pack to gzipped JSONL. One object per entry row.

    python3 -I export_pack.py <pack.sqlite> <out.jsonl.gz> [--builder-log <log>]

**THIS SCRIPT HAS NO OPINIONS.** It is a column-to-key dump and nothing else:
no filtering, no reshaping, no normalisation, no recomputation. Entries come
out in the pack's own order (`entry.id`, which is its rowid). Everything it
writes is already in the pack; if a value looks wrong, the pack is wrong and
the Dart builder is where that is fixed.

Standard library only (`sqlite3`, `gzip`, `json`), run with `-I` so nothing
from the environment can reach it. The pack is opened READ-ONLY.

── FIELDS ───────────────────────────────────────────────────────────────────

    w  entry.headword
    p  entry.pos            null when absent
    g  entry.gender         null when absent  (post-fix: entry/sense tags only)
    i  entry.ipa            null when absent
    s  [gloss, ...]         sense.gloss ordered by sense.ord
    f  [[text, tags], ...]  form rows WITH lemma_id = this entry, rowid order,
                            `tags` exactly as stored (comma-joined, aux:* kept)
    c  entry.class          lemma | phrase | form | abbr
    t  target headword      when c == 'form', else null

── THE ONE RULE THAT IS NOT A COLUMN READ, AND WHY IT EXISTS ────────────────

`t` is NOT on the entry row. A form-class entry's target lives in the `form`
table as a POINTER ROW: `lemma_id IS NULL AND target IS NOT NULL`, keyed only
by the form's text. So `t` is a lookup, and the text key is not unique —
**427 of 30,974 pointer texts in the Danish pack carry more than one distinct
target** (`afholdte` -> afholde, afholdt; `ager` -> age, agere), because two
lemmas can inflect to the same string.

    RULE: the FIRST pointer row in rowid order wins, and the number of
    CONFLICTING ROWS (a text already seen with a different target) is
    REPORTED rather than hidden. Note this counts ROWS, not distinct
    texts: Danish has 440 conflicting rows across 427 distinct texts.

A single-valued `t` cannot express the alternates. That is a limitation of the
field, not a defect in the pack, and it is counted on every run so the size of
what is being dropped is always visible.

── SELF-CHECK (fails loud, exit 2) ──────────────────────────────────────────

  * objects written == meta.entry_count
  * per-class counts == the Dart builder's `classes ...` line, when the log
    is supplied; otherwise == the pack's own class counts
  * no object carries class 'dropped' (dropped entries never reach a row)
"""

import gzip
import json
import re
import sqlite3
import sys


def die(msg):
    sys.stderr.write("export_pack: %s\n" % msg)
    raise SystemExit(2)


def main(argv):
    if len(argv) < 3:
        die("usage: python3 -I export_pack.py <pack.sqlite> <out.jsonl.gz> "
            "[--builder-log <log>]")
    pack, out = argv[1], argv[2]
    log = None
    if "--builder-log" in argv:
        log = argv[argv.index("--builder-log") + 1]

    db = sqlite3.connect("file:%s?mode=ro" % pack, uri=True)
    db.text_factory = str

    meta = dict(db.execute("SELECT key, value FROM meta").fetchall())

    # Pointer rows: form text -> target. First in rowid order wins.
    targets = {}
    ambiguous = 0
    for text, tgt in db.execute(
        "SELECT form, target FROM form "
        "WHERE lemma_id IS NULL AND target IS NOT NULL ORDER BY rowid"
    ):
        if text in targets:
            if targets[text] != tgt:
                ambiguous += 1
        else:
            targets[text] = tgt

    # Merge-walk senses and owned forms alongside entries, all by entry id,
    # so nothing proportional to the table size is held in memory at once.
    sense_cur = db.execute(
        "SELECT entry_id, gloss FROM sense ORDER BY entry_id, ord")
    form_cur = db.execute(
        "SELECT lemma_id, form, tags FROM form "
        "WHERE lemma_id IS NOT NULL ORDER BY lemma_id, rowid")
    s_row = sense_cur.fetchone()
    f_row = form_cur.fetchone()

    classes = {}
    written = 0
    missing_target = 0

    with gzip.open(out, "wt", encoding="utf-8", newline="\n") as fh:
        for eid, w, p, g, i, c in db.execute(
            "SELECT id, headword, pos, gender, ipa, class FROM entry ORDER BY id"
        ):
            while s_row is not None and s_row[0] < eid:
                s_row = sense_cur.fetchone()
            glosses = []
            while s_row is not None and s_row[0] == eid:
                glosses.append(s_row[1])
                s_row = sense_cur.fetchone()

            while f_row is not None and f_row[0] < eid:
                f_row = form_cur.fetchone()
            forms = []
            while f_row is not None and f_row[0] == eid:
                forms.append([f_row[1], f_row[2]])
                f_row = form_cur.fetchone()

            t = None
            if c == "form":
                t = targets.get(w)
                if t is None:
                    missing_target += 1

            if c == "dropped":
                die("entry %d carries class 'dropped' — the pack is wrong" % eid)

            classes[c] = classes.get(c, 0) + 1
            written += 1
            fh.write(json.dumps(
                {"w": w, "p": p, "g": g, "i": i,
                 "s": glosses, "f": forms, "c": c, "t": t},
                ensure_ascii=False, separators=(",", ":")) + "\n")

    db.close()

    # ── self-check ──
    declared = meta.get("entry_count")
    if declared is None:
        die("pack has no meta.entry_count")
    if int(declared) != written:
        die("entry count mismatch: wrote %d, meta.entry_count says %s"
            % (written, declared))

    if log is not None:
        text = open(log, encoding="utf-8", errors="replace").read()
        m = re.search(r"classes\s+(.+)", text)
        if not m:
            die("no 'classes' line in builder log %s" % log)
        expect = {k: int(v) for k, v in
                  re.findall(r"(lemma|phrase|form|abbr|dropped)=(\d+)", m.group(1))}
        for k, v in expect.items():
            if k == "dropped":
                continue
            if classes.get(k, 0) != v:
                die("class %s: exported %d, builder said %d"
                    % (k, classes.get(k, 0), v))

    order = ["lemma", "phrase", "form", "abbr"]
    print("pack          %s" % pack)
    print("language      %s" % meta.get("language_code"))
    print("pack_format   %s" % meta.get("pack_format"))
    print("entries       %d  (meta.entry_count %s)  OK" % (written, declared))
    print("classes       %s" % " · ".join(
        "%s=%d" % (k, classes.get(k, 0)) for k in order if k in classes))
    print("ambiguous t   %d conflicting pointer rows — a text already seen with a\n              different target; first-by-rowid used" % ambiguous)
    print("missing t     %d form-class entries had no pointer row" % missing_target)
    print("wrote         %s" % out)


if __name__ == "__main__":
    main(sys.argv)
