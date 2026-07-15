# RGCS v2 — Traceability Matrix

**Author:** Sub-Agent 09. **Date:** 2026-07-14.
Chain: requirement → registered equation(s) (RGCS-M.x, authoritative in
`docs/model_registry.yaml`, 61 entries) → implementing module → covering
tests → manuscript section. Hypothesis rows additionally trace to
`ROADMAP_TO_FALSIFICATION.md`. Classification per
`SCIENTIFIC_CLASSIFICATION_POLICY.md`.

| Requirement | RGCS-M.x | Module | Tests | Manuscript |
|---|---|---|---|---|
| Faceted/tapered/double-terminated geometry (areas, caps, volumes) | M.1–M.6 | `rgcs_core.geometry` | `unit/test_geometry.py`; `golden` G-01..G-04 | §4 (sec:ladder), §3 |
| Density-constrained inverse sizing (Newton + bisection) | M.7 | `rgcs_core.geometry` | `unit/test_geometry.py`; `golden` | §4; App. C (Algorithms) |
| Wave-speed default + systematic band | M.9–M.10 | `rgcs_core.uncertainty` | `unit`, `property` (band propagation) | §3, §4 |
| 4096 harmonic ladder, axial half-wave lengths | M.11–M.13 | `rgcs_core.harmonics` | `unit/test_harmonics_compact.py`; `golden` G-05..G-06 | §4 |
| Compact-coordinate spectrum f_n² = f_b² + (nκ_χ)²; parity families; zero-mode flag (H-01/H-01a) | M.13–M.17 | `rgcs_core.compact_modes` | `unit/test_harmonics_compact.py`; `property` (monotonicity); `golden` G-07 | §6 (sec:compact); Fig. 2–3 |
| Resonance offset ε_R^(f); Q-derived class bins; far-detuned control ε=1.25 | M.18–M.22 | `rgcs_core.resonance` | `unit/test_resonance_coupled.py`; `golden` | §7 (sec:offset); Fig. 4 |
| Two-mode avoided crossing, mixing angle, strong-coupling ratio R_g | M.23–M.27 | `rgcs_core.coupled_modes.static` | `unit/test_resonance_coupled.py`; `golden` G-08 (990/1010 Hz) | §8 (sec:coupled); Fig. 5 |
| N-mode eigenproblem (symmetric g, zero diagonal) | M.28 | `rgcs_core.coupled_modes.static` | `unit` (matches 2-mode); `property` (interlacing) | §8 |
| Coupling geometry scaling g ∝ (2πR_χ)^(−1/2) (H-05) | M.29 | `rgcs_core.coupled_modes.static` | `unit` | §8; Table 9 |
| Log-spiral cone: pitch, 3D path length, per-turn segmentation, curvature invariant | M.30–M.35 | `rgcs_core.geometry.spiral` | `unit/test_geometry.py`; `golden` G-09..G-11 | §5 (sec:spiral); Fig. 6 |
| Compact radius prior R_χ^(s) = ℓ_3D/(2πT) (authoritative; WB B23/B24 superseded, WB-SO-1) | M.36 | `rgcs_core.geometry.spiral` (`compact_radius_prior_mm`) | `unit/test_geometry.py` | §5; Fig. 6 (H-06a) |
| Node estimators (metric center, measured supersedes) (H-07) | M.37–M.39 | `rgcs_core.geometry.nodes` | `unit/test_geometry.py` | §9 (sec:node) |
| Loading: added modal mass, k_H, proxy k̃_H (H-08/H-08b) | M.40–M.45 | `rgcs_core.loading` | `unit/test_loading_drive.py`; `golden` | §9 |
| Stuart–Landau complex modal dynamics (H-09); damping γ = ω/2Q | M.46–M.49 | `rgcs_core.coupled_modes.dynamics` | `unit/test_resonance_coupled.py` (ringdown); `regression/test_qa_d04_coupling_map.py` | §10 (sec:coherence) Eq. (22); App. B.4 |
| Time↔frequency coupling consistency \|K\| = 2πg, anti-Hermitian K = i·2πg (pre-registered H-09 gate; QA-D-04 erratum) | M.46 | `rgcs_core.coupled_modes.static` (`coupling_consistency`) | `regression/test_qa_d04_coupling_map.py`; `unit` | §10.1; App. B.4; Fig. 11 |
| Coherence metrics: analytic signal, phase, circular stats, windowed autocorrelation coherence + baseline, PL, PLV, onset/decay | M.51–M.56 (COH-M1..M11) | `rgcs_core.coherence.metrics` | `unit/test_coherence.py`; `regression` (manifest, 50) | §10; Fig. 7–8; App. B.3 |
| Unified initial-phase estimator φ₀ = arg z(0) mod 2π (QA-D-03) | M.61 context | `rgcs_core.coherence.metrics.initial_phase_estimate` | `unit/test_qa_hardening.py` | Fig. 8 caption; Table 8 |
| Rayleigh spontaneity test (H-13) | M.61 (COH-M4) | `rgcs_core.coherence.metrics.rayleigh_test` | `unit/test_coherence.py`; `regression` | §10.2; Fig. 8; Table 8 |
| Spatial anisotropy: per-axis phase rates, shear scalar, decay-law comparison (H-10/H-11) | M.51–M.55 | `rgcs_core.coherence.anisotropy`, `.models` | `unit/test_coherence.py`; `property` (invariances); `golden` G-15 | §11 (sec:anisotropy); Fig. 9 |
| Drive families, exact-cycle allocation, phase residue r_φ (D-13 closed) | M.57–M.60 | `rgcs_core.drive` | `unit/test_loading_drive.py`; `golden` G-12..G-14, D-13 row | §12 (sec:drive); Table 5 |
| Control-subtracted metrics; controls matrix | — | `rgcs_core.experiments` | `unit/test_experiments_provenance.py` | §13 (sec:protocols); Fig. 10 |
| Classification metadata + forbidden vocabulary (core & desktop) | policy | `rgcs_core.provenance` | `unit/test_experiments_provenance.py` | §1 (sec:scope) |
| Desktop vertical slice (gate 6) | consumes all above | `rgcs_desktop` | `integration/test_vertical_slice.py`; `ui/test_smoke.py` | §17 (sec:software) |
| Workspace data safety + corruption recovery | — | `rgcs_desktop.workspaces` | `unit/test_qa_hardening.py` | §17 |
| Malformed-input handling (CSV/JSON) | — | `rgcs_desktop.jobs.workers`, `.services.schemas` | `unit/test_malformed_inputs.py`, `unit/test_qa_hardening.py` | §17 |

