# Terra public-release filter report (v0.6)

**PUBLICATION HOLD — the filter classifies; it does not release.**
Nothing was published, tagged or pushed by this run.

## Rules, as implemented

- Exclusion terms (case-insensitive, path/title/tag): `crabwood`,
  `ascii`, `plaintext`, `message_decode`, `message-decoding`,
  `glyph_message`, `private_comms`.
- **Exclusion beats inclusion** on any conflict — a coordinate document
  mentioning Crabwood is `PRIVATE_EXCLUDED`, because a false release is
  worse than a false hold.
- Material already inside a declared private/non-release archive
  (`internal-docs`, `release/r1013-private`, `cwatlas_private`,
  `negative_results`) is `PRIVATE_ARCHIVED` per the spec's "unless"
  clause: it is not release-bound in the first place.
- Coordinate/codec hints (`coordinate`, `codec`, `terra`, `vector`,
  `projector`, `variable-length`, …) admit; anything unmatched is
  `REVIEW_REQUIRED`, never silently released.

## Live-tree scan (docs/, r1053/, cwatlas/)

```
total 1498 files
  PUBLIC_RELEASE_ALLOWED   219
  PRIVATE_EXCLUDED           7
  PRIVATE_ARCHIVED           1
  REVIEW_REQUIRED         1271
no_excluded_term_released: TRUE
```

The 7 exclusions are exactly the Crabwood message-decoding lane
(`docs/proofs/r1064b-vertex-root-crabwood/*`, `docs/r1064b/CRABWOOD_*`) —
the material the v0.6 scope exists to keep out of a public coordinate
release. That the filter finds precisely this lane, and nothing in the
coordinate/codec lanes, is the end-to-end check.

The large `REVIEW_REQUIRED` bucket is by design: this filter never
upgrades an unmatched file to releasable. A human pass over that bucket
is part of any actual release, which this is not.

## Tests

9 filter tests: every declared exclusion term excludes; inclusion hints
admit; exclusion beats inclusion; archives are respected; tags
participate; unmatched → review; case-insensitive; deterministic; and the
live-tree invariant `no_excluded_term_released` holds.
