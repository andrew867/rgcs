# V4-Completion Adaptation Matrix (Agent M1)

Machine authority: `sources/registry/v4_equation_ledger.yaml`
(loaded + ceiling-enforced by `rscs2_core/provenance_v4.py`). This is
the human view; the YAML wins on conflict.

| equation | source | adaptation | ceiling | key forbidden transfer |
|---|---|---|---|---|
| RGCS-V4-EQ-001 toroidal moment | SRC-V4-01 (Toyoda, metadata-only) | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz; identity w/ circulation or optical vortex |
| EQ-002 IOME free energy | SRC-V4-01 | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz; static E×H misuse |
| EQ-003 directional complex index | SRC-V4-01 | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz; Re/Im collapse |
| EQ-004 exciton cos²(θ/2) | SRC-V4-06 (topic-only) | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz; BSE claims |
| EQ-005 avoided crossing | frozen v3 authority | DIRECT | CORE_VALIDATED | reinterpretation of frozen results |
| EQ-006 nonlinear AFM trajectory | SRC-V4-03 (Schlauderer) | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz; ab-initio claims |
| EQ-007 J(Q) exchange | SRC-V4-04 (Afanasiev) | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz; DFT values |
| EQ-008 FDT force | SRC-V4-18 | HYPOTHESIS | SOURCE_HYPOTHESIS | ALL default solvers; EST/DER |
| EQ-009 FDT α_R | SRC-V4-18 | HYPOTHESIS | SOURCE_HYPOTHESIS | ALL default solvers; EST/DER |
| EQ-010 g2 transfer | SRC-V4-09 (topic-only) | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | bulk quartz; microscopic plasmonics |
| EQ-011 dynamic ME tensor | SRC-V4-12 (topic-only) | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz; shape-inferred reciprocity |
| EQ-012 SAM/OAM densities | EST standard (SRC-V4-00) | DIRECT | CORE_VALIDATED | identity w/ mechanical/toroidal quantities |
| EQ-013 chiral phonon L_z | SRC-V4-13 (topic-only) | REDUCED_ORDER | REDUCED_ORDER_VALIDATED | quartz default; identity w/ optical SAM |
| EQ-014 Frenet-Serret | EST standard | DIRECT | CORE_VALIDATED | twist identity; spacetime torsion |
| EQ-015 Saint-Venant torsion | EST standard | DIRECT | CORE_VALIDATED | — |

Ceiling audit is a live test
(`test_equation_ledger_complete_and_linked`): the first run of this
programme caught EQ-012 citing a topic-only source while claiming
CORE_VALIDATED — corrected by re-sourcing to the EST standard form
(the enforcement is mechanical, not editorial).
