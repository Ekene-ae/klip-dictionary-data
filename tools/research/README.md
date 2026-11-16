# tools/research — the measurement scripts, rescued from outside the repos

**These are the ONLY copies.** They lived in a working folder outside both
repositories (`~/dict-work`) that is being deleted, and an inventory on
2026-11-16 found them in neither `klip` nor `klip-dictionary-data`. Everything
else in that folder was reproducible — the packs and exports matched this
repository's own v6 release by sha256, the kaikki dumps are re-downloadable
and their digests are recorded in `packs.sha256`, and the rest was Python
virtualenvs. **Of 5.91 GB, these 212 KB were what existed nowhere else.**

They are preserved here as HISTORY AND METHOD, not as a build input.

```
NOTHING HERE IS IMPORTED BY THE APP, BY ANY BUILD, OR BY ANY TEST.
Each script's own header says "OUTSIDE THE REPO" and that is still true of
what it does — only of where the file sits has changed.
NO OUTPUTS WERE COPIED. The CSVs, JSON scans, fetched pages, feed snapshots
and run logs stayed behind; the measurements they produced are cited in the
klip repository's design documents and register, where the conclusions live.
```

**NO CREDENTIALS ARE IN THESE FILES, AND THAT WAS CHECKED BEFORE THEY MOVED.**
Every one was scanned for key-shaped literals. `_oracle_common.py` reads its
keys from the environment (`DEEPL_AUTH_KEY`, `GOOGLE_TRANSLATE_API_KEY`) and
its own header records that they are not accepted any other way; the two
reference oracles take their inputs as command-line arguments. The only long
literals in the set are regexes, printf format strings and HTTP headers.

## What each folder measured

| folder | what it measured |
|---|---|
| `.` (top level) | the translation-quality oracles and the feed fetchers — see the per-file list below |
| `podscan/` | **podcast transcript availability**, the Listen door's input. Which feeds carry a usable transcript, per language, plus the per-feed coverage and the synthetic-transcript screen |
| `readscan/` | **the Read starter list's input, at FEED level**: does the feed itself carry the article text? The answer was almost never, which is what produced readscan 2 |
| `readscan2/` | **PAGE-level extraction**: does a reader view get an article out of the page? The question that actually decides the Read door. Also the EU licence and parallel-corpus probes |
| `readscan2b/` | **B6's refined wall detector**, re-measured. It re-fetches rather than re-reading disk, because the extracted body cannot be derived from what readscan 2 stored |
| `readscan2b-dr/` | **the 18 DR candidates plus `sporten`**, 2026-11-08. A separate directory on purpose: `readscan2b/report_b6.py` globs its own pages, so mixing them would have changed that report |
| `readscan3/` | **Wikipedia, and the endpoint behind the press-corner shell** — the third of three, after feeds and pages. APIs, stdlib only |

### The top-level scripts

| script | what it does |
|---|---|
| `argos_ref.py` | the Argos half of the (d1) bench, and **the zipf lookup `tool/dict_pack/bench.dart` in the klip repo depends on** — that file says "argos\_ref.py --zipf … Outside the repo (wordfreq)", so without this script half of that benchmark cannot be reproduced |
| `deepl_ref.py` | the DeepL oracle for the d1b bench, same CSV contract as `argos_ref.py` |
| `google_ref.py` | the Google Translate oracle, same CSV contract |
| `_oracle_common.py` | shared plumbing for the HTTP oracles, and the record of **what is sent**: dictionary headwords from the published assets, nothing else |
| `dedupe_measure.py` | PD3's folded-key dedupe measurement — safety first, size second |
| `fetch_candidates.py` | live-fetches the candidate feeds, with an **absolute per-feed deadline** rather than a socket timeout (the zh lesson: `urlopen(timeout=)` is per-socket-operation) |
| `review_starter.py` | fetches the 42 curated starter feeds and reports what a reviewer needs |
| `confirm_final.py` | re-fetches the final set to confirm nothing moved |

`export_pack.py` is **not** here: it already lives at this repository's root
and the copies are byte-identical, so adding a second would have been the
duplicate this move exists to avoid.
