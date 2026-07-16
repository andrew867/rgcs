# Eye Node-Coincidence Correction (V4C-D-001)

Corrective integration, 2026-07-16. User-identified P1 scientific
defect: the eye engine classified any candidate within a physical
proximity threshold (4 mm in the bundle run; 3 mm engine default) of a
conventional node/antinode station as CONVENTIONAL_NODE_EXPLAINS_
RESULT — conceptually rounding a resolved separation to zero.
Physical proximity and numerical coincidence are different concepts.

## What changed

- The proximity threshold is REMOVED (`node_tol_mm` is accepted but
  ignored, recorded as removed in every procedure record).
- Node coincidence is now decided by
  `eye.node_coincidence_comparison`: EXACT only within the declared
  numerical tolerance (1e-6 mm); UNCERTAINTY_OVERLAPS when the
  candidate and comparator localization intervals overlap
  (mesh resolution ⊕ convergence shift ⊕ material-draw cloud rms);
  otherwise NEAR-BUT-DISTINCT / DISTINCT with the exact separation.
- Classification now happens AFTER all persistence gates, so an
  artifact near a node is still an artifact and a stable candidate
  near a node is still reported at its own coordinate.
- The verdict vocabulary gained DISTINCT_STABLE_CANDIDATE,
  UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE,
  CONVENTIONAL_MODEL_INSUFFICIENT, CANDIDATE_NEW_COUPLING,
  INSUFFICIENT_RESOLUTION, CONTRADICTORY_DIAGNOSTICS.
- Every stable candidate now ships `node_coincidence.json` (raw
  coordinate, comparator coordinate, exact separation, halfwidths,
  mesh resolution, convergence shift, cloud rms, rule) and
  `frequency_sensitivity.json` (per-mode Rayleigh df/dm at the
  candidate).
- Regression battery `tests/v4/test_v4c_node_coincidence.py`:
  3.94 mm never coincident; 0.1 mm distinct unless intervals overlap;
  exact synthetic coincidence passes; coarse-mesh uncertainty yields
  OVERLAP, never a forced conventional verdict.
- Reason-code refinement: unimplemented quartz mechanisms now return
  `MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` with an explicit
  "not evidence of physical nonexistence" note; the binding scope
  statement (`WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md`) was
  replaced with the full does-and-does-not-claim text.

## Reclassification of the canonical 110 mm result (preserved)

The 102.2 mm feature is NOT discarded. Corrected-run evidence
(proof_bundle_110mm/eye/node_coincidence.json):

| quantity | value |
|---|---|
| candidate coordinate | (−0.295, −0.205, **102.240**) mm |
| nearest conventional node/antinode station | (−0.447, 0.774, 106.018) mm |
| exact separation | **3.906 mm** (reported as 3.906 mm, not zero) |
| mesh resolution (element-centroid spacing, clmax 8) | 3.076 mm |
| convergence shift (coarse→fine centroid) | 0.353 mm |
| material-draw cloud rms | 0.032 mm |
| candidate localization halfwidth | 3.076 mm (mesh-dominated) |
| comparator halfwidth | 3.076 mm |
| numerical coincidence tolerance | 1e-6 mm |
| frequency sensitivity at candidate (modes 1/2, ~13.78 kHz pair) | df/dm ≈ −4.86×10⁵ Hz/kg |

Classification: **UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE** — the
implemented conventional model MAY explain the feature within the
current localization uncertainty (interpretation statement 2 of 4).
It is NOT statement 1 ("explains"): the old verdict's implication of
established conventional identity was too strong. It is also NOT a
resolved anomaly: the separation (3.906 mm) is smaller than the
combined localization interval (6.15 mm), which is dominated by the
coarse-mesh element spacing.

Distances to the other declared comparators (unchanged, preserved):
geometric centre ≈ 47 mm; shaft midpoint ≈ 47 mm; frozen RGCS node
prior (RGCS-M.39, z = 51.62 mm female frame) ≈ 50.6 mm along z — the
feature is unambiguously DISTINCT from the geometric centre and the
frozen prior; the male cap/shaft junction plane (z ≈ 101.8 mm) lies
~0.4 mm from the candidate and remains a viable conventional
explanation (junction stress concentration) to be tested, not
assumed.

## What would discriminate

Combined localization halfwidth must fall below ~3.9 mm: mesh levels
near clmax ≈ 4 mm (element-centroid spacing ~1.5 mm) would give a
combined interval ~3 mm and resolve DISTINCT vs OVERLAP; the
convergence shift (0.35 mm) and draw cloud (0.03 mm) are already small
enough. This is a declared computation, not a promise.

## Record keeping

- The published v4.0.0 tag, release, and bundle are FROZEN history
  (their verdict text reflects the old rule).
- The pre-correction second run is preserved at
  `docs/v4/proof/M9-precorrection/`.
- The corrected interpretation ships in the v4.1.0 line; no existing
  tag is rewritten.
