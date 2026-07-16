# Lessons Learned — RGCS v4 programme

1. **Cheap invariants catch expensive bugs.** The uᵀMu = ρV mass patch
   (one matvec) would have caught V4-D-001 instantly; it now runs as a
   permanent guard. Corollary: every assembly deserves a
   closed-form-scale smoke test before any benchmark.
2. **Never assume mode ordering.** Twice (thick cantilever, free
   tuning fork) the "obvious" first modes were not the modes being
   tested for. Classify modes by measured field structure (signed
   component amplitudes at physical stations), never by index.
3. **Diagnose the coupling regime before fitting a model.** The free
   fork is strongly coupled through base flexure; the textbook
   weak-coupling picture required clamping the base. Fitting the
   two-mode model to the wrong regime would have "worked" with
   meaningless parameters.
4. **Degenerate eigenbases are landmines.** The V4-D-003 determinism
   fix rotated a degenerate eigenspace and thereby exposed V4-D-004 —
   a consensus path that could grant STABLE with no persistence
   evidence. Fixing one defect adversarially stress-tests others;
   run the full battery after every numerical change.
5. **Determinism is a feature you must design for.** ARPACK's random
   start vector and meshio's timestamp header both silently broke
   bit-reproducibility. Fixed seeds are not enough; audit actual
   byte-level artifacts (two builds + SHA256 diff).
6. **Refusal beats approximation.** Diagnostics that refuse to run
   without their inputs (D5/D9/D10/D12), backends that raise instead
   of falling back, and coupling reports that demand leakage controls
   each prevented a class of silent dishonesty.
7. **Audit the audit.** The QA tool's own claims check flagged
   exclusion statements (V4-D-002). Meta-defects are real; manual
   verification of tool findings belongs in the loop.
8. **Registries keep honesty cheap.** Requiring
   id/units/class/provenance/exclusions/tests before first use made
   the honest path the low-friction path for 44+ objects.
9. **Null results need first-class engineering.** Making
   NO_STABLE_CANDIDATE / CONVENTIONAL_NODE_EXPLAINS_RESULT tested,
   machine-readable outcomes (with a scrambled-field control in every
   bundle) is what makes the canonical verdict credible.
10. **Copied evidence must be declared.** The two copied artifact
    classes (hardware benchmarks, fork sweep) are listed in
    PROVENANCE.json; the audit verifies nothing else is copied.
