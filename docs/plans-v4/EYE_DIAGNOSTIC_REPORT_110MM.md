# Eye Diagnostic Report — Canonical 110 mm Crystal (RGCS v4, Agent 09)

**Verdict: `CONVENTIONAL_NODE_EXPLAINS_RESULT`.**
The canonical crystal does **not** exhibit a stable, computationally
special interaction region under the registered 16-diagnostic
consensus procedure. The single region that reached cross-family
agreement is explained by ordinary modal node/antinode structure.
Per the engine's charter, this null-adjacent result is a **passing
scientific outcome** — the engine never assumed an eye exists
(DV4-010: eye claims are never Established).

Engine: `rscs2_core/eye.py`  Tests: `tests/v4/test_rscs2_eye.py` (15,
including the full mandatory adversarial battery)
Evidence: `evidence/v4/agent09/` (consensus JSON, candidate CSV, field
overlays, uncertainty-cloud figure, null-comparison table, run summary)

## 1. The sixteen registered diagnostics

All sixteen (RSCS2-D.1–D.16) carry field definition, units,
normalization, conventional interpretation, failure conditions,
artifact risks, classification (all **DER** — never EST, DV4-010), and
provenance in `DIAGNOSTIC_SPECS`; registered in the machine registry.

| ID | field | note |
|---|---|---|
| D1 | displacement amplitude | antinode structure is conventional |
| D2 | strain-energy density | junction concentration is conventional |
| D3 | kinetic-energy density | co-located with D1 by construction |
| D4 | von Mises stress | corner singularities = classic artifact |
| D5 | electric-energy density | REFUSES to run without a solved potential |
| D6 | optical-path sensitivity | probe direction declared |
| D7 | drive-mode overlap | drive pattern declared |
| D8 | cross-modal overlap | near-degenerate pair declared |
| D9 | phase coherence | REFUSES real fields (degenerate case declared) |
| D10 | phase singularity | REFUSES real fields; winding validated on a synthetic vortex (+1 at the planted point) |
| D11 | displacement vorticity | plotted circulation ≠ physical vortex (D6-003) |
| D12 | EM circulation | REFUSES to run without a solved field; validated against Ampère's law (μ₀I, 10⁻³) |
| D13 | boundary sensitivity | gate over BC variants |
| D14 | mesh persistence | gate over refinement |
| D15 | uncertainty persistence | gate over material draws |
| D16 | cross-physics consensus | family-deduplicated agreement count |

**Anti-double-counting:** D1/D3/D7 are one *kinematic* family, D2/D4
one *elastic-energy* family, etc. Agreement is counted over distinct
families, so correlated diagnostics cannot vote twice.

## 2. The consensus procedure (documented, not an average)

Sequential pass/fail gates, every rejection recorded with its reason:
(1) top-quantile (95%) region extraction per diagnostic — candidates
are REGIONS (centroid + bounding box), never point claims;
(2) cross-diagnostic clustering; ≥3 distinct families required;
(2b) localization: region extent ≤ 0.35 × body length (a flat or
body-spanning field is not an interaction region);
(3) inside-body validity; (4) null comparison against the ordinary
node/antinode stations of the modes examined; (5) mesh persistence
(D14); (6) boundary sensitivity (D13); (7) mode dependence (≥2 modes);
(8) uncertainty persistence (D15).

## 3. Mandatory adversarial battery (all green)

| case | expected | result |
|---|---|---|
| symmetric body (real FEM free cube) | no unique eye | not STABLE ✔ |
| synthetic planted candidate | found as region at the planted point | STABLE, centroid < 3 mm ✔ |
| mesh artifact absent from refined solve | rejected | MESH_ARTIFACT_REJECTED ✔ |
| boundary-created candidate | flagged | BOUNDARY_SENSITIVE_CANDIDATE ✔ |
| two competing regions | both reported, ambiguity flagged | 2 candidates, competing=True ✔ |
| candidate outside the body | invalid | rejected + NO_STABLE_CANDIDATE ✔ |
| uncertainty collapse (1/4 draws) | dropped | "collapsed under parameter uncertainty" ✔ |
| no candidate (flat + random noise) | null passes | NO_STABLE_CANDIDATE ✔ |

## 4. The canonical-110 run (real anisotropic FEM)

Free-free ideal-N7 crystal, frozen α-quartz stiffness/density, gmsh
meshes at clmax 8.0 mm (coarse) and 5.5 mm (refined); cradle-support
boundary variant (springs at the 0.224L/0.776L fixture stations);
three ±1% material draws (C ±1%, ρ +1%). First elastic modes:

| mode | coarse (Hz) | refined (Hz) |
|---|---|---|
| 1 | 13781.7 | 13775.7 |
| 2 | 13782.0 | 13775.7 |
| 3 | 26067.0 | 25897.0 |
| 4 | 31897.6 | 31855.2 |

Modes 1/2 are a symmetry-protected degenerate bending pair (hexagonal
cross-section) — resolved as such, not averaged away.

**Outcome:** 15 cross-diagnostic clusters formed. Fourteen failed the
family-agreement gate (kinematic-only or elastic-energy-only hotspots:
shaft-surface antinode rings, cap stress concentrations). One region —
centroid (−0.15, −0.04, 102.18) mm, at the male cap/shaft junction,
extent 14.0 mm, families {kinematic, cross-modal, rotational} —
reached 3-family agreement, passed localization and validity, and was
then resolved by the **null comparison**: it lies 3.94 mm from an
ordinary node/antinode station of the examined modes
(≤ 4 mm tolerance) → `CONVENTIONAL_NODE_EXPLAINS_RESULT`.

Distances of that region from the declared references:
geometric centre 47.2 mm, shaft midpoint ≈ 47 mm, frozen RGCS node
prior (RGCS-M.39) ≈ 46 mm — it is NOT the historical node-prior
location; it is the male-junction modal feature.

## 5. What would change this verdict

A STABLE_CANDIDATE_REGION would require a localized region where ≥3
independent diagnostic families co-locate away from ordinary modal
features, persisting across mesh refinement, boundary variants, ≥2
modes, and material uncertainty. Nothing in the first four elastic
modes of the canonical geometry does this. Extending to more modes,
piezo-coupled (D5) and driven complex-response (D9/D10) fields is
mechanically supported by the engine and remains open work — the
present verdict covers what was actually computed, no more.
