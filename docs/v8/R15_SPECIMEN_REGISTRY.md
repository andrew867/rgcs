# R15 P04 — Crystal and Specimen Registry

**Tranche:** T2 Specimen Authority · **Module:** `r15/specimens.py` ·
**Tests:** `tests/v8/test_specimens.py` · **Receipt:**
`docs/v8/receipts/P04.json`

## What this is

The authority for **what was in the holder**. It creates typed, immutable,
content-hashed `SpecimenRecord` entries for quartz, glass controls, PCB
disks, metal disks and synthetic specimens; tracks their revision history;
and moves them through the lifecycle a real specimen passes:

```
REGISTERED → MEASURED
REGISTERED → DAMAGED / QUARANTINED → RETIRED (terminal)
```

Nothing here is measured. No specimen is cut, weighed, mounted, oriented
or scanned. The registry records what a specimen *would* be specified by
and refuses every promotion of that description into a measurement.

## The load-bearing distinction: registered ≠ measured

Registering a specimen records **metadata** — material, cut, dimensions
and tolerances, mass, provenance/lot, surface finish, defects. That is a
description, not an acquisition.

- A specimen with **no bound physical artifact** is a `SOURCE_CLAIM`
  (or a `SYNTHETIC_FIXTURE` when it is fabricated). It is **never** a
  `PHYSICAL_MEASUREMENT`.
- `refuse_specimen_as_measured(record)` raises `ClaimError` rather than let
  a described specimen be read as measured.
- `SpecimenRegistry.promote_to_measured(...)` refuses without bound
  artifacts, refuses a missing dimension, refuses an unknown mass, and
  **blocks the `REAL` acquisition path** — no hardware or real specimen
  exists in this environment, so a real physical measurement is a
  `BLOCKED_MISSING_INPUT`, not a result. Synthetic / replay /
  fault-injection artifacts are accepted and the specimen stays visibly
  non-physical (`SYNTHETIC_FIXTURE` / `SYNTHETIC_OBSERVATION`).

## Every field carries its epistemic status

A `Quantity` is tagged `MEASURED`, `NOMINAL`, `INFERRED` or `UNKNOWN`:

- An **unknown** value stays unknown — it carries `value=None` and cannot
  smuggle in a number.
- A **nominal** or **inferred** value cannot be read as measured;
  `require_measured(q)` raises for anything but `MEASURED`.
- Only a `MEASURED` quantity may carry an uncertainty.
- **Density** is `INFERRED` from mass and disk geometry
  (`ρ = m / (π (d/2)² t)`), never observed, and collapses to `UNKNOWN` if
  any input is unknown.

## Materials, modes, states

| Group | Values |
|---|---|
| Material | `alpha-quartz`, `glass-control`, `pcb-disk`, `metal-disk`, `synthetic` |
| Field class | `MEASURED`, `NOMINAL`, `INFERRED`, `UNKNOWN` |
| Acquisition mode | `REAL`, `REPLAY`, `SYNTHETIC`, `FAULT_INJECTION` (kept distinct) |
| Lifecycle state | `REGISTERED`, `MEASURED`, `DAMAGED`, `QUARANTINED`, `RETIRED` |
| Handedness | `LEFT` (P3₂21), `RIGHT` (P3₁21), `NOT_APPLICABLE`, `UNKNOWN` |

**Synthetic specimens are visibly synthetic.** A specimen whose material is
`SYNTHETIC`, or whose artifacts were produced in `SYNTHETIC` /
`FAULT_INJECTION` mode, reports the `SYNTHETIC_FIXTURE` claim class and
flags `"synthetic": true` in its record.

## Immutability, revision history, content hash

- `specimen_id` is a deterministic, seeded, UUID-like id
  (`derive_specimen_id`) — no wall-clock, no randomness — and is **immutable
  across every revision**.
- Each lifecycle change appends a new frozen `SpecimenRecord` with an
  incremented `revision` and a `revision_reason`; prior records are never
  mutated. `RETIRED` is terminal.
- `content_hash()` is the SHA-256 of the canonical (sorted-key) record body.
  `verify_record(dict)` recomputes it; **any tamper with any field flips the
  hash** and verification fails.

## Crystallographic frame is reused, not reinvented

Quartz orientation is tied to the alpha-quartz lattice frame of
`r13.crystalframe` (`Orientation.quartz(...)`):

- lattice constants `a ≈ 4.913 Å`, `c ≈ 5.405 Å` as
  **CONVENTIONAL_LITERATURE** (quoted, not measured here);
- the enantiomorphic space-group pair `P3₁21 / P3₂21`;
- a cut plane `(hkl)` whose reciprocal-space normal `G(hkl)` is
  established-physics geometry via `LatticeFrame.reciprocal_vector`, not a
  diffraction result. The `(0,0,0)` plane is refused.

Amorphous / isotropic specimens (glass, metal) carry no crystallographic
frame; asking for one refuses.

## Required tests (all green)

- **Unknown remains unknown** — an `UNKNOWN` quantity has no value and none
  can be smuggled in.
- **Nominal cannot masquerade as measured** — `require_measured` refuses a
  nominal / inferred / unknown value.
- **Damage creates a new state** — `mark_damaged` appends a `DAMAGED`
  revision with a new defect; identity and history are preserved.
- **Synthetic specimens are visibly synthetic** — flagged in the record and
  in the claim class.
- Plus: registered ≠ measured, promotion without artifacts refused, `REAL`
  blocked, missing dimension refused, hash tamper detected, schema
  conformance, and determinism.

`pytest tests/v8/test_specimens.py -q` → **29 passed**.

## Claim cap

`measured_here = "nothing"`; `physical_validation =
PHYSICAL_VALIDATION_NOT_CLAIMED`. The strongest claim class any record
reaches from this module is `SYNTHETIC_FIXTURE` /
`SYNTHETIC_OBSERVATION` / `SOURCE_CLAIM`. No specimen reaches a measurement
class, because real acquisition does not exist in this environment.
