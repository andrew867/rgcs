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
