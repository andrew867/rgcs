# Reference Models


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


`rgcs_phryll_aperture_generator.scad` is a parametric geometry baseline. It models:

- a 35-position annulus;
- 33 active apertures and two configurable gaps;
- prime-derived inner and outer radii;
- a simplified six-sided double-terminated crystal.

It does not select the correct gap indices. It does not model coils, fields, structural loads, optical propagation, or propulsion. The Claude implementation pack must add automated syntax and render checks where OpenSCAD is available.
