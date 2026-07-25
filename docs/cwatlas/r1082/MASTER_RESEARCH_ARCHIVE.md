# Master Research Archive — RGCS R10.8.2 (`EARTH_ROOT_D_V1`)

**Locked Two-Layer Earth Root and Source-Map Calibration**
**Phase:** P31 (tranche T08, Application and Release)
**Profile:** `EARTH_ROOT_D_V1` (immutable, hashed; see the Locked Decision ADR)
**Authority in code:** `cwatlas/r1082/config_authority.py`,
`cwatlas/r1082/claims.py`

This archive makes **every locked decision and every phase output traceable** to
its module, tests, receipt, and (where applicable) the decision/communications
record. It is the traceability document the P32 release notes reference.

> **Governance posture (whole programme):**
> ```
> measured_here            = nothing
> PHYSICAL_VALIDATION_NOT_CLAIMED
> PHYSICAL_EFFECTS_NOT_CLAIMED
> SOURCE_ORIGIN_NOT_VALIDATED
> ```
> A candidate pin is a `SOFTWARE_RESULT` under a declared, frozen calibration
> (`CALIBRATED_CANDIDATE` at most). It is not a measured fact; the source
> attribution is user-reported and unverified; no nonhuman origin and no
> physical effect is claimed.

---

## 1. The locked profile: 15 operator selections + 7 frozen parameters

### 1.1 The fifteen `EARTH_ROOT_D_V1` locked decisions

Encoded as an ADR-in-code in `config_authority.LOCKED_DECISIONS` and validated
against the public fixture `cwatlas/r1082/fixtures/earth_root_D_v1.json`. Every
decision is `OPERATOR_SELECTION` evidence — an operator-selected input, not a
measured fact. Changing any one changes `ConfigurationAuthority.freeze_hash()`
and therefore **mints a new profile id**.

| # | Key | Locked value | Decision-record source |
|---|-----|--------------|------------------------|
| 1 | `origin` | `EARTH_CENTER_OF_MASS` | Locked Decision ADR / comms: root frame |
| 2 | `axis` | `MEAN_ROTATION_AXIS_SOUTH_UP` | comms: orientation |
| 3 | `partition` | `SPHERICAL_ICOSAHEDRON_20_FACES` | comms: topology |
| 4 | `dual_graph` | `DODECAHEDRAL_20_VERTEX_DUAL` | comms: adjacency graph |
| 5 | `root_feature` | `ICOSAHEDRAL_FACE_CENTER` | comms: root feature |
| 6 | `fixed_anchor` | `WILKES_GRAVITY_ANOMALY_CENTROID` | comms: fixed spatial anchor |
| 7 | `dynamic_zero` | `SAA_FIELD_MAGNITUDE_MINIMUM` | comms: dynamic phase-zero |
| 8 | `orientation_pole` | `SOUTH_UP` | comms: orientation |
| 9 | `positive_rotation` | `CLOCKWISE_FROM_ABOVE_ANTARCTICA` | comms: handedness |
| 10 | `opposite_view` | `ANTICLOCKWISE_FROM_NORTH_DOWN` | comms: handedness (inverse view) |
| 11 | `second_anchor` | `STONEHENGE_PRIVATE_001` (opaque id) | comms: Stonehenge training anchor |
| 12 | `local_coordinate` | `BARYCENTRIC` | comms: local coordinate |
| 13 | `route_core` | `FIVE_TOKEN_BASE_100` | comms: codec (`01\|65\|87\|65\|23`) |
| 14 | `semantic_address` | `SEVEN_LOGICAL_FIELDS_PACKED_SHELL_EPOCH` | comms: semantic address |
| 15 | `variable_depth` | `VARIABLE_DEPTH_EXPANDING_CERTIFICATE` | comms: variable depth |

Full rationale: `docs/cwatlas/r1082/LOCKED_DECISION_ADR.md`.

### 1.2 The seven frozen parameters

Sealed at the calibration freeze (`claims.FROZEN_PARAMETERS`,
`calibration_freeze.py`). After the freeze, changing any of these is
result-shopping and is refused (`claims.refuse_post_output_retuning`); a new
value is only expressible as a new profile id.

