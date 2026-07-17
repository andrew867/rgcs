# Timing family audit (Agent C04)

Coverage: **F001–F052** (timing side). Status: registry +
`SOURCE_HYPOTHESIS` per entry.
Implementation: `rscs2_core.frequency_keys.build_registry`.

## Timing candidates and their inverses

Every timing motif in the corpus is registered with its exact formula
and its frequency inverse, so a period and a frequency can never be
confused for independent evidence of each other:

| Motif | Value | Inverse | Kind |
|---|---|---|---|
| 46 ms | 0.046 s | 21.739 Hz | `timing_inverse` |
| 60π/4096 | 0.04602 s | 21.729 Hz | `timing_inverse` |
| 192 cycles @ 4096 Hz | 0.046875 s | 21.333 Hz | `timing_inverse` |
| φ⁸ | 46.979 | — | `dimensionless_ratio` |
| 552 ms | 0.552 s | 1.812 Hz | `timing_inverse` |
| 2260.992 | — | — | `arithmetic_motif` |
| 1507.328 | — | — | `arithmetic_motif` |

## The 46 ms cluster is the instructive case

Four different constructions land near 46 ms: a round 46, 60π/4096 =
46.02, 192 cycles at 4096 Hz = 46.875, and φ⁸ = 46.979 (dimensionless,
and therefore **not** a time at all).

They are close. They are **not equal**, and the differences (up to 2%)
exceed the tolerance any of them would be tested at. The register keeps
them as four distinct entries rather than one "≈46 ms family", because
merging them would manufacture agreement that the arithmetic does not
contain.

φ⁸ deserves the sharpest note: it is a pure number. Reading 46.979 as
"46.979 ms" silently attaches a unit that no equation supplies. It is
registered as a `dimensionless_ratio` and cannot enter the timing graph.

## Harmonic graph versus near-overlap table

Two structures, deliberately separate:

- **Exact algebraic relations** (the harmonic graph): 4096 = 2¹² × 1,
  40.96 = 4096/100, 20.48 = 40.96/2. These are identities. They are
  true by construction and carry no physical content.
- **Near numerical overlaps** (the coincidence table): 4095 vs 4096,
  20.6061 vs 20.62116, the tuner families 4096/4160/4225. These are
  *not* identities and each is reported with its exact separation and
  its look-elsewhere expectation.

Keeping them in one table would let an identity lend credibility to a
coincidence sitting next to it.

## Neighbour control requirement

Every frequency dispatched by an experimental protocol must be
accompanied by neighbours at ±0.5% and ±2%. The logic:

- If the response at 4096 Hz is indistinguishable from 4076 and 4116
  Hz, the number is not special — the instrument or the mode is broad.
- If it is distinguishable, the claim survives one round and the effect
  size is measured against the neighbours, not against silence.

The E01 acoustic campaign implements this as a required control class.

## Progressive 10..550 sequence

Registered as an `arithmetic_motif` sweep plan. A sweep that visits 100+
frequencies and reports the best one has tried 100+ candidates; the
look-elsewhere penalty applies with M = 100+, and
`coincidence_significance()` is the arbiter.

## Failure conditions

- A timing motif is promoted without its dimensional check → schema
  refuses (`FrequencyKeyRecord` requires a legal `frequency_kind`).
- A near overlap is reported without its `expected_chance_hits` → QA
  defect.
- Two distinct values silently merged into a family → P02 violation
  (ORPHAN rule).

## Status

Every entry here is `SOURCE_HYPOTHESIS` or an arithmetic motif. **None
is an established physical frequency of any quartz body.** The
computed modal frequencies from the FEM solver are the only entries
carrying `exact_physical_frequency`, and those come from the model, not
from the corpus.
