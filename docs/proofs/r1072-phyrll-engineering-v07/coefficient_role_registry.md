# Coefficient Role Registry (v0.7)

Machine-readable copy: `coefficient_role_registry.json`.

**The rule:** four lanes, five role classes, and only lane D
(`PHYSICAL_MEASUREMENT`) may make a physical-performance claim — and only
with a measured value **and** an uncertainty attached. As shipped,
**no entry qualifies**; `performance_claimants()` returns `[]` and a test
holds it there.

## The mandated status block

```text
SOURCE DISPLAY:            67.3 N/W
EXACT RECOVERED CALC:      64672/961 N/W_ring,coupled
RELATION:                  rounds to same one-decimal value
NOT:                       exact equality
EXACT GAP:                 673/10 − 64672/961 = 33/9610   (asserted)
```

## Lanes

| Lane | Meaning | Entries |
|---|---|---|
| A | SOURCE_COEFFICIENTS — numbers as supplied | 67.3, 47/63, 27/93, 631/732, 236805 |
| B | EXACT_CALCULATION — recovered arithmetic | 64672/961, 9/31, the gap 33/9610 |
| C | DESIGN_GEOMETRY — the source locks | 37, 35/37, 33, 411/37 = 11+4/37, 188/288 = 47/72 |
| D | PHYSICAL_MEASUREMENT — all **pending** | η_couple, η_F_measured, L_eff, C_eff, Q_L, R_loss |

Lane D entries carry role `BENCH_REQUIRED` until measured. The registry
constructor rejects unknown lanes and unknown role classes, so a new
coefficient cannot enter untyped.

## What this fixes

v0.6 tagged 67.3 `SOURCE_PROVENANCE` beside the exact value, which left
the rounding relation implicit. v0.7 makes the display/exact split a type
distinction with the exact gap as its own registry entry — the arithmetic
can no longer be mistaken for carrying the physics.
