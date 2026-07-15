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
