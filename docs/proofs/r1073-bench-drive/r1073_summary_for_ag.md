# Summary for AG — R10.73 bench-drive spec

The constrained recipe is now a wiring diagram, a probe map, and a
falsification test. Nothing computes force; the strongest validation is
`arg(ΔB) ≈ arg(d_eff)`, exactly as you framed it.

## The deliverables

- **`drive_table.{csv,json}`** — 37 rows. 4 blanked (open sector), 33
  active, every active cell ≥ 0.544 amplitude (floor honoured). Per cell:
  angle, amplitude weight, phase offset (rad + deg), capacitive/gap
  loading weight, floor status.
- **`probe_plan.json`** — 54 probes (center + 37 perimeter + 8 compass +
  4/4 above/below plane), lock-in at 1,683,456 Hz with 4096 Hz envelope,
  sample-rate floors.
- **`null_masks.json`** — all-active, binary-best, 8 equal-resource
  randomized, reversed-lag, rotated, mirrored; plus dummy-load /
  no-crystal / dummy-crystal bench conditions.
- **`bench_protocol.md`** — the six pass/fail criteria and what a PASS
  does and does not mean.

## Predicted observable (the target)

```text
d_eff:  |0.4124|  at  207.05°   (+12.46° off the anti-blank axis)
```

The exact model transforms give three independent controls, not one:

| Drive change | arg(ΔB) must do |
|---|---|
| rotate table by k cells | +9.73k° (= 360k/37) |
| mirror table | negate the +12.46° offset |
| reverse lag (−π) | negate the offset, same \|ΔB\| |

If arg(ΔB) tracks all three within σ, the asymmetry is controllable, not
coincidental. That is a much harder test to pass by accident than a
single-angle match.

## One thing worth flagging

I asserted the reversed-lag transform was a conjugation. **A test caught
it: it is not.** Conjugating the weights does not conjugate the basis
phases, so d(−lag) ≠ conj(d(+lag)). The true transform is a mirror about
the amplitude-only axis (offset negates, magnitude holds), which I've
made the test and the protocol control. The gate did its job on my own
work.

## The refusal gate

`evaluate_bench_result` **raises** rather than returning a verdict when
the angular uncertainty is undeclared or any of the seven required
control results is missing. PASS and FAIL are both demonstrably reachable
with full inputs — so the refusals are a live gate, not a stub that
always says no.

## Where this sits

```text
maybe geometry means something        (v0.5)
→ audited arithmetic + firewall       (v0.6)
→ optimizer + measured loophole       (v0.7 / R10.72)
→ exact drive pattern, probe map,     (R10.73)  ← here
  falsification test
→ bench data                          (BENCH_REQUIRED, not yet)
```

Everything downstream of here is copper and instruments. The model has
said exactly what the magnetic asymmetry must do and exactly how it can
fail. PUBLICATION_HOLD; no tag; no push.
