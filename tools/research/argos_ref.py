#!/usr/bin/env python3
"""argos_ref.py — the Argos half of the PR (d1) bench. OUTSIDE THE REPO.

Reads a samples CSV from `bench.dart --emit-samples`, asks Argos Translate
for an English rendering of each headword (and the reverse), and writes a
refs CSV that `bench.dart --score` consumes.

WHY THIS IS NOT IN THE REPO
    Argos is Python with a large native dependency tree (ctranslate2,
    sentencepiece). Vendoring it would make `bench.dart` unrunnable from a
    bare checkout. The repo keeps the harness; this file keeps the oracle.

WHAT IT IS NOT
    NOT a source of pack data. Its output is a SIGNAL for a human look
    (DICTIONARY_SOURCES.md, "SIGNAL ONLY"). Nothing it produces is written
    back into a pack, ever.

USAGE
    python3 argos_ref.py --install <lang>...        install model pairs
    python3 argos_ref.py --list                     what is installed
    python3 argos_ref.py --licences <out.txt>       dump each model's README
    python3 argos_ref.py --zipf <cand.csv> <out.csv> <lang>   wordfreq zipf
    python3 argos_ref.py <samples.csv> <refs.csv> <lang>

LANGUAGE CODES
    Klip's pack codes are passed through EXCEPT `no`, which Argos/OPUS-MT
    call `nb` (Bokmal) — the owner's recorded mapping. `nn` (Nynorsk) is out
    of scope by ruling and is refused rather than silently mapped to `nb`.
"""
import csv
import sys
import os

# ── TWO WORKAROUNDS, BOTH FOUND THE HARD WAY ────────────────────────────────
#
# 1. THREADS PINNED TO ONE. ctranslate2 uses OpenMP, and on this Intel Mac two
#    concurrent interpreters holding the same model DEADLOCKED at 0.0% CPU —
#    two runs sat for 1h47m and 1h37m having written nothing. Pinned here so a
#    caller cannot forget.
# 2. os._exit AT THE END. A process that had ALREADY PRINTED its translation
#    then failed to exit, hanging in ctranslate2/OpenMP teardown. The work was
#    complete; only the shutdown hung. A hard exit skips it.
#
# **A HANG AFTER THE WORK IS DONE LOOKS IDENTICAL TO A HANG DURING IT** — the
# only thing that separated them was a flushed print landing before the stall.
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('CT2_INTER_THREADS', '1')
os.environ.setdefault('CT2_INTRA_THREADS', '1')

# Owner ruling: Klip `no` is Argos `nb`. `nn` is OUT OF SCOPE and must not be
# quietly folded into `nb` — a Nynorsk headword scored against a Bokmal model
# would be a measurement of the wrong language reported as the right one.
KLIP_TO_ARGOS = {'no': 'nb'}
REFUSED = {'nn': 'Nynorsk is out of scope by ruling; it is NOT nb'}


def argos_code(klip_code):
    if klip_code in REFUSED:
        raise SystemExit('refusing %s: %s' % (klip_code, REFUSED[klip_code]))
    return KLIP_TO_ARGOS.get(klip_code, klip_code)


def _pkg():
    import argostranslate.package
    return argostranslate.package


def cmd_list():
    import argostranslate.translate as tr
    langs = tr.get_installed_languages()
    print('installed languages: %d' % len(langs))
    for a in langs:
        for b in langs:
            if a is b:
                continue
            if a.get_translation(b):
                print('  %s -> %s' % (a.code, b.code))


