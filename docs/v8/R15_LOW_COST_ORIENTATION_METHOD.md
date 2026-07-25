# R15 P05 — The Low-Cost Orientation Method (No XRD Assumed)

**Authority:** RGCS R15 / v8.0.0 (candidate) — Tranche T2 Specimen Authority
**Scope:** a synthetic forward model from a crystal orientation to cheap
optical/goniometric observables, an inverse solver that recovers a planted
orientation within a stated error budget, and the explicit alias/handedness
caps that a diffraction-free bench cannot lift.
**Branch:** `v800-r15`
**Related code / tests:** `r15/orientation.py`, `tests/v8/test_orientation.py`
(27 tests). Extends `r13/crystalframe.py` (point-group-32 symmetry
operators, reciprocal frame) and `r13/magroot.py` (orientation-from-vector,
alias-set idea). Governance from `r15/claims.py`.
**Receipt:** `docs/v8/receipts/P05.json`
**Known limitations:** every observation here is deterministic simulator
output in dimensionless model units. No goniometer is read, no polarizer is
turned, no conoscopic figure is photographed, and no specimen is mounted.
The recovered orientation is a `MODEL_PREDICTION`; the observations are a
`SYNTHETIC_OBSERVATION`.
**Next review trigger:** substitution of a real bench dataset for the
declared synthetic one, or any diffraction acquisition that would lift the
symmetry alias, the c-axis sign, or the handedness cap.

## Verdict

`r15.orientation.orientation_report()["verdict"]` returns:

> **`LOW_COST_ORIENTATION_ALIAS_LIMITED_NO_XRD`**

An orientation recovered from cheap data, limited by aliases, and never
promoted to a measurement.

## The mission

Fixing the crystallographic orientation of a specimen is normally the job of
single-crystal X-ray diffraction — a Laue back-reflection or an indexed
four-circle scan reads the lattice directly. R15's specimen authority must
serve an operator who does **not** own that instrument. This module builds
the strongest orientation workflow a cheap, accessible bench can support and
is scrupulous about the three things that bench can never recover: which of
the six symmetry-equivalent orientations is the true domain, the sign of the
optic axis, and the handedness.

The material is alpha-quartz (trigonal, point group `32`, enantiomorph pair
`P3_121` / `P3_221`), whose lattice frame and proper-rotation symmetry are
reused from R13 rather than re-derived.

## What is represented, separately

The orientation state (`OrientationState`) carries each degree of freedom
apart, exactly as the phase prompt requires:

- **c-axis / optic axis** — a unit direction in the lab frame. For uniaxial
  quartz the optic axis *is* the c-axis, and it is an undirected **line**.
- **a-axis azimuth** — the rotation about the c-axis, in degrees.
- **handedness** — `RIGHT` (`P3_121`), `LEFT` (`P3_221`), or `UNDETERMINED`,
  held separately because no observation here constrains it.
- **facet normals** — the six rhombohedral face normals, *derived* from the
  frame (never stored), so they cannot drift out of sync.
- **uncertainty** — carried by the error budget, not baked into the state.

## The synthetic forward model (orientation → observable)

`forward_observation(state, mode, noise_deg, seed)` maps an orientation to
three cheap observables, deterministically in `(state, noise_deg, seed)`:

| Evidence type | Observable | Constrains | Cannot constrain |
|---|---|---|---|
| `POLARIZATION` | extinction azimuth (mod 90°) between crossed polarizers | projected optic-axis azimuth | tilt, c-sign, handedness |
| `EXTINCTION` | extinction contrast vs. tilt | optic-axis tilt magnitude | azimuth sense, c-sign, handedness |
| `CONOSCOPIC` | melatope offset / optic-axis tilt | optic-axis polar tilt | c-sign, handedness, a-azimuth |
| `GEOMETRY` | goniometric facet normals (6-face `32` orbit) | c-line + a-azimuth up to group | which alias, c-sign, handedness |
| `CERTIFICATE` | the emitted orientation certificate | — (capped, see below) | — |

The four acquisition modes (`SYNTHETIC`, `REPLAY`, `REAL`,
`FAULT_INJECTION`) are kept distinct; `REAL` is refused, because no physical
goniometer exists here.

The facet normals are the **full point-group-32 orbit** of one generating
rhombohedral face (`r13.crystalframe.QUARTZ_FRAME.reciprocal_vector(1,0,1)`
carried through all six proper rotations). Because the orbit is closed under
the group, the set is symmetric about the c-**line** — the geometric fact the
solver exploits.

## The inverse solver (POWER)

`solve_orientation(obs, budget)` recovers the planted orientation:

1. **c-axis** = the isolated eigenvector of the facet-normal scatter matrix
   `Σ nᵢnᵢᵀ`. The faces lie on two cones symmetric about the c-line, so one
   eigenvalue is isolated and its eigenvector is the c-axis — returned
   **sign-free**, an undirected line.
2. **a-azimuth** = a representative face azimuth about that axis.
3. **residual** = the largest deviation of any observed face from the fitted
   shared cone half-angle at its own azimuth (zero on a clean orbit, growing
   with per-face noise).

