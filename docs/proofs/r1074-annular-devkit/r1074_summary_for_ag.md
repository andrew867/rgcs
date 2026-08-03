# R10.74 / RGCS-ARDK-001 Implementation Summary

**Verdict:** `R10_74_GREEN_DEVKIT_SPEC_READY_PUBLICATION_HOLD`

**Fabrication readiness:** `REFUSED`

**Publication:** `PUBLICATION_HOLD`; no tag and no push.

## Bounded purpose

This implementation is a parametric development scaffold for a stationary,
37-sector annular electromagnetic field-asymmetry demonstrator. Its only
measurement claim is whether `DeltaB` magnitude and direction follow a
declared command within uncertainty and required controls. It provides no
mechanical-performance or energy-production computation.

## Authority trace

R10.73 commit `710e5947c80ea7a2299dc0a40fd63a4262891e39` is imported as an
exact, hash-pinned snapshot. The generator refuses missing, modified, or seed
inputs.

| Input | Canonical SHA-256 |
|---|---|
| `drive_table.json` | `2a6f3e111f2f52497096d4388cc6d7bc1d5033b07b4b8faf5fe3ba6a723fda9c` |
| `probe_plan.json` | `33fdbd959d42ac24b36581bec7f719f2803adda5601505ada69e1d64e6708c4e` |
| `null_masks.json` | `6746abcc1def89f5fde50b9cc49b5f1f19100fd4142577dd958c2646d9a6c0e3` |
| `bench_protocol.md` | `6f8d418b7d8ba280efe14e7ca7c3ecc0220198f25d7e77a9e5bb63b394cf158a` |

## Implemented subsystems

- Locked JSON/YAML parameter files and typed validation.
- Exact-rational annular geometry with shared PCB/fixture alignment.
- Separate KiCad-oriented Board A passive and Board B active/loading writers.
- Stationary 37-pickup phase encoder, 8-pickup compass estimator, center reference interface, and external probe authority.
- DeltaB-only PID reference, default-off runtime, interlocks, heartbeat, and SPI frame codec.
- OpenSCAD mechanical fixture scaffold with no electrical ownership.
- Receipt schema, structural refusal gate, release filter, claim firewall, FMEA, and readiness report.
- Focused acceptance suite covering positive, negative, transform, determinism, and refusal cases.

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| Repository safety | PASS | Hold asserted; scoped local changes; no tag/push |
| R10.73 authority | PASS | Source commit, blob IDs, canonical hashes, and invariant validation |
| Geometry | PASS | 37 sectors; `360/37`; 288/188 mm; `47/72` |
| PCB scaffold | PASS | Separate deterministic board files and net registry |
| Control and sensing | PASS | 37/8/center topology; DeltaB-only feedback; hard clamps |
| Bench evaluator | PASS | Missing evidence raises; complete PASS and FAIL reachable |
| Claim firewall | PASS | AST namespace audit clean; public-path exclusion live |
| Fabrication release | REFUSED | Physical/manufacturing evidence is absent |

## Verification

- Focused R10.74 acceptance: `54 passed`.
- Complete repository suite: `7919 passed, 11 skipped, 3 warnings` from
  7,930 collected tests in 19 minutes 11 seconds.
- Skips include the documented archived-environment byte-equality node; its
  portable numerical-equivalence companion passed.
- Python compilation and deterministic Board A/Board B regeneration passed.

## Negative findings

The supplied ZIP validates for 60 non-self entries. Its manifest's own listed
hash does not equal the final manifest bytes, a circular self-hash issue; no
design input depends on that entry. KiCad CLI and OpenSCAD executables were not
available locally, so native DRC, render, STEP, Gerber, drill, and STL checks
remain blocked.
