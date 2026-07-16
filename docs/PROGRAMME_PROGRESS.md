# RGCS v3 / RSCS 1.0 — Programme Progress Register

Authoritative execution ledger. One row per agent; updated at each agent
completion. Inherited failures = documented frozen-baseline Windows/numpy
discrepancies — NOT regressions, re-verified at every checkpoint.
† As of Agent 06 the inherited count dropped 4 → 2: two vertical-slice
failures were missing-`jsonschema` artifacts and pass once
`jsonschema`/`referencing` are installed (environment fix; Agent 08
declares them in pyproject). Remaining 2: V2-WIN-01 (zip arcname
backslashes) and NR3-001 (Linux-generated golden CSVs).
‡ Agent 08 fixed V2-WIN-01 (POSIX bundle arcnames) and declared the
schema deps, so the inherited count is now 1: only NR3-001 (byte-equality
of Linux-generated golden CSVs; deselected in Windows CI, passes on the
Linux reference platform).

| Agent | Scope | Status | Commits | Suite (passed/inherited-failed/new-regressions) | Handoff |
|---|---|---|---|---|---|
| 01 | v2.0.0 baseline freeze + migration map | COMPLETE | `f9fd2c2` (baseline), `715486b` | 223/4/0 (of 227 v2) | `V2_BASELINE_AUDIT.md`, `V2_TO_V3_MIGRATION_MAP.md` |
| 02 | Source ingestion, equation provenance, frozen notation | COMPLETE | `939e030`, `af0b22f` | 227+6 lint /4/0 | `RSCS_NOTATION_LEDGER.md` (GATE OPEN, D3-008) |
| 03 | RSCS mathematical core + Conservative Extension | COMPLETE | `5048687`, `c4cde1c`, `a1cdd80`, `b42f977` | 293/4/0 | `AGENT_03_HANDOFF.md` |
| 04 | NHT/HAL → Hydrogenuine memory bridge | COMPLETE | `7e00f19` | 307/4/0 | `NHT_HAL_RSCS_MAPPING.md`, `HG_RSCS_MEMORY_ARCHITECTURE.md` |
| 05 | Crystal application (anisotropic Christoffel) | COMPLETE | `4ccdd89` | 315/4/0 | `RGCS_CRYSTAL_APPLICATION.md` |
| 06 | Optical / photon–phonon / nonreciprocal coupling | COMPLETE | `1052c24` | 347/2/0 † | `AGENT_06_HANDOFF.md` |
| 07 | Coil / laser / timing / experiment design | COMPLETE | `8751b51` | 364/2/0 | `AGENT_07_HANDOFF.md` |
| 08 | Software / hardware / CAD / portability (T1) | COMPLETE | `75229cc` | 376/1/0 ‡ | `AGENT_08_HANDOFF.md` |
| 09 | Four manuscripts + public docs + Lessons Learned | COMPLETE | `7baad8c` | 376/1/0 | `AGENT_09_HANDOFF.md` |
| 10 | Independent adversarial QA | COMPLETE | `22dd988` | 376/1/0; 3 new defects D-V3-01..03 documented | `QA_REPORT_V3.md` |
| 11 | Integration, repair, release, public package | COMPLETE | `1bd9c5a` + (this commit); tag `v3.0.0-rc1` | 376/1/0; D-V3-01..03 FIXED; gate table GREEN (rc) | `release/RELEASE_NOTES.md` |

## FINAL VERDICT (2026-07-15)

**GREEN — v3.0.0 released.** All 12 quality gates green with hosted CI
evidence: GitHub Actions matrix (ubuntu/windows/macos x Python
3.11/3.13 portable + pinned ubuntu reference) all green at the release
lineage. Repository: https://github.com/andrew867/rgcs. Release
artifacts + checksums + provenance under `release/`; Agent 13 record in
`docs/GITHUB_PUBLICATION_REPORT.md`.

## Registry / claims state

