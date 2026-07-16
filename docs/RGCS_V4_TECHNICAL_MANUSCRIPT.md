# RGCS v4 / RSCS 2.0 — Technical Manuscript

**Scope statement (binding, per the v4 required wording):** all v4
results are **computational**. The historical "eye" is a **Source
claim**; computed candidates are **diagnostics**, not discoveries; **no
experimental confirmation exists** for any coupling, region, or effect
described here; the eye engine **may return no candidate**, and for the
canonical crystal it returned a conventional explanation. The **CPU
float64 path is the numerical authority**; GPU statements reflect
**measured device evidence only**. The **nominal (110.000000 mm)** and
**ideal (110.037667410714… mm = 770.263671875/7, arithmetic)**
geometries are **distinct** and never interchanged.

## 1. Architecture

v4 adds `rscs2_core` beside the frozen v3 packages (`rgcs_core`,
`rscs_core` — tags v3.0.x, untouched). New mathematical objects are
registered in the append-only RSCS2 registry with id, units,
classification, provenance, exclusions, and tests (44+ objects at
release). gmsh runs as an external subprocess only (GPL isolation).

## 2. Validated CPU solver (RSCS2-E.1..E.3, S.1..S.4, B.1..B.5)

Second-order tetrahedral vector FEM (scikit-fem), generalized
eigensolve with shift-invert and a deterministic ARPACK start vector
(V4-D-003). Anchors: Euler–Bernoulli cantilever (<0.5% converged),
Timoshenko thick beam (+0.03%), static tip deflection, exact cube Lamé
mode (Demarest 1971; +0.03–0.05%, ν-independent), constrained-bar
P-wave ladder against the frozen Z-axis speed. Boundary machinery:
free/fixed/Robin/surface-mass with limit tests. Defect V4-D-001 (mass
form) is documented with its permanent guards.

## 3. Anisotropic quartz (Agent 04)

Full 3×3×3×3 stiffness from the frozen Voigt constants; Christoffel
speeds reproduce the frozen v3 axes to 1e-9; trigonal class-32
symmetry (120° Z invariance) and Bond-rotation frame invariance are
pinned by tests; orientation sweeps (V.6 conservative extension).

## 4. Canonical 110 mm crystal (Agent 05)

Hexagonal faceted body, SP-Q154 diameter ratios (40/154, 30/154),
face-slope angles 51.843°/60°, across-vertices diameters, frozen v2
cap-height/area helpers. Machine-exact analytic volume matched by the
mesh to 1e-9; deterministic gmsh meshes (SHA256-stable). Ideal and
nominal variants carry exact, distinct lengths.

## 5. Piezoelectricity (Agent 06)

Stress-charge saddle formulation, P2/P2, static condensation with
gauge; single-element energy patch (1e-9) pins tensor order and sign;
e=0 recovers elasticity exactly; short/open electrode conditions with
physical k_eff²; reversal antisymmetry.

## 6. Acceleration (Agent 07)

OpenCL Christoffel kernel with closed-form symmetric-3×3 eigenvalues.
Real hardware: Intel Iris Xe (fp32) 6.6 ms vs 346.6 ms fair CPU
closed-form baseline at 500k directions, parity 3.4e-05 (< 2e-4
registered); i5-1135G7 CPU-CL (fp64) parity 1.8e-14. Kernel status:
MULTI_DEVICE_REPRODUCED. CUDA: INTERFACE_TESTED only. Explicit
backends never fall back silently.

## 7. Projections (Agent 08)

Ghosh (1999) Sellmeier indices anchored to the frozen handbook values;
vector Snell pinned to the frozen scalar law; probe-path menu
(geometric centre / frozen node prior / eye-candidate slot, null);
photoelastic phase projection; Jones elements on the frozen RSCS-C.9
state; Biot–Savart coil pair (exact on-axis anchor; div B = 0);
modal drive projection (Mφ_k → e_k exactly); leakage-gated coupling
records. The octave wavelength presets (c/2⁴⁹, c/2⁴⁸) are arithmetic
statements only.

## 8. Eye diagnostics and consensus (Agent 09)

Sixteen registered diagnostics (all Derived; never Established) and a
sequential multi-criterion consensus: family-deduplicated agreement,
localization, validity, null comparison, mesh persistence (required
for any STABLE verdict — V4-D-004), boundary sensitivity, mode
dependence, uncertainty persistence. Adversarial battery: planted
candidate found; flat/noise/outside/collapse/artifact/boundary cases
all rejected correctly; NO_STABLE_CANDIDATE is a first-class outcome.

**Canonical result (corrected, V4C-D-001):**
UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE — one 3-family region at
(−0.295, −0.205, 102.240) mm near the male cap/shaft junction, an
exactly reported **3.906 mm** from the nearest ordinary node/antinode
station at (−0.447, 0.774, 106.018) mm. The separation is real and
preserved; at the current mesh-dominated localization uncertainty
(±3.08 mm per side) the intervals overlap, so the implemented
conventional model MAY explain the feature — deliberately weaker than
"explains". The candidate is unambiguously distinct from the
geometric centre (~47 mm) and the frozen RGCS node prior (~50.6 mm);
the junction plane (~0.4 mm away) remains a viable, untested
conventional explanation; mesh levels near clmax ≈ 4 mm would
discriminate. The v4.0.0 release used a proximity-threshold rule
(defect V4C-D-001, corrected in the v4.1.0 line; v4.0.0 records are
frozen history). `eye_coordinate` remains null everywhere.

## 9. Reference systems (Agent 10)

Cavity vs exact Helmholtz spectrum (1.7e-4, degeneracy resolved);
base-fixed tuning fork weak-coupling pair (S₀ = 8.70 Hz, CMR 0.26);
V.9: the frozen two-mode model tracks FEM avoided-crossing splitting
within 6.4% under Rayleigh tip-mass detuning. The free fork's
strong-coupling regime is documented as a diagnosed pitfall.

## 10. Reproducibility (Agents 11–12)

One deterministic command builds the 111-file proof bundle
(bit-identical data artifacts across builds; SHA256 manifest); the
`rgcs-v4` CLI exposes every capability; a 10-step scripted demo runs
from a clean workspace to exit 0 with runtime/memory/hash records.

## 11. QA (Agent 13)

Independent adversarial audit (19 programmatic checks), defect
register V4-D-001..004 (all closed, each with a regression test),
domain audits, and the G1–G30 gate table in
RELEASE_RECOMMENDATION.md.

## Limitations

See proof bundle `reports/LIMITATIONS.md`: STEP export untested
(declared); phase diagnostics require driven complex responses;
consensus covered 4 elastic modes × 2 mesh levels × 1 boundary
variant × 3 material draws; acceleration evidence is device-specific;
cross-platform bit-identity is not claimed (tolerance-level CI only).