POWER, from `tests/v8/test_orientation.py`: a planted orientation is
recovered so that the recovered c-axis line matches the planted one within
the expanded uncertainty, and noiselessly to `< 1e-6°`.

## The error budget

`build_error_budget()` returns a record conforming to
`r15/schemas/error_budget.schema.json`:

| Component | Type | 1σ (deg) |
|---|---|---|
| `goniometer_facet_angle` | B | 0.5 |
| `polarizer_extinction_angle` | B | 1.0 |
| `conoscopic_tilt_angle` | B | 1.5 |

Combination is **root-sum-of-squares** (≈ 1.871° combined standard
uncertainty); the coverage factor is `k = 2`, giving an expanded uncertainty
of ≈ 3.742°. A fit whose residual exceeds the expanded uncertainty is
**refused** — noisier data than the budget allows yields no orientation, not
a worse one.

## The three intrinsic ambiguities (surfaced, never hidden)

1. **Symmetry alias set.** The six proper rotations of point group `32`
   (`r13.crystalframe`) map any solved orientation onto five others with
   *identical* observations — the alias idea of `r13.magroot`.
   `alias_set()` returns all six; `refuse_orientation_as_unique()` refuses to
   collapse them. A cheap-bench fit names an equivalence class, not a point.

2. **Optic-axis 180° ambiguity.** Among those six aliases the three
   two-folds send the c-axis to `−c`, so `distinct_c_axes()` always returns
   both ends of the optic-axis line. Linear birefringence, the conoscopic
   figure and the face angles are identical for `+c` and `−c`.
   `refuse_optic_axis_polarity()` raises.

3. **Handedness.** Every observable here is achiral: `P3_121` and its `P3_221`
   enantiomorph share the same face angles, birefringence and tilt.
   Handedness is therefore returned as `UNDETERMINED` regardless of what was
   planted; `refuse_handedness_from_geometry()` raises. **Handedness is not
   inferred from the c-axis alone.**

## The orientation certificate and its cap

`generate_orientation_certificate()` runs the whole workflow and emits a
certificate with the recovered orientation, the alias set, the residual, the
error budget, and a **confidence** capped at `PRESUMPTIVE`
(`NO_XRD_CONFIDENCE_CAP`). The two confirmed levels (`XRD_CONFIRMED`,
`XRD_REPLICATED`) are unreachable without diffraction;
`refuse_certificate_confirmed_without_xrd()` raises if one is requested.
Because the observation binds an uncertainty and a protocol but no
instrument, calibration, specimen, fixture, clock, environment or raw
artifact, the evidence level caps below a physical measurement (`E4`) per
`r15.claims`.

## Exactly what would upgrade the confidence

`additional_evidence_to_upgrade()` names the physical acquisitions — every
one **`PREREGISTERED_NOT_RUN`**:

| Ambiguity | Acquisition that resolves it | Unlocks |
|---|---|---|
| point-group-32 alias set | indexed single-crystal diffraction (Laue or four-circle) selecting one domain | `XRD_CONFIRMED` |
| optic-axis sign (180°) | diffraction polarity determination (anomalous dispersion / Laue back-reflection) | `XRD_CONFIRMED` |
| handedness | chiral probe: optical-rotation sign, etch-figure symmetry, or anomalous-dispersion XRD | `XRD_CONFIRMED` |
| single-run non-replication | independent remounted determination on a second instrument | `XRD_REPLICATED` |

## Required tests, mapped

| Phase-prompt requirement | Test(s) |
|---|---|
| A planted orientation is recovered | `test_planted_orientation_is_recovered_within_budget`, `test_noiseless_recovery_is_essentially_exact` |
| A 180-degree ambiguity remains explicit | `test_optic_axis_is_a_line_both_signs_in_alias_set`, `test_refuse_optic_axis_polarity_always_raises` |
| Handedness is not inferred from c-axis alone | `test_handedness_is_never_recovered_regardless_of_plant`, `test_enantiomorphs_are_indistinguishable_on_the_bench`, `test_refuse_handedness_from_geometry_always_raises` |
| No-XRD certificates are capped | `test_certificate_confidence_is_capped_without_xrd`, `test_refuse_confirmed_certificate_without_xrd_raises` |
| Negative / refusal paths | `test_refuse_orientation_as_unique_raises`, `test_noise_beyond_budget_is_refused`, `test_real_acquisition_mode_is_refused` |
| Determinism | `test_forward_observation_is_deterministic`, `test_solve_is_deterministic` |
| Governance (nothing measured) | `test_report_claims_nothing_measured`, `test_certificate_evidence_is_capped_below_physical` |

## What this does not say

It does not measure an orientation: the observations are deterministic
simulator output, not a goniometer, polarizer or camera reading of a mounted
specimen, and the recovered orientation is a `MODEL_PREDICTION`. It does not
claim a unique orientation — point group `32` leaves a six-member symmetry
alias set including both signs of the optic-axis line. It does not infer the
c-axis sign or the handedness, which are invisible to these achiral
observations. And it does not issue an XRD-confirmed certificate: without
diffraction the confidence is capped at `PRESUMPTIVE`. **Nothing here is
measured. `PHYSICAL_VALIDATION_NOT_CLAIMED`.**
