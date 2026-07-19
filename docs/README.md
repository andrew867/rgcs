# docs/ — index

Documents accumulate fast across a programme that has now run from
v2.0.0 to v5.1.0. There are ~88 files here, ~128 under `v4/`, and the
v5 material under `v5/` and `v51/`.

This index tells you which ones matter for what. Convention: files
marked **(v2, frozen record)** describe the v2.0.0 baseline and are not
updated; **(living register)** files are append-only and current;
**(v3)**, **(v4)**, **(v5)** files were authored during that programme.

**Historical documents are not corrected in place.** Where a later
programme found an earlier document wrong, the correction is stated
*inline next to the original claim* rather than replacing it — see
`v4/cspc/CSCP_FINDINGS.md` §5 for the pattern. A document's age is not
evidence against it, but its date matters.

## Start here — current

| File | What it is |
|---|---|
| `../SCIENTIFIC_BOUNDARIES.md` | what the project has **not** established; the measured evidence distribution |
| `../NON_CLAIMS.md` | everything not claimed, including claims withdrawn after review |
| `v51/RGCS_RELEASE_AND_DISCLOSURE_TIMELINE.md` | every release, and the public/private disclosure record |
| `v51/R8_PRIOR_ART_REVIEW.md` | three adversarial literature reviews and what they demolished |
| `v51/V5_1_FINAL_OPERATOR_REPORT.md` | what exists, what failed, what remains unmeasured |

## Start here — historical governance

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

## v4 documents (`docs/v4/`)

The v4 programme keeps its documentation under `docs/v4/`. These
describe v4.1–v4.2; the v4.6 onward material is listed in the v5
section below. Start with:

| File | What it is |
|---|---|
| `v4/RELEASE_NOTES_V4_2_0.md` | (v4.2) what is in the release, and the explicit hardware/ethics blockers |
| `v4/V4X_PROGRAMME_REPORT.md` | (v4.2) all research-expansion lanes and their honest statuses |
| `v4/V4X_COVERAGE_LEDGER.md` | GENERATED — 248/248 backlog IDs with owner/artifact/status; regenerate via `tools/v4x_coverage_ledger.py` |
| `v4/V4X_EYE_SUBMM_REFINEMENT.md` | (v4.2) the sub-mm Eye ladder: INSUFFICIENT_RESOLUTION, canonical record preserved |
| `v4/WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md` | (binding) scope statement — read before citing any result |
| `v4/EYE_NODE_COINCIDENCE_CORRECTION.md` | (v4.1) the V4C-D-001 uncertainty-aware node classification |
| `v4/V4C_DECISION_LOG.md` | (living register) v4 binding decisions, DV4C-001 onward |
| `v4/RGCS_V4_1_COMPLETION_MANUSCRIPT.md` | (v4.1) the completion manuscript |

The consciousness research lane lives in `consciousness_lane/` at the
repository root and is quarantined from quartz computation (audit check
G51); its registry documents itself.

## The coordinate / timing / evidence thread (v4.6 → v5.1)

This is where most of the project's later work lives, and it is a
different subject from the v2–v4 quartz stack. It runs across five
programme generations and its documents are split by the version that
produced them.

| Programme | Version | Documents | Headline |
|---|---|---|---|
| **CSCP** — coordinates, nulls | v4.6.0 | `v4/cspc/CSCP_FINDINGS.md`, `v4/cspc/PROGRAMME_LEDGER.md` | the simplicity metric measured human convention; its own candidate set came back CIRCULAR. Contains the DDS phase-closure result (§4) |
| **PMWR** — phase memory, worldline recovery | v4.7.0 | `v4/pmwr/PMWR_FINDINGS.md` | multipath recovery declared **textbook** by the programme itself |
| **R3** — root-space resolver | v4.7.1 | `v4/pmwr/R3_FINDINGS.md` | a root is not the first wrapped phase zero; bounded relational root lock is the ceiling |
| **R4** — exact radix codec | v4.8.x | `v4/r4/R4_FINDINGS.md` | 4096 = 8⁴ = 4⁶ = 2¹² verified exhaustively and **refused as compression** |
| **R6** — witness memory, mailbox | v4.9.0 | `v4/R6_MANUSCRIPT.md`, `v4/R6_CORRECTIONS.md` | a decaying memory is not a spacetime sensor; sovereign navigation unsupported |
| **R7** — clock link, CW null | v5.0.0 | `v5/R7_MANUSCRIPT.md`, `v5/R7_PUBLICATION_DECISION.md` | metric actuation refused by arithmetic at ≥17.8 decades |
| **R8.1** — papers, audit, commons | v5.1.0 | `v51/` (see below) | three manuscripts repositioned by prior-art review |

### `docs/v51/` — the current programme

| File | What it is |
|---|---|
| `R8_PRIOR_ART_REVIEW.md` | three adversarial reviews. **All three found substantial prior art**; two papers changed shape and one stopped being a research paper |
| `R8_KNOWLEDGE_AUDIT.md` | 271 canonical records, evidence distribution, publishability matrix. States its own incompleteness |
| `RGCS_RELEASE_AND_DISCLOSURE_TIMELINE.md` | every release; records that v3.0.0–v4.8.1 were **public under MIT** 2026-07-15→18 |
| `R8_1_FINAL_GATE_ZERO_RECEIPT.md` | verified state at release, six defects closed, two tags withdrawn before publication |
| `V5_1_PUBLICATION_DECISION.md` | `PUBLIC_OPEN_COMMONS`, superseding `PRIVATE_RC` |
| `V5_1_FINAL_OPERATOR_REPORT.md` | the twelve-question closeout |
| `RELEASE_NOTES_V5_1_0.md` | the release itself |

### Manuscripts (`papers/`)

| Path | Type after review |
|---|---|
| `papers/dds/PAPER.md` | short correspondence — closure formula is published prior art |
| `papers/coordinates/TECHNICAL_REPORT.md` | technical report, **not** a research paper |

### Commons layer (repository root)

`HUMANITY_COMMONS_CHARTER.md` · `SCIENTIFIC_BOUNDARIES.md` ·
`NON_CLAIMS.md` · `LICENSE_MAP.md` ·
`PATENT_NON_ASSERTION_INTENT.md` (policy intent, **not** a covenant).

## A note on reading order

If you are evaluating the project rather than working on it, read in
this order and stop whenever you have enough:

1. `../SCIENTIFIC_BOUNDARIES.md` — what is not established
2. `../NON_CLAIMS.md` — what is not claimed
3. `v51/R8_PRIOR_ART_REVIEW.md` — what is not novel
4. `papers/coordinates/TECHNICAL_REPORT.md` — the one integration claim
5. everything else

Three of the first four documents are about limits. That ordering is
deliberate and reflects where the project's confidence actually sits.
