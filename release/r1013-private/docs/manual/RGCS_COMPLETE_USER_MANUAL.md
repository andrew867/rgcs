# RGCS Complete User Manual (R10.13, consolidated)

Generated from the component documents; the component files are the editing source of truth.


---

<!-- docs/r1013/manual/00_START/GLOSSARY.md -->

# Glossary

**Alpha quartz**: The crystalline form of silicon dioxide used by the default material record.

**Anisotropy**: Direction-dependent material behavior. Quartz wave speed depends on direction and polarization.

**Across flats**: Diameter measured between two opposite flat faces.

**Across vertices**: Diameter measured between two opposite corners.

**Boundary condition**: The rule that describes how the specimen is supported, loaded, electrically connected, or constrained.

**Candidate frequency**: A frequency produced by arithmetic, an analytic model, or a simulation. It is not a measured peak.

**Christoffel solve**: The directional eigenvalue calculation that produces acoustic phase velocities from the stiffness tensor and density.

**Evidence class**: A machine-readable label that states how a result was obtained.

**Facet**: One side face of the crystal shaft.

**FEM**: Finite-element method. A numerical method that divides a three-dimensional object into small elements and solves its field equations.

**Fixture**: The support, clamp, cradle, suspension, electrodes, or holder used with the specimen.

**Mode**: A spatial vibration pattern with a calculated or measured frequency.

**Mode family**: A group such as axial, flexural, torsional, or shear-like modes.

**Orientation**: The rotation between the crystal lattice axes and the specimen body axes.

**Phonon**: A quantized lattice vibration in a quantum description. In ordinary bench work, use elastic wave or vibration mode unless the quantum model is required.

**Proof bundle**: A deterministic package of inputs, outputs, hashes, environment data, tests, and reports.

**Quick estimate**: A low-order calculation such as a quarter-wave or half-wave model.

**Resonant frequency**: A frequency where a real system responds strongly under declared boundary and drive conditions. A calculation predicts it. A measurement observes it.

**Specimen file**: The JSON record that describes one physical or hypothetical crystal.

**Termination**: The pointed end geometry of a double-terminated crystal.

**Uncertainty**: A quantified range associated with measurements, material constants, geometry, numerical resolution, or model choice.


---

<!-- docs/r1013/manual/00_START/QUICK_START_10_MINUTES.md -->

# Quick Start in Ten Minutes


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


This path produces a documented candidate-frequency estimate. It does not produce a measured resonance.

## 1. Install

For a future R10.13 release package:

```bash
python -m venv .venv
```

Linux or macOS:

