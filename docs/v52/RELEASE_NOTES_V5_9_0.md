# RGCS v5.9.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.8.0
**Licence:** MIT, unchanged. No relicensing.

R10.10: the natural-geological-quartz source requirement, the verified
postwar quartz-growth patent timeline, a natural-vs-synthetic matched
experiment, CW codec V2, nonlinear optics, nonlinear inverse estimation,
and bus-factor-zero continuity.

Everything here is arithmetic, verified history, conventional physics, and
software. **No physical measurement was performed by this project.**

---

## Verified history, and the refusal

The postwar synthetic-quartz patent timeline through Brush, Clevite, and
Bell Laboratories is **verified** (`POSTWAR_QUARTZ_INDUSTRIAL_TIMELINE_VERIFIED`),
and so is the **defense-company overlap** (`DEFENSE_COMPANY_OVERLAP_VERIFIED`).
The third thing is **refused**: `CLASSIFIED_TECHNOLOGY_LINK_NOT_ESTABLISHED`.
Corporate and defense adjacency is ordinary industrial history — firms that
grew oscillator quartz also had ordnance business because oscillators go in
radios — **not** a hidden or extraterrestrial lineage, and chronology is
not causation. Patent dates are `HISTORICAL_FACT` as sourced (transcribed
from primary-record research), not independently re-verified here.

## Natural quartz: source-required, experimentally unresolved

The private source hypothesis that natural geological quartz is *required*
stays private. Publicly it becomes one disciplined statement — **geological
growth history is an independent experimental variable** —
`SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED`. Consciousness is never
published as materials science. **Synthetic quartz, fused silica, and glass
are mandatory controls.** The matched protocol is blinded and
preregistered, with a label-shuffle null (power proven on a planted
effect), multiplicity correction, and **ordinary differentiators**
(trace elements, inclusions, water, defects) explaining any difference
first. A seller label is not provenance — origin is `VERIFIED` only with a
chain of custody. Real specimens: `BLOCKED_NO_SPECIMENS`.

## What R10.10 adds

Ten new `r10` modules (143 new tests): `quartzhistory`, `naturalsource`,
`natsynth`, `specimen`, `characterize`, `cwcodec2` (40-bit packed decimal,
null windows, collision audit, no retrofit — `NO_DECODER_IDENTIFIED`
carried forward), `codecbind` (a codec number is not a coordinate without a
frame, epoch, and uncertainty), `nlinverse` (detects non-identifiability,
calibrates uncertainty by coverage), `nlo` (quartz SHG is real but
`NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ`), and `continuity` (deterministic
manifest, export/restore verification, clean-room successor drill).

The required **30-document public documentation set** is delivered under
[`docs/v59/`](R10_10_FINDINGS.md) with a standard header on every document.

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 3485 passed
```

> **CI note.** The project's free-tier GitHub Actions minutes are
> exhausted, so this release was not built by hosted CI. The verification
> of record is the full local suite on the exact release commit
> (`docs/v4/RELEASE_METADATA.json`); the recipe above reproduces it.

## What this release does not claim

- No apparatus, no specimen measured, no crystal driven, no signal emitted.
- Natural quartz is source-required but **experimentally unresolved**;
  synthetic quartz is a **mandatory control**; no natural-superiority or
  consciousness claim.
- Verified corporate/defense history does **not** establish a classified
  or extraterrestrial lineage.
- The CW vectors are **not decoded**; no codec output is a coordinate
  without a frame, epoch, and uncertainty.
- Bulk quartz SHG is weak and not phase-matched.
- No private name, locality, raw source text, or CW vector digit enters the
  public tree.

## Not executed (deferred / blocked)

The matched natural-vs-synthetic experiment (`BLOCKED_NO_SPECIMENS`), all
characterization measurement, and hosted CI. Hardware and specimens do not
exist in this environment.

See [R10_10_FINDINGS.md](R10_10_FINDINGS.md) for the full analysis.
