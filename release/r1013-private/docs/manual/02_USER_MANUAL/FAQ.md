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
