# RSCS 1.0 — Coordinate Schema

**Author:** Agent 03. **Date:** 2026-07-14. Serialization and validation
schema for the 14 RSCS-C.* typed coordinates. Authoritative types live in
`rscs_core/coordinates/`; the machine registry is
`rscs_core/registry/rscs_registry.yaml`. Every coordinate is an immutable
(frozen) dataclass; `to_dict()` gives a deterministic, JSON-ready mapping that
always includes the `rscs_id`.

## Common rules

- **Immutable.** Instances are frozen; "modifying" returns a new instance.
- **Validated at construction.** Non-finite (NaN/inf) values, wrong shapes,
  non-orthogonal frames, out-of-range populations, and un-acknowledged
  hypothesis coordinates all raise `ValueError`/`TypeError` immediately.
- **Unit-tagged.** Component keys carry the unit suffix (`_mm`, `_rad`,
  `_rad_s`, `_s`, `_rad_mm`). No implicit unit conversion; display never
  mutates stored values (v2 policy 3).
- **Deterministic serialization.** Arrays → lists; complex → `{re, im}`;
  same input → same JSON (used for content hashing).

## Per-coordinate schema

| ID | Type | Fields (unit) | Validation | Serialized keys |
|---|---|---|---|---|
| C.1 | `SpatialCoordinate` | `xyz_mm:(f,f,f)`, `frame:str` | finite 3-vector; non-empty frame | `xyz_mm`, `frame` |
| C.2 | `TimeCoordinate` | `t_s:f` | finite | `t_s` |
| C.3 | `PhaseCoordinate` | `phi_rad:f` | finite; wrapped to [0,2π) | `phi_rad` |
| C.4 | `AngularFrequency` | `omega_rad_s:f` | finite; `from_hz`/`f_hz` bridge | `omega_rad_s`, `f_hz` |
| C.5 | `Wavevector` | `k_rad_mm:(f,f,f)` | finite 3-vector | `k_rad_mm`, `magnitude_rad_mm` |
| C.6 | `ModeIndex` | `indices:(int…)`, `labels:(str…)` | labels match indices or empty | `indices`, `labels` |
| C.7 | `ModalState` | `amplitudes:complex[n]` | finite, non-empty 1-D | `amplitudes`, `amplitude`, `phase_rad`, `total_occupancy` |
| C.8 | `OrientationFrame` | `rotation:3×3`, `handedness:±1`, `name:str` | orthogonal (RᵀR=I, \|det\|=1) | `rotation`, `handedness`, `name` |
| C.9 | `PolarizationState` | `stokes:(f,f,f)` | non-zero; normalized to \|s\|=1 | `stokes`, `helicity` |
| C.10 | `SelectionCoordinate` | `value:f`, `population:[0,1]`, `unit:str` | finite value; population in range | `value`, `population`, `unit` |
| C.11 | `GroupDelay` | `tau_g_s:f[n]` | finite, non-empty 1-D | `tau_g_s`, `imbalance_s` |
| C.12 | `Uncertainty` | `value:f`, `u_rel:[0,1)`, `dist:str` | v2 `UncertainValue` range rules | `value`, `u_rel`, `sigma`, `dist` |
| C.13 | `ProvenanceTag` | `source_id:str`, `claim_class:∈classes`, `path:(str…)` | non-empty source; valid class | `source_id`, `claim_class`, `path` |
| C.14 | `MemoryLattice` **(HYP)** | `orientation_index:(int…)`, `carrier_phase_rad:f[n]`, `acknowledge_hypothesis:bool` | **requires `acknowledge_hypothesis=True`**; phase length matches index | `orientation_index`, `carrier_phase_rad`, `claim_class="HYP"` |

## Manifolds

E³ (C.1), ℝ (C.2), S¹ (C.3), ℝ (C.4), ℝ³ (C.5), ℤⁿ (C.6), ℂⁿ (C.7),
SO(3)×{±} (C.8), S² Poincaré (C.9), ℝ-or-ℤ selector (C.10), ℝⁿ (C.11),
uncertainty triple (C.12), enum tuple (C.13), Tⁿ torus (C.14).

## Quarantine (C.14)

`MemoryLattice` is a **HYP** coordinate seeded from NHT/HAL (SRC-3-07). It
cannot be constructed without `acknowledge_hypothesis=True`, so EST/DER code
paths cannot depend on it by accident. It carries no physical claim; Agent 04
must attach an observable and a pre-registered failure condition before any
downstream use (notation ledger §1.5; `docs/EXCLUSION_MATRIX.md`).
