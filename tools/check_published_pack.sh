#!/usr/bin/env bash
#
# A PUBLISHED PACK MUST MATCH ITS MANIFEST, AND THE PUBLISHED MANIFEST MUST
# MATCH THIS REPOSITORY.
#
# ── WHY THIS EXISTS ──────────────────────────────────────────────────────
#
# `klip` already has `tool/check_published_artifact.sh` for the audio-ingest
# JSON artifacts, and it resolves its source as `tool/audio_ingest/$NAME`.
# `packs.sha256` lives at the ROOT of THIS repository and the packs are
# RELEASE ASSETS, so that script can check neither. Nothing did — a pack
# release could land, or half-land, with no instrument saying so.
#
# ── THE TWO FAILURES IT IS FOR ───────────────────────────────────────────
#
#   1. THE MANIFEST AND THE PACK DISAGREE. `packs.sha256` records a
#      `pack.sha256` and a `pack.bytes` per language. The app verifies the
#      download against them, so a manifest describing bytes nobody serves
#      makes the pack UNINSTALLABLE rather than merely stale.
#   2. THE RELEASE HALF-LANDED. An in-place release replaces assets one at a
#      time, and `releases/latest/download/` has been observed serving the
#      OLD bytes after a release that had actually completed — the incident
#      recorded in `klip`'s own check. **THAT IS WHY THE RULE IS TO RUN THIS
#      TWICE**, a minute apart, and to believe the second run.
#
# IT NEVER SKIPS QUIETLY. No network is a FAILURE, not a pass: a
# skip-when-offline is a silent green, which is the failure mode this exists
# to catch.
#
# Usage:  tools/check_published_pack.sh [lang ...]      # default: da
#         tools/check_published_pack.sh da de it
#
# Honest User-Agent. Nothing is sent but the GET.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BASE="https://github.com/Ekene-ae/klip-dictionary-data/releases/latest/download"
UA="Klip-data-check/1.0"
LANGS=("${@:-da}")
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM

fetch () {            # fetch <url> <dest> — a failure is a failure
  if ! curl -fsSL --max-time 600 -A "$UA" -o "$2" "$1"; then
    echo "FAIL  could not fetch $1" >&2
    echo "      No network is NOT a pass. Re-run when the network is back." >&2
    exit 2
  fi
}

digest () { shasum -a 256 "$1" | awk '{print $1}'; }

fail=0

# ── 1. The manifest: published vs this repository ───────────────────────
echo "== packs.sha256 =="
fetch "$BASE/packs.sha256" "$TMP/packs.sha256"
if cmp -s "$REPO/packs.sha256" "$TMP/packs.sha256"; then
  echo "OK    published manifest is byte-identical to this repository"
else
  echo "FAIL  the published manifest and this repository DISAGREE" >&2
  echo "      repo      $(digest "$REPO/packs.sha256")  $(wc -c < "$REPO/packs.sha256") bytes" >&2
  echo "      published $(digest "$TMP/packs.sha256")  $(wc -c < "$TMP/packs.sha256") bytes" >&2
  diff <(sed -n '1,400p' "$REPO/packs.sha256") <(sed -n '1,400p' "$TMP/packs.sha256") \
    | head -20 >&2 || true
  fail=1
fi

# ── 2. Each pack: published bytes vs what the manifest claims ───────────
#
# The expected values are read from the MANIFEST rather than hardcoded: the
# manifest is the claim the app verifies against, so it is the thing a pack
# has to match.
for lang in "${LANGS[@]}"; do
  echo "== klip-dict-$lang.sqlite =="
  want_sha="$(awk -v f="klip-dict-$lang.sqlite" '
    $1=="pack" && $2==f {found=1; next}
    found && $1=="pack.sha256" {print $2; exit}' "$REPO/packs.sha256")"
  want_bytes="$(awk -v f="klip-dict-$lang.sqlite" '
    $1=="pack" && $2==f {found=1; next}
    found && $1=="pack.bytes" {print $2; exit}' "$REPO/packs.sha256")"
  if [ -z "$want_sha" ] || [ -z "$want_bytes" ]; then
    echo "FAIL  no pack.sha256/pack.bytes row for $lang in packs.sha256" >&2
    fail=1; continue
  fi
  fetch "$BASE/klip-dict-$lang.sqlite" "$TMP/pack.sqlite"
  got_sha="$(digest "$TMP/pack.sqlite")"
  got_bytes="$(wc -c < "$TMP/pack.sqlite" | tr -d ' ')"
  if [ "$got_sha" = "$want_sha" ] && [ "$got_bytes" = "$want_bytes" ]; then
    echo "OK    published pack matches the manifest ($got_bytes bytes)"
  else
    echo "FAIL  the published pack does NOT match the manifest" >&2
    echo "      manifest  $want_sha  $want_bytes bytes" >&2
    echo "      published $got_sha  $got_bytes bytes" >&2
    fail=1
  fi
  rm -f "$TMP/pack.sqlite"
done

echo
if [ "$fail" -eq 0 ]; then
  echo "ALL CHECKS PASSED — now RUN IT AGAIN. A release can be observed"
  echo "half-landed, and the second run is the one to believe."
  exit 0
fi
echo "ONE OR MORE CHECKS FAILED — the release is not complete." >&2
exit 1
