# Ring Steering Optimizer report (v0.7)

Data: `ring_steering_optimizer_report.{json,csv}`. **No force is computed
anywhere in this lane.** Success metric: |d_eff| under the source locks.

Source locks held throughout: 37-family ring, 35/37 running, 33 active
steering, no mechanical rotation, f_c = 1,683,456 Hz (411/37 = 11 + 4/37),
188/288 = 47/72.

## Results (hub radius = 1; 400-trial equal-resource nulls)

| Family | Active | \|d_eff\| | Null p95 | Beats null | Lock 33 |
|---|---|---|---|---|---|
| **capacitive_gap_weighting** | 33 | **0.2830** | 0.124 | ✓ | ✓ |
| **graded_current_taper** | 33 | **0.1786** | 0.111 | ✓ | ✓ |
| **graded_phase_taper** | 33 | **0.1460** | 0.119 | ✓ | ✓ |
| two_adjacent_blanks | 35 | 0.0569 | 0.056 | ✓ (marginal) | 35-lock |
| two_separated_blanks | 35 | 0.0413 | 0.056 | ✗ | 35-lock |
| single_blank | 36 | 0.0278 | degenerate | ✗ (see below) | ✗ |
| near_opposite_blanks | 35 | 0.0024 | 0.056 | ✗ | 35-lock |

**Lock-compliant ranking:** capacitive_gap_weighting →
graded_current_taper → graded_phase_taper.

## The engineering finding

**Grading beats blanking.** Every graded 33-active family more than
doubles the best binary family's |d_eff|, and the first-harmonic
capacitive/gap loading profile is the strongest tested — 0.283, about 5×
the two-adjacent-blank baseline — while beating a null that holds the
*same weight multiset* and randomises only its arrangement. The blanks
open the sector; the graded drive is what moves the field centre.

Secondary observations, all model-level:

- **Phase taper steers direction at magnitude cost.** It is the only
  family whose d_eff rotates off the blank axis (anti-alignment error
  ≈ 25°). A magnitude knob (loading) and a direction knob (phase lag)
  may therefore be composable — the natural next sweep.
- **Amplitude families are exactly anti-aligned with S** (d_eff points at
  surviving current; S points at the blanks). arg(S) remains the correct
  bench prediction for arg(ΔB) up to that sign convention.
- **Separated and near-opposite blanks fail their nulls** — spreading the
  hole is worse than random placement of the same resource. Honest
  negatives, kept.
- **The single-blank null is degenerate** (every placement is a rotation
  of every other), so it is reported as *not* beating its null rather
  than winning by floating-point noise.
- All families are rotation-invariant to 1e−9, as the lock demands.

## What success is, and is not

```text
model success:  |d_eff| ↑ under locks          — achieved, ranked above
bench success:  |ΔB| ↑, arg(ΔB) = arg(S),      — BENCH_REQUIRED
                thermal/vibration/electrostatic
                controls bounded
NOT success:    force                            — not computed, by design
```
