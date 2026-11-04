# klip-dictionary-data

Machine-readable dictionary data for the 19 languages Klip supports, derived
from **English Wiktionary** via **[kaikki.org](https://kaikki.org/)** and
stripped to a compact per-entry shape.

One gzipped JSONL file per language, published as **release assets** (not as
files in the git tree).

---

## v3 changelog — 2026-11-04

**v3 rebuilds THREE languages — `zh`, `ja`, `ko` — and nothing else.** The
other sixteen assets are the v2 artifacts unchanged and are **not re-attached
to this release**; fetch them from v2, where their recorded `asset.sha256`
still identifies them. `packs.sha256` v3 carries all nineteen blocks so the
dataset has one provenance record, and marks each carried block
`unchanged from v2`.

### Han single-character words were being dropped as non-words

English Wiktionary files Chinese single characters under **`pos=character`**.
Klip's entry classifier dropped that part-of-speech wholesale, so 水 (water),
人 (person), 犬 (dog) and 大 (big) were absent from `zh` while compounds
containing them were present. The same rule was silently removing **kanji**
from `ja` and **hanja** from `ko`.

A `pos=character` entry is now a **`lemma`** when its headword is **entirely
Han script** and it carries **at least one gloss**. Everything else stays
dropped.

```
rescued (entries moved dropped -> lemma, read from the published files)

              rescued   Han glyph-only   non-Han glossed   non-Han glyph
  zh           21,153            8,156               384             392
  ja            5,585            8,986               266             170
  ko            4,044            6,118               133               5
  da (control)       0                0                17               0
```

`lemma` counts: **`zh` 138,501 → 159,654 · `ja` 78,451 → 84,036 ·
`ko` 34,016 → 38,060.** Nothing else moved — `phrase`, `form` and `abbr` are
identical to v2 in all three languages, and the whole delta is
`dropped → lemma`. The three extracts' `sha256` were **re-verified against
v2's manifest before the build**, so the deltas are attributable to the
classifier and to nothing in the source.

### The gate is SCRIPT, not language

The rule asks what script the headword is written in, never what language the
pack is. A language gate would have been easier and wrong in both directions:
it would have admitted the **384 non-Han glossed** `zh` rows (Latin, Greek and
Cyrillic letters filed under `pos=character`), and it would have needed
re-opening for every further Han-script language.

Danish is the control. `da` has **17** `pos=character` entries — letter
entries like `A` — and **all 17 stay dropped**, which is the result a
language gate could not have produced while also admitting 水.

Han is tested across **CJK Unified Ideographs** (`U+4E00`–`U+9FFF`),
**Extension A** (`U+3400`–`U+4DBF`), **Extension B** (`U+20000`–`U+2A6DF`) and
**Compatibility Ideographs** (`U+F900`–`U+FAFF`). Braille (`U+2800`–`U+28FF`)
headwords stay dropped, as in v2.

**`pos` is kept as `character`.** The pack records what an entry *is* and
stays language-agnostic; a learner-facing label ("single-character word" for
`zh`, "kanji" for `ja`, "hanja" for `ko`) is the consumer's business. Rewriting
the `pos` to `noun` would bake one reading into the data and lose the fact
that the entry is a character.

### Two things a consumer should know

- **16 of the 30,782 rescued entries have multi-character headwords** — 8 in
  `zh` (望乞, 搭配詞, 螴蜳 …) and 8 in `ko` (陽光, 弱點, 無間地獄 …). They are
  genuine words that English Wiktionary happens to file under
  `pos=character`, and the rule admits them because it tests *entirely Han*,
  not *exactly one character*. They are correct as lemmas, but a surface that
  labels every `pos=character` row "single-character word" will misdescribe
  these 16. **Label by measuring the headword's length, not by trusting the
  `pos`.**
- **Surface policy, recorded here because it is not in the data.** Klip will
  include `zh` character-lemmas in its vocabulary-discovery pool (they are
  words) and **exclude** `ja`/`ko` character-lemmas from it, while keeping all
  three searchable and browsable — kanji and hanja meanings are reference
  material rather than vocabulary cards. **Nothing in this dataset encodes
  that**; it is a consumer-side decision, deferred in Klip to the branch that
  ships the pack, and it is stated here only so the distinction is not
  mistaken for a property of the data.

### A correction to the figures this change was first reported with

The rescue was first measured at **`zh` 16,031 · `ja` 5,560 · `ko` 3,731**.
Those numbers are **distinct headwords**, not entries, because the measuring
script accumulated headwords into a set. kaikki carries several entries per
headword (one per etymology), and the classifier classifies entries — so the
entry counts are the **21,153 · 5,585 · 4,044** above, confirmed three ways:
the builder's own class line, a re-scan of the extract applying the
classifier's exact predicate, and a tally of the published assets. The
headword figures are not wrong as headword figures; they were reported under
the wrong unit. Recorded rather than quietly replaced, per this repo's
founding rule.

### Carried forward unchanged

The `zh` build continues to report that **no template-artifact form rows were
skipped**, which is unexpected for a kaikki extract. This is **not new in
v3**: `zh`'s form-side numbers are identical to v2's (`form` 1,851, 1,787
form-class entries without a pointer row), so the condition predates this
release and the Han rescue did not touch it. It is noted, not fixed.

---

## v2 changelog — 2026-11-04

**v2 replaces v1 wholesale. Two of v1's stated caveats were WRONG, and both
are corrected here rather than left standing.**

### Corrections to v1's own claims

- **`no` was never "effectively empty".** v1 reported *"Norwegian is
  effectively empty — 1,454 entries"* and said both Bokmål and Nynorsk "404 as
  kaikki extract names". **The fetch was wrong, not the data.** kaikki
  URL-encodes the space in the *directory* and *removes* it from the
  *filename* — `Norwegian%20Bokm%C3%A5l/kaikki.org-dictionary-NorwegianBokmål.jsonl.gz`
  resolves. `no` now carries **79,433 entries** and is Bokmål.
- **`zh` is no longer pinyin-keyed.** v1 shipped kaikki's *Mandarin* extract,
  which keys on pinyin: 75,537 of 75,844 headwords were Latin-script and 307
  were Han, so looking up 水 matched nothing. v2 ships the *Chinese* extract
  (96.2% Han-headed) — **138,501 lemmas**.

### New in v2

- **Entry classes (`c`).** Every entry is classified `lemma`, `phrase`, `form`
  or `abbr`. Dropped entries are not exported at all.
- **Form targets (`t`).** A `form`-class entry names the headword it inflects
  from, so a consumer can resolve an inflection to its lemma.
- **Proper nouns are dropped, by category and not by hand.** `pos=name`
  entries drop unless a kaikki *category* rescues them, and a `Countries`
  category vetoes the rescue — `Rwanda`, `Kiribati` and `Myanmar` had been
  pulled back in by a `Languages` category. No hand-maintained exception list
  exists anywhere in the generator.
- **Arabic's unglossed forms are parsed.** 196,443 unglossed Arabic verb forms
  were being discarded before anything looked for their target, because the
  code checked `glossed.isEmpty` first. `ar` form entries went
  **12,198 → 208,561**; `ar` dropped went **199,878 → 3,515**.
- **Gender was reading the wrong word's tag.** The gender set was the union of
  every `forms[]` tag and every `senses[]` tag — and `forms[]` holds the
  *counterpart*, so `Arzt` carrying `('Ärztin', ['feminine'])` stored
  `feminine`. A sort then picked alphabetically, and `feminine < masculine <
  neuter`, so feminine won **deterministically**. Gender now reads entry tags
  then sense tags, in source order, and **never forms**:

  ```
  wrong values   de 5,407 -> 21   es 6,089 -> 34   fr 3,584 -> 21
                 pt 2,981 -> 25   it 4,246 -> 1,626
  ```

  Italian's remainder is **not residual error**: they are `-ista` nouns,
  genuinely feminine, whose own feminine plural is legitimately tagged
  feminine. All 1,626 were checked against the source's own tags.

  **Danish lost 2,806 values to the same fix** — 2,364 of them adjectives
  assigned `neuter` from their own neuter *agreement* form (`gratis`,
  `digital`, `sky`). Danish adjectives have no gender; they agree.

- **25% of verb form rows were template noise.** A `-` placeholder asserts a
  cell has *no* form and is now rejected. A leading auxiliary is stripped from
  the form and **kept as a tag** (`aux:har`, `aux:er`, `aux:var`, `aux:at`) —
  moved, never discarded, because Danish er-verbs versus har-verbs is a real
  distinction. Forms then dedupe per entry with tag sets merged.

  ```
  Danish verb form rows   38,097 -> 20,368
  "-" placeholders         4,115 -> 0
  participle resolvable     82.4% -> 100.0%
  ```

  The stored perfect of `acceptere` had been `"har accepteret"`, so a learner
  typing `accepteret` — the participle they actually meet — matched nothing.
  Only the *leading* group is touched: `dukke op` keeps its particle.

- **Braille is dropped.** Headwords whose every rune is in U+2800–U+28FF are a
  transcription system, not vocabulary. Found via 114 Korean headwords that
  diverged from an independent Python mirror of the classifier.

### Still true from v1, and still worth knowing

- **`f` measures TRANSLITERATION, not morphology, for several languages** —
  Korean, Arabic, Hindi, Russian and Greek included. A high form count is not
  evidence of rich inflection tables.
- **`ar` glosses are sparse** — the lowest gloss rate here by a wide margin.
- **No frequency field exists anywhere in this data.** Any ranking must come
  from an outside list.
- **`g` is `null` for Japanese, Korean and Chinese, and that is correct** —
  those languages have no grammatical gender.
- **Audio filenames are not included**, because per-file Commons licences vary
  and shipping them would carry an unstated obligation.
- **Glosses are ENGLISH.** These are per-language extracts of *English*
  Wiktionary.

---

## Per-language counts — read from the published files

Counted by decompressing each published asset and tallying `c`, not copied
from a build log.

| code | language | entries | lemma | phrase | form | abbr | asset bytes |
|---|---|---:|---:|---:|---:|---:|---:|
| `ar` | Arabic | 229,902 | 19,933 | 1,329 | 208,561 | 79 | 15,987,204 |
| `da` | Danish | 55,906 | 22,296 | 1,232 | 32,186 | 192 | 1,550,579 |
| `de` | German | 356,465 | 79,747 | 3,600 | 271,501 | 1,617 | 15,465,744 |
| `el` | Greek | 81,303 | 25,468 | 1,242 | 54,259 | 334 | 3,998,224 |
| `en` | English | 1,247,916 | 491,614 | 141,785 | 592,069 | 22,448 | 40,552,607 |
| `es` | Spanish | 801,725 | 91,933 | 15,474 | 693,484 | 834 | 15,792,654 |
| `fr` | French | 391,326 | 71,069 | 16,048 | 303,141 | 1,068 | 7,797,453 |
| `hi` | Hindi | 35,877 | 19,516 | 1,797 | 14,541 | 23 | 2,938,848 |
| `it` | Italian | 601,352 | 131,820 | 9,025 | 459,177 | 1,330 | 11,338,464 |
| `ja` | Japanese | 90,417 | 84,036 | 908 | 3,488 | 1,985 | 7,945,161 |
| `ko` | Korean | 52,558 | 38,060 | 898 | 13,217 | 383 | 3,809,319 |
| `nl` | Dutch | 131,705 | 53,720 | 3,126 | 74,103 | 756 | 4,143,472 |
| `no` | Norwegian Bokmål | 79,433 | 21,644 | 526 | 57,142 | 121 | 1,760,393 |
| `pl` | Polish | 165,934 | 65,345 | 7,856 | 92,317 | 416 | 12,337,234 |
| `pt` | Portuguese | 433,003 | 61,268 | 7,336 | 363,307 | 1,092 | 8,464,584 |
| `ru` | Russian | 436,278 | 47,697 | 3,511 | 384,617 | 453 | 18,045,714 |
| `sv` | Swedish | 307,847 | 52,796 | 3,309 | 251,194 | 548 | 5,631,411 |
| `tr` | Turkish | 40,251 | 18,405 | 4,072 | 17,567 | 207 | 15,487,674 |
| `zh` | Chinese (Han-keyed) | 173,530 | 159,654 | 10,612 | 1,851 | 1,413 | 7,676,956 |
| | **19 languages** | **5,712,728** | **1,556,021** | **233,686** | **3,887,722** | **35,299** | **200,723,695** |

**English is the largest by a wide margin** — a 534 MB compressed extract that
decompresses to 3.2 GiB and yields **1,247,916 entries**, more than a quarter
of everything here. It was built last and alone so the other 18 could ship
first.

Note English's shape differs from the rest: its `phrase` count (141,785) is
larger than any other language's and its `form` count is proportionally much
smaller, because English Wiktionary's English entries carry idioms and
multi-word expressions densely and inflection tables sparsely. A high entry
count here is not a high inflection count.

---

## Record format

One JSON object per line. No wrapping array, so a consumer can stream it.

```json
{"w":"hund","p":"noun","g":"common-gender","i":"[hunˀ]",
 "s":["dog","hound"],
 "f":[["hunden","definite,singular"],["hunde","indefinite,plural"]],
 "c":"lemma","t":null}
```

| key | meaning |
|---|---|
| `w` | headword, verbatim |
| `p` | part of speech as the source states it (`noun`, `verb`, `adj`, …), or `null` |
| `g` | grammatical gender, or `null` — read from entry and sense tags only, never from forms |
| `i` | IPA, verbatim, or `null` |
| `s` | **every** gloss, in the source's own sense order |
| `f` | inflected forms as `[form, comma-joined tags]` pairs, `aux:*` tags included |
| `c` | entry class — `lemma`, `phrase`, `form` or `abbr` |
| `t` | for `c == "form"`, the headword this form inflects from; otherwise `null` |

**One line per (headword, part-of-speech) pair**, which is the source's own
grain — so a headword that is both a noun and a verb appears twice.

### One limitation of `t`, stated rather than hidden

A form's target is keyed only by the form's text, and **two lemmas can inflect
to the same string** — Danish `afholdte` points at both `afholde` and
`afholdt`; `ager` at both `age` and `agere`. `t` is single-valued, so the
**first pointer row in the pack's own row order wins** and the alternates are
not expressed. The number of conflicting rows is reported by the exporter on
every run and varies sharply by language: 0 for `zh`, 440 for `da`, **44,476
for `ar`**.

A smaller count of `form`-class entries carry **no** pointer row at all and
get `t: null`; that is also reported per run.

---

## Generation method

```
kaikki extract (.jsonl.gz)
   └─ gunzip
       └─ Klip tool/dict_pack/build_pack.dart   ->  klip-dict-<code>.sqlite
           └─ export_pack.py (in this repo)     ->  klip_dictionary_<code>.jsonl.gz
```

**Builder:** Klip commit `09a912748412d2b09681390a7103b21150974a8a` (the
merge of Klip PR #256 into `develop`). Every classification, gender read and
form normalisation above happens there — this repository does not reimplement
any of it.

**Exporter:** [`export_pack.py`](export_pack.py), committed here. Standard
library only, run as `python3 -I`, opens the pack **read-only**, and is a
column-to-key dump: no filtering, no reshaping, no recomputation. Entries are
emitted in the pack's own row order. It self-checks on every file — the object
count must equal the pack's `meta.entry_count`, and the per-class counts must
equal the Dart builder's own `classes` line — and **exits non-zero** if either
disagrees. All 19 files passed.

**Inputs are pinned.** [`packs.sha256`](packs.sha256) carries, per language:
the asset's sha256 and byte size, the intermediate pack's sha256 and byte size,
the class counts, and **the kaikki extract's sha256 with its upstream
`Last-Modified`**.

> **Why the extract hash is new in v2.** kaikki.org serves a **rolling** dump
> with no versioned archive, and v1 recorded no extract hash — so v1's numbers
> cannot be reproduced. This is not hypothetical: the gender fix's removal
> count measured **2,806** against one snapshot and **2,828** against a
> fresher one, and that 22-value gap can no longer be closed because the older
> extract no longer exists anywhere. v2 pins every input so the same question
> is answerable next time.

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

## Provenance of this README

The discipline these notes follow is the Klip dictionary arc's founding rule:
**no number without its measurement method, no claim without a citation
carrying a URL and an access date.** Where v1 breached it — the `no` and `zh`
caveats — v2 says so in the changelog above rather than quietly correcting the
text.
