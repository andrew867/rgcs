# Agent 03 — Handoff

**Agent:** 03, RSCS Mathematical Core and Conservative Extension.
**Date:** 2026-07-14. **Verdict: GREEN.**

## Commits (branch `main`, on top of Agent 02 `af0b22f`)

| Hash | Content |
|---|---|
| `5048687` | rscs_core backbone: coordinates, operators, embedding, registry, units |
| `c4cde1c` | RSCS test suite (unit/property/regression/adversarial); firewall + phase-wrap fixes |
| `a1cdd80` | RSCS docs: mathematical model, operator registry, coordinate schema, traceability, decision log |
| (this doc) | Agent 03 handoff |

## Files added

- `rscs_core/units.py`, `rscs_core/__init__.py` (populated),
  `rscs_core/registry/` (`__init__.py` firewall + `rscs_registry.yaml`),
  `rscs_core/coordinates/` (`_base, space, spectral, modal, medium, meta,
  memory` + `__init__`), operator packages `transforms, coupling, modes,
  propagation, state_preparation, observation, uncertainty, provenance,
  memory`, `rscs_core/operators/` (flat facade), `rscs_core/embedding/`.
- Tests: `tests/unit/test_rscs_coordinates.py`,
  `tests/unit/test_rscs_operators.py`,
  `tests/property/test_rscs_properties.py`,
  `tests/regression/test_rscs_conservative_extension.py`,
  `tests/adversarial/test_rscs_firewall.py`.
- Docs: `docs/RSCS_MATHEMATICAL_MODEL.md`,
  `docs/RSCS_OPERATOR_REGISTRY.md`, `docs/RSCS_COORDINATE_SCHEMA.md`,
  `docs/AGENT_03_HANDOFF.md`; appended RSCS section to
  `docs/TRACEABILITY_MATRIX.md`; D3-009..015 in `docs/DECISION_LOG.md`;
  `manuscripts/rscs_foundations/README.md` (skeleton).

## Files changed (non-frozen only)

- `pyproject.toml` (package `rscs_core*` include + `registry/*.yaml`
  package-data; testpaths already included `tests/adversarial`).
- **No file under `archive/v2.0.0/`, and no `rgcs_core`, `rgcs_desktop`,
  `docs/model_registry.yaml`, or `docs/NOTATION_AND_UNITS.md` was modified**
  (verified: `git diff --stat 715486b HEAD -- archive/v2.0.0` and
  `git diff --stat 939e030 HEAD -- rgcs_core rgcs_desktop docs/model_registry.yaml`
  are both empty).

## Coordinates implemented (RSCS-C.1..14) — all 14

space (C.1), time (C.2), phase (C.3, S¹-wrapped), angular frequency (C.4),
wavevector (C.5), mode index (C.6), modal state (C.7, ℂⁿ), orientation frame
(C.8, SO(3)×{±}), polarization/spin (C.9, S²), selection coordinate (C.10),
group delay (C.11), uncertainty (C.12, wraps v2 `UncertainValue`), provenance
tag (C.13), memory lattice (C.14, **HYP, quarantined**).

## Operators implemented (RSCS-O.1..13) — all 13

frame transform (O.1), time↔freq (O.2, →RGCS-M.55), space→phase (O.3, HYP),
coupling (O.4, anti-Hermitian K=i·2πg, →RGCS-M.23/24/28/46), parity basis
(O.5, →RGCS-M.23-25), transfer cascade (O.6), phase matching (O.7),
group-delay balance (O.8), state preparation (O.9), observation (O.10,
→RGCS-M.56), uncertainty propagation (O.11, →RGCS-M.10/11), provenance
propagation (O.12, firewall), memory store/recall (O.13, HYP).

## Conservative Extension Property — evidence

Embedding ι in `rscs_core/embedding/`; battery `run_all_cep()` all-green.
`O_RSCS(ι(x)) = ι(O_RGCS(x))` within rtol 1e-9 / atol 1e-12 for:

- **O.4 coupling** → RGCS-M.23/24/28: hybrid frequencies and 2g splitting;
  golden G-08 reproduced (f_A=f_B=1000 Hz, g=10 → 990/1010 Hz).
- **O.2 analytic signal** → RGCS-M.55 (delegates; exact).
- **O.10 coherence** → RGCS-M.56 (delegates; exact).
- **O.11 uncertainty** → RGCS-M.10/11 (scale/embed commute).
- **Anti-Hermitian convention (QA-D-04):** exact unitary evolution
  `exp(i·2πH·t)` gives a 2g Hz splitting and **norm-preserving** dynamics
  (no growth); a contrast test shows the forbidden real-symmetric `K=π·g`
  grows without bound.

## Tests added and final pass count

