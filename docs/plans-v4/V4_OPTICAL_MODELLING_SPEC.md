# V4 Optical Modelling Spec (RSCS2-E.8/E.9; extends frozen `rgcs_core.optics`)

**Status:** PLANNING. Geometric ray optics first; wave-optics/FDTD only
as an **integration contract**, not a rebuilt Maxwell solver (brief +
DV4-012). **Safety:** no high-power-laser or human-exposure content;
the frozen D6/D7 envelope (class ≤3R, ≤5 mW, interlock) is binding on
any optical run description.

## 1. Geometric ray tracing (RSCS2-E.8, EST)

- Trace rays through the faceted anisotropic body: Snell entry/exit at
  tagged optical facets (`optical-entry` tags), straight segments inside
  (extends `rgcs_core.optics.ray_to_target` from single-segment to
  multi-surface), optical-path length and phase per segment.
- **Ordinary/extraordinary handling where feasible:** at each interface
  the ray may split into o/e polarizations with the α-quartz uniaxial
  indices (frozen `QUARTZ_N_O/N_E`); birefringent walk-off computed from
  the index ellipsoid. Where the full uniaxial ray-splitting is not yet
  implemented, the code declares the o-branch result and marks e-branch
  "not-modelled" (fail-loud, never silent single-index).

## 2. Polarization state

Jones vectors along a ray and Stokes states (reuse frozen
`PolarizationState` C.9 + Jones↔Stokes conversions); polarizer/λ4
elements as Jones matrices along the path. σ⁺/σ⁻ preparation supported
for the H-23 null design.

## 3. Photoelastic coupling (RSCS2-E.9, EST) — the elastodynamics link

The FE strain field S (from the elastic/piezo solve) perturbs the index
via Δ(1/n²)_I = p_IJ S_J (α-quartz photoelastic p, frozen
`QUARTZ_PHOTOELASTIC`). This turns a computed mode into a **predicted
optical-path-phase modulation** along a probe ray → the optical
diagnostics RSCS2-D.5 and the H-20 photoelastic-sideband prediction.
Absorption / photothermal deposition (RSCS2-E.6 link) is bounded, not a
heating claim.

## 4. Modulation & synchronization

Intensity and polarization modulation as time-varying Jones/intensity;
laser↔coil phase synchronization via the frozen v3 timing phase budget
(`rgcs_core.timing.phase_at_coordinate`). This is the modelling
counterpart of the Agent-14 optical branch — it *predicts* the
observables the bench would measure.

## 5. Wave-optics / FDTD — integration contract only

A documented interface contract (fields in/out, units, coordinate frame)
for an external solver (e.g. an FDTD package) to consume the FE index
field and return diffraction/near-field results. **v4 does not build a
Maxwell solver.** The contract lets a future contributor plug one in
without touching v4 internals.

## 6. Reciprocity posture (frozen D6-003)

Unbiased passive quartz is reciprocal; any modelled directional optical
asymmetry defaults to zero and is a HYP requiring the reversal battery
before any class change. A visualization showing circulating Poynting
flux does **not** establish a physical optical vortex (exclusion).

## 7. Tests

Snell round-trip vs closed form; OPL/phase vs `rgcs_core.optics`
(conservative-extension of the single-segment model); Jones↔Stokes
round-trip; photoelastic Δn magnitude vs frozen `photoelastic_index_shift`;
o/e split unit tests where implemented + fail-loud where not; reciprocity
null default; safety-envelope lint on any run description.
