# Natural vs Synthetic Quartz — Source Requirement and Matched Experiment

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** how a private "natural quartz is required" source hypothesis becomes a public, blinded, controlled experiment — and nothing more.
**Last verified commit:** v5.8.0 baseline (branch `v580-r10-10`).
**Prerequisites:** [SCIENTIFIC_BOUNDARIES](../../SCIENTIFIC_BOUNDARIES.md), [CRYSTAL_SPECIMEN_PROGRAM](CRYSTAL_SPECIMEN_PROGRAM.md).
**Related code / tests / schemas:** [`r10/naturalsource.py`](../../r10/naturalsource.py), [`r10/natsynth.py`](../../r10/natsynth.py), [`r10/specimen.py`](../../r10/specimen.py); schemas `NaturalSyntheticComparison`, `Specimen`.
**Known limitations:** no specimens are in hand (`BLOCKED_NO_SPECIMENS`); nothing is measured; hardware deferred.
**Next review trigger:** acquisition of verified specimens, or any measured endpoint.

---

## The claim ladder, and where we are on it

```
SOURCE_REQUIREMENT -> HISTORICAL_FACT -> MATHEMATICAL_DERIVATION ->
SOFTWARE_VERIFIED -> MATERIAL_DIFFERENCE_MEASURED ->
CONTROLLED_EFFECT_MEASURED -> INDEPENDENTLY_REPLICATED
```

We are at `SOFTWARE_VERIFIED`. The rungs from `MATERIAL_DIFFERENCE_MEASURED`
onward are **empty** — no measurement has been made. There are no
automatic jumps.

## Source requirement → experimental variable

The private source hypothesis is that naturally grown geological quartz is
*required* because its growth history is part of the intended function.
That interpretation is **private Tier-A material and stays private.**
Publicly it becomes exactly one disciplined thing:

> **Geological growth history is an independent experimental variable.**

`refuse_publish_consciousness_as_materials_science()` blocks any attempt
to publish the private interpretation as established science. The public
verdict is **`SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED`**: the source
requires it, and no experiment here resolves whether it matters.

## Synthetic quartz is a mandatory control, not a rival

- **Primary lane:** verified natural geological quartz (with a
  [chain of custody](CRYSTAL_SPECIMEN_PROGRAM.md) — a seller label is not
  provenance).
- **Mandatory controls:** hydrothermal synthetic alpha-quartz, fused
  silica, nonquartz glass, multiple localities, varied defect levels.

Dropping a control is refused (`refuse_drop_synthetic_control`): the
natural-primary lane is untestable without them, and a missing control is
how a null becomes a false positive.

## The matched protocol

`r10/natsynth.py` builds a **blinded, preregistered** design matched on
geometry, handedness, mass, `c`-axis, and fixture, with **dummy**
specimens and randomized, coded identities. Endpoints must be
preregistered (`refuse_unpreregistered_endpoint`). The test is a
**label-shuffle null** with **multiplicity correction**; it has proven
**power** on a planted natural-group effect and returns non-significance
when there is no real difference.

## The ordinary-explanation firewall

If a natural/synthetic difference is ever measured, it is attributed to
**ordinary differentiators first** — trace elements, inclusions,
dislocations, hydroxyl/water, growth sectors, internal stress. A group
difference is **materials science until proven otherwise**;
`refuse_exotic_explanation()` refuses to call it evidence of "consciousness
storage" or any special property, and `refuse_natural_superiority_claim()`
refuses any claim that natural quartz is superior.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
