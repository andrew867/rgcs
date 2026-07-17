# Specimen metrology protocol (Agent C05)

Coverage: **G001–G030** (metrology side). Gates: **G12, G25**.
Status: `PROTOCOL_READY_HARDWARE_REQUIRED`.
Implementation: [`rscs2_core/metrology.py`](../../rscs2_core/metrology.py).
Tests: [`tests/v4/test_v4x_depth_metrology_bvd_apparatus.py`](../../tests/v4/test_v4x_depth_metrology_bvd_apparatus.py).

## Nothing here has been measured

No specimen has been weighed, scanned, or XRD-oriented. Every value in
the specimen registry is a **seller claim** (`SRC`). This document is
the protocol that would produce measurements, plus the code that
refuses to let a seller claim pretend to be one.

**Audit note.** The v4.2.0 ledger pointed C05 at
`harmonic_family.specimen_registry()`. That is a registry — a table of
declared values — not a metrology pipeline. The v4.2.1 audit recorded
this as registry-only work labelled as an implemented workstream, and
built the pipeline the prompt required.

## Seller versus measured: enforced in code

The single most important rule in C05 is that seller values and
measured values never merge. `specimen_record()` keeps them in
separate blocks and:

- refuses a `measured_values` block without `measurement_provenance`
  (instrument, calibration_id, operator, timestamp);
- refuses an unknown instrument;
- keeps `seller_values` immutable — a measurement never overwrites a
  claim, it sits beside it.

`seller_vs_measured_delta()` reports the disagreement at its exact
value and does **not** reconcile it. A vendor saying 110.0 mm and a
caliper saying 109.7 mm is information; averaging them destroys it.

The vendor "100 nm" precision claim stays `SRC` until independently
measured (ORPHAN-014).

## Required instruments and resolutions

| Instrument | Quantity | Resolution | Calibration artifact |
|---|---|---|---|
| caliper | length | 0.01 mm | gauge block |
| micrometer | width | 0.001 mm | gauge block |
| balance | mass | 0.001 g | OIML class E2 |
| goniometer | facet angle | 0.1 deg | optical flat |
| camera | image scale | 0.05 px/mm | checkerboard |
| scanner | surface | 0.05 mm | sphere artifact |
| XRD | c-axis orientation | 0.05 deg | reference quartz |

## Procedure

1. Calibrate every instrument; record `calibration_id`.
2. Calibrated multi-angle photography against a scale target.
3. Tip-to-tip length — caliper, 3 repeats, ≥2 operators.
4. Widths at ≥5 declared axial stations — micrometer.
5. Facet count and rotation — goniometer + photograph.
6. Cap heights and included apex angles.
7. Mass — balance, 3 repeats.
8. Volume — displacement or scan-derived; method declared.
9. Density and the mass-volume consistency check.
10. Polish / chip / crack / inclusion / rutile map.
11. Mount points and electrode coverage.
12. XRD c-axis and lateral axis — `INTERFACE_ONLY` until hardware.
13. Temperature and humidity at measurement time.
14. Seller values recorded separately, never overwritten.

## Consistency checks that can fail

`mass_volume_consistency()` compares the implied density against alpha
quartz (2.648 g/cm³, EST) at 2% tolerance and returns one of:

- `CONSISTENT_WITH_QUARTZ`
- `LOW_DENSITY: voids/fractures, wrong volume, or not quartz`
- `HIGH_DENSITY: dense inclusions, wrong volume, or not quartz`

It never rescales a measurement to fit. A specimen that fails this
check is telling you something.

Uncertainty propagates first-order:
`(u_rho/rho)² = (u_m/m)² + (u_V/V)²`, and the apex angle carries the
propagated uncertainty from both the cap height and the width.

## Scan-to-mesh refuses to repair

`scan_to_mesh()` reports a point cloud as usable only if it is dense
enough (median nearest-neighbour spacing ≤ target) and finite.
Malformed or sparse scans return `INSUFFICIENT_RESOLUTION`.

**No hole filling. No smoothing.** A repaired scan is a model, and if
it entered the solver it would carry the authority of a measurement
while being a guess. `ideal_vs_scanned()` likewise reports the
deviation without adjusting either geometry to match the other.

## Failure conditions

- Inter-operator spread exceeds 5× the instrument resolution → the
  protocol is not reproducible and the data are not usable.
- Implied density deviates >2% from quartz without an inclusion
  explanation → the specimen or the measurement is wrong.
- XRD unavailable → orientation stays `INTERFACE_ONLY`. Axes are
  **never** inferred from facet geometry (see
  [XRD_ORIENTATION_CONTRACT.md](XRD_ORIENTATION_CONTRACT.md)).

## Blocker

`PROTOCOL_READY_HARDWARE_REQUIRED` — requires physical instruments and
specimens in hand. Andrew is the only one who can lift this.
