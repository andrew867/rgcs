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