- **64 new RSCS tests, all pass** (unit 27 + operators 11-ish, property 9,
  regression 11, adversarial 15; see files).
- **Full suite: 293 passed, 4 failed.** The 4 failures are the **documented
  frozen-baseline Windows/numpy failures**, byte-identical to the pre-Agent-03
  set (`docs/V2_BASELINE_AUDIT.md` §3): generator determinism (numpy drift
  NR3-001), and the three vertical-slice Windows portability defects
  (V2-WIN-01). **Zero new regressions.** Agent 02 provenance lint: 6/6 pass.

## Documents produced

`RSCS_MATHEMATICAL_MODEL.md`, `RSCS_OPERATOR_REGISTRY.md`,
`RSCS_COORDINATE_SCHEMA.md`, `AGENT_03_HANDOFF.md`; TRACEABILITY_MATRIX RSCS
section; DECISION_LOG D3-009..015; `rscs_core/registry/rscs_registry.yaml`
(machine-readable, 27 entries).

## APIs opened for Agents 04–08

Stable, typed, tested import surfaces (all under `rscs_core`):

- **Coordinates:** `from rscs_core.coordinates import ModalState,
  SpatialCoordinate, OrientationFrame, PhaseCoordinate, AngularFrequency,
  Wavevector, ModeIndex, PolarizationState, SelectionCoordinate, GroupDelay,
  Uncertainty, ProvenanceTag, MemoryLattice` (+ `COORDINATE_TYPES`).
- **Operators (flat):** `from rscs_core import operators as ops` →
  `ops.couple_modes, ops.anti_hermitian_coupling, ops.to_parity_basis,
  ops.cascade/reverse_cascade, ops.phase_match, ops.balance_group_delay,
  ops.prepare_two_level, ops.coherence/insertion_loss_db/isolation_db,
  ops.scale/combine_relative, ops.propagate_provenance, ops.memory_store/…`
  (+ `ops.OPERATORS` id→callable map).
- **Embedding / CEP:** `from rscs_core import embedding` →
  `iota_frequency, iota_uncertainty, check_*_cep, run_all_cep`.
- **Registry / firewall:** `from rscs_core import load_registry,
  registry_ids, classification_of`; `from rscs_core.registry import
  rscs_classified, assert_no_src_upgrade`.

Guidance per downstream agent:
- **Agent 04 (NHT/HAL memory bridge):** build on `MemoryLattice` (C.14) and
  `memory.store/recall` (O.13) — both HYP and require
  `acknowledge_hypothesis=True`. You MUST attach an observable, uncertainty,
  and a pre-registered failure condition before promoting anything out of the
  HYP quarantine. `space_to_phase` (O.3) is the space→phase encoding.
- **Agent 05 (crystal application):** compose `couple_modes` (O.4) and
  `to_parity_basis` (O.5) with the frozen `rgcs_core.geometry/…`; use
  `Uncertainty` (C.12) so σ-bands propagate.
- **Agent 06 (optics/nonreciprocal):** `cascade`/`reverse_cascade` (O.6,
  swap-on-reversal nonreciprocity), `phase_match` (O.7),
  `balance_group_delay` (O.8), and the anti-Hermitian coupling for
  nonreciprocity indicators.
- **Agent 07 (coil/laser timing):** `prepare_two_level` (O.9) and the
  observation metrics (O.10).
- **Agent 08 (software/hardware):** the registry loader + firewall are the
  contract for wiring provenance/classification into the app and schemas.

Extension rule for all: any NEW coordinate/operator needs a
`rscs_registry.yaml` row (id, class, units, module, ≥1 test), a
`docs/RSCS_NOTATION_LEDGER.md` append (before first use, logged in
DECISION_LOG), and must not redefine a frozen symbol or RGCS-M.* equation.

## Known limitations

- O.3 (space→phase) and O.13/C.14 (memory) are **HYP scaffolding** — typed
  APIs only, no physical model; Agent 04 owns the science.
- `apply_coupling` (O.4) is a small-step demonstrator; production time
  integration should use `rgcs_core.coupled_modes.dynamics` (with damping/
  nonlinearity) or the exact propagator shown in the regression test — v2's
  explicit-Euler integrator is unstable for a *pure* conservative oscillation.
- O.9 preparation covers the two-level case; higher-dimensional preparation
  is left for the agent that needs it.
- The 4 Windows/numpy baseline failures persist by design (frozen; a Linux
  pinned rerun is the closure path, CLM-3-001 / A3-001).

## Unresolved decisions requiring orchestration

None blocking. One item for the orchestrator to ratify at integration:
whether the RSCS registry stays a separate file (current: D3-015) or is later
merged into a schema-2 `model_registry.yaml` by Agent 11 at packaging — Agent
03 recommends keeping it separate to preserve the baseline immutability
guarantee.
