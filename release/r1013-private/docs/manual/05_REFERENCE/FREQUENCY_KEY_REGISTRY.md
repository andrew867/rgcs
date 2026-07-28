# Frequency Key Registry


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Candidate keys may have several registered roles. One role does not prove another.

| Value | Candidate roles | Status |
|---:|---|---|
| 8 Hz | base rhythm or difference key | candidate |
| 16 Hz | ring or traveling-pattern rate | candidate |
| 20 Hz | pulse family | candidate |
| 20.48 Hz | 4096/200 macrocycle family | derived candidate |
| 32 Hz | two-gap passage rate at 16 Hz | exact geometry-frequency realization |
| 396 | active-area numerator in 396/623; frequency candidate | multi-role candidate |
| 512 Hz | 32 blank sub-bins times 16 Hz | exact derived rate |
| 528 Hz | 33 active passages at 16 Hz; frequency key | exact geometry-frequency realization and candidate drive |
| 560 Hz | 35 total passages at 16 Hz; frequency key | exact geometry-frequency realization and candidate drive |
| 925 Hz | keyed carrier candidate | source-derived candidate |
| 4096 Hz | phase authority and carrier candidate | registered base |
| 20.480 kHz | 5 times 4096 Hz | exact arithmetic candidate |
| 32.768 kHz | binary clock family | exact arithmetic candidate |

The registry must store origin, arithmetic role, physical hypothesis, tests, controls, and evidence class separately.
