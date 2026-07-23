# R11 Planetary Root Report — Body-Specific, Epoch-Bound, Unresolved

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the body-specific root framework, its field-class taxonomy, seven competing constructions, the preregistered circularity test, and the epoch requirement.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md)
**Related code / tests:** `r11/planetroot.py`, `tests/v6/test_r11_planetroot.py` (62 tests), `tests/v6/test_r11_redteam.py`
**Known limitations:** every field grid used is synthetic and labelled `NUMERICAL_SIMULATION`; published spherical-harmonic coefficient sets are `BLOCKED_MISSING_DATA`. No root is located, and none is claimed to be physical.
**Next review trigger:** arrival of a real published magnetic-model coefficient set for any modelled body.

## Verdict

`r11.planetroot.planetroot_report()["verdict"]` returns:

> **`PLANETARY_ROOT_FRAMEWORK_SPECIFIABLE`**

Specifiable. Not located, not measured, not physical. The public alias for the
object under study is **`PLANETARY_ROOT_CANDIDATE_A`**, whose status is
`CANDIDATE_HYPOTHESIS`.

## Field-class taxonomy

A magnetic "root" is a candidate origin point for an address frame, derived
from a body's field. The module refuses to treat the six bodies as one physics.
Five field classes are defined, and the assignment is:

| Body | Field class |
|---|---|
| EARTH | `INTRINSIC_DYNAMO_FIELD` |
| MERCURY | `OFFSET_OR_MULTIPOLE_DYNAMO` |
| JUPITER | `OFFSET_OR_MULTIPOLE_DYNAMO` |
| MARS | `CRUSTAL_REMANENT_FIELD` |
| MOON | `CRUSTAL_REMANENT_FIELD` |
| VENUS | `INDUCED_SOLAR_WIND_FIELD` |

The fifth class, `NO_RESOLVED_FIELD_MODEL`, exists for bodies the module
declines to model at all.

The consequence is enforced, not merely noted. A rule that means "the dynamo's
strongest radial expression" on Earth means "whichever patch of ancient crust
happens to be most magnetised" on Mars. Carrying the Earth recipe across is
equivocation, and `refuse_earth_method_on_non_dynamo_body` raises for MARS,
MOON and VENUS. Separately, `refuse_surface_assumption_for_gas_giant` raises
for JUPITER: there is no solid surface to place a point on.

## Seven competing constructions

The module implements seven root constructions and dispatches them side by
side rather than picking one:

1. `RADIAL_FIELD_EXTREMUM` — strongest radial-field extremum
2. `HORIZONTAL_GRADIENT_EXTREMUM` — strongest horizontal-gradient extremum
3. `STABLE_CLOSED_CONTOUR` — stable closed contour around an extremum
4. `NULL_SADDLE_NETWORK` — magnetic null / saddle network
5. `HARMONIC_PRINCIPAL_AXIS` — principal-axis decomposition of low-degree
   spherical harmonics
6. `CRUSTAL_ANOMALY_CENTROID` — crustal-anomaly centroid, for bodies with no
   global dynamo
7. `SPIN_AXIS_NULL_CONTROL` — **the null control**: spin axis plus prime
   meridian only, using no magnetic data whatsoever

Construction 7 is the load-bearing one. If a magnetic construction cannot beat
a root built from geometry alone, the magnetism was not doing the work.

Each construction declares which field classes it is applicable to, so an
inapplicable pairing is a typed error rather than a silently plausible number.

## The circularity test, preregistered

A fitted contour may not be called a circle until it passes a test whose
tolerance was fixed **before any data was seen**. The registered parameters,
read from `PREREGISTERED_CIRCULARITY`:

- statistic: `rms radial residual / fitted radius`
- `tolerance_normalised_rms`: **0.05**
- `min_points`: **8**
- `registered_before_seeing_data`: **true**

`refuse_circle_without_test` raises if the word "circle" is used before the
test runs. The test module exercises both directions — it must pass a genuine
circle and fail a deliberately non-circular contour — so the test has power and
is not a rubber stamp.

## The universal anomaly circle is UNSUPPORTED

The claim that a single anomaly circle, of some shared radius, appears on every
body and can serve as a universal root is carried in the report with
`status: "UNSUPPORTED"`. The module's own stated reason:

no such circle has been demonstrated on any two bodies here, let alone all of
them; the field classes differ, the features differ, and the epochs differ. The
claim is recorded so that it can be tested, not assumed.

## The epoch requirement

Every field modelled here moves. `KNOWN_DRIFTING_FEATURES` names six:
`NORTH_MAGNETIC_DIP_POLE`, `SOUTH_MAGNETIC_DIP_POLE`, `SOUTH_ATLANTIC_ANOMALY`,
`NON_DIPOLE_WESTWARD_DRIFT_FEATURE`, `ECCENTRIC_DIPOLE_CENTRE`, and
`GREAT_BLUE_SPOT`.

The rule that follows is short: **a root that drifts cannot be a timeless
address.** A certificate with no `magnetic_model_epoch`, or one whose feature
is on the drifting list, is refused the word "timeless" by
`refuse_timeless_root`. What `certify_root` will issue instead is an
*epoch-bound* certificate: valid for a stated model, at a stated epoch, with a
stated uncertainty, and no further.

## Look-elsewhere discipline

`refuse_target_dependent_selection` raises when a construction method is chosen
after the target is in view. Picking the rule that lands nearest the answer you
already wanted is the look-elsewhere sin, not a result. In the red team this is
attack 2, and it fails with a typed `PlanetRootError`.

## Data status

`REAL_MODEL_STATUS` is `BLOCKED_MISSING_DATA`: published spherical-harmonic
coefficient sets and crustal anomaly maps for these bodies are not bundled in
this environment, so every grid used is synthetic and labelled
`NUMERICAL_SIMULATION`. Body parameters are `ESTABLISHED_SOURCE`; the
constructions are `ANALYTIC_MODEL`. No result from a real magnetic model is
reported anywhere in the module.

## Non-claims

This module does not locate any body's magnetic root. It does not claim any
constructed point is physical. It does not claim a universal anomaly circle. It
does not license carrying an Earth dynamo recipe to Mars, the Moon or Venus. It
does not place a root on a gas giant's non-existent surface. It does not call
any root timeless. And nothing here implies a planetary terraforming system, a
ship, a transmission, or a decoded location.

PHYSICAL_VALIDATION_NOT_CLAIMED
