# R10.19 — SurfaceBridge recovery

**Label:** `R10_19_SURFACE_BRIDGE_HEADER_STRIPPED_AFFINE_CANDIDATE`
**Status:** CONFIRMED for canonical same-location pairs; **REFUTED** as a
general transport-row canonicalization.
**Evidence class:** DERIVED (symbolic). No physical validation is claimed.

## What was recovered

The R10.8-era affine `y = (923x + 550585316) mod 2^30` was shelved at
R10.9 as `R109-MTL-02-SUPERSEDED`. It had been applied to the **whole**
transport wire, where it produces nothing defensible.

Applied after stripping the lexical `16` transport header **only**, it
reproduces both recorded same-location pairs exactly:

| Anchor | Transport wire | Header-stripped | Bridged | Recorded SurfaceWord | |
|---|---|---|---|---|---|
| Stonehenge | 1643789253 | 43789253 | 165876523 | 165876523 | EXACT |
| Toronto | 1672875493 | 72875493 | 168930443 | 168930443 | EXACT |

Zero parameters were fitted in this run. `923` and `550585316` are read
from `r109.superseded.LEDGER`, recorded long before this analysis. The
operator confirms all vectors are source material, not generated here,
so the reproduction is evidential rather than circular.

## How strong that evidence actually is

Two points do **not** uniquely pin an affine mod 2^30 here.
`X2 − X1 = 29086240` and `gcd(29086240, 2^30) = 32`, so exactly **32**
`(A, B)` pairs satisfy both equations. The honest claim is therefore
*membership in a 32-member family*, not a one-in-2^60 coincidence.

The recorded pair is in that family, and is the member with the
**smallest `A`**. Probability that a pair recorded in advance lands
inside the family by chance: `32 / 2^60 = 2.8 × 10⁻¹⁷`.

## Where it fails

Applied to the 66 variable/transport rows (62 parseable; Montréal
quarantined per R10.18C):

- rows matching the anchor profile (F5 ∈ {4,5} **and** S3 = 3): **3 / 62**
- **two of those three are Stonehenge and Toronto themselves.** The
  anchors sit inside the transport list, so they are training data. A
  headline of "3/62, 6.2× enrichment" would have been training leakage.
- **independent confirmations: 1 / 60, against 0.5 expected by chance.**

That is chance. The apparent structure in the output S3 distribution
(61 of 62 odd) is an artifact of the multiplier, not signal: `A` is odd
and `B ≡ 4 (mod 8)`, so `S3 = (3X + 4) mod 8` is odd whenever `X` is.

The Avebury cross-check *appears* to fail — `1647012173 → 993148035`,
sharing 0 of 10 `surface_octal10` prefix symbols with Stonehenge — but
that was a **category error, not evidence**. Avebury belongs to a
different family. Its relation to Stonehenge is exact in **payload
octal** space:

    Stonehenge 165876523  payload octal = 2173604
    Avebury    1647012173 payload octal = 21736041 = 2173604 || 1

(`4701217 = 587652 × 8 + 1`, one octal level deeper.) See
[R10.19B](R10_19B_FAMILY_SORT_RESULT.md). The affine must never be
applied to this family.

## Provenance caveat

The only product recorded for these constants in
`r109.superseded.LEDGER` is the Montréal mapping, and the ledger tag is
`MTL`. The constants are Montréal-lane derived. Montréal is quarantined,
so they are used here as opaque recorded numbers and no Montréal value
is ever evaluated — `r1019.bridge` calls `r1016.quarantine.assert_clean`
on every input and raises on the three quarantined values.

## Type-safety note

A SurfaceWord such as `165876523` **also** begins with `16`, so the
lexical header cannot type a value on its own. `strip_header` refuses
recorded SurfaceWords explicitly. Residual ambiguity is recorded rather
than papered over: transport wires and SurfaceWords are not separable by
digit count (both may be 9–10 digits and below 2^30), so the guard is a
recorded-value check, not a decision procedure.

## What this does and does not license

- It **does** establish that the header-stripped affine is the correct
  relation for the recorded canonical same-location pairs.
- It **does not** license canonicalizing the 66 transport rows.
- It **may not** be used to manufacture anchors. The hard independent
  anchor count remains **3**; the 17 projection-derived rows remain
  internal-consistency only. The requirement of ≥8 independent anchors
  before the codec search is discriminating is unchanged.

NO_TAG · NO_PUSH · PUBLICATION_HOLD
