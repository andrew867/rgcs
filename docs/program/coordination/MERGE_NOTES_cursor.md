# Merge notes — program/cursor-app-integration

## Merge order (operator / integration agent)

1. Shared schemas / authority docs (Claude) if present
2. Pure core algorithms (Codex) if present — displace `rgcs_lab/reference/*`
3. This branch: hub, FastAPI, adapters, static distro, tests
4. Full regression — do not delete or weaken failing tests

## Conflicts

- Prefer frozen authority over new wording
- Prefer existing tested `rgcs_coordinate` over reimplementation
- Prefer adapter imports of Codex packages over reference demos when both exist
- Do not resolve by changing golden fixtures to pass

## Artifacts

- `static/hub/` — static distribution
- `docs/program/coordination/HANDOFF_cursor.json`
- `examples/lab/` — CLI examples
- `schemas/lab/receipt.schema.json`

## Known YELLOW

- Physical Earth projection underdetermined
- High-fidelity spoof-SPP underdetermined (reduced-order only)
- Prospective predictions pending measurement
- Reference Golay/frames/lattice demos pending Codex package displacement
