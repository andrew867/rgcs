# RGCS Crystal Application (RSCS 1.0)

**Author:** Agent 05 (Crystal Application Expansion). **Date:** 2026-07-14.
Builds on the frozen v2 crystal work (retained) and the RSCS backbone
(`rscs_core`). This document is the spine of the Crystal Application
monograph (production deferred to Agent 09). Implemented additions are
tested code; planned additions are classified and scoped for their owning
agent. Nothing imports a source-domain physical conclusion by analogy
(`docs/EXCLUSION_MATRIX.md`); every claim keeps its class.

## 0. Preserve-and-extend posture

All valid v2 geometry, ladder, compact-mode, resonance-offset, coupled-mode,
loading, damping, coherence, and uncertainty work is **retained** (frozen
`rgcs_core`; golden values unchanged — verified by the untouched v2 suite and
the RSCS Conservative Extension Property). This agent adds anisotropic
elastic propagation, a full mode taxonomy, competing node definitions, and
the environmental/model-selection framing. Anything that cannot survive
dimensional/statistical/physical review is flagged for retirement in
`docs/INCONSISTENCY_REGISTER.md`, not silently changed.

## 1. Anisotropic elastic propagation — IMPLEMENTED & TESTED

**The flagship correction.** v2 used a single scalar effective wave speed
`v_L = 6310 m/s` with a 5% relative uncertainty, explicitly a **Hypothesis**
that one scalar suffices (RGCS-M.10). Agent 05 resolves this into a
**measured-orientation** model:

- **RSCS-O.17** (`rscs_core.propagation.christoffel_wave_speeds`): the
  Christoffel eigenproblem `Γ_ik = c_ijkl n_j n_l`, eigenvalues `= ρv²`,
  giving the quasi-longitudinal and two quasi-shear phase speeds along any
  direction `n̂`. General over any crystal (stiffness + density + direction).
- **α-quartz application** (`rgcs_core.anisotropy`): published elastic
  constants (class 32; c11=86.6, c33=106.1, c44=57.8, c12=6.7, c13=12.6,
  c14=17.8 GPa; ρ=2648 kg/m³), Established handbook input (closes v2 D-19a
  "citation required for v_L").

**Conservative extension (tested):** along X, `v_qL = √(c11/ρ) = 5719 m/s`;
along Z (optic axis), `v_qL = √(c33/ρ) = 6330 m/s` with degenerate quasi-shear
(transverse isotropy about the optic axis). The Z quasi-longitudinal speed
lands 0.3% from v2's 6310 m/s default — **inside** the ±5% band — so the
scalar model is recovered as the axial special case, and its uncertainty band
is now *explained* as the physical X–Z anisotropy spread rather than an
undeclared systematic (v2 D-05). Tests:
`tests/unit/test_rscs_anisotropy.py`,
`tests/regression/test_rscs_conservative_extension.py::test_anisotropy_reproduces_scalar_vL`.

**Impact on the ladder.** Axial half-wave frequencies (RGCS-M.8) scale with
the effective speed; the anisotropic model lets a specimen's measured
crystallographic orientation replace the scalar, shrinking the dominant
systematic once orientation is known (was v2 D-05, ~few-percent).

## 2. Mode taxonomy — quasi-modes implemented; full taxonomy planned

The Christoffel eigenproblem already classifies the three bulk **quasi-modes**
per direction: quasi-longitudinal + two quasi-shear (with polarization
eigenvectors returned). The complete taxonomy for the monograph:

| Mode family | Status | Where |
|---|---|---|
| Longitudinal / quasi-longitudinal | **implemented** (RSCS-O.17) | `rscs_core.propagation` |
| Shear / quasi-shear (fast/slow) | **implemented** (RSCS-O.17 eigenvectors) | `rscs_core.propagation` |
| Flexural, torsional (bar/rod modes) | planned — closed-form bar theory (EST) | crystal monograph §mode-taxonomy |
| Surface (Rayleigh/SAW) | planned — HYP relevance to RGCS geometry | monograph; ties Agent 06 optics |
| Localized defect modes | planned — HYP, needs a defect model | monograph |

Flexural/torsional/surface modes are DER from standard elastodynamics; their
*relevance* to the RGCS resonance ladder is HYP and gets a falsification row.

## 3. Competing eye/node definitions — framed, one implemented

v2 has `rgcs_core.geometry.nodes` (metric center, measured-supersedes; H-07).
Agent 05 frames the **eight** competing node definitions as an explicit,
classified menu (no single one presumed correct):

| # | Node definition | Class | Basis |
|---|---|---|---|
| 1 | metric center | Established | geometry (v2 RGCS-M.38, implemented) |
| 2 | prismatic-shaft prior | Derived | geometry midpoint (v2 RGCS-M.39, implemented) |
| 3 | measured vibration node | Established (measured) | supersedes priors (v2 H-07) |
| 4 | electrical node | HYP | impedance minimum; needs a measurement |
| 5 | optical path/phase feature | HYP | ties Agent 06 |
| 6 | maximal multimode overlap | HYP | coupling-integral argmax |
| 7 | coupling-integral maximum | HYP | RSCS-O.4 overlap |
| 8 | phase singularity / saddle | HYP | phase-field critical point |

