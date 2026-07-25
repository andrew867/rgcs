# R15 P10 — Immutable Measurement Ledger

**Tranche:** T4 Evidence Engine
**Module:** `r15/measurement_ledger.py`
**Tests:** `tests/v8/test_measurement_ledger.py`
**Receipt:** `docs/v8/receipts/P10.json`
**Verdict:** `IMMUTABLE_MEASUREMENT_LEDGER_APPEND_ONLY_HASH_CHAINED`
**Claim class:** `SOFTWARE_IMPLEMENTED` · **Measured here:** nothing · `PHYSICAL_VALIDATION_NOT_CLAIMED`

## What this is

An append-only, hash-chained ledger for runs, artifacts, derivations,
observations, and receipts. Every entry is appended and never edited in
place. The ledger is built directly on the R13 provenance layer
(`r13.serialize`): each entry becomes a `Record` whose hash is taken over its
payload, its claim class, a passed-in epoch, and the hash of the record
before it. Editing any past entry changes that record's recomputed hash and
breaks the back-link of every entry after it, so a single tampered row fails
`verify_chain` from that point onward. The ledger is tamper-**evident**, not
merely tamper-resistant.

Nothing here is measured. The ledger records provenance and integrity; a
matching content hash proves the bytes, not the physics.

## What it does

1. **Content-addressed manifests.** `Artifact.from_bytes` computes the
   SHA-256 of the exact bytes and stores it as `content_hash`. The manifest
   *is* the fingerprint: the same bytes always address the same way, and a
   single changed byte changes the address. `Artifact` is a frozen
   dataclass with `immutable=True` — a raw artifact cannot be mutated in
   place, and `immutable=False` is refused at construction.

2. **Typed artifact stages.** `ArtifactKind` separates `RAW`, `CALIBRATED`,
   `FILTERED`, `FITTED`, and `INTERPRETED`. Only `RAW` is an acquisition
   output; every later stage must be produced by a recorded `Derivation`.

3. **Software and parameters for every derivation.** `Derivation` records
   the output artifact id, the exact source artifact ids, the software name
   and version, and the parameters used — so a fit or filter links back to
   the precise bytes it consumed and the precise code that produced it. A
   derivation with no source, or no software/version, is refused.

4. **Tamper detection.** `MeasurementLedger.verify` delegates to
   `r13.serialize.verify_chain`, recomputing every record hash and
   back-link. Mutating any past entry fails verification for that entry and
   every entry downstream of it.

5. **External large-file stores through verified hashes.**
   `ExternalArtifactPointer` carries a URI plus the declared content hash
   and byte count; the bytes are not stored. `verify(data)` re-hashes the
   fetched bytes and checks the size, so an external store is trusted only
   through a matching hash, never on faith.

## Evidence bindings and capping

The ledger binds an observation to the R15 evidence bindings — instrument,
calibration, specimen, fixture, protocol, clock, environment, raw artifact,
uncertainty (`r15.claims.EvidenceBindings`). `append_observation` caps a
requested class and evidence level by what is actually bound:

- A missing binding collapses a requested measurement class to the software
  ceiling (`MODEL_PREDICTION`) via `cap_class_for_bindings`.
- The evidence level cannot reach E4 without every physical binding
  (`claims.evidence_cap`).

The **capped** values are what enter the record, so the chain itself never
carries an over-claim. A complete set of bindings in this environment is
over synthetic fixtures, so no entry is ever promoted to a physical
measurement — the capping only ever removes over-claims, never grants one.

## Determinism and the clock

Every epoch is **passed in**; the ledger never reads a wall clock. Canonical
serialization (from R13) makes the same logical entry serialize to identical
bytes, so two ledgers built from the same inputs produce identical record
hashes. `array_bytes` gives a stable, dtype- and shape-tagged byte string
for content-addressing numeric raw artifacts.

## Modes

`AcquisitionMode` keeps `REAL`, `REPLAY`, `SYNTHETIC`, and `FAULT_INJECTION`
lanes distinct on every artifact and run, so a synthetic or replayed
byte-stream is never silently read as a real one. No physical acquisition
is performed here; the worked report runs entirely in `SYNTHETIC` mode.

## Tests

`tests/v8/test_measurement_ledger.py` (18 tests):

- **Focused** — appends grow the ledger and `verify_chain` holds; tip
  hashes advance and back-link; raw artifacts are content-addressed;
  manifests carry the schema keys; derivations link a fit to its exact
  source and code.
- **Negative** — mutating a past record breaks verification downstream; a
  raw artifact is frozen and re-hashes differently on any change;
  `immutable=False` is refused; a missing-binding observation is capped
  below `PHYSICAL_MEASUREMENT` and below E4; the ledger stores only the
  capped class; external pointers reject wrong bytes (and same-size,
  wrong-hash bytes); a derivation with no source or software is refused.
- **Determinism** — identical inputs give identical content addresses and
  identical record-hash sequences; the report measures nothing and detects
  tampering.

## What this does not say

It measures nothing. A matching content hash proves the bytes are unaltered
(integrity), not who produced them (that needs a signature, per R13's
`refuse_hash_match_as_authentication`) and not that any physics occurred.
There is no physical measurement, no device, and no calibration asserted by
this module — only provenance, immutability, and honest capping.
