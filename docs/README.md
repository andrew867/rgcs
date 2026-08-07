# docs/ — index

Documents accumulate fast across a programme that has run from v2.0.0 to v8.3.0.
There are ~99 files here plus ~30 subdirectories. **This page is the map.**

If you read only three: [QUICKSTART](QUICKSTART.md) ·
[ARCHITECTURE](ARCHITECTURE.md) · [CLAIM_BOUNDARIES](CLAIM_BOUNDARIES.md)

## Conventions

Files are marked **(v2, frozen record)** where they describe the v2.0.0 baseline and
are not updated; **(living register)** where they are append-only and current; and
**(v3)/(v4)/(v5)/(v8)** by the programme that authored them.

**Historical documents are not corrected in place.** Where a later programme found an
earlier document wrong, the correction is stated *inline next to the original claim*
rather than replacing it — see `v4/cspc/CSCP_FINDINGS.md` §5 for the pattern. A
document's age is not evidence against it, but its date matters.

**If two documents disagree**, resolution order is:
[BLOCKERS_B01_B07](BLOCKERS_B01_B07.md) and [CLAIM_BOUNDARIES](CLAIM_BOUNDARIES.md)
first, then the current-practice sections below, then per-generation archives, then
[archive/](archive/) — which is historical only and never authoritative.

---

## Start here — what the project does and does not claim

| File | What it is |
|---|---|
| [`../SCIENTIFIC_BOUNDARIES.md`](../SCIENTIFIC_BOUNDARIES.md) | what the project has **not** established; the measured evidence distribution |
| [`../NON_CLAIMS.md`](../NON_CLAIMS.md) | everything not claimed, including claims withdrawn after review |
| [CLAIM_BOUNDARIES](CLAIM_BOUNDARIES.md) | (v8) claim classes; verified vs not, for the map lane |
| [BLOCKERS_B01_B07](BLOCKERS_B01_B07.md) | (v8) the seven open problems, unsoftened |
| [`../negative_results/`](../negative_results/) | refusals published as results |
| [NEGATIVE_RESULTS](NEGATIVE_RESULTS.md) | (living register) |
| [v51/V5_1_FINAL_OPERATOR_REPORT](v51/V5_1_FINAL_OPERATOR_REPORT.md) | what exists, what failed, what remains unmeasured |
| [v51/R8_PRIOR_ART_REVIEW](v51/R8_PRIOR_ART_REVIEW.md) | three adversarial literature reviews and what they demolished |
| [v51/RGCS_RELEASE_AND_DISCLOSURE_TIMELINE](v51/RGCS_RELEASE_AND_DISCLOSURE_TIMELINE.md) | every release and the public/private disclosure record |

## Start here — using the software

| File | What it is |
|---|---|
| [QUICKSTART](QUICKSTART.md) | (v8) clone to a working map in five minutes |
| [USER_MANUAL](USER_MANUAL.md) | (v8) the map workbench, with real screenshots |
| [USER_GUIDE](USER_GUIDE.md) | (v2, frozen) the original crystal workflow |
| [USER_GUIDE_V4](USER_GUIDE_V4.md) | (v4) the multiphysics workflow |
| [ARCHITECTURE](ARCHITECTURE.md) | (v2, frozen + v3 addendum) how the packages fit together |
| [LAB_MANUAL](LAB_MANUAL.md) | working against real hardware |
| [CONTRIBUTOR_ROADMAP](CONTRIBUTOR_ROADMAP.md) | where help is wanted |

## Start here — Design Studio

The task-first entry points for the desktop workbench (`rgcs-workbench`).

| Task | Document |
|---|---|
| Install RGCS | [`../INSTALL.md`](../INSTALL.md) |
| Launch Design Studio | [user/DESIGN_STUDIO](user/DESIGN_STUDIO.md) |
| Validate a crystal | [user/CRYSTAL_VALIDATOR](user/CRYSTAL_VALIDATOR.md) |
| Generate a certification sheet | [user/CERTIFICATION_SHEETS](user/CERTIFICATION_SHEETS.md) |
| Generate a Phyrll generator holder | [user/PHYRLL_GENERATOR_DESIGNER](user/PHYRLL_GENERATOR_DESIGNER.md) |
| Design coils and pulse settings | [user/COIL_PULSE_DESIGNER](user/COIL_PULSE_DESIGNER.md) |
| Design an annular ring prototype | [user/ANNULAR_RING_DESIGNER](user/ANNULAR_RING_DESIGNER.md) |
| Use frequency keys | [user/FREQUENCY_KEYS](user/FREQUENCY_KEYS.md) |
| Open Advanced Mode | [user/ADVANCED_MODE](user/ADVANCED_MODE.md) |
| Packaging (developers) | [developer/PACKAGING](developer/PACKAGING.md) |

