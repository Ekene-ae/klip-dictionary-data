# klip-dictionary-data

Machine-readable dictionary data for the 19 languages Klip supports, derived
from **English Wiktionary** via **[kaikki.org](https://kaikki.org/)** and
stripped to a compact per-entry shape.

One gzipped JSONL file per language, published as **release assets** (not as
files in the git tree).

---

## v4 changelog — 2026-11-04

**v4 rebuilds ALL NINETEEN languages.** v3 rebuilt three and carried sixteen;
this release carries nothing — the entry classifier changed in a way that can
move rows in any language, and it moved rows in every one of them.

### One sub-sense was demoting the whole word

An entry's class was decided by a **union over every sense's tags**:

```
Wasser  [0] "water (H₂O)"                              neuter, strong
        [1] "water, waters (body of water)"            neuter
        [3] "urine"                                    euphemistic
        [4] "clipping of Mineralwasser/Tafelwasser"    abbreviation, clipping
```

The union carried `clipping`, so **`Wasser` shipped as an `abbr`** — an
abbreviation of `Mineralwasser`. So did `Apfel` (of `Pferdeapfel`),
`Schlüssel`, and Japanese 水, 月 and 車.

Class is now read from the entry's **own tags, else its FIRST GLOSSED
SENSE**. Wiktionary orders senses by primacy, so sense 0 is the entry's
identity.

**This is the same defect as v2's gender bug, one column over.** That one
unioned `forms[]` and `senses[]` tags and stored the *counterpart's* gender;
this unioned `senses[]` tags and stored the *sub-sense's* class.

It is also the second time this rule has been wrong. v2 removed `short-form`
from the abbreviation family after it falsely marked 13,940 Russian adverbs.
That was the instance fix; this is the class fix — and removing tags one at a
time could never have reached `Wasser`, whose tag is legitimately `clipping`.

### It was never only the abbreviation rule

`misspelling` and the form check read the **same union**, and `alt-of`
accompanies `abbreviation` on the same sense almost always. Repairing only
the abbreviation rule moved these entries to `form` instead of to `lemma`
(Japanese: 816 of 825; English: 2,800 of 2,810) — `Wasser` would have become
a *form of* `Mineralwasser`. All three rules now take the per-sense rule.

### Apocopic forms are FORMS

**100% of apocopic senses also carry an abbreviation-family tag on the same
sense** (it 897/897, es 65/65, pt 62/62, fr 21/21, de 10/10), so the
per-sense rule alone would have left every one of them `abbr`. An apocopic
form is a shortened form of its lemma, so it is resolved to `form` ahead of
the abbreviation check: `color` → `form`, target `colore`.

Its target is not in `form_of` — **2 of Italian's 897** carry one — so it is
parsed from the first gloss by **one anchored pattern**, `^apocopic (form )?of
X`, and left **NULL on a miss**. Not widened to a general "… of Y" matcher:
`con` is glossed "alternative form of com, apocopic form of come" and
`adequar` "apocopic form of (archaic) adequare", so a loose pattern would
store a confident wrong lemma. 1,041 of 1,055 apocopic glosses parse.

### Per-language class deltas

Against the published baselines — v3 for zh/ja/ko, v2 for the other sixteen.

| code | lemma Δ | abbr Δ | form Δ | phrase Δ | dropped Δ | total Δ |
|---|---:|---:|---:|---:|---:|---:|
| `ar` | +118 | −42 | −79 | +3 | +0 | 0 |
| `da` | +36 | −8 | −28 | +0 | +0 | 0 |
| `de` | +299 | −188 | −115 | +4 | +0 | 0 |
| `el` | +224 | −18 | −208 | +2 | +0 | 0 |
| `en` | +2,402 | −1,147 | −1,560 | +305 | +0 | 0 |
| `es` | +335 | −125 | −224 | +14 | +0 | 0 |
| `fr` | +132 | −90 | −52 | +10 | +0 | 0 |
| `hi` | +17 | −3 | −14 | +0 | +0 | 0 |
| `it` | +224 | −910 | +679 | +7 | +0 | 0 |
| `ja` | +670 | −602 | −68 | +0 | +0 | 0 |
| `ko` | +87 | −65 | −22 | +0 | +0 | 0 |
| `nl` | +143 | −35 | −109 | +1 | +0 | 0 |
| `no` | +42 | −18 | −26 | +2 | +0 | 0 |
| `pl` | +158 | −33 | −128 | +3 | +0 | 0 |
| `pt` | +292 | −188 | −107 | +3 | +0 | 0 |
| `ru` | +2,058 | −38 | −2,020 | +0 | +0 | 0 |
| `sv` | +146 | −66 | −85 | +5 | +0 | 0 |
| `tr` | +85 | −55 | −33 | +3 | +0 | 0 |
| `zh` | +487 | −220 | −270 | +3 | +0 | 0 |
| | **+7,955** | **−3,851** | **−4,469** | **+365** | **+0** | **0** |

**TWO INVARIANTS HOLD IN EVERY LANGUAGE, AND THEY ARE THE REAL CHECK:**
`dropped` is **+0 everywhere**, and each language's **total Δ is exactly 0**.
The change only redistributes entries among `lemma`, `abbr`, `form` and
`phrase` — nothing enters or leaves the dataset, and entry counts per
language are identical to v3/v2. A classifier fix that moved the dropped
count would be doing something it was not asked to.

`it` is the apocopic rescue read straight off the table: `abbr` −910 against
`form` +679. **`ru` and `el` are almost entirely the FORM half** of the fix
(−2,020 and −208 form) — languages where the original defect report saw
nothing, which is the clearest evidence that fixing only the abbreviation
rule would have left most of this in place.

### A note on the residual metric, because it is not zero

The defect was found by asking: how many `abbr`-class entries have a first
gloss that does not announce an abbreviation, and a headword that is not
all-caps or symbolic? After the fix that instrument still reports
**en 1,120, pt 134, fr 85, de 58, sv 45, es 40, it 39, ja 25 … hi 0**.

**That is an upper bound, not a defect count.** The instrument reads gloss
WORDING; the authority is the tag. Bucketing English's residual:

```
1,114 of 1,635   "ellipsis of ..."     <- essentially ALL of en's 1,120
  475            no shortening wording at all
   34            "alternative ..."
```

`ellipsis of` is a shortening statement the instrument simply does not list —
`döner` ← `döner kebap`, `ton` ← `ton balığı`. Those are correctly `abbr`. So
are abbreviations glossed by meaning rather than relation: `i.e.` "That is,
namely", `who's` "Who is", `path` "Pathology", and Danish `døgner` "a kiosk
(open twenty-four seven)", a clipping of `døgnkiosk` with nothing in the
gloss saying so.

The raw figures are published here **with** that explanation rather than
quietly adding `ellipsis` to the instrument and reporting a prettier number.

What settles it is the named entries, classified from real extract lines:

```
Apfel lemma · Schlüssel lemma · Wasser lemma · 水 lemma · 車 lemma
color form (target colore) · colore lemma · mm abbr
月 BOTH — abbr for "short for 月曜日", lemma for "the Moon" (two etymologies)
```

### Provenance

All nineteen extract `sha256` were **re-verified against the v3/v2 manifest
before building** and all nineteen matched, so every input is pinned across
v2, v3 and v4 and the deltas are attributable to the classifier alone.

**`pack.sha256` is NOT recorded in v4, and that is a regression from v2/v3.**
Each intermediate `.sqlite` was deleted immediately after export and was not
hashed first. v3's hashes are *not* carried forward — a different builder
produces a different pack, and copying them would be a false record. The
chain is still verifiable end to end: `extract.sha256` pins the input, the
builder commit pins the code, and `asset.sha256` pins the published artifact,
which is what a rebuild must reproduce.

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
| `ar` | Arabic | 229,902 | 20,051 | 1,332 | 208,482 | 37 | 15,986,648 |
| `da` | Danish | 55,906 | 22,332 | 1,232 | 32,158 | 184 | 1,550,482 |
| `de` | German | 356,465 | 80,046 | 3,604 | 271,386 | 1,429 | 15,464,140 |
| `el` | Greek | 81,303 | 25,692 | 1,244 | 54,051 | 316 | 3,997,999 |
| `en` | English | 1,247,916 | 494,016 | 142,090 | 590,509 | 21,301 | 40,548,330 |
| `es` | Spanish | 801,725 | 92,268 | 15,488 | 693,260 | 709 | 15,791,252 |
| `fr` | French | 391,326 | 71,201 | 16,058 | 303,089 | 978 | 7,796,897 |
| `hi` | Hindi | 35,877 | 19,533 | 1,797 | 14,527 | 20 | 2,938,786 |
| `it` | Italian | 601,352 | 132,044 | 9,032 | 459,856 | 420 | 11,339,017 |
| `ja` | Japanese | 90,417 | 84,706 | 908 | 3,420 | 1,383 | 7,943,213 |
| `ko` | Korean | 52,558 | 38,147 | 898 | 13,195 | 318 | 3,809,015 |
| `nl` | Dutch | 131,705 | 53,863 | 3,127 | 73,994 | 721 | 4,143,201 |
| `no` | Norwegian Bokmål | 79,433 | 21,686 | 528 | 57,116 | 103 | 1,760,258 |
| `pl` | Polish | 165,934 | 65,503 | 7,859 | 92,189 | 383 | 12,336,543 |
| `pt` | Portuguese | 433,003 | 61,560 | 7,339 | 363,200 | 904 | 8,463,663 |
| `ru` | Russian | 436,278 | 49,755 | 3,511 | 382,597 | 415 | 18,036,283 |
| `sv` | Swedish | 307,847 | 52,942 | 3,314 | 251,109 | 482 | 5,630,903 |
| `tr` | Turkish | 40,251 | 18,490 | 4,075 | 17,534 | 152 | 15,487,586 |
| `zh` | Chinese (Han-keyed) | 173,530 | 160,141 | 10,615 | 1,581 | 1,193 | 7,675,874 |
| | **19 languages** | **5,712,728** | **1,563,976** | **234,051** | **3,883,253** | **31,448** | **200,700,090** |

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