| # | Frozen parameter | Bound to locked decision(s) |
|---|------------------|------------------------------|
| 1 | `grid_rotation` | 8 `orientation_pole` (SOUTH_UP) |
| 2 | `handedness` | 9/10 `positive_rotation` (CLOCKWISE) |
| 3 | `root_feature` | 5 `root_feature` |
| 4 | `topology` | 3 `partition` |
| 5 | `tokenization` | 13 `route_core` |
| 6 | `destination_label_split` | 14 `semantic_address` |
| 7 | `epoch_choice` | 7 `dynamic_zero` epoch |

The two sealed **training anchors** — the Wilkes fixed root (decision 6) and the
Stonehenge training anchor (decision 11) — calibrate the map. Landing near any
other well-known place is coincidence, never rewarded
(`candidate_ensemble.refuse_famous_place_reward`).

---

## 2. Acceptance matrix — phase → verdict → evidence

Every phase P01–P32 maps to its module, tests, and receipt. Tranches T01–T06
(P01–P24) and T07 (P25–P28) are green; T08 (P29–P31) is this tranche; P32 is the
release bundle (authored by the release lead).

| Phase | Tranche | Title | Module | Tests | Receipt | Verdict |
|-------|---------|-------|--------|-------|---------|---------|
| P01 | T01 | Gate Zero and Repository Reconciliation | `__init__.py`, `claims.py` | `test_claims.py` (13) | `receipts/P01.json` | GATE_ZERO_VERIFIED |
| P02 | T01 | Locked Decision ADR / Config Authority | `config_authority.py` | `test_config_authority.py` (8) | `receipts/P02.json` | LOCKED_DECISION_ADR_HASHED_AND_IMMUTABLE |
| P03 | T01 | Private Provenance / Source Registry Import | `source_import.py` | `test_source_import.py` (7) | `receipts/P03.json` | PROVENANCE_IMPORTED_NO_NARRATIVE_EXPOSED |
| P04 | T01 | Claim State / Candidate Map Result Migration | `result_states.py` | `test_result_states.py` (12) | `receipts/P04.json` | CANDIDATE_RESULT_STATES_WITH_EVIDENCE_FIREWALL |
| P05 | T02 | Wilkes Fixed Anchor Profile Registry | `wilkes.py` | `test_wilkes.py` (16) | `receipts/P05.json` | WILKES_FIXED_ANCHOR_NO_INVENTED_PRECISION |
| P06 | T02 | Shell-Resolved SAA Magnetic Minimum | `saa.py` | `test_saa.py` (14) | `receipts/P06.json` | SAA_SHELL_RESOLVED_EPOCH_AND_RADIUS_DEPENDENT |
| P07 | T02 | South-Up Basis / Viewpoint-Safe Handedness | `southup.py` | `test_southup.py` (13) | `receipts/P07.json` | SOUTH_UP_VIEWPOINT_SAFE_NO_AMBIGUOUS_SIGN |
| P08 | T02 | Root Certificate / Time-Varying Frame API | `root_certificate.py` | `test_root_certificate.py` (15) | `receipts/P08.json` | ROOT_CERTIFICATE_TWO_LAYER_CACHEABLE_AUDITED |
| P09 | T03 | Five-Token Base-100 Parser / Prefix Tree | `route_core.py` | `test_route_core.py` (24) | `receipts/P09.json` | FIVE_TOKEN_BASE_100_PARSER_AND_PREFIX_TREE |
| P10 | T03 | Seven-Field Semantic Expansion | `semantic_expand.py` | `test_semantic_expand.py` (16) | `receipts/P10.json` | SEVEN_FIELD_SEMANTIC_EXPANSION |
| P11 | T03 | Packed Shell-Epoch / Variable-Depth Wire | `wire_format.py` | `test_wire_format.py` (18) | `receipts/P11.json` | PACKED_SHELL_EPOCH_VARIABLE_DEPTH_WIRE |
| P12 | T03 | Cs-Ba Epoch Profile Registry | `epoch_profiles.py` | `test_epoch_profiles.py` (19) | `receipts/P12.json` | CS_BA_EPOCH_PROFILE_REGISTRY |
| P13 | T04 | Icosahedral 20-Face Partition Authority | `partition.py` | `test_partition.py` (7) | `receipts/P13.json` | ICOSA20_PARTITION_AUTHORITY_VERSIONED_HASHED |
| P14 | T04 | Dodecahedral-Dual Route Graph | `route_graph.py` | `test_route_graph.py` (8) | `receipts/P14.json` | DODECA_DUAL_ROUTE_GRAPH_NO_CONFLATION |
| P15 | T04 | Recursive Eight-Way Spatialization Families | `spatialization.py` | `test_spatialization.py` (8) | `receipts/P15.json` | SPATIALIZATION_FAMILIES_BOUNDED_INVERTIBLE |
| P16 | T04 | Barycentric Local Coordinate / Inverse | `local_coord.py` | `test_local_coord.py` (7) | `receipts/P16.json` | BARYCENTRIC_LOCAL_COORD_NEAREST_ENCODABLE |
| P17 | T05 | Stonehenge Training Anchor Authority | `stonehenge_anchor.py` | `test_stonehenge_anchor.py` (10) | `receipts/P17.json` | STONEHENGE_ANCHOR_OPAQUE_ID_NEVER_MEASURED |
| P18 | T05 | Two-Anchor Orientation / Token Calibration | `calibration_fit.py` | `test_calibration_fit.py` (10) | `receipts/P18.json` | TWO_ANCHOR_FIT_RANKED_SET_NO_SILENT_PICK |
| P19 | T05 | Calibration Freeze / Cryptographic Receipt | `calibration_freeze.py` | `test_calibration_freeze.py` (10) | `receipts/P19.json` | CALIBRATION_FROZEN_SHA256_NO_RESULT_SHOPPING |
| P20 | T05 | Candidate Map Ensemble / Agreement Surface | `candidate_ensemble.py` | `test_candidate_ensemble.py` (11) | `receipts/P20.json` | CANDIDATE_MAP_ENSEMBLE_ALIAS_SET_SURFACE |
| P21 | T06 | Source Vector to Pin, Cell, or Region | `geocode_forward.py` | `test_geocode_forward.py` (33) | `receipts/P21.json` | FORWARD_GEOCODER_PIN_CELL_REGION_NEVER_BARE |
| P22 | T06 | Map Selection to Source-Style Vector | `geocode_inverse.py` | `test_geocode_inverse.py` (21) | `receipts/P22.json` | INVERSE_GEOCODER_SOURCE_STYLE_NEAREST_ENCODABLE |
| P23 | T06 | Profile Round Trip / Nearest Encodable Point | `round_trip.py` | `test_round_trip.py` (17) | `receipts/P23.json` | ROUND_TRIP_NEAREST_ENCODABLE_NO_FALSE_EXACTNESS |
| P24 | T06 | Dynamic Globe / Shell / Magnetic Overlay | `overlay_spec.py` | `test_overlay_spec.py` (11) | `receipts/P24.json` | OVERLAY_CONTRACT_TWO_LAYER_ROOT_VISIBLE |
| P25 | T07 | Holdout Vector Registry / Body-Scope Firewall | `holdout_registry.py` | `test_holdout_registry.py` | `receipts/P25.json`† | HOLDOUT_REGISTRY_DISJOINT_SEALED_BODY_SCOPE |
| P26 | T07 | No-Retune Enforcement | `no_retune.py` | `test_no_retune.py` | `receipts/P26.json`† | NO_RETUNE_ENFORCED_FROZEN_CHANGES_REFUSED |
| P27 | T07 | Search-Space / Description-Length Ledger | `search_ledger.py` | `test_search_ledger.py` | `receipts/P27.json`† | SEARCH_LEDGER_FREEDOM_COUNTED_DOF_SURFACED |
| P28 | T07 | Prospective Bidirectional Challenge | `prospective_challenge.py` | `test_prospective_challenge.py` | `receipts/P28.json`† | PROSPECTIVE_CHALLENGE_FALSIFIABLE_SEALED |
| **P29** | **T08** | **Backend API and CLI Integration** | **`cli.py`** | **`test_cli.py` (24)** | **`receipts/P29.json`** | **CLI_APPLICATION_BOUNDARY_CANDIDATE_NEVER_MEASURED** |
| **P30** | **T08** | **Atlas UI and Operator Workflow** | **`ui_state.py`** + `ATLAS_UI_SPEC.md` | **`test_ui_state.py` (12)** | **`receipts/P30.json`** | **UI_VIEW_MODEL_CODE_BACKED_NO_HIDDEN_DEFAULTS** |
| **P31** | **T08** | **Master Research Archive / Comms Crosswalk** | this document | (documentation phase) | **`receipts/P31.json`** | **MASTER_ARCHIVE_TRACEABLE_TO_COMMS_RECORD** |
| P32 | T08 | R10.8.2 Release and Demonstration Bundle | (release bundle) | (release gate) | `receipts/P32.json`‡ | (authored by the release lead) |

