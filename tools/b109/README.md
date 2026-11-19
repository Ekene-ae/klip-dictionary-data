# tools/b109 — how the Danish pack's frequency layer was made

**THE APP REPOSITORY'S PACK BUILDER CANNOT REPRODUCE THE PUBLISHED DANISH
PACK, AND THAT IS WHY THESE FILES ARE HERE.** `klip`'s
`tool/dict_pack/build_pack.dart` builds entries, senses and forms from a
kaikki extract. It knows nothing about `entry.lemma_freq` or the
`known_form` table — those were added by the three scripts in this directory,
run once, on 2026-11-18. Without them the published pack is an artifact whose
recipe lives nowhere.

They are preserved as **HISTORY AND METHOD**, the same standing as
`tools/research/`: nothing here is imported by the app, by any build or by any
test, and nothing here is a build input. Each script's own header says it runs
OUTSIDE the repositories, and that is still true of what it does.

```
NO DATA SHIPS WITH THEM. The corpora are deleted after counting, by rule. The
frequency table they produce (8.5 MB) is not in this repository either. What
is here is the recipe, the digests to check it against, and the scripts.
```

## What the layer is

```
entry.lemma_freq   nullable INTEGER on an existing table. The lemma's own fold
                   plus every form the pack lists for it, counted over the
                   corpora below. 17,229 of 22,332 lemmas non-null (77.1%);
                   NULL where the corpora never contain the lemma, because 0
                   would be a claim and absence is not a count.
known_form         a new table, fold TEXT PRIMARY KEY + freq INTEGER. 83,670
                   corpus-frequent Danish surface folds the pack does NOT
                   already carry, at frequency >= 20.
meta               eight new rows: the recipe, the three archive digests, the
                   input pack's digest, and the credits.
pack_format        UNCHANGED at 2, deliberately. `dictionary_service.dart`
                   checks it by EXACT EQUALITY, so a bump is refused at open
                   by every installed build.
```

## The corpora, and their digests as fetched

Per-pair OPUS Moses downloads, Danish side only. 131,679,525 tokens, 855,655
distinct folds.

| corpus | version | Danish tokens | archive sha256 |
|---|---|---|---|
| DGT | v2021 | 86,283,061 | `6e654992791140f5fc60ac4a2eef7980cb539b2574f9e0b19b4778cf0e5fedfb` |
| Europarl | v8 | 45,177,140 | `83eddbf2c016c39a5b0b6d3468dd65417f7a65acfd0e31cbdb5217ae6361a2dd` |
| Tatoeba | v2026-07-08 | 219,324 | `a8662857fdc0bbb10d93726cb239db440e94f98469e954c07ca29ba477cc7514` |

```
https://object.pouta.csc.fi/OPUS-DGT/v2021/moses/da-en.txt.zip
https://object.pouta.csc.fi/OPUS-Europarl/v8/moses/da-en.txt.zip
https://object.pouta.csc.fi/OPUS-Tatoeba/v2026-07-08/moses/da-en.txt.zip
```

Each licence was read from the files **inside** its archive, never from a web
page. DGT's attribution obligation is quoted in the pack's own `meta.licence`.

## The recipe, exactly

Run from a working directory OUTSIDE both repositories, with these four
scripts copied into it — they resolve their inputs next to themselves.

```bash
D=~/b109-work && mkdir -p "$D" && cd "$D"
cp <this repo>/tools/b109/*.py .

# The corpus list the counting step reads. Written here rather than committed,
# because no data ships with these scripts.
cat > b110_corpora.json <<'JSON'
{"DGT":      {"url":"https://object.pouta.csc.fi/OPUS-DGT/v2021/moses/da-en.txt.zip"},
 "Europarl": {"url":"https://object.pouta.csc.fi/OPUS-Europarl/v8/moses/da-en.txt.zip"},
 "Tatoeba":  {"url":"https://object.pouta.csc.fi/OPUS-Tatoeba/v2026-07-08/moses/da-en.txt.zip"}}
JSON

# The input pack, at the path step 3 asserts.
mkdir -p ~/b107/downloads/pack-da
curl -fsSL -o ~/b107/downloads/pack-da/klip-dict-da.sqlite \
  https://github.com/Ekene-ae/klip-dictionary-data/releases/download/v6/klip-dict-da.sqlite
# ^ must digest aab33f71c0105df94598d51523e68d991b519cc8e575b7d3e979ae46577780bc
#   — that is the pack BEFORE the frequency layer. Step 3 asserts it and
#   refuses to run on anything else, which is what makes the recipe safe to
#   re-run.

# STEP 1 — count the three corpora into one table. Downloads, counts and
# DELETES each before the next, so peak disk stays under about 1 GB. Writes
# b109_freq.tsv: 507,073 folds at count >= 2, 8,529,464 bytes.
python3 -I b109_freq.py

# STEP 2 — the threshold trade, measured by BUILDING real SQLite tables with
# their indexes rather than estimating from row widths. Prints the curve that
# chose >= 20: +20.2% pack for 82.1% of the real-word occurrences.
python3 -I b109_size.py          # needs b110_inventory.json from B-110; see below

# STEP 3 — the pack post-step. Works on a COPY; never touches a published
# asset. Asserts every pre-existing row is byte-identical afterwards, by a
# digest over every row of entry, sense and form — not merely by the counts.
python3 -I b109_build.py
```