```bash
. .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the package:

```bash
python -m pip install -U pip
python -m pip install "rgcs[workbook,fem]"
```

For the current source repository, use the source-install guide.

## 2. Create a specimen file

R10.13 target command:

```bash
rgcs crystal new my-crystal.json
```

Open the file and enter at least:

```json
{
  "schema_version": "rgcs.crystal-specimen/1.0",
  "specimen_id": "my-crystal-001",
  "name": "My quartz crystal",
  "material": {
    "material_id": "alpha_quartz",
    "density_g_cm3": 2.65,
    "handedness": "unknown"
  },
  "geometry": {
    "length_mm": 77.8,
    "wide_diameter_mm": 30.2,
    "narrow_diameter_mm": null,
    "facets": 6,
    "female_angle_deg": 51.843,
    "male_angle_deg": 60.0,
    "diameter_mode": "across_vertices",
    "angle_mode": "face_slope"
  },
  "measurements": {
    "mass_g": 68.0
  }
}
```

A null narrow diameter is allowed only for a minimum-data estimate. A full mesh needs both diameters.

## 3. Validate

```bash
rgcs crystal validate my-crystal.json
```

Fix all errors. Read all warnings.

## 4. Calculate quick estimates

```bash
rgcs crystal estimate my-crystal.json --models axial-quarter,axial-half
```

The result must state the wave speed, path length, boundary assumption, harmonic index, uncertainty, and evidence class.

## 5. Read the result

The quarter-wave estimate uses:

\[
f_n = \frac{(2n-1)v}{4L_{\mathrm{eff}}}.
\]

The half-wave estimate uses:

\[
f_n = \frac{nv}{2L_{\mathrm{eff}}}.
\]

These equations are screening tools. They do not include the full taper, terminations, anisotropy, or fixture.

## 6. Save a report

```bash
rgcs crystal report my-crystal.json --from latest --out my-crystal-report
```

The report should include the input file, validation receipt, equations, assumptions, frequency table, warnings, and hashes.

## Next

Measure the narrow diameter and termination angles. Then run the full FEM tutorial.


---

<!-- docs/r1013/manual/00_START/START_HERE.md -->

# Start Here


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


RGCS is a research and computation system for crystal geometry, resonant modes, phase relationships, evidence records, and explicit refusal when the input or model is insufficient.

## What a normal user can do

The R10.13 target workflow lets you:

1. Create a specimen file.
2. Enter the measurements of your crystal.
3. Validate the measurements and units.
4. Calculate simple candidate frequencies.
5. Build a three-dimensional mesh.
6. Calculate anisotropic elastic modes.
7. Add fixture and orientation assumptions.
8. Compare calculations with measured peaks later.
9. Save a result certificate and proof bundle.

## What RGCS does not do

RGCS does not determine one magical frequency from mass and length. A real crystal has many modes. The modes depend on geometry, material tensors, crystallographic orientation, supports, electrodes, temperature, and the measurement method.

RGCS does not treat an arithmetic relationship as physical validation. It does not call a simulation a measurement. It does not report Phryll, propulsion, gravity modification, healing, consciousness transfer, or multiverse energy as established effects.

## Pick your task

- Ten-minute first result: `QUICK_START_10_MINUTES.md`
- Measure your specimen: `../02_USER_MANUAL/MEASURING_YOUR_CRYSTAL.md`
- Create the input file: `../02_USER_MANUAL/SPECIMEN_FILE_FORMAT.md`
- Understand the math: `../04_TECHNICAL/RESONANCE_MATH.md`
- Run a full solve: `../03_TUTORIALS/TUTORIAL_FULL_FEM.md`
- Understand a mode table: `../02_USER_MANUAL/UNDERSTANDING_RESULTS.md`
- Diagnose a problem: `../02_USER_MANUAL/TROUBLESHOOTING.md`

## Current and target command names

Current v8.0.0 commands include:

```text
rgcs-v4
rgcs-workbook
rgcs-workbench
```

The R10.13 target adds a unified command:

```text
rgcs
```

The release must preserve `rgcs-v4` as a compatibility command. Do not assume the target commands work until the R10.13 implementation and clean-install gate pass.


---

<!-- docs/r1013/manual/00_START/WHAT_RGCS_DOES_AND_DOES_NOT_DO.md -->

# What RGCS Does and Does Not Do


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## RGCS does

- store crystal geometry and measurement provenance;
- validate units and geometric consistency;
- calculate polygon areas, termination heights, volume, mass estimates, and density inverses;
- calculate quick one-dimensional resonance estimates;
- calculate anisotropic acoustic wave speeds;
- build three-dimensional finite-element meshes;
- solve elastic and piezoelectric mode systems;
- model optical paths and coil fields where implemented;
- record fixtures, orientation, environment, uncertainty, and software versions;
- compare calculations with later measurements without rewriting history;
- return a typed refusal when the model cannot support the request.

## RGCS does not

- identify a unique resonance from incomplete dimensions;
- infer crystallographic orientation from facet count alone;
- convert a simulation into a bench measurement;
- claim a source message is externally verified;
- claim new energy, propulsion, gravity modification, healing, or consciousness effects;
- hide a failed model behind a zero;
- tune a result to a famous location or preferred frequency after seeing the target;
- treat frequency keys as proof that a crystal physically prefers those values.

## A computed frequency is a model output

Use this language:

- candidate frequency;
- estimated mode;
- simulated mode;
- measured peak;
- replicated peak.

Do not call all of them resonance. The word resonance must include its evidence class.


---

<!-- docs/r1013/manual/01_INSTALL/INSTALL_FROM_SOURCE.md -->

# Install from Source


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Clone and create an isolated environment

```bash
git clone https://github.com/andrew867/rgcs.git
cd rgcs
python -m venv .venv
```

Activate the environment and install:

```bash
python -m pip install -U pip
python -m pip install -e '.[desktop,workbook,dev]'
```

## Run the tests

```bash
python -m pytest
```

The test count changes by release. Do not hard-code an expected count in a user guide. Record the exact count in release notes and proof bundles.

## Verify package metadata

```bash
python -c "import importlib.metadata as m; print(m.version('rgcs'))"
```

## Build a wheel

```bash
python -m pip install build
python -m build
```

Install the wheel into a new environment. Do not use the source tree for the final clean-install test.


---

<!-- docs/r1013/manual/01_INSTALL/INSTALL_LINUX.md -->

# Install on Linux


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Source install

```bash
git clone https://github.com/andrew867/rgcs.git
cd rgcs
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[desktop,workbook,dev]'
```

Verify the current commands:

```bash
rgcs-v4 --help
rgcs-workbook --help
python -m rgcs_desktop
```

Verify the R10.13 target command after implementation:

```bash
rgcs doctor
rgcs self-test
```

## Gmsh

Install the Gmsh executable or Python-provided console wrapper. RGCS uses it as an external process and exchanges files with it.

Test:

```bash
gmsh --version
```

## Headless use

The CLI can run without the desktop extra. For a server:

```bash
python -m pip install -e '.[workbook]'
```

A full FEM solve can consume substantial memory. Begin with a coarse `clmax_mm` and a small mode count.


---

<!-- docs/r1013/manual/01_INSTALL/INSTALL_WINDOWS.md -->

# Install on Windows


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Recommended release install

Use the signed installer or portable archive when the R10.13 release candidate provides one. A packaged build contains Python and the required runtime.

1. Download the release artifact and `SHA256SUMS.txt`.
2. Verify the SHA-256 hash.
3. Install or extract to a folder that you can write to.
4. Start `rgcs-workbench`.
5. Run the doctor command from a terminal:

```powershell
rgcs doctor
```

## Source install

Install Python 3.11 or newer and Git. Then:

```powershell
git clone https://github.com/andrew867/rgcs.git
cd rgcs
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[desktop,workbook,dev]"
```

The current public entry points are:

```powershell
rgcs-v4 --help
rgcs-workbook --help
rgcs-workbench
```

The target release also provides:

```powershell
rgcs --help
```

## Optional tools

- Gmsh is required for three-dimensional mesh generation.
- An OpenCL runtime is optional for supported sweeps.
- OpenSCAD is optional for rendering the reference apparatus model.

RGCS must detect each optional tool. It must not silently substitute a different backend.


---

<!-- docs/r1013/manual/01_INSTALL/UPDATE_AND_ROLLBACK.md -->

# Update and Roll Back


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Before an update

1. Export specimen files and run configurations.
2. Record the installed version.
3. Verify existing proof bundles.
4. Read the migration guide.

## Update a source checkout

```bash
git fetch --tags
git checkout <approved-tag-or-commit>
python -m pip install -e '.[desktop,workbook]'
```

## Roll back

Install the exact prior wheel or check out the prior tag. Do not edit old proof bundles. A bundle belongs to the software version that created it.

## Schema migration

The command:

```bash
rgcs crystal migrate old.json --out migrated.json
```

must create a new file. It must preserve the old file and write a migration receipt.


---

<!-- docs/r1013/manual/01_INSTALL/VERIFY_INSTALLATION.md -->

# Verify the Installation


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Run the commands that exist in v8.0.0:

```bash
rgcs-v4 devices
rgcs-v4 material
rgcs-v4 geometry nominal
```

For the R10.13 target release, also run:

```bash
rgcs --version
rgcs doctor
rgcs self-test
rgcs schema verify
rgcs examples verify
```

A passing installation report must state:

- package version;
- Python version;
- operating system;
- CPU and optional accelerator;
- Gmsh availability;
- desktop availability;
- schema versions;
- example validation count;
- documentation example test count;
- no-mock audit status.

A missing optional tool may produce a warning. A missing required dependency must produce an error with a repair command.


---

<!-- docs/r1013/manual/02_USER_MANUAL/CALCULATING_RESONANT_FREQUENCIES.md -->

# Calculating Resonant Frequencies


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## There is no single universal formula

Use the simplest model that answers the question, then move to a more complete model when needed.

## Quick axial quarter-wave estimate

\[
f_n = \frac{(2n-1)v}{4L_{\mathrm{eff}}}, \qquad n=1,2,3,\ldots
\]

Use this only when the boundary and mode resemble a quarter-wave path.

For a declared speed of 6310 m/s and length 77.8 mm:

\[
f_1 \approx \frac{6310}{4(0.0778)} \approx 20276.35\ \mathrm{Hz}.
\]

This is a screening estimate. It is not a full crystal mode.

## Quick axial half-wave estimate

\[
f_n = \frac{nv}{2L_{\mathrm{eff}}}.
\]

For the same example:

\[
f_1 \approx 40552.70\ \mathrm{Hz}.
\]

## Directional anisotropic estimate

For a direction vector \(\mathbf n\), solve:

\[
\Gamma_{ik}p_k = \rho v^2p_i,
\qquad
\Gamma_{ik}=C_{ijkl}n_jn_l.
\]

This returns three branches. Each branch can produce a path-frequency estimate. The result depends on crystal orientation.

Target command:

```bash
rgcs crystal christoffel my-crystal.json --directions body-z,body-x,body-y
```

## Full elastic FEM

The finite-element solver builds stiffness and mass matrices:

\[
K\mathbf u = \omega^2 M\mathbf u.
\]

Each non-rigid eigenpair gives:

\[
f=\frac{\omega}{2\pi}.
\]

The result includes a mode shape. It can distinguish axial, flexural, torsional, and mixed modes better than a one-dimensional formula.

## Piezoelectric solve

The coupled system adds electric potential and piezoelectric constitutive terms. Electrical boundary conditions such as open and short can shift the modes.

## Fixture effect

A calculated free-body mode and a clamped measured mode are different systems. Always include the fixture in the comparison.

## Convergence

Run at least three mesh sizes. A result should report:

- frequency change;
- mode-shape correlation;
- residual;
- degrees of freedom;
- solver tolerance;
- memory and runtime;
- whether mode ordering changed.

## Candidate frequency registry

A frequency key can be overlaid on the calculated spectrum. It does not become a mode because it was registered.

Use:

```bash
rgcs frequency compare modes.json --keys 4096,528,560,925,20480,32768
```

The output should show nearest modes and normalized distance without changing the solve.


---

<!-- docs/r1013/manual/02_USER_MANUAL/CLI_REFERENCE.md -->

# CLI Reference


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Existing v8.0.0 command

```text
rgcs-v4
```

Existing subcommands include `devices`, `material`, `geometry`, `mesh`, `modes`, `sweep`, `piezo`, `optical`, `coil`, `diagnostics`, `refsystems`, `capabilities`, `proof-bundle`, `report`, and `verify-checksums`.

## Unified command (implemented)

```text
rgcs
```

The implementation must retain `rgcs-v4` as a compatibility entry point.

## General

```bash
rgcs --version
rgcs doctor
rgcs self-test
rgcs schema verify
rgcs examples verify
```

## Crystal records

```bash
rgcs crystal new FILE
rgcs crystal validate FILE
rgcs crystal inspect FILE
rgcs crystal migrate FILE --out NEW_FILE
rgcs crystal hash FILE
```

## Geometry and estimates

```bash
rgcs crystal geometry FILE
rgcs crystal density-check FILE
rgcs crystal estimate FILE --models LIST
rgcs crystal christoffel FILE --directions LIST
```

## Mesh and modes

```bash
rgcs crystal mesh FILE --clmax-mm FLOAT --out DIR
rgcs crystal modes FILE --mesh DIR --count INT --fixture NAME --out DIR
rgcs crystal converge FILE --levels 8,6,4 --count 24 --out DIR
rgcs crystal piezo FILE --condition open|short --count INT --out DIR
```

## Reports and bundles

```bash
rgcs crystal report FILE --from RESULT_DIR --out DIR
rgcs crystal bundle FILE --result RESULT_DIR --out BUNDLE_DIR
rgcs bundle verify BUNDLE_DIR
```

## Frequency registry

Note: a frequency-to-coordinate command is NOT shipped: it would assert the state-to-geometry bridge, which is underdetermined. The refusal is recorded in receipts/COMMAND_STATUS.json.

```bash
rgcs frequency list
rgcs frequency compare MODE_FILE --keys 4096,528,560
```

## Codec research

```bash
rgcs wire parse WIRE
rgcs wire explain WIRE
rgcs wire roundtrip WIRE
rgcs transition candidates WIRE --child C
rgcs mesh trace WIRE
```

Unknown transition cells must return a typed refusal.

## Output modes

Every command should support:

```text
--format human
--format json
--format csv
--quiet
--output PATH
```

Human output is for a normal user. JSON output is the stable automation interface.


---

<!-- docs/r1013/manual/02_USER_MANUAL/COMPLETE_USER_MANUAL.md -->

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


---

<!-- docs/r1013/manual/02_USER_MANUAL/DESKTOP_APP_GUIDE.md -->

# Desktop App Guide


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (DEFERRED from this release; use the CLI workflow) (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


The current repository provides `rgcs-workbench`. R10.13 must add a normal-user crystal workflow without removing existing research views.

> DEFERRAL NOTE: the seven-page New Specimen wizard is deferred from this release. The rgcs-workbench desktop app itself is unchanged; create and calculate specimens with the `rgcs crystal` commands documented in CLI_REFERENCE.md.

## First-run screen

The target first-run screen has five actions:

1. Add a crystal.
2. Open a specimen file.
3. Calculate a quick estimate.
4. Run a full mode solve.
5. Verify a proof bundle.

## New Specimen wizard

Pages:

1. Identity and photographs.
2. Material.
3. Geometry.
4. Orientation.
5. Mass and uncertainty.
6. Fixture.
7. Validation summary.

Each field must show:

- plain-language name;
- unit;
- measurement diagram;
- default source;
- whether the value is measured, assumed, or unknown;
- why the solver needs it.

## Results screen

The default screen should not show only a dense mode table. It should show:

- what was calculated;
- what was assumed;
- the strongest warnings;
- a simple frequency plot;
- a mode list;
- a link to the full certificate;
- an evidence label.

## Expert mode

Expert mode may expose mesh settings, tensors, solver tolerances, backend selection, orientation ensembles, and coupled fields.

## No hidden mutation

Editing the specimen after a solve creates a new revision. It does not rewrite the old result.


---

<!-- docs/r1013/manual/02_USER_MANUAL/FAQ.md -->

# Frequently Asked Questions


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Can I enter only length and mass?

You can run a limited estimate. You cannot build a reliable three-dimensional tapered crystal from only length and mass.

## Does RGCS calculate the exact natural frequency?

No. It calculates model-dependent candidate modes. A physical measurement is required to observe the real system.

## Why do I get many frequencies?

A three-dimensional crystal has many elastic modes. Different modes move in different patterns.

## Which one is the main frequency?

That depends on the drive, sensor, fixture, orientation, and purpose. RGCS should show participation and mode shape instead of choosing one without a rule.

## Can I use a natural irregular crystal?

Yes, but a regular faceted model may be inadequate. Import a measured mesh or use an uncertainty ensemble.

## Are 4096 Hz, 528 Hz, or 560 Hz guaranteed resonances?

No. They are registered candidate keys and control values. Compare them with the calculated and measured spectrum.

## Does the aperture model prove a craft design?

No. It defines a parametric geometry and timing hypothesis that can be modeled and tested.

## Does dynamic boundary switching create free energy?

No such result is established. The switch and pump supply work. Any residual requires a complete energy ledger and replication.

## Can I use the software without a laboratory?

Yes. You can build specimen records, calculate geometry, run simulations, create protocols, and generate proof bundles. Physical evidence remains absent until instruments acquire data.


---

<!-- docs/r1013/manual/02_USER_MANUAL/MEASURING_YOUR_CRYSTAL.md -->

# Measuring Your Crystal


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Tools

A basic record can use:

- digital calipers;
- a scale with suitable resolution;
- a flat background and camera;
- a protractor or angle gauge;
- a rotating polarizer or polarized display for orientation work;
- soft gloves or clean hands;
- a specimen identifier label that does not touch the crystal during a solve.

## Measurement order

1. Photograph the untouched specimen.
2. Assign a specimen ID.
3. Measure mass.
4. Measure tip-to-tip length.
5. Count shaft facets.
6. Measure the widest cross-section.
7. Measure the narrow cross-section.
8. Record whether each diameter is across vertices or across flats.
9. Measure both termination angles and record the angle convention.
10. Inspect chips, inclusions, repairs, coatings, glue, and asymmetric facets.
11. Estimate orientation and uncertainty.
12. Repeat each dimension at least three times.

## Length

Measure from one apex to the other. Do not measure only the shaft. Record the tool resolution and repeated readings.

Example:

```json
{
  "length_mm": 77.80,
  "length_uncertainty_mm": 0.10
}
```

## Diameters

A tapered crystal needs two diameters.

- Wide diameter: the larger shaft cross-section near the wide termination.
- Narrow diameter: the smaller shaft cross-section near the narrow termination.

Measure at a defined axial station. Photograph the station.

## Mass and density

Mass helps detect an inconsistent geometry or assumed density. It does not determine a unique mode spectrum by itself.

For alpha quartz, a nominal density may be used as a material default. A measured density or supplier certificate should replace it when available.

## Termination angles

Do not copy 51.843 degrees and 60 degrees unless they describe your specimen. Those values are defaults and source claims for a particular geometry family.

When the angle is unknown, enter null and choose a model that can operate without it. A full geometry solve must refuse or use an explicit uncertainty ensemble.

## Facet irregularity

The regular-polygon model assumes equal facets. If the specimen is irregular, capture each vertex or use a mesh imported from photographs or scanning. Do not average severe asymmetry into a false regular crystal.

## Defects

Record defects because they may change local stiffness, mass, damping, optical response, and measured Q.

Use neutral descriptions:

- chip at male apex;
- internal inclusion at 0.42L;
- repaired fracture;
- surface coating;
- glued holder residue.

## Orientation

A visual shaft axis is not automatically the crystallographic C-axis. Store orientation confidence separately from geometry confidence.

## Measurement worksheet

Use `examples/crystal_measurement_worksheet.csv` or the desktop wizard. Keep the raw readings. Do not keep only the average.


---

<!-- docs/r1013/manual/02_USER_MANUAL/SPECIMEN_FILE_FORMAT.md -->

# Specimen File Format


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


The canonical format is JSON. The schema is `schemas/crystal-specimen.schema.json`.

## Minimum record

A minimum record supports only selected quick estimates.

```json
{
  "schema_version": "rgcs.crystal-specimen/1.0",
  "specimen_id": "crystal-001",
  "name": "Six-sided quartz",
  "material": {
    "material_id": "alpha_quartz",
    "density_g_cm3": 2.65,
    "handedness": "unknown"
  },
  "geometry": {
    "length_mm": 77.8,
    "wide_diameter_mm": 30.2,
    "narrow_diameter_mm": null,
    "facets": 6,
    "female_angle_deg": null,
    "male_angle_deg": null,
    "diameter_mode": "across_vertices",
    "angle_mode": "face_slope"
  },
  "orientation": {
    "status": "unknown"
  },
  "measurements": {
    "mass_g": 68.0
  }
}
```

## Complete regular-faceted record

```json
{
  "schema_version": "rgcs.crystal-specimen/1.0",
  "specimen_id": "crystal-001",
  "name": "Measured six-sided quartz",
  "description": "Double-terminated tapered specimen",
  "material": {
    "material_id": "alpha_quartz",
    "density_g_cm3": 2.65,
    "handedness": "unknown",
    "material_record_version": "alpha-quartz-default"
  },
  "geometry": {
    "length_mm": 77.8,
    "wide_diameter_mm": 30.2,
    "narrow_diameter_mm": 24.0,
    "facets": 6,
    "female_angle_deg": 51.843,
    "male_angle_deg": 60.0,
    "diameter_mode": "across_vertices",
    "angle_mode": "face_slope"
  },
  "orientation": {
    "status": "assumed",
    "c_axis_body_axis": "+Z",
    "euler_zxz_deg": [0.0, 0.0, 0.0],
    "uncertainty_deg": [0.0, 10.0, 360.0]
  },
  "measurements": {
    "mass_g": 68.0,
    "length_uncertainty_mm": 0.1,
    "diameter_uncertainty_mm": 0.2,
    "angle_uncertainty_deg": 1.0,
    "mass_uncertainty_g": 0.1,
    "temperature_c": 22.0
  },
  "provenance": {
    "operator": "local-user",
    "measurement_date": "2026-07-28",
    "source_type": "operator_measurement",
    "notes": "Replace example values with actual measurements."
  }
}
```

## Null and unknown

Use null when a value was not measured. Use `unknown` for a categorical state. Do not use zero for missing data.

## Source claim versus measured value

A marketplace listing or handwritten note belongs under `source_claims`. A caliper measurement belongs under `measurements`. Preserve both when they differ.

## Custom mesh

An irregular specimen may add:

```json
{
  "mesh_source": {
    "type": "stl",
    "path": "specimens/crystal-001.stl",
    "units": "mm",
    "sha256": "..."
  }
}
```

The mesh must have a declared scale and closed-volume audit.


---

<!-- docs/r1013/manual/02_USER_MANUAL/TROUBLESHOOTING.md -->

# Troubleshooting


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## `COMMAND_NOT_FOUND`

Activate the virtual environment. Check the installed entry points:

```bash
python -m pip show rgcs
python -c "import shutil; print(shutil.which('rgcs-v4')); print(shutil.which('rgcs'))"
```

## `SPECIMEN_SCHEMA_INVALID`

Run:

```bash
rgcs crystal validate specimen.json --format human
```

The message should name the field, the expected unit or type, and an example repair.

## `INSUFFICIENT_GEOMETRY_FOR_FEM`

A full mesh needs both diameters and both termination angles for the regular-faceted model, or a valid imported mesh.

Use a quick estimate or add the missing measurements.

## `CAPS_EXCEED_TOTAL_LENGTH`

The selected angle convention or dimensions create termination heights larger than the crystal. Check whether the angles are face slope, axis-to-face, or apex included.

## `ORIENTATION_UNKNOWN`

Choose an orientation ensemble. Do not force zero rotation unless it is an explicit assumption.

## `GMSH_NOT_FOUND`

Install Gmsh and verify:

```bash
gmsh --version
```

Quick estimates and some directional calculations can run without Gmsh.

## `BACKEND_UNAVAILABLE`

Use CPU or install the requested runtime. RGCS does not silently fall back when an explicit backend was requested.

## `MODE_SOLVER_FAILED`

Try a coarser mesh, fewer modes, or more memory. Save the generated mesh and error receipt.

## `MODE_ORDER_CHANGED`

Use mode-shape correlation. Do not compare only by mode index.

## Result differs from measurement

Check:

- fixture;
- orientation;
- temperature;
- geometry convention;
- unit scale;
- material record;
- electrode loading;
- sensor position;
- mesh convergence;
- specimen defects.

Do not tune all parameters at once.


---

<!-- docs/r1013/manual/02_USER_MANUAL/UNDERSTANDING_RESULTS.md -->

# Understanding Results


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Read the evidence class first

A frequency without an evidence class is incomplete.

Common classes:

- `SOURCE_CLAIM`: copied from a source record.
- `DERIVED_ARITHMETIC`: exact or approximate arithmetic on declared inputs.
- `ANALYTIC_MODEL`: result of a closed-form or low-order model.
- `NUMERICAL_SIMULATION`: result of FEM or another numerical solver.
- `SYNTHETIC_RUN`: generated test data.
- `BENCH_MEASUREMENT`: data acquired from a physical instrument with required metadata.
- `INDEPENDENT_REPLICATION`: a qualifying independent repeat.
- `UNSUPPORTED`: the requested conclusion is not supported.
- `UNDERDETERMINED`: several results remain possible.
- `REVOKED` or `HISTORICAL_ONLY`: preserved history that cannot become active.

## Mode table fields

A useful mode table includes:

- mode index;
- frequency;
- rigid-body flag;
- residual;
- mode family classification;
- dominant displacement direction;
- effective mass or participation;
- mesh level;
- fixture;
- orientation;
- confidence and warnings.

## Rigid modes

A free three-dimensional body has near-zero rigid translations and rotations. Do not confuse them with elastic resonances.

## Mode ordering

Modes may cross or exchange order as the mesh, fixture, or orientation changes. Match modes by shape, not only by list index.

## Precision

Six decimal places do not create six-decimal physical accuracy. Report numerical precision separately from input and model uncertainty.

## A null result can pass

The correct result may be:

- no mode near the candidate key;
- no directional asymmetry;
- no change beyond uncertainty;
- insufficient input;
- model family falsified.

RGCS treats an honest null as a successful scientific result.


---

<!-- docs/r1013/manual/03_TUTORIALS/TUTORIAL_BATCH_CRYSTALS.md -->

# Tutorial: Batch of Crystals


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Validate and estimate several specimens without mixing their provenance.

## Batch file

Use `examples/crystal_batch.csv`. Each row points to one JSON specimen file.

## Run

```bash
rgcs batch validate examples/crystal_batch.csv --out batch/validation
rgcs batch estimate examples/crystal_batch.csv --models axial-quarter,axial-half --out batch/estimates
```

## Rules

- Each result retains the specimen hash.
- A failed specimen does not disappear from the batch.
- Batch summary statistics do not replace individual reports.
- Do not select only the specimens nearest a frequency key after the run.


---

<!-- docs/r1013/manual/03_TUTORIALS/TUTORIAL_FIXTURE_COMPARISON.md -->

# Tutorial: Fixture Comparison


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Compare a free specimen, a three-point cradle, and a center clamp.

## Run three declared fixtures

```bash
rgcs crystal modes crystal.json --fixture fixtures/free.json --out runs/free
rgcs crystal modes crystal.json --fixture fixtures/three_point.json --out runs/three-point
rgcs crystal modes crystal.json --fixture fixtures/center_clamp.json --out runs/center-clamp
```

## Compare

```bash
rgcs compare fixtures runs/free runs/three-point runs/center-clamp --out runs/fixture-comparison
```

The report should show frequency shift, mode-shape change, and new fixture-local modes.


---

<!-- docs/r1013/manual/03_TUTORIALS/TUTORIAL_FULL_FEM.md -->

# Tutorial: Full Three-Dimensional FEM


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Calculate the first 24 elastic modes of a complete regular-faceted specimen.

## Prepare complete data

Use `examples/crystal_complete.json`. Replace the example values with measured values.

## Validate

```bash
rgcs crystal validate examples/crystal_complete.json --model fem-elastic
```

## Build a coarse mesh

```bash
rgcs crystal mesh examples/crystal_complete.json --clmax-mm 8 --out tutorial/fem/cl8
```

## Solve

```bash
rgcs crystal modes examples/crystal_complete.json --mesh tutorial/fem/cl8 --count 24 --fixture free --out tutorial/fem/modes-cl8
```

## Refine

Repeat at 6 mm and 4 mm. Then:

```bash
rgcs crystal convergence tutorial/fem/modes-cl8 tutorial/fem/modes-cl6 tutorial/fem/modes-cl4 --out tutorial/fem/convergence
```

## Pass condition

The pass condition must be declared before the final run. Example:

- frequency change below 1 percent for the modes of interest;
- mode-shape correlation above 0.95;
- residual below the solver threshold;
- no invalid or inverted elements.

A mode that fails convergence remains provisional.


---

<!-- docs/r1013/manual/03_TUTORIALS/TUTORIAL_ORIENTATION_SWEEP.md -->

# Tutorial: Orientation Sweep


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Quantify how unknown lattice orientation changes the candidate modes.

## Define the ensemble

```bash
rgcs orientation plan crystal.json --beta 0:15:5 --gamma 0:330:30 --out orientation-plan.json
```

The exact syntax is a target interface. The plan must record every orientation before execution.

## Run

```bash
rgcs crystal modes crystal.json --orientation-plan orientation-plan.json --count 12 --clmax-mm 8 --out runs/orientation
```

## Read the result

Report a distribution for each tracked mode. Do not report only the orientation that places a mode nearest a preferred key.


---

<!-- docs/r1013/manual/03_TUTORIALS/TUTORIAL_PROOF_BUNDLE.md -->

# Tutorial: Build and Verify a Proof Bundle


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Build

```bash
rgcs crystal bundle crystal.json --result runs/final --out proof/crystal-001
```

## Verify

```bash
rgcs bundle verify proof/crystal-001
```

## Expected contents

- specimen JSON and hash;
- material record;
- fixture and orientation records;
- mesh manifest and mesh hash;
- solver configuration;
- raw result files;
- convergence report;
- user report;
- software and environment receipt;
- `SHA256SUMS.txt`;
- evidence classification;
- limitations and refusals.

A proof bundle proves reproducibility and integrity. It does not prove that a physical prediction is correct.


---

<!-- docs/r1013/manual/03_TUTORIALS/TUTORIAL_QUICK_ESTIMATE.md -->

# Tutorial: Quick Estimate


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Calculate quarter-wave and half-wave screening frequencies for a 77.8 mm specimen.

## Create the file

Copy `examples/crystal_minimum.json` to `my-crystal.json`.

## Validate

```bash
rgcs crystal validate my-crystal.json
```

## Run

```bash
rgcs crystal estimate my-crystal.json --models axial-quarter,axial-half --wave-speed-m-s 6310
```

## Verify by hand

Convert length:

\[
77.8\ \mathrm{mm}=0.0778\ \mathrm{m}.
\]

Quarter-wave:

\[
f=6310/(4\times0.0778)=20276.35\ \mathrm{Hz}.
\]

Half-wave:

\[
f=6310/(2\times0.0778)=40552.70\ \mathrm{Hz}.
\]

## Interpret

These two numbers are not competing truths. They correspond to different boundary assumptions. The software must print the assumption beside each number.


---

<!-- docs/r1013/manual/04_TECHNICAL/ANISOTROPY_AND_CHRISTOFFEL.md -->

# Anisotropy and the Christoffel Solver


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


For every unit direction \(\mathbf n\), build:

\[
\Gamma_{ik}=C_{ijkl}n_jn_l.
\]

Solve:

\[
\Gamma\mathbf p=\rho v^2\mathbf p.
\]

The eigenvectors are polarizations. The eigenvalues produce squared phase velocities.

## Output requirements

The solver must report:

- direction in crystal and body frames;
- branch identity;
- phase velocity;
- polarization;
- group velocity where calculated;
- source tensor version;
- orientation;
- numerical residual.

## Orientation uncertainty

When azimuth around the C-axis is unknown, sweep it. Do not choose the azimuth that best matches a preferred frequency after the calculation.


---

<!-- docs/r1013/manual/04_TECHNICAL/APERTURE_RING_MODEL.md -->

# Aperture Ring Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Source-provenance geometry

- 35 physical positions;
- 33 active apertures;
- 2 omitted positions;
- occupancy \(33/35\);
- inner and outer area indices 29 and 89;
- prime denominator family 37;
- scalable geometry.

## Radial relationship

\[
\frac{R_i^2}{R_o^2}=\frac{29}{89},
\qquad
R_i=R_o\sqrt{\frac{29}{89}}.
\]

The prime-ratio construction gives candidate numerical radii:

\[
R_i\approx82.2616108\ \mathrm{units},
\qquad
R_o\approx144.1096998\ \mathrm{units}.
\]

Generator-scale candidate in millimetres:

- inner radius 82.2616 mm;
- outer radius 144.1097 mm;
- outer diameter 288.2194 mm;
- annular width 61.8481 mm.

Craft-scale candidate in metres:

- inner radius 0.822616 m;
- outer radius 1.441097 m;
- outer diameter 2.882194 m;
- annular width 0.618481 m.

## Torus equivalent

\[
R_{\mathrm{major}}=\frac{R_o+R_i}{2},
\qquad
a_{\mathrm{minor}}=\frac{R_o-R_i}{2}.
\]

## Angular lattice

\[
\Delta\theta=360^\circ/35=10.285714\ldots^\circ.
\]

Five positions give:

\[
5\Delta\theta=360^\circ/7=51.428571\ldots^\circ.
\]

## Frequency-to-geometry realization

For a 16 Hz traveling pattern:

\[
35\times16=560\ \mathrm{Hz},
\]

\[
33\times16=528\ \mathrm{Hz},
\]

\[
2\times16=32\ \mathrm{Hz}.
\]

Each position has 16 sub-bins:

- total bins: 560;
- active bins: 528;
- blank bins: 32.

## Integer master timing

A compatible exact lattice has 224000 ticks per 16 Hz revolution and a 3.584 MHz master clock. The target implementation must regenerate and verify every integer relationship rather than hard-code the values.

## Missing geometry

- exact gap indices;
- aperture diameter and shape;
- plate thickness;
- upper and lower ring offset;
- optical path;
- conductive or dielectric implementation;
- drive and sensor geometry.


---

<!-- docs/r1013/manual/04_TECHNICAL/API_REFERENCE.md -->

# Python API Reference Contract


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


The exact module names must be reconciled with the target repository. The stable R10.13 user API should provide typed functions equivalent to:

```python
from rgcs import crystals