Reverse index (hypotheses): H-01/H-01a→M.13–M.17; H-02→drive/coherence;
H-03/H-04→M.11–M.13; H-05→M.29; H-06/H-06a→M.30–M.36; H-07→M.37–M.39;
H-08/H-08b→M.40–M.45; H-09→M.46–M.49; H-10/H-11→anisotropy M.51–M.55;
H-12/H-13→COH metrics + M.61; H-14→COH-M5/M10 re-adjudication. Each has a
failure condition in manuscript Table 9 and a protocol row in
`ROADMAP_TO_FALSIFICATION.md`.

---

## RSCS 1.0 traceability (Agent 03)

Chain: RSCS id → source equation/provenance (`references/equation_provenance.yaml`
EP-*; or the frozen RGCS-M.* it reproduces) → module → tests → manuscript
target. Authoritative machine registry: `rscs_core/registry/rscs_registry.yaml`.
RSCS reproduces (never redefines) the cited RGCS-M.* on the v2 domain via the
Conservative Extension Property.

| RSCS id | Source / reproduces | Module | Tests | Manuscript target |
|---|---|---|---|---|
| RSCS-C.1..14 | typed coordinates; EP-07-01/02-01/04-02/05-01/02-03/03-01/08-01 | `rscs_core.coordinates.*` | `unit/test_rscs_coordinates.py`; `adversarial/test_rscs_firewall.py` | RSCS Foundations §coordinates; RSCS_COORDINATE_SCHEMA.md |
| RSCS-O.1 frame transform | EP-08-01 | `rscs_core.transforms:frame_transform` | `property::test_frame_roundtrip` | RSCS Foundations §frames |
| RSCS-O.2 time↔freq | reproduces RGCS-M.55 | `rscs_core.transforms:time_to_frequency` | `regression::test_analytic_signal_cep` | RSCS Foundations §spectral |
| RSCS-O.3 space→phase (HYP) | EP-07-01 | `rscs_core.transforms:space_to_phase` | `adversarial::test_space_to_phase_is_hyp` | Historical companion / Agent 04 (HYP) |
| RSCS-O.4 coupling | EP-01-01, EP-04-01; reproduces RGCS-M.23/24/28/46 | `rscs_core.coupling:couple_modes` | `regression::test_two_mode_cep`, `::test_anti_hermitian_2g_splitting`, `::test_no_growth_degenerate_pair` | RSCS Foundations §coupling algebra |
| RSCS-O.5 parity basis | EP-02-02, EP-06-02; reproduces RGCS-M.23–25 | `rscs_core.modes:to_parity_basis` | `property::test_parity_self_inverse`; `unit::test_parity_diagonalizes_degenerate` | RSCS Foundations §modal projection |
| RSCS-O.6 transfer cascade | EP-02-02/03, EP-06-03 | `rscs_core.propagation:cascade` | `unit::test_cascade_unitary`; `property::test_cascade_associative` | RSCS Foundations §propagation |
| RSCS-O.7 phase matching | EP-02-01 | `rscs_core.propagation:phase_match` | `unit::test_phase_match` | RSCS Foundations §phase matching |
| RSCS-O.8 group-delay balance | EP-02-03 | `rscs_core.propagation:balance_group_delay` | `unit::test_group_delay_balance` | RSCS Foundations §dispersion |
| RSCS-O.9 state preparation | EP-04-02, EP-05-01 | `rscs_core.state_preparation:prepare_two_level` | `unit::test_state_prep_occupancy` | RSCS Foundations §preparation |
| RSCS-O.10 observation | EP-01-03/04-03/05-02; reproduces RGCS-M.56 | `rscs_core.observation:coherence` | `regression::test_coherence_cep`; `unit::test_dB_metrics` | RSCS Foundations §observation |
| RSCS-O.11 uncertainty | reproduces RGCS-M.10/11 | `rscs_core.uncertainty:scale` | `regression::test_uncertainty_cep`; `property::test_uncertainty_monotonic` | RSCS Foundations §uncertainty |
| RSCS-O.12 provenance | design principle 4 firewall | `rscs_core.provenance:propagate` | `adversarial::test_no_src_upgrade`, `::test_provenance_propagate_caps_class` | RSCS Foundations §provenance firewall |
| RSCS-O.13 memory (HYP) | EP-07-01/02 | `rscs_core.memory:store` | `adversarial::test_memory_store_requires_ack` | Historical companion / Agent 04 (HYP) |

