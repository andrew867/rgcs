# Experiment Handbook

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The preregistered natural-vs-synthetic protocol, the specimen ontology and chain of custody, and the characterization ladders — all as computational scaffolding, with real specimens blocked.
**Prerequisites:** [NULLS_AND_FALSIFICATION.md](./NULLS_AND_FALSIFICATION.md), [DATA_MODEL.md](./DATA_MODEL.md)
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Related code / tests / schemas:** [../../r10/natsynth.py](../../r10/natsynth.py), [../../r10/specimen.py](../../r10/specimen.py), [../../r10/characterize.py](../../r10/characterize.py), [../../tests/v52/test_r10_natsynth.py](../../tests/v52/test_r10_natsynth.py)
**Known limitations:** There is **no apparatus** and hardware is deferred. No specimen has been measured; the natural-vs-synthetic comparison returns `BLOCKED_NO_SPECIMENS`. Everything here defines *how* an experiment would run, not results.
**Next review trigger:** Specimens or apparatus become available, or the preregistered protocol changes.

## The natural-vs-synthetic matched protocol

`r10/natsynth.py` defines a **blinded, preregistered, matched** comparison between
natural and synthetic quartz specimens. The design (`matched_protocol`,
`matches_required_variables`) requires matching on:

- geometry,
- handedness,
- mass,
- c-axis orientation,
- fixture.

Additional requirements:

- **Blinding** — `blind_labels` assigns blinded labels from a fixed seed; `reveal`
  unblinds only against the held key.
- **Dummy controls** — dummies are carried through alongside real specimens.
- **Ordinary explanations first** — any observed difference must be explained by
  ordinary differentiators before any exotic explanation is entertained;
  `refuse_exotic_explanation` enforces this, and `refuse_unpreregistered_endpoint`
  blocks endpoints that were not preregistered.
- **Nulls** — label-shuffle nulls (`label_shuffle_null`) with multiplicity correction
  (`multiplicity_correct`) and a planted-effect power check
  (`planted_group_effect_power`). See [NULLS_AND_FALSIFICATION.md](./NULLS_AND_FALSIFICATION.md).

**Current status: real specimens are `BLOCKED_NO_SPECIMENS`.** The protocol runs only
on planted/dummy data to demonstrate power and refusal behavior.

## Specimen ontology and chain of custody

`r10/specimen.py` types a specimen with a closed material class, handedness, and
origin status, plus a **chain of custody** (`ChainOfCustody`, `CustodyEvent`). Origin
is derived (`origin_status`), never assumed. The module **refuses** a natural-origin
claim without custody (`refuse_natural_claim_without_custody`) and refuses a material
class without measurement (`refuse_material_class_without_measurement`). A specimen
with no custody cannot be called natural.

## Characterization ladders

`r10/characterize.py` defines tiered characterization **methods** and **defect
proxies** (`Tier`, `Method`, `methods_in_tier`, `DefectKind`, `DefectProxy`,
`request_defect`). It **refuses a result without a measurement**
(`refuse_result_without_measurement`): a proxy is a request for characterization, not
a finding. The ladder describes what would be measured and in what order — it does not
stand in for having measured it.

## Reading this handbook correctly

Every protocol here is the **design** of an experiment. No specimen has been
characterized, no comparison has been run on real material, and no apparatus exists.
The value of the code is that it encodes the blinding, matching, preregistration, and
refusal discipline in advance, so that if specimens ever arrive the analysis cannot be
tuned after the fact.

PHYSICAL_VALIDATION_NOT_CLAIMED
