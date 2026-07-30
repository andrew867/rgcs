# Claim boundaries

## The line

```text
Vertex POSITIONS are projector output and remain underdetermined under V1-B01/B02.

Path, polygon, distance, perimeter, centroid, and area geometry are exact for the
selected vertices.

The tool verifies geometry.
It does not verify that a candidate vertex is physically true.
```

This appears on the map pages, in the CLI output, in every address certificate, and in
the release notes. It is the whole claim.

---

## What RGCS V1 is

> RGCS is a coordinate, mapping, signal, and provenance research workbench. It converts
> received or user-supplied numeric vectors into reproducible binary/octal parse
> receipts, candidate Earth-root positions, great-circle paths, and polygonal map
> regions.
>
> RGCS does not claim that anomalous sources, craft, crop formations, physical
> propulsion, or non-human communication are proven.

## The workbench boundary, verbatim

This exact wording is emitted by `r1053.certificate.CLAIM_BOUNDARY` and is asserted by
test wherever it appears:

> RGCS V1 is a coordinate/research workbench with a candidate Earth-root projection. It can parse and emit structured vector receipts, reproduce the V1 calibration artifacts, and classify residuals under declared cell-scale and operational-envelope hypotheses. It does not prove physical craft, alien sources, crop-circle authorship, Phryll propulsion, or metric engineering.

## Release status

```text
RGCS V1 is done-for-now as a frozen candidate codec + Earth-root workbench.
The mapping, path, and polygon geometry are implemented and testable.
The projector endpoints remain candidate outputs under B01/B02.
```

This is released as **software**, not as **proof**.

---

## Claim classes

Every result carries one or more of these. They are emitted in the JSON, not just
written in prose.

| class | meaning | example |
|---|---|---|
| `EXACT_ARITHMETIC` | reproducible bit arithmetic, verifiable by re-execution | the codec lane |
| `STRUCTURAL_PARSE_EXACT` | the wire decomposition is exact and reversible | any direct word |
| `TRAINING_EQUALITY` | agreement that exists **because it was fitted** — not evidence | the three fit anchors |
| `NOT_EVIDENCE_FITS_THE_MAP` | this row helped define the model it appears to confirm | anchor residuals |
| `PROJECTION_UNDERDETERMINED` | output of a law with free parameters remaining | every projected point |
| `CANDIDATE_NOT_LOCATED_TARGET` | a projected point, not a place | every non-anchor word |

The class that does the most work is `TRAINING_EQUALITY`. Much of what looks like
progress in coordinate reconstruction is quantities agreeing because they were
constructed to agree. The anchor residual of 0.000000 km is the canonical case: it is
arithmetic, and the tooling says so rather than presenting it as a result.

---

## What is verified

| question | status | how |
|---|---|---|
| Does the codec parse exactly and reversibly? | **verified** | field reconstruction tests; `F5<<25 \| Q22<<3 \| S3 == word` |
| Are the PATH7 decompositions correct? | **verified** | computed arithmetically in test, not asserted in prose |
| Is the check digit excluded from geometry? | **verified** | 8 words differing only in S3 land in the identical cell |
| Is the great-circle distance correct? | **verified** | three independent formulas agree to < 1e-6 km; 90° = exactly ¼ circumference |
| Is the drawn path a true great circle? | **verified** | sampled midpoint equidistant from both ends; segments sum to the reported distance |
| Is the polygon area correct? | **verified** | two independent exact methods agree to ~1e-13; a spherical octant is exactly ⅛ of the sphere |
| Does the browser kernel match the library? | **verified** | 0.000000 m drift across all seven known vectors |
| Are wide-envelope records refused, never truncated? | **verified** | structural bit-width gate |

## What is not verified

| question | status |
|---|---|
| **Are the projected endpoints the right places?** | **NOT verified** — B01, B02 |
| Is `165879243` in Britain or Quebec? | **NOT verified** — B03; two admissible pinnings disagree by 5121.7 km |
| Is the 15 km cell-scale relation real? | **NOT established** — B04, n = 1 |
| Do decodes land in water as the source states? | **NOT scoreable** — B05, no coastline data |
| Is there a transport bridge for wide records? | **NO** — B07, the affine was refuted |

---

## What RGCS V1 never claims

```text
the coordinate system is proven
physical craft are proven
Phryll is proven
Orion's Arm is a factual authority
"The L's" are externally verified
crop circles validate the codec
```

---

## How lore and provenance material is used

Hard-SF corpora, witness reports, and crop-glyph observations appear in this project as
a **source of distinctions and testable suggestions**. They may motivate a test. They
may never stand in for one.

The operative test of whether a source is being used as a prior or as evidence:
**if every reference to it were deleted, would any verdict or blocker change?**

For Orion's Arm, the answer is no. Nothing in the codec, the projector, or the test
suite depends on it. See [OA Convergence Ledger](OA_CONVERGENCE_LEDGER.md).

Private operator material and personal correspondence are **not published**. Where such
material motivated a result, it is summarised as labelled provenance with the finding
stated on its own terms.

---

## Why the contradictions are shipped

The B01 map — one vector, one octal word, one branch, two admissible positions
5121.7 km apart — is included in the public documentation deliberately.

A tool that only showed its successes would be a tool you could not check. The
instrument is trustworthy precisely because it renders the disagreement as clearly as
it renders the agreement.

```text
Release the instrument.
Do not release the certainty.
```