Conservative Extension Property coverage: `rscs_core/embedding/` +
`tests/regression/test_rscs_conservative_extension.py` (O.2/O.4/O.10/O.11 vs
frozen RGCS-M.55/23-28-46/56/10-11). RSCS-M.* namespace reserved and unused.

## Agent 04 — Hydrogenuine memory bridge

| RSCS id | Source / class | Module | Tests | Claims / manuscript |
|---|---|---|---|---|
| RSCS-C.15 HG record | ENG; NHT/HAL fields (SRC-3-07/08) | `rscs_core.memory.hydrogenuine:HydrogenuineRecord` | `unit/test_rscs_hg_memory.py` | RSCS Foundations memory chapter |
| RSCS-O.14 HG store | ENG | `rscs_core.memory.hydrogenuine:store` | `unit/test_rscs_hg_memory.py::test_store_requires_frame_consistency` | H-15/H-16 |
| RSCS-O.15 HG replay | ENG | `rscs_core.memory.hydrogenuine:replay` | `property/test_rscs_hg_properties.py::test_replay_fidelity` | H-16/H-18 |
| RSCS-O.16 HG update | ENG | `rscs_core.memory.hydrogenuine:update` | `unit/test_rscs_hg_memory.py::test_update_records_observation` | H-19 |
| RSCS-O.3 space→phase (HYP) | HYP; NHT (EP-07-01) | `rscs_core.transforms:space_to_phase` | `adversarial/test_rscs_firewall.py::test_nht_lattice_still_hyp_quarantined` | H-15..H-19 depend on it staying HYP |
| RSCS-C.14/O.13 HAL lattice (HYP) | HYP quarantined (SRC-3-07) | `rscs_core.coordinates.memory`, `rscs_core.memory` | `adversarial/test_rscs_firewall.py` | Historical companion |

Falsifiable software claims H-15..H-19 in `docs/CLAIM_REGISTER.md`;
mapping/classification in `docs/NHT_HAL_RSCS_MAPPING.md`; architecture in
`docs/HG_RSCS_MEMORY_ARCHITECTURE.md`. NHT/HAL stays HYP; consciousness/quartz
claims excluded (`docs/EXCLUSION_MATRIX.md`).

