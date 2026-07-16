# Case Study — The Canonical 110 mm Crystal (computational)

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

## The eye question

The 16-diagnostic consensus (Agent 09; rerun in every proof bundle)
returns **CONVENTIONAL_NODE_EXPLAINS_RESULT**: the single region where
three independent diagnostic families agree (male cap/shaft junction,
z ≈ 102.2 mm) lies within 4 mm of an ordinary node/antinode station of
the examined modes. Distances: ~47 mm from the geometric centre
(L/2), ~46 mm from the frozen RGCS node prior (RGCS-M.39). A
scrambled-field control returns NO_STABLE_CANDIDATE every build.
**No stable, computationally special interaction region was found**;
`eye_coordinate` remains null.

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
