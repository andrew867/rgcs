# Schema Reference


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Schemas in this package:

- `crystal-specimen.schema.json`;
- `fixture.schema.json`;
- `run-config.schema.json`;
- `result-certificate.schema.json`.

## Versioning

Use semantic schema identifiers. A breaking field or meaning change increments the major version. A new optional field increments the minor version.

## Unknown fields

The release must choose and document whether unknown fields are rejected or preserved. Scientific records should normally reject unknown fields in authoritative mode and preserve them in migration mode.

## Units

The schema uses explicit unit-suffixed field names such as `length_mm`, `mass_g`, and `temperature_c`. A generic numeric field named only `length` is forbidden.
