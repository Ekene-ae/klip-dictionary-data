#!/usr/bin/env python3
"""google_ref.py — the Google Translate oracle for the d1b bench. OUTSIDE THE REPO.

Same CSV contract as argos_ref.py: reads a stratified samples CSV, writes a
refs CSV carrying tier and zipf through untouched.

WHAT IS SENT: dictionary HEADWORDS only — public CC-BY-SA material from
English Wiktionary via kaikki.org. NO LEARNER DATA, NO APP DATA, NOTHING
ELSE ABOUT KLIP. Approved by the owner on exactly those terms.

WHAT COMES BACK IS EVALUATION-ONLY and NEVER ENTERS THE PACK OR THE REPO.
Google's output is not openly licensed; see DICTIONARY_SOURCES.md. Any other
use must be RE-RULED from scratch.

KEY: GOOGLE_TRANSLATE_API_KEY from the environment. Never a flag, never
  logged. **THE KEY IS A QUERY PARAMETER IN THIS API**, so it would appear
  in any logged URL — error paths therefore report the host and status only,
  never the request URL.

USAGE
  python3 google_ref.py --languages                 what Google supports
  python3 google_ref.py --dry-run <samples.csv> <lang>
  python3 google_ref.py <samples.csv> <refs.csv> <lang> [budget]

Usage/quota: the v2 API returns no usage endpoint, so characters are counted
LOCALLY by the budget and reported. Billing is visible only in the console.
"""
import sys
import os
import urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _oracle_common import (DEFAULT_BUDGET, Budget, api_code, post_json,  # noqa: E402
                            read_samples, require_key, write_refs)

ORACLE = 'google'
BASE = 'https://translation.googleapis.com/language/translate/v2'


def _translate(key, text, source, target):
    # The key rides in the query string. It is interpolated ONLY here and
    # never passed to anything that logs or raises with the URL attached.
    url = '%s?key=%s' % (BASE, urllib.parse.quote(key))
    r = post_json(url, {'q': text, 'source': source, 'target': target,
                        'format': 'text'},
                  {'Content-Type': 'application/x-www-form-urlencoded'})
    t = (r.get('data', {}).get('translations') or [{}])
    return t[0].get('translatedText', '') if t else ''


def cmd_languages():
    key = require_key('GOOGLE_TRANSLATE_API_KEY')
    url = '%s/languages?key=%s&target=en' % (BASE, urllib.parse.quote(key))
    r = post_json(url, {}, {'Content-Type': 'application/x-www-form-urlencoded'})
    codes = sorted(x['language'] for x in r.get('data', {}).get('languages', []))
    print('google supports %d languages' % len(codes))
    need = ['ar', 'da', 'de', 'el', 'es', 'fr', 'hi', 'it', 'ja', 'ko',
            'nl', 'nb', 'pl', 'pt', 'ru', 'sv', 'tr', 'zh']
    missing = [c for c in need if c not in codes]
    print('Klip needs : %s' % ' '.join(need))
    print('MISSING    : %s' % (' '.join(missing) or 'none'))


def cmd_dry_run(samples, klip_code):
    rows = read_samples(samples)
    fwd = sum(len(r['headword']) for r in rows)
    print('dry-run   %s %s  rows=%d  forward chars=%d  '
          'projected total (incl. round trip) ~%d'
          % (ORACLE, klip_code, len(rows), fwd, int(fwd * 2.3)))
    print('NOTHING WAS SENT.')


def main(a):
    if not a:
        raise SystemExit(__doc__)
    if a[0] == '--languages':
        return cmd_languages()
    if a[0] == '--dry-run':
        return cmd_dry_run(a[1], a[2])
    samples, refs, klip = a[0], a[1], a[2]
    cap = int(a[3]) if len(a) > 3 else DEFAULT_BUDGET
    key = require_key('GOOGLE_TRANSLATE_API_KEY')
    code = api_code(klip)
    rows = read_samples(samples)
    budget = Budget(cap)
    write_refs(refs, ORACLE, klip, rows,
               lambda t: _translate(key, t, code, 'en'),
               lambda t: _translate(key, t, 'en', code),
               budget)
    print('google chars this run: %d (no usage endpoint on v2 — counted '
          'locally; billing is console-only)' % budget.used)


if __name__ == '__main__':
    main(sys.argv[1:])
