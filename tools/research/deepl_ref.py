#!/usr/bin/env python3
"""deepl_ref.py — the DeepL oracle for the d1b bench. OUTSIDE THE REPO.

Same CSV contract as argos_ref.py: reads a stratified samples CSV, writes a
refs CSV carrying tier and zipf through untouched.

WHAT IS SENT: dictionary HEADWORDS only — public CC-BY-SA material from
English Wiktionary via kaikki.org. NO LEARNER DATA, NO APP DATA, NOTHING
ELSE ABOUT KLIP. Approved by the owner on exactly those terms.

WHAT COMES BACK IS EVALUATION-ONLY and NEVER ENTERS THE PACK OR THE REPO.
DeepL's output is not openly licensed; see DICTIONARY_SOURCES.md. Any other
use must be RE-RULED from scratch.

KEY: DEEPL_API_KEY from the environment, or DEEPL_AUTH_KEY if that is what
  is exported — the FIRST of the two that is set. Never a flag, never
  logged. (This file required DEEPL_AUTH_KEY alone until 2026-11-17 and
  would have refused to run against the DEEPL_API_KEY this project
  actually exports; owner ruling the same day: read it, and DO NOT
  export a second copy of the key under another name.)
  A key ending `:fx` is a Free-tier key and selects api-free.deepl.com;
  anything else selects api.deepl.com. Getting that wrong returns 403 with
  no hint, so it is derived rather than configured.

USAGE
  python3 deepl_ref.py --languages                 what DeepL supports
  python3 deepl_ref.py --usage                     characters used this period
  python3 deepl_ref.py --dry-run <samples.csv> <lang>
  python3 deepl_ref.py <samples.csv> <refs.csv> <lang> [budget]
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _oracle_common import (DEFAULT_BUDGET, Budget, api_code, post_json,  # noqa: E402
                            read_samples, require_key_any, write_refs)

# Accepted in this order; the first one SET wins. See require_key_any.
KEY_VARS = ('DEEPL_API_KEY', 'DEEPL_AUTH_KEY')

ORACLE = 'deepl'


def _host(key):
    return 'https://api-free.deepl.com' if key.endswith(':fx') \
        else 'https://api.deepl.com'


def _translate(key, text, source, target):
    r = post_json(
        _host(key) + '/v2/translate',
        {'text': text, 'source_lang': source.upper(), 'target_lang': target.upper()},
        {'Authorization': 'DeepL-Auth-Key ' + key,
         'Content-Type': 'application/x-www-form-urlencoded'})
    return (r.get('translations') or [{}])[0].get('text', '')


def cmd_languages():
    key = require_key_any(*KEY_VARS)
    for direction in ('source', 'target'):
        r = post_json(_host(key) + '/v2/languages', {'type': direction},
                      {'Authorization': 'DeepL-Auth-Key ' + key,
                       'Content-Type': 'application/x-www-form-urlencoded'})
        codes = sorted(x['language'].lower() for x in r)
        print('%-6s %s' % (direction, ' '.join(codes)))
    need = ['ar', 'da', 'de', 'el', 'es', 'fr', 'hi', 'it', 'ja', 'ko',
            'nl', 'nb', 'pl', 'pt', 'ru', 'sv', 'tr', 'zh']
    print()
    print('Klip needs: %s' % ' '.join(need))
    print('A LANGUAGE DeepL DOES NOT SUPPORT IS A FINDING, NOT AN ERROR — '
          'report it rather than substituting another.')


def cmd_usage():
    key = require_key_any(*KEY_VARS)
    r = post_json(_host(key) + '/v2/usage', {},
                  {'Authorization': 'DeepL-Auth-Key ' + key,
                   'Content-Type': 'application/x-www-form-urlencoded'})
    used, limit = r.get('character_count', 0), r.get('character_limit', 0)
    print('deepl usage  %d / %d characters (%.1f%%)'
          % (used, limit, (100.0 * used / limit) if limit else 0.0))


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
    if a[0] == '--usage':
        return cmd_usage()
    if a[0] == '--dry-run':
        return cmd_dry_run(a[1], a[2])
    samples, refs, klip = a[0], a[1], a[2]
    cap = int(a[3]) if len(a) > 3 else DEFAULT_BUDGET
    key = require_key_any(*KEY_VARS)
    code = api_code(klip)
    rows = read_samples(samples)
    budget = Budget(cap)
    write_refs(refs, ORACLE, klip, rows,
               lambda t: _translate(key, t, code, 'en-US'),
               lambda t: _translate(key, t, 'en', code),
               budget)
    cmd_usage()


if __name__ == '__main__':
    main(sys.argv[1:])
