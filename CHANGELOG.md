# Changelog

All notable changes to RGCS / RSCS. Semantic versioning; the frozen
v2.0.0 baseline is tag `v2.0.0` and `archive/v2.0.0/`.

## [Unreleased] — 3.0.0 programme (RSCS 1.0)

### Added
- Agent 01: `docs/V2_BASELINE_AUDIT.md` (baseline reproduced: 232/232
  archive files identical, 10/10 release checksums verified, 223/227
  tests pass on Windows with all 4 discrepancies explained).
- Agent 01: `docs/V2_TO_V3_MIGRATION_MAP.md` (all 61 equations and 14
  hypotheses dispositioned; registry/versioning rules for v3).
- Programme control documents: `DECISION_LOG.md`, `CLAIM_REGISTER.md`,
  `SOURCE_REGISTER.md`, `ASSUMPTIONS.md`, `NEGATIVE_RESULTS.md`
  (v2's `INCONSISTENCY_REGISTER.md` and `TRACEABILITY_MATRIX.md`
  continue as living registers).
- v3 skeleton per `EXPECTED_TREE`: `rscs_core/` (10 subpackages),
  `manuscripts/` (4 works), `embedded/`, `references/`,
  `tests/adversarial/`, `experiments/protocols|notebooks`.
- `.gitattributes` line-ending normalization.

- Agent 02: verified source registry, equation-provenance ledger, adaptation
  /exclusion matrices, and the frozen `docs/RSCS_NOTATION_LEDGER.md`
  (RSCS-C.1..14 coordinates, RSCS-O.1..13 operators).
- Agent 03: `rscs_core` mathematical backbone — 14 typed coordinates, 13
  operators, RGCS→RSCS embedding with the Conservative Extension Property
  (reproduces RGCS-M.23/24/28/46/55/56/10-11), a claim/provenance firewall,
  and a machine-readable RSCS registry. 64 new tests; anti-Hermitian coupling
  `K=i·2πg` (QA-D-04) enforced. Docs: `RSCS_MATHEMATICAL_MODEL.md`,
  `RSCS_OPERATOR_REGISTRY.md`, `RSCS_COORDINATE_SCHEMA.md`,
  `AGENT_03_HANDOFF.md`.
- Agent 04: Hydrogenuine memory bridge — RSCS-C.15 HG record (ENG) +
  RSCS-O.14/15/16 store/replay/update; NHT/HAL kept HYP-quarantined;
  falsifiable software claims H-15..H-19. Docs: `NHT_HAL_RSCS_MAPPING.md`,
  `HG_RSCS_MEMORY_ARCHITECTURE.md`.
- Agent 05: anisotropic crystal propagation — RSCS-O.17 Christoffel wave
  speeds (`rscs_core.propagation`) + `rgcs_core/anisotropy` (α-quartz
  elastic constants, closes v2 D-19a); resolves the scalar `v_L`
  Hypothesis into a measured-orientation model reproducing v2 at the
  crystal axes. Doc: `RGCS_CRYSTAL_APPLICATION.md`.
- Agent 06: optical/photon-phonon/nonreciprocal layer — RSCS-C.16/C.17
  coordinates, Jones↔Stokes on C.9, RSCS-O.18..O.23 (dispersion phase,
  conversion selection rules, Autler–Townes, critical coupling,
  state-dependent susceptibility with reciprocal-null default, directional
  betas/beating); `rgcs_core/optics` (quartz optical constants, ray/path
  model, photoelastic/M2 estimates); optical experiment schema +
  generated mechanism comparison table; claims H-20..H-23 (H-21/H-23
  pre-registered nulls, D6-003). Doc:
  `OPTICAL_AND_NONRECIPROCAL_COUPLING.md`.

### Changed
- `pyproject.toml`: project renamed `rgcs-v3` 3.0.0a1 (D3-001); missing
  `pyyaml` dependency declared (fixes V2-PKG-01 for v3 builds); `rscs_core`
  packaged with its registry yaml.
- v2 release artifacts moved unchanged to `archive/v2.0.0/release/`;
  top-level `release/` reserved for v3 outputs.

## [2.0.0] — 2026-07-14

Frozen baseline. See `archive/v2.0.0/release/RELEASE_NOTES.md`.
