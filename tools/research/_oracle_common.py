"""Shared plumbing for the HTTP oracles (d1b). OUTSIDE THE REPO.

WHAT IS SENT, AND IT IS ONLY THIS
    Dictionary HEADWORDS from the published klip-dictionary-data assets —
    public CC-BY-SA material derived from English Wiktionary via kaikki.org.
    **NO LEARNER DATA, NO APP DATA, NOTHING ELSE ABOUT KLIP, EVER.** The
    outward send was approved by the owner on exactly those terms.

WHAT COMES BACK IS EVALUATION-ONLY
    DeepL and Google output is **NOT openly licensed**, unlike OPUS-MT's
    CC-BY 4.0. It NEVER enters a pack and never enters the repo: refs and
    review files live in ~/dict-work/bench/ by owner ruling (SC-1). Any
    other use must be RE-RULED from scratch.

KEYS COME FROM THE ENVIRONMENT AND ARE NEVER LOGGED
    DEEPL_AUTH_KEY, GOOGLE_TRANSLATE_API_KEY. They are not accepted as
    flags, never printed, never written to an output file, and never
    included in an error message — a traceback carrying a URL would carry
    the key with it, so request URLs are rebuilt for logging without it.

CHARACTER BUDGET
    Counted BEFORE each request and refused if it would exceed the cap, so a
    run stops and reports rather than silently truncating. Default 250,000
    characters per oracle per run, against free tiers of 500,000/month.
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BUDGET = 250_000

# Klip `no` is `nb` everywhere outside the pack; `nn` is out of scope by
# ruling and is REFUSED rather than folded into `nb` — a Nynorsk headword
# scored against a Bokmal model measures the wrong language.
KLIP_TO_API = {'no': 'nb'}
REFUSED = {'nn': 'Nynorsk is out of scope by ruling; it is NOT nb'}


def api_code(klip_code):
    if klip_code in REFUSED:
        raise SystemExit('refusing %s: %s' % (klip_code, REFUSED[klip_code]))
    return KLIP_TO_API.get(klip_code, klip_code)


def require_key(var):
    k = os.environ.get(var, '').strip()
    if not k:
        raise SystemExit('%s is not set. Export it; it is never passed as a flag.' % var)
    return k


class Budget:
    """Character budget, enforced before the send."""

    def __init__(self, cap):
        self.cap = cap
        self.used = 0
        self.calls = 0

    def spend(self, text):
        n = len(text)
        if self.used + n > self.cap:
            raise BudgetExceeded(
                'character cap %d would be exceeded (used %d, next %d). '
                'Stopping rather than truncating.' % (self.cap, self.used, n))
        self.used += n
        self.calls += 1
        return n


class BudgetExceeded(Exception):
    pass


def post_json(url, data, headers, retries=3):
    """POST form/JSON with a bounded retry. The URL is assumed key-free."""
    body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) \
        else json.dumps(data).encode()
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            # 429/5xx are worth retrying; 4xx otherwise is not.
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                last = e
                continue
            detail = ''
            try:
                detail = e.read().decode()[:200]
            except Exception:                                   # noqa: BLE001
                pass
            raise SystemExit('HTTP %s from the oracle: %s' % (e.code, detail))
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                last = e
                continue
            raise SystemExit('network error: %s' % e)
    raise SystemExit('exhausted retries: %s' % last)


def read_samples(path):
    with open(path, newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def write_refs(path, oracle, klip_code, rows, forward, reverse, budget):
    """Shared refs writer — the SAME CSV CONTRACT as argos_ref.py.

    tier and zipf are CARRIED THROUGH, never recomputed: the stratification
    is the Dart side's ruled decision. Dropping them once produced a bench
    whose HEADLINE row read n=0 while every other number looked right.
    """
    out = open(path, 'w', newline='', encoding='utf-8')
    w = csv.writer(out)
    w.writerow(['language', 'headword', 'extract_sha256', 'l_to_en',
                'en_to_l', 'tier', 'zipf', 'oracle'])
    done = 0
    try:
        for i, r in enumerate(rows, 1):
            hw = r['headword']
            f = b = ''
            try:
                budget.spend(hw)
                f = forward(hw) or ''
            except BudgetExceeded:
                raise
            except SystemExit:
                raise
            except Exception as e:                              # noqa: BLE001
                print('  forward failed on %r: %s' % (hw, e), file=sys.stderr)
            if f and reverse is not None:
                try:
                    budget.spend(f)
                    b = reverse(f) or ''
                except BudgetExceeded:
                    raise
                except Exception as e:                          # noqa: BLE001
                    print('  reverse failed on %r: %s' % (f, e), file=sys.stderr)
            w.writerow([klip_code, hw, r.get('extract_sha256', ''), f, b,
                        r.get('tier', ''), r.get('zipf', ''), oracle])
            done = i
            if i % 25 == 0:
                print('  %s %s %d/%d  chars=%d' % (oracle, klip_code, i,
                                                   len(rows), budget.used),
                      flush=True)
    except BudgetExceeded as e:
        print('BUDGET STOP after %d of %d rows: %s' % (done, len(rows), e),
              file=sys.stderr)
    finally:
        out.close()
    print('refs      %s %s  n=%d/%d  chars=%d  calls=%d  -> %s'
          % (oracle, klip_code, done, len(rows), budget.used, budget.calls, path))
    return done
