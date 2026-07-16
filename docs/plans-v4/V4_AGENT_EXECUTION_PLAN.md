# V4 Agent Execution Plan

**Status:** PLANNING. How an autonomous multi-run execution maps to the
32 phases. Mirrors the v3 agent model (sequential, tested, committed,
handed-off units) with a lead agent per tranche plus standing QA/release
agents.

## 1. Execution-agent map

| Agent | Tranche / role | Phases | Primary specs |
|---|---|---|---|
| V4-A1 | Foundations | P1–P4 | DECISION_LOG, MATH_MODEL, dependency/licence |
| V4-A2 | Geometry & mesh | P5–P8 | GEOMETRY_AND_MESH |
| V4-A3 | CPU solver | P9–P12 | CPU_SOLVER, REFERENCE_SYSTEMS (V.1–V.3,V.5,V.8) |
| V4-A4 | Anisotropy & piezo | P13–P16 | ANISOTROPIC_QUARTZ, PIEZO_MULTIPHYSICS |
| V4-A5 | Acceleration | P17–P20 | ACCELERATOR_BACKEND |
| V4-A6 | Eye + projections | P21–P24 | EYE_DIAGNOSTICS, OPTICAL, COIL_AND_EM |
| V4-A7 | Reference systems & inverse | P25–P28 | REFERENCE_SYSTEMS, DATA_AND_INVERSE |
| V4-A8 | Interfaces & release | P29–P32 | VISUALIZATION, DESKTOP_AND_CLI, RELEASE |
| V4-QA | Independent adversarial QA | after F, G, H | all — documents defects before fixes |
| V4-REL | Integration & release | P32 | RELEASE_PLAN |

## 2. Per-agent handoff protocol (inherits v3)

Each agent, on completing its tranche:
1. run the tranche's required tests + conservative-extension anchors;
2. verify frozen-path diff empty;
3. commit coherent checkpoints;
4. write `docs/AGENT_V4_A<n>_HANDOFF.md` (APIs, ids added, test state,
   open items for the next agent);
5. update `V4_TRACEABILITY_MATRIX`, the living registers, and
   `PROGRAMME_PROGRESS`;
6. hand to the next agent.

## 3. Autonomy rules (inherits v3 orchestrator)

- Continue automatically between phases; do not pause for routine
  confirmation.
- Stop only for a genuine blocker: a red conservative-extension anchor
  that cannot be fixed without touching frozen v3; a licence blocker; a
  dependency that cannot satisfy CPU-authority; a required GPU device
  that does not exist (→ ship experimental, do not fake); a safety/legal
  concern; or a contradiction between frozen authorities.
- Context limits are not a stop reason: finish the coherent unit, commit,
  handoff, continue.

## 4. Genuine decisions that may need the human

- **GPU CI runner:** parity/benchmark statuses beyond INTERFACE need a
  device — the human decides whether to provide a self-hosted/cloud GPU
  runner or accept "experimental, INTERFACE-only" for v4.0.0.
- **Public dataset selection/licences:** which quartz/resonator datasets
  are legally usable may need a human licence call (RV4-05).
- **Optional 4th reference system:** which branch to exercise (cavity /
  plate / ring) is a scope choice.
- **STEP import depth:** how far to push STEP/OCC vs "documented
  unsupported" is a cost/value call.

These are flagged, not assumed; everything else proceeds autonomously.

## 5. Parallelism

Tranches A→B→C are sequential (each needs the prior). From C onward, D
(physics) and E (acceleration) can proceed in parallel once the seam
(P17) exists; F needs D; G needs C+D; H needs all. The map above is the
critical path; a multi-agent run may fan out D/E and G-datasets early.
