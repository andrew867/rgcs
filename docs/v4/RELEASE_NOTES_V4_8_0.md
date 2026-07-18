# RGCS v4.8.0 — R4: Tetrahedral Spin-Addressed Codec and Four-State Memory Qualification

**SOFTWARE_VERIFIED, PHYSICAL_SPIN_UNTESTED.** No spin has been
written, read, or reset in any material. Quartz is BLOCKED, every
physical stop-matrix gate is open, and no bench stage is runnable. All
prior tags untouched.

Full account: [R4 findings](r4/R4_FINDINGS.md) · manuscript §15.

## The exact answer — and what it is not

    64   = 8^2 = 4^3 = 2^6
    4096 = 8^4 = 4^6 = 2^12

Three quaternary symbols select one of 64 states, six select one of
4096, and all 4096 keys round-trip through quaternary, octal and binary
— verified **exhaustively**, since the space is finite.

**This is zero compression.** The same twelve bits in a different base.
The claim is refused in code, and the benchmark carries a
`RAW_QUATERNARY` baseline that costs exactly what flat binary costs.

## Compression: the honest result

Real gains must survive **full bit accounting** (topology + address +
codebook + symbols + entropy model + residual) against fair baselines:

- **Wins** on piecewise-constant payloads against flat float32, raw
  quaternary, uniform Q8 and entropy Q8;
- **Loses to zlib** on that same data (13049 vs 1624 bits) — DEFLATE
  eats run-length structure;
- **Offers nothing** on smooth, sparse or ramp payloads;
- **Negative controls pass**: no gain on random data, which is what
  separates structure exploitation from bookkeeping.

Two methodological defects were found and fixed while running it: the
rate-distortion curve initially swept only λ (pinning fidelity at the
*codebook* bottleneck rather than tracing a frontier), and the HAL
ablation pinned λ so the tree never split. Both now sweep every rate
knob.

## Four states: what the ontology refuses

- **Four spin-1/2 directions are not four states.** The tetrahedral
  frame has pairwise overlap −1/3 in a 2-dimensional Hilbert space;
  the SIC outcome object raises if treated as storage. It is an
  informationally complete *measurement* representation.
- **Spin-3/2 readout resolves |m_s| pairs**, so the sign is erased —
  the engine returns an explicit `ERASURE` with 1 bit recovered, never
  a guess; resolving the sign costs an operation carried in the rate
  budget.
- **The write compiler refuses Δm_s ≠ ±1** single pulses: −3/2 → +3/2
  compiles to three sequential allowed pulses.
- **Quartz is BLOCKED** with all ten stop-matrix gates open.
- **Classical four-domain cells are separated from the spin claim** —
  they test the codec, and they are stage S0 of the bench precisely
  because that is the cheapest disqualifying test.

## Release-process fix (R04/R65)

v4.6, v4.7.0 and v4.7.1 each needed a commit *after* the tag to sync
the committed workbook and manifest, so the tagged tree was never quite
the released tree. `tools/r4_release_gate.py` now refuses a tag unless
those artifacts are current. **v4.8.0 is the first release whose tag
already contains every release-owned artifact.**

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 1217 passed
python -m pytest tests/v4/test_r4_all.py -q       # the R4 suite (62)
python tools/r4_release_gate.py                   # TAG_MAY_PROCEED
python tools/qa_audit_v4.py --fast                # 19/19
```

## Boundary

Nothing here is evidence of spin storage in quartz, of four orthogonal
states from four directions, of compression from base conversion, or of
any memory operation in any material. The codec results are synthetic
corpora only, and an off-the-shelf compressor beats this codec on its
own best case.
