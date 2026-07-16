# Agent 09 Handoff — Eye Diagnostic and Consensus Engine

Status: COMPLETE. 15 tests (full mandatory adversarial battery);
RSCS2-D.1..D.16 registered; canonical-110 verdict:
**CONVENTIONAL_NODE_EXPLAINS_RESULT** (a passing outcome).

## Delivered

- `rscs2_core/eye.py`: DIAGNOSTIC_SPECS (16 diagnostics, full
  metadata, all DER per DV4-010), DiagnosticField/Candidate/
  EyeConsensusResult, elastic field evaluators (D1-D4, D6-D8, D11),
  D5/D9/D10/D12 evaluators that REFUSE to run without their solved
  inputs, top-quantile region extraction, and the documented
  multi-criterion consensus (family-deduplicated agreement,
  localization, validity, null comparison, mesh/boundary/mode/
  uncertainty gates — sequential pass/fail, never an average).
- `tests/v4/test_rscs2_eye.py`: 8 mandatory adversarial cases +
  registry completeness + D5/D9/D10/D12 validity/refusal + Ampère
  anchor + JSON serialization.
- Canonical-110 run artifacts in `evidence/v4/agent09/`;
  `docs/plans-v4/EYE_DIAGNOSTIC_REPORT_110MM.md`.

## Facts Agent 11 (proof bundle) must carry forward

1. The 110 mm verdict is CONVENTIONAL_NODE_EXPLAINS_RESULT: one
   3-family region at the male cap/shaft junction (z ≈ 102.2 mm),
   resolved as ordinary modal structure (3.94 mm from a node/antinode
   station). eye_coordinate stays **null** in all records.
2. Modes 1/2 (≈13.78 kHz) are a symmetry-protected degenerate bending
   pair — report as degenerate, never average.
3. `probe_paths(..., eye_candidate_mm=...)` (Agent 08) therefore takes
   NO eye coordinate for the canonical crystal.
4. Rerun recipe: `scratchpad agent09_run.py` logic — coarse cl 8.0 +
   refined cl 5.5 + cradle variant + 3 material draws, link_radius
   6 mm, node_tol 4 mm. Deterministic (fixed gmsh meshes, LAPACK).

## Open (declared, not hidden)

- D5 (piezo) and D9/D10 (driven complex response) fields were NOT part
  of the canonical-110 consensus run (engine supports them; the run
  covered elastic diagnostics). The verdict statement in the report is
  scoped accordingly.
