# klip-dictionary-data

Machine-readable dictionary data for the 19 languages Klip supports, derived
from **English Wiktionary** via **[kaikki.org](https://kaikki.org/)** and
stripped to a compact per-entry shape.

One gzipped JSONL file per language, published as **release assets** (not as
files in the git tree — they total ~180 MiB excluding English).

---

## Attribution

This data is derived from **Wiktionary**, extracted by **`wiktextract`**
(Tatu Ylönen) and published at **kaikki.org**.

> "This data is made available under the same licenses as Wiktionary — both
> CC-BY-SA and GFDL."
> — <https://kaikki.org/dictionary/index.html>, accessed 2026-10-30T15:07:45Z

## Licence — **CC BY-SA, SHARE-ALIKE**

**These files are a derived database of CC-BY-SA material, and they are
published under the same terms.** Share-alike is the reason this repository is
public rather than private: redistributing Wiktionary-derived data carries an
attribution and share-alike obligation, and meeting it in the open is simpler
and more honest than meeting it by reference.

If you use these files, you inherit the same obligation: credit Wiktionary and
kaikki.org, and keep derived data under CC-BY-SA.

> **This is the repository owner's reading of the licence, not legal advice.**
> Shipping Wiktionary-derived data under CC-BY-SA with attribution is
> established practice for dictionary applications. That is a practice
> observation, and this README is not clearance. The narrow open question is
> how far share-alike reaches over a re-formatted derived pack bundled in a
> paid application.

---

## Record format

One JSON object per line. No wrapping array, so a consumer can stream it.

```json
{"w":"hund","p":"noun","g":"common-gender","i":"[hunˀ]",
 "s":["dog","hound"],
 "f":[["hunden","definite,singular"],["hunde","indefinite,plural"]]}
```

| key | meaning |
|---|---|
| `w` | headword, verbatim |
| `p` | part of speech as the source states it (`noun`, `verb`, `adj`, …), or `null` |
| `g` | grammatical gender — one of `common-gender`, `neuter`, `masculine`, `feminine` — or `null` |
| `i` | IPA, verbatim, or `null` |
| `s` | **every** gloss, in the source's own sense order |
| `f` | inflected forms as `[form, comma-joined tags]` pairs |

**One line per (headword, part-of-speech) pair**, which is the source's own
grain — so a headword that is both a noun and a verb appears twice.

---

## Generation method

Every number and every file below is reproducible from the cited inputs.

### 1. Source extracts

Each language's per-language JSONL extract was downloaded from:

```
https://kaikki.org/dictionary/<Language>/kaikki.org-dictionary-<Language>.jsonl.gz
```

All extracts were **accessed 2026-10-30** (between 20:57Z and 21:45Z), and all
carried a server `Last-Modified` of **Sun, 25 Oct 2026** — i.e. one upstream
extract run.

### 2. Filter rules applied

Two transformations, both deliberate:

**Template artifacts are removed from `f`.** `forms[]` rows tagged
`table-tags` or `inflection-template` are `wiktextract` internals, not word
forms — their "forms" read `no-table-tags` and `da-noun-infl`. **83.7% of
form-bearing Danish entries carry them**, measured across all 58,686 entries.
Unfiltered, a consumer renders those to a reader as inflections.

**A form that merely echoes its own headword is dropped**, since it is not an
inflection.

Nothing else is altered: headwords, glosses, IPA and tags are verbatim.

### 3. Known caveats a consumer should not discover the hard way

- **`zh` (Mandarin) is keyed on PINYIN, not Han characters.** 75,537 of 75,844
  headwords are Latin-script; 307 are Han. Looking up 水 against this file
  matches nothing. Han-character entries live in kaikki's separate *Chinese*
  extract, which is **not** included here.
- **`f` measures TRANSLITERATION, not morphology, for several languages.**
  Mandarin's `forms[]` is 72,664 Bopomofo rows plus Wade-Giles and Pinyin. The
  same applies to Korean, Arabic, Hindi, Russian and Greek: a high form count
  is not evidence of rich inflection tables.
- **`no` (Norwegian) is effectively empty — 1,454 entries**, two orders of
  magnitude below Swedish and Danish. `Norwegian Bokmål` and `Norwegian
  Nynorsk` both 404 as kaikki extract names, so no variant file explains it.
- **`ar` (Arabic) glosses are sparse: 15.2%** of headwords carry an English
  gloss, the lowest of all languages here by a factor of four.
- **There is no frequency field anywhere in this data.** Any ranking a
  consumer wants must come from an outside list.
- **`g` is `null` for Japanese, Korean and Mandarin, and that is correct** —
  those languages have no grammatical gender. An absent field is not a gap
  when the category does not exist.
- **Audio filenames are not included.** The source carries Wikimedia Commons
  references whose per-file licences vary (47% public domain, 29% CC0, and
  24% requiring attribution, measured over the 180 Danish files). Audio is
  omitted here rather than shipped with an unstated obligation.
- **Glosses are ENGLISH.** These are per-language extracts of *English*
  Wiktionary, and they carry no non-English translation tables — measured at
  0 across all 18 non-English languages (one stray row in Swedish).

---

## Files

See the [latest release](../../releases/latest). Per-language line counts and
sizes are listed there.

---

## Provenance of this README

Produced alongside Klip's own dictionary pack generator, whose filter rules are
the ones described above. The discipline these notes follow is the Klip
dictionary arc's founding rule: **no number without its measurement method, no
claim without a citation carrying a URL and an access date.**