## Agent 05 — crystal application (anisotropic propagation)

| RSCS/RGCS id | Source / reproduces | Module | Tests | Manuscript |
|---|---|---|---|---|
| RSCS-O.17 anisotropic Christoffel | Christoffel elastodynamics; reproduces scalar RGCS-M.10 at crystal axes | `rscs_core.propagation:christoffel_wave_speeds` | `unit/test_rscs_anisotropy.py`; `regression::test_anisotropy_reproduces_scalar_vL` | Crystal Application §1 |
| α-quartz elastic model (EST handbook) | closes v2 D-19a | `rgcs_core.anisotropy` | `unit/test_rscs_anisotropy.py::test_axis_speeds_match_closed_form` | Crystal Application §1 |
| Quasi-mode taxonomy (qL, qS1, qS2) | Christoffel eigenvectors | `rscs_core.propagation` | `unit/test_rscs_anisotropy.py::test_quasi_long_is_fastest` | Crystal Application §2 |

Node menu (§3, 8 definitions; 1-3 implemented in frozen v2, 4-8 HYP for
Agent 07), environmental factors (§5), model selection (§7), CAD/FEA (§8,
Agent 08), crystal DB + inverse design (§9, Agent 08), historical crosswalk
(§10, Agent 09) are framed in `docs/RGCS_CRYSTAL_APPLICATION.md`.

## Agent 06 — optical / photon-phonon / nonreciprocal coupling

| RSCS/RGCS id | Source / reproduces | Module | Tests | Manuscript |
|---|---|---|---|---|
| RSCS-C.16 optical carrier | carrier/envelope separation (standard) | `rscs_core.coordinates.optical:OpticalCarrier` | `unit/test_rscs_optical.py::test_optical_carrier` | RSCS Foundations, optical ch. |
| RSCS-C.17 directional propagation pair | EP-06-01 (TMOKE perturbation form, math only) | `rscs_core.coordinates.optical:DirectionalPropagation` | `unit/test_rscs_optical.py::test_directional_propagation` | RSCS Foundations |
| RSCS-C.9 Jones<->Stokes extension | standard polarization algebra | `rscs_core.coordinates.medium:PolarizationState.from_jones/.jones` | `unit::test_jones_stokes_roundtrip`; `property::test_jones_stokes_roundtrip_property` | RSCS Foundations |
| RSCS-O.18 dispersion phase | EP-02-01/03 (Taylor expansion) | `rscs_core.propagation:dispersion_phase` | `unit::test_dispersion_phase_at_carrier`; `property::test_dispersion_phase_polynomial` | RSCS Foundations |
| RSCS-O.19 photon-phonon conversion | EP-02-01/02 (four selection rules) | `rscs_core.coupling:mode_conversion, overlap_integral` | `unit::test_mode_conversion_selection_rules`; `property::test_overlap_cauchy_schwarz` | Crystal Application, optical section |
| RSCS-O.20 Autler-Townes lineshape | EP-01-02; reproduces RGCS-M.24 (G = 2*pi*2g) | `rscs_core.observation:autler_townes_response` | `unit::test_ats_peak_separation`; `regression::test_ats_matches_coupled_mode_splitting` | RSCS Foundations |
| RSCS-O.21 critical coupling | EP-01-03 | `rscs_core.observation:critical_coupling_transmission` | `unit::test_critical_coupling_zero` | RSCS Foundations |
| RSCS-O.22 state-dependent susceptibility + NR metrics | EP-04-01/02/03 (null default, D6-003) | `rscs_core.coupling:state_dependent_susceptibility, nonreciprocal_metrics` | `unit::test_reciprocal_null`; `property::test_real_chi_pure_phase` | RSCS Foundations |
| RSCS-O.23 directional betas / beating length | EP-06-01/03 | `rscs_core.propagation:directional_betas, beating_length_mm` | `unit::test_beating_length`; `property::test_beating_length_positive_and_symmetric` | RSCS Foundations |
| alpha-quartz optical constants (EST handbook) | D6-002 (Hecht; Narasimhamurty) | `rgcs_core.optics` | `unit/test_rgcs_optics.py` | Crystal Application, optical section |
| Ray/path model (entry facet -> node menu target) | geometry (EST) | `rgcs_core.optics:ray_to_target` | `unit/test_rgcs_optics.py::test_ray_to_target_addresses_node` | Crystal Application section 3 |
| Photoelastic/M2 estimates (DER) | standard elasto-optics; uses Agent 05 anisotropy | `rgcs_core.optics:photoelastic_index_shift, quartz_acousto_optic_m2` | `regression::test_quartz_m2_uses_agent05_anisotropy` | Crystal Application, optical section |

