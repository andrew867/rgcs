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