† T07 modules (`holdout_registry`, `no_retune`, `search_ledger`,
`prospective_challenge`) are present and importable; their phase receipts are
authored by the T07 tranche. The CLI imports them **lazily** and degrades
gracefully if absent.
‡ P32 (release/version ritual) is out of scope for this tranche and authored by
the release lead — no version bump, tag, or commit is performed here.

---

## 3. Communications / decision crosswalk

The locked decisions originate in the operator's communications chronicle. This
crosswalk cross-references the entries that supplied each decision axis to the
module that encodes it and the receipt that seals it.

| Decision axis | Comms-supplied decision | Encoding module | Sealed in |
|---------------|-------------------------|-----------------|-----------|
| Root / origin / axis | decisions 1, 2 | `config_authority.py` | `receipts/P02.json` |
| Topology (partition + dual) | decisions 3, 4, 5 | `partition.py`, `route_graph.py` | `receipts/P13.json`, `P14.json` |
| Fixed spatial anchor (Wilkes) | decision 6 | `wilkes.py` | `receipts/P05.json` |
| Dynamic phase-zero (SAA), shell | decision 7 | `saa.py`, `semantic_expand.py` | `receipts/P06.json`, `P10.json` |
| Orientation / handedness | decisions 8, 9, 10 | `southup.py` | `receipts/P07.json` |
| Stonehenge training anchor | decision 11 | `stonehenge_anchor.py` | `receipts/P17.json` |
| Codec (five-token) / local coord | decisions 12, 13 | `route_core.py`, `local_coord.py` | `receipts/P09.json`, `P16.json` |
| Semantic address / variable depth | decisions 14, 15 | `wire_format.py`, `semantic_expand.py` | `receipts/P11.json`, `P10.json` |