specimen = crystals.load_specimen("crystal.json")
validation = crystals.validate_specimen(specimen)
geometry = crystals.calculate_geometry(specimen)
estimates = crystals.estimate_frequencies(specimen, models=["axial-quarter", "axial-half"])
mesh = crystals.build_mesh(specimen, clmax_mm=6.0, output_dir="run/mesh")
modes = crystals.solve_elastic_modes(specimen, mesh=mesh, count=24, fixture="free")
report = crystals.build_report(specimen, modes, output_dir="run/report")
```

## Return contract

Every result object must include:

- schema version;
- evidence class;
- input hashes;
- warnings;
- status or typed refusal;
- deterministic serialization;
- provenance and correction state.

## Compatibility

Existing packages such as `rgcs_core`, `rscs_core`, `rscs2_core`, and `r15` remain importable according to the release policy. The new user API should wrap them rather than duplicate their mathematics.


---

<!-- docs/r1013/manual/04_TECHNICAL/ARCHITECTURE.md -->

# Architecture


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Layers

```text
user input
  -> specimen schema
  -> validation and provenance
  -> geometry model
  -> material and orientation model
  -> low-order estimate or mesh
  -> elastic or piezoelectric solver
  -> uncertainty and convergence
  -> evidence classification
  -> report and proof bundle
