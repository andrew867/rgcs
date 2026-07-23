# Data Model

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** How records are typed, how evidence classes constrain them, and how the public/private firewall keeps private content out of the public repository.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [CONTRIBUTOR_ONBOARDING.md](./CONTRIBUTOR_ONBOARDING.md)
**Related code / tests / schemas:** [../../r10/firewall.py](../../r10/firewall.py), [../../r10/claimfirewall.py](../../r10/claimfirewall.py), [../../r10/specimen.py](../../r10/specimen.py), [../../tests/v52/test_r10_claimfirewall.py](../../tests/v52/test_r10_claimfirewall.py)
**Known limitations:** The model types *claims and provenance*, not measurements. No record asserts a physical result; hardware is deferred.
**Next review trigger:** A new evidence class, a new publication class, or a change to firewall policy.

## Typed records

Each schema is a **typed dataclass**. Records carry their provenance and their
epistemic status explicitly rather than by convention. Enumerations (for example
material class, handedness, origin status, custody events in
[../../r10/specimen.py](../../r10/specimen.py)) keep categorical fields closed and
checkable.

## Evidence classes

Every record declares an **evidence class**. The classes in use include:

- `SOURCE_CLAIM` — asserted by a source; not independently established.
- `DERIVED_MATHEMATICS` — a consequence of stated math, nothing more.
- `HISTORICAL_FACT` — an established historical fact.
- `CONVENTIONAL_LITERATURE` — standard, citable literature.
- `SOURCE_REQUIREMENT` — a requirement imposed by a source, held as such.

**No auto-promotion.** A `SOURCE_CLAIM` never becomes `HISTORICAL_FACT` (or any
stronger class) by processing. Promotion is refused structurally;
`r10/claimfirewall.py` exposes `refuse_promotion(...)` and related refusals, and the
tests require those refusals to fire.

## Publication class and the firewall

Every record may carry `publication_class`, defaulting to `PRIVATE_ONLY`. The
public/private firewall is two-layered:

- **Structural** — [../../r10/firewall.py](../../r10/firewall.py). `scan_committed`,
  `scan_working_tree`, and `scan_git_history` scan for leaked private content across
  tracked files, the working tree, and history. `enforce(...)` composes them.
  `frozen_surface_exposure(...)` guards frozen surfaces. Findings must be **empty**
  before any commit.
- **Content claims** — [../../r10/claimfirewall.py](../../r10/claimfirewall.py). It
  quarantines claims and refuses categories that must never be emitted (promotion
  across classes, person classification, biological/genetic targeting, medical
  advice, public accusation, financial action).

## What must never enter a public record

Personal names, private place names, private filesystem paths, the private
repository's literal name, and raw signal digits are all firewall violations. Keep
them out of public files; when a public export is needed, use the sanitized-export
path (`sanitized_export_record`) so only hashes cross the boundary.

## What the model does not represent

The data model records claims, provenance, and epistemic status. It does **not**
record physical measurements, and no record's presence implies validation.

PHYSICAL_VALIDATION_NOT_CLAIMED
