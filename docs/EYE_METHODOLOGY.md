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
   inside-body validity → null comparison against the ordinary
   node/antinode stations of the very modes examined → mesh
   persistence (REQUIRED for STABLE; V4-D-004) → boundary sensitivity
   → mode dependence → uncertainty persistence. Every rejection is
   recorded with its reason.
4. **Null outcomes are results.** NO_STABLE_CANDIDATE and
   CONVENTIONAL_NODE_EXPLAINS_RESULT are first-class, tested statuses;
   a scrambled-field control runs inside every proof bundle.
5. **Adversarial validation before use.** The engine passed a
   mandatory battery: planted candidate, symmetric body, mesh
   artifact, boundary false positive, competing regions, outside-body,
   uncertainty collapse, and the null case — before it ever saw the
   canonical crystal.

Applied to the canonical 110 mm crystal the method returned
CONVENTIONAL_NODE_EXPLAINS_RESULT (see EYE_DIAGNOSTIC_REPORT_110MM.md).
What would overturn it is specified in advance: a localized region
where ≥3 independent families co-locate away from ordinary modal
features, persisting across refinement, boundary variants, ≥2 modes,
and material uncertainty.