```

Research extensions add:

```text
phase and frequency registry
  -> dynamic boundary timing
  -> aperture geometry
  -> optical and acoustic mode redistribution
  -> measured or simulated observables
```

Coordinate research adds:

```text
decimal transport envelope
  -> two-sided octal refinement
  -> E3 and three S6 states
  -> state transitions
  -> state-dependent analytic edge law
  -> topology and body realization
```

## Separation rules

- Geometry is separate from material.
- Material is separate from orientation.
- Orientation is separate from fixture.
- Topology is separate from node positions.
- Angular mesh compensation is separate from ellipsoid realization.
- A source hypothesis is separate from its physical translation.
- A model output is separate from a physical measurement.


---

<!-- docs/r1013/manual/04_TECHNICAL/CRYSTAL_GEOMETRY_MODEL.md -->

# Crystal Geometry Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Regular faceted model

Inputs:

- total length \(L\);
- wide diameter \(D_w\);
- narrow diameter \(D_n\);
- facet count \(N\);
- female and male termination angles;
- diameter and angle conventions.

For across-vertices diameter, polygon area is:

\[
A=\frac{N}{8}D^2\sin\left(\frac{2\pi}{N}\right).
\]

For across-flats diameter:

\[
A=N\left(\frac{D}{2}\right)^2\tan\left(\frac{\pi}{N}\right).
\]

The apothem for across-vertices diameter is:

\[
r_a=\frac{D}{2}\cos\left(\frac{\pi}{N}\right).
\]

The default face-slope cap height is:

\[
h=r_a\tan\alpha.
\]

The shaft length is:

\[
h_s=L-h_f-h_m.
\]

The model refuses \(h_s\le0\).

## Volume

The tapered shaft is a frustum:

\[
V_s=\frac{h_s}{3}\left(A_w+A_n+\sqrt{A_wA_n}\right).
\]

Add both termination pyramids:

\[
V=V_s+\frac{A_wh_f}{3}+\frac{A_nh_m}{3}.
\]

## Mass consistency

\[
m=\rho V.
\]

The density inverse may scale diameters to match a measured mass. This is a diagnostic. It does not replace direct diameter measurements.

## Irregular geometry

Use an imported mesh when facet irregularity is significant. The import audit must verify units, closure, manifold status, volume, orientation, and scale.


---

<!-- docs/r1013/manual/04_TECHNICAL/EVIDENCE_AND_PROVENANCE.md -->

# Evidence and Provenance


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Core rule

Lore proposes. Mathematics translates. Software attacks. Evidence decides. Provenance remembers.

## Record fields

Every result should record:

- source identifiers;
- operator and timestamp where appropriate;
- input hashes;
- software version and commit;
- equation or model identifier;
- assumptions;
- uncertainty;
- evidence class;
- correction status;
- superseded and superseding records;
- public-safety status.

## Private provenance firewall

Private operator records, personal identity claims, ancestry, political allegations, family allegations, appearance-based classification, and source-origin claims cannot become technical solver authority.

## Correction rule

Never delete a superseded value. Preserve the raw record, correction, reason, timestamp, and active replacement.


---

<!-- docs/r1013/manual/04_TECHNICAL/FEM_PIPELINE.md -->

# Finite-Element Pipeline


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Steps

1. Validate the specimen.
2. Build or import a closed geometry.
3. Generate a tetrahedral mesh.
4. Audit element quality and orientation.
5. Rotate material tensors.
6. Apply fixture and electrical boundary conditions.
7. Assemble matrices.
8. Solve eigenpairs.
9. Remove or label rigid modes.
10. Calculate residuals and orthogonality.
11. Classify mode shapes.
12. Repeat on a refinement ladder.
13. Write a result certificate.

## Shared requirements

- deterministic inputs produce deterministic manifests;
- mesh units are explicit;
- solver backend is recorded;
- CPU float64 remains the numerical authority unless a later release changes the policy explicitly;
- an unavailable requested backend fails loudly;
- full deep meshes are bounded by memory policy.


---

<!-- docs/r1013/manual/04_TECHNICAL/MATERIAL_MODEL.md -->

# Material Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Default material

The default record is alpha quartz. It includes density, elastic stiffness, piezoelectric, dielectric, and selected optical properties where implemented.

## Tensor authority

A material record must state:

- source and version;
- temperature;
- crystal convention;
- unit system;
- tensor ordering;
- whether values are measured, published, fitted, or assumed;
- uncertainty or source spread.

## Rotation

The stiffness tensor is rotated into the specimen frame:

\[
C'_{pqrs}=R_{pi}R_{qj}R_{rk}R_{sl}C_{ijkl}.
\]

The piezoelectric and dielectric tensors use their corresponding rotation laws.

## Capability firewall

A material record declares supported mechanisms. Unsupported mechanisms return a typed refusal. They do not return zero.


---

<!-- docs/r1013/manual/04_TECHNICAL/OPTICAL_AND_ACOUSTIC_PHASE.md -->

# Optical and Acoustic Phase


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Quartz can act as a resonator, transducer, phase reference, birefringent medium, acousto-optic medium, and nonlinear optical medium in different devices.

## Phase state

A coherent component can be represented by:

\[
\mathcal X=(\omega,\mathbf k,\phi,t_0,\mathrm{domain},\mathrm{path},\Sigma).
\]

A received residual is:

\[
\delta\phi=\phi_{\mathrm{received}}-\phi_{\mathrm{ideal}}.
\]

Separate residual contributions from synthesis, clock, path, medium, motion, transducer, fixture, and noise.

## Acousto-optic modulation

A traveling strain field changes refractive index and can create a moving optical grating. Phase and timing determine diffraction and pulse gating.

The 1970 research lead identifies resonant self-pulsing acousto-optic quartz modulation and variable delay as prior-art areas that require formal verification in the repository bibliography.


---

<!-- docs/r1013/manual/04_TECHNICAL/PHRYLL_DYNAMIC_BOUNDARY_MODEL.md -->

# Phryll Dynamic-Boundary Research Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Status

This chapter preserves a source-provenance hypothesis and its conventional physical translation. It does not establish Phryll, free energy, propulsion, gravity modification, or multiverse transfer.

## Exact timing relationship

Carrier:

\[
f_c=4096\ \mathrm{Hz}.
\]

Nominal macrocycle:

\[
T_0=552\ \mathrm{ms}.
\]

Carrier cycles in the nominal interval:

\[
f_cT_0=2260.992=2260+\frac{124}{125}.
\]

The next integer closure is 2261 cycles:

\[
T_{\mathrm{closed}}=\frac{2261}{4096}=552.001953125\ \mathrm{ms}.
\]

Difference:

\[
\Delta t=1.953125\ \mu\mathrm{s}.
\]

Phase step:

\[
\Delta\phi=360^\circ/125=2.88^\circ.
\]

Define \(q\in\{0,\ldots,124\}\):

\[
\Delta t(q)=q(1.953125\ \mu\mathrm{s}),
\qquad
\Delta\phi(q)=q(2.88^\circ).
\]

## Dynamic boundary

Let \(g_q(t)\) be a timed gate applied to an optical or acoustic wavepacket envelope \(u(t)\).

Energy-weighted duty cycle:

\[
D_{\mathrm{eff}}(q)=
\frac{\int|u(t)|^2g_q(t)dt}{\int|u(t)|^2dt}.
\]

A time-dependent boundary may mix modes:

\[
a_m^{\mathrm{out}}=\sum_n\left(\alpha_{mn}a_n^{\mathrm{in}}+\beta_{mn}a_n^{\mathrm{in}\dagger}\right).
\]

The conventional energy ledger is:

\[
E_{\mathrm{before}}+W_{\mathrm{switch}}+E_{\mathrm{pump}}
=E_{\mathrm{after}}+E_{\mathrm{loss}}.
\]

## Testable observables

- transmitted and reflected optical energy;
- optical sidebands;
- acoustic sidebands;
- crystal ring-down;
- piezoelectric output;
- switching work;
- thermal change;
- mechanical mode redistribution;
- dependence on \(q\), pulse tail, and effective duty cycle.

## Source interpretation

The source model relates phase-controlled tail chopping to Phryll generation, environmental emission, and craft motion. That interpretation remains unverified and must not replace the energy ledger.


---

<!-- docs/r1013/manual/04_TECHNICAL/PIEZOELECTRIC_MODEL.md -->

# Piezoelectric Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Quartz couples strain, stress, electric field, and electric displacement.

A coupled discretization contains mechanical displacement and electric potential. The result depends on electrode geometry and electrical boundary.

## Required electrical states

- open;
- short;
- finite capacitance or impedance, when implemented;
- no electrodes;
- source-reproduction electrode profile;
- reversed polarity control.

## Comparison rule

A frequency shift between open and short conditions is a model result. It is not proof of an extraordinary mechanism.


---

<!-- docs/r1013/manual/04_TECHNICAL/RESONANCE_MATH.md -->

# Resonance Mathematics


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## One-dimensional screening

Quarter-wave:

\[
f_n=\frac{(2n-1)v}{4L}.
\]

Half-wave:

\[
f_n=\frac{nv}{2L}.
\]

Closed path:

\[
f_n=\frac{nv}{L_{\mathrm{path}}}.
\]

These formulas need a declared path, speed, and boundary model.

## Anisotropic plane waves

\[
\det\left(C_{ijkl}n_jn_l-\rho v^2\delta_{ik}\right)=0.
\]

The three eigenvalues produce three phase velocities. Group velocity may not align with the phase normal.

## Finite-element eigenproblem

\[
K\mathbf u=\omega^2M\mathbf u.
\]

For piezoelectric coupling, use the block electromechanical system and declared open, short, or finite-load boundary.

## Damping and Q

A lossless eigenproblem predicts frequencies and mode shapes. It does not predict measured Q unless damping is modeled or fitted.

A measured Q may be estimated by:

\[
Q=\frac{f_0}{\Delta f_{-3\mathrm{dB}}}.
\]

## Frequency uncertainty

For a simple length model:

\[
\left(\frac{\sigma_f}{f}\right)^2\approx
\left(\frac{\sigma_v}{v}\right)^2+
\left(\frac{\sigma_L}{L}\right)^2.
\]

Full models require sampling geometry, material, orientation, fixture, and numerical uncertainty.


---

<!-- docs/r1013/manual/04_TECHNICAL/SCHEMA_REFERENCE.md -->

# Schema Reference


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Schemas in this package:

- `crystal-specimen.schema.json`;
- `fixture.schema.json`;
- `run-config.schema.json`;
- `result-certificate.schema.json`.

## Versioning

Use semantic schema identifiers. A breaking field or meaning change increments the major version. A new optional field increments the minor version.

## Unknown fields

The release must choose and document whether unknown fields are rejected or preserved. Scientific records should normally reject unknown fields in authoritative mode and preserve them in migration mode.

## Units

The schema uses explicit unit-suffixed field names such as `length_mm`, `mass_g`, and `temperature_c`. A generic numeric field named only `length` is forbidden.


---

<!-- docs/r1013/manual/04_TECHNICAL/VALIDATION_AND_UNCERTAINTY.md -->

# Validation and Uncertainty


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Uncertainty sources

- length and diameter measurement;
- angle measurement and convention;
- density and material constants;
- crystallographic orientation;
- fixture and preload;
- electrode loading;
- temperature;
- mesh resolution;
- solver tolerance;
- mode matching;
- sensor position;
- calibration and clock.

## Required uncertainty layers

1. Input uncertainty.
2. Material uncertainty.
3. Orientation uncertainty.
4. Fixture uncertainty.
5. Numerical uncertainty.
6. Measurement uncertainty.
7. Model-family uncertainty.

## Prospective comparison

Freeze the model and candidate frequencies before importing the holdout measurement. Preserve all comparisons, including nulls.


---

<!-- docs/r1013/manual/04_TECHNICAL/VARIABLE_CODEC_AND_STATE_GEOMETRY.md -->

# Variable Codec and State Geometry


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Corrected variable form

There is no one-bit extension field. Refinement can be added on the left or right of the fixed core:

\[
C_{L,3}^{d_L}
\mid E_3
\mid S_{\mathrm{tor},6}
\mid S_{\mathrm{pol},6}
\mid S_{\mathrm{rad},6}
\mid C_{R,3}^{d_R}.
\]

The decimal transport envelope is:

```text
16 | packed payload | terminal
```

Legal payload width:

\[
W=21+3(d_L+d_R).
\]

The parser chooses the smallest legal width that contains the payload. It then enumerates all legal left and right splits.

## State meaning

The three S6 states are source-reported as:

- toroidal phase;
- poloidal phase;
- radial phase.

The radial phase is not a linear \(s/63\) distance. The active hypothesis uses a nonlinear sundial table with 15 degrees per hour-like phase unit.

## Recursive operators

Left refinement:

\[
\mathcal R_L(c):(L,\mathbf s,R)\rightarrow(L\oplus_Lc,T_c^L(\mathbf s),R).
\]

Right refinement:

\[
\mathcal R_R(c):(L,\mathbf s,R)\rightarrow(L,T_c^R(\mathbf s),R\oplus_Rc).
\]

Left and right operations are not assumed to commute.

## State-dependent edge law

The base odds ratio is source-approved as 10/9, modified by state, child, edge, and refinement side:

\[
r_e=\frac{10}{9}M(\phi_{\mathrm{tor}},\phi_{\mathrm{pol}},\phi_{\mathrm{rad}},c,e,\sigma).
\]

Convert odds to an edge fraction:

\[
t_e=\frac{r_e}{1+r_e}.
\]

Generate the shared node analytically by spherical interpolation or the declared body-space equivalent.

A global 10/9 law was not recovered. Only the state-dependent base-ratio model remains active.

## Training corpus

The corrected 19-wire response is intended to encode eight compact/refined pairs and one three-depth same-point chain. The solver must recover the partition. It must use every wire exactly once and must not request the same relationship again before exhausting the exact-cover search.


---

<!-- docs/r1013/manual/05_REFERENCE/CONTRIBUTOR_DOC_MAINTENANCE.md -->

# Contributor Documentation Maintenance


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## One source per fact

Generate command lists from the parser or test them directly. Generate schema field tables from the schema. Do not maintain three hand-written copies of the same interface.

## Required documentation tests

- every shell command parses;
- every executable example runs in a clean environment;
- every JSON example validates;
- every referenced path exists;
- every evidence label is valid;
- every command marked current exists;
- every command marked target is removed from release docs unless implemented;
- version and release status match package metadata;
- no private provenance enters public docs;
- no unsupported physical claim passes the vocabulary and claim gates.

## Writing rules

Use short direct sentences. Use one term per concept. Put conditions before actions. Put warnings before the step that can cause harm or data loss. Avoid marketing language.


---

<!-- docs/r1013/manual/05_REFERENCE/DOCUMENTATION_ACCEPTANCE_MATRIX.md -->

# Documentation Acceptance Matrix

| ID | Requirement | Verification |
|---|---|---|
| DOC-001 | A new user can create a specimen without reading source code. | clean-user walkthrough |
| DOC-002 | The manual distinguishes measured and computed frequencies. | claim-lint test |
| DOC-003 | Every JSON example validates. | schema test |
| DOC-004 | Every current command exists. | help-tree test |
| DOC-005 | Every release example executes. | documentation integration test |
| DOC-006 | Windows and Linux installs are covered. | clean VM or CI jobs |
| DOC-007 | Geometry conventions have diagrams or unambiguous text. | human review |
| DOC-008 | Unknown orientation produces a range or refusal. | solver test |
| DOC-009 | Proof bundle verification is documented. | end-to-end test |
| DOC-010 | Research hypotheses carry non-claim boundaries. | claim audit |
| DOC-011 | No public document contains private personal provenance. | privacy scan |
| DOC-012 | The consolidated manual matches the individual documents. | build and diff gate |


---

<!-- docs/r1013/manual/05_REFERENCE/ERROR_MESSAGES.md -->

# Error Message Contract

An error message must state:

1. What failed.
2. Which field or artifact caused it.
3. Why the operation cannot continue.
4. The smallest repair action.
5. Whether the input was modified.

Examples:

`SPECIMEN_SCHEMA_INVALID: geometry.length_mm must be greater than zero. Enter the measured tip-to-tip length in millimetres. The file was not modified.`

`INSUFFICIENT_GEOMETRY_FOR_FEM: geometry.narrow_diameter_mm is null. Add the measured narrow diameter or use a quick estimate. No mesh was created.`

`GMSH_NOT_FOUND: the full mesh command needs the Gmsh executable. Install Gmsh and run 'gmsh --version'. Quick estimates remain available.`

`ORIENTATION_UNDERDETERMINED: the full anisotropic result requires orientation. Add an orientation record or run an orientation ensemble.`


---

<!-- docs/r1013/manual/05_REFERENCE/FREQUENCY_KEY_REGISTRY.md -->

# Frequency Key Registry


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Candidate keys may have several registered roles. One role does not prove another.

| Value | Candidate roles | Status |
|---:|---|---|
| 8 Hz | base rhythm or difference key | candidate |
| 16 Hz | ring or traveling-pattern rate | candidate |
| 20 Hz | pulse family | candidate |
| 20.48 Hz | 4096/200 macrocycle family | derived candidate |
| 32 Hz | two-gap passage rate at 16 Hz | exact geometry-frequency realization |
| 396 | active-area numerator in 396/623; frequency candidate | multi-role candidate |
| 512 Hz | 32 blank sub-bins times 16 Hz | exact derived rate |
| 528 Hz | 33 active passages at 16 Hz; frequency key | exact geometry-frequency realization and candidate drive |
| 560 Hz | 35 total passages at 16 Hz; frequency key | exact geometry-frequency realization and candidate drive |
| 925 Hz | keyed carrier candidate | source-derived candidate |
| 4096 Hz | phase authority and carrier candidate | registered base |
| 20.480 kHz | 5 times 4096 Hz | exact arithmetic candidate |
| 32.768 kHz | binary clock family | exact arithmetic candidate |

The registry must store origin, arithmetic role, physical hypothesis, tests, controls, and evidence class separately.


---

<!-- docs/r1013/manual/05_REFERENCE/KNOWN_LIMITATIONS.md -->

# Known Limitations


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


- No RGCS physical hypothesis has been confirmed by the software alone.
- The current observed public repository has zero confirming bench measurements in its canonical evidence store.
- The regular faceted model cannot represent severe natural irregularity.
- Unknown orientation can dominate anisotropic results.
- Fixture modeling may be incomplete.
- Loss and Q prediction are limited without damping data.
- A full microscopic quantum model is not implemented.
- Dynamic boundary calculations do not establish multiverse transfer.
- The aperture model lacks exact gap indices and several construction dimensions.
- The variable codec transition and radial phase table remain underdetermined.
- Geographic rendering must stop at the highest justified stage.


---

<!-- docs/r1013/manual/05_REFERENCE/MIGRATION_GUIDE.md -->

# Migration Guide


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## From canonical-only v8.0.0 workflows

The current CLI accepts `ideal_n7` and `nominal`. R10.13 adds custom specimen files.

Canonical workflows remain valid:

```bash
rgcs-v4 geometry nominal
rgcs-v4 modes nominal --n 12
```

Equivalent target workflow:

```bash
rgcs crystal export-canonical nominal --out nominal.json
rgcs crystal modes nominal.json --count 12
```

The exported file must reproduce the canonical geometry exactly.

## Historical codec profiles

Old monolithic packet profiles remain historical compatibility records. They cannot become the default parser for the active segmented family.

## Proof bundles

Never migrate a proof bundle in place. Create a new bundle and preserve the old one.


---

<!-- docs/r1013/manual/05_REFERENCE/RELEASE_CHECKLIST.md -->

# Documentation Release Checklist

- [ ] Repository branch and HEAD recorded.
- [ ] Package version matches release notes.
- [ ] Current command tree captured.
- [ ] Custom specimen workflow implemented.
- [ ] Desktop wizard implemented or docs state it is absent.
- [ ] All examples validate and execute.
- [ ] Three-platform clean install passes.
- [ ] Gmsh absence and presence paths tested.
- [ ] Quick estimate matches hand calculation.
- [ ] FEM convergence tutorial passes.
- [ ] Proof bundle builds and verifies.
- [ ] No-mock audit passes.
- [ ] Private provenance scan passes.
- [ ] Unsupported claim scan passes.
- [ ] SHA-256 inventory generated.
- [ ] No tag, push, or public upload without operator authorization.


---

<!-- docs/r1013/manual/05_REFERENCE/SOURCE_BASIS.md -->

# Source Basis


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


This baseline was drafted from the following active or current records:

- Public repository README observed at blob `8f70665abd2f2a6df0a24b8c3fdd9293793d9101`.
- `docs/guide/README.md` blob `24deef9fe0c312affce5c0a5eb59e0355618b47a`.
- `pyproject.toml` blob `092e6acafa47c558d8a54e5c6fe353e9b58262e9`.
- `docs/guide/USING_THE_CLI.md` blob `40380d135afa4a76ceaec17cb633730b77a6329e`.
- `docs/guide/USING_THE_PYTHON_API.md` blob `51a8ce49284a43ae460f5060d5691a0bbbae57c0`.
- `docs/USER_GUIDE_V4.md` blob `870501bc0e440346d5936ecabef9af01ef438057`.
- `rscs2_core/crystal110.py` blob `2670eaa037f3f4f201a66a556ccac85c0fc01a67`.
- `rgcs_core/geometry/crystal.py` blob `2a91ccf3fd2df12e633554f3d0938685501d68ec`.
- `rscs2_core/cli.py` blob `2b241f60b871f4f9a48bf6e949673def6856f5c6`.
- `docs/v8/R15_FINDINGS.md` blob `70385c31b675c0fe66b9f658e22a2c189618ae41`.
- R10.12 consolidated private release prompt pack, SHA-256 `4b1f774e956cb7a3c46da1b2331963d38afb7378fca533e625767236c546b17c`.
- Corrected R10.13 source-provenance notes for the variable codec, 19-wire training response, dynamic-boundary timing, aperture geometry, and phase-state model.

Historical documents are used only when they remain compatible with active corrections.


---

<!-- docs/r1013/manual/05_REFERENCE/UNITS_AND_CONVENTIONS.md -->

# Units and Conventions

- Length input: millimetres unless the field states another unit.
- Mesh internal length: metres where required by the solver.
- Mass: grams for specimen input.
- Density: grams per cubic centimetre for specimen input; kilograms per cubic metre in SI solver records.
- Frequency: hertz.
- Time: seconds; display may use milliseconds or microseconds.
- Angle: degrees in user files; radians in internal trigonometric calculations.
- Diameter mode: `across_vertices` or `across_flats`.
- Angle mode: `face_slope`, `axis_to_face`, or `apex_included`.
- Body axis: female or wide apex toward male or narrow apex, unless the specimen file overrides the convention explicitly.
- Missing value: null, never zero.
