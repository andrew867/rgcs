# Resonator electrical model and measurement plan (v0.7)

All performance-bearing quantities here are `BENCH_REQUIRED`. The model
supplies consistency relations and extraction protocols, nothing more.

## What the carrier lock already pins down

If the ring resonates at the locked carrier f₀ = 1,683,456 Hz, then

```text
L_eff · C_eff = 1/(2π f₀)² = 8.9379e−15 s²      (exact consequence)
```

One degree of freedom, not two. A design point on the locked line, for
orientation only (`MODEL_OUTPUT`, not a measured device):

```text
C_eff = 1 nF  →  L_eff = 8.938 µH ;  at Q_L = 100 → R_loss ≈ 0.945 Ω
```

## Extraction protocols (one row per unknown)

| Unknown | Method | Protocol | Target σ |
|---|---|---|---|
| L_eff | impedance sweep | \|Z\|(f) + phase, f₀/10 → 10f₀; series-RLC fit; L from the inductive slope below resonance | 2% |
| C_eff | same sweep | C from the capacitive slope above resonance; cross-check L·C against measured f₀ | 2% |
| Q_L | ring-down **and** 3 dB bandwidth | τ-fit → Q = π f₀ τ; confirm with f₀/BW; the two must agree or the discrepancy is itself reported | 5% |
| R_loss | derived | R = 2π f₀ L/Q from the measured pair; sanity-check vs DC + skin estimate | propagated |
| η_couple | power accounting | wall power in vs ring energy turnover ωU/Q at steady state; calorimetry on the drive chain closes the budget | 10% |

## Standing rules carried forward

- `P_ring = ωU/Q` takes the **ring's** stored energy; wall power enters
  only through `ring_power_from_wall`, which raises without a declared
  η_couple (unchanged from v0.6, retested in v0.7).
- The only candidate-force computation in the package is
  `force_boundary.candidate_force`, tagged `BENCH_REQUIRED`; a thrust
  claim requires a lane-D measured η with uncertainty, and no such
  measurement exists.

## Companion firewall

`conventional_force_firewall.md` covers what must be subtracted from any
measured force before a residual may even be quoted.