Historical guides remain below; the Design Studio user docs are the current
task-first entry points.

## Governance

| File | What it is |
|---|---|
| [SCIENTIFIC_CLASSIFICATION_POLICY](SCIENTIFIC_CLASSIFICATION_POLICY.md) | (v2, still binding) the five-label claim system |
| [DECISION_LOG](DECISION_LOG.md) | (living register) every binding decision, D3-001 onward — the "why" |
| [CLAIM_REGISTER](CLAIM_REGISTER.md) | (living register) claims with pre-registered failure conditions |
| [ROADMAP_TO_FALSIFICATION](ROADMAP_TO_FALSIFICATION.md) | hypothesis → protocol mapping |
| [TRACEABILITY_MATRIX](TRACEABILITY_MATRIX.md) | (living register) deliverable → module → test |
| [DEFECT_REGISTER](DEFECT_REGISTER.md) · [INCONSISTENCY_REGISTER](INCONSISTENCY_REGISTER.md) · [RISK_REGISTER](RISK_REGISTER.md) · [ASSUMPTIONS](ASSUMPTIONS.md) | (living registers) |
| [PROGRAMME_PROGRESS](PROGRAMME_PROGRESS.md) | (v3) the execution ledger |

## Provenance and sources

| File | What it is |
|---|---|
| [SOURCE_REGISTER](SOURCE_REGISTER.md) · [SOURCE_EVIDENCE_LEDGER](SOURCE_EVIDENCE_LEDGER.md) | source rows (RG-*, SRC-3-*), preserved not endorsed |
| [ADAPTATION_MATRIX](ADAPTATION_MATRIX.md) · [EXCLUSION_MATRIX](EXCLUSION_MATRIX.md) · [CONCEPT_EXTRACTION](CONCEPT_EXTRACTION.md) | (v3) what crossed from sources, what is forbidden |
| [OA_CONVERGENCE_LEDGER](OA_CONVERGENCE_LEDGER.md) | (v8) hard-SF material as a prior, never as evidence |
| [SOURCE_DELTA_REPORT](SOURCE_DELTA_REPORT.md) | (v2, frozen record) |

---

## Coordinates & mapping (v8)

The V1 Earth-root map workbench — `r1053`, `rgcs_coordinate`, `cwatlas`.

| File | What it is |
|---|---|
| [V1_COORDINATE_SYSTEM](V1_COORDINATE_SYSTEM.md) | the whole pipeline on one page |
| [VARIABLE_LENGTH_CODEC](VARIABLE_LENGTH_CODEC.md) | direct octal lane, staged grammar, the wide-envelope gate |
| [EARTH_ROOT_V1](EARTH_ROOT_V1.md) | frame D_V1, SAA phase hand, the pinning problem |
| [MAP_PATH_POLYGON_GUIDE](MAP_PATH_POLYGON_GUIDE.md) | how path and polygon geometry is computed and cross-checked |
| [15KM_CELL_FIELD_ENVELOPE_MODEL](15KM_CELL_FIELD_ENVELOPE_MODEL.md) | the cell-scale reading **and its null** |
| [FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS](FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md) | epoch gating, Ba-130, SPICE frame hygiene |
| [RSCS_COORDINATE_SCHEMA](RSCS_COORDINATE_SCHEMA.md) | (v3) the typed coordinate record |
| [cwatlas/](cwatlas/) · [r1019/](r1019/) | CW Atlas, geocoder, and the R10.19 addressing work |

## Crystal & resonator physics

The lane RGCS is named for.