**Provenance discipline.** The user-reported source correspondences are imported
under a privacy firewall (`source_import.py`, P03) and bound to a hash-chained
provenance ledger. Public artifacts reference the Stonehenge anchor by the opaque
id `STONEHENGE_PRIVATE_001` only — never the raw private vector or narrative.

---

## 4. Corrections and failed codecs preserved

Per the phase requirement to preserve corrections and failed approaches:

- **Legacy bare refusal → richer result classes.** R10.8.1 stopped a
  source-vector map at a single `NO_UNIQUE_GEOGRAPHIC_DECODE`. R10.8.2 migrates
  this to the seven bounded result classes
  (`result_states.migrate_no_unique_decode`, P04) — pin / cell / region / alias
  set with declared uncertainty, never invented precision.
- **Unaddressable terminal cells preserved as honest residuals.** The five-token
  codec addresses `100**5 = 10**10` states, smaller than a family's depth-10
  address space, so more than half of each face's cells are unaddressable. Rather
  than fake exactness, `geocode_forward.safe_family_inverse` clamps to the
  nearest encodable point and reports the true (larger) residual with
  `in_route_space = false` (P21).
- **Ambiguity preserved, not collapsed.** Where the two anchors cannot select
  one mapping, the complete bounded `CANDIDATE_ALIAS_SET` and the agreement
  surface are returned (`candidate_ensemble.py`, P20) — uncertainty is never
  zero-collapsed.
- **Foreign bodies typed out of scope, not force-decoded.** A non-Earth/Terra
  vector is typed `INVALID` / out of scope; no pin is invented (P21).

---

## 5. Posture and refusals (the evidence firewall)

The programme's refusals are indexed in `claims.FORBIDDEN_PROMOTIONS`:

