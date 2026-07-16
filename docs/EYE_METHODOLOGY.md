# Eye Diagnostic Methodology (RGCS v4)

The question "does this body possess a stable, computationally special
interaction region?" is answered by machinery that is structurally
incapable of assuming the answer:

1. **Sixteen registered diagnostics** (RSCS2-D.1–D.16), each with a
   declared field definition, units, normalization, conventional
   interpretation, failure conditions, artifact risks, classification
   (always Derived — an eye claim is never Established, DV4-010), and
   provenance. Diagnostics that need inputs the run does not have
   (solved potential, complex response, solved EM field) refuse to run
   rather than approximate.
2. **Regions, not points.** Candidates are top-quantile clusters with
   centroid + bounding box + score — no unjustified point precision.
3. **Sequential gates, never averaging.** Family-deduplicated
   agreement (correlated diagnostics count once) → localization →
   inside-body validity → uncertainty-aware node-coincidence
   comparison against the ordinary node/antinode stations of the very
   modes examined (`node_coincidence_comparison`: EXACT only within
   the declared numerical tolerance of 1e-6 mm; interval overlap and
   resolved separations reported at their exact values — the old 4 mm
   proximity rule was removed as defect V4C-D-001) → mesh persistence
   (REQUIRED for STABLE; V4-D-004) → boundary sensitivity → mode
   dependence → uncertainty persistence. Every rejection is recorded
   with its reason.
4. **Null and indeterminate outcomes are results.**
   NO_STABLE_CANDIDATE, UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE,
   NEAR_CONVENTIONAL_NODE_BUT_DISTINCT, INSUFFICIENT_RESOLUTION, and
   the rest of the corrected vocabulary are first-class, tested
   statuses; a scrambled-field control runs inside every proof bundle.
   A candidate coordinate is never moved onto a comparator and a
   resolved separation is never conceptually rounded to zero.
5. **Adversarial validation before use.** The engine passed a
   mandatory battery: planted candidate, symmetric body, mesh
   artifact, boundary false positive, competing regions, outside-body,
   uncertainty collapse, and the null case — before it ever saw the
   canonical crystal.

Applied to the canonical 110 mm crystal the corrected method returns
**UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE** (candidate z = 102.240 mm,
nearest station z = 106.018 mm, separation 3.906 mm, localization
halfwidth 3.08 mm — the conventional model *may* explain the result
within uncertainty; it is not established that it does). See
`docs/v4/EYE_NODE_COINCIDENCE_CORRECTION.md` and the proof bundle's
`eye/node_coincidence.json`. The discriminating next computation is
finer mesh resolution; what would establish a distinct candidate is
specified in advance: non-overlapping localization intervals
persisting across refinement, boundary variants, ≥2 modes, and
material uncertainty. (The v4.0.0 report used the retired proximity
rule and is preserved as labelled history.)
