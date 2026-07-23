# RGCS v5.7.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.6.0
**Licence:** MIT, unchanged. No relicensing.

R10.7: rooted interbody routing, solar and slate calibration roots, a
phase-conjugate return path, and a sky-observation reconstruction
engine.

Everything here is arithmetic, linear-systems DSP, and software.
**No physical measurement was performed by this project.**

---

## What R10.7 adds

Six new `r10` modules, each translating source material into typed,
refutable software whose **default output is a refusal or a null**:

- **`received.py`** — the transcription correction `8300 → 8.300` and
  `1876 → 1.876` is recorded **append-only**, never overwriting the raw
  values. The correction is scale-invariant: `8.300/1.876 = 8300/1876 =
  2075/469` exactly, so the residual against the phase-frame value
  `4096/925` is **unchanged** at `1649/433825 ≈ 0.086%`. Verdict
  `APPROXIMATE_NOT_EXACT`; no unit is inferred; `PhysicalMappingUnresolved`.
- **`rootframe.py`** — body frames built roots-first. Two non-parallel
  directions determine a proper rotation (matrix ↔ quaternion round-trip
  to 1e-9); a single direction is `ROOT_UNDERDETERMINED`. A latitude and
  a longitude are calibration on a known frame, **not** a frame.
- **`route.py`** — a rooted interbody route compiler. A rooted
  Earth–Moon route compiles and carries a **light-time floor of ≈1.28 s**.
  A hop claiming zero transit across a nonzero distance raises
  `CausalityViolation`. No route beats the floor; the report disclaims
  any "gateway."
- **`solarroot.py`** — a dynamic solar root as the weighted centroid of
  emission directions, with **demonstrated power** on a planted centroid.
  The real catalog is declared `BLOCKED_NO_DATA_SOURCE`, **not faked**.
  Verdict `ROOT_CANDIDATE_ONLY`.
- **`skytrack.py`** — an anonymized sky-observation engine. It ranks the
  *ordinary* candidates a kinematic description is consistent with, but
  the terminal verdict is `UNIDENTIFIED_OBSERVATION`; it refuses to
  identify anything without a catalog match and holds no specific
  observation.
- **`phaseconj.py`** — a phase-conjugate return treated as ordinary DSP.
  A reciprocal channel refocuses a phase-conjugated pulse (round trip
  multiplies the spectrum by `|H|²`, which is real); the refocus is exact
  and sits far above an energy-matched random-return null.

## The result is conventional, and the firewalls are the point

Phase conjugation / time reversal is a century-old piece of
linear-systems engineering, and the module says so. Its four firewalls
are quantitative:

- **Conjugation is a specific operation.** A sign flip, a bare time
  reversal, and a pointwise conjugate each **fail** to refocus; only
  spectral conjugation (conjugate **and** time-reverse) works.
- **Reciprocity is the control.** A nonreciprocal return channel does
  not refocus — `RECIPROCITY_REQUIRED`.
- **Causality holds.** Folding the propagation delay into the conjugated
  phase cancels it algebraically (a superluminal return);
  `refuse_superluminal_return()` rejects it and the honest round trip
  books the full delay — `CAUSAL_DELAY_REQUIRED`.
- **Roles stay separate.** Carrier, key, local oscillator and message
  clock are four typed roles; sharing a frequency is not sharing a role.

## Private side (never public)

`SRC_JH` (Jen Han) and `SRC_LS` (The L's) carry forward as **distinct
Tier-A private sources** under the single public alias
`OMEGA_REGION_SOURCE`. The five twelve-digit CW vectors and the
twelve-word Vortex Opening Key are preserved **byte-for-byte**
(integrity re-verified against the R10.6 SHA-256 receipt — all match).
A source-provenance trail and a field-observation record — whose
particulars concern a real named individual and a personal observation —
were written to the **private repository only** and are not reproduced
publicly: recorded verbatim, every post-message item a lead, **no
independent verification performed or fabricated**, and no claim about
any real person.

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 3079 passed
```

The deselected node is a byte-equality test requiring the archived
v2.0.0 build environment. Hosted CI deselects exactly that node id per
policy D-V3-04; its portable sibling `test_generator_numerically_equivalent`
runs everywhere.

## What this release does not claim

- No apparatus was built, no signal sent, no channel measured, no return
  refocused on a bench, no crystal driven.
- No root, frame, or route was physically realized; frames are
  underdetermined without a second direction, the solar catalog is
  blocked, and no interbody edge is physically supported.
- No decoder was found and none was attempted anew; the base-10 clue
  remains `NO_DECODER_IDENTIFIED` from R10.6.
- No observation was identified — not called a craft, not called nothing.
- The corrected numbers change no physics: scale-invariant ratio,
  unchanged residual, mapping unresolved, no unit invented.
- No named person and no source text enters the public tree.

## Not executed (deferred / blocked)

Density-layer routing (P08), the apparatus / field-solver and
mechanical-source phases (P11), the blinded / prospective harness run
(P12 — nothing to reveal against yet), the private narrative archive
(P13), real slate-image ingestion (P05), and the real solar catalog
(P04, `BLOCKED_NO_DATA_SOURCE`). Hardware and future-data phases remain
deferred.

See [R10_7_FINDINGS.md](R10_7_FINDINGS.md) for the full analysis.
