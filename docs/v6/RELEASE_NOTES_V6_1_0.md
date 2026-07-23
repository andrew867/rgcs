# RGCS v6.1.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v6.0.0
**Licence:** MIT, unchanged. No relicensing.

The R11 delta: exact timing, classical dynamic boundaries, a
truncated-photon adapter, a hybrid rotor, a geometry inverse, a Mars
frame pilot, and a detector matrix. Seven new `r11` modules; nothing
existing was reset.

Everything here is arithmetic, conventional physics, and software.
**No physical measurement was performed by this project.**

---

## Mandatory corrections

**The "0.03 Hz below" figure is resolved.** It never belonged to 13788 Hz:

```
13772.28 − 13772.25 = 0.03    exactly   ← the real 0.03-below candidate
13788.00 − 13772.28 = 15.72   exactly   ← what 13788 actually is
```

`13772.25 Hz` is now the registered candidate; 13788 stays refuted and
**above** the computed mode. Registered as **arithmetic only** — a 0.03 Hz
step from a computed mode is a statement about rounding, not a carrier.

`NO_DECODER_IDENTIFIED` is preserved. The historical-name exposure remains
a `DECLARED_RESIDUAL_EXPOSURE`; **no history was rewritten.**

## Paper ingest — and a provenance catch

The request named **arXiv:2510.21636v2** (*"A truncated photon"*) with a
digest, but the **attached** file was a different paper —
**arXiv:2306.05929v2** (cavity mode mixing). Both were located and hashed:
the named paper's digest **matched exactly** (`b9e54ac8…`) and its
equations are now registered; the attachment is registered separately as
conventional cavity optics. Recorded as `RESOLVED_BOTH_REGISTERED` rather
than assuming the attachment was the paper.

## The seven new verdicts

| Module | Verdict |
|---|---|
| `exacttiming` | `EXACT_TIMING_REGISTERED` |
| `mechboundary` | `CLASSICAL_DYNAMIC_BOUNDARY_MODEL_IMPLEMENTED` |
| `photonadapter` | `QUANTUM_TRUNCATION_NOT_BENCH_VALIDATED` |
| `rotor` | `HYBRID_ROTOR_MODEL_IMPLEMENTED` |
| `geominverse` | `CENTROID_INVERSE_UNDERDETERMINED` |
| `marspilot` | `MARS_FRAME_PILOT_COMPLETE_MAGNETIC_ROOT_NOT_IDENTIFIED` |
| `detectors` | `CCD_PHONON_DETECTION_REFUSED` |

## Results, all bounded or negative

- **552.001953125 ms = 2261/4096 s exactly** = 2261 cycles at 4096 Hz. The
  registered **−1/125 cycle residue is provably unrealisable** by any
  integer-hertz carrier over that macrocycle (`gcd(2261,4096)=1` fixes the
  residue lattice at multiples of 1/4096, and 4096/125 = 32.768 is not an
  integer). Retained as a supplied datum, **not fitted**.
- A **sudden** mechanical boundary change scatters **37–52%** of a mode's
  energy; a long ramp recovers the adiabatic limit. **Damping is an honest
  null** — it never moves the modal basis.
- The truncated-photon paper's optical example **reproduces**
  (`⟨n⟩ ≤ 1.43` at `T = 10⁻¹⁴ s`), with Eq. 31's upper inequality reported
  as **marginal** there rather than smoothed. Only a classical analogue is
  implemented; there is no QFT solver here.
- **192 teeth at 1280 RPM = 4096 passages/second, exactly.** Spin
  authorization is refused unconditionally.
- **atan(√φ) = 51.8272923…° is NOT 51.843°** (gap 0.0157° = 56.5 arcsec;
  they agree to one decimal place). A centroid plus one frequency leaves a
  **rank-2 Jacobian with deficiency 3** and a solution family.
- The **Mars frame completes; its magnetic root does not** — the MAG/ER
  grid is `BLOCKED_MISSING_DATA`.
- **No detector couples to phonons at all**, not even the piezo, so the
  CCD refusal does not rest on an overclaim elsewhere.

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 4412 passed
```

> **CI note.** The free-tier GitHub Actions minutes are exhausted, so this
> release was not built by hosted CI. The verification of record is the
> full local suite on the exact release commit.

## What this release does not claim

No ship, no external transmission, no new particle, no decoded location,
no unique epoch, no planetary terraforming system, no physical crystal
effect. No apparatus was built, no rotor spun, no field measured, no
quantum state prepared.

See [R11_DELTA_FINDINGS.md](R11_DELTA_FINDINGS.md) for the full analysis.
