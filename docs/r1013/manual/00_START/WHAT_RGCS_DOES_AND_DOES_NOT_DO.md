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
