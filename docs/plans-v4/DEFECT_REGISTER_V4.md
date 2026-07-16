# V4 Defect Register (Agent 13 Role B/C)

Rule: every defect is REGISTERED before it is fixed; P0/P1 defects get
a reproduction, a regression test, a fix, focused + full test runs,
regenerated evidence, and an audit-trail update.

| ID | Sev | Status | Summary |
|---|---|---|---|
| V4-D-001 | P0 | CLOSED (Agent 03) | Vector mass form used `ddot(u,v)` (matrix double contraction) inflating M ~480×; cantilever modes 4–22× low, worsening with refinement. Fix: `rho*dot(u,v)`; permanent guards: uᵀMu=ρV mass patch (1e-9) + explicit wrong-form test. Secondary: hand-rolled stiffness was asymmetric → frozen to skfem `linear_elasticity` / validated einsum form. |
| V4-D-002 | P2 | CLOSED | QA claims-wording audit (G29, `tools/qa_audit_v4.py`) flagged "therapeutic/consciousness/metric engineering" in V4_PRODUCT_SPEC.md and V4_MATHEMATICAL_MODEL_PLAN.md. MANUAL VERIFICATION: both occurrences are EXCLUSION statements ("No experimental confirmation, therapeutic effect, consciousness causation, metric engineering … import"). Defect is in the AUDIT TOOL's negation detection (required the literal phrase "no unsupported"), not in the docs. Fix: audit recognizes negation/exclusion context markers; the two sites re-verified manually and recorded here. G29 holds. |
| V4-D-003 | P1 | CLOSED | Proof bundle NOT bit-deterministic across two builds in one process: `eigsh` (ARPACK, shift-invert) uses a RANDOM start vector from NumPy's global RNG, so eigenpairs jitter at ~1e-10 between calls. Amplitude-only fields (D1/D7/D8/D11) survived 6-sig-fig printing; strain/frequency-derived artifacts (D2/D3/D4/D6 CSVs, patch_tests.json orthonormality, eye consensus JSONs) flipped last digits. Reproduction: `tools/qa_audit_v4.py` bundle-determinism check (two `--fast` builds, SHA256 compare) — 8 files differed. Fix: deterministic ARPACK start vector `v0 = ones/√n` in `fem.solve_modes`, `refsystems.cavity_modes_fem`, and `piezo.solve_piezo_modes`. Regression test: `tests/v4/test_rscs2_solver.py::test_solve_modes_bit_deterministic` (two solves, exact array equality — fails before fix). SECOND SOURCE found on re-audit: meshio stamps the OBJ export header with wall-clock time — header normalized in the bundle builder. Evidence regenerated: proof bundle rebuilt, audit re-run GREEN (two builds bit-identical on all data artifacts). |

| V4-D-004 | P1 | CLOSED | Eye engine could grant STABLE_CANDIDATE_REGION with NO mesh-persistence evidence: all persistence gates (D13/D14/D15) were optional inputs, so `eye_consensus(fields, geom)` alone could return STABLE — violating G21 ("candidate persistence is evaluated over mesh refinement"). EXPOSED adversarially when the V4-D-003 deterministic-v0 fix rotated the free cube's degenerate-mode basis and the symmetric-body test produced localized 3-family corner clusters that sailed through the gate-free path. Fix: without `refined_fields` a candidate is REJECTED with reason "mesh-refinement persistence not evaluated … STABLE cannot be granted (G21)"; overall status falls back to NO_STABLE_CANDIDATE. Regression: the symmetric-body test now passes for the RIGHT reason, plus `test_stable_requires_persistence_evidence` (synthetic planted candidate WITHOUT refined fields must not be STABLE). Canonical run unaffected (it always supplies refinement + boundary + uncertainty inputs). |

## Pre-existing, NOT v4 defects (recorded for completeness)

- `tests/regression/test_generator_determinism.py::test_generator_deterministic`
  fails outside the archived v2 reference environment (last-digit
  float drift). This is the documented D-V3-04 scoping; hosted CI
  deselects exactly this node id. No action for v4.
