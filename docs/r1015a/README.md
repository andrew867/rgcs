# Scale A 4096 Hz Mechanical Crystal Candidate (R10.15A)

Design id: `SCALE_A_4096HZ_SHEAR_463P867_SIX_SIDED`
Status: `GEOMETRY_AND_HALF_WAVE_PROXY_ONLY`. Publication HOLD.

## What this lane is, and what it is not

This is a **mechanical bulk-acoustic** candidate: a six-sided
Vogel-terminated quartz body whose first-order half-wave *shear* path
lands on 4096 Hz.

It is a **separate lane** from `rgcs_surface_wave`, which studied an
*electromagnetic* annular surface-wave device. That study returned a
negative result and it is **frozen**:

- the tested annular electromagnetic eigenmode was about 1.150903 GHz;
- 4096 Hz was falsified as the electromagnetic carrier for that
  geometry;
- resolving 16 Hz sidebands required an unattainable Q for that model;
- reversed modulation produced zero nonreciprocal contrast;
- lateral force tracked ordinary mask asymmetry and closed against the
  support;
- manufactured solutions, independent formulations, and privacy gates
  passed.

Nothing in this lane reopens any of that. The two lanes share only the
number 4096, and **a shared number is not evidence**. `r1015a` never
imports `rgcs_surface_wave` (test-enforced), and
`assert_em_boundary()` refuses to let 4096 Hz become an
electromagnetic carrier again without all four of: a new geometry, a
new eigenproblem, declared holdout criteria, and an explicit executed
result.

## The number

```text
L_eff = v_phase / (2 f N) = 3800 / (2 x 4096) = 475/1024 m
      = 463.8671875 mm exactly
```

This is a **dyadic rational**, so it is exact in binary floating point
and the package computes it with `fractions.Fraction` throughout.

`463.8671875 mm` is an **exact first-order half-wave path candidate
under a scalar 3800 m/s shear proxy**. It is:

- **not** a measured resonance;
- **not** the final physical tip-to-tip cut length;
- a one-dimensional model applied to a tapered, anisotropic, 3D body.

The longitudinal branch (5700 m/s, 695.80078125 mm) is a **control
branch, not a second preferred answer**. It exists so that any result
appearing on both branches can be recognised as branch-independent and
therefore not evidence for either.

## Derived geometry (reproduces the supplied spec to zero difference)

| quantity | value |
|---|---:|
| tip-to-tip length | 463.867187500 mm |
| wide / narrow diameter | 95.152243590 / 59.470152244 mm |
| Rx cap (51.843 deg) | 52.439501540 mm |
| Tx cap (60.000 deg) | 44.602614183 mm |
| central tapered shaft | 366.825071777 mm |
| idealized volume | 1586.310842 cm3 |
| idealized mass at 2.65 g/cm3 | 4203.724 g |

Every one of these is recomputed from first principles by
`r1015a.design` and cross-checked against the supplied JSON; the
maximum deviation is exactly `0.0`.

## Two findings worth acting on

**1. The target mode is not isolated.** The analytic screen puts the
second free-free flexural mode at about 4366.6 Hz, only **+6.6 %** from
the 4096 Hz target. Flexural modes are easy to excite and easy to
mistake for the intended mode on an impedance sweep, so **mode
identity** must be established by full-field mapping or a 3D
eigenvector, not by a peak position. The flexural figure is an
Euler-Bernoulli *upper bound*; for this thick body (L/d = 6) Timoshenko
corrections push it **down**, i.e. **closer** to the target.

**2. The 3:2 velocity ratio is an artifact.** The two proxy velocities
are in an exact 3:2 ratio (5700/3800), which makes the extensional and
shear ladders coincide at 12288 Hz and every third shear mode. Real
alpha-quartz has a ratio near 1.9 and produces no such coincidence.
**Any "harmonic alignment" read off this screen is an artifact of two
round proxy numbers and must not be reported as structure.**

## The physical length is not solved

```text
L_physical = L_effective + termination + electrode + fixture
             + temperature + machining trim
```

`physical_length_budget()` returns `None` and refuses to total the
budget while any term is unknown, because returning a number there
would present the effective path as a cut sheet. All five terms are
currently unknown.

Velocity uncertainty dominates everything else: the path is exactly
linear in velocity, so a +-5 % velocity band gives a **+-23 mm** length
band on this body, far larger than any machining tolerance.

## Before this becomes a fabrication drawing

Fourteen items are listed in the design spec. The seven that the
software treats as **mandatory typed inputs**, and refuses to solve
without, are: handedness, c-axis direction, a-axis azimuth, electrode
condition, fixture, temperature, and velocity uncertainty. A
`finite_load` electrode also needs its impedance, and a declared
fixture needs its contacts.

## Commands

```bash
rgcs scale-a design            # exact proxy + derived geometry
rgcs scale-a length-budget     # refuses while terms are unknown
rgcs scale-a modes             # mode crowding and identity risk
rgcs scale-a sweep             # velocity uncertainty + branch control
rgcs scale-a fem-profile       # what the 3D solve still needs
rgcs scale-a verify            # SCAD + JSON verification
rgcs scale-a em-boundary       # the frozen R10.15 EM result
```

Add `--format json` for the machine interface.

## Reference model

`vogel_parametric_crystal_models_v7_scaleA_4096Hz.scad` is imported
under the reference-model authority. OpenSCAD is **not installed** in
this environment, so verification level is **`STATIC_INSPECTION_ONLY`**:
delimiter balance, both required presets, exact numbers, ASCII
cleanliness, 11 modules and 19 functions all pass, and the file hashes
to `cb288b2b…`. **No render is claimed.** F5/F6 render and STL export
must be performed where OpenSCAD is available before this is treated
as render-verified.

## Nonclaims

This lane does not establish a measured 4096 Hz quartz resonance, a
Vogel termination as an acoustic mode purifier, 4096 Hz as an
electromagnetic carrier, propulsion, anomalous force, gravity
modification, free energy, or Phryll as a measured quantity.
