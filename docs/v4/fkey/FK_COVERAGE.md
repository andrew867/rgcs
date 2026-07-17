# FK coverage ledger (A02)

Requirements: **46** — **ALL PASS**

| ID | Requirement | Status |
|---|---|---|
| FK-P001 | frozen seed keys registered with provenance | IMPLEMENTED_AND_TESTED |
| FK-P002 | prearrival specimen immutable; seller claims never measurements | IMPLEMENTED_AND_TESTED |
| FK-P003 | FK-CORR-001 equal-percentage-error correction record | IMPLEMENTED_AND_TESTED |
| FK-P004 | hypotheses preregistered, optimizer cannot rewrite | IMPLEMENTED_AND_TESTED |
| FK-P005 | no lore language can reach measured status: evidence classes enumerated and schema-enforced | IMPLEMENTED_AND_TESTED |
| FK-M001 | exact rational parsing; floats refused | IMPLEMENTED_AND_TESTED |
| FK-M002 | mechanism taxonomy, one primary class per relation | IMPLEMENTED_AND_TESTED |
| FK-M003 | frozen seed corpus classifies per the pack | IMPLEMENTED_AND_TESTED |
| FK-M004 | mechanism-first ranking; dedup; harmonic census | IMPLEMENTED_AND_TESTED |
| FK-M005 | phase closure: windows, drift, burst design | IMPLEMENTED_AND_TESTED |
| FK-M006 | sine has no 5th; square has 1/5 (analytic + FFT cross-check) | IMPLEMENTED_AND_TESTED |
| FK-M007 | edge/plant shaping and expected-line gate | IMPLEMENTED_AND_TESTED |
| FK-M008 | Nyquist/alias arithmetic incl. the marginal-48k case | IMPLEMENTED_AND_TESTED |
| FK-M009 | AM sideband arithmetic | IMPLEMENTED_AND_TESTED |
| FK-C001 | prearrival screening model reproduces pack numbers; candidate band not magic number | IMPLEMENTED_AND_TESTED |
| FK-C002 | 2-DOF plant; transducer-vs-crystal discrimination | IMPLEMENTED_AND_TESTED |
| FK-C003 | linear plant has zero intermodulation; nonlinearity explicit | IMPLEMENTED_AND_TESTED |
| FK-C004 | fit refusal on undersampled/saturated; bootstrap Q | IMPLEMENTED_AND_TESTED |
| FK-C005 | thermal drift model for warm-up blocks | IMPLEMENTED_AND_TESTED |
| FK-C006 | BVD reuse from rscs2_core (no duplication) | IMPLEMENTED_AND_TESTED |
| FK-O001 | mechanism-first optimizer; arithmetic scores zero amplitude | IMPLEMENTED_AND_TESTED |
| FK-O002 | Pareto frontier per hypothesis, never one winner | IMPLEMENTED_AND_TESTED |
| FK-O003 | ten required drive comparisons compiled as families | IMPLEMENTED_AND_TESTED |
| FK-O004 | randomized blinded campaigns with sham + stop rules + no-post-hoc rule | IMPLEMENTED_AND_TESTED |
| FK-J001 | drive-recipe schema; strict validation; fuzz | IMPLEMENTED_AND_TESTED |
| FK-J002 | canonical JSON + content hash | IMPLEMENTED_AND_TESTED |
| FK-J003 | unknown versions refused with explicit no-migration | IMPLEMENTED_AND_TESTED |
| FK-J004 | desktop bridge: compile/upload/arm/run/logs/verify, never bypassing the FSM | IMPLEMENTED_AND_TESTED |
| FK-F001 | firmware source tree with FSM mirroring the twin | FIRMWARE_SOURCE_PROVIDED_NOT_COMPILED |
| FK-F002 | board profiles compile-time; unknown => OUTPUT_DISABLED | IMPLEMENTED_AND_TESTED |
| FK-F003 | signal backends with requested vs calculated-realized vs measured(None) separation | IMPLEMENTED_AND_TESTED |
| FK-F004 | 4096/20480 timing report with quantization + drift | IMPLEMENTED_AND_TESTED |
| FK-H001 | pin-conflict detection incl. boot-strap and input-only | IMPLEMENTED_AND_TESTED |
| FK-H002 | board questionnaire before any pin is named | IMPLEMENTED_AND_TESTED |
| FK-H003 | Gen-0 BOM/wiring/fixture/bring-up | ENGINEERING_PROTOTYPE_NOTHING_BUILT |
| FK-H004 | sensor limitations documented: INA219 slow-only, 48k mic marginal at 20.48k | IMPLEMENTED_AND_TESTED |
| FK-S001 | output off at boot; only RUNNING may drive output | IMPLEMENTED_AND_TESTED |
| FK-S002 | fresh single-use expiring arm lease; no auto-arm | IMPLEMENTED_AND_TESTED |
| FK-S003 | all 14 fault causes force output off and latch | IMPLEMENTED_AND_TESTED |
| FK-S004 | reset/watchdog/brownout land output-off, authority dropped | IMPLEMENTED_AND_TESTED |
| FK-S005 | missing amplitude refused, never defaulted | IMPLEMENTED_AND_TESTED |
| FK-S006 | hearing/animal caution documented; conservative first-run limits in schema (duty<=0.5, <=60s) | IMPLEMENTED_AND_TESTED |
| FK-T001 | six synthetic demos run from a fresh clone | IMPLEMENTED_AND_TESTED |
| FK-T002 | hash-chained device logs, verified by the bridge | IMPLEMENTED_AND_TESTED |
| FK-T003 | A24 red-team attacks as executable regression tests | IMPLEMENTED_AND_TESTED |
| FK-T004 | coverage bidirectional orphan check (this tool) | IMPLEMENTED_AND_TESTED |
