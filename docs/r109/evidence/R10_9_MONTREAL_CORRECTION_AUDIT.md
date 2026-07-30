# R10.9 Montréal Correction Audit (Phase 5)

## The correction

`165879243` is now parsed **directly** as compact RGCS-30
(R109-MTL-01, EXACT_ARITHMETIC for the parse; SOURCE_REPORTED for the
location attribution):

```text
binary30: 001001111000110001110111001011
octal10:  1170616713
F5:       4          -> source_face (4+14) mod 20 = 18 -> mesh face 12
path:     3,3,0,1,2,0,3,2,3,2,1
S3:       3          (decimal terminal marker also 3 — kept distinct)
```

Verified against the frozen public parser with exact round-trip; no
parser change was needed or made.

## What was removed from current authority (and preserved)

| Item | New status | Preserved in |
|---|---|---|
| General affine bridge `y=(923x+550585316) mod 2^30` | SUPERSEDED (R109-MTL-02) — refused in production; historical replay only via explicit profile id | `r109.superseded`, archived V1 candidate |
| `165879243 -> 168500683` mapping | SUPERSEDED — never applied without an explicitly selected historical profile (test-enforced) | superseded-model ledger |
| Transcription `168729543` | SUPERSEDED provenance — not the current Montréal packet; not a fit anchor (test-enforced) | vector registry V2 |

Note: the archived V1 affine arithmetic still replays EXACTLY under the
historical profile (`43789253 -> 165876523` reproduced in tests) — the
model is preserved, only its authority is revoked.

## Structural consequence (reported, not smoothed over)

Direct Montréal lies on **packet face 4 — the same face as
Stonehenge** — and its pre-warp cell is only ~0.30° from Stonehenge's
pre-warp cell on mesh face 12, while the physical targets are ~5,000 km
apart. Consequences, measured:

1. Under V1, `165879243` lands at (51.79, −2.14) — near Stonehenge,
   not Montréal. V1 cannot represent the corrected packet.
2. V2 (`EARTH_ALIGNMENT_V2_MONTREAL_DIRECT`) maps every calibration
   anchor exactly (max residual 8.5e-7°) **but folds**: 361
   orientation reversals on the level-6 mesh vs V1's 0. The corrected
   Montréal packet is in strong tension with the smooth-warp family at
   V1's scales.
3. The old V1 exact tree-equilateral statement (Erie/Montréal/Toronto
   LCP=2 on face 5) does NOT hold for the direct packet (face 4); the
   pack's own framing — equilateral only after correct nonlinear,
   face-dependent, shell-dependent decoding — remains a SOURCE_REPORTED
   constraint on the future decoding model, not a current result.

## V1/V2 comparison

Global and per-vector numbers: `R10_9_EARTH_V1_V2_COMPARISON.csv`,
`R10_9_EARTH_V2_OPERATOR.json`, `R10_9_GLOBAL_DISTORTION_REPORT.md`.
Both operators are preserved; neither claims validation.
