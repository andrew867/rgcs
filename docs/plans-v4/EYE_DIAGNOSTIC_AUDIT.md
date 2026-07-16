# Eye Diagnostic Audit (Agent 13 Role B)

Scope: false-positive resistance, null behavior, uncertainty (G18–G23).

## False-positive attacks (all held)

- **Planted synthetic candidate** recovered as a REGION (< 3 mm) — the
  engine finds real signals (G18).
- **Flat/body-spanning fields**: rejected by the localization gate
  ("not localized"); **independent random hotspots**: rejected by
  family agreement → NO_STABLE_CANDIDATE both ways (G19).
- **Correlated-diagnostic double counting**: D1/D3/D7 (kinematic) and
  D2/D4 (elastic-energy) count ONCE via family deduplication — an
  attacker cannot reach min_agree with one physical field.
- **Mesh artifact**: blob absent from the refined solve →
  MESH_ARTIFACT_REJECTED (G21).
- **Boundary-created candidate**: shifts across BC variants →
  BOUNDARY_SENSITIVE_CANDIDATE.
- **Outside-body candidate**: rejected as invalid.
- **Uncertainty collapse**: 1/4 recurrence < 0.6 threshold → dropped
  with recorded reason (G22).
- **Conventional feature**: blob on a node/antinode station →
  CONVENTIONAL_NODE_EXPLAINS_RESULT, never promoted (G23).
- **Symmetric body (real FEM cube)**: no STABLE verdict possible from
  single-mode fields.

## Null behavior (G19/G20)

NO_STABLE_CANDIDATE is a first-class, tested status; the proof bundle
additionally runs a scrambled-field control every build
(`eye/no_candidate_control.json`) and requires it to return
NO_STABLE_CANDIDATE — it does.

## Refusal honesty

D5/D9/D10/D12 REFUSE to run without their solved inputs (tested); the
canonical run's phase-diagnostic gap is a written status record, not a
silent omission.

## Canonical verdict integrity (G23)

`eye/centre_comparison.csv` + `conventional_node_comparison.csv`
explicitly compare candidate centroids against the geometric centre,
shaft midpoint, frozen RGCS node prior, and ordinary node/antinode
stations. The one 3-family region sits 3.94 mm from an ordinary modal
station and ~46–47 mm from centre/prior → explained conventionally.
`eye_coordinate` is null in every record.

No defects found. The engine's failure modes are the documented ones
(all-variant artifacts pass D13; declared in the spec).
