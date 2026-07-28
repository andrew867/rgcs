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
