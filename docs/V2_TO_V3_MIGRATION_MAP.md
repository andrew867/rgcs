# V2 → V3 Migration Map

Agent 01 deliverable. Dispositions: **retain** (unchanged, still
authoritative), **revise** (kept, edited in place for v3), **supersede**
(replaced by a new v3 artifact; v2 copy remains in the tag/archive),
**archive** (frozen under `archive/v2.0.0/` or the `v2.0.0` tag, no v3
role), **remove** (deleted with justification). No silent redefinitions:
any symbol or equation change must go through `docs/DECISION_LOG.md` and
the registry rules in §4.

## 1. Code modules

| v2 asset | Disposition | Notes |
|---|---|---|
| `rgcs_core/geometry/` (crystal, spiral, nodes, angles) | retain → revise | Becomes the crystal-application layer over `rscs_core.coordinates`; API kept, internals may delegate to RSCS transforms. |
| `rgcs_core/harmonics/`, `compact_modes/` | retain → revise | Compact-mode spectrum (RGCS-M.13–17) re-expressed as RSCS modal occupancy; numerical outputs must stay golden-test identical. |
| `rgcs_core/resonance/`, `coupled_modes/` | retain → revise | Two-mode/N-mode machinery generalizes into `rscs_core.coupling`; QA-D-04 anti-Hermitian convention is the frozen sign/units convention for RSCS coupling operators. |
| `rgcs_core/coherence/` | retain | Coherence metrics are measurement-layer; RSCS `observation` wraps them, does not replace them. |
| `rgcs_core/loading/`, `drive/` | retain → revise | Drive families map to RSCS `state_preparation`. |
| `rgcs_core/uncertainty.py` | supersede | Generalized into `rscs_core.uncertainty` (typed intervals/distributions); v2 functions kept as thin wrappers until v3.0.0 final. |
| `rgcs_core/provenance/`, `experiments/` | retain → revise | Extended for RSCS provenance coordinates; schema version bump only, no field removals. |
| `rgcs_desktop/` (13 panels) | retain → revise | Workbench continues; gains RSCS views. **MIG-CODE-07:** fix V2-WIN-01 (zip arcname separators, `services/bundle.py`) and the specimen-listing Windows defect; add Windows CI. |
| `rgcs_desktop` missing `pyyaml` dep (V2-PKG-01) | revise | Declare `pyyaml` in pyproject (done in v3 skeleton commit). |
| `tools/` (figures, tables, golden generator, packaging) | retain → revise | Regeneration pipeline reused for the four v3 manuscripts; golden regeneration must pin numpy/scipy versions (see MIG-TEST-02). |
| `tools/RGCS_v2_Computational_Workbook.xlsx` | archive | Historical origin artifact; WB-SO-1..3 gaps already documented. |
| `scad/` | retain → revise | D-02 (inert compact render mode) remains open; scheduled with Agent 08. |
| `experiments/` schemas/templates/controls/sample_data | retain | v3 adds protocols/notebooks alongside; existing schema files version-frozen at schema 1. Golden CSVs are baseline evidence — never regenerated in place (MIG-TEST-02). |
| `tests/` (unit/property/golden/regression/ui/integration) | retain | All 227 stay green (with pinned env); v3 adds `tests/adversarial/` and Windows-marked expectations. |

## 2. Documents

