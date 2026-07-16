# V4 Multiphysics Model (Agent M2)

The v4-completion platform is capability-aware: no numerical module
executes without a registered material/reference capability decision.

## Architecture

1. **MaterialCapabilities** (`rscs2_core/multiphysics/capabilities.py`;
   JSON schema `schemas/v4/material_capabilities.schema.json`):
   24 typed capability records per material — status
   (SUPPORTED/REFERENCE_ONLY/INTERFACE_ONLY/UNSUPPORTED/UNKNOWN),
   classification, parameter sets, sources, constraints, reason.
   UNKNOWN is not permission (tested).
2. **Registered records** (`materials.py`): 16 — alpha quartz plus 15
   reference/quarantine systems (isotropic benchmark, cantilever,
   tuning fork, cavity, optical vortex field, chiral phonon,
   exciton-magnon, SOE-phonon, dynamic ME, metacrystal, LiNiPO4,
   MnF2, nonlinear AFM, phonon-exchange, FDT adapter). Reference
   systems carry `reference_only: true`; alias lookups are rejected
   so a toy fixture can never inherit quartz identity.
3. **Applicability service** (`applicability()`): APPLICABLE /
   REFERENCE_ONLY / INTERFACE_ONLY / NOT_APPLICABLE with reason codes;
   surfaced on the CLI as `rgcs-v4 capabilities [material] [--check]`.
4. **Block state + coupling graph** (`coupling.py`): 13 state blocks
   (mechanical … source_hypothesis). Every edge declares operator,
   units, symmetry, capability predicate, classification, provenance,
   reversibility, energy accounting, and null behavior. The compiler
   rejects unsupported edges BEFORE numerics; the source_hypothesis
   block can never drive a physics block (FDT/lore quarantine at the
   graph level).
5. **Result envelope** (`envelope.py`, `rgcs.v4.result.1`):
   deterministic serialization; NOT_APPLICABLE ⇒ null value + reason
   code (no fake zeros); classification is checked against every cited
   source's M1 ceiling at envelope construction (anti-laundering,
   defense in depth with the provenance layer).

## Alpha-quartz posture (frozen boundary 6)

Supported: anisotropic/isotropic elasticity, piezoelectricity,
anisotropic dielectric, photoelasticity, birefringence (all
CORE_VALIDATED — the v4.0.0 stack). Interface-only: nonlinear optics.
Unsupported (with recorded reasons): magnetic order, magnons,
excitons (all flavors), exciton-magnon coupling, spin-phonon and
spin-orbit coupling, chiral phonons (no registered quartz g-factor),
dynamic magnetoelectric tensors, plasmonics, quantum-statistical
response, microscopic tunnelling, ferrotoroidic order, directional
optical response, domain writing, thermal domain selection.

## Backward compatibility

v2/v3 material inputs (frozen `rgcs_core` constants) are consumed
unchanged by the v4.0.0 solvers; the capability layer sits ABOVE them
and adds no capability silently — quartz's record mirrors exactly what
the validated stack implements.

Generated matrix: `docs/v4/V4_MATERIAL_CAPABILITY_MATRIX.md` (gate C5).
