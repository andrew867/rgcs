# Case Study — The Canonical 110 mm Crystal (computational)
> **Corrective addendum (V4C-D-001, 2026-07-16):** the verdict below used a node-proximity threshold. Corrected reclassification: UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE with the exact 3.906 mm separation preserved - see docs/v4/EYE_NODE_COINCIDENCE_CORRECTION.md.


All results computational; no experimental confirmation exists. The
historical eye is a Source claim; the ideal and nominal geometries are
distinct.

## Geometry

| | ideal N=7 | nominal |
|---|---|---|
| length | 770.263671875/7 = 110.037667410714… mm (exact arithmetic) | 110.000000 mm |
| wide diameter (across vertices) | L·40/154 | L·40/154 |
| narrow diameter | L·30/154 | L·30/154 |
| female / male face slope | 51.843° / 60° | same |
| frame | female apex z=0 → male apex z=L; C-axis ∥ +Z | same |

Cap heights from the frozen v2 helpers; analytic volume exact
(2 pyramids + frustum); meshes deterministic (SHA256 in
`proof_bundle_110mm/geometry/geometry_hashes.json`).

## First elastic modes (free-free, frozen α-quartz, medium mesh)

From `proof_bundle_110mm/modes/eigenvalues_*.csv` (this build):
modes 1/2 form a symmetry-protected degenerate bending pair
(hexagonal section) near 13.78 kHz; modes 3/4 near 25.9/31.9 kHz;
refinement moves the pair < 0.05% (mesh_convergence.csv). Ideal vs
nominal frequencies differ by the expected −ΔL/L scaling family —
the two configurations are numerically distinguishable and never
conflated.

## The eye question (corrected, v4.1.0)

The 16-diagnostic consensus (rerun in every proof bundle) finds one
region where three independent diagnostic families agree, at the male
cap/shaft junction. Corrected uncertainty-aware record (V4C-D-001; the
old 4 mm proximity rule is removed):

- candidate coordinate: (−0.295, −0.205, **102.240**) mm;
- nearest conventional node/antinode station:
  (−0.447, 0.774, **106.018**) mm;
- exact separation: **3.906 mm** (reported exactly, never absorbed);
- localization halfwidth: 3.08 mm (mesh-resolution dominated);
  convergence shift between mesh levels: 0.353 mm; material-draw
  cloud rms: 0.032 mm; numerical coincidence tolerance: 1e-6 mm;
- verdict: **`UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE`** — the
  implemented conventional model *may* explain the result within
  current localization uncertainty; it is *not established that it
  does*. Finer mesh resolution is the discriminating next computation.

Distances from declared priors: ~47 mm from the geometric centre
(L/2), ~46 mm from the frozen RGCS node prior (RGCS-M.39) — the
candidate is neither. A scrambled-field control returns
NO_STABLE_CANDIDATE every build. `eye_coordinate` remains null (no
exact coincidence and no distinct-stable claim). The v4.0.0 records,
which used the retired proximity rule, are frozen history
(`docs/v4/proof/M9-precorrection/`).

## Addressability projections (no coupling claims)

- Optical: axial OPL 169.745 mm (632.8 nm o-index), transit 0.566 ns;
  side-entry paths to centre/node-prior differ by 0.17 mm OPL-scale.
- Piezo: static 10 V on opposed shaft electrodes produces a solved
  displacement/potential field (bundle fields/electric/).
- Drive: uniform-x body force couples to the bending pair; overlap
  tables in the bundle.

## Reproduce

`python -m rscs2_core.proofbundle` → verify with
`rgcs-v4 verify-checksums`. Verdict is machine-read from VERDICT.json.