| v2 doc | Disposition | Notes |
|---|---|---|
| `docs/MATHEMATICAL_MODEL.md`, `NOTATION_AND_UNITS.md` | supersede | Superseded by `RSCS_MATHEMATICAL_MODEL.md` + frozen-notation deliverable of Agent 02/03; v2 symbols may not be redefined, only extended. |
| `docs/model_registry.yaml` | revise | Registry schema 2: adds RSCS namespace; all RGCS-M.\* entries immutable (§4). |
| `docs/SCIENTIFIC_CLASSIFICATION_POLICY.md` | revise | Extend EST/DER/HYP/SRC with ENG label (per quality gates). |
| `docs/ROADMAP_TO_FALSIFICATION.md` | revise | H-01…H-14 retained verbatim; v3 hypotheses append H-15+. |
| `docs/INCONSISTENCY_REGISTER.md`, `TRACEABILITY_MATRIX.md`, `PROVENANCE_REGISTER.csv`, `RISK_REGISTER.md`, `DEFECT_REGISTER.md` | revise | Continue as living registers; v2 rows never deleted, only appended/annotated. |
| `docs/SPEC.md`, `ARCHITECTURE.md`, `TEST_PLAN.md`, `IMPLEMENTATION_PLAN.md`, `MILESTONE.md`, `ACCEPTANCE_CRITERIA.md`, `RELEASE_CHECKLIST.md`, `USER_GUIDE.md` | revise | Rewritten for v3 scope in place; v2 state preserved in tag. |
| Remaining v2 analysis docs (COHERENCE_\*, DIMENSIONAL_ANALYSIS, DYNAMIC_COHERENCE_SPEC, STATISTICAL_ANALYSIS_PLAN, EXPERIMENT_PROTOCOL, MODEL_ASSUMPTIONS, SAFETY_AND_ARTIFACT_CHECKLIST, CLAIM_AUDIT, SOURCE_\*, QA_REPORT, REPRODUCIBILITY_AUDIT, LAYOUT_QA_REPORT) | retain → revise | Kept as v3 working documents; Agent 10 issues a fresh QA report rather than editing the v2 one in `archive/`. |
| `manuscript/` (v2 LaTeX + generated figures/tables) | archive + supersede | v2 manuscript frozen (tag + `archive/v2.0.0/release/`); v3 produces four new manuscripts under `manuscripts/`. The v2 `manuscript/` tree stays for reference until Agent 09 stands up `manuscripts/`, then moves to `archive/v2.0.0/manuscript/`. |
| `release/*` (v2 artifacts) | archive | Moved to `archive/v2.0.0/release/`; top-level `release/` reserved for v3. |
| `README.md`, `CITATION.cff`, `LICENSE`, `pyproject.toml` | revise | Updated for rgcs-v3 / RSCS 1.0 naming (Phase 0 naming freeze, DECISION_LOG D3-001). |

Nothing is classified **remove** at this stage; candidates (e.g. v2
LaTeX build byproducts `*.aux/.log/.fls` under `manuscript/`) will be
proposed by Agent 11 with justification at packaging time.

## 3. Equations — all 61 accounted for

All registry entries **RGCS-M.1 through RGCS-M.61** (61/61, census in
`V2_BASELINE_AUDIT.md` §5) are **retained verbatim** under the frozen
`RGCS-M.*` namespace: ID, symbol set, units, classification, and numeric
behaviour are immutable. RSCS work introduces a **new namespace**
(`RSCS-O.*` operators, `RSCS-C.*` coordinate/schema definitions,
`RSCS-M.*` reserved-against-collision: NOT used) rather than renumbering.
Where an RSCS operator generalizes a v2 equation (e.g. RGCS-M.23–28
two-/N-mode machinery, RGCS-M.46–48 complex modal dynamics), the new
entry must cite the RGCS-M source ID in its provenance field and carry a
consistency test proving numerical agreement on the v2 domain.

## 4. Registry and versioning rules (binding on Agents 02–11)

1. **Semantic versioning:** software `3.0.0` (pre-releases `3.0.0aN`);
   math framework `RSCS 1.0`; registry `schema_version: 2`.
2. RGCS-M.\* entries are append-only annotated, never edited numerically;
   a correction requires a new ID plus an INCONSISTENCY_REGISTER row and
   an erratum note, exactly as v2 handled QA-D-04.
3. New equations require: registry ID, units, classification
   (EST/DER/HYP/SRC/ENG), source provenance (page/equation for adapted
   material), and at least one machine test, before first use in any
   document (orchestrator integration rule).
4. No agent may redefine a symbol from `NOTATION_AND_UNITS.md`; new
   symbols go through Agent 02's frozen notation ledger.
5. Golden data (`experiments/sample_data/golden_coherence/`) is
   regenerated only with the pinned environment recorded in
   `release/PROVENANCE.json` semantics (MIG-TEST-02); cross-version float
   drift is compared with tolerance-aware checks, not byte equality, in
   any NEW v3 tests (the v2 byte-equality test is retained as-is and
   marked platform-pinned).
