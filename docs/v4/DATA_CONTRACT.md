# Data, statistics, blinding, and preregistration contract (Agent D01)

Coverage: shared infrastructure. Gates: **G29, G30, G48**.
Implementation: [`rscs2_core/research_records.py`](../../rscs2_core/research_records.py),
`rscs2_core.protocols_v4x.blind_labels`.

## The 25 record kinds

`SourceRecord`, `EquationRecord`, `FrequencyKeyRecord`,
`TimingCandidateRecord`, `GeometryMotifRecord`, `SpecimenRecord`,
`MaterialCapabilityRecord`, `ApparatusRecord`, `InstrumentRecord`,
`CalibrationRecord`, `SafetyLimitRecord`, `ExperimentProtocolRecord`,
`PreregistrationRecord`, `RunRecord`, `RawObservationRecord`,
`ParticipantRecord`, `WaterSampleRecord`, `ResultEnvelope`,
`HypothesisRecord`, `FalsificationRecord`, `ConsciousnessLayerRecord`,
`CoverageLedgerRecord`, `ProofArtifactRecord`, `DefectRecord`,
`ReleaseManifest`.

Common fields on every record: schema version, immutable ID, title,
lane, status, evidence tags, source IDs, equation IDs, units,
assumptions, uncertainty, controls, failure conditions, producer
commit, timestamps, public/private, licence, warnings.

## The measurement rule (G30)

A record tagged `MEAS` **must** carry: `raw_hash`, `instrument`,
`calibration_id`, `protocol_version`, `randomization`, `blinding`,
`safety_gate_id`. `make_record` raises if any is missing.

And the rule that matters most:

> **Synthetic data can never be relabelled measured.**

`synthetic: true` + `MEAS` → `RecordError`.
`synthetic: true` + `EXPERIMENTALLY_MEASURED` → `RecordError`.

This is enforced in the constructor, not in review, because review is
exactly what fails at 2 a.m. on release day.

**Every dataset in this repository is synthetic.** No `MEAS` record
exists. The rule has never had to stop anything, and it is in place for
the day it would.

## Blinding and randomization

`blind_labels(n, conditions, seed)` returns opaque `SAMPLE-###` labels
plus a **sealed map** held by the randomization custodian until
analysis lock. Deterministic given the seed (so it is reproducible) and
balanced across conditions (tested).

The analysis sees labels. It does not see conditions. That ordering is
the whole mechanism.

## Preregistration

Every campaign carries a `PREREG-<campaign>` id with primary and
secondary outcomes declared **before** data exist. The analysis plan
(FFT peak, Q, ring-down, control subtraction, look-elsewhere model) is
part of the protocol record, not a later choice.

Optional stopping, hidden exclusions, and post-hoc outcome swaps are
the failure modes this exists to prevent, and each is named as a QA
attack in [V4X_QA_FINAL_VERDICT.md](V4X_QA_FINAL_VERDICT.md).

## Statistics

- **Multiple comparisons.** Integrated with the frequency
  look-elsewhere model — see
  [NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md](NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md).
  Significance is never computed on a post-selected peak without the
  search space.
- **Null equivalence.** A null needs a minimum detectable effect to
  mean anything; "we saw nothing" without a power statement is not a
  result.
- **Hierarchical/repeated measures.** Within-specimen repeats and
  between-specimen variation are separate variance components.
- **Bayes factors** only with declared priors.

## Negative results (G48)

A null is registered, not deleted. `EXPERIMENTALLY_NULL` is a
first-class status, and ORPHAN-016 preserves the corpus's own recorded
nulls. **A null result is not a failed project.** Deleting nulls is
how a record becomes a highlight reel.

## Synthetic DAQ validation (G29)

`synth_ring_down()` plants a known f₀ and Q; `analyze_ring_down()`
recovers them (f₀ ±1 Hz, Q ±15% at 1% noise). The pipeline is
validated against known truth before it is ever pointed at unknown
data — and its output carries no `MEAS` tag, so the caller must supply
provenance deliberately.
