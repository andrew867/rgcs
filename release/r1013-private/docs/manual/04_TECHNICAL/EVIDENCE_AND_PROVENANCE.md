# Evidence and Provenance


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Core rule

Lore proposes. Mathematics translates. Software attacks. Evidence decides. Provenance remembers.

## Record fields

Every result should record:

- source identifiers;
- operator and timestamp where appropriate;
- input hashes;
- software version and commit;
- equation or model identifier;
- assumptions;
- uncertainty;
- evidence class;
- correction status;
- superseded and superseding records;
- public-safety status.

## Private provenance firewall

Private operator records, personal identity claims, ancestry, political allegations, family allegations, appearance-based classification, and source-origin claims cannot become technical solver authority.

## Correction rule

Never delete a superseded value. Preserve the raw record, correction, reason, timestamp, and active replacement.
