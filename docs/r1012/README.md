# RGCS R10.12 — Consolidated Analytic Codec (Private Release Candidate)

**Publication: HOLD. Private local bundle only. No tag, no push.**

One refusal-first surface over the R10.11C/D/E/F results. The software
computes exactly what the evidence supports and refuses everything else
with typed errors — no fitted warps, no guessed transitions, no famous
places, no invented latitude/longitude.

## Quick start

```bash
rgcs --version
rgcs wire parse 168742538943
rgcs wire explain 165876523
rgcs wire roundtrip 1658274383
rgcs corpus verify
rgcs evidence show 165876523
rgcs transition lookup --child 5 --state 15
rgcs transition refine 165876523 --child 5
rgcs transition candidates 165652893 --child 5
rgcs mesh build --level 2
rgcs mesh audit --level 4
rgcs mesh trace 165876523
rgcs self-test
rgcs release verify
```

## Codec specification (locked)

Segmented frame for the 16-headed family:

    001 | 110 | E3 | S6 | S6 | S6 | C3^depth | M3
     Sol   Terra

- header `16` = octal `1|6` (Sol|Terra), locked by source.
- E3: three aligned bits; the source's two-bit shell/epoch wording is
  preserved; internal subdivision UNRESOLVED. Observed values 2,3,4,6.
- three six-bit states; depth = payload decimal width − 6; one 3-bit
  child per refinement level; terminal digit kept distinct (only 3 is
  the source-reported broad surface class; 5/7/9 are never conflated).
- Width family: 21 + 3·depth bits; overflow REFUSES (never truncates).
- Golden corpus: the A2-corrected 28-wire batch (28/28 exact parses;
  sha256 4e426c0f…). The malformed transcription 1687425419853 lives
  only in the correction ledger.
- The old monolithic F5|Q22|S3 profile is HISTORICAL_ONLY; legacy wires
  are migrated through the canonical parser, never reparsed the old way.

## Transition evidence guide

Twelve SOURCE_KNOWN cells of the 64×8 table (children 5 and 6),
verified on four exact same-location pairs. Everything else is typed:
CONDITIONAL_CONSENSUS (identical under all 32 affine completions),
UNDERDETERMINED (32 possibilities, listed), UNSUPPORTED (children
0,1,2,3,4,7 — no envelope exists). `refine` demands three SOURCE_KNOWN
cells; otherwise use `candidates`. Probes P5/P6 stay frozen with
hashed candidate sets; `rgcs probe register` then `score` is the only
intake path.

## Analytic geometry guide

Topology (20 faces, 30 shared edge IDs), node positions (analytic
Wilkes/SAA frame), refinement law (NONE selected — r=1 stands; the
whole preregistered family was near-inert on anchors), body
realization (WGS84 via the exact geodesy core), and shell projection
are separate layers. **A segmented wire's geometry stops at
STATE_MAPPED**: the S6-state→geometry mapping is the principal
unresolved bridge (six declared hypothesis families, all
UNDERDETERMINED). The 627-step fitted operator is REVOKED; fitted
meshes are HISTORICAL_ONLY.

## Shell and epoch guide

Ba-130 is the sole long-origin epoch authority (Cs-133 downstream fine
phase only). Shell-relative candidate profiles close outer-in vs
inner-out exactly; no shell reduces to a trailing decimal digit.
Gravity-vertical projection refuses without physical field data unless
the geocentric substitute is explicitly requested.

## Limitations (the honest list)

- 12/512 transition cells known; the rest typed, not guessed.
- S6→geometry: UNDERDETERMINED — no latitude/longitude for segmented
  wires, full stop.
- No uniform ratio law selected (10/9 is the source-approved primary
  CANDIDATE; it did not improve held-out anchors).
- E3 internal semantics unresolved; 167-Luna vs Erie tension unresolved.
- Nothing here validates source origin, geography, or physics.

## Correction ledger

See `rgcs release verify` and `r1012/ledger.py` (COR-01…COR-08):
E2→E3; monolithic→segmented; malformed wire superseded; 27/28→28/28;
144000 reclassified as primed-retrospective; 627-step warp revoked;
no 1200-step substitute ever existed; publication HOLD.

## Reproduction

`rgcs self-test` runs the ten mandatory end-to-end workflows live.
`rgcs corpus verify` re-parses the golden 28 + 19 legacy wires and
checks the frozen batch hash. Evidence receipts under
`docs/r1011/evidence/**` and `docs/r1012/`.
