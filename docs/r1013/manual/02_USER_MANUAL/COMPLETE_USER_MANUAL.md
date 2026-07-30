# Complete User Manual


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## 1. Purpose

This manual explains how to enter your own crystal data, calculate candidate resonant frequencies, run a full three-dimensional solve, understand the result, and preserve a reproducible record.

RGCS is not a single-frequency calculator. A crystal has many modes. Each method answers a different question.

## 2. Choose the level of calculation

### Level 1: quick estimate

Use length and a declared wave speed. This is fast and useful for screening.

### Level 2: directional material estimate

Use the alpha-quartz stiffness tensor, density, propagation direction, and orientation. This calculates three direction-dependent acoustic branches.

### Level 3: full three-dimensional elastic FEM

Use the complete shape, material tensor, orientation, mesh, and fixture. This calculates spatial mode shapes and frequencies.

### Level 4: coupled piezoelectric solve

Add electrodes and electrical boundary conditions. This calculates coupled mechanical and electrical modes.

### Level 5: comparison with measurements

Import an impedance, accelerometer, microphone, vibrometer, or optical response dataset. Match peaks to predicted modes with uncertainty and fixture controls.

## 3. Create a specimen

Use the desktop wizard or the target command:

```bash
rgcs crystal new my-crystal.json
```

Enter measured values. Do not use listing dimensions when you can measure the specimen directly. Keep listing values as source claims in a separate field.

## 4. Required fields

A quick estimate needs:

- specimen identifier;
- material identifier or declared wave speed;
- effective path length;
- boundary model.

A full geometry solve needs:

- total length;
- wide diameter;
- narrow diameter;
- facet count;
- both termination angles;
- diameter convention;
- angle convention;
- density or material record;
- orientation or an orientation-uncertainty ensemble;
- fixture model.

## 5. Geometry conventions

### Diameter convention

`across_vertices` means corner to opposite corner.

`across_flats` means flat face to opposite flat face.

The values are not interchangeable. A six-sided cross-section converts by a cosine factor.

### Angle convention

`face_slope` is the angle of the termination face relative to the base plane.

`axis_to_face` is the angle between the body axis and the face.

`apex_included` is the full angle through the apex.

Choose the convention used by the measuring tool or drawing.

## 6. Validate before calculating

```bash
rgcs crystal validate my-crystal.json
```

Validation checks:

- positive and finite measurements;
- wide diameter not smaller than narrow diameter;
- cap heights do not exceed total length;
- facet count is at least three;
- units are explicit;
- required fields exist for the requested model;
- uncertainty fields are non-negative;
- orientation is internally consistent;
- fixture fields match a registered fixture type.

## 7. Quick estimates

```bash
rgcs crystal estimate my-crystal.json --models axial-quarter,axial-half
```

The output must identify the exact formula. It must never print one unexplained number.

Example table:

| Model | Harmonic | Frequency | Evidence | Main limitation |
|---|---:|---:|---|---|
| axial quarter-wave | 1 | candidate | ANALYTIC_MODEL | ignores taper and anisotropy |
| axial half-wave | 1 | candidate | ANALYTIC_MODEL | assumes free or symmetric ends |
| directional QL | 1 | candidate | ANALYTIC_MODEL | one propagation direction |
| full elastic FEM | 1 | candidate | NUMERICAL_SIMULATION | mesh and fixture dependent |

## 8. Full FEM solve

Complete the geometry. Then:

```bash
rgcs crystal mesh my-crystal.json --clmax-mm 5 --out runs/my-crystal/mesh
rgcs crystal modes my-crystal.json --mesh runs/my-crystal/mesh --count 24 --fixture free --out runs/my-crystal/modes
```

A smaller `clmax-mm` creates a finer mesh. It normally increases runtime and memory use. Run a convergence ladder instead of trusting one mesh.

Suggested first ladder:

```text
8 mm
6 mm
4 mm
```

The result is converged only when the frequency and mode-shape changes are below the declared tolerance.

## 9. Orientation

Quartz is anisotropic. Unknown orientation is not a harmless blank.

Use one of these states:

- `known`: measured or supplier-certified orientation;
- `estimated`: low-cost polarization estimate with uncertainty;
- `unknown`: run an orientation ensemble;
- `assumed`: a modeling assumption, clearly labelled.

An unknown orientation should produce a range or ensemble. It should not silently default to C-axis alignment and report a precise answer.

## 10. Fixture

The same specimen can show different frequencies in different fixtures.

Common fixtures:

- free suspension;
- three-point cradle;
- soft pads;
- center clamp;
- end clamp;
- bonded electrodes;
- custom holder.

Record contact position, preload, material, and repeatability.

## 11. Result certificates

Every solve should create a certificate with:

- specimen hash;
- material hash;
- geometry and orientation;
- fixture;
- solver and mesh settings;
- software version and commit;
- frequency table;
- residuals and convergence;
- uncertainty;
- evidence class;
- warnings and refusals;
- artifact hashes.

## 12. Compare with a real measurement

Do not move the model after looking at the peak unless you create a new analysis branch and preserve the old prediction.

Use:

```bash
rgcs measurement import sweep.csv --specimen my-crystal.json --fixture fixture.json --out measurements/run-001
rgcs compare modes runs/my-crystal/modes measurements/run-001 --out comparisons/run-001
```

The comparison must consider frequency tolerance, Q, mode shape, sensor position, fixture modes, temperature, and multiple comparisons.

## 13. Frequency keys

RGCS can register values such as 4096 Hz, 528 Hz, 560 Hz, 925 Hz, 20.48 kHz, and 32.768 kHz as candidate drive or comparison values.

A registered key is not a predicted natural mode. Compare it prospectively:

1. Calculate the mode spectrum without forcing the key.
2. Measure the specimen without tuning the analysis to the key.
3. Calculate the distance between the key and the nearest mode.
4. Compare with matched control frequencies.
5. Preserve null results.

## 14. Dynamic-boundary research model

The R10.13 research model includes a 4096 Hz carrier, a 552 ms nominal macrocycle, a 1.953125 microsecond closure trim, and a 2.88 degree phase step. It also includes a 35-position aperture ring with 33 active positions and two gaps.

This model describes timed boundary changes, optical or acoustic gating, sidebands, ring-down changes, and energy supplied by the switch or pump. It does not establish Phryll, propulsion, or multiverse energy transfer.

## 15. Get help

Use:

```bash
rgcs doctor
rgcs crystal explain my-crystal.json
rgcs help error <ERROR_CODE>
```

The troubleshooting guide explains common errors in normal language.
