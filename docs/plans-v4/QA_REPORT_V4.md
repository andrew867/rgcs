# QA Report — RGCS v4 (Agent 13 Role B, independent adversarial pass)

Method: the QA role did NOT trust the test suite. A standalone audit
(`tools/qa_audit_v4.py`, results in `tools/qa_audit_v4_results.json`)
re-derived every load-bearing claim from scratch: matrix symmetry,
mass/stiffness scale patches, tensor ordering, Bond rotations, frozen
Christoffel anchors, units end-to-end, rigid modes, residuals,
orthogonality, piezo uncoupled limit, material constants vs published
values, geometry distinctness, registry completeness, frozen git
history, screenshot authenticity, claims wording, bundle determinism,
and licences — 19 checks. The eye engine was additionally audited via
its mandatory adversarial battery (8 cases) and the scrambled-field
null control inside the proof bundle.

## Outcome

- 17/19 checks passed on first adversarial run.
- 2 defects found, registered BEFORE fixing (DEFECT_REGISTER_V4.md):
  - **V4-D-002 (P2)**: the audit tool's own claims-wording check
    flagged exclusion statements; docs verified clean manually; the
    tool's negation detection was fixed.
  - **V4-D-003 (P1)**: proof bundle not bit-deterministic — ARPACK's
    random start vector jittered eigenpairs ~1e-10 between calls.
    Fixed with a deterministic v0 in all three eigensolvers
    (`fem.solve_modes`, `refsystems.cavity_modes_fem`,
    `piezo.solve_piezo_modes`); regression test
    `test_solve_modes_bit_deterministic` added; bundle regenerated;
    audit re-run green (two builds bit-identical on all data
    artifacts).
- Historical P0 **V4-D-001** (mass form `ddot` vs `dot`) remains
  closed with permanent guards (mass patch + wrong-form test),
  re-verified independently by this audit.

## Domain audits

Detailed findings per domain: NUMERICAL_AUDIT_V4.md,
QUARTZ_TENSOR_AUDIT.md, PIEZOELECTRIC_AUDIT.md, ACCELERATOR_AUDIT.md,
EYE_DIAGNOSTIC_AUDIT.md, REFERENCE_SYSTEM_AUDIT.md,
REPRODUCIBILITY_AUDIT_V4.md, SCREENSHOT_AND_LAYOUT_AUDIT.md.

## Verdict

No open P0/P1 defects (G28). Release recommendation:
RELEASE_RECOMMENDATION.md.
