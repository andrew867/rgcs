# Agent 06 Handoff — Optical, Photon–Phonon, and Nonreciprocal Coupling

**Date:** 2026-07-15. **Status: COMPLETE, GREEN.** Consumers: Agent 07
(experiment design), Agent 08 (desktop/hardware views), Agent 09
(manuscripts), Agent 10 (QA).

## What exists now

- **Coordinates:** `OpticalCarrier` (RSCS-C.16), `DirectionalPropagation`
  (RSCS-C.17) in `rscs_core.coordinates.optical`; Jones↔Stokes conversions
  on `PolarizationState` (C.9): `from_jones(ex, ey)` / `.jones`.
- **Operators:**
  - `rscs_core.propagation`: `dispersion_phase`, `dispersion_group_delay`
    (O.18); `directional_betas`, `beating_length_mm` (O.23).
  - `rscs_core.coupling`: `overlap_integral`, `mode_conversion` (O.19);
    `state_dependent_susceptibility`, `nonreciprocal_metrics` (O.22).
  - `rscs_core.observation`: `autler_townes_response`, `is_strong_coupling`
    (O.20); `critical_coupling_transmission`, `is_critically_coupled`
    (O.21).
  - All re-exported by `rscs_core.operators`; `OPERATORS` map now covers
    O.1–O.23 (the facade also picked up the previously missing
    O.14–O.17 rows).
- **Crystal application:** `rgcs_core.optics` — quartz n_o/n_e,
  photoelastic constants, Snell, OPL/phase, `ray_to_target` (entry facet →
  geometric_center/predicted_node/measured_node as DISTINCT targets),
  `photoelastic_index_shift`, `acousto_optic_m2`,
  `quartz_acousto_optic_m2` (uses Agent 05 anisotropic X speed).
- **Schema:** `experiments/schemas/optical_probe.schema.json` (+ example,
  registered in `validate.py`, validates green). Laser class ≤ 3R,
  power ≤ 5 mW, interlock metadata; direction + reversal-pair id; control
  enum; mechanism predictions with classification.
- **Generated:** `docs/generated/OPTICAL_MECHANISM_COMPARISON.md` from the
  frozen provenance YAMLs (`tools/generate_optical_comparison.py`;
  determinism pinned by a unit test).
- **Docs:** `docs/OPTICAL_AND_NONRECIPROCAL_COUPLING.md` (spine of the
  optical chapters); notation ledger §4c; DECISION_LOG D6-001..003;
  registry 40 ids; TRACEABILITY_MATRIX §Agent 06; CLAIM_REGISTER
  H-20..H-23.

## Binding rules downstream agents inherit

1. **Reciprocity null (D6-003).** Unbiased passive quartz optics is
   reciprocal. H-21/H-23 are *pre-registered nulls*: design experiments to
   try to refute the null, and treat any surviving asymmetry as HYP pending
   a conventional-mechanism audit. Never present the null expectation as a
   deficiency.
2. **No device-value import.** Isolation dB, insertion loss, bandwidth
   figures from SRC-3-01..06 stay in the comparison table; they never enter
   a quartz prediction.
3. **Selection rules are conjunctive.** O.19 blocks conversion when ANY of
   frequency/momentum/parity/overlap fails; do not weaken this in an
   experiment design.
4. **ATS↔coupled-mode mapping is fixed:** G = 2π·(2g). Regression-pinned;
   any lineshape fit must use it.

## For Agent 07 (next)

- Use the schema's control enum + reversal pairs as the optical branch of
  the control matrix; H-20..H-23 rows are ready to receive protocols.
- Coupling budgets: `critical_coupling_transmission` defines the
  drive/readout matching language; `is_strong_coupling` the resolvability
  threshold.
- The intensity-modulation block (`synchronized_to: master_clock`) is the
  hook for the Agent 07 master-clock/laser-trigger architecture.
- Node-menu falsification rows H-2x: node definitions 4–8 of the crystal
  application §3 still need their protocol rows (Agent 05 flag, unchanged).

## For Agent 08

- Optical-path/phase-delay views: consume `ray_to_target` output
  (direction, lengths, transit time, phase) and O.18 phases.
- `jsonschema`/`referencing` are required by `experiments/schemas/
  validate.py` but are NOT declared in pyproject dev extras — declare them
  (packaging fix, goes with V2-PKG-01 family).

## Test state after Agent 06

Full suite: **347 passed, 2 failed**; zero new regressions. The 2 failures
are the documented frozen-baseline pair V2-WIN-01 (zip arcname backslashes,
`test_step_7_reproducibility_bundle`) and NR3-001
(`test_generator_deterministic`, Linux-generated goldens). Note: 2 of the
previously 4 inherited failures were missing-`jsonschema` artifacts and now
PASS after installing `jsonschema`/`referencing` for schema validation —
an environment fix, not a code change; Agent 08 must declare both in
pyproject (V2-PKG-01 family). Frozen paths verified untouched:
`git diff --stat 715486b HEAD -- archive/v2.0.0` empty.
