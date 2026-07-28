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
