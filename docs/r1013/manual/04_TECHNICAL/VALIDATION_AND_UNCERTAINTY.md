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
