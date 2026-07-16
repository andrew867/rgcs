# V4 Handoff — planning package → execution

**Status:** PLANNING COMPLETE. This package is implementation-ready for
an autonomous execution run. **No production code was written this pass**
(brief rule). Start at `V4_IMPLEMENTATION_PLAN.md` P1.

## 1. What exists (this planning package)

`docs/plans-v4/`: 25 planning documents —
V4_PRODUCT_SPEC, V4_SYSTEM_ARCHITECTURE, V4_MATHEMATICAL_MODEL_PLAN,
V4_GEOMETRY_AND_MESH_SPEC, V4_CPU_SOLVER_SPEC,
V4_ACCELERATOR_BACKEND_SPEC, V4_ANISOTROPIC_QUARTZ_SPEC,
V4_PIEZOELECTRIC_MULTIPHYSICS_SPEC, V4_OPTICAL_MODELLING_SPEC,
V4_COIL_AND_EM_COUPLING_SPEC, V4_EYE_DIAGNOSTICS_SPEC,
V4_REFERENCE_SYSTEMS_SPEC, V4_DATA_AND_INVERSE_MODELLING_SPEC,
V4_VISUALIZATION_AND_REPORTING_SPEC, V4_DESKTOP_AND_CLI_SPEC,
V4_TEST_PLAN, V4_IMPLEMENTATION_PLAN, V4_MILESTONE, V4_RISK_REGISTER,
V4_ACCEPTANCE_CRITERIA, V4_TRACEABILITY_MATRIX, V4_RELEASE_PLAN,
V4_AGENT_EXECUTION_PLAN, V4_DECISION_LOG, and this handoff.

Living registers updated: CLAIM_REGISTER (H-31 v4 eye robustness),
DECISION_LOG (DV4 mirror), RISK_REGISTER, TRACEABILITY_MATRIX,
ROADMAP_TO_FALSIFICATION, PROGRAMME_PROGRESS.

## 2. Binding constraints the executor inherits

- Frozen immutable: v2.0.0, v3.0.0, `archive/v2.0.0/`, `RGCS-M.*`,
  `RSCS-C.*`/`RSCS-O.*`. Never rewritten.
- New ids only in `RSCS2-*` namespaces (DV4-002), via the governance
  path (registry row before first use).
- CPU is the numerical authority; CPU-only must always work (DV4-004).
- No new physics; every governing equation EST + cited (DV4-012).
- Eye stays SRC; candidates DER/HYP, never EST; NULL-capable (DV4-010).
- v4 reproduces frozen v3 (V.6/V.9 anchors, DV4-009).
- GPU claims per the four-status ladder; no benchmark without hardware.
- Safety envelope (D6/D7) binds all optical/coil run descriptions.

## 3. Iteration template (Hydrogenuine format — use per phase)

Each phase's execution produces a block:

```
## Phase P<n> — <name>
PRODUCT impact:      <what a user can now do>
SPEC changes:        <which V4_*_SPEC sections realized/refined>
TEST changes:        <exact test node ids added; categories>
IMPLEMENTATION:      <modules/functions; RSCS2-* ids registered>
RISKS:               <from V4_RISK_REGISTER; new ones>
ACCEPTANCE:          <the measurable exit criteria met>
EVIDENCE ARTIFACTS:  <benchmark results, plots, manifests, provenance>
ROLLBACK:            <how to revert; what a failure means>
```

## 4. First actions for the execution run (P1)

1. Resolve repo root; confirm HEAD and frozen-path diff empty.
2. Create `rscs2_core` package skeleton + `rscs2_core/registry/` with an
   empty schema-versioned `rscs2_registry.yaml` (mirrors rscs_core).
3. Author the first registry rows (stubs) for the ids Tranche B needs.
4. Run the v3 suite to confirm the baseline is green before adding.
5. Begin P3 dependency PoCs + licence audit; record the backend
   decision (P4) in `V4_DECISION_LOG`.

## 5. Definition of planning-done (this pass)

- 25 planning docs present; every brief requirement mapped in the
  traceability matrix; crystal primary; fork+cantilever mandatory; CPU
  authority preserved; eye non-EST + NULL-capable; conservative-extension
  anchors defined; GPU honesty ladder defined; no new physics; no
  safety creep; frozen artifacts untouched; registers updated.
- **Verdict: PLANNING COMPLETE — ready for execution.**
