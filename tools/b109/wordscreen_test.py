#!/usr/bin/env python3
"""Tests for wordscreen's per-language elision rule. Run: python3 -I wordscreen_test.py

This repository has no test runner and these scripts run standalone, so this
is a self-checking script in the same style: it asserts, it prints what it
checked, and it exits non-zero on failure.

**THE FIRST TEST IS THE ONE THAT MATTERS MOST.** B-110's published Danish
figures were produced before this rule existed. If `lang=None` ever stops
meaning "change nothing", those figures silently become unreproducible.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wordscreen import split_elisions, screen, dict_fold, ELIDABLE

ok = 0
def check(label, got, want):
    global ok
    assert got == want, '%s\n   got:  %r\n   want: %r' % (label, got, want)
    ok += 1
    print('  ok  %s' % label)

print('1. THE DEFAULT CHANGES NOTHING — the Danish regression guard')
for t in ["Han sagde 'goddag' til mig.", "nell'omelia", "l'homme", "don't", "aujourd'hui"]:
    check('lang=None leaves %r byte-identical' % t, split_elisions(t, None), t)
check('a language with no rule leaves text alone', split_elisions("l'homme", 'da'), "l'homme")
check('danish is not in ELIDABLE at all', 'da' in ELIDABLE, False)
check('english is NOT in ELIDABLE — contractions are word-internal',
      'en' in ELIDABLE, False)

print('\n2. ITALIAN — the elision that produced the artefact')
check("nell'omelia splits", split_elisions("nell'omelia", 'it'), 'nell omelia')
check("dell'ISIS splits", split_elisions("dell'ISIS", 'it'), 'dell ISIS')
check("un'edera splits", split_elisions("un'edera", 'it'), 'un edera')
check("l'Angelus splits regardless of case", split_elisions("L'Angelus", 'it'), 'L Angelus')
check("quest'asta splits", split_elisions("quest'asta", 'it'), 'quest asta')
check('a typographic apostrophe splits too',
      split_elisions('nell’omelia', 'it'), 'nell omelia')
check('a word with no elision is untouched',
      split_elisions('omelia cantata', 'it'), 'omelia cantata')

print('\n3. FRENCH — and the word that looks like an elision and is not')
check("l'homme splits", split_elisions("l'homme", 'fr'), 'l homme')
check("qu'il splits", split_elisions("qu'il", 'fr'), 'qu il')
check("jusqu'a splits on the longest stem, not on l or d",
      split_elisions("jusqu'a", 'fr'), 'jusqu a')
check("AUJOURD'HUI SURVIVES WHOLE", split_elisions("aujourd'hui", 'fr'), "aujourd'hui")
check("aujourd'hui survives in a sentence that also elides",
      split_elisions("aujourd'hui l'homme", 'fr'), "aujourd'hui l homme")
check("Aujourd'hui survives whatever its case",
      split_elisions("Aujourd'hui", 'fr'), "Aujourd'hui")

print('\n4. CATALAN AND PORTUGUESE')
check("ca l'home splits", split_elisions("l'home", 'ca'), 'l home')
check("ca s'ha splits", split_elisions("s'ha", 'ca'), 's ha')
check("pt d'agua splits", split_elisions("pingo d'agua", 'pt'), 'pingo d agua')
check("pt leaves an English contraction alone (no en rule applies)",
      split_elisions("don't", 'pt'), "don't")

print('\n5. THE BARE ARTICLE IS A FUNCTION WORD, NOT A CANDIDATE')
folds = {dict_fold('omelia'), dict_fold('cantata')}
r = screen("nell'omelia cantata", folds, lang='it')
check('the noun now resolves', r['nonword'], [])
check('the bare article is classed as an elision', [w.lower() for w in r['elision']], ['nell'])
check('and it is not a nonword', r['nonword'], [])
check('token count sees two words, not one', r['tokens'], 3)

print('\n6. WITHOUT THE RULE, THE SAME LINE PRODUCES THE ARTEFACT')
r2 = screen("nell'omelia cantata", folds)          # lang=None, the old behaviour
check("nell'omelia is one unresolvable token", r2['nonword'], ["nell'omelia"])
check('which is exactly the probable-mishearing the fix removes',
      len(r2['nonword']), 1)

print('\n%d checks passed' % ok)
