# docs/ — index

Sixty-odd documents accumulate fast in a two-version programme. This
index tells you which ones matter for what. Convention: files marked
**(v2, frozen record)** describe the v2.0.0 baseline and are not updated;
**(living register)** files are append-only and current; **(v3)** files
were authored during the v3 programme.

## Start here

| File | What it is |
|---|---|
| `PROGRAMME_PROGRESS.md` | (v3) the execution ledger: every agent, commit, test count, final verdict |
| `DECISION_LOG.md` | (living register) every binding decision, D3-001 onward — the "why" |
| `SCIENTIFIC_CLASSIFICATION_POLICY.md` | (v2, still binding) the five-label claim system |
| `QA_REPORT_V3.md` | (v3) the independent adversarial QA of everything |

## Mathematics and notation

| File | What it is |
|---|---|
| `RSCS_NOTATION_LEDGER.md` | (v3, frozen + governed appends) every RSCS id and symbol |
| `RSCS_MATHEMATICAL_MODEL.md` / `RSCS_OPERATOR_REGISTRY.md` / `RSCS_COORDINATE_SCHEMA.md` | (v3) the typed framework in prose |
| `MATHEMATICAL_MODEL.md`, `NOTATION_AND_UNITS.md`, `model_registry.yaml` | (v2, frozen) the 61 baseline equations and symbol authority |
| `DIMENSIONAL_ANALYSIS.md` | (v2, frozen record) |

## Claims, evidence, provenance

| File | What it is |
|---|---|
| `CLAIM_REGISTER.md` | (living register) claims H-01..H-30 with failure conditions |
| `ROADMAP_TO_FALSIFICATION.md` | (v2, extended) hypothesis → protocol mapping |
| `NEGATIVE_RESULTS.md`, `INCONSISTENCY_REGISTER.md`, `ASSUMPTIONS.md` | (living registers) |
| `SOURCE_EVIDENCE_LEDGER.md`, `SOURCE_REGISTER.md` | source rows (RG-*, SRC-3-*) |
| `ADAPTATION_MATRIX.md`, `EXCLUSION_MATRIX.md`, `CONCEPT_EXTRACTION.md` | (v3) what crossed from sources, what is forbidden |
| `TRACEABILITY_MATRIX.md` | (living register) deliverable → module → test, per agent |
| `generated/OPTICAL_MECHANISM_COMPARISON.md` | GENERATED — regenerate via `tools/generate_optical_comparison.py` |

## v3 subject documents

`RGCS_CRYSTAL_APPLICATION.md`, `OPTICAL_AND_NONRECIPROCAL_COUPLING.md`,
`COIL_LASER_TIMING_AND_PHASE.md`, `EXPERIMENTAL_PROGRAMME.md`,
`SOFTWARE_HARDWARE_ARCHITECTURE.md`, `NHT_HAL_RSCS_MAPPING.md`,
`HG_RSCS_MEMORY_ARCHITECTURE.md`, `V2_BASELINE_AUDIT.md`,
`V2_TO_V3_MIGRATION_MAP.md`.

## QA and audits

v3: `QA_REPORT_V3.md`, `CLAIM_AUDIT_V3.md`, `REPRODUCIBILITY_AUDIT_V3.md`,
`LAYOUT_QA_REPORT_V3.md`, `DEFECT_REGISTER.md` (living, with per-agent
addenda). v2 counterparts (`QA_REPORT.md`, `CLAIM_AUDIT.md`,
`REPRODUCIBILITY_AUDIT.md`) are the frozen v2 record — same names minus
the suffix; that is deliberate, not duplication.

## Agent handoffs

`AGENT_03_HANDOFF.md` … `AGENT_09_HANDOFF.md` — dated snapshots written
at each stage boundary. Historical statements in them (e.g. id counts at
the time) are accurate *as of their date*; the current truth is always
the registries.

## v2 engineering docs (frozen record)

`SPEC.md`, `CORE_API_SPEC.md`, `DESKTOP_ARCHITECTURE.md`,
`DESKTOP_PRODUCT_SPEC.md`, `DATA_SCHEMA.md`, `TEST_PLAN.md`,
`IMPLEMENTATION_PLAN.md`, `MILESTONE.md`, `ACCEPTANCE_CRITERIA.md`,
`RISK_REGISTER.md`, `RELEASE_CHECKLIST.md`, `USER_GUIDE.md`,
`EXPERIMENT_PROTOCOL.md`, `STATISTICAL_ANALYSIS_PLAN.md`,
`COHERENCE_METRICS.md`, `COHERENCE_TEST_MATRIX.md`,
`DYNAMIC_COHERENCE_SPEC.md`, `SAFETY_AND_ARTIFACT_CHECKLIST.md`,
`ARCHITECTURE.md`, `MODEL_ASSUMPTIONS.md`, `SOURCE_DELTA_REPORT.md`,
`MILESTONE.md` — each now carries a short "v3 Agent 08 addendum" section
where the v3 programme extended it.
