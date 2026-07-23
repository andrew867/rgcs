# Nulls and Falsification

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** How the programme reports null results, why a null must prove its own power, and how look-elsewhere and multiplicity are handled.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [TESTING.md](./TESTING.md)
**Related code / tests / schemas:** [../../r10/base10.py](../../r10/base10.py), [../../r10/cue1604.py](../../r10/cue1604.py), [../../r10/nodes.py](../../r10/nodes.py), [../../r10/natsynth.py](../../r10/natsynth.py)
**Known limitations:** Every null here is computational. None rests on a physical measurement; a null does not confirm or deny any physical effect, only what the analysis can and cannot recover.
**Next review trigger:** A new search or decoder is added, or the null/power contract changes.

## A null must prove its power

A null result is only meaningful if the method could have found a signal had one been
present. So every null is paired with a **planted-signal power check**: inject a known
effect and require the pipeline to recover it. A null with demonstrated power says
"there is nothing here that this method can see, and this method can see a planted
signal" — not merely "we found nothing."

The distinction is explicit in the verdict strings. For example the base-10 search
reports `NO_DECODER_IDENTIFIED`, **not** `NO_DECODER_POSSIBLE`: the method failed to
find a decoder, and it does not claim none can exist.

## Look-elsewhere and matched nulls

Searches over many candidate expressions or alignments inflate the chance of a
spurious hit. The programme uses **look-elsewhere / matched nulls**: the observed
statistic is compared against a null distribution built under the same search breadth
(span-matched, label-matched, or geometry-matched as appropriate), so the reported
p-value already accounts for how many places were looked.

## Worked verdicts

- **Continuous-wave construction** — `EXPLAINED_BY_CONSTRUCTION`: the apparent
  structure follows from how the object was built, so it is not evidence of anything
  beyond the construction.
- **Base-10 decoder search** (`r10/base10.py`) — `NO_DECODER_IDENTIFIED`, with a
  span-matched null giving p ≈ 0.86. The clustering is reported as real; no decoder is
  claimed.
- **1604 ≈ 925·√3 numeric cue** (`r10/cue1604.py`) — `NO_BETTER_THAN_CHANCE`,
  p ≈ 1.0. The power control plants an exact grid expression and recovers it at
  essentially zero, so the null has demonstrated power.
- **Node alignment** (`r10/nodes.py`) — `NO_BETTER_THAN_CHANCE`.

## Natural-vs-synthetic nulls

The natural-vs-synthetic comparison (`r10/natsynth.py`) uses **label-shuffle nulls**
with **multiplicity correction** (`label_shuffle_null`, `multiplicity_correct`,
default Bonferroni), a demonstrated planted-group-effect power check
(`planted_group_effect_power`), and refusals for unpreregistered endpoints and for
reaching an exotic explanation before ordinary ones. See
[EXPERIMENT_HANDBOOK.md](./EXPERIMENT_HANDBOOK.md).

## The falsification stance

The programme is built to be **falsifiable and mostly falsified**: the default result
is a null or a refusal. A positive result must survive a power check and the
multiplicity/look-elsewhere correction before it is reported at all — and even then it
is a computational finding, never a physical validation.

PHYSICAL_VALIDATION_NOT_CLAIMED
