#!/usr/bin/env python3
"""The non-word screen — B-107 ruling 2, and B-110's instrument. OUTSIDE THE REPO.

A token RESOLVES when its dictFold key is an entry fold or a form fold in the
pack. Unresolved tokens are then split three ways, because the raw rate is not
the interesting number:

  NAME      capitalised mid-sentence — B-106 measured 161 of 376 gaps this way
  LOANWORD  an English word the pack is not expected to carry
  NON-WORD  everything left. THIS is the candidate recognition error.

dictFold is REPLICATED from lib/utils/dict_fold.dart and the replication is
ASSERTED against every stored fold before any rate is reported — a fold that
drifts would make every token look unresolvable and the rate would be a
measurement of my own bug. (B-106 did the same and got 0 mismatches.)
"""
import json, re, sqlite3, sys, unicodedata

NON_DECOMPOSING = {
    'ø': 'o', 'æ': 'a', 'å': 'a', 'ð': 'd', 'þ': 'th',
    'ł': 'l', 'đ': 'd', 'ı': 'i', 'ß': 'ss',
}
MARKS = {
    'á':'a','à':'a','â':'a','ä':'a','ã':'a','ā':'a','ă':'a',
    'é':'e','è':'e','ê':'e','ë':'e','ē':'e','ė':'e','ę':'e',
    'í':'i','ì':'i','î':'i','ï':'i','ī':'i','į':'i',
    'ó':'o','ò':'o','ô':'o','ö':'o','õ':'o','ō':'o',
    'ú':'u','ù':'u','û':'u','ü':'u','ū':'u','ů':'u',
    'ý':'y','ÿ':'y','ñ':'n','ń':'n','ň':'n','ç':'c','ć':'c','č':'c',
    'ś':'s','š':'s','ş':'s','ź':'z','ž':'z','ż':'z','ť':'t','ţ':'t',
    'ř':'r','ĺ':'l','ľ':'l','ğ':'g','ĝ':'g',
    'ĉ':'c','ĵ':'j','ŝ':'s','ŭ':'u',
}
def _arabic_mark(r):
    return (0x064B <= r <= 0x065F) or r == 0x0670 or r == 0x0640 or (0x06D6 <= r <= 0x06ED)

def dict_fold(s):
    if not s: return ''
    out = []
    for ch in s.lower():
        if _arabic_mark(ord(ch)): continue
        out.append(NON_DECOMPOSING.get(ch, ch))
    return ''.join(MARKS.get(c, c) for c in ''.join(out))

def load(packpath):
    db = sqlite3.connect('file:%s?mode=ro' % packpath, uri=True)
    rows = db.execute('select headword, fold from entry').fetchall()
    bad = [(h, f) for h, f in rows if dict_fold(h) != f]
    folds = {f for _, f in rows}
    folds |= {f for (f,) in db.execute('select fold from form')}
    db.close()
    return folds, len(rows), bad

# ── ELISION IS PER-LANGUAGE, AND THE DEFAULT IS TO LEAVE TEXT ALONE ──────
#
# **FOUND 2026-11-19 RUNNING B-110 FOR ITALIAN, BY READING THE FLAGS.**
# `TOKEN` below joins words across an apostrophe. That is right for the Danish
# this screen was written for — Danish barely uses the apostrophe — and WRONG
# FOR THE ROMANCE LANGUAGES, where it marks an ELISION: `nell'omelia` is
# *nella* + *omelia*, two words. Glued, the pair cannot resolve in any pack
# and falls into "absent from all three corpora" — **a probable mishearing
# that is ordinary Italian**.
#
# What it cost before it was fixed, on the Italian shortlist: every rate was
# inflated (Penisolabella 12.89 -> 10.10 per 1,000, Update 3.30 -> 1.46) and
# the DICTIONARY-GAP band collapsed when it was corrected (Penisolabella
# 52 -> 1). The gap band is the tell: a glued elision the corpora happened to
# contain was being scored as "a real word the pack lacks".
#
# **THE DEFAULT IS `lang=None`, WHICH SPLITS NOTHING.** Danish's published
# B-110 figures were produced without this and must not move; a caller opts
# in by naming its language. **English MUST NOT opt in**: `don't`, `it's` and
# `we'll` are contractions, where the apostrophe really is word-internal, and
# splitting them would invent the exact artefact this fixes.
ELIDABLE = {
    # Italian: articles, prepositions and the apocopated forms that take an
    # apostrophe before a vowel.
    'it': {'l', 'un', 'dell', 'nell', 'all', 'sull', 'dall', 'coll', 'quell',
           'quest', 'quant', 'cert', 'altr', 'bell', 'sant', 'grand', 'buon',
           'mezz', 'tutt', 'nessun', 'ogn', 'anch', 'dov', 'com', 'cos',
           'c', 'd', 'n', 's', 'gl', 't', 'm', 'v', 'po'},
    # French: articles, pronouns, and the conjunctions that elide before a
    # vowel. `jusqu'`, `lorsqu'`, `puisqu'`, `quoiqu'` are one word each until
    # the apostrophe, exactly like `qu'`.
    'fr': {'l', 'd', 'j', 'n', 'm', 't', 's', 'c', 'qu', 'jusqu', 'lorsqu',
           'puisqu', 'quoiqu', 'presqu', 'quelqu', 'entr'},
    # Catalan: the article and the weak pronouns.
    'ca': {'l', 'd', 's', 'n', 'm', 't', 'ns', 'us', 'qu'},
    # Portuguese elides rarely and mostly in fixed phrases (`pingo d'agua`),
    # but the two that occur are real.
    'pt': {'d', 'n'},
}