| Refusal | Enforces |
|---------|----------|
| `candidate_as_measured` | a candidate is never a `MEASURED`/`REPLICATED` fact |
| `source_origin_validated` | the source attribution is user-reported, unverified |
| `nonhuman_origin` | no nonhuman/extraterrestrial origin is claimed |
| `physical_effect` | the atlas maps coordinates; it acts on nothing |
| `post_output_retuning` | no result shopping after the freeze |
| `altitude_missing_when_shell_present` | the shell supplies the radius |
| `source_as_geographic` | a source vector is not a decoded location |

Every module exposes a `<name>_report()` carrying `measured_here = "nothing"`,
the three seals, and a `verdict`. The CLI (P29) additionally enforces an
**output firewall** (`cli._guard_no_measured_leak`): it refuses to emit any
payload whose `evidence_class` is `MEASURED`/`REPLICATED` or that contains a
`SOURCE_ORIGIN_VALIDATED` token.

`SOURCE_ORIGIN_NOT_VALIDATED` · `PHYSICAL_VALIDATION_NOT_CLAIMED` ·
`PHYSICAL_EFFECTS_NOT_CLAIMED`

---

## 6. Reproduction and manifest

- **Focused + regression tests:**
  `.venv/Scripts/python.exe -m pytest tests/cwatlas/r1082/ -q --import-mode=importlib`
  (all green).
- **CLI boundary:** `python -m cwatlas.r1082.cli --help`; each subcommand
  (`root`, `calibration`, `encode`, `decode`, `inspect`, `batch`, `receipt`)
  prints deterministic JSON and returns a process exit code.
- **Deterministic freeze:** a clean checkout reproduces
  `ConfigurationAuthority.freeze_hash()` and the calibration `freeze_hash` (no
  wall-clock reads anywhere in the package).
- **SHA-256 manifest:** the up-to-date artifact manifest is generated by the P32
  release bundle (out of scope for this tranche).

---

## 7. Empirical result at v8.2.0 (the headline null)

The experiment ran end to end on the locked profile. The empirical finding is a
**null result** on the question the source-map hypothesis poses — and it is
reported here plainly rather than buried:

- Fitting the four candidate families against the two sealed anchors (Wilkes
  fixed root + the `165876523 = Stonehenge` training anchor) yields a **best**
  Stonehenge angular residual of **5.69°** (family `F4_ROTATED_DIRECT_LE`);
  the other retained families are 66.6° and 80.3° off. The Wilkes residual is
  ≥ 36° for every family.
- With the fitted per-family orientation **applied** (see below), decoding the
  Stonehenge *training* vector places the best family **648.8 km** from
  Stonehenge (consistent with 5.69° × 111 km); the other families are 7,431 km
  and 8,948 km away.
- This is **structural, not a defect**: the calibration has one free parameter
  (a single azimuth per family) trying to satisfy two anchor directions
  (4 scalar constraints). One angle cannot align two arbitrary
  (code-cell → location) pairs. Adding parameters until the training anchor is
  hit would be overfitting two points and is refused (`refuse_famous_place_reward`;
  a test fails any placement within 100 km of the training anchor).
- The application therefore renders a **`CANDIDATE_ALIAS_SET`** with per-family
  uncertainty and an agreement/disagreement surface — a pin or region always,
  never a bare refusal, and never invented precision. **The two sealed anchors
  do not select a mapping that places the source vectors at their claimed Earth
  locations.**

**Release-time correctness fix (v8.2.0):** the fitted per-family orientation was
computed and sealed but not applied by the forward geocoder (identity
fallback), making the calibration cosmetic. `geocode_forward` now applies each
retained family's sealed azimuth and `calibration_freeze.FrozenCalibration`
exposes `orientation_matrix_by_family()`; locked in by
`tests/cwatlas/r1082/test_orientation_wiring.py`. This changed placements (the
best family rotated from off-Oregon toward the Bay of Biscay) but **not** the
null conclusion above.

## 8. What this archive does **not** say

This archive records a software calibration experiment and its provenance. The
locked decisions are operator-selected inputs; encoding and hashing them
validates neither the source's origin nor any physical effect. Every candidate
map is a `CALIBRATED_CANDIDATE` under a declared, frozen calibration — a software
result, not a measured fact. `SOURCE_ORIGIN_NOT_VALIDATED`. Reproducing a
training anchor to within its fit residual is not evidence the mapping is
correct; only the prospective bidirectional challenge (P28), scored on anchors
withheld from the fit, could provide that, and it is designed to be able to
fail.