| File | What it is |
|---|---|
| [RGCS_CRYSTAL_APPLICATION](RGCS_CRYSTAL_APPLICATION.md) | (v3) the crystal workflow end to end |
| [CANONICAL_110MM_CASE_STUDY](CANONICAL_110MM_CASE_STUDY.md) | the worked reference specimen |
| [EYE_METHODOLOGY](EYE_METHODOLOGY.md) | eye-node diagnostics and their limits |
| [CALIBRATION_GUIDE](CALIBRATION_GUIDE.md) · [BENCH_HARDWARE](BENCH_HARDWARE.md) | calibrating; what sits on the bench |
| [MEASUREMENT_PROTOCOL](MEASUREMENT_PROTOCOL.md) · [EXPERIMENT_PROTOCOL](EXPERIMENT_PROTOCOL.md) | how measurements are taken |
| [EXPERIMENTAL_PROGRAMME](EXPERIMENTAL_PROGRAMME.md) | the programme of experiments |
| [COIL_LASER_TIMING_AND_PHASE](COIL_LASER_TIMING_AND_PHASE.md) | excitation timing |
| [OPTICAL_AND_NONRECIPROCAL_COUPLING](OPTICAL_AND_NONRECIPROCAL_COUPLING.md) | optical / nonreciprocal coupling |
| [COHERENCE_METRICS](COHERENCE_METRICS.md) · [COHERENCE_TEST_MATRIX](COHERENCE_TEST_MATRIX.md) · [DYNAMIC_COHERENCE_SPEC](DYNAMIC_COHERENCE_SPEC.md) | coherence definitions and tests |
| [SAFETY_AND_ARTIFACT_CHECKLIST](SAFETY_AND_ARTIFACT_CHECKLIST.md) | **read before running hardware** |
| [surface_wave/](surface_wave/) · [r1015a/](r1015a/) | annular surface-wave model; Scale A mechanical lane |
| [generated/OPTICAL_MECHANISM_COMPARISON](generated/OPTICAL_MECHANISM_COMPARISON.md) | GENERATED — regenerate via `tools/generate_optical_comparison.py` |

## Mathematics and notation

| File | What it is |
|---|---|
| [RSCS_MATHEMATICAL_MODEL](RSCS_MATHEMATICAL_MODEL.md) · [RSCS_OPERATOR_REGISTRY](RSCS_OPERATOR_REGISTRY.md) | (v3) the typed framework in prose |
| [RSCS_NOTATION_LEDGER](RSCS_NOTATION_LEDGER.md) | (v3, frozen + governed appends) every RSCS id and symbol |
| [MATHEMATICAL_MODEL](MATHEMATICAL_MODEL.md) · [NOTATION_AND_UNITS](NOTATION_AND_UNITS.md) | (v2, frozen) the 61 baseline equations and symbol authority |
| [DIMENSIONAL_ANALYSIS](DIMENSIONAL_ANALYSIS.md) | (v2, frozen record) |
| [HG_RSCS_MEMORY_ARCHITECTURE](HG_RSCS_MEMORY_ARCHITECTURE.md) · [NHT_HAL_RSCS_MAPPING](NHT_HAL_RSCS_MAPPING.md) | (v3) the memory architecture lane |

## Engineering and APIs

| File | What it is |
|---|---|
| [CORE_API_SPEC](CORE_API_SPEC.md) · [V4_API_REFERENCE](V4_API_REFERENCE.md) | the programming interfaces |
| [V4_MODELLING_GUIDE](V4_MODELLING_GUIDE.md) · [MODELLING_ROADMAP](MODELLING_ROADMAP.md) | modelling practice and direction |
| [DATA_SCHEMA](DATA_SCHEMA.md) · [DATA_PIPELINE](DATA_PIPELINE.md) | data in, data out |
| [DESKTOP_ARCHITECTURE](DESKTOP_ARCHITECTURE.md) · [DESKTOP_PRODUCT_SPEC](DESKTOP_PRODUCT_SPEC.md) | the PySide6 workbench |
| [SOFTWARE_HARDWARE_ARCHITECTURE](SOFTWARE_HARDWARE_ARCHITECTURE.md) | software/hardware split |
| [SPEC](SPEC.md) · [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) · [MILESTONE](MILESTONE.md) | (v2, frozen record) |
| [workbench/](workbench/) · [developer/](developer/) · [user/](user/) · [guide/](guide/) | per-audience guides |