- RSCS registry ids: **40** (C.1–17 minus reserved; O.1–23) —
  `rscs_core/registry/rscs_registry.yaml`. Frozen RGCS-M registry: 61,
  schema 1, untouched.
- Claims: H-01..H-14 (v2, frozen), H-15..H-19 (Agent 04, ENG software),
  H-20..H-23 (Agent 06, optical; H-21/H-23 pre-registered nulls),
  H-24..H-30 (Agent 07: node-menu rows + timing gates).
- DECISION_LOG: D3-001..015, D4-001..003, D5-001..002, D6-001..003,
  D7-001..003.

## Standing verification (every checkpoint)

1. `.\.venv\Scripts\python -m pytest -q` → only the 4 inherited failures.
2. `git diff --stat 715486b HEAD -- archive/v2.0.0` → empty (freeze).
3. `python tools/generate_optical_comparison.py --check` → up to date.
4. `python experiments/schemas/validate.py` → all OK (needs jsonschema).

## Post-release stages

| Stage | Scope | Status | Record |
|---|---|---|---|
| 12 | Publication polish + contributor experience | COMPLETE (c9acd86..3ab9bf0) | docs/PUBLICATION_READINESS_REPORT.md |
| 13 | GitHub bootstrap, 3-OS CI, v3.0.0 release, public flip | COMPLETE (tag v3.0.0 at 83521f7) | docs/GITHUB_PUBLICATION_REPORT.md |
| 13b | Figure-rendering audit (D-V3-05/06 fixed, assets refreshed) | COMPLETE | DEFECT_REGISTER addendum |
| 14 | Measurement campaign design (ENG): lab manual, calibration, bench, protocol, pipeline, validation plan for H-01..H-30 | COMPLETE (this commit) | docs/VALIDATION_PLAN.md |
| 15 | Publication/DOI/community release: .zenodo.json + metadata, 7-piece communication kit (docs/community/), contributor + modelling roadmaps, final publication report (PUBLISH COMPLETE) | COMPLETE (this commit) | docs/FINAL_PUBLICATION_REPORT.md |
| v4-plan | RGCS v4 / RSCS 2.0 implementation planning (25 docs, 8 tranches, 32 phases; no production code) | COMPLETE (this commit) | docs/plans-v4/V4_HANDOFF.md |
| v4-A00 | RGCS v4 execution opened (branch v4-dev): dependency proof (scikit-fem/meshio/gmsh), rscs2_core foundation (reference formulas + registry/lint, 7 tests green), user decisions recorded. **M3 solver gate RED (defect V4-D-001): CPU eigensolver not yet reproducing analytic benchmarks -> no release.** | COMPLETE (defect closed by v4-A03) | docs/plans-v4/V4_AGENT_00_HANDOFF.md |
| v4-A03 | CPU elasticity authority COMPLETE (M3 gate GREEN): V4-D-001 closed (ddot-mass root cause); benchmarks green: cantilever EB -0.07%, convergence monotone, static deflection -0.2%, Timoshenko thick-beam +0.03%, cube exact Lame mode +0.03-0.05% (nu-independent), isotropic P-wave ladder, quartz Christoffel ladder EXACT vs frozen v3 (conservative extension V.6); boundaries B.1-B.4 validated (Robin limits, Rayleigh tip-mass); harmonic FRF, M-orthonormality <1e-8, .npz round-trip. 19 v4 tests. | COMPLETE (v4-dev) | rscs2_core/fem.py + tests/v4/ |

| v4-A04 | Anisotropic alpha-quartz COMPLETE: material record (+piezo/dielectric constants, Bechmann 1958), exact Bond rotations (identity/inverse/composition/trigonal-symmetry/90-deg anchor vs frozen), batched Christoffel == frozen v3 to printed digits on axes+40 off-axis+sweep, free-crystal 6 rigid modes + convergence + frame invariance + orientation sensitivity, degeneracy taxonomy (numerical/symmetry/section). 28 v4 tests. | COMPLETE (v4-dev) | ANISOTROPIC_QUARTZ_VALIDATION.md |
