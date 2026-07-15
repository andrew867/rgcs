# RSCS 1.0 — Operator and Coordinate Registry

**Author:** Agent 03. **Date:** 2026-07-14. Human-readable view of the
authoritative machine registry `rscs_core/registry/rscs_registry.yaml`
(schema 1), validated by `rscs_core.registry.load_registry` and cross-checked
by `tests/adversarial/test_rscs_firewall.py`. Every id used anywhere in RSCS
code or docs must appear here; every entry has ≥1 test.

This registry is a **separate namespace** from the frozen RGCS-M.1..61
(`docs/model_registry.yaml`, schema 1, untouched). `RSCS-M.*` is reserved and
unused (DECISION_LOG D3-006).

## Coordinates (RSCS-C.*)

| ID | Name | Class | Units / manifold | Module | Provenance | Exclusions |
|---|---|---|---|---|---|---|
| RSCS-C.1 | spatial coordinate | EST | mm, E³ | `coordinates.space:SpatialCoordinate` | — | — |
| RSCS-C.2 | time | EST | s, ℝ | `coordinates.spectral:TimeCoordinate` | — | — |
| RSCS-C.3 | phase | EST | rad, S¹ | `coordinates.spectral:PhaseCoordinate` | — | — |
| RSCS-C.4 | angular frequency | EST | rad/s, ℝ | `coordinates.spectral:AngularFrequency` | — | — |
| RSCS-C.5 | wavevector | EST | rad/mm, ℝ³ | `coordinates.spectral:Wavevector` | EP-07-01, EP-02-01 | — |
| RSCS-C.6 | mode index tuple | EST | ℤⁿ | `coordinates.modal:ModeIndex` | — | — |
| RSCS-C.7 | modal state | EST | ℂⁿ (obs. X) | `coordinates.modal:ModalState` | — | — |
| RSCS-C.8 | orientation frame | EST | SO(3)×{±} | `coordinates.space:OrientationFrame` | EP-08-01 | no visual-perception (SRC-3-08) |
| RSCS-C.9 | polarization/spin | EST | S² Stokes | `coordinates.medium:PolarizationState` | EP-04-02 | no atomic-vapor NLNR (SRC-3-04) |
| RSCS-C.10 | selection coordinate | DER | selector unit + [0,1] | `coordinates.medium:SelectionCoordinate` | EP-05-01 | no single-photon regime (SRC-3-05) |
| RSCS-C.11 | group-delay | DER | s, ℝⁿ | `coordinates.medium:GroupDelay` | EP-02-03 | — |
| RSCS-C.12 | uncertainty | DER | (val, rel σ, dist) | `coordinates.meta:Uncertainty` | — | — |
| RSCS-C.13 | provenance tag | EST | (source, class, path) | `coordinates.meta:ProvenanceTag` | EP-03-01 | — |
| RSCS-C.14 | memory lattice | **HYP** | Tⁿ (rad) | `coordinates.memory:MemoryLattice` | EP-07-01/02 | **NHT/HAL quarantine (SRC-3-07)** |

## Operators (RSCS-O.*)

| ID | Name | Class | Signature (in → out) | Module | Provenance | Reproduces v2 | Tests |
|---|---|---|---|---|---|---|---|
| RSCS-O.1 | frame transform | EST | (C.1,C.8)→C.1 | `transforms:frame_transform` | EP-08-01 | — | `property::test_frame_roundtrip` |
| RSCS-O.2 | time↔freq (analytic) | EST | real→complex | `transforms:time_to_frequency` | — | RGCS-M.55 | `regression::test_analytic_signal_cep` |
| RSCS-O.3 | space→phase | **HYP** | (C.1,C.5,ω,t)→C.3 | `transforms:space_to_phase` | EP-07-01 | — | `adversarial::test_space_to_phase_is_hyp` |
| RSCS-O.4 | coupling (anti-Herm.) | EST | (f,g)→{H,K,hybrids} | `coupling:couple_modes` | EP-01-01, EP-04-01 | RGCS-M.23/24/28/46 | `regression::test_two_mode_cep`, `::test_anti_hermitian_2g_splitting`, `::test_no_growth_degenerate_pair` |
| RSCS-O.5 | parity basis | EST | C.7(2)→C.7(2) | `modes:to_parity_basis` | EP-02-02, EP-06-02 | RGCS-M.23/24/25 | `property::test_parity_self_inverse`, `unit::test_parity_diagonalizes_degenerate` |
| RSCS-O.6 | transfer cascade | EST | seq[2×2]→2×2 | `propagation:cascade` | EP-02-02/03, EP-06-03 | — | `unit::test_cascade_unitary`, `property::test_cascade_associative` |
| RSCS-O.7 | phase matching | EST | (k₊,q,k₋)→{Δq,matched} | `propagation:phase_match` | EP-02-01 | — | `unit::test_phase_match` |
| RSCS-O.8 | group-delay balance | DER | C.11→C.11 | `propagation:balance_group_delay` | EP-02-03 | — | `unit::test_group_delay_balance` |
| RSCS-O.9 | state preparation | DER | (C.9,C.10)→C.7 | `state_preparation:prepare_two_level` | EP-04-02, EP-05-01 | — | `unit::test_state_prep_occupancy` |
| RSCS-O.10 | observation/metric | EST | C.7/seg→(𝒞,IL,iso,contrast) | `observation:coherence` (+IL/iso/contrast) | EP-01-03, EP-04-03, EP-05-02 | RGCS-M.56 | `regression::test_coherence_cep`, `unit::test_dB_metrics` |
| RSCS-O.11 | uncertainty prop. | DER | (C.12,factor)→C.12 | `uncertainty:scale` | — | RGCS-M.10/11 | `regression::test_uncertainty_cep`, `property::test_uncertainty_monotonic` |
| RSCS-O.12 | provenance prop. | EST | (op,cls,*C.13)→C.13 | `provenance:propagate` | — | — | `adversarial::test_no_src_upgrade`, `::test_provenance_propagate_caps_class` |
| RSCS-O.13 | memory store/recall | **HYP** | (C.7,idx)→C.14 | `memory:store` | EP-07-01/02 | — | `adversarial::test_memory_store_requires_ack` |

## Manuscript targets

O.1–O.11 → **RSCS Foundations** manuscript (frame transforms, spectral maps,
coupling algebra, propagation, preparation/observation, uncertainty
boundary). O.3, O.13 and C.14 → **Historical Companion / Agent 04 memory
bridge** (HYP; quarantined). Full mapping in `docs/TRACEABILITY_MATRIX.md`.

## Conventions frozen here (do not regress)

- **Coupling sign:** `K = i·2π·g` (anti-Hermitian), never real-symmetric
  `π·g` (QA-D-04; DECISION_LOG D3-007).
- **Classes:** EST > DER > HYP/ENG > SRC; strong (DER/EST) output from weak
  (HYP/ENG/SRC) input is a firewall violation (design principle 4).
- **Units:** inherited verbatim from `docs/NOTATION_AND_UNITS.md`; nothing
  incompatible introduced.