def cmd_zipf(candidates_path, out_path, klip_code):
    """headword -> wordfreq zipf. Phase 0b of the stratified bench (ruling 1).

    A zipf of 0.0 means NO ENTRY in wordfreq, which the Dart side excludes
    from the sample and counts separately from "rarer than the known tier" —
    conflating those two would hide how much of the pack wordfreq cannot see.

    wordfreq's code for Norwegian is `nb`, the same mapping Argos needs.
    """
    from wordfreq import zipf_frequency, available_languages
    code = argos_code(klip_code)          # reuses the no->nb mapping
    if code not in available_languages():
        raise SystemExit('wordfreq has no data for %s (klip %s)' % (code, klip_code))
    with open(candidates_path, newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    out = open(out_path, 'w', newline='', encoding='utf-8')
    w = csv.writer(out)
    w.writerow(['headword', 'zipf'])
    n = 0
    for r in rows:
        hw = r['headword']
        w.writerow([hw, '%.4f' % zipf_frequency(hw, code)])
        n += 1
    out.close()
    print('zipf      %s (wordfreq %s)  n=%d  -> %s' % (klip_code, code, n, out_path))


def cmd_available(klip_codes):
    """Which L<->en pairs the index offers, WITHOUT downloading a model.

    A MISSING PAIR IS A FINDING, NOT AN ERROR. Reported so "all 19" can be
    checked before ~4 GB is spent, rather than discovered afterwards.
    """
    p = _pkg()
    p.update_package_index()
    index = p.get_available_packages()
    print('%-4s %-9s %-9s %s' % ('klip', 'argos', 'L->en', 'en->L'))
    missing = []
    for k in klip_codes:
        if k in REFUSED:
            print('%-4s %-9s %-9s %s' % (k, '-', 'REFUSED', REFUSED[k]))
            continue
        c = argos_code(k)
        f = next((x for x in index if x.from_code == c and x.to_code == 'en'), None)
        b = next((x for x in index if x.from_code == 'en' and x.to_code == c), None)
        print('%-4s %-9s %-9s %s' % (
            k, c,
            ('yes' if f else 'NO MODEL'), ('yes' if b else 'NO MODEL')))
        if not f:
            missing.append(k)
    print()
    print('index packages: %d' % len(index))
    print('NO L->en MODEL: %s' % (', '.join(missing) or 'none — all requested pairs exist'))


def cmd_install(klip_codes):
    p = _pkg()
    p.update_package_index()
    index = p.get_available_packages()
    want = set()
    for k in klip_codes:
        c = argos_code(k)
        want.add((c, 'en'))
        want.add(('en', c))
    got, missing = [], []
    for pair in sorted(want):
        hit = next((x for x in index
                    if x.from_code == pair[0] and x.to_code == pair[1]), None)
        if hit is None:
            missing.append('%s->%s' % pair)
            continue
        hit.install()
        got.append('%s->%s' % pair)
    print('installed : %s' % (', '.join(got) or 'none'))
    print('NO MODEL  : %s' % (', '.join(missing) or 'none'))
    if missing:
        print('A MISSING PAIR IS A FINDING, NOT AN ERROR — report it rather '
              'than substituting another language.')


def cmd_licences(out_path):
    """Dump every installed package's README and metadata VERBATIM.

    The arc's founding rule: no claim without a citation. A licence quoted
    from memory is not a verification, so this writes the actual bytes the
    package ships and records where they came from.
    """
    p = _pkg()
    lines = []
    for pkg in p.get_installed_packages():
        d = getattr(pkg, 'package_path', None)
        lines.append('=' * 70)
        lines.append('PACKAGE   %s -> %s  (%s)' %
                     (pkg.from_code, pkg.to_code, getattr(pkg, 'package_version', '?')))
        lines.append('PATH      %s' % d)
        for name in ('README', 'README.md', 'LICENSE', 'LICENSE.md', 'metadata.json'):
            fp = os.path.join(str(d), name) if d else None
            if fp and os.path.exists(fp):
                lines.append('--- %s ---' % name)
                with open(fp, encoding='utf-8', errors='replace') as fh:
                    lines.append(fh.read().strip())
        lines.append('')
    open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('wrote %s (%d packages)' % (out_path, len(p.get_installed_packages())))


def cmd_translate(samples_path, refs_path, klip_code):
    import argostranslate.translate as tr
    code = argos_code(klip_code)
    langs = {l.code: l for l in tr.get_installed_languages()}
    src, en = langs.get(code), langs.get('en')
    if src is None or en is None:
        raise SystemExit('no installed model for %s<->en' % code)
    fwd, rev = src.get_translation(en), en.get_translation(src)
    if fwd is None:
        raise SystemExit('no %s->en translation installed' % code)

    with open(samples_path, newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    out = open(refs_path, 'w', newline='', encoding='utf-8')
    w = csv.writer(out)
    # extract_sha256 is a REQUIRED column by ruling: a bench row whose inputs
    # are not pinned is not evidence. It is carried through from the samples.
    # tier and zipf are CARRIED THROUGH, not recomputed: the stratification
    # is the Dart side's ruled decision and this file must not re-derive it.
    # Dropping them once produced a bench whose HEADLINE row read n=0 while
    # every other number looked right.
    w.writerow(['language', 'headword', 'extract_sha256', 'l_to_en',
                'en_to_l', 'tier', 'zipf'])
    for i, r in enumerate(rows, 1):
        hw = r['headword']
        try:
            f = fwd.translate(hw).strip()
        except Exception as e:                      # noqa: BLE001
            f = ''
            print('  forward failed on %r: %s' % (hw, e), file=sys.stderr)
        b = ''
        if rev is not None and f:
            # en->L is the ROUND TRIP: translate the English back, and the
            # bench reports it SEPARATELY. It never folds into the primary
            # L->en metric (owner ruling).
            try:
                b = rev.translate(f).strip()
            except Exception as e:                  # noqa: BLE001
                print('  reverse failed on %r: %s' % (f, e), file=sys.stderr)
        w.writerow([klip_code, hw, r.get('extract_sha256', ''), f, b,
                    r.get('tier', ''), r.get('zipf', '')])
        if i % 25 == 0:
            print('  %s %d/%d' % (klip_code, i, len(rows)), flush=True)
    out.close()
    print('refs      %s  n=%d  -> %s' % (klip_code, len(rows), refs_path))


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == '--zipf':
        cmd_zipf(a[1], a[2], a[3])
    elif a[0] == '--available':
        cmd_available(a[1:])
    elif a[0] == '--list':
        cmd_list()
    elif a[0] == '--install':
        cmd_install(a[1:])
    elif a[0] == '--licences':
        cmd_licences(a[1])
    else:
        cmd_translate(a[0], a[1], a[2])
    # see the teardown note at the top: the work is done, the shutdown hangs.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