Claims H-20..H-23 in `docs/CLAIM_REGISTER.md` (H-21/H-23 pre-registered
nulls per D6-003). Reference-mechanism comparison table GENERATED from the
frozen provenance ledgers: `docs/generated/OPTICAL_MECHANISM_COMPARISON.md`
(`tools/generate_optical_comparison.py`, determinism-pinned by
`unit::test_comparison_table_up_to_date`). Optical experiment schema:
`experiments/schemas/optical_probe.schema.json` (+ validated example).

## Agent 07 — coil / laser / timing / experimental design

No new RSCS ids (D7-001); all rows are application-layer `rgcs_core.timing`
with v2 `@classified` decorators.

| Deliverable | Source / rule | Module / file | Tests |
|---|---|---|---|
| Master-clock model (single reference, latency slots) | RG-14; D7-001 | `rgcs_core.timing:master_clock` | `unit/test_rgcs_timing.py::test_master_clock_carrier` |
| Exact-cycle closures (golden 125 ms -> 512 & 187) | RG-12/13 | `timing:exact_closure, closure_window_s, key_closures` | `::test_golden_125ms_closure`, `::test_key_closures_644_587` |
| Modulation families 20/20.48/21/40.96 Hz | RG-13 (Source) + Derived exact variants | `timing:MODULATION_FAMILIES, modulation_family_report` | `::test_modulation_families` |
| Macro sequences + "shorter by half" naming | frozen v2 drive (D-13); D7-002 | v2 `rgcs_core.drive` (unchanged) + schema enum | `::test_presets_signal_level_and_names` |
| Coil A/B phases (opposed/in_phase/offset) | RG-14 (WB3 complementary) | `timing:coil_pair_phases` | `::test_coil_pair_modes` |
| Phase at interaction coordinate (6 delay terms) | brief; uses Agent 05 anisotropy + Agent 06 optics | `timing:phase_at_coordinate` | `::test_phase_at_coordinate_terms` |
| Coil model (Z, self-resonance, mutual L, ringing, energy) | standard circuit theory (EST) | `timing:coil_impedance, self_resonance_hz, mutual_inductance_h, ring_response, pulse_energy_uj` | `::test_coil_impedance_and_resonance` etc. |
| Safety envelope + dummy-load-first | D7-003 | `timing:SAFETY_LIMITS, safe_drive_check` | `::test_pulse_energy_and_safety` |
| Sweeps + factorial control matrix + seeded blinding | brief items | `timing:phase_sweep, sweep_grid, control_matrix, randomized_order` | `::test_sweep_grid_and_control_matrix` |
| Cross-correlation / signal fidelity | EP-05-02 principle (classical) | `timing:cross_correlation, signal_fidelity` | `::test_cross_correlation_recovers_lag` |
| Function-generator presets (signal-level) | RG-12/13/14; D7-003 | `timing:function_generator_presets` | `::test_presets_signal_level_and_names` |
| Timing programme schema + example | brief; D7-002/003 | `experiments/schemas/timing_program.schema.json` | `validate.py` (green) |

Claims H-24..H-30 in `docs/CLAIM_REGISTER.md`; pre-registration spine
`docs/EXPERIMENTAL_PROGRAMME.md`; engineering detail
`docs/COIL_LASER_TIMING_AND_PHASE.md` (embedded acceptance requirements
section 9 feed Agent 08).

## Agent 08 — software / hardware / CAD / portability

