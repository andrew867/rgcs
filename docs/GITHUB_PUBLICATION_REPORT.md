# GitHub Publication Report (Agent 13)

**Date:** 2026-07-15.

## Repository

| Field | Value |
|---|---|
| Owner / name | `andrew867/rgcs` (preferred name was available) |
| URL | https://github.com/andrew867/rgcs |
| Visibility | **PUBLIC** (created private; flipped after release verification) |
| Default branch | `main` |
| License detection | MIT (detected) |
| Citation detection | `CITATION.cff` (detected) |

## Commits and tags

| Ref | Commit | Meaning |
|---|---|---|
| `v2.0.0` | `f9fd2c2` | frozen baseline (immutable, pushed unmodified) |
| `v3.0.0-rc1` | `eed8e37` | release candidate (never moved) |
| version-flip commit | `441612c` | 3.0.0 versions + final release notes; source zip cut from this tree |
| `v3.0.0` | `83521f7` | final release tag (release-artifacts commit; full hosted matrix green) |

## Hosted CI matrix (final state: ALL GREEN)

Workflow: `.github/workflows/ci.yml`. Runs:
first matrix `…719`, repair runs `…410`/`…821`, final `29441702023`
(https://github.com/andrew867/rgcs/actions/runs/29441702023).

| Job | 3.11 | 3.13 |
|---|---|---|
| portable / ubuntu-latest | ✅ | ✅ |
| portable / windows-latest | ✅ | ✅ |
| portable / macos-latest | ✅ | ✅ |
| reference / ubuntu / pinned numpy+scipy | ✅ (single job) | — |

Portable tier: 377 tests per job (byte-equality node id deselected per
policy) + schema validation + generated-doc freshness. Reference tier:
pinned numpy/scipy, full portable behavior + release-builder smoke.
JUnit XML uploaded from every job; no `continue-on-error` anywhere.

## Failures encountered and fixes (repair loop)

1. **Reference job byte-equality failure with numpy pinned**
   (case_a drift). Documented as **D-V3-04** before fixing. First
   attempt: pin scipy 1.17.1 too (the goldens' recorded version).
2. **Still drifted with both pinned** → toolchain/libm sensitivity;
   executed the pre-registered fallback: byte-exactness scoped to the
   archived v2 build environment (verified at v2 release, recorded by
   checksum); **new portable test** `test_generator_numerically_equivalent`
   regenerates the goldens on EVERY platform and requires printed-precision
   agreement — this closed a real coverage gap (portable platforms
   previously had no regeneration check at all).
3. **macOS/ARM manifest drift**: manifest `expected` floats are full
   double precision; large trajectory-derived values needed a relative
   term. Comparison now `max(2e-8 abs, 1e-9 rel)` with per-field
   mismatch reporting. All platforms green thereafter.

No project regressions were found by hosted CI; every defect was in the
determinism-test environment policy, exactly where the v2 audit had
flagged the risk.

## Repository settings applied

- Issues ON, wiki OFF, discussions default (off), delete-branch-on-merge
  ON, squash merge ON, merge commits OFF, rebase merge OFF.
- Topics: reproducible-research, research-software, resonance, quartz,
  elastodynamics, coupled-oscillators, acousto-optics, falsification,
  pre-registration, provenance, python, metrology, open-science.
- Branch protection on `main` (applied after the public flip; the API
  is plan-gated for private free repos): 7 required status checks (all
  six portable jobs + reference), force pushes blocked, deletion
  blocked, `enforce_admins` OFF so a single maintainer is never locked
  out, strict up-to-date OFF (single-maintainer practicality).

## Release `v3.0.0`

https://github.com/andrew867/rgcs/releases/tag/v3.0.0 — 9 assets, sizes
verified equal to local bytes after upload:

| Asset | Size (bytes) | SHA256 (prefix) |
|---|---|---|
| rgcs-v3.0.0-source.zip | 30,618,281 | `dc6b1aa7` |
| rgcs_v3_manuscripts.zip | 311,919 | `bc4d99a1` |
| rgcs_v3_sample_experiments.zip | 6,580,763 | `477f82e1` |
| SHA256SUMS.txt | 446 | (self) |
| PROVENANCE.json | 1,248 | `1125f77e` |
| rscs_foundations.pdf | 85,686 | in manuscripts zip CHECKSUMS |
| rgcs_crystal_application.pdf | 68,607 | ditto |
| software_hardware_plan.pdf | 57,690 | ditto |
| historical_source_companion.pdf | 51,453 | ditto |

## Anonymous/public verification

Repository page 200; raw README image 200; release page 200; release
asset downloads 200 (SHA256SUMS content spot-verified); license MIT
detected; CITATION.cff detected; CI badge serves. Hygiene: tracked-file
secret scan clean before first push; no internal-docs/.venv/caches in
the repo or the source zip. Known accepted artifact: the immutable v2
archive's PROVENANCE.json records generic sandbox build paths
(`/home/claude/…`) — build-environment provenance, not personal data,
unmodifiable under the freeze.

## Known platform limitations

- Byte-exact golden reproduction requires the archived v2 build
  environment (D-V3-04); every hosted platform verifies numerical
  equivalence to printed precision instead.
- Source release only: no packaged desktop binaries (documented in the
  release notes; acceptance policy satisfied).

## DOI status

**DOI ISSUED (2026-07-16):** version DOI `10.5281/zenodo.21387947`,
concept DOI `10.5281/zenodo.21387946` — minted automatically from the
v3.0.1 release (the webhook was enabled after v3.0.0, so v3.0.1 is the
first archived release; v3.0.0 remains cited via the concept DOI
lineage). CITATION.cff and the README badge carry the DOIs.

## Commands for future releases

```bash
# 1. ensure green matrix on main
gh run list --branch main --limit 1
# 2. version flip commit (pyproject, CITATION.cff, __version__s,
#    tools/build_v3_release.py VERSION, release notes) + push, wait green
# 3. rebuild artifacts from the version commit and commit them
python tools/build_v3_release.py "$(git rev-parse HEAD)"
git add release && git commit && git push   # wait for green
# 4. tag + release + verify
git tag -a vX.Y.Z -m "…" && git push origin vX.Y.Z
gh release create vX.Y.Z --title "…" --notes-file … release/*.zip \
  release/SHA256SUMS.txt release/PROVENANCE.json manuscripts/*/*.pdf
gh release view vX.Y.Z --json assets
```
