# R11 Earth Face and the Magnetic Zero That Is a Set

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the nine-stage geodetic-to-gradient-zero pipeline, the proper-rotation South-Up view, the frozen icosahedron, and the four-axis alias set.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md), [R11_PLANETARY_ROOT_REPORT.md](R11_PLANETARY_ROOT_REPORT.md)
**Related code / tests:** `r11/earthface.py`, `tests/v6/test_r11_earthface.py` (44 tests), `tests/v6/test_r11_redteam.py`
**Known limitations:** the field is a declared tilted-centred dipole toy model in dimensionless model units. No magnetometer was read, no survey was made, no site was visited.
**Next review trigger:** substitution of a real published field model for the declared toy dipole, or any fixing of the scalar, sign, altitude or epoch on independent grounds.

## Verdict

`r11.earthface.earthface_report()["verdict"]` returns:

> **`EARTH_FACE_LOCAL_ZERO_SPECIFIABLE_WITH_ALIASES`**

Specifiable, with aliases. A specifiable zero is not a detected one.

## The pipeline, all nine stages

The module walks one explicit chain and refuses to pretend it is shorter:

```
geodetic (lat, lon, h)
  -> ITRF at a DECLARED epoch
  -> ECEF on the WGS-84 ellipsoid
  -> South-Up PROPER rotation  R = diag(1, -1, -1)
  -> city geocentric ray
  -> frozen canonical icosahedron face
  -> ray-face intersection (SET-VALUED on edges and vertices)
  -> local face frame
  -> horizontal magnetic-gradient direction (candidate zero)
```

Four of those stages are pure arithmetic and are checkable:
`geodetic_to_ecef`, `south_up`, `ray_face_intersection`, `local_face_frame`.

## The arithmetic

**Geodetic to ECEF** is closed-form on WGS-84 and is asserted against known
values: `lat=0, lon=0, h=0` lands at `x = a`; the pole lands at `z = b`.

**South-Up is a proper rotation.** `SOUTH_UP_ROTATION = diag(1, -1, -1)`. Its
determinant is `(+1)(-1)(-1) = +1` and `R Rᵀ = I`, so
`is_proper_rotation(SOUTH_UP_ROTATION)` returns **True**. Looking at the planet
from the south is a *change of viewpoint*, not a reflection. A mirror
(`det = -1`) would silently swap handedness, and `refuse_mirror_view` raises
rather than allow it. This distinction is load-bearing: an accidental
reflection would flip every chirality downstream while producing numbers that
still look reasonable.

**The icosahedron is frozen.** `CANONICAL_ICOSAHEDRON` has 12 vertices and 20
faces and is fixed before any target data is loaded.
`refuse_rotate_after_load` raises if it is rotated afterwards, because a
polyhedron free to spin can be made to point anywhere. This is red-team
attack 1.

**Ray-face intersection is set-valued.** A ray that lands on an edge or a vertex
hits more than one face, and `ray_face_intersection` returns all of them rather
than choosing. `EDGE_TOLERANCE` governs the boundary case.

## The choices — and the ALIAS SET

The final stage is not one answer. "The horizontal magnetic-gradient zero" is a
direction only once four things are fixed **independently of the result**:

1. **which scalar** the gradient is taken of;
2. **which sign** of the resulting direction is meant — a zero direction is a
   line, and `+d` and `-d` both lie on it;
3. **which altitude** the field is evaluated at;
4. **which epoch** the field model is evaluated for.

The six unresolved scalars are `TOTAL_INTENSITY`, `HORIZONTAL_INTENSITY`,
`VERTICAL_COMPONENT`, `DECLINATION`, `INCLINATION`, `POTENTIAL`. The module
defaults are `DEFAULT_SIGNS = (1, -1)`, `DEFAULT_ALTITUDES_M = (0.0, 1000.0)`
and `DEFAULT_EPOCHS = ('2020.0', '2026.0')`.

So the alias set has

> **6 scalars × 2 signs × 2 altitudes × 2 epochs = 48 members**

and `gradient_zero_alias_set` returns all 48. `refuse_single_zero_direction`
raises whenever a caller asks for one unique direction while any of the four
axes is still unspecified. Both vector signs are preserved unless a sign is
fixed on independent grounds (`both_signs_preserved: true`).

This is the whole point of the module. Fixing the four axes *after* seeing
which combination lands somewhere agreeable is exactly how a search space gets
reported as a discovery.

## The control site

`SEDONA_FACE_CONTROL` is a public **control** location used to exercise the
pipeline, declared as `role='CONTROL'`, frame `ITRF2020`, epoch `2026.0`.
Running the pipeline on it yields a unique candidate face (face index 10), an
orthonormal face frame, `icosahedron_frozen: True`, and `alias_count: 48`.

Naming a control makes no claim about it. It is a control and nothing more.

## Field model status

`FIELD_MODEL = TILTED_CENTRED_DIPOLE_DECLARED_TOY_MODEL` in
`MODEL_UNITS = DIMENSIONLESS_MODEL_UNITS`. The dipole tilt and its 2020
longitude with a declared drift rate are model constants, not measurements.
Evidence class is `ANALYTIC_MODEL`; `measured_here` is `"nothing"`.

## Red-team coverage

Attacks 1, 2 and 3 target this module directly and all three fail with a typed
`EarthFaceError` (see `tests/v6/test_r11_redteam.py`): rotating the frozen
solid after loading target data; choosing the magnetic scalar target-by-target;
and flipping the gradient sign target-by-target. Attack 3 additionally asserts
that more than one alias survives, i.e. that both signs really are retained
rather than silently collapsed.

## Non-claims

This document does not say a magnetic zero exists at any site, that any site
sits on a meaningful face, or that the icosahedron is a feature of the Earth.
No magnetometer was read. No location was decoded, named, or implied — the
control site is a control. No ship, no transmission, no terraforming system, no
new particle and no physical crystal effect follow from anything here.

PHYSICAL_VALIDATION_NOT_CLAIMED