## QA, verification and audits

| File | What it is |
|---|---|
| [TEST_PLAN](TEST_PLAN.md) · [VALIDATION_PLAN](VALIDATION_PLAN.md) · [ACCEPTANCE_CRITERIA](ACCEPTANCE_CRITERIA.md) | how the software is checked, and what "done" means |
| [STATISTICAL_ANALYSIS_PLAN](STATISTICAL_ANALYSIS_PLAN.md) | pre-registered analysis |
| [QA_REPORT_V3](QA_REPORT_V3.md) · [CLAIM_AUDIT_V3](CLAIM_AUDIT_V3.md) · [REPRODUCIBILITY_AUDIT_V3](REPRODUCIBILITY_AUDIT_V3.md) · [LAYOUT_QA_REPORT_V3](LAYOUT_QA_REPORT_V3.md) | (v3) adversarial QA |
| [QA_REPORT](QA_REPORT.md) · [CLAIM_AUDIT](CLAIM_AUDIT.md) · [REPRODUCIBILITY_AUDIT](REPRODUCIBILITY_AUDIT.md) | (v2, frozen record) — same names minus the suffix; deliberate, not duplication |
| [V2_BASELINE_AUDIT](V2_BASELINE_AUDIT.md) · [V2_TO_V3_MIGRATION_MAP](V2_TO_V3_MIGRATION_MAP.md) | the frozen baseline and the migration |

## Releases and publication

| File | What it is |
|---|---|
| [releases/](releases/) | per-release notes, newest first |
| [RELEASE_CHECKLIST](RELEASE_CHECKLIST.md) | the gate before shipping |
| [RELEASE_NOTES_V4](RELEASE_NOTES_V4.md) · [RELEASE_NOTES_V4_1](RELEASE_NOTES_V4_1.md) | (v4) |
| [DOI_RELEASE_GUIDE](DOI_RELEASE_GUIDE.md) · [ZENODO_METADATA](ZENODO_METADATA.md) · [ZENODO_METADATA_V4](ZENODO_METADATA_V4.md) | minting a DOI |
| [PUBLICATION_READINESS_REPORT](PUBLICATION_READINESS_REPORT.md) · [FINAL_PUBLICATION_REPORT](FINAL_PUBLICATION_REPORT.md) · [GITHUB_PUBLICATION_REPORT](GITHUB_PUBLICATION_REPORT.md) | publication gates |
| [PUBLIC_COMMUNICATION](PUBLIC_COMMUNICATION.md) | how to talk about this work publicly |
| [RGCS_V4_TECHNICAL_MANUSCRIPT](RGCS_V4_TECHNICAL_MANUSCRIPT.md) | (v4) the technical manuscript |

---

## Per-generation directories

Each generation kept its own working set. **Historical** — current practice is above.

| Directory | Generation |
|---|---|
| [v4/](v4/) · [plans-v4/](plans-v4/) | RGCS v4 / RSCS 2.0 (~128 files under `v4/`) |
| [v5/](v5/) · [v51/](v51/) · [v52/](v52/) · [v59/](v59/) | v5 series |
| [v6/](v6/) · [v7/](v7/) · [v8/](v8/) | v6–v8 series |
| [r109/](r109/) · [r1010/](r1010/) · [r1011/](r1011/) · [r1012/](r1012/) · [r1013/](r1013/) · [r1015a/](r1015a/) · [r1019/](r1019/) | the R10.x research chain |
| [program/](program/) · [community/](community/) | programme records; community material |
| [proofs/](proofs/) · [generated/](generated/) · [images/](images/) · [screenshots/](screenshots/) · [assets/](assets/) | bundles, generated output, media |
| [archive/](archive/) | **superseded documents, with correction banners** |

## Agent handoffs (historical)

[AGENT_03](AGENT_03_HANDOFF.md) · [AGENT_06](AGENT_06_HANDOFF.md) ·
[AGENT_07](AGENT_07_HANDOFF.md) · [AGENT_08](AGENT_08_HANDOFF.md) ·
[AGENT_09](AGENT_09_HANDOFF.md) — dated snapshots written at each stage boundary.
Historical statements in them (e.g. id counts at the time) are accurate *as of their
date*; the current truth is always the registries.
