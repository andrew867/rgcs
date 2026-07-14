# RGCS v2 — Milestones

**Author:** Sub-Agent 09. **Date:** 2026-07-14.

## M1 — Evidence base frozen (DONE)
Source corpus ingested with per-claim provenance; classification policy
ratified; 24 corpus inconsistencies registered. Exit: every downstream
artifact can cite a ledger row.

## M2 — Mathematical contract frozen (DONE)
61 equations registered (RGCS-M.1..M.61) with units, assumptions,
classifications; 14 hypotheses H-01..H-14 pre-registered with observables,
controls, failure conditions, uncertainties. Exit: `model_registry.yaml`
schema 1.

## M3 — Coherence/dynamics normative spec (DONE)
COH-M1..M14 defined; golden datasets (cases a–f) generated with frozen
manifest. Exit: independent re-implementation reproduces every manifest
value (verified by QA).

## M4 — Computational core (DONE)
`rgcs_core` 2.0.0; all registry equations implemented and tested; golden
values exact. Exit: core-only suites green.

## M5 — Desktop workbench (DONE)
13-panel PySide6 app; vertical slice (workspace→bundle) automated. Exit:
gate 6 integration test green.

## M6 — Experiment kit (DONE)
8 branch templates, control matrix, schemas, statistical analysis plan.
Exit: schema validation strict + versioned; ethics gate enforced.

## M7 — Manuscript (DONE)
28 pp., fully generated numerics, classification labels throughout. Exit:
zero errors/undefined refs; all pages visually inspected.

## M8 — Independent QA (DONE, verdict YELLOW 2026-07-14)
26 defects registered (5 P1, no P0); all gates exercised with evidence.

## M9 — Release 2.0.0 (THIS MILESTONE)
All P1 defects fixed with regression tests (bibliography, estimator
unification, coupling map, workspace corruption); P2 hardening (loader
errors, finiteness gates, vocab-lint scope, register errata, checksums);
227/227 tests; release artifacts + provenance manifest in `release/`.
Exit criteria: see `RELEASE_CHECKLIST.md` gate walk.

## M10 — First hardware campaign (FUTURE, out of scope for 2.0.0)
Execute branch 1 (modal survey) per `EXPERIMENT_PROTOCOL.md`; first
adjudication of H-01/H-03/H-04 per `STATISTICAL_ANALYSIS_PLAN.md`.
