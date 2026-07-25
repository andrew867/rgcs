# RGCS v8.2.0 - R10.8.2 Locked Two-Layer Earth Root and Source-Map Calibration

**Release date:** 2026-07-25
**Predecessor:** v8.1.0 (R10.8.1 CW Atlas)
**Final verdict:** RGCS_R10_8_2_GREEN_LOCKED_SOURCE_MAP_READY / EARTH_ROOT_D_V1_LOCKED / WILKES_FIXED_ROOT_RESOLVED / SAA_DYNAMIC_ZERO_RESOLVED_FROM_SHELL_AND_EPOCH / STONEHENGE_TRAINING_ANCHOR_APPLIED / SOURCE_VECTOR_CANDIDATE_PINS_RENDERED / MAP_TO_SOURCE_STYLE_VECTOR_IMPLEMENTED / ROUND_TRIP_PROFILE_VERIFIED / NO_POST_OUTPUT_RETUNING / SOURCE_ORIGIN_NOT_VALIDATED

## What this release is

R10.8.2 adds the `cwatlas.r1082` subpackage on top of the R10.8.1 CW Atlas
engine. Where R10.8.1 shipped a general geocoder that returned an alias set or
a refusal for source vectors, R10.8.2 **locks** the operator-selected
`EARTH_ROOT_D_V1` configuration and produces **candidate pins, cells, regions,
or a bounded alias set with uncertainty** — the application always produces a
map result, never a bare generic refusal, and never invents precision it does
not have.

31 modules, 32 phase receipts (P01–P32, 8 tranches T01–T08), 30 test files,
408 subpackage tests inside a 7800-test repository suite.

## The locked two-layer Earth root (EARTH_ROOT_D_V1)

* **Fixed spatial anchor** — the Wilkes Land gravity-anomaly centroid, carried
  as a versioned centroid + 2×2 covariance profile. Uncertainty is never
  collapsed; a zero / non-positive-definite covariance is refused.
* **Dynamic phase-zero direction** — the South Atlantic Anomaly magnetic
  minimum, resolved at the packet's encoded **epoch** and the body-relative
  **shell radius**. The shell profile supplies the radius, so altitude is never
  reported as missing when a shell is present.
* **South-Up + viewpoint-safe handedness** — "clockwise from above Antarctica"
  and "anticlockwise from North, viewed from below" produce the identical
  rotation matrix; a rotation without a declared viewpoint is refused.
* Icosahedral **face-centre** root, **dodecahedral-dual** adjacency,
  **five-token base-100** route core, **seven** semantic fields, **barycentric**
  local coordinate, **packed shell + epoch** wire format, variable depth.
* Epoch lanes (Cs-133 fine phase, Cs-137 decay envelope, Ba-137 daughter
  ratio, Ba-130 parent) are kept **typed and separate**; UTC/TAI/TT/TDB are
  mandatory in the certificate. No lane can be marked proven.

## Calibration discipline

* Candidate maps are fit **only** against the two sealed training anchors: the
  Wilkes fixed root and the user-reported `165876523 = Stonehenge` training
  anchor (referenced by opaque id against a synthetic public coordinate with
  non-zero positional uncertainty).
* The retained ensemble is **frozen** with a SHA-256 receipt sealing the seven
  frozen parameters (grid rotation, handedness, root feature, topology,
  tokenization, destination-label split, epoch choice) **before** any holdout
  is scored.
* **No result shopping.** After the freeze, any change to a frozen parameter —
  or moving a label between training and holdout — mints a new profile id and
  is refused (`no_retune` detects the specific changed parameter).
* Two anchors **under-determine** the four candidate mapping families (and
  families F1≡F3 are permanently indistinguishable), so the app renders the
  complete **bounded alias set** and a per-cell **agreement/disagreement
  surface** rather than silently picking one mapping.

## Bidirectional source geocoder

* **Source vector → pin / cell / region / alias set**, each with an uncertainty
  footprint from the terminal-cell quantization. Body-scope firewall: vectors
  reported for other planets or stars are typed out of scope, not force-decoded
  onto Earth.
* **Map click → source-style five-token vector** under a named frozen profile,
  returning the nearest-encodable address.
* **Round trip** separates the exact canonical codec round trip from the
  source-style calibrated round trip; near cell edges/vertices it returns an
  interval/region. The five-token codec (10¹⁰ states) cannot address a family's
  full depth-10 space (20·8¹⁰), so the inverse reports a true (large) residual
  instead of a false-exact point.
* A **search-space / description-length ledger** counts the real freedom used
  (4 families / 3 distinguishable, 1 continuous orientation angle, centroid ×
  epoch × codec alternatives) and surfaces DOF ≥ sealed-anchors as a
  weak-constraint finding.
* A **prospective bidirectional challenge** that can fail cleanly after the
  release is frozen (the synthetic held-back suite produces both SUCCESS and
  FAILURE outcomes).

## Application

A pure-stdlib CLI exposes `root`, `calibration`, `encode`, `decode`,
`inspect`, `batch`, and `receipt`, each printing deterministic sealed JSON. An
output firewall refuses to emit any result carrying MEASURED/REPLICATED
evidence or a source-origin-validated token. The dynamic globe / shell /
magnetic overlay and the Atlas operator UI are delivered as a **code-backed
view-model** (`ui_state.build_view_model`, `overlay_spec.build_overlay_state`)
plus a written spec over the tested backend; the browser front-end is not
executed in this environment.

## What this release does NOT claim

* A candidate pin is a `CALIBRATED_CANDIDATE` **software result** under a
  declared, frozen calibration. **It is not a measured fact** and cannot be
  promoted to MEASURED/REPLICATED.
* The source attribution is **user-reported and unverified**. Producing a
  calibrated candidate map does **not** validate the source's origin
  (`SOURCE_ORIGIN_NOT_VALIDATED`), and no nonhuman/extraterrestrial origin is
  claimed or established.
* The atlas maps and calibrates coordinates; it asserts **no physical effect**
  (`PHYSICAL_EFFECTS_NOT_CLAIMED`) and no physical validation
  (`PHYSICAL_VALIDATION_NOT_CLAIMED`).

Additive; no prior work reset, no public history rewritten. See
`docs/cwatlas/r1082/MASTER_RESEARCH_ARCHIVE.md`,
`docs/cwatlas/r1082/ATLAS_UI_SPEC.md`, and `docs/cwatlas/r1082/receipts/`.

# expect: 7803 passed (1 archived-environment byte test deselected by policy D-V3-04)
