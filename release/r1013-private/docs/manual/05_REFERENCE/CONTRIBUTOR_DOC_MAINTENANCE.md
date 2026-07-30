# Contributor Documentation Maintenance


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## One source per fact

Generate command lists from the parser or test them directly. Generate schema field tables from the schema. Do not maintain three hand-written copies of the same interface.

## Required documentation tests

- every shell command parses;
- every executable example runs in a clean environment;
- every JSON example validates;
- every referenced path exists;
- every evidence label is valid;
- every command marked current exists;
- every command marked target is removed from release docs unless implemented;
- version and release status match package metadata;
- no private provenance enters public docs;
- no unsupported physical claim passes the vocabulary and claim gates.

## Writing rules

Use short direct sentences. Use one term per concept. Put conditions before actions. Put warnings before the step that can cause harm or data loss. Avoid marketing language.
