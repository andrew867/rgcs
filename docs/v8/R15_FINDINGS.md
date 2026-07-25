# R15 — Experimental Phase Infrastructure

**Authority:** RGCS R15 / v8.0.0 (candidate)
**Scope:** the `r15/` package (33 phase modules + a governance core + 11 JSON
schemas), 36 phase receipts under `docs/v8/receipts/`, and the phase ledger.
**Baseline:** branch `v800-r15`, cut from `v7.0.0` (`59667f9`).
**Related code / tests:** `r15/*.py`, `tests/v8/test_*.py`.
**Verdict:** `R15_GREEN_EXPERIMENTAL_INFRASTRUCTURE_READY_NO_PHYSICAL_CLAIMS_ADVANCED`.

---

## What R15 is

R15 turns the completed R13 software/simulation architecture into an
**instrument-ready, calibration-bound, uncertainty-aware experimental
platform** — without requiring the operator to own or buy any laboratory
equipment. It executes all 36 phases of the pack across eight tranches:

- **T1 Instrument Authority** (P01–P03): an instrument registry with one
  interface over REAL / REPLAY / SYNTHETIC / FAULT_INJECTION modes, a
  measurement-provenance authority, and an environmental ledger feeding an
  eleven-component error budget.
- **T2 Specimen Authority** (P04–P06): a crystal/specimen registry, a
  low-cost orientation solver (alias-limited by symmetry), and a fixture
  registry whose shifts are booked as ordinary `FIXTURE_EFFECT`s.
- **T3 Experimental Execution** (P07–P09): a frozen executable-protocol
  engine, a pre-committed randomization engine, and a blind-operator mode.
- **T4 Evidence Engine** (P10–P12): an immutable hash-chained measurement
  ledger, the ordinary-explanation firewall (eleven attack detectors), and a
  residual classifier whose ceiling is `UNEXPLAINED_INSTRUMENT_RESIDUAL`.
- **T5 Cross-Domain Measurement** (P13–P18): six measurement lanes
  (mechanical, electrical, optical, thermal, magnetic/RF, clock/phase), each
  with all four device modes and a full error budget.
- **T6 Statistical Firewall** (P19–P24): prospective-prediction registry,
  sealed holdout authority, null-model registry (power on planted data),
  circularity/leakage audit, multiple-comparison + sequential control, and
  independent-replication receipting.
- **T7 Hardware Automation** (P25–P30): a DDS recipe compiler, an ESP32
  embedded-runner twin, an automated sweep controller, live impedance/BVD
  fitting, a real-time mode tracker, and a laser-trim planning simulator.
- **T8 Publication and Release** (P31–P36): manuscript, figure/evidence
  package, statistical appendices, non-claims register, replication package,
  and this release.

## The standing laws (all held)

- **No purchase.** Every hardware-facing lane is software-complete
  (interface + deterministic simulator + replay + fault injection + schema +
  protocol + error budget + tests + docs). Only physical acquisition is
  `PREREGISTERED_NOT_RUN` / `BLOCKED_MISSING_INPUT`.
- **Evidence, not assertion.** No observation reaches a physical class
  without instrument, calibration, specimen, fixture, protocol, clock,
  environment, timestamps, uncertainty, immutable artifacts, hashes, and
  derivation lineage. Missing any binding caps the evidence below E4.
- **No promotion.** Synthetic ↛ physical, source ↛ measurement, model ↛
  measurement, noise ↛ resonance, and unexplained residual ↛ new physics —
  each a refusal in `r15/claims.py`. There is **no `PHRYLL_DETECTED` state**;
  a residual below combined uncertainty is not anomalous.

## Non-claims

R15 establishes no new energy, no Phyrll, no spacetime modification, no
decoded destination or person-specific resonance, and no anomaly. The
strongest an unreplicated residual reaches is `UNEXPLAINED_INSTRUMENT_RESIDUAL`;
only ≥2 mutually independent, firewall-surviving replications reach
`REPLICATED_ANOMALY`, which is still not new physics. See
`docs/v8/R15_NON_CLAIMS.md`.

## R13 closure

All ten R13 handoff obligations are CLOSED by R15 phases
(`docs/v8/R15_R13_CLOSURE.csv`).

## Verdict

`R15_GREEN_EXPERIMENTAL_INFRASTRUCTURE_READY_NO_PHYSICAL_CLAIMS_ADVANCED`.
Nothing here is measured; `PHYSICAL_VALIDATION_NOT_CLAIMED` throughout.
