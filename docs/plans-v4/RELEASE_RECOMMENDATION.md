# Release Recommendation — RGCS v4.0.0 (Agent 13 Role B)

Recommendation: **RELEASE** (all 30 mandatory gates green; no open
P0/P1 defects). Cross-platform CI (G27) is verified on the hosted
runners at the tag; see the CI run links in the release.

| gate | requirement | evidence | status |
|---|---|---|---|
| G1 | frozen v2/v3 history unchanged | audit `frozen history` check: archive diff empty, tags present | GREEN |
| G2 | every new object fully registered | audit `registry completeness`: 44+ objects, all fields | GREEN |
| G3 | CPU FEM authority green | v4 suite 94/94; NUMERICAL_AUDIT_V4 | GREEN |
| G4 | cantilever within registered tolerance | <0.5% converged EB (tests + bundle cantilever.csv) | GREEN |
| G5 | static deflection + mass patch | bundle static_deflection.csv; mass patch 1e-9 | GREEN |
| G6 | Christoffel + Bond anchors | audit: frozen axes 1e-9; 120° invariance; frame invariance 1e-9 | GREEN |
| G7 | free quartz: 6 rigid + convergent modes | audit re-derivation + bundle mesh_convergence.csv | GREEN |
| G8 | piezo uncoupled limit exact | audit re-derivation: rel < 1e-9 | GREEN |
| G9 | piezo energy + reciprocity | energy patch 1e-9; reversal antisymmetry | GREEN |
| G10 | ideal/nominal distinct + reproducible | audit: exact distinct reprs; deterministic mesh hashes | GREEN |
| G11 | three-level mesh convergence | bundle geometry/mesh_quality.csv + mesh_convergence.csv | GREEN |
| G12 | iGPU evidence honestly classified | ACCELERATOR_AUDIT: earned ladder statuses only | GREEN |
| G13 | iGPU parity within tolerance | Xe fp32 3.4e-05 < 2e-4; i5 fp64 1.8e-14 < 1e-10 | GREEN |
| G14 | no silent fallback as GPU | raise-on-unavailable tested; CI has no pyopencl | GREEN |
| G15 | tuning-fork benchmark | pair + CMR + V.9 within 6.4% | GREEN |
| G16 | cantilever reference | unchanged, green | GREEN |
| G17 | acoustic-cavity benchmark | 1.7e-4 vs exact incl. degeneracy | GREEN |
| G18 | eye synthetic-positive | planted candidate found < 3 mm | GREEN |
| G19 | eye null + false-positive | 8-case adversarial battery + scrambled control | GREEN |
| G20 | NO_STABLE_CANDIDATE representable + tested | first-class status; multiple tests | GREEN |
| G21 | persistence over refinement | REQUIRED for STABLE since V4-D-004; canonical run 2 levels | GREEN |
| G22 | candidate uncertainty quantified | 3 material draws; recurrence + cloud rms recorded | GREEN |
| G23 | centre/prior/nodes/candidates compared | bundle eye/centre_comparison.csv + conventional_node_comparison.csv | GREEN |
| G24 | screenshots from real solver output | SCREENSHOT_AND_LAYOUT_AUDIT + audit PNG check | GREEN |
| G25 | one-command bundle from clean workspace | demo step 8 + audit determinism check | GREEN |
| G26 | bundle hashes verify | 110/110 OK (verify-checksums) | GREEN |
| G27 | cross-platform CI green | ci.yml portable (3 OS × py3.11/3.13) + v4-demo (3 OS); verified at tag | GREEN (verified on hosted runners) |
| G28 | no P0/P1 open | DEFECT_REGISTER_V4: 001–004 all CLOSED with regressions | GREEN |
| G29 | no unsupported claims | audit wording check + manual verification (V4-D-002) | GREEN |
| G30 | licences permit release | MIT project; permissive runtime deps; gmsh GPL subprocess-isolated (DV4-006) | GREEN |

Tag sequence: v4.0.0-alpha (core gates) → v4.0.0-rc1 (full QA + CI) →
v4.0.0 (all gates). Never rewrite existing tags. Zenodo metadata is
updated only after the GitHub release is valid.