| Deliverable | Rule / defect | Module / file | Tests |
|---|---|---|---|
| V2-WIN-01 fix (POSIX zip arcnames) | MIG-CODE-07 | `rgcs_desktop/services/bundle.py` | `integration/test_vertical_slice.py::test_step_7` (now green) + `unit/test_rgcs_platform.py::test_bundle_arcnames_posix` |
| Specimen-listing re-diagnosis | MIG-CODE-07 | pyproject dev extra (jsonschema/referencing) | vertical-slice steps 4/4b green |
| Windows CI | MIG-CODE-07 | `.github/workflows/ci.yml` | CI matrix itself |
| FEA export contract | crystal app section 8 | `rgcs_core/fea_export.py` | `unit/test_rgcs_platform.py::test_fea_export_roundtrip` |
| Crystal DB + migration | crystal app section 9 | `rgcs_core/crystal_db.py` | `::test_crystal_db_roundtrip`, `::test_crystal_db_migration_rules` |
| HG memory persistence (H-15/17/19 machine-tested) | Agent 04 claims | `rscs_core/memory/persistence.py` | `::test_hg_persistence_*`, `::test_hg_uncertainty_calibration_h19` |
| Provenance graph service | brief desktop rule 5 | `rgcs_desktop/services/provenance_graph.py` | `::test_provenance_graph_builds` |
| Waveform/timing preview service | Agent 07 acceptance 9.6 | `rgcs_desktop/services/waveform_preview.py` | `::test_waveform_preview` |
| SCAD v7 (D-02 fix) + CAD provenance | D-02 | `scad/vogel_parametric_crystal_models_v7_RGCS_v3.scad`, `scad/README.md` | manual OpenSCAD render (CAD, no unit harness) |
| HG Embedded OS contract + app manifest schema | brief embedded section | `embedded/HG_EMBEDDED_OS_CONTRACT.md`, `embedded/app_manifest.schema.json` | schema is JSON-Schema-valid; firmware tests at T4 |
| Timing hardware roadmap (quantified) | brief timing roadmap | `docs/SOFTWARE_HARDWARE_ARCHITECTURE.md` section 7 | requirements from Agent 07 section 9 |

Registry file repair: RSCS-C.16/C.17 rows moved from the operators list to
the coordinates list (YAML placement error introduced in the Agent 06
append; ids/content unchanged; graph test now pins 17 coordinates + 23
operators).

## Agent 09 — manuscripts and public documentation

| Deliverable | Source of numbers | File(s) | Verification |
|---|---|---|---|
| RSCS Foundations (PDF+TeX) | tools/make_v3_artifacts.py (registry, CEP battery, coupling golden, ATS figure) | manuscripts/rscs_foundations/ | build log 0 undefined / 0 overfull; CHECKSUMS.json |
| RGCS Crystal Application (PDF+TeX) | axis speeds, optics constants, M2, anisotropy sweep | manuscripts/rgcs_crystal_application/ | same |
| Software & Hardware Roadmap (PDF+TeX) | timing closures, modulation families, provenance-graph counts, safety limits, macro envelopes | manuscripts/software_hardware_plan/ | same |
| Historical & Source Companion (PDF+TeX) | equation_provenance.yaml adaptation ledger (landscape) | manuscripts/historical_source_companion/ | same |
| Shared preamble + handbook bib | -- | manuscripts/common/ | builds on MiKTeX by filename-loaded fonts |
| README Lessons Learned + v3 header | -- | README.md | Agent 10 public-claims review |
| Layout QA | build logs | docs/LAYOUT_QA_REPORT_V3.md | Agent 10 re-check |
| QA-D-02 closure | manuscript/references.bib (v2) verified correct | docs/DEFECT_REGISTER.md addendum | Agent 10 |

## Agent 10 — independent adversarial QA

| Deliverable | File | Outcome |
|---|---|---|
| QA report (fresh, v3) | docs/QA_REPORT_V3.md | YELLOW -> GREEN after D-V3-01..03 |
| Defect register updates | docs/DEFECT_REGISTER.md (Agent 10 addendum) | 3 new defects documented BEFORE fixes |
| Claim audit (v3 rows) | docs/CLAIM_AUDIT_V3.md | no classification defects |
| Reproducibility audit | docs/REPRODUCIBILITY_AUDIT_V3.md | tables byte-stable; figures D-V3-02 |
| Layout re-check | QA_REPORT_V3 section 2 | 0 undefined / 0 overfull (independent scan) |
| Cross-platform report | QA_REPORT_V3 sections 2/4 + REPRODUCIBILITY_AUDIT_V3 | Windows green (376/1); Linux gap recorded |
| Source/provenance audit | adversarial lint suite + registry cross-resolution script | pass |
| Gate recommendation | QA_REPORT_V3 section 5 | proceed to Agent 11 |
