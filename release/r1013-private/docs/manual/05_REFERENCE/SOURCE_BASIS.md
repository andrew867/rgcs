# Source Basis


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


This baseline was drafted from the following active or current records:

- Public repository README observed at blob `8f70665abd2f2a6df0a24b8c3fdd9293793d9101`.
- `docs/guide/README.md` blob `24deef9fe0c312affce5c0a5eb59e0355618b47a`.
- `pyproject.toml` blob `092e6acafa47c558d8a54e5c6fe353e9b58262e9`.
- `docs/guide/USING_THE_CLI.md` blob `40380d135afa4a76ceaec17cb633730b77a6329e`.
- `docs/guide/USING_THE_PYTHON_API.md` blob `51a8ce49284a43ae460f5060d5691a0bbbae57c0`.
- `docs/USER_GUIDE_V4.md` blob `870501bc0e440346d5936ecabef9af01ef438057`.
- `rscs2_core/crystal110.py` blob `2670eaa037f3f4f201a66a556ccac85c0fc01a67`.
- `rgcs_core/geometry/crystal.py` blob `2a91ccf3fd2df12e633554f3d0938685501d68ec`.
- `rscs2_core/cli.py` blob `2b241f60b871f4f9a48bf6e949673def6856f5c6`.
- `docs/v8/R15_FINDINGS.md` blob `70385c31b675c0fe66b9f658e22a2c189618ae41`.
- R10.12 consolidated private release prompt pack, SHA-256 `4b1f774e956cb7a3c46da1b2331963d38afb7378fca533e625767236c546b17c`.
- Corrected R10.13 source-provenance notes for the variable codec, 19-wire training response, dynamic-boundary timing, aperture geometry, and phase-state model.

Historical documents are used only when they remain compatible with active corrections.
