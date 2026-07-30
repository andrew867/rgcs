# RGCS Coordinate Workbench — Quick start

## Decode a packet (CLI)

```bash
rgcs-coordinate decode 165876523
```

```text
[STRUCTURAL CODEC: GREEN] [PHYSICAL PROJECTION: YELLOW UNDERDETERMINED] [STONEHENGE: TRAINING EQUALITY]
Decimal        165876523
Fixture        Stonehenge training equality (supplied training equality)
Binary 30      001001111000110001001100101011
Octal 10       1170611453
Face           4 (00100, valid-source-face-range)
Q22 bits       1111000110001001100101
Q22 path       3 3 0 1 2 0 2 1 2 1 1
Extracted S3   3 (011)
Spatial octal  117061145
Morton X/Y/Z   83 / 80 / 461
Structural     EXACT_STRUCTURAL_DECODE
Projection     UNDERDETERMINED
note: Morton X/Y/Z are hierarchical path indices, not coordinates
```

Add `--json` for the canonical `rgcs.structural-trace.v1` document.

## Encode fields back to a packet

```bash
rgcs-coordinate encode --face 4 --path 33012021211 --shell 3
```

## Round-trip check

```bash
rgcs-coordinate roundtrip 165876523
```

## Python API

```python
import rgcs_coordinate as rc

trace = rc.decode_coordinate(165876523)
print(trace.face_id, trace.q22_path, trace.extracted_shell)   # 4 (3,3,...) 3

word = rc.encode_coordinate(4, (3,3,0,1,2,0,2,1,2,1,1), 3)    # 165876523
assert rc.roundtrip_coordinate(word)["exact"]

text = rc.export_trace(trace)      # canonical JSON
trace2 = rc.load_trace(text)       # verified against the arithmetic
```

## Candidate physical projection (honest YELLOW)

```bash
rgcs-coordinate project 165876523 --profile earth-r1085a
```

Returns a JSON result whose `status` is `UNDERDETERMINED` (exit code
4), listing every assumption of the `earth-r1085a` profile. When the
scientific backend is installed it also includes a
`TRAINING_CALIBRATED_CANDIDATE` placement — the frame was *fitted to*
the Stonehenge training equality, so the placement can never validate
it. See CONCEPTS_AND_CLAIM_BOUNDARIES.md before quoting any number
from this command.

## The four fixtures

| decimal | label | note |
|---------|-------|------|
| 165876523 | Stonehenge | supplied training equality and regression fixture |
| 165892743 | orange-slice A | intended shell 7 |
| 165892763 | orange-slice B | active shell 7 by registered operator correction; raw extraction (shell 3) kept in provenance |
| 165892783 | orange-slice C | intended shell 7 |

```bash
rgcs-coordinate corpus validate
```
