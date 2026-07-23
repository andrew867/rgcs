# RGCS v6.0.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.9.0
**Licence:** MIT, unchanged. No relicensing.

R11: body-specific planetary magnetic roots, a South-Up Earth face frame,
compressed address envelopes, a four-fraction phase alphabet,
crystal-carrier and isotope-epoch searches, a dynamical-boundary photon
lane, orbital-versus-atomic scaling nulls, and decoder identifiability.

Everything here is arithmetic, conventional physics, and software.
**No physical measurement was performed by this project.**

**Final verdict: `R11_GREEN_MODELS_IMPLEMENTED_DECODER_NOT_IDENTIFIED`.**

---

## Why a major version

`r11` is a new top-level public package and `tests/v6` a new suite root.
The package is registered in **both** packaging lists — `pyproject`
`packages.find` *and* `build_meta.SOURCE_ROOTS` — closing the trap that
silently shipped none of r6/r7/r8 in v4.9.0–v5.1.0.

## Gate Zero, and the one condition that was waived

The required start state (commit, tag, clean worktree, suite of record,
private files ignored and untracked) verified. One condition could **not**
be met: alleged-communicator identity strings exist in the public tree and
in **immutable history**, back to the frozen v2.0.0 baseline and inside
published tags. Removing them would require rewriting published history
and re-cutting released tags, which release policy forbids.

Per operator decision it is **waived and recorded** as a
`DECLARED_RESIDUAL_EXPOSURE` in `r11/sources.py` — by *category*, never by
restating the strings — following the precedent already used for the
frozen v2.0.0 absolute-path residual. **R11 adds no new identity strings
and refuses to.** See [R11_GATE_ZERO.md](R11_GATE_ZERO.md).

## The results, all negative or bounded

- **The phase alphabet has a hard limit.** `2/3, 3/4, 5/6, 7/2` reduce to
  240°, 270°, 300°, 180° on the 15° lattice — but a **single quadratic
  channel maps 240° and 300° to the same value**, so it cannot carry all
  four symbols. Computed, not asserted.
- **The crystal carrier is arithmetic only.** Look-elsewhere
  **p = 0.35** over a 2160-expression grid → `NO_BETTER_THAN_CHANCE`.
- **No unique epoch.** Cs-133 aliasing falls from ~1.6×10¹⁹ to ~1.7×10¹⁰
  with a second carrier and still leaves no unique answer.
- **Orbital/atomic scaling is unestablished.** The random order-statistic
  null is **competitive** with every structured law (p = 0.16); one moon
  system beats its control but fails the look-elsewhere correction.
- **The truncated photon is not a new particle.** A time-dependent
  boundary gives a multimode Bogoliubov state; the instantaneous-switching
  divergence is an unphysical idealization, not free energy, and the
  switching apparatus supplies the energy.
- **No decoder was identified.** No decoder beat chance on any null, while
  the power control separates cleanly on planted data.

## Two corrections to the source pack's own arithmetic

Recorded rather than adopted:

1. The exact base for 9192 (13788 Hz) sits **15.72 Hz above** the finest
   computed mode — not "0.03 Hz below" as stated. Wrong in sign and ~500×
   in magnitude.
2. The reference shell radii require **R_E = 6371.0087455872 km**, not
   6371.0.

## Red team

Sixteen named attacks — rotating the frozen solid after seeing targets,
picking a magnetic scalar or gradient sign per target, reading decimal
digits as octal, truncating payload bits, reordering the shell readings,
inventing timestamps, choosing an isotope orientation from a desired year,
selecting a carrier after seeing the target, equating units by number
alone, conflating nuclear spin 7/2 with the phase 7/2, calling
interference a broken photon, calling the divergence free energy, using an
Earth dynamo root on a body without one, and leaking private provenance —
**each fails with a typed reason.**

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 4062 passed
```

> **CI note.** The free-tier GitHub Actions minutes are exhausted, so this
> release was not built by hosted CI. The verification of record is the
> full local suite on the exact release commit
> (`docs/v4/RELEASE_METADATA.json`); the recipe above reproduces it.

## What this release does not claim

No ship, no external transmission, no new particle species, no decoded
location, no unique epoch, no planetary terraforming system, and no
physical crystal effect is established. No apparatus was built and nothing
was measured. Arithmetic and source claims remain typed as such.

See [R11_FINDINGS_AND_NONCLAIMS.md](R11_FINDINGS_AND_NONCLAIMS.md) for the
full analysis.