# **ONE WORD PER LANGUAGE THAT LOOKS LIKE AN ELISION AND IS NOT.** French
# `aujourd'hui` is a single word; splitting it yields `aujourd` and `hui`,
# NEITHER of which resolves, so the fix would manufacture two candidates per
# occurrence of one of the commonest words in the language.
ELISION_EXCEPTIONS = {
    'fr': {"aujourd'hui"},
}

_APOS = "['\u2019]"
_elision_re = {}


def _elision_pattern(lang):
    if lang not in _elision_re:
        stems = ELIDABLE.get(lang)
        if not stems:
            _elision_re[lang] = None
        else:
            alt = '|'.join(sorted((re.escape(x) for x in stems), key=len, reverse=True))
            _elision_re[lang] = re.compile(r'\b(%s)%s' % (alt, _APOS), re.I)
    return _elision_re[lang]


def split_elisions(text, lang):
    """Split Romance elisions so each side is tokenised as its own word.

    `lang=None`, or a language with no rule, returns the text UNCHANGED.
    Exceptions are protected first, so `aujourd'hui` survives whole.
    """
    pat = _elision_pattern(lang)
    if pat is None:
        return text
    # **THE GUARD RESTORES WHAT IT MATCHED, NOT THE CANONICAL SPELLING.** An
    # earlier cut substituted the exception's own lowercase form back in, so
    # `Aujourd'hui` came out `aujourd'hui` — and CASE IS LOAD-BEARING here:
    # `screen` reads a leading capital mid-sentence as a NAME. Caught by
    # wordscreen_test.py, which is why that test exists.
    held = []
    for word in sorted(ELISION_EXCEPTIONS.get(lang, ())):
        rx = re.compile(re.escape(word).replace("'", _APOS), re.I)

        def _hold(m):
            held.append(m.group(0))
            return '\x00%d\x00' % (len(held) - 1)

        text = rx.sub(_hold, text)
    text = pat.sub(lambda m: m.group(1) + ' ', text)
    for i, original in enumerate(held):
        text = text.replace('\x00%d\x00' % i, original)
    return text


LOANWORDS = {
    'podcast','podcasts','episode','reality','summit','talk','quote','approach',
    'burger','instagram','online','mail','ok','okay','weekend','job','jobs',
    'test','fitness','stress','update','briefing','challenge','blog','app',
}
TOKEN = re.compile(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", re.UNICODE)

def screen(text, folds, first_token_is_sentence_start=True, lang=None):
    """`lang` opts into that language's elision rule. Default: no splitting,
    so every existing caller's figures are unchanged."""
    text = split_elisions(text, lang)
    res = {'tokens': 0, 'name': [], 'loan': [], 'nonword': [], 'elision': []}
    elidable = ELIDABLE.get(lang) or frozenset()
    toks = list(TOKEN.finditer(text))
    for i, m in enumerate(toks):
        w = m.group(0)
        res['tokens'] += 1
        if dict_fold(w) in folds:
            continue
        if w.lower() in elidable:
            # the bare article left behind by the split. A function word, and
            # not a candidate for anything — without this the fix would trade
            # one artefact for another.
            res['elision'].append(w)
            continue
        mid_sentence = i > 0 and not re.search(r'[.!?]\s*$', text[:m.start()].rstrip() or ' ')
        if w[:1].isupper() and mid_sentence:
            res['name'].append(w)
        elif w.lower() in LOANWORDS:
            res['loan'].append(w)
        else:
            res['nonword'].append(w)
    return res

if __name__ == '__main__':
    pack = sys.argv[1]
    folds, n, bad = load(pack)
    print('pack entries: %d · distinct folds (entry+form): %d' % (n, len(folds)))
    print('DICTFOLD REPLICATION: %d mismatches across %d stored folds%s'
          % (len(bad), n, '' if not bad else ' — ' + repr(bad[:3])))
    if bad:
        raise SystemExit('REFUSING TO REPORT A RATE: the fold replication drifted.')
    doc = json.load(open(sys.argv[2], encoding='utf-8'))
    tot = {'tokens': 0, 'name': 0, 'loan': 0, 'nonword': 0}
    flagged = []
    for l in doc['lines']:
        r = screen(l['da'], folds)
        for k in ('tokens',): tot[k] += r[k]
        for k in ('name', 'loan', 'nonword'): tot[k] += len(r[k])
        if r['nonword']:
            flagged.append((l['id'], l['slice'], r['nonword'], l['da']))
    print('\nTHE 50 LINES: %d tokens · %d names · %d loanwords · %d NON-WORDS (%.2f%%)'
          % (tot['tokens'], tot['name'], tot['loan'], tot['nonword'],
             100.0 * tot['nonword'] / tot['tokens']))
    print('lines carrying at least one non-word: %d of %d\n' % (len(flagged), len(doc['lines'])))
    for i, (lid, sl, nw, text) in enumerate(flagged, 1):
        print('%2d. %s [%s] %s' % (i, lid, sl, ', '.join(sorted(set(nw)))))
        print('      %s' % (text[:150] + ('…' if len(text) > 150 else '')))
