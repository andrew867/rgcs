# Composed loading + phase-lag 2-D sweep

Data: `composed_sweep_report.{json,csv}`. All `MODEL_OUTPUT`; **no force
computed anywhere**; every grid point runs its own equal-resource null
(same weight multiset, arrangement shuffled) and all 110 beat it. Locks
held at every point: 33 active, rotation-invariant to 1e−9.

Composed family:

```text
w_k = a_k · (1 + mod·cos(φ_k − φ_c − π)) · exp(−i·lag·exp(−(dist_k/width)²))
```

`mod = 0` reduces exactly to the pure phase taper; `lag = 0` reduces
exactly to the pure capacitive/gap loading family (both asserted by
test), so the sweep genuinely contains the single-knob baselines.

## Headline: composition works — and then it found a loophole

Grid (10 mods × 11 lags): |d_eff| = **0.4913** at (mod = 0.9,
lag = 2.5) — 1.74× the single-knob best. But the maximum sat at the grid
**corner**, and a boundary extension shows |d_eff| rising monotonically
through mod = 0.95, lag = 3.5 (0.5165) with no interior optimum.

**Diagnosis — this is de facto blanking, not better drive.** At mod = 0.9
the near-sector "active" cells run at 0.18 amplitude; at 0.95, at 0.13.
Past lag = π they overshoot anti-phase. Nominally 33-active, effectively
~29-active: the optimizer was escaping the lock through amplitude → 0.
A monotone climb toward a physical boundary is the model asking to
violate the constraint's spirit while honouring its letter.

## The fix: an amplitude floor, declared and codified

```text
ACTIVE_AMPLITUDE_FLOOR = 0.5      (an active cell carries ≥ half amplitude)
LAG_BOUND = π                     (no overshoot past anti-phase)
⇒ mod ≤ 0.5  (first-harmonic loading has min|w| = 1 − mod)
```

The floor is enforced in `constrained_optimum()` by **checking the
winner's actual min amplitude**, not by trusting the mod bound.

## Constrained recipe (the deliverable)

```text
mod = 0.5, lag = π
|d_eff| = 0.4124        min active amplitude = 0.544   (floor honoured)
direction offset = 12.5°  off the anti-blank axis
beats its null            1.46× the single-knob best (0.283)
```

Steering under the same constraint:

| Commanded offset | Best \|d_eff\| | Retention |
|---|---|---|
| ~10° | 0.4124 | 100% |
| ~20° | 0.3692 | 89% |
| ~30° | 0.3104 | 75% |

Direction is commanded by trading `mod` down at fixed high `lag`; the
constrained recipe already sits ~12° off-axis, so ±10° of steer is free.

A secondary finding: the pure phase knob was under-driven in v0.7 —
`lag = π` alone gives 0.310, more than double the 0.146 at the v0.7
default `lag = 0.8`.

## Bench translation (all BENCH_REQUIRED)

The recipe in hardware terms: first-harmonic capacitive/gap loading at
50% modulation depth, with the cells nearest the open sector driven in
anti-phase (lag → π across a 4-cell envelope). The bench observables
remain |ΔB| ↑ and arg(ΔB) tracking the commanded arg(d_eff), with
thermal/vibration/electrostatic controls bounded — force is not among
them.

## Tests

9 new: both single-knob reductions exact; every point lock-33,
rotation-invariant, forceless, and beating its null; the boundary
monotonicity codified as a test (so the loophole stays documented);
the floor declared, enforced on the winner, and the constrained optimum
still ≥ 1.3× the single-knob best.
