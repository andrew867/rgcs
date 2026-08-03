# Miami / Bermuda calibration report (v0.6)

**PUBLICATION HOLD.** No projector was fitted to Miami; the frozen r1053
projector was used unmodified.

## 1. The exact candidate `EXACT_ARITHMETIC` → `MODEL_OUTPUT`

```
236805/142 = 1667.640845070423 km
reference    1667.541270502605 km   (declared Miami–Bermuda side)
abs error        0.099575 km  (≈ 99.6 m)     rel ≈ 6.0e−5
```

The ~100 m miss is reported as a miss. Nothing rounds it away.

## 2. Frame honesty — the near-hit is frame-specific

| Frame | Miami–Bermuda | Candidate error |
|---|---|---|
| geodesic (metrics file) | 1667.541 km | **0.0996 km** |
| r1053 projector sphere (haversine) | 1662.233 km | **5.408 km** |

The two frames disagree by 5.3 km, and the candidate is a near-hit
**only against the geodesic figure** — under the repository's own
spherical projector frame it misses by 5.4 km. Any use of this candidate
must therefore state its frame, and the repo's active projector is not
the frame in which it looks good.

## 3. Look-elsewhere null control `MODEL_OUTPUT`

All ordered fraction pairs from the 20-integer coefficient pool landing
in 100–20,000 km were tested against all five declared Bermuda metrics
at ±0.1 km:

```
47 in-range fractions × 5 metrics = 235 comparisons
hits: 1   — 236805/142 vs miami_bermuda, err 0.0996 km
```

The candidate is the **only** hit in its own pool at this tolerance —
roughly a 1-in-235 comparison event, taken at face value. That makes it
worth recording and *not yet* meaningful: one fraction, one metric, one
tolerance, chosen after the fact. It becomes evidence only if the same
construction predicts a distance **not** used to find it.

## 4. Vector candidates through the existing projector — honest negative

Both wires parse under the R10.14A split (H=16 … T=3). Every legal
branch of the frozen r1053 direct lane was projected; over-limit
branches were refused, not truncated.

### `1680769543` — `BERMUDA_FLORIDA_VERTEX_VECTOR_CANDIDATE`

| Branch | Result | To Miami | To Bermuda |
|---|---|---|---|
| payload_only (8076954) | −38.04°, +85.68° | 18,112 km | 17,267 km |
| payload+terminal (80769543) | −10.25°, +62.88° | 15,766 km | 14,133 km |
| whole_wire | **REFUSED** — 1680769543 ≥ 2³⁰ | — | — |

### `168593073`

| Branch | Result | To Miami | To Bermuda |
|---|---|---|---|
| payload_only (859307) | −39.30°, +87.31° | 18,113 km | 17,393 km |
| payload+terminal (8593073) | −37.48°, +85.96° | 18,172 km | 17,297 km |
| whole_wire (168593073) | +47.84°, −64.98° | 2,791 km | 1,728 km |

**No legal branch of either wire lands within 500 km of Miami or
Bermuda** (asserted by test). The closest any parse comes is the
whole-wire branch of the second wire, 1,728 km from Bermuda — the wrong
side of the Gulf of St Lawrence.

**Consequence:** the `BERMUDA_FLORIDA_VERTEX` label remains a
*candidate label with no supporting parse* under the active projector.
It is not deleted (provenance) and not confirmed (no evidence). No new
projector was fitted to change this, per the spec's explicit
prohibition.

## 5. Verdict line

```
MIAMI_BERMUDA_CANDIDATE: RECORDED, FRAME-SPECIFIC, UNIQUE-IN-POOL,
                         NOT PROMOTED
VECTOR_CANDIDATES:       NO SUPPORTING PARSE UNDER THE ACTIVE PROJECTOR
PROJECTOR:               UNMODIFIED
```

The single most valuable next input for this lane: **an independently
sourced distance prediction from the same 236805/142 construction that
was not used to select it** — or a typed provenance record for either
vector that would justify a different legal branch set.
