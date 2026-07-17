# Prospective harmonic family N=5..12 (Agent C03)

Coverage: **A11, A12, G001–G014**. Gates: **G09, G12**.
Status: `CANDIDATE_NEW_COUPLING` — **prospective, not confirmed**.
Implementation: [`rscs2_core/harmonic_family.py`](../../rscs2_core/harmonic_family.py).

## What "prospective" means here

The family is **predicted and unbuilt**. No specimen in it exists, none
has been measured, and the arithmetic being self-consistent is not
evidence that the physics is.

The C03 boundary is the sharpest one in the programme: *do not optimize
each fabricated specimen after seeing its measured peak and then call
the family prediction successful.* Acceptance bands are therefore
declared **now**, before any specimen exists — that is the whole point
of writing this document at this stage.

## The relation

    L_N = 770.263671875 / N   mm

recomputed from the registered velocity and model, not hard-coded from
rounded values. `family_length_mm(n)` is the authority; the table below
is generated from it.

| N | target (kHz) | L_N (mm) |
|---|---|---|
| 5 | 20.480 | 154.053 |
| 6 | 24.576 | 128.377 |
| 7 | 28.672 | 110.038 |
| 8 | 32.768 | 96.283 |
| 9 | 36.864 | 85.585 |
| 10 | 40.960 | 77.026 |
| 11 | 45.056 | 70.024 |
| 12 | 49.152 | 64.189 |

N=7 at 110.038 mm is the length family the canonical 110 mm work sits
in — which is exactly why the prospective members matter: they are the
predictions that could fail.

## Mass scaling

For scale-similar bodies m_N ∝ N⁻³, since every linear dimension
scales as 1/N. Tested.

## Variants supported

- Facets: 6, 8, 12, 24.
- Rx and Tx angle variants.
- Density correction, taper, C-axis orientation.
- Manufacturing tolerances and electrode/mount allowances.

## Angle conventions are kept distinct

**51.843°** and **51°51′51″ (= 51.8642°)** differ by 0.0212° and are
**separate registry entries** (G001–G006). They are not merged, not
rounded into each other, and not averaged. See ORPHAN-011.

`angle_separations()` reports the separation at its exact value. The
0.0212° difference is small; it is not zero, and the record says so.

## Tolerance sensitivity

`tolerance_sensitivity()` returns −dL/L: the fractional frequency
error induced by a fractional length error. A ±0.1 mm machining
tolerance on the N=12 member (64.189 mm) is a ±0.16% frequency shift —
larger than the spacing between some registered frequency candidates,
which is a **prospective acceptance-band** problem, not a detail.

## Prospective acceptance (preregistration)

Declared before fabrication:

1. The acceptance band for each member is set by the tolerance
   analysis above, not by the observed peak.
2. Mode crowding is expected to increase with N; a "match" found among
   a dense forest of modes must survive the look-elsewhere correction
   in [NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md](NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md).
3. A member whose measured fundamental misses its band is a **failed
   prediction** and is recorded as such (G48).

## What would falsify the family

Fabricated members whose measured fundamentals do not track L_N ∝ 1/N
beyond the tolerance budget. That test requires specimens and
instruments; neither exists (`PROTOCOL_READY_HARDWARE_REQUIRED`).

## Status honesty

`CANDIDATE_NEW_COUPLING` is not `CORE_VALIDATED`. The arithmetic
relation is exact by construction — 770.263671875/N is a definition,
not a discovery. Whether alpha quartz bodies at those lengths resonate
where the relation says is an open empirical question with zero
measurements behind it.
