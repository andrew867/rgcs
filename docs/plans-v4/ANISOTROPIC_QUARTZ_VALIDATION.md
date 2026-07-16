# Anisotropic α-Quartz Validation (Agent 04)

**Branch:** v4-dev. **Module:** `rscs2_core/quartz.py`. **Tests:**
`tests/v4/test_rscs2_quartz.py` (9, green; v4 suite 28/28). All numbers
below are real solver output; evidence under `evidence/v4/agent04/`.

## 1. Material record

Elastic constants and density are the **frozen v3 module verbatim**
(`rgcs_core.anisotropy`; Bechmann 1958 / Auld 1973). New v4 constants
(first use, registered): class-32 piezoelectric matrix e11 = 0.171,
e14 = −0.0406 C/m² and constant-strain relative permittivity
ε11 = 4.428, ε33 = 4.634 (Bechmann 1958, IEEE-176 convention; 2 %
declared uncertainty; T_ref = 25 °C). Tensor symmetries machine-checked
(minor+major for C; (i,j) symmetry and zero k=Z row for class-32 e; SPD
ε; elastic energy positivity on random strains).

## 2. Bond rotation (exact full-tensor transformation)

`rotate_stiffness/rotate_piezo/rotate_dielectric` with intrinsic z-x-z
Euler angles (crystal→lab, matching the v3 `fea_export` record). Tested:
identity; inverse round-trip; composition R₂(R₁C) = (R₂R₁)C; symmetry
preservation; energy positivity after rotation; improper-rotation
rejection; **trigonal symmetry checks** — C invariant under 120° about Z
and 180° about X (class-32 group operations); and the 90° known case
v_lab(m; R·C) = v_crystal(Rᵀm) against the frozen module at rel 1e-9.

## 3. Christoffel anchors

| Axis | frozen v3 v_qL (m/s) | v4 v_qL | v4 v_qS1 | v4 v_qS2 |
|---|---|---|---|---|
| X | 5718.734781 | 5718.734781 | 5096.767454 | 3307.206387 |
| Y | 5992.675993 | 5992.675993 | 4315.038412 | 3884.180481 |
| Z | 6329.927000 | 6329.927000 | 4672.022534 | 4672.022534 |

Agreement to all printed digits (rel 1e-9 in tests), plus 40 random
off-axis directions and a 61×121 spherical sweep (figure
`wave_speed_surfaces.png`: the qL surface shows the trigonal 3-fold
azimuthal symmetry, machine-asserted on the equatorial ring; Z-pole ring
uniform at 6329.927 m/s; Z-axis shear degeneracy visible). Polarization
triads orthonormal to 1e-9.

## 4. Free anisotropic crystal modes

Free 20×20×50 mm quartz block (full-tensor assembly): exactly **6 rigid
modes** at both refinements; all elastic frequencies positive; elastic
residuals < 1e-6; refinement moves the first four modes DOWN by < 0.1 %
(P2 upper-bound behavior), |Δf|/f < 2 %. **Frame invariance:** rotating
the material by a body-symmetry rotation of a cube leaves the spectrum
unchanged (rel 2e-3); a non-symmetry 90° X-rotation of the elongated
block shifts modes by > 2 % (the physical orientation effect —
`orientation_sweep_modes.png/csv`, β = 0…90°).

## 5. Degeneracy taxonomy (V.9 groundwork)

Machine-distinguished on cantilevers: **numerical degeneracy** (isotropic
square section: flexural-pair split shrinks under refinement, < 2 Hz);
**symmetry-protected degeneracy** (same case, exact in the continuum);
**section-induced splitting** (rectangular 10×12 mm: split > 50 Hz,
persistent within 10 % across refinement). The externally-coupled 2g
case lands with the tuning fork (Agent 10), where the frozen
`RSCS-O.4` avoided-crossing anchor applies. Rigid-mode residuals are now
reported as NaN (0/0-undefined) rather than a misleading number.

## 6. Acceptance vs the brief

Christoffel anchors PASS · Bond rotations PASS · free-crystal
convergence PASS · six rigid modes PASS · no frozen-v3 regression
(anchor equality to printed digits) PASS.
