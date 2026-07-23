# Crystal Specimen Program

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** Specimen ontology, chain of custody, and the characterization ladders for a natural-vs-synthetic quartz study — all as measurement *requests*.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [INVERSE_PROBLEMS.md](INVERSE_PROBLEMS.md) (why a proxy is not a measurement); [NONLINEAR_OPTICS.md](NONLINEAR_OPTICS.md) (optical properties of quartz)
**Related code / tests / schemas:** [../../r10/specimen.py](../../r10/specimen.py), [../../r10/characterize.py](../../r10/characterize.py); tests/v52/test_r10_specimen.py, tests/v52/test_r10_characterize.py
**Known limitations:** There is no bench in this repository — no polariscope, goniometer, diffractometer, spectrometer, or balance with a specimen on it. Nothing here is measured. Every attribute is `REQUESTED` and cannot be promoted to `MEASURED`.
**Next review trigger:** Acquisition of a real specimen with a documented custody chain, or any instrument coming online.

## The two load-bearing fields

A specimen carries dozens of describable attributes — handedness, twin
law, cut angles, dimensions, mass, inclusions, trace elements — and none
of them is load-bearing. The two fields that decide whether a specimen
means anything are its **verified origin** and its **chain of custody**.
Everything else is measurable after the specimen is in hand; provenance
is the one thing that cannot be recovered later if it was never
established.

The study's whole point is to distinguish natural geological quartz from
hydrothermal synthetic quartz *by measurement*. That makes two labels
worthless as evidence:

- **A seller's "natural" label is not provenance.** Origin is `VERIFIED`
  only when a documented, append-only chain of custody backs it. A
  purchase with no custody record is `ORIGIN_UNVERIFIED`; a specimen
  tagged NATURAL with an empty custody chain is, by construction,
  `ORIGIN_UNVERIFIED`.
- **A material-class label is not a measurement.** Confirming that a
  specimen is natural quartz (rather than synthetic quartz, fused silica,
  or non-quartz glass) requires measurement — that is the study, not an
  input to it.

Synthetic quartz is a **mandatory control**, not an afterthought: without
it the study cannot tell a natural signature from an artefact of the
measurement. Natural quartz is source-required but experimentally
unresolved.

## The characterization ladders (`characterize.py`)

Every rung is a **measurement request**, born `REQUESTED`, never promoted
here because nothing measured it.

- **Low-cost ladder (optical/visual, first):** crossed polarizers for
  twinning and strain; goniometry for crystallographic axis from face
  angles; immersion for inclusion counting; Mohs scratch hardness;
  density by Archimedes weighing.
- **Advanced ladder (instrumental, second):** X-ray Laue for c-axis and
  handedness; FTIR for hydroxyl / structural water; EPR for paramagnetic
  point defects; acoustic-Q ringdown; dielectric loss tan-δ;
  cathodoluminescence for growth sectors; ICP-MS for trace elements.

Two pieces of arithmetic in the module are exact and closed-form:

- **Archimedes density** of α-quartz lands near `2.65 g/cm³` — a check
  value, computed, not weighed here.
- **The c-axis is recoverable from two non-parallel face directions**;
  a single direction is underdetermined (mirroring the roll rule in
  [COORDINATE_SPACE.md](COORDINATE_SPACE.md)).

**Handedness is never inferred from external shape.** Right- vs
left-handed quartz is a lattice property; a stone's habit does not decide
it. Handedness requires X-ray or optical-rotation measurement, or it stays
unknown.

## Summary

The specimen program is an ontology and a request list. It establishes
what would have to be true, and in what order, for a natural-vs-synthetic
determination to mean anything. It determines nothing on its own.

PHYSICAL_VALIDATION_NOT_CLAIMED
