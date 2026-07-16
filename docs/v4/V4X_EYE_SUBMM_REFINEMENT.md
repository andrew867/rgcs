# V4X C02 — Eye sub-millimetre refinement

Ledger coverage: **A07, A08, A09, A10**. Gates: **G07** (exact-coordinate
preservation), **G08** (adaptive convergence or honest insufficient
resolution).

Status: **INSUFFICIENT_RESOLUTION**.

Artifacts: [refinement_ladder.json](proof/C02/refinement_ladder.json),
[driven_phase_diagnostics.json](proof/C02/driven_phase_diagnostics.json),
[frequency_sensitivity_map.json](proof/C02/frequency_sensitivity_map.json).
Reproduce with `python tools/v4x_eye_refinement_run.py`.

## What was run

A three-level mesh ladder on the canonical ideal N=7 geometry
(characteristic length 8.0 → 5.5 → 4.5 mm), eight elastic modes per
level, with the Eye candidate taken as the nearest D2/D1/D8 diagnostic
cluster to the canonical candidate coordinate.

| Level | clmax (mm) | Candidate centroid (mm) | Element spacing (mm) | f₁ (Hz) |
|---|---|---|---|---|
| coarse | 8.0 | (−0.256, 0.016, 102.288) | 6.896 | 13781.7 |
| fine | 5.5 | (−0.060, 0.051, 102.307) | 4.972 | 13775.7 |
| finer | 4.5 | (0.090, −0.321, 102.053) | 4.096 | 13774.0 |

## What it shows

The axial coordinate is stable across the ladder: the candidate stays at
z ≈ 102.05–102.31 mm at every level, consistent with the canonical
v4.1 record (z = 102.240 mm). Modal frequencies converge monotonically
(13781.7 → 13775.7 → 13774.0 Hz, changes of 6.0 then 1.7 Hz).

The transverse coordinate does **not** converge. The centroid moves
0.42 mm between the last two levels, which is comparable to the element
spacing at the finest level (4.096 mm). The localization halfwidth
therefore remains ≈ 4.096 mm — it has **not** contracted below the
candidate-to-station separation of 4.149 mm computed at this level.

## Verdict

The refined run returns `UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE` with
separation 4.149 mm and halfwidth 4.096 mm. Because the halfwidth is of
the same order as the separation, and because the transverse centroid is
still moving at the mesh scale, this refinement is recorded as
**INSUFFICIENT_RESOLUTION** for the question it was built to answer.

Read plainly: **this run did not resolve whether the candidate coincides
with the conventional node.** It did not refute coincidence and it did
not establish distinctness. A finer ladder (clmax ≲ 1 mm) is required
before the halfwidth can be smaller than the separation, and that is the
condition under which the classification would carry information.

## What is not claimed

- No proximity threshold is used anywhere in this analysis. Exact
  conventional-node coincidence is asserted only within the numerical
  tolerance of 1e-6 mm. A separation of 4.149 mm is reported as
  4.149 mm.
- The canonical v4.1 record is unchanged and is not superseded by this
  run: candidate (−0.295, −0.205, 102.240) mm, station
  (−0.447, 0.774, 106.018) mm, separation 3.906 mm, halfwidth 3.08 mm,
  convergence shift 0.353 mm, cloud RMS 0.032 mm. This refinement is an
  additional, coarser-mesh record, not a replacement.
- The candidate has not been moved onto the comparator, and the
  comparator has not been moved onto the candidate.
- Nothing here is experimental confirmation of anything.

## D9/D10 driven-response diagnostics (A09)

The complex driven response at the first elastic mode
(`fem.harmonic_field`, normalized force, damping ratio as declared in
the run script) gives a mean phase coherence of 0.773 over the thinned
slab points and 4 phase singularities on the interpolated x–z plane.

These are reported as measured properties of the computed field, not as
evidence for the candidate. The realness guards in
`eye.phase_coherence_field` and `eye.phase_singularities_on_plane` were
changed from an absolute `np.allclose(w.imag, 0)` test to a relative one
(`max|Im w| < 1e-12 × scale`): the absolute form rejected genuine complex
driven responses whose amplitudes are small in absolute terms, which is
a solver-scale artifact rather than a physical statement.

## Frequency sensitivity (A10)

`frequency_sensitivity_map` was evaluated at the candidate, the station,
and their midpoint; see the artifact. The map is a derived sensitivity of
the modal frequency to coordinate perturbation and carries no claim about
which location is physically preferred.
