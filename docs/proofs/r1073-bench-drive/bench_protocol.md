# R10.73 bench protocol — 37-cell annular drive

Authority: the R10.72 constrained optimum, frozen — `mod = 0.5`,
`lag = π`, active-cell amplitude floor ≥ 0.5 (winner min 0.544),
predicted `|d_eff| = 0.4124` at 12.46° off the anti-blank axis.

**No force. No thrust. No wall power.** The observable is ΔB. A verdict
without a declared uncertainty and a complete control set is refused by
the evaluator, not defaulted.

## 1. Drive

`drive_table.{csv,json}` — 37 rows: 4 cells BLANKED (indices 0–3, the
open sector), 33 active, every active cell ≥ 0.544 amplitude
(floor honoured; asserted in code). Active amplitudes span 0.544–1.500
(first-harmonic loading); phase offsets span 0° to −121.8° (the π-lag
envelope across four cells nearest the sector). Loading column gives the
normalized capacitive/gap weighting to realise the amplitude profile
passively where preferred.

Carrier: 1,683,456 Hz (= 4096 × 411), per-cell m = 4 winding as in v0.6;
envelope reference 4096 Hz.

## 2. Predicted observable

```text
d_eff:  magnitude 0.4124 (hub radii), angle 207.05°,
        offset +12.46° from the anti-blank axis
```

Bench predictions that must hold if the model is right:

- `arg(ΔB) ≈ 207° ± σ_θ` (commanded);
- rotating the whole drive table by k cells rotates arg(ΔB) by
  360k/37 = 9.73k°, exactly (model transform is exact to 1e−6°);
- **mirroring** the table negates the offset (conjugate d_eff);
- **reversing the lag** (−π) mirrors the steer about the amplitude-only
  axis: −12.46°, same magnitude — *found by a failing test*: the naive
  claim d(−lag) = conj(d(+lag)) is false, and the corrected exact
  transform is the sharper control prediction;
- |ΔB| exceeds the equal-resource null distribution p95.

## 3. Probes (`probe_plan.json`, 54 probes)

Center probe; 37 perimeter probes at every cell angle (1.25 R, resolves
the 37-fold structure); 8 compass probes at 1.6 R (coarse asymmetry
vector standalone); 4+4 above/below-plane probes at ±20 mm (separates
in-plane from axial asymmetry). Acquisition: lock-in referenced to
1,683,456 Hz with 4096 Hz envelope as second reference; direct sampling
fallback ≥ 4.21 MS/s; demodulated channels ≥ 40.96 kS/s.

## 4. Nulls (`null_masks.json`)

Weight-table nulls: all-active symmetric; binary blanking best;
8 equal-resource randomized loading masks (**same amplitude multiset,
asserted**); reversed phase lag; rotated (k=7); mirrored. Bench
conditions: dummy resistive load, no-crystal, dummy-crystal.

## 5. Pass/fail

All six criteria reference the measurement's **own declared
uncertainty** — there are no absolute thresholds to game — and
`evaluate_bench_result` **refuses** (raises, does not FAIL, does not
PASS) when σ_θ is undeclared or any of the seven required control
results is missing. PASS and FAIL are both demonstrated reachable with
complete inputs, so the refusals are a working gate, not a stub.

## 6. What a PASS would and would not mean

PASS ⇒ a controllable annular field-asymmetry: |ΔB| follows the mod/lag
table and arg(ΔB) tracks command. That is the whole claim. It implies
nothing about force, propulsion, or any energy anomaly — those remain
behind the R10.72 force boundary and the six-term firewall, untouched.
FAIL ⇒ the model gets corrected before anyone wastes copper.
