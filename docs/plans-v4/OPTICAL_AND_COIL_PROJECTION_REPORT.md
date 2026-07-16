# Optical and Coil Projection Report (RGCS v4, Agent 08)

Status: IMPLEMENTED + TESTED (16 tests green)
Module: `rscs2_core/projections.py`  Tests: `tests/v4/test_rscs2_projections.py`
Evidence: `evidence/v4/agent08/`

Computational drive and observation projections only — no high-power
equipment content. The frozen safety envelopes bind every run
description (optical class ≤3R ≤5 mW interlock; coil ≤30 V ≤3 A
≤5 mJ/pulse dummy-load-first, D7-003).

## Optical branch (RSCS2-E.8, E.9)

**Wavelength presets** (`WAVELENGTH_PRESETS_NM`): 532 nm (DPSS),
532.538 nm, 632.8/635 nm references, 1064 nm, 1065.077 nm.

> **Octave arithmetic disclaimer (stated, per user decision):** the
> two "octave" presets are pure arithmetic — λ = c/2⁴⁹ = 532.538 nm
> and λ = c/2⁴⁸ = 1065.077 nm, i.e. the optical frequencies are the
> 4096 Hz (= 2¹²  Hz) carrier raised 37 and 36 octaves. This numeric
> relationship between two frequencies is **not** evidence of any
> special optical–acoustic coupling, and no such claim is made.

**Anisotropic index model:** Ghosh (1999) Sellmeier fits for α-quartz
(validity 198–2053 nm). Conservative-extension anchor: at 589.3 nm the
fit reproduces the frozen handbook constants n_o = 1.5443,
n_e = 1.5534 within 2×10⁻⁴ (tested). The uniaxial e-ray index n(θ)
follows the index ellipsoid; θ=0 → n_o, θ=90° → n_e, monotone
(tested). **o/e scope honesty:** plane-wave indices only; full
double-refraction walk-off is NOT modelled and is declared as such in
the docstring — any walk-off-dependent quantity must fail loud.

**Ray machinery:** vector Snell refraction pinned to the frozen scalar
`snell_refraction` (angle equality + plane-of-incidence + TIR raise
tested). Probe-path menu on the canonical 110 mm crystal (all via the
frozen `ray_to_target`): axial tx→rx and rx→tx (identical OPL/phase —
reciprocity partner paths, D6-003 posture), side entry at the lower
shaft facet (z = 0.4 L per the canonical region annotations) aimed at
the geometric centre (RGCS-M.38), the RGCS node prior (frozen
RGCS-M.39; offset from centre = (h_f−h_m)/2 exactly, tested), and an
eye-candidate slot that is **None until Agent 09 produces a measured/
derived coordinate — never assumed**. Numbers (632.8 nm, ideal N=7):
axial OPL 169.745 mm, transit 0.566 ns; side-to-centre 24.284 mm
(`probe_paths.csv`, `ray_paths.png`).

**Photoelastic projection:** Δφ = (2π/λ)·Σ Δn(S_i)·L_i with Δn from
the frozen `photoelastic_index_shift` (Δn(S=10⁻⁷) ≈ −2.95×10⁻⁸,
docstring anchor tested). This is the FE-strain → probe-phase
projection RSCS2-D.5 consumes (H-20 sideband magnitude).

**Polarization:** Jones waveplate elements against the frozen
`PolarizationState` (RSCS-C.9). Round trip Jones↔Stokes exact; QWP at
45° turns linear into circular (|helicity| = 1); HWP rotates linear by
2×22.5° (tested). σ⁺/σ⁻ preparation available via the frozen class.

**Absorption proxy:** Beer–Lambert deposited power with declared α;
transparent and opaque limits tested; explicitly *not* a temperature
claim.

## Coil branch (RSCS2-E.10, E.11)

**Biot–Savart** polyline integrator (Hanson–Hirshman stable closed
form per segment), validated against the exact single-loop on-axis
field at z = 0, R, 2R (rel 10⁻⁴) and handedness reversal. div B = 0 to
10⁻⁶ relative off the wire (gradient-tensor trace, tested).

**Coil pair:** opposed A/B coaxial pair with electrical phases from the
frozen `coil_pair_phases` and geometric winding handedness. Verified
combinatorics (tested + `coil_field_overlay.png`):
counter-wound + electrically opposed → fields **add** on axis
(double negative); same-wound + opposed → cancel at the midpoint;
in-phase same-wound → exactly 2× the single-loop field. **No toroidal
eye is assumed anywhere** — the field is whatever Biot–Savart gives.

**Drive projection:** f_n = ∫φ_n·b dV assembled with skfem, projected
on mass-orthonormal modes. Projecting F = M·φ_k returns exactly e_k
(pins projection + orthonormality, tested). Overlap table for uniform
and gradient force patterns on the reference cantilever:
`drive_mode_overlap.csv` (uniform z couples to z-bending pairs,
uniform x to the axial mode — physically correct selectivity).

**Leakage control:** `coil_coupling_report` REFUSES to produce a
coupling record without the coil-only/no-specimen baseline field at
the sensor coordinate (raises, tested). The artifact channel is
structural, not optional.

**Capacitive proxy:** t = e₁₁·V/gap surface-traction magnitude for
drive budgeting (full field solve lives in `rscs2_core.piezo`).

## Timing projections

`macro_sequences`: standard windows reproduce the frozen golden
closures (1496 Hz/125 ms, 644 Hz/250 ms, 587 Hz/1 s vs 4096 Hz);
half-spacing variants are honestly FLAGGED as not closing (1496 Hz:
93.5 cycles in 62.5 ms) via the frozen `exact_closure` — flags tested.
`drive_phase_table`: per-frequency actual phase at the interaction
coordinate from the frozen `phase_at_coordinate`, six delay terms
reported separately; the optical transit term comes straight from
`ray_to_target` and the acoustic term uses the frozen Z-axis speed
6329.927 m/s (`phase_delay_budget.png`, `phase_delay_table.csv`).

## Registered

RSCS2-E.8 (anisotropic index + ray model), RSCS2-E.9 (photoelastic
projection), RSCS2-E.10 (quasi-static coil field), RSCS2-E.11 (modal
drive projection) — all with tests and honest exclusions.