Definitions 1–3 are implemented in frozen v2; 4–8 are pre-registered HYP with
observables (each becomes a falsification row H-2x for Agent 07). The monograph
presents them side-by-side and states that "the eye" is a **modeling choice
to be measured**, not a fact.

## 4. Spiral/cone/toroidal geometry — candidate paths, not assumed fields

v2's spiral/cone geometry (RGCS-M.30–37) is retained as **explicit candidate
paths** (geometry Established; physical-field relevance HYP, H-06/H-06a). The
monograph adds a toroidal candidate path alongside, with the same discipline:
the path is a geometric hypothesis for where a compact coordinate might live,
never an assumed internal field. No claim of a literal extra spatial dimension
in quartz (EXCLUSION_MATRIX).

## 5. Environmental and fixture factors — register

Surface finish, defects, inclusions, electrode geometry, fixture, hand
loading (v2 RGCS-M.40–45, loading), thermal state, humidity/adsorbates, and
ionic effects are enumerated as **declared inputs/uncertainties** in the
crystal database schema (§9). Hand loading and added modal mass are already
in v2 (H-08/H-08b); thermal (elastic-constant temperature drift ~1e-4/K) and
humidity/adsorbate mass loading are new DER uncertainty terms with pre-
registered magnitudes for Agent 07's controls.

## 6. Coupling, avoided crossing, parity, critical coupling, transfer matrices

All available now via RSCS operators (Agent 03), composed with crystal
geometry: strong/weak coupling and avoided crossing (RSCS-O.4, reproduces
RGCS-M.23–28), parity/supermodes (RSCS-O.5), critical coupling and isolation
metrics (RSCS-O.10), transfer-matrix cascades (RSCS-O.6). The crystal
application supplies the mode frequencies (from §1 anisotropic ladder) and
coupling estimates (fitted, DER); the operators do the algebra with the frozen
anti-Hermitian `K = i·2πg` convention.

## 7. Model selection against simpler baselines (the "earns its complexity" test)

Each crystal claim is compared to a simpler model, per the RSCS discipline:

| Phenomenon | Simpler baseline | When the richer model earns it |
|---|---|---|
| Axial ladder | scalar `v_L` rod | anisotropic model only when orientation is measured (§1) — else use the scalar + band |
| Compact spectrum | plain harmonic rod | only if the compact-coordinate fit (RGCS-M.13–14) beats a rod on held-out modes (H-01) |
| Coupled pair | two independent modes | only if `R_g = 2g/(Γ_A+Γ_B) ≳ 1` (strong coupling, RGCS-M.27) |
| Node location | metric center | measured node supersedes only if it moves predictions (H-07) |
| Anisotropy | scalar + 5% band | FEA/Christoffel only where the directional spread matters |

The monograph states, per example, what extra prediction/measurement the
richer model buys — or defers to the baseline.

## 8. OpenSCAD / FEA export — planned (Agent 08 boundary)

The anisotropic stiffness tensor and density are now available in SI
(`alpha_quartz_stiffness_pa`), which is exactly the material card an FEA
export needs. CAD updates (SCAD compact-render D-02 fix) and FEA geometry
export are scoped to Agent 08's software/hardware tranche; §1 supplies the
material model.

## 9. Crystal database and uncertainty-aware inverse design — schema

A crystal record carries: geometry (v2 fields), measured crystallographic
orientation (feeds §1), density, surface/defect/electrode/fixture descriptors
(§5), thermal/humidity state, and an `Uncertainty` (RSCS-C.12) on each. Inverse
design (given a target ladder, solve for geometry+orientation) reuses the v2
density-inverse solver (RGCS-M.7) with the anisotropic speed replacing the
scalar — an uncertainty-aware inverse because every input carries its σ. Schema
and solver are scoped with Agent 08 persistence.

## 10. Historical / source crosswalk

The JH/Vogel historical wave-speed and geometry statements are preserved
verbatim as SRC in `docs/HISTORICAL_SOURCE_CORPUS.md` (Agent 09) with the
adjacent mathematical translation stated (e.g. "a single crystal tone" →
the scalar `v_L` special case of §1; "the eye" → the node menu of §3). Source
wording is retained; the translation is labelled, never substituted for the
source, and never upgraded to physics.

## Deliverable status

- **Implemented & tested:** anisotropic propagation (§1, RSCS-O.17 +
  `rgcs_core.anisotropy`), quasi-mode taxonomy (§2), coupling algebra reuse
  (§6). 7 new unit tests + 1 regression, all green.
- **Framed & classified for downstream:** full mode taxonomy (Agent 09
  monograph), node menu falsification rows (Agent 07), CAD/FEA export and DB
  persistence (Agent 08), historical crosswalk (Agent 09).
- Manuscript source/PDF: deferred to Agent 09 (`manuscripts/rgcs_crystal_application/`).