**Step 2 is the only one that needs something B-110 produced**
(`b109_size.py` reads `b110_inventory.json`, the per-feed unresolved-token
inventory, to express the trade as "real-word occurrences still admitted").
It is a *reporting* step: it chose the threshold and prints the evidence, and
step 3 does not read it. Skip it and the layer still builds; you just lose the
argument for 20.

## The expected output, and why a rebuild will not match it byte-for-byte

```
input pack    aab33f71c0105df94598d51523e68d991b519cc8e575b7d3e979ae46577780bc  18,231,296 B
PUBLISHED     b85cb1f548ec6a8fe96654b67bd382b31fbf8abb83caf72854bda9ee0d2308e9  21,962,752 B
```

**A RE-RUN PRODUCES A DIFFERENT DIGEST, AND THE REASON IS ONE META ROW.**
`b109_build.py` writes `meta.freq_built_at` from the clock:

```python
'freq_built_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
```

The published pack carries

```
freq_built_at = 2026-11-18T05:49:09.625613+00:00
```

so to reproduce `b85cb1f5…08e9` **byte for byte**, pin that value instead of
calling the clock. Everything else in the pipeline is deterministic: the
corpus counts, the threshold, the fold, the row order and SQLite's own
`VACUUM` output. A re-run that pins the timestamp and still differs is a real
finding — start with the corpus archives' digests, since a changed corpus
release is the only other moving part.

**What this does NOT reproduce is the entries.** The extract behind the
pack's 55,906 entries (built 2026-11-06) was not retained, and kaikki.org
serves a rolling dump with no versioned archive, so it cannot be re-fetched or
digested. `meta.kaikki_extract_sha256` says `UNRECOVERABLE` and
`meta.kaikki_extract_note` says why: a digest taken today would describe a
DIFFERENT extract and would be a false provenance claim. A real digest comes
with a pack REBUILD, where the extract is in hand — logged as **B-117**.

## Why `wordscreen.py` is here

The two counting scripts import `dict_fold` and `TOKEN` from it. It is B-110's
screen, and it carries the thing that matters for provenance: a replication of
`klip`'s `lib/utils/dict_fold.dart`, **asserted against every stored fold in
the pack before any figure is reported** — 0 mismatches across all 55,906. A
drifted fold would make every token look unresolvable, and the resulting table
would measure the replication's bug rather than the language. Keep that
assertion in any future re-run; it is the one check the whole layer rests on.

## One footgun, recorded because it bit

`sqlite3 <path> "<query>"` **creates the file if it is missing**, so a read
against a deleted pack silently manufactures an empty database and reports
`no such table: meta` — which reads as corruption rather than absence. Use the
read-only URI, as these scripts do:

```
sqlite3 "file:<path>?mode=ro" "<query>"      # refuses to create; says "unable to open"
```

## Verifying the published pack

```bash
tools/check_published_pack.sh da          # then run it again; believe the second
```


## wordscreen's elision rule, added 2026-11-19

`wordscreen.py`'s `TOKEN` joins words across an apostrophe. Right for Danish;
**wrong for the Romance languages**, where the apostrophe marks an elision —
`nell'omelia` is *nella* + *omelia*. Glued, the pair cannot resolve in any
pack and lands in "probable mishearing": **an artefact that reads as a
finding.** Found running B-110 for Italian by reading the flags.

```
split_elisions(text, lang)     lang=None splits NOTHING — the default, so
                               B-110's published Danish figures cannot move
screen(text, folds, lang=...)  opts in, and classes the bare article left
                               behind as `elision` rather than as a candidate
ELIDABLE                       it, fr, ca, pt. **en is deliberately absent:**
                               `don't` and `it's` are contractions, where the
                               apostrophe really is word-internal
ELISION_EXCEPTIONS             fr `aujourd'hui` is ONE word; splitting it
                               manufactures two candidates per occurrence of
                               one of the commonest words in French
```

**Tests: `python3 -I wordscreen_test.py` — 31 checks.** The first group is the
regression guard that matters most (`lang=None` changes nothing). The tests
caught a real bug during development: the exception guard restored the
canonical lowercase spelling, so `Aujourd'hui` came back `aujourd'hui` —
and case is load-bearing, because `screen` reads a leading capital
mid-sentence as a NAME.
