# V4 Risk Register

**Status:** PLANNING. P=probability, I=impact (both L/M/H). Mirrored into
top-level `docs/RISK_REGISTER.md`.

| id | Risk | P | I | Mitigation | Owner |
|---|---|---|---|---|---|
| RV4-01 | scikit-fem cannot meet CPU-authority accuracy/scale | M | H | P3 PoC gate before committing; PETSc/SLEPc optional fallback; dense cross-check on small cases | Tranche A/C |
| RV4-02 | Gmsh GPL contaminates MIT licence | M | H | **DV4-006**: Gmsh only as subprocess/file interchange; meshio (MIT) bridge; licence audit P3 | Tranche B |
| RV4-03 | No GPU hardware → acceleration unverifiable | H | M | **DV4-007** four-status ladder; ship experimental; INTERFACE via CPU-mock; PARITY needs contributor runner; CPU stays authority | Tranche E |
| RV4-04 | Eye diagnostics over-interpreted as physical structure | M | H | **DV4-010**: SRC/DER/HYP only, never EST; robustness battery; NULL verdict; taxonomy labels; exclusion lint | Tranche F |
| RV4-05 | Public datasets have unclear/unusable licences | M | M | licence-presence lint; fetch-script+checksum instead of embedding; synthetic-first | Tranche G |
| RV4-06 | Piezoelectric constitutive tensors mis-signed / wrong convention | M | H | V.7 single-element round-trip vs IEEE-176; independent dense cross-check | Tranche D |
| RV4-07 | Mesh non-determinism across Gmsh versions | M | M | manifest records Gmsh version; tolerance-aware coordinate comparison (D-V3-04 law), element-count exactness | Tranche B |
| RV4-08 | Conservative-extension anchor (V.6/V.9) fails → v4 diverges from v3 | L | H | anchors are hard gates at M4/M8; failure halts the tranche, not "adjust the tolerance" | Tranche D |
| RV4-09 | Dependency bloat makes CPU install hard | M | M | **DV4-005** smallest stack; heavy deps optional behind capability detection; CPU-only install = numpy+scipy+scikit-fem+meshio | Tranche A |
| RV4-10 | float32/GPU silently corrupts a headline number | L | H | f64 authority; f32 opt-in with recorded error bound into UncertainValue; no silent GPU path | Tranche E |
| RV4-11 | Scope explosion (5 fidelity levels × many systems) | H | M | staged levels; M3 MVP; partial-release per tranche; no level gates the ones below it | all |
| RV4-12 | Visualization emits mathtext/vortex-as-physics artifacts | M | M | D-V3-05 mathtext lint; caption classification chips; "field feature" labels; visual-regression tests | Tranche H |
| RV4-13 | Inverse fitting overfits / leaks | M | H | held-out split + leakage test; null-model comparison mandatory; posterior not point | Tranche G |
| RV4-14 | Frozen v3/v2 accidentally modified | L | H | frozen-path diff gate in CI (existing); anchors reference frozen modules read-only | all |
| RV4-15 | Safety content creep (high-power laser/EM) | L | H | D6/D7 envelope lint on all run descriptions; optical ≤3R, coil ≤ envelope, no human exposure | Tranche F |
