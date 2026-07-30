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
