# Scale A 4096 Hz Shear-Path Vogel Geometry Candidate

## Frozen nominal geometry

| Field | Value |
|---|---:|
| Design identifier | `SCALE_A_4096HZ_SHEAR_463P867_SIX_SIDED` |
| Status | Geometry and half-wave proxy only |
| Target frequency | 4096 Hz |
| Working acoustic branch | Shear proxy |
| Working phase velocity | 3800.000 m/s |
| Exact half-wave path | 463.867187500 mm |
| Rounded project name | 463.867 mm |
| Facets | 6 |
| Rx face slope | 51.843 degrees |
| Tx face slope | 60.000 degrees |
| Diameter convention | Across vertices |
| Length / average diameter | 6.000 |
| Wide / narrow diameter | 1.600 |
| Wide diameter | 95.152243590 mm |
| Narrow diameter | 59.470152244 mm |
| Rx cap height | 52.439501540 mm |
| Central tapered shaft | 366.825071777 mm |
| Tx cap height | 44.602614183 mm |
| Idealized volume | 1586.310842 cm3 |
| Idealized mass at 2.65 g/cm3 | 4203.724 g |
| Alternate longitudinal path | 695.800781250 mm |

The principal relationship is:

```text
L_eff = v_phase / (2 f N)
```

For the frozen first-order shear proxy:

```text
L_eff = 3800 m/s / (2 x 4096 Hz x 1)
      = 463.867187500 mm
```

## What the CAD number means

`463.8671875 mm` is the calculated **effective half-wave path candidate** under a
scalar 3800 m/s shear-velocity proxy.

The v7 file initially sets the physical tip-to-tip CAD length equal to this
effective path. That equality is a starting hypothesis, not a final cut sheet.

The finished physical length may need a correction:

```text
L_physical = L_effective
           + termination correction
           + electrode correction
           + fixture correction
           + temperature correction
           + machining trim allowance
```

The SCAD therefore exposes:

- `effective_path_correction_mm`
- `nominal_body_minus_effective_path_mm`
- velocity and branch controls
- operating temperature bookkeeping
- blank allowances
- axis and mode-reference helpers

## Required data before manufacturing

The following are mandatory before this becomes a fabrication drawing:

1. Crystal handedness.
2. Crystallographic c-axis direction.
3. a-axis azimuth relative to the six facets.
4. Full rotated elastic, piezoelectric and dielectric tensors.
5. Selected shear polarization and propagation direction.
6. Electrode geometry and electrical boundary condition.
7. Mount contact locations, preload and support compliance.
8. Temperature-frequency model.
9. Termination reflection and mode-conversion model.
10. Full 3D eigenmode ensemble with uncertainty.
11. Manufacturer kerf, polish and defect allowances.
12. X-ray, polarization or equivalent axis-orientation receipt.
13. Impedance, ringdown and full-field mode mapping after cutting.
14. Trim plan with irreversible-step limits.

## R10.15 authority boundary

Claude's R10.15 result must remain frozen:

- the tested annular electromagnetic surface-wave mode was approximately
  1.150903 GHz;
- 4096 Hz was excluded as the electromagnetic carrier for that geometry;
- the 16 Hz modulation did not resolve against its linewidth;
- lateral force closed as ordinary asymmetric reaction force.

This Scale A file opens a separate **mechanical bulk-acoustic candidate**. It
does not modify or invalidate the R10.15 electromagnetic result.

## Nonclaims

This design does not establish:

- a measured 4096 Hz quartz resonance;
- a Vogel termination as a mode purifier;
- 4096 Hz as an electromagnetic surface-wave carrier;
- anomalous force;
- gravity modification;
- propulsion;
- free energy;
- Phryll as a measured physical quantity.
