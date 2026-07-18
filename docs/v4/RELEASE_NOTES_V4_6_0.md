# RGCS v4.6.0 — Crystalline Spacetime Coordinate Program (CSCP)

**SOFTWARE_VERIFIED, PHYSICAL_UNTESTED.** No apparatus was built, no
data was collected, and no physical hypothesis in this programme is
supported. Every prior tag is untouched.

This release implements the v4.6 programme: exact unit-aware frequency
mathematics, a frozen statistical null engine, the 64-tetrahedron
lane, phase-coherent DDS/NCO compilation, preregistered experiment
definitions, and a relativistic clock / metric-energy audit — plus the
firewalls that stop any of it from being read as physics.

Full detail: [CSCP findings](cspc/CSCP_FINDINGS.md) ·
[programme ledger](cspc/PROGRAMME_LEDGER.md)

## The question, and the answer this programme can support

> Can crystalline resonators bridge stable phase, cross-domain
> frequency conversion, temporal order, spacetime measurement, and
> "space-time travel"?

**No bridge to travel is supported.** One genuine capability survives:
**metrology**. Resonators and clocks measure the metric; they do not
control it.

## Corrections to the source material

- **"2.45 GHz is the frequency of water" — corrected.** Water's
  microwave response is broad dipolar *relaxation*, not resonance. A
  single-Debye model puts the loss maximum near **19.2 GHz**, 7.9×
  above the ISM band, where 2.45 GHz carries only ~25% of peak loss.
- **"0.0356521923…" — corrected.** It retains **hertz**: it is
  `2.45e9 / 2^36`, the least-significant step of a 36-bit accumulator,
  i.e. a frequency *resolution*.
- **"11th octave" — corrected.** `8^11 = 2^33` is thirty-three
  octaves, not eleven.
- **"64-tetrahedron grid" — underdetermined.** Four readings are
  registered and analysed; none is promoted.

## Findings

- **Precision does not survive the input.** `2.45e9 / 8^9` is exactly
  18.25392246246337890625 Hz as arithmetic and **18.3 Hz** as physics
  (the input is nominal at three significant figures). The code
  reports both and flags the overclaim.
- **The simplicity metric measures human convention, not nature.**
  Under a frozen, hash-pinned metric with family-wise correction,
  everything surviving is either constructed from its own reference or
  is a table of human-chosen round numbers (ISM bands, quartz clock
  crystals). The programme's own candidates score "simple" and are
  flagged **CIRCULAR** — they were built that way. Positive control
  (just intonation) is detected; irrational control (equal
  temperament) is not.
- **4096 from "64 tetrahedra" is counting.** 4096 = 64², so every
  64-element structure has it, including unstructured ones. Across
  four non-isomorphic families the geometric lattices are unusually
  *poorly* connected versus degree-matched nulls; none is specially
  synchronizable.
- **The elegant phase closure fails on real hardware — and a clock
  choice fixes it.** On a 100 MHz reference the common closure window
  collapses from 1/4096 s to ≈42.9 s (×175 000). On a binary reference
  clock (2²⁶ Hz = 67.108864 MHz, a stock part) every target is exact
  and the ideal window returns. **This is the most useful engineering
  output of the release.**
- **Spacetime.** The weak-field model reproduces Pound–Rebka
  (2.4551e-15 vs 2.45e-15) and the GPS correction (net **+38.44
  µs/day** vs +38.5). Capability: an optical clock at 1e-18 resolves
  ~9 mm of height. Refutation: 100 W for an hour implies a
  Schwarzschild radius of **5.9e-39 m** — 23 orders of magnitude below
  a proton, smaller than the Planck length.
- **Temporal order is not travel.** Subharmonic response is ordinary
  nonlinear dynamics unless many-body rigidity is shown, and even a
  genuine time-crystal candidate makes no travel claim. All five
  travel-adjacent claims are **UNSUPPORTED** with the specific
  evidence each would require.

## Also in this release

- Four new **Master Evidence Workbook** sheets (CSCP Candidates,
  Tetrahedron, Spacetime, Experiments) generated from the canonical
  store, showing exact and physically-supported precision side by side.
- **RF safety is structural**: `approve()` refuses open 2.45 GHz
  radiation, unshielded band work, biological exposure, improvised
  mains and non-isolated supplies, with no override flag.
- Five defects found by running the analysis honestly, including a
  null model that made *every* corpus look significant (fixing it
  inverted the headline result) and a source-hash guard that
  misreported fresh binaries as stale on Windows checkouts.

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 1062 passed
python -m pytest tests/v4/ -q -k cspc          # the CSCP suite
python tools/cspc_baseline.py                  # programme baseline
python tools/qa_audit_v4.py --fast             # 19/19
```

## Boundary

Nothing here is evidence that a crystal prefers a frequency, that the
64-tetrahedron model is physical, that 4096 is universal, that water
has a unique 2.45 GHz resonance, that the optical candidate couples
across 35 octaves, or that any temporal mechanism was created. Bench
evidence would be required, and none exists.
