# Hydrogenuine (HG) RSCS Memory Architecture

**Author:** Agent 04. **Date:** 2026-07-14. Implementation:
`rscs_core/memory/hydrogenuine.py` (RSCS-C.15, RSCS-O.14/15/16). Class **ENG**
— an engineering memory data structure, never evidence. NHT/HAL interpretation
is HYP and excluded from any physical claim (`docs/EXCLUSION_MATRIX.md`).

## 1. The memory record (RSCS-C.15)

A `HydrogenuineRecord` is an immutable, typed composite:

| Field | RSCS coordinate | Role |
|---|---|---|
| `allocentric` | C.1 SpatialCoordinate | world/map-frame position (the invariant anchor) |
| `egocentric` | C.1 SpatialCoordinate | sensor/observer-frame position |
| `frame` | C.8 OrientationFrame | ego → allo transform |
| `event_time` | C.2 TimeCoordinate | when the record was formed |
| `phase` | C.3 PhaseCoordinate (optional) | NHT space-to-phase encoding (**HYP** when set) |
| `predicted` | C.7 ModalState | expected observation |
| `observed` | C.7 ModalState \| None | actual observation (None until seen) |
| `uncertainty` | C.12 Uncertainty | localization uncertainty (wraps v2 σ) |
| `provenance` | C.13 ProvenanceTag | source + class + process path |

**Invariant (checked at store time):** `allocentric == frame · egocentric`
within 1e-6 mm. A record may be stored unreconciled only with an explicit
`require_consistent=False`.

## 2. Semantics (RSCS-O.14/15/16)

- **Store (O.14, `store`).** Write a record; enforce frame consistency
  unless opted out. Provenance defaults to `(internal, ENG)`; a NHT phase
  slot, if filled, carries a HYP provenance.
- **Replay (O.15, `replay`).** Recall the record as seen from a query frame.
  The **allocentric anchor is invariant**; the egocentric position is
  recomputed as `query_frame⁻¹ · allocentric`. Replaying into the original
  frame reproduces the egocentric position (fidelity, H-18). This is the
  egocentric↔allocentric re-referencing of MePMoS, as a deterministic
  transform.
- **Update (O.16, `update`).** Fold an observation into the record: the
  observed state is recorded, uncertainty is reconciled (caller supplies the
  posterior σ; the prior is kept if omitted). Prediction error is
  `predicted` vs `observed`, exposed to the caller. No hidden state.

The predict → observe → update cycle is the software realization of the
MePMoS loop ordering — as an engineering event-update, with no cognitive
claim.

## 3. Replay / update example (round-trip)

```
frame  = OrientationFrame(rot_z(90°))            # ego→allo is a 90° turn
ego    = SpatialCoordinate((1, 0, 0))            # 1 mm ahead of the sensor
allo   = frame · ego  = (0, 1, 0)                # 1 mm along world-y
rec    = store(allo, ego, frame, t=0, predicted) # frame-consistent ✓
rp     = replay(rec, identity_frame)             # ego re-referenced to world
#        rp.egocentric == (0, 1, 0) == rp.allocentric  (identity query)
#        rp.allocentric == (0, 1, 0)  (invariant)
up     = update(rec, observed, posterior_σ)      # observed recorded, σ reconciled
```

This exact flow is exercised by `tests/unit/test_rscs_hg_memory.py` and
`tests/property/test_rscs_hg_properties.py`.

## 4. Falsifiable software claims

H-15..H-19 (`docs/NHT_HAL_RSCS_MAPPING.md` §4, `docs/CLAIM_REGISTER.md`):
retrieval quality, transform consistency, temporal continuity, localization/
replay fidelity, uncertainty calibration. Each has a pre-registered failure
condition. H-16/H-18 are machine-tested now; H-15/H-17/H-19 test at the
persistence layer.

## 5. Software implementation tranche (for Agent 08)

The in-memory primitives are complete and deterministic. The software/
hardware plan should add:

1. **Persistence** — an append-only store of `HydrogenuineRecord`s keyed by
   allocentric position + event time (event-sourced; supports H-15/H-17).
2. **Query** — nearest-anchor recall with a declared metric (spatial mm on
   C.1; never a collapsed physical+state scalar, per RSCS_MATHEMATICAL_MODEL
   §7).
3. **Calibration harness** — measured σ vs realized error, testing H-19.
4. **Serialization** — `to_dict()` is already deterministic/JSON-ready
   (null-not-NaN); wire it to the workspace schema.

No firmware or UI is built by Agent 04; those are Agent 08's boundary.

## 6. Boundaries

- The HG record is ENG. It does not become HYP or EST by being used.
- The NHT phase encoding (O.3) and HAL lattice (C.14/O.13) remain HYP and
  quarantined; the record may reference them but never launders their class.
- No consciousness, perception, or quartz-memory claim is made or implied.
