# Null and significance policy

A decoder that always produces output is not evidence. Every lane ships with a
matched control, and the number of hypotheses searched is reported so the
correction can be applied.

## Required controls

| control | destroys | preserves |
|---|---|---|
| random bits, equal length | everything | length |
| byte-shuffled source | order | byte multiset |
| row-shuffled source | row order | per-row values |
| **permutation of the same symbols** | order only | symbol frequency |
| channel-swapped | channel identity | both channels |
| bitplane-permuted | plane assignment | planes |
| matched Poisson counts | structure | rate |
| phase-randomised surrogate | phase | power spectrum |
| injected known message | - | positive control |

The permutation null is usually the right one: it holds symbol frequency fixed, so
a result cannot come from a skewed alphabet.

## Reporting

Report raw score, empirical null percentile, hypothesis count, corrected p-value,
stability across adjacent windows and across equivalent reversible
representations, and **whether the result was selected before or after labels were
revealed**.

## Lessons already paid for

- **Decode success is not evidence.** 56.7% of *random* 24-bit words "decode"
  under Golay. Only distance carries information.
- **A metric may be incapable of carrying the signal you are testing for.** In
  absolute-bearing mode, route straightness is order-invariant - vector addition
  commutes - so it cannot detect ordering. A first pass reported 11 significant
  splits; every one was an artifact of that.
- **Anchor a test to a closed form, not to last week's output.** A planar
  "shoelace" area formula agreed with prior results and was wrong by 42% on a real
  triangle and by a factor of two on a spherical octant.
- **Correct the arithmetic before trusting the conclusion.** A divisibility
  argument computed over framing bits declared three character packings
  impossible; on the stripped payload all three fit exactly.

## Result classes

`NO_PARSE`, `STRUCTURAL_PARSE_ONLY`, `CONVENTIONAL_TEXT_CANDIDATE`,
`ERROR_CONTROL_CANDIDATE`, `RGCS_ENVELOPE_CANDIDATE`, `RGCS_ROUTE_CANDIDATE`,
`ARCHIVE_ARTIFACT`, `INSTRUMENT_ARTIFACT`, `NULL_COMPATIBLE`,
`REPLICATION_REQUIRED`.

There is no `DISCOVERY` and no `MESSAGE_CONFIRMED`.
