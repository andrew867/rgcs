# RSCS Foundations — manuscript (skeleton)

**Status:** skeleton only. Production deferred to Agent 09 (DECISION_LOG
D3-014). Agent 03 has delivered the mathematical content this manuscript
will present; the manuscript itself (XeLaTeX, generated figures/tables) is
Agent 09's dependency boundary.

## Source material (authored by Agent 03)

- `docs/RSCS_MATHEMATICAL_MODEL.md` — state space, operators, composition,
  coupling algebra, Conservative Extension Property, invariants.
- `docs/RSCS_OPERATOR_REGISTRY.md` — the 14 coordinates + 13 operators.
- `docs/RSCS_COORDINATE_SCHEMA.md` — serialization/validation schema.
- `rscs_core/` — the tested implementation (single source of numbers).

## Planned sections (for Agent 09)

1. Introduction — what RSCS is, and the "earns its complexity" test.
2. The typed state space (base × fibre × modes × metadata).
3. Coordinates (RSCS-C.1..14) with units and manifolds.
4. Operators (RSCS-O.1..13): frames, spectral maps, coupling algebra,
   propagation, preparation, observation, uncertainty, provenance firewall.
5. Conservative Extension Property and the embedding ι, with the machine
   evidence reproducing RGCS-M.23/24/28/46/55/56/10-11.
6. Identifiability, gauge, singularities, uncertainty boundary.
7. Comparison with standard coordinate systems.

Every numeral in the eventual manuscript must be generated from `rscs_core`
at build time (no hand-typed numbers), matching the v2 manuscript discipline.
