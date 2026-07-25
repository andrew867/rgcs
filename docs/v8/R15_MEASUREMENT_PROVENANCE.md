# R15 P02 — Measurement Provenance

**Tranche:** T1 Instrument Authority
**Modules:** `r15/artifacts.py`, `r15/provenance.py`
**Status:** COMPLETE — non-physical work only; no physical measurement performed.

## What this phase builds

A measurement-provenance authority that binds every reported value to the
evidence and the conditions that produced it. It has two layers.

### Immutable artifacts (`r15/artifacts.py`)

A `MeasurementArtifact` is the raw, write-once evidence a measurement lane
emits (a trace, a spectrum, an image, a log). It carries the raw bytes
themselves and its `content_hash` is the SHA-256 of exactly those bytes, so:

- **A one-byte change alters the hash.** `fault_injected(...)` flips a single
  byte and yields a different content hash; the original is never mutated.
- **The record is immutable.** It is a frozen dataclass whose payload is an
  immutable `bytes` object. `to_manifest()` always reports `immutable = True`
  and conforms to `r15/schemas/measurement_artifact.schema.json`.
- **Every artifact binds an instrument and a calibration.** Construction is
  refused without a non-empty `instrument_id` and `calibration_id`.
- **Acquisition modes stay distinct** — `REAL`, `REPLAY`, `SYNTHETIC`,
  `FAULT_INJECTION`. No `REAL` device exists in this environment, so every
  artifact built here is software output and is never a physical measurement.

### Provenance-bound observations (`r15/provenance.py`)

An `ObservationRecord` binds one reported quantity to its full provenance:
instrument, calibration, specimen, fixture, protocol, clock, environment, the
passed-in start/end timestamps, an uncertainty budget, the immutable source
artifacts (by content hash), and a `DerivationGraph` from raw bytes through
each analysis step to the value. It conforms to
`r15/schemas/observation_record.schema.json`.

- **Lineage is hashed.** `lineage_hash` is a canonical hash over the source
  artifacts' content hashes and every derivation step. Tamper with any source
  artifact and `verify_lineage(...)` returns `False`: derived data cannot be
  silently re-based onto different evidence.
- **Derived data require their sources.** `build_observation(...)` refuses an
  observation with no source artifacts.
- **Bindings cap the claim.** The claim class and evidence level follow from
  the acquisition mode and the bindings actually present, through
  `r15.claims.evidence_cap` and `EvidenceBindings`. A missing calibration,
  clock, raw artifact, or any other required binding caps the evidence below
  a physical measurement (E4).

## Evidence ladder and the caps that bite here

| Case | Claim class | Evidence |
| --- | --- | --- |
| Fully bound, synthetic source | `SYNTHETIC_OBSERVATION` | E2 |
| Missing a binding (e.g. clock, calibration) | capped below physical | E3 (software ceiling) |
| `REAL` + every binding (in principle only) | `PHYSICAL_MEASUREMENT` | E4 |

The third row is unreachable here: no `REAL` device exists, so every
observation this module builds is a `SYNTHETIC_OBSERVATION` at best. The row
is retained so the ladder stays honest about what is still missing.

## Timestamps are passed in, never read from a clock

`start_epoch` and `end_epoch` are always supplied by the caller; the clock
binding is formed from them. `r13.serialize.refuse_wallclock_timestamp`
guards the anti-pattern. As a result a record serialises identically on
every run and its lineage hash is reproducible (deterministic replay).

## What this phase reuses (extends, does not duplicate)

- `r13.serialize` — canonical deterministic serialization and content hashing
  for manifests, derivation graphs, and lineage hashes; the wall-clock refusal.
- `r15.claims` — the claim taxonomy, the evidence ladder, `EvidenceBindings`,
  `evidence_cap`, `cap_claim_to_software`, and `refuse_synthetic_as_physical`.

## What this phase does not say

Nothing here is measured. Every source artifact is software-produced, so even
a fully bound observation is a `SYNTHETIC_OBSERVATION`, capped below a physical
measurement; a missing binding caps it further. A matching content or lineage
hash proves the bytes are unaltered (integrity) and that a value was derived
from exactly those bytes — never who produced them or that they were
physically acquired. There is no `PHYSICAL_MEASUREMENT`, and no
`PHRYLL_DETECTED`, anywhere in this phase.

## Tests

`tests/v8/test_measurement_provenance.py` — 27 tests, all passing:
schema conformance for both records; one-byte changes alter hashes; identical
bytes hash identically; replay does not mutate the original; derived data
require source artifacts; tamper of any source artifact breaks the lineage;
missing clock and missing calibration each cap evidence below physical; the
`REAL`+complete path is physical only in principle; determinism/replay
reproduce identical records; and both module reports claim `measured_here =
"nothing"`.
