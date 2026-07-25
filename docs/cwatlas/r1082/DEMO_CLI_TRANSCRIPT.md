# R10.8.2 CLI demonstration transcript

Real output of the `cwatlas.r1082.cli` on the locked EARTH_ROOT_D_V1
profile. Every result is a CALIBRATED_CANDIDATE software result under a
declared, frozen calibration — never a measured fact, never a validated
source origin. Captured at v8.2.0.

## 1. Structural inspection of the Stonehenge training vector

```console
$ python -m cwatlas.r1082.cli inspect --vector 165876523
{
  "cli_id": "CW-R1082-CLI",
  "cli_version": "1.0.0",
  "codec_id": "CW_BASE100_ROUTE_V2",
  "command": "inspect",
  "evidence_class": "DERIVED_MATHEMATICS",
  "input": "165876523",
  "max_evidence": "CALIBRATED_CANDIDATE",
  "measured_here": "nothing",
  "note": "structural parse only: a source vector is not a decoded location; use `decode` to place a candidate.",
  "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
  "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
  "raw": "0165876523",
  "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
  "tokens": [
    1,
    65,
    87,
    65,
    23
  ],
  "valid": true,
  "wire": "01|65|87|65|23"
}
```

## 2. Decode under the full retained ensemble (uncalibrated) -> alias set

```console
$ python -m cwatlas.r1082.cli decode --vector 165876523 --shell 3
{
  "altitude_missing": false,
  "api_code": "OK_CANDIDATE_ALIAS_SET",
  "cli_id": "CW-R1082-CLI",
  "cli_version": "1.0.0",
  "command": "decode",
  "evidence_class": "CALIBRATED_CANDIDATE",
  "geometry": [
    {
      "cell_face_id": 3,
      "family_name": "F1_CANONICAL_DIRECT_BE",
      "ground_sigma_m": 284.6910465228163,
      "latitude_deg": -28.336353745564704,
      "longitude_deg": 167.25996982924335,
      "radius_m": 6371000.0,
      "route": [
        1,
        65,
        87,
        65,
        23
      ],
      "shell": 3
    },
    {
      "cell_face_id": 1,
      "family_name": "F2_REVERSED_DIRECT_BE",
      "ground_sigma_m": 2267.9561326943235,
      "latitude_deg": -14.886800908710619,
      "longitude_deg": 176.58133117150578,
      "radius_m": 6371000.0,
      "route": [
        1,
        65,
        87,
        65,
        23
      ],
      "shell": 3
    },
    {
      "cell_face_id": 5,
      "family_name": "F4_ROTATED_DIRECT_LE",
      "ground_sigma_m": 500.0526474324689,
      "latitude_deg": 46.53076329492542,
      "longitude_deg": -125.7470939657487,
      "radius_m": 6371000.0,
      "route": [
        1,
        65,
        87,
        65,
        23
      ],
      "shell": 3
    }
  ],
  "input": {
    "body": "EARTH",
    "epoch_year": 2020.0,
```

## 3. Root certificate at epoch 2020, shell 3 (surface)

```console
$ python -m cwatlas.r1082.cli root --epoch 2020 --shell 3
{
  "altitude_missing": false,
  "certificate": {
    "axis": "MEAN_ROTATION_AXIS_SOUTH_UP",
    "certificate_hash": "sha256:926fa9d4392acc8c537c791a9747ef1e3f680b9ddcb72bc64f5de5db80c1fa94",
    "dual_graph": "DODECAHEDRAL_20_VERTEX_DUAL",
    "dynamic_zero": {
      "epoch": {
        "bucket": 2020.0,
        "year": 2020.0
      },
      "field_model": "CW-SAA-PARAMETRIC",
      "field_model_version": "1.0.0",
      "minimum_deg": [
        -25.4,
        -49.19999999999999
      ],
      "shell": {
        "index": 3,
        "radius_m": 6371000.0
      },
      "type": "SAA_FIELD_MAGNITUDE_MINIMUM"
    },
    "fixed_anchor": {
      "candidate_id": "WILKES_A_PLACEHOLDER",
      "centroid_deg": [
        -66.5,
        135.0
      ],
      "profile_version": "WILKES_CENTROID_ENSEMBLE_V1",
      "selection_basis": "OPERATOR_SELECTION",
      "type": "WILKES_GRAVITY_ANOMALY_CENTROID",
      "uncertainty": {
        "area_deg2": 18.84955592153876,
        "collapsed_to_point": false,
        "cov_deg2": [
          [
            4.0,
            0.0
          ],
          [
            0.0,
            9.0
          ]
        ],
```

## 4. Evidence receipt / claim seals

```console
$ python -m cwatlas.r1082.cli receipt
{
  "claim_taxonomy": {
    "evidence_classes": [
      "SOURCE",
      "OPERATOR_SELECTION",
      "DERIVED_MATHEMATICS",
      "SOFTWARE_RESULT",
      "CALIBRATED_CANDIDATE",
      "MEASURED",
      "REPLICATED"
    ],
    "forbidden_promotions": [
      "candidate_as_measured",
      "source_origin_validated",
      "nonhuman_origin",
      "physical_effect",
      "post_output_retuning",
      "altitude_missing_when_shell_present",
      "source_as_geographic"
    ],
    "frozen_parameters": [
      "grid_rotation",
      "handedness",
      "root_feature",
      "topology",
      "tokenization",
      "destination_label_split",
      "epoch_choice"
    ],
    "max_candidate_evidence": "CALIBRATED_CANDIDATE",
    "measured_here": "nothing",
    "measurement_evidence": [
      "REPLICATED",
      "MEASURED"
    ],
    "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
    "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
    "result_classes": [
      "CANONICAL_EXACT_POINT",
      "CANDIDATE_CALIBRATED_POINT",
      "CANDIDATE_REGION",
      "CANDIDATE_ALIAS_SET",
      "CALIBRATION_REQUIRED",
      "UNDERDETERMINED",
      "INVALID"
```

## Reading these results honestly

The decode of `165876523` returns a **CANDIDATE_ALIAS_SET**, not a single
pin. Under the frozen two-anchor calibration the best-fitting family places
the Stonehenge *training* vector ~649 km from Stonehenge (its sealed 5.69-deg
angular residual); the other families are 7,000-9,000 km away. A single
fitted azimuth cannot align two arbitrary anchor directions, so the atlas
renders the bounded alias set with per-family uncertainty rather than a
false pin. This is the designed, honest behaviour:
SOURCE_ORIGIN_NOT_VALIDATED, PHYSICAL_EFFECTS_NOT_CLAIMED.
